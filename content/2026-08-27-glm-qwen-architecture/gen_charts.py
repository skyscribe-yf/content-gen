#!/usr/bin/env python3
"""GLM+Qwen 架构篇脚本图：数字必须与 weixin.md 一致（2026-08-27）。

01-attention-cost.png: 注意力成本曲线——全注意力 O(n²) vs 混合注意力（线性压缩+稀疏检索）
                       上下文 1K→1M，全注意力计算量随 n² 爆炸，混合注意力近似线性
02-architecture-compare.png: GLM-5.3-Flash vs Qwen3.8-Flash-Next 架构对照
                       3:1 混合注意力结构示意（34 KDA + 11 MLA/DSA vs 12 组 × 3 GDN + 1 QSA）
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
INK = "#1F2937"
BLUE = "#0F4C81"
RED = "#C0392B"
GREEN = "#2E7D32"
GOLD = "#B8860B"
GRAY = "#9CA3AF"


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print("saved", name)


# ---------- 01 注意力成本曲线 ----------
def chart01():
    ctx = np.array([1, 4, 16, 64, 256, 1024])  # K tokens
    dense = ctx**2  # O(n²) 相对计算量
    hybrid = 0.5 * ctx + 8  # 线性压缩 + 稀疏检索，近似线性（示意）

    fig, ax = plt.subplots(figsize=(8.6, 5.2), facecolor=BG)
    ax.set_facecolor(BG)
    ax.plot(ctx, dense, "-o", color=RED, lw=3, ms=7, label="全注意力：O(n²)，每生成一个字翻全部历史")
    ax.plot(ctx, hybrid, "-s", color=BLUE, lw=3, ms=7, label="混合注意力：压缩记忆 + 稀疏检索（近似线性）")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(ctx)
    ax.set_xticklabels(["1K", "4K", "16K", "64K", "256K", "1M"])
    ax.set_xlabel("上下文长度", fontsize=13)
    ax.set_ylabel("相对计算量（对数轴）", fontsize=13)
    ax.set_title("上下文翻倍，全注意力计算翻 4 倍——这就是拆注意力的原因", fontsize=14, color=INK, pad=14)
    ax.legend(fontsize=11, loc="upper left", frameon=False)
    ax.grid(True, which="both", ls=":", alpha=0.4)
    ax.annotate("1M 上下文：\n每生成一个字\n要算 100 万次相关性", xy=(1024, 1024**2),
                xytext=(60, 3e5), fontsize=11, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED))
    ax.annotate("笔记 + 检索：\n只读压缩后的记忆", xy=(1024, 0.5 * 1024 + 8),
                xytext=(8, 200), fontsize=11, color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE))
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    save(fig, "01-attention-cost.png")


# ---------- 02 架构对照图 ----------
def chart02():
    """GLM vs Qwen 架构对照。注释一律放在色块右侧同一行，避免压字重叠。
    数字与 weixin.md 第②③④节一致（2026-08-27 核查）。"""
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.6), facecolor=BG)

    def draw_glm(ax):
        ax.set_facecolor(BG)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")
        ax.set_title("智谱 GLM-5.3-Flash\n320B 总参 · 每 token 激活 18B · 45 层", fontsize=12, color=INK)
        # 34 层 KDA（压缩记忆）
        ax.add_patch(plt.Rectangle((0.6, 7.9), 3.6, 0.9, fc=BLUE, ec="white", lw=1))
        ax.text(2.4, 8.35, "34 层 KDA", ha="center", fontsize=11, color="white", fontweight="bold")
        ax.text(4.6, 8.35, "线性注意力：历史压成「浓缩笔记」", ha="left", va="center", fontsize=9, color=INK)
        # 11 层 MLA/DSA（省 KV）
        ax.add_patch(plt.Rectangle((0.6, 5.9), 3.6, 0.9, fc=GREEN, ec="white", lw=1))
        ax.text(2.4, 6.35, "11 层 MLA/DSA", ha="center", fontsize=11, color="white", fontweight="bold")
        ax.text(4.6, 6.35, "稀疏检索：KV 缓存砍 4.4 倍", ha="left", va="center", fontsize=9, color=INK)
        # 效果（金块，三行）
        ax.add_patch(plt.Rectangle((0.6, 4.0), 3.6, 1.6, fc=GOLD, ec="white", lw=1))
        for t, y in [("注意力计算 -3.01×", 5.25), ("KV 缓存 -4.44×", 4.8), ("上下文 1M", 4.35)]:
            ax.text(2.4, y, t, ha="center", fontsize=9, color="white", fontweight="bold")

    def draw_qwen(ax):
        ax.set_facecolor(BG)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")
        ax.set_title("阿里 Qwen3.8-Flash-Next\n125B 总参 · 每 token 激活 6B · 48 层", fontsize=12, color=INK)
        # 12 组 × (3 GDN + 1 QSA)：虚线框包住一组，文字居中不溢出
        ax.add_patch(plt.Rectangle((0.6, 5.5), 4.6, 3.6, fc="none", ec=GRAY, ls="--", lw=1.2))
        ax.add_patch(plt.Rectangle((0.6, 7.9), 4.6, 0.9, fc=BLUE, ec="white", lw=1))
        ax.text(2.9, 8.35, "3 层 GDN", ha="center", fontsize=11, color="white", fontweight="bold")
        ax.text(5.6, 8.35, "GDN：历史压成「浓缩笔记」", ha="left", va="center", fontsize=9, color=INK)
        ax.add_patch(plt.Rectangle((0.6, 5.8), 4.6, 0.9, fc=GREEN, ec="white", lw=1))
        ax.text(2.9, 6.25, "1 层 QSA", ha="center", fontsize=11, color="white", fontweight="bold")
        ax.text(5.6, 6.25, "QSA：微块级稀疏检索，精准查档案", ha="left", va="center", fontsize=9, color=INK)
        ax.text(2.9, 4.9, "× 12 组重复 = 48 层", ha="center", fontsize=10, color=GRAY)
        # 效果（金块，三行）
        ax.add_patch(plt.Rectangle((0.6, 1.0), 4.6, 1.6, fc=GOLD, ec="white", lw=1))
        for t, y in [("训练成本 1/9", 2.25), ("51B n-gram 嵌入放显存外", 1.8), ("上下文 262K 原生，可扩 1M", 1.35)]:
            ax.text(2.9, y, t, ha="center", fontsize=9, color="white", fontweight="bold")

    draw_glm(axes[0])
    draw_qwen(axes[1])
    fig.suptitle("同一天，两家把全注意力拆成「压缩记忆 + 稀疏检索」", fontsize=14, color=INK, y=1.0)
    fig.tight_layout()
    save(fig, "02-architecture-compare.png")


if __name__ == "__main__":
    chart01()
    chart02()
