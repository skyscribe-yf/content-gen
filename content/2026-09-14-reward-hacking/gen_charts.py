#!/usr/bin/env python3
"""奖励函数 hack 篇数字图：
01 两个效用函数的错位（δ 的形状）/ 02 梯度裂成两项后的三条曲线。
风格对齐 2026-09-13-grpo-math/gen_charts.py（PIL 直绘，1254 宽，同一套色板）。
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG = "#F8FAFC"
INK = "#17324D"
BLUE = "#0F4C81"
CYAN = "#55C9EA"
YELLOW = "#F6BD60"
ORANGE = "#E76F51"
MUTED = "#6B7C8F"
PALE_BLUE = "#DCEAF4"
PALE_YELLOW = "#FFF1C7"
PALE_ORANGE = "#FCE1D9"
GRAY = "#9AA7B4"
RED = "#C0453B"
AMBER = "#D98A1F"
W = 1254
H = 836


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


F_TITLE = font(44, True)
F_SUB = font(24)
F_BODY = font(24)
F_SMALL = font(19)
F_TINY = font(17)
F_BIG = font(30, True)


def canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((64, 52), title, font=F_TITLE, fill=INK)
    d.text((64, 122), subtitle, font=F_BODY, fill=MUTED)
    d.line([(64, 186), (W - 64, 186)], fill=PALE_BLUE, width=3)
    return img, d


def gauss(x: float, mu: float, sigma: float) -> float:
    return math.exp(-((x - mu) ** 2) / (2 * sigma**2))


# ---------------- 图 01：两个效用函数的错位 ----------------
def chart_two_functions() -> None:
    img, d = canvas(
        "评估器看的是「有没有按压」，你要的是「瓶子有没有进桶」",
        "两条曲线的差 δ = Rφ − U，就是可以被钻空子的那部分空间",
    )
    x0, x1, y0, y1 = 130, 1150, 300, 690

    # 网格与坐标轴
    for frac in (0.0, 0.5, 1.0):
        y = y1 - (y1 - y0) * frac
        d.line([(x0, y), (x1, y)], fill=PALE_BLUE, width=2)
        d.line([(x0 - 8, y), (x0, y)], fill=INK, width=2)
        d.text((x0 - 60, y - 12), f"{frac:g}", font=F_SMALL, fill=MUTED)
    d.line([(x0, y0), (x0, y1), (x1, y1)], fill=INK, width=3)

    def px(t: float) -> float:
        return x0 + (x1 - x0) * t

    def py(v: float) -> float:
        return y1 - (y1 - y0) * v

    steps = 400
    U = [(i / steps, gauss(i / steps, 0.82, 0.055)) for i in range(steps + 1)]
    R = [(i / steps, gauss(i / steps, 0.55, 0.160)) for i in range(steps + 1)]

    # δ 填充区（R > U 的部分）
    band = [(px(t), py(min(ru, uu)), py(max(ru, uu))) for (t, uu), (_, ru) in zip(U, R) if ru > uu]
    for x, ya, yb in band:
        d.line([(x, ya), (x, yb)], fill=PALE_YELLOW, width=2)

    for pts, color, width in ((R, AMBER, 5), (U, BLUE, 5)):
        d.line([(px(t), py(v)) for t, v in pts], fill=color, width=width)

    # 标签：代理奖励（峰值在按压处）—— 放在峰值右上方的空白区
    d.text((px(0.55) + 60, py(0.93)), "代理奖励 Rφ", font=F_BIG, fill=AMBER)
    d.text((px(0.55) + 60, py(0.93) + 38), "评估器看到的：按压", font=F_TINY, fill=MUTED)
    # 标签：真实效用 —— 放在尖峰右上方，避开曲线
    d.text((px(0.82) + 30, py(0.92)), "真实效用 U", font=F_BIG, fill=BLUE)
    d.text((px(0.82) + 30, py(0.92) + 38), "你要的：瓶子进桶", font=F_TINY, fill=MUTED)

    # δ 双向箭头
    ax = px(0.68)
    d.line([(ax, py(0.62)), (ax, py(0.10))], fill=RED, width=3)
    for yy, sgn in ((py(0.62), 1), (py(0.10), -1)):
        d.polygon([(ax, yy), (ax - 9, yy + 14 * sgn), (ax + 9, yy + 14 * sgn)], fill=RED)
    d.text((ax + 18, py(0.40)), "δ = Rφ − U", font=F_BIG, fill=RED)
    d.text((ax + 18, py(0.40) + 34), "被钻空子的空间", font=F_SMALL, fill=RED)

    d.text((x0, y1 + 22), "轨迹空间：从「什么都没做」到「真正把瓶子投进桶」",
           font=F_SMALL, fill=MUTED)
    img.save(ROOT / "01-two-functions.png")


# ---------------- 图 02：梯度裂成两项 ----------------
def chart_delta_gradient() -> None:
    img, d = canvas(
        "损失在降、代理分在涨、真实效用在掉",
        "梯度裂成两项后，优化器选了更省力的那一项 ∇θE[δ]，三件事可以同时发生",
    )
    x0, x1, y0, y1 = 130, 1150, 300, 690
    N = 40

    for frac in (0.0, 0.5, 1.0):
        y = y1 - (y1 - y0) * frac
        d.line([(x0, y), (x1, y)], fill=PALE_BLUE, width=2)
        d.line([(x0 - 8, y), (x0, y)], fill=INK, width=2)
        d.text((x0 - 60, y - 12), f"{frac:g}", font=F_SMALL, fill=MUTED)
    d.line([(x0, y0), (x0, y1), (x1, y1)], fill=INK, width=3)

    def px(i: float) -> float:
        return x0 + (x1 - x0) * i / N

    def py(v: float) -> float:
        return y1 - (y1 - y0) * v

    # 代理分：快速冲到天花板
    r = [(i, 1.0 * (1 - math.exp(-i / 6.0))) for i in range(N + 1)]
    # 不钻空子本该有的真实效用
    u = [(i, 0.30 * (1 - math.exp(-i / 26.0))) for i in range(N + 1)]
    # 实际真实效用：跟随后停滞并回落
    u_eff = [(i, v - 0.16 * (1 - math.exp(-(max(i - 14, 0) ** 2) / 400.0))) for i, v in u]

    # 差距填充
    band = [(px(i), py(a), py(b)) for (i, a), (_, b) in zip(u_eff, u)]
    for x, ya, yb in band:
        d.line([(x, ya), (x, yb)], fill=PALE_ORANGE, width=2)

    d.line([(px(i), py(v)) for i, v in r], fill=AMBER, width=5)
    d.line([(px(i), py(v)) for i, v in u_eff], fill=RED, width=5)
    for i in range(0, N, 2):  # 虚线：本该有的效用
        d.line([(px(i), py(u[i][1])), (px(i + 1), py(u[i + 1][1]))], fill=BLUE, width=4)

    # 图例
    lx, ly = x0 + 30, y0 + 16
    d.line([(lx, ly + 12), (lx + 46, ly + 12)], fill=AMBER, width=5)
    d.text((lx + 58, ly), "代理分 Rφ：涨得又快又满", font=F_SMALL, fill=INK)
    d.line([(lx, ly + 50), (lx + 46, ly + 50)], fill=RED, width=5)
    d.text((lx + 58, ly + 38), "真实效用 U：停住甚至倒退", font=F_SMALL, fill=INK)
    d.line([(lx, ly + 88), (lx + 46, ly + 88)], fill=BLUE, width=4)
    d.text((lx + 58, ly + 76), "不钻空子本该有的 U", font=F_SMALL, fill=INK)

    # 标注放在曲线上方的空白带（y≈0.62~0.75），并用引线指回曲线
    d.text((px(14), py(0.72)), "梯度沿这里走最快：∇θE[δ]", font=F_BODY, fill=AMBER)
    d.line([(px(14) + 20, py(0.72) + 30), (px(9), py(0.80))], fill=AMBER, width=2)

    d.text((px(20), py(0.33)), "这一段差距 = 被吃掉的效用", font=F_BODY, fill=RED)
    d.line([(px(20) + 20, py(0.33) + 30), (px(28), py(0.20))], fill=RED, width=2)

    d.text((x0, y1 + 22), "训练步数 →", font=F_SMALL, fill=MUTED)
    img.save(ROOT / "02-delta-gradient.png")


if __name__ == "__main__":
    chart_two_functions()
    chart_delta_gradient()
    print("done: 01-two-functions.png, 02-delta-gradient.png")
