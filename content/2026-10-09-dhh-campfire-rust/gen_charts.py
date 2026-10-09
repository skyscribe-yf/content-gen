#!/usr/bin/env python3
# dhh-campfire-rust 篇脚本图：01-two-rounds.png
# 只画两个已核对数字：初版 4.4 倍、公开图约 150 倍。不画未重数的 commit。
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

labels = ["初版\n（仓库自己的说明）", "公开图\n（10 月初，The Register 引）"]
values = [4.4, 150.3]  # 150.3 = 36260/241，图上标「约 150 倍」
colors = ["#95A5A6", "#C0392B"]

bars = ax.bar(labels, values, width=0.52, color=colors, edgecolor="none")
ax.set_yscale("log")
ax.set_ylim(1, 400)

ax.text(0, 4.4 * 1.25, "4.4 倍", ha="center", fontsize=15, fontweight="bold", color="#566573")
ax.text(1, 150.3 * 1.18, "约 150 倍", ha="center", fontsize=15, fontweight="bold", color="#C0392B")

# 中间箭头：不是同一轮
ax.annotate(
    "",
    xy=(1, 110), xytext=(0, 7),
    arrowprops=dict(arrowstyle="->", color="#1A5276", lw=2.0, connectionstyle="arc3,rad=-0.25"),
)
ax.text(
    0.5, 32,
    "中间隔着几百个 commit\n和十几个性能优化 PR（第三方清点）",
    ha="center", fontsize=11, color="#1A5276",
    bbox=dict(boxstyle="round,pad=0.4", fc="#EBF5FB", ec="#1A5276", lw=1.0, alpha=0.95),
)

ax.set_ylabel("房间页相对 Rails 的速度倍数（log）", fontsize=12)
ax.set_title("同一个房间页，两轮成绩：150 倍和 4.4 倍不是同一轮", fontsize=13)
ax.grid(True, axis="y", ls=":", alpha=0.4)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "01-two-rounds.png", bbox_inches="tight", facecolor="white")
print("saved", OUT / "01-two-rounds.png")
