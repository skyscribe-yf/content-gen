#!/usr/bin/env python3
"""AlphaGo 篇脚本图：数字必须与 weixin.md 一致（2026-08-25 核验）。

01-go-tree.png: 矛盾对比——围棋合法局面约 2.08e170 vs AlphaGo 每步模拟几千手
                （对数轴水平条形；y 轴标签加宽，注解放条形右侧独立区）
02-assembly.png: 两个函数组装流程（策略网络报候选 → 搜索 → 价值网络打分 →
                 随机模拟验证 → 落子，箭头链；文字均为概念词，无具体数字）
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


def fig_go_tree():
    """01: 穷举 vs 每步几千手（对数轴）"""
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(colors=INK, labelsize=11)

    labels = ["围棋合法局面数\n（全部穷举）", "AlphaGo 每步模拟\n（随机试下）"]
    values = [2.08e170, 3e3]
    colors = [RED, GREEN]
    ypos = [0.75, 0.28]
    ax.barh(ypos, values, color=colors, height=0.20, zorder=3)

    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=12, color=INK)
    ax.set_xscale("log")
    ax.set_xlim(1e1, 1e195)  # 更宽，给右侧注解文字留空间
    ax.set_xlabel("数量级（对数轴）", fontsize=12.5, color=INK)

    # mathtext 上标（避开上标字形缺失）
    xticks = [1e3, 1e30, 1e60, 1e100, 1e140, 1e170]
    ax.set_xticks(xticks)
    ax.set_xticklabels(
        [r"$10^{3}$", r"$10^{30}$", r"$10^{60}$", r"$10^{100}$",
         r"$10^{140}$", r"$10^{170}$"],
        fontsize=11, color=MUTED,
    )

    # 注解：红条右端外（文字不被 x 轴裁掉），绿条右端外
    ax.text(2.3e170, 0.75, r"约 $2\times10^{170}$" + "\n比整个宇宙的原子还多",
            fontsize=12, color=RED, ha="left", va="center")
    ax.text(2.4e4, 0.28, "几千手\n亿亿亿分之一都不到",
            fontsize=12, color=GREEN, ha="left", va="center")

    # 虚线引导（条形末端 → 注解）
    ax.plot([2.08e170, 2.25e170], [0.75, 0.75], color=RED, lw=1.2, ls="--", zorder=2)
    ax.plot([3e3, 2.3e4], [0.28, 0.28], color=GREEN, lw=1.2, ls="--", zorder=2)

    fig.subplots_adjust(left=0.24, right=0.97, top=0.94, bottom=0.16)
    fig.savefig(OUT / "01-go-tree.png", dpi=160, facecolor=BG)
    plt.close(fig)


def fig_assembly():
    """02: 两个函数组装流程（无具体数字，只标概念）"""
    fig, ax = plt.subplots(figsize=(10.0, 4.8))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.axis("off")

    steps = [
        ("1 策略网络", "扫一眼棋型\n报 3 个候选", AMBER),
        ("2 搜索展开", "把候选分支\n展开成树", INK),
        ("3 价值网络", "给每个局面\n估一个胜率", GREEN),
        ("4 随机模拟", "实习生试下几手\n统计谁赢得多", RED),
        ("5 落子", "选验证后\n胜率最高的", AMBER),
    ]
    n = len(steps)
    xs = np.linspace(0.07, 0.87, n)

    for i, (title, desc, color) in enumerate(steps):
        box = plt.Rectangle((xs[i] - 0.085, 0.32), 0.17, 0.44,
                            facecolor=CARD, edgecolor=color, lw=2.2, zorder=3)
        ax.add_patch(box)
        ax.text(xs[i], 0.66, title, ha="center", va="center",
                fontsize=12.5, color=color, fontweight="bold", zorder=4)
        ax.text(xs[i], 0.46, desc, ha="center", va="center",
                fontsize=10.5, color=INK, zorder=4)
        if i < n - 1:
            ax.annotate("", xy=(xs[i + 1] - 0.085, 0.54),
                        xytext=(xs[i] + 0.085, 0.54),
                        arrowprops=dict(arrowstyle="->", color=INK, lw=1.8))

    ax.text(0.5, 0.12, "每个候选都能退回第 2 步再展开——不是一条路走到黑",
            ha="center", fontsize=11.5, color=MUTED, style="italic")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(OUT / "02-assembly.png", dpi=160, facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_go_tree()
    fig_assembly()
    print("生成完成：01-go-tree.png / 02-assembly.png")
