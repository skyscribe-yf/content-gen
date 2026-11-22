#!/usr/bin/env python3
"""cpp-ai-coexistence 篇脚本结构图（结构化信息禁走 AI 生图轨；全图无承重数字）：

01-four-reviewers.png   四审查员工作流：4 persona 并行 → 汇总 agent → 「改什么」清单
02-cpp-ai-friction.png  C++ 对 AI 的五大不友好（清单式，AI++ 201 课程页口径）

注：03-agentic-loop.png 于 2026-11-21 改为 AI 生成概念图（作者要求），本脚本不再生成，防重跑覆盖。

风格：2026-11-15 作者「明快严肃」口径——浅色中性底 #F8F6F1，低饱和金/青强调。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False

BG, FG, GOLD, TEAL, RED, GRID = "#F8F6F1", "#26292F", "#B87C0E", "#0E7A6E", "#C24A28", "#DCD8CE"
DIR = "content/2026-11-30-cpp-ai-coexistence"


def new_fig(w=10, h=5.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 56)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, title, sub, color, title_size=13, sub_size=9.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                linewidth=1.6, edgecolor=color, facecolor="#FFFFFF", zorder=3))
    ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="center",
            fontsize=title_size, fontweight="bold", color=FG, zorder=4)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 3.4, sub, ha="center", va="center",
                fontsize=sub_size, color="#6E6A5E", zorder=4, linespacing=1.5)


def arrow(ax, x1, y1, x2, y2, color=GOLD, lw=2.0, style="-|>", rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=16,
                                 linewidth=lw, color=color, zorder=2,
                                 connectionstyle=f"arc3,rad={rad}"))


# ── 01：四审查员工作流 ──
fig, ax = new_fig(10, 6.0)
ax.text(2, 53.2, "四个审查员，各看一遍", fontsize=16, fontweight="bold", color=FG)
ax.text(2, 49.6, "Hagins 的多 agent 审查制：persona 分工 + 小焦点 + 汇总", fontsize=10, color="#8A8578")

reviewers = [
    ("常规审查员", "限定目录 · 产出 feedback.md\n切断构建权限", TEAL),
    ("API Audrey", "专盯接口设计", TEAL),
    ("Nate", "1970 年代贝尔实验室\nC 老手的人设", GOLD),
    ("安全关键老将", "NASA · 核电站 ·\n导弹发射井履历", RED),
]
pos = [(2, 30), (27, 30), (2, 14), (27, 14)]
for (title, sub, color), (x, y) in zip(reviewers, pos):
    box(ax, x, y, 23, 12.5, title, sub, color)

ax.add_patch(FancyBboxPatch((58, 20), 22, 14, boxstyle="round,pad=0.6,rounding_size=1.2",
                            linewidth=2.0, edgecolor=FG, facecolor="#FFFFFF", zorder=3))
ax.text(69, 30.2, "汇总 agent", ha="center", fontsize=13.5, fontweight="bold", color=FG, zorder=4)
ax.text(69, 25.4, "四份审查汇成一份\n「改什么」清单\n还会分析分歧", ha="center", va="center",
        fontsize=9.5, color="#6E6A5E", zorder=4, linespacing=1.5)

box(ax, 86, 20, 12, 14, "改动", "落到代码里", GOLD, title_size=12)
for (x, y) in pos:
    arrow(ax, x + 23, y + 6.2, 58, 27, color="#B9B4A6", lw=1.6, rad=0.12)
arrow(ax, 80, 27, 86, 27, color=GOLD, lw=2.4)
ax.text(50, 8.5, "纪律：任何一个审查员都不许「审查一切」——焦点小而封闭，才能查深",
        ha="center", fontsize=10.5, color=FG,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F3EFE3", edgecolor=GRID))
plt.tight_layout()
plt.savefig(f"{DIR}/01-four-reviewers.png", facecolor=BG, bbox_inches="tight")
plt.close()

# ── 02：C++ 对 AI 的五大不友好 ──
fig, ax = new_fig(10, 6.2)
ax.text(2, 53.5, "C++ 简直是 AI 最不想碰的语言", fontsize=16, fontweight="bold", color=FG)
ax.text(2, 50.0, "AI++ 201 课程页列出的五大挑战（Hagins）", fontsize=10, color="#8A8578")

items = [
    ("编译延迟", "改完一行要等很久才知道对错，快速迭代的反馈环被打破", TEAL),
    ("头源分裂", ".h 和 .cpp 分成两处，上下文需求被放大", TEAL),
    ("模板错误信息", "读起来像加密勒索信", GOLD),
    ("未定义行为", "能编译、能跑、但是错的——错了都不知道错在哪", RED),
    ("构建系统", "复杂度是又要穿越的一层", TEAL),
]
y = 42
for i, (t, d, c) in enumerate(items, 1):
    ax.add_patch(FancyBboxPatch((2, y - 6.4), 96, 6.8, boxstyle="round,pad=0.4,rounding_size=0.8",
                                linewidth=1.2, edgecolor=GRID, facecolor="#FFFFFF", zorder=3))
    ax.add_patch(plt.Circle((7, y - 2.9), 2.1, color=c, zorder=4))
    ax.text(7, y - 2.9, str(i), ha="center", va="center", fontsize=11,
            fontweight="bold", color="#FFFFFF", zorder=5)
    ax.text(12, y - 2.0, t, ha="left", va="center", fontsize=12.5, fontweight="bold", color=FG, zorder=4)
    ax.text(30, y - 2.4, d, ha="left", va="center", fontsize=10, color="#6E6A5E", zorder=4)
    y -= 8.4
ax.text(50, 2.6, "五条叠起来——偏偏是它，最先摸出了与 AI 共存的完整活法",
        ha="center", fontsize=11, fontweight="bold", color=GOLD)
plt.tight_layout()
plt.savefig(f"{DIR}/02-cpp-ai-friction.png", facecolor=BG, bbox_inches="tight")
plt.close()

print("01/02 done")
