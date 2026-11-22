#!/usr/bin/env python3
"""本篇脚本画图：01 八档可见性光谱 / 02 四条路线就位 / 03 隐藏思维链机制。
规矩：数字/结构用脚本画，图内数字与正文逐字一致。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["axes.unicode_minus"] = False
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
D = "content/2026-11-22-latent-reasoning-four-routes"

BG = "#F8F6F1"
INK = "#26292F"
SUB = "#5b6b7f"
TEAL = "#0E7A6E"
TEAL_L = "#d9ebe7"
GOLD = "#B87C0E"
RED = "#C24A28"
GRID = "#DCD8CE"


def fp(size=13, bold=True):
    return matplotlib.font_manager.FontProperties(fname=FONT if bold else FONT_R, size=size)


def newfig(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
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


# ---------- 01 八档可见性光谱 ----------
def fig01():
    fig, ax = newfig(11.4, 7.6)
    title(ax, "思维链的八档光谱", "判断标准：给不给你看？有没有 token？谁在付钱？")

    rows = [
        ("①", "显式可见 CoT", "思维链全量流式可见（DeepSeek V4 thinking）", TEAL, TEAL_L),
        ("②", "摘要式 CoT", "只给看提炼后的轨迹（GPT-6.1 Sol / Claude 默认）", TEAL, TEAL_L),
        ("③", "完全隐藏 CoT", "token 照常生成，用户不可见、厂商可读", TEAL, TEAL_L),
        ("④", "哑 token 推理", "pause / filler tokens，token 无语义", INK, "#e8e4dc"),
        ("⑤", "抽象 token 语言", "Abstract-CoT，两端之间的过渡带", INK, "#e8e4dc"),
        ("⑥", "连续 latent thought", "Coconut / CODI，思考装在连续向量里", INK, "#e8e4dc"),
        ("⑦", "循环/隐藏计算", "Ouro / Astra recurrent depth / Hidden Decoding", INK, "#e8e4dc"),
        ("⑧", "neuralese", "私有稠密表示里思考——概念下限，目前不存在", RED, "#f6e7e2"),
    ]
    x0, w = 0.155, 0.70
    y_top, rh, gap = 0.845, 0.082, 0.0165
    for i, (num, name, desc, ec, fc) in enumerate(rows):
        y = y_top - i * (rh + gap) - rh
        dashed = (i == 7)
        box(ax, x0, y, w, rh, fc, ec, lw=1.6 if dashed else 1.2,
            ls=(0, (4, 3)) if dashed else "-")
        ax.text(x0 + 0.022, y + rh / 2, num, ha="center", va="center",
                fontproperties=fp(15), color=ec)
        ax.text(x0 + 0.058, y + rh / 2, name, ha="left", va="center",
                fontproperties=fp(13.5), color=INK)
        ax.text(x0 + 0.27, y + rh / 2, desc, ha="left", va="center",
                fontproperties=fp(11, False), color=SUB)

    # 左括号：前三档 / 后五档
    y3 = y_top - 2 * (rh + gap) - rh / 2
    y4 = y_top - 3 * (rh + gap) - rh / 2
    y8 = y_top - 7 * (rh + gap) - rh / 2
    for (ya, yb, lab, col) in [
        (y_top - rh / 2, y3, "前三档\n给不给你看", TEAL),
        (y4, y8, "后五档\n有没有 token", INK),
    ]:
        ax.plot([0.115, 0.125, 0.125, 0.115], [ya, ya, yb, yb],
                color=col, lw=2.2, solid_capstyle="round")
        ax.text(0.105, (ya + yb) / 2, lab, ha="right", va="center",
                fontproperties=fp(11.5), color=col, linespacing=1.5)

    # ③/④ 分界标注（右侧短标签，避开可见性箭头）
    yb = y_top - 3 * (rh + gap)
    ax.plot([x0, x0 + w], [yb + 0.004, yb + 0.004], color=GOLD, lw=2.0, ls=(0, (5, 3)))
    ax.text(x0 + w + 0.018, yb + 0.062, "分界", ha="left", va="center",
            fontproperties=fp(12), color=GOLD)
    ax.text(x0 + w + 0.018, yb + 0.022, "左 = 显示策略", ha="left", va="center",
            fontproperties=fp(10.5), color=GOLD)
    ax.text(x0 + w + 0.018, yb - 0.018, "右 = 计算机制", ha="left", va="center",
            fontproperties=fp(10.5), color=GOLD)

    # 右侧可见性箭头
    ax.annotate("", xy=(0.955, y8), xytext=(0.955, y_top - rh / 2),
                arrowprops=dict(arrowstyle="-|>", color=SUB, lw=1.6))
    ax.text(0.978, (y_top - rh / 2 + y8) / 2, "用户可见性递减", ha="center", va="center",
            rotation=90, fontproperties=fp(11), color=SUB)
    fig.savefig(f"{D}/01-visible-spectrum.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ---------- 02 四条路线在光谱上的就位 ----------
def fig02():
    fig, ax = newfig(11.4, 6.8)
    title(ax, "四条路线，各就各位", "④–⑦ 四档被四条研究路线填实")

    spine = [
        ("④", "哑 token 推理", 0.845),
        ("⑤", "抽象 token 语言", 0.705),
        ("⑥", "连续 latent thought", 0.565),
        ("⑦", "循环/隐藏计算", 0.425),
    ]
    sx, sw, sh = 0.055, 0.30, 0.085
    for num, name, y in spine:
        box(ax, sx, y - sh / 2, sw, sh, "#e8e4dc", INK, lw=1.1)
        ax.text(sx + 0.022, y, num, ha="center", va="center",
                fontproperties=fp(13), color=INK)
        ax.text(sx + 0.052, y, name, ha="left", va="center",
                fontproperties=fp(12), color=INK)

    cards = [
        ("A", "Pause / Filler tokens", "2310.02226 / 2404.15758", "零成本试水，天花板低；依赖密集监督", 0.845, TEAL),
        ("B", "Coconut / CODI", "2412.06769 / 2502.21074", "最纯 latent；训练最重、推理串行", 0.565, GOLD),
        ("C", "WeLM Hidden Decoding", "2607.08186", "工程最干净；唯一验证到前沿规模（80B/617B）", 0.425, RED),
        ("D", "Ouro looped", "2502.05171 / 2510.25741", "参数效率最高；同一组权重循环 T 次", 0.425, "#6b4fa0"),
    ]
    cx, cw, chh = 0.475, 0.45, 0.15
    ys = [0.845, 0.60, 0.325, 0.125]
    for (tag, name, arx, desc, sy, col), cy in zip(cards, ys):
        box(ax, cx, cy - chh / 2, cw, chh, "#ffffff", col, lw=1.6)
        ax.text(cx + 0.028, cy + chh / 2 - 0.038, f"{tag}. {name}", ha="left", va="center",
                fontproperties=fp(13.5), color=col)
        ax.text(cx + 0.028, cy + 0.012, f"arXiv:{arx}", ha="left", va="center",
                fontproperties=fp(10.5, False), color=SUB)
        ax.text(cx + 0.028, cy - chh / 2 + 0.036, desc, ha="left", va="center",
                fontproperties=fp(11, False), color=INK)
        ax.add_patch(FancyArrowPatch((sx + sw + 0.008, sy), (cx - 0.008, cy),
                                     arrowstyle="-|>", mutation_scale=13,
                                     color=col, lw=1.5, alpha=0.75,
                                     connectionstyle="arc3,rad=0.06"))

    ax.text(0.5, 0.012, "C、D 同驻第七档：一个并行流，一个深度循环——都是「没有思维链 token」",
            ha="center", fontproperties=fp(11), color=SUB)
    fig.savefig(f"{D}/02-four-routes-on-spectrum.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ---------- 03 隐藏思维链机制 ----------
def fig03():
    fig, ax = newfig(11.4, 4.6)
    title(ax, "隐藏思维链：token 照常生成，只是不给你看", y=0.93)

    stages = [
        ("你的问题", "prompt", "#e8e4dc", INK),
        ("思考 token\n逐个生成", "占上下文 · 每 token 一次前向", TEAL_L, TEAL),
        ("API 返回处\n被拦掉", "厂商后端可读，用户不可见", "#f6e7e2", RED),
        ("用户只看到\n最终答案", "思维链不在返回值里", "#e8e4dc", INK),
    ]
    x0, bw, bh, gap = 0.045, 0.195, 0.34, 0.045
    y = 0.42
    for i, (name, desc, fc, ec) in enumerate(stages):
        x = x0 + i * (bw + gap)
        box(ax, x, y - bh / 2, bw, bh, fc, ec, lw=1.6)
        ax.text(x + bw / 2, y + 0.055, name, ha="center", va="center",
                fontproperties=fp(13.5), color=INK, linespacing=1.5)
        ax.text(x + bw / 2, y - 0.085, desc, ha="center", va="center",
                fontproperties=fp(10.5, False), color=SUB, linespacing=1.5)
        if i < 3:
            ax.add_patch(FancyArrowPatch((x + bw + 0.006, y), (x + bw + gap - 0.006, y),
                                         arrowstyle="-|>", mutation_scale=16, color=SUB, lw=2))

    ax.text(0.5, 0.135, "计费口径：OpenAI / Anthropic 输出单价 = 输入 5×；DeepSeek 峰时 3–4×",
            ha="center", fontproperties=fp(12), color=GOLD)
    ax.text(0.5, 0.045, "所以「藏起来」买的是不给你看，不是省钱",
            ha="center", fontproperties=fp(12), color=RED)
    fig.savefig(f"{D}/03-hidden-cot-tokens.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig01(); fig02(); fig03()
    print("✅ 01/02/03 三张脚本图完成")
