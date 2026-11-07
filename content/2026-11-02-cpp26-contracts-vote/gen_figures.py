#!/usr/bin/env python3
"""本篇两张脚本结构图（数字/结构禁走 AI 生图轨）：

01-dis-vote-thresholds.png — DIS 双阈值投票图（全文数字脊梁）
02-contract-semantics.png  — P2900 四种 evaluation semantic 表 + 跨 TU 不一致警示
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).parent
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BLUE, RED, INK, GRAY, LINE = "#0F4C81", "#C0392B", "#1A1A1A", "#777777", "#D8DEE6"


def F(path, size):
    return ImageFont.truetype(path, size)


def ctext(d, xy, s, font, fill, anchor="mm"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def fig1():
    W, H = 1200, 780
    im = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(im)
    ctext(d, (W / 2, 66), "两道门槛，一道都没够", F(BOLD, 46), INK)
    ctext(d, (W / 2, 122), "C++26 DIS 批准投票 · 10 月 22 日截止 · 票数为据报道口径",
          F(REG, 24), GRAY)
    x0, x1 = 90, 1110
    track = x1 - x0

    def bar(y, label, got, need, fill, thr_txt, val_txt, thr_ratio):
        ctext(d, (x0, y - 46), label, F(BOLD, 30), fill, anchor="lm")
        d.rounded_rectangle([x0, y, x1, y + 64], 10, outline=LINE, width=2)
        fw = int(track * got / need[1])
        d.rounded_rectangle([x0, y, x0 + fw, y + 64], 10, fill=fill)
        ctext(d, (x0 + fw / 2, y + 32), val_txt, F(BOLD, 30), "#FFFFFF")
        tx = x0 + int(track * thr_ratio)
        d.line([tx, y - 26, tx, y + 90], fill=RED, width=4)
        for yy in range(y - 26, y + 90, 14):
            d.line([tx, yy, tx + 10, yy + 7], fill=RED, width=3)
        ctext(d, (tx + 12, y - 38), thr_txt, F(BOLD, 26), RED, anchor="lm")
        ctext(d, (x1, y + 96), f"共 {need[1]} 票 · 已画 {got} 票", F(REG, 22), GRAY,
              anchor="rm")

    bar(230, "P 成员国赞成票", 12, (14, 20), BLUE, "需要 14 张（2/3）", "12 票 = 60%", 14 / 20)
    bar(480, "国家体反对票", 9, (5, 22), RED, "上限 5 张（1/4）", "9 票 = 41%", 5 / 22)
    d.line([90, 640, 1110, 640], fill=LINE, width=2)
    ctext(d, (W / 2, 688), "任何一道不过，草案即被否 · ISO 官方记录未公开，数字为 Seacord / Pusz 报道口径",
          F(REG, 24), GRAY)
    im.save(D / "01-dis-vote-thresholds.png")


def fig2():
    W, H = 1200, 760
    im = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(im)
    ctext(d, (W / 2, 62), "P2900 给每个断言留了四种运行语义", F(BOLD, 42), INK)
    ctext(d, (W / 2, 116), "pre / post / contract_assert 写在签名与函数体里，语义在构建时选定",
          F(REG, 24), GRAY)
    x0, x1 = 70, 1130
    rows = [
        ("ignore", "不求值，什么都不发生", True),
        ("observe", "打违规报告，继续运行", False),
        ("enforce", "打报告后 abort（GCC 16.2 实测 exit 134）", False),
        ("quick_enforce", "最小开销版 enforce", False),
    ]
    hy, rh = 176, 86
    d.rectangle([x0, hy, x1, hy + 62], fill=BLUE)
    ctext(d, (x0 + 30, hy + 31), "语义", F(BOLD, 28), "#FFFFFF", anchor="lm")
    ctext(d, (x0 + 330, hy + 31), "违反时行为", F(BOLD, 28), "#FFFFFF", anchor="lm")
    y = hy + 62
    for i, (name, desc, hot) in enumerate(rows):
        if hot:
            d.rectangle([x0, y, x1, y + rh], fill="#FDF3F2")
            d.rectangle([x0, y, x0 + 8, y + rh], fill=RED)
        elif i % 2:
            d.rectangle([x0, y, x1, y + rh], fill="#F5F7FA")
        ctext(d, (x0 + 30, y + rh / 2), name, F(BOLD, 30), RED if hot else INK, anchor="lm")
        ctext(d, (x0 + 330, y + rh / 2), desc, F(REG, 27), INK, anchor="lm")
        if hot:
            ctext(d, (x1 - 24, y + rh / 2), "← 反对派最恨的一行", F(BOLD, 24), RED, anchor="rm")
        y += rh
    d.rectangle([x0, y + 18, x1, y + 108], outline=RED, width=3)
    ctext(d, (W / 2, y + 63), "致命细节：同一份源码，在不同编译单元里可以有不同语义", F(BOLD, 28), RED)
    im.save(D / "02-contract-semantics.png")


if __name__ == "__main__":
    fig1()
    fig2()
    print("figures saved")
