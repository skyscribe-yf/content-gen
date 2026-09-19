#!/usr/bin/env python3
"""《GAN 一步就能出图，为什么输给了要跑 50 步的扩散？》数字配图（PIL 直绘）。

风格对齐 2026-09-13~09-16 各篇 gen_charts.py。

数字来源（正文改动数字须同步此文件）：
  01-steps：SDXL 官方口径 50 步 → SDXL-Turbo 1 步、A100 207ms（Stability AI, 2023-11-28）；
           阿里智能引擎 2 步蒸馏：Qwen-Image-2512 从 80-100 步前向压到 2 步、40 倍（量子位 2026-01-30）。
  02-js-gradient：GAN 最优判别器代入后 C(G)=2·JSD-2log2；分布不重叠时 JSD=log2、梯度为 0
            （Goodfellow et al., 2014；Arjovsky & Bottou, 2017）。
  03-timeline：2014 GAN → 2020 DDPM → 2021 ADM → 2023 ADD/SDXL-Turbo → 2024 DMD2 → 2025 R3GAN → 2026 阿里 2 步。
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG = "#F8FAFC"
INK = "#17324D"
BLUE = "#0F4C81"
CYAN = "#55C9EA"
YELLOW = "#F6BD60"
ORANGE = "#E76F51"
GREEN = "#2A9D8F"
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


def draw_steps() -> None:
    """步数对比：GAN 1 次前向 vs 扩散 50 步，以及蒸馏之后回到 1-2 步。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((72, 46), "出图要几步：GAN 一次前向，扩散要跑 50 步", font=font(40, True), fill=INK)
    d.text(
        (72, 104),
        "SDXL 官方口径 50 步（Stability AI, 2023-11）；蒸馏之后扩散回到 1–2 步",
        font=font(24),
        fill=GREY,
    )

    rows = [
        ("GAN", 1, "1 次前向", BLUE),
        ("SDXL（扩散）", 50, "50 步", ORANGE),
        ("SDXL-Turbo", 1, "1 步 · A100 单张 207ms", GREEN),
        ("Qwen-Image Turbo", 2, "2 步 · 80–100 步压缩 40 倍", GREEN),
    ]

    left, right = 470, W - 240
    top, row_h, bar_h = 210, 150, 52
    scale = (right - left) / 50.0

    # 分组标签（左侧，垂直居中于组）
    d.text((72, top + 10), "原生", font=font(28, True), fill=GREY)
    d.text((72, top + 2 * row_h + 10), "蒸馏后", font=font(28, True), fill=GREEN)

    for i, (name, v, lab, color) in enumerate(rows):
        y = top + i * row_h
        f = font(26, True)
        tw = d.textlength(name, font=f)
        d.text((left - 24 - tw, y + (bar_h - 30) / 2), name, font=f, fill=INK)

        bw = max(scale * v, 10)
        d.rounded_rectangle((left, y, left + bw, y + bar_h), radius=10, fill=color)

        d.text((left + bw + 18, y + 2), lab, font=font(26, True), fill=color)

    # 分组分隔线
    sep_y = top + 2 * row_h - 34
    d.line((72, sep_y, W - 72, sep_y), fill=GRID, width=2)

    d.text(
        (72, H - 96),
        "GAN 靠「对抗」一次出图；扩散用 50 步换稳定。蒸馏把步数压回 1–2 步时，",
        font=font(24),
        fill=GREY,
    )
    d.text(
        (72, H - 58),
        "判别器又被请回来当裁判——这就是 2023 年之后发生的事。",
        font=font(24),
        fill=GREY,
    )

    img.save(ROOT / "01-steps.png")
    print("saved 01-steps.png", img.size)


def gaussian(x: float, mu: float, sigma: float) -> float:
    return math.exp(-((x - mu) ** 2) / (2 * sigma * sigma))


def draw_js_gradient() -> None:
    """左：分布不重叠；右：JS 随距离的平坦曲线 + 梯度为 0。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((72, 46), "分布不重叠时，JS 散度是个常数，梯度是零", font=font(40, True), fill=INK)
    d.text(
        (72, 104),
        "GAN 博弈等价于最小化 JS 散度；两个分布离得越远，它反而越没有方向可给",
        font=font(24),
        fill=GREY,
    )

    # ---- 左图：两条分离的高斯 ----
    lx0, ly0, lw, lh = 110, 220, 480, 380
    d.rectangle((lx0, ly0, lx0 + lw, ly0 + lh), outline=GRID, width=2)

    def to_px(x, y, x0, y0, w, h):
        return x0 + x * w, y0 + h - y * h

    for mu, color, label in [(-1.9, BLUE, "真实数据"), (1.9, ORANGE, "生成分布")]:
        pts = []
        for i in range(241):
            x = -3.2 + 6.4 * i / 240
            y = gaussian(x, mu, 0.55)
            pts.append(to_px((x + 3.2) / 6.4, y * 1.15, lx0, ly0, lw, lh))
        d.line(pts, fill=color, width=5)
        d.text((lx0 + (lw * 0.18 if mu < 0 else lw * 0.66), ly0 + 24), label, font=font(26, True), fill=color)

    d.line((lx0, ly0 + lh, lx0 + lw, ly0 + lh), fill=INK, width=2)
    d.text((lx0, ly0 + lh + 18), "两个分布完全不重叠（训练开局几乎必然如此）", font=font(24), fill=GREY)

    # ---- 右图：JS 随距离的曲线 ----
    rx0, ry0 = 690, 220
    d.rectangle((rx0, ry0, rx0 + lw, ry0 + lh), outline=GRID, width=2)

    pts = []
    for i in range(241):
        t = i / 240  # 0..1 距离
        # 距离小 → JS 小；距离大 → 平台 log2
        js = math.log(2) * (1 - math.exp(-6 * t))
        pts.append(to_px(t, js / 1.05, rx0, ry0, lw, lh))
    d.line(pts, fill=BLUE, width=5)

    y_log2 = ry0 + lh - (math.log(2) / 1.05) * lh
    d.line((rx0, y_log2, rx0 + lw, y_log2), fill=ORANGE, width=2)
    d.text((rx0 + 12, y_log2 - 44), "平台区：JS = log 2（常数）", font=font(24, True), fill=ORANGE)
    for txt, f, c, dy in [("这里梯度 = 0", font(30, True), ORANGE, 14), ("判别器全对，生成器收不到信号", font(22), GREY, 54)]:
        tw = d.textlength(txt, font=f)
        d.text((rx0 + lw - 14 - tw, y_log2 + dy), txt, font=f, fill=c)
    d.line((rx0, ry0 + lh, rx0 + lw, ry0 + lh), fill=INK, width=2)
    d.text((rx0, ry0 + lh + 18), "两个分布的距离 →", font=font(24), fill=GREY)

    d.text(
        (72, H - 96),
        "GAN 的训练本质上是在拉近两个分布；可开局阶段它们几乎不重叠，",
        font=font(24),
        fill=GREY,
    )
    d.text(
        (72, H - 58),
        "JS 恒等于 log 2，梯度为零——训练不稳定与模式崩溃的数学根源。",
        font=font(24),
        fill=GREY,
    )

    img.save(ROOT / "02-js-gradient.png")
    print("saved 02-js-gradient.png", img.size)


def draw_timeline() -> None:
    """时间线：GAN 的兴衰与回归。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((72, 46), "十二年，判别器从主角到被嫌弃，再被请回来", font=font(40, True), fill=INK)
    d.text((72, 104), "生成模型的一条主线：对抗登场 → 扩散接棒 → 对抗蒸馏回归", font=font(24), fill=GREY)

    nodes = [
        ("2014", "GAN 论文", "酒吧争论后的一夜之作", BLUE, "up"),
        ("2020", "DDPM", "扩散走上台前", GREY, "down"),
        ("2021", "ADM", "论文标题：击败 GAN", ORANGE, "up"),
        ("2023", "SDXL-Turbo", "50 步 → 1 步，207ms", GREEN, "down"),
        ("2024", "DMD2", "GAN 损失加进蒸馏", GREEN, "up"),
        ("2025", "R3GAN", "练稳了，但没成主流", GREY, "down"),
        ("2026", "阿里 2 步蒸馏", "模式崩溃 → 请回判别器", ORANGE, "up"),
    ]

    y0 = 470
    x0, x1 = 120, W - 120
    d.line((x0, y0, x1, y0), fill=INK, width=4)

    step = (x1 - x0) / (len(nodes) - 1)
    for i, (year, name, note, color, side) in enumerate(nodes):
        x = x0 + i * step
        d.ellipse((x - 11, y0 - 11, x + 11, y0 + 11), fill=color, outline=BG, width=3)
        ty = y0 - 132 if side == "up" else y0 + 46
        d.line((x, y0 - 12 if side == "up" else y0 + 12, x, ty + 26 if side == "up" else ty - 6), fill=GRID, width=2)
        for txt, f, c, dy in [(year, font(26, True), color, 0), (name, font(24, True), INK, 34), (note, font(19), GREY, 64)]:
            tw = d.textlength(txt, font=f)
            lx = min(max(24, x - tw / 2), W - 24 - tw)
            d.text((lx, ty + dy), txt, font=f, fill=c)

    d.text(
        (72, H - 96),
        "同一套「对抗」结构，换了一身衣服又回到最快的生成模型里；",
        font=font(24),
        fill=GREY,
    )
    d.text(
        (72, H - 58),
        "从 GAN 到 actor/critic、到 RSI，生成与评判的交替，一直都在。",
        font=font(24),
        fill=GREY,
    )

    img.save(ROOT / "03-timeline.png")
    print("saved 03-timeline.png", img.size)


if __name__ == "__main__":
    draw_steps()
    draw_js_gradient()
    draw_timeline()
