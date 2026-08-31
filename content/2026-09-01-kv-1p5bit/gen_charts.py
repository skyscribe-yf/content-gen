#!/usr/bin/env python3
"""KV 1.5bit 文章脚本画图：数字/结构由脚本承载，AI 图不碰数字。
调色：主蓝 #0F4C81（grace 主题）、橙 #E8A33D、警告红 #C0392B。
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
OUT = "content/2026-09-01-kv-1p5bit"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{OUT}/{name}", dpi=150)
    print("saved", name)


# ---------- 04: 位宽账本 ----------
def chart_bitwidth():
    labels = ["FP16（原始）", "量化 1.25bit\n（75% 层 1bit）"]
    pct = [100.0, 100.0 / (16 / 1.25)]
    fig, ax = plt.subplots(figsize=(7.6, 5.2), dpi=150)
    bars = ax.barh(labels, pct, color=[BLUE, ORANGE], height=0.5)
    for b, v in zip(bars, pct):
        ax.text(v + 1.5, b.get_y() + b.get_height() / 2,
                f"{v:.1f}%" if v == 100 else f"{v:.1f}%（省 92.2%）",
                va="center", fontsize=13)
    ax.annotate("同样的 KV 缓存\n体积只剩 1/12.8",
                xy=(7.8, 1), xytext=(22, 0.72),
                arrowprops=dict(arrowstyle="->", color=GRAY), fontsize=12)
    ax.set_xlim(0, 118)
    ax.set_xlabel("KV 缓存占显存比例（相对 FP16 = 100%）", fontsize=12)
    ax.set_title("16bit → 平均 1.25bit：12.8 倍压缩，省 92.2% KV 显存", fontsize=13)
    ax.grid(True, axis="x", alpha=0.25)
    save(fig, "04-bit-width-ledger.png")


# ---------- 05: 任务性能对照 ----------
def chart_tasks():
    tasks = ["TruthfulQA", "CoQA", "TriviaQA", "TREC", "RepoBench-P"]
    fp16 = [30.76, 63.88, 87.72, 66.0, 59.82]
    q15 = [38.77, 58.12, 85.27, 65.50, 43.35]
    x = np.arange(len(tasks))
    fig, ax = plt.subplots(figsize=(9.2, 5.4), dpi=150)
    w = 0.36
    b1 = ax.bar(x - w / 2, fp16, w, label="FP16 浮点", color=BLUE)
    b2 = ax.bar(x + w / 2, q15, w, label="AsymKV 量化（约 1.25~1.5bit）", color=ORANGE)
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.2,
                    f"{b.get_height():.1f}", ha="center", fontsize=10.5)
    ax.annotate("反而更高\n（去噪效应）", xy=(0.18, 38.77), xytext=(-0.1, 50),
                arrowprops=dict(arrowstyle="->", color=GRAY), fontsize=11)
    ax.annotate("代码任务掉 16 分", xy=(4 + w / 2, 43.35), xytext=(3.1, 25),
                arrowprops=dict(arrowstyle="->", color=RED), fontsize=11, color=RED)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, fontsize=12)
    ax.set_ylabel("得分（越高越好）", fontsize=12)
    ax.set_title("AsymKV 量化后：多数任务保住 9 成，个别任务打折", fontsize=13)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=11, loc="upper right")
    ax.grid(True, axis="y", alpha=0.25)
    save(fig, "05-task-compare.png")


# ---------- 06: DeepSeek V4 架构压缩 ----------
def chart_v4():
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.6), dpi=150)
    # KV 缓存
    ax = axes[0]
    ax.bar(["标准注意力\n（V3.2 基线）", "DeepSeek V4\nCSA + HCA"], [100, 10],
           color=[GRAY, BLUE], width=0.5)
    ax.text(0, 100 + 2, "100%", ha="center", fontsize=13)
    ax.text(1, 10 + 2, "10%", ha="center", fontsize=13, color=BLUE)
    ax.set_ylim(0, 118)
    ax.set_title("1M 上下文 KV 缓存占用", fontsize=13)
    ax.set_ylabel("相对基线", fontsize=11)
    ax.grid(True, axis="y", alpha=0.25)
    # 计算量
    ax = axes[1]
    ax.bar(["标准注意力", "DeepSeek V4\nCSA + HCA"], [100, 27],
           color=[GRAY, BLUE], width=0.5)
    ax.text(0, 100 + 2, "100%", ha="center", fontsize=13)
    ax.text(1, 27 + 2, "27%", ha="center", fontsize=13, color=BLUE)
    ax.set_ylim(0, 118)
    ax.set_title("单 token 计算量（FLOPs）", fontsize=13)
    ax.grid(True, axis="y", alpha=0.25)
    fig.suptitle("架构级压缩：HCA 以 128:1 压缩率做稠密注意力", fontsize=13)
    save(fig, "06-csa-hca.png")


if __name__ == "__main__":
    chart_bitwidth()
    chart_tasks()
    chart_v4()
