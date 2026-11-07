#!/usr/bin/env python3
"""封面叠字（通用版）：AI 无字底图 → 裁切 21:9 → 脚本画金色/暖白发光两行短标题。

替代过去每篇目录一份的 make_cover.py 副本。用法：

  python3 scripts/make_cover.py <文章目录> [--no-crop]

本篇封面文字外置到文章目录的 cover_spec.json（唯一必填项）：

  {"lines": ["标准答案", "越看越崩"]}

可选覆盖项（默认值即 2026-11-10 篇规格，一般不用动）：
  gold_top/gold_bot  渐变字色 RGB（作者 2026-11-07 要求：白 → 暖白；
                     旧金色 #E8A317 对比度不足已废止）
  canvas             21:9 目标尺寸 [1916, 821]
  text_y             文字块垂直位置（画面高比例，默认 0.34）
  width_ratio        文字块宽度（画面宽比例，默认 0.94）
  glow_radius        辉光半径（画面高比例，默认 0.022）

硬规格（AGENTS.md「封面标题显眼度规格」）：金色/暖白发光 · 两行居中 ·
每行字高约画面高 1/9–1/8 · 整块文字高 ≤ 画面高 1/4 · 除标题外无任何文字 ·
背景压暗退后。封面文字总字数 ≤12（信息流缩略可读下限）。
⚠️ 上游忽略 size 参数（实测返回约 1536x1024），故强制中心裁切到 21:9。
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

_args = [a for a in sys.argv[1:] if not a.startswith("--")]
D = Path(_args[0]).resolve() if _args else Path.cwd()

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_INDEX = 2  # .ttc 里 index=2 是 SC（简体）字面

_spec_path = D / "cover_spec.json"
if not _spec_path.exists():
    sys.exit(f"❌ 缺 {_spec_path}——封面文字（lines）必须外置到 cover_spec.json")
_spec = json.loads(_spec_path.read_text(encoding="utf-8"))
if not _spec.get("lines"):
    sys.exit(f"❌ {_spec_path} 缺 lines（两行短标题，合计 ≤12 字）")

LINES = _spec["lines"]
GOLD_TOP = tuple(_spec.get("gold_top", (255, 255, 255)))
GOLD_BOT = tuple(_spec.get("gold_bot", (255, 238, 190)))
CANVAS = tuple(_spec.get("canvas", (1916, 821)))  # 21:9（2026-10-09 篇同规格）
TEXT_Y = _spec.get("text_y", 0.34)
WIDTH_RATIO = _spec.get("width_ratio", 0.94)
GLOW_RADIUS = _spec.get("glow_radius", 0.022)


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
    im.resize(size, Image.LANCZOS).save(dst, "PNG")
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
    x = 0
    # 画布必须容纳 ascent+descent（Noto Sans CJK ≈ 1.47em）；过低会裁掉字形底部
    img = Image.new("L", (int(target_w) + 4, size * 2), 0)
    d = ImageDraw.Draw(img)
    for i, ch in enumerate(text):
        d.text((x, 0), ch, font=f, fill=255)
        x += widths[i] + (gap if i in gap_after else 0)
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img, img.size[0], size


def gold_gradient(w, h):
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px_row = tuple(round(a + (b - a) * t) for a, b in zip(GOLD_TOP, GOLD_BOT))
        for x in range(w):
            px[x, y] = px_row
    return g


def make_cover(bg_path, out_path, lines=LINES, width_ratio=WIDTH_RATIO, glow_radius=GLOW_RADIUS):
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
    y = int(H * TEXT_Y)  # 垂直居中偏上（两行短标题）
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
    if not raw.exists():
        sys.exit(f"❌ 缺 {raw}——先放 AI 无字底图（00-cover-raw.png）")
    if "--no-crop" not in sys.argv:
        crop_21_9(raw, fixed)
    p, sz, fs, bh, ratio = make_cover(fixed, D / "00-cover.png")
    total_chars = sum(len(t) for t in LINES)
    meta = {
        "lines": LINES,
        "total_chars": total_chars,
        "font_size_px": fs,
        "block_height_px": bh,
        "block_ratio": round(ratio, 4),
        "canvas": list(sz),
        "rule": "封面文字必须脚本叠加（PIL），禁止 AI 生图直接写中文；总字数 ≤12；文字块高 ≤25% 画面高",
    }
    (D / "cover_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"封面已生成: {p}  尺寸 {sz}  字号 {fs}")
    print(f"  两行文字块高 {bh}px = 画面高 {ratio:.1%}（硬上限 25%）")
    print(f"  封面文字: {' / '.join(LINES)}  共 {total_chars} 字（硬上限 12）")
    print("  cover_meta.json 已写入（quality_check.py 自动读取核验）")
