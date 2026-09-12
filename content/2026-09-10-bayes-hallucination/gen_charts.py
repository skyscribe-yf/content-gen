#!/usr/bin/env python3
"""贝叶斯篇脚本图：01 先验→后验更新（猜硬币）/ 02 全概率分解（看病检测）/ 03 temperature 采样（DeepSeek）。

数字与正文一致：3 次正面后验 89%；发病率 0.1%、准确率 99% → 阳性真得病 9%、误检是真阳性 10 倍；
DeepSeek temperature 默认 1.0、范围 0-2、代码/数学建议 0.0。
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
    """猜硬币：先验 50% → 3 次正面 → 后验 89%"""
    im, d = new_canvas()
    centered(d, (800, 100), "贝叶斯更新：数据不会证明假设，只会更新假设", F_TITLE, INK)
    centered(d, (800, 155), "连抛 3 次正面，硬币「偏向正面」的把握从 50% 跳到 89%", F_BODY, MUTED)

    # 三张卡片：先验 → 似然 → 后验
    cards = [
        ("先验", "P(假设)", "50%", "抛硬币之前，你心里默认正反各半", PALE_YELLOW, ORANGE),
        ("似然", "P(数据|假设)", "3 次正面", "如果硬币偏向正面，看到 3 次正面很自然", PALE_BLUE, BLUE),
        ("后验", "P(假设|数据)", "89%", "先验 × 似然，更新后的把握", PALE_ORANGE, ORANGE),
    ]
    cw, gap, x0, y0 = 440, 50, 120, 300
    for i, (t1, t2, t3, t4, pale, color) in enumerate(cards):
        x = x0 + i * (cw + gap)
        rounded(d, (x, y0, x + cw, y0 + 480), radius=24, fill=pale)
        d.rectangle([x, y0, x + cw, y0 + 12], fill=color)
        centered(d, (x + cw / 2, y0 + 70), t1, F_SUB, INK)
        centered(d, (x + cw / 2, y0 + 130), t2, F_BODY, MUTED)
        centered(d, (x + cw / 2, y0 + 210), t3, F_BIG, color)
        centered(d, (x + cw / 2, y0 + 300), t4, F_SMALL, INK)
        if i < 2:
            centered(d, (x + cw + gap / 2, y0 + 200), "×", F_BIG, GRAY)
    centered(d, (x0 + cw + gap / 2, y0 + 200), "×", F_BIG, GRAY)
    centered(d, (x0 + 2 * (cw + gap) + gap / 2, y0 + 200), "=", F_BIG, GRAY)

    im.save(ROOT / "01-bayes-update.png")


def chart_02():
    """看病检测：全概率分解，阳性 = 真阳 + 误检，真得病只有 9%"""
    im, d = new_canvas()
    centered(d, (800, 100), "阳性报告的两条来路：真阳性 vs 误检", F_TITLE, INK)
    centered(d, (800, 155), "发病率 0.1%、检测准确率 99%——阳性了，真得病只有 9%", F_BODY, MUTED)

    # 左：真阳性（0.099%）
    x0, y0, w, h = 150, 300, 560, 420
    rounded(d, (x0 - 20, y0 - 20, x0 + w + 20, y0 + h + 70), fill="#FFFFFF", outline=PALE_BLUE)
    centered(d, (x0 + w / 2, y0 + h + 32), "真阳性：0.099%", F_SUB, ORANGE)
    # 条形：真阳性占比极小
    d.rectangle([x0, y0 + h - 20, x0 + w * 0.099, y0 + h], fill=ORANGE)
    d.rectangle([x0, y0 + h - 20, x0 + w, y0 + h], outline=INK, width=3)
    centered(d, (x0 + w / 2, y0 + 60), "1000 人里 1 人得病", F_BODY, INK)
    centered(d, (x0 + w / 2, y0 + 120), "检出率 99% → 真阳性 0.099%", F_BODY, MUTED)

    # 右：误检（0.999%）
    x1, y1, w1, h1 = 890, 300, 560, 420
    rounded(d, (x1 - 20, y1 - 20, x1 + w1 + 20, y1 + h1 + 70), fill="#FFFFFF", outline=PALE_BLUE)
    centered(d, (x1 + w1 / 2, y1 + h1 + 32), "误检：0.999%", F_SUB, BLUE)
    d.rectangle([x1, y1 + h1 - 20, x1 + w1 * 0.999, y1 + h1], fill=BLUE)
    d.rectangle([x1, y1 + h1 - 20, x1 + w1, y1 + h1], outline=INK, width=3)
    centered(d, (x1 + w1 / 2, y1 + 60), "999 人没得病", F_BODY, INK)
    centered(d, (x1 + w1 / 2, y1 + 120), "误检率 1% → 误检 0.999%", F_BODY, MUTED)

    # 底部结论条
    centered(d, (800, 800), "误检数量是真阳性的 10 倍 → 阳性报告里真得病只有 9%", F_SUB, ORANGE)

    im.save(ROOT / "02-total-probability.png")


def chart_03():
    """temperature 采样：同一个问题，不同温度抽出不同答案"""
    im, d = new_canvas()
    centered(d, (800, 100), "temperature：从分布里怎么抽", F_TITLE, INK)
    centered(d, (800, 155), "DeepSeek 默认 1.0（范围 0-2），代码/数学建议 0.0", F_BODY, MUTED)

    # 左：低温度（确定性）
    x0, y0, w, h = 150, 300, 560, 420
    rounded(d, (x0 - 20, y0 - 20, x0 + w + 20, y0 + h + 70), fill="#FFFFFF", outline=PALE_BLUE)
    centered(d, (x0 + w / 2, y0 + h + 32), "temperature = 0.0 · 每次都抽最可能的", F_SUB, BLUE)
    # 分布：尖峰
    for i in range(7):
        cx = x0 + w * (i + 0.5) / 7
        hh = h * (0.9 if i == 3 else 0.15)
        d.rectangle([cx - 30, y0 + h - hh, cx + 30, y0 + h], fill=BLUE if i == 3 else PALE_BLUE)
    centered(d, (x0 + w / 2, y0 + 60), "答案几乎一样", F_BODY, INK)

    # 右：高温度（随机）
    x1, y1, w1, h1 = 890, 300, 560, 420
    rounded(d, (x1 - 20, y1 - 20, x1 + w1 + 20, y1 + h1 + 70), fill="#FFFFFF", outline=PALE_BLUE)
    centered(d, (x1 + w1 / 2, y1 + h1 + 32), "temperature = 1.0 · 偶尔抽个冷门", F_SUB, ORANGE)
    # 分布：平缓
    for i in range(7):
        cx = x1 + w1 * (i + 0.5) / 7
        hh = h * (0.5 if i == 3 else 0.3)
        d.rectangle([cx - 30, y1 + h - hh, cx + 30, y1 + h], fill=ORANGE if i == 3 else PALE_ORANGE)
    centered(d, (x1 + w1 / 2, y1 + 60), "同一个问题，答案可能不一样", F_BODY, INK)

    centered(d, (800, 800), "模型的「确定性」是参数调出来的，不是它「知道」", F_SUB, ORANGE)

    im.save(ROOT / "03-temperature-sampling.png")


if __name__ == "__main__":
    chart_01()
    chart_02()
    chart_03()
    print("charts done")
