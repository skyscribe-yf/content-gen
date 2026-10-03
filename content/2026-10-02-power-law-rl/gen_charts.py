#!/usr/bin/env python3
# power-law-rl 篇 3 张脚本图
# 输出到 content/2026-10-02-power-law-rl/
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

OUT = Path("content/2026-10-02-power-law-rl")
OUT.mkdir(parents=True, exist_ok=True)

for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False


def fig_zipf():
    """01 幂律长尾：词频 log-log 直线（Zipf f ∝ 1/r）。"""
    fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=150)
    r = np.arange(1, 1001)
    f = 1.0 / r

    ax.loglog(r, f, color="#2E86C1", lw=2.4, label="词频 $f(r) \\propto 1/r$（幂律）")
    ax.fill_between(r, f, 1e-4, color="#2E86C1", alpha=0.12, lw=0)

    # 关键标注：1/10/100 倍关系（Zipf 经典量级）
    for rank, mult in [(1, "第一名"), (10, "第十名 ≈ 1/10"), (100, "第一百名 ≈ 1/100")]:
        ax.scatter([rank], [1.0 / rank], color="#C0392B", zorder=5, s=45)
    ax.annotate(
        "第一名 the ≈ 第十名的 10 倍\n≈ 第一百名的 100 倍",
        xy=(1, 1.0), xytext=(0.30, 0.82), textcoords="axes fraction",
        fontsize=11, color="#C0392B",
        arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.4),
        bbox=dict(boxstyle="round,pad=0.4", fc="#FDEDEC", ec="#C0392B", lw=1.0, alpha=0.95),
    )
    ax.annotate(
        "长尾：排名 100 之后的词\n单个罕见，加起来却占大头",
        xy=(300, 1.0 / 300), xytext=(0.52, 0.32), textcoords="axes fraction",
        fontsize=11, color="#1A5276",
        arrowprops=dict(arrowstyle="->", color="#2E86C1", lw=1.4),
        bbox=dict(boxstyle="round,pad=0.4", fc="#EBF5FB", ec="#2E86C1", lw=1.0, alpha=0.95),
    )

    ax.set_xlabel("按出现次数的排名 r（log）", fontsize=12)
    ax.set_ylabel("出现次数 f（log）", fontsize=12)
    ax.set_title("幂律的身份证：双对数坐标上的一条直线（Zipf 词频）", fontsize=13)
    ax.set_xlim(0.8, 1200)
    ax.set_ylim(1e-4, 2)
    ax.legend(loc="lower left", fontsize=11)
    ax.grid(True, which="both", ls=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(OUT / "01-powerlaw-loglog.png", facecolor="white")
    plt.close(fig)


def fig_scaling():
    """02 RL 后训练 Scaling Law：幂律下降 + 小模型外推示意（示意曲线，数字只标论文原文量级）。"""
    fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=150)

    x = np.linspace(0.02, 1.0, 300)
    # 示意：测试损失 L=1-pass@1 随算力幂律下降（不同参数量学习效率不同）
    for N, k, c in [("0.5B", 0.9, "#AED6F1"), ("7B", 1.35, "#5DADE2"), ("32B", 1.7, "#2E86C1"), ("72B", 1.85, "#1A5276")]:
        L = 0.9 * x ** (-0.22 * k) * 0.45 + 0.12
        ax.plot(x, L, lw=2.2, color=c, label=f"{N}（示意）")
        ax.scatter([x[60]], [L[60]], color=c, s=35, zorder=5)

    # 外推示意：小模型前 20-30% 数据 → 收敛值
    ax.axvspan(0.02, 0.30, color="#F9E79F", alpha=0.35, lw=0)
    ax.annotate(
        "训练早期 20%–30% 数据点\n就能外推收敛值（论文原文）",
        xy=(0.16, 0.78), xytext=(0.10, 0.82), textcoords="axes fraction",
        fontsize=11, color="#B9770E",
        arrowprops=dict(arrowstyle="->", color="#B9770E", lw=1.4),
        bbox=dict(boxstyle="round,pad=0.4", fc="#FEF9E7", ec="#B9770E", lw=1.0, alpha=0.95),
    )
    ax.annotate(
        "小模型数据可外推 72B 训练轨迹\n幂律拟合 R²>0.99（论文原文）",
        xy=(0.75, 0.30), xytext=(0.42, 0.55), textcoords="axes fraction",
        fontsize=11, color="#1A5276",
        arrowprops=dict(arrowstyle="->", color="#2E86C1", lw=1.4),
        bbox=dict(boxstyle="round,pad=0.4", fc="#EBF5FB", ec="#2E86C1", lw=1.0, alpha=0.95),
    )

    ax.set_xlabel("训练算力 / 数据量（log，示意）", fontsize=12)
    ax.set_ylabel("测试损失 L = 1 − pass@1（log，示意）", fontsize=12)
    ax.set_title("RL 后训练的幂律：损失随算力按幂律下降（示意）", fontsize=13)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.legend(loc="lower left", fontsize=11, ncol=2)
    ax.grid(True, which="both", ls=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(OUT / "02-rl-scaling-law.png", facecolor="white")
    plt.close(fig)


def fig_narrowing():
    """03 剪尾前后：分布收窄示意（无具体数字，仅示意）。"""
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.6), dpi=150, sharey=True)

    x = np.linspace(-6, 6, 800)
    # 剪尾前：多峰长尾（罕见解住在尾巴上）
    mix = (
        0.42 * np.exp(-0.5 * ((x + 2.2) / 1.5) ** 2)
        + 0.24 * np.exp(-0.5 * ((x - 0.6) / 1.2) ** 2)
        + 0.12 * np.exp(-0.5 * ((x - 2.8) / 0.9) ** 2)
        + 0.06 * np.exp(-0.5 * ((x - 4.6) / 0.7) ** 2)
        + 0.03 * np.exp(-0.5 * ((x + 4.8) / 0.8) ** 2)
    )
    # 剪尾后：概率集中到主峰
    narrow = 0.86 * np.exp(-0.5 * ((x - 0.2) / 0.75) ** 2)

    ax = axes[0]
    ax.plot(x, mix, color="#2E86C1", lw=2.4)
    ax.fill_between(x, mix, color="#2E86C1", alpha=0.15, lw=0)
    ax.annotate("尾巴上的罕见解法", xy=(4.6, 0.06), xytext=(0.30, 0.72),
                textcoords="axes fraction", fontsize=11, color="#B9770E",
                arrowprops=dict(arrowstyle="->", color="#B9770E", lw=1.4),
                bbox=dict(boxstyle="round,pad=0.4", fc="#FEF9E7", ec="#B9770E", lw=1.0, alpha=0.95))
    ax.set_title("剪尾前：分布宽、长尾上有罕见解", fontsize=12)
    ax.set_xlabel("解法空间（示意）", fontsize=11)

    ax = axes[1]
    ax.plot(x, narrow, color="#C0392B", lw=2.4)
    ax.fill_between(x, narrow, color="#C0392B", alpha=0.15, lw=0)
    ax.plot(x, mix, color="#2E86C1", lw=1.0, ls="--", alpha=0.45, label="剪尾前（对照）")
    ax.annotate("概率集中到少数模式\n= 熵坍缩", xy=(0.2, 0.86), xytext=(0.34, 0.72),
                textcoords="axes fraction", fontsize=11, color="#C0392B",
                arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.4),
                bbox=dict(boxstyle="round,pad=0.4", fc="#FDEDEC", ec="#C0392B", lw=1.0, alpha=0.95))
    ax.set_title("剪尾后：分布变窄，长尾消失", fontsize=12)
    ax.set_xlabel("解法空间（示意）", fontsize=11)
    ax.legend(loc="upper left", fontsize=10)

    for ax in axes:
        ax.set_ylabel("概率密度（示意）", fontsize=11)
        ax.set_yticks([])
        ax.grid(True, ls=":", alpha=0.35)

    fig.suptitle("RL 后训练的剪刀：涨分的秘密 = 长尾被剪掉（示意，无具体数字）", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUT / "03-sharpening-collapse.png", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    fig_zipf()
    fig_scaling()
    fig_narrowing()
    print("done:", sorted(p.name for p in OUT.glob("0*.png")))
