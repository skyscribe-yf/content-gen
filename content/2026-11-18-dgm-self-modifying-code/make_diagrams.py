#!/usr/bin/env python3
"""DGM 篇脚本图：01 判分经济学成本账 + 02 分数台阶（含冷水）+ 03 Greedy 消融。深色底 + 金/青强调。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False

BG, FG, GOLD, TEAL, RED, GRID = "#101418", "#E8E6E1", "#E8B45A", "#4FB3A9", "#D9603B", "#2A2F36"
DIR = "content/2026-11-18-dgm-self-modifying-code"

# ── 01：判分经济学（左右两栏）──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.0), dpi=150,
                               gridspec_kw={"width_ratios": [1.15, 1]})
fig.patch.set_facecolor(BG)

# 左栏：单次运行成本
ax1.set_facecolor(BG)
names = ["DGM 完整运行", "基线 A", "基线 B"]
vals = [22000, 10000, 10000]
colors = [GOLD, GRID, GRID]
bars = ax1.barh(names, vals, color=colors, height=0.55, zorder=3)
for b, v in zip(bars, vals):
    ax1.text(v + 500, b.get_y() + b.get_height() / 2, f"${v:,}",
             va="center", ha="left", color=FG, fontsize=12)
ax1.set_xlim(0, 27500)
ax1.set_title("单次运行的账（§E.1）", color=FG, fontsize=13, pad=12, loc="left")
ax1.set_xlabel("美元", color=FG, fontsize=10)
ax1.tick_params(colors=FG, labelsize=11)
for s in ax1.spines.values(): s.set_visible(False)
ax1.xaxis.grid(True, color=GRID, zorder=0); ax1.set_axisbelow(True)
ax1.invert_yaxis()

# 右栏：判 60 题的单价
ax2.set_facecolor(BG)
names2 = ["SWE-bench\n60 题", "Polyglot\n60 题"]
vals2 = [350, 5]
colors2 = [RED, TEAL]
bars2 = ax2.bar(names2, vals2, color=colors2, width=0.5, zorder=3)
for b, v in zip(bars2, vals2):
    ax2.text(b.get_x() + b.get_width() / 2, v + 8, f"${v}",
             ha="center", color=FG, fontsize=13)
ax2.set_ylim(0, 420)
ax2.set_title("判 60 题的单价：差 70 倍", color=FG, fontsize=13, pad=12, loc="left")
ax2.set_ylabel("美元", color=FG, fontsize=10)
ax2.tick_params(colors=FG, labelsize=11)
for s in ax2.spines.values(): s.set_visible(False)
ax2.yaxis.grid(True, color=GRID, zorder=0); ax2.set_axisbelow(True)

fig.suptitle("倒推口径：论文未给拆分；$350 × 80 次迭代 ≈ $28k > $22k，判分至少一半",
             color=GOLD, fontsize=12, y=0.985)
plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(f"{DIR}/01-cost-account.png", facecolor=BG, bbox_inches="tight")
plt.close()

# ── 02：分数台阶（20.0 → 50.0 → 51.0）──
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
steps = ["起点\n（DGM 初代 agent）", "DGM\n（200 题子集）", "当时最好的开源方案\nOpenHands+CodeAct v2.1\n（同一批 200 题）"]
vals = [20.0, 50.0, 51.0]
colors = [GRID, GOLD, RED]
bars = ax.bar(steps, vals, color=colors, width=0.52, zorder=3)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.1f}%",
            ha="center", color=FG, fontsize=14)
ax.set_ylim(0, 62)
ax.set_ylabel("SWE-bench Verified 解决率（%）", color=FG, fontsize=11)
ax.tick_params(colors=FG, labelsize=11)
for s in ax.spines.values(): s.set_visible(False)
ax.yaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
ax.set_title("不是赢了全场，是赢了自己昨天的 30 个百分点", color=FG, fontsize=14, pad=14, loc="left")
ax.annotate("", xy=(1.42, 51.0), xytext=(1.42, 50.0),
            arrowprops=dict(arrowstyle="<->", color=FG, lw=1.2))
ax.text(1.47, 50.4, "1.0 pp", color=FG, fontsize=10, va="center")
plt.tight_layout()
plt.savefig(f"{DIR}/02-score-steps.png", facecolor=BG, bbox_inches="tight")
plt.close()

# ── 03：Greedy vs 完整 DGM（200 题子集）──
fig, ax = plt.subplots(figsize=(9.5, 5.0), dpi=150)
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
groups = ["SWE-bench Verified\n（200 题子集）", "Polyglot\n（50 题子集）"]
dgm = [50.0, 38.0]
greedy = [39.7, 30.0]
import numpy as np
x = np.arange(len(groups)); w = 0.32
b1 = ax.bar(x - w / 2, dgm, w, label="DGM 完整版（档案库全采样）", color=GOLD, zorder=3)
b2 = ax.bar(x + w / 2, greedy, w, label="DGM Greedy（只啃第一名）", color=TEAL, zorder=3)
for bars in (b1, b2):
    for b in bars:
        v = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.1f}",
                ha="center", color=FG, fontsize=13)
ax.set_xticks(x); ax.set_xticklabels(groups, color=FG, fontsize=11)
ax.set_ylim(0, 60)
ax.set_ylabel("解决率（%）", color=FG, fontsize=11)
ax.tick_params(colors=FG, labelsize=11)
for s in ax.spines.values(): s.set_visible(False)
ax.yaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
ax.set_title("差的不是算法，是敢不敢回头：−10.3 pp", color=FG, fontsize=14, pad=14, loc="left")
leg = ax.legend(facecolor=BG, edgecolor=GRID, fontsize=11, loc="upper right")
for t in leg.get_texts(): t.set_color(FG)
plt.tight_layout()
plt.savefig(f"{DIR}/03-greedy.png", facecolor=BG, bbox_inches="tight")
plt.close()

print("done: 01-cost-account.png / 02-score-steps.png / 03-greedy.png")
