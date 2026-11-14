#!/usr/bin/env python3
"""本篇脚本画图：01 计数器 RNG vs 线性 RNG / 03 GPU 并行层级 / 04 一维下标到线程网格 / 05 W=W0+Δ 分解。
规矩：结构/公式用脚本画，图内数字与正文逐字一致；AI 概念图禁载数字（02 洗牌图走 AI）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["axes.unicode_minus"] = False
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
D = "content/2026-11-14-国产大模型GB300之谜"

INK = "#1a2332"
SUB = "#5b6b7f"
BLUE = "#0F4C81"
RED = "#c0392b"
GOLD = "#E8A317"
GREEN = "#1e7d5a"
BG = "#ffffff"
LIGHT = "#eef2f7"


def fp(size=13):
    return matplotlib.font_manager.FontProperties(fname=FONT, size=size)


def newfig(w=11, h=5.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def title(ax, text, y=0.95):
    ax.text(0.5, y, text, ha="center", fontproperties=fp(19), color=INK)


def box(ax, x, y, w, h, text, fc=LIGHT, ec=INK, tc=INK, size=12, lw=1.4, weight="bold"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004",
                                fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontproperties=fp(size), color=tc, weight=weight)


def arrow(ax, x1, y1, x2, y2, color=SUB, lw=1.6, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=14, color=color, lw=lw))


# ---------- 01 线性 RNG 的链 vs 计数器 RNG 的并行 ----------
def fig01():
    fig, ax = newfig(11, 5.2)
    title(ax, "链式生成排着队，计数器生成随便并行")

    # 左：线性链
    ax.text(0.25, 0.86, "线性随机数生成器", ha="center", fontproperties=fp(15), color=RED)
    xs = [0.06, 0.18, 0.30, 0.42]
    for i, x in enumerate(xs):
        box(ax, x, 0.55, 0.09, 0.12, f"$x_{{{i}}}$", fc="#fdf0ee", ec=RED, tc=RED, size=14)
        if i < len(xs) - 1:
            arrow(ax, x + 0.09, 0.61, x + 0.12 - 0.005, 0.61, color=RED)
    ax.text(0.06, 0.45, r"$x_{n+1}=(ax_n+c)\ \mathrm{mod}\ m$", ha="left",
            fontproperties=fp(13), color=SUB)
    ax.text(0.06, 0.36, "下一个要用上一个：海量参数面前慢到没法用",
            ha="left", fontproperties=fp(12), color=SUB)

    # 分隔线
    ax.plot([0.5, 0.5], [0.30, 0.88], color="#d5dde6", lw=1.2)

    # 右：计数器并行
    ax.text(0.75, 0.86, "计数器随机数生成器", ha="center", fontproperties=fp(15), color=BLUE)
    for i, x in enumerate([0.56, 0.70, 0.84]):
        box(ax, x, 0.66, 0.11, 0.11, f"$n_{{{i}}}$", fc=LIGHT, ec=BLUE, tc=BLUE, size=13)
        box(ax, x, 0.44, 0.11, 0.11, f"$r_{{{i}}}$", fc="#e8f0f8", ec=BLUE, tc=BLUE, size=13)
        arrow(ax, x + 0.055, 0.66, x + 0.055, 0.55, color=BLUE)
    box(ax, 0.615, 0.20, 0.27, 0.10, "seed 一起进去搅", fc="#fdf6e8", ec=GOLD, tc=INK, size=12)
    arrow(ax, 0.75, 0.30, 0.75, 0.43, color=GOLD)
    ax.text(0.75, 0.10, "位置即输入：要第几个现场算，互不依赖",
            ha="center", fontproperties=fp(12), color=SUB)
    fig.savefig(f"{D}/01-counter-rng.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 03 GPU 并行层级 ----------
def fig03():
    fig, ax = newfig(11, 5.6)
    title(ax, "整卡、SM、Warp、线程：随机数按最细粒度铺开")

    box(ax, 0.06, 0.60, 0.88, 0.24, "", fc="#f7f9fc", ec=INK, lw=1.8)
    ax.text(0.10, 0.79, "一张 GPU", fontproperties=fp(14), color=INK, weight="bold")

    for i, x in enumerate([0.10, 0.38, 0.66]):
        box(ax, x, 0.66, 0.24, 0.12, f"SM {i+1}（型号定死）", fc="#e8f0f8", ec=BLUE, tc=BLUE, size=11)
        for j, wx in enumerate([x + 0.02, x + 0.09, x + 0.16]):
            box(ax, wx, 0.485, 0.06, 0.09, "Warp", fc=LIGHT, ec=SUB, tc=SUB, size=9, lw=1.0)
            for k, tx in enumerate([wx + 0.012, wx + 0.030]):
                box(ax, tx, 0.36, 0.016, 0.07, "", fc="#c9d6e4", ec=SUB, lw=0.8)
        ax.text(x + 0.12, 0.335, "32 个线程", ha="center", fontproperties=fp(9), color=SUB)

    box(ax, 0.10, 0.14, 0.24, 0.10, "TensorCore（管算，不管发随机数）",
        fc="#f5f5f5", ec="#b0b8c2", tc=SUB, size=9, lw=1.0)
    ax.text(0.50, 0.09, "指纹读的就是最底层：每个线程一条独立的随机数流",
            ha="center", fontproperties=fp(12), color=SUB)
    fig.savefig(f"{D}/03-gpu-structure.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 04 一维下标 → 线程 × 取数次 二维网格 ----------
def fig04():
    fig, ax = newfig(11, 5.4)
    title(ax, "一维权重下标，落到线程网格的第几列第几行")

    # 左：一维权重
    ax.text(0.14, 0.88, "权重向量 $W$（一维下标 $i$）", ha="center",
            fontproperties=fp(13), color=INK)
    for i, x in enumerate([0.03, 0.09, 0.15, 0.21]):
        box(ax, x, 0.62, 0.05, 0.12, f"$i_{{{i}}}$", fc=LIGHT, ec=SUB, tc=SUB, size=10, lw=1.0)
    ax.text(0.03, 0.55, "…", ha="left", fontproperties=fp(14), color=SUB)
    ax.text(0.03, 0.47, r"$t=i\ \mathrm{mod} G$（第几列）", ha="left",
            fontproperties=fp(13), color=BLUE)
    ax.text(0.03, 0.39, "$q=\\lfloor i/G\\rfloor$（第几行）", ha="left",
            fontproperties=fp(13), color=GOLD)
    arrow(ax, 0.28, 0.68, 0.40, 0.68, color=INK, lw=2.0)

    # 右：二维网格
    gx, gy, cw, ch = 0.46, 0.30, 0.085, 0.11
    for r in range(3):
        for c in range(4):
            hl = (r == 1 and c == 2)
            box(ax, gx + c * cw, gy + (2 - r) * ch, cw * 0.92, ch * 0.9, "",
                fc="#fdf3dc" if hl else LIGHT, ec=GOLD if hl else SUB,
                lw=1.8 if hl else 0.9)
    ax.text(gx + 2 * cw + cw * 0.46, gy + ch + 0.02, "$t$", ha="center",
            fontproperties=fp(13), color=BLUE)
    ax.text(gx - 0.04, gy + 2 * ch + 0.05, "$q$", ha="center",
            fontproperties=fp(13), color=GOLD)
    ax.text(gx + 2 * cw + cw * 0.46, gy + ch + 0.16, "同一格 = 同一个随机数", ha="center",
            fontproperties=fp(11), color=INK)
    ax.text(0.70, 0.16, "列数 $G$ 由 SM 数定死，行随便长", ha="center",
            fontproperties=fp(12), color=SUB)
    fig.savefig(f"{D}/04-placement.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 05 W = W0 + Δ 分解 ----------
def fig05():
    fig, ax = newfig(11, 5.2)
    title(ax, "训练塞进来的增量，比 initialization 大两个数量级")

    x0, w = 0.30, 0.40
    box(ax, x0, 0.66, w, 0.10, "已发布的权重 $W$", fc="#f7f9fc", ec=INK, size=13)
    box(ax, x0, 0.42, w, 0.06, "初始化 $W_0$（信号）", fc="#fdf3dc", ec=GOLD, tc=INK, size=11)
    box(ax, x0, 0.42 + 0.06, w, 0.18, "训练累计更新 $\\Delta$（噪声级）", fc="#e8f0f8", ec=BLUE, tc=BLUE, size=12)
    ax.text(x0 + w + 0.03, 0.51, "$W=W_0+\\Delta$", ha="left",
            fontproperties=fp(15), color=INK)

    ax.text(0.5, 0.26, "更新与初始化近似无关时：", ha="center",
            fontproperties=fp(12), color=SUB)
    ax.text(0.5, 0.16, "$\\mathrm{Corr}(W,W_0)=\\dfrac{1}{\\sqrt{1+\\mathrm{Var}(\\Delta)/\\mathrm{Var}(W_0)}}$",
            ha="center", fontproperties=fp(15), color=INK)
    ax.text(0.5, 0.06, "报告实测：方差比约 228，相关性仍剩 0.066（约 57σ）",
            ha="center", fontproperties=fp(12), color=SUB)
    fig.savefig(f"{D}/05-covariance.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig01(); fig03(); fig04(); fig05()
    print("4 张脚本图已生成")
