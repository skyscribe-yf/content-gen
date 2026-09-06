#!/usr/bin/env python3
"""方差篇数字图：01 两班成绩对比 / 02 偏差距离平方 / 03 标准差区间。"""

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


def centered(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill=INK):
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2), text, font=fnt, fill=fill)


def rounded(draw: ImageDraw.ImageDraw, box, radius=22, fill=PALE_BLUE, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def chart_01():
    im, d = new_canvas()
    centered(d, (800, 110), "平均分都是 90", F_TITLE, INK)
    centered(d, (800, 165), "柱子高度一样，波动完全不一样", F_BODY, MUTED)

    # 两班柱子
    class_a = [85, 87, 90, 93, 95]
    class_b = [60, 95, 95, 100, 100]
    base_y = 760
    scale = 5.2  # 每分像素
    bw = 86

    def draw_class(x0, values, color, pale, label):
        centered(d, (x0 + 215, 250), label, F_SUB, INK)
        for i, v in enumerate(values):
            x = x0 + 30 + i * (bw + 26)
            h = int((v - 40) * scale)
            top = base_y - h
            d.rounded_rectangle([x, top, x + bw, base_y], radius=12, fill=pale)
            d.rectangle([x, top, x + bw, top + 6], fill=color)
            centered(d, (x + bw / 2, top - 34), str(v), F_BODY, INK)
        # 平均线
        avg_y = base_y - int((90 - 40) * scale)
        d.line([x0 + 10, avg_y, x0 + 580, avg_y], fill=ORANGE, width=4)
        d.text((x0 + 590, avg_y - 26), "平均 90", font=F_SMALL, fill=ORANGE)

    draw_class(60, class_a, BLUE, PALE_BLUE, "A 班：85 打底，整整齐齐")
    draw_class(960, class_b, ORANGE, PALE_ORANGE, "B 班：60 垫底，大起大落")

    centered(d, (800, 850), "只看平均分，分不出哪个班更稳", F_BODY, MUTED)
    im.save(ROOT / "01-class-scores.png")


def chart_02():
    im, d = new_canvas()
    centered(d, (800, 100), "波动怎么量：先看每个分数离平均有多远", F_TITLE, INK)
    centered(d, (800, 155), "直接把偏差加起来会正负抵消，所以先平方", F_BODY, MUTED)

    class_a = [85, 87, 90, 93, 95]
    class_b = [60, 95, 95, 100, 100]
    dev_a = [v - 90 for v in class_a]
    dev_b = [v - 90 for v in class_b]

    def draw_dev(x0, values, devs, color, pale, label):
        centered(d, (x0 + 215, 240), label, F_SUB, INK)
        y_start = 340
        gap = 92
        for i, (v, dv) in enumerate(zip(values, devs)):
            y = y_start + i * gap
            d.rounded_rectangle([x0 + 40, y, x0 + 240, y + 58], radius=14, fill=pale)
            centered(d, (x0 + 140, y + 29), f"{v} 分", F_BODY, INK)
            # 偏差箭头（向右/向左）
            if dv >= 0:
                xa, ya = x0 + 330, y + 29
                xb = xa + dv * 4
                d.line([xa, ya, xb, ya], fill=color, width=5)
                d.polygon([(xb, ya), (xb - 16, ya - 10), (xb - 16, ya + 10)], fill=color)
            else:
                xa, ya = x0 + 330, y + 29
                xb = xa + dv * 4
                d.line([xa, ya, xb, ya], fill=color, width=5)
                d.polygon([(xb, ya), (xb + 16, ya - 10), (xb + 16, ya + 10)], fill=color)
            centered(d, (x0 + 480, y + 29), f"偏差 {dv:+d}", F_BODY, color)
        # 平方和
        sumsq = sum(dv * dv for dv in devs)
        var = sumsq / len(devs)
        rounded(d, [x0 + 40, y_start + len(values) * gap - 30, x0 + 500, y_start + len(values) * gap + 50], fill="#FFFFFF", outline=color, width=3)
        centered(d, (x0 + 270, y_start + len(values) * gap + 10), f"平方后平均：方差 = {var:g}", F_BODY, color)

    draw_dev(60, class_a, dev_a, BLUE, PALE_BLUE, "A 班：偏差都在 ±5 以内")
    draw_dev(960, class_b, dev_b, ORANGE, PALE_ORANGE, "B 班：有人差 30 分")

    centered(d, (800, 855), "B 班方差 230 ≈ A 班 13.6 的 17 倍", F_BODY, INK)
    im.save(ROOT / "02-deviation-squares.png")


def chart_03():
    im, d = new_canvas()
    centered(d, (800, 110), "标准差：把单位换回「分」", F_TITLE, INK)
    centered(d, (800, 165), "平均分 90 不变，波动区间差 4 倍", F_BODY, MUTED)

    # 区间条：x 轴 70~110 映射到 150~1450
    def xmap(v):
        return 150 + (v - 70) / 40 * 1300

    # 90 刻度线
    d.line([xmap(90), 260, xmap(90), 720], fill=GRAY, width=3)
    d.text((xmap(90) - 40, 720), "90", font=F_SMALL, fill=MUTED)

    # A 班 90±3.7
    centered(d, (400, 320), "A 班", F_SUB, INK)
    xa1, xa2 = xmap(90 - 3.7), xmap(90 + 3.7)
    d.rounded_rectangle([xa1, 370, xa2, 430], radius=16, fill=BLUE)
    centered(d, (400, 400), "90 ± 3.7 分", F_BODY, "#FFFFFF")

    # B 班 90±15.2
    centered(d, (400, 530), "B 班", F_SUB, INK)
    xb1, xb2 = xmap(90 - 15.2), xmap(90 + 15.2)
    d.rounded_rectangle([xb1, 580, xb2, 640], radius=16, fill=ORANGE)
    centered(d, (400, 610), "90 ± 15.2 分", F_BODY, "#FFFFFF")

    # 刻度
    for v in [70, 80, 90, 100, 110]:
        d.line([xmap(v), 680, xmap(v), 700], fill=GRAY, width=3)
        centered(d, (xmap(v), 715), str(v), F_SMALL, MUTED)

    centered(d, (800, 850), "B 班波动区间是 A 班的约 4 倍——85 打底 vs 60 垫底", F_BODY, INK)
    im.save(ROOT / "03-std-range.png")


if __name__ == "__main__":
    chart_01()
    chart_02()
    chart_03()
    print("done: 01/02/03")
