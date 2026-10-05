#!/usr/bin/env python3
"""把 AI 实景和精确数字合成贴图。数字不经过生图模型。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
INK = (245, 250, 255)
DIM = (203, 213, 225)
GOLD = (255, 196, 64)
CYAN = (110, 231, 255)
RED = (255, 138, 128)
GREEN = (134, 239, 172)


def font(size):
    return ImageFont.truetype(FONT, size, index=2)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def scrim_bottom(im, top_ratio, alpha=228):
    w, h = im.size
    top = int(h * top_ratio)
    grad = Image.new("L", (1, h), 0)
    for y in range(top, h):
        t = (y - top) / max(1, h - top)
        grad.putpixel((0, y), int(alpha * (t ** 1.15)))
    layer = Image.new("RGBA", im.size, (8, 12, 20, 255))
    layer.putalpha(grad.resize(im.size))
    return Image.alpha_composite(im.convert("RGBA"), layer)


def chip(draw, xy, text, fill, fg=(8, 12, 20)):
    f = font(32)
    x, y = xy
    tw = text_w(draw, text, f)
    pad_x, pad_y = 16, 8
    box = [x, y, x + tw + pad_x * 2, y + 32 + pad_y * 2]
    draw.rounded_rectangle(box, radius=12, fill=fill)
    draw.text((x + pad_x, y + pad_y - 2), text, font=f, fill=fg)
    return box


def poster_01():
    im = Image.open(ROOT / "base-01-desk.png").convert("RGBA")
    im = scrim_bottom(im, 0.62, 236)
    d = ImageDraw.Draw(im)
    d.text((48, 40), "数解AI", font=font(32), fill=CYAN)
    d.text((48, 86), "图 1 / 3  ·  论文里的银行例子", font=font(30), fill=GOLD)
    # 物件在画面上半，标签贴在物件旁，不盖住主体
    chip(d, (36, 430), "该调 · 余额", GREEN)
    chip(d, (430, 250), "多翻 · 流水", GOLD)
    chip(d, (620, 430), "多翻 · 储蓄", GOLD)
    chip(d, (500, 640), "多翻 · 卡号", RED)
    y = 930
    d.text((48, y), "DeepSeek V4 Pro 越权最狠，", font=font(56), fill=INK)
    y += 66
    d.text((48, y), "查个余额它把卡号也翻了", font=font(56), fill=INK)
    y += 90
    for line in (
        "字面最少：一个余额接口",
        "实际常一起调：流水、储蓄、卡号",
        "这是 OverAct 的原例，不是比喻",
    ):
        d.text((48, y), line, font=font(36), fill=DIM)
        y += 56
    im.convert("RGB").save(ROOT / "01.png", "PNG")


def bar_row(draw, y, name, value, vmax, highlight=False):
    x0, bar_x, bar_w, h = 48, 430, 500, 46
    f = font(30)
    color = GOLD if highlight else (120, 170, 210)
    draw.text((x0, y + 6), name, font=f, fill=INK if highlight else DIM)
    bw = int(bar_w * value / vmax)
    draw.rounded_rectangle([bar_x, y, bar_x + bar_w, y + h], radius=8, fill=(30, 41, 59))
    draw.rounded_rectangle([bar_x, y, bar_x + max(bw, 8), y + h], radius=8, fill=color)
    label = f"{value:.2f}"
    draw.text((bar_x + bar_w + 16, y + 6), label, font=f, fill=GOLD if highlight else INK)


def poster_02():
    """纸堆照片的高低和 Table 1 对不上，不能当数据图用。这张只画表。"""
    W, H = 1024, 1536
    base = Image.new("RGBA", (W, H), (10, 16, 28, 255))
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, W, 8], fill=GOLD)
    d.text((48, 48), "数解AI", font=font(32), fill=CYAN)
    d.text((48, 110), "图 2 / 3  ·  调用个数 / 最少该调的个数", font=font(30), fill=GOLD)
    d.text((48, 168), "七个模型，没有一个刚好", font=font(56), fill=INK)
    d.text((48, 250), "1.00 才是刚好。这七根都高于 1.00，全是多调。", font=font(30), fill=DIM)
    rows = [
        ("DeepSeek V4 Pro", 2.39, True),
        ("GLM-5.2", 1.96, False),
        ("Qwen3.7-Max", 1.74, False),
        ("Qwen3.6-Plus", 1.65, False),
        ("Kimi K2.7 Code", 1.65, False),
        ("Qwen3.6-Flash", 1.50, False),
        ("DeepSeek-v3", 1.18, False),
    ]
    y = 330
    for name, val, hi in rows:
        bar_row(d, y, name, val, 2.6, hi)
        y += 92
    notes = [
        "平均每题大约多调 0.7 个工具",
        "模糊说法的超额，是精确说法的 2.7 倍",
        "工具加到 36 个，倍数停在 2.00",
        "和 24 个时的 1.97 差不多，再加也不明显更高",
        "温度从 0 拉到 1，超额几乎不动",
    ]
    y += 24
    for line in notes:
        d.text((48, y), line, font=font(32), fill=DIM)
        y += 52
    d.text((48, H - 72), "数字来自 OverAct Table 1 与第 4 章，不是示意。", font=font(28), fill=(148, 163, 184))
    base.convert("RGB").save(ROOT / "02.png", "PNG")


def poster_03():
    im = Image.open(ROOT / "base-03-gate.png").convert("RGBA")
    im = scrim_bottom(im, 0.58, 236)
    d = ImageDraw.Draw(im)
    d.text((48, 36), "数解AI", font=font(32), fill=CYAN)
    d.text((48, 82), "图 3 / 3  ·  两种补救", font=font(30), fill=GOLD)
    chip(d, (28, 150), "先解释  +9%", RED, fg=INK)
    chip(d, (520, 520), "只放行一个", GREEN)
    d.text((48, 980), "解释被当成了许可证", font=font(56), fill=INK)
    y = 1070
    for line, color in (
        ("只解释：隐私超额升 9%", RED),
        ("只删除：降 36%", GREEN),
        ("解释加删除：降 43%", GREEN),
        ("温度 0 到 1，超额几乎不动", DIM),
        ("话说精确，93.3% 的多翻不想要", GOLD),
    ):
        d.text((48, y), line, font=font(34), fill=color)
        y += 58
    im.convert("RGB").save(ROOT / "03.png", "PNG")


if __name__ == "__main__":
    poster_01()
    poster_02()
    poster_03()
    print("saved 01.png 02.png 03.png")
