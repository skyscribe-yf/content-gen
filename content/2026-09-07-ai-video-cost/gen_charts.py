#!/usr/bin/env python3
"""AI 视频成本篇数字图：01 每秒价格对比 / 02 30秒=900帧 / 03 帧数平方增长。"""

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
MUTED = "#6B7C8F"
PALE_BLUE = "#DCEAF4"
PALE_YELLOW = "#FFF1C7"
PALE_ORANGE = "#FCE1D9"
GRAY = "#9AA7B4"


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
F_SUB = font(26, True)
F_BODY = font(24)
F_SMALL = font(19)
F_BIG = font(34, True)


def new_canvas(size=(1600, 900)):
    im = Image.new("RGB", size, BG)
    return im, ImageDraw.Draw(im)


def centered(d: ImageDraw.ImageDraw, xy, text: str, fnt, fill=INK):
    box = d.textbbox((0, 0), text, font=fnt)
    d.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2), text, font=fnt, fill=fill)


def rounded(d: ImageDraw.ImageDraw, box, radius=22, fill=PALE_BLUE, outline=None, width=2):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def chart_01():
    """每秒价格对比：主流区间 vs 可灵三档 vs H3。"""
    im, d = new_canvas()
    centered(d, (800, 100), "生成一秒 AI 视频，要花多少钱？", F_TITLE, INK)
    centered(d, (800, 155), "单位：元/秒（2026 年实测与官方定价）", F_BODY, MUTED)

    # 柱状图：7款实测区间 0.18~1.38 / 可灵 0.9/1.2/3.0 / H3 2K 0.8 / H3 768p 0.1
    items = [
        ("7 款主流实测", 0.18, 1.38, BLUE, PALE_BLUE, "0.18 ~ 1.38"),
        ("可灵 API 720P", 0.9, 0.9, BLUE, PALE_BLUE, "0.9"),
        ("可灵 API 1080P", 1.2, 1.2, BLUE, PALE_BLUE, "1.2"),
        ("可灵 API 2K", 3.0, 3.0, BLUE, PALE_BLUE, "3.0"),
        ("MiniMax H3 2K", 0.8, 0.8, ORANGE, PALE_ORANGE, "0.8"),
        ("MiniMax H3 768p", 0.1, 0.1, ORANGE, PALE_ORANGE, "0.1"),
    ]
    base_y = 720
    scale = 150  # 每元像素
    bw = 150
    x0 = 120
    gap = 30
    for i, (label, lo, hi, color, pale, txt) in enumerate(items):
        x = x0 + i * (bw + gap)
        h = int(hi * scale)
        top = base_y - h
        d.rounded_rectangle([x, top, x + bw, base_y], radius=12, fill=pale)
        d.rectangle([x, top, x + bw, top + 6], fill=color)
        centered(d, (x + bw / 2, top - 30), txt, F_BIG, color)
        # 标签两行
        words = label.split(" ")
        if len(words) == 2:
            centered(d, (x + bw / 2, base_y + 40), words[0], F_SMALL, INK)
            centered(d, (x + bw / 2, base_y + 70), words[1], F_SMALL, INK)
        else:
            centered(d, (x + bw / 2, base_y + 40), label, F_SMALL, INK)
    # 基线
    d.line([x0 - 20, base_y, x0 + 6 * (bw + gap) + 40, base_y], fill=GRAY, width=3)
    centered(d, (800, 850), "H3 把 2K 价格打到主流的三分之一，768p 只要 0.1 元/秒", F_BODY, ORANGE)
    im.save(ROOT / "01-price-per-second.png")


def chart_02():
    """30 秒 = 900 帧：每一帧都是一张图。"""
    im, d = new_canvas()
    centered(d, (800, 100), "30 秒视频 = 900 帧 = 900 次「画图」", F_TITLE, INK)
    centered(d, (800, 155), "30 帧/秒 × 30 秒 = 900 帧，每一帧都是一次完整生成", F_BODY, MUTED)

    # 左侧：帧网格示意（30 帧一行，画 3 行代表 90 帧，标注 ×10）
    gx0, gy0 = 120, 260
    cell = 26
    gap = 4
    rows, cols = 3, 30
    for r in range(rows):
        for c in range(cols):
            x = gx0 + c * (cell + gap)
            y = gy0 + r * (cell + gap)
            d.rounded_rectangle([x, y, x + cell, y + cell], radius=5, fill=PALE_BLUE, outline=BLUE, width=1)
    d.text((gx0, gy0 + rows * (cell + gap) + 12), "1 秒 = 30 帧", font=F_SMALL, fill=MUTED)
    d.text((gx0 + 200, gy0 + rows * (cell + gap) + 12), "这里只画了 3 秒（90 帧）", font=F_SMALL, fill=MUTED)

    # 右侧：放大一帧
    rx0, ry0 = 1050, 260
    d.rounded_rectangle([rx0, ry0, rx0 + 380, ry0 + 380], radius=18, fill=PALE_YELLOW, outline=YELLOW, width=3)
    centered(d, (rx0 + 190, ry0 + 120), "1 帧", F_BIG, INK)
    centered(d, (rx0 + 190, ry0 + 190), "从纯噪声", F_BODY, INK)
    centered(d, (rx0 + 190, ry0 + 240), "迭代几十步", F_BODY, INK)
    centered(d, (rx0 + 190, ry0 + 290), "才出一张图", F_BODY, INK)
    d.text((rx0, ry0 + 400), "文生图：1 张", font=F_SMALL, fill=MUTED)
    d.text((rx0, ry0 + 430), "视频：900 张", font=F_SMALL, fill=ORANGE)

    centered(d, (800, 850), "贵的第一层原因：量。900 张图 × 每张的扩散成本", F_BODY, INK)
    im.save(ROOT / "02-900-frames.png")


def chart_03():
    """帧数 vs 计算量：平方增长。"""
    im, d = new_canvas()
    centered(d, (800, 100), "帧与帧要互相「对答案」：成本平方级增长", F_TITLE, INK)
    centered(d, (800, 155), "每一帧都要关注所有其他帧——帧数翻倍，计算量翻 4 倍", F_BODY, MUTED)

    # 曲线：y = x^2 采样点
    points = [(10, 100), (30, 900), (60, 3600), (120, 14400), (300, 90000), (900, 810000)]
    # 对数刻度画点
    plot_x0, plot_y0, plot_w, plot_h = 200, 300, 1200, 420
    max_x, max_y = 900, 810000

    def px(x):
        return plot_x0 + (x / max_x) ** 0.5 * plot_w

    def py(y):
        return plot_y0 + plot_h - (y / max_y) ** 0.5 * plot_h

    # 网格
    for gx in [0.25, 0.5, 0.75, 1.0]:
        x = plot_x0 + gx * plot_w
        d.line([x, plot_y0, x, plot_y0 + plot_h], fill="#E3E9F0", width=2)
    for gy in [0.25, 0.5, 0.75, 1.0]:
        y = plot_y0 + plot_h - gy * plot_h
        d.line([plot_x0, y, plot_x0 + plot_w, y], fill="#E3E9F0", width=2)

    # 曲线
    curve = [(px(x), py(y)) for x, y in points]
    d.line(curve, fill=BLUE, width=6)

    # 标注点
    labels = {
        10: "10 帧\n100 对",
        30: "30 帧\n900 对",
        900: "900 帧\n81 万对",
    }
    for x, y in points:
        if x in labels:
            cx, cy = px(x), py(y)
            d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=ORANGE)
            lx = cx + 20 if x < 600 else cx - 260
            ly = cy - 30
            d.text((lx, ly), labels[x], font=F_SMALL, fill=INK)

    # 轴标签
    d.text((plot_x0 - 30, plot_y0 + plot_h + 20), "帧数 →", font=F_SMALL, fill=MUTED)
    d.text((plot_x0 - 200, plot_y0 - 30), "两两关系对数 ↑", font=F_SMALL, fill=MUTED)

    centered(d, (800, 850), "900 帧 → 81 万对关系：这就是长视频烧钱的根本原因", F_BODY, INK)
    im.save(ROOT / "03-quadratic-cost.png")


if __name__ == "__main__":
    chart_01()
    chart_02()
    chart_03()
    print("done")
