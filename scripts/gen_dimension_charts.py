#!/usr/bin/env python3
# gen_dimension_charts.py — 维度诅咒/祝福 文章的 4 张脚本图
# 输出到 content/2026-08-12-维度诅咒/
import math
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("content/2026-08-12-维度诅咒")
OUT.mkdir(parents=True, exist_ok=True)

# 中文字体
for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False


def chi_pdf(r, d):
    """R=||x|| for x~N(0,I_d): chi distribution PDF"""
    logp = (
        math.log(2) * (1 - d / 2)
        + (d - 1) * np.log(r)
        - (r**2) / 2
        - math.lgamma(d / 2)
    )
    return np.exp(logp)


def fig_thin_shell():
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=160)
    d_list = [10, 100, 1000]
    colors = ["#2a6fdb", "#e0a82e", "#8a4fd8"]
    for d, c in zip(d_list, colors):
        r = np.linspace(0.1, math.sqrt(d) * 2.2, 400)
        p = chi_pdf(r, d)
        ax.plot(r, p, color=c, lw=2.4, label=f"维度 d = {d}")
        peak = math.sqrt(d - 1)
        ax.axvline(peak, color=c, lw=0.8, ls="--", alpha=0.55)
    ax.set_xlabel("半径 r = ‖x‖")
    ax.set_ylabel("概率密度")
    ax.set_title("高斯薄球壳：维度越高，质量越集中在半径 √d 附近的薄壳上", pad=12)
    ax.legend(frameon=False)
    ax.set_xlim(0, 100)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "03-thin-shell-curve.png", bbox_inches="tight")
    plt.close(fig)


def fig_angle_hist():
    rng = np.random.default_rng(42)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=160)
    for ax, d in zip(axes, [10, 1000]):
        u = rng.normal(size=(20000, d))
        v = rng.normal(size=(20000, d))
        cos = (u * v).sum(1) / (np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1))
        ax.hist(cos, bins=80, color="#2a6fdb", alpha=0.85)
        ax.set_title(f"d = {d}：夹角集中在 90° 附近", fontsize=12)
        ax.set_xlabel("余弦相似度 cos θ")
        ax.set_ylabel("频数")
        ax.set_xlim(-1, 1)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("高维随机向量近似正交", y=1.02, fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / "05-angle-histogram.png", bbox_inches="tight")
    plt.close(fig)


def box(ax, x, y, w, h, text, fc, ec):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04",
            fc=fc, ec=ec, lw=1.6,
        )
    )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11.5)


def arrow(ax, x1, y1, x2, y2, label=None):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
            color="#333333", lw=1.8,
        )
    )
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.08, label, ha="center", va="bottom", fontsize=10.5, color="#555555")


def fig_mla():
    fig, ax = plt.subplots(figsize=(10.5, 4.2), dpi=160)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.4)
    ax.axis("off")
    box(ax, 0.3, 2.2, 2.0, 1.4, "K / V 缓存\n（高维）", "#eef3fc", "#2a6fdb")
    arrow(ax, 2.3, 2.9, 3.7, 2.9, "低秩压缩")
    box(ax, 3.7, 2.2, 2.2, 1.4, "隐空间\n（低维主方向）", "#fdf3d7", "#e0a82e")
    arrow(ax, 5.9, 2.9, 7.3, 2.9, "用的时候展开")
    box(ax, 7.3, 2.2, 2.0, 1.4, "恢复 K / V\n（信息仍在）", "#eef3fc", "#2a6fdb")
    arrow(ax, 9.3, 2.9, 10.6, 2.9)
    box(ax, 10.6, 2.2, 1.5, 1.4, "注意力", "#f2e7fb", "#8a4fd8")
    ax.text(6, 4.9, "MLA：方向保留，冗余去掉——高维里真正需要的是主方向", ha="center", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "06-mla-lowrank.png", bbox_inches="tight")
    plt.close(fig)


def fig_v4():
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=160)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 5.8)
    ax.axis("off")
    box(ax, 0.3, 2.3, 2.2, 1.4, "长上下文\ntoken 流", "#eef3fc", "#2a6fdb")
    arrow(ax, 2.5, 3.0, 3.8, 3.0, "压缩成块")
    box(ax, 3.8, 2.3, 2.4, 1.4, "压缩后的\nKV 块", "#fdf3d7", "#e0a82e")
    arrow(ax, 6.2, 3.0, 7.4, 3.0)
    box(ax, 7.4, 2.3, 2.3, 1.4, "Lightning\nIndexer 打分", "#f2e7fb", "#8a4fd8")
    arrow(ax, 9.7, 3.0, 10.9, 3.0, "只挑 top-k")
    box(ax, 10.9, 2.3, 2.1, 1.4, "注意力\n只算选中块", "#eef3fc", "#2a6fdb")
    ax.text(6.6, 5.2, "V4：不压缩所有 KV，而是先筛后算——高维里值得关注的方向本来就不多", ha="center", fontsize=12.5)
    fig.tight_layout()
    fig.savefig(OUT / "07-v4-csa-indexer.png", bbox_inches="tight")
    plt.close(fig)


def main():
    fig_thin_shell()
    fig_angle_hist()
    fig_mla()
    fig_v4()
    print("charts done ->", OUT)


if __name__ == "__main__":
    main()
