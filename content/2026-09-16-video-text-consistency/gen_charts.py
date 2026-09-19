#!/usr/bin/env python3
"""《AI 视频里的字为什么一帧一个样》数字配图（PIL 直绘）。

风格对齐 2026-09-13-grpo-math / 2026-09-14-reward-hacking / 2026-09-15-text-rendering。

数字来源（正文改动数字须同步此文件）：
  01-scores：T2VTextBench 主表（arXiv:2505.04946）10 个模型平均分（满分 1）。
  02-token-budget：Wan 2.1 技术报告 3D 因果 VAE 时空压缩 4×8×8（arXiv:2503.20314 图 5）；
                   8×8 空间压缩 → 32×32 像素的字压成 4×4=16 格。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG = "#F8FAFC"
INK = "#17324D"
BLUE = "#0F4C81"
CYAN = "#55C9EA"
YELLOW = "#F6BD60"
ORANGE = "#E76F51"
GREY = "#5B7186"
GRID = "#D9E2EC"

W, H = 1254, 940
FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def font(size: int, bold: bool = False):
    for p in (FONT_PATHS if bold else FONT_PATHS[1:] + FONT_PATHS[:1]):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# T2VTextBench 主表：10 个模型平均分（降序）
SCORES = [
    ("Sora", 0.37),
    ("Pika 2.1", 0.36),
    ("Hailuo", 0.35),
    ("Wan 2.1", 0.33),
    ("SD Video", 0.33),
    ("LTX Video", 0.20),
    ("Mochi-1", 0.19),
    ("Qingying", 0.17),
    ("Dreamina", 0.11),
    ("Kling", 0.01),
]


def draw_scores() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((72, 50), "10 个视频模型考「写字」，最高只有 0.37 分", font=font(40, True), fill=INK)
    d.text(
        (72, 108),
        "T2VTextBench：73 条提示词 × 人工评分（满分 1 分，arXiv:2505.04946 主表）",
        font=font(24),
        fill=GREY,
    )

    left, right = 300, W - 120
    top, row_h, bar_h = 190, 66, 36
    scale = (right - left) / 0.40  # 以 0.40 为满刻度，留头

    for i, (name, v) in enumerate(SCORES):
        y = top + i * row_h
        f = font(26, True)
        tw = d.textlength(name, font=f)
        d.text((left - 24 - tw, y + (bar_h - 30) / 2), name, font=f, fill=INK)

        color = BLUE if i == 0 else (ORANGE if i == len(SCORES) - 1 else "#8CA3B8")
        bw = max(scale * v, 3)
        d.rounded_rectangle((left, y, left + bw, y + bar_h), radius=8, fill=color)

        lab = f"{v:.2f}"
        d.text((left + bw + 16, y + 2), lab, font=font(26, True), fill=color if i in (0, len(SCORES) - 1) else INK)

    # 参考线：0.5
    x05 = left + scale * 0.5
    d.line((x05, top - 26, x05, top + 10 * row_h), fill=GRID, width=2)
    d.text((x05 + 10, top - 52), "0.5 参考线：没有人到", font=font(22), fill=GREY)

    d.text((72, H - 54), "最高 0.37（Sora），最低 0.01（Kling）——满分 1 分", font=font(24), fill=GREY)

    img.save(ROOT / "01-scores.png")
    print("saved 01-scores.png", img.size)


def draw_token_budget() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((72, 50), "一个字进模型前，先被压成 16 个格子", font=font(40, True), fill=INK)
    d.text(
        (72, 108),
        "3D 因果 VAE 8×8 空间压缩：笔画只有 2–3 像素宽，不到一个格子大（Wan 2.1，arXiv:2503.20314）",
        font=font(24),
        fill=GREY,
    )

    # 左上：原始 32×32 像素（渲染一个汉字到 32×32，再放大 8 倍）
    char = "福"
    src = Image.new("L", (32, 32), 255)
    sd = ImageDraw.Draw(src)
    gfont = font(30, True)
    bbox = sd.textbbox((0, 0), char, font=gfont)
    sd.text(
        ((32 - (bbox[2] - bbox[0])) / 2 - bbox[0], (32 - (bbox[3] - bbox[1])) / 2 - bbox[1]),
        char,
        font=gfont,
        fill=0,
    )
    orig = src.resize((256, 256), Image.NEAREST)

    pooled = src.resize((4, 4), Image.BOX).resize((256, 256), Image.NEAREST)

    x1, y1 = 110, 240
    x2 = x1 + 256 + 170
    img.paste(Image.merge("RGB", (orig, orig, orig)), (x1, y1))

    # 原始图上的 4×4 网格（= 压缩后的格子边界）
    for k in range(5):
        gx = x1 + k * 64
        gy = y1 + k * 64
        d.line((gx, y1, gx, y1 + 256), fill=ORANGE, width=2)
        d.line((x1, gy, x1 + 256, gy), fill=ORANGE, width=2)

    d.text((x1, y1 + 276), "原始：32×32 像素", font=font(28, True), fill=INK)
    d.text((x1, y1 + 316), "红格 = 压缩后的一格（8×8 像素）", font=font(22), fill=GREY)

    # 箭头
    ax = x1 + 256 + 30
    ay = y1 + 128
    d.line((ax, ay, ax + 100, ay), fill=INK, width=5)
    d.polygon([(ax + 100, ay - 14), (ax + 100, ay + 14), (ax + 128, ay)], fill=INK)
    d.text((ax - 6, ay - 52), "8×8 压缩", font=font(24, True), fill=INK)

    # 右：压缩后 4×4 格
    img.paste(Image.merge("RGB", (pooled, pooled, pooled)), (x2, y1))
    for k in range(5):
        gx = x2 + k * 64
        gy = y1 + k * 64
        d.line((gx, y1, gx, y1 + 256), fill=INK, width=2)
        d.line((x2, gy, x2 + 256, gy), fill=INK, width=2)

    d.text((x2, y1 + 276), "压缩后：4×4 = 16 个格子", font=font(28, True), fill=ORANGE)
    d.text((x2, y1 + 316), "每个格子记的是 8×8 像素的平均", font=font(22), fill=GREY)

    d.text(
        (72, H - 54),
        "而一段 5 秒 720p 视频，压完约 30 万个格子；时间维还要 4 帧并 1 帧",
        font=font(24),
        fill=GREY,
    )

    img.save(ROOT / "02-token-budget.png")
    print("saved 02-token-budget.png", img.size)


if __name__ == "__main__":
    draw_scores()
    draw_token_budget()
