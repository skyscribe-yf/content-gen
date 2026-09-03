#!/usr/bin/env python3
"""Draw the numeric and formula diagrams for the MLE article."""

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


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


F_TITLE = font(42, True)
F_SUB = font(24, True)
F_BODY = font(23)
F_SMALL = font(18)
F_BIG = font(30, True)


def rounded(draw: ImageDraw.ImageDraw, box, radius=22, fill=PALE_BLUE, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill=INK):
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2), text, font=fnt, fill=fill)


def arrow(draw: ImageDraw.ImageDraw, start, end, fill=BLUE, width=5):
    draw.line([start, end], fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 18
    left = (end[0] - length * math.cos(angle - 0.45), end[1] - length * math.sin(angle - 0.45))
    right = (end[0] - length * math.cos(angle + 0.45), end[1] - length * math.sin(angle + 0.45))
    draw.polygon([end, left, right], fill=fill)


def new_canvas(size=(1600, 900)):
    return Image.new("RGB", size, BG), ImageDraw.Draw(Image.new("RGB", size, BG))


def draw_logit():
    im = Image.new("RGB", (1600, 900), BG)
    d = ImageDraw.Draw(im)
    d.text((70, 50), "Logit 只是原始分数", font=F_TITLE, fill=INK)
    d.text((72, 112), "先打分，再归一化成概率", font=F_BODY, fill=MUTED)

    left = (70, 190, 770, 820)
    right = (830, 190, 1530, 820)
    rounded(d, left, fill="#EEF5F9", outline=PALE_BLUE)
    rounded(d, right, fill="#FFF9E9", outline=PALE_YELLOW)
    d.text((110, 225), "原始分数（logit）", font=F_SUB, fill=BLUE)
    d.text((870, 225), "Softmax 后的概率", font=F_SUB, fill=ORANGE)

    tokens = ["猫", "狗", "兔", "企鹅"]
    logits = [5, 3, -2, -100]
    weights = [math.exp(v - max(logits)) for v in logits]
    total = sum(weights)
    probs = [w / total for w in weights]
    max_abs = 100
    y0 = 325
    gap = 105
    for i, (tok, logit, prob) in enumerate(zip(tokens, logits, probs)):
        y = y0 + i * gap
        d.text((120, y - 18), tok, font=F_BIG, fill=INK)
        d.text((225, y - 13), f"{logit}", font=F_BIG, fill=BLUE if logit >= 0 else ORANGE)
        bar_x0, bar_x1 = 355, 700
        d.rounded_rectangle((bar_x0, y - 15, bar_x1, y + 15), radius=15, fill="#D8E5EE")
        length = max(8, int((logit + 100) / 105 * (bar_x1 - bar_x0)))
        d.rounded_rectangle((bar_x0, y - 15, bar_x0 + length, y + 15), radius=15, fill=BLUE if i < 2 else ORANGE)

        d.text((880, y - 18), tok, font=F_BIG, fill=INK)
        p_text = "接近 0" if i == 3 else ("0.08%" if i == 2 else f"{prob * 100:.1f}%")
        d.text((1020, y - 18), p_text, font=F_BIG, fill=ORANGE if i == 3 else BLUE)
        p_len = max(8, int(prob * 410))
        d.rounded_rectangle((1190, y - 15, 1480, y + 15), radius=15, fill="#F7E8B9")
        d.rounded_rectangle((1190, y - 15, 1190 + p_len, y + 15), radius=15, fill=YELLOW if i == 0 else ORANGE)

    d.text((880, 735), "概率在 0 和 1 之间，且总和为 1", font=F_BODY, fill=MUTED)
    d.text((120, 735), "logit 可正可负，不要求总和为 1", font=F_BODY, fill=MUTED)
    im.save(ROOT / "02-logit-probability.png")


def draw_sequence():
    im = Image.new("RGB", (1600, 900), BG)
    d = ImageDraw.Draw(im)
    d.text((70, 50), "一段文本的概率：条件概率连乘", font=F_TITLE, fill=INK)
    d.text((72, 112), "给定前缀，预测下一个 token", font=F_BODY, fill=MUTED)

    tokens = ["我", "喜欢", "吃", "苹果"]
    x_positions = [180, 510, 840, 1170]
    for x, token in zip(x_positions, tokens):
        rounded(d, (x - 70, 205, x + 70, 285), fill=PALE_BLUE, outline=CYAN)
        centered(d, (x, 245), token, F_BIG, fill=BLUE)
    for x in x_positions[:-1]:
        arrow(d, (x + 82, 245), (x + 238, 245), fill=BLUE, width=5)

    labels = ["P(喜欢｜我)", "P(吃｜我，喜欢)", "P(苹果｜我，喜欢，吃)"]
    starts = [(90, 375, 430, 475), (555, 375, 1045, 475), (1145, 375, 1545, 475)]
    for box, label in zip(starts, labels):
        rounded(d, box, fill="#FFF9E9", outline=YELLOW)
        centered(d, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), label, F_BODY, fill=INK)

    arrow(d, (800, 520), (800, 590), fill=ORANGE, width=6)
    centered(d, (800, 550), "取对数", F_SUB, fill=ORANGE)
    rounded(d, (150, 630, 1450, 750), fill="#EEF5F9", outline=PALE_BLUE)
    centered(d, (800, 690), "−log p1  +  −log p2  +  −log p3  =  NLL 累加", F_BIG, fill=BLUE)
    rounded(d, (1130, 780, 1450, 850), fill=PALE_ORANGE, outline=ORANGE)
    centered(d, (1290, 815), "长序列避免数值下溢", F_SMALL, fill=ORANGE)
    im.save(ROOT / "03-sequence-likelihood.png")


def draw_mle_bayes():
    im = Image.new("RGB", (1600, 900), BG)
    d = ImageDraw.Draw(im)
    d.text((70, 50), "MLE 与贝叶斯：一个点，一团分布", font=F_TITLE, fill=INK)
    d.text((72, 112), "同一批数据，对参数不确定性的两种表达", font=F_BODY, fill=MUTED)

    rounded(d, (70, 190, 755, 815), fill="#EEF5F9", outline=PALE_BLUE)
    rounded(d, (845, 190, 1530, 815), fill="#FFF9E9", outline=PALE_YELLOW)
    d.text((110, 225), "MLE：一个最优点", font=F_SUB, fill=BLUE)
    d.text((885, 225), "贝叶斯：后验分布", font=F_SUB, fill=ORANGE)

    # MLE landscape and point.
    origin = (180, 700)
    arrow(d, origin, (650, 700), fill=MUTED, width=3)
    arrow(d, origin, (180, 320), fill=MUTED, width=3)
    for cx, cy, rx, ry, color in [(390, 520, 190, 110, "#DCEAF4"), (470, 560, 125, 70, "#B9D8E8"), (530, 605, 55, 32, "#8DC7DF")]:
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=color, width=5)
    d.ellipse((515, 590, 545, 620), fill=BLUE)
    d.text((555, 575), "最优参数点", font=F_BODY, fill=BLUE)

    # Posterior cloud / bell-like contour.
    origin2 = (955, 700)
    arrow(d, origin2, (1470, 700), fill=MUTED, width=3)
    arrow(d, origin2, (955, 320), fill=MUTED, width=3)
    points = []
    for x in range(1000, 1430, 10):
        z = (x - 1200) / 130
        height = 250 * math.exp(-0.5 * z * z)
        points.append((x, 690 - height))
    d.line(points, fill=ORANGE, width=7, joint="curve")
    d.line([(x, 690) for x, _ in points], fill="#F3D6B9", width=2)
    d.ellipse((1185, 405, 1215, 435), fill=YELLOW)
    d.text((1240, 405), "中心", font=F_BODY, fill=ORANGE)
    d.text((900, 755), "宽度、形状、方差 = 参数不确定性", font=F_SMALL, fill=MUTED)

    rounded(d, (410, 835, 1190, 880), radius=14, fill=PALE_BLUE, outline=PALE_BLUE)
    centered(d, (800, 858), "P(θ｜D) ∝ P(D｜θ)P(θ)", F_BODY, fill=INK)
    im.save(ROOT / "06-mle-vs-bayes.png")


if __name__ == "__main__":
    draw_logit()
    draw_sequence()
    draw_mle_bayes()
    print("drawn: 02-logit-probability.png, 03-sequence-likelihood.png, 06-mle-vs-bayes.png")
