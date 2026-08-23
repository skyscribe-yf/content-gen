#!/usr/bin/env python3
"""PPO 数学篇脚本图：数字必须与 weixin.md 一致（2026-08-23 蒙特卡洛实测）。

01-kl-sweep.png:     ε=0.1/0.2/0.3 → KL 上界 0.006/0.025/0.064，横线 TRPO δ=0.01
02-clip-flatline.png: A>0 与 A<0 两条目标函数折线：区间 [0.8,1.2] 内斜面、区间外拍平
04-ratio-split.png:  KL=0.022 步长下 r 分布直方图，0.8/1.2 竖线，阴影 32.4% 被截断
"""
import os
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent
for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

BG = "#F7F3EB"
INK = "#2C2A26"
AMBER = "#D97706"
RED = "#C2410C"
GREEN = "#3F6F4A"
MUTED = "#8A8478"
CARD = "#FFFCF6"


def _prep_ax(ax, bg=BG):
    ax.set_facecolor(bg)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(colors=INK, labelsize=10.5)


def fig_kl_sweep():
    eps = np.linspace(0.04, 0.40, 400)
    exact = 0.5 * np.log(1 / (1 - eps)) ** 2          # 精确上界 ½(ln(1/(1-ε)))²
    approx = 0.5 * eps ** 2                           # 一阶近似 ½ε²

    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=160, facecolor=BG)
    _prep_ax(ax)

    ax.plot(eps, exact, color=AMBER, lw=3.0, label="精确上界 $\\frac{1}{2}(\\ln\\frac{1}{1-\\epsilon})^2$")
    ax.plot(eps, approx, color=MUTED, lw=1.8, ls="--", label="一阶近似 $\\frac{1}{2}\\epsilon^2$（低估）")

    # TRPO 预算横线
    ax.axhline(0.01, color=GREEN, lw=2.2, ls=":")
    ax.text(0.395, 0.0125, "TRPO 预算 $\\delta=0.01$", ha="right", va="bottom",
            fontsize=11.5, color=GREEN, fontweight="bold")

    # 标注点（与正文一致）
    pts = [(0.1, 0.0056, "0.1→0.006"), (0.2, 0.0249, "0.2→0.025"), (0.3, 0.0636, "0.3→0.064")]
    for x, y, lab in pts:
        ax.plot(x, y, "o", color=RED, ms=9, zorder=5)
        ax.annotate(lab, xy=(x, y), xytext=(x + 0.018, y + 0.0075),
                    fontsize=12, color=RED, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=RED, lw=1.6))

    # δ 区域
    ax.fill_between(eps, 0, 0.01, color=GREEN, alpha=0.08)

    ax.set_xlim(0.04, 0.40)
    ax.set_ylim(0, 0.085)
    ax.set_xlabel("clip 的 ε（比率截断上限）", fontsize=12, color=INK)
    ax.set_ylabel("每步隐含 KL 上界（nats）", fontsize=12, color=INK)
    ax.legend(loc="upper left", fontsize=10.5, framealpha=0.9, facecolor=CARD)
    ax.set_title("ε 每加一档，KL 上界翻一档：0.2 是 0.01 预算的 2.5 倍",
                 fontsize=13, color=INK, fontweight="bold", pad=10)

    fig.savefig(OUT / "01-kl-sweep.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_clip_flatline():
    r = np.linspace(0.35, 1.65, 800)
    a_pos = np.minimum(r * 1.0, np.clip(r, 0.8, 1.2) * 1.0)     # A=+1：涨过头封顶
    a_neg = np.minimum(r * -1.0, np.clip(r, 0.8, 1.2) * -1.0)   # A=−1：跌过头封顶

    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=160, facecolor=BG)
    _prep_ax(ax)

    ax.axvspan(0.8, 1.2, color=AMBER, alpha=0.10)
    ax.axvline(0.8, color=AMBER, lw=2.0, ls="-.")
    ax.axvline(1.2, color=AMBER, lw=2.0, ls="-.")

    ax.plot(r, a_pos, color=GREEN, lw=3.0, label="好员工 A>0：超额业绩封顶（右平）")
    ax.plot(r, a_neg, color=RED, lw=3.0, label="坏员工 A<0：摸鱼扣款封顶（左平）")

    ax.annotate("区间内：按实际算账", xy=(1.0, 1.0), xytext=(0.86, 1.42),
                fontsize=11.5, color=AMBER, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=AMBER, lw=1.8))
    ax.annotate("涨过头\n不记功", xy=(1.45, 1.20), xytext=(1.42, 1.55),
                fontsize=11.5, color=GREEN, fontweight="bold")
    ax.annotate("跌过头\n不记过", xy=(0.48, -0.80), xytext=(0.44, -1.28),
                fontsize=11.5, color=RED, fontweight="bold")

    ax.set_xlim(0.35, 1.65)
    ax.set_ylim(-1.65, 1.75)
    ax.set_xlabel("响应比 r（新策略/旧策略）", fontsize=12, color=INK)
    ax.set_ylabel("目标函数贡献 $\\min(rA,\\ clip(r)A)$", fontsize=12, color=INK)
    ax.legend(loc="upper center", fontsize=10.5, framealpha=0.92, facecolor=CARD, ncol=1)
    ax.set_title("min 的几何：区间内是斜面，区间外一半拍平",
                 fontsize=13, color=INK, fontweight="bold", pad=10)

    fig.savefig(OUT / "02-clip-flatline.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def mc_ratio_samples(seed=42, scale=0.2, n=400000):
    """逐字复现 2026-08-23 验证脚本的 RNG 顺序（delta、idx 交替绘制），
    scale=0.2 一轮：KL 真值 0.022487，采样口径 KL≈0.022。"""
    np.random.seed(seed)
    K = 500
    logits_old = np.random.randn(K) * 0.5
    p_old = np.exp(logits_old - logits_old.max())
    p_old /= p_old.sum()
    for s in [0.05, 0.1, scale]:
        delta = np.random.randn(K) * s
        logits_new = logits_old + delta
        p_new = np.exp(logits_new - logits_new.max())
        p_new /= p_new.sum()
        idx = np.random.choice(K, size=n, p=p_old)
    r = p_new[idx] / p_old[idx]
    return r, p_old, p_new


def fig_ratio_split():
    r, _, _ = mc_ratio_samples()
    frac_clip = float(np.mean((r < 0.8) | (r > 1.2)))

    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=160, facecolor=BG)
    _prep_ax(ax)

    ax.hist(r, bins=90, range=(0.1, 2.6), color=AMBER, alpha=0.55, edgecolor="none")
    for x0, x1 in [(0.1, 0.8), (1.2, 2.6)]:
        ax.axvspan(x0, x1, color=RED, alpha=0.13, hatch="//", edgecolor=RED, lw=0.0)

    ax.axvline(0.8, color=RED, lw=2.2, ls="--")
    ax.axvline(1.2, color=RED, lw=2.2, ls="--")
    ax.text(0.82, ax.get_ylim()[1] * 0.95, "0.8", color=RED, fontsize=12, fontweight="bold", va="top")
    ax.text(1.22, ax.get_ylim()[1] * 0.95, "1.2", color=RED, fontsize=12, fontweight="bold", va="top")

    ax.text(0.43, ax.get_ylim()[1] * 0.55, f"被拍平\n{frac_clip*100:.1f}%",
            ha="center", fontsize=13, color=RED, fontweight="bold")
    ax.text(1.00, ax.get_ylim()[1] * 0.38, f"区间内\n{(1-frac_clip)*100:.1f}% 照常算账",
            ha="center", fontsize=13, color=INK, fontweight="bold")

    ax.set_xlim(0.1, 2.6)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    ax.set_xlabel("响应比 r（同一个动作，新策略/旧策略）", fontsize=12, color=INK)
    ax.set_ylabel("样本占比", fontsize=12, color=INK)
    ax.set_title(f"KL≈0.022 的一步：ε=0.2 时 {frac_clip*100:.1f}% 的样本撞上限速牌",
                 fontsize=13, color=INK, fontweight="bold", pad=10)

    fig.savefig(OUT / "04-ratio-split.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)

    kl = None
    return frac_clip


if __name__ == "__main__":
    fig_kl_sweep()
    fig_clip_flatline()
    fc = fig_ratio_split()
    print(f"done: 01/02/04 生成完毕；截断比例实测 {fc*100:.1f}%（正文 32.4%）")
