#!/usr/bin/env python3
"""本篇脚本画图：01 逐字写 vs 逐块抠 / 02 家族时间线 / 03 玩家层格局。
规矩：数字/结构用脚本画，图内数字与正文逐字一致。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["axes.unicode_minus"] = False
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
D = "content/2026-11-26-diffusion-language-model"

BG = "#F8F6F1"
INK = "#26292F"
SUB = "#5b6b7f"
TEAL = "#0E7A6E"
TEAL_L = "#d9ebe7"
GOLD = "#B87C0E"
RED = "#C24A28"
GREY_L = "#e8e4dc"


def fp(size=13, bold=True):
    return matplotlib.font_manager.FontProperties(fname=FONT if bold else FONT_R, size=size)


def newfig(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.facecolor = BG
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def title(ax, text, sub=None, y=0.955):
    ax.text(0.5, y, text, ha="center", fontproperties=fp(19), color=INK)
    if sub:
        ax.text(0.5, y - 0.052, sub, ha="center", fontproperties=fp(11.5, False), color=SUB)


def box(ax, x, y, w, h, fc, ec, lw=1.2, ls="-", r=0.012):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={r}",
                                facecolor=fc, edgecolor=ec, linewidth=lw, linestyle=ls))


def token(ax, cx, cy, s, on, col):
    """一个 token 方格：on=是否已点亮"""
    box(ax, cx - s / 2, cy - s / 2, s, s,
        col if on else "#ffffff", col if on else "#c9c4b8", lw=1.3)


# ---------- 01 逐字写 vs 逐块抠 ----------
def fig01():
    fig, ax = newfig(11.4, 7.2)
    title(ax, "逐字写 vs 逐块抠", "同一个 16 token 的回答：写法不同，点亮顺序不同")

    n, per = 16, 4
    s, gap = 0.036, 0.010
    row_w = n * s + (n - 1) * gap
    x0 = 0.5 - row_w / 2

    def row(y, blocks, mode, col):
        """blocks: 每块内哪些序号在该步点亮（1-indexed）；mode: 'ar'|'block'"""
        # 块分隔虚线
        for b in range(1, per):
            xb = x0 + b * (per * s + (per - 1) * gap) - gap / 2
            ax.plot([xb, xb], [y - 0.055, y + 0.055], color=GREY_L, lw=1.2, ls=(0, (3, 3)))
        for b, idxs in enumerate(blocks):
            for i in idxs:
                cx = x0 + (b * per + i - 1) * (s + gap) + s / 2
                token(ax, cx, y, s, True, col)
        # 未点亮的空格
        lit = {i for idxs in blocks for i in idxs}
        for i in range(1, n + 1):
            if i not in lit:
                cx = x0 + (i - 1) * (s + gap) + s / 2
                token(ax, cx, y, s, False, col)
        return row_w

    # 上排：自回归——第 5 步时只亮了 5 个，一字排开
    y_ar = 0.66
    row(y_ar, [[1], [2], [3], [4]], "ar", SUB)
    ax.text(x0 - 0.035, y_ar, "自回归\n第 5 步", ha="right", va="center",
            fontproperties=fp(12.5), color=SUB, linespacing=1.5)
    ax.annotate("", xy=(x0 + row_w + 0.028, y_ar), xytext=(x0 + row_w + 0.008, y_ar),
                arrowprops=dict(arrowstyle="-|>", color=SUB, lw=1.6))
    ax.text(x0 + row_w + 0.045, y_ar, "一次一个字\n写错的收不回来", ha="left", va="center",
            fontproperties=fp(11), color=SUB, linespacing=1.5)

    # 下排：块扩散——第 2 步时第 1、2 块整块点亮
    y_bd = 0.30
    row(y_bd, [[1, 2, 3, 4], [1, 2, 3, 4]], "block", TEAL)
    ax.text(x0 - 0.035, y_bd, "masked 扩散\n第 2 步", ha="right", va="center",
            fontproperties=fp(12.5), color=TEAL, linespacing=1.5)
    ax.text(x0 + row_w + 0.045, y_bd, "块内同时点亮\n块间仍要排队", ha="left", va="center",
            fontproperties=fp(11), color=TEAL, linespacing=1.5)

    # 中间因果箭头
    ax.annotate("", xy=(0.5, y_bd + 0.062), xytext=(0.5, y_ar - 0.062),
                arrowprops=dict(arrowstyle="-|>", color=GOLD, lw=2.2))
    ax.text(0.5, (y_ar + y_bd) / 2, "顺序反过来 → 所以能并行", ha="center", va="center",
            fontproperties=fp(13), color=GOLD,
            bbox=dict(boxstyle="round,pad=0.35", fc=BG, ec=GOLD, lw=1.2))

    ax.text(0.5, 0.045, "旋钮：每一步敢同时点亮几个词（并行度 / schedule）",
            ha="center", fontproperties=fp(11.5), color=SUB)
    fig.savefig(f"{D}/01-paradigm.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ---------- 02 家族时间线 ----------
def fig02():
    fig, ax = newfig(11.4, 6.4)
    title(ax, "从遮词游戏到生成方式", "masked 扩散一脉：预任务 → 生成范式")

    stops = [
        ("2021", "D3PM", "把扩散搬进离散空间", SUB),
        ("2022–2023", "SEDD / MDLM", "连续时间去噪的离散版\nmasked 一脉的数学地基", SUB),
        ("2025", "LLaDA / Dream 7B", "8B from scratch\n reversal poem 超 GPT-4o", TEAL),
        ("2026", "LLaDA2.0 / SDAR", "首个 100B 级 dLLM\n30B MoE 块内扩散", GOLD),
    ]
    xs = [0.13, 0.38, 0.63, 0.87]
    y_line = 0.46
    ax.plot([0.06, 0.95], [y_line, y_line], color=GREY_L, lw=3, zorder=1)

    for (yr, name, desc, col), x in zip(stops, xs):
        ax.scatter([x], [y_line], s=180, color=col, zorder=3, edgecolor=BG, linewidth=2)
        ax.text(x, y_line + 0.135, yr, ha="center", fontproperties=fp(14), color=col)
        ax.text(x, y_line + 0.075, name, ha="center", fontproperties=fp(13), color=INK)
        ax.text(x, y_line - 0.115, desc, ha="center", va="top",
                fontproperties=fp(10.5, False), color=SUB, linespacing=1.5)

    ax.annotate("", xy=(0.95, 0.16), xytext=(0.06, 0.16),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.8))
    ax.text(0.5, 0.095, "BERT 时代的预任务（遮住一些词，猜回来）→ 换成生成方式本身",
            ha="center", fontproperties=fp(12), color=INK)
    fig.savefig(f"{D}/02-family.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ---------- 03 玩家层格局 ----------
def fig03():
    fig, ax = newfig(11.4, 7.4)
    title(ax, "2026 年，谁在不逐字写字", "三极 / 开源双雄 / 国产一条线")

    cols = [
        ("三极（商用/巨头）", TEAL, [
            ("Inception Mercury", "1,109 tok/s\nArtificial Analysis 独立实测"),
            ("Google DiffusionGemma", "1000+ tok/s 官方口径\n26B MoE / 激活 3.8B"),
            ("NVIDIA Nemotron-Diffusion", "每前向 6x tokens\nSPEED-Bench 4x 吞吐"),
        ]),
        ("开源双雄", GOLD, [
            ("LLaDA2.0", "首个 100B 级 dLLM\nflash 100B / mini 16B MoE"),
            ("SDAR", "30B MoE\n块内扩散 + 块间 AR"),
        ]),
        ("国产一条线", RED, [
            ("人大高瓴 + 蚂蚁 LLaDA", "8B from scratch\n reversal poem 超 GPT-4o"),
            ("字节 Seed Diffusion", "2,146 tok/s@H20\narXiv 摘要级口径"),
            ("DiffuSpace Clover", "SWE-bench Verified 73.6\n单卡 GB300 680 tok/s"),
        ]),
    ]
    cw, gap = 0.295, 0.028
    x_start = 0.5 - (3 * cw + 2 * gap) / 2
    y_top, ch, cgap = 0.72, 0.165, 0.032

    for ci, (cname, col, cards) in enumerate(cols):
        cx = x_start + ci * (cw + gap)
        box(ax, cx, y_top + 0.045, cw, 0.075, col, col, lw=1.2, r=0.02)
        ax.text(cx + cw / 2, y_top + 0.082, cname, ha="center", va="center",
                fontproperties=fp(13.5), color="#ffffff")
        for k, (name, desc) in enumerate(cards):
            cy = y_top - k * (ch + cgap)
            box(ax, cx, cy - ch, cw, ch, "#ffffff", col, lw=1.5)
            ax.text(cx + 0.018, cy - 0.042, name, ha="left", va="center",
                    fontproperties=fp(12.5), color=INK)
            ax.text(cx + 0.018, cy - 0.105, desc, ha="left", va="center",
                    fontproperties=fp(10.5, False), color=SUB, linespacing=1.5)

    ax.text(0.5, 0.055, "口径提醒：1,109 是第三方实测，1000+ 与 6x 是官方/论文口径，73.6 是论文自报",
            ha="center", fontproperties=fp(11), color=SUB)
    fig.savefig(f"{D}/03-players.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig01(); fig02(); fig03()
    print("✅ 01/02/03 三张脚本图完成")
