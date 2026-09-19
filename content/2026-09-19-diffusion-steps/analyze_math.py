#!/usr/bin/env python3
"""补数学深度用的推导核验：正文新增的每一个数字都必须在这里跑实。

A. DDIM 的收敛阶：以 N=4000 的解为「精确 ODE 解」，测误差随步数 N 的幂律斜率。
   （对同一批 x_T 起点做配对比较，把统计噪声从离散误差里剥掉。）
B. 1 步最优解为什么不是原点：cosine 末端 alpha_bar 被压到 AB_MIN，残留信号让
   后验权重不均匀，条件均值被拉向与残影匹配的那个峰。
C. 全方差分解 Var(x0) = E[Var(x0|x_T)] + Var(E[x0|x_T])：一步映射只能拿到
   「组间」那一项，「组内」（该画哪个峰）那一项被永久丢掉。
D. x0_hat 的误差放大倍率 1/sqrt(SNR)，SNR = alpha_bar/(1-alpha_bar)。
E. 采样器走过的 log-SNR 区间，以及 N 步走完全程时每步跨多少 nats（= SNR 每步变 e^Δλ 倍）。
F. 「该画哪个峰」的比特账：8 峰等权有 3 bit，纯噪声 x_T 里还剩几 bit（峰编号与 x_T 的互信息）。

产物：math_audit.json（正文数字须与此一致）、05-convergence-order.png
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
BLUE, ORANGE, INK, GREY, GREEN = rx.BLUE, rx.ORANGE, rx.INK, rx.GREY, rx.GREEN

ROOT = Path(__file__).resolve().parent
rng = np.random.default_rng(rx.SEED)
out: dict = {"seed": rx.SEED, "T": rx.T, "modes": rx.MODES, "radius": rx.RADIUS,
             "sigma": rx.SIGMA, "alpha_bar_min": rx.AB_MIN}


# ---------------------------------------------------------------- A. 收敛阶
def q_sample(x0, t_idx, noise):
    """前向加噪：x_t = sqrt(ab) x0 + sqrt(1-ab) eps。"""
    ab = rx.AB_IDX[t_idx]
    return math.sqrt(ab) * x0 + math.sqrt(1 - ab) * noise


def order_experiment() -> dict:
    n_start = 1500
    x0_seed = rx.sample_true(n_start, rng)
    noise = rng.normal(0, 1, size=(n_start, 2))
    starts = q_sample(x0_seed, rx.T, noise)          # 同一批 x_T 起点

    ref = rx.ddim_flow(starts, 4000)                 # 视为精确 ODE 解
    grid = [400, 200, 100, 50, 25, 20, 10, 5, 4, 2]
    errs = {}
    for n in grid:
        got = rx.ddim_flow(starts, n)
        errs[n] = float(np.sqrt(((got - ref) ** 2).sum(1).mean()))   # RMS 位移

    ns = np.array(sorted(grid), dtype=float)
    es = np.array([errs[int(n)] for n in ns])
    slope, icpt = np.polyfit(np.log(ns), np.log(es), 1)
    band = (ns >= 10) & (ns <= 100)        # n*err 平坦的那段，才是渐近区
    slope_band = float(np.polyfit(np.log(ns[band]), np.log(es[band]), 1)[0])
    c_ref = float(np.median([n * errs[n] for n in (10, 20, 25, 50)]))   # 1/N 的系数
    pred = {n: c_ref / n for n in grid}
    pred50_10 = errs[50] / errs[10]
    return {
        "reference": "N=4000 的 DDIM 解当作精确 probability-flow ODE 解",
        "rms_error_by_steps": {str(k): round(v, 6) for k, v in errs.items()},
        "n_times_err": {str(n): round(n * errs[n], 4) for n in grid},
        "err_over_sigma_by_steps": {str(n): round(errs[n] / rx.SIGMA, 3) for n in grid},
        "deviation_from_one_over_N": {str(n): round(errs[n] / pred[n], 3) for n in grid},
        "one_over_N_coefficient": round(c_ref, 3),
        "loglog_slope": round(float(slope), 3),
        "loglog_slope_band_10_100": round(slope_band, 3),
        "implied_order": f"误差 ~ N^({round(float(slope),2)})",
        "error_ratio_10_over_50": round(float(pred50_10), 3),
        "one_over_N_prediction": 5.0,
        "data_scale_radius": rx.RADIUS,
        "mode_width_sigma": rx.SIGMA,
        "rms_at_10_relative_to_radius": round(errs[10] / rx.RADIUS, 5),
        "rms_at_50_relative_to_radius": round(errs[50] / rx.RADIUS, 5),
        "rms_at_2_relative_to_radius": round(errs[2] / rx.RADIUS, 3),
    }


# ------------------------------------------------- B/C. 1 步最优解的结构
def one_step_structure() -> dict:
    n = 6000
    x0_true = rx.sample_true(n, rng)
    noise = rng.normal(0, 1, size=(n, 2))
    x_T = q_sample(x0_true, rx.T, noise)

    ab = rx.AB_IDX[rx.T]
    r, s2 = rx.responsibilities(x_T, ab)
    prec = 1 / rx.SIGMA ** 2 + ab / (1 - ab)
    v = 1 / prec
    per_mode_mean = v * (rx.CENTERS[None] / rx.SIGMA ** 2
                         + math.sqrt(ab) * x_T[:, None] / (1 - ab))       # (n,K,2)
    mean = (r[:, :, None] * per_mode_mean).sum(1)                          # E[x0|x_T]
    # 混合物后验二阶矩：E[x0 x0^T | x_T] 的对角和
    second = (r * (((per_mode_mean - mean[:, None, :]) ** 2).sum(-1) + 2 * v)).sum(1)
    post_var = second                                          # 混合物方差恒等式：已是组内项

    total_var = float(((x0_true - x0_true.mean(0)) ** 2).sum(1).mean())
    between = float(((mean - mean.mean(0)) ** 2).sum(1).mean())
    within = float(post_var.mean())

    radius = np.linalg.norm(mean, axis=1)

    # 「该画哪个峰」这 3 bit，在纯噪声 x_T 里还剩多少？
    pk = r.mean(0)                                        # 峰的先验（实测，接近 1/8）
    h_prior = float(-(pk * np.log(pk)).sum() / math.log(2))
    h_cond = float(-(r * np.log(np.clip(r, 1e-12, None))).sum(1).mean() / math.log(2))
    return {
        "sum_of_mode_centers_norm": round(float(np.linalg.norm(rx.CENTERS.sum(0))), 9),
        "uniform_weight_mean_norm": round(float(np.linalg.norm(r.mean(0) @ rx.CENTERS)), 6),
        "alpha_bar_at_T": ab,
        "residual_signal_sqrt_alpha_bar": round(math.sqrt(ab), 4),
        "responsibility_max_avg": round(float(r.max(1).mean()), 4),
        "responsibility_uniform_baseline": round(1 / rx.MODES, 4),
        "mean_output_radius": round(float(radius.mean()), 4),
        "measured_1step_radius_from_results": None,
        "mode_bits": {
            "prior_H_mode_bits": round(h_prior, 3),
            "conditional_H_mode_given_xT_bits": round(h_cond, 3),
            "I_mode_xT_bits": round(h_prior - h_cond, 3),
            "surviving_pct": round(100 * (h_prior - h_cond) / h_prior, 2),
        },
        "law_total_variance": {
            "total_Var_x0": round(total_var, 4),
            "between_Var_E_x0_given_xT": round(between, 4),
            "within_E_Var_x0_given_xT": round(within, 4),
            "sum_check": round(between + within, 4),
            "between_share_pct": round(100 * between / total_var, 2),
            "within_share_pct": round(100 * within / total_var, 2),
        },
    }


# ------------------------------------------------------------- D. 放大倍率
def amplification() -> dict:
    rows = {}
    for name, ab in [("t=T (纯噪声端)", rx.AB_MIN), ("alpha_bar=0.5", 0.5),
                     ("alpha_bar=0.9", 0.9), ("alpha_bar=0.99", 0.99)]:
        snr = ab / (1 - ab)
        rows[name] = {"alpha_bar": ab, "SNR": round(snr, 4),
                      "eps_error_amplified_by": round(1 / math.sqrt(snr), 3)}
    return rows


def energy_floor() -> dict:
    """「完全采对」时能量距离读数是多少？真分布独立抽两批互比，多 seed 看波动。"""
    vals = []
    for s in range(8):
        g = np.random.default_rng(1000 + s)
        a = rx.sample_true(rx.N_EVAL, g)
        b = rx.sample_true(rx.N_EVAL, g)
        vals.append(rx.energy_distance(a, b, g))
    return {"n_samples_each_side": rx.N_EVAL,
            "mean": round(float(np.mean(vals)), 5),
            "std": round(float(np.std(vals)), 5),
            "min": round(float(np.min(vals)), 5),
            "max": round(float(np.max(vals)), 5)}


def logsnr_span() -> dict:
    ab = np.clip(rx.AB_IDX[1:], 1e-9, 1 - 1e-9)          # 采样器走过的区间：t = 1..T
    lam = np.log(ab / (1 - ab))
    lo, hi = float(lam.min()), float(lam.max())          # hi 在 t=1（干净端），lo 在 t=T
    span = hi - lo
    return {"lambda_clean_end": round(hi, 2),
            "lambda_noise_end": round(lo, 2),
            "span": round(span, 2),
            "per_step_by_N": {str(n): round(span / n, 2) for n in (200, 50, 10, 5, 2, 1)},
            "snr_factor_per_step": {str(n): round(math.exp(span / n), 1)
                                    for n in (200, 50, 10, 5, 2, 1)}}


def plot_order(res: dict, path) -> None:
    grid = sorted(int(k) for k in res["rms_error_by_steps"])
    errs = [res["rms_error_by_steps"][str(n)] for n in grid]
    c = res["one_over_N_coefficient"]
    slope = res["loglog_slope_band_10_100"]

    fig, ax = plt.subplots(figsize=(11.4, 6.4), facecolor="#F8FAFC")
    ax.loglog(grid, errs, "o", color=BLUE, ms=10, lw=0, label="实测轨迹误差（配对）")
    ref = [c / n for n in grid]
    ax.loglog(grid, ref, "--", color=ORANGE, lw=2.2,
              label=f"纯 1/N 外推（渐近区斜率 {slope:.2f}，系数 {c}）")
    for n, e in zip(grid, errs):
        ax.annotate(f"{e:.3g}".rstrip("0").rstrip("."), (n, e), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=10, color=BLUE,
                    bbox=dict(boxstyle="round,pad=0.18", fc="#F8FAFC", ec="none", alpha=.92))
    ax.axhline(rx.RADIUS, color=GREY, ls=":", lw=1.4)
    ax.text(grid[-1], rx.RADIUS * 1.12, f"整张图的尺度（峰心半径 {rx.RADIUS}）",
            fontsize=11, color=GREY, ha="right")
    ax.axhline(rx.SIGMA, color=GREEN, ls="--", lw=1.6)
    ax.text(grid[-1], rx.SIGMA * 1.18, f"团的标准差 σ={rx.SIGMA}",
            fontsize=11, color=GREEN, ha="right")
    ax.axvspan(2, 4.6, color="#E76F51", alpha=.10)
    ax.text(3.1, 0.012, "1/N 在这里失效\n图也在这里塌", fontsize=11, color=ORANGE,
            ha="center", va="center")
    ax.set_xlabel("采样步数 N（对数轴）", fontsize=13)
    ax.set_ylabel("同一条 ODE，N 步解与精确解的 RMS 位移", fontsize=13)
    ax.set_title("离散误差按 1/N 增长——而它恰好在画面崩掉的那个点上不再遵守 1/N",
                 fontsize=15, color=INK)
    ax.grid(which="both", alpha=.22)
    ax.set_ylim(0.0012, 5.5)
    ax.legend(fontsize=12, frameon=False, loc="lower left")
    ax.set_xticks(grid)
    ax.set_xticklabels([str(n) for n in grid], fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


if __name__ == "__main__":
    out["A_convergence_order"] = order_experiment()
    out["B_C_one_step"] = one_step_structure()
    out["D_amplification"] = amplification()
    out["E_logsnr_span"] = logsnr_span()
    out["F_energy_floor"] = energy_floor()
    res = json.loads((ROOT / "results.json").read_text())["results"]
    out["B_C_one_step"]["measured_1step_radius_from_results"] = res["1"]["radius_mean"]
    e = out["A_convergence_order"]["rms_error_by_steps"]
    out["A_convergence_order"]["err_10_over_50"] = round(e["10"] / e["50"], 2)
    out["A_convergence_order"]["err_5_over_10"] = round(e["5"] / e["10"], 2)
    plot_order(out["A_convergence_order"], ROOT / "05-convergence-order.png")
    (ROOT / "math_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps(out, ensure_ascii=False, indent=2))
