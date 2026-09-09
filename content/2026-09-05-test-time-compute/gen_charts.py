#!/usr/bin/env python3
"""R1 推理篇脚本图：数字必须与 weixin.md 一致（2026-09-05 核验）。

02-majority-vote.png: 64 次作答 → 众数答案（投票直觉图，无数字）
03-vote-gain.png: 自一致性收益——单次 71.0% vs 64 次投票 86.7%，o1-0912 投票 83.3% 对照
04-verifier-search.png: 验证器打分挑答案（best-of-N 直觉：答案们排序，高分入选，无数字）
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


def fig_majority_vote():
    """02: 同一题答 64 遍 → 数票 → 得票最多的答案交卷"""
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")

    rng = np.random.default_rng(42)
    # 左：64 个小圆点（答案卡片流）
    for i in range(8):
        for j in range(8):
            c = GREEN if rng.random() < 0.42 else (AMBER if rng.random() < 0.5 else MUTED)
            ax.add_patch(plt.Circle((1.1 + i * 0.5, 6.1 - j * 0.55), 0.19,
                                    facecolor=c, edgecolor="none", alpha=0.85, zorder=3))
    ax.text(3.1, 7.5, "同一道题，答 64 遍", fontsize=13, fontweight="bold", color=INK, ha="center")

    # 箭头
    ax.annotate("", xy=(6.2, 4.0), xytext=(5.4, 4.0),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.5))
    ax.text(5.8, 4.8, "数票", fontsize=12, color=INK, ha="center")

    # 右：票仓（众数答案突出）
    bars = [("答案 A", 26, GREEN), ("答案 B", 14, AMBER), ("答案 C", 10, MUTED),
            ("其他", 14, MUTED)]
    for i, (label, n, color) in enumerate(bars):
        y = 6.3 - i * 1.5
        ax.add_patch(plt.Rectangle((7.4, y - 0.38), n * 0.11, 0.86,
                                   facecolor=color, edgecolor="none", alpha=0.9, zorder=3))
        ax.text(7.2, y, label, fontsize=10.5, color=INK, ha="right", va="center")
        ax.text(7.5 + n * 0.11 + 0.15, y, str(n) + " 票", fontsize=10.5, color=MUTED,
                va="center")
    ax.text(12.1, 6.3, "交卷：答案 A", fontsize=12.5, color=GREEN, fontweight="bold",
            ha="right")

    fig.tight_layout()
    fig.savefig(OUT / "02-majority-vote.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("02-majority-vote.png done")


def fig_vote_gain():
    """03: 单次 71.0% vs 投票 86.7%（对照 o1-0912 83.3%）"""
    fig, ax = plt.subplots(figsize=(10, 5.4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(colors=INK, labelsize=11)

    labels = ["单次作答", "答 64 遍取多数票"]
    values = [71.0, 86.7]
    colors = [MUTED, GREEN]
    bars = ax.bar(labels, values, color=colors, width=0.5, zorder=3)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.1f}%",
                ha="center", fontsize=14.5, fontweight="bold", color=INK)

    ax.axhline(83.3, color=RED, lw=1.8, ls="--")
    ax.text(1.62, 84.2, "对照：o1-0912 投票 83.3%", fontsize=11, color=RED,
            ha="right")

    ax.set_ylim(0, 100)
    ax.set_ylabel("AIME 2024 正确率（%）", fontsize=12.5, color=INK)
    ax.set_title("同一个模型，一个参数不改：多想一会儿 +15.7 个点",
                 fontsize=14, color=INK, pad=14, fontweight="bold")
    ax.annotate("+15.7", xy=(1.5, 88.4), xytext=(0.62, 93),
                fontsize=13, color=GREEN, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.8))

    fig.tight_layout()
    fig.savefig(OUT / "03-vote-gain.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("03-vote-gain.png done")


def fig_verifier_search():
    """04: 验证器打分挑答案——三份解答排排站，最高分入选"""
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")

    answers = [("解答 1", 0.92, "每个中间步骤\n请验证器打分", True),
               ("解答 2", 0.55, "", False),
               ("解答 3", 0.78, "", False)]
    for i, (label, score, note, best) in enumerate(answers):
        y = 6.0 - i * 1.9
        color = GREEN if best else MUTED
        ax.add_patch(plt.Rectangle((1.0, y - 0.55), 4.6, 1.3, facecolor=CARD,
                                   edgecolor=color, lw=2.2, zorder=3))
        ax.text(1.35, y + 0.08, label, fontsize=12.5, color=INK, va="center", zorder=4)
        ax.text(4.1, y + 0.08, f"{score:.2f}", fontsize=13.5, color=color,
                fontweight="bold", va="center", zorder=4)
        if note:
            ax.text(3.3, y - 1.5, note, fontsize=10.5, color=AMBER, ha="center")

    ax.annotate("", xy=(10.6, 4.0), xytext=(6.0, 4.0),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.5))
    ax.text(8.3, 4.9, "只选最高分路径\n继续想", fontsize=11.5, color=INK, ha="center")
    ax.add_patch(plt.Rectangle((10.8, 2.9), 2.4, 2.0, facecolor=GREEN, edgecolor=GREEN,
                               lw=2, zorder=3))
    ax.text(12.0, 3.9, "交卷", fontsize=13, fontweight="bold", color="white",
            ha="center", va="center", zorder=4)

    fig.tight_layout()
    fig.savefig(OUT / "04-verifier-search.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("04-verifier-search.png done")


if __name__ == "__main__":
    fig_majority_vote()
    fig_vote_gain()
    fig_verifier_search()
