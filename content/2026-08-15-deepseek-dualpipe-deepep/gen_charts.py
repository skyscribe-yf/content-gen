#!/usr/bin/env python3
# gen_charts.py — DeepEP/DualPipe 篇的 2 张脚本图（数字由脚本承载，AI 图不承载数字）
#   04-bubble-chart.png  气泡账：1F1B / ZB1P / DualPipe（V3 报告 Table 2 公式 + 演示值）
#   06-cb-chart.png      C/B 判据：V4-Pro 门槛 6144 vs H800 的 NVLink / IB
# 数字与 experiment.py 一致。
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

OUT = Path(__file__).parent
for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

C1, C2, C3 = "#3b6ea5", "#8a9bb5", "#e8a33d"  # 蓝 / 灰蓝 / 橙

# ── 04-bubble-chart.png ─────────────────────────────────────
F, B, W, FnB = 1.0, 2.0, 0.8, 2.2  # 与 experiment.py 同款演示值
pps = [4, 8, 16, 32]
b1 = [(pp - 1) * (F + B) for pp in pps]
bz = [(pp - 1) * (F + B - 2 * W) for pp in pps]
bd = [(pp / 2 - 1) * (FnB + B - 3 * W) for pp in pps]

fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=150)
x = np.arange(len(pps))
w = 0.26
ax.bar(x - w, b1, w, label="1F1B", color=C1)
ax.bar(x, bz, w, label="ZB1P", color=C2)
ax.bar(x + w, bd, w, label="DualPipe", color=C3)
ax.set_xticks(x)
ax.set_xticklabels([f"PP={p}" for p in pps], fontsize=12)
ax.set_ylabel("气泡时间（演示单位，越小越好）", fontsize=12)
ax.set_title("流水线气泡：1F1B vs ZB1P vs DualPipe（演示值）", fontsize=14)
ax.legend(fontsize=11, frameon=False)
for xi, v in zip(x - w, b1):
    ax.text(xi, v + 1.5, f"{v:.0f}", ha="center", fontsize=10, color=C1)
for xi, v in zip(x + w, bd):
    ax.text(xi, v + 1.5, f"{v:.1f}", ha="center", fontsize=10, color=C3)
ax.spines[["top", "right"]].set_visible(False)
ax.set_ylim(0, max(b1) * 1.12)
plt.tight_layout()
plt.savefig(OUT / "04-bubble-chart.png", bbox_inches="tight")
plt.close()

# ── 06-cb-chart.png ─────────────────────────────────────────
threshold = 2 * 3072  # 2d = 6144 FLOPs/Byte（V4-Pro）
cb_nv = 1.98e15 / 900e9     # NVLink：≈2200
cb_ib = 1.98e15 / 50e9      # IB：≈39600

fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=150)
labels = ["NVLink\n900 GB/s", "IB\n50 GB/s", "藏满门槛\n2d = 6144"]
vals = [cb_nv, cb_ib, threshold]
colors = ["#2e7d32", "#c62828", "#666666"]
barl = ax.bar(labels, vals, [0.32, 0.32, 0.05], color=colors)
for b, v in zip(barl, vals):
    ax.text(b.get_x() + b.get_width() / 2, v * 1.03,
            f"{v:,.0f}", ha="center", fontsize=13, fontweight="bold")
ax.axhline(threshold, color="#666666", ls="--", lw=1.2)
ax.set_yscale("log")
ax.set_ylabel("C/B（FLOPs/Byte，对数轴）", fontsize=12)
ax.set_title("通信藏得满吗？C/B 判据：C/B ≤ 6144", fontsize=14)
ax.annotate("藏得满 ✓", xy=(0, threshold), xytext=(0.22, 500),
            fontsize=13, color="#2e7d32",
            arrowprops=dict(arrowstyle="->", color="#2e7d32"))
ax.annotate("藏不满 ×", xy=(1, cb_ib), xytext=(1.62, 20000),
            fontsize=13, color="#c62828",
            arrowprops=dict(arrowstyle="->", color="#c62828"))
ax.spines[["top", "right"]].set_visible(False)
ax.set_ylim(1e2, 2e5)
plt.tight_layout()
plt.savefig(OUT / "06-cb-chart.png", bbox_inches="tight")
plt.close()

print("OK: 04-bubble-chart.png, 06-cb-chart.png")
