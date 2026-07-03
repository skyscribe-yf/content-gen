"""
yairouter 高质量图片生成客户端 — gpt-image-1

基于 AGENTS.md 文档中的 yairouter API 配置：
  端点: https://api.yairouter.com/v1/images/generations
  模型: gpt-image-1
  认证: Authorization: Bearer $XAI_API_KEY
  质量: high

用法:
  # 单张生成
  python yairouter_img.py --prompt "..." --size 1024x1536 --output card.png

  # 批量从 cards.json
  python yairouter_img.py --config content/2026-07-03-梯度下降/xiaohongshu/cards.json

  # 检查 key
  python yairouter_img.py --check
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("需要 requests: pip install requests")

API_URL = "https://api.yairouter.com/v1/images/generations"


def _load_dotenv():
    start = Path(__file__).resolve().parent
    for d in [start, *start.parents]:
        env_path = d / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("'\"")
                os.environ.setdefault(k, v)
            return


def _api_key() -> str:
    _load_dotenv()
    key = os.environ.get("XAI_API_KEY", "").strip()
    if not key:
        sys.exit("❌ 请设置 XAI_API_KEY 环境变量或在 .env 中配置")
    return key


# 尺寸映射：小红书 3:4 竖版
SIZE_MAP = {
    "3:4": "1024x1536",
    "1:1": "1024x1024",
    "16:9": "1792x1024",
    "2.35:1": "1792x768",
}


def generate(
    prompt: str,
    size: str = "1024x1536",
    quality: str = "high",
    n: int = 1,
    output_dir: str = ".",
    filename: str = "",
) -> list[str]:
    """生成图片并保存"""
    key = _api_key()

    # 解析尺寸
    if size in SIZE_MAP:
        size = SIZE_MAP[size]

    print(f"📤 提交 gpt-image-1 (size={size}, quality={quality}, n={n})")
    print(f"   Prompt: {prompt[:80]}...")

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-image-1",
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
        },
        timeout=180,
    )

    if resp.status_code != 200:
        print(f"❌ API 返回 {resp.status_code}: {resp.text[:300]}")
        sys.exit(1)

    data = resp.json()
    items = data.get("data", [])
    if not items:
        print(f"❌ 无图片返回: {json.dumps(data, ensure_ascii=False)[:300]}")
        return []

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for i, item in enumerate(items):
        b64 = item.get("b64_json", "").strip()
        url = item.get("url", "").strip()

        if b64:
            img_bytes = base64.b64decode(b64)
        elif url:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            img_bytes = r.content
        else:
            print(f"  ⚠️ 第 {i+1} 张无数据")
            continue

        # 确定文件名
        if i == 0 and filename:
            fname = filename
        else:
            ext = "png"
            fname = f"yairouter-{int(time.time())}-{i+1}.{ext}"

        filepath = output_dir / fname
        filepath.write_bytes(img_bytes)
        saved.append(str(filepath))
        print(f"  ✅ 已保存: {filepath} ({len(img_bytes)//1024}KB)")

    return saved


def generate_series(config_path: str):
    """从 cards.json 批量生成系列图"""
    with open(config_path) as f:
        config = json.load(f)

    cards = config.get("cards", [])
    output_dir = config.get("output_dir", "output")
    # gpt-image-1 不用 model/quality 字段，直接用默认
    size = config.get("size", "1024x1536")
    quality = config.get("quality", "high")

    total = len(cards)
    all_saved = []

    for i, card in enumerate(cards, 1):
        prompt = card.get("prompt", "")
        filename = card.get("filename", f"{i:02d}.png")
        n = card.get("n", 1)

        print(f"\n{'='*50}")
        print(f"📷 [{i}/{total}] {card.get('title', '无标题')}")

        saved = generate(
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
            output_dir=output_dir,
            filename=filename,
        )
        all_saved.extend(saved)

        # 限速：避免 API 限流
        if i < total:
            print("  ⏳ 等待 3s 避免限流...")
            time.sleep(3)

    print(f"\n🎉 系列图完成！共 {total} 组，{len(all_saved)} 张")
    print(f"   保存目录: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="yairouter gpt-image-1 高质量图片生成")
    parser.add_argument("--prompt", help="生成提示词")
    parser.add_argument("--size", default="1024x1536", help="尺寸 (默认 1024x1536)")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"])
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--filename", default="", help="输出文件名")
    parser.add_argument("--config", help="cards.json 批量生成")
    parser.add_argument("--check", action="store_true", help="检查 API key")
    args = parser.parse_args()

    if args.check:
        key = _api_key()
        print(f"✅ XAI_API_KEY 已配置 ({key[:8]}...{key[-4:]})")
    elif args.config:
        generate_series(args.config)
    elif args.prompt:
        generate(
            prompt=args.prompt,
            size=args.size,
            quality=args.quality,
            n=args.n,
            output_dir=args.output_dir,
            filename=args.filename,
        )
    else:
        parser.print_help()
