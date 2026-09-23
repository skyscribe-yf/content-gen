#!/usr/bin/env python3
"""三目标对照实验：同一 toy 数据、同一网络、同一预算，分别学 x0 / eps / score。

问题（2208.11970 §3.4；Ho 2020 / Imagen 的实证）：三个训练目标的最优解是同一件事，
但实践里「预测 eps 更好」。这个实验把那句话变成可看的曲线：
等价的是最优解，不等价的是学习难度——三个目标各自在不同的噪声段先学不动。

数据：8 峰高斯混合（与步数篇同一分布）；VP / cosine 调度，T = 1000。
模型：纯 numpy 手写小 MLP（3 -> 128 -> 128 -> 2，SiLU），三个目标共用同一初始化，
      并且同一步吃同一批数据。训练目标（都不加权 MSE 回归）：
        x0    目标：x0
        eps   目标：eps
        score 目标：-eps / sqrt(1-abar)   （denoising score matching 的回归目标）

评价：解析真值参照。E[x0|x_t]、E[eps|x_t]、∇log p_t(x_t) 均有闭式（后验责任度加权）。
      每个噪声水平上报：学出的场与解析场的余弦、换算回 x0 空间的 RMSE、
      以及各目标自身的相对误差（正文按需引用）。
诚实边界：玩具 + 逐点指标，不等于端到端生成质量；结论只用于说明机制。
产物：results.json（正文数字必须与此一致）/ 02-target-alignment.png / 03-three-faces.png
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = ["Noto Sans CJK TC", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent
SEED = 20260920
T = 1000
MODES = 8
RADIUS = 3.0
SIGMA = 0.35
AB_MIN = 0.01
STEPS = 4000
BATCH = 512
HID = 128
LR = 1e-3
N_EVAL = 4000
AB_EVAL = [0.99, 0.95, 0.9, 0.8, 0.6, 0.4, 0.2, 0.1, 0.05, 0.02, 0.01]
BLUE, ORANGE, YELLOW, INK, GREY, GREEN = (
    "#0F4C81", "#E76F51", "#F6BD60", "#17324D", "#5B7186", "#2A9D8F")

_ang = np.arange(MODES) * 2 * np.pi / MODES
CENTERS = np.stack([RADIUS * np.cos(_ang), RADIUS * np.sin(_ang)], 1)


def cosine_ab() -> np.ndarray:
    g = np.arange(1, T + 1) / T
    f = np.cos((g + 0.008) / 1.008 * math.pi / 2) ** 2
    ab = f / np.cos(0.008 / 1.008 * math.pi / 2) ** 2
    ab = np.clip(ab, AB_MIN, 1.0)
    return np.concatenate([[1.0], ab])


AB_IDX = cosine_ab()


def sample_true(n, rng):
    return CENTERS[rng.integers(0, MODES, size=n)] + rng.normal(0, SIGMA, size=(n, 2))


def logsnr(ab):
    return np.log(ab / (1 - ab))


# ------------------------------------------------------------ 解析真值参照
def responsibilities(x, ab: float):
    s2 = ab * SIGMA ** 2 + (1 - ab)
    mu = math.sqrt(ab) * CENTERS
    d2 = ((x[:, None, :] - mu[None]) ** 2).sum(-1)
    logit = -d2 / (2 * s2)
    logit -= logit.max(1, keepdims=True)
    w = np.exp(logit)
    return w / w.sum(1, keepdims=True), s2


def analytic_fields(x, ab: float):
    """返回 (E[x0|x_t], E[eps|x_t], ∇log p_t(x_t))，全部闭式。"""
    r, s2 = responsibilities(x, ab)
    mbar = (r[:, :, None] * CENTERS[None]).sum(1)
    score = (math.sqrt(ab) * mbar - x) / s2
    eps = -math.sqrt(1 - ab) * score
    prec = 1 / SIGMA ** 2 + ab / (1 - ab)
    v = 1 / prec
    m_k = v * (CENTERS[None] / SIGMA ** 2 + math.sqrt(ab) * x[:, None] / (1 - ab))
    x0_mean = (r[:, :, None] * m_k).sum(1)
    return x0_mean, eps, score


# ------------------------------------------------ 纯 numpy 小 MLP（手写反传 + Adam）
def silu(x):
    return x / (1 + np.exp(-x))


def silu_grad(x):
    s = 1 / (1 + np.exp(-x))
    return s * (1 + x * (1 - s))


class MLP:
    def __init__(self, seed: int, din=3, h=HID, dout=2):
        rng = np.random.default_rng(seed)
        def w(a, b):
            return rng.normal(0, math.sqrt(2.0 / a), (a, b))
        self.p = {"W1": w(din, h), "b1": np.zeros(h),
                  "W2": w(h, h), "b2": np.zeros(h),
                  "W3": w(h, dout), "b3": np.zeros(dout)}
        self.m = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.step_n = 0

    def forward(self, X):
        z1 = X @ self.p["W1"] + self.p["b1"]
        a1 = silu(z1)
        z2 = a1 @ self.p["W2"] + self.p["b2"]
        a2 = silu(z2)
        out = a2 @ self.p["W3"] + self.p["b3"]
        self.cache = (X, z1, a1, z2, a2)
        return out

    def train_step(self, X, Y):
        B = X.shape[0]
        out = self.forward(X)
        dout = (out - Y) / B                       # 半 MSE：loss = 0.5 * mean_batch ||out-Y||^2
        Xc, z1, a1, z2, a2 = self.cache
        g = {}
        g["W3"] = a2.T @ dout
        g["b3"] = dout.sum(0)
        dz2 = (dout @ self.p["W3"].T) * silu_grad(z2)
        g["W2"] = a1.T @ dz2
        g["b2"] = dz2.sum(0)
        dz1 = (dz2 @ self.p["W2"].T) * silu_grad(z1)
        g["W1"] = Xc.T @ dz1
        g["b1"] = dz1.sum(0)
        self.step_n += 1
        b1, b2, eps = 0.9, 0.999, 1e-8
        for k in self.p:
            self.m[k] = b1 * self.m[k] + (1 - b1) * g[k]
            self.v[k] = b2 * self.v[k] + (1 - b2) * g[k] ** 2
            mhat = self.m[k] / (1 - b1 ** self.step_n)
            vhat = self.v[k] / (1 - b2 ** self.step_n)
            self.p[k] -= LR * mhat / (np.sqrt(vhat) + eps)
        return float(0.5 * ((out - Y) ** 2).sum(1).mean())


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)              # 数据流唯一来源：三个模型吃同一批
    names = ["x0", "eps", "score"]
    models = {n: MLP(SEED + 1) for n in names}     # 同一初始化
    losses = {n: [] for n in names}

    for step in range(STEPS):
        t_idx = rng.integers(1, T + 1, size=BATCH)
        ab = AB_IDX[t_idx]
        x0 = sample_true(BATCH, rng)
        eps = rng.normal(0, 1, size=(BATCH, 2))
        x_t = np.sqrt(ab)[:, None] * x0 + np.sqrt(1 - ab)[:, None] * eps
        feat = np.stack([x_t[:, 0], x_t[:, 1], logsnr(ab) / 5.0], 1)
        tgt = {"x0": x0, "eps": eps, "score": -eps / np.sqrt(1 - ab)[:, None]}
        for n in names:
            losses[n].append(models[n].train_step(feat, tgt[n]))
        if (step + 1) % 500 == 0:
            tail = {n: round(float(np.mean(losses[n][-200:])), 4) for n in names}
            print(f"step {step+1:5d}  losses {tail}  ({time.time()-t0:.0f}s)", flush=True)

    # ---------------------------------------------------------------- 评价
    out = {
        "config": {"seed": SEED, "T": T, "modes": MODES, "radius": RADIUS, "sigma": SIGMA,
                   "schedule": "cosine", "alpha_bar_min": AB_MIN, "steps": STEPS,
                   "batch": BATCH, "hidden": HID, "lr": LR, "n_eval": N_EVAL,
                   "targets": {"x0": "x0", "eps": "eps", "score": "-eps/sqrt(1-abar)"},
                   "model": "tiny numpy MLP, identical init & data order for the 3 targets"},
        "final_train_loss": {n: round(float(np.mean(losses[n][-500:])), 5) for n in names},
        "by_alpha": {},
    }
    for ab in AB_EVAL:
        x0e = sample_true(N_EVAL, rng)
        epse = rng.normal(0, 1, size=(N_EVAL, 2))
        x_te = math.sqrt(ab) * x0e + math.sqrt(1 - ab) * epse
        fe = np.stack([x_te[:, 0], x_te[:, 1],
                       np.full(N_EVAL, math.log(ab / (1 - ab)) / 5.0)], 1)
        x0_star, eps_star, score_star = analytic_fields(x_te, ab)
        t_idx = int(np.argmin(np.abs(AB_IDX - ab)))
        row = {"t_over_T": round(t_idx / T, 4), "alpha_bar": ab}
        for n in names:
            pred = models[n].forward(fe)
            if n == "x0":
                tgt, xhat = x0_star, pred
            elif n == "eps":
                tgt, xhat = eps_star, (x_te - math.sqrt(1 - ab) * pred) / math.sqrt(ab)
            else:
                tgt, xhat = score_star, (x_te + (1 - ab) * pred) / math.sqrt(ab)
            rmse = float(np.sqrt(((pred - tgt) ** 2).sum(1).mean()))
            sig = float(np.sqrt((tgt ** 2).sum(1).mean()))
            num = (pred * tgt).sum(1)
            den = np.linalg.norm(pred, axis=1) * np.linalg.norm(tgt, axis=1) + 1e-12
            row[n] = {
                "rmse": round(rmse, 4),
                "target_rms": round(sig, 4),
                "rel_err": round(rmse / max(sig, 1e-9), 4),
                "cos": round(float((num / den).mean()), 4),
                "x0_space_rmse": round(float(np.sqrt(((xhat - x0_star) ** 2).sum(1).mean())), 4),
            }
        out["by_alpha"][str(ab)] = row
        print(f"ab={ab:<5} t/T={row['t_over_T']:.2f}  "
              + "  ".join(f"{n}: cos={row[n]['cos']:.3f} x0rmse={row[n]['x0_space_rmse']:.3f}"
                          for n in names), flush=True)

    # ------------------------------------------------------ 三张脸的恒等式核对
    ab0 = 0.5
    x_chk = math.sqrt(ab0) * sample_true(400, rng) + math.sqrt(1 - ab0) * rng.normal(0, 1, (400, 2))
    x0_star, eps_star, score_star = analytic_fields(x_chk, ab0)
    dev_score_eps = float(np.abs(eps_star + math.sqrt(1 - ab0) * score_star).max())
    dev_x0_eps = float(np.abs(math.sqrt(ab0) * x0_star + math.sqrt(1 - ab0) * eps_star - x_chk).max())
    out["identity_check"] = {
        "alpha_bar": ab0, "n_points": 400,
        "max_abs_dev_eps_vs_neg_sqrt1mab_score": f"{dev_score_eps:.3e}",
        "max_abs_dev_xt_vs_sqrtab_x0star_plus_sqrt1mab_epsstar": f"{dev_x0_eps:.3e}",
        "note": "eps = -sqrt(1-abar) * score 与 x_t = sqrt(abar) E[x0|x_t] + sqrt(1-abar) E[eps|x_t] 的数值残差",
    }

    out["runtime_sec"] = round(time.time() - t0, 1)
    (ROOT / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    plot_alignment(out, ROOT / "02-target-alignment.png")
    plot_faces(x_chk, x0_star, eps_star, score_star, ab0, out["identity_check"],
               ROOT / "03-three-faces.png")
    print("saved.", flush=True)


def plot_alignment(res, path):
    rows = [res["by_alpha"][str(ab)] for ab in AB_EVAL]
    xs = [r["t_over_T"] for r in rows]
    colors = {"x0": ORANGE, "eps": BLUE, "score": GREEN}
    labels = {"x0": "学「预测原图 x₀」", "eps": "学「预测噪声 ε」", "score": "学「预测分数 ∇log p」"}

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.4), facecolor="#F8FAFC")
    for n in ("x0", "eps", "score"):
        axes[0].plot(xs, [r[n]["cos"] for r in rows], "-o", color=colors[n], lw=2.2, ms=7,
                     label=labels[n])
        axes[1].plot(xs, [r[n]["x0_space_rmse"] for r in rows], "-o", color=colors[n], lw=2.2,
                     ms=7, label=labels[n])
    axes[0].set_ylim(-0.1, 1.06)
    axes[0].set_ylabel("学出的场 vs 解析真值的余弦", fontsize=12)
    axes[1].set_ylabel("换算回 x₀ 的估计误差（RMSE，数据半径 = 3）", fontsize=12)
    for ax in axes:
        ax.set_xlabel("噪声水平 t/T（越右越噪）", fontsize=12)
        ax.grid(alpha=.25)
        ax.legend(fontsize=11, frameon=False)
    axes[0].set_title("方向对不对：三个目标的场与真值余弦", fontsize=14, color=INK)
    axes[1].set_title("代价多大：同一个 x₀ 单位下比谁错得多", fontsize=14, color=INK)
    fig.suptitle("同一网络、同一预算，只换训练目标", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


def plot_faces(x_chk, x0_star, eps_star, score_star, ab0, ident, path):
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.8), facecolor="#F8FAFC")
    a = axes[0]
    a.scatter(-math.sqrt(1 - ab0) * score_star[:, 0], eps_star[:, 0], s=8, color=BLUE, alpha=.55)
    lo = float(min(-math.sqrt(1 - ab0) * score_star[:, 0].min(), eps_star[:, 0].min())) * 1.05
    hi = float(max(-math.sqrt(1 - ab0) * score_star[:, 0].max(), eps_star[:, 0].max())) * 1.05
    a.plot([lo, hi], [lo, hi], "--", color=GREY, lw=1.2)
    a.set_xlabel("由「分数」换算出的噪声：−√(1−ᾱ)·∇log p", fontsize=11)
    a.set_ylabel("真值 E[ε|xₜ]", fontsize=11)
    a.set_title(f"ε 和分数是同一张脸（残差 {ident['max_abs_dev_eps_vs_neg_sqrt1mab_score']}）",
                fontsize=12.5, color=INK)
    a.grid(alpha=.25)
    b = axes[1]
    recon = math.sqrt(ab0) * x0_star[:, 0] + math.sqrt(1 - ab0) * eps_star[:, 0]
    b.scatter(recon, x_chk[:, 0], s=8, color=ORANGE, alpha=.55)
    lo2 = float(min(recon.min(), x_chk[:, 0].min())) * 1.05
    hi2 = float(max(recon.max(), x_chk[:, 0].max())) * 1.05
    b.plot([lo2, hi2], [lo2, hi2], "--", color=GREY, lw=1.2)
    b.set_xlabel("√ᾱ·E[x₀|xₜ] + √(1−ᾱ)·E[ε|xₜ]", fontsize=11)
    b.set_ylabel("实际含噪图 xₜ", fontsize=11)
    b.set_title(f"三张脸拼回原样（残差 {ident['max_abs_dev_xt_vs_sqrtab_x0star_plus_sqrt1mab_epsstar']}）",
                fontsize=12.5, color=INK)
    b.grid(alpha=.25)
    fig.suptitle("数学上是同一件事：三张脸的换算恒等式逐点核对", fontsize=15, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


if __name__ == "__main__":
    main()
