#!/usr/bin/env python3
"""记忆诅咒篇脚本图：01 信任博弈合作率崩塌（HL=2 vs HL=80）+ 02 机制对比（前瞻比率 / 词汇变化）。浅色底 + 金/青强调（2026-11-15 作者「明快」口径）。数字全部来自 .grill/memory-curse-research.md 第三节。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False

BG, FG, GOLD, TEAL, RED, GRID = "#F8F6F1", "#26292F", "#B87C0E", "#0E7A6E", "#C24A28", "#DCD8CE"
DIR = "content/2026-11-20-memory-curse"

# ── 01：信任博弈合作率，HL=2 vs HL=80（GPT-OSS-120B）──
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
labels = ["HL = 2（短记忆）", "HL = 80（长记忆）"]
vals = [92.7, 7.3]
colors = [TEAL, RED]
bars = ax.bar(labels, vals, color=colors, width=0.46, zorder=3)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 2.5, f"{v}%",
            ha="center", color=FG, fontsize=15, fontweight="bold")
# 崩塌连线
ax.plot([0, 1], [92.7, 7.3], color=GOLD, lw=2.2, ls="--", zorder=4)
ax.annotate("−85.4 个百分点", xy=(0.5, 52), xytext=(0.5, 60),
            ha="center", color=GOLD, fontsize=13, fontweight="bold")
ax.set_ylim(0, 108)
ax.set_ylabel("信任博弈合作率（%）", color=FG, fontsize=12)
ax.tick_params(colors=FG, labelsize=13)
for s in ax.spines.values(): s.set_visible(False)
ax.yaxis.grid(True, color=GRID, zorder=0)
ax.set_axisbelow(True)
ax.set_title("GPT-OSS-120B：换个困境，记忆越长合作越少", color=FG, fontsize=15, pad=14, loc="left")
ax.text(0, -22, "注：同一模型在囚徒困境中 HL=2→80 全程 100% 免疫；本篇取论文报告的两端 HL",
        color="#8A8578", fontsize=10)
plt.tight_layout()
plt.savefig(f"{DIR}/01-memory-curse-curve.png", facecolor=BG, bbox_inches="tight")
plt.close()

# ── 02：机制对比——前瞻比率 + 词汇变化 ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.2), dpi=150)
fig.patch.set_facecolor(BG)

# 左：前瞻比率 immune vs cursed（HL=80）
ax1.set_facecolor(BG)
labels1 = ["免疫组\n（10 个设置）", "中招组\n（18 个设置）"]
vals1 = [0.504, 0.340]
bars1 = ax1.bar(labels1, vals1, color=[TEAL, RED], width=0.46, zorder=3)
for b, v in zip(bars1, vals1):
    ax1.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}",
             ha="center", color=FG, fontsize=14, fontweight="bold")
ax1.set_ylim(0, 0.62)
ax1.set_title("前瞻比率（HL=80）", color=FG, fontsize=14, pad=12, loc="left")
ax1.tick_params(colors=FG, labelsize=12)
for s in ax1.spines.values(): s.set_visible(False)
ax1.yaxis.grid(True, color=GRID, zorder=0)
ax1.set_axisbelow(True)

# 右：偏执词持平 vs 合作词崩塌（GPT-OSS-20B，相对变化）
ax2.set_facecolor(BG)
labels2 = ["偏执类词汇\n绝对频率", "合作类词汇\n用量"]
vals2 = [0, -57]
colors2 = [GRID, RED]
bars2 = ax2.bar(labels2, vals2, color=colors2, width=0.46, zorder=3)
ax2.axhline(0, color=FG, lw=1)
for b, v in zip(bars2, vals2):
    off = 3 if v >= 0 else -9
    ax2.text(b.get_x() + b.get_width() / 2, v + off, f"{v:+d}%",
             ha="center", color=FG, fontsize=14, fontweight="bold")
ax2.set_ylim(-75, 25)
ax2.set_title("扩记忆后词汇变化（GPT-OSS-20B）", color=FG, fontsize=14, pad=12, loc="left")
ax2.tick_params(colors=FG, labelsize=12)
for s in ax2.spines.values(): s.set_visible(False)
ax2.yaxis.grid(True, color=GRID, zorder=0)
ax2.set_axisbelow(True)

fig.suptitle("机制：塌的是前瞻意图，不是偏执", color=FG, fontsize=15, x=0.02, ha="left")
plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(f"{DIR}/02-mechanism-comparison.png", facecolor=BG, bbox_inches="tight")
plt.close()

print("OK: 01-memory-curse-curve.png, 02-mechanism-comparison.png")

# ── 04：记忆净化——HL=80 固定，80−X 轮换合成合作记录，X=2 时恢复 ──
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
labels = ["GPT-OSS-20B\n净化前（全真实历史）", "GPT-OSS-20B\n净化后（X=2）", "强模型恢复区间\n（X=2）"]
vals = [3.4, 36.3, 92.0]
colors = [RED, TEAL, GOLD]
bars = ax.barh(labels, vals, color=colors, height=0.52, zorder=3)
notes = ["3.4%", "36.3%", "87%–97%"]
for b, v, n in zip(bars, vals, notes):
    ax.text(v + 1.5, b.get_y() + b.get_height() / 2, n,
            va="center", ha="left", color=FG, fontsize=14, fontweight="bold")
ax.text(92.0, 2, "  Llama-3.3-70B 97.4%", va="center", ha="left", color=GOLD, fontsize=11)
ax.set_xlim(0, 112)
ax.set_xlabel("信任博弈合作率（%，HL=80 固定）", color=FG, fontsize=11)
ax.tick_params(colors=FG, labelsize=12)
for s in ax.spines.values(): s.set_visible(False)
ax.xaxis.grid(True, color=GRID, zorder=0)
ax.set_axisbelow(True)
ax.set_title("记忆净化：决定伤害的是记忆里「有什么」，不是「有多少」", color=FG, fontsize=14, pad=14, loc="left")
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(f"{DIR}/04-memory-purification.png", facecolor=BG, bbox_inches="tight")
plt.close()

print("OK: 04-memory-purification.png")
