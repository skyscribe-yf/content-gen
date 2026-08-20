#!/usr/bin/env python3
"""03 / 04 脚本图：数字必须与 weixin.md 一致。

03-same-step-two-fates.png: 同一 Δμ=0.1，窄方向 KL=0.5 vs 宽方向 KL=0.00005（10000 倍）
04-trust-region-step.png:  δ=0.01 时允许步长 0.014 vs 1.41（100 倍）
"""
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


def fig_same_step():
    """同一 Δμ=0.1：窄方向 KL=0.5 vs 宽方向 KL=0.00005"""
    fig, ax = _axes(8.6, 5.8)
    ax.text(5, 6.55, "同一 0.1，两种命运", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")
    ax.text(5, 6.08, r"$\Delta\mu = 0.1$　　同一个椭圆云 $\Sigma=\mathrm{diag}(0.01,\,100)$",
            ha="center", va="center", fontsize=11, color=MUTED)

    # 窄方向（改行数）
    _box(ax, (0.4, 3.15), 4.2, 2.5, ec=RED, lw=1.8)
    ax.text(2.5, 5.15, "窄方向（改行数）", ha="center", fontsize=12, color=RED)
    ax.text(2.5, 4.15, r"$\mathrm{KL} = \frac{1}{2}\cdot\frac{0.1^2}{0.01} = 0.5$",
            ha="center", fontsize=13, color=INK)
    ax.text(2.5, 3.45, "翻天覆地", ha="center", fontsize=13, color=RED, fontweight="bold")

    # 宽方向（测试时长）
    _box(ax, (5.2, 3.15), 4.4, 2.5, ec=GREEN, lw=1.8)
    ax.text(7.4, 5.15, "宽方向（测试时长）", ha="center", fontsize=12, color=GREEN)
    ax.text(7.4, 4.15, r"$\mathrm{KL} = \frac{1}{2}\cdot\frac{0.1^2}{100} = 0.00005$",
            ha="center", fontsize=13, color=INK)
    ax.text(7.4, 3.45, "几乎无感", ha="center", fontsize=13, color=GREEN, fontweight="bold")

    _box(ax, (0.4, 0.18), 9.2, 0.65, fc="#F3E6D4", ec=AMBER)
    ax.text(5, 0.5, "同一 0.1，差 10000 倍。欧氏尺子失灵。",
            ha="center", va="center", fontsize=12, color=INK)
    fig.savefig(OUT / "03-same-step-two-fates.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_trust_region():
    """δ=0.01 时允许步长：窄方向 0.014 vs 宽方向 1.41（100 倍）"""
    fig, ax = _axes(8.6, 5.8)
    ax.text(5, 6.55, "KL 上限 δ=0.01：一次能拧多大", ha="center", va="center",
            fontsize=16, color=INK, fontweight="bold")
    ax.text(5, 6.08, r"允许步长 $\Delta\mu = \sqrt{2\delta\Sigma}$",
            ha="center", va="center", fontsize=11, color=MUTED)

    # 窄方向
    _box(ax, (0.4, 3.15), 4.2, 2.5, ec=RED, lw=1.8)
    ax.text(2.5, 5.15, "窄方向（Σ=0.01）", ha="center", fontsize=12, color=RED)
    ax.text(2.5, 4.15, r"$\sqrt{2\times0.01\times0.01} = 0.014$",
            ha="center", fontsize=13, color=INK)
    ax.text(2.5, 3.45, "只能挪一点点", ha="center", fontsize=13, color=RED, fontweight="bold")

    # 宽方向
    _box(ax, (5.2, 3.15), 4.4, 2.5, ec=GREEN, lw=1.8)
    ax.text(7.4, 5.15, "宽方向（Σ=100）", ha="center", fontsize=12, color=GREEN)
    ax.text(7.4, 4.15, r"$\sqrt{2\times0.01\times100} = 1.41$",
            ha="center", fontsize=13, color=INK)
    ax.text(7.4, 3.45, "可以大步走", ha="center", fontsize=13, color=GREEN, fontweight="bold")

    _box(ax, (0.4, 0.18), 9.2, 0.65, fc="#F3E6D4", ec=AMBER)
    ax.text(5, 0.5, "允许步长差 100 倍——这就是「一次能拧多大」的答案。",
            ha="center", va="center", fontsize=12, color=INK)
    fig.savefig(OUT / "04-trust-region-step.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_same_step()
    fig_trust_region()
    print("wrote", OUT / "03-same-step-two-fates.png",
          OUT / "04-trust-region-step.png")
