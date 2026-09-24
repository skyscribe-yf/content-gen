#!/usr/bin/env python3
"""《同样 1M 上下文，KV 缓存差 15 倍》账本拆解图（PIL 直绘）。

风格对齐 2026-09-16-video-text-consistency/gen_charts.py（BG/BLUE/ORANGE 同一套）。

数字来源（正文改动数字须同步此文件）：
  DeepSeek-V4.1-Flash：890 B/token = 3 × 178 B + 356 B（L21 合并账），arXiv:2609.19969
  小米 HySparse2：2,560 B/token = 5 × 512 B，arXiv:2609.26368
  GLM-5.3-Flash：5,995 B/token = 11 × 545 B，Z.ai 2026-08-26 博客
  Qwen3.8-Flash-Next：13,056 B/token = 12 × 1,088 B，arXiv:2608.30320
  1M = 1,048,576 token；GB 一律 10 进制（13,056 B × 1,048,576 = 13.69 GB）
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG = "#F8FAFC"
INK = "#17324D"
BLUE = "#0F4C81"
ORANGE = "#E76F51"
GREY = "#5B7186"
GRID = "#D9E2EC"

W, H = 1254, 940
FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]

# (名称, 每层字节, 记账层数, 额外合并账字节, 每 token 总账, 1M 时 GB)
MODELS = [
    ("DeepSeek-V4.1-Flash", 178, 3, 356, 890, 0.93),
    ("小米 HySparse2", 512, 5, 0, 2_560, 2.69),
    ("GLM-5.3-Flash", 545, 11, 0, 5_995, 6.3),
    ("Qwen3.8-Flash-Next", 1_088, 12, 0, 13_056, 13.7),
]
TOKENS_1M = 1_048_576


def font(size: int, bold: bool = False):
    for p in (FONT_PATHS if bold else FONT_PATHS[1:] + FONT_PATHS[:1]):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def self_check() -> None:
    """一行可跑的断言：乘法关系与 GB 换算必须自洽。"""
    for name, per_layer, n_layer, extra, total, gb in MODELS:
        assert per_layer * n_layer + extra == total, (name, "乘积对不上")
        assert abs(total * TOKENS_1M / 1e9 - gb) < 0.02, (name, "GB 换算对不上", total * TOKENS_1M / 1e9)
    ratio = MODELS[-1][4] / MODELS[0][4]
    assert 14.5 < ratio < 15.0, ratio
    print(f"self-check ok：总账倍数 {ratio:.2f}×（正文口径 15 倍）")


def draw() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((72, 46), "同样的账，四家配方不同：差在几层记账", font=font(40, True), fill=INK)
    d.text(
        (72, 104),
        "每 token 总账 = 存 KV 的层数 × 每层每 token 字节数（1M = 1,048,576 token）",
        font=font(24),
        fill=GREY,
    )

    # 左面板：每层字节；右面板：每 token 总账
    lx, lw = 372, 280          # 左条起点 / 满刻度宽度（1,088 B）
    rx, rw = 760, 230          # 右条起点 / 满刻度宽度（13,056 B）
    top, row_h, bar_h = 200, 150, 46
    scale_l = lw / 1_088
    scale_r = rw / 13_056

    d.text((lx, top - 44), "每层每 token 字节", font=font(23, True), fill=GREY)
    d.text((rx, top - 44), "每 token 总账（1M 时 GB）", font=font(23, True), fill=GREY)

    for i, (name, per_layer, n_layer, extra, total, gb) in enumerate(MODELS):
        y = top + i * row_h
        d.text((72, y + 4), name, font=font(25, True), fill=INK)
        d.text((72, y + 40), f"{n_layer} 层记账", font=font(23), fill=GREY)

        color = ORANGE if i in (0, 3) else BLUE

        # 左：每层字节
        bw = max(scale_l * per_layer, 4)
        d.rounded_rectangle((lx, y, lx + bw, y + bar_h), radius=9, fill=color)
        d.text((lx + bw + 14, y + 8), f"{per_layer:,} B", font=font(25, True), fill=INK)
        d.text((lx + bw + 14, y + 40), f"× {n_layer} 层", font=font(23), fill=GREY)

        # 右：总账
        bw2 = max(scale_r * total, 4)
        c2 = ORANGE if i in (0, 3) else BLUE
        d.rounded_rectangle((rx, y, rx + bw2, y + bar_h), radius=9, fill=c2)
        lab = f"{total:,} B" + ("＋356 B" if extra else "")
        d.text((rx + bw2 + 14, y + 8), lab, font=font(25, True), fill=c2)
        d.text((rx + bw2 + 14, y + 40), f"{gb} GB @ 1M", font=font(23), fill=GREY)

    # 最省 / 最贵 标注（右对齐，避开副标题）
    gap = "最省 0.93 GB ↔ 最贵 13.7 GB：15 倍"
    d.text((W - 72 - d.textlength(gap, font=font(23, True)), 58), gap, font=font(23, True), fill=ORANGE)

    d.text(
        (72, H - 92),
        "差的不是量化位数：每层差 6 倍（178 ↔ 1,088），记账层数差 4 倍（3 ↔ 12），乘起来 24 倍，",
        font=font(23),
        fill=GREY,
    )
    d.text(
        (72, H - 58),
        "DeepSeek 解码器那本 356 B 合并账把它拉回 15 倍。",
        font=font(23),
        fill=GREY,
    )

    img.save(ROOT / "01-kv-account.png")
    print("saved 01-kv-account.png", img.size)


if __name__ == "__main__":
    self_check()
    draw()
