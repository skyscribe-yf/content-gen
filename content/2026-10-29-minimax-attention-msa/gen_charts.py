#!/usr/bin/env python3
"""《1M 上下文只算 2048 个 token》配图（PIL 直绘，风格对齐 2026-09-24-four-arch-kv）。

数字来源（正文改动数字须同步此文件）：
  01 三代：Text-01 456B/45.9B、1M（arXiv:2501.08313）；M2 229.9B/9.8B、192K（arXiv:2605.26494）；
           M3 428B/23B、1M（官方发布 2026-06-01）
  02 机制：Bk=128、k=16、16×128=2,048（arXiv:2606.13392 §3）
  03 账本：1M 处 FLOPs 28.4×、H800 prefill 14.2×、decode 7.6×（同上 §5.4）
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


def title(d, text, sub=None):
    d.text((72, 46), text, font=font(40, True), fill=INK)
    if sub:
        d.text((72, 104), sub, font=font(24), fill=GREY)


# ---------------------------------------------------------------- 01 三次转向
def chart_turns() -> None:
    W, H = 1254, 720
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title(d, "三次转向：先押线性，再退回全量，最后只挑块",
          "同一家公司，22 个月里对注意力做了三次方向性选择")

    cards = [
        ("2025-01", "Text-01", "7:1 线性 + softmax", "456B / 45.9B", "1M", BLUE, "省 KV，但检索弱"),
        ("2025-10", "M2", "GQA 全注意力", "229.9B / 9.8B", "192K", ORANGE, "多跳推理掉，退回全量"),
        ("2026-06", "M3", "MSA 块稀疏", "428B / 23B", "1M", BLUE, "保留 softmax，只挑块"),
    ]

    cw, gap, top = 330, 42, 190
    for i, (date, name, design, params, ctx, color, note) in enumerate(cards):
        x = 72 + i * (cw + gap)
        d.rounded_rectangle((x, top, x + cw, top + 380), radius=16, fill="#FFFFFF", outline=GRID, width=2)
        d.rounded_rectangle((x, top, x + cw, top + 8), radius=4, fill=color)
        d.text((x + 24, top + 34), date, font=font(23), fill=GREY)
        d.text((x + 24, top + 68), name, font=font(40, True), fill=INK)
        d.text((x + 24, top + 132), design, font=font(26, True), fill=color)
        d.text((x + 24, top + 186), "总参 / 激活", font=font(21), fill=GREY)
        d.text((x + 24, top + 214), params, font=font(28, True), fill=INK)
        d.text((x + 24, top + 268), "上下文", font=font(21), fill=GREY)
        d.text((x + 24, top + 296), ctx, font=font(28, True), fill=INK)
        d.text((x + 24, top + 344), note, font=font(20), fill=GREY)

    for i in range(2):
        ax = 72 + (i + 1) * cw + i * gap + 8
        ay = top + 190
        d.line((ax, ay, ax + 26, ay), fill=GREY, width=4)
        d.polygon([(ax + 26, ay - 9), (ax + 42, ay), (ax + 26, ay + 9)], fill=GREY)

    d.text((72, H - 84), "激活从 45.9B 掉到 9.8B，又回到 23B；上下文从 1M 掉到 192K，再回到 1M。",
           font=font(23), fill=GREY)
    d.text((72, H - 48), "第三次不是回到线性，也不是固定滑窗——softmax 留着，只把「看谁」交给索引分支。",
           font=font(23), fill=GREY)

    img.save(ROOT / "01-three-turns.png")
    print("saved 01-three-turns.png", img.size)


# ---------------------------------------------------------------- 02 两分支
def chart_branches() -> None:
    W, H = 1254, 900
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title(d, "MSA 怎么选：先选块，再算精确注意力",
          "Index Branch 决定看哪儿，Main Branch 只对选中的块做 softmax")

    # 上：索引分支
    d.text((72, 156), "① 索引分支：每个 group 一个 index query 头，全局共用一个 index key 头",
           font=font(24, True), fill=INK)

    bx, by, bw, bh, bgap = 72, 206, 62, 34, 10
    for i in range(16):
        x = bx + i * (bw + bgap)
        d.rounded_rectangle((x, by, x + bw, by + bh), radius=6, fill=LIGHT, outline=GRID)
    d.text((72, by + 46), "逐 token 打分（极轻，参数可忽略）", font=font(20), fill=GREY)

    # max-pool 箭头
    d.line((72, by + 96, 72 + 8 * (bw + bgap), by + 96), fill=GRID, width=3)
    d.text((72 + 8 * (bw + bgap) + 18, by + 86), "按 128 token 一块 max-pool", font=font(21), fill=GREY)

    # 块行
    by2 = by + 128
    sel = {0, 2, 3, 5, 8, 9, 11, 14}
    for i in range(16):
        x = bx + i * (bw + bgap)
        on = i in sel
        d.rounded_rectangle((x, by2, x + bw, by2 + bh + 10), radius=6,
                            fill=BLUE if on else LIGHT, outline=GRID)
    d.text((72, by2 + 60), "示意：被选中的块进 top-16；本地块无条件常驻，不参与竞争",
           font=font(20), fill=GREY)

    # 下：主分支
    d.text((72, 462), "② 主分支：只对这些块做精确 softmax，注意力形式不变",
           font=font(24, True), fill=INK)

    my, mbh = 512, 92
    # 索引块（选中）
    for i in range(16):
        x = 72 + i * 52
        d.rounded_rectangle((x, my, x + 44, my + mbh), radius=7, fill=BLUE)
    d.text((72 + 16 * 52 + 8, my + 6), "16 块", font=font(24, True), fill=BLUE)
    d.text((72 + 16 * 52 + 8, my + 42), "× 128 token", font=font(21), fill=GREY)
    d.text((72 + 16 * 52 + 8, my + 70), "= 2,048", font=font(24, True), fill=ORANGE)

    # 本地块
    d.rounded_rectangle((72, my + mbh + 26, 72 + 44, my + mbh + 26 + 54), radius=7,
                        fill=ORANGE)
    d.text((132, my + mbh + 34), "本地块常驻：防止退化选择把 query 自己的邻域丢掉",
           font=font(21), fill=GREY)

    d.rounded_rectangle((72, H - 130, W - 72, H - 56), radius=14, fill="#FFFFFF", outline=GRID, width=2)
    d.text((96, H - 114), "每个 query 每层最多看 2,048 个 token；KV 缓存本身还在，少的是「看谁」。",
           font=font(23, True), fill=INK)

    img.save(ROOT / "02-msa-branches.png")
    print("saved 02-msa-branches.png", img.size)


# ---------------------------------------------------------------- 03 账本
def chart_budget() -> None:
    W, H = 1254, 700
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title(d, "28.4 倍是 FLOPs，不是墙钟",
          "1M 上下文、H800 实测算力节省（论文 §5.4 与摘要口径）")

    # 左：理论
    d.text((72, 176), "理论：注意力 FLOPs 少", font=font(24, True), fill=INK)
    top, bar_h = 232, 56
    maxw = 420
    scale = maxw / 28.4
    d.text((72, top), "全注意力 GQA 的 1/28.4", font=font(21), fill=GREY)
    bw = scale * 28.4
    d.rounded_rectangle((72, top + 44, 72 + bw, top + 44 + bar_h), radius=10, fill=BLUE)
    d.text((72 + bw + 16, top + 56), "28.4×", font=font(38, True), fill=BLUE)

    # 右：实测
    d.text((72, 418), "实测：墙钟只兑现一部分", font=font(24, True), fill=INK)
    rows = [("Prefill", 14.2, ORANGE), ("Decode", 7.6, BLUE)]
    s2 = 420 / 14.2
    for i, (name, v, color) in enumerate(rows):
        y = 470 + i * 78
        d.text((72, y + 12), name, font=font(23, True), fill=INK)
        d.rounded_rectangle((200, y, 200 + s2 * v, y + 46), radius=9, fill=color)
        d.text((200 + s2 * v + 14, y + 4), f"{v}×", font=font(30, True), fill=color)

    d.text((72, H - 66),
           "差额花在索引构建、top-k、query gather 和两段式 combine 上——省下的算力要先付手续费。",
           font=font(22), fill=GREY)
    d.text((72, H - 34), "另外：28.4× 是 109B 消融模型上的比值，生产 M3 是 428B。",
           font=font(22), fill=GREY)

    img.save(ROOT / "03-budget.png")
    print("saved 03-budget.png", img.size)


# ---------------------------------------------------------------- 04 残差
def chart_caveats() -> None:
    W, H = 1254, 640
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title(d, "MSA 与全注意力的差距：多数打平，检索略亏",
          "论文表 3，128K 上下文，MSA 减去全注意力（百分点）")

    rows = [
        ("HELMET-128K", "总体", -0.60, "46.53 → 45.93"),
        ("HELMET-128K", "Rerank / RAG", -2.10, "34.60 → 32.50"),
        ("RULER-128K", "总体", 0.12, "72.00 → 72.12"),
        ("RULER-128K", "CWE / FWE", -1.35, "46.35 → 45.00"),
    ]

    zero_x = 700
    scale = 110  # 1.0 个百分点 = 110px
    top = 200
    for i, (bench, item, val, detail) in enumerate(rows):
        y = top + i * 92
        d.text((72, y + 6), bench, font=font(22), fill=GREY)
        d.text((72, y + 36), item, font=font(27, True), fill=INK)

        d.line((zero_x, y - 6, zero_x, y + 66), fill=GRID, width=2)
        w = abs(val) * scale
        color = BLUE if val >= 0 else ORANGE
        if val >= 0:
            d.rounded_rectangle((zero_x, y + 12, zero_x + w, y + 60), radius=8, fill=color)
            d.text((zero_x + w + 14, y + 20), f"+{val:.2f}", font=font(26, True), fill=color)
        else:
            d.rounded_rectangle((zero_x - w, y + 12, zero_x, y + 60), radius=8, fill=color)
            d.text((zero_x - w - 96, y + 20), f"{val:.2f}", font=font(26, True), fill=color)
        d.text((zero_x + 150, y + 24), detail, font=font(21), fill=GREY)

    d.text((72, H - 76), "四条里三条是负的，最伤的是 Rerank / RAG（−2.10）。",
           font=font(22), fill=GREY)
    d.text((72, H - 42), "所以「1M 只算 2048 个 token」不是免费：省下来的算力，买了一点点检索精度。",
           font=font(22), fill=GREY)

    img.save(ROOT / "04-caveats.png")
    print("saved 04-caveats.png", img.size)


if __name__ == "__main__":
    assert 16 * 128 == 2048
    assert abs(28.4 / 14.2 - 2.0) < 0.05
    chart_turns()
    chart_branches()
    chart_budget()
    chart_caveats()
