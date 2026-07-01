"""
小红书信息图生成器
纯 Python + Pillow，零 API 费用，本地出图

用法:
  python xhs_card.py --title "梯度下降的直觉" --subtitle "蒙着眼下山" --items "梯度=坡度方向" "学习率=步子大小" "极值点=山底" --output gradient.jpg
  python xhs_card.py --config card_config.json
"""
import argparse
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ponytail: 全局配色，与 Manim 模板统一
THEMES = {
    "purple": {
        "bg": (45, 27, 105),       # #2D1B69
        "bg_gradient": (74, 47, 189),
        "accent": (255, 107, 157),  # #FF6B9D
        "text": (255, 255, 255),
        "text_secondary": (180, 160, 220),
        "badge_bg": (255, 107, 157),
        "badge_text": (45, 27, 105),
    },
    "dark_blue": {
        "bg": (15, 23, 42),        # #0F172A
        "bg_gradient": (30, 64, 175),
        "accent": (88, 196, 221),   # #58c4dd
        "text": (255, 255, 255),
        "text_secondary": (148, 163, 184),
        "badge_bg": (88, 196, 221),
        "badge_text": (15, 23, 42),
    },
    "warm": {
        "bg": (255, 248, 235),      # cream
        "bg_gradient": (255, 224, 178),
        "accent": (224, 124, 90),   # #e07c5a
        "text": (44, 44, 44),
        "text_secondary": (120, 100, 80),
        "badge_bg": (224, 124, 90),
        "badge_text": (255, 255, 255),
    },
}

# 小红书标准 3:4 竖版
CARD_W, CARD_H = 1080, 1440


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """尝试加载中文字体，逐个回退"""
    # macOS / Linux 常见中文字体路径
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]
    bold_candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]

    paths = bold_candidates if bold else candidates
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size, index=0)
            except Exception:
                continue

    # 最终回退：Pillow 默认字体
    return ImageFont.load_default()


def _draw_gradient(draw: ImageDraw.Draw, w: int, h: int, color_top: tuple, color_bot: tuple):
    """从上到下渐变背景"""
    for y in range(h):
        ratio = y / h
        r = int(color_top[0] + (color_bot[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bot[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bot[2] - color_top[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _draw_rounded_rect(draw: ImageDraw.Draw, bbox: tuple, radius: int, fill: tuple):
    """画圆角矩形"""
    x0, y0, x1, y1 = bbox
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.pieslice([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270, fill=fill)
    draw.pieslice([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90, fill=fill)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """按像素宽度自动换行"""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if font.getlength(test) > max_width:
            if current:
                lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def generate_card(
    title: str,
    subtitle: str = "",
    items: list[str] | None = None,
    footer: str = "收藏不迷路 ❤️",
    theme: str = "purple",
    output: str = "card.jpg",
    card_type: str = "knowledge",  # knowledge | comparison | steps | data
    # comparison 专用
    concept_a: str = "",
    concept_b: str = "",
    points_a: list[str] | None = None,
    points_b: list[str] | None = None,
    # data 专用
    big_number: str = "",
    data_source: str = "",
    sub_data: list[str] | None = None,
):
    """生成一张小红书信息图"""
    theme_colors = THEMES.get(theme, THEMES["purple"])
    items = items or []
    img = Image.new("RGB", (CARD_W, CARD_H))
    draw = ImageDraw.Draw(img)

    # 渐变背景
    _draw_gradient(draw, CARD_W, CARD_H, theme_colors["bg"], theme_colors["bg_gradient"])

    # ── 顶部标题区 ──
    y = 80
    title_font = _get_font(56, bold=True)
    sub_font = _get_font(28)
    body_font = _get_font(24)
    badge_font = _get_font(28, bold=True)
    small_font = _get_font(20)
    footer_font = _get_font(22)

    # 标题
    title_lines = _wrap_text(title, title_font, CARD_W - 120)
    for line in title_lines:
        draw.text((60, y), line, fill=theme_colors["text"], font=title_font)
        y += 70
    y += 10

    # 副标题
    if subtitle:
        sub_lines = _wrap_text(subtitle, sub_font, CARD_W - 120)
        for line in sub_lines:
            draw.text((60, y), line, fill=theme_colors["text_secondary"], font=sub_font)
            y += 40
    y += 30

    # 分割线
    draw.line([(60, y), (CARD_W - 60, y)], fill=theme_colors["accent"], width=3)
    y += 40

    # ── 内容区 ──
    if card_type == "knowledge":
        y = _draw_knowledge_items(draw, y, items, theme_colors, body_font, badge_font, small_font)
    elif card_type == "comparison":
        y = _draw_comparison(
            draw, y, concept_a, concept_b,
            points_a or [], points_b or [],
            theme_colors, body_font, small_font,
        )
    elif card_type == "steps":
        y = _draw_steps(draw, y, items, theme_colors, body_font, badge_font, small_font)
    elif card_type == "data":
        y = _draw_data(
            draw, y, big_number, data_source,
            sub_data or [], theme_colors, body_font, title_font, small_font,
        )

    # ── 底部 CTA ──
    footer_y = CARD_H - 120
    _draw_rounded_rect(
        draw,
        (CARD_W // 2 - 200, footer_y, CARD_W // 2 + 200, footer_y + 60),
        30,
        theme_colors["accent"],
    )
    fw = footer_font.getlength(footer)
    draw.text(
        (CARD_W // 2 - fw // 2, footer_y + 15),
        footer,
        fill=theme_colors["badge_text"],
        font=footer_font,
    )

    # 保存
    img.save(output, quality=95)
    print(f"✅ 已生成: {output} ({CARD_W}x{CARD_H})")
    return img


def _draw_knowledge_items(draw, y, items, colors, body_font, badge_font, small_font):
    """知识科普卡：编号要点列表"""
    for i, item in enumerate(items, 1):
        # 数字徽章
        badge_x, badge_y = 60, y
        _draw_rounded_rect(draw, (badge_x, badge_y, badge_x + 50, badge_y + 50), 10, colors["accent"])
        num_text = str(i)
        nw = badge_font.getlength(num_text)
        draw.text(
            (badge_x + 25 - nw // 2, badge_y + 8),
            num_text,
            fill=colors["badge_text"],
            font=badge_font,
        )

        # 要点文字（自动换行）
        text_x = 130
        lines = _wrap_text(item, body_font, CARD_W - 180)
        for line in lines:
            draw.text((text_x, badge_y + 5), line, fill=colors["text"], font=body_font)
            badge_y += 35
        y = badge_y + 30

    return y


def _draw_comparison(draw, y, concept_a, concept_b, points_a, points_b, colors, body_font, small_font):
    """对比卡：左右布局"""
    col_w = (CARD_W - 160) // 2
    left_x, right_x = 60, CARD_W // 2 + 20

    # 概念标题
    draw.text((left_x, y), concept_a, fill=colors["accent"], font=body_font)
    draw.text((right_x, y), concept_b, fill=colors["accent"], font=body_font)
    y += 50

    # VS 分隔
    mid_x = CARD_W // 2
    draw.line([(mid_x, y), (mid_x, CARD_H - 150)], fill=colors["text_secondary"], width=1)
    draw.text((mid_x - 20, y), "VS", fill=colors["accent"], font=small_font)

    # 左右要点
    for pa, pb in zip(points_a, points_b):
        draw.text((left_x, y + 30), f"• {pa}", fill=colors["text"], font=small_font)
        draw.text((right_x, y + 30), f"• {pb}", fill=colors["text"], font=small_font)
        y += 50

    return y + 40


def _draw_steps(draw, y, items, colors, body_font, badge_font, small_font):
    """步骤卡：竖排编号"""
    for i, item in enumerate(items, 1):
        # 大号步骤编号
        step_font = _get_font(64, bold=True)
        num_text = f"{i:02d}"
        draw.text((60, y), num_text, fill=colors["accent"], font=step_font)

        # 步骤说明
        lines = _wrap_text(item, body_font, CARD_W - 200)
        for line in lines:
            draw.text((200, y + 15), line, fill=colors["text"], font=body_font)
            y += 35
        y += 50

    return y


def _draw_data(draw, y, big_number, data_source, sub_data, colors, body_font, title_font, small_font):
    """数据冲击卡：大数字 + 补充数据"""
    # 大数字居中
    num_font = _get_font(120, bold=True)
    nw = num_font.getlength(big_number)
    draw.text(
        (CARD_W // 2 - nw // 2, y),
        big_number,
        fill=colors["accent"],
        font=num_font,
    )
    y += 150

    # 数据来源
    if data_source:
        sw = small_font.getlength(data_source)
        draw.text(
            (CARD_W // 2 - sw // 2, y),
            data_source,
            fill=colors["text_secondary"],
            font=small_font,
        )
        y += 50

    # 补充数据
    for d in sub_data:
        draw.text((80, y), f"📊 {d}", fill=colors["text"], font=body_font)
        y += 45

    return y


# ── 批量生成系列图 ──

def generate_series(config_path: str):
    """从一个 JSON 配置批量生成系列信息图"""
    with open(config_path) as f:
        config = json.load(f)

    series_title = config.get("series_title", "系列")
    cards = config.get("cards", [])
    theme = config.get("theme", "purple")
    output_dir = Path(config.get("output_dir", "output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    total = len(cards)
    for i, card in enumerate(cards, 1):
        card_type = card.get("type", "knowledge")
        output = str(output_dir / f"{i:02d}-{card.get('filename', f'card-{i}.jpg')}")

        generate_card(
            title=card.get("title", f"{series_title} ({i}/{total})"),
            subtitle=card.get("subtitle", ""),
            items=card.get("items", []),
            footer=card.get("footer", f"{i}/{total} ❤️ 收藏不迷路"),
            theme=theme,
            output=output,
            card_type=card_type,
            concept_a=card.get("concept_a", ""),
            concept_b=card.get("concept_b", ""),
            points_a=card.get("points_a", []),
            points_b=card.get("points_b", []),
            big_number=card.get("big_number", ""),
            data_source=card.get("data_source", ""),
            sub_data=card.get("sub_data", []),
        )

    print(f"\n🎉 系列图生成完毕！共 {total} 张，保存在 {output_dir}/")


# ── CLI ──

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书信息图生成器")
    parser.add_argument("--title", help="主标题")
    parser.add_argument("--subtitle", default="", help="副标题")
    parser.add_argument("--items", nargs="+", default=[], help="要点列表")
    parser.add_argument("--theme", default="purple", choices=THEMES.keys(), help="配色主题")
    parser.add_argument("--output", default="card.jpg", help="输出文件名")
    parser.add_argument("--type", default="knowledge", choices=["knowledge", "comparison", "steps", "data"], help="卡片类型")
    parser.add_argument("--config", help="批量生成用的 JSON 配置文件路径")
    args = parser.parse_args()

    if args.config:
        generate_series(args.config)
    else:
        generate_card(
            title=args.title,
            subtitle=args.subtitle,
            items=args.items,
            theme=args.theme,
            output=args.output,
            card_type=args.type,
        )
