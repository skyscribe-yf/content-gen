#!/usr/bin/env python3
"""本篇脚本画图：01 两轴分类 / 02 五条线地图 / 03 DGM 曲线 / 04 验证层级。
规矩：数字/结构用脚本画，AI 图禁载数字；图内数字与正文逐字一致。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["axes.unicode_minus"] = False
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
D = "content/2026-11-12-self-iteration-panorama"

INK = "#1a2332"
SUB = "#5b6b7f"
BLUE = "#0F4C81"
RED = "#c0392b"
GOLD = "#E8A317"
GREEN = "#1e7d5a"
GRAY = "#b8c4d0"
BG = "#ffffff"


def fp(size=13, bold=True):
    return matplotlib.font_manager.FontProperties(fname=FONT if bold else FONT_R, size=size)


def newfig(w=11, h=5.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def title(ax, text, y=0.94, size=20):
    ax.text(0.5, y, text, ha="center", fontproperties=fp(size), color=INK)


# ---------- 01 两轴分类：改进什么 × 闭环程度 ----------
def fig01():
    fig, ax = newfig(11, 6.0)
    title(ax, "综述的两条轴：改进什么 × 闭环程度")

    cols = ["改进行为\n（部署期，393）", "改进策略\n（训练期，340）",
            "改进裁判\n（自评估，318）", "改进研究\n（自主科研，139）"]
    rows = ["人在环内", "人在环上", "全闭环"]
    x0, y0, cw, ch = 0.13, 0.26, 0.205, 0.155
    for j, c in enumerate(cols):
        ax.text(x0 + cw * (j + 0.46), 0.865, c, ha="center", va="center",
                fontproperties=fp(12), color=INK, linespacing=1.6)
    for i, r in enumerate(rows):
        yy = y0 + ch * (2 - i)
        ax.text(x0 - 0.03, yy + ch / 2, r, ha="right", va="center",
                fontproperties=fp(12), color=SUB)
        for j in range(4):
            thin = (i == 2 and j == 2)
            ax.add_patch(plt.Rectangle((x0 + cw * j, yy), cw * 0.93, ch * 0.90,
                                       facecolor=RED if thin else "#eef3f8",
                                       alpha=0.82 if thin else 1.0,
                                       edgecolor="white", lw=2))

    # 标注放在网格下方，不压格子
    ax.annotate("最薄的一格：系统开始改写自己「什么算更好」",
                xy=(x0 + cw * 2.46, y0 + ch * 0.45), xytext=(x0 + cw * 2.46, 0.135),
                fontproperties=fp(12), color=RED, ha="center",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.8))
    ax.text(0.02, 0.045,
            "1,250 篇（2024–2026）　蓝色格 = 人在环内 / 环上，论文密集　红色格 = 全闭环 × 自评估，据综述描述最稀疏",
            fontproperties=fp(10, bold=False), color=SUB)
    fig.savefig(f"{D}/01-two-axes.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 02 五条线地图：人类还剩什么 ----------
def fig02():
    fig, ax = newfig(11, 6.4)
    title(ax, "五条线，按「人类还剩什么」排")

    lines = [
        ("① 自产推理数据", "题目 + 标准答案", "便宜", GREEN),
        ("② 自产奖励", "少量种子偏好", "贵", RED),
        ("③ 自产课程", "只有一个执行器", "便宜（仅可执行域）", GREEN),
        ("④ 自改权重", "初始权重 + 元目标", "最贵", RED),
        ("⑤ 自改脚手架", "初始配置", "便宜", GREEN),
    ]
    top, gap, bh = 0.80, 0.125, 0.095
    for i, (name, remain, price, col) in enumerate(lines):
        y = top - gap * i
        ax.add_patch(FancyBboxPatch((0.05, y), 0.30, bh, boxstyle="round,pad=0.008,rounding_size=0.02",
                                    facecolor=BLUE if i in (0, 4) else "#eef3f8", edgecolor="none"))
        ax.text(0.20, y + bh / 2, name, ha="center", va="center", fontproperties=fp(13),
                color="white" if i in (0, 4) else INK)
        ax.text(0.40, y + bh / 2, "人类还剩：" + remain, ha="left", va="center",
                fontproperties=fp(12, bold=False), color=SUB)
        ax.text(0.94, y + bh / 2, price, ha="right", va="center", fontproperties=fp(12), color=col)
        if i < 4:
            ax.add_patch(FancyArrowPatch((0.20, y - 0.005), (0.20, y - gap + bh + 0.008),
                                         arrowstyle="-|>", color=INK, lw=1.4,
                                         mutation_scale=14))

    ax.text(0.05, 0.04, "蓝底 = 已在生产里跑的两条（① ⑤）　红字 = 监督贵的那三条",
            fontproperties=fp(11, bold=False), color=SUB)
    fig.savefig(f"{D}/02-five-lines.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 03 DGM 四次实测：起点 / 两个消融 / 完整 ----------
def fig03():
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    labels = ["起点\n（未改进）", "去掉开放式探索\n（只爬山）", "去掉自我改进\n（固定 meta-agent）", "完整 DGM\n（80 次迭代）"]
    vals = [20.0, 23.0, 39.0, 50.0]
    colors = [SUB, GRAY, GOLD, BLUE]
    bars = ax.bar(range(4), vals, color=colors, width=0.56, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.1f}%",
                ha="center", va="bottom", fontproperties=fp(16), color=INK)

    ax.set_xticks(range(4))
    ax.set_xticklabels(labels, fontproperties=fp(11, bold=False), linespacing=1.6)
    ax.set_ylabel("SWE-bench Verified 解决率 %（选定 200 题）", fontproperties=fp(11), color=INK)
    ax.set_ylim(0, 58)
    ax.grid(axis="y", alpha=0.18, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=10, colors=SUB)
    ax.set_title("论文实测的四个数：自我改进与开放式探索，两个都不能少",
                 fontproperties=fp(15), color=INK, pad=14)
    fig.tight_layout()
    fig.savefig(f"{D}/03-dgm-ablation.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


# ---------- 04 验证层级四档 ----------
def fig04():
    fig, ax = newfig(11, 6.2)
    title(ax, "验证层级：越往上，实测到的自我改进越强", y=0.955)

    tiers = [
        ("形式验证器", "单测 / 执行器 / 定理证明", GREEN, 0.71),
        ("执行反馈", "跑一遍，看输出对不对", GREEN, 0.53),
        ("学出来的裁判", "奖励模型 / LLM-as-judge", GOLD, 0.35),
        ("内在自评", "同一套权重自己给自己打分", RED, 0.17),
    ]
    for i, (name, ex, col, y) in enumerate(tiers):
        w = 0.34 + 0.10 * (3 - i)
        ax.add_patch(FancyBboxPatch((0.12, y), w, 0.115,
                                    boxstyle="round,pad=0.008,rounding_size=0.02",
                                    facecolor=col, alpha=0.88, edgecolor="none"))
        ax.text(0.12 + w / 2, y + 0.0575, name, ha="center", va="center",
                fontproperties=fp(13), color="white")
        ax.text(0.12 + w + 0.025, y + 0.0575, ex, ha="left", va="center",
                fontproperties=fp(11, bold=False), color=SUB)

    ax.add_patch(FancyArrowPatch((0.055, 0.16), (0.055, 0.885), arrowstyle="-|>",
                                 color=INK, lw=1.8, mutation_scale=18))
    ax.text(0.030, 0.52, "实测改进强度", rotation=90, ha="center", va="center",
            fontproperties=fp(11), color=INK)
    ax.text(0.12, 0.05, "违反这个顺序的失败模式：自我确认循环 · 模型坍缩 · 多样性坍缩",
            fontproperties=fp(11, bold=False), color=SUB)
    fig.savefig(f"{D}/04-verification-hierarchy.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig01(); fig02(); fig03(); fig04()
    print("done: 01 / 02 / 03 / 04")