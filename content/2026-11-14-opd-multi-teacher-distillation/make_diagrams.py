#!/usr/bin/env python3
"""OPD 篇脚本图：01 三范式归一化分对比 + 03 换师前后三项诊断。深色底 + 金/青强调。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False

BG, FG, GOLD, TEAL, RED, GRID = "#101418", "#E8E6E1", "#E8B45A", "#4FB3A9", "#D9603B", "#2A2F36"
DIR = "content/2026-11-14-opd-multi-teacher-distillation"

# ── 01：六种整合方案归一化分（同源老师，Qwen3-30B-A3B 三域）──
names = ["朴素权重平均", "级联 RL", "off-policy 微调", "任务算术合并", "Mix-RL（数据空间）", "OPD（策略空间）"]
vals = [0.3280, 0.7752, 0.8241, 0.8574, 0.8818, 0.9373]
colors = [GRID, GRID, GRID, GRID, TEAL, GOLD]

fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
bars = ax.barh(names, vals, color=colors, height=0.62, zorder=3)
for b, v in zip(bars, vals):
    ax.text(v + 0.012, b.get_y() + b.get_height() / 2, f"{v:.4f}",
            va="center", ha="left", color=FG, fontsize=12)
ax.set_xlim(0, 1.06)
ax.set_xlabel("三域归一化分（老师 = 1.0000）", color=FG, fontsize=11)
ax.tick_params(colors=FG, labelsize=12)
for s in ax.spines.values(): s.set_visible(False)
ax.xaxis.grid(True, color=GRID, zorder=0)
ax.set_axisbelow(True)
ax.set_title("同源老师下，六种整合思路的归一化分", color=FG, fontsize=15, pad=14, loc="left")
plt.tight_layout()
plt.savefig(f"{DIR}/01-three-paradigms.png", facecolor=BG, bbox_inches="tight")
plt.close()

# ── 03：换师前后三项诊断 ──
groups = ["合并归一化分", "起始 reverse-KL\n（逐 token 距离）", "输出熵"]
same = [0.9373, 0.04, 0.30]
swap = [0.6003, 0.19, 0.21]

import numpy as np
x = np.arange(len(groups)); w = 0.34
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
b1 = ax.bar(x - w / 2, same, w, label="同源老师", color=TEAL, zorder=3)
b2 = ax.bar(x + w / 2, swap, w, label="换成更强的老师", color=RED, zorder=3)
for bars in (b1, b2):
    for b in bars:
        v = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, v + 0.018, f"{v:.4f}".rstrip("0").rstrip("."),
                ha="center", color=FG, fontsize=12)
ax.set_xticks(x); ax.set_xticklabels(groups, color=FG, fontsize=12)
ax.set_ylim(0, 1.08)
ax.tick_params(colors=FG)
for s in ax.spines.values(): s.set_visible(False)
ax.yaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
leg = ax.legend(facecolor=BG, edgecolor=GRID, fontsize=12, loc="upper right")
for t in leg.get_texts(): t.set_color(FG)
ax.set_title("换个更强的老师，三项诊断全变了", color=FG, fontsize=15, pad=14, loc="left")
plt.tight_layout()
plt.savefig(f"{DIR}/03-teacher-swap.png", facecolor=BG, bbox_inches="tight")
plt.close()
print("01/03 脚本图完成")
