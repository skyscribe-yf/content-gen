#!/usr/bin/env python3
"""V4.1 KV 跨层复用脚本图：01 890 vs 4倍 / 02 短名单 / 03 三刀 / 04 Replay。

数字白名单（与正文一致）：890、1/4、1/8、128、437、512、16384、2048、8。
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
MUTED = "#6B7C8F"
PALE_BLUE = "#DCEAF4"
PALE_YELLOW = "#FFF1C7"
PALE_ORANGE = "#FCE1D9"
GRAY = "#9AA7B4"
WHITE = "#FFFFFF"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


F_TITLE = font(42, True)
F_SUB = font(26, True)
F_BODY = font(24)
F_SMALL = font(19)
F_BIG = font(48, True)
F_NUM = font(64, True)


def new_canvas(size=(1600, 900)):
    im = Image.new("RGB", size, BG)
    return im, ImageDraw.Draw(im)


def centered(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill=INK):
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2), text, font=fnt, fill=fill)


def rounded(draw: ImageDraw.ImageDraw, box, radius=22, fill=PALE_BLUE, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def chart_01():
    """890 字节 vs 上一代 Flash 约 4 倍"""
    im, d = new_canvas()
    centered(d, (800, 70), "每个词的全局账：890 字节", F_TITLE, INK)
    centered(d, (800, 125), "大约是上一代 Flash 的 1/4", F_BODY, MUTED)

    # 左：上一代
    rounded(d, (80, 200, 760, 780), fill=WHITE, outline=PALE_BLUE, width=3)
    centered(d, (420, 250), "上一代 V4-Flash", F_SUB, MUTED)
    d.rectangle([180, 320, 660, 700], fill=PALE_ORANGE, outline=ORANGE, width=3)
    centered(d, (420, 470), "约 4 倍", F_NUM, ORANGE)
    centered(d, (420, 560), "同一套全局账更厚", F_BODY, INK)

    # 右：V4.1
    rounded(d, (840, 200, 1520, 780), fill=WHITE, outline=PALE_BLUE, width=3)
    centered(d, (1180, 250), "V4.1 Flash 全局账", F_SUB, MUTED)
    d.rectangle([1040, 480, 1320, 700], fill=PALE_BLUE, outline=BLUE, width=3)
    centered(d, (1180, 560), "890", F_NUM, BLUE)
    centered(d, (1180, 640), "字节 / token", F_BODY, INK)

    centered(d, (800, 850), "对照物是上一代 Flash，不是「四十层四十本账」", F_SUB, ORANGE)
    im.save(ROOT / "01-kv-890.png")


def chart_02():
    """第一层筛短名单 → 后面的层只在短名单里找"""
    im, d = new_canvas()
    centered(d, (800, 70), "第一层筛短名单，后面的层只在短名单里找", F_TITLE, INK)
    centered(d, (800, 125), "不再对着整本仓库重新建账", F_BODY, MUTED)

    # 仓库
    rounded(d, (60, 200, 520, 780), fill=WHITE, outline=PALE_BLUE, width=3)
    centered(d, (290, 250), "整本仓库", F_SUB, INK)
    for i in range(8):
        y = 310 + i * 50
        d.rectangle([100, y, 480, y + 36], fill=PALE_YELLOW if i in (1, 3, 6) else "#EEF3F7")
        label = "相关文件" if i in (1, 3, 6) else "其他文件"
        centered(d, (290, y + 18), label, F_SMALL, ORANGE if i in (1, 3, 6) else MUTED)

    # 箭头
    d.polygon([(540, 470), (620, 440), (620, 500)], fill=BLUE)

    # 短名单
    rounded(d, (640, 260, 1040, 720), fill=PALE_BLUE, outline=BLUE, width=3)
    centered(d, (840, 310), "短名单", F_SUB, BLUE)
    centered(d, (840, 370), "Top-512", F_BIG, BLUE)
    centered(d, (840, 450), "第一层筛过的", F_BODY, INK)
    centered(d, (840, 500), "可能相关的位置", F_BODY, INK)
    centered(d, (840, 600), "候选池最多 16,384", F_SMALL, MUTED)
    centered(d, (840, 640), "2,048 块 × 8", F_SMALL, MUTED)

    # 箭头
    d.polygon([(1060, 470), (1140, 440), (1140, 500)], fill=BLUE)

    # 后面的层
    rounded(d, (1160, 260, 1540, 720), fill=PALE_YELLOW, outline=ORANGE, width=3)
    centered(d, (1350, 330), "后面的层", F_SUB, ORANGE)
    centered(d, (1350, 430), "只在名单里找", F_BODY, INK)
    centered(d, (1350, 500), "不再扫全仓库", F_BODY, INK)
    centered(d, (1350, 600), "有的连名单都抄", F_SMALL, MUTED)
    centered(d, (1350, 640), "有的只抄账本再挑", F_SMALL, MUTED)

    im.save(ROOT / "02-shortlist.png")


def chart_03():
    """三刀叠成 890"""
    im, d = new_canvas()
    centered(d, (800, 70), "890 字节是三刀合计，不是一刀砍出来的", F_TITLE, INK)
    centered(d, (800, 125), "跨层复用是主刀，另外两刀后文交代", F_BODY, MUTED)

    cards = [
        ("刀 1 主刀", "跨层复用", "第一层筛短名单\n后面的层只在名单里找", PALE_BLUE, BLUE),
        ("刀 2", "FP4 主账", "格子改成 4 位\n相对 FP8 近乎再半", PALE_YELLOW, ORANGE),
        ("刀 3", "窗口不落盘", "最近 128 词重放\n持久化约收到 1/8", PALE_ORANGE, ORANGE),
    ]
    cw, gap, x0, y0 = 440, 50, 90, 220
    for i, (tag, title, body, pale, color) in enumerate(cards):
        x = x0 + i * (cw + gap)
        rounded(d, (x, y0, x + cw, y0 + 500), fill=pale, outline=color, width=3)
        d.rectangle([x, y0, x + cw, y0 + 14], fill=color)
        centered(d, (x + cw / 2, y0 + 70), tag, F_SMALL, MUTED)
        centered(d, (x + cw / 2, y0 + 150), title, F_BIG, color)
        lines = body.split("\n")
        for j, line in enumerate(lines):
            centered(d, (x + cw / 2, y0 + 280 + j * 50), line, F_BODY, INK)
        if i < 2:
            centered(d, (x + cw + gap / 2, y0 + 220), "+", F_BIG, GRAY)

    centered(d, (800, 800), "三刀叠完：全局账 890 字节 / token", F_SUB, BLUE)
    im.save(ROOT / "03-three-cuts.png")


def chart_04():
    """窗口账不落盘，最近 128 词重放"""
    im, d = new_canvas()
    centered(d, (800, 70), "窗口账不落盘，需要时现场重放", F_TITLE, INK)
    centered(d, (800, 125), "滑动窗口 128 个词 · 890 说的是全局账，不含这截持久化", F_BODY, MUTED)

    # 长条：历史
    rounded(d, (80, 280, 1520, 480), fill=WHITE, outline=PALE_BLUE, width=3)
    d.rectangle([100, 330, 1180, 430], fill="#EEF3F7")
    centered(d, (640, 380), "已经读过的词（全局账 890 字节 / token）", F_BODY, MUTED)
    d.rectangle([1200, 330, 1500, 430], fill=PALE_YELLOW, outline=ORANGE, width=3)
    centered(d, (1350, 380), "最近 128 词", F_SUB, ORANGE)

    # 下方两列
    rounded(d, (80, 540, 760, 820), fill=PALE_BLUE, outline=BLUE, width=3)
    centered(d, (420, 600), "全局账", F_SUB, BLUE)
    centered(d, (420, 670), "写入持久化", F_BODY, INK)
    centered(d, (420, 730), "相对 V1 约小 437 倍", F_SMALL, MUTED)

    rounded(d, (840, 540, 1520, 820), fill=PALE_YELLOW, outline=ORANGE, width=3)
    centered(d, (1180, 600), "窗口账", F_SUB, ORANGE)
    centered(d, (1180, 670), "不落盘，用时重放 128 词", F_BODY, INK)
    centered(d, (1180, 730), "持久化 KV 约收到 1/8", F_SMALL, MUTED)

    im.save(ROOT / "04-replay.png")


if __name__ == "__main__":
    chart_01()
    chart_02()
    chart_03()
    chart_04()
    print("charts done")
