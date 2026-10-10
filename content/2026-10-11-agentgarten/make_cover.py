#!/usr/bin/env python3
"""封面叠字：AI 无字底图 → 裁切 21:9 → 脚本画**金色发光短标题**。

本次口径（作者 2026-10-10 现场指令，覆盖 AGENTS.md 旧规）：
  封面文字**只突出一两个要点，不是全文标题**；无文字亦可。
  版式规格沿用：金色发光 · 两行居中 · 每行字高约画面高 1/9–1/8 ·
  整块文字高 ≤ 画面高 1/4 · 除标题外无任何文字。

⚠️ 上游会忽略 size 参数（实测返回 2073x759），故本脚本强制中心裁切到 21:9。
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = Path("content/2026-10-11-agentgarten")
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_INDEX = 2  # .ttc 里 index=2 是 SC（简体）字面

# 封面短标题（作者拍板：只突出一两个要点）
LINES = ["1 亿局 vs 几轮", "差的是练习场"]
GOLD_TOP, GOLD_BOT = (255, 231, 120), (232, 163, 23)  # #FFE778 → #E8A317

CANVAS = (1916, 821)  # 21:9（2026-10-09 篇同规格）


def crop_21_9(src: Path, dst: Path, size=CANVAS) -> Path:
    """中心裁切到目标比例（保持全幅内容，不拉伸）后再缩放到目标尺寸。"""
    im = Image.open(src).convert("RGB")
    W, H = im.size
    tw, th = size
    want = tw / th
    if W / H > want:                      # 太宽 → 裁两侧
        nw = int(round(H * want))
        im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else:                                 # 太高 → 裁上下
        nh = int(round(W / want))
        im = im.crop((0, (H - nh) // 2, W, (H - nh) // 2 + nh))
    im = im.resize(size, Image.LANCZOS)
    im.save(dst, "PNG")
    return dst


def is_wide(ch: str) -> bool:
    """CJK / 全角标点等宽字符。数字、拉丁字母、空格都算窄字符。"""
    return ord(ch) >= 0x2E80


def layout(text, size, target_w):
    """渲染一行。字距只在宽字符参与的边界上舒展（上限 0.10 em）。"""
    f = ImageFont.truetype(FONT, size, index=FONT_INDEX)
    widths = [f.getlength(ch) for ch in text]
    natural = sum(widths)
    gap_after = {i for i in range(len(text) - 1)
                 if is_wide(text[i]) or is_wide(text[i + 1])}
    gap = 0.0
    if gap_after and target_w > natural:
        gap = min(size * 0.10, (target_w - natural) / len(gap_after))
    total_w = natural + gap * len(gap_after)

    glyph_h = size
    m = Image.new("L", (int(total_w) + 8, int(size * 1.5) + 8), 0)
    d = ImageDraw.Draw(m)
    x = 4.0
    for i, (ch, w) in enumerate(zip(text, widths)):
        d.text((x, 4), ch, font=f, fill=255)
        x += w
        if i in gap_after:
            x += gap
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


def make_cover(bg_path, out_path, lines=LINES, width_ratio=0.94, glow_radius=0.022):
    bg = Image.open(bg_path).convert("RGB")
    W, H = bg.size
    target_w = W * width_ratio

    # 短标题两行：允许把字号顶到「块高 ≤1/4」的上限，尽量显眼
    size = int(H / 8 * 0.86)

    def metrics(sz):
        line_h = sz + 8
        leading = int(line_h * 0.12)
        return line_h, leading, line_h * len(lines) + leading * (len(lines) - 1)

    line_h, leading, block_h = metrics(size)
    while block_h > H * 0.25:
        size = int(size * (H * 0.25) / block_h) - 1
        line_h, leading, block_h = metrics(size)

    f = ImageFont.truetype(FONT, size, index=FONT_INDEX)
    max_nat = max(sum(f.getlength(ch) for ch in t) for t in lines)
    if max_nat > target_w:
        size = int(size * target_w / max_nat)
        line_h, leading, block_h = metrics(size)

    masks = [layout(t, size, target_w) for t in lines]

    canvas = Image.new("L", (W, H), 0)
    y = int(H * 0.34)  # 垂直居中偏上（两行短标题）
    for m, _, _ in masks:
        canvas.paste(m, ((W - m.size[0]) // 2, y), m)
        y += line_h + leading

    gr = max(6, int(H * glow_radius))
    glow = canvas.filter(ImageFilter.GaussianBlur(gr))
    glow = glow.point(lambda v: min(255, int(v * 1.15)))
    out = bg.copy()
    halo = Image.new("RGB", (W, H), (255, 200, 60))
    out = Image.composite(Image.blend(out, halo, 0.85), out, glow)
    text_rgb = gold_gradient(W, H)
    out = Image.composite(text_rgb, out, canvas)
    hi = canvas.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: int(v * 0.35))
    out = Image.composite(Image.new("RGB", (W, H), (255, 250, 220)), out, hi)

    out.save(out_path, "PNG")
    return out_path, out.size, size, int(block_h), block_h / H


if __name__ == "__main__":
    raw = D / "00-cover-raw.png"
    fixed = D / "00-cover-base.png"
    if "--no-crop" not in sys.argv:
        crop_21_9(raw, fixed)
    p, sz, fs, bh, ratio = make_cover(fixed, D / "00-cover.png")
    print(f"封面已生成: {p}  尺寸 {sz}  字号 {fs}")
    print(f"  两行文字块高 {bh}px = 画面高 {ratio:.1%}（硬上限 25%）")
    print(f"  封面文字: {' / '.join(LINES)}")
