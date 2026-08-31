#!/usr/bin/env python3
"""NSA 稀疏注意力文章脚本画图：数字/结构由脚本承载，AI 图不碰数字。
调色：主蓝 #0F4C81（grace 主题）、橙 #E8A33D、警告红 #C0392B。
数字与 weixin.md 正文一致：8.6% = 5632/65536；11.6×/9.0×/6.0×。
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os

for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

BLUE = "#0F4C81"
ORANGE = "#E8A33D"
RED = "#C0392B"
GRAY = "#999999"
OUT = "content/2026-09-02-nsa-sparse-attention"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{OUT}/{name}", dpi=150)
    print("saved", name)


# ---------- 01: attention map 块状聚类（回应开头） ----------
def chart_attention_map():
    rng = np.random.default_rng(42)
    n = 64
    # 块状结构：分成 16 个块，每块统一强度 + 少量噪声；右下 query 附近更亮
    scores = np.zeros((n, n))
    blocks = rng.integers(0, 4, size=16)
    for b in range(16):
        val = [0.12, 0.3, 0.55, 0.9][blocks[b]]
        scores[b * 4:(b + 1) * 4, :] = val
    scores += rng.uniform(0, 0.08, size=(n, n))
    # 让「当前 token」行整体更强
    scores[60:, :] = np.clip(scores[60:, :] + 0.25, 0, 1)
    scores[:, 60:] = np.clip(scores[:, 60:] + 0.1, 0, 1)
    scores = np.clip(scores, 0, 1)

    fig, ax = plt.subplots(figsize=(7.8, 6.6), dpi=150)
    im = ax.imshow(scores, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlabel("历史 token（key）", fontsize=12)
    ax.set_ylabel("当前 token（query）", fontsize=12)
    ax.set_title("attention scores 天然成块：相邻 token 的重要度相近", fontsize=13)
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("注意力分数", fontsize=11)
    # 红圈标出真正的亮块
    ax.annotate("亮的是整块，不是单点", xy=(62, 62), xytext=(30, 12),
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.8),
                fontsize=12, color=RED)
    save(fig, "01-attention-map.png")


# ---------- 02: 8.6% 账本 ----------
def chart_863():
    ctx = ["8192", "16384", "32768", "65536"]
    loaded = [2048, 2560, 3584, 5632]
    pct = [round(v / int(c) * 100, 1) for v, c in zip(loaded, ctx)]
    x = np.arange(len(ctx))
    fig, ax = plt.subplots(figsize=(8.6, 5.4), dpi=150)
    bars = ax.bar(x, loaded, width=0.55, color=BLUE)
    for b, v, p, c in zip(bars, loaded, pct, ctx):
        ax.text(b.get_x() + b.get_width() / 2, v + 60,
                f"{v}\n({p}%)", ha="center", fontsize=12)
    # 堆叠说明最后一根的构成：4096 压缩 + 1024 选择 + 512 滑窗 = 5632
    ax.text(3, 5632 + 480, "4096 压缩 + 1024 选择 + 512 滑窗", ha="center",
            fontsize=11.5, color=ORANGE)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\n上下文" for c in ctx], fontsize=12)
    ax.set_ylim(0, 6800)
    ax.set_ylabel("每步真正加载的 token 数", fontsize=12)
    ax.set_title("序列越长，实际加载占比越低：65536 时只有 8.6%", fontsize=13)
    ax.grid(True, axis="y", alpha=0.25)
    save(fig, "02-863-accounting.png")


# ---------- 03: 速度对比 ----------
def chart_speedup():
    labels = ["decode", "prefill（前向）", "反向"]
    speed = [11.6, 9.0, 6.0]
    fig, ax = plt.subplots(figsize=(8.6, 5.2), dpi=150)
    bars = ax.bar(labels, speed, width=0.5, color=[BLUE, ORANGE, GRAY])
    for b, v in zip(bars, speed):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.2, f"{v}×",
                ha="center", fontsize=15, fontweight="bold")
    ax.set_ylim(0, 13.5)
    ax.set_ylabel("相对 FlashAttention-2（倍速）", fontsize=12)
    ax.set_title("64k 上下文速度对比：解码 11.6×，前向 9.0×，反向 6.0×", fontsize=13)
    ax.grid(True, axis="y", alpha=0.25)
    save(fig, "03-speedup.png")


if __name__ == "__main__":
    chart_attention_map()
    chart_863()
    chart_speedup()
