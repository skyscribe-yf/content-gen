#!/usr/bin/env python3
"""多模态分歧篇脚本图：数字必须与 weixin.md 一致。

01-model-table.png: 国产旗舰视觉能力对照表
02-ablation.png: DeepSeek-VL 消融（MMLU：41.8 基线 → 100%图文 31.5(-10.3) / 70:30 41.5(-0.3)）
03-fusion-curve.png: 融合时机 vs 文本能力（后期拼接先降后恢复 vs 早期融合一路上行）
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT = Path(__file__).parent
for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

BG = "#F7F3EB"
INK = "#2C2A26"
AMBER = "#D97706"
RED = "#C2410C"
GREEN = "#3F6F4A"
MUTED = "#8A8478"
CARD = "#FFFCF6"
BLUE = "#0F4C81"


def _prep_ax(ax):
    ax.set_facecolor(BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=13)
    ax.title.set_color(INK)


# ---------- 01 国产旗舰对照表 ----------
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.axis("off")
fig.patch.set_facecolor(BG)

rows = [
    ("模型", "总参数", "视觉能力", "备注"),
    ("DeepSeek V4-Pro", "1.6T", "× 纯文本", "开源推理最强"),
    ("GLM-5.2", "744B", "× 纯文本", "1M 长上下文"),
    ("Kimi K3", "2.8T", "√ 原生多模态", "视觉反哺推理"),
    ("Qwen3.8-Max", "2.4T", "√ 原生视觉", "全模态"),
    ("MiniMax M3", "—", "√ 多模态融合", "性价比"),
]
ncol = 4
col_w = [0.30, 0.14, 0.26, 0.30]
y = 0.92
rh = 0.155
for i, row in enumerate(rows):
    x = 0.03
    for j, cell in enumerate(row):
        if i == 0:
            ax.text(x, y, cell, fontsize=13, fontweight="bold", color=INK,
                    ha="left", va="center")
        elif j == 2:
            color = RED if "×" in cell else GREEN
            ax.text(x, y, cell, fontsize=12.5, color=color, ha="left", va="center",
                    fontweight="bold")
        elif j == 0:
            ax.text(x, y, cell, fontsize=12.5, color=INK, ha="left", va="center",
                    fontweight="bold")
        else:
            ax.text(x, y, cell, fontsize=12, color=INK, ha="left", va="center")
        x += col_w[j]
    y -= rh
ax.text(0.03, y - 0.06, "数据截至 2026-08：DeepSeek/GLM 旗舰纯文本，Kimi/Qwen/MiniMax 原生多模态",
        fontsize=10.5, color=MUTED, ha="left")
plt.tight_layout()
plt.savefig(OUT / "01-model-table.png", dpi=200, facecolor=BG)
plt.close()

# ---------- 02 消融柱状（MMLU） ----------
fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor(BG)
_prep_ax(ax)

labels = ["基线\n(纯文本)", "100% 图文\n(-10.3)", "70% 图文\n+30% 文本\n(-0.3)"]
vals = [41.8, 31.5, 41.5]
colors = [MUTED, RED, GREEN]
bars = ax.bar(labels, vals, width=0.5, color=colors, zorder=3)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.7, f"{v}", ha="center",
            fontsize=15, fontweight="bold", color=INK)
ax.set_ylim(0, 48)
ax.set_ylabel("MMLU（文本能力）", fontsize=13, color=INK)
ax.set_title("给模型装眼睛：图文配比决定文本掉多少分\n（DeepSeek-VL 消融实验）",
             fontsize=15, fontweight="bold", color=INK, pad=14)
ax.grid(axis="y", color=MUTED, alpha=0.25, zorder=0)
plt.tight_layout()
plt.savefig(OUT / "02-ablation.png", dpi=200, facecolor=BG)
plt.close()

# ---------- 03 融合时机曲线 ----------
fig, ax = plt.subplots(figsize=(9, 5.4))
fig.patch.set_facecolor(BG)
_prep_ax(ax)

import numpy as np
x = np.linspace(0, 1, 100)
# 后期拼接：前期平稳 → 加视觉后明显掉 → 缓慢恢复
late = np.concatenate([
    np.linspace(40, 52, 55),
    np.linspace(52, 30, 15),
    np.linspace(30, 34, 30),
])
# 早期融合：一路上行
early = np.linspace(40, 66, 100)

ax.plot(x, late, color=RED, lw=2.8, label="后期拼接（先训文本，再贴视觉）")
ax.plot(x, early, color=GREEN, lw=2.8, label="早期融合（图文一起训）")

ax.annotate("加视觉后文本能力骤降", xy=(0.62, 46), xytext=(0.62, 58),
            arrowprops=dict(arrowstyle="->", color=RED), color=RED, fontsize=11.5)
ax.annotate("Kimi K2.5：只练视觉\n文本推理也变强", xy=(0.55, 54.3), xytext=(0.30, 60),
            arrowprops=dict(arrowstyle="->", color=GREEN), color=GREEN, fontsize=11.5)

ax.set_xlabel("训练进程 →", fontsize=13, color=INK)
ax.set_ylabel("文本能力（示意）", fontsize=13, color=INK)
ax.set_title("伤脑子的不是多模态，是融合时机", fontsize=15, fontweight="bold",
             color=INK, pad=14)
ax.set_xlim(0, 1)
ax.set_ylim(25, 72)
ax.legend(fontsize=12, facecolor=CARD, edgecolor=MUTED, loc="lower right")
ax.grid(color=MUTED, alpha=0.25, zorder=0)
plt.tight_layout()
plt.savefig(OUT / "03-fusion-curves.png", dpi=200, facecolor=BG)
plt.close()

print("done: 01-model-table.png / 02-ablation.png / 03-fusion-curves.png")
