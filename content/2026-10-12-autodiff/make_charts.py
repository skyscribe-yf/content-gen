#!/usr/bin/env python3
"""本篇 4 张脚本结构图（数字只走这条轨，AI 概念图禁止承载数字）。

01 三路对照 / 02 一次一列还是一次一行 / 04 差分精度天花板 / 05 千倍差距
数字来源：~/scripts/matrix-calculus-ad/verify.py（2026-10-12 三次连跑的中位数）。
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = Path(__file__).parent
plt.rcParams["axes.unicode_minus"] = False

CAND = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]
for c in CAND:
    if Path(c).exists():
        font_manager.fontManager.addfont(c)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=c).get_name()
        break

INK = "#1b1b1f"
MUTED = "#6b6b76"
ACCENT = "#0F4C81"   # 账号主色（grace / scienceBlue）
WARM = "#B3541E"
LINE = "#d8d8de"


def save(fig, name):
    out = HERE / name
    fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.3, facecolor="white")
    plt.close(fig)
    print("wrote", out)


# ── 01 三路对照 ────────────────────────────────────────────────────────────
def chart_01():
    cols = ["数值微分（差分）", "符号微分", "自动微分"]
    rows = [
        ("得到什么", "近似数", "表达式", "精确数"),
        ("精度", "受相消误差限制\nx=1e6 时 1.2e-03", "精确", "浮点舍入量级"),
        ("代价", "n+1 次函数求值", "表达式膨胀", "一次前向 + 一次反向"),
        ("不光滑点", "被抹平", "需要人决定", "按实现约定的次梯度"),
        ("能否对一个程序求导", "能（黑盒）", "不能", "能"),
    ]
    fig, ax = plt.subplots(figsize=(11.4, 4.5))
    ax.set_axis_off()
    tbl = ax.table(
        cellText=[[r[0]] + list(r[1:]) for r in rows],
        colLabels=[""] + cols,
        cellLoc="left",
        colWidths=[0.20, 0.27, 0.20, 0.30],
        loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(12.5)
    tbl.scale(1, 2.15)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor(LINE)
        cell.set_linewidth(0.9)
        if r == 0:
            cell.set_facecolor("#f2f5f9")
            cell.set_text_props(color=ACCENT, weight="bold")
        elif c == 0:
            cell.set_text_props(color=MUTED, weight="bold")
        else:
            cell.set_text_props(color=INK)
        if r > 0 and c == 3:
            cell.set_facecolor("#fbfcfe")
        cell.PAD = 0.045
    ax.set_title("求导的三条路", fontsize=15, color=INK, weight="bold", pad=14)
    save(fig, "01-三路对照.png")


# ── 02 一次一列，一次给一行 ──────────────────────────────────────────────────
def chart_02():
    rng = np.random.default_rng(0)
    J = rng.integers(1, 9, size=(5, 6))
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))

    for ax, (title, hi, tail, color) in zip(
        axes,
        [
            ("从右边乘：$Jv$", "col", "拿到 J 的第 1 列", ACCENT),
            ("从左边乘：$u^\\top J$", "row", "拿到 J 的第 1 行", WARM),
        ],
    ):
        ax.set_axis_off()
        for i in range(5):
            for j in range(6):
                on = (hi == "col" and j == 1) or (hi == "row" and i == 0)
                ax.add_patch(
                    plt.Rectangle(
                        (j, 4 - i), 0.94, 0.94,
                        facecolor=color if on else "#f4f5f7",
                        edgecolor="white", linewidth=2.0,
                    )
                )
                ax.text(j + 0.47, 4 - i + 0.47, str(J[i, j]),
                        ha="center", va="center", fontsize=13,
                        color="white" if on else "#9a9aa4")

        ax.text(3.0, 6.55, f"{title}\n一次给出一列" if hi == "col"
                else f"{title}\n一次给出一行",
                ha="center", va="top", fontsize=13.5, color=INK, weight="bold",
                linespacing=1.5)
        ax.text(3.0, -1.15, tail, ha="center", fontsize=12, color=color)

        if hi == "col":
            ax.annotate("", xy=(1.47, 4.62), xytext=(1.47, 5.30),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=2.4))
            ax.text(1.98, 4.72, "$v$", fontsize=14, color=color, ha="left", va="center")
        else:
            ax.annotate("", xy=(-0.12, 4.47), xytext=(-1.30, 4.47),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=2.4))
            ax.text(-1.62, 4.47, "$u^\\top$", fontsize=13.5, color=color,
                    ha="right", va="center")

        ax.set_xlim(-2.35, 6.15)
        ax.set_ylim(-1.6, 7.05)

    fig.suptitle("导数是一张矩阵，而矩阵可以从两个方向被乘", fontsize=15, color=INK,
                 weight="bold", y=1.0)
    save(fig, "02-一次一列还是一次一行.png")


# ── 04 差分精度天花板 ──────────────────────────────────────────────────────
def chart_04():
    xs = [r"$x=10^0$", r"$x=10^3$", r"$x=10^6$"]
    eps = ["eps=1e-4", "eps=1e-6", "eps=1e-8"]
    E = np.array([
        [1.7e-09, 5.1e-11, 4.8e-09],
        [1.9e-09, 2.5e-09, 7.9e-07],
        [5.4e-07, 7.6e-06, 1.2e-03],
    ])
    fig, ax = plt.subplots(figsize=(8.6, 4.3))
    im = ax.imshow(np.log10(E), cmap="Oranges", aspect="auto", vmin=-11, vmax=-3)
    ax.set_xticks(range(3), eps, fontsize=12)
    ax.set_yticks(range(3), xs, fontsize=12)
    for i in range(3):
        for j in range(3):
            hot = E[i, j] >= 1e-4
            ax.text(j, i, f"{E[i, j]:.1e}", ha="center", va="center",
                    fontsize=13, color="white" if hot else INK,
                    weight="bold" if E[i, j] == E.max() else "normal")
    ax.set_xticks(np.arange(-0.5, 3, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 3, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2.4)
    ax.tick_params(which="both", length=0)
    ax.set_title("中心差分的相对误差：x 越大，误差越离谱", fontsize=14.5,
                 color=INK, weight="bold", pad=12)
    ax.set_xlabel("差分步长", fontsize=12, color=MUTED)
    ax.set_ylabel("求导的位置", fontsize=12, color=MUTED)
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("log10 相对误差", fontsize=11, color=MUTED)
    cb.outline.set_visible(False)
    save(fig, "04-差分精度天花板.png")


# ── 05 千倍差距 ────────────────────────────────────────────────────────────
def chart_05():
    labels = ["正向逐列\n4096 次", "反向\n一次"]
    vals = [3765.5, 2.0]
    colors = [MUTED, ACCENT]
    fig, ax = plt.subplots(figsize=(8.4, 3.9))
    y = np.arange(2)[::-1]
    ax.barh(y, vals, height=0.46, color=colors)
    for yy, v, l in zip(y, vals, labels):
        ax.text(v * 1.18, yy, f"{v:,.1f} ms", va="center", fontsize=14,
                color=INK, weight="bold")
    ax.set_yticks(y, labels, fontsize=12.5)
    ax.set_xscale("log")
    ax.set_xlim(0.9, 20000)
    ax.set_xticks([1, 10, 100, 1000, 10000], ["1", "10", "100", "1000", "10000"])
    ax.set_xlabel("耗时（毫秒，对数轴）", fontsize=12, color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=11)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.grid(axis="x", color=LINE, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    ax.annotate("", xy=(vals[1] * 1.05, 0.70), xytext=(vals[0] / 1.05, 0.70),
                arrowprops=dict(arrowstyle="<|-|>", color=WARM, lw=1.6))
    ax.text(np.sqrt(vals[0] * vals[1]), 0.50,
            "快了 1911 倍",
            ha="center", va="center", fontsize=13, color=WARM, weight="bold")
    ax.text(np.sqrt(vals[0] * vals[1]), 0.29,
            "（同一道题，同一种梯度）",
            ha="center", va="center", fontsize=10, color=MUTED)
    ax.set_ylim(-0.5, 1.35)
    ax.set_title("$f:\\mathbb{R}^{4096}\\to\\mathbb{R}$ 求一次完整梯度",
                 fontsize=14.5, color=INK, weight="bold", pad=12)
    save(fig, "05-千倍差距.png")


def chart_06():
    fig, ax = plt.subplots(figsize=(10.4, 4.5))
    ax.set_axis_off()

    def shards(x0, y, n=4, w=0.46, h=0.52, gap=0.13, fc="#e8edf4", ec=LINE):
        for i in range(n):
            ax.add_patch(plt.Rectangle((x0 + i * (w + gap), y), w, h,
                                        facecolor=fc, edgecolor=ec, linewidth=1.2))
        return x0 + n * (w + gap) - gap

    # 前向
    shards(0.0, 1.85)
    ax.annotate("", xy=(4.1, 2.11), xytext=(2.55, 2.11),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=2.6))
    ax.text(3.32, 2.24, "all-gather", ha="center", fontsize=12.5, color=ACCENT,
            weight="bold")
    ax.add_patch(plt.Rectangle((4.35, 1.72), 3.6, 0.78, facecolor="#dbe5f1",
                                edgecolor=ACCENT, linewidth=1.3))
    ax.text(6.15, 2.11, "完整的压缩 KV", ha="center", va="center", fontsize=12, color=INK)
    ax.text(0.0, 2.62, "前向：每张卡手里的那一段，拼成完整的一份",
            fontsize=12.5, color=MUTED)

    # 反向
    ax.add_patch(plt.Rectangle((0.0, 0.62), 3.6, 0.78, facecolor="#f7e9df",
                                edgecolor=WARM, linewidth=1.3))
    ax.text(1.8, 1.01, "上游回传的梯度", ha="center", va="center", fontsize=12, color=INK)
    ax.annotate("", xy=(4.15, 1.01), xytext=(3.85, 1.01),
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=2.6))
    ax.text(4.75, 1.32, "reduce-scatter", ha="center", fontsize=12.5, color=WARM,
            weight="bold")
    shards(4.35, 0.62, fc="#f7e9df", ec=WARM)
    for i in range(4):
        ax.text(4.58 + i * 0.59, 0.88, "Σ", ha="center", va="center",
                fontsize=13, color=WARM, weight="bold")
    ax.text(0.0, 0.28, "反向：每张卡只拿回自己那一段的梯度总和（不是完整拷贝）",
            fontsize=12.5, color=MUTED)

    ax.set_xlim(-0.35, 8.25)
    ax.set_ylim(0.0, 3.0)
    ax.set_title("通信算子也有自己的伴随", fontsize=15, color=INK, weight="bold", pad=10)
    save(fig, "06-伴随算子.png")


if __name__ == "__main__":
    chart_01()
    chart_02()
    chart_04()
    chart_05()
    chart_06()
