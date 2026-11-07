#!/usr/bin/env python3
"""本篇脚本画图：01 存储账 / 03 JL 界衰减 / 04 k 只依赖 ln N / 05 三路线对照 / 07 Matryoshka 截断。
规矩：数字/结构用脚本画，AI 图禁载数字；图内数字与正文逐字一致。"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["axes.unicode_minus"] = False
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
D = "content/2026-11-08-jl-random-projection"

INK = "#1a2332"
SUB = "#5b6b7f"
BLUE = "#0F4C81"
RED = "#c0392b"
GOLD = "#E8A317"
GREEN = "#1e7d5a"
BG = "#ffffff"


def fp(size=13):
    return matplotlib.font_manager.FontProperties(fname=FONT, size=size)


def newfig(w=11, h=5.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def title(ax, text, y=0.94):
    ax.text(0.5, y, text, ha="center", fontproperties=fp(20), color=INK)


# ---------- 01 存储账：10 万篇文档，600MB vs 50MB ----------
def fig01():
    fig, ax = newfig(11, 5.4)
    title(ax, "同样 10 万篇文档，存储账差 12 倍")
    base_y, max_h, bw, x1, x2 = 0.16, 0.56, 0.20, 0.26, 0.64
    ax.add_patch(plt.Rectangle((x1, base_y), bw, max_h, color=BLUE))
    h2 = max_h * 50 / 600
    ax.add_patch(plt.Rectangle((x2, base_y), bw, h2, color=GOLD))
    ax.plot([0.16, 0.86], [base_y, base_y], color=INK, lw=1.4)
    ax.text(x1 + bw / 2, base_y + max_h + 0.04, "600MB+", ha="center", fontsize=25,
            color=BLUE, fontweight="bold", fontproperties=fp(25))
    ax.text(x2 + bw / 2, base_y + h2 + 0.04, "50MB", ha="center", fontsize=25,
            color=GOLD, fontweight="bold", fontproperties=fp(25))
    ax.text(x1 + bw / 2, base_y - 0.06, "1536 维全精度\nfloat32", ha="center",
            fontproperties=fp(13), color=INK)
    ax.text(x2 + bw / 2, base_y - 0.06, "128 维\n砍完再用", ha="center",
            fontproperties=fp(13), color=INK)
    ax.annotate("", xy=(x1 + bw + 0.02, base_y + max_h * 0.5),
                xytext=(x2 - 0.02, base_y + max_h * 0.5),
                arrowprops=dict(arrowstyle="->", color=SUB, lw=1.6))
    ax.text(0.5, base_y + max_h * 0.56, "第一件事不是建索引，是砍维度", ha="center",
            fontproperties=fp(13), color=SUB)
    fig.savefig(f"{D}/01-storage-account.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 03 JL 界：偏离概率指数衰减 ----------
def fig03():
    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=150)
    fig.patch.set_facecolor(BG)
    eps = 0.1
    denom = eps**2 / 2 - eps**3 / 3
    ks = list(range(50, 6001, 50))
    ys = [2 * math.exp(-k * denom) for k in ks]
    ax.plot(ks, ys, color=BLUE, lw=2.6)
    ax.set_yscale("log")
    n = 10**5
    k_star = 2 * math.log(n) / denom
    ax.axhline(2 / n**2, color=RED, lw=1.6, ls="--")
    ax.text(120, 2 / n**2 * 1.6, "10 万点全部点对联合界的线", fontproperties=fp(12), color=RED)
    ax.plot([k_star], [2 / n**2], "o", color=RED, ms=9)
    ax.annotate(f"k≈{round(k_star, -2):.0f} 维，\n全部点对 10% 内误差",
                xy=(k_star, 2 / n**2), xytext=(k_star * 0.44, 2 / n**2 * 40),
                fontproperties=fp(13), color=INK,
                arrowprops=dict(arrowstyle="->", color=SUB, lw=1.4))
    ax.set_xlabel("投影维度 k", fontproperties=fp(13), color=INK)
    ax.set_ylabel("单对点偏离超过 10% 的概率", fontproperties=fp(13), color=INK)
    ax.set_title("投影维度每加一截，偏离概率按指数往下掉", fontproperties=fp(20), color=INK, pad=14)
    for s in ax.spines.values():
        s.set_color(SUB)
    ax.tick_params(colors=SUB)
    for lb in ax.get_xticklabels() + ax.get_yticklabels():
        lb.set_fontproperties(fp(11))
    fig.savefig(f"{D}/03-jl-bound.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 04 k 只依赖 ln N，与 D 无关 ----------
def fig04():
    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=150)
    fig.patch.set_facecolor(BG)
    ns = [10**2, 10**3, 10**4, 10**5, 10**6, 10**7, 10**8, 10**9]
    for eps, color, lab in [(0.1, BLUE, "容忍 10% 误差"), (0.3, GOLD, "容忍 30% 误差")]:
        denom = eps**2 / 2 - eps**3 / 3
        ks = [2 * math.log(n) / denom for n in ns]
        ax.plot(ns, ks, "o-", color=color, lw=2.4, ms=7, label=lab)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.axvline(10**5, color=SUB, lw=1.2, ls=":")
    ax.annotate("10 万个点：\n10% → 约 5000 维\n30% → 约 640 维",
                xy=(10**5, 5000), xytext=(1.3e3, 9000),
                fontproperties=fp(13), color=INK,
                arrowprops=dict(arrowstyle="->", color=SUB, lw=1.4))
    ax.set_xlabel("点的个数 N", fontproperties=fp(13), color=INK)
    ax.set_ylabel("需要的投影维度 k", fontproperties=fp(13), color=INK)
    ax.set_title("k 只跟着点的个数对数走——公式里没有原始维度 D", fontproperties=fp(20), color=INK, pad=14)
    leg = ax.legend(prop=fp(12), loc="lower right", frameon=False)
    for s in ax.spines.values():
        s.set_color(SUB)
    ax.tick_params(colors=SUB)
    for lb in ax.get_xticklabels() + ax.get_yticklabels():
        lb.set_fontproperties(fp(11))
    fig.savefig(f"{D}/04-k-vs-n.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 05 三路线对照 ----------
def fig05():
    fig, ax = newfig(11, 4.9)
    title(ax, "保住 10% 的距离误差，三条路线各要多少维")
    rows = [
        ("随机 JL（不看数据）", 5000, BLUE, "约 5000 维"),
        ("PCA（数据有低秩才赢）", None, SUB, "看数据"),
        ("MLA 学习投影（DeepSeek）", 576, GOLD, "512 + 64 = 576 个标量"),
    ]
    base_y, bh, gap = 0.72, 0.14, 0.235
    x0, xmax = 0.30, 0.90
    for i, (name, val, color, lab) in enumerate(rows):
        y = base_y - i * gap
        ax.text(x0 - 0.02, y + bh / 2, name, ha="right", va="center",
                fontproperties=fp(14), color=INK)
        if val is None:
            ax.add_patch(FancyBboxPatch((x0, y), xmax - x0, bh,
                                        boxstyle="round,pad=0.004,rounding_size=0.02",
                                        fc="#eef2f7", ec=SUB, lw=1.4, hatch="//"))
            ax.text(x0 + (xmax - x0) / 2, y + bh / 2, "取决于数据本身有没有低秩结构",
                    ha="center", va="center", fontproperties=fp(12), color=SUB)
        else:
            w = (xmax - x0) * (math.log10(val) / math.log10(5000))
            ax.add_patch(plt.Rectangle((x0, y), w, bh, color=color))
            ax.text(x0 + w + 0.012, y + bh / 2, lab, ha="left", va="center",
                    fontproperties=fp(13), color=INK)
    ax.text(0.5, 0.06, "随机是地板，学习是天花板", ha="center",
            fontproperties=fp(15), color=RED)
    fig.savefig(f"{D}/05-three-way.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 07 Matryoshka 截断 ----------
def fig07():
    fig, ax = newfig(11, 5.2)
    title(ax, "Matryoshka：同一个向量，截出一串长度")
    dims = [(1024, BLUE, "原生"), (512, BLUE, ""), (256, GOLD, ""), (128, RED, "标题里的数")]
    base_y, bh, gap = 0.70, 0.115, 0.155
    x0, xmax = 0.24, 0.86
    for i, (d, color, note) in enumerate(dims):
        y = base_y - i * gap
        w = (xmax - x0) * d / 1024
        ax.add_patch(plt.Rectangle((x0, y), w, bh, color=color, alpha=0.92))
        ax.text(x0 - 0.02, y + bh / 2, f"{d} 维", ha="right", va="center",
                fontproperties=fp(14), color=INK)
        if note:
            ax.text(x0 + w + 0.015, y + bh / 2, note, ha="left", va="center",
                    fontproperties=fp(12), color=SUB)
    ax.annotate("", xy=(x0 + 0.02, base_y + 0.05), xytext=(x0 + (xmax - x0) + 0.02, base_y + 0.05),
                arrowprops=dict(arrowstyle="->", color=SUB, lw=1.4))
    ax.text(0.5, base_y + 0.09, "越截越短，也越省——但精度掉多少，只能自己的数据实测",
            ha="center", fontproperties=fp(13), color=SUB)
    fig.savefig(f"{D}/07-matryoshka-layers.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig01(); fig03(); fig04(); fig05(); fig07()
    print("5 script figures done")
