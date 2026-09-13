#!/usr/bin/env python3
"""GRPO 数学篇数字图：01 全同分组概率曲线 / 03 错误回答更长（R1-Zero 实测）。"""

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
W = 1254

G = 16  # R1 第一阶段 RL 组大小


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


F_TITLE = font(44, True)
F_SUB = font(26, True)
F_BODY = font(24)
F_SMALL = font(19)
F_BIG = font(34, True)
F_NUM = font(30, True)


def p_all_same(p: float, g: int = G) -> float:
    """一道正确率 p 的题，G 份答卷全同分（全对或全错）的概率。"""
    return p**g + (1.0 - p) ** g


def report() -> None:
    print(f"== 全同分组概率（G={G}）==")
    for p in (0.5, 0.8, 0.9, 0.95, 0.99):
        pp = p_all_same(p)
        print(f"p={p:.2f}  P(全对)={p**G*100:.4f}%  P(全错)={(1-p)**G*100:.6f}%  合计={pp*100:.2f}%")
    print("== R1-Zero 回答长度（Dr. GRPO 论文 Table 5）==")
    wrong, right = 8206.1, 4965.4
    print(f"错误回答平均 {wrong} 字符，正确回答平均 {right} 字符，错误长 {wrong/right:.0%}")


def canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, 836), BG)
    d = ImageDraw.Draw(img)
    d.text((64, 52), title, font=F_TITLE, fill=INK)
    d.text((64, 122), subtitle, font=F_BODY, fill=MUTED)
    d.line([(64, 186), (W - 64, 186)], fill=PALE_BLUE, width=3)
    return img, d


def chart_all_same() -> None:
    img, d = canvas("练得越好，信号越少", f"一道题答 {G} 遍全对或全错（组内无差异）的概率，随题目正确率的变化")
    # 绘图区
    x0, x1, y0, y1 = 130, 1150, 300, 700
    d.line([(x0, y0), (x0, y1), (x1, y1)], fill=INK, width=3)
    # 轴刻度（均匀三档，避免末端拥挤；90/95/99 由橙色标注点表达）
    for p in (0.5, 0.75, 1.0):
        x = x0 + (x1 - x0) * (p - 0.5) / 0.5
        d.line([(x, y1), (x, y1 + 8)], fill=INK, width=2)
        d.text((x - 22, y1 + 14), f"{p:.0%}", font=F_SMALL, fill=MUTED)
    for frac, lab in ((0.0, "0%"), (0.5, "50%"), (1.0, "100%")):
        y = y1 - (y1 - y0) * frac
        d.line([(x0 - 8, y), (x0, y)], fill=INK, width=2)
        d.text((x0 - 76, y - 12), lab, font=F_SMALL, fill=MUTED)
    # 曲线 y = p^16 + (1-p)^16，x 取 0.5~1 区间放大
    pts = []
    steps = 240
    for i in range(steps + 1):
        p = 0.5 + 0.5 * i / steps
        v = p_all_same(p)
        x = x0 + (x1 - x0) * (p - 0.5) / 0.5
        y = y1 - (y1 - y0) * v
        pts.append((x, y))
    d.line(pts, fill=BLUE, width=6)
    # 标注点
    marks = ((0.5, "0.003%", -8, -56), (0.9, "18.5%", -46, -52), (0.95, "44.0%", -50, -52), (0.99, "85.1%", -160, -14))
    for p, lab, dx, dy in marks:
        v = p_all_same(p)
        x = x0 + (x1 - x0) * (p - 0.5) / 0.5
        y = y1 - (y1 - y0) * v
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=ORANGE)
        d.text((x + dx, y + dy), lab, font=F_NUM, fill=ORANGE)
    # 注释：两端含义
    d.text((x0 + 8, y0 - 6), "零优势组概率", font=F_SMALL, fill=MUTED)
    box_x, box_y = 560, 250
    d.rounded_rectangle([box_x, box_y, box_x + 380, box_y + 200], radius=18, fill=PALE_YELLOW)
    d.text((box_x + 20, box_y + 22), "正确率 99% 的简单题：", font=F_SUB, fill=INK)
    d.text((box_x + 20, box_y + 64), "16 份答卷几乎必然全对", font=F_BODY, fill=INK)
    d.text((box_x + 20, box_y + 106), "全同分组 → 组内标准差 = 0", font=F_BODY, fill=INK)
    d.text((box_x + 20, box_y + 148), "→ 这批样本梯度为 0，白跑", font=F_BODY, fill=INK)
    d.text((64, 736), "注：全对概率 p^16，全错概率 (1-p)^16，两者相加即全同分组概率。模型越强（p 越高），零信号组占比越高。",
           font=F_SMALL, fill=MUTED)
    img.save(ROOT / "01-all-same-group.png")
    print("saved 01-all-same-group.png")


def chart_wrong_longer() -> None:
    img, d = canvas("错了，还更啰嗦", "DeepSeek-R1-Zero 平均回答长度：错误 vs 正确（Dr. GRPO 论文 Table 5）")
    wrong, right = 8206, 4965
    bar_x, bar_w = 300, 700
    max_v = 9000
    rows = (("错误回答", wrong, PALE_ORANGE, ORANGE), ("正确回答", right, PALE_BLUE, BLUE))
    y = 300
    for lab, v, pale, full in rows:
        h = 96
        d.rounded_rectangle([bar_x, y, bar_x + int(bar_w * v / max_v), y + h], radius=14, fill=pale)
        d.text((110, y + 30), lab, font=F_SUB, fill=INK)
        d.text((bar_x + int(bar_w * v / max_v) + 18, y + 28), f"{v} 字符", font=F_NUM, fill=full)
        y += 170
    d.text((64, y + 10), "错误回答平均比正确回答长 65%：写长一点，每个 token 摊到的惩罚就被稀释一分。",
           font=F_BODY, fill=INK)
    d.text((64, 736), "注：长度来自 Dr. GRPO 论文（arXiv 2503.20783）对 DeepSeek-R1-Zero 回答的统计，单位为字符。",
           font=F_SMALL, fill=MUTED)
    img.save(ROOT / "03-wrong-longer.png")
    print("saved 03-wrong-longer.png")


if __name__ == "__main__":
    report()
    chart_all_same()
    chart_wrong_longer()
