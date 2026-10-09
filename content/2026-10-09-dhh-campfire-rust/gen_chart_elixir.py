#!/usr/bin/env python3
# dhh-campfire-rust 篇脚本图 3：03-elixir-queue.png
# 结构示意，无数字。对应第三节：agent 交的 Elixir 把 SQL 收进一个 GenServer → 查询串行。
# 上排=这份代码的样子，下排=Elixir 本来的样子。Zach Daniel 2026-10-04 的说法。
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

RED, BLUE, GREY = "#C0392B", "#1A5276", "#566573"
XS = [0.55, 2.45, 4.35, 6.25]

fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=150)
ax.set_xlim(0, 10)
ax.set_ylim(0, 7.6)
ax.axis("off")


def box(x, y, w, h, label, ec, fs=11):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.12",
                                fc="white", ec=ec, lw=1.5))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, color=ec)


# ── 上排：串行 ──────────────────────────────────────────────
ax.text(0, 7.15, "这份 agent 交的 Elixir 版", fontsize=12.5, fontweight="bold", color=RED)
ax.text(3.0, 7.15, "：SQL 查询收进一个 GenServer", fontsize=12, color=GREY)

ax.add_patch(FancyBboxPatch((0.3, 5.0), 7.75, 1.6,
                            boxstyle="round,pad=0.12,rounding_size=0.18",
                            fc="#FDEDEC", ec=RED, lw=1.3, ls="--"))
ax.text(0.5, 6.41, "GenServer（单进程）", fontsize=10, color=RED)

for i, x in enumerate(XS):
    box(x, 5.4, 1.5, 0.78, f"查询 {i + 1}", RED)
    if i:
        ax.annotate("", xy=(x - 0.08, 5.79), xytext=(XS[i - 1] + 1.56, 5.79),
                    arrowprops=dict(arrowstyle="->", color=RED, lw=1.8))
ax.annotate("", xy=(9.1, 5.79), xytext=(8.12, 5.79),
            arrowprops=dict(arrowstyle="->", color=RED, lw=1.8))
ax.text(9.15, 5.79, "数据库", fontsize=11, color=GREY, va="center")
ax.text(0, 4.55, "所有查询排成一队，一次只办一件：后面的等前面的", fontsize=11.5, color=RED)

# ── 下排：并发（四条独立通道，不交叉） ──────────────────────
ax.text(0, 3.85, "Elixir 本来可以", fontsize=12.5, fontweight="bold", color=BLUE)
ax.text(2.45, 3.85, "：同时查，不排队", fontsize=12, color=GREY)

rows = [3.15, 2.50, 1.85, 1.20]
for yc in rows:
    box(1.2, yc - 0.26, 1.5, 0.52, "查询", BLUE, fs=10.5)
    ax.annotate("", xy=(7.58, yc), xytext=(2.78, yc),
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))
ax.add_patch(FancyBboxPatch((7.6, 0.94), 1.6, 2.47,
                            boxstyle="round,pad=0.06,rounding_size=0.12",
                            fc="#EBF5FB", ec=BLUE, lw=1.5))
ax.text(8.4, 2.18, "数据库", ha="center", va="center", fontsize=11, color=BLUE)
ax.text(0, 0.35, "每个查询各走各的，互相不等：语言本身没拦着", fontsize=11.5, color=BLUE)

fig.tight_layout()
fig.savefig(OUT / "03-elixir-queue.png", bbox_inches="tight", facecolor="white")
print("saved", OUT / "03-elixir-queue.png")
