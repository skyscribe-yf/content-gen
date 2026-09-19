#!/usr/bin/env python3
"""《AI 出图要跑 50 步，为什么砍到 10 步还清晰，砍到 1 步就糊了？》数字配图（PIL 直绘）。

风格对齐 2026-09-13~09-18 各篇 gen_charts.py。

数字来源（正文改动数字须同步此文件）：
  03-timeline：DDIM 2020（arXiv:2010.02502，论文口径 10x-50x 加速）；
    Consistency Models 2023-03（arXiv:2303.01469，一步/两步生成）；
    LCM 2023-10（arXiv:2310.04378，2~4 步、32 A100 GPU 小时）；
    SDXL-Turbo 2023-11-28（Stability AI 官方，1 步、A100 单张 207ms）；
    阿里 2 步蒸馏 2026-01-30（量子位，80-100 步压到 2 步、5 秒 4 张 2K）。

实验图 01/02 由 run_experiment.py 直接产出，不在本脚本内。
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


def tw(d, text, f):
    b = d.textbbox((0, 0), text, font=f)
    return b[2] - b[0]


def th(d, text, f):
    b = d.textbbox((0, 0), text, font=f)
    return b[3] - b[1]


def draw_timeline() -> None:
    """加速路线：跳步（改采样）→ 约束终点/重新训练（换目标）。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((72, 46), "想更快：先改采样器，后来干脆换掉训练目标", font=font(40, True), fill=INK)
    d.text((72, 106), "上半段还在「怎么少跑几步」，下半段已经在「一步就该到哪」", font=font(24), fill=GREY)

    items = [
        ("2020", "DDIM", "把 1000 步随机链\n改成确定性 ODE", "10×–50× 加速", "改采样器", BLUE),
        ("2023-03", "Consistency\nModels", "轨迹上任一点\n都要落到同一终点", "一步 / 两步生成", "换训练目标", ORANGE),
        ("2023-10", "LCM / LCM-LoRA", "把一致性约束\n做成通用 LoRA", "2~4 步 · 32 A100 小时", "换训练目标", ORANGE),
        ("2023-11", "SDXL-Turbo", "模仿老师之外\n再请回判别器", "1 步 · A100 207ms", "换训练目标", GREEN),
        ("2026-01", "阿里 2 步蒸馏", "Qwen-Image\n从 80–100 步压到 2 步", "5 秒 4 张 2K", "换训练目标", GREEN),
    ]

    f_year, f_name, f_how, f_num, f_tag = (
        font(26, True), font(30, True), font(22), font(24, True), font(20, True))
    PILL_H = 32

    n = len(items)
    left, right = 158, W - 158
    step_w = (right - left) / (n - 1)
    axis_y = 470

    d.line([(left - 40, axis_y), (right + 40, axis_y)], fill=GRID, width=4)
    d.polygon([(right + 40, axis_y - 11), (right + 68, axis_y), (right + 40, axis_y + 11)], fill=GREY)

    for i, (year, name, how, num, kind, color) in enumerate(items):
        x = left + i * step_w
        above = i % 2 == 0

        blocks = [(year, f_year, color, 8), (name, f_name, INK, 16),
                  (how, f_how, GREY, 24), (num, f_num, color, 14)]
        stack_h = sum(th(d, t, f) + g for t, f, _, g in blocks) + PILL_H
        for t, f, _, _ in blocks:
            if tw(d, t, f) / 2 > min(x, W - x):
                print(f"  ! 溢出画布: {t!r}")

        top = (axis_y - 34 - stack_h) if above else (axis_y + 46)

        r = 13
        d.ellipse([x - r, axis_y - r, x + r, axis_y + r], fill=color, outline="white", width=3)
        stem_top = top + stack_h if above else top
        d.line([(x, axis_y - r if above else axis_y + r), (x, stem_top)], fill=GRID, width=2)

        y = top
        for t, f, fill, gap in blocks:
            d.text((x, y), t, font=f, fill=fill, anchor="ma")
            y += th(d, t, f) + gap

        label_w = tw(d, kind, f_tag) + 26
        d.rounded_rectangle([x - label_w / 2, y, x + label_w / 2, y + PILL_H],
                            radius=16, outline=color, width=2)
        d.text((x, y + PILL_H / 2), kind, font=f_tag, fill=color, anchor="mm")

    d.text((W / 2, H - 62), "DDIM 之后，没有人再靠「调小步数」把模型做到 1 步——那件事只能重新训练",
           font=font(24, True), fill=INK, anchor="mm")
    img.save(ROOT / "03-timeline.png")
    print("03-timeline.png")


if __name__ == "__main__":
    draw_timeline()
