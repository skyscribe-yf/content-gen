#!/usr/bin/env python3
"""本篇脚本配图（数字/结构图）。AI 概念图不承载数字，数字图全走脚本。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = "content/2026-10-08-multiagent-debate/"
BLUE, ORANGE, RED, GRAY = "#0F4C81", "#e07a2f", "#c0392b", "#9aa5b1"


# ---------- 05 误差复利曲线 ----------
fig, ax = plt.subplots(figsize=(10, 4.4))
ns = list(range(1, 21))
ys = [0.95 ** n * 100 for n in ns]
ax.plot(ns, ys, color=BLUE, lw=2.8, zorder=3)
ax.axhline(100, color=GRAY, lw=1.2, ls="--", zorder=1)
ax.scatter([1], [95], s=70, color=ORANGE, zorder=4)
ax.annotate("单步 95%", (1, 95), xytext=(1.4, 92), fontsize=13, color=ORANGE)
ax.scatter([10], [0.95 ** 10 * 100], s=80, color=RED, zorder=4)
ax.annotate("串 10 步：只剩 60%", (10, 0.95 ** 10 * 100), xytext=(10.6, 68),
            fontsize=14, fontweight="bold", color=RED,
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6))
ax.set_title("误差是乘法，不是加法：每步可靠率 95%", fontsize=16, fontweight="bold",
             color="#1f2933", pad=14)
ax.set_xlabel("任务串行步数 n", fontsize=12)
ax.set_ylabel("整体成功率（%）", fontsize=12)
ax.set_xlim(0.5, 20); ax.set_ylim(0, 108)
ax.grid(alpha=0.25, lw=0.7)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(OUT + "05-pn-curve.png", dpi=200)
plt.close(fig)

# ---------- 06 阿姆达尔天花板 ----------
fig, ax = plt.subplots(figsize=(10, 4.4))
NN = list(range(1, 17))
sp = [1 / (0.2 + 0.8 / n) for n in NN]
ax.plot(NN, NN, color=GRAY, lw=1.6, ls=":", zorder=2)
ax.annotate("理想：线性加速", (13.2, 13.2), xytext=(11.2, 14.3), fontsize=11, color=GRAY)
ax.plot(NN, sp, color=BLUE, lw=2.8, zorder=3)
ax.axhline(5, color=RED, lw=1.4, ls="--", zorder=1)
ax.text(15.7, 5.22, "上限 5 倍", fontsize=13, color=RED, ha="right")
ax.scatter([8], [1 / (0.2 + 0.8 / 8)], s=80, color=ORANGE, zorder=4)
ax.annotate("8 个 agent：只快 3.3 倍", (8, 3.333), xytext=(8.6, 1.9), fontsize=14,
            fontweight="bold", color=ORANGE,
            arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.6))
ax.set_title("并行有天花板：读结果、对齐、拍板是串行的（占两成）", fontsize=16,
             fontweight="bold", color="#1f2933", pad=14)
ax.set_xlabel("并行 agent 数 N", fontsize=12)
ax.set_ylabel("实际加速倍数", fontsize=12)
ax.set_xlim(0.5, 16); ax.set_ylim(0, 16)
ax.grid(alpha=0.25, lw=0.7)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(OUT + "06-amdahl-curve.png", dpi=200)
plt.close(fig)

# ---------- 07 四条派活规矩卡 ----------
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("什么时候派一群？我的四条规矩", fontsize=17, fontweight="bold",
             color="#1f2933", pad=16)
rules = [
    ("①", "容易分发的任务", "快速派出去"),
    ("②", "复杂有深度的任务", "自己干"),
    ("③", "复杂一点的编排流程", "交给更强的模型做收敛"),
    ("④", "仔细安排指令提示词", "防止无脑吞合成提示而停摆"),
]
h, gap = 0.16, 0.075
y0 = 0.88
for i, (no, left, right) in enumerate(rules):
    y = y0 - i * (h + gap) - h
    ax.add_patch(FancyBboxPatch((0.06, y), 0.88, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                fc="#eef3f8" if i % 2 == 0 else "#f7f9fb", ec=BLUE, lw=1.6, zorder=2))
    ax.text(0.10, y + h / 2, no, ha="center", va="center", fontsize=17, color=ORANGE,
            fontweight="bold", zorder=3)
    ax.text(0.16, y + h / 2, left, ha="left", va="center", fontsize=13.5, color="#1f2933", zorder=3)
    ax.text(0.55, y + h / 2, "→", ha="center", va="center", fontsize=14, color=GRAY, zorder=3)
    ax.text(0.60, y + h / 2, right, ha="left", va="center", fontsize=13.5, color=BLUE,
            fontweight="bold", zorder=3)
fig.tight_layout()
fig.savefig(OUT + "07-rules-card.png", dpi=200)
plt.close(fig)

print("charts done")
