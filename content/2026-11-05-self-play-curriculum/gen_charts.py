#!/usr/bin/env python3
"""《AI 自己出题自己考》配图 01/02/03（PIL 直绘，风格对齐 2026-10-31 篇）。

数字来源（正文改动数字须同步此文件，全部一手核对于 arXiv 全文/摘要）：
  01 AZR 自循环：出题 → 代码执行器验证 → 解题 → 回炉 RL 更新（arXiv:2505.03335v3）
  02 三类任务：演绎/溯因/归纳，任务三元组 (程序, 输入, 输出)（同上 §3.2）
  03 零数据反超：平均 +1.8（vs 几万道人类题的 zero-setting 模型）、
     代码域 +0.3（vs 专家标注数据模型）、3B/7B/14B OOD 增益 +5.7/+10.2/+13.2（同上 §4.2）
  04 skill-sp 为 AI 概念图（禁数字禁中文），不走本脚本。
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
LIGHT = "#E8EEF5"
GREEN = "#2A9D8F"

FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def font(size: int, bold: bool = False):
    for p in ([FONT_BOLD, FONT_REG] if bold else [FONT_REG, FONT_BOLD]):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def header(d, title, sub=None):
    d.text((72, 52), title, font=font(42, True), fill=INK)
    if sub:
        d.text((72, 112), sub, font=font(26), fill=GREY)


def footer(d, w, h, text):
    d.line([(72, h - 78), (w - 72, h - 78)], fill=GRID, width=2)
    d.text((72, h - 64), text, font=font(22), fill=GREY)


def arrow(d, x0, y0, x1, y1, color=GREY, w=5, head=18):
    d.line([(x0, y0), (x1, y1)], fill=color, width=w)
    import math
    ang = math.atan2(y1 - y0, x1 - x0)
    for da in (2.6, -2.6):
        d.line([(x1, y1),
                (x1 - head * math.cos(ang + da), y1 - head * math.sin(ang + da))],
               fill=color, width=w)


def box(d, xy, title, sub=None, fill=LIGHT, edge=BLUE, tcol=INK, r=14):
    d.rounded_rectangle(xy, radius=r, fill=fill, outline=edge, width=3)
    x0, y0, x1, y1 = xy
    cx = (x0 + x1) / 2
    if sub:
        d.text((cx, (y0 + y1) / 2 - 26), title, font=font(30, True), fill=tcol, anchor="mm")
        d.text((cx, (y0 + y1) / 2 + 22), sub, font=font(21), fill=GREY, anchor="mm")
    else:
        d.text((cx, (y0 + y1) / 2), title, font=font(30, True), fill=tcol, anchor="mm")


def fig_loop():
    """01 AZR 自循环：出题 → 执行器验证 → 解题 → 回炉。"""
    W, H = 1600, 900
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    header(d, "Absolute Zero 的自循环：一个模型，两个角色",
           "唯一的外部是代码执行器——它只回答「输出对不对」")

    bw, bh, y = 300, 150, 300
    xs = [90, 460, 830, 1200]
    specs = [
        ("出题 proposer", "生成三类推理题", LIGHT, BLUE),
        ("代码执行器", "验证题合法+答案对错", "#FDF1E7", ORANGE),
        ("解题 solver", "解出题、拿奖励", LIGHT, BLUE),
        ("回炉 RL 更新", "同一套权重变强", "#E7F4F2", GREEN),
    ]
    for x, (t, s, f, e) in zip(xs, specs):
        box(d, [x, y, x + bw, y + bh], t, s, fill=f, edge=e)
    for i in range(3):
        arrow(d, xs[i] + bw + 8, y + bh / 2, xs[i + 1] - 8, y + bh / 2, color=GREY, w=6)

    # 回环：从回炉绕回出题
    ry = y + bh + 90
    d.line([(xs[3] + bw / 2, y + bh + 6), (xs[3] + bw / 2, ry)], fill=GREEN, width=6)
    d.line([(xs[3] + bw / 2, ry), (xs[0] + bw / 2, ry)], fill=GREEN, width=6)
    arrow(d, xs[0] + bw / 2, ry, xs[0] + bw / 2, y + bh + 8, color=GREEN, w=6)
    d.text(((xs[0] + xs[3]) / 2 + bw / 2, ry - 44), "更强的模型，出更难的题",
           font=font(28, True), fill=GREEN, anchor="mm")

    # 底部注：人类只剩什么
    d.rounded_rectangle([90, 640, W - 90, 760], radius=14, fill="#FFFFFF", outline=GRID, width=2)
    d.text((120, 672), "人类提供的全部：一个冷启动的基座 + 一个代码执行器", font=font(30, True), fill=INK)
    d.text((120, 716), "题目、答案、难度筛选，全部由模型自己完成", font=font(24), fill=GREY)

    footer(d, W, H, "机制据 arXiv:2505.03335v3（Absolute Zero，2025-10 修订）；图中无数字，结构为示意")
    im.save(ROOT / "01-az-loop.png")
    return im


def fig_tasks():
    """02 三类任务：任务三元组 (程序, 输入, 输出) 的三个推断方向。"""
    W, H = 1600, 900
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    header(d, "出的题只有三类：把 (程序, 输入, 输出) 遮掉一个",
           "代码执行器同时当出题人和阅卷人——跑一遍，真假自分")

    cols = [
        ("演绎", ["程序", "输入"], "输出", "给程序和输入，猜输出"),
        ("溯因", ["程序", "输出"], "输入", "给程序和输出，反推输入"),
        ("归纳", ["输入", "输出"], "程序", "给输入输出对，反推程序"),
    ]
    cw = 440
    gap = (W - 140 - cw * 3) / 2
    for i, (name, givens, target, desc) in enumerate(cols):
        x0 = 70 + i * (cw + gap)
        cx = x0 + cw / 2
        d.text((cx, 210), name, font=font(40, True), fill=BLUE, anchor="mm")
        d.text((cx, 262), desc, font=font(23), fill=GREY, anchor="mm")
        # 已知两个
        for j, g in enumerate(givens):
            box(d, [cx - 150, 310 + j * 96, cx + 150, 310 + j * 96 + 74], g, fill=LIGHT, edge=BLUE)
        # 箭头
        arrow(d, cx, 310 + 96 + 82, cx, 560, color=GREY, w=6)
        # 待推断的一个（问号）
        d.rounded_rectangle([cx - 150, 566, cx + 150, 648], radius=14, fill="#FDF1E7", outline=ORANGE, width=3)
        d.text((cx - 92, 607), target, font=font(30, True), fill=INK, anchor="mm")
        d.text((cx + 96, 607), "？", font=font(38, True), fill=ORANGE, anchor="mm")
        if i < 2:
            d.text((x0 + cw + gap / 2, 470), "或", font=font(26), fill=GREY, anchor="mm")

    d.text((W / 2, 742), "三类题共用同一个验证器：程序跑一遍，输出对不上就判错",
           font=font(26, True), fill=INK, anchor="mm")
    footer(d, W, H, "任务类型据 arXiv:2505.03335v3 §3.2（deduction / abduction / induction）")
    im.save(ROOT / "02-three-tasks.png")
    return im


def fig_zero():
    """03 零数据反超：领先分数 + 规模增益。"""
    W, H = 1600, 900
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    header(d, "零人类数据，反超 1.8 分；模型越大，自练收益越大",
           "论文自报数（arXiv:2505.03335v3，Qwen2.5 系列基座），非第三方实测")

    # 左：领先分数
    d.text((250, 200), "反超「用人类题训的模型」", font=font(28, True), fill=INK, anchor="mm")
    left = [("平均（zero-setting 对比）", 1.8, "领先 1.8 分"),
            ("代码域（对比专家标注数据）", 0.3, "领先 0.3 分")]
    for i, (name, v, tag) in enumerate(left):
        y = 270 + i * 150
        d.text((90, y), name, font=font(24), fill=GREY)
        bw = v / 2.0 * 620
        d.rounded_rectangle([90, y + 40, 90 + max(bw, 26), y + 96], radius=8, fill=BLUE)
        d.text((90 + max(bw, 26) + 16, y + 68), tag, font=font(30, True), fill=BLUE, anchor="lm")
    d.text((250, 590), "零道人类题", font=font(30, True), fill=ORANGE, anchor="mm")
    d.text((250, 634), "vs 几万道人工题", font=font(22), fill=GREY, anchor="mm")

    d.line([(800, 180), (800, 800)], fill=GRID, width=2)

    # 右：规模增益
    d.text((1200, 200), "自练带来的 OOD 增益", font=font(28, True), fill=INK, anchor="mm")
    bars = [("3B", 5.7), ("7B", 10.2), ("14B", 13.2)]
    base, top = 800, 280
    vmax = 14.0
    for i, (name, v) in enumerate(bars):
        x = 930 + i * 190
        h = v / vmax * 420
        d.rounded_rectangle([x, base - h, x + 120, base], radius=8, fill=GREEN if i == 2 else BLUE)
        d.text((x + 60, base - h - 34), f"+{v}", font=font(32, True), fill=INK, anchor="mm")
        d.text((x + 60, base + 36), name, font=font(28, True), fill=GREY, anchor="mm")
    d.text((1200, 640), "基座越大，自己练自己的回报越高", font=font(26, True), fill=INK, anchor="mm")
    d.text((1200, 684), "另一发现：代码先验放大推理（Coder 基座练完反超 0.7 分）",
           font=font(22), fill=GREY, anchor="mm")

    footer(d, W, H, "数据：arXiv:2505.03335v3 §4.2（2025-10 修订版全文核对）")
    im.save(ROOT / "03-zero-data.png")
    return im


if __name__ == "__main__":
    fig_loop()
    fig_tasks()
    fig_zero()
    print("01-az-loop.png / 02-three-tasks.png / 03-zero-data.png 已生成")
