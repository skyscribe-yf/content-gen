#!/usr/bin/env python3
"""玩具扩散实验：数据分布完全已知，只改采样步数，看图像怎么坏掉。

为什么不用神经网络：真实模型带训练误差，会把「步数」这个变量污染掉。
本实验数据是 8 个高斯峰的混合，VP 扩散下加噪后的分布仍是混合高斯，
所以 eps(x,t) 有闭式解 —— 模型零误差，唯一变量就是步数。
结论因此是下界性质的：真实模型只会比这里更早崩，不会更晚。

指标定义：
  能量距离（energy distance）：样本 vs 真分布的两样本检验统计量，越小越像。
  模式覆盖率：8 个峰里拿到 >= 1/(4*8) 质量的比例（1 步时全塌到中心，覆盖=0）。
  1 步解析解：DDIM 一步的输出恰好等于 E[x0|x_T]，即「所有可能答案的加权平均」。

产物（正文数字必须与此一致）：
  01-step-samples.png   各步数样本散点 + 真实分布
  02-error-coverage.png    能量距离 + 模式覆盖率随步数变化
  analytic_1step.png      1 步 = 条件均值的解析演示
  results.json            全部量化数字
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = ["Noto Sans CJK TC", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent

SEED = 20260919
T = 1000                    # 训练期离散步数（连续时间的离散化基准）
MODES = 8
RADIUS = 3.0
SIGMA = 0.35
AB_MIN = 0.01               # cosine 调度在 t=T 处 alpha_bar 归零会让 1/sqrt(ab) 爆炸，压到 0.01
N_EVAL = 3000
STEP_GRID = [100, 50, 20, 10, 5, 2, 1]

BLUE, ORANGE, YELLOW, INK, GREY, GREEN = "#0F4C81", "#E76F51", "#F6BD60", "#17324D", "#5B7186", "#2A9D8F"

_ang = np.arange(MODES) * 2 * np.pi / MODES
CENTERS = np.stack([RADIUS * np.cos(_ang), RADIUS * np.sin(_ang)], axis=1)


def _cosine_ab() -> np.ndarray:
    g = np.arange(1, T + 1) / T
    f = np.cos((g + 0.008) / 1.008 * math.pi / 2) ** 2
    ab = f / np.cos(0.008 / 1.008 * math.pi / 2) ** 2
    ab = np.clip(ab, AB_MIN, 1.0)
    return np.concatenate([[1.0], ab])          # AB_IDX[t], t = 0..T；AB_IDX[T] = AB_MIN


AB_IDX = _cosine_ab()


def sample_true(n, rng):
    return CENTERS[rng.integers(0, MODES, size=n)] + rng.normal(0, SIGMA, size=(n, 2))


def responsibilities(x, ab):
    """p(mode | x_t)。x_t | mode k ~ N(sqrt(ab)*mu_k, s2 I)。"""
    s2 = ab * SIGMA ** 2 + (1 - ab)
    mu = math.sqrt(ab) * CENTERS
    d2 = ((x[:, None, :] - mu[None]) ** 2).sum(-1)
    logit = -d2 / (2 * s2)
    logit -= logit.max(1, keepdims=True)
    w = np.exp(logit)
    return w / w.sum(1, keepdims=True), s2


def eps_exact(x, t_idx):
    """闭式 eps 预测（等价于精确 score）。t_idx: 标量时间下标。"""
    ab = AB_IDX[t_idx]
    r, s2 = responsibilities(x, ab)
    m = (r[:, :, None] * CENTERS[None]).sum(1)          # 加权峰心
    score = (math.sqrt(ab) * m - x) / s2
    return -math.sqrt(1 - ab) * score


def x0_posterior_mean(x, t_idx):
    """E[x0 | x_t] 的闭式解：各峰后验均值的责任加权。"""
    ab = AB_IDX[t_idx]
    r, _ = responsibilities(x, ab)
    prec = 1 / SIGMA ** 2 + ab / (1 - ab)
    v = 1 / prec
    m_k = v * (CENTERS[None] / SIGMA ** 2 + math.sqrt(ab) * x[:, None] / (1 - ab))
    return (r[:, :, None] * m_k).sum(1)


def ddim_flow(x, num_steps):
    """确定性 DDIM（eta=0，即 probability-flow ODE 的离散化）。步数 = 网络调用次数。"""
    ts = np.unique(np.round(np.linspace(T, 1, num_steps)).astype(int))[::-1]  # 必须降序：T → 1
    x = x.copy()
    for i, t in enumerate(ts):
        ab = AB_IDX[t]
        eps = eps_exact(x, t)
        x0_hat = (x - math.sqrt(1 - ab) * eps) / math.sqrt(ab)
        if i == len(ts) - 1:
            return x0_hat
        abn = AB_IDX[ts[i + 1]]
        x = math.sqrt(abn) * x0_hat + math.sqrt(1 - abn) * eps


def energy_distance(a, b, rng):
    """两样本能量距离：2*mean|A-B| - mean|A-A'| - mean|B-B'|（取子样本控内存）。"""
    s = 1200
    A, B = a[:s], b[:s]
    def pdist(P, Q):
        return np.sqrt(((P[:, None, :] - Q[None]) ** 2).sum(-1) + 1e-12)
    return float(2 * pdist(A, B).mean() - pdist(A, A).mean() - pdist(B, B).mean())


def coverage(pts):
    d2 = ((pts[:, None, :] - CENTERS[None, :, :]) ** 2).sum(-1)
    dist = np.sqrt(d2.min(1))
    lab = d2.argmin(1)
    on_mode = dist < 2 * SIGMA          # 只有落在某个峰附近才算「画到了真图上」
    if on_mode.sum() == 0:
        return 0.0, 0.0, [0.0] * MODES
    counts = np.bincount(lab[on_mode], minlength=MODES) / len(pts)
    cov = float((counts > 1.0 / (4 * MODES)).sum() / MODES)
    return cov, float(on_mode.mean()), [round(float(c), 4) for c in counts]


def main():
    rng = np.random.default_rng(SEED)
    x_true = sample_true(N_EVAL, rng)
    rows, panel = {}, []
    for n in STEP_GRID:
        x_T = rng.normal(0, 1, size=(N_EVAL, 2))
        s = ddim_flow(x_T, n)
        cov, on_mode, counts = coverage(s)
        ed = energy_distance(s, x_true, rng)
        rows[n] = {"energy_distance": round(ed, 4), "coverage": round(cov, 3),
                   "on_mode_ratio": round(on_mode, 3), "mode_counts": counts,
                   "radius_mean": round(float(np.linalg.norm(s, axis=1).mean()), 3)}
        panel.append((n, s))
        print(f"steps={n:4d}  energyDist={ed:7.4f}  coverage={cov:.3f}  onMode={on_mode:.3f} "
              f"meanRadius={rows[n]['radius_mean']:.3f}", flush=True)

    # 1 步的解析对照：起点 x_T 的条件均值（模型的最优 1 步猜测）
    x_T = rng.normal(0, 1, size=(N_EVAL, 2))
    one_step_mean = x0_posterior_mean(x_T, T)
    cov1, on1, _ = coverage(one_step_mean)
    rows["analytic_1step_E[x0|xT]"] = {
        "energy_distance": round(energy_distance(one_step_mean, x_true, rng), 4),
        "coverage": round(cov1, 3), "on_mode_ratio": round(on1, 3),
        "radius_mean": round(float(np.linalg.norm(one_step_mean, axis=1).mean()), 3),
    }
    print(f"解析 1 步（条件均值）  energyDist={rows['analytic_1step_E[x0|xT]']['energy_distance']:.4f}  "
          f"onMode={on1:.3f}  meanRadius={rows['analytic_1step_E[x0|xT]']['radius_mean']:.3f}", flush=True)

    plot_points(x_true, panel, one_step_mean, ROOT / "01-step-samples.png")
    plot_curve(rows, ROOT / "02-error-coverage.png")
    plot_analytic(one_step_mean, x_true, ROOT / "analytic_1step.png")
    (ROOT / "results.json").write_text(json.dumps({
        "config": {"modes": MODES, "radius": RADIUS, "sigma": SIGMA, "T": T,
                   "alpha_bar_min": AB_MIN, "n_eval": N_EVAL, "seed": SEED,
                   "schedule": "cosine", "sampler": "deterministic DDIM (probability-flow ODE)",
                   "model": "exact analytic score (zero training error)"},
        "results": {str(k): v for k, v in rows.items()}}, ensure_ascii=False, indent=2))
    print("saved.")


def plot_points(x_true, panel, one_step_mean, path):
    n_panels = len(panel) + 2
    ncol = 3
    nrow = math.ceil(n_panels / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.6 * ncol, 3.6 * nrow), facecolor="#F8FAFC")
    axes = np.asarray(axes).ravel()
    axes[0].scatter(x_true[:, 0], x_true[:, 1], s=3, color=INK, alpha=.5)
    axes[0].set_title("真实分布（8 个峰）", fontsize=12, color=INK)
    for ax, (n, s) in zip(axes[1:], panel):
        ax.scatter(s[:, 0], s[:, 1], s=3, color=BLUE, alpha=.5)
        ax.set_title(f"采样 {n} 步", fontsize=12, color=INK)
    axes[len(panel) + 1].scatter(one_step_mean[:, 0], one_step_mean[:, 1], s=3, color=ORANGE, alpha=.5)
    axes[len(panel) + 1].set_title("1 步解析解 = 条件均值", fontsize=12, color=INK)
    for ax in axes:
        ax.set_xlim(-5.5, 5.5); ax.set_ylim(-5.5, 5.5)
        ax.set_aspect("equal"); ax.grid(alpha=.25); ax.tick_params(labelsize=8)
    for j in range(n_panels, len(axes)):
        axes[j].axis("off")
    fig.suptitle("模型零误差，只改采样步数", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


def plot_curve(rows, path):
    steps = sorted(STEP_GRID)
    ed = [rows[s]["energy_distance"] for s in steps]
    om = [rows[s]["on_mode_ratio"] for s in steps]
    fig, ax1 = plt.subplots(figsize=(11, 6.4), facecolor="#F8FAFC")
    ax1.plot(steps, ed, "-o", color=BLUE, lw=2.4, ms=9)
    ax1.set_ylabel("与真分布的能量距离（越小越像）", fontsize=13, color=BLUE)
    ax1.tick_params(axis="y", labelcolor=BLUE, labelsize=11)
    ax1.set_ylim(0, max(ed) * 1.22)
    ax2 = ax1.twinx()
    ax2.plot(steps, om, "-s", color=ORANGE, lw=2.4, ms=9)
    ax2.set_ylabel("落在真图流形上的样本比例", fontsize=13, color=ORANGE)
    ax2.tick_params(axis="y", labelcolor=ORANGE, labelsize=11)
    ax2.set_ylim(0, 1.18)
    ax1.set_xscale("log", base=2)
    ax1.set_xticks(steps)
    ax1.set_xticklabels([f"{s}" for s in steps], fontsize=12)
    ax1.set_xlabel("采样步数（对数轴，越右越慢）", fontsize=13)
    ax1.grid(alpha=.25)
    label_bg = dict(boxstyle="round,pad=0.18", fc="#F8FAFC", ec="none", alpha=.92)
    for s, e in zip(steps, ed):
        ax1.annotate(f"{e:.3f}".rstrip("0").rstrip("."), (s, e), textcoords="offset points",
                     xytext=(0, 13), ha="center", fontsize=10, color=BLUE, bbox=label_bg)
    for s, c in zip(steps, om):
        dy = 14 if c < 0.15 else -20
        ax2.annotate(f"{c:.2f}", (s, c), textcoords="offset points",
                     xytext=(0, dy), ha="center", fontsize=10, color=ORANGE, bbox=label_bg)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


def plot_analytic(one_step_mean, x_true, path):
    fig, ax = plt.subplots(figsize=(9, 8), facecolor="#F8FAFC")
    ax.scatter(x_true[:, 0], x_true[:, 1], s=6, color=INK, alpha=.35, label="真实分布（8 个峰）")
    ax.scatter(one_step_mean[:, 0], one_step_mean[:, 1], s=6, color=ORANGE, alpha=.6,
               label="1 步最优解 E[x0|纯噪声]（各峰的加权平均）")
    ax.add_patch(plt.Circle((0, 0), float(np.linalg.norm(one_step_mean, axis=1).mean()),
                            fill=False, ls="--", color=GREY, lw=1.4))
    ax.set_aspect("equal"); ax.grid(alpha=.25)
    ax.legend(fontsize=11, loc="upper right")
    ax.set_title("一步走完全程，模型只能给出「平均脸」", fontsize=15, color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


if __name__ == "__main__":
    main()
