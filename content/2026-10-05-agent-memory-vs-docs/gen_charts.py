#!/usr/bin/env python3
"""本篇脚本配图（结构/概念图，无虚构数字）。AI 图不承载数字/结构，全走脚本。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = "content/2026-10-05-agent-memory-vs-docs/"
BLUE, ORANGE, RED, GRAY = "#0F4C81", "#e07a2f", "#c0392b", "#9aa5b1"


def box(ax, x, y, w, h, text, fc="#eef3f8", ec=BLUE, tc="#1f2933", fs=13, lw=1.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, zorder=3)


def arrow(ax, p, q, color=BLUE, lw=2.0, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=16,
                                 lw=lw, color=color, linestyle=ls, zorder=1))


# ---------- 01 记忆插件四步流水线 ----------
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("市面上的记忆插件，架构几乎都一样", fontsize=16, fontweight="bold", color="#1f2933", pad=14)
steps = ["扫会话\n抽片段", "塞进\n向量库", "每次提问\n注入 top-5"]
xs = [0.06, 0.38, 0.70]
for x, t in zip(xs, steps):
    box(ax, x, 0.52, 0.24, 0.26, t, fs=13)
for i in range(len(xs) - 1):
    arrow(ax, (xs[i] + 0.24, 0.65), (xs[i + 1], 0.65), color=BLUE, lw=2.2)
# 回环：不够 → 检索工具
arrow(ax, (0.94, 0.52), (0.94, 0.24), color=ORANGE)
arrow(ax, (0.94, 0.24), (0.30, 0.24), color=ORANGE)
arrow(ax, (0.30, 0.24), (0.30, 0.52), color=ORANGE)
ax.text(0.62, 0.19, "还不够？再给它一个检索工具", ha="center", va="top", fontsize=12, color=ORANGE)
ax.text(0.5, 0.88, "每一步都在烧 token —— 问题却可能从一开始就问错了",
        ha="center", va="center", fontsize=12.5, color="#52606d")
plt.tight_layout()
plt.savefig(OUT + "01-memory-pipeline.png", dpi=160)
plt.close()

# ---------- 02 相似度只捞回孤立片段 ----------
fig, ax = plt.subplots(figsize=(10, 4.4))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("相似度只捞回“看起来像”的孤立片段", fontsize=16, fontweight="bold", color="#1f2933", pad=14)
ax.text(0.5, 0.86, "要拼 3 段才能得到的答案", ha="center", fontsize=12.5, color="#52606d")
box(ax, 0.10, 0.44, 0.22, 0.24, "片段 A\n（被召回）", fc="#e8f1f8", ec=BLUE)
box(ax, 0.39, 0.44, 0.22, 0.24, "片段 B\n（没被召回）", fc="#f0f0f0", ec=GRAY, tc="#8a94a0", lw=1.4)
box(ax, 0.68, 0.44, 0.22, 0.24, "片段 C\n（被召回）", fc="#e8f1f8", ec=BLUE)
arrow(ax, (0.32, 0.56), (0.39, 0.56), color=BLUE)
arrow(ax, (0.61, 0.56), (0.68, 0.56), color=GRAY, ls=(0, (4, 3)))
ax.text(0.50, 0.40, "字面不像 → 漏掉", ha="center", va="top", fontsize=11.5, color="#52606d")
ax.text(0.5, 0.16, "reranker 只能在“已召回”的里重排，救不回没进门的 B",
        ha="center", fontsize=12.5, color=RED)
plt.tight_layout()
plt.savefig(OUT + "02-recall-gap.png", dpi=160)
plt.close()

# ---------- 03 三条自检问题卡 ----------
fig, ax = plt.subplots(figsize=(9, 5.4))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("装“记忆”之前，先过这三问", fontsize=16, fontweight="bold", color="#1f2933", pad=14)
qs = [
    ("1", "它召回的是 what，还是 why？", "事实也许捞得回；“当初为什么这么定”常常捞不回"),
    ("2", "跨段关系，它拼得出来吗？", "要跳几处的答案，单段相似度天生拼不出"),
    ("3", "过期和错的，谁发现？", "能不能被审计、被删掉，还是只增不减"),
]
y = 0.70
for n, q, sub in qs:
    ax.add_patch(FancyBboxPatch((0.06, y), 0.88, 0.20,
                                boxstyle="round,pad=0.02,rounding_size=0.03",
                                fc="#f4f7fa", ec=BLUE, lw=1.6, zorder=1))
    ax.text(0.12, y + 0.10, n, ha="center", va="center", fontsize=22, color=ORANGE, fontweight="bold")
    ax.text(0.18, y + 0.135, q, ha="left", va="center", fontsize=14, color="#1f2933", fontweight="bold")
    ax.text(0.18, y + 0.055, sub, ha="left", va="center", fontsize=11, color="#52606d")
    y -= 0.24
plt.tight_layout()
plt.savefig(OUT + "03-checklist.png", dpi=160)
plt.close()

print("配图已生成：01-memory-pipeline.png / 02-recall-gap.png / 03-checklist.png")
