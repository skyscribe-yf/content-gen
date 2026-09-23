#!/usr/bin/env python3
"""篇 2 实验：分数场 / 单级朗之万 / 多级退火 / 流形与薄壳。

主线问题（2208.11970 §5；Song & Ermon 2019 NCSN）：只学「每一点的坡度」（分数），
凭什么能采样出图？理论上一个噪声级别就够（朗之万），实践上会崩在哪、为什么崩、
多级噪声退火为什么是必需品——四块实验：

  A 分数场质量   ：空间均匀度量下，误差按「离数据环多远」分桶——空地吃掉大部分
                   平方误差，而训练样本几乎从不落在空地（0.x%）。
  B 单级朗之万   ：步长扫描（走不动 / 飞出去 / 比例错）+ σ 扫描——单级的两难是
                   **位置 vs 比例**：σ 小 → 位置准、比例错；σ 大 → 比例准、样本糊。
  C 同预算对打   ：同样的分数调用次数，单级 vs 多级退火；画「清晰度 × 比例」权衡面，
                   退火落在两个都好的角落。
  D 流形与薄壳   ：左——1D 曲线嵌 2D，三个 σ 的场（大 σ 抹平 / 小 σ 空地乱）；
                   右——维度一高，几乎整个空间都是空地（正交嵌入保距：锅在空间不在数据）。

数据：8 峰高斯混合（环上等角、不等权【不等权才能暴露比例错】、σ_peak=0.35、半径 3）；
      D 左用正弦曲线（1D 流形）；D 右用嵌入到高维的环。
模型：纯 numpy 手写小 MLP（Adam）——σ 条件网络（训练噪声级 log-uniform）+ 单级网络
      （只在 σ=0.05 训练）。网络权重存 nets.npz，重跑可跳过训练。
诚实边界：玩具 + 逐点指标 ≠ 端到端生成质量；结论只说明机制。
产物：results.json / nets.npz / A-…-quality.png / B-…-failures.png /
      C-budget-showdown.png / D-manifold-panel.png
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
SEED = 20260921
MODES, RADIUS, SIGMA_PEAK = 8, 3.0, 0.35
WEIGHTS = np.array([0.30, 0.20, 0.15, 0.10, 0.08, 0.07, 0.06, 0.04])
SIGMA_MIN, SIGMA_MAX, LEVELS = 0.05, 3.0, 10
SIGMAS_TRAIN = np.geomspace(SIGMA_MIN, SIGMA_MAX, 32)
LOG_SMIN, LOG_SMAX = math.log(SIGMA_MIN), math.log(SIGMA_MAX)
STEPS_COND, BATCH, HID = 30000, 512, 128
STEPS_FIXED = 6000
SIGMA_SINGLE = 0.05
SIGMAS_EVAL_A = [0.05, 0.15, 0.35, 1.0, 3.0]
BLUE, ORANGE, YELLOW, INK, GREY, GREEN, RED, PURPLE = (
    "#0F4C81", "#E76F51", "#F6BD60", "#17324D", "#5B7186", "#2A9D8F", "#C44536", "#7B5EA7")

ANG = np.arange(MODES) * 2 * np.pi / MODES
CENTERS = np.stack([RADIUS * np.cos(ANG), RADIUS * np.sin(ANG)], 1)


# ------------------------------------------------------------------ 数据与解析真值
def sample_data(n, rng):
    k = rng.choice(MODES, size=n, p=WEIGHTS)
    return CENTERS[k] + rng.normal(0, SIGMA_PEAK, size=(n, 2))


def gmm_resp(x, sig):
    s2 = SIGMA_PEAK ** 2 + np.asarray(sig, float) ** 2
    d2 = ((x[:, None, :] - CENTERS[None]) ** 2).sum(-1)
    logw = np.log(WEIGHTS)[None] - d2 / (2 * s2)
    logw -= logw.max(1, keepdims=True)
    r = np.exp(logw)
    return r / r.sum(1, keepdims=True), s2


def analytic_eps(x, sig):
    r, s2 = gmm_resp(x, sig)
    x0m = (r[:, :, None] * ((SIGMA_PEAK ** 2 * x[:, None, :]
                             + np.asarray(sig, float) ** 2 * CENTERS[None]) / s2)).sum(1)
    return (x - x0m) / np.asarray(sig, float)


def analytic_score(x, sig):
    return -analytic_eps(x, sig) / np.asarray(sig, float)


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


def feat_cond(x, sig):
    s = np.full((x.shape[0], 1), float(sig)) if np.ndim(sig) == 0 \
        else np.asarray(sig, float).reshape(-1, 1)
    u = (np.log(s) - LOG_SMIN) / (LOG_SMAX - LOG_SMIN)
    return np.concatenate([x, u], 1)


def train_cond_net(seed):
    net = MLP(seed, din=3)
    rng = np.random.default_rng(seed + 7)
    losses = []
    for _ in range(STEPS_COND):
        x0 = sample_data(BATCH, rng)
        sig = SIGMAS_TRAIN[rng.integers(0, len(SIGMAS_TRAIN), size=BATCH)]
        eps = rng.normal(0, 1, size=(BATCH, 2))
        losses.append(net.train_step(feat_cond(x0 + sig[:, None] * eps, sig), eps))
    return net, losses


def train_fixed_net(sig, seed, din=2, steps=STEPS_FIXED, sampler=None):
    net = MLP(seed, din=din)
    rng = np.random.default_rng(seed + 11)
    losses = []
    for _ in range(steps):
        x0 = sample_data(BATCH, rng) if sampler is None else sampler(BATCH, rng)
        eps = rng.normal(0, 1, size=(BATCH, 2))
        losses.append(net.train_step(x0 + sig * eps, eps))
    return net, losses


def score_of(net, x, sig, cond=True):
    eps_hat = net.forward(feat_cond(x, sig)) if cond else net.forward(x)
    return -eps_hat / sig


# ------------------------------------------------------------------------- 采样器
def langevin(net, x0, sig, eta, steps, rng, cond=True):
    x = np.array(x0, dtype=float)
    for _ in range(steps):
        x = x + eta * score_of(net, x, sig, cond) + math.sqrt(2 * eta) * rng.normal(0, 1, x.shape)
    return x


def annealed(net, x0, sigmas, steps_per_level, rng, eta_scale=0.1):
    x = np.array(x0, dtype=float)
    for sig in sigmas:
        x = langevin(net, x, sig, eta_scale * sig ** 2, steps_per_level, rng)
    return x


def uniform_disk(n, radius, rng):
    r = radius * np.sqrt(rng.random(n))
    th = rng.random(n) * 2 * np.pi
    return np.stack([r * np.cos(th), r * np.sin(th)], 1)


# ------------------------------------------------------------------------- 度量
def assign_modes(x):
    return ((x[:, None, :] - CENTERS[None]) ** 2).sum(-1).argmin(1)


def prop_l1(x):
    counts = np.bincount(assign_modes(x), minlength=MODES) / len(x)
    return float(np.abs(counts - WEIGHTS).sum()), counts


def blur(x):
    """清晰度：样本到数据环的中位距离（数据自身宽度 σ_peak≈0.35 → 真样本约 0.41）。"""
    return float(np.median(np.abs(np.linalg.norm(x, axis=1) - RADIUS)))


def energy_distance(A, B, rng, m=700):
    A = A if len(A) <= m else A[rng.choice(len(A), m, replace=False)]
    B = B if len(B) <= m else B[rng.choice(len(B), m, replace=False)]
    d_ab = np.sqrt(((A[:, None, :] - B[None]) ** 2).sum(-1)).mean()
    d_aa = np.sqrt(((A[:, None, :] - A[None]) ** 2).sum(-1)).mean()
    d_bb = np.sqrt(((B[:, None, :] - B[None]) ** 2).sum(-1)).mean()
    return float(2 * d_ab - d_aa - d_bb)


def true_samples_at(sig, n, rng):
    return sample_data(n, rng) + sig * rng.normal(0, 1, size=(n, 2))


# ------------------------------------------------------------------- 实验 A：场质量
A_EDGES = [0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 5.0]


def exp_A(net_cond, net_fixed):
    rng = np.random.default_rng(SEED + 101)
    n = 20000
    pts = uniform_disk(n, 5.0, rng)
    d_ring = np.abs(np.linalg.norm(pts, axis=1) - RADIUS)
    bin_id = np.digitize(d_ring, A_EDGES) - 1
    out = {"measure": "空间均匀（半径 5 圆盘），非 p_σ 加权", "bins": A_EDGES, "by_sigma": {}}
    for sig in SIGMAS_EVAL_A:
        s_star = analytic_score(pts, sig)
        s_hat = score_of(net_cond, pts, sig, cond=True)
        rel = np.linalg.norm(s_hat - s_star, axis=1) / (np.linalg.norm(s_star, axis=1) + 1e-12)
        err2 = ((s_hat - s_star) ** 2).sum(1)
        tot = err2.sum()
        samp = true_samples_at(sig, n, rng)
        s_bin = np.digitize(np.abs(np.linalg.norm(samp, axis=1) - RADIUS), A_EDGES) - 1
        rows = []
        for b in range(len(A_EDGES) - 1):
            m = bin_id == b
            if not m.any():
                continue
            rows.append({
                "d_lo": A_EDGES[b], "d_hi": A_EDGES[b + 1],
                "space_share_pct": round(100 * float(m.mean()), 2),
                "train_sample_share_pct": round(100 * float((s_bin == b).mean()), 4),
                "median_rel_err": round(float(np.median(rel[m])), 4),
                "pct_rel_err_gt_1": round(100 * float((rel[m] > 1).mean()), 2),
                "err_share_pct": round(100 * float(err2[m].sum() / tot), 2),
            })
        far = d_ring > 1.0
        samp_far = np.abs(np.linalg.norm(samp, axis=1) - RADIUS) > 1.0
        out["by_sigma"][str(sig)] = {
            "bins": rows,
            "median_rel_err_all": round(float(np.median(rel)), 4),
            "far_err_share_pct": round(100 * float(err2[far].sum() / tot), 2),
            "far_space_share_pct": round(100 * float(far.mean()), 2),
            "train_sample_far_share_pct": round(100 * float(samp_far.mean()), 4),
            "far_median_rel_err": round(float(np.median(rel[far])), 4),
            "near_median_rel_err": round(float(np.median(rel[~far])), 4),
            "far_pct_rel_err_gt_1": round(100 * float((rel[far] > 1).mean()), 2),
            "near_pct_rel_err_gt_1": round(100 * float((rel[~far] > 1).mean()), 2),
        }
    s_star = analytic_score(pts, SIGMA_SINGLE)
    out["single_level_net_compare"] = {}
    for tag, net, cond in (("cond", net_cond, True), ("fixed_single", net_fixed, False)):
        s_hat = score_of(net, pts, SIGMA_SINGLE, cond=cond)
        rel = np.linalg.norm(s_hat - s_star, axis=1) / (np.linalg.norm(s_star, axis=1) + 1e-12)
        out["single_level_net_compare"][tag] = {
            "median_rel_err": round(float(np.median(rel)), 4),
            "far_median_rel_err": round(float(np.median(rel[d_ring > 1.0])), 4),
        }
    return out


# ------------------------------------------------------- 实验 B：单级朗之万会崩
def exp_B(net_fixed, net_cond):
    rng = np.random.default_rng(SEED + 202)
    M, STEPS = 1500, 800
    init = uniform_disk(M, 5.0, rng)
    eta_grid = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1, 1.0]
    rows = []
    for eta in eta_grid:
        r = np.random.default_rng(SEED + 303)
        x = langevin(net_fixed, init, SIGMA_SINGLE, eta, STEPS, r, cond=False)
        bad = ~np.isfinite(x).all(1)
        far = (np.linalg.norm(x, axis=1) > 20) | bad
        moved = float(np.median(np.linalg.norm(x[~far] - init[~far], axis=1))) if (~far).any() else 0.0
        l1 = prop_l1(x[~far])[0] if (~far).any() else float("nan")
        rows.append({"eta": eta, "flew_pct": round(100 * float(far.mean()), 2),
                     "median_move": round(moved, 3),
                     "prop_l1": round(l1, 4) if l1 == l1 else None})
    ok = [r for r in rows if r["flew_pct"] < 5 and r["median_move"] > 1.0 and r["prop_l1"] is not None]
    best = min(ok, key=lambda r: r["prop_l1"]) if ok else rows[4]
    # σ 扫描：每个 σ 自己挑最优步长（η = c σ²），记录「比例」与「清晰度」两个指标
    sig_grid = [0.05, 0.08, 0.12, 0.2, 0.35, 0.6, 1.0, 1.8, 3.0]
    ref = true_samples_at(SIGMA_SINGLE, M, np.random.default_rng(SEED + 404))
    ref_blur = blur(ref)
    sweep = []
    for sig in sig_grid:
        cand_best = None
        for c in [0.05, 0.1, 0.2]:
            r = np.random.default_rng(SEED + 505)
            x = langevin(net_cond, init, sig, c * sig ** 2, 500, r, cond=True)
            far = (np.linalg.norm(x, axis=1) > 20) | ~np.isfinite(x).all(1)
            if far.mean() > 0.05:
                continue
            l1 = prop_l1(x)[0]
            ed = energy_distance(x, ref, np.random.default_rng(SEED + 606))
            cand = {"c": c, "prop_l1": round(l1, 4), "energy_dist": round(ed, 4),
                    "blur": round(blur(x), 4)}
            if cand_best is None or cand["energy_dist"] < cand_best["energy_dist"]:
                cand_best = cand
        sweep.append({"sigma": sig, **(cand_best or {"c": None, "prop_l1": None,
                                                     "energy_dist": None, "blur": None})})
    return {"eta_sweep": rows, "best_eta": best["eta"], "best_prop_l1": best["prop_l1"],
            "best_median_move": best["median_move"], "sigma_sweep": sweep,
            "steps": STEPS, "particles": M, "ref_blur": round(ref_blur, 4)}


# --------------------------------------------- 实验 C：同预算对打（单级 vs 退火）
def annealed_variants(net_cond, init, budget, seeds):
    """三种退火配置，同预算；用于确认结论不依赖某一种调参。"""
    cfgs = {
        "uniform_10": dict(sigmas=np.geomspace(SIGMA_MAX, SIGMA_MIN, 10), eta_scale=0.1),
        "uniform_10_eta3": dict(sigmas=np.geomspace(SIGMA_MAX, SIGMA_MIN, 10), eta_scale=0.3),
        "uniform_15": dict(sigmas=np.geomspace(SIGMA_MAX, SIGMA_MIN, 15), eta_scale=0.1),
    }
    out = {}
    for name, cfg in cfgs.items():
        l1s, blurs = [], []
        for sd in seeds:
            r = np.random.default_rng(sd + 5)
            x = annealed(net_cond, init, cfg["sigmas"], max(1, budget // len(cfg["sigmas"])),
                         r, eta_scale=cfg["eta_scale"])
            l1s.append(prop_l1(x)[0])
            blurs.append(blur(x))
        out[name] = {"prop_l1_mean": round(float(np.mean(l1s)), 4), "blur_mean": round(float(np.mean(blurs)), 4)}
    return out


def exp_C(net_fixed, net_cond, best_eta):
    budgets = [250, 500, 1000, 2000]
    seeds = [SEED + 11, SEED + 22, SEED + 33]
    M = 1000
    curve = []
    for B in budgets:
        row = {"budget": B}
        for tag, kind in (("single", "s"), ("annealed", "a")):
            l1s, eds, blurs = [], [], []
            for sd in seeds:
                r = np.random.default_rng(sd)
                init = uniform_disk(M, 5.0, r)
                if kind == "s":
                    x = langevin(net_fixed, init, SIGMA_SINGLE, best_eta, B, r, cond=False)
                else:
                    x = annealed(net_cond, init, np.geomspace(SIGMA_MAX, SIGMA_MIN, LEVELS),
                                 max(1, B // LEVELS), r)
                l1s.append(prop_l1(x)[0])
                blurs.append(blur(x))
                ref = true_samples_at(SIGMA_SINGLE, M, np.random.default_rng(sd + 1))
                eds.append(energy_distance(x, ref, np.random.default_rng(sd + 2)))
            row[tag] = {"prop_l1_mean": round(float(np.mean(l1s)), 4),
                        "prop_l1_std": round(float(np.std(l1s)), 4),
                        "blur_mean": round(float(np.mean(blurs)), 4),
                        "energy_dist_mean": round(float(np.mean(eds)), 4),
                        "energy_dist_std": round(float(np.std(eds)), 4)}
        curve.append(row)
    # 权衡面：单级按 σ 扫（同预算 1000）+ 退火按预算扫，画「清晰度 × 比例」
    trade = {"single_by_sigma": [], "annealed_by_budget": []}
    init = uniform_disk(M, 5.0, np.random.default_rng(SEED + 77))
    for sig in [0.05, 0.1, 0.2, 0.35, 0.6, 1.0, 1.8, 3.0]:
        c = None
        for cc in [0.05, 0.1, 0.2]:
            x = langevin(net_cond, init, sig, cc * sig ** 2, 1000,
                         np.random.default_rng(SEED + 888), cond=True)
            far = (np.linalg.norm(x, axis=1) > 20) | ~np.isfinite(x).all(1)
            if far.mean() > 0.05:
                continue
            l1 = prop_l1(x)[0]
            if c is None or l1 < c[1]:
                c = (cc, l1, blur(x))
        if c:
            trade["single_by_sigma"].append({"sigma": sig, "eta_c": c[0], "prop_l1": round(c[1], 4),
                                             "blur": round(c[2], 4)})
    for B in [250, 500, 1000, 2000, 4000]:
        x = annealed(net_cond, init, np.geomspace(SIGMA_MAX, SIGMA_MIN, LEVELS),
                     max(1, B // LEVELS), np.random.default_rng(SEED + 999))
        trade["annealed_by_budget"].append({"budget": B, "prop_l1": round(prop_l1(x)[0], 4),
                                            "blur": round(blur(x), 4)})
    return {"curve": curve, "tradeoff": trade,
            "annealed_variants_at_1000": annealed_variants(net_cond, init, 1000, seeds),
            "scatter": {"single": langevin(net_fixed, init, SIGMA_SINGLE, best_eta, 1000,
                                           np.random.default_rng(SEED + 77), cond=False).tolist(),
                        "annealed": annealed(net_cond, init, np.geomspace(SIGMA_MAX, SIGMA_MIN, LEVELS),
                                             100, np.random.default_rng(SEED + 78)).tolist()}}


# ------------------------------------------------------- 实验 D：流形 + 高维薄壳
CURVE_N = 800
_t = np.linspace(-3.0, 3.0, CURVE_N)
CURVE = np.stack([_t, 1.2 * np.sin(1.1 * _t)], 1)
CURVE_W = np.ones(CURVE_N) / CURVE_N


def curve_target(n, rng):
    return CURVE[rng.integers(0, CURVE_N, size=n)]


def curve_field(x, sig):
    d2 = ((x[:, None, :] - CURVE[None]) ** 2).sum(-1)
    w = np.exp(-d2 / (2 * sig ** 2)) * CURVE_W[None]
    Z = w.sum(1, keepdims=True) + 1e-300
    return (-((x[:, None, :] - CURVE[None]) / sig ** 2) * w[:, :, None]).sum(1) / Z


def exp_D(nets_cache=None):
    sig_list = [0.05, 0.3, 1.2]
    nets = {}
    for i, sig in enumerate(sig_list):
        nets[sig] = train_fixed_net(sig, SEED + 900 + i, steps=8000, sampler=curve_target)[0]
    xs = np.linspace(-4, 4, 15)
    ys = np.linspace(-3.2, 3.2, 12)
    XX, YY = np.meshgrid(xs, ys)
    grid = np.stack([XX.ravel(), YY.ravel()], 1)
    dcurve = np.sqrt(((grid[:, None, :] - CURVE[None]) ** 2).sum(-1)).min(1)
    panels = []
    for sig in sig_list:
        star = curve_field(grid, sig)
        hat = score_of(nets[sig], grid, sig, cond=False)
        rel = np.linalg.norm(hat - star, axis=1) / (np.linalg.norm(star, axis=1) + 1e-12)
        panels.append({
            "sigma": sig,
            "median_rel_err": round(float(np.median(rel)), 4),
            "rel_err_near_curve": round(float(np.median(rel[dcurve < 3 * sig])), 4)
            if (dcurve < 3 * sig).any() else None,
            "rel_err_off_curve": round(float(np.median(rel[dcurve >= 5 * sig])), 4)
            if (dcurve >= 5 * sig).any() else None,
            "pct_rel_err_gt_1_off_curve": round(
                100 * float((rel[dcurve >= 5 * sig] > 1).mean()), 2)
            if (dcurve >= 5 * sig).any() else None,
        })
    base = sample_data(1500, np.random.default_rng(SEED + 808))
    shell = []
    for D in [2, 4, 8, 16, 64]:
        Q, _ = np.linalg.qr(np.random.default_rng(SEED + 909).normal(0, 1, (D, 2)))
        XD = base @ Q.T
        rmc = np.random.default_rng(SEED + 1010)
        m, R = 8000, 4.0
        dirs = rmc.normal(0, 1, (m, D))
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        Y = dirs * (R * rmc.random(m) ** (1.0 / D))[:, None]
        uy = Y @ Q
        out_y = np.sqrt(np.maximum((Y ** 2).sum(1) - (uy ** 2).sum(1), 0))
        dy = np.sqrt(out_y ** 2 + (np.linalg.norm(uy, axis=1) - RADIUS) ** 2)
        # 分块算最近距离：D=64 时 (8000,1500,64) 全量广播要 ~6GB，会触发 OOM 杀进程
        dd = np.empty(len(Y))
        for s in range(0, len(Y), 500):
            blk = Y[s:s + 500]
            dd[s:s + 500] = np.sqrt(((blk[:, None, :] - XD[None]) ** 2).sum(-1)).min(1)
        shell.append({
            "D": D,
            "empty_share_pct": round(100 * float((dy > 3 * SIGMA_PEAK).mean()), 2),
            "median_dist_to_data_over_R": round(float(np.median(dd) / R), 4),
        })
    return {"curve_sigma_panels": panels, "shell": shell}, nets


# ------------------------------------------------------------------------- 画图
def plot_A(res, path):
    sigs = SIGMAS_EVAL_A
    colors = {0.05: RED, 0.15: ORANGE, 0.35: BLUE, 1.0: GREEN, 3.0: GREY}
    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.4), facecolor="#F8FAFC")
    for sig in sigs:
        rows = res["by_sigma"][str(sig)]["bins"]
        xs = [(r["d_lo"] + min(r["d_hi"], 2.5)) / 2 for r in rows]
        axes[0].plot(xs, [min(r["median_rel_err"], 50) for r in rows], "-o",
                     color=colors[sig], lw=2.0, ms=6, label=f"σ = {sig}")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("离数据环的距离（数据尺度：半径 3，峰的标准差 0.35）", fontsize=11.5)
    axes[0].set_ylabel("分数场的中位相对误差（对数轴）", fontsize=11.5)
    axes[0].set_title("越往空地走，学到的坡度越不可信", fontsize=13.5, color=INK)
    axes[0].grid(alpha=.25)
    axes[0].legend(fontsize=10.5, frameon=False)
    w = 0.36
    idx = np.arange(len(sigs))
    far_err = [res["by_sigma"][str(s)]["far_err_share_pct"] for s in sigs]
    far_space = [res["by_sigma"][str(s)]["far_space_share_pct"] for s in sigs]
    far_samp = [res["by_sigma"][str(s)]["train_sample_far_share_pct"] for s in sigs]
    axes[1].bar(idx - w / 2, far_err, w, color=BLUE, label="误差占比（空地上）")
    axes[1].bar(idx + w / 2, far_space, w, color=YELLOW, label="空间占比（空地）")
    axes[1].plot(idx, far_samp, "o--", color=RED, lw=2.0, ms=7, label="训练样本落在空地的比例")
    axes[1].set_xticks(idx)
    axes[1].set_xticklabels([f"σ={s}" for s in sigs], fontsize=11)
    axes[1].set_ylabel("百分比（%，离数据环 > 1.0 视为空地）", fontsize=11.5)
    axes[1].set_ylim(0, 105)
    axes[1].set_title("空地吃掉大部分误差，却是训练样本几乎不去的地方", fontsize=13.5, color=INK)
    axes[1].grid(alpha=.25, axis="y")
    axes[1].legend(fontsize=10.5, frameon=False)
    fig.suptitle("实验 A：分数场的误差分布（空间均匀度量）", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


def plot_B(res, path, net_fixed, best_eta):
    fig, axes = plt.subplots(1, 3, figsize=(16.8, 5.2), facecolor="#F8FAFC")
    rng0 = np.random.default_rng(SEED + 202)
    init = uniform_disk(600, 5.0, rng0)
    axes[0].scatter(init[:, 0], init[:, 1], s=3, alpha=.25, color=GREY, label="出发位置")
    for eta, col, name in ((1e-3, GREEN, "η = 1e-3（走不动）"),
                           (best_eta, BLUE, f"η = {best_eta:g}（能走，但比例错）"),
                           (1.0, RED, "η = 1（飞出去）")):
        x = langevin(net_fixed, init, SIGMA_SINGLE, eta, res["steps"],
                     np.random.default_rng(SEED + 222), cond=False)
        keep = np.isfinite(x).all(1) & (np.linalg.norm(x, axis=1) < 8)
        axes[0].scatter(x[keep, 0], x[keep, 1], s=3, alpha=.5, color=col, label=name)
    axes[0].scatter(CENTERS[:, 0], CENTERS[:, 1], marker="x", s=60, color=INK, label="峰心")
    axes[0].set_aspect("equal")
    axes[0].set_xlim(-6, 6)
    axes[0].set_ylim(-6, 6)
    axes[0].set_title("三种步长的终点（σ=0.05）", fontsize=13, color=INK)
    axes[0].grid(alpha=.25)
    axes[0].legend(fontsize=9.5, frameon=False, loc="upper right")
    rows = res["eta_sweep"]
    xs = [r["eta"] for r in rows]
    ax2 = axes[1]
    ax2.plot(xs, [r["prop_l1"] if r["prop_l1"] is not None else np.nan for r in rows],
             "-o", color=BLUE, lw=2, ms=6, label="模式比例 L1")
    ax2.plot(xs, [r["median_move"] / 5 for r in rows], "-s", color=GREEN, lw=2, ms=6,
             label="中位位移 ÷ 5")
    ax2.plot(xs, [r["flew_pct"] / 100 for r in rows], "-^", color=RED, lw=2, ms=6,
             label="飞出去的比例")
    ax2.set_xscale("log")
    ax2.set_xlabel("步长 η（σ = 0.05，自然尺度 η ≈ σ²）", fontsize=11.5)
    ax2.set_ylabel("指标（归一化后画在一起）", fontsize=11.5)
    ax2.set_title("步长扫描：走不动 / 飞出去 / 比例错", fontsize=13, color=INK)
    ax2.grid(alpha=.25)
    ax2.legend(fontsize=10.5, frameon=False)
    ax3 = axes[2]
    sw = res["sigma_sweep"]
    ax3.plot([r["sigma"] for r in sw],
             [r["prop_l1"] if r["prop_l1"] is not None else np.nan for r in sw],
             "-o", color=BLUE, lw=2, ms=6, label="模式比例 L1（比例）")
    ax3.plot([r["sigma"] for r in sw],
             [r["blur"] if r["blur"] is not None else np.nan for r in sw],
             "-s", color=ORANGE, lw=2, ms=6, label="样本到数据环的中位距离（清晰度）")
    ax3.axhline(res["ref_blur"], ls=":", color=GREY, lw=1.5,
                label=f"真数据自身的宽度（{res['ref_blur']:.2f}）")
    ax3.set_xscale("log")
    ax3.set_xlabel("只给一个噪声级别 σ（各自最优步长）", fontsize=11.5)
    ax3.set_title("单级的两难：位置 vs 比例", fontsize=13, color=INK)
    ax3.grid(alpha=.25)
    ax3.legend(fontsize=9.5, frameon=False)
    fig.suptitle("实验 B：单级朗之万实战——它真的会崩", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


def plot_C(res, path):
    curve = res["curve"]
    bs = [r["budget"] for r in curve]
    fig, axes = plt.subplots(1, 3, figsize=(16.8, 5.2), facecolor="#F8FAFC")
    for ax, key, stdkey, title, ylab in (
            (axes[0], "prop_l1_mean", "prop_l1_std", "模式比例 L1（越低越准）", "模式比例 L1"),
            (axes[1], "blur_mean", None, "清晰度：样本离数据环的中位距离", "到数据环的距离")):
        if stdkey:
            ax.errorbar(bs, [r["single"][key] for r in curve],
                        yerr=[r["single"][stdkey] for r in curve], fmt="-o", color=RED,
                        lw=2.2, ms=7, capsize=4, label="单级（最优步长）")
            ax.errorbar(bs, [r["annealed"][key] for r in curve],
                        yerr=[r["annealed"][stdkey] for r in curve], fmt="-o", color=BLUE,
                        lw=2.2, ms=7, capsize=4, label="多级退火")
        else:
            ax.plot(bs, [r["single"][key] for r in curve], "-o", color=RED, lw=2.2, ms=7,
                    label="单级（最优步长）")
            ax.plot(bs, [r["annealed"][key] for r in curve], "-o", color=BLUE, lw=2.2, ms=7,
                    label="多级退火")
        ax.set_xlabel("分数调用次数（同一预算）", fontsize=11.5)
        ax.set_ylabel(ylab, fontsize=11.5)
        ax.set_title(title, fontsize=13, color=INK)
        ax.grid(alpha=.25)
        ax.legend(fontsize=10.5, frameon=False)
    ax = axes[2]
    tr = res["tradeoff"]
    ax.plot([p["blur"] for p in tr["single_by_sigma"]],
            [p["prop_l1"] for p in tr["single_by_sigma"]], "-o", color=RED, lw=2, ms=7,
            label="单级：换 σ 的轨迹")
    for p in tr["single_by_sigma"]:
        ax.annotate(f"σ={p['sigma']:g}", (p["blur"], p["prop_l1"]), fontsize=8.5,
                    textcoords="offset points", xytext=(4, 4), color=RED)
    ax.plot([p["blur"] for p in tr["annealed_by_budget"]],
            [p["prop_l1"] for p in tr["annealed_by_budget"]], "-s", color=BLUE, lw=2, ms=7,
            label="退火：加预算的轨迹")
    for p in tr["annealed_by_budget"]:
        ax.annotate(f"{p['budget']}", (p["blur"], p["prop_l1"]), fontsize=8.5,
                    textcoords="offset points", xytext=(4, -10), color=BLUE)
    ax.set_xlabel("模糊程度（离数据环的中位距离，越小越清晰）", fontsize=11.5)
    ax.set_ylabel("模式比例 L1（越小越准）", fontsize=11.5)
    ax.set_title("清晰度 × 比例：退火落在两个都好的角落", fontsize=13, color=INK)
    ax.grid(alpha=.25)
    ax.legend(fontsize=10, frameon=False)
    fig.suptitle("实验 C：同预算对打——单级 vs 多级退火", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


def plot_D(res, path, nets, sig_list):
    fig = plt.figure(figsize=(16.8, 9.6), facecolor="#F8FAFC")
    gs = fig.add_gridspec(3, 4, width_ratios=[1, 1, 0.12, 1.1])
    xs = np.linspace(-4, 4, 15)
    ys = np.linspace(-3.2, 3.2, 12)
    XX, YY = np.meshgrid(xs, ys)
    grid = np.stack([XX.ravel(), YY.ravel()], 1)
    for i, sig in enumerate(sig_list):
        star = curve_field(grid, sig)
        hat = score_of(nets[sig], grid, sig, cond=False)
        for j, (F, name, col) in enumerate(((star, "解析真值", GREY), (hat, "学到的场", BLUE))):
            ax = fig.add_subplot(gs[i, j])
            ax.plot(CURVE[:, 0], CURVE[:, 1], "-", color=ORANGE, lw=1.6, alpha=.85)
            sn = F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-12)
            ax.quiver(grid[:, 0], grid[:, 1], sn[:, 0], sn[:, 1], color=col, alpha=.85,
                      scale=30, width=.0035)
            ax.set_xlim(-4, 4)
            ax.set_ylim(-3.2, 3.2)
            ax.set_xticks([])
            ax.set_yticks([])
            if i == 0:
                ax.set_title(name, fontsize=12.5, color=INK)
            if j == 0:
                ax.set_ylabel(f"σ = {sig}", fontsize=12.5, color=INK)
    axr = fig.add_subplot(gs[:, 3])
    shell = res["shell"]
    Ds = [s["D"] for s in shell]
    axr.plot(Ds, [s["empty_share_pct"] for s in shell], "-o", color=RED, lw=2.4, ms=8,
             label="空地占比（距流形 > 3 倍峰的标准差 0.35）")
    axr.plot(Ds, [s["median_dist_to_data_over_R"] * 100 for s in shell], "-s", color=BLUE,
             lw=2.4, ms=8, label="随机点到最近数据的中位距离 ÷ 环境半径（×100）")
    axr.set_xscale("log", base=2)
    axr.set_xticks(Ds)
    axr.set_xticklabels([str(d) for d in Ds])
    axr.set_xlabel("数据被嵌入的环境维度 D（正交嵌入保距）", fontsize=11.5)
    axr.set_ylabel("百分比 / 相对距离", fontsize=11.5)
    axr.set_title("维度一高，几乎整个空间都是空地", fontsize=13, color=INK)
    axr.grid(alpha=.25)
    axr.legend(fontsize=10, frameon=False, loc="center right")
    for s in shell:
        axr.annotate(f"{s['empty_share_pct']:.1f}%", (s["D"], s["empty_share_pct"]),
                     textcoords="offset points", xytext=(0, 9), ha="center", fontsize=9.5,
                     color=RED)
    fig.suptitle("实验 D：一条 1D 曲线上的场（左）+ 高维空间的薄壳（右）", fontsize=16, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(path, dpi=150, facecolor="#F8FAFC")
    plt.close(fig)


# --------------------------------------------------------------------------- main
def main(t0=None):
    t0 = t0 or time.time()
    nets_path = ROOT / "nets.npz"
    if nets_path.exists():
        net_cond = MLP(SEED + 1, din=3)
        net_cond.load(nets_path, "cond")
        net_fixed = MLP(SEED + 2, din=2)
        net_fixed.load(nets_path, "fixed")
        losses_c, losses_f = [0.0], [0.0]
        print("载入 nets.npz，跳过训练", flush=True)
    else:
        print("训练 σ 条件网络 …", flush=True)
        net_cond, losses_c = train_cond_net(SEED + 1)
        print(f"  完成（{time.time()-t0:.0f}s）终损 {np.mean(losses_c[-500:]):.4f}", flush=True)
        print("训练单级网络（σ=0.05）…", flush=True)
        net_fixed, losses_f = train_fixed_net(SIGMA_SINGLE, SEED + 2)
        print(f"  完成（{time.time()-t0:.0f}s）终损 {np.mean(losses_f[-300:]):.4f}", flush=True)
        np.savez_compressed(nets_path,
                            **{f"cond_{k}": v for k, v in net_cond.p.items()},
                            **{f"fixed_{k}": v for k, v in net_fixed.p.items()})

    print("实验 A …", flush=True)
    A = exp_A(net_cond, net_fixed)
    print("实验 B …", flush=True)
    B = exp_B(net_fixed, net_cond)
    print(f"  最优步长 η = {B['best_eta']}，比例 L1 = {B['best_prop_l1']}", flush=True)
    print("实验 C …", flush=True)
    C = exp_C(net_fixed, net_cond, B["best_eta"])
    print("实验 D …", flush=True)
    D, curve_nets = exp_D()

    key = [r for r in C["curve"] if r["budget"] == 1000][0]
    out = {
        "config": {"seed": SEED, "modes": MODES, "radius": RADIUS, "sigma_peak": SIGMA_PEAK,
                   "weights": WEIGHTS.tolist(), "sigma_min": SIGMA_MIN, "sigma_max": SIGMA_MAX,
                   "levels": LEVELS, "sigma_single": SIGMA_SINGLE, "steps_cond": STEPS_COND,
                   "steps_fixed": STEPS_FIXED, "batch": BATCH, "hidden": HID,
                   "model": "tiny numpy MLP (Adam): σ-conditioned + single-σ"},
        "final_train_loss": {"cond": round(float(np.mean(losses_c[-500:])), 5),
                             "fixed_single": round(float(np.mean(losses_f[-300:])), 5)},
        "headline": {
            "A_sigma0.05": {
                "far_err_share_pct": A["by_sigma"]["0.05"]["far_err_share_pct"],
                "far_space_share_pct": A["by_sigma"]["0.05"]["far_space_share_pct"],
                "train_samples_in_far_pct": A["by_sigma"]["0.05"]["train_sample_far_share_pct"],
                "far_pct_rel_err_gt_1": A["by_sigma"]["0.05"]["far_pct_rel_err_gt_1"],
                "near_pct_rel_err_gt_1": A["by_sigma"]["0.05"]["near_pct_rel_err_gt_1"],
            },
            "B_best_eta": B["best_eta"],
            "B_best_prop_l1": B["best_prop_l1"],
            "B_ref_blur": B["ref_blur"],
            "B_sigma_sweep": B["sigma_sweep"],
            "C_at_1000_calls": {"single": key["single"], "annealed": key["annealed"]},
            "C_curve": C["curve"],
            "C_tradeoff": C["tradeoff"],
            "C_annealed_variants_at_1000": C["annealed_variants_at_1000"],
            "D_empty_share_2d_vs_64d": [D["shell"][0]["empty_share_pct"],
                                        D["shell"][-1]["empty_share_pct"]],
            "D_curve_panels": D["curve_sigma_panels"],
        },
        "exp_A": A, "exp_B": B, "exp_D": D,
        "runtime_sec": round(time.time() - t0, 1),
    }
    (ROOT / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    plot_A(A, ROOT / "A-score-field-quality.png")
    plot_B(B, ROOT / "B-single-level-failures.png", net_fixed, B["best_eta"])
    plot_C(C, ROOT / "C-budget-showdown.png")
    plot_D(D, ROOT / "D-manifold-panel.png", curve_nets, [0.05, 0.3, 1.2])
    print(f"saved results.json + 4 张图（{out['runtime_sec']}s）", flush=True)
    return C


def replot():
    """只重绘四张图：读 results.json + 载入 nets.npz（曲线面板网络现训）。"""
    t0 = time.time()
    res = json.loads((ROOT / "results.json").read_text())
    net_fixed = MLP(SEED + 2, din=2)
    net_fixed.load(ROOT / "nets.npz", "fixed")
    A, B, D = res["exp_A"], res["exp_B"], res["exp_D"]
    C = {"curve": res["headline"]["C_curve"], "tradeoff": res["headline"]["C_tradeoff"]}
    plot_A(A, ROOT / "A-score-field-quality.png")
    plot_B(B, ROOT / "B-single-level-failures.png", net_fixed, B["best_eta"])
    plot_C(C, ROOT / "C-budget-showdown.png")
    _, curve_nets = exp_D()
    plot_D(D, ROOT / "D-manifold-panel.png", curve_nets, [0.05, 0.3, 1.2])
    print(f"replotted 4 张图（{time.time()-t0:.0f}s）", flush=True)


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:
        replot()
    else:
        main()
