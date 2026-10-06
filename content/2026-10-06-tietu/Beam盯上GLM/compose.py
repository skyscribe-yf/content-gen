#!/usr/bin/env python3
"""Beam 贴图：yai 实景打底，官网原图嵌入，中文和大数字后绘。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W, H = 1024, 1536
INK = (248, 250, 252)
DIM = (226, 232, 240)
GOLD = (255, 196, 64)
RED = (255, 110, 96)
CYAN = (125, 211, 252)
GREEN = (167, 243, 208)


def font(size):
    return ImageFont.truetype(FONT, size, index=2)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def fit_font(draw, s, max_w, start, floor=28):
    size = start
    while size > floor and text_w(draw, s, font(size)) > max_w:
        size -= 2
    return font(size)


def cover_crop(im, size, focus=None):
    im = im.convert("RGB")
    tw, th = size
    scale = max(tw / im.width, th / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    if focus is None:
        left, top = (nw - tw) // 2, (nh - th) // 2
    else:
        fx, fy = focus
        left = int(fx * scale - tw / 2)
        top = int(fy * scale - th / 2)
        left = max(0, min(left, nw - tw))
        top = max(0, min(top, nh - th))
    return im.crop((left, top, left + tw, top + th))


def scrim_top(im, y1, alpha=220):
    h = im.size[1]
    grad = Image.new("L", (1, h), 0)
    for y in range(0, min(h, y1)):
        t = y / max(1, y1)
        grad.putpixel((0, y), int(alpha * (1 - t) ** 0.65))
    layer = Image.new("RGBA", im.size, (6, 8, 14, 255))
    layer.putalpha(grad.resize(im.size))
    return Image.alpha_composite(im.convert("RGBA"), layer)


def rounded_paste(base, img, xy, radius=22, shadow=16):
    x, y = xy
    img = img.convert("RGBA")
    w, h = img.size
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [x + 6, y + 10, x + w + 6, y + h + 10], radius=radius, fill=(0, 0, 0, 150)
        )
        base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow)))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    base.paste(img, (x, y), mask)


def contain(im, box):
    bw, bh = box
    im = im.convert("RGB")
    scale = min(bw / im.width, bh / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def number_card(big, small, accent):
    card = Image.new("RGB", (300, 210), (250, 248, 242))
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, 300, 8], fill=accent)
    f = fit_font(d, big, 270, 64)
    d.text(((300 - text_w(d, big, f)) / 2, 36), big, font=f, fill=(18, 18, 20))
    g = font(30)
    d.text(((300 - text_w(d, small, g)) / 2, 130), small, font=g, fill=(70, 64, 58))
    return card


def poster_01():
    base = cover_crop(Image.open(ROOT / "base-03-cards.png"), (W, H), focus=(780, 520))
    veil = Image.new("RGBA", (W, H), (8, 10, 16, 70))
    base = Image.alpha_composite(base.convert("RGBA"), veil)
    base = scrim_top(base, 340, 230)
    d = ImageDraw.Draw(base)
    d.text((40, 28), "数解AI", font=font(28), fill=CYAN)
    for i, line in enumerate(("Beam盯上GLM，", "501B其实只跑23B")):
        f = fit_font(d, line, W - 72, 62)
        d.text((36, 78 + i * 78), line, font=f, fill=INK)

    cards = (
        ("501B", "总参，听着很大", GOLD),
        ("23B", "每次真正干活", RED),
        ("少3到4倍", "号称对标GLM", GREEN),
    )
    x = 42
    for big, small, color in cards:
        rounded_paste(base, number_card(big, small, color), (x, 280), radius=18, shadow=12)
        x += 322
    # 盖住底图上三张空白纸，避免看起来像没做完
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sg = ImageDraw.Draw(shade)
    sg.rectangle([0, 500, W, H], fill=(12, 10, 8, 170))
    base = Image.alpha_composite(base, shade)
    d = ImageDraw.Draw(base)
    d.text((48, 508), "不是分数赢了。是号称同样的活，少烧卡。", font=font(30), fill=GOLD)
    chart = contain(Image.open(SRC / "bench.png"), (940, 640))
    rounded_paste(base, chart, ((W - chart.width) // 2, 560), radius=16, shadow=14)
    d = ImageDraw.Draw(base)
    d.text((48, H - 68), "黑线在左，橙点是 GLM。权重这个月才放。", font=font(28), fill=INK)
    base.convert("RGB").save(ROOT / "01.png", "PNG")


def poster_02():
    base = cover_crop(Image.open(ROOT / "base-01-desk.png"), (W, H), focus=(780, 420))
    base = Image.alpha_composite(base.convert("RGBA"), Image.new("RGBA", (W, H), (6, 8, 12, 80)))
    base = scrim_top(base, 250, 210)
    chart = contain(Image.open(SRC / "bench.png"), (944, 560))
    rounded_paste(base, chart, ((W - chart.width) // 2, 250), radius=16)
    d = ImageDraw.Draw(base)
    d.text((40, 24), "数解AI", font=font(28), fill=CYAN)
    d.text((40, 68), "官网原图", font=font(32), fill=GOLD)
    line = "同样的分，点在更左边"
    f = fit_font(d, line, W - 72, 54)
    d.text((40, 112), line, font=f, fill=INK)
    notes = (
        ("黑线", "Beam", INK),
        ("橙点", "GLM-5.2", (255, 150, 80)),
        ("蓝点", "Qwen 更高也更费", (140, 190, 255)),
    )
    x = 40
    y = 860
    for name, desc, color in notes:
        d.rounded_rectangle([x, y, x + 118, y + 48], radius=10, fill=color)
        d.text((x + 14, y + 8), name, font=font(26), fill=(16, 16, 18))
        d.text((x, y + 60), desc, font=font(26), fill=DIM)
        x += 320
    d.text((40, 1000), "这张图没有 Kimi。", font=font(34), fill=GOLD)
    d.text((40, 1052), "Kimi K3 领先，是正文里的一句话。", font=font(30), fill=DIM)
    d.text((40, 1120), "算力是估算，不是实测账单。", font=font(28), fill=DIM)
    base.convert("RGB").save(ROOT / "02.png", "PNG")


def poster_03():
    base = cover_crop(Image.open(ROOT / "base-02-rack.png"), (W, H), focus=(900, 400))
    base = scrim_top(base, 280, 200)
    chart = contain(Image.open(SRC / "rl.png"), (944, 420))
    rounded_paste(base, chart, ((W - chart.width) // 2, 860), radius=16, shadow=12)
    d = ImageDraw.Draw(base)
    d.text((40, 24), "数解AI", font=font(28), fill=CYAN)
    d.text((40, 70), "你现在下不到", font=font(64), fill=INK)
    rows = (
        ("1.05万张", "GB300，跑了4周"),
        ("超过1亿次", "rollout，到8000万还在涨"),
        ("本月才放", "Apache 2.0，现在只能排队"),
    )
    y = 180
    for big, small in rows:
        d.text((48, y), big, font=font(48), fill=GOLD)
        d.text((48, y + 58), small, font=font(30), fill=DIM)
        y += 140
    d.text((48, 1320), "分数是自己报的。技术报告还没出。", font=font(30), fill=INK)
    base.convert("RGB").save(ROOT / "03.png", "PNG")


if __name__ == "__main__":
    poster_01()
    poster_02()
    poster_03()
    print("saved")
