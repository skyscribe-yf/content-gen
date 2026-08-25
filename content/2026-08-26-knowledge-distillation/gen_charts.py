#!/usr/bin/env python3
"""蒸馏篇脚本图：数字必须与 weixin.md 一致。

01-temp-softmax.png: T=1 vs T=3 三柱，0.981/0.010/0.010 对 0.700/0.150/0.150
02-grad-hard-soft.png: 硬标签 vs 软标签梯度 −0.010/+0.005/+0.005 对 +0.097/−0.048/−0.048（含 1/T=3）
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
BLUE = "#0F4C81"


def _prep_ax(ax):
    ax.set_facecolor(BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(colors=INK, labelsize=10.5)


def fig_temp_softmax():
    labels = ["改实现", "改断言", "改配置"]
    t1 = np.array([0.981, 0.010, 0.010])
    t3 = np.array([0.700, 0.150, 0.150])
    x = np.arange(len(labels))
    w = 0.36

    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=160, facecolor=BG)
    _prep_ax(ax)
    b1 = ax.bar(x - w / 2, t1, w, color=RED, label="T=1：0.981 / 0.010 / 0.010")
    b3 = ax.bar(x + w / 2, t3, w, color=AMBER, label="T=3：0.700 / 0.150 / 0.150")

    for bars, vals in ((b1, t1), (b3, t3)):
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + 0.02,
                f"{v:.3f}",
                ha="center",
                va="bottom",
                fontsize=11,
                color=INK,
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("每个选项的把握", fontsize=12, color=INK)
    ax.legend(loc="upper right", fontsize=10.5, framealpha=0.92, facecolor=CARD)
    ax.set_title("同一组 logits：T=1 几乎只剩标准解法，T=3 才露出 0.15",
                 fontsize=13, color=INK, fontweight="bold", pad=10)
    fig.savefig(OUT / "01-temp-softmax.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_grad():
    labels = ["改实现", "改断言", "改配置"]
    hard = np.array([-0.010, 0.005, 0.005])
    soft = np.array([0.097, -0.048, -0.048])
    x = np.arange(len(labels))
    w = 0.36

    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=160, facecolor=BG)
    _prep_ax(ax)
    ax.axhline(0, color=MUTED, lw=1.0)
    b1 = ax.bar(x - w / 2, hard, w, color=MUTED, label="硬标签：−0.010 / +0.005 / +0.005")
    b2 = ax.bar(x + w / 2, soft, w, color=AMBER, label="软标签（含 1/T=3）：+0.097 / −0.048 / −0.048")

    for bars, vals in ((b1, hard), (b2, soft)):
        for bar, v in zip(bars, vals):
            offset = 0.018 if v >= 0 else -0.018
            va = "bottom" if v >= 0 else "top"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + offset,
                f"{v:+.3f}",
                ha="center",
                va=va,
                fontsize=11,
                color=INK,
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylim(-0.10, 0.18)
    ax.set_ylabel("梯度 $p_S - p_T$", fontsize=12, color=INK)
    ax.legend(loc="upper right", fontsize=10.5, framealpha=0.92, facecolor=CARD)
    ax.set_title("学生已 0.99 抄死时：硬标签几乎停，软标签仍在推",
                 fontsize=13, color=INK, fontweight="bold", pad=10)
    fig.savefig(OUT / "02-grad-hard-soft.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_temp_softmax()
    fig_grad()
    print("done: 01-temp-softmax / 02-grad-hard-soft")
