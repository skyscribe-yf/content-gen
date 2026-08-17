#!/usr/bin/env python3
"""03 / 04 脚本图：数字必须与 weixin.md 一致。"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

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


def _axes(fig_w=8.4, fig_h=5.4):
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=160, facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    return fig, ax


def _box(ax, xy, w, h, fc=CARD, ec=INK, lw=1.4, r=0.18):
    p = FancyBboxPatch(
        xy, w, h, boxstyle=f"round,pad=0.02,rounding_size={r}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2,
    )
    ax.add_patch(p)
    return p


def fig_td():
    fig, ax = _axes()
    ax.text(5, 6.55, "两步 TD：样本在推着改账", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")
    ax.text(5, 6.05, r"$V(s_0)$    $\gamma=0.9$    $\alpha=0.5$",
            ha="center", va="center", fontsize=11, color=MUTED)

    xs = [1.6, 5.0, 8.4]
    vals = [0.50, 0.34, 0.67]
    labels = ["起步", "第一次：测试红", "第二次：测试绿"]
    details = [r"瞎估 $V=0.50$", r"$R=0$，$\delta=-0.32$", r"$R=+1$，$\delta=0.66$"]
    colors = [INK, RED, GREEN]

    for x, v, lab, det, c in zip(xs, vals, labels, details, colors):
        _box(ax, (x - 1.25, 2.15), 2.5, 3.15, ec=c, lw=1.8)
        ax.text(x, 4.85, lab, ha="center", va="center", fontsize=11, color=c)
        ax.text(x, 3.85, f"{v:.2f}", ha="center", va="center",
                fontsize=26, color=c, fontweight="bold")
        ax.text(x, 2.75, det, ha="center", va="center", fontsize=10, color=MUTED)

    ax.annotate("", xy=(3.65, 3.7), xytext=(2.95, 3.7),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.8))
    ax.annotate("", xy=(7.05, 3.7), xytext=(6.35, 3.7),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.8))

    _box(ax, (1.1, 0.35), 7.8, 1.15, fc="#F3E6D4", ec=AMBER)
    ax.text(5, 0.92, r"$0.50 \rightarrow 0.34 \rightarrow 0.67$　　先被红单拉低，再被绿单拉高",
            ha="center", va="center", fontsize=12, color=INK)
    fig.savefig(OUT / "03-td-two-updates.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_q():
    fig, ax = _axes(8.6, 5.6)
    ax.text(5, 6.55, "Q-learning：下一步取最大，不取实际动作",
            ha="center", va="center", fontsize=15, color=INK, fontweight="bold")
    ax.text(5, 6.08, r"红状态两个动作　　$\gamma=0.9$",
            ha="center", va="center", fontsize=11, color=MUTED)

    _box(ax, (0.55, 2.55), 3.5, 3.05, ec=INK)
    ax.text(2.3, 5.2, "到了红以后", ha="center", fontsize=12, color=INK)
    ax.text(2.3, 4.35, "重写  $Q=0.40$", ha="center", fontsize=13, color=GREEN)
    ax.text(2.3, 3.55, "回退  $Q=0.10$", ha="center", fontsize=13, color=MUTED)
    ax.text(2.3, 2.9, "实际也许会走回退", ha="center", fontsize=10, color=MUTED)

    _box(ax, (4.7, 3.55), 4.6, 2.05, fc="#EDF4EE", ec=GREEN, lw=1.8)
    ax.text(7.0, 5.1, "Q-learning 用", ha="center", fontsize=12, color=GREEN)
    ax.text(7.0, 4.4, r"$\max(0.40,\ 0.10)=0.40$", ha="center",
            fontsize=15, color=GREEN, fontweight="bold")

    _box(ax, (4.7, 1.35), 4.6, 1.85, fc="#F6EEE8", ec=RED)
    ax.text(7.0, 2.75, "若按实际动作（SARSA）", ha="center", fontsize=11, color=RED)
    ax.text(7.0, 2.05, r"$Q($回退$)=0.10$", ha="center",
            fontsize=14, color=RED, fontweight="bold")

    ax.annotate("", xy=(4.7, 4.55), xytext=(4.05, 4.35),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.6))
    ax.annotate("", xy=(4.7, 2.3), xytext=(4.05, 3.2),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.4))

    _box(ax, (0.55, 0.3), 8.75, 0.85, fc="#F3E6D4", ec=AMBER)
    ax.text(5, 0.72, "按最好的那招记账，不按当时心情",
            ha="center", va="center", fontsize=12, color=INK)
    fig.savefig(OUT / "04-q-max.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_td()
    fig_q()
    print("wrote", OUT / "03-td-two-updates.png", OUT / "04-q-max.png")
