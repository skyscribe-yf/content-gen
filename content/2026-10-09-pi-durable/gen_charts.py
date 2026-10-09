#!/usr/bin/env python3
"""本篇脚本配图（结构/数字图）。AI 概念图不承载数字，数字与结构全走脚本。

视觉语言（刻意区别于前几篇的浅底图表）：深色终端底 + 高对比功能色。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = "content/2026-10-09-pi-durable/"
BG = "#0d1117"
PANEL = "#161b22"
LINE = "#30363d"
TEXT = "#e6edf3"
DIM = "#8b949e"
GOLD = "#FFC53D"
GREEN = "#3fb950"
RED = "#f85149"
BLUE = "#58a6ff"


def canvas(w=10, h=5.2):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, fc=PANEL, ec=LINE, lw=1.6, r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0.012,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, zorder=2))


def title(ax, s, sz=17):
    ax.text(0.5, 0.945, s, ha="center", va="center", fontsize=sz,
            fontweight="bold", color=TEXT, zorder=3)


def arrow(ax, p, q, color=DIM, lw=2.0, style="-|>", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=18,
                                 color=color, lw=lw, zorder=3,
                                 connectionstyle=f"arc3,rad={rad}"))


# ---------- 01 崩溃点四象限 ----------
fig, ax = canvas(10, 5.0)
title(ax, "崩溃点上，你只知道一半")
box(ax, 0.05, 0.56, 0.42, 0.28)
ax.text(0.26, 0.78, "进程活着 · 效果已发生", ha="center", fontsize=13.5, color=TEXT)
ax.text(0.26, 0.665, "重来是错的", ha="center", fontsize=13, color=GREEN, fontweight="bold")
box(ax, 0.05, 0.20, 0.42, 0.28)
ax.text(0.26, 0.42, "进程活着 · 效果没发生", ha="center", fontsize=13.5, color=TEXT)
ax.text(0.26, 0.305, "重来是对的", ha="center", fontsize=13, color=GREEN, fontweight="bold")
box(ax, 0.53, 0.20, 0.42, 0.64, fc="#2a1416", ec=RED, lw=2.0)
ax.text(0.74, 0.71, "进程死了", ha="center", fontsize=15, color=TEXT, fontweight="bold")
ax.text(0.74, 0.55, "？", ha="center", fontsize=62, color=RED, fontweight="bold")
ax.text(0.74, 0.35, "不知道", ha="center", fontsize=20, color=RED, fontweight="bold")
ax.text(0.74, 0.255, "重发？当成功？去补偿？", ha="center", fontsize=12.5, color=DIM)
ax.text(0.26, 0.09, "确定", ha="center", fontsize=12.5, color=GREEN)
ax.text(0.74, 0.09, "整个 durable 要处理的就是这一格", ha="center", fontsize=12.5, color=RED)
fig.savefig(OUT + "01-crash-point.png", dpi=200, facecolor=BG)
plt.close(fig)

# ---------- 02 效果三明治 ----------
fig, ax = canvas(10, 5.4)
title(ax, "效果三明治：把「我打算做这件事」先落盘")
steps = [("① 提交意图", "「要调 deploy，\n参数 v2.3.1」"),
         ("② 真正碰外界", "副作用在这里发生"),
         ("③ 提交结果", "成功 / 失败 /\n下一相位")]
for i, (h1, h2) in enumerate(steps):
    x = 0.045 + i * 0.315
    box(ax, x, 0.63, 0.28, 0.20, ec=RED if i == 1 else LINE, lw=2.2 if i == 1 else 1.6)
    ax.text(x + 0.14, 0.775, h1, ha="center", fontsize=14,
            color=RED if i == 1 else TEXT, fontweight="bold")
    ax.text(x + 0.14, 0.69, h2, ha="center", fontsize=11.5, color=DIM)
    if i < 2:
        arrow(ax, (x + 0.295, 0.73), (x + 0.35, 0.73), color=DIM)
ax.text(0.14, 0.585, "已落盘", ha="center", fontsize=11.5, color=GREEN)
ax.text(0.45, 0.585, "崩在这里 ⇒ 副作用可能已经发生", ha="center", fontsize=12.5,
        color=RED, fontweight="bold")
ax.text(0.77, 0.585, "已落盘", ha="center", fontsize=11.5, color=GREEN)
ax.text(0.5, 0.51, "停在中间那层，只剩三种诚实的做法", ha="center", fontsize=13, color=TEXT)
exits = [("安全重跑", "replay: \"safe\"", GREEN), ("轮询外部句柄", "带 handle + pollAt", BLUE),
         ("记录中断", "interrupted + 部分输出", GOLD)]
for i, (h1, h2, c) in enumerate(exits):
    x = 0.045 + i * 0.315
    box(ax, x, 0.20, 0.28, 0.22, fc="#0f2020" if i == 0 else PANEL, ec=c, lw=1.8)
    ax.text(x + 0.14, 0.345, h1, ha="center", fontsize=14, color=c, fontweight="bold")
    ax.text(x + 0.14, 0.265, h2, ha="center", fontsize=11, color=DIM)
    arrow(ax, (0.45, 0.62), (x + 0.14, 0.435), color=LINE, lw=1.4)
ax.text(0.5, 0.105, "默认 unsafe：省略 replay 声明，就是不允许重跑", ha="center",
        fontsize=12.5, color=RED)
fig.savefig(OUT + "02-effect-sandwich.png", dpi=200, facecolor=BG)
plt.close(fig)

# ---------- 03 任务状态机 ----------
fig, ax = canvas(10, 5.0)
title(ax, "每个相位必须前进：不提交进展，任务直接 faulted")
states = [("pending", "重开时的起点"), ("running", "相位代码在跑"),
          ("waiting", "只存检查点\n不跑代码"), ("completing", "等名下的子任务"),
          ("terminal", "结果落定")]
for i, (h1, h2) in enumerate(states):
    x = 0.035 + i * 0.192
    box(ax, x, 0.60, 0.165, 0.22, ec=GOLD if i == 3 else LINE)
    ax.text(x + 0.0825, 0.745, h1, ha="center", fontsize=12.5, color=TEXT, fontweight="bold")
    ax.text(x + 0.0825, 0.655, h2, ha="center", fontsize=10.5, color=DIM)
    if i < 4:
        arrow(ax, (x + 0.175, 0.71), (x + 0.225, 0.71), color=DIM, lw=1.6)
arrow(ax, (0.33, 0.585), (0.19, 0.585), color=BLUE, lw=1.5)
ax.text(0.26, 0.545, "依赖到齐，回到 running", ha="center", fontsize=11, color=BLUE)
for i in range(5):
    x = 0.035 + i * 0.192 + 0.0825
    arrow(ax, (x, 0.585), (0.5, 0.40), color=RED, lw=1.1)
ax.text(0.5, 0.345, "任何状态都可以 abort", ha="center", fontsize=12.5, color=RED)
box(ax, 0.34, 0.16, 0.32, 0.13, fc="#2a1416", ec=RED, lw=1.8)
ax.text(0.5, 0.225, "abort 自底向上级联", ha="center", fontsize=13, color=RED, fontweight="bold")
ax.text(0.5, 0.09, "close() 只是停掉调用、保留工作；只有 abort 才是持久取消",
        ha="center", fontsize=11.5, color=DIM)
fig.savefig(OUT + "03-task-fsm.png", dpi=200, facecolor=BG)
plt.close(fig)

# ---------- 04 所有权树 ----------
fig, ax = canvas(10, 5.2)
title(ax, "所有权是一棵树：abort 先撤子，再撤自己")
box(ax, 0.40, 0.72, 0.20, 0.15, ec=GOLD, lw=2.0)
ax.text(0.50, 0.795, "会话", ha="center", fontsize=14, color=GOLD, fontweight="bold")
box(ax, 0.10, 0.44, 0.26, 0.15)
ax.text(0.23, 0.565, "工具调用任务", ha="center", fontsize=13, color=TEXT, fontweight="bold")
ax.text(0.23, 0.485, "属于当前这轮工作", ha="center", fontsize=10.5, color=DIM)
box(ax, 0.64, 0.44, 0.26, 0.15)
ax.text(0.77, 0.565, "后台任务", ha="center", fontsize=13, color=TEXT, fontweight="bold")
ax.text(0.77, 0.485, "Esc 不动它", ha="center", fontsize=10.5, color=DIM)
arrow(ax, (0.46, 0.715), (0.23, 0.60), color=LINE, lw=1.6)
arrow(ax, (0.54, 0.715), (0.77, 0.60), color=LINE, lw=1.6)
box(ax, 0.10, 0.19, 0.26, 0.15, ec=BLUE)
ax.text(0.23, 0.315, "子代理会话", ha="center", fontsize=13, color=BLUE, fontweight="bold")
ax.text(0.23, 0.235, "崩了也接着跑", ha="center", fontsize=10.5, color=DIM)
arrow(ax, (0.23, 0.435), (0.23, 0.35), color=LINE, lw=1.6)
arrow(ax, (0.26, 0.20), (0.13, 0.30), color=RED, lw=2.2)
arrow(ax, (0.23, 0.36), (0.23, 0.45), color=RED, lw=2.2)
arrow(ax, (0.26, 0.62), (0.30, 0.72), color=RED, lw=2.2)
ax.text(0.50, 0.32, "abort 标记是\n持久的意图", ha="center", fontsize=12, color=RED)
ax.text(0.50, 0.215, "中间再崩一次，\n重开还会重新派生", ha="center", fontsize=11, color=DIM)
ax.text(0.50, 0.10, "补偿写在做事的那一层：Compensate at the level that did the effect",
        ha="center", fontsize=11.5, color=GOLD)
fig.savefig(OUT + "04-ownership-tree.png", dpi=200, facecolor=BG)
plt.close(fig)

# ---------- 05 两种重复 ----------
fig, ax = canvas(10, 5.2)
title(ax, "两种重复，只挡住了一种")
box(ax, 0.04, 0.53, 0.92, 0.30, fc="#0f2020", ec=GREEN, lw=1.8)
ax.text(0.075, 0.775, "崩溃重放型重复", ha="left", fontsize=15, color=GREEN, fontweight="bold")
ax.text(0.075, 0.675, "进程死了 → 任务重跑 → 同一件事被做第二遍",
        ha="left", fontsize=12, color=TEXT)
ax.text(0.075, 0.585, "挡住它的：replay 声明 · memo 首写胜 · 确定性 ID · requestId",
        ha="left", fontsize=11.5, color=DIM)
ax.text(0.895, 0.685, "✓", ha="center", fontsize=34, color=GREEN, fontweight="bold")
box(ax, 0.04, 0.16, 0.92, 0.30, fc="#2a1416", ec=RED, lw=1.8)
ax.text(0.075, 0.405, "模型重新规划型重复", ha="left", fontsize=15, color=RED, fontweight="bold")
ax.text(0.075, 0.305, "新一轮生成 → 另起一个新的工具调用 ID → 工具侧看到全新请求",
        ha="left", fontsize=12, color=TEXT)
ax.text(0.075, 0.215, "挡住它的：还没有。缺的是编排层派生的幂等键",
        ha="left", fontsize=11.5, color=GOLD)
ax.text(0.895, 0.315, "×", ha="center", fontsize=34, color=RED, fontweight="bold")
ax.text(0.5, 0.085, "每层单独看都很干净，合起来照样重复", ha="center",
        fontsize=13, color=TEXT, fontweight="bold")
fig.savefig(OUT + "05-two-duplicates.png", dpi=200, facecolor=BG)
plt.close(fig)

print("charts done: 01-crash-point / 02-effect-sandwich / 03-task-fsm / 04-ownership-tree / 05-two-duplicates")
