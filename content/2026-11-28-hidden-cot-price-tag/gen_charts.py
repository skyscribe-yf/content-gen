#!/usr/bin/env python3
"""本篇脚本画图：01 四家可见性对比 / 02 五道坎 / 03 一本账的结构。
规矩：浅色中性底（#F8F6F1），低饱和三色（暖灰/去饱和青/哑光金），中文标签，
概念图不承载具体金额数字；对比与结构用图形说话。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["axes.unicode_minus"] = False
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
D = "content/2026-11-28-hidden-cot-price-tag"

BG = "#F8F6F1"
INK = "#26292F"
SUB = "#5b6b7f"
TEAL = "#0E7A6E"
TEAL_L = "#d9ebe7"
GOLD = "#B87C0E"
GOLD_L = "#f3e6cd"
RED = "#C24A28"
RED_L = "#f6e7e2"
GREY_L = "#e8e4dc"


def fp(size=13, bold=True):
    return matplotlib.font_manager.FontProperties(fname=FONT if bold else FONT_R, size=size)


def newfig(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def title(ax, text, sub=None, y=0.955):
    ax.text(0.5, y, text, ha="center", fontproperties=fp(19), color=INK)
    if sub:
        ax.text(0.5, y - 0.055, sub, ha="center", fontproperties=fp(11.5, False), color=SUB)


def box(ax, x, y, w, h, fc, ec, lw=1.2, ls="-", r=0.012):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={r}",
                                facecolor=fc, edgecolor=ec, linewidth=lw, linestyle=ls))


# ---------- 01 四家可见性对比 ----------
def fig01():
    fig, ax = newfig(11.4, 7.2)
    title(ax, "四家，给不给你看思维链", "判断标准：API 把思维链返回给调用者吗？")

    # 每行：厂商 / API 返回什么 / 可见性横条（实心=看得见，空心=看不见但照常计费）
    rows = [
        ("DeepSeek", "思维链全量返回\n（reasoning_content 字段）", 1.00, TEAL, TEAL_L, "全量可见"),
        ("OpenAI", "只给摘要\n（summary 参数开启）", 0.45, GOLD, GOLD_L, "摘要级"),
        ("Anthropic", "不返回原始思维链\n（5.x 默认 omitted）", 0.00, RED, RED_L, "不可见"),
        ("Google", "默认只返回最终输出\n（thinking_summaries 才开）", 0.00, RED, RED_L, "不可见"),
    ]
    x0, w = 0.055, 0.90
    y_top, rh, gap = 0.815, 0.145, 0.045
    bx, bw = 0.60, 0.30          # 可见性横条区域
    for i, (name, desc, fill, ec, fc, tag) in enumerate(rows):
        y = y_top - i * (rh + gap) - rh
        box(ax, x0, y, w, rh, fc, ec, lw=1.6 if fill == 1.0 else 1.2)
        ax.text(x0 + 0.022, y + rh / 2, name, ha="left", va="center",
                fontproperties=fp(15), color=INK)
        ax.text(x0 + 0.155, y + rh / 2, desc, ha="left", va="center",
                fontproperties=fp(11, False), color=SUB, linespacing=1.5)
        # 横条：整条 = 模型思考过程；实心段 = 调用者看得见的部分
        by = y + rh / 2 - 0.021
        ax.add_patch(FancyBboxPatch((bx, by), bw, 0.042,
                                    boxstyle="round,pad=0,rounding_size=0.008",
                                    facecolor="#ffffff", edgecolor=SUB, linewidth=1.1))
        if fill > 0:
            ax.add_patch(FancyBboxPatch((bx, by), bw * fill, 0.042,
                                        boxstyle="round,pad=0,rounding_size=0.008",
                                        facecolor=ec, edgecolor=ec, linewidth=1.1))
        ax.text(bx + bw + 0.018, by + 0.021, tag, ha="left", va="center",
                fontproperties=fp(11.5), color=ec)
        # 看不见的那段标注「照常计费」
        if fill < 1.0:
            ax.text(bx + bw * fill + (bw * (1 - fill)) / 2, by - 0.038, "照常计费",
                    ha="center", va="center", fontproperties=fp(9.5, False), color=SUB)

    # 底部结论条
    yb = y_top - 4 * (rh + gap) - 0.005
    ax.plot([x0 + 0.01, x0 + w - 0.01], [yb, yb], color=GOLD, lw=2.0, ls=(0, (5, 3)))
    ax.text(0.5, yb - 0.038, "四家里只有一家把思维链完整返回——另外三家的官方文档都明确写了不返回原始推理",
            ha="center", va="center", fontproperties=fp(12), color=GOLD)
    fig.savefig(f"{D}/01-vendor-visibility.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ---------- 02 五道坎 ----------
def fig02():
    fig, ax = newfig(11.4, 7.0)
    title(ax, "五道坎，拦的是两件不同的事", "为什么其他厂商不上 latent reasoning")

    rows = [
        ("①", "CoT 监控的安全刚需", "思维链是安全审计和对齐检查的抓手", TEAL, TEAL_L, "拦可见性"),
        ("②", "latent 隐蔽行为的实证威胁", "ICLR 2026 有 latent 携带不对齐的研究", INK, GREY_L, "拦 latent"),
        ("③", "工程代价", "looped 与流水线并行不兼容，KV 语义全新", INK, GREY_L, "拦 latent"),
        ("④", "收益不确定", "Astra 的提升主要来自训练而非循环结构", INK, GREY_L, "拦 latent"),
        ("⑤", "计费结构", "隐藏 token 按输出计费，本身就是收入来源", GOLD, GOLD_L, "最实的一道"),
    ]
    x0, w = 0.185, 0.72
    y_top, rh, gap = 0.80, 0.125, 0.038
    for i, (num, name, desc, ec, fc, tag) in enumerate(rows):
        y = y_top - i * (rh + gap) - rh
        hot = (i == 4)
        box(ax, x0, y, w, rh, fc, ec, lw=2.0 if hot else 1.2)
        ax.text(x0 + 0.028, y + rh / 2, num, ha="center", va="center",
                fontproperties=fp(15), color=ec)
        ax.text(x0 + 0.062, y + rh / 2, name, ha="left", va="center",
                fontproperties=fp(13.5), color=INK)
        ax.text(x0 + 0.335, y + rh / 2, desc, ha="left", va="center",
                fontproperties=fp(11, False), color=SUB)
        ax.text(x0 + w + 0.018, y + rh / 2, tag, ha="left", va="center",
                fontproperties=fp(11.5), color=ec)

    # 左括号：① 拦可见性 / ②③④ 拦 latent
    y1 = y_top - rh / 2
    y2 = y_top - 4 * (rh + gap) - rh / 2
    for (ya, yb, lab, col) in [(y1, y1, "拦可见性", TEAL), (y2 - 0.0, y2, "拦 latent", INK)]:
        pass
    # ① 单行括号
    ax.plot([0.165, 0.175, 0.175, 0.165], [y1, y1, y1, y1], color=TEAL, lw=2.2)
    ax.text(0.155, y1, "拦可见性", ha="right", va="center",
            fontproperties=fp(11.5), color=TEAL)
    # ②③④ 括号
    yb2 = y_top - 3 * (rh + gap) - rh / 2
    ax.plot([0.165, 0.175, 0.175, 0.165], [yb2, yb2, yb2, yb2], color=INK, lw=0)  # 占位
    ax.plot([0.168, 0.176, 0.176, 0.168], [yb2 + 0.02, yb2 + 0.02, y2 - 0.02, y2 - 0.02],
            color=INK, lw=2.2, solid_capstyle="round")
    ax.text(0.155, (yb2 + y2) / 2, "拦 latent", ha="right", va="center",
            fontproperties=fp(11.5), color=INK)

    # ⑤ 右侧强调
    ax.annotate("", xy=(0.955, y2), xytext=(0.955, y1),
                arrowprops=dict(arrowstyle="-|>", color=GOLD, lw=1.8))
    ax.text(0.978, (y1 + y2) / 2, "越往下越不技术", ha="center", va="center",
            rotation=90, fontproperties=fp(11), color=GOLD)
    fig.savefig(f"{D}/02-five-obstacles.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ---------- 03 一本账的结构 ----------
def fig03():
    fig, ax = newfig(11.4, 6.4)
    title(ax, "一本账，三段都计费", "思考的 token 照常生成、照常按输出价计费，只是不返回给你")

    blocks = [
        ("你的 prompt", "输入 token", "按输入价计费", TEAL, TEAL_L, "solid"),
        ("模型思考", "隐藏 token", "按输出价计费 · 不返回", RED, RED_L, "dashed"),
        ("最终输出", "输出 token", "按输出价计费", TEAL, TEAL_L, "solid"),
    ]
    bw, bh = 0.245, 0.30
    y = 0.40
    xs = [0.055, 0.375, 0.695]
    for (x, (name, kind, bill, ec, fc, style)) in zip(xs, blocks):
        ls = (0, (5, 3)) if style == "dashed" else "-"
        box(ax, x, y, bw, bh, fc, ec, lw=2.0 if style == "dashed" else 1.3, ls=ls)
        ax.text(x + bw / 2, y + bh - 0.062, name, ha="center", va="center",
                fontproperties=fp(16), color=INK)
        ax.text(x + bw / 2, y + bh - 0.125, kind, ha="center", va="center",
                fontproperties=fp(12.5, False), color=SUB)
        ax.text(x + bw / 2, y + 0.058, bill, ha="center", va="center",
                fontproperties=fp(12), color=ec)
        if style == "dashed":
            ax.text(x + bw / 2, y + bh + 0.045, "看不见", ha="center", va="center",
                    fontproperties=fp(11.5), color=RED)
            # 被拦掉的示意：返回口打叉
            ax.plot([x + bw - 0.075, x + bw - 0.025], [y + bh - 0.09, y + bh - 0.04],
                    color=RED, lw=2.0)
            ax.plot([x + bw - 0.075, x + bw - 0.025], [y + bh - 0.04, y + bh - 0.09],
                    color=RED, lw=2.0)

    for i in range(2):
        xa = xs[i] + bw
        ax.annotate("", xy=(xs[i + 1] - 0.012, y + bh / 2), xytext=(xa + 0.012, y + bh / 2),
                    arrowprops=dict(arrowstyle="-|>", color=SUB, lw=1.8))

    # 底部：三段都进账单
    ax.add_patch(FancyBboxPatch((0.055, 0.145), 0.885, 0.115,
                                boxstyle="round,pad=0,rounding_size=0.012",
                                facecolor="#ffffff", edgecolor=GOLD, linewidth=1.6))
    ax.text(0.4975, 0.2025, "三段 token 全部计入账单 —— 隐藏思维链买的是「不给你看」，不是「更便宜」",
            ha="center", va="center", fontproperties=fp(13), color=GOLD)

    # 输出价更长的视觉提示（无数值，只用比例）
    ax.text(0.4975, 0.075, "输出单价高于输入价，难 query 的思考用量能把总成本推高数倍",
            ha="center", va="center", fontproperties=fp(11, False), color=SUB)
    fig.savefig(f"{D}/03-billing-structure.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig01(); fig02(); fig03()
    print("done")
