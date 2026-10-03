#!/usr/bin/env python3
"""贴图叠字（双轨配图的下半轨）：AI 底图 + 脚本叠**精确**文字。

为什么需要它：AI 生图会编数字、写错字（项目硬规则禁止 AI 图承载数字），
而贴图的图必须承载关键要素。解法 = AI 出无字底图，文字由本脚本画。

⚠️ 字形坑（2026-10-03 实测 Noto Sans CJK Bold）：`⇄` 在 CJK 字面里没有字形，会渲染成
乱码块；`↔` 会渲染成断开的两个小箭头。要表达「双向」请用 `⇌`，或直接用文字（推荐）。
叠字前先用 `ImageFont.getmask()` 探宽度不够——它照样返回尺寸，必须实渲一张看。

用法：
  python3 scripts/tietu_overlay.py --base base.png --out 01.png \
      --kicker "图 1 / 2 · 打破 CUDA 壁垒的第一步" \
      --title "DeepSeek 开源昇腾全套组件" \
      --line "6 个项目 · 与英伟达一一对应" \
      --line "昇腾 950 · 128 卡超节点"
"""
import argparse
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
PAD = 64
ACCENT = (34, 211, 238)      # cyan-400
INK = (245, 250, 255)
DIM = (203, 213, 225)        # slate-300
BRAND = (125, 211, 252)      # sky-300


def font(size, index=2):
    """Noto Sans CJK .ttc 里 index=2 是 SC（简体）字面。"""
    return ImageFont.truetype(FONT, size, index=index)


def scrim(im, top_ratio=0.58, bottom_alpha=232):
    """底部压暗渐变，保证叠字对比度。"""
    w, h = im.size
    top = int(h * top_ratio)
    grad = Image.new("L", (1, h), 0)
    for y in range(top, h):
        t = (y - top) / max(1, h - top)
        grad.putpixel((0, y), int(bottom_alpha * (t ** 1.25)))
    layer = Image.new("RGBA", im.size, (4, 10, 20, 255))
    layer.putalpha(grad.resize(im.size))
    return Image.alpha_composite(im.convert("RGBA"), layer)


def overlay(base, out, kicker, title, lines, brand="数解AI", index=2):
    im = Image.open(base).convert("RGB")
    im = scrim(im)
    d = ImageDraw.Draw(im)
    W, H = im.size

    # 页眉品牌
    d.text((PAD, 48), brand, font=font(34, index), fill=BRAND)

    # 底部文字块（自下而上排版，再整体落位）
    fl_kick, fl_title, fl_line = font(34, index), font(int(W * 0.062), index), font(38, index)
    gap_kick, gap_line = 26, 20
    block = fl_kick.size + gap_kick + fl_title.size + 34
    block += len(lines) * (fl_line.size + gap_line)
    y = H - PAD - block

    d.text((PAD, y), kicker, font=fl_kick, fill=ACCENT)
    y += fl_kick.size + gap_kick
    d.line([(PAD, y - 12), (PAD + 96, y - 12)], fill=ACCENT, width=5)

    d.text((PAD, y), title, font=fl_title, fill=INK)
    y += fl_title.size + 34

    for ln in lines:
        d.text((PAD, y), ln, font=fl_line, fill=DIM)
        y += fl_line.size + gap_line

    im.convert("RGB").save(out, "PNG")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kicker", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--line", action="append", default=[])
    ap.add_argument("--brand", default="数解AI")
    a = ap.parse_args()
    print("saved:", overlay(a.base, a.out, a.kicker, a.title, a.line, a.brand))
