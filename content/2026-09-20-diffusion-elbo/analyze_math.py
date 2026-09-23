#!/usr/bin/env python3
"""解析侧核验（配合 run_experiment.py 的三目标对照）。

A. 各目标的可解释比例 R²(t)：E[目标|x_t] 的方差 / 目标总方差——
   「这个目标在当前噪声段，有多少是 x_t 里真能学到的」。闭式场 + 大样本估计。
B. 各目标的不可约方差下限（沿训练期 t 分布）：0.5*E_t[Var(目标|x_t)]，
   与训练损失对照——「损失里有多少是学不动的部分」。
C. 重绘 02-target-alignment.png（三面板：R² 理论 / 实测相对误差 / 统一到 x₀ 的误差）。

产物：math_audit.json、02-target-alignment.png（覆盖 run_experiment.py 的同名版本）
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import run_experiment as rx

plt.rcParams["font.family"] = ["Noto Sans CJK TC", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
ROOT = Path(__file__).resolve().parent
rng = np.random.default_rng(rx.SEED + 99)
BLUE, ORANGE, YELLOW, INK, GREY, GREEN = rx.BLUE, rx.ORANGE, rx.YELLOW, rx.INK, rx.GREY, rx.GREEN
COLORS = {"x0": ORANGE, "eps": BLUE, "score": GREEN}
LABELS = {"x0": "学 x₀（预测原图）", "eps": "学 ε（预测噪声）", "score": "学分数 ∇log p"}


def fields_vec(x, ab):
    """逐样本解析场：(E[x0|x_t], E[eps|x_t], ∇log p_t(x_t))，ab 为 (n,)。"""
    ab = np.asarray(ab, dtype=float).reshape(-1)
    x = np.asarray(x, dtype=float).reshape(-1, 2)
    n = ab.shape[0]
    root_ab = np.sqrt(ab).reshape(n, 1, 1)                    # (n,1,1)
    s2 = (ab * rx.SIGMA ** 2 + (1 - ab)).reshape(n, 1)        # (n,1)
    mu = root_ab * rx.CENTERS.reshape(1, -1, 2)               # (n,K,2)
    d2 = ((x.reshape(n, 1, 2) - mu) ** 2).sum(-1)             # (n,K)
    logit = -d2 / (2 * s2)
    logit -= logit.max(1, keepdims=True)
    w = np.exp(logit)
    r = w / w.sum(1, keepdims=True)                           # (n,K)
    mbar = (r[:, :, None] * rx.CENTERS.reshape(1, -1, 2)).sum(1)      # (n,2)
    score = (root_ab.reshape(n, 1) * mbar - x) / s2           # (n,2)
    eps = -np.sqrt(1 - ab).reshape(n, 1) * score
    v = (1.0 / (1 / rx.SIGMA ** 2 + ab / (1 - ab))).reshape(n, 1, 1)
    m_k = v * (rx.CENTERS.reshape(1, -1, 2) / rx.SIGMA ** 2
               + root_ab * x.reshape(n, 1, 2) / (1 - ab).reshape(n, 1, 1))
    x0_mean = (r[:, :, None] * m_k).sum(1)                    # (n,2)
    return x0_mean, eps, score


def sample_at(ab, n):
    x0 = rx.sample_true(n, rng)
    eps = rng.normal(0, 1, size=(n, 2))
    x_t = math.sqrt(ab) * x0 + math.sqrt(1 - ab) * eps
    return x0, eps, x_t


def r2_table(n=20000):
    out = {}
    for ab in rx.AB_EVAL:
        x0, eps, x_t = sample_at(ab, n)
        x0s, epss, scores = fields_vec(x_t, np.full((n, 1), ab))
        tgt = {"x0": x0, "eps": eps, "score": -eps / math.sqrt(1 - ab)}
        fld = {"x0": x0s, "eps": epss, "score": scores}
        row = {}
        for k in tgt:
            resid = float(((tgt[k] - fld[k]) ** 2).sum(1).mean())
            var = float(((tgt[k] - tgt[k].mean(0)) ** 2).sum(1).mean())
            row[k] = {
                "R2_explainable": round(1 - resid / var, 4),
                "field_rms": round(math.sqrt(var - resid), 4),
                "target_rms": round(math.sqrt(var), 4),
                "irreducible_rms": round(math.sqrt(resid), 4),
            }
        out[str(ab)] = row
    return out


def loss_floors(n=100000):
    """沿训练期 t 分布（均匀 U{1..T}）的不可约方差下限，与前缀 0.5 系数对齐训练损失。"""
    t_idx = rng.integers(1, rx.T + 1, size=n)
    ab = rx.AB_IDX[t_idx]
    x0 = rx.sample_true(n, rng)
    eps = rng.normal(0, 1, size=(n, 2))
    x_t = np.sqrt(ab)[:, None] * x0 + np.sqrt(1 - ab)[:, None] * eps
    x0s, epss, scores = fields_vec(x_t, ab[:, None])
    tgt = {"x0": x0, "eps": eps, "score": -eps / np.sqrt(1 - ab)[:, None]}
    fld = {"x0": x0s, "eps": epss, "score": scores}
    return {k: round(0.5 * float(((tgt[k] - fld[k]) ** 2).sum(1).mean()), 4) for k in tgt}


def plot_alignment(res, r2, path):
    rows = [res["by_alpha"][str(ab)] for ab in rx.AB_EVAL]
    xs = [r["t_over_T"] for r in rows]
    fig, axes = plt.subplots(1, 3, figsize=(16.8, 5.2), facecolor="#F8FAFC")
    for k in ("x0", "eps", "score"):
        lbl1 = LABELS[k] + ("（与 ε 完全重合）" if k == "score" else "")
        axes[0].plot(xs, [r2[str(ab)][k]["R2_explainable"] for ab in rx.AB_EVAL], "-o",
                     color=COLORS[k], lw=2.2, ms=6, label=lbl1)
        axes[1].plot(xs, [r[k]["rel_err"] for r in rows], "-o", color=COLORS[k], lw=2.2, ms=6,
                     label=LABELS[k])
        axes[2].plot(xs, [r[k]["x0_space_rmse"] for r in rows], "-o", color=COLORS[k], lw=2.2,
                     ms=6, label=LABELS[k])
    axes[0].set_ylim(-0.03, 1.05)
    axes[0].set_ylabel("可解释比例 R²（理论：x_t 里真正学得到的部分）", fontsize=11.5)
    axes[1].set_ylabel("实测相对误差（对各自的回归目标）", fontsize=11.5)
    axes[2].set_yscale("log")
    axes[2].set_ylabel("换算回 x₀ 的估计误差（RMSE，对数轴）", fontsize=11.5)
    for ax in axes:
        ax.set_xlabel("噪声水平 t/T（越右越噪）", fontsize=11.5)
        ax.grid(alpha=.25)
    axes[0].annotate("干净端：x₀ 几乎全可学\nε 只剩个零头", xy=(0.06, 0.5), fontsize=10.5,
                     color=GREY, ha="left")
    axes[0].annotate("噪声端：两条曲线\n换了个位置", xy=(0.72, 0.35), fontsize=10.5, color=GREY)
    axes[2].annotate("噪声端：ε 的残余误差\n被换算放大 10 倍", xy=(0.72, 1.0), fontsize=10.5,
                     color=GREY)
    axes[2].annotate("干净端：ε 换算回来\n反而更准", xy=(0.056, 0.02), fontsize=10.5, color=GREY)
    fig.suptitle("同一次训练，只换回归目标：数学等价，难度分配不等价", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


if __name__ == "__main__":
    res = json.loads((ROOT / "results.json").read_text())
    r2 = r2_table()
    floors = loss_floors()
    achieved = res["final_train_loss"]
    out = {
        "note": "R² = 1 - E||目标 - E[目标|x_t]||² / Var(目标)；损失下限 = 0.5 * E_t[Var(目标|x_t)]",
        "r2_by_alpha": r2,
        "loss_floor_vs_achieved": {k: {"floor": floors[k], "achieved": achieved[k],
                                       "floor_share_pct": round(100 * floors[k] / achieved[k], 1)}
                                   for k in floors},
        "headline": {
            "R2_clean_end": {k: r2[str(rx.AB_EVAL[0])][k]["R2_explainable"] for k in floors},
            "R2_noisy_end": {k: r2[str(rx.AB_EVAL[-1])][k]["R2_explainable"] for k in floors},
            "rel_err_eps_clean_to_noisy": [res["by_alpha"][str(rx.AB_EVAL[0])]["eps"]["rel_err"],
                                           res["by_alpha"][str(rx.AB_EVAL[-1])]["eps"]["rel_err"]],
            "rel_err_x0_clean_to_noisy": [res["by_alpha"][str(rx.AB_EVAL[0])]["x0"]["rel_err"],
                                          res["by_alpha"][str(rx.AB_EVAL[-1])]["x0"]["rel_err"]],
            "x0_space_rmse_clean": {k: res["by_alpha"][str(rx.AB_EVAL[0])][k]["x0_space_rmse"]
                                    for k in floors},
            "x0_space_rmse_noisy": {k: res["by_alpha"][str(rx.AB_EVAL[-1])][k]["x0_space_rmse"]
                                    for k in floors},
            "identity_check": res["identity_check"],
        },
    }
    (ROOT / "math_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    plot_alignment(res, r2, ROOT / "02-target-alignment.png")
    print(json.dumps(out["headline"], ensure_ascii=False, indent=2))
    print(json.dumps(out["loss_floor_vs_achieved"], ensure_ascii=False, indent=2))
    print("saved 02-target-alignment.png + math_audit.json")
