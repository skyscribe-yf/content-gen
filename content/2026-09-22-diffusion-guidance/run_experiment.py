#!/usr/bin/env python3
"""篇 3 实验：引导（CFG）——方向从哪来 / γ 在买什么 / 负向词把锚换到哪。

主线问题（分类器引导 Dhariwal & Nichol 2021；CFG Ho & Salimans 2022；
过曝与重缩放 Lin et al. 2023；负向词机制 Ban et al. ECCV 2024）。四块实验：

  ① 方向验证     ：恒等式 eps_uncond - eps_y = sigma * grad log p(y|x) 的实测对拍
                   （贝叶斯分解 = "CFG 就是隐式分类器引导" 的数值证据）。
                   按 sigma 与「离数据环多远」两个维度看误差长在哪。
  ② gamma 扫描   ：保真度（落进目标峰的比例）× 多样性（目标盆地内散度）×
                   出壳率（离开数据薄壳的比例）三条曲线 → 找临界点。
                  gamma=1 是「纯条件模型」，>1 是外推。
  ③ 出壳面板     ：并入 ②（09-15 已定性断言，本篇给数字）。
  ④ 负向推力     ：把 CFG 的无条件端点换成另一个峰的锚 —— 样本被推到哪个峰？
                   相邻锚 / 对侧锚两种；看「反而落到第三个峰」是否出现。

数据：8 峰高斯混合（环上等角、不等权、sigma_peak=0.35、半径 3），**每个峰 = 一个类别**。
模型：纯 numpy 手写小 MLP（Adam）——无条件网络 eps(x, sigma) 与
      类别条件网络 eps(x, sigma, y)（y 用 one-hot）。权重 nets.npz，可 --replot 只重绘。
解析侧：类后验是闭式的（责任值），所以真分类器梯度可精确算 —— 实验 ① 零模型误差对拍。
诚实边界：玩具 + 逐点指标 != 端到端生成质量；结论只说明机制。
产物：results.json / nets.npz / A-direction-check.png / B-gamma-scan.png / C-negative-push.png
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
SEED = 20260922
MODES, RADIUS, SIGMA_PEAK = 8, 3.0, 0.35
WEIGHTS = np.array([0.30, 0.20, 0.15, 0.10, 0.08, 0.07, 0.06, 0.04])
SIGMA_MIN, SIGMA_MAX, LEVELS = 0.05, 3.0, 10
SIGMAS_TRAIN = np.geomspace(SIGMA_MIN, SIGMA_MAX, 32)
LOG_SMIN, LOG_SMAX = math.log(SIGMA_MIN), math.log(SIGMA_MAX)
STEPS_UNCOND, STEPS_COND, BATCH, HID = 24000, 32000, 512, 128
SIGMA_SINGLE = 0.05

BLUE, ORANGE, YELLOW, INK, GREY, GREEN, RED, PURPLE = (
    "#0F4C81", "#E76F51", "#F6BD60", "#17324D", "#5B7186", "#2A9D8F", "#C44536", "#7B5EA7")

ANG = np.arange(MODES) * 2 * np.pi / MODES
CENTERS = np.stack([RADIUS * np.cos(ANG), RADIUS * np.sin(ANG)], 1)


# ------------------------------------------------------------------ 数据与解析真值
def sample_data(n, rng, y=None):
    """不传 y：按真实权重抽样；传 y（标量或数组）：从对应峰里抽。"""
    if y is None:
        k = rng.choice(MODES, size=n, p=WEIGHTS)
    else:
        k = np.broadcast_to(np.asarray(y, int), (n,))
    return CENTERS[k] + rng.normal(0, SIGMA_PEAK, size=(n, 2)), k


def gmm_resp(x, sig):
    """p_σ 下各峰的责任值（= 类后验 p(y|x) 在加噪分布下的闭式）。"""
    s2 = SIGMA_PEAK ** 2 + np.asarray(sig, float) ** 2
    d2 = ((x[:, None, :] - CENTERS[None]) ** 2).sum(-1)
    logw = np.log(WEIGHTS)[None] - d2 / (2 * s2)
    logw -= logw.max(1, keepdims=True)
    r = np.exp(logw)
    return r / r.sum(1, keepdims=True), s2


def analytic_eps(x, sig, y=None):
    """加噪分布下的最优噪声预测。y=None → 无条件（混合）；否则 → 条件（单峰）。

    条件分布 p_σ(x|y) = N(x; μ_y, σ_peak² + σ²)，其最优 ε 是它的后验均值：
        E[x₀|x] = (σ_peak² x + σ² μ_y) / (σ_peak² + σ²)，  ε = (x − E[x₀|x]) / σ
    """
    sig = np.asarray(sig, float)
    if y is None:
        r, s2 = gmm_resp(x, sig)
        x0m = (r[:, :, None] * ((SIGMA_PEAK ** 2 * x[:, None, :]
                                 + sig ** 2 * CENTERS[None]) / s2)).sum(1)
        return (x - x0m) / sig
    mu = CENTERS[np.asarray(y, int)][:, None, :] if np.ndim(y) else CENTERS[int(y)][None, :]
    s2 = SIGMA_PEAK ** 2 + sig ** 2
    x0m = (SIGMA_PEAK ** 2 * x + sig ** 2 * mu) / s2
    return (x - x0m) / sig


def classifier_grad(x, sig, y):
    """真分类器梯度 ∇log p_σ(y|x) = (μ_y − μ̄(x)) / s²（闭式，μ̄ = 责任加权峰心）。

    恒等式（本篇实验 ① 的对拍对象）：ε_∅ − ε_y = σ · ∇log p_σ(y|x)，数值残差 ~1e-16。
    """
    r, s2 = gmm_resp(x, sig)
    mu_bar = (r[:, :, None] * CENTERS[None]).sum(1)
    mu_y = CENTERS[np.asarray(y, int)]
    return (mu_y[None, :] - mu_bar) / s2


# ---------------------------------------------------------- 纯 numpy 小 MLP + Adam
def silu(x):
    return x / (1 + np.exp(-np.clip(x, -60, 60)))


def silu_grad(x):
    s = 1 / (1 + np.exp(-np.clip(x, -60, 60)))
    return s * (1 + x * (1 - s))


class MLP:
    def __init__(self, seed, din, h=HID, dout=2, lr=1e-3):
        rng = np.random.default_rng(seed)

        def w(a, b):
            return rng.normal(0, math.sqrt(2.0 / a), (a, b))

        self.p = {"W1": w(din, h), "b1": np.zeros(h),
                  "W2": w(h, h), "b2": np.zeros(h),
                  "W3": w(h, dout), "b3": np.zeros(dout)}
        self.m = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.step_n, self.lr = 0, lr

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
        dout = (out - Y) / B
        Xc, z1, a1, z2, a2 = self.cache
        g = {"W3": a2.T @ dout, "b3": dout.sum(0)}
        dz2 = (dout @ self.p["W3"].T) * silu_grad(z2)
        g["W2"], g["b2"] = a1.T @ dz2, dz2.sum(0)
        dz1 = (dz2 @ self.p["W2"].T) * silu_grad(z1)
        g["W1"], g["b1"] = Xc.T @ dz1, dz1.sum(0)
        self.step_n += 1
        b1, b2, eps = 0.9, 0.999, 1e-8
        for k in self.p:
            self.m[k] = b1 * self.m[k] + (1 - b1) * g[k]
            self.v[k] = b2 * self.v[k] + (1 - b2) * g[k] ** 2
            mh = self.m[k] / (1 - b1 ** self.step_n)
            vh = self.v[k] / (1 - b2 ** self.step_n)
            self.p[k] -= self.lr * mh / (np.sqrt(vh) + eps)
        return float(0.5 * ((out - Y) ** 2).sum(1).mean())

    def save(self, path, prefix):
        np.savez_compressed(path, **{f"{prefix}_{k}": v for k, v in self.p.items()})

    def load(self, path, prefix):
        z = np.load(path)
        for k in self.p:
            self.p[k] = z[f"{prefix}_{k}"]


def f_uncond(x, sig):
    s = np.full((x.shape[0], 1), float(sig)) if np.ndim(sig) == 0 \
        else np.asarray(sig, float).reshape(-1, 1)
    return np.concatenate([x, (np.log(s) - LOG_SMIN) / (LOG_SMAX - LOG_SMIN)], 1)


def f_cond(x, sig, y):
    s = np.full((x.shape[0], 1), float(sig)) if np.ndim(sig) == 0 \
        else np.asarray(sig, float).reshape(-1, 1)
    u = (np.log(s) - LOG_SMIN) / (LOG_SMAX - LOG_SMIN)
    yy = np.zeros((x.shape[0], MODES))
    yy[np.arange(x.shape[0]), np.broadcast_to(np.asarray(y, int), (x.shape[0],))] = 1.0
    return np.concatenate([x, u, yy], 1)


def train_uncond(seed):
    net = MLP(seed, din=3)
    rng = np.random.default_rng(seed + 7)
    losses = []
    for _ in range(STEPS_UNCOND):
        x0, _ = sample_data(BATCH, rng)
        sig = SIGMAS_TRAIN[rng.integers(0, len(SIGMAS_TRAIN), size=BATCH)]
        eps = rng.normal(0, 1, size=(BATCH, 2))
        losses.append(net.train_step(f_uncond(x0 + sig[:, None] * eps, sig), eps))
    return net, losses


def train_cond(seed):
    net = MLP(seed, din=2 + 1 + MODES)
    rng = np.random.default_rng(seed + 13)
    losses = []
    for _ in range(STEPS_COND):
        y = rng.integers(0, MODES, size=BATCH)
        x0, _ = sample_data(BATCH, rng, y=y)
        sig = SIGMAS_TRAIN[rng.integers(0, len(SIGMAS_TRAIN), size=BATCH)]
        eps = rng.normal(0, 1, size=(BATCH, 2))
        losses.append(net.train_step(f_cond(x0 + sig[:, None] * eps, sig, y), eps))
    return net, losses


# ------------------------------------------------------------------------- 采样器
def annealed_cfg(net_u, net_c, x0, sigmas, steps_per_level, rng, eps_fn, eta_scale=0.35,
                 y_inv=None, neg_out=None):
    """多级退火朗之万，每级用 CFG 组合场。

    eps_fn(X, sig) → eps_hat：调用方决定引导参数。
    """
    x = np.array(x0, dtype=float)
    for sig in sigmas:
        eta = eta_scale * sig ** 2
        for _ in range(steps_per_level):
            eps_hat = eps_fn(x, sig)
            x = x + eta * (-eps_hat / sig) + math.sqrt(2 * eta) * rng.normal(0, 1, x.shape)
    return x


def make_eps_fn(net_u, net_c, gamma, y_pos, y_neg=None):
    """γ 语义：eps_hat = eps_end + gamma * (eps_pos - eps_end)。

    y_neg=None → eps_end = 无条件（eps_∅）：这就是 CFG。
    y_neg=k    → eps_end = 类别条件（负向词）：这把无条件那一端的锚换掉了。
    γ=1 即纯条件模型；γ>1 为外推。
    """
    def fn(X, sig):
        eps_pos = net_c.forward(f_cond(X, sig, y_pos))
        if y_neg is None:
            eps_end = net_u.forward(f_uncond(X, sig))
        else:
            eps_end = net_c.forward(f_cond(X, sig, y_neg))
        return eps_end + gamma * (eps_pos - eps_end)
    return fn


# ------------------------------------------------------------------------- 度量
def assign_modes(x):
    return ((x[:, None, :] - CENTERS[None]) ** 2).sum(-1).argmin(1)


def shell_exit_pct(x, tol=1.0):
    """离开数据薄壳的比例（与篇 2 实验 A 的空地判据一致：离数据环 > tol）。"""
    d = np.abs(np.linalg.norm(x, axis=1) - RADIUS)
    return round(100 * float((d > tol).mean()), 2), round(float(np.median(d)), 4)


def basin_stats(x):
    idx = assign_modes(x)
    counts = np.bincount(idx, minlength=MODES) / len(x)
    ent = float(-(counts[counts > 0] * np.log(counts[counts > 0])).sum() / math.log(MODES))
    return counts, round(ent, 4)


# ------------------------------------------------------------------- 实验 ① 方向验证
SIGMAS_EVAL = [0.05, 0.15, 0.35, 1.0, 3.0]
DIR_EDGES = [0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 5.0]


def exp_A(net_u, net_c):
    """恒等式实测对拍：ε_∅ − ε_y = σ · ∇log p_σ(y|x)。

    两个维度看：方向（余弦相似度）与幅度（实测/解析的投影比）。
    """
    rng = np.random.default_rng(SEED + 101)
    n = 12000
    x = uniform_disk(n, 5.0, rng)
    y = 0
    d_ring = np.abs(np.linalg.norm(x, axis=1) - RADIUS)
    bin_id = np.digitize(d_ring, DIR_EDGES) - 1
    out = {"identity": "eps_empty(x,sigma) - eps_y(x,sigma) = sigma * grad_x log p_sigma(y|x)",
           "target_mode": y, "measure": "空间均匀（半径 5 圆盘）", "by_sigma": {}}
    for sig in SIGMAS_EVAL:
        lhs = net_u.forward(f_uncond(x, sig)) - net_c.forward(f_cond(x, sig, y))
        analytic_rhs = sig * classifier_grad(x, sig, y)
        # 方向：两张量夹角的余弦
        num = (lhs * analytic_rhs).sum(1)
        den = np.linalg.norm(lhs, axis=1) * np.linalg.norm(analytic_rhs, axis=1) + 1e-12
        cos = num / den
        # 幅度：lhs 在 analytic_rhs 方向上的投影比（1.0 = 幅度也对）
        proj = num / ((analytic_rhs ** 2).sum(1) + 1e-30)
        rel = np.linalg.norm(lhs - analytic_rhs, axis=1) / \
            (np.linalg.norm(analytic_rhs, axis=1) + 1e-12)
        rows = []
        for b in range(len(DIR_EDGES) - 1):
            m = bin_id == b
            if not m.any():
                continue
            rows.append({
                "d_lo": DIR_EDGES[b], "d_hi": DIR_EDGES[b + 1],
                "space_share_pct": round(100 * float(m.mean()), 2),
                "median_cos": round(float(np.median(cos[m])), 4),
                "median_proj": round(float(np.median(proj[m])), 4),
                "median_rel_err": round(float(np.median(rel[m])), 4),
                "pct_rel_err_gt_1": round(100 * float((rel[m] > 1).mean()), 2),
            })
        far = d_ring > 1.0
        out["by_sigma"][str(sig)] = {
            "bins": rows,
            "median_cos_all": round(float(np.median(cos)), 5),
            "median_proj_all": round(float(np.median(proj)), 4),
            "median_rel_err_all": round(float(np.median(rel)), 4),
            "far_median_cos": round(float(np.median(cos[far])), 5),
            "far_median_proj": round(float(np.median(proj[far])), 4),
            "far_median_rel_err": round(float(np.median(rel[far])), 4),
            "near_median_cos": round(float(np.median(cos[~far])), 5),
            "near_median_proj": round(float(np.median(proj[~far])), 4),
            "near_median_rel_err": round(float(np.median(rel[~far])), 4),
            "far_pct_rel_err_gt_1": round(100 * float((rel[far] > 1).mean()), 2),
            "near_pct_rel_err_gt_1": round(100 * float((rel[~far] > 1).mean()), 2),
        }
    # 解析侧自检：真值之间的恒等式残差应为 0（证明推导没写错）
    sig = 0.35
    lhs_a = analytic_eps(x, sig, None) - analytic_eps(x, sig, y)
    rhs_a = sig * classifier_grad(x, sig, y)
    out["analytic_identity_max_abs_residual"] = float(np.abs(lhs_a - rhs_a).max())
    return out


# ------------------------------------------------------------------- 实验 ② γ 扫描
GAMMAS = [0.0, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 5.0, 8.0, 12.0]


def exp_B(net_u, net_c, n=1500, sigmas=None, steps_per_level=40):
    sigmas = sigmas if sigmas is not None else np.geomspace(SIGMA_MAX, SIGMA_MIN, LEVELS)
    out = {"gammas": GAMMAS, "n": n, "schedule": [float(s) for s in sigmas],
           "steps_per_level": steps_per_level, "target_mode": 0,
           "ref_within_std": SIGMA_PEAK, "shell_tol": 1.0, "rows": []}
    for g in GAMMAS:
        # 锚点噪声：与数据尺度无关的均匀圆盘（和篇 2 实验 B 同口径）
        rng = np.random.default_rng(SEED + 500 + int(g * 100))
        init = uniform_disk(n, 5.0, rng)
        fn = make_eps_fn(net_u, net_c, g, y_pos=0, y_neg=None)
        x = annealed_cfg(net_u, net_c, init, sigmas, steps_per_level, rng, fn)
        counts, ent = basin_stats(x)
        exit_pct, med_d = shell_exit_pct(x)
        idx = assign_modes(x)
        hit = (idx == 0) & (np.abs(np.linalg.norm(x, axis=1) - RADIUS) <= 1.0)
        within = float(np.linalg.norm(x[hit] - CENTERS[0], axis=1).std()) if hit.sum() > 5 else None
        out["rows"].append({
            "gamma": g,
            "target_hit_pct": round(100 * float((idx == 0).mean()), 2),
            "basin_entropy": ent,
            "basin_counts": [round(float(c), 4) for c in counts],
            "within_target_std": None if within is None else round(within, 4),
            "shell_exit_pct": exit_pct,
            "median_ring_dist": med_d,
        })
        print(f"    γ={g}: 命中 {out['rows'][-1]['target_hit_pct']}% "
              f"熵 {ent} 出壳 {exit_pct}%", flush=True)
    return out


# ------------------------------------------------------------------- 实验 ④ 负向推力
NEG_CASES = [("相邻锚（峰 1）", 1), ("对侧锚（峰 4）", 4)]


def exp_C(net_u, net_c, n=1500, sigmas=None, steps_per_level=40):
    sigmas = sigmas if sigmas is not None else np.geomspace(SIGMA_MAX, SIGMA_MIN, LEVELS)
    out = {"n": n, "target_mode": 0, "gammas": GAMMAS, "cases": []}
    for name, y_neg in NEG_CASES:
        rows = []
        for g in GAMMAS:
            rng = np.random.default_rng(SEED + 900 + 37 * y_neg + int(g * 100))
            init = uniform_disk(n, 5.0, rng)
            fn = make_eps_fn(net_u, net_c, g, y_pos=0, y_neg=y_neg)
            x = annealed_cfg(net_u, net_c, init, sigmas, steps_per_level, rng, fn)
            counts, ent = basin_stats(x)
            exit_pct, med_d = shell_exit_pct(x)
            idx = assign_modes(x)
            rows.append({
                "gamma": g,
                "basin_counts": [round(float(c), 4) for c in counts],
                "target_hit_pct": round(100 * float((idx == 0).mean()), 2),
                "neg_hit_pct": round(100 * float((idx == y_neg).mean()), 2),
                "third_peak_pct": round(100 * float((~np.isin(idx, [0, y_neg])).mean()), 2),
                "shell_exit_pct": exit_pct,
                "median_ring_dist": med_d,
                "basin_entropy": ent,
            })
            print(f"    [{name}] γ={g}: 目标 {rows[-1]['target_hit_pct']}% "
                  f"负向位 {rows[-1]['neg_hit_pct']}% 第三个峰 {rows[-1]['third_peak_pct']}% "
                  f"出壳 {exit_pct}%", flush=True)
        out["cases"].append({"name": name, "neg_mode": y_neg, "rows": rows})
    # 参照：不带负向词（= 常规 CFG，y_neg=None）同 γ 下的落点对照
    ref = []
    for g in GAMMAS:
        rng = np.random.default_rng(SEED + 7777 + int(g * 100))
        init = uniform_disk(n, 5.0, rng)
        fn = make_eps_fn(net_u, net_c, g, y_pos=0, y_neg=None)
        x = annealed_cfg(net_u, net_c, init, sigmas, steps_per_level, rng, fn)
        counts, ent = basin_stats(x)
        idx = assign_modes(x)
        exit_pct, med_d = shell_exit_pct(x)
        ref.append({
            "gamma": g, "target_hit_pct": round(100 * float((idx == 0).mean()), 2),
            "third_peak_pct": round(100 * float((idx != 0).mean()), 2),
            "shell_exit_pct": exit_pct, "basin_counts": [round(float(c), 4) for c in counts],
        })
    out["reference_no_negative"] = ref
    return out


def uniform_disk(n, radius, rng):
    r = radius * np.sqrt(rng.random(n))
    th = rng.random(n) * 2 * np.pi
    return np.stack([r * np.cos(th), r * np.sin(th)], 1)


# ---------------------------------------------------------------------------- 绘图
def plot_A(res, path):
    sigs = SIGMAS_EVAL
    colors = {0.05: RED, 0.15: ORANGE, 0.35: BLUE, 1.0: GREEN, 3.0: GREY}
    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.4), facecolor="#F8FAFC")
    idx = np.arange(len(sigs))
    w = 0.36
    near = [res["by_sigma"][str(s)]["near_median_cos"] for s in sigs]
    far = [res["by_sigma"][str(s)]["far_median_cos"] for s in sigs]
    axes[1].bar(idx - w / 2, near, w, color=BLUE, label="数据环附近（≤1.0）")
    axes[1].bar(idx + w / 2, far, w, color=RED, label="空地（>1.0）")
    axes[1].set_ylim(0.9, 1.008)
    axes[1].set_xticks(idx)
    axes[1].set_xticklabels([f"σ={s}" for s in sigs], fontsize=11)
    axes[1].set_ylabel("方向余弦相似度（越接近 1 越准）", fontsize=11.5)
    axes[1].set_title("方向：处处都对得上（无论 σ、无论远近）", fontsize=13.5, color=INK)
    axes[1].grid(alpha=.25, axis="y")
    axes[1].legend(fontsize=10, frameon=False, loc="upper center",
                   bbox_to_anchor=(0.5, -0.12), ncol=2)
    for i, (n, f) in enumerate(zip(near, far)):
        axes[1].text(i - w / 2, n + 0.002, f"{n:.4f}", ha="center", fontsize=8.5, color=INK)
        axes[1].text(i + w / 2, f + 0.002, f"{f:.4f}", ha="center", fontsize=8.5, color=INK)
    near_p = [res["by_sigma"][str(s)]["near_median_proj"] for s in sigs]
    far_p = [res["by_sigma"][str(s)]["far_median_proj"] for s in sigs]
    axes[0].bar(idx - w / 2, near_p, w, color=BLUE, label="数据环附近（≤1.0）")
    axes[0].bar(idx + w / 2, far_p, w, color=RED, label="空地（>1.0）")
    axes[0].axhline(1.0, ls="--", color=INK, lw=1.8, label="幅度正确 = 1.0")
    axes[0].set_ylim(0, 1.62)
    axes[0].set_xticks(idx)
    axes[0].set_xticklabels([f"σ={s}" for s in sigs], fontsize=11)
    axes[0].set_ylabel("实测 ÷ 解析（投影比）", fontsize=11.5)
    axes[0].set_title("幅度：差得整齐——网络把梯度整体缩放了", fontsize=13.5, color=INK)
    axes[0].grid(alpha=.25, axis="y")
    axes[0].legend(fontsize=10, frameon=False, loc="upper center",
                   bbox_to_anchor=(0.5, -0.12), ncol=2)
    for i, (n, f) in enumerate(zip(near_p, far_p)):
        axes[0].text(i - w / 2, n + 0.02, f"{n:.3f}", ha="center", fontsize=8.5, color=INK)
        axes[0].text(i + w / 2, f + 0.02, f"{f:.3f}", ha="center", fontsize=8.5, color=INK)
    fig.suptitle("实验 ①：\"CFG = 隐式分类器引导\"的数值对拍", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0.04, 1, 0.93])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


def plot_B(res, path):
    rows = res["rows"]
    gs = [r["gamma"] for r in rows]
    fig, axes = plt.subplots(1, 3, figsize=(16.8, 5.2), facecolor="#F8FAFC")
    axes[0].plot(gs, [r["target_hit_pct"] for r in rows], "-o", color=BLUE, lw=2.4, ms=7)
    axes[0].set_xscale("symlog", linthresh=1.0)
    axes[0].set_xlabel("γ（引导强度；γ=1 即纯条件模型）", fontsize=11.5)
    axes[0].set_ylabel("落进目标峰的比例（%）", fontsize=11.5)
    axes[0].set_ylim(-3, 105)
    axes[0].set_title("保真度：几乎白送（γ≈0.3 就到位）", fontsize=13, color=INK)
    axes[0].grid(alpha=.25)
    axes[0].axvline(1.0, ls=":", color=GREY, lw=1.5)
    axes[1].plot(gs, [r["basin_entropy"] for r in rows], "-s", color=ORANGE, lw=2.4, ms=7)
    axes[1].set_xscale("symlog", linthresh=1.0)
    axes[1].set_xlabel("γ", fontsize=11.5)
    axes[1].set_ylabel("终点在各峰上的归一化熵（1 = 铺满）", fontsize=11.5)
    axes[1].set_ylim(-0.03, 1.0)
    axes[1].set_title("多样性：γ 一大，样本全挤进同一个盆地", fontsize=13, color=INK)
    axes[1].grid(alpha=.25)
    axes[1].axvline(1.0, ls=":", color=GREY, lw=1.5, label="γ = 1")
    axes[1].legend(fontsize=10.5, frameon=False)
    axes[2].plot(gs, [r["shell_exit_pct"] for r in rows], "-^", color=RED, lw=2.4, ms=7)
    axes[2].set_xscale("symlog", linthresh=1.0)
    axes[2].set_xlabel("γ", fontsize=11.5)
    axes[2].set_ylabel("离开数据薄壳的样本比例（%）", fontsize=11.5)
    axes[2].set_title("代价：推过头，样本直接掉出数据薄壳", fontsize=13, color=INK)
    axes[2].grid(alpha=.25)
    axes[2].axvline(1.0, ls=":", color=GREY, lw=1.5, label="γ = 1")
    axes[2].legend(fontsize=10.5, frameon=False)
    fig.suptitle("实验 ②③：γ 是一根两头都有代价的旋钮（终点落在哪）", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


def plot_C(res, path):
    gs = res["gammas"]
    fig, axes = plt.subplots(1, 3, figsize=(16.8, 5.2), facecolor="#F8FAFC")
    names = [c["name"] for c in res["cases"]] + ["不带负向词（纯 CFG 参照）"]
    series = [c["rows"] for c in res["cases"]] + [res["reference_no_negative"]]
    colors = [PURPLE, ORANGE, BLUE]
    for rows, nm, col in zip(series, names, colors):
        axes[0].plot(gs, [r["target_hit_pct"] for r in rows], "-o", color=col, lw=2.2, ms=6, label=nm)
    axes[0].set_xscale("symlog", linthresh=1.0)
    axes[0].set_xlabel("γ", fontsize=11.5)
    axes[0].set_ylabel("落进目标峰（峰 0）的比例（%）", fontsize=11.5)
    axes[0].set_ylim(-3, 105)
    axes[0].set_title("换个锚之后，目标还守得住吗", fontsize=13, color=INK)
    axes[0].grid(alpha=.25)
    axes[0].legend(fontsize=9.5, frameon=False)
    for rows, nm, col in zip(series, names, colors):
        axes[1].plot(gs, [r["shell_exit_pct"] for r in rows], "-^", color=col, lw=2.2, ms=6, label=nm)
    axes[1].set_xscale("symlog", linthresh=1.0)
    axes[1].set_xlabel("γ", fontsize=11.5)
    axes[1].set_ylabel("离开数据薄壳的比例（%）", fontsize=11.5)
    axes[1].set_ylim(-3, 105)
    axes[1].set_title("换个锚之后，掉出薄壳的代价", fontsize=13, color=INK)
    axes[1].grid(alpha=.25)
    axes[1].legend(fontsize=9.5, frameon=False)
    for c, nm, col in zip(res["cases"], names[:2], [PURPLE, ORANGE]):
        bad = [100 - r["target_hit_pct"] - r["neg_hit_pct"] for r in c["rows"]]
        axes[2].plot(gs, bad, "-o", color=col, lw=2.2, ms=6, label=nm)
    ref_bad = [100 - r["target_hit_pct"] for r in res["reference_no_negative"]]
    axes[2].plot(gs, ref_bad, "-o", color=BLUE, lw=2.2, ms=6, label="不带负向词（纯 CFG 参照）")
    axes[2].set_xscale("symlog", linthresh=1.0)
    axes[2].set_xlabel("γ", fontsize=11.5)
    axes[2].set_ylabel("既不是目标、也不是锚的比例（%）", fontsize=11.5)
    axes[2].set_ylim(-3, 105)
    axes[2].set_title("\"不要 A\" 推出个 C：锚一换，落点就偏", fontsize=13, color=INK)
    axes[2].grid(alpha=.25)
    axes[2].legend(fontsize=9.5, frameon=False)
    fig.suptitle("实验 ④：负向词 = 把外推另一端的锚换掉", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


# --------------------------------------------------------------------------- main
def main(t0=None):
    t0 = t0 or time.time()
    nets_path = ROOT / "nets.npz"
    if nets_path.exists():
        net_u = MLP(SEED + 1, din=3)
        net_u.load(nets_path, "uncond")
        net_c = MLP(SEED + 2, din=2 + 1 + MODES)
        net_c.load(nets_path, "cond")
        losses_u, losses_c = [0.0], [0.0]
        print("载入 nets.npz，跳过训练", flush=True)
    else:
        print("训练无条件网络 …", flush=True)
        net_u, losses_u = train_uncond(SEED + 1)
        print(f"  完成（{time.time()-t0:.0f}s）终损 {np.mean(losses_u[-500:]):.4f}", flush=True)
        print("训练类别条件网络 …", flush=True)
        net_c, losses_c = train_cond(SEED + 2)
        print(f"  完成（{time.time()-t0:.0f}s）终损 {np.mean(losses_c[-500:]):.4f}", flush=True)
        np.savez_compressed(nets_path,
                            **{f"uncond_{k}": v for k, v in net_u.p.items()},
                            **{f"cond_{k}": v for k, v in net_c.p.items()})

    print("自检：解析恒等式（应 ~1e-16）…", flush=True)
    rng0 = np.random.default_rng(SEED + 55)
    x_chk = uniform_disk(200, 4.0, rng0)
    for sig in [0.05, 0.35, 1.0, 3.0]:
        lhs = analytic_eps(x_chk, sig, None) - analytic_eps(x_chk, sig, 0)
        rhs = sig * classifier_grad(x_chk, sig, 0)
        print(f"  σ={sig}: max|残差| = {np.abs(lhs - rhs).max():.3e}", flush=True)
    print("实验 ① 方向验证 …", flush=True)
    A = exp_A(net_u, net_c)
    print(f"  解析恒等式残差 {A['analytic_identity_max_abs_residual']:.2e}", flush=True)
    print("实验 ② γ 扫描 …", flush=True)
    B = exp_B(net_u, net_c)
    print("实验 ④ 负向推力 …", flush=True)
    C = exp_C(net_u, net_c)

    out = {}
    out["config"] = {
        "seed": SEED, "modes": MODES, "radius": RADIUS, "sigma_peak": SIGMA_PEAK,
        "weights": WEIGHTS.tolist(), "sigma_min": SIGMA_MIN, "sigma_max": SIGMA_MAX,
        "levels": LEVELS, "steps_uncond": STEPS_UNCOND, "steps_cond": STEPS_COND,
        "batch": BATCH, "hidden": HID,
        "model": "tiny numpy MLP (Adam): unconditional + class-conditional",
        "gamma_semantics": "eps_hat = eps_end + gamma*(eps_pos - eps_end); "
                           "gamma=1 -> pure conditional",
    }
    # 真数据参照（正文引用的两个常数，随结果一起落盘以便溯源）
    rng_ref = np.random.default_rng(SEED + 31337)
    x0_ref, _ = sample_data(200000, rng_ref)
    d_ref = np.abs(np.linalg.norm(x0_ref, axis=1) - RADIUS)
    out["config"]["reference_true_data"] = {
        "weight_entropy_normalized": round(-float((WEIGHTS * np.log(WEIGHTS)).sum()
                                                 / math.log(MODES)), 4),
        "shell_exit_pct": round(100 * float((d_ref > 1.0).mean()), 3),
        "median_ring_dist": round(float(np.median(d_ref)), 4),
    }
    out["final_train_loss"] = {"uncond": round(float(np.mean(losses_u[-500:])), 5),
                               "cond": round(float(np.mean(losses_c[-500:])), 5)}
    out["headline"] = {
        "A_identity_residual": A["analytic_identity_max_abs_residual"],
        "A_sigma0.35": {
            "near_median_cos": A["by_sigma"]["0.35"]["near_median_cos"],
            "far_median_cos": A["by_sigma"]["0.35"]["far_median_cos"],
            "near_median_proj": A["by_sigma"]["0.35"]["near_median_proj"],
            "far_median_proj": A["by_sigma"]["0.35"]["far_median_proj"],
        },
        "B_rows": B["rows"],
        "C_cases": C["cases"],
        "C_reference": C["reference_no_negative"],
    }
    out["exp_A"], out["exp_B"], out["exp_C"] = A, B, C
    out["runtime_sec"] = round(time.time() - t0, 1)
    (ROOT / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    plot_A(A, ROOT / "A-direction-check.png")
    plot_B(B, ROOT / "B-gamma-scan.png")
    plot_C(C, ROOT / "C-negative-push.png")
    print(f"saved results.json + 3 张图（{out['runtime_sec']}s）", flush=True)
    return out


def replot():
    t0 = time.time()
    res = json.loads((ROOT / "results.json").read_text())
    plot_A(res["exp_A"], ROOT / "A-direction-check.png")
    plot_B(res["exp_B"], ROOT / "B-gamma-scan.png")
    plot_C(res["exp_C"], ROOT / "C-negative-push.png")
    print(f"replotted 3 张图（{time.time()-t0:.0f}s）", flush=True)


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:
        replot()
    else:
        main()
