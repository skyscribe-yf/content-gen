#!/usr/bin/env python3
"""本篇脚本图 2 张（数字只走脚本轨，AI 图不承载数字）。

- 05-average-hides.png  §6：平均分持平，最差相位塌陷（9.9% vs 58.4%）
- 06-same-bet.png       §6：同一个赌注——四条分支汇到「查询之前就合并」

数字来源：arXiv:2609.36322 §3.2（W8/S8 压缩模型最差相位 9.9%，全注意力基线 58.4%；
同一对模型的平均准确率与验证损失几乎持平，论文原话 "nearly matches"）。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

for c in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"):
    try:
        font_manager.fontManager.addfont(c)
    except Exception:
        pass
plt.rcParams["font.family"] = font_manager.FontProperties(
    fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc").get_name()
plt.rcParams["axes.unicode_minus"] = False

INK = "#1b1b1f"
BLUE = "#0F4C81"
RED = "#c0392b"
GOLD = "#E8A317"
GREY = "#8a8a93"


def fig_average_hides(out="05-average-hides.png"):
    fig, ax = plt.subplots(figsize=(9.6, 4.6), dpi=200)
    labels = ["全注意力基线", "分块压缩模型\n（W8/S8，八头）"]
    vals = [58.4, 9.9]
    colors = [GREY, RED]
    bars = ax.bar(labels, vals, width=0.42, color=colors, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.6, f"{v}%",
                ha="center", va="bottom", fontsize=21, weight="bold", color=INK)
    # 平均值参考：论文只说「几乎持平」，故用虚线示意不加数字
    ax.axhline(58.4, color=GREY, ls=":", lw=1.4, zorder=2)
    ax.annotate("", xy=(1.33, 58.4), xytext=(1.33, 9.9),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=1.6))
    ax.text(1.40, 32, "最差相位\n差 48.5 个百分点", fontsize=15, weight="bold",
            color=INK, va="center", ha="left")
    ax.set_ylim(0, 98)
    ax.set_ylabel("该模型最差相位的检索准确率（%）", fontsize=14, color=INK)
    ax.set_title("平均分持平，最差相位塌陷", fontsize=19, weight="bold", color=INK, pad=16)
    ax.text(0.0, 0.99,
            "同一对模型的平均准确率与验证损失几乎持平（论文原话：nearly matches）\n"
            "可它最差的那个相位只剩 9.9%，基线是 58.4%",
            transform=ax.transAxes, fontsize=12.5, color="#3a3a42", va="top")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", ls=":", alpha=0.35, zorder=0)
    ax.tick_params(labelsize=14)
    fig.tight_layout()
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    return out


def fig_same_bet(out="06-same-bet.png"):
    fig, ax = plt.subplots(figsize=(9.6, 5.2), dpi=200)
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.4); ax.axis("off")

    branches = ["KV 缓存量化", "agent 的记忆摘要", "RAG 的分块", "长文摘要"]
    for i, t in enumerate(branches):
        y = 5.4 - i * 1.05
        ax.add_patch(FancyBboxPatch((0.15, y - 0.3), 2.75, 0.62,
                                    boxstyle="round,pad=0.04,rounding_size=0.12",
                                    fc="#eef2f7", ec=BLUE, lw=1.4))
        ax.text(1.52, y + 0.005, t, ha="center", va="center", fontsize=14.5, color=INK)
        ax.add_patch(FancyArrowPatch((2.98, y), (5.05, 3.15),
                                     arrowstyle="-|>", mutation_scale=18,
                                     color=BLUE, lw=1.5, alpha=0.85))

    ax.add_patch(FancyBboxPatch((5.1, 2.28), 4.6, 1.78,
                                boxstyle="round,pad=0.06,rounding_size=0.16",
                                fc="#0F4C81", ec="none"))
    ax.text(7.4, 3.55, "查询出现之前", ha="center", va="center",
            fontsize=17, weight="bold", color="white")
    ax.text(7.4, 2.86, "就把内容合并掉", ha="center", va="center",
            fontsize=17, weight="bold", color=GOLD)

    ax.add_patch(FancyArrowPatch((7.4, 2.2), (7.4, 1.42),
                                 arrowstyle="-|>", mutation_scale=20, color=INK, lw=1.8))
    ax.text(7.4, 1.02, "都在赌你以后用不到\n被合掉的那一部分", ha="center", va="center",
            fontsize=14, color=INK, linespacing=1.5)
    ax.text(0.15, 6.18, "同一个赌注", fontsize=19, weight="bold", color=INK)
    fig.tight_layout()
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    print("已生成:", fig_average_hides(), "+", fig_same_bet())
