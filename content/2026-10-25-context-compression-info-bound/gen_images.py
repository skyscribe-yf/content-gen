#!/usr/bin/env python3
"""C1 数据图：02 分月重复调用 / 03 Fano 457 / 04 率失真曲线。配色沿用项目 house style。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np

FP = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
plt.rcParams["axes.unicode_minus"] = False
BLUE, SUB, INK, GOLD, LINE, BG = "#0F4C81", "#5B7A99", "#1A2733", "#B8860B", "#C9D6E0", "#FFFFFF"

def frame(fig, title, sub):
    fig.patch.set_facecolor(BG)
    fig.text(0.5, 0.965, title, ha="center", fontproperties=FP, fontsize=20, color=INK)
    fig.text(0.5, 0.905, sub, ha="center", fontproperties=FP, fontsize=11.5, color=SUB)

# ---- 02 分月重复调用 ----
fig, ax = plt.subplots(figsize=(10, 5.6))
frame(fig, "本机 202 次压缩的分月拆解", "压缩次数 vs 压缩后 25 步内重复调用（Pi 会话日志，2026-10-24 扫描，观察性口径）")
months = ["6月", "7月", "8月", "9月", "10月"]
comp, dup = [94, 67, 22, 6, 13], [13, 31, 1, 2, 0]
x, w = np.arange(5), 0.38
ax.bar(x - w / 2, comp, w, color=LINE, label="压缩次数")
ax.bar(x + w / 2, dup, w, color=GOLD, label="重复调用次数")
for i, (c, d) in enumerate(zip(comp, dup)):
    ax.text(i - w / 2, c + 1.5, str(c), ha="center", fontproperties=FP, fontsize=12, color=SUB)
    ax.text(i + w / 2, d + 1.5, str(d), ha="center", fontproperties=FP, fontsize=12, color=INK)
ax.annotate("峰值：31/67", xy=(1 + w / 2, 31), xytext=(1.7, 52), fontproperties=FP,
            fontsize=13, color=GOLD, arrowprops=dict(arrowstyle="->", color=GOLD))
ax.set_xticks(x); ax.set_xticklabels(months, fontproperties=FP, fontsize=13)
ax.legend(prop=FP, loc="upper right", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("02-monthly-dups.png", bbox_inches="tight", facecolor=BG); plt.close(fig)

# ---- 03 Fano 457 ----
fig = plt.figure(figsize=(10, 5.6))
frame(fig, "457 选 1：信息不够时，失败有下界", "AppWorld 的 457 个 API（arXiv 2407.18901）；摘要对该选择零信息（简化模型）")
axL = fig.add_axes([0.04, 0.10, 0.46, 0.70])
cols, rows = 23, 20
for idx in range(cols * rows):
    r, c = divmod(idx, cols)
    if idx < 457:
        axL.add_patch(plt.Rectangle((c, rows - 1 - r), 0.8, 0.8,
                                    color=GOLD if idx == 200 else "#DCE6F0"))
axL.set_xlim(-0.5, cols); axL.set_ylim(-0.5, rows)
axL.set_aspect("equal"); axL.axis("off")
axL.text(cols / 2, -1.8, "457 个等可能动作，只有 1 个正确（金色）", ha="center",
         fontproperties=FP, fontsize=12, color=SUB)
axR = fig.add_axes([0.56, 0.08, 0.42, 0.75]); axR.axis("off")
axR.text(0.5, 0.60, "≥ 88.7%", ha="center", fontproperties=FP, fontsize=52, color=GOLD)
axR.text(0.5, 0.38, "错误率下界", ha="center", fontproperties=FP, fontsize=15, color=INK)
axR.text(0.5, 0.20, "Pe ≥ 1 − 1/log2(457)\n（Fano 不等式，简化 M 选一任务，非真实失败率）",
         ha="center", fontproperties=FP, fontsize=11.5, color=SUB, linespacing=1.6)
fig.savefig("03-fano-457.png", bbox_inches="tight", facecolor=BG); plt.close(fig)

# ---- 04 率失真曲线 ----
fig, ax = plt.subplots(figsize=(9.5, 5.6))
frame(fig, "率失真：不声明失真，压缩率没有意义",
      "二值信源 + 汉明失真：R(D) = H(p) − H(D)，p = 0.5（Cover & Thomas 第 10 章标准结果）")
D = np.linspace(1e-9, 0.5, 400)
H = lambda d: -d * np.log2(d) - (1 - d) * np.log2(1 - d)
ax.plot(D, 1 - H(D), color=BLUE, lw=3)
ax.scatter([0], [1], s=90, color=GOLD, zorder=5)
ax.annotate("D = 0：不可压缩的底\nR = H(p) = 1 bit", xy=(0, 1), xytext=(0.09, 0.86),
            fontproperties=FP, fontsize=12.5, color=INK,
            arrowprops=dict(arrowstyle="->", color=SUB))
ax.scatter([0.5], [0], s=90, color=SUB, zorder=5)
ax.annotate("D = 0.5：可以压到 0\n（允许一半失真）", xy=(0.5, 0), xytext=(0.27, 0.16),
            fontproperties=FP, fontsize=12.5, color=INK,
            arrowprops=dict(arrowstyle="->", color=SUB))
ax.set_xlabel("失真 D（允许丢失 / 错误的预算）", fontproperties=FP, fontsize=13, color=INK)
ax.set_ylabel("信息率 R（bit/符号）", fontproperties=FP, fontsize=13, color=INK)
ax.set_xlim(-0.02, 0.56); ax.set_ylim(-0.06, 1.12)
for lbl in ax.get_xticklabels() + ax.get_yticklabels():
    lbl.set_fontproperties(FP); lbl.set_fontsize(11)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("04-rate-distortion.png", bbox_inches="tight", facecolor=BG); plt.close(fig)
print("3 figures done")
