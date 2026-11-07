#!/usr/bin/env python3
"""《DeepSeek 只换了权重》配图（PIL 直绘，风格对齐 2026-10-29 篇）。

数字来源（正文改动数字须同步此文件）：
  02 输出长度：AIME 中位 1681→1124、最长链 3814→1880、effort=1 1974→790
     （sference 2026-10-17 第三方实测，10 题×3 次×两组）
  03 已改为 AI 概念图（03-probability.png），本脚本不再生成
  04 三轴排序：arXiv:2610.23946，仅取指数排序（environment > task > trajectory），不画具体数值
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG = "#F8FAFC"
INK = "#17324D"
BLUE = "#0F4C81"
ORANGE = "#E76F51"
GREY = "#5B7186"
GRID = "#D9E2EC"
LIGHT = "#E8EEF5"

FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def font(size: int, bold: bool = False):
    for p in ([FONT_BOLD, FONT_REG] if bold else [FONT_REG, FONT_BOLD]):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def header(d, title, sub=None):
    d.text((72, 52), title, font=font(42, True), fill=INK)
    if sub:
        d.text((72, 112), sub, font=font(26), fill=GREY)


def footer(d, w, h, text):
    d.line([(72, h - 78), (w - 72, h - 78)], fill=GRID, width=2)
    d.text((72, h - 64), text, font=font(22), fill=GREY)


def chart_time():
    W, H = 1600, 900
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    header(d, "同一批题，只换权重：输出长度全面变短",
           "中位输出 token 数；AIME 与 MATH-500 各 10 题 × 3 次，effort=1 为最低思考档")

    groups = [
        ("AIME 中位输出", 1681, 1124),
        ("最长的那条链", 3814, 1880),
        ("effort=1 时", 1974, 790),
    ]
    x0, x1 = 388, W - 190
    top, bottom = 220, H - 170
    vmax = 4200
    row_h = (bottom - top) / len(groups)

    for i, (name, old, new) in enumerate(groups):
        cy = top + row_h * (i + 0.5)
        d.text((72, cy - 104), name, font=font(28, True), fill=INK)
        for j, (val, color, tag) in enumerate(((old, GREY, "旧权重"), (new, BLUE, "新权重"))):
            y = cy - 36 + j * 46
            w = (val / vmax) * (x1 - x0)
            d.rounded_rectangle([x0, y, x0 + w, y + 34], radius=6, fill=color)
            d.text((x0 + w + 14, y + 3), f"{val:,}", font=font(24, True), fill=color)
            d.text((x0 - 18, y + 3), tag, font=font(20), fill=GREY, anchor="ra")
        pct = (new - old) / old * 100
        d.text((W - 90, cy - 36 + 46 + 3), f"{pct:+.0f}%", font=font(26, True), fill=ORANGE, anchor="ra")

    footer(d, W, H, "数据：sference 第三方实测（2026-10-17），同题同种子同采样，仅权重组不同")
    im.save(ROOT / "02-time-token.png")
    return im


def chart_passk():
    W, H = 1600, 900
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    header(d, "后训练没有造出新答案，只是把它挪到了第 1 次",
           "示意：基座里正确答案本来就在，只是要采样很多次才碰上")

    ox, oy = 180, H - 190
    ex, ey = W - 150, 210
    d.line([(ox, oy), (ex, oy)], fill=INK, width=3)
    d.line([(ox, oy), (ox, ey)], fill=INK, width=3)
    d.text((ex, oy + 18), "采样次数", font=font(24), fill=GREY, anchor="ra")
    d.text((ox - 18, ey - 26), "至少一次答对", font=font(24), fill=GREY, anchor="ra")

    import math
    KMAX = 300

    def ypos(p):
        return oy - p * (oy - ey - 30)

    def curve(tau, color, width):
        pts = []
        for i in range(0, 301):
            k = i
            p = 1 - math.exp(-k / tau)
            pts.append((ox + k / KMAX * (ex - ox), ypos(p)))
        d.line(pts, fill=color, width=width)

    curve(110, GREY, 6)
    curve(14, BLUE, 6)

    # 虚线：最终都能到
    top_y = ypos(0.9)
    x = ox + 10
    while x < ex - 10:
        d.line([(x, top_y), (min(x + 16, ex - 10), top_y)], fill=ORANGE, width=3)
        x += 30
    d.text((ex - 10, top_y - 34), "最后都能到 100%，差别只在要试几次",
           font=font(24), fill=ORANGE, anchor="ra")

    d.text((ox + 250, ypos(0.30) + 44), "基座：试上百次才稳", font=font(26), fill=GREY)
    d.text((ox + 330, ypos(0.97) + 40), "后训练后：第一次就中", font=font(26), fill=BLUE)

    footer(d, W, H, "形状为示意；实测依据 arXiv:2504.13837：RL 主要提升采样效率，上界由基座决定")
    im.save(ROOT / "03-probability.png")
    return im


def chart_axes():
    W, H = 1600, 900
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    header(d, "该扩哪条轴？答案是环境，不是题目",
           "agentic RL 数据的扩展指数排序（定性；arXiv:2610.23946，多模型多域拟合）")

    items = [("环境", "environment", "同一种任务，能长出多少种世界", ORANGE),
             ("任务", "task", "同一类问题，能出多少道题", BLUE),
             ("轨迹", "trajectory", "同一道题，能采多少条路径", GREY)]

    y = 250
    for i, (zh, en, desc, color) in enumerate(items):
        h = 150
        d.rounded_rectangle([110, y, W - 110, y + h], radius=18, fill="white", outline=GRID, width=2)
        d.rounded_rectangle([110, y, 130, y + h], radius=18, fill=color)
        d.text((175, y + 32), f"{i + 1}", font=font(56, True), fill=color)
        d.text((270, y + 42), zh, font=font(40, True), fill=INK)
        d.text((270, y + 96), desc, font=font(24), fill=GREY)
        d.text((W - 150, y + 62), en, font=font(26), fill=color, anchor="ra")
        y += h + 26

    footer(d, W, H, "排序结论可用，具体倍数未在图中给出：拟合区间与模型清单见原论文")
    im.save(ROOT / "04-three-axes.png")
    return im


if __name__ == "__main__":
    chart_time().save(ROOT / "02-time-token.png")
    chart_axes().save(ROOT / "04-three-axes.png")
    print("ok:", [p.name for p in sorted(ROOT.glob("0[234]-*.png"))])
