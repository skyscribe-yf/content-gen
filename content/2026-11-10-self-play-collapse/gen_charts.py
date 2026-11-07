#!/usr/bin/env python3
"""本篇两张自绘图：
01-gating-loop.png  两把杠杆（数据门控 / 奖励接地）流程示意
03-agreement-reward.png  自洽奖励 k/16 在「输出确定」与「输出模糊」两类题上的示意

用法：uv run --with matplotlib --with numpy python gen_charts.py
数值口径：03 图的 k/16 由论文自洽奖励公式直接算出，属机制示意（非论文实测值）。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

INK = "#1f2933"
BLUE = "#0F4C81"
GOLD = "#C8901E"
GREY = "#8a949e"
RED = "#c0392b"
GREEN = "#2e7d5b"


def chart_loop(path="01-gating-loop.png"):
    fig, ax = plt.subplots(figsize=(9.0, 4.6), dpi=200)
    ax.set_xlim(0, 10.4)
    ax.set_ylim(0, 5.6)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#ffffff", ec=INK, fs=11, lw=1.6, tc=INK):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.12",
                                    fc=fc, ec=ec, lw=lw, zorder=2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=tc, zorder=3, linespacing=1.4)

    def arrow(p1, p2, color=INK, ls="-", rad=0.0, lw=1.7):
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=14,
                                     color=color, lw=lw, linestyle=ls,
                                     connectionstyle=f"arc3,rad={rad}", zorder=1))

    # 出题器 -> 候选题 -> 门控 -> 训练池 -> 解题器
    box(0.10, 3.55, 1.65, 0.95, "出题器", fc="#eef3f8", fs=11)
    box(2.05, 3.55, 1.45, 0.95, "候选题", fs=11)
    box(3.80, 3.30, 2.30, 1.45, "门控\n同段程序跑两遍\n输出一致？", fc="#fdf6e3", ec=GOLD, fs=10.5)
    box(6.45, 3.55, 1.45, 0.95, "训练池", fs=11)
    box(8.15, 3.55, 1.55, 0.95, "解题器", fs=11)

    arrow((1.80, 4.02), (2.00, 4.02))
    arrow((3.55, 4.02), (3.75, 4.02))
    arrow((6.15, 4.02), (6.40, 4.02))
    arrow((7.95, 4.02), (8.10, 4.02))

    # 丢弃分支
    box(4.00, 1.75, 1.90, 0.85, "丢弃：不许进池", fc="#fdecea", ec=RED, fs=10, tc=RED)
    arrow((4.95, 3.28), (4.95, 2.65), color=RED)
    ax.text(5.08, 2.98, "否", color=RED, fontsize=10.5)
    ax.text(6.30, 4.32, "是", color=GREEN, fontsize=10.5)

    # 判分 + 回灌
    box(6.45, 0.55, 3.55, 0.90, "判分：真值　还是　自洽（组内一致率）", fc="#eef3f8", fs=9.6)
    arrow((8.92, 3.50), (8.92, 1.50))
    arrow((8.92, 0.52), (6.40, 0.52))
    arrow((6.40, 0.52), (0.92, 0.52))
    arrow((0.92, 0.55), (0.92, 3.50))

    # 标注两把杠杆
    ax.annotate("杠杆① 在数据层", xy=(4.95, 5.00), ha="center", fontsize=11, color=GOLD, weight="bold")
    ax.annotate("杠杆② 在奖励层", xy=(8.22, 1.68), ha="center", fontsize=11, color=BLUE, weight="bold")

    ax.text(0.10, 5.30, "自我对弈：门控决定存在哪些题，判分决定怎么用它们",
            fontsize=11.5, color=INK, weight="bold")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def chart_agreement(path="03-agreement-reward.png"):
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.2), dpi=200)

    specs = [
        dict(title="输出确定的题", agree=12, correct=12, note="一致 = 正确"),
        dict(title="输出模糊的题", agree=15, correct=1, note="一致 ≠ 正确"),
    ]
    for ax, sp in zip(axes, specs):
        ax.set_xlim(0, 4.1)
        ax.set_ylim(0, 10.5)
        ax.axis("off")
        ax.set_title(sp["title"], fontsize=12, color=INK, weight="bold", pad=8)
        k = sp["agree"]
        for i in range(16):
            r, c = divmod(i, 4)
            major = i < k
            ax.add_patch(Rectangle((0.08 + c * 0.97, 5.95 + (3 - r) * 0.97), 0.88, 0.80,
                                   fc=BLUE if major else "#e8b4ad", ec="white", lw=1.2))
        ax.text(2.0, 5.25, f"{k} / 16 一致", ha="center", fontsize=10.5, color=INK)
        ax.text(2.0, 4.25, f"自洽奖励  k/16 = {k/16:.2f}", ha="center", fontsize=12,
                color=BLUE, weight="bold")
        ax.text(2.0, 3.35, f"真准确率  {sp['correct']}/16 = {sp['correct']/16:.2f}",
                ha="center", fontsize=12, color=RED, weight="bold")
        ax.text(2.0, 2.35, sp["note"], ha="center", fontsize=10.5, color=GREY)

    fig.suptitle("同一套自洽奖励：越模糊的题，越容易凑出一致", fontsize=12.5, color=INK,
                 weight="bold", y=0.985)
    fig.text(0.5, 0.015, "示意：k/16 按论文自洽奖励公式计算，非论文实测值",
             ha="center", fontsize=9, color=GREY)
    fig.tight_layout(rect=(0, 0.045, 1, 0.94))
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    chart_loop()
    chart_agreement()
    print("ok: 01-gating-loop.png 03-agreement-reward.png")
