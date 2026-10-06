#!/usr/bin/env python3
"""贴图合成：yai 实景打底，Nieman 原图原样嵌入，中文由脚本后绘。"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W, H = 1024, 1536
INK = (248, 250, 252)
DIM = (226, 232, 240)
GOLD = (255, 196, 64)
RED = (255, 72, 72)
GREEN = (134, 239, 172)
CYAN = (125, 211, 252)


def font(size):
    return ImageFont.truetype(FONT, size, index=2)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def fit_font(draw, s, max_w, start, floor=36):
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


def rounded_paste(base, img, xy, radius=24, shadow=18):
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


def trim_white(im, thresh=245, pad=8):
    a = np.array(im.convert("L"))
    ink = a < thresh
    ys, xs = np.where(ink)
    if len(xs) == 0:
        return im
    x0, x1 = max(0, xs.min() - pad), min(im.width, xs.max() + pad)
    y0, y1 = max(0, ys.min() - pad), min(im.height, ys.max() + pad)
    return im.crop((x0, y0, x1, y1))


def contain(im, box):
    bw, bh = box
    im = im.convert("RGB")
    scale = min(bw / im.width, bh / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def circle_on(draw, box, width=8, fill=None):
    draw.ellipse(box, outline=RED, width=width)
    if fill:
        draw.ellipse(box, outline=RED, width=width)


def scrim(im, y0, y1, alpha=210):
    h = im.size[1]
    grad = Image.new("L", (1, h), 0)
    for y in range(max(0, y0), min(h, y1)):
        t = (y - y0) / max(1, y1 - y0)
        # stronger at the far end of the band
        if y0 < h / 2:
            val = int(alpha * (1 - t) ** 0.7)
        else:
            val = int(alpha * (t ** 0.85))
        grad.putpixel((0, y), val)
    layer = Image.new("RGBA", im.size, (8, 10, 16, 255))
    layer.putalpha(grad.resize(im.size))
    return Image.alpha_composite(im, layer)


def mark_circle(im, center, radius=36):
    im = im.convert("RGBA")
    d = ImageDraw.Draw(im)
    x, y = center
    d.ellipse([x - radius, y - radius, x + radius, y + radius], outline=RED, width=7)
    return im


def poster_01():
    """封面：买咖啡那张假图对上本人的画。普通人一眼能看懂。"""
    base = cover_crop(Image.open(ROOT / "base-02-desk.png"), (W, H), focus=(760, 520))
    base = base.convert("RGBA")
    veil = Image.new("RGBA", (W, H), (8, 10, 16, 90))
    base = Image.alpha_composite(base, veil)
    base = scrim(base, 0, 280, 230)

    # 去掉 Nieman 的英文色条，红圈标在 e. flake 上
    fake = Image.open(SRC / "flake-ai.jpg").crop((0, 48, 1000, 877))
    fake = mark_circle(fake, (798, 592), 42)
    real = Image.open(SRC / "flake-real.jpg").crop((0, 48, 998, 877))
    real = mark_circle(real, (770, 637), 34)
    fake = trim_white(fake)
    real = trim_white(real)
    card_w = 920
    gap = 16
    # leave room for title and a bottom line
    avail = 1080
    fake_h = int(avail * 0.50)
    real_h = avail - fake_h - gap
    fake = contain(fake, (card_w - 28, fake_h - 72))
    real = contain(real, (card_w - 28, real_h - 72))

    def card(im, label, label_bg):
        cw, ch = card_w, im.size[1] + 78
        canvas = Image.new("RGB", (cw, ch), (248, 246, 240))
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle([0, 0, cw - 1, 62], radius=0, fill=label_bg)
        d.rectangle([0, 40, cw, 62], fill=label_bg)
        f = font(34)
        d.text((22, 12), label, font=f, fill=(12, 12, 14))
        canvas.paste(im, ((cw - im.width) // 2, 70))
        return canvas

    top = card(fake, "假的 · 对白是「她去买咖啡」", (255, 92, 82))
    bot = card(real, "真的 · 这句才是笑话 · 同一支笔名", (110, 210, 140))
    y = 250
    rounded_paste(base, top, (52, y), radius=22)
    y += top.size[1] + gap
    rounded_paste(base, bot, (52, y), radius=22)

    d = ImageDraw.Draw(base)
    d.text((48, 28), "数解AI", font=font(30), fill=CYAN)
    title = ["ChatGPT假画，", "签了超过15个真人名字"]
    yy = 72
    for line in title:
        f = fit_font(d, line, W - 80, 68)
        d.text((40, yy), line, font=f, fill=INK)
        yy += f.size + 6
    d.text((48, H - 78), "两张都签着 e. flake。笑点是瞎的，签名是真的。", font=font(32), fill=GOLD)
    base.convert("RGB").save(ROOT / "01.png", "PNG")


def poster_02():
    """原帖嵌进手机屏幕，签名放大到桌面上。"""
    base = Image.open(ROOT / "base-01-phone.png").convert("RGBA")
    base = scrim(base, 0, 250, 220)

    panel = Image.open(SRC / "loper-forgery.jpg").crop((12, 96, 848, 1005))
    # phone inner screen, inset so rounded corners don't eat the signature
    sx0, sy0, sx1, sy1 = 378, 336, 682, 998
    sw, sh = sx1 - sx0, sy1 - sy0
    fitted = contain(panel, (sw - 8, sh - 8))
    px = sx0 + (sw - fitted.width) // 2
    py = sy0 + (sh - fitted.height) // 2
    mask = Image.new("L", fitted.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, fitted.width - 1, fitted.height - 1], radius=18, fill=255
    )
    base.paste(fitted, (px, py), mask)

    # Bloper 在原图约 (730, 910)；panel 原点是 (12, 96)
    scale = fitted.width / panel.width
    sig_x = px + (730 - 12) * scale
    sig_y = py + (910 - 96) * scale

    sig = Image.open(SRC / "loper-forgery.jpg").crop((600, 860, 845, 990))
    sig = trim_white(sig, thresh=236, pad=18)
    loupe = 300
    sig_fit = contain(sig, (loupe - 36, loupe - 36))
    disk = Image.new("RGBA", (loupe, loupe), (248, 244, 236, 255))
    disk.paste(sig_fit, ((loupe - sig_fit.width) // 2, (loupe - sig_fit.height) // 2))
    circ = Image.new("L", (loupe, loupe), 0)
    ImageDraw.Draw(circ).ellipse([8, 8, loupe - 9, loupe - 9], fill=255)
    # place on the wood, lower right, clear of the right thumb
    lx, ly = 690, 1120
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse(
        [lx + 8, ly + 10, lx + loupe + 8, ly + loupe + 10], fill=(0, 0, 0, 160)
    )
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
    base.paste(disk, (lx, ly), circ)
    d = ImageDraw.Draw(base)
    d.ellipse([lx + 4, ly + 4, lx + loupe - 5, ly + loupe - 5], outline=GOLD, width=8)
    d.line([(sig_x, sig_y), (lx + 36, ly + 28)], fill=GOLD, width=5)
    r = 22
    d.ellipse([sig_x - r, sig_y - r, sig_x + r, sig_y + r], outline=RED, width=6)

    d.text((40, 24), "数解AI", font=font(28), fill=CYAN)
    d.text((40, 64), "8月26日这一条", font=font(34), fill=GOLD)
    line = "2.5万赞，签的不是他"
    f = fit_font(d, line, W - 80, 60)
    d.text((40, 108), line, font=f, fill=INK)
    d.text((40, 178), "浏览 42.2万 · 笔名 Bloper", font=font(32), fill=DIM)
    d.text((lx + 78, ly - 40), "放大看签名", font=font(26), fill=GOLD)
    base.convert("RGB").save(ROOT / "02.png", "PNG")


def paste_disk(base, img, center, radius):
    """把原图嵌进放大镜镜片，并留住玻璃高光。"""
    cx, cy = center
    side = radius * 2
    fitted = contain(img.convert("RGB"), (int(side * 0.92), int(side * 0.40)))
    disk = Image.new("RGBA", (side, side), (246, 242, 232, 255))
    disk.paste(fitted, ((side - fitted.width) // 2, (side - fitted.height) // 2))
    orig = base.crop((cx - radius, cy - radius, cx + radius, cy + radius)).convert("RGBA")
    glare = orig.point(lambda p: p)
    # 只把镜片里特别亮的高光叠回去
    ga = np.array(orig)
    lum = ga[:, :, :3].mean(axis=2)
    gmask = np.clip((lum - 210) * 4, 0, 180).astype(np.uint8)
    glare_layer = Image.new("RGBA", (side, side), (255, 248, 230, 0))
    glare_layer.putalpha(Image.fromarray(gmask))
    disk = Image.alpha_composite(disk, glare_layer)
    circ = Image.new("L", (side, side), 0)
    ImageDraw.Draw(circ).ellipse([8, 8, side - 9, side - 9], fill=255)
    circ = circ.filter(ImageFilter.GaussianBlur(5))
    base.paste(disk, (cx - radius, cy - radius), circ)


def poster_03():
    """放大镜里嵌进 Byrnes 的签名，假画和真迹句号都在。"""
    base = cover_crop(Image.open(ROOT / "base-03-glass.png"), (W, H), focus=(690, 560))
    base = base.convert("RGBA")
    # 镜片中心：cover_crop 后大约落在这里
    paste_disk(
        base,
        Image.open(SRC / "byrnes-ai.jpg").crop((640, 668, 815, 728)),
        (575, 710),
        230,
    )

    def sig_chip(path, box, caption, cap_color):
        im = trim_white(Image.open(path).crop(box), thresh=230, pad=12)
        im = contain(im, (420, 150))
        canvas = Image.new("RGB", (460, 220), (250, 248, 242))
        canvas.paste(im, ((460 - im.width) // 2, 12))
        d = ImageDraw.Draw(canvas)
        d.text((16, 172), caption, font=font(30), fill=cap_color)
        return canvas

    fake = sig_chip(SRC / "byrnes-ai.jpg", (640, 668, 815, 728), "假画 · 句号在", (180, 40, 36))
    real = sig_chip(SRC / "byrnes-real.jpg", (745, 642, 955, 705), "真迹 · 句号也在", (20, 90, 50))

    # drop the chips on the lower paper, under the lens
    rounded_paste(base, fake, (40, 1080), radius=18, shadow=12)
    rounded_paste(base, real, (524, 1080), radius=18, shadow=12)

    base = scrim(base, 0, 220, 200)
    d = ImageDraw.Draw(base)
    d.text((40, 28), "数解AI", font=font(28), fill=CYAN)
    d.text((40, 72), "十几张假画", font=font(58), fill=INK)
    d.text((40, 142), "句号都在", font=font(58), fill=GOLD)
    base.convert("RGB").save(ROOT / "03.png", "PNG")


if __name__ == "__main__":
    poster_01()
    poster_02()
    poster_03()
    print("saved 01.png 02.png 03.png")
