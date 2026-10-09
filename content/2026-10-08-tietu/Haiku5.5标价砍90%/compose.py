#!/usr/bin/env python3
"""Haiku 5.5 贴图：yai 实景打底，牌价和标题由脚本后绘。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W, H = 1024, 1536
INK = (248, 250, 252)
DIM = (226, 232, 240)
GOLD = (255, 196, 64)
RED = (255, 92, 82)
GREEN = (134, 239, 172)
CYAN = (125, 211, 252)


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


def scrim(im, y0, y1, alpha=210):
    h = im.size[1]
    grad = Image.new("L", (1, h), 0)
    for y in range(max(0, y0), min(h, y1)):
        t = (y - y0) / max(1, y1 - y0)
        val = int(alpha * (1 - t) ** 0.65) if y0 < h / 2 else int(alpha * (t ** 0.8))
        grad.putpixel((0, y), val)
    layer = Image.new("RGBA", im.size, (8, 10, 16, 255))
    layer.putalpha(grad.resize(im.size))
    return Image.alpha_composite(im, layer)


def band_veil(im, y0, y1, alpha=190, feather=120):
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


def shadow_text(d, xy, s, f, fill, shadow=(0, 0, 0, 210)):
    x, y = xy
    for dx, dy in ((2, 2), (0, 2), (2, 0), (-1, 1)):
        d.text((x + dx, y + dy), s, font=f, fill=shadow)
    d.text((x, y), s, font=f, fill=fill)


def draw_center(d, y, segments, f, cx=W // 2):
    total = sum(d.textlength(t, font=f) for t, _ in segments)
    x = cx - total / 2
    # 先铺一层暗影，金色大字才压得住价签高光
    for t, _ in segments:
        for dx, dy in ((3, 3), (0, 3), (3, 0)):
            d.text((x + dx, y + dy), t, font=f, fill=(0, 0, 0, 220))
        x += d.textlength(t, font=f)
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


def load_base(name):
    return cover_crop(Image.open(ROOT / name), (W, H)).convert("RGBA")


def poster_01():
    base = load_base("base-01-slash.png")
    base = scrim(base, 0, 190, 170)
    base = band_veil(base, 430, 1080, alpha=200)
    d = ImageDraw.Draw(base)
    f_brand = font(30)
    d.text(((W - d.textlength("数解AI", font=f_brand)) / 2, 42), "数解AI", font=f_brand, fill=CYAN)

    lines = [
        [("Haiku 5.5", GOLD), ("标价砍", INK), ("90%", GOLD)],
        [("账单没这么爽", RED)],
    ]
    size = 78
    for segs in lines:
        f = fit_font(d, "".join(t for t, _ in segs), W - 96, 78, floor=46)
        size = min(size, f.size)
    f_big = font(size)
    punch = "牌价对齐了，账单没对齐。"
    f_punch = font(40)
    total_h = size * 2 + 16 + 36 + f_punch.size
    y = int(H * 0.54 - total_h / 2)
    for segs in lines:
        draw_center(d, y, segs, f_big)
        y += size + 16
    y += 28
    shadow_text(d, ((W - d.textlength(punch, font=f_punch)) / 2, y), punch, f_punch, GOLD)
    meta = "10月7日发布 · 10万 token 以内的标价"
    f_meta = font(28)
    d.text(((W - d.textlength(meta, font=f_meta)) / 2, H - 78), meta, font=f_meta, fill=DIM)
    base.convert("RGB").save(ROOT / "01.png", "PNG")


def price_card(name, inp, out, note, accent, wide=False):
    cw, ch = (920, 250) if wide else (440, 340)
    im = Image.new("RGB", (cw, ch), (18, 22, 32))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=24, outline=accent, width=4)
    d.text((28, 22), name, font=font(32), fill=accent)
    d.text((28, 78), inp, font=fit_font(d, inp, cw - 56, 52, floor=32), fill=INK)
    d.text((28, 148), out, font=fit_font(d, out, cw - 56, 40, floor=26), fill=DIM)
    d.text((28, ch - 64), note, font=font(26), fill=GOLD)
    return im


def poster_02():
    base = load_base("base-02-counters.png")
    base = scrim(base, 0, 260, 230)
    d = ImageDraw.Draw(base)
    d.text((48, 28), "数解AI", font=font(28), fill=CYAN)
    head = "Haiku 5.5 和 Luna，短档同价"
    f_head = fit_font(d, head, W - 96, 46, floor=32)
    d.text((48, 72), head, font=f_head, fill=INK)
    d.text((48, 140), "每百万 token · 标准档", font=font(28), fill=GOLD)
    cards = [
        price_card("Haiku 4.5", "输入 $1.00", "输出 $5.00", "昨天之前的牌价", DIM),
        price_card("Haiku 5.5", "输入 $0.10", "输出 $0.50", "10万 token 以内", GOLD),
        price_card("GPT-6 Luna", "输入 $0.10", "输出 $0.50", "27.2万以内的短档", CYAN),
        price_card("缓存也对齐", "读取 $0.01", "写入 $0.125", "短档两边一样", GREEN),
    ]
    positions = [(52, 220), (532, 220), (52, 590), (532, 590)]
    for card, xy in zip(cards, positions):
        rounded_paste(base, card, xy, radius=24)
    base = scrim(base, 1180, H, 230)
    d = ImageDraw.Draw(base)
    shadow_text(d, (48, H - 250), "标价低了 90%", font(52), GOLD)
    shadow_text(d, (48, H - 180), "只相对于 Haiku 4.5 的这一档", font(32), INK)
    shadow_text(d, (48, H - 110), "旧 Haiku 大约九成请求落在这条线里", font(28), DIM)
    base.convert("RGB").save(ROOT / "02.png", "PNG")


def cliff_card(kicker, big, body, accent):
    cw, ch = 920, 250
    im = Image.new("RGB", (cw, ch), (18, 22, 32))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=22, outline=accent, width=4)
    d.text((28, 22), kicker, font=font(28), fill=accent)
    d.text((28, 68), big, font=fit_font(d, big, cw - 56, 48, floor=32), fill=INK)
    y = 140
    for line in body:
        d.text((28, y), line, font=font(28), fill=DIM)
        y += 40
    return im


def poster_03():
    base = load_base("base-03-toll.png")
    base = scrim(base, 0, 240, 220)
    d = ImageDraw.Draw(base)
    d.text((48, 28), "数解AI", font=font(28), fill=CYAN)
    d.text((48, 70), "过线就换价目表", font=font(52), fill=INK)
    d.text((48, 140), "单价，不是我算的整单", font=font(28), fill=GOLD)
    cards = [
        cliff_card("Haiku 5.5", "过 10 万 token，单价 ×5", ["输入 $0.10 → $0.50", "输出 $0.50 → $2.50"], RED),
        cliff_card("GPT-6 Luna", "过 27.2 万，整单重算", ["输入 $0.10 → $0.20", "输出 $0.50 → $0.75"], CYAN),
        cliff_card("同一段字", "大约多计 30% token", ["官方原话：具体看内容", "平均跑一次，便宜约 75%"], GOLD),
    ]
    y = 210
    for card in cards:
        rounded_paste(base, card, (52, y), radius=22)
        y += 280
    base = scrim(base, 1240, H, 230)
    d = ImageDraw.Draw(base)
    shadow_text(d, (48, H - 180), "90% 写在牌价上", font(40), GOLD)
    shadow_text(d, (48, H - 110), "75% 才是官方说的平均", font(32), INK)
    base.convert("RGB").save(ROOT / "03.png", "PNG")


def poster_04():
    base = load_base("base-04-cache.png")
    base = scrim(base, 0, 280, 220)
    base = band_veil(base, 980, 1320, alpha=170, feather=80)
    d = ImageDraw.Draw(base)
    d.text((48, 28), "数解AI", font=font(28), fill=CYAN)
    d.text((48, 74), "Sonnet 5.5", font=font(56), fill=INK)
    d.text((48, 150), "缓存读取砍半", font=font(52), fill=GOLD)
    left = price_card("昨天", "缓存读取 $0.20", "每百万 token", "砍之前", DIM)
    right = price_card("今天", "缓存读取 $0.10", "每百万 token", "直接对半", GREEN)
    rounded_paste(base, left, (52, 280), radius=24)
    rounded_paste(base, right, (532, 280), radius=24)
    base = band_veil(base, 660, 1000, alpha=160, feather=40)
    base = scrim(base, 1280, H, 220)
    d = ImageDraw.Draw(base)
    shadow_text(d, (48, 700), "他们说，多数 agent 活", font(36), INK)
    shadow_text(d, (48, 760), "因此大约少两成", font(52), GOLD)
    shadow_text(d, (48, 860), "输入输出牌价没动", font(32), DIM)
    shadow_text(d, (48, 920), "少的是缓存读取这一项", font(32), DIM)
    shadow_text(d, (48, H - 180), "小活你丢给 Haiku", font(44), INK)
    shadow_text(d, (48, H - 110), "还是丢给 Luna？", font(44), GOLD)
    base.convert("RGB").save(ROOT / "04.png", "PNG")


if __name__ == "__main__":
    poster_01()
    poster_02()
    poster_03()
    poster_04()
    print("wrote 01.png 02.png 03.png 04.png")
