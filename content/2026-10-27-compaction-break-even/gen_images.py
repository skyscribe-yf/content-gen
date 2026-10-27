#!/usr/bin/env python3
"""C2 钱账数据图：01 缓存击穿恢复 / 02 N*–ρ 曲线 / 03 ρ 阶梯回本 / 04 三家 harness 对照。
数据源：compaction_controlled.json（scripts/compaction_stats.py 产出）。配色沿用项目 house style。"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch
import numpy as np

FP = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
plt.rcParams["axes.unicode_minus"] = False
BLUE, SUB, INK, GOLD, LINE, BG = "#0F4C81", "#5B7A99", "#1A2733", "#B8860B", "#C9D6E0", "#FFFFFF"

S = [s for s in json.load(open("compaction_controlled.json"))["samples"]]


def med(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def frame(fig, title, sub):
    fig.patch.set_facecolor(BG)
    fig.text(0.5, 0.965, title, ha="center", fontproperties=FP, fontsize=20, color=INK)
    fig.text(0.5, 0.905, sub, ha="center", fontproperties=FP, fontsize=11.5, color=SUB)


def hit(u):
    return u["cacheRead"] / max(1, u["cacheRead"] + u["input"])


# ---- 01 缓存击穿恢复 ----
pre = [[s["pre"][i] for s in S if len(s["pre"]) > i] for i in range(5)]
post = [[s["post"][i] for s in S if len(s["post"]) > i] for i in range(5)]
xs = list(range(-5, 0)) + list(range(1, 6))
hits = [med(list(map(hit, w))) * 100 for w in pre + post]
costs = [med([u["cost"] for u in w]) for w in pre + post]

fig, ax = plt.subplots(figsize=(10, 5.6))
frame(fig, "压缩那一刻，缓存先死一次", "51 个干净窗口的逐轮中位数：命中率（左轴）与单轮成本（右轴，美元）")
ax.plot(xs, hits, "-o", color=BLUE, lw=2.5, ms=7, label="缓存命中率（中位）")
ax.axvline(0, color=GOLD, lw=2, ls="--")
ax.text(0, 12, " 压缩", fontproperties=FP, fontsize=14, color=GOLD, ha="center")
ax.annotate("99.6%", xy=(-1, hits[4]), xytext=(-3.9, 88), fontproperties=FP,
            fontsize=13, color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE))
ax.annotate("48.5%", xy=(1, hits[5]), xytext=(1.2, 30), fontproperties=FP,
            fontsize=13, color=INK, arrowprops=dict(arrowstyle="->", color=INK))
ax.annotate("98.3%", xy=(5, hits[9]), xytext=(3.6, 88), fontproperties=FP,
            fontsize=13, color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE))
ax.set_ylim(0, 112)
ax.set_ylabel("缓存命中率", fontproperties=FP, fontsize=13, color=BLUE)
ax.set_xticks(xs)
ax.set_xticklabels(["前5", "前4", "前3", "前2", "前1", "后1", "后2", "后3", "后4", "后5"],
                   fontproperties=FP, fontsize=12)
ax2 = ax.twinx()
ax2.plot(xs, costs, "-s", color=GOLD, lw=2, ms=6, label="单轮成本（中位）")
ax2.set_ylim(0, 0.145)
ax2.set_ylabel("单轮成本（美元）", fontproperties=FP, fontsize=13, color=GOLD)
ax2.annotate("$0.108", xy=(1, costs[5]), xytext=(2.8, 0.122), fontproperties=FP,
             fontsize=12.5, color=INK, arrowprops=dict(arrowstyle="->", color=INK))
ax2.annotate("$0.082", xy=(-1, costs[4]), xytext=(-4.4, 0.062), fontproperties=FP,
             fontsize=12.5, color=SUB, arrowprops=dict(arrowstyle="->", color=SUB))
for a in (ax, ax2):
    a.spines[["top"]].set_visible(False)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, prop=FP, loc="lower right", fontsize=11)
fig.savefig("01-cache-bust.png", bbox_inches="tight", facecolor=BG)
plt.close(fig)

# ---- 02 N*–ρ 曲线 ----
usable = []
for s in S:
    T = s.get("tokensBefore") or 0
    Tp = s["post"][0]["input"] + s["post"][0]["cacheRead"]
    C = s["compaction_usage"]["totalTokens"]
    if T and Tp and T > Tp:
        usable.append((T, Tp, C))

def nstar(T, Tp, C, rho):
    return (C + Tp * (1 - rho)) / max(1e-9, (T - Tp) * rho)

grid = np.logspace(np.log10(0.01), np.log10(1.0), 200)
curve = [med([nstar(T, Tp, C, r) for T, Tp, C in usable]) for r in grid]
pts = [(0.02, 19.3, "DeepSeek V4.1-Flash\n官方价 ρ=0.02"),
       (0.033, None, "DeepSeek V4-Pro\n官方价 ρ=0.033"),
       (0.10, 3.5, "OpenAI 官方\nρ=0.10"),
       (0.20, 1.6, "GLM-5.3-Flash\n官方价 ρ=0.20")]
pts[1] = (0.033, med([nstar(T, Tp, C, 0.033) for T, Tp, C in usable]), pts[1][2])

fig, ax = plt.subplots(figsize=(10, 5.6))
frame(fig, "缓存越便宜，压缩越难回本", "回本轮数 N* 随缓存折扣系数 ρ 的变化（49 个样本的中位数，双对数轴）")
ax.plot(grid, curve, color=BLUE, lw=2.5)
# 标签用绝对数据坐标避开下降曲线带：0.02 放曲线下方空白区，0.033 放上方空白区
label_pos = {0.02: (0.013, 5.0), 0.033: (0.052, 32.0), 0.10: (0.105, 6.5), 0.29: (0.33, 1.7), 0.20: (0.30, 3.2)}
for r, n, lab in pts:
    ax.scatter([r], [n], s=90, color=GOLD, zorder=5)
    tx, ty = label_pos[r]
    ax.annotate(lab, xy=(r, n), xytext=(tx, ty), fontproperties=FP,
                fontsize=11.5, color=INK, arrowprops=dict(arrowstyle="->", color=SUB))
ax.axhline(99, color=SUB, lw=1.6, ls="--")
ax.text(0.011, 99 * 1.15, "会话剩余轮数中位：99 轮（过了这条线，回不了本）",
        fontproperties=FP, fontsize=11.5, color=SUB)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("缓存折扣系数 ρ（缓存命中价 ÷ 输入价）", fontproperties=FP, fontsize=13)
ax.set_ylabel("回本轮数 N*（中位）", fontproperties=FP, fontsize=13)
ax.set_xlim(0.01, 1.0)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("02-nstar-rho.png", bbox_inches="tight", facecolor=BG)
plt.close(fig)

# ---- 03 ρ 阶梯回本 ----
rows = [("GLM-5.3-Flash\nρ=0.20", 1.6, "100% 回本", GOLD),
        ("OpenAI\nρ=0.10", 3.5, "96% 回本", BLUE),
        ("DeepSeek V4.1-Flash\nρ=0.02", 19.3, "84% 回本\n16% 永不回本", INK)]
fig, ax = plt.subplots(figsize=(10, 5.6))
frame(fig, "同一个压缩动作，换一家价格表就翻转", "49 个样本按各家园例价重算：回本轮数中位 vs 会话剩余轮数中位")
x = np.arange(3)
vals = [r[1] for r in rows]
bars = ax.bar(x, vals, 0.5, color=[r[3] for r in rows])
for i, (lab, n, note, c) in enumerate(rows):
    ax.text(i, n + 8, f"{n} 轮", ha="center", fontproperties=FP, fontsize=15, color=c)
    # 回本比例一律放柱外（短柱放不下柱内白字），紧跟数值下方
    ax.text(i, n + 1.5, note.replace("\n", " · "), ha="center", fontproperties=FP,
            fontsize=11.5, color=c)
ax.axhline(99, color=SUB, lw=1.8, ls="--")
ax.text(2.42, 101, "会话剩余 99 轮（中位）", fontproperties=FP, fontsize=12, color=SUB, ha="right")
ax.set_xticks(x)
ax.set_xticklabels([r[0] for r in rows], fontproperties=FP, fontsize=12.5)
ax.set_ylabel("回本轮数 N*（中位）", fontproperties=FP, fontsize=13)
ax.set_ylim(0, 118)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("03-recoup.png", bbox_inches="tight", facecolor=BG)
plt.close(fig)

# ---- 04 三家 harness 对照 ----
fig, ax = plt.subplots(figsize=(10, 5.6))
frame(fig, "这笔账，harness 们早就在算", "同一公式的三个工程化身（无数字；整理自各家官方文档与公开讨论）")
cards = [
    ("Anthropic", "clear_at_least", "清旧内容必须清够量，\n否则宁可不清理——\n「清掉的量要对得起\nprompt cache 的作废」", BLUE),
    ("Codex", "限额 + 阈值", "per-tool output_token_limit\n管住工具输出膨胀，\nmodel_auto_compact_\ntoken_limit 管触发时机", SUB),
    ("OpenCode", "历史教训", "早期每轮修剪工具结果，\n缓存每轮全部作废\n（后来已改）——\n把每轮节省直接归零", GOLD),
]
for i, (name, knob, desc, c) in enumerate(cards):
    cx = 0.035 + i * 0.325
    ax.add_patch(FancyBboxPatch((cx, 0.10), 0.28, 0.70, boxstyle="round,pad=0.012",
                                fc="#FFFFFF", ec=c, lw=2.2))
    ax.text(cx + 0.14, 0.72, name, ha="center", fontproperties=FP, fontsize=16, color=c)
    ax.text(cx + 0.14, 0.575, knob, ha="center", fontproperties=FP, fontsize=12.5, color=INK)
    ax.text(cx + 0.14, 0.30, desc, ha="center", fontproperties=FP, fontsize=11,
            color=SUB, linespacing=1.7)
ax.set_xlim(0, 1)
ax.set_ylim(0, 0.86)
ax.axis("off")
fig.savefig("04-harness.png", bbox_inches="tight", facecolor=BG)
plt.close(fig)

print("done: 01-cache-bust / 02-nstar-rho / 03-recoup / 04-harness")
