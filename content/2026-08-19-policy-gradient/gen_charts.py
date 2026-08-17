#!/usr/bin/env python3
"""03 / 04 脚本图：数字必须与 weixin.md 一致。"""
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


def _axes(fig_w=8.4, fig_h=5.4):
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


def fig_g():
    fig, ax = _axes()
    ax.text(5, 6.55, "两条轨迹，G 推了两笔", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")
    ax.text(5, 6.08, r"都从 $\pi($跑测试$)=0.70$ 起　　$\alpha=0.5$",
            ha="center", va="center", fontsize=11, color=MUTED)

    # red
    _box(ax, (0.55, 1.7), 4.2, 3.9, ec=RED, lw=1.8)
    ax.text(2.65, 5.15, "红　　G = 0", ha="center", fontsize=13, color=RED)
    ax.text(2.65, 4.15, "0.70", ha="center", fontsize=28, color=RED, fontweight="bold")
    ax.text(2.65, 3.25, r"$0 \times 0.30 = 0$", ha="center", fontsize=12, color=MUTED)
    ax.text(2.65, 2.45, "旋钮不动", ha="center", fontsize=13, color=INK)

    # green
    _box(ax, (5.25, 1.7), 4.2, 3.9, ec=GREEN, lw=1.8)
    ax.text(7.35, 5.15, "绿　　G = 1", ha="center", fontsize=13, color=GREEN)
    ax.text(7.35, 4.15, "0.73", ha="center", fontsize=28, color=GREEN, fontweight="bold")
    ax.text(7.35, 3.25, r"$0.847 + 0.15 = 0.997$", ha="center", fontsize=11, color=MUTED)
    ax.text(7.35, 2.45, r"$0.70 \rightarrow 0.73$", ha="center", fontsize=13, color=INK)

    _box(ax, (0.55, 0.3), 8.9, 1.1, fc="#F3E6D4", ec=AMBER)
    ax.text(5, 0.85, "赢的那条会教。输的那条沉默。",
            ha="center", va="center", fontsize=13, color=INK)
    fig.savefig(OUT / "03-g-two-episodes.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_delta():
    fig, ax = _axes(8.6, 5.8)
    ax.text(5, 6.55, "同一红绿：G 列 vs δ 列", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")
    ax.text(5, 6.08, r"$V(s_0)=0.50$　　都从 $0.70$ 起",
            ha="center", va="center", fontsize=11, color=MUTED)

    headers = [("用 G", 2.5), ("用 δ", 7.3)]
    for name, x in headers:
        ax.text(x, 5.45, name, ha="center", fontsize=13, color=INK, fontweight="bold")

    # G red
    _box(ax, (0.4, 3.15), 4.2, 1.95, ec=RED)
    ax.text(2.5, 4.6, "红  G = 0", ha="center", fontsize=12, color=RED)
    ax.text(2.5, 3.75, r"$0.70 \rightarrow 0.70$", ha="center", fontsize=16, color=RED, fontweight="bold")

    # G green
    _box(ax, (0.4, 1.0), 4.2, 1.95, ec=GREEN)
    ax.text(2.5, 2.45, "绿  G = 1", ha="center", fontsize=12, color=GREEN)
    ax.text(2.5, 1.6, r"$0.70 \rightarrow 0.73$", ha="center", fontsize=16, color=GREEN, fontweight="bold")

    # d red
    _box(ax, (5.2, 3.15), 4.4, 1.95, fc="#F6EEE8", ec=RED, lw=1.8)
    ax.text(7.4, 4.6, r"红  $\delta = -0.50$", ha="center", fontsize=12, color=RED)
    ax.text(7.4, 3.75, r"$0.70 \rightarrow 0.68$", ha="center", fontsize=16, color=RED, fontweight="bold")

    # d green
    _box(ax, (5.2, 1.0), 4.4, 1.95, fc="#EDF4EE", ec=GREEN, lw=1.8)
    ax.text(7.4, 2.45, r"绿  $\delta = +0.50$", ha="center", fontsize=12, color=GREEN)
    ax.text(7.4, 1.6, r"$0.70 \rightarrow 0.72$", ha="center", fontsize=16, color=GREEN, fontweight="bold")

    _box(ax, (0.4, 0.18), 9.2, 0.65, fc="#F3E6D4", ec=AMBER)
    ax.text(5, 0.5, "绿还是往上。红终于会往下。",
            ha="center", va="center", fontsize=12, color=INK)
    fig.savefig(OUT / "04-delta-vs-g.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_multiply():
    fig, ax = _axes(8.6, 5.5)
    ax.text(5, 6.5, "走完再乘回去", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")

    # path nodes
    xs = [1.6, 4.4, 8.0]
    labs = ["跑测试", "再看一眼", "手里的分数"]
    fcs = [CARD, CARD, "#F3E6D4"]
    ecs = [INK, INK, AMBER]
    for x, lab, fc, ec in zip(xs, labs, fcs, ecs):
        _box(ax, (x - 1.15, 2.55), 2.3, 1.7, fc=fc, ec=ec, lw=1.8)
        ax.text(x, 3.4, lab, ha="center", va="center", fontsize=13, color=INK)

    ax.annotate("", xy=(3.2, 3.4), xytext=(2.8, 3.4),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.5))
    ax.annotate("", xy=(6.8, 3.4), xytext=(5.6, 3.4),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.5))

    # back arrows
    ax.annotate("", xy=(1.6, 2.5), xytext=(7.4, 2.5),
                arrowprops=dict(arrowstyle="-|>", color=AMBER, lw=1.6,
                                connectionstyle="arc3,rad=-0.28"))
    ax.annotate("", xy=(4.4, 2.5), xytext=(7.6, 2.5),
                arrowprops=dict(arrowstyle="-|>", color=AMBER, lw=1.6,
                                connectionstyle="arc3,rad=-0.18"))
    ax.text(4.6, 1.55, "乘回去", ha="center", fontsize=12, color=AMBER)

    _box(ax, (0.7, 0.28), 8.6, 0.95, fc="#F3E6D4", ec=AMBER)
    ax.text(5, 0.75, "分数乘到走过的动作上",
            ha="center", va="center", fontsize=13, color=INK)
    fig.savefig(OUT / "02-multiply-g-back.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_multiply()
    fig_g()
    fig_delta()
    print("wrote", OUT / "02-multiply-g-back.png",
          OUT / "03-g-two-episodes.png", OUT / "04-delta-vs-g.png")
