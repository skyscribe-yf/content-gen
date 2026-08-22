#!/usr/bin/env python3
"""01 / 04 脚本图：数字必须与 weixin.md 一致（2026-08-21 蒙特卡洛验证）。

01-ordinary-gradient.png: 普通梯度 η=0.1 一步 (0.1, 0.1) → 窄方向 KL=0.5 = 预算 δ=0.01 的 50 倍
04-closed-form-step.png:  TRPO 一步 (0.00014, 1.414) → 窄方向 1%、宽方向恰踩满 1.41 上限
"""
import os
from pathlib import Path

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

# 椭圆云参数（与正文一致）：Σ=diag(0.01, 100)，窄=改行数，宽=测试时长
DELTA = 0.01
ALLOW_NARROW = (2 * DELTA * 0.01) ** 0.5   # 0.0141
ALLOW_WIDE = (2 * DELTA * 100.0) ** 0.5    # 1.4142


def _setup(fig_w=8.8, fig_h=5.8):
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=160, facecolor=BG)
    ax.set_facecolor(BG)
    return fig, ax


def _budget_band(ax, x0, w, y_bottom, y_top, color=GREEN, label=""):
    """绿色预算区间带（KL≤δ 允许范围）。"""
    from matplotlib.patches import Rectangle

    ax.add_patch(Rectangle((x0, y_bottom), w, y_top - y_bottom,
                           facecolor=color, alpha=0.15, edgecolor=color, lw=1.2))
    if label:
        ax.text(x0 + w / 2, y_top + 0.22, label, ha="center", va="bottom",
                fontsize=9.5, color=color)


def _panel(ax, title, xlim, ylim=(0, 4.2), pos=None):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    ax.text((xlim[0] + xlim[1]) / 2, ylim[1] - 0.35, title, ha="center",
            fontsize=12.5, color=INK, fontweight="bold")
    # 中轴线
    ax.plot([xlim[0], xlim[1]], [2.0, 2.0], color=MUTED, lw=1.0, zorder=1)
    ax.text(xlim[0], 1.72, "旧策略", ha="left", fontsize=8.5, color=MUTED)
    return ax


def _arrow(ax, x0, x1, y=2.0, color=RED, lw=2.6):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw), zorder=4)


def fig_ordinary_gradient():
    """普通梯度 η=0.1：窄方向踩爆预算（KL=0.5=50 倍），宽方向几乎没动。"""
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 5.4), dpi=160, facecolor=BG)
    for a in axes:
        a.set_facecolor(BG)

    fig.suptitle("普通梯度：一个学习率走所有方向", fontsize=15, color=INK, fontweight="bold", y=0.99)
    fig.text(0.5, 0.925, r"$\eta=0.1$，梯度 $g=[1,1]$ → 两个方向各走 $0.1$",
             ha="center", fontsize=10.5, color=MUTED)

    # ---- 左：窄方向（改行数）----
    ax1 = axes[0]
    _panel(ax1, "改行数（窄方向）", (-0.16, 0.26))
    _budget_band(ax1, -ALLOW_NARROW, 2 * ALLOW_NARROW, 0.6, 3.4,
                 label=f"预算区间 $\\pm{ALLOW_NARROW:.3f}$")
    _arrow(ax1, 0.0, 0.1, color=RED, lw=3.0)
    ax1.scatter([0.1], [2.0], s=40, color=RED, zorder=5)
    ax1.text(0.105, 2.3, "$0.1$", fontsize=10.5, color=RED, fontweight="bold")
    ax1.text(0.105, 1.62, "步长超出上限 7 倍", fontsize=9, color=RED)
    ax1.text(-0.155, 0.42, r"$\mathrm{KL}\approx0.5$", fontsize=12, color=RED, fontweight="bold")
    ax1.text(-0.155, 0.05, "预算 δ=0.01 的 50 倍", fontsize=10, color=RED)

    # ---- 右：宽方向 ----
    ax2 = axes[1]
    _panel(ax2, "测试时长（宽方向）", (-0.45, 0.45))
    _budget_band(ax2, -ALLOW_WIDE, 2 * ALLOW_WIDE, 0.6, 2.0, label="允许区间 ±1.41")
    _arrow(ax2, 0.0, 0.1, color=GREEN, lw=3.0)
    ax2.scatter([0.1], [2.0], s=40, color=GREEN, zorder=5)
    ax2.text(0.115, 2.5, "$0.1$", fontsize=10.5, color=GREEN, fontweight="bold")
    ax2.text(0.0, 1.62, "远在允许区间内", fontsize=9, color=GREEN)
    ax2.text(-0.42, 0.42, r"$\mathrm{KL}=0.00005$", fontsize=12, color=GREEN, fontweight="bold")
    ax2.text(-0.42, 0.05, "几乎无感", fontsize=10, color=GREEN)

    fig.text(0.5, 0.12, "窄方向一脚踩爆预算 → 昨天会的，今天忘了",
             ha="center", fontsize=12, color=RED, fontweight="bold")
    fig.tight_layout(rect=(0, 0.15, 1, 0.9))
    fig.savefig(OUT / "01-ordinary-gradient.png", bbox_inches="tight")
    plt.close(fig)


def fig_closed_form():
    """TRPO：窄方向 0.00014（1%），宽方向 1.414（恰好踩满），KL 恰为 δ。"""
    fig, ax = plt.subplots(1, 2, figsize=(8.8, 5.4), dpi=160, facecolor=BG)
    for a in ax:
        a.set_facecolor(BG)

    fig.suptitle("TRPO：步长由云的形状自动分配", fontsize=15, color=INK, fontweight="bold", y=0.99)
    fig.text(0.5, 0.925, r"同一梯度 $g=[1,1]$，闭式解一步 → $(0.00014,\,1.414)$",
             ha="center", fontsize=10.5, color=MUTED)

    # ---- 左：窄方向 ----
    ax1 = ax[0]
    _panel(ax1, "改行数（窄方向）", (-0.05, 0.06))
    _budget_band(ax1, -ALLOW_NARROW, 2 * ALLOW_NARROW, 0.6, 3.4,
                label="允许 ±0.014")
    _arrow(ax1, 0.0, 0.00014, color=GREEN, lw=2.0)
    ax1.scatter([0.00014], [2.0], s=30, color=GREEN, zorder=5)
    ax1.text(0.00014 + 0.001, 2.3, "$0.00014$", fontsize=10, color=GREEN, fontweight="bold")
    ax1.text(0.00014 + 0.001, 1.6, "只用掉上限 1%", fontsize=9.5, color=GREEN)
    ax1.text(-0.048, 0.42, "基本没动", fontsize=11.5, color=GREEN, fontweight="bold")

    # ---- 右：宽方向 ----
    ax2 = ax[1]
    _panel(ax2, "测试时长（宽方向）", (-1.9, 1.9))
    _budget_band(ax2, -ALLOW_WIDE, 2 * ALLOW_WIDE, 0.6, 3.4,
                label="允许 ±1.41")
    _arrow(ax2, 0.0, ALLOW_WIDE, color=GREEN, lw=3.0)
    ax2.scatter([ALLOW_WIDE], [2.0], s=40, color=GREEN, zorder=5)
    ax2.text(ALLOW_WIDE - 0.05, 2.3, "$1.414$", fontsize=10.5, color=GREEN, fontweight="bold")
    ax2.text(ALLOW_WIDE - 0.35, 1.6, "恰好踩上 1.41 上限", fontsize=9.5, color=GREEN)
    ax2.text(-1.85, 0.2, r"$\mathrm{KL}=0.01=\delta$，一分不差", fontsize=11.5, color=GREEN, fontweight="bold")

    fig.text(0.5, 0.12, "同一份梯度：普通更新器踩爆 50 倍，TRPO 一步不差",
             ha="center", fontsize=12, color=GREEN, fontweight="bold")
    fig.tight_layout(rect=(0, 0.15, 1, 0.9))
    fig.savefig(OUT / "04-closed-form-step.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_ordinary_gradient()
    fig_closed_form()
    print("生成 01 / 04 脚本图")
