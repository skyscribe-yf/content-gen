#!/usr/bin/env python3
"""MASA 篇自测实验（数字只走脚本轨）。

跑法：/home/skyscribe/.venvs/content-gen-charts/bin/python masa_scan.py
（venv 在 ~/.venvs/content-gen-charts，含 numpy + matplotlib；pypi 默认 CDN 下不动，需 -i 清华镜像）

A. 两列反例复刻：质量差 66 倍 vs 相对矩阵乘积误差 98% / 3%
B. 块粒度方向扫描：注意力质量排序 vs 矩阵逼近打分，value 方向从一致到互相抵消
   两个变体：global（所有块同享离散度）/ top（只有质量最大的块抵消）

口径（与 MASA 论文一致）：单 query 行 y = Σ_j a_j x_j，稀疏单元 = 块，
相对误差 = ||y - Σ_{j∈S} a_j x_j|| / ||y||。
MASA 单元打分（论文 §3.2 Eq.7/8）：s(u) = 2<y, C_u> - ||C_u||^2，C_u = (M_u ⊙ A)X。
"""
import json
import math

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for _c in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"):
    try:
        font_manager.fontManager.addfont(_c)
    except Exception:
        pass
plt.rcParams["font.family"] = font_manager.FontProperties(
    fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc").get_name()
plt.rcParams["axes.unicode_minus"] = False

INK, BLUE, RED, GOLD, GREY = "#1b1b1f", "#0F4C81", "#c0392b", "#E8A317", "#8a8a93"


# ---------------------------------------------------------------- A 两列反例
def two_column_counterexample():
    """按论文 Fig.1 口径自造两列例子：质量差 66 倍，预算 1 列。

    x1 = δ·u（范数极小，sink 型），x2 = ρ·v，两方向夹角 θ。
    由 err(u1)=98%、err(u2)=3% 反解得 cosθ≈0.658、ρ/δ≈2158。
    """
    cos_theta, rho_over_delta = 0.658, 2158.0
    theta = math.acos(cos_theta)
    a1, a2, delta, rho = 0.66, 0.01, 1.0, rho_over_delta
    u = np.array([1.0, 0.0])
    v = np.array([math.cos(theta), math.sin(theta)])
    x1, x2 = delta * u, rho * v
    y = a1 * x1 + a2 * x2
    err = lambda sub: float(np.linalg.norm(y - sub) / np.linalg.norm(y))
    s = lambda a, x: float(2 * a * np.dot(y, x) - a * a * np.dot(x, x))
    return dict(mass_ratio=a1 / a2, norm_ratio=rho / delta, cos_theta=cos_theta,
                err_mass_pct=round(err(a1 * x1) * 100, 2),
                err_masa_pct=round(err(a2 * x2) * 100, 2),
                masa_picks_u2=bool(s(a2, x2) > s(a1, x1)),
                s_mass_pick=round(s(a1, x1), 6), s_masa_pick=round(s(a2, x2), 6))


# ------------------------------------------------------------ B 块粒度方向扫描
def draw(rng, B=16, m=16, d=64, flips=None, alpha=2.0, jitter=0.15):
    """块内 value 范数全为 1（剥掉范数因子，只留方向）。flips[b] = 该块列方向被翻转的概率，
    0.5 时块内近似完全抵消。每列还叠一个小抖动 jitter，避免退化。"""
    N = B * m
    w = (rng.random(B) + 1e-9) ** (-alpha)
    block_mass = w / w.sum()
    u = rng.random((B, m)) + 0.3
    a = (block_mass[:, None] * u / u.sum(axis=1, keepdims=True)).reshape(N)
    p = np.asarray(flips)[:, None].repeat(m, axis=1).reshape(N)
    sign = np.where(rng.random(N) < p, -1.0, 1.0)
    phi = rng.normal(0.0, jitter, size=N)
    nu = rng.normal(0.0, 1.0, size=(N, d)); nu[:, 0] = 0.0
    nu /= np.linalg.norm(nu, axis=1, keepdims=True)
    e0 = np.zeros(d); e0[0] = 1.0
    X = sign[:, None] * np.cos(phi)[:, None] * e0 + np.sin(phi)[:, None] * nu
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    return a.reshape(B, m), X.reshape(B, m, d), block_mass


def scan(kappas, mode="top", B=16, m=16, d=64, R=400, seed=0, alpha=2.0, K=1):
    """kappas 此处是翻转比例 f：0 = 块内方向一致，0.5 = 块内互相抵消。"""
    out = {"kappas": list(map(float, kappas)), "mass": [], "masa": [], "corr": [],
           "top_pick_pct": []}
    for f in kappas:
        em, ea, cor, hit = [], [], [], 0
        for r in range(R):
            rng = np.random.default_rng(seed * 100003 + r)
            if mode == "top":
                w = (rng.random(B) + 1e-9) ** (-alpha)
                flips = np.zeros(B); flips[int(np.argmax(w))] = f
                rng = np.random.default_rng(seed * 100003 + r)   # 同一路随机数
            else:
                flips = np.full(B, f)
            a, X, bmass = draw(rng, B, m, d, flips, alpha)
            C = np.einsum("bm,bmd->bd", a, X)
            y = C.sum(axis=0)
            nm = np.linalg.norm(C, axis=1)
            score = 2 * C @ y - nm ** 2
            err = lambda S: float(np.linalg.norm(y - C[S].sum(axis=0)) / np.linalg.norm(y))
            Sm = np.argsort(-bmass)[:K]; SM = np.argsort(-score)[:K]
            em.append(err(Sm)); ea.append(err(SM))
            cor.append(float(np.corrcoef(bmass, nm)[0, 1]))
            hit += int(set(Sm) == set(np.argsort(-nm)[:K]))
        out["mass"].append(round(100 * float(np.mean(em)), 2))
        out["masa"].append(round(100 * float(np.mean(ea)), 2))
        out["corr"].append(round(float(np.mean(cor)), 3))
        out["top_pick_pct"].append(round(100.0 * hit / R, 1))
    return out


def fig(res, path="02-direction-scan.png", title="同一预算下，换一个排序分数"):
    fig, ax = plt.subplots(figsize=(9.6, 4.9), dpi=200)
    x = res["kappas"]
    ax.plot(x, res["mass"], "-o", color=RED, lw=2.8, ms=6, zorder=4,
            label="按注意力质量挑（现有方法）")
    ax.plot(x, res["masa"], "-^", color=BLUE, lw=2.8, ms=6, zorder=4,
            label="按矩阵逼近打分挑（MASA）")
    for key, color in (("mass", RED), ("masa", BLUE)):
        v = res[key][-1]
        ax.text(x[-1] + 0.03, v, f"{v:.0f}%", color=color, fontsize=16,
                weight="bold", va="center")
    ax.set_xlabel("块内 value 方向翻转比例 $f$（0 ＝ 方向一致，0.5 ＝ 完全互相抵消）",
                  fontsize=13)
    ax.set_ylabel("相对矩阵乘积误差", fontsize=13)
    ax.set_xlim(min(x) - 0.02, max(x) + 0.10)
    ax.set_ylim(0, max(max(res["mass"]), max(res["masa"])) * 1.25)
    ax.grid(axis="y", ls=":", color=GREY, alpha=0.45, zorder=0)
    ax.legend(frameon=False, fontsize=13, loc="upper left")
    ax.set_title(title, fontsize=16, weight="bold", color=INK, pad=12)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    print(f"[fig] {path}")


if __name__ == "__main__":
    print("== A 两列反例 ==")
    print(json.dumps(two_column_counterexample(), ensure_ascii=False, indent=2))
    kappas = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    runs = [("global", 1, None), ("top", 1, "02-direction-scan.png"),
            ("top", 4, None)]
    for mode, K, png in runs:
        print(f"== B 方向扫描（mode={mode}, 预算 K={K}/16 块）==")
        res = scan(kappas, mode=mode, K=K)
        for k, m, a, c, h in zip(res["kappas"], res["mass"], res["masa"],
                                 res["corr"], res["top_pick_pct"]):
            print(f"  f={k:<5} mass={m:6.1f}%  MASA={a:6.1f}%   "
                  f"corr(质量,‖贡献‖)={c:+.3f}   选中集合=贡献最大的 K 块：{h:5.1f}%")
        if png:
            fig(res, path=png, title="质量最大的那块，方向越抵消，排序错得越狠")


def fig_counterexample(path="01-66x-98.png"):
    """第三节配图：两列反例——质量 66× vs 1×，误差 98% vs 3%。"""
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2), dpi=200)
    groups = ["第一列\n(分数大、产出小)", "第二列\n(分数小、产出大)"]
    mass = [66.0, 1.0]
    err = [98.0, 3.0]
    for ax, vals, title, fmt in ((axes[0], mass, "注意力分数（相对值）", "{:.0f}×"),
                                 (axes[1], err, "相对矩阵乘积误差", "{:.0f}%")):
        bars = ax.bar(groups, vals, width=0.44, color=[RED, BLUE], zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.04,
                    fmt.format(v), ha="center", va="bottom", fontsize=19,
                    weight="bold", color=INK)
        ax.set_title(title, fontsize=14.5, weight="bold", color=INK, pad=10)
        ax.set_ylim(0, max(vals) * 1.28)
        ax.grid(axis="y", ls=":", color=GREY, alpha=0.45, zorder=0)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].annotate("现有方法挑这列", xy=(0, 66), xytext=(0.02, 78),
                     ha="center", fontsize=11.5, color=RED)
    axes[1].annotate("矩阵逼近挑这列", xy=(1, 3), xytext=(1, 34),
                     ha="center", fontsize=11.5, color=BLUE)
    fig.suptitle("质量高 66 倍的那列，反而丢掉 98% 的输出", fontsize=16,
                 weight="bold", color=INK, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, facecolor="white")
    print(f"[fig] {path}")


fig_counterexample()
