#!/usr/bin/env python3
"""本篇 5 张脚本结构图（数字只走这条轨，AI 概念图禁止承载数字）。

01 数量漏斗 / 03 VJP 表就是矩阵导数表 / 04 eigh 重根与近重根 / 05 STE 前后向 / 06 三路裁判
数字来源：
  · 404 / 110 / 199 / 76 / 6 / 1.18e-08  → ~/scripts/matrix-calculus-ad/rule_count.py（2026-10-12 复跑）
  · 粒度表（1/2/8/9/13/23）              → primitive_anatomy.py
  · 特征向量梯度随间距变化                → 本篇新增扫描（2026-10-12）
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = Path(__file__).parent
plt.rcParams["axes.unicode_minus"] = False

CAND = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]
for c in CAND:
    if Path(c).exists():
        font_manager.fontManager.addfont(c)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=c).get_name()
        break

INK = "#1b1b1f"
MUTED = "#6b6b76"
ACCENT = "#0F4C81"
WARM = "#B3541E"
LINE = "#d8d8de"


def save(fig, name):
    out = HERE / name
    fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.3, facecolor="white")
    plt.close(fig)
    print("wrote", out)


# ── 01 数量漏斗 ────────────────────────────────────────────────────────────
def chart_01():
    labels = [
        "jax.numpy 对外暴露的\n可调用函数",
        "lax 里的原语\n（IR 不再拆开的那层）",
        "注册的导数规则\n前向 199 / 转置 76",
        "一个普通层\n实际用到的原语",
    ]
    vals = [404, 110, 199, 6]
    notes = ["", "", "", "线性 + tanh + 手拼 LayerNorm"]
    colors = ["#dbe5f1", "#b9cde6", "#8fb0d6", ACCENT]

    fig, ax = plt.subplots(figsize=(10.6, 4.6))
    y = np.arange(len(vals))[::-1]
    for yy, v, lab, n, col in zip(y, vals, labels, notes, colors):
        ax.barh(yy, v, height=0.52, color=col)
        ax.text(v + 6, yy, str(v), va="center", fontsize=15, color=INK, weight="bold")
        ax.text(-8, yy, lab, va="center", ha="right", fontsize=11.5, color=INK,
                linespacing=1.45)
        if n:
            ax.text(v + 44, yy - 0.34, n, va="center", fontsize=10, color=WARM)
    ax.set_yticks([])
    ax.set_xlim(-135, 470)
    ax.set_xlabel("数量", fontsize=11.5, color=MUTED, labelpad=8)
    ax.tick_params(colors=MUTED, labelsize=10.5)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.grid(axis="x", color=LINE, linewidth=0.7, alpha=0.75)
    ax.set_axisbelow(True)
    ax.set_title("从 404 个入口，到 6 个真正干活的原语", fontsize=15,
                 color=INK, weight="bold", pad=14)
    save(fig, "01-数量漏斗.png")


# ── 03 VJP 表就是矩阵导数表 ────────────────────────────────────────────────
def chart_03():
    rows = [
        ("逐元素 / 线性", "加减、逐元素乘", "分叉变求和", "线性"),
        ("矩阵乘法  $Z=XY$", "$\\bar X=\\bar Z Y^\\top$", "$\\bar Y=X^\\top \\bar Z$",
         "$dZ=(dX)Y+X(dY)$"),
        ("矩阵求逆  $Z=X^{-1}$", "$\\bar X=-X^{-\\top}\\bar Z X^{-\\top}$", "",
         "$d(X^{-1})=-X^{-1}dX\\,X^{-1}$"),
        ("对数行列式  $Z=\\log\\det X$", "$\\bar X=\\bar Z\\cdot X^{-\\top}$", "",
         "$d\\log\\det X=\\operatorname{tr}(X^{-1}dX)$"),
        ("Softmax", "$\\bar x=p\\odot(\\bar z-p^\\top\\bar z)$", "",
         "$J=\\operatorname{diag}(p)-pp^\\top$"),
    ]
    fig, ax = plt.subplots(figsize=(12.2, 4.4))
    ax.set_axis_off()
    cells = []
    for r in rows:
        if r[0].startswith("逐元素"):
            cells.append([r[0], r[1], "分叉变求和", r[3]])
        else:
            cells.append([r[0], r[1], r[2] or "—", r[3]])
    tbl = ax.table(
        cellText=cells,
        colLabels=["前向", "反向（回传）", "另一个输入", "对应的矩阵微分"],
        cellLoc="left",
        colWidths=[0.24, 0.30, 0.16, 0.30],
        loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11.5)
    tbl.scale(1, 2.1)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor(LINE)
        cell.set_linewidth(0.9)
        if r == 0:
            cell.set_facecolor("#f2f5f9")
            cell.set_text_props(color=ACCENT, weight="bold")
        elif c == 3:
            cell.set_facecolor("#fbfcfe")
            cell.set_text_props(color=INK)
        else:
            cell.set_text_props(color=INK)
        if r == 1 and c == 2:
            cell.set_text_props(color=WARM, weight="bold")
        cell.PAD = 0.05
    ax.set_title("代码里登记的反向规则，就是手推时那张矩阵导数表",
                 fontsize=14.5, color=INK, weight="bold", pad=14)
    save(fig, "03-VJP表就是矩阵导数表.png")


# ── 04 eigh：重根与近重根 ──────────────────────────────────────────────────
def chart_04():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.3),
                                   gridspec_kw={"width_ratios": [1, 1.25]})

    # 左：重根处谁有定义
    ax1.set_axis_off()
    ax1.text(0.5, 0.80, "重根处（两个特征值相等）", ha="center", fontsize=13,
             color=INK, weight="bold", transform=ax1.transAxes)
    for i, (name, val, ok) in enumerate([
        ("grad(特征值)", "diag(1,0,0)", True),
        ("grad(特征向量)", "全是 NaN", False),
    ]):
        y = 0.52 - i * 0.24
        ax1.add_patch(plt.Rectangle((0.06, y), 0.88, 0.17,
                                    transform=ax1.transAxes,
                                    facecolor="#f4f5f7" if ok else "#f7e9df",
                                    edgecolor=LINE if ok else WARM, linewidth=1.3))
        ax1.text(0.13, y + 0.085, name, transform=ax1.transAxes, va="center",
                 fontsize=11.5, color=INK)
        ax1.text(0.93, y + 0.085, val, transform=ax1.transAxes, va="center",
                 ha="right", fontsize=12, weight="bold",
                 color=ACCENT if ok else WARM)
    ax1.text(0.5, 0.13, "同一个算子里，一半良定义、一半不是", transform=ax1.transAxes,
             ha="center", fontsize=11, color=MUTED)

    # 右：梯度随间距变化
    Delta = np.array([1.000, 0.102, 0.022, 0.020])
    gv = np.array([0.500, 4.784, 17.013, 18.069])
    ge = np.array([1.0, 1.0, 1.0, 1.0])
    ax2.plot(Delta, gv, "o-", color=WARM, lw=2.2, ms=8,
             label="特征向量梯度（最大值）")
    ax2.plot(Delta, ge, "s--", color=ACCENT, lw=2.0, ms=7,
             label="特征值梯度（范数）")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("两个特征值的间距 $\\Delta$（对数轴）", fontsize=11.5, color=MUTED)
    ax2.set_ylabel("梯度的量级（对数轴）", fontsize=11.5, color=MUTED)
    ax2.tick_params(colors=MUTED, labelsize=10)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax2.spines[s].set_color(LINE)
    ax2.grid(color=LINE, linewidth=0.7, alpha=0.7)
    ax2.set_axisbelow(True)
    ax2.legend(fontsize=10.5, frameon=False, loc="center left")
    ax2.annotate("间距缩十倍，\n梯度被顶住不再涨",
                 xy=(0.020, 18.069), xytext=(0.12, 8.5),
                 fontsize=10.5, color=WARM,
                 arrowprops=dict(arrowstyle="->", color=WARM, lw=1.4))
    ax2.set_title("间距越小梯度越大，但会被排斥机制顶住", fontsize=13.5,
                  color=INK, weight="bold", pad=10)

    fig.suptitle("为什么偏偏是特征分解这类算子", fontsize=15, color=INK,
                 weight="bold", y=1.02)
    save(fig, "04-eigh重根与近重根.png")


# ── 05 STE 前后向 ─────────────────────────────────────────────────────────
def chart_05():
    x = np.linspace(-2.2, 2.2, 600)
    step = 0.5
    quant = np.round(x / step) * step          # 前向：取整
    fig, ax = plt.subplots(figsize=(8.8, 4.3))
    ax.plot(x, x, "--", color=MUTED, lw=1.6, label="反向：当作恒等（直通）")
    ax.plot(x, quant, "-", color=ACCENT, lw=2.6, label="前向：量化取整")
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.4, 2.4)
    ax.set_xlabel("权重取值", fontsize=11.5, color=MUTED)
    ax.set_ylabel("模型实际用到的值", fontsize=11.5, color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=10.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LINE)
    ax.grid(color=LINE, linewidth=0.7, alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=11, frameon=False, loc="upper left")
    ax.set_title("前向让模型吃到低精度误差，反向不让梯度链断掉",
                 fontsize=14, color=INK, weight="bold", pad=12)
    save(fig, "05-STE前后向.png")


# ── 06 三路裁判 ───────────────────────────────────────────────────────────
def chart_06():
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_axis_off()

    def box(x, y, w, h, text, fc, ec, tc=INK, fs=12):
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                                   linewidth=1.4))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=tc, linespacing=1.5)

    box(3.30, 2.65, 2.5, 0.85, "手写反向模式", "#dbe5f1", ACCENT, fs=12.5)
    box(0.10, 0.95, 2.5, 0.85, "中心差分\n（不认识解析式）", "#f7e9df", WARM, fs=12)
    box(6.40, 0.95, 2.6, 0.85, "教科书解析式\n（同一个公式）", "#f4f5f7", LINE, fs=12)

    ax.annotate("", xy=(1.55, 1.85), xytext=(4.0, 2.60),
                arrowprops=dict(arrowstyle="<|-|>", color=WARM, lw=2.2))
    ax.annotate("", xy=(7.40, 1.85), xytext=(5.1, 2.60),
                arrowprops=dict(arrowstyle="<|-|>", color=MUTED, lw=2.2))

    ax.text(2.0, 2.30, "对上了\n= 公式对", ha="center", va="center", fontsize=11.5,
            color=WARM, weight="bold", linespacing=1.5)
    ax.text(6.5, 2.30, "对上了\n只说明用了同一个公式", ha="center", va="center",
            fontsize=11, color=MUTED, linespacing=1.5)

    ax.text(4.55, 1.35, "谁是裁判？", ha="center", fontsize=12.5, color=INK,
            weight="bold")
    ax.text(4.55, 0.55, "差分不认识解析式，它只是自己去试——\n所以只有它能证明公式本身是对的",
            ha="center", va="center", fontsize=11.5, color=INK, linespacing=1.6)

    ax.set_xlim(0, 9.4)
    ax.set_ylim(0, 3.9)
    ax.set_title("三路对照：谁在证明谁", fontsize=15, color=INK, weight="bold", pad=8)
    save(fig, "06-三路裁判.png")


if __name__ == "__main__":
    chart_01()
    chart_03()
    chart_04()
    chart_05()
    chart_06()
