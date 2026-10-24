#!/usr/bin/env python3
"""本篇脚本画图：02 Copilot 数字卡 / 03 时间线 / 04 四档暴露 / 05 默认关理由。
规矩：数字/结构用脚本画，AI 图禁载数字；图内数字与正文逐字一致。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties

FP = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
plt.rcParams["axes.unicode_minus"] = False
D = "content/2026-10-21-pi-codemode-mcp"

INK = "#1a2332"      # 主文字
SUB = "#5b6b7f"      # 次文字
BLUE = "#0F4C81"     # 主色（grace 蓝）
RED = "#c0392b"      # 警告
GOLD = "#E8A317"     # 逆转金
BG = "#ffffff"


def newfig(w=11, h=5.4):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    return fig, ax


def card(ax, x, y, w, h, fc, ec, lw=1.6, r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.004,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, mutation_aspect=1))


# ---------- 02 Copilot 数字卡 ----------
def fig02():
    fig, ax = newfig(11, 5.8)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.955, "MCP 的上下文账单", ha="center", fontproperties=FP, fontsize=21, color=INK)

    rows = [
        ("同一个模型，两样命", "Claude Sonnet 4 经 Copilot 只剩 128k 窗口，别处是 1M", 0.66),
        ("官方 MCP server 一接上", "token 从 34k 涨到 80k（用户实测，66 个工具）", 0.40),
        ("Copilot CLI 上更狠", "系统提示 + 工具定义占 146k/200k = 73%，首条消息即触发自动压缩", 0.14),
    ]
    for title, desc, y in rows:
        card(ax, 0.04, y, 0.92, 0.17, "#f7f9fc", "#d7e0ea")
        ax.text(0.07, y + 0.115, title, fontproperties=FP, fontsize=13.5, color=BLUE, va="center")
        ax.text(0.07, y + 0.048, desc, fontproperties=FP, fontsize=11.5, color=INK, va="center")

    # 三条迷你条形：128k vs 1M
    ax.text(0.60, 0.795, "128k", fontproperties=FP, fontsize=13, color=RED, va="center")
    ax.add_patch(plt.Rectangle((0.68, 0.775), 0.10, 0.035, color=RED))
    ax.text(0.60, 0.745, "1M", fontproperties=FP, fontsize=13, color=SUB, va="center")
    ax.add_patch(plt.Rectangle((0.68, 0.725), 0.27, 0.035, color="#b9c6d4"))
    # 34k -> 80k
    ax.text(0.60, 0.535, "34k", fontproperties=FP, fontsize=13, color=SUB, va="center")
    ax.add_patch(plt.Rectangle((0.68, 0.515), 0.07, 0.035, color="#b9c6d4"))
    ax.text(0.60, 0.505, "80k", fontproperties=FP, fontsize=13, color=RED, va="center")
    ax.add_patch(plt.Rectangle((0.68, 0.485), 0.16, 0.035, color=RED))
    ax.annotate("", xy=(0.755, 0.525), xytext=(0.725, 0.525),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6))
    # 73% 占位条
    ax.add_patch(plt.Rectangle((0.60, 0.205), 0.34, 0.05, color="#e6ebf1"))
    ax.add_patch(plt.Rectangle((0.60, 0.205), 0.34 * 0.73, 0.05, color=RED))
    ax.text(0.60, 0.265, "146k", fontproperties=FP, fontsize=12, color=RED, va="center")
    ax.text(0.945, 0.265, "200k", fontproperties=FP, fontsize=12, color=SUB, va="center", ha="right")
    ax.text(0.60, 0.163, "73%", fontproperties=FP, fontsize=15, color=RED, va="center")

    fig.savefig(f"{D}/02-copilot-context.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 03 时间线 ----------
def fig03():
    fig, ax = newfig(11, 4.6)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.94, "从骂 MCP 到请回 MCP", ha="center", fontproperties=FP, fontsize=20, color=INK)

    nodes = [
        ("2025-07", "Armin 发文骂 MCP\n两宗罪：不可组合、吃上下文", RED),
        ("2025-11", "Mario 写文追问\npi.dev 挂牌：不支持 MCP", SUB),
        ("2026-04", "Earendil 收购 pi\nMario 加入，两人同桌", BLUE),
        ("2026-09", "《You Said No MCP!》\nMCP 进核心，HN 672 点", GOLD),
    ]
    xs = [0.13, 0.38, 0.63, 0.88]
    y = 0.52
    ax.plot([0.06, 0.95], [y, y], color="#c9d4e0", lw=2.4, zorder=1)
    for (date, txt, c), x in zip(nodes, xs):
        ax.scatter([x], [y], s=340, color=c, zorder=3, edgecolor="white", linewidth=2)
        ax.text(x, y + 0.13, date, ha="center", fontproperties=FP, fontsize=14.5, color=c)
        ax.text(x, y - 0.16, txt, ha="center", fontproperties=FP, fontsize=10.5, color=INK,
                linespacing=1.5)
    ax.annotate("", xy=(0.955, y), xytext=(0.9, y),
                arrowprops=dict(arrowstyle="-|>", color="#c9d4e0", lw=2.4))
    fig.savefig(f"{D}/03-timeline.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 04 四档暴露 ----------
def fig04():
    fig, ax = newfig(11, 5.2)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.95, "MCP 工具的四档暴露：不再只有全量灌一种姿势",
            ha="center", fontproperties=FP, fontsize=17, color=INK)

    tiers = [
        ("direct  直接声明", "像内置工具一样常驻上下文", "上下文成本 高", 0.92, RED),
        ("deferred  按需搜索", "用时才加载进下一次请求", "上下文成本 中", 0.70, GOLD),
        ("codemode  只许脚本调用", "模型看不到声明，脚本里调", "上下文成本 低", 0.48, BLUE),
        ("hidden  隐藏", "注册但不可达", "上下文成本 无", 0.26, SUB),
    ]
    for name, desc, cost, y, c in tiers:
        card(ax, 0.05, y, 0.9, 0.15, "#f7f9fc", "#d7e0ea")
        ax.add_patch(plt.Rectangle((0.05, y), 0.012, 0.15, color=c))
        ax.text(0.09, y + 0.093, name, fontproperties=FP, fontsize=14, color=c, va="center")
        ax.text(0.09, y + 0.038, desc, fontproperties=FP, fontsize=11, color=INK, va="center")
        ax.text(0.91, y + 0.075, cost, fontproperties=FP, fontsize=11.5, color=SUB,
                va="center", ha="right")
    fig.savefig(f"{D}/04-exposure-tiers.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 05 默认关的三个理由 ----------
def fig05():
    fig, ax = newfig(11, 5.2)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.95, "作者亲口：codemode 为什么默认关", ha="center",
            fontproperties=FP, fontsize=19, color=INK)

    reasons = [
        ("① 跨模型 benchmark 不够", "没有拿得出手的跨模型对比数据"),
        ("② 本身很占 system prompt", " codemode 的说明词写进系统提示， itself 就是成本"),
        ("③ 小模型会过度使用", "能力不足的模型容易滥用脚本编排"),
    ]
    y = 0.72
    for t, d in reasons:
        card(ax, 0.06, y, 0.88, 0.14, "#fdf6e8", "#ecd9ae")
        ax.text(0.10, y + 0.088, t, fontproperties=FP, fontsize=13.5, color="#8a5a00", va="center")
        ax.text(0.10, y + 0.033, d, fontproperties=FP, fontsize=11, color=INK, va="center")
        y -= 0.17

    card(ax, 0.06, 0.10, 0.88, 0.14, "#eef4fa", "#b9cfe4")
    ax.text(0.10, 0.188, "作者的判断：方向对，但收益不确定、成本确定", fontproperties=FP,
            fontsize=13.5, color=BLUE, va="center")
    ax.text(0.10, 0.133, "那就默认关——证据弱的时候，压小赌注", fontproperties=FP,
            fontsize=11.5, color=INK, va="center")
    fig.savefig(f"{D}/05-default-off.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig02(); fig03(); fig04(); fig05()
    print("02/03/04/05 已生成")
