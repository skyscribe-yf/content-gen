#!/usr/bin/env python3
"""封面叠字：AI 无字底图 + 脚本画**金色发光标题**。

为什么这样做：AI 画中文全角标点不可靠 —— 实测两次都把全角「：」「，」画成半角
`:` `,`（docs/image-generation.md 第 5 条记过这个坑）。把标题交给脚本画，
才能保证「数字标点一字不差」这条硬规格。

规格（docs/image-generation.md「封面标题显眼度规格」）：
  金色发光 · 两行居中 · 每行字高约画面高 1/9–1/8 · 整块文字高 ≤ 画面高 1/4 ·
  每行尽量横向铺满（靠字间距微调，不放大字号） · 除标题外无任何文字
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = Path("content/2026-10-04-semantic-entropy")
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_INDEX = 2  # .ttc 里 index=2 是 SC（简体）字面

LINES = ["问 AI 100 遍：100 种说法，", "为什么只算 1 种答案？"]
GOLD_TOP, GOLD_BOT = (255, 231, 120), (232, 163, 23)  # #FFE778 → #E8A317


def layout(draw, text, size, target_w):
    """渲染一行。字间距只做轻微舒展（上限 0.10 em）——绝不为了填满画幅把字排散。"""
    f = ImageFont.truetype(FONT, size, index=FONT_INDEX)
    widths = [f.getlength(ch) for ch in text]
    glyph_h = size  # 画布按 em 高度给，视觉字高约 0.86×size

    gap = size * 0.10

    m = Image.new("L", (int(sum(widths) + gap * (len(text) - 1)) + 8, glyph_h + 8), 0)
    d = ImageDraw.Draw(m)
    x = 4.0
    for ch, w in zip(text, widths):
        d.text((x, 4), ch, font=f, fill=255)
        x += w + gap
    return m, m.size[0], glyph_h


def gold_gradient(w, h):
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px_row = tuple(round(a + (b - a) * t) for a, b in zip(GOLD_TOP, GOLD_BOT))
        for x in range(w):
            px[x, y] = px_row
    return g


def make_cover(bg_path, out_path, lines=LINES, width_ratio=0.90, glow_radius=0.022):
    bg = Image.open(bg_path).convert("RGB")
    W, H = bg.size

    # 字号：视觉字高 ≈ H/9.5（落在 1/9–1/8 区间内偏小，给两行留总量余量）
    size = int(H / 9.5 / 0.86)

    masks = [layout(ImageDraw.Draw(Image.new("L", (1, 1))), t, size, 0) for t in lines]
    line_h = max(m.size[1] for m, _, _ in masks)
    leading = int(line_h * 0.12)
    block_h = line_h * len(lines) + leading * (len(lines) - 1)

    # 整块 ≤ H/4 硬约束
    if block_h > H * 0.25:
        scale = H * 0.25 / block_h
        size = int(size * scale)
        masks = [layout(ImageDraw.Draw(Image.new("L", (1, 1))), t, size, 0) for t in lines]
        line_h = max(m.size[1] for m, _, _ in masks)
        leading = int(line_h * 0.12)
        block_h = line_h * len(lines) + leading * (len(lines) - 1)

    canvas = Image.new("L", (W, H), 0)
    y = int(H * 0.13)
    for m, _, _ in masks:
        canvas.paste(m, ((W - m.size[0]) // 2, y), m)
        y += line_h + leading

    # 外发光
    gr = max(6, int(H * glow_radius))
    glow = canvas.filter(ImageFilter.GaussianBlur(gr))
    glow = glow.point(lambda v: min(255, int(v * 1.15)))
    glow_rgb = gold_gradient(W, H)
    out = bg.copy()
    halo = Image.new("RGB", (W, H), (255, 200, 60))
    out = Image.composite(Image.blend(out, halo, 0.85), out, glow)
    # 实心金字
    text_rgb = gold_gradient(W, H)
    out = Image.composite(text_rgb, out, canvas)
    # 高光：字面再叠一层提亮
    hi = canvas.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: int(v * 0.35))
    out = Image.composite(Image.new("RGB", (W, H), (255, 250, 220)), out, hi)

    out.save(out_path, "PNG")
    return out_path, out.size, size, int(block_h), block_h / H


if __name__ == "__main__":
    p, sz, fs, bh, ratio = make_cover(D / "00-cover-bg.png", D / "00-cover.png")
    print(f"封面已生成: {p}  尺寸 {sz}  字号 {fs}")
    print(f"  两行文字块高 {bh}px = 画面高 {ratio:.1%}（硬上限 25%）")
