#!/usr/bin/env python3
"""持续学习贴图：AI 实景 + 脚本画精确数字。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
INK = (245, 250, 255)
DIM = (203, 213, 225)
GOLD = (255, 196, 64)
CYAN = (110, 231, 255)
RED = (255, 138, 128)
GREEN = (134, 239, 172)


def font(size):
    return ImageFont.truetype(FONT, size, index=2)


def scrim_bottom(im, top_ratio, alpha=230):
    w, h = im.size
    top = int(h * top_ratio)
    grad = Image.new("L", (1, h), 0)
    for y in range(top, h):
        t = (y - top) / max(1, h - top)
        grad.putpixel((0, y), int(alpha * (t ** 1.15)))
    layer = Image.new("RGBA", im.size, (8, 12, 20, 255))
    layer.putalpha(grad.resize(im.size))
    return Image.alpha_composite(im.convert("RGBA"), layer)


def chip(draw, xy, text, fill, fg=(8, 12, 20)):
    f = font(30)
    x, y = xy
    tw = draw.textlength(text, font=f)
    box = [x, y, x + tw + 32, y + 48]
    draw.rounded_rectangle(box, radius=12, fill=fill)
    draw.text((x + 16, y + 6), text, font=f, fill=fg)
    return box


def poster_01():
    im = scrim_bottom(Image.open(ROOT / "base-01-dormant.png").convert("RGBA"), 0.58, 236)
    d = ImageDraw.Draw(im)
    chip(d, (760, 28), "数解AI", (8, 18, 28), CYAN)
    chip(d, (36, 150), "还在学", GREEN)
    chip(d, (430, 150), "这些已经睡了", (71, 85, 105), INK)
    d.text((40, 930), "图 1 / 3  ·  单元睡着了", font=font(30), fill=GOLD)
    d.text((40, 975), "Sutton 学生有点扎心：", font=font(48), fill=INK)
    d.text((40, 1033), "AI 不是忘了旧的，是学不动新的", font=font(48), fill=INK)
    y = 1110
    for line in (
        "隐藏单元睡着了，彼此还越变越像",
        "梯度还在照常降，新东西就是学不进去",
        "出自 Sutton 第 15 个博士生的论文",
    ):
        d.text((40, y), line, font=font(34), fill=DIM)
        y += 54
    im.convert("RGB").save(ROOT / "01.png", "PNG")


def poster_02():
    im = scrim_bottom(Image.open(ROOT / "base-02-swap.png").convert("RGBA"), 0.60, 236)
    d = ImageDraw.Draw(im)
    d.text((40, 36), "数解AI", font=font(32), fill=CYAN)
    d.text((40, 82), "图 2 / 3  ·  持续反向传播", font=font(30), fill=GOLD)
    chip(d, (36, 160), "其余继续工作", GREEN)
    chip(d, (520, 430), "只换这一块", GOLD)
    d.text((40, 1000), "整机不停，只重置一小部分", font=font(48), fill=INK)
    y = 1080
    for line in (
        "换的是最少用的单元",
        "新单元出边先置 0，免得搅乱已学的函数",
        "重置率 0.0003，通常每步还不到一个",
    ):
        d.text((40, y), line, font=font(32), fill=DIM)
        y += 54
    im.convert("RGB").save(ROOT / "02.png", "PNG")


def poster_03():
    W, H = 1024, 1536
    im = Image.new("RGBA", (W, H), (10, 16, 28, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 8], fill=GOLD)
    d.text((48, 48), "数解AI", font=font(32), fill=CYAN)
    d.text((48, 108), "图 3 / 3  ·  持续版 ImageNet", font=font(30), fill=GOLD)
    d.text((48, 168), "早期能到 88%", font=font(64), fill=INK)
    d.text((48, 252), "任务一多，普通反向传播学不动", font=font(34), fill=DIM)

    cards = [
        ("88%", "早期任务测试集最高", "第 4 章"),
        ("2000", "放到 2000 个任务，损失很严重", "Figure 4.11"),
        ("5000", "第 5000 个任务，比第一个还高", "持续反传"),
        ("10 对 125", "到达最佳准确率的 epoch", "比重置整网快 10 倍"),
        ("低 5 个点", "CIFAR-100 增量训完，对比从头重训", "相当于拿掉批归一化"),
    ]
    y = 340
    for big, mid, small in cards:
        d.rounded_rectangle([48, y, 976, y + 168], radius=18, fill=(22, 32, 48))
        d.text((72, y + 22), big, font=font(48), fill=GOLD)
        d.text((72, y + 86), mid, font=font(32), fill=INK)
        d.text((72, y + 126), small, font=font(26), fill=DIM)
        y += 186
    d.text((48, H - 70), "数字来自 Dohare 2026 博士论文，不是示意。", font=font(28), fill=(148, 163, 184))
    im.convert("RGB").save(ROOT / "03.png", "PNG")


if __name__ == "__main__":
    poster_01()
    poster_02()
    poster_03()
    print("saved")
