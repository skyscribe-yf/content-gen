#!/usr/bin/env python3
"""生成 5 张正文脚本图（数字全部来自本轮一手核实，无 AI 概念图）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch

FP = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
plt.rcParams["axes.unicode_minus"] = False

BLUE = "#0F4C81"
SUB = "#5B7A99"
INK = "#1A2733"
RED = "#B03A2E"
GOLD = "#B8860B"
LINE = "#C9D6E0"
BG = "#FFFFFF"


def new_ax(w=10, h=5.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.patch.set_facecolor(BG)
    return fig, ax


def title(ax, text, sub=None):
    ax.text(0.5, 0.965, text, ha="center", fontproperties=FP, fontsize=20, color=INK)
    if sub:
        ax.text(0.5, 0.905, sub, ha="center", fontproperties=FP, fontsize=12, color=SUB)


def save(fig, name):
    fig.savefig(name, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print("saved", name)


# ---------- 01 收敛时间线 ----------
fig, ax = new_ax(11, 5.2)
title(ax, "三家独立收敛到三档暴露", "时间线上没有牵头人：四步，四套文档，同一个答案")
events = [
    ("2026-01", "Anthropic", "tool search 进 Claude Code\n默认行为（10% 阈值自动开）", BLUE),
    ("2026-06", "Codex", "PR #29486：MCP 工具\n无条件默认走 tool search", BLUE),
    ("2026-08", "Codex", "PR #36781：三档补齐\n直接 / 搜索 / 代码模式", BLUE),
    ("2026-10", "pi 1.0", "codemode 进核心\nMCP 经它落地", BLUE),
]
xs = [0.13, 0.37, 0.61, 0.85]
y0 = 0.42
ax.plot([0.06, 0.94], [y0, y0], color=LINE, lw=3, zorder=1)
for (date, who, desc, color), x in zip(events, xs):
    ax.scatter([x], [y0], s=260, color=color, zorder=3, edgecolor="white", linewidth=2)
    ax.text(x, y0 + 0.13, date, ha="center", fontproperties=FP, fontsize=14, color=color)
    ax.text(x, y0 + 0.065, who, ha="center", fontproperties=FP, fontsize=11.5, color=INK)
    ax.text(x, y0 - 0.10, desc, ha="center", fontproperties=FP, fontsize=10, color=SUB, linespacing=1.5)
ax.text(0.5, 0.10, "三档暴露：direct / 按需搜索 / 代码模式 —— 三个团队，三种命名，同一张图纸",
        ha="center", fontproperties=FP, fontsize=12.5, color=INK)
save(fig, "01-convergence-timeline.png")

# ---------- 02 三档对照 ----------
fig, ax = new_ax(11, 5.4)
title(ax, "同一张图纸的三种写法", "每家文档里的措辞不同，分档结构一致")
cols = ["Anthropic", "Codex", "pi"]
rows = ["直接声明", "按需搜索", "代码模式"]
cells = [
    ["直接声明进上下文", "directly", "direct"],
    ["tool search 按需加载", "tool search（2026-06 默认）", "deferred（不进描述）"],
    ["Programmatic Tool Calling", "Code Mode（exec/wait）", "codemode（沙箱脚本）"],
]
col_x = [0.235, 0.5, 0.765]
row_y = [0.66, 0.50, 0.34]
for j, cname in enumerate(cols):
    ax.text(col_x[j], 0.78, cname, ha="center", fontproperties=FP, fontsize=15, color=BLUE)
for i, rname in enumerate(rows):
    ax.text(0.10, row_y[i], rname, ha="right", va="center", fontproperties=FP, fontsize=12, color=INK)
for j in range(3):
    for i in range(3):
        bb = FancyBboxPatch((col_x[j] - 0.115, row_y[i] - 0.052), 0.23, 0.104,
                            boxstyle="round,pad=0.010", fc="#F2F6FA", ec=LINE, lw=1.2)
        ax.add_patch(bb)
        ax.text(col_x[j], row_y[i], cells[i][j], ha="center", va="center",
                fontproperties=FP, fontsize=10.5, color=INK)
ax.text(0.5, 0.14, "档位本身就是答案：harness 承认自己不该替用户决定工具怎么进上下文",
        ha="center", fontproperties=FP, fontsize=12.5, color=SUB)
save(fig, "02-three-tiers.png")

# ---------- 03 三种 placement ----------
fig, ax = new_ax(11, 5.4)
title(ax, "代码跑在哪一侧，三家三个答案", "三种位置 = 三种信任模型：可审计 / 不回传 / 可复现")
cards = [
    ("pi", "harness 脑侧", "沙箱跟着工具流水线\n每次调用过权限闸门\n调用链可审计", "可审计", BLUE),
    ("Anthropic", "服务商侧", "Code Execution 在服务商\n中间结果由脚本消费\n根本不回客户端", "结果不回传", GOLD),
    ("Codex", "本地 V8", "exec / wait 两工具\n脚本躺在本机\n用户能读能复现", "脚本透明", RED),
]
for i, (who, pos, desc, tag, color) in enumerate(cards):
    x = 0.055 + i * 0.32
    bb = FancyBboxPatch((x, 0.22), 0.29, 0.56, boxstyle="round,pad=0.015",
                        fc="#F7FAFC", ec=color, lw=2)
    ax.add_patch(bb)
    ax.text(x + 0.145, 0.71, who, ha="center", fontproperties=FP, fontsize=16, color=color)
    ax.text(x + 0.145, 0.635, pos, ha="center", fontproperties=FP, fontsize=12.5, color=INK)
    ax.text(x + 0.145, 0.47, desc, ha="center", fontproperties=FP, fontsize=10.5, color=SUB, linespacing=1.6)
    tb = FancyBboxPatch((x + 0.065, 0.27), 0.16, 0.075, boxstyle="round,pad=0.012",
                        fc=color, ec="none")
    ax.add_patch(tb)
    ax.text(x + 0.145, 0.3075, tag, ha="center", va="center", fontproperties=FP, fontsize=11, color="white")
ax.text(0.5, 0.10, "不是谁强谁弱，是三套不同的账：安全、隐私、可复现，各买各的",
        ha="center", fontproperties=FP, fontsize=12.5, color=SUB)
save(fig, "03-placement.png")

# ---------- 04 结果侧三种管法 ----------
fig, ax = new_ax(11, 5.4)
title(ax, "工具吐回来的东西，太大了", "三家管的是「中间数据怎么不进模型的眼」")
bars = [
    ("pi · bash", "模型只看尾部 2000 行", SUB),
    ("pi · codemode", "同一工具最多 1 MiB", BLUE),
    ("Anthropic", "脚本消费中间结果，模型只看终点", GOLD),
    ("Codex", "per-tool 限额，hook 先于截断", RED),
]
y = 0.70
for name, desc, color in bars:
    bb = FancyBboxPatch((0.055, y - 0.055), 0.24, 0.10, boxstyle="round,pad=0.010",
                        fc=color, ec="none", alpha=0.9)
    ax.add_patch(bb)
    ax.text(0.175, y - 0.005, name, ha="center", va="center",
            fontproperties=FP, fontsize=13, color="white")
    ax.text(0.325, y - 0.005, desc, ha="left", va="center",
            fontproperties=FP, fontsize=13, color=INK)
    y -= 0.155
ax.text(0.5, 0.115, "共同点：中间结果由脚本或 hook 消费，模型看到的越少，上下文越省",
        ha="center", fontproperties=FP, fontsize=12.5, color=SUB)
save(fig, "04-result-limits.png")

# ---------- 05 默认关 ----------
fig, ax = new_ax(11, 5.6)
title(ax, "谁也不敢默认开", "三家收敛到同一个答案，又独立把它压在默认关")
rows = [
    ("pi", "仅 MCP 开启时自动启用", "作者四理由：benchmark 不够 / 编码层次 / 占 system prompt / 小模型过度使用", SUB),
    ("Codex", "under development, off by default", "官方配置页原文；issue #29122 至今 open——静默激活事故：模型签发 terminate:true", RED),
    ("Anthropic", "beta", "tool search 为 beta；老模型或走代理，回退成全量加载", GOLD),
]
for k, (who, state, why, color) in enumerate(rows):
    yc = 0.68 - k * 0.24
    bb = FancyBboxPatch((0.055, yc - 0.095), 0.89, 0.19, boxstyle="round,pad=0.012",
                        fc="#F7FAFC", ec=LINE, lw=1.2)
    ax.add_patch(bb)
    ax.text(0.09, yc + 0.052, who, fontproperties=FP, fontsize=15, color=BLUE, va="center")
    ax.text(0.09, yc + 0.012, state, fontproperties=FP, fontsize=11.5, color=color, va="center")
    ax.text(0.09, yc - 0.032, why, fontproperties=FP, fontsize=10.5, color=SUB, va="center")
ax.text(0.5, 0.055, "不是保守：方向对，但收益不确定、成本确定——同一份判断，做了三遍",
        ha="center", fontproperties=FP, fontsize=12.5, color=INK)
save(fig, "05-default-off.png")

print("ALL 5 IMAGES DONE")
