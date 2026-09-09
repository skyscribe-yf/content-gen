#!/usr/bin/env python3
"""R1 训练篇脚本图：数字必须与 weixin.md 一致（2026-09-05 核验）。

02-gamble-vs-road.png: 一步赌大小 vs 长思维链修路 对比（左右分区，无数字）
03-rl-loop.png: RL 循环三要素（生成解答 → 规则打分 → 推高/压低概率，闭环箭头）
04-aime-curve.png: AIME 2024 训练曲线（15.6% → 71.0%，R1-Zero；标注 o1-0912 74.4% 对照线）
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


def fig_gamble_vs_road():
    """02: 一步赌大小（单条窄路走到底） vs 长思维链（小步+检查+回头）"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.2))
    for ax in (ax1, ax2):
        ax.set_facecolor(BG)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")

    # 左：一步赌大小——一条笔直窄路，起点箭头，中途岔口直接走错
    ax1.plot([1, 9], [5, 5], color=RED, lw=3, solid_capstyle="round")
    ax1.plot([1, 5.2], [5, 2.2], color=MUTED, lw=2, ls="--")
    ax1.plot([5.2, 9], [2.2, 1.4], color=RED, lw=3, solid_capstyle="round")
    ax1.scatter([1], [5], s=220, color=INK, zorder=5)
    ax1.annotate("", xy=(1.9, 5), xytext=(1, 5),
                 arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.5))
    ax1.text(0.7, 8.8, "直接答：一步赌大小", fontsize=14, fontweight="bold", color=INK)
    ax1.text(4.6, 6.6, "岔路口\n押错方向", fontsize=10.5, color=RED, ha="center")
    ax1.text(9.3, 1.2, "全盘皆输", fontsize=11, color=RED, ha="right")
    ax1.text(5, 0.45, "没有回头路", fontsize=10, color=MUTED, ha="center")

    # 右：长思维链——一段段小台阶，每段可回看
    xs = np.linspace(1, 9, 6)
    ys = np.array([1.6, 3.2, 4.6, 5.6, 6.2, 6.2])
    for i in range(len(xs) - 1):
        ax2.plot([xs[i], xs[i + 1]], [ys[i], ys[i + 1]], color=GREEN, lw=3.5,
                 solid_capstyle="round", zorder=3)
        if i % 2 == 0:
            # 小检查圈
            ax2.plot([xs[i], xs[i] + 0.45], [ys[i] - 0.55, ys[i] - 0.05],
                     color=AMBER, lw=2, ls=":")
            ax2.scatter([xs[i] + 0.45], [ys[i] - 0.05], s=90, color=AMBER, zorder=5)
    ax2.scatter([1], [1.6], s=220, color=INK, zorder=5)
    ax2.annotate("", xy=(1.85, 1.6), xytext=(1, 1.6),
                 arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.5))
    ax2.text(0.7, 8.8, "长思维链：小步 + 检查", fontsize=14, fontweight="bold", color=INK)
    ax2.text(5, 9.6, "每段都能回头验证", fontsize=10.5, color=AMBER, ha="center")
    ax2.text(9, 7.0, "步步为营\n越走越高", fontsize=11, color=GREEN, ha="right")

    fig.patch.set_facecolor(BG)
    fig.tight_layout()
    fig.savefig(OUT / "02-gamble-vs-road.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("02-gamble-vs-road.png done")


def fig_rl_loop():
    """03: RL 循环——题目 → 生成一堆解答 → 规则打分（对加分/错扣分）→ 概率推高/压低 → 循环
    布局：四盒横向主流程，连接箭头在盒间隙中（无交叉）；回环用盒子下方的半圆环箭头。"""
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")

    boxes = [
        (0.8, 3.6, "数学题", CARD),
        (3.6, 3.6, "模型写一堆解答", CARD),
        (6.4, 3.6, "规则打分\n答对 +1 / 答错 -1", CARD),
        (9.2, 3.6, "推高对的轨迹\n压低错的轨迹", CARD),
    ]
    for x, y, label, face in boxes:
        ax.add_patch(plt.Rectangle((x, y), 2.3, 1.9, facecolor=face, edgecolor=INK,
                                   lw=1.6, zorder=3))
        ax.text(x + 1.15, y + 0.95, label, ha="center", va="center",
                fontsize=11.5, color=INK, zorder=4)

    # 主流程箭头：位于盒间隙中间高度（与盒子无交叉）
    for x1, x2 in zip([3.1, 5.9, 8.7], [3.6, 6.4, 9.2]):
        ax.annotate("", xy=(x2 + 0.02, 4.55), xytext=(x1 - 0.02, 4.55),
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.2))

    # 回环：盒子下方扁椭圆下半弧（圆环感），从最右盒下方绕回最左盒下方，箭头指回起点
    t = np.linspace(0, np.pi, 60)  # 右端 → 左端，下开口
    cx, cy, rx, ry = 6.1, 2.7, 4.85, 1.65
    x = cx + rx * np.cos(t)
    y = cy - ry * np.sin(t)
    ax.plot(x, y, color=AMBER, lw=2.6, solid_capstyle="round", zorder=2)
    ax.annotate("", xy=(x[-1], y[-1]), xytext=(x[-2], y[-2]),
                arrowprops=dict(arrowstyle="-|>", color=AMBER, lw=2.6))
    ax.text(6.1, 2.55, "几千轮，重复", fontsize=13.5, color=AMBER,
            ha="center", va="center", fontweight="bold")

    fig.tight_layout()
    fig.savefig(OUT / "03-rl-loop.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("03-rl-loop.png done")


def fig_aime_curve():
    """04: R1-Zero AIME 2024 训练曲线——15.6% → 71.0%，对照 o1-0912 74.4%"""
    fig, ax = plt.subplots(figsize=(10, 5.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(colors=INK, labelsize=11)

    steps = np.linspace(0, 10400, 60)
    # 平滑 sigmoid 形训练曲线：0 步 ≈ 15.6，收敛 ≈ 71
    curve = 15.6 + (71.0 - 15.6) / (1 + np.exp(-(steps - 5200) / 1300))
    ax.plot(steps, curve, color=AMBER, lw=3.2, zorder=3)

    # 起终点标注
    ax.scatter([0, 10400], [15.6, 71.0], s=90, color=RED, zorder=5)
    ax.annotate("训练前：15.6%", xy=(0, 15.6), xytext=(600, 8),
                fontsize=12.5, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.6))
    ax.annotate("RL 训练后：71.0%", xy=(10400, 71.0), xytext=(7000, 80),
                fontsize=12.5, color=RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.6))

    # o1-0912 对照线
    ax.axhline(74.4, color=MUTED, lw=1.8, ls="--")
    ax.text(9800, 75.6, "o1-0912：74.4%", fontsize=11, color=MUTED, ha="right")

    ax.set_xlim(0, 10600)
    ax.set_ylim(0, 88)
    ax.set_xlabel("强化学习训练步数", fontsize=12.5, color=INK)
    ax.set_ylabel("AIME 2024 正确率（pass@1）", fontsize=12.5, color=INK)
    ax.set_title("没人教它：R1-Zero 靠纯 RL 从 15.6% 涨到 71.0%",
                 fontsize=14, color=INK, pad=14, fontweight="bold")

    fig.tight_layout()
    fig.savefig(OUT / "04-aime-curve.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("04-aime-curve.png done")


if __name__ == "__main__":
    fig_gamble_vs_road()
    fig_rl_loop()
    fig_aime_curve()
