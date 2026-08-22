#!/usr/bin/env python3
"""02 / 05 脚本图：数字必须与 weixin.md 一致。

02-kl-decompose.png: KL = H(P,Q) − H(P)，熵=常数求导归零，交叉熵才是主角
05-ood-cliff.png:    P=N(0,1), Q=N(3,1)，P>0 而 Q≈0 区域 KL 贡献爆炸
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

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


def _card(ax, x, y, w, h, title, sub, color):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.12",
                         facecolor=CARD, edgecolor=color, lw=2.0)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
            fontsize=15, color=color, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center",
            fontsize=10.5, color=INK)


def fig_decompose():
    fig, ax = plt.subplots(figsize=(8.8, 5.6), dpi=160, facecolor=BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.3)
    ax.axis("off")

    # 左：KL 定义卡
    _card(ax, 0.30, 2.45, 3.0, 2.05,
          r"$\mathbb{E}_{P}\left[\log\dfrac{P(x)}{Q(x)}\right]$",
          "KL 散度：想压小的目标", INK)

    # 等号
    ax.text(3.68, 3.48, "=", ha="center", va="center", fontsize=22, color=INK, fontweight="bold")

    # 右上：交叉熵（主角）
    _card(ax, 4.40, 3.42, 5.2, 1.70,
          r"$H(P,Q)=-\,\mathbb{E}_{P}\left[\log Q(x)\right]$",
          "交叉熵：样本从 Q 抽出的可能性 → 模型能学", AMBER)

    # 减号
    ax.text(7.00, 3.02, "−", ha="center", va="center", fontsize=20, color=MUTED, fontweight="bold")

    # 右下：熵（常数）
    _card(ax, 4.40, 0.95, 5.2, 1.70,
          r"$H(P)=-\,\mathbb{E}_{P}\left[\log P(x)\right]$",
          "信息熵：只跟数据有关 → 常数，求导归零", MUTED)

    # 底部结论横幅（顶部）
    banner = FancyBboxPatch((0.30, 5.50), 9.3, 0.62,
                            boxstyle="round,pad=0.05,rounding_size=0.14",
                            facecolor="#EAF0E6", edgecolor=GREEN, lw=1.8)
    ax.add_patch(banner)
    ax.text(4.95, 5.81, "最小化 KL ≡ 最小化交叉熵（常数那一半对优化毫无贡献）",
            ha="center", va="center", fontsize=13, color=GREEN, fontweight="bold")

    fig.savefig(OUT / "02-kl-decompose.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def fig_ood_cliff():
    import numpy as np

    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=160, facecolor=BG)
    ax.set_facecolor(BG)

    x = np.linspace(-6, 7, 1200)
    p = np.exp(-(x ** 2) / 2) / np.sqrt(2 * np.pi)            # P = N(0,1)
    q = np.exp(-((x - 3) ** 2) / 2) / np.sqrt(2 * np.pi)      # Q = N(3,1)

    ax.plot(x, p, color=GREEN, lw=2.6, label="$P$：数据真实分布 $N(0,1)$")
    ax.plot(x, q, color=AMBER, lw=2.6, label="$Q$：模型分布 $N(3,1)$")

    # 危险区：P>0 而 Q≈0（x < -1）
    mask = (x < -1) & (p > 1e-4)
    ax.fill_between(x[mask], p[mask], color=RED, alpha=0.30, hatch="//",
                    edgecolor=RED, lw=0.0)
    ax.annotate("黑天鹅区：$P(x)>0$ 而 $Q(x)\\approx 0$\n该点贡献 $\\log\\dfrac{P}{Q} \\to +\\infty$",
                xy=(-1.55, 0.075), xytext=(-5.7, 0.66),
                fontsize=11.5, color=RED, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=2.0))

    # 优化器逃离箭头（上方空白区）
    ax.annotate("", xy=(2.6, 0.86), xytext=(-0.2, 0.86),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.4))
    ax.text(1.2, 0.94, "优化器把 $Q$ 推离危险区", ha="center", fontsize=11, color=INK)

    # KL 值对比框（闭式解：Δμ²/2 = 4.5 nats）
    ax.text(6.55, 1.02, f"$D_{{KL}}(P\\|Q) \\approx {kl_value():.1f}$ nats", ha="center",
            fontsize=13, color=RED, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=CARD, edgecolor=RED, lw=1.8))
    ax.text(6.55, 0.60, "全靠左边悬崖抬起来的", ha="center", fontsize=10.5, color=MUTED)

    ax.set_xlim(-6, 7.5)
    ax.set_ylim(0, 1.28)
    ax.legend(loc="upper left", fontsize=10.5, framealpha=0.0,
              bbox_to_anchor=(0.0, 0.97))
    ax.set_title("一把只看整体的尺子，会在没覆盖的地方爆炸", fontsize=13.5,
                 color=INK, fontweight="bold", pad=10)

    fig.savefig(OUT / "05-ood-cliff.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def kl_value():
    """闭式解：KL(N(μ1,1)||N(μ2,1)) = Δμ²/2 = 9/2。"""
    return (3 - 0) ** 2 / 2


if __name__ == "__main__":
    fig_decompose()
    fig_ood_cliff()
    print("done:", OUT / "02-kl-decompose.png", OUT / "05-ood-cliff.png")
