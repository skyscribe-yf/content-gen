#!/usr/bin/env python3
# gen_manifold_charts.py — 流形假设篇 2 张脚本图
# 输出到 content/2026-09-30-manifold-hypothesis/
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

OUT = Path("content/2026-09-30-manifold-hypothesis")
OUT.mkdir(parents=True, exist_ok=True)

for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

D_AMBIENT = 150_528  # ImageNet 224x224x3


def fig_sampling():
    """采样需求的指数：按环境维度 vs 按内在维度（26-43）。"""
    fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=150)
    d = np.linspace(1, D_AMBIENT, 400)

    ax.plot(d, d, color="#C0392B", lw=2.4, label="按环境维度均匀采样（立方体顶点 2$^d$，示意）")
    ax.axhspan(26, 43, color="#2E86C1", alpha=0.30, lw=0)
    ax.plot([], [], color="#2E86C1", alpha=0.7, lw=8, label="按内在维度（26–43，学习界只随它涨）")

    ax.axvline(D_AMBIENT, color="#888", ls=":", lw=1.2)
    ax.scatter([D_AMBIENT], [D_AMBIENT], color="#C0392B", zorder=5, s=45)
    ax.annotate(
        "ImageNet 环境维度 150,528\n指数 = 150,528（2$^{150528}$，写不出的数）",
        xy=(D_AMBIENT, D_AMBIENT), xytext=(0.60, 0.80), textcoords="axes fraction",
        fontsize=11, color="#C0392B",
        arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.4),
        bbox=dict(boxstyle="round,pad=0.4", fc="#FDEDEC", ec="#C0392B", lw=1.0, alpha=0.95),
    )
    ax.annotate(
        "内在维度 26–43：指数最多 43\n2$^{43}$ ≈ 8.8 万亿，够摸清纸面",
        xy=(D_AMBIENT * 0.45, 43), xytext=(0.30, 0.30), textcoords="axes fraction",
        fontsize=11, color="#1A5276",
        arrowprops=dict(arrowstyle="->", color="#2E86C1", lw=1.4),
        bbox=dict(boxstyle="round,pad=0.4", fc="#EAF2F8", ec="#2E86C1", lw=1.0, alpha=0.95),
    )

    ax.set_xlabel("空间维度 $d$", fontsize=12)
    ax.set_ylabel("采样需求的指数（样本数 = 2$^y$）", fontsize=12)
    ax.set_title("样本需求随维度指数增长：关键是指数里放的是哪个维度", fontsize=13, pad=10)
    ax.set_xlim(0, D_AMBIENT * 1.04)
    ax.set_ylim(0, D_AMBIENT * 1.10)
    ax.legend(loc="upper left", fontsize=10, framealpha=0.95)
    ax.grid(alpha=0.25)
    fig.text(0.5, 0.015,
             "示意曲线（指数取 c=1）；依据：样本界只依赖内在维度、与环境维度无关"
             "（Narayanan & Mitter 2010，转引自 Pope et al. 2021）",
             ha="center", fontsize=9, color="#555")
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(OUT / "01-sampling-explosion.png", facecolor="white")
    plt.close(fig)


def fig_text_id():
    """Pedashenko 2025：文体内在维度 科学 8 / 百科 9 / 创作 10.5。"""
    fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=150)
    labels = ["科学文本", "百科文本", "创作/观点文本"]
    vals = [8, 9, 10.5]
    colors = ["#2E86C1", "#5DADE2", "#E67E22"]
    bars = ax.bar(labels, vals, color=colors, width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.22, f"{v:g}",
                ha="center", fontsize=13, fontweight="bold")
    ax.set_ylabel("模型表示空间中的内在维度（ID）", fontsize=12)
    ax.set_ylim(0, 13.2)
    ax.set_title("同一批模型：创作类文本需要的自由度最高", fontsize=13, pad=10)
    ax.grid(axis="y", alpha=0.25)
    ax.text(0.5, -0.22,
            "隐藏层环境维度动辄几千；真正用到的自由度只有 8–10.5"
            "（Pedashenko et al. 2025, arXiv:2511.15210，全部被测模型一致）",
            transform=ax.transAxes, ha="center", fontsize=9, color="#555")
    fig.tight_layout()
    fig.savefig(OUT / "04-text-id.png", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    fig_sampling()
    fig_text_id()
    print("done:", sorted(p.name for p in OUT.glob("0*.png")))
