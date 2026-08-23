#!/usr/bin/env python3
"""GAE 篇脚本图：数字必须与 weixin.md 一致（2026-08-24 蒙特卡洛实测）。

01-eff-horizon.png:  (γλ)^l 权重衰减曲线 λ=0.95 (0.9405^l) vs λ=1 (0.99^l)，
                     标注 20 步处 29% vs 82%，有效视野 16.8 vs 100
02-lambda-sweep.png: λ 扫描方差曲线（实测 1.03/1.40/6.95/15.0/60.9/128.1）
                     标注 8.5×/91×/124× 反差 + 偏差线
"""
import os
from pathlib import Path

import numpy as np
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


def _prep_ax(ax, bg=BG):
    ax.set_facecolor(bg)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(colors=INK, labelsize=10.5)


def fig_eff_horizon():
    l = np.arange(0, 101)
    w95 = 0.9405 ** l
    w1 = 0.99 ** l

    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=160, facecolor=BG)
    _prep_ax(ax)

    ax.plot(l, w1, color=RED, lw=3.0, label="λ=1：权重 0.99$^l$（看全程）")
    ax.plot(l, w95, color=AMBER, lw=3.0, label="λ=0.95：权重 0.9405$^l$（近视）")

    # 20 步标注：29% vs 82%
    for x, y, lab, c in [(20, 0.99 ** 20, "20 步后\n还剩 82%", RED),
                         (20, 0.9405 ** 20, "20 步后\n还剩 29%", AMBER)]:
        ax.plot(x, y, "o", color=c, ms=9, zorder=5)
        ax.annotate(lab, xy=(x, y), xytext=(x + 2.5, y + 0.08),
                    fontsize=11.5, color=c, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=c, lw=1.6))

    # 有效视野标注
    ax.axvspan(0, 16.8, color=GREEN, alpha=0.08)
    ax.text(16.8, 0.97, "有效视野 16.8 步", ha="center", va="top",
            fontsize=12, color=GREEN, fontweight="bold")
    ax.axvline(16.8, color=GREEN, lw=2.0, ls=":")
    ax.text(62, 0.86, "λ=1 看全程：权重到 100 步仍有 37%", ha="center",
            fontsize=11, color=RED)

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("从当前步往后的第 l 步", fontsize=12, color=INK)
    ax.set_ylabel("这份功劳能传到的比例 $(γλ)^l$", fontsize=12, color=INK)
    ax.legend(loc="upper right", fontsize=10.5, framealpha=0.92, facecolor=CARD)
    ax.set_title("λ 只差 0.05：0.9405 的 20 步后只剩 29%，0.99 还剩 82%",
                 fontsize=13, color=INK, fontweight="bold", pad=10)

    fig.savefig(OUT / "01-eff-horizon.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_lambda_sweep():
    lams = np.array([0.0, 0.5, 0.9, 0.95, 0.99, 1.0])
    var = np.array([1.03, 1.40, 6.95, 15.0, 60.9, 128.1])
    bias = np.array([0.003, -0.004, -0.048, -0.094, -0.255, -0.392])
    err = np.array([0.002, 0.002, 0.005, 0.01, 0.05, 0.1])

    fig, ax1 = plt.subplots(figsize=(8.8, 5.2), dpi=160, facecolor=BG)
    _prep_ax(ax1)

    ax1.plot(lams, var, color=RED, lw=3.0, marker="o", ms=7, label="方差（左读，log 轴）")
    ax1.set_yscale("log")
    ax1.set_ylim(0.8, 400)
    ax1.set_xlim(-0.03, 1.05)
    ax1.set_xlabel("λ（衰减旋钮）", fontsize=12, color=INK)
    ax1.set_ylabel("优势估计的方差（log）", fontsize=12, color=INK)

    # 反差标注
    ax1.annotate("λ=0.5 → 1\n方差 ×91", xy=(1.0, 128.1), xytext=(0.72, 220),
                 fontsize=11.5, color=RED, fontweight="bold",
                 arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.8))
    ax1.annotate("λ=0.95 → 1\n只差 0.05，×8.5", xy=(1.0, 128.1), xytext=(0.62, 60),
                 fontsize=11.5, color=RED, fontweight="bold",
                 arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.8))

    # 偏差线（次轴）
    ax2 = ax1.twinx()
    ax2.set_facecolor(BG)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    ax2.plot(lams, bias, color=GREEN, lw=2.2, marker="s", ms=6, ls="--",
             label="偏差（critic 误差进账）")
    ax2.set_ylabel("偏差（期望误差）", fontsize=12, color=GREEN)
    ax2.set_ylim(-0.45, 0.05)
    ax2.tick_params(colors=GREEN, labelsize=10)
    ax2.axhline(0, color=MUTED, lw=1.0)

    # 值标注
    for x, y in zip(lams, var):
        ax1.annotate(f"{y:.1f}", xy=(x, y), xytext=(x - 0.01, y * 1.25),
                     fontsize=10, color=INK, ha="center")

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=10.5,
               framealpha=0.92, facecolor=CARD)
    ax1.set_title("λ 越大方差越炸：λ=1 是 λ=0.95 的 8.5 倍、λ=0.5 的 91 倍",
                  fontsize=13, color=INK, fontweight="bold", pad=10)

    fig.savefig(OUT / "02-lambda-sweep.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_eff_horizon()
    fig_lambda_sweep()
    print("done: 01-eff-horizon / 02-lambda-sweep 生成完毕")
    print("校验: 0.99^20 =", round(0.99 ** 20, 3), " 0.9405^20 =", round(0.9405 ** 20, 3))
