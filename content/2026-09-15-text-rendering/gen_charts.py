#!/usr/bin/env python3
"""《AI 生图写不对字》数字配图：好看度 vs 文字准确率的落差。

风格对齐 2026-09-13-grpo-math / 2026-09-14-reward-hacking 的 gen_charts.py（PIL 直绘）。
数字来源：OCRGenBench (arXiv:2507.15085v4)，Nano Banana Pro 海报 T2I 任务
VIEScore(美观)=91.87，AR(文字准确率)=58.22。正文改动数字须同步此文件。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG = "#F8FAFC"
INK = "#17324D"
BLUE = "#0F4C81"
CYAN = "#55C9EA"
YELLOW = "#F6BD60"
ORANGE = "#E76F51"
GREY = "#5B7186"
GRID = "#D9E2EC"

W, H = 1254, 940
FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def font(size: int, bold: bool = False):
    for p in (FONT_PATHS if bold else FONT_PATHS[1:] + FONT_PATHS[:1]):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((72, 56), "同一个模型、同一批海报任务", font=font(42, True), fill=INK)
    d.text((72, 116), "OCRGenBench：19 个模型评测（arXiv:2507.15085v4）", font=font(24), fill=GREY)

    # 绘图区
    left, right, top, bottom = 190, W - 130, 230, 760
    d.line((left, bottom, right, bottom), fill=INK, width=3)
    d.line((left, top, left, bottom), fill=INK, width=3)

    # y 轴刻度 0/25/50/75/100
    for v in (0, 25, 50, 75, 100):
        y = bottom - (bottom - top) * v / 100
        d.line((left, y, right, y), fill=GRID, width=1)
        d.text((left - 70, y - 14), str(v), font=font(22), fill=GREY)

    bar_w = 190
    xs = [left + 175, left + 470]
    vals = [91.87, 58.22]
    colors = [YELLOW, BLUE]

    for x, v, c in zip(xs, vals, colors):
        y = bottom - (bottom - top) * v / 100
        d.rounded_rectangle((x, y, x + bar_w, bottom), radius=10, fill=c)
        label = f"{v}"
        fb = font(46, True)
        tw = d.textlength(label, font=fb)
        d.text((x + bar_w / 2 - tw / 2, y - 62), label, font=fb, fill=INK)

    # 落差标注
    ax = xs[1] + bar_w + 60
    y1 = bottom - (bottom - top) * 91.87 / 100
    y2 = bottom - (bottom - top) * 58.22 / 100
    d.line((ax, y1, ax, y2), fill=ORANGE, width=4)
    d.line((ax - 16, y1, ax + 16, y1), fill=ORANGE, width=4)
    d.line((ax - 16, y2, ax + 16, y2), fill=ORANGE, width=4)
    d.text((ax + 26, (y1 + y2) / 2 - 20), "差 34 分", font=font(34, True), fill=ORANGE)

    # x 轴标签
    for x, t in zip(xs, ["美观度（VIEScore）", "文字准确率（AR）"]):
        f = font(28, True)
        tw = d.textlength(t, font=f)
        d.text((x + bar_w / 2 - tw / 2, bottom + 22), t, font=f, fill=INK)

    d.text((72, H - 58), "同一张图：好看 91.87 分，字只对了 58.22%", font=font(24), fill=GREY)

    img.save(ROOT / "01-two-scores.png")
    print("saved 01-two-scores.png", img.size)

    draw_error_budget()


def draw_error_budget() -> None:
    """02 图：一个字的错误，在像素尺子上有多小。"""
    img = Image.new("RGB", (W, H), "#F8FAFC")
    d = ImageDraw.Draw(img)

    d.text((72, 56), "损失函数按像素平均，字占的像素太少", font=font(42, True), fill=INK)
    d.text((72, 116), "招牌写错一个偏旁，摊进整张图的均方误差里几乎听不见", font=font(24), fill=GREY)

    # 左：整张图（示意网格），其中一小格代表文字区域
    grid_x, grid_y, cell, n = 96, 240, 58, 9
    for i in range(n):
        for j in range(n):
            x0, y0 = grid_x + i * cell, grid_y + j * cell
            fill = "#E6EDF5" if (i, j) != (4, 4) else ORANGE
            d.rectangle((x0, y0, x0 + cell - 4, y0 + cell - 4), fill=fill)

    d.text((grid_x, grid_y + n * cell + 30), "整张图 = 81 个格子", font=font(26, True), fill=INK)
    d.text((grid_x, grid_y + n * cell + 72), "文字只占其中 1 个", font=font(26, True), fill=ORANGE)

    # 右：解释文字
    tx = grid_x + n * cell + 90
    lines = [
        ("均方误差把每个像素的", INK),
        ("误差加在一起再平均", INK),
        ("", INK),
        ("字错了 → 分母太大", INK),
        ("损失几乎不动", ORANGE),
        ("", INK),
        ("天空少一片云 →", INK),
        ("占的像素多，损失叫得响", BLUE),
        ("", INK),
        ("模型优化的是", INK),
        ("「整体像不像」", ORANGE),
    ]
    y = 260
    for text, color in lines:
        if text:
            d.text((tx, y), text, font=font(30, True), fill=color)
        y += 50

    d.text((72, H - 52), "误差代价按像素面积算，文字的价值不按像素面积算", font=font(24), fill=GREY)

    img.save(ROOT / "02-pixel-budget.png")
    print("saved 02-pixel-budget.png", img.size)


if __name__ == "__main__":
    main()
