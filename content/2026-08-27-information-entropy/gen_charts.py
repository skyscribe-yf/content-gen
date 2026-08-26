#!/usr/bin/env python3
"""信息熵篇脚本图：数字必须与 weixin.md 一致（2026-08-25 闭式计算）。

01-entropy-curve.png: 二进制熵 H(p) = -p log2 p - (1-p) log2 (1-p)，p∈(0,1)
                      标注 p=0.5 处最大 1.000 bit、9:1 硬币 0.469 bit
03-zip-compare.png:   zip 实验对比：1MB 循环文本 → 994 B（1006×） vs
                      1MB 真随机 → 1,000,316 B（+0.03%），对数轴条形
"""
import os
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT = Path(__file__).parent
for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

BG = "#F7F3EB"
INK = "#2C2A26"
AMBER = "#D97706"
RED = "#C2410C"
GREEN = "#3F6F4A"
MUTED = "#8A8478"
CARD = "#FFFCF6"


def _prep_ax(ax, bg=BG):
    ax.set_facecolor(bg)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(colors=INK, labelsize=10.5)


def fig_entropy_curve():
    p = np.linspace(0.001, 0.999, 600)
    h = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    fig.patch.set_facecolor(BG)
    _prep_ax(ax)

    ax.plot(p, h, color=AMBER, lw=3.0)
    # 标注：最大值 p=0.5 → 1.000
    ax.scatter([0.5], [1.0], color=RED, s=64, zorder=5)
    ax.annotate("p=0.5 时最大：1.000 bit\n（最「没谱」，信息最多）",
                xy=(0.5, 1.0), xytext=(0.28, 1.12),
                fontsize=11.5, color=RED, ha="center",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.4))
    # 标注：9:1 硬币 → 0.469
    h09 = 0.469
    ax.scatter([0.9], [h09], color=GREEN, s=64, zorder=5)
    ax.annotate("9:1 硬币：0.469 bit\n（越偏越省信息）",
                xy=(0.9, h09), xytext=(0.68, 0.22),
                fontsize=11.5, color=GREEN, ha="center",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.4))

    ax.set_xlabel("正面的概率 p", fontsize=12, color=INK)
    ax.set_ylabel("熵 H(p)（bit）", fontsize=12, color=INK)
    ax.set_ylim(0, 1.25)
    ax.set_title("二进制熵曲线：越「没谱」，熵越大",
                 fontsize=13.5, color=INK, fontweight="bold", pad=10)
    fig.savefig(OUT / "01-entropy-curve.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_zip_compare():
    labels = ["1MB 循环文本\n（abcabc…）", "1MB 真随机字节\n（无规律）"]
    sizes = [994, 1000316]
    comp = ["压到 994 字节（1006×）", "压到 1,000,316 字节（+0.03%）"]
    colors = [GREEN, RED]
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    fig.patch.set_facecolor(BG)
    _prep_ax(ax)

    bars = ax.bar(labels, sizes, color=colors, width=0.45, zorder=3)
    ax.set_yscale("log")
    ax.set_ylim(300, 4_000_000)
    for bar, txt, c in zip(bars, comp, colors):
        ax.annotate(txt, xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 14), textcoords="offset points",
                    fontsize=11.5, color=c, ha="center", fontweight="bold")

    ax.set_ylabel("zlib 压缩后大小（字节，对数轴）", fontsize=12, color=INK)
    ax.set_title("zip 实验：一样大的文件，一个压到 1/1000，一个压完反而变大",
                 fontsize=13.5, color=INK, fontweight="bold", pad=10)
    fig.savefig(OUT / "03-zip-compare.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_entropy_curve()
    fig_zip_compare()
    print("done: 01-entropy-curve / 03-zip-compare 生成完毕")
    print("校验: H(0.5)=", round(-0.5 * np.log2(0.5) * 2, 3),
          " H(0.9)=", round(-0.9 * np.log2(0.9) - 0.1 * np.log2(0.1), 3),
          " 1000000/994=", round(1000000 / 994, 1))
