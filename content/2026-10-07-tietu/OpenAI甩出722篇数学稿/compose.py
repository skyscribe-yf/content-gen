#!/usr/bin/env python3
"""贴图合成：yai 实景打底，数字和 Lean 原文由脚本后绘。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
W, H = 1024, 1536
INK = (248, 250, 252)
DIM = (226, 232, 240)
GOLD = (255, 196, 64)
RED = (255, 92, 82)
GREEN = (134, 239, 172)
CYAN = (125, 211, 252)
CARD = (12, 16, 24)


def font(size, mono=False):
    if mono:
        return ImageFont.truetype(MONO, size)
    return ImageFont.truetype(FONT, size, index=2)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def fit_font(draw, s, max_w, start, floor=28, mono=False):
    size = start
    while size > floor and text_w(draw, s, font(size, mono)) > max_w:
        size -= 2
    return font(size, mono)


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


def scrim(im, y0, y1, alpha=210):
    h = im.size[1]
    grad = Image.new("L", (1, h), 0)
    for y in range(max(0, y0), min(h, y1)):
        t = (y - y0) / max(1, y1 - y0)
        if y0 < h / 2:
            val = int(alpha * (1 - t) ** 0.65)
        else:
            val = int(alpha * (t ** 0.8))
        grad.putpixel((0, y), val)
    layer = Image.new("RGBA", im.size, (8, 10, 16, 255))
    layer.putalpha(grad.resize(im.size))
    return Image.alpha_composite(im, layer)


def band_veil(im, y0, y1, alpha=190, feather=120):
    """中间一条柔边暗带，给居中的大字让出底。"""
    h = im.size[1]
    mask = Image.new("L", (1, h), 0)
    for y in range(h):
        v = 0
        if y0 <= y <= y1:
            v = alpha
        elif y0 - feather < y < y0:
            v = int(alpha * (y - (y0 - feather)) / feather)
        elif y1 < y < y1 + feather:
            v = int(alpha * (1 - (y - y1) / feather))
        mask.putpixel((0, y), v)
    layer = Image.new("RGBA", im.size, (8, 10, 16, 255))
    layer.putalpha(
        mask.resize(im.size, Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(12))
    )
    return Image.alpha_composite(im, layer)


def draw_center(d, y, segments, f, cx=W // 2):
    """一行多色文字，整体按中线居中。"""
    total = sum(d.textlength(t, font=f) for t, _ in segments)
    x = cx - total / 2
    for t, fill in segments:
        d.text((x, y), t, font=f, fill=fill)
        x += d.textlength(t, font=f)


def rounded_paste(base, img, xy, radius=22, shadow=16):
    x, y = xy
    img = img.convert("RGBA")
    w, h = img.size
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [x + 8, y + 12, x + w + 8, y + h + 12], radius=radius, fill=(0, 0, 0, 150)
        )
        base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow)))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    base.paste(img, (x, y), mask)


def poster_01():
    base = cover_crop(Image.open(ROOT / "base-01-door.png"), (W, H)).convert("RGBA")
    base = scrim(base, 0, 190, 170)
    base = band_veil(base, 420, 1120, alpha=190)
    d = ImageDraw.Draw(base)

    f_brand = font(30)
    d.text(((W - d.textlength("数解AI", font=f_brand)) / 2, 42), "数解AI", font=f_brand, fill=CYAN)

    # 中央大字：两行，与定稿标题同一句
    lines = [
        [("OpenAI甩出", INK), ("722", GOLD), ("篇数学稿，", INK)],
        [("模型却", INK), ("不给用", RED)],
    ]
    size = 84
    for segs in lines:
        f = fit_font(d, "".join(t for t, _ in segs), W - 130, 84, floor=48)
        size = min(size, f.size)
    f_big = font(size)

    punch = "给你看，不给你用。"
    f_punch = font(46)

    total_h = size * 2 + 12 + 34 + f_punch.size
    y = int(H * 0.48 - total_h / 2)
    for segs in lines:
        draw_center(d, y, segs, f_big)
        y += size + 12
    y += 24
    d.text(((W - d.textlength(punch, font=f_punch)) / 2, y), punch, font=f_punch, fill=GOLD)

    meta = "10月6日 · 稿在 GitHub · openai/math"
    f_meta = font(30)
    d.text(((W - d.textlength(meta, font=f_meta)) / 2, H - 82), meta, font=f_meta, fill=DIM)
    base.convert("RGB").save(ROOT / "01.png", "PNG")


def num_card(number, unit, note, accent):
    cw, ch = 440, 280
    im = Image.new("RGB", (cw, ch), (18, 22, 32))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=24, outline=accent, width=4)
    f = fit_font(d, number, cw - 48, 92, floor=48)
    d.text((28, 36), number, font=f, fill=accent)
    d.text((28, 150), unit, font=font(36), fill=INK)
    d.text((28, 206), note, font=font(26), fill=DIM)
    return im


def poster_02():
    base = cover_crop(Image.open(ROOT / "base-02-desk.png"), (W, H)).convert("RGBA")
    base = scrim(base, 0, 280, 230)
    d = ImageDraw.Draw(base)
    d.text((48, 32), "数解AI", font=font(28), fill=CYAN)
    d.text((48, 78), "仓库自己写的数", font=font(56), fill=INK)
    d.text((48, 152), "openai/math · README", font=font(30), fill=GOLD)
    cards = [
        num_card("722", "篇手稿", "分成 372 个家族", GOLD),
        num_card("372", "个家族", "相关稿归在一起", CYAN),
        num_card("约4000", "道题", "给模型出的题量", GREEN),
        num_card("3小时", "ChatGPT Pro 连轴转", "一篇的算力，不是耗时", RED),
    ]
    positions = [(52, 250), (532, 250), (52, 560), (532, 560)]
    for card, xy in zip(cards, positions):
        rounded_paste(base, card, xy, radius=24)
    d = ImageDraw.Draw(base)
    f_sum = fit_font(d, "平均一篇的算力，够 ChatGPT Pro 连轴转 3 小时", W - 96, 34, floor=26)
    d.text((48, H - 250), "平均一篇的算力，够 ChatGPT Pro 连轴转 3 小时", font=f_sum, fill=INK)
    d.text((48, H - 190), "模型还没放出来", font=font(40), fill=GOLD)
    d.text((48, H - 110), "未形式化的，仓库写了：可能有问题", font=font(28), fill=DIM)
    base.convert("RGB").save(ROOT / "02.png", "PNG")


def code_card():
    lines = [
        "theorem main : MainStatement.{u} := by",
        "  sorry",
    ]
    cw, ch = 920, 280
    im = Image.new("RGB", (cw, ch), (16, 18, 22))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=18, outline=RED, width=4)
    d.rectangle([0, 0, cw, 52], fill=(48, 18, 18))
    d.text((20, 10), "BarnetteHamiltonian.lean", font=font(26, mono=True), fill=GOLD)
    y = 78
    for i, line in enumerate(lines):
        color = RED if "sorry" in line else (230, 236, 242)
        d.text((28, y), line, font=font(32, mono=True), fill=color)
        y += 52
    d.text((28, 214), "sorry  =  证明还没填上", font=font(28), fill=GOLD)
    return im


def poster_03():
    base = cover_crop(Image.open(ROOT / "base-03-rack.png"), (W, H)).convert("RGBA")
    base = scrim(base, 0, 340, 230)
    base = scrim(base, 1180, H, 180)
    d = ImageDraw.Draw(base)
    d.text((48, 28), "数解AI", font=font(28), fill=CYAN)
    d.text((48, 74), "说明写着：证明了", font=font(52), fill=INK)
    d.text((48, 146), "文件里是 sorry", font=font(56), fill=GOLD)
    d.text((48, 224), "1969 年的 Barnette 猜想", font=font(32), fill=DIM)
    card = code_card()
    rounded_paste(base, card, (52, 340), radius=18)
    # 两张对照条
    def strip(title, body, color):
        im = Image.new("RGB", (440, 220), (18, 22, 32))
        dd = ImageDraw.Draw(im)
        dd.rounded_rectangle([0, 0, 439, 219], radius=18, outline=color, width=4)
        dd.text((22, 28), title, font=font(30), fill=color)
        yy = 88
        for line in body:
            dd.text((22, yy), line, font=font(32), fill=INK)
            yy += 44
        return im

    left = strip("lean/docs/180.md", ["形式化证明了", "每一个这样的图"], GREEN)
    right = strip("对照文件", ["theorem main", ":= by sorry"], RED)
    rounded_paste(base, left, (52, 680), radius=18)
    rounded_paste(base, right, (532, 680), radius=18)
    d = ImageDraw.Draw(base)
    d.text((48, H - 200), "到 9 月 29 日，百科还标着未解", font=font(32), fill=INK)
    d.text((48, H - 140), "顾问组同月写过：请停", font=font(36), fill=GOLD)
    d.text((48, H - 80), "用外人用不了的模型刷高难数学", font=font(28), fill=DIM)
    base.convert("RGB").save(ROOT / "03.png", "PNG")


if __name__ == "__main__":
    poster_01()
    poster_02()
    poster_03()
    print("wrote 01.png 02.png 03.png")
