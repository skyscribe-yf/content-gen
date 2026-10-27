#!/usr/bin/env python3
"""C3 安全账数据图：01 约束幸存率 / 03 论文违反率对照 / 05 规矩放置三层。
数据源：scripts/constraint_survival_scan.py 全量扫描输出（本机 202 次 compaction）；
论文数字：arXiv 2606.22528 摘要（Governance Decay）。配色沿用项目 house style。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch

FP = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
plt.rcParams["axes.unicode_minus"] = False
BLUE, SUB, INK, GOLD, LINE, BG = "#0F4C81", "#5B7A99", "#1A2733", "#B8860B", "#C9D6E0", "#FFFFFF"
RED = "#A33A3A"
GREEN = "#3A7A5A"


def frame(fig, title, sub):
    fig.patch.set_facecolor(BG)
    fig.text(0.5, 0.965, title, ha="center", fontproperties=FP, fontsize=20, color=INK)
    fig.text(0.5, 0.905, sub, ha="center", fontproperties=FP, fontsize=11.5, color=SUB)


# ---- 01 约束幸存率：两种形态，两种命 ----
fig, ax = plt.subplots(figsize=(10, 5.6))
frame(fig, "两种规矩，两种命", "Pi 本机 202 次压缩、2,556 条约束实例的幸存率（按形态分）")
rows = [
    ("随口叮嘱\n（只在会话里说过一次）", 56.0, 19.7, 24.4, "n=193"),
    ("结构化规则\n（skill / 系统注入）", 90.8, 8.9, 0.3, "n=2,363"),
]
y = [0, 1]
for (lab, s, p, l, n), yy in zip(rows, y):
    ax.barh(yy, s, 0.52, color=BLUE)
    ax.barh(yy, p, 0.52, left=s, color=LINE)
    ax.barh(yy, l, 0.52, left=s + p, color=RED)
    ax.text(s / 2, yy, f"幸存 {s}%", ha="center", va="center",
            fontproperties=FP, fontsize=13, color="#FFFFFF")
    if p > 6:
        ax.text(s + p / 2, yy, f"{p}%", ha="center", va="center",
                fontproperties=FP, fontsize=11, color=INK)
    ax.text(s + p + l / 2, yy + 0.31, f"丢失 {l}%", ha="center",
            fontproperties=FP, fontsize=13.5, color=RED)
    ax.text(103, yy, n, ha="left", va="center", fontproperties=FP, fontsize=11.5, color=SUB)
ax.set_yticks(y)
ax.set_yticklabels([r[0] for r in rows], fontproperties=FP, fontsize=12.5)
ax.set_xlim(0, 118)
ax.set_ylim(-0.55, 1.62)
ax.set_xlabel("占实例比例（%）", fontproperties=FP, fontsize=12.5)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("01-survival.png", bbox_inches="tight", facecolor=BG)
plt.close(fig)

# ---- 03 论文对照：幸存就是违反率的开关 ----
fig, ax = plt.subplots(figsize=(10, 5.6))
frame(fig, "约束活着，违反率是 0；丢了，38", "Governance Decay 论文 ConstraintRot 基准：7 个模型、1,323 个 episode")
bars = [("约束活过压缩", 0, GREEN), ("约束被摘要丢掉", 38, RED)]
x = [0, 1]
for (lab, v, c), xx in zip(bars, x):
    ax.bar(xx, v, 0.42, color=c)
    ax.text(xx, v + 1.2, f"{v}%", ha="center", fontproperties=FP, fontsize=20, color=c)
ax.annotate("软性组织策略的衰减\n是硬安全规范的 8.3 倍", xy=(0.5, 19), ha="center",
            fontproperties=FP, fontsize=13.5, color=INK,
            bbox=dict(boxstyle="round,pad=0.5", fc="#F5EFE0", ec=GOLD, lw=1.6))
ax.set_xticks(x)
ax.set_xticklabels([b[0] for b in bars], fontproperties=FP, fontsize=13.5)
ax.set_ylabel("任务违规率（%）", fontproperties=FP, fontsize=13)
ax.set_ylim(0, 46)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("03-violation.png", bbox_inches="tight", facecolor=BG)
plt.close(fig)

# ---- 05 规矩放置三层 ----
fig, ax = plt.subplots(figsize=(10, 5.6))
frame(fig, "规矩放在哪，决定它活多久", "三层位置，压缩够得着的只有第一层")
cards = [
    ("会话历史", "压缩区", "随口叮嘱的规矩住在这里\n幸存率 56%\n四分之一没能活下来", RED),
    ("系统提示 / AGENTS.md", "每轮重新注入", "写进指令文件\n压缩前后都在\nagent 随时能翻到", BLUE),
    ("工具层 / 配置", "压缩够不着", "授权与边界放这里\nfail-closed：不确定\n就不执行", GREEN),
]
for i, (name, tag, desc, c) in enumerate(cards):
    cx = 0.035 + i * 0.325
    ax.add_patch(FancyBboxPatch((cx, 0.10), 0.28, 0.70, boxstyle="round,pad=0.012",
                                fc="#FFFFFF", ec=c, lw=2.2))
    ax.text(cx + 0.14, 0.72, name, ha="center", fontproperties=FP, fontsize=15.5, color=c)
    ax.text(cx + 0.14, 0.60, tag, ha="center", fontproperties=FP, fontsize=12, color=INK)
    ax.text(cx + 0.14, 0.32, desc, ha="center", fontproperties=FP, fontsize=11,
            color=SUB, linespacing=1.7)
ax.set_xlim(0, 1)
ax.set_ylim(0, 0.86)
ax.axis("off")
fig.savefig("05-where.png", bbox_inches="tight", facecolor=BG)
plt.close(fig)

print("done: 01-survival / 03-violation / 05-where")
