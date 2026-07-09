"""
小红书出图 Pipeline — 从选题配置生成信息图

用法:
  python3 xhs-pipeline.py generate --topic gradient_descent
  python3 xhs-pipeline.py generate --topic gradient_descent --mode ai
  python3 xhs-pipeline.py generate --config content/2026-07-01-gradient_descent/xiaohongshu/cards.json
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
XHS_CARD_SCRIPT = ROOT / "scripts" / "xhs_card.py"
CHEAP_IMG_SCRIPT = ROOT / "scripts" / "cheap_img_client.py"
CONTENT_DIR = ROOT / "content"

# ponytail: 复用content-pipeline的选题数据
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ponytail: 直接内嵌选题列表，避免跨文件import问题
TOPICS = {
    "gradient_descent": {"title": "梯度下降：蒙着眼下山", "type": "principle"},
    "softmax": {"title": "Softmax：温和的投票", "type": "principle"},
    "attention": {"title": "Transformer注意力：谁在听谁说话", "type": "principle"},
    "moe_route": {"title": "为什么DeepSeek比GPT便宜10倍？", "type": "fusion"},
    "diffusion": {"title": "扩散模型：从噪声中还原真相", "type": "principle"},
    "cot": {"title": "AI做数学题为什么总算错？", "type": "fusion"},
}


def generate_local(config_path: str):
    """用xhs_card.py本地出图"""
    cmd = [sys.executable, str(XHS_CARD_SCRIPT), "--config", config_path]
    print(f"🖼️  本地出图: {config_path}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"❌ 出图失败")
    else:
        print(f"✅ 出图完成")


def generate_ai(config_path: str, provider: str = "minimax"):
    """用AI出图（廉价版）"""
    # 读取配置，把卡片信息转成prompt
    with open(config_path) as f:
        config = json.load(f)

    cards = config.get("cards", [])
    output_dir = config.get("output_dir", ".")

    print(f"🎨 AI出图: {len(cards)} 张 (provider={provider})")

    for i, card in enumerate(cards, 1):
        card_type = card.get("type", "knowledge")
        title = card.get("title", "")
        items = card.get("items", [])

        # 构建prompt
        prompt = _card_to_prompt(card, config.get("theme", "purple"))
        print(f"\n  [{i}/{len(cards)}] {title}")

        # 用cheap_img_client出图
        cmd = [
            sys.executable, str(CHEAP_IMG_SCRIPT),
            "--prompt", prompt,
            "--provider", provider,
            "--size", "3:4",
            "--output-dir", output_dir,
        ]
        subprocess.run(cmd)


def _card_to_prompt(card: dict, theme: str) -> str:
    """把卡片配置转成AI出图prompt"""
    card_type = card.get("type", "knowledge")
    title = card.get("title", "")

    if card_type == "knowledge":
        items = card.get("items", [])
        items_text = "，".join(items[:5])
        return (f"小红书风格知识科普卡片，3:4竖版，深紫色背景，"
                f"白色加粗标题「{title}」，"
                f"5个编号要点：{items_text}，"
                f"底部粉色CTA，高保真中文排版，无水印")

    elif card_type == "comparison":
        concept_a = card.get("concept_a", "A")
        concept_b = card.get("concept_b", "B")
        return (f"小红书概念对比卡，3:4竖版，"
                f"标题「{concept_a} vs {concept_b}」，"
                f"左右对比布局，蓝色vs绿色，"
                f"高保真中文排版，无水印")

    elif card_type == "steps":
        items = card.get("items", [])
        return (f"小红书步骤教程卡，3:4竖版，米色背景，"
                f"标题「{title}」，"
                f"{len(items)}个步骤垂直排列，"
                f"温暖橙色强调，高保真中文排版，无水印")

    elif card_type == "data":
        big_number = card.get("big_number", "")
        return (f"小红书数据卡片，3:4竖版，深蓝渐变背景，"
                f"标题「{title}」，"
                f"核心大数字「{big_number}」占画面40%，"
                f"高保真中文排版，无水印")

    return f"小红书信息图，3:4竖版，标题「{title}」，高保真中文排版，无水印"


def generate(topic_name: str, mode: str, report_date: str):
    """生成小红书信息图"""
    if topic_name not in TOPICS:
        print(f"❌ 未知选题: {topic_name}")
        return

    # 找到cards.json
    topic_dir = CONTENT_DIR / f"{report_date}-{topic_name}"
    cards_path = topic_dir / "xiaohongshu" / "cards.json"

    if not cards_path.exists():
        print(f"❌ 未找到配置: {cards_path}")
        print(f"💡 先运行: make content TOPIC={topic_name}")
        return

    if mode == "local":
        generate_local(str(cards_path))
    elif mode == "ai":
        generate_ai(str(cards_path))
    else:
        print(f"未知模式: {mode}，可用: local, ai")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书出图Pipeline")
    parser.add_argument("--topic", help="选题名称")
    parser.add_argument("--config", help="直接指定cards.json路径")
    parser.add_argument("--mode", default="local", choices=["local", "ai"],
                        help="出图模式")
    parser.add_argument("--date", default=None, help="日期（自动检测最新）")
    parser.add_argument("--provider", default="minimax",
                        choices=["minimax", "nanobanana", "sparkpix"],
                        help="AI出图提供商")

    args = parser.parse_args()

    if args.config:
        if args.mode == "local":
            generate_local(args.config)
        else:
            generate_ai(args.config, args.provider)
    elif args.topic:
        # 自动找最新日期的目录
        if args.date:
            report_date = args.date
        else:
            # 找包含该topic的最新目录
            matching = sorted(CONTENT_DIR.glob(f"*-{args.topic}"))
            if matching:
                # 目录名格式: YYYY-MM-DD-topic，取前3段拼成日期
                report_date = "-".join(matching[-1].name.split("-")[:3])
            else:
                from datetime import date
                report_date = date.today().isoformat()

        generate(args.topic, args.mode, report_date)
    else:
        parser.print_help()
