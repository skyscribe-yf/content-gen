#!/usr/bin/env python3
"""CLT-FP8 篇脚本图：01 骰子实验 / 02 √n 增长曲线 / 03 三死法判据卡。

数字与正文一致：12 个骰子和集中在 42 附近；√n = 1,2,4,8,16,64；√4096=64。
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
    centered(d, (800, 100), "骰子叠加：均匀怎么变成钟形", F_TITLE, INK)
    centered(d, (800, 155), "1 个骰子：每面 1/6，一条水平线；12 个骰子：总和趋向钟形", F_BODY, MUTED)

    # 左：1 个骰子均匀
    x0, y0, w, h = 150, 300, 520, 420
    rounded(d, (x0 - 20, y0 - 20, x0 + w + 20, y0 + h + 70), fill="#FFFFFF", outline=PALE_BLUE)
    centered(d, (x0 + w / 2, y0 + h + 32), "1 个骰子 · 均匀", F_SUB, INK)
    # 面值刻度
    for i in range(6):
        cx = x0 + w * (i + 0.5) / 6
        d.line([(cx, y0 + h), (cx, y0 + h + 12)], fill=GRAY, width=3)
        centered(d, (cx, y0 + h + 36), str(i + 1), F_BODY, MUTED)
    d.line([(x0, y0 + h / 3), (x0 + w, y0 + h / 3)], fill=BLUE, width=6)
    centered(d, (x0 + w / 2, y0 + h / 3 - 30), "每面 1/6", F_BODY, BLUE)
    d.line([(x0, y0 + h), (x0 + w, y0 + h)], fill=INK, width=3)

    # 右：12 个骰子钟形（用二项近似：和 = 6*12=72 减 12..72，用组合卷积近似正态）
    x1, y1, w1, h1 = 930, 300, 520, 420
    rounded(d, (x1 - 20, y1 - 20, x1 + w1 + 20, y1 + h1 + 70), fill="#FFFFFF", outline=PALE_BLUE)
    centered(d, (x1 + w1 / 2, y1 + h1 + 32), "12 个骰子 · 钟形", F_SUB, INK)

    # 近似正态曲线：均值 42，std = sqrt(12 * 35/12) ≈ 5.9
    mu, sd = 42.0, math.sqrt(12 * 35 / 12)
    xs = list(range(12, 73))
    ys = [math.exp(-0.5 * ((x - mu) / sd) ** 2) for x in xs]
    maxy = max(ys)
    pts = []
    for x, y in zip(xs, ys):
        px = x1 + (x - 12) / 60 * w1
        py = y1 + h1 - (y / maxy) * h1 * 0.92
        pts.append((px, py))
    d.line(pts, fill=BLUE, width=5)
    d.line([(x1, y1 + h1), (x1 + w1, y1 + h1)], fill=INK, width=3)
    # 标注 42
    mx = x1 + (42 - 12) / 60 * w1
    d.line([(mx, y1 + h1), (mx, y1 + h1 + 14)], fill=ORANGE, width=3)
    centered(d, (mx, y1 + h1 + 38), "42 ≈ 和集中在中间", F_SMALL, ORANGE)

    im.save(ROOT / "01-dice-clt.png")


def chart_02():
    im, d = new_canvas()
    centered(d, (800, 100), "误差波动按 √n 走", F_TITLE, INK)
    centered(d, (800, 155), "想减半？代价 ×4——这就是随机误差的宿命", F_BODY, MUTED)

    x0, y0, w, h = 200, 280, 1200, 460
    n_pts = [1, 4, 16, 64, 4096]
    # 画布坐标
    def px(n):
        return x0 + math.log(n, 2) / math.log(4096, 2) * w

    def py(v):
        return y0 + h - (v / 64) * h * 0.9

    d.line([(x0, y0 + h), (x0 + w, y0 + h)], fill=INK, width=3)
    d.line([(x0, y0), (x0, y0 + h)], fill=INK, width=3)

    curve = [(px(n), py(math.sqrt(n))) for n in [1, 4, 16, 64, 4096]]
    d.line(curve, fill=BLUE, width=6)

    # 参照线：线性 n（归一化到 64）
    lin = [(px(n), py(n / 64 * 64)) for n in [1, 4, 16, 64, 4096]]
    d.line([(x0, y0 + h), (x0 + w, y0)], fill=GRAY, width=4)

    for n in n_pts:
        cx = px(n)
        d.line([(cx, y0 + h), (cx, y0 + h + 12)], fill=INK, width=3)
        centered(d, (cx, y0 + h + 36), f"n={n}", F_BODY, INK)
        r = math.sqrt(n)
        cy = py(r)
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=ORANGE)
        centered(d, (cx, cy - 40), f"√n={int(r)}", F_BODY, ORANGE)

    centered(d, (x0 + w + 40, y0 + 40), "n", F_SUB, MUTED)
    centered(d, (x0 - 60, y0 - 30), "√n", F_SUB, MUTED)
    centered(d, (x0 + w * 0.62, y0 + 120), "√n 曲线：波动只按开根号爬", F_BODY, BLUE)
    centered(d, (x0 + w * 0.78, y0 + 240), "线性：n 倍（相关误差）", F_BODY, GRAY)

    im.save(ROOT / "02-sqrt-n-curve.png")


def chart_03():
    im, d = new_canvas()
    centered(d, (800, 100), "CLT 三前提 = 三种死法", F_TITLE, INK)
    centered(d, (800, 155), "随机误差温和（√n），系统性偏置致命（n）", F_SUB, ORANGE)

    cards = [
        ("前提一：零均值", "被四舍五入打破", "偏置按 n 线性涨", "必死", "解法：随机舍入", PALE_YELLOW, ORANGE),
        ("前提二：独立性", "被相关误差打破", "波动按 n 涨而非 √n", "死得无声无息", "解法：128 拍结算", PALE_BLUE, BLUE),
        ("前提三：方差有限", "被重尾分布打破", "收敛慢，波动难预算", "死不瞑目", "解法：分组量化", PALE_ORANGE, ORANGE),
    ]
    cw, gap, x0, y0 = 460, 40, 110, 300
    for i, (t1, t2, t3, t4, t5, pale, color) in enumerate(cards):
        x = x0 + i * (cw + gap)
        rounded(d, (x, y0, x + cw, y0 + 480), radius=24, fill=pale)
        d.rectangle([x, y0, x + cw, y0 + 12], fill=color)
        centered(d, (x + cw / 2, y0 + 70), t1, F_SUB, INK)
        centered(d, (x + cw / 2, y0 + 130), t2, F_BODY, INK)
        centered(d, (x + cw / 2, y0 + 200), t3, F_BODY, INK)
        centered(d, (x + cw / 2, y0 + 290), t4, F_BIG, color)
        centered(d, (x + cw / 2, y0 + 380), t5, F_BODY, MUTED)

    im.save(ROOT / "03-clt-three-deaths.png")


if __name__ == "__main__":
    chart_01()
    chart_02()
    chart_03()
    print("charts done")
