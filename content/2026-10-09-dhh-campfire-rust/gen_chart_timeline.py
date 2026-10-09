#!/usr/bin/env python3
# dhh-campfire-rust 篇脚本图 4：04-scoreboard-timeline.png
# 时间线，对应第五节：第一天 Rust 约 150 倍，第二天老 C 领先。
# 五个节点日期/说法全部出自正文与参考资料（DHH 09-28 / 10-04 / 10-08；第三方 10-05~06；The Register 10-07）。
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

RED, BLUE, GREY = "#C0392B", "#1A5276", "#7F8C8D"

EVENTS = [
    (1.15, "09-28", "代码丑、比人写的啰嗦 6 倍\n他一眼没看", +1, GREY),
    (3.05, "10-04", "要量的是 agent\n开箱交出来的那一版", -1, GREY),
    (4.95, "10-05~06", "第三方清点：几百个 commit\n十几个性能优化 PR", +1, GREY),
    (6.85, "10-07", "报道引图：Rust 约 150 倍", -1, RED),
    (8.75, "10-08", "Good old C is now in the lead\n老 C 领先了", +1, BLUE),
]

fig, ax = plt.subplots(figsize=(8.6, 4.4), dpi=150)
ax.set_xlim(0, 10.6)
ax.set_ylim(-3.5, 3.5)
ax.axis("off")

ax.annotate("", xy=(10.5, 0), xytext=(0.3, 0),
            arrowprops=dict(arrowstyle="->", color=GREY, lw=2.0))

for x, date, text, side, color in EVENTS:
    ax.plot([x, x], [0, 0.42 * side], color=color, lw=2.4, solid_capstyle="round")
    ax.text(x, 0.62 * side, date, ha="center", va="bottom" if side > 0 else "top",
            fontsize=11, fontweight="bold", color=color)
    ax.text(x, 1.12 * side, text, ha="center", va="bottom" if side > 0 else "top",
            fontsize=10, color="#2C3E50",
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=color, lw=1.1))

ax.text(0.3, 3.15, "这场对账的时间线", fontsize=13.5, fontweight="bold", color="#2C3E50")
ax.text(0.3, -3.2, "第一天 Rust 领先，第二天换成 C：这张记分牌上的数字，保质期只有一天",
        fontsize=11.5, color=RED)

fig.tight_layout()
fig.savefig(OUT / "04-scoreboard-timeline.png", bbox_inches="tight", facecolor="white")
print("saved", OUT / "04-scoreboard-timeline.png")
