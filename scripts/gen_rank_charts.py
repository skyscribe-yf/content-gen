#!/usr/bin/env python3
# gen_rank_charts.py — 矩阵的秩 文章的 4 张脚本图
# 输出到 content/2026-08-18-矩阵秩/
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("content/2026-08-18-矩阵秩")
OUT.mkdir(parents=True, exist_ok=True)

# 中文字体
for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

BLUE = "#2a6fdb"
GOLD = "#e0a82e"
PURPLE = "#8a4fd8"
GRAY = "#555555"


def box(ax, x, y, w, h, text, fc, ec, fs=11.5):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04",
            fc=fc, ec=ec, lw=1.6,
        )
    )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, x1, y1, x2, y2, label=None, color="#333333"):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
            color=color, lw=1.8,
        )
    )
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.08, label, ha="center",
                va="bottom", fontsize=10.5, color=GRAY)


def fig_change_of_basis():
    """同一个线性变换，换基就换矩阵；秩不变"""
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=160)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 5.8)
    ax.axis("off")
    box(ax, 0.3, 2.2, 2.4, 1.6, "线性变换 T\n（本质，与基无关）", "#f2e7fb", PURPLE, fs=12)
    arrow(ax, 2.7, 3.0, 4.0, 3.6, "基 $e_1, e_2$")
    arrow(ax, 2.7, 3.0, 4.0, 2.4, "基 $f_1, f_2$")
    box(ax, 4.0, 2.9, 2.6, 1.4, "矩阵 $A$", "#eef3fc", BLUE)
    box(ax, 4.0, 1.7, 2.6, 1.4, "矩阵 $A' = P^{-1}AP$", "#eef3fc", BLUE)
    arrow(ax, 6.6, 3.6, 7.9, 3.6)
    arrow(ax, 6.6, 2.4, 7.9, 2.4)
    box(ax, 7.9, 2.9, 2.6, 1.4, "坐标表象 1", "#fdf3d7", GOLD)
    box(ax, 7.9, 1.7, 2.6, 1.4, "坐标表象 2", "#fdf3d7", GOLD)
    arrow(ax, 10.5, 3.0, 11.8, 3.0, "秩相同", color=GOLD)
    box(ax, 11.8, 2.2, 1.2, 1.6, "rank\n不变", "#e8f5e9", "#2e7d32", fs=11)
    ax.text(6.5, 5.2, "矩阵只是线性变换的坐标快照：换基就换矩阵，但秩不随表象改变",
            ha="center", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "02-change-of-basis.png", bbox_inches="tight")
    plt.close(fig)


def fig_full_vs_low_rank():
    """满秩保维度 vs 低秩压扁：秩 = 信息损失探测器"""
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=160)
    for ax, title, color in [
        (axes[0], "满秩：信息无损", BLUE),
        (axes[1], "低秩：大量维度被压扁", GOLD),
    ]:
        ax.set_xlim(-1.6, 1.6)
        ax.set_ylim(-1.6, 1.6)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=13, pad=10)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        # 输入网格
        g = np.linspace(-1, 1, 5)
        for x in g:
            ax.plot([x, x], [-1, 1], color="#cccccc", lw=0.8, zorder=1)
        for y in g:
            ax.plot([-1, 1], [y, y], color="#cccccc", lw=0.8, zorder=1)
    # 左：满秩 —— 网格映射到旋转+拉伸的完整 2D 区域
    ax = axes[0]
    theta = np.pi / 6
    R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    S = np.array([[1.3, 0], [0, 0.9]])
    M = S @ R
    for x in g:
        pts = np.stack([np.full(5, x), g], axis=1) @ M.T
        ax.plot(pts[:, 0], pts[:, 1], color=BLUE, lw=1.1, alpha=0.75, zorder=2)
    for y in g:
        pts = np.stack([g, np.full(5, y)], axis=1) @ M.T
        ax.plot(pts[:, 0], pts[:, 1], color=BLUE, lw=1.1, alpha=0.75, zorder=2)
    ax.text(0, -1.45, "rank = 2：二维输入 → 二维输出，一一对应", ha="center", fontsize=10.5, color=GRAY)
    # 右：低秩 —— 网格被压成一条线
    ax = axes[1]
    for x in g:
        pts = np.stack([np.full(5, x), g], axis=1) @ np.array([[1.0, 0.0], [0.0, 0.0]]).T
        ax.plot(pts[:, 0], pts[:, 1], color=GOLD, lw=1.1, alpha=0.75, zorder=2)
    for y in g:
        pts = np.stack([g, np.full(5, y)], axis=1) @ np.array([[1.0, 0.0], [0.0, 0.0]]).T
        ax.plot(pts[:, 0], pts[:, 1], color=GOLD, lw=1.1, alpha=0.75, zorder=2)
    ax.annotate("零空间：\n整个 y 方向\n被压成 0", xy=(0, 0.55), xytext=(0.75, 1.05),
                fontsize=10, color="#c0392b", ha="center",
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.4))
    ax.text(0, -1.45, "rank = 1：二维输入 → 一维直线，信息大量丢失", ha="center", fontsize=10.5, color=GRAY)
    fig.suptitle("秩 = 信息损失探测器：满秩保维度，低秩有水分", y=1.0, fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / "03-full-vs-low-rank.png", bbox_inches="tight")
    plt.close(fig)


def fig_mla():
    """MLA 低秩压缩：K/V 压进低维潜变量空间"""
    fig, ax = plt.subplots(figsize=(11, 4.4), dpi=160)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    box(ax, 0.3, 2.2, 2.2, 1.5, "K / V 缓存\n（高维）", "#eef3fc", BLUE)
    arrow(ax, 2.5, 2.95, 3.9, 2.95, "低秩压缩\nc = W_DKV·h")
    box(ax, 3.9, 2.2, 2.4, 1.5, "潜变量空间 c\n（低维主方向）", "#fdf3d7", GOLD)
    arrow(ax, 6.3, 2.95, 7.7, 2.95, "用的时候展开")
    box(ax, 7.7, 2.2, 2.2, 1.5, "恢复 K / V\n（信息仍在）", "#eef3fc", BLUE)
    arrow(ax, 9.9, 2.95, 11.2, 2.95)
    box(ax, 11.2, 2.2, 1.6, 1.5, "注意力", "#f2e7fb", PURPLE)
    ax.text(6.6, 5.0, "MLA：KV 只存低维潜变量，用的时候再展开——低秩压缩不丢方向",
            ha="center", fontsize=12.5)
    fig.tight_layout()
    fig.savefig(OUT / "04-mla-lowrank.png", bbox_inches="tight")
    plt.close(fig)


def fig_lora():
    """LoRA：A/B 低秩矩阵对偶映射，ΔW = BA"""
    fig, ax = plt.subplots(figsize=(11.5, 4.6), dpi=160)
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 5.8)
    ax.axis("off")
    box(ax, 0.3, 2.2, 2.6, 1.6, "预训练权重 W\n（冻结，d×k）", "#eef3fc", BLUE, fs=12)
    ax.text(1.6, 1.6, "训练中不变", ha="center", fontsize=10, color=GRAY)
    box(ax, 4.2, 2.2, 2.6, 1.6, "低秩更新\nΔW = B·A", "#fdf3d7", GOLD, fs=12)
    box(ax, 4.2, 0.5, 1.2, 1.2, "B\nd×r", "#fdf3d7", GOLD, fs=10.5)
    box(ax, 5.6, 0.5, 1.2, 1.2, "A\nr×k", "#fdf3d7", GOLD, fs=10.5)
    ax.text(5.0, 0.15, "r ≪ min(d, k)：两个小矩阵", ha="center", fontsize=10, color=GRAY)
    arrow(ax, 6.8, 3.0, 8.2, 3.0, "对偶映射回去")
    box(ax, 8.2, 2.2, 2.6, 1.6, "领域知识\n（低秩表示空间）", "#f2e7fb", PURPLE, fs=12)
    arrow(ax, 10.8, 3.0, 12.2, 3.0)
    box(ax, 12.2, 2.2, 1.2, 1.6, "FFN\n输出", "#eef3fc", BLUE, fs=11)
    ax.text(6.8, 5.2, "LoRA：rank(BA) ≤ min(rank(B), rank(A)) ≤ r——小矩阵装得下低秩更新",
            ha="center", fontsize=12.5)
    fig.tight_layout()
    fig.savefig(OUT / "05-lora.png", bbox_inches="tight")
    plt.close(fig)


def main():
    fig_change_of_basis()
    fig_full_vs_low_rank()
    fig_mla()
    fig_lora()
    print("charts done ->", OUT)


if __name__ == "__main__":
    main()
