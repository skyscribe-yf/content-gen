#!/usr/bin/env python3
# semantic-entropy 篇 4 张脚本图（数字/结构一律脚本画，AI 图不承载数字）
# 输出到 content/2026-10-04-semantic-entropy/
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

OUT = Path("content/2026-10-04-semantic-entropy")
OUT.mkdir(parents=True, exist_ok=True)

for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

BLUE, RED, GRAY, GREEN = "#2E86C1", "#C0392B", "#7F8C8D", "#27AE60"


def fig_two_rulers():
    """01 同一批 100 段回答，两把尺子量出两个方向（实测：0/100 vs 98/100）。"""
    fig, ax = plt.subplots(figsize=(8.6, 4.4), dpi=150)
    labels = ["字面层\n（逐字相同的比例）", "意思层\n（答同一个答案的比例）"]
    vals = [0, 98]
    colors = [GRAY, BLUE]
    y = [0.36, -0.36]
    ax.barh(y, [100, 100], height=0.50, color="#ECF0F1", edgecolor="#D5DBDB", lw=1)
    ax.barh(y, vals, height=0.50, color=colors)
    for yi, v, c in zip(y, vals, colors):
        ax.text(v + 2 if v > 6 else 2, yi, f"{v}/100", va="center", ha="left",
                fontsize=17, fontweight="bold", color=c)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=13)
    ax.set_xlim(0, 118)
    ax.set_ylim(-0.85, 0.85)
    ax.set_xticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("同一批 100 段回答，两把尺子量出相反的方向", fontsize=15, pad=14)
    fig.text(0.5, 0.02, "实测：DeepSeek-V4.1-Flash，temperature 1.0，n=100",
             ha="center", fontsize=10, color=GRAY)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(OUT / "01-two-rulers.png", facecolor="white")
    plt.close(fig)


def fig_semantic_cluster():
    """02 100 段回答按「解法」聚簇：95 段同一条路，5 段其他（实测口径）。"""
    rng = np.random.default_rng(20261004)
    fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=150)
    centers = [(0.32, 0.58, 95, BLUE, "同一条路（95 段）"),
               (0.76, 0.62, 5, RED, "其他路（5 段）")]
    for cx, cy, n, c, lab in centers:
        sd = 0.085 if n > 20 else 0.038
        pts = rng.normal([cx, cy], sd, size=(n, 2))
        ax.scatter(pts[:, 0], pts[:, 1], s=34, color=c, alpha=0.62,
                   edgecolor="white", lw=0.6, label=f"{lab}")
    ax.add_patch(plt.Circle((0.32, 0.58), 0.165, fill=False, color=BLUE,
                            lw=1.8, ls="--", alpha=0.55))
    ax.add_patch(plt.Circle((0.76, 0.62), 0.072, fill=False, color=RED,
                            lw=1.8, ls="--", alpha=0.55))
    ax.annotate("逐字看：100 段，没有两段一样", xy=(0.03, 0.93), xycoords="axes fraction",
                fontsize=12.5, color=GRAY)
    ax.annotate("按解法看：\n95 段是同一条路", xy=(0.76, 0.70), xytext=(0.76, 0.90),
                textcoords="axes fraction", fontsize=12.5, color=RED, ha="center",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))
    ax.legend(loc="lower left", fontsize=11, frameon=False, scatterpoints=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("100 段回答，按「解法」重新聚一遍", fontsize=15, pad=12)
    fig.text(0.5, 0.02, "实测：温度 1.0，n=100", ha="center", fontsize=10, color=GRAY)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(OUT / "02-semantic-cluster.png", facecolor="white")
    plt.close(fig)


def fig_support_shrinkage():
    """03 RL 前后的分布：不是删掉其他路，是概率质量被抽到主路上。"""
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.3), dpi=150, sharey=True)
    x = np.linspace(0, 1, 500)
    for ax, (mu, sd, c, t, sub) in zip(
        axes,
        [(0.50, 0.155, GRAY, "训练前", "几条路都还有份量"),
         (0.30, 0.055, BLUE, "RL 之后", "概率几乎全押在一条上")],
    ):
        y = np.exp(-0.5 * ((x - mu) / sd) ** 2)
        ax.fill_between(x, y, color=c, alpha=0.22, lw=0)
        ax.plot(x, y, color=c, lw=2.6)
        ax.axvline(mu, color=c, lw=1.2, ls=":", alpha=0.8)
        ax.set_title(f"{t}\n{sub}", fontsize=13, color=c)
        ax.set_xlabel("解法空间", fontsize=11, color=GRAY)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("RL 没有把其他路删掉，只是把概率质量抽走了", fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(OUT / "03-support-shrinkage.png", facecolor="white")
    plt.close(fig)


def fig_your_turn():
    """04 要「3 种不同解法」20 次：0 次凑满 3 条（实测 8/12/0）。"""
    fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=150)
    xs = ["1 条真路", "2 条真路", "3 条真路"]
    counts = [8, 12, 0]
    colors = [GRAY, BLUE, "#EAECEE"]
    bars = ax.bar(xs, counts, color=colors, width=0.52,
                  edgecolor=["none", "none", "#D5DBDB"])
    for b, v in zip(bars, counts):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.35, f"{v}/20",
                ha="center", fontsize=16, fontweight="bold",
                color=RED if v == 0 else "#2C3E50")
    ax.axhline(0, color="#D5DBDB", lw=1)
    ax.annotate("你要的是 3 种，\n它一次都没凑满", xy=(2, 0.15), xytext=(2, 7.4),
                ha="center", fontsize=13, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.6))
    ax.set_ylim(0, 15)
    ax.set_ylabel("出现次数（20 次请求）", fontsize=12, color=GRAY)
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(axis="x", labelsize=13)
    ax.set_title("跟 AI 说「给我 3 种不同的解法」之后", fontsize=15, pad=12)
    fig.text(0.5, 0.02, "判据：只换变量名／数值／公式形式／叙述顺序算同一条路",
             ha="center", fontsize=10, color=GRAY)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(OUT / "04-your-turn.png", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    fig_two_rulers()
    fig_semantic_cluster()
    fig_support_shrinkage()
    fig_your_turn()
    print("脚本图 4 张已生成 →", OUT)
