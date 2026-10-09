#!/usr/bin/env python3
# dhh-campfire-rust 篇脚本图 5：05-commit-gap.png
# 横向不对等：Rust 版几百个 commit 跨好几天，另外几份只有初始改写的 1~2 个。
# 出自 José Valim（Elixir 作者）2026-10-05。图为示意，非精确比例。
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

fig, ax = plt.subplots(figsize=(8.6, 4.2), dpi=150)
ax.set_xlim(0, 10)
ax.set_ylim(0, 5.6)
ax.axis("off")

ax.text(0, 5.2, "同一张记分牌，两种投入量", fontsize=13.5, fontweight="bold", color="#2C3E50")

# Rust：长条（示意，非精确比例）
ax.text(0, 4.05, "Rust 版", fontsize=12, fontweight="bold", color=RED, va="center")
ax.add_patch(FancyBboxPatch((1.5, 3.6), 7.6, 0.9,
                            boxstyle="round,pad=0.04,rounding_size=0.10",
                            fc="#FDEDEC", ec=RED, lw=1.5))
# 用竖线示意「很多次提交」
for i in range(1, 38):
    x = 1.5 + i * (7.6 / 38)
    ax.plot([x, x], [3.72, 4.38], color=RED, lw=0.8, alpha=0.55)
ax.text(5.3, 4.05, "几百个 commit，跨好几天", ha="center", va="center",
        fontsize=12, fontweight="bold", color=RED)

# 其它：短条
ax.text(0, 2.35, "Elixir / Go 版", fontsize=12, fontweight="bold", color=GREY, va="center")
ax.add_patch(FancyBboxPatch((1.5, 1.9), 0.55, 0.9,
                            boxstyle="round,pad=0.04,rounding_size=0.10",
                            fc="#F2F4F4", ec=GREY, lw=1.5))
ax.text(2.3, 2.35, "初始改写的 1~2 个 commit", fontsize=12, color=GREY, va="center")

# 分界线
ax.plot([0, 10], [1.45, 1.45], color="#D5D8DC", lw=1.0)

ax.text(0, 0.95, "各份要求也不一样：Go 版说明把 Rust 当范本，Elixir 版对标的是 Rails。",
        fontsize=11.5, color=BLUE)
ax.text(0, 0.3, "出自 José Valim（Elixir 作者）2026-10-05；示意图，非精确比例。",
        fontsize=10, color="#95A5A6")

fig.tight_layout()
fig.savefig(OUT / "05-commit-gap.png", bbox_inches="tight", facecolor="white")
print("saved", OUT / "05-commit-gap.png")
