#!/usr/bin/env python3
"""解析侧审计（配合 run_experiment.py 的四块实验）。

1. **盆地面积 → 比例错的理论预测**：单级朗之万在有限步内换不了盆地时，
   粒子的最终分配 ≈ 出发分布在各盆地的质量份额（Uniform 圆盘 ≈ 面积份额），
   而不是模式的真实权重。用蒙特卡洛算面积份额，和实测 L1 对照。
2. **鞍点/峰顶密度比**：跨盆地的难易程度（越小的比值 = 越难翻越），
   给「为什么有限步内翻不过去」一个数字。
3. **步长稳定界**：分数场的 Lipschitz 常数（谱范数上界）→ Euler 稳定上限 η ≲ 2/L，
   与实验 B 里「飞出去」的 η 区段对照。
4. 与 results.json 交叉核对 headline 数字。

产物：math_audit.json
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import run_experiment as rx

ROOT = Path(__file__).resolve().parent
rng = np.random.default_rng(rx.SEED + 4242)


def basin_area_shares(m=400000, radius=5.0):
    """出发分布（半径 5 圆盘）里各 Voronoi 盆地的质量份额。"""
    pts = rx.uniform_disk(m, radius, rng)
    idx = rx.assign_modes(pts)
    counts = np.bincount(idx, minlength=rx.MODES) / m
    return counts


def saddle_ratio(sig):
    """沿环扫描 p_σ：鞍点处密度 / 峰顶处密度（σ 下的跨盆地难度）。"""
    ang = np.linspace(0, 2 * np.pi, 4000, endpoint=False)
    pts = np.stack([rx.RADIUS * np.cos(ang), rx.RADIUS * np.sin(ang)], 1)
    r, s2 = rx.gmm_resp(pts, sig)
    dens = np.exp(-((pts[:, None, :] - rx.CENTERS[None]) ** 2).sum(-1) / (2 * s2))
    p = (rx.WEIGHTS[None] * dens).sum(1)
    peak_idx = np.argsort(p)[-rx.MODES:]
    saddle_idx = np.argsort(p)[:rx.MODES]
    return float(p[saddle_idx].max() / p[peak_idx].min())


def score_lipschitz(sig, n_side=161):
    """网格上估计分数场 Jacobian 的最大谱范数 L；Euler 稳定要求 η ≲ 2/L。"""
    xs = np.linspace(-4.5, 4.5, n_side)
    gx, gy = np.meshgrid(xs, xs)
    pts = np.stack([gx.ravel(), gy.ravel()], 1)
    h = 1e-3
    L = 0.0
    for d in range(2):
        off = np.zeros(2)
        off[d] = h
        J = (rx.analytic_score(pts + off, sig) - rx.analytic_score(pts - off, sig)) / (2 * h)
        for k in range(len(pts)):
            M = np.outer(J[k], J[k])
            L = max(L, math.sqrt(float(np.linalg.eigvalsh(M)[-1])))
    return L


def main():
    res = json.loads((ROOT / "results.json").read_text())
    shares = basin_area_shares()
    area_l1 = float(np.abs(shares - rx.WEIGHTS).sum())

    sig_probe = rx.SIGMA_SINGLE
    L = score_lipschitz(sig_probe)
    eta_bound = 2.0 / L
    saddle = saddle_ratio(sig_probe)
    saddle_coarse = saddle_ratio(rx.SIGMA_MAX)

    B = res["exp_B"]
    eta_rows = B["eta_sweep"]
    flew = [r["eta"] for r in eta_rows if r["flew_pct"] > 5]
    stuck = [r["eta"] for r in eta_rows if r["median_move"] < 0.5]

    audit = {
        "note": "解析侧审计：盆地面积 / 鞍点比 / 步长稳定界；与 results.json 交叉核对",
        "basin": {
            "init": "半径 5 的均匀圆盘（不分模式）",
            "area_share": {f"peak_{i+1}": round(float(shares[i]), 4) for i in range(rx.MODES)},
            "true_weights": {f"peak_{i+1}": round(float(rx.WEIGHTS[i]), 4) for i in range(rx.MODES)},
            "area_share_L1_vs_true_weights": round(area_l1, 4),
            "measured_single_level_prop_L1": B["best_prop_l1"],
            "note": "单级朗之万实测的比例 L1 与「出发盆地面积 vs 真权重」的 L1 接近 → "
                    "有限步内换不了盆地的直接证据",
        },
        "saddle": {
            "sigma_single": sig_probe,
            "saddle_over_peak_density_ratio": f"{saddle:.3e}",
            "sigma_max": rx.SIGMA_MAX,
            "saddle_over_peak_density_ratio_at_sigma_max": f"{saddle_coarse:.3e}",
            "note": "单级 σ 下鞍点密度比峰顶低若干数量级 → 翻盆地几乎不可能；"
                    "大 σ 下这个比值接近 1 → 粒子可以自由重排（退火能修比例的机制）",
        },
        "step_size_bound": {
            "sigma": sig_probe,
            "score_lipschitz_max": round(L, 2),
            "euler_stable_eta_upper": round(eta_bound, 4),
            "empirical_flew_etas": flew,
            "empirical_stuck_etas": stuck,
            "note": "Euler 离散稳定要求 η ≲ 2/L；实测飞出去的 η 与之对照",
        },
        "cross_check": {
            "final_train_loss": res["final_train_loss"],
            "A_sigma0.05": res["exp_A"]["by_sigma"]["0.05"],
            "B_best": {"eta": B["best_eta"], "prop_l1": B["best_prop_l1"],
                       "median_move": B["best_median_move"]},
            "C_1000": res["headline"]["C_at_1000_calls"],
            "D_shell": res["exp_D"]["shell"],
            "runtime_sec": res["runtime_sec"],
        },
    }
    (ROOT / "math_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(json.dumps({
        "area_L1": round(area_l1, 4),
        "measured_prop_L1": B["best_prop_l1"],
        "saddle_ratio": f"{saddle:.3e}",
        "eta_bound": round(eta_bound, 4),
        "flew_etas": flew,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
