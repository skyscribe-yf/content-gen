#!/usr/bin/env python3
"""封面叠字：AI 无字底图 → 裁 21:9 → 脚本画金色发光两行短标题。

本篇封面文字（只突出一两个要点，两行合计 ≤12 字）：
  LINES = ["它写完了", "却不肯交卷"]

版式：金色发光 · 两行居中 · 每行字高约画面高 1/9–1/8 ·
整块文字高 ≤ 画面高 1/4 · 除标题外无任何文字 · 背景压暗退后。

相对旧模板的改动（作者 2026-10-31 反馈「呆板、没内容」）：
  1. 文字块上移到画面暗部（上 1/4），不再压在主体亮面上；
  2. 金色改为上亮下深的渐变 + 双层辉光 + 黑色投影，不再平涂；
  3. 字距放宽到 0.16em，两行宽度接近，形成横向带状；
  4. 文字后方加一层柔和暗场 scrim，保证缩到信息流卡片仍可读。
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

D = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_INDEX = 2  # .ttc 里 index=2 是 SC（简体）字面

LINES = ["它写完了", "却不肯交卷"]
GOLD_TOP, GOLD_BOT = (255, 232, 138), (222, 148, 26)
TRACK = 0.16  # em

CANVAS = (1916, 821)
SRC = D / "00-cover-raw-b.png"


def crop_21_9(src: Path, dst: Path, size=CANVAS) -> Path:
    im = Image.open(src).convert("RGB")
    W, H = im.size
    tw, th = size
    want = tw / th
    if W / H > want:
        nw = int(round(H * want))
        im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else:
        nh = int(round(W / want))
        top = (H - nh) // 2
        im = im.crop((0, top, W, top + nh))
    im = im.resize(size, Image.LANCZOS)
    im.save(dst, "PNG")
    return dst


def line_width(chars: list[str], f: ImageFont.FreeTypeFont, size: int) -> float:
    return sum(f.getlength(c) for c in chars) + TRACK * size * (len(chars) - 1)


def draw_line(layer: Image.Image, text: str, f: ImageFont.FreeTypeFont,
              center_y: int, size: int, color: tuple[int, int, int]) -> None:
    d = ImageDraw.Draw(layer)
    w = line_width(list(text), f, size)
    x = (CANVAS[0] - w) / 2
    for ch in text:
        d.text((x, center_y), ch, font=f, fill=color, anchor="lm")
        x += f.getlength(ch) + TRACK * size


def gradient_text(mask: Image.Image, size: int) -> Image.Image:
    """按 mask 的 alpha 铺上亮→深金色竖向渐变。"""
    grad = Image.new("RGB", (1, size), GOLD_TOP)
    top, bot = GOLD_TOP, GOLD_BOT
    for y in range(size):
        t = y / max(1, size - 1)
        grad.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    grad = grad.resize(CANVAS, Image.BILINEAR)
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def cool_grade(base: Image.Image) -> Image.Image:
    """把底图的暖色压到冷调，金色只留给标题——保证高对比与信息流可读性。"""
    img = base.convert("RGB")
    g = ImageOps.grayscale(img)
    tinted = ImageOps.colorize(g, black=(6, 12, 22), white=(214, 231, 247))
    return Image.blend(img, tinted, 0.66)


def scrim(base: Image.Image) -> Image.Image:
    """文字区上方压暗，底部保主体亮度。"""
    W, H = CANVAS
    layer = Image.new("L", (1, H))
    for y in range(H):
        t = y / H
        v = 118 if t < 0.30 else max(0, int(118 * (1 - (t - 0.30) / 0.22)))
        layer.putpixel((0, y), v)
    layer = layer.resize((W, H))
    shade = Image.new("RGBA", CANVAS, (2, 6, 12, 255))
    shade.putalpha(layer)
    return Image.alpha_composite(base.convert("RGBA"), shade)


def main() -> None:
    base_path = D / "00-cover-base.png"
    crop_21_9(SRC, base_path)
    base = cool_grade(Image.open(base_path)).convert("RGBA")

    size = 92  # 821/8.9 ≈ 每行字高 1/8.9 画面高
    f = ImageFont.truetype(FONT, size, index=FONT_INDEX)
    gap = int(size * 0.20)
    block_h = size * 2 + gap
    v_center = int(CANVAS[1] * 0.19)  # 文字块中心落在上 1/4 的暗部
    y1 = v_center - gap // 2 - size // 2
    y2 = v_center + gap // 2 + size // 2

    mask = Image.new("L", CANVAS, 0)
    draw_line(mask, LINES[0], f, y1, size, 255)
    draw_line(mask, LINES[1], f, y2, size, 255)

    canvas = scrim(base)

    # 投影
    shadow = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    sh_mask = mask.filter(ImageFilter.GaussianBlur(10))
    shadow.paste((0, 0, 0, 150), (0, 6), sh_mask)
    canvas = Image.alpha_composite(canvas, shadow)

    # 宽辉光 + 紧辉光
    for radius, alpha in ((26, 110), (9, 150)):
        glow_mask = mask.filter(ImageFilter.GaussianBlur(radius))
        glow = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        glow.paste(GOLD_TOP + (alpha,), (0, 0), glow_mask)
        canvas = Image.alpha_composite(canvas, glow)

    canvas = Image.alpha_composite(canvas, gradient_text(mask, size))
    canvas.convert("RGB").save(D / "00-cover.png", "PNG")

    meta = {
        "lines": LINES,
        "chars": sum(len(x) for x in LINES),
        "font_size": size,
        "block_h": block_h,
        "block_h_ratio": round(block_h / CANVAS[1], 3),
        "line_h_ratio": round(size / CANVAS[1], 3),
    }
    (D / "cover_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
    print(meta)


if __name__ == "__main__":
    main()
