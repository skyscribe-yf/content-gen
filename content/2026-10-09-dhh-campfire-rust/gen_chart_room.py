#!/usr/bin/env python3
# dhh-campfire-rust 篇脚本图 2：02-room-page.png
# 房间页四个已核对数字（The Register 2026-10-07 引 DHH 公开图）。
# log 轴，Rust 与 Rails 用强对比色，其余弱化，突出 150 倍差距。
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

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

fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=150)

labels = ["Rust", "Go", "Elixir", "Rails"]
values = [36260, 3860, 722, 241]
colors = ["#C0392B", "#7F8C8D", "#7F8C8D", "#1A5276"]

bars = ax.bar(labels, values, width=0.55, color=colors, edgecolor="none")
ax.set_yscale("log")
ax.set_ylim(100, 90000)

for b, v in zip(bars, values):
    ax.text(b.get_x() + b.get_width() / 2, v * 1.15, f"{v:,}", ha="center",
            fontsize=13, fontweight="bold",
            color=b.get_facecolor())

# 150 倍标注
ax.annotate(
    "约 150 倍",
    xy=(0, 36260 * 0.55), xytext=(0.9, 20000),
    fontsize=13, fontweight="bold", color="#C0392B",
    arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.6),
    bbox=dict(boxstyle="round,pad=0.35", fc="#FDEDEC", ec="#C0392B", lw=1.0),
)

ax.set_ylabel("房间页每秒请求数（log）", fontsize=12)
ax.set_title("公开图上的房间页：36,260 对 241（The Register 2026-10-07 引）", fontsize=12.5)
ax.grid(True, axis="y", ls=":", alpha=0.4)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "02-room-page.png", bbox_inches="tight", facecolor="white")
print("saved", OUT / "02-room-page.png")
