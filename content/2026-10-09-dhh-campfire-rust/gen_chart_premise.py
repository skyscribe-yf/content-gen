#!/usr/bin/env python3
# dhh-campfire-rust 篇脚本图 6：06-premise-switch.png
# 第四节：前提换了，比赛就换了。旧前提「人读代码」，新前提「人不读代码」。
# productivity and developer joy 出自 The Register 2026-10-07 引 DHH。
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

OUT = Path("content/2026-10-09-dhh-campfire-rust")
OUT.mkdir(parents=True, exist_ok=True)

for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

RED, BLUE, GREY = "#C0392B", "#1A5276", "#7F8C8D"

fig, ax = plt.subplots(figsize=(8.6, 4.4), dpi=150)
ax.set_xlim(0, 10)
ax.set_ylim(0, 6.0)
ax.axis("off")

ax.text(0, 5.55, "他的反方：前提一换，比赛就换", fontsize=13.5, fontweight="bold", color="#2C3E50")

# 左：旧前提
ax.add_patch(FancyBboxPatch((0.1, 2.05), 4.3, 3.0,
                            boxstyle="round,pad=0.12,rounding_size=0.18",
                            fc="#F8F9F9", ec=GREY, lw=1.6))
ax.text(2.25, 4.65, "原来的前提", ha="center", fontsize=12, fontweight="bold", color=GREY)
ax.text(2.25, 3.85, "人还在读代码", ha="center", fontsize=13, fontweight="bold", color="#2C3E50")
ax.text(2.25, 3.05, "性能让位于\nproductivity and developer joy\n（人和开发体验）",
        ha="center", va="center", fontsize=10.5, color=GREY, linespacing=1.5)

# 右：新前提
ax.add_patch(FancyBboxPatch((5.6, 2.05), 4.3, 3.0,
                            boxstyle="round,pad=0.12,rounding_size=0.18",
                            fc="#EBF5FB", ec=BLUE, lw=1.6))
ax.text(7.75, 4.65, "换过之后的前提", ha="center", fontsize=12, fontweight="bold", color=BLUE)
ax.text(7.75, 3.85, "代码没人读了", ha="center", fontsize=13, fontweight="bold", color=BLUE)
ax.text(7.75, 3.05, "只看前沿 agent\n开箱交出来的那一版\n（丑、啰嗦 6 倍也不看）",
        ha="center", va="center", fontsize=10.5, color=BLUE, linespacing=1.5)

ax.annotate("", xy=(5.45, 3.55), xytext=(4.55, 3.55),
            arrowprops=dict(arrowstyle="->", color="#2C3E50", lw=2.4))

ax.text(0.1, 1.45, "前提一换，「专家能写出更快的 Elixir」就落在另一张牌上——他量的是开箱成绩，",
        fontsize=11.5, color="#2C3E50")
ax.text(0.1, 0.85, "而公开图上的 150 倍，落在几百个 commit 的优化之后。",
        fontsize=11.5, color=RED)
ax.text(0.1, 0.2, "DHH 09-28 / 10-04 两条推文；productivity and developer joy 出自 The Register 2026-10-07。",
        fontsize=10, color="#95A5A6")

fig.tight_layout()
fig.savefig(OUT / "06-premise-switch.png", bbox_inches="tight", facecolor="white")
print("saved", OUT / "06-premise-switch.png")
