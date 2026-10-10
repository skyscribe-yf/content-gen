#!/usr/bin/env python3
"""本篇 5 张脚本结构图（数字只走这条轨，AI 概念图禁止承载数字）。

05 两难对照 / 06 动作到下一帧回路 / 07 范式对照 / 08 五层有损压缩链 / 09 缺失实验表
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).parent
plt.rcParams["axes.unicode_minus"] = False

CAND = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]
for c in CAND:
    if Path(c).exists():
        font_manager.fontManager.addfont(c)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=c).get_name()
        break

INK = "#1b1b1f"
MUTED = "#6b6b76"
ACCENT = "#0F4C81"   # 账号主色（grace / scienceBlue）
WARM = "#B3541E"
LINE = "#d8d8de"


def frame(figsize):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_axis_off()
    return fig, ax


def save(fig, name):
    out = HERE / name
    fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.28, facecolor="white")
    plt.close(fig)
    print("wrote", out)


def title(ax, text, sub=None):
    ax.text(0.0, 1.02, text, fontsize=17, color=INK, weight="bold", va="bottom")
    if sub:
        ax.text(0.0, 0.955, sub, fontsize=10.5, color=MUTED, va="bottom")


def card(ax, x, y, w, h, head, lines, edge, head_color=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                 linewidth=1.4, edgecolor=edge, facecolor="#fbfbfd"))
    ax.text(x + w / 2, y + h - 0.055, head, ha="center", va="top",
            fontsize=13, weight="bold", color=head_color or edge)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.135 - i * 0.072, ln, ha="center", va="top",
                fontsize=10.5, color=INK)


# ---------------------------------------------------------------- 05 两难对照
def chart_05():
    fig, ax = frame((9.6, 5.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    title(ax, "忠实与拟真，是一对矛盾",
          "两条老路各占一半：状态可靠的不好看，好看的不可靠")

    card(ax, 0.035, 0.50, 0.42, 0.36, "模拟器 / 游戏引擎",
         ["忠实 √  状态与规则由程序保证",
          "拟真 ×  程序化场景视觉贫乏",
          "代价：每个环境一套美术资产"],
         ACCENT)
    card(ax, 0.545, 0.50, 0.42, 0.36, "视频世界模型",
         ["拟真 √  画面贴近真实分布",
          "忠实 ×  长程交互物理会漂移",
          "代价：状态不一致，学不到因果"],
         WARM)

    ax.add_patch(FancyBboxPatch((0.035, 0.13), 0.93, 0.24,
                                 boxstyle="round,pad=0.012,rounding_size=0.02",
                                 linewidth=1.6, edgecolor=ACCENT, facecolor="#eef3f8"))
    ax.text(0.5, 0.30, "于是环境本身成了瓶颈", ha="center", va="center",
            fontsize=14, weight="bold", color=ACCENT)
    ax.text(0.5, 0.215, "合成数据快被采干之后，可扩展的环境从哪来？",
            ha="center", va="center", fontsize=11, color=INK)
    ax.text(0.5, 0.155, "agent 能学到什么，被它练习的环境所限制",
            ha="center", va="center", fontsize=10.5, color=MUTED, style="italic")
    save(fig, "05-两难对照.png")


# ------------------------------------------------------------ 06 回路
def chart_06():
    fig, ax = frame((9.8, 4.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    title(ax, "一个世界，两种真相：代码管事实，渲染器管皮")

    boxes = [
        (0.02, "Agent", ["发出动作"]),
        (0.26, "代码世界", ["持久世界状态", "程序定义交互规则"]),
        (0.50, "几何条件", ["深度图 / 表面法线", "从 agent 视角导出"]),
        (0.74, "神经渲染器", ["+ 参考图 + 文本", "+ 视觉历史"]),
    ]
    for x, head, lines in boxes:
        ax.add_patch(FancyBboxPatch((x, 0.30), 0.19, 0.34,
                                     boxstyle="round,pad=0.012,rounding_size=0.02",
                                     linewidth=1.4,
                                     edgecolor=ACCENT if head != "神经渲染器" else WARM,
                                     facecolor="#fbfbfd"))
        ax.text(x + 0.095, 0.565, head, ha="center", va="center",
                fontsize=12.5, weight="bold",
                color=ACCENT if head != "神经渲染器" else WARM)
        for i, ln in enumerate(lines):
            ax.text(x + 0.095, 0.485 - i * 0.075, ln, ha="center", va="center",
                    fontsize=9.8, color=INK)

    for x0, x1 in [(0.21, 0.26), (0.45, 0.50), (0.69, 0.74)]:
        ax.add_patch(FancyArrowPatch((x0, 0.47), (x1 - 0.004, 0.47),
                                      arrowstyle="-|>", mutation_scale=14,
                                      linewidth=1.4, color=MUTED))
    ax.text(0.475, 0.53, "导出的是几何，不是像素", ha="center",
            fontsize=9.8, color=WARM)
    ax.text(0.725, 0.245, "只负责“皮”", ha="center", fontsize=9.8, color=WARM)
    ax.text(0.355, 0.245, "只负责“事实”", ha="center", fontsize=9.8, color=ACCENT)

    ax.add_patch(FancyArrowPatch((0.935, 0.36), (0.935, 0.13),
                                  arrowstyle="-", linewidth=1.4, color=MUTED))
    ax.add_patch(FancyArrowPatch((0.935, 0.13), (0.115, 0.13),
                                  arrowstyle="-", linewidth=1.4, color=MUTED))
    ax.add_patch(FancyArrowPatch((0.115, 0.13), (0.115, 0.29),
                                  arrowstyle="-|>", mutation_scale=14,
                                  linewidth=1.4, color=MUTED))
    ax.text(0.53, 0.165, "下一帧观察回到 agent", ha="center", fontsize=10.5, color=INK)
    save(fig, "06-动作到下一帧.png")


# ------------------------------------------------------------ 07 范式对照
def chart_07():
    fig, ax = frame((9.8, 5.0))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    title(ax, "换掉的不是渲染器，是整个 agent 范式",
          "同一个躲猫猫场地，OpenAI 2019 与 AgentGarten 两套配置")

    col_x = [0.02, 0.30, 0.66]
    col_w = [0.26, 0.34, 0.32]
    heads = ["", "OpenAI 2019 经典", "AgentGarten"]
    hcolors = [INK, MUTED, ACCENT]
    for x, w, h, c in zip(col_x, col_w, heads, hcolors):
        ax.text(x + w / 2, 0.90, h, ha="center", va="center",
                fontsize=12.5, weight="bold", color=c)

    rows = [
        ("观察", ["对象状态向量", "位置 / 速度 / 尺寸 / 雷达读数"], ["神经渲染的第一人称画面", "拿不到坐标与隐藏状态"]),
        ("动作", ["每步一个连续控制信号"], ["短 Python 程序", "step(turn=-1, steps=2)"]),
        ("记忆", ["policy 网络权重"], ["playbook 技能文件", "一个文件一条经验"]),
        ("学习信号", ["self-play RL + 奖励"], ["每轮复盘，教训写进 playbook"]),
    ]
    y = 0.78
    for r in rows:
        ax.add_patch(FancyBboxPatch((col_x[0], y - 0.145), col_w[0], 0.155,
                                     boxstyle="round,pad=0.008,rounding_size=0.02",
                                     linewidth=1.0, edgecolor=LINE, facecolor="#f4f4f7"))
        ax.text(col_x[0] + col_w[0] / 2, y - 0.065, r[0], ha="center", va="center",
                fontsize=11.5, weight="bold", color=INK)
        for ci, txts in ((1, r[1]), (2, r[2])):
            ax.add_patch(FancyBboxPatch((col_x[ci], y - 0.145), col_w[ci], 0.155,
                                         boxstyle="round,pad=0.008,rounding_size=0.02",
                                         linewidth=1.0,
                                         edgecolor=LINE,
                                         facecolor="#fbfbfd" if ci == 1 else "#eef3f8"))
            for i, t in enumerate(txts):
                ax.text(col_x[ci] + col_w[ci] / 2, y - 0.045 - i * 0.058, t,
                        ha="center", va="center", fontsize=9.8,
                        color=INK if i == 0 else MUTED)
        y -= 0.185

    ax.text(0.02, 0.045,
            "结果：建掩体 2,500 万局 → 第 4 轮；用斜坡进入掩体 1 亿局 → 第 10 轮",
            fontsize=11, color=WARM, weight="bold")
    save(fig, "07-范式对照.png")


# ------------------------------------------------------- 08 五层有损压缩链
def chart_08():
    fig, ax = frame((9.0, 6.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    title(ax, "从真实世界到训练数据，五层有损压缩",
          "每一层都丢一次，而且过滤器之间互相强化")

    layers = [
        ("① 感知层", "人类观测为适应度优化，不是为真理优化"),
        ("② 数据层", "训练数据是这些观测的不精确采样"),
        ("③ 衍生层", "LLM 学出的分布生成代码世界，虚妄冻结成公理"),
        ("④ 优化层", "典型性偏置 + 隐式正则 + RLHF 对齐税"),
        ("⑤ 递归层", "生成产物回到训练集，分布尾部最先死"),
    ]
    top, hgt, gap = 0.82, 0.125, 0.022
    widths = [0.92, 0.84, 0.76, 0.68, 0.60]
    for i, (ln, txt) in enumerate(layers):
        w = widths[i]
        x = (1 - w) / 2
        y = top - i * (hgt + gap)
        shade = 0.10 + i * 0.13
        ax.add_patch(FancyBboxPatch((x, y - hgt), w, hgt,
                                     boxstyle="round,pad=0.008,rounding_size=0.02",
                                     linewidth=1.3,
                                     edgecolor=ACCENT,
                                     facecolor=(0.93 - shade * 0.55,
                                                0.95 - shade * 0.45,
                                                0.98 - shade * 0.30)))
        ax.text(x + 0.028, y - hgt * 0.34, ln, fontsize=12.5, weight="bold",
                color=ACCENT, va="center")
        ax.text(x + 0.028, y - hgt * 0.72, txt, fontsize=10.2, color=INK, va="center")

    ax.text(0.5, 0.035, "最深的损失：那些从未成为记录候选物的 mundane 具身经验",
            ha="center", fontsize=11.5, weight="bold", color=WARM)
    ax.text(0.5, -0.012, "——而那恰恰是物理直觉和可供性的基座",
            ha="center", fontsize=10.2, color=MUTED)
    save(fig, "08-五层压缩链.png")


# ------------------------------------------------------------ 09 缺失实验表
def chart_09():
    fig, ax = frame((9.8, 4.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    title(ax, "如果这篇论文要补实验，我会先补这四项",
          "前三项是诊断，第四项是干预")

    rows = [
        ("训练后迁移到真实世界任务", "公理特异性能力塌、程序性技能幸存", False),
        ("渲染器幻觉率 vs agent 行为错误率", "感知层污染训练信号的剂量曲线", False),
        ("世界库数量饱和曲线", "多样性代偿真理性的有效期", False),
        ("接入在线现实反馈通道（哪怕极窄）", "唯一能打破支撑集锁死的干预", True),
    ]
    y = 0.76
    for i, (a, b, hl) in enumerate(rows, 1):
        bh = 0.155
        ax.add_patch(FancyBboxPatch((0.02, y - bh), 0.96, bh,
                                     boxstyle="round,pad=0.008,rounding_size=0.02",
                                     linewidth=1.6 if hl else 1.0,
                                     edgecolor=WARM if hl else LINE,
                                     facecolor="#fbf1e9" if hl else "#fbfbfd"))
        ax.text(0.055, y - bh / 2, f"{i}", fontsize=15, weight="bold",
                color=WARM if hl else MUTED, va="center")
        ax.text(0.10, y - bh * 0.36, a, fontsize=11.5, weight="bold",
                color=WARM if hl else INK, va="center")
        ax.text(0.10, y - bh * 0.74, b, fontsize=10, color=MUTED, va="center")
        y -= bh + 0.035

    ax.text(0.02, 0.02, "标题里那个“还没人做的实验”，就是第 4 行。",
            fontsize=11, weight="bold", color=WARM)
    save(fig, "09-缺失实验表.png")


if __name__ == "__main__":
    chart_05()
    chart_06()
    chart_07()
    chart_08()
    chart_09()
