#!/usr/bin/env python3
"""本篇脚本配图（数字/结构图，全部脚本绘制；AI 图不承载数字）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = "content/2026-10-08-rysana-ts-cpp/"
BLUE, ORANGE, RED, GRAY = "#0F4C81", "#e07a2f", "#c0392b", "#9aa5b1"


def box(ax, x, y, w, h, text, fc="#eef3f8", ec=BLUE, tc="#1f2933", fs=13, lw=1.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, zorder=3)


# ---------- 01 两条重写路线 ----------
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("同一道题，两条重写路线", fontsize=16, fontweight="bold", color="#1f2933", pad=14)

# 上：微软 Go（16 个月）
ax.text(0.04, 0.80, "微软 Go 重写（官方）", fontsize=13, fontweight="bold", color=BLUE, va="center")
ax.add_patch(FancyArrowPatch((0.42, 0.80), (0.94, 0.80), arrowstyle="-|>", mutation_scale=18,
                             lw=3.0, color=BLUE, zorder=1))
ax.text(0.68, 0.87, "16 个月", ha="center", fontsize=13, color=BLUE, fontweight="bold")
ax.text(0.42, 0.72, "2025-03 官宣", ha="center", va="top", fontsize=10.5, color="#52606d")
ax.text(0.94, 0.72, "2026-07 GA", ha="center", va="top", fontsize=10.5, color="#52606d")
ax.text(0.42, 0.60, "提速 8–12×", ha="left", va="center", fontsize=12.5, color=BLUE)

# 隔线
ax.plot([0.04, 0.96], [0.50, 0.50], color="#d5dbe1", lw=1.0)

# 下：John C++（十天窗口）
ax.text(0.04, 0.36, "John 的 C++ 复刻（自称）", fontsize=13, fontweight="bold", color=ORANGE, va="center")
ax.add_patch(FancyArrowPatch((0.42, 0.36), (0.50, 0.36), arrowstyle="-|>", mutation_scale=18,
                             lw=3.0, color=ORANGE, zorder=1))
ax.text(0.53, 0.36, "公开窗口约 10 天", ha="left", va="center", fontsize=11.5, color=ORANGE)
ax.text(0.42, 0.27, "09-27 首推", ha="center", va="top", fontsize=10.5, color="#52606d")
ax.text(0.68, 0.27, "10-07 100% 对位", ha="center", va="top", fontsize=10.5, color="#52606d")
ax.text(0.42, 0.14, "提速自称 25–750×（对 TS6）· 内存 RSS 低 5–20×", ha="left", va="center",
        fontsize=12.5, color=ORANGE)

ax.text(0.5, 0.03, "微软数字为官方口径；John 数字为其本人公布，未第三方验证",
        ha="center", fontsize=10, color="#8a94a0")
plt.tight_layout()
plt.savefig(OUT + "01-race.png", dpi=160)
plt.close()

# ---------- 02 三笔账单 ----------
fig, ax = plt.subplots(figsize=(10, 4.3))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("三笔账单：把代码“搬个家”要多少钱", fontsize=16, fontweight="bold", color="#1f2933", pad=14)

rows = [
    ("John：TS C++ 移植", 10, "$10K", "推理成本 · ~10 万行 C++ · 100% 对位", ORANGE),
    ("Copilot runtime → Rust", 120, "$120K", "token 成本 · 43 万→80 万行 · 15.9×", BLUE),
    ("Bun → Rust", 165, "$165K", "token 成本 · ≈53.5 万行 · 99.8% 测试", BLUE),
]
maxv = 165
y = 0.62
for name, v, label, sub, col in rows:
    ax.text(0.03, y + 0.075, name, fontsize=12.5, fontweight="bold", color="#1f2933", va="center")
    ax.text(0.03, y + 0.005, sub, fontsize=10, color="#52606d", va="center")
    w = 0.50 * v / maxv
    ax.add_patch(FancyBboxPatch((0.42, y), max(w, 0.02), 0.135,
                                boxstyle="round,pad=0.004,rounding_size=0.012",
                                fc=col, ec="none", zorder=2))
    ax.text(0.42 + max(w, 0.02) + 0.015, y + 0.068, label, fontsize=13, fontweight="bold", color=col, va="center")
    y -= 0.235

ax.text(0.5, 0.06, "John 为其本人公布口径；Copilot 为微软公布、Bun 为报道口径",
        ha="center", fontsize=10.5, color="#8a94a0")
plt.tight_layout()
plt.savefig(OUT + "02-bills.png", dpi=160)
plt.close()

print("配图已生成：01-race.png / 02-bills.png")
