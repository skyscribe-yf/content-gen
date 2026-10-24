#!/usr/bin/env python3
"""本篇脚本画图：02 ProgramBench 实测对比 / 05 四层分工。
规矩：数字/结构用脚本画，AI 图禁载数字；图内数字与正文逐字一致。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["axes.unicode_minus"] = False
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
D = "content/2026-10-22-rust-agent-language"

INK = "#1a2332"      # 主文字
SUB = "#5b6b7f"      # 次文字
BLUE = "#0F4C81"     # 主色（grace 蓝）
RED = "#c0392b"      # 警示红
GOLD = "#E8A317"     # 强调金
BG = "#ffffff"


def newfig(w=11, h=5.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def card(ax, x, y, w, h, fc, ec, lw=1.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.02",
                                fc=fc, ec=ec, lw=lw, mutation_aspect=1))


# ---------- 02 ProgramBench：简单第一，难任务垫底 ----------
def fig02():
    fig, ax = newfig(11, 5.8)
    ax.text(0.5, 0.95, "同一批 192 个任务，答案分两半", ha="center",
            fontproperties=matplotlib.font_manager.FontProperties(fname=FONT),
            fontsize=20, color=INK)

    # 两根柱：简单任务 74.7（蓝）vs 难任务 24.7（红）
    base_y, max_h = 0.14, 0.62
    bw, x1, x2 = 0.20, 0.24, 0.62
    h1 = max_h * 74.7 / 100
    h2 = max_h * 24.7 / 100
    ax.add_patch(plt.Rectangle((x1, base_y), bw, h1, color=BLUE))
    ax.add_patch(plt.Rectangle((x2, base_y), bw, h2, color=RED))
    ax.plot([0.16, 0.90], [base_y, base_y], color=INK, lw=1.4)

    ax.text(x1 + bw / 2, base_y + h1 + 0.035, "74.7", ha="center", fontsize=26,
            color=BLUE, fontweight="bold",
            fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))
    ax.text(x2 + bw / 2, base_y + h2 + 0.035, "24.7", ha="center", fontsize=26,
            color=RED, fontweight="bold",
            fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))
    ax.text(x1 + bw / 2, base_y - 0.05, "简单任务\n全场第一", ha="center", fontsize=13,
            color=INK, fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))
    ax.text(x2 + bw / 2, base_y - 0.05, "难任务\n垫底", ha="center", fontsize=13,
            color=INK, fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))

    # 跌幅标注
    ax.annotate("", xy=(0.545, base_y + h2), xytext=(0.545, base_y + h1),
                arrowprops=dict(arrowstyle="-|>", color=GOLD, lw=2.6))
    ax.text(0.545, (base_y + h1 + base_y + h2) / 2 + 0.01, "−50 点", ha="center",
            fontsize=17, color=GOLD, fontweight="bold", rotation=90,
            fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))
    ax.text(0.545, (base_y + h1 + base_y + h2) / 2 - 0.075, "全场最大跌幅", ha="center",
            fontsize=11, color=SUB, rotation=90,
            fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))

    # 底部成本条
    card(ax, 0.16, 0.005, 0.74, 0.075, "#fdf6e7", GOLD)
    ax.text(0.5, 0.042, "还全程最贵：每个任务平均 1.40 美元，构建轮次最多",
            ha="center", fontsize=12.5, color=INK,
            fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))

    fig.savefig(f"{D}/02-bench-split.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 05 四层分工 ----------
def fig05():
    fig, ax = newfig(11, 6.2)
    ax.text(0.5, 0.955, "按活选语言，不按时代口号选", ha="center",
            fontproperties=matplotlib.font_manager.FontProperties(fname=FONT),
            fontsize=20, color=INK)

    rows = [
        ("模型、评测、实验胶水", "Python", "#2b6cb0"),
        ("agent 产品、MCP、插件、界面", "TypeScript", "#0F4C81"),
        ("新后端服务，要快而确定的循环", "Go", "#0e7490"),
        ("运行时、沙箱、等不起的热路径", "Rust", "#b45309"),
    ]
    y, rh = 0.72, 0.155
    for what, lang, color in rows:
        card(ax, 0.04, y, 0.92, rh, "#f7f9fc", "#d7e0ea")
        ax.add_patch(plt.Rectangle((0.04, y), 0.012, rh, color=color))
        ax.text(0.075, y + rh / 2, what, fontsize=13.5, color=INK, va="center",
                fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))
        ax.text(0.93, y + rh / 2, lang, fontsize=16, color=color, va="center", ha="right",
                fontweight="bold",
                fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))
        y -= rh + 0.035

    ax.text(0.5, 0.025, "约束和验收标准明确的地方，收益可能更大",
            ha="center", fontsize=12.5, color=GOLD,
            fontproperties=matplotlib.font_manager.FontProperties(fname=FONT))

    fig.savefig(f"{D}/05-layer-table.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig02()
    fig05()
    print("02-bench-split.png / 05-layer-table.png 已生成")
