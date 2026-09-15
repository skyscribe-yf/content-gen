#!/usr/bin/env python3
"""MoE 负载均衡篇数字图：01 路由坍缩示意 / 02 α 权衡曲线 / 03 384 专家分布。"""

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


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def new_canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w, h), BG)
    return img, ImageDraw.Draw(img)


def draw_01() -> None:
    """路由坍缩：384 个专家，token 全挤到少数几个。"""
    w, h = 1200, 700
    img, d = new_canvas(w, h)
    f_title = font(44, bold=True)
    f_sub = font(28)
    f_label = font(24)

    d.text((60, 40), "路由坍缩：token 全挤到少数几个专家", font=f_title, fill=INK)

    # 左：384 个专家（小方块网格）
    d.text((60, 130), "训练早期（不干预）", font=f_sub, fill=MUTED)
    grid_x, grid_y, cell, gap = 60, 180, 26, 6
    hot = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)]
    for r in range(12):
        for c in range(16):
            x = grid_x + c * (cell + gap)
            y = grid_y + r * (cell + gap)
            if (c, r) in hot:
                d.rounded_rectangle([x, y, x + cell, y + cell], radius=4, fill=ORANGE)
            else:
                d.rounded_rectangle([x, y, x + cell, y + cell], radius=4, fill=PALE_BLUE)
    d.text((60, 180 + 12 * 32 + 20), "橙色 = 被 token 挤爆的少数专家，蓝色 = 收不到 token 的冷门专家", font=f_label, fill=MUTED)

    # 右：token 流向
    d.text((700, 130), "token 流向", font=f_sub, fill=MUTED)
    cx = 700
    for i in range(8):
        y = 200 + i * 55
        d.rounded_rectangle([cx, y, cx + 200, y + 40], radius=8, fill=PALE_YELLOW)
        d.text((cx + 20, y + 6), f"token {i+1}", font=f_label, fill=INK)
        # 箭头指向热点专家
        d.line([cx + 200, y + 20, cx + 320, 240], fill=ORANGE, width=4)
        d.polygon([(cx + 320, 240), (cx + 308, 230), (cx + 308, 250)], fill=ORANGE)
    d.text((700, 200 + 8 * 55 + 20), "全部流向同一批专家 → 其余专家梯度为零", font=f_label, fill=ORANGE)

    img.save(ROOT / "01-routing-collapse.png")


def draw_02() -> None:
    """α 权衡：太小坍缩，太大性能受损，0.01 恰到好处。"""
    w, h = 1200, 700
    img, d = new_canvas(w, h)
    f_title = font(44, bold=True)
    f_sub = font(28)
    f_label = font(24)

    d.text((60, 40), "α 太小坍缩，α 太大伤性能", font=f_title, fill=INK)

    # 坐标轴
    ox, oy = 120, 560
    ax_w, ax_h = 900, 400
    d.line([ox, oy, ox + ax_w, oy], fill=INK, width=3)
    d.line([ox, oy, ox, oy - ax_h], fill=INK, width=3)
    d.text((ox + ax_w - 60, oy + 20), "α（价格系数）", font=f_label, fill=MUTED)
    d.text((ox - 90, oy - ax_h - 10), "模型性能", font=f_label, fill=MUTED)

    # 曲线：先升后降（坍缩区 → 最优 → 罚金绑架）
    pts = []
    for i in range(101):
        x = ox + i * ax_w / 100
        # 性能：0.01 处最高，两侧下降
        perf = 0.9 - 0.5 * abs(i - 10) / 10 - 0.3 * max(0, i - 10) / 90
        y = oy - perf * ax_h
        pts.append((x, y))
    d.line(pts, fill=BLUE, width=5)

    # 三个区域标注
    d.text((ox + 20, oy - 60), "α 太小\n路由坍缩", font=f_label, fill=ORANGE)
    d.text((ox + 380, oy - 330), "α = 0.01\n恰到好处", font=f_label, fill=BLUE)
    d.text((ox + 700, oy - 60), "α 太大\n罚金绑架", font=f_label, fill=ORANGE)

    # 最优值标记
    best_x = ox + 10 * ax_w / 100
    best_y = oy - 0.9 * ax_h
    d.ellipse([best_x - 8, best_y - 8, best_x + 8, best_y + 8], fill=YELLOW, outline=BLUE, width=3)

    img.save(ROOT / "02-alpha-tradeoff.png")


def draw_03() -> None:
    """384 个专家：每个 token 只激活 6 个。"""
    w, h = 1200, 700
    img, d = new_canvas(w, h)
    f_title = font(44, bold=True)
    f_sub = font(28)
    f_label = font(24)

    d.text((60, 40), "384 个路由专家，每个 token 只激活 6 个", font=f_title, fill=INK)

    # 384 个专家网格
    grid_x, grid_y, cell, gap = 60, 150, 30, 8
    active = [(0, 0), (1, 1), (2, 0), (3, 2), (4, 1), (5, 0)]
    for r in range(12):
        for c in range(16):
            x = grid_x + c * (cell + gap)
            y = grid_y + r * (cell + gap)
            if (c, r) in active:
                d.rounded_rectangle([x, y, x + cell, y + cell], radius=5, fill=YELLOW, outline=ORANGE, width=2)
            else:
                d.rounded_rectangle([x, y, x + cell, y + cell], radius=5, fill=PALE_BLUE)
    d.text((60, 150 + 12 * 38 + 20), "黄色 = 本次激活的 6 个专家，蓝色 = 本次未激活的 378 个", font=f_label, fill=MUTED)

    # 右侧：token 序列
    d.text((760, 150), "同一序列，下一个 token 换一批专家", font=f_sub, fill=MUTED)
    for i in range(4):
        y = 210 + i * 90
        d.rounded_rectangle([760, y, 1120, y + 60], radius=10, fill=PALE_YELLOW)
        d.text((780, y + 14), f"token {i+1} → 激活专家 {[6*i+1, 6*i+2, 6*i+3, 6*i+4, 6*i+5, 6*i+6]}", font=f_label, fill=INK)

    img.save(ROOT / "03-384-experts.png")





def draw_04() -> None:
    """拉格朗日几何：等高线 + 约束线 + 无约束最优 vs 约束最优。"""
    w, h = 1200, 700
    img, d = new_canvas(w, h)
    f_title = font(44, bold=True)
    f_sub = font(28)
    f_label = font(24)

    d.text((60, 40), "拉格朗日：约束不是铁律，是价格", font=f_title, fill=INK)

    # 坐标轴
    ox, oy = 200, 560
    ax_w, ax_h = 800, 420
    d.line([ox, oy, ox + ax_w, oy], fill=INK, width=3)
    d.line([ox, oy, ox, oy - ax_h], fill=INK, width=3)
    d.text((ox + ax_w - 40, oy + 20), "x", font=f_label, fill=MUTED)
    d.text((ox - 40, oy - ax_h - 10), "y", font=f_label, fill=MUTED)

    # 等高线（椭圆族，中心 = 无约束最优）
    cx, cy = ox + 560, oy - 300
    for r in (60, 110, 160, 210, 260):
        d.ellipse([cx - r, cy - int(r * 0.55), cx + r, cy + int(r * 0.55)], outline=PALE_BLUE, width=3)
    d.text((cx + 20, cy - 20), "无约束最优", font=f_label, fill=BLUE)
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=BLUE)

    # 约束线 g(x)=0（斜线穿过）
    line_pts = [(ox + 80, oy - 60), (ox + 700, oy - 380)]
    d.line(line_pts, fill=ORANGE, width=5)
    d.text((ox + 60, oy - 90), "约束线 g(x)=0", font=f_label, fill=ORANGE)

    # 约束最优点（切点）
    tx, ty = ox + 380, oy - 240
    d.ellipse([tx - 8, ty - 8, tx + 8, ty + 8], fill=YELLOW, outline=ORANGE, width=3)
    d.text((tx + 20, ty - 30), "约束最优（切点）", font=f_label, fill=INK)

    # 说明
    d.text((60, 640), "无约束时最优在椭圆中心；加上约束线后，最优被拉到切点——拉格朗日乘子就是这条线的「价格」", font=f_sub, fill=MUTED)

    img.save(ROOT / "04-lagrange-geometry.png")


def draw_05() -> None:
    """拉格朗日无处不在：β-VAE / WGAN-GP / L1L2 三例卡片。"""
    w, h = 1200, 700
    img, d = new_canvas(w, h)
    f_title = font(44, bold=True)
    f_sub = font(28)
    f_label = font(24)

    d.text((60, 40), "拉格朗日在 AI 里无处不在", font=f_title, fill=INK)

    cards = [
        ("β-VAE", "β 就是乘子", "约束隐变量别跑太远\nβ > 1 时表示更解耦", PALE_YELLOW, YELLOW),
        ("WGAN-GP", "λ = 10 就是乘子", "判别器当警察\n梯度惩罚是执法成本", PALE_BLUE, BLUE),
        ("L1/L2 正则", "weight_decay 就是乘子", "约束权重别太大\n罚金形式（岭回归/LASSO）", PALE_ORANGE, ORANGE),
    ]
    card_w, card_h, gap = 340, 380, 40
    x0, y0 = 60, 150
    for i, (name, sub, body, bg, accent) in enumerate(cards):
        x = x0 + i * (card_w + gap)
        d.rounded_rectangle([x, y0, x + card_w, y0 + card_h], radius=16, fill=bg)
        d.rounded_rectangle([x, y0, x + card_w, y0 + 12], radius=6, fill=accent)
        d.text((x + 30, y0 + 40), name, font=font(40, bold=True), fill=INK)
        d.text((x + 30, y0 + 110), sub, font=f_sub, fill=accent)
        for j, line in enumerate(body.split("\n")):
            d.text((x + 30, y0 + 180 + j * 50), line, font=f_label, fill=INK)

    d.text((60, 600), "同一个套路：给约束标个价，加进目标函数——只是名字不叫拉格朗日", font=f_sub, fill=MUTED)

    img.save(ROOT / "05-lagrange-everywhere.png")

if __name__ == "__main__":
    draw_01()
    draw_02()
    draw_03()
    draw_04()
    draw_05()
    print("done: 01-routing-collapse.png / 02-alpha-tradeoff.png / 03-384-experts.png / 04-lagrange-geometry.png / 05-lagrange-everywhere.png")
