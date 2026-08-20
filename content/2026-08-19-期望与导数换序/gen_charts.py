#!/usr/bin/env python3
"""04-07 脚本图：数字必须与 weixin.md 正文一致（3.5 / 15.17 / 8 / 0.21）。"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

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


def _axes(fig_w=8.6, fig_h=5.6):
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=160, facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    return fig, ax


def _box(ax, xy, w, h, fc=CARD, ec=INK, lw=1.4, r=0.18):
    from matplotlib.patches import FancyBboxPatch

    p = FancyBboxPatch(
        xy, w, h, boxstyle=f"round,pad=0.02,rounding_size={r}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2,
    )
    ax.add_patch(p)
    return p


def fig_expectation():
    """04：骰子 E[X] vs E[X²]"""
    fig, ax = _axes()
    ax.text(5, 6.55, "骰子的两个加权平均", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")
    ax.text(5, 6.08, "每个点数权重 1/6，只有变换不同",
            ha="center", va="center", fontsize=11, color=MUTED)

    # left: E[X]
    _box(ax, (0.5, 1.9), 4.35, 3.7, ec=INK, lw=1.6)
    ax.text(2.67, 5.15, r"$E[X]$", ha="center", fontsize=15, color=MUTED)
    ax.text(2.67, 4.1, "3.5", ha="center", fontsize=34, color=INK, fontweight="bold")
    ax.text(2.67, 2.95, r"$1\times\frac{1}{6}+\cdots+6\times\frac{1}{6}$",
            ha="center", fontsize=12, color=MUTED)
    ax.text(2.67, 2.35, "变换：不变（取点数本身）",
            ha="center", fontsize=11, color=INK)

    # right: E[X^2]
    _box(ax, (5.15, 1.9), 4.35, 3.7, fc="#F3E6D4", ec=AMBER, lw=1.6)
    ax.text(7.32, 5.15, r"$E[X^2]$", ha="center", fontsize=15, color=AMBER)
    ax.text(7.32, 4.1, "15.17", ha="center", fontsize=34, color=AMBER, fontweight="bold")
    ax.text(7.32, 2.95, r"$1^2\times\frac{1}{6}+\cdots+6^2\times\frac{1}{6}$",
            ha="center", fontsize=12, color=MUTED)
    ax.text(7.32, 2.35, "变换：取平方", ha="center", fontsize=11, color=INK)

    _box(ax, (0.5, 0.3), 9.0, 1.0, fc="#F3E6D4", ec=AMBER)
    ax.text(5, 0.8, "变换不同，权重相同：期望 = 变换 × 概率权重，全加起来",
            ha="center", va="center", fontsize=12, color=INK)
    fig.savefig(OUT / "04-expectation.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_sum_integral():
    """05：离散求和 vs 连续积分"""
    fig, ax = _axes(8.8, 5.4)
    ax.text(5, 6.5, "从离散到连续：求和变积分", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")

    # left: discrete bars (dice)
    ax.text(2.5, 5.8, "离散：加六块", ha="center", fontsize=13, color=INK, fontweight="bold")
    xs = [1.0, 1.7, 2.4, 3.1, 3.8, 4.5]
    for i, x in enumerate(xs):
        ax.add_patch(plt.Rectangle((x - 0.27, 1.2), 0.54, 3.4, facecolor=CARD,
                                   edgecolor=INK, lw=1.4, zorder=2))
        ax.text(x, 4.75, str(i + 1), ha="center", fontsize=10, color=MUTED)
    ax.plot([0.7, 4.9], [1.2, 1.2], color=INK, lw=1.4, zorder=1)
    ax.text(2.8, 0.85, "概率都是 1/6", ha="center", fontsize=10, color=MUTED)

    # right: continuous curve
    ax.text(7.6, 5.8, "连续：整条曲线", ha="center", fontsize=13, color=INK, fontweight="bold")
    import numpy as np
    t = np.linspace(0.6, 4.9, 200)
    y = 2.1 * (1 - ((t - 2.75) / 1.5) ** 2) + 0.3
    ax.fill_between(t, 1.2, y, facecolor="#F3E6D4", edgecolor=AMBER, lw=1.6, zorder=2)
    ax.plot([0.6, 4.9], [1.2, 1.2], color=INK, lw=1.4, zorder=1)
    ax.scatter([2.75], [2.1 + 0.3], color=RED, s=26, zorder=4)
    ax.text(2.75, 4.0, "单点概率 = 0", ha="center", fontsize=11, color=RED)
    ax.annotate("", xy=(2.75, 3.75), xytext=(2.75, 2.6),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.3))
    ax.text(7.6, 0.85, "面积才是概率", ha="center", fontsize=10, color=MUTED)

    # arrow between
    ax.annotate("", xy=(5.3, 3.4), xytext=(5.05, 3.4),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=2))
    ax.text(5.2, 4.15, r"$\sum \rightarrow \int$", ha="center", fontsize=14, color=INK)

    _box(ax, (0.5, 0.14), 8.8, 0.55, fc="#F3E6D4", ec=AMBER)
    ax.text(4.9, 0.42, "单点概率为零，但附近有概率：面积说了算",
            ha="center", va="center", fontsize=11, color=INK)
    fig.savefig(OUT / "05-sum-to-integral.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_linearity():
    """06：E[2X+1] 两条路"""
    fig, ax = _axes()
    ax.text(5, 6.55, "线性性：两条路，同一个数", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")
    ax.text(5, 6.08, r"骰子  $E[2X+1]$", ha="center", va="center",
            fontsize=11, color=MUTED)

    # left: transform first
    _box(ax, (0.5, 1.8), 4.35, 3.9, ec=INK, lw=1.6)
    ax.text(2.67, 5.35, "先变换，后平均", ha="center", fontsize=13, color=INK, fontweight="bold")
    ax.text(2.67, 4.25, r"$3\times\frac{1}{6}+5\times\frac{1}{6}$", ha="center", fontsize=12, color=MUTED)
    ax.text(2.67, 3.6, r"$+\cdots+13\times\frac{1}{6}$", ha="center", fontsize=12, color=MUTED)
    ax.text(2.67, 2.6, "8", ha="center", fontsize=34, color=INK, fontweight="bold")
    ax.text(2.67, 2.0, "每个 2X+1 先算出来，再平均", ha="center", fontsize=10, color=MUTED)

    # right: average first
    _box(ax, (5.15, 1.8), 4.35, 3.9, fc="#F3E6D4", ec=AMBER, lw=1.6)
    ax.text(7.32, 5.35, "先平均，后变换", ha="center", fontsize=13, color=AMBER, fontweight="bold")
    ax.text(7.32, 4.25, r"$E[X] = 3.5$", ha="center", fontsize=14, color=MUTED)
    ax.text(7.32, 3.6, r"$2\times 3.5 + 1$", ha="center", fontsize=14, color=MUTED)
    ax.text(7.32, 2.6, "8", ha="center", fontsize=34, color=AMBER, fontweight="bold")
    ax.text(7.32, 2.0, "先平均，再套变换", ha="center", fontsize=10, color=MUTED)

    ax.text(5, 4.6, "=", ha="center", fontsize=28, color=GREEN, fontweight="bold")

    _box(ax, (0.5, 0.3), 9.0, 0.95, fc="#EDF4EE", ec=GREEN)
    ax.text(5, 0.78, r"$E[aX+b] = aE[X]+b$　　：线性性",
            ha="center", va="center", fontsize=13, color=INK)
    fig.savefig(OUT / "06-linearity.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_swap():
    """07：换序手算 0.21 = 0.21"""
    fig, ax = _axes()
    ax.text(5, 6.55, "换序手算：同一个数", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")
    ax.text(5, 6.08, "两个动作：跑测试 0.70，再改 0.30；绿 G=1，红 G=0",
            ha="center", va="center", fontsize=11, color=MUTED)

    # left: differentiate first
    _box(ax, (0.5, 1.7), 4.35, 4.0, ec=INK, lw=1.6)
    ax.text(2.67, 5.35, "先求导，后平均", ha="center", fontsize=13, color=INK, fontweight="bold")
    ax.text(2.67, 4.45, r"$\nabla_\theta E[G]=\nabla_\theta\pi$", ha="center", fontsize=13, color=MUTED)
    ax.text(2.67, 3.8, r"$=\pi(1-\pi)$", ha="center", fontsize=13, color=MUTED)
    ax.text(2.67, 3.15, r"$=0.70\times0.30$", ha="center", fontsize=13, color=MUTED)
    ax.text(2.67, 2.25, "0.21", ha="center", fontsize=34, color=INK, fontweight="bold")

    # right: average first
    _box(ax, (5.15, 1.7), 4.35, 4.0, fc="#F3E6D4", ec=AMBER, lw=1.6)
    ax.text(7.32, 5.35, "先平均，再求导", ha="center", fontsize=13, color=AMBER, fontweight="bold")
    ax.text(7.32, 4.45, r"$E[G\,\nabla_\theta\log\pi]$", ha="center", fontsize=13, color=MUTED)
    ax.text(7.32, 3.8, r"$=1\times0.70\times0.30$", ha="center", fontsize=13, color=MUTED)
    ax.text(7.32, 3.15, r"$+0\times(\cdots)$", ha="center", fontsize=13, color=MUTED)
    ax.text(7.32, 2.25, "0.21", ha="center", fontsize=34, color=AMBER, fontweight="bold")

    ax.text(5, 4.6, "=", ha="center", fontsize=28, color=GREEN, fontweight="bold")

    _box(ax, (0.5, 0.28), 9.0, 0.95, fc="#EDF4EE", ec=GREEN)
    ax.text(5, 0.76, r"$0.21 = 0.21$　　：离散、有限项，换序免费",
            ha="center", va="center", fontsize=13, color=INK)
    fig.savefig(OUT / "07-swap.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_expectation()
    fig_sum_integral()
    fig_linearity()
    fig_swap()
    print("wrote", OUT / "04-expectation.png",
          OUT / "05-sum-to-integral.png",
          OUT / "06-linearity.png", OUT / "07-swap.png")
