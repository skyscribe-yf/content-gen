"""生成本篇 4 张正文图（脚本画图，数字与正文一致）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

BLUE = "#0F4C81"
GOLD = "#C9A227"
RED = "#B23A48"
GRAY = "#6B7280"
LIGHT = "#F3F4F6"
OUT = Path(__file__).parent


def canvas(w=12, h=6.8):
    fig, ax = plt.subplots(figsize=(w, h), dpi=110)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


# 图1：两臂对照
fig, ax = canvas()
ax.text(2, 92, "同一段代码，同一模型，只换了一句要求", fontsize=20, color=BLUE, weight="bold")
bars = [
    ("「覆盖率尽量高」", 73, 6, 0, "73 条用例，6 条连正确实现都过不了"),
    ("「目标是抓住改错的一行」", 11, 0, 14, "11 条用例，杀死 15 个变异体里的 14 个"),
]
y = [64, 30]
for (label, total, bad, killed, note), yy in zip(bars, y):
    ax.text(2, yy + 16, label, fontsize=15, color="#111827", weight="bold")
    ax.add_patch(FancyBboxPatch((2, yy), 8, 10, boxstyle="round,pad=0.3",
                                facecolor=LIGHT, edgecolor="none"))
    scale = 70 / 75
    ax.add_patch(FancyBboxPatch((2, yy), total * scale, 10, boxstyle="round,pad=0.3",
                                facecolor=BLUE, edgecolor="none"))
    if bad:
        ax.add_patch(FancyBboxPatch((2 + (total - bad) * scale, yy), bad * scale, 10,
                                    boxstyle="round,pad=0.3", facecolor=RED, edgecolor="none"))
    ax.text(2 + total * scale + 2, yy + 2, f"{total} 条", fontsize=13, color=GRAY)
    ax.text(2, yy - 13, note, fontsize=12, color=GRAY)
ax.text(2, 12, "红色 = 对着正确实现也失败的用例　蓝色 = 通过　右臂另计变异体杀伤", fontsize=11, color=GRAY)
save(fig, "01-arms.png")

# 图2：那条断言
fig, ax = canvas()
ax.text(2, 92, "它写下的那条用例", fontsize=20, color=BLUE, weight="bold")
ax.add_patch(FancyBboxPatch((2, 38), 96, 44, boxstyle="round,pad=0.6",
                            facecolor="#0B1220", edgecolor="none"))
code = [
    ("def test_leading_minus_ignored():", "#93C5FD"),
    ('    assert parse_duration("-1h") == 3600', "#E5E7EB"),
    ('    assert parse_duration("-1d2h") == 86400 + 7200', "#E5E7EB"),
    ('    assert parse_duration(" -1h") == 3600', "#E5E7EB"),
]
for i, (line, color) in enumerate(code):
    ax.text(5, 73 - i * 9, line, fontsize=14, color=color, family="monospace")
ax.add_patch(FancyBboxPatch((2, 8), 96, 15, boxstyle="round,pad=0.4",
                            facecolor="#FDF2F2", edgecolor=RED, linewidth=1.2))
ax.text(5, 16, "而这个函数的问题正是：负号被悄悄吃掉，本该报错。", fontsize=14, color=RED)
ax.text(5, 11, "它没发现，反而给这个 bug 起了名字，写成了标准答案。", fontsize=14, color=RED)
save(fig, "02-assertion.png")

# 图3：三种失败
fig, ax = canvas()
ax.text(2, 92, "白盒补测试的三种失败", fontsize=20, color=BLUE, weight="bold")
cards = [
    ("漏测", "重复单位不报错\n「1h1h」返回 7200\n一条用例都没写", RED),
    ("测错", "断言「1 h 30 m」合法\n实现要求数字与单位相邻\n那条用例从出生就挂", GOLD),
    ("把 bug 写成预期", "负号被吞\n写成一条 test_leading_\nminus_ignored 用例\n测试全绿", BLUE),
]
for i, (title, body, color) in enumerate(cards):
    x = 2 + i * 33
    ax.add_patch(FancyBboxPatch((x, 34), 30, 42, boxstyle="round,pad=0.6",
                                facecolor="white", edgecolor=color, linewidth=2))
    ax.text(x + 2, 68, title, fontsize=16, color=color, weight="bold")
    ax.text(x + 2, 56, body, fontsize=11, color="#111827", va="top", linespacing=1.7)
save(fig, "03-three-failures.png")

# 图4：SpecBench
fig, ax = canvas()
ax.text(2, 92, "可见套件刷满，隐藏套件掉档", fontsize=20, color=BLUE, weight="bold")
ax.text(2, 84, "Claude 的 C 编译器：18.6 万行，通过 GCC 九百多个测试", fontsize=13, color=GRAY)
vals = [("可见验证套件", 97.8, BLUE), ("隐藏组合套件", 83.3, RED)]
for i, (label, v, color) in enumerate(vals):
    yy = 60 - i * 22
    ax.text(2, yy + 12, label, fontsize=14, color="#111827")
    ax.add_patch(FancyBboxPatch((2, yy), v * 0.88, 9, boxstyle="round,pad=0.3",
                                facecolor=color, edgecolor="none"))
    ax.text(2 + v * 0.88 + 2, yy + 1.5, f"{v}%", fontsize=14, color=color, weight="bold")
ax.text(2, 12, "差 14.5 个百分点，几乎全在「拒绝非法的 C 程序」这一维", fontsize=14, color=RED, weight="bold")
ax.text(2, 4, "代码量每翻十倍，可见与隐藏的差距再涨约 28 个百分点", fontsize=12, color=GRAY)
save(fig, "04-specbench.png")
