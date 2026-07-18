"""
zairouter GPT-Image-2 图片生成客户端

API 文档: https://zairouter.com/blog/gpt-5-5-gpt-image-2-xai-router/
端点:     https://api.zairouter.com/v1/images/generations
模型:     gpt-image-2
认证:     Authorization: Bearer $ZAI_API_KEY

用法:
  # 单张生成
  python zairouter_client.py --prompt "..." --size 16:9 --output cover.png

  # 一次生成多张（--n）
  python zairouter_client.py --prompt "..." --n 3 --output-dir ./output

  # 批量从 JSON 配置
  python zairouter_client.py --config cards.json

  # 检查 key
  python zairouter_client.py --check
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

API_URL = "https://api.zairouter.com/v1/images/generations"

# 分辨率选择依据：
# - ZAI Router 最长边 ≤ 3840（4096x4096 实测返回 HTTP 400）
# - 3840x2160 / 2160x3840 实测通过
# - 项目默认：1:1 正方形（正文配图），21:9 电影宽幅（封面图）
SIZE_MAP = {
    # ── 1:1 正方形 ──
    "1:1":      "1024x1024",   # 默认，1K 级别
    "1:1-2k":   "2048x2048",   # 2K 正方形（最长边 ≤ 3840，安全）
    # ── 21:9 电影宽幅（封面图强制）──
    "21:9":     "1248x528",    # 1K 宽幅（最小合法：≥655,360px, 边÷16）
    "21:9-2k":  "2688x1152",   # 2K 宽幅
    "21:9-4k":  "3840x1648",   # 4K 宽幅
    # ── 其他常用 ──
    "16:9":     "1088x608",
    "16:9-4k":  "3840x2160",   # 实测通过
    "9:16":     "608x1088",
    "9:16-4k":  "2160x3840",   # 实测通过
    "3:4":      "768x1024",    # 小红书竖版
    "4:3":      "1024x768",
    "3:2":      "1024x688",
    "2:3":      "688x1024",
}


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
    key = os.environ.get("ZAI_API_KEY", "").strip()
    if not key:
        sys.exit("❌ 请设置 ZAI_API_KEY 环境变量或在 .env 中配置")
    return key


def generate(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "high",
    output_format: str = "png",
    n: int = 1,
    output_dir: str = ".",
    filename: str = "",
) -> list[str]:
    """生成图片并保存。返回已保存的文件路径列表。"""
    key = _api_key()

    if size in SIZE_MAP:
        size = SIZE_MAP[size]

    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "n": n,
        "size": size,
        "quality": quality,
        "output_format": output_format,
    }

    print(f"📤 提交 gpt-image-2 (size={size}, quality={quality}, n={n})")
    print(f"   Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=300,
    )

    if resp.status_code != 200:
        print(f"❌ API 返回 {resp.status_code}: {resp.text[:500]}")
        sys.exit(1)

    data = resp.json()

    # 打印 usage 信息
    usage = data.get("usage", {})
    if usage:
        print(f"   📊 tokens: {usage.get('total_tokens', '?')} "
              f"(in={usage.get('input_tokens', '?')}, out={usage.get('output_tokens', '?')})")

    items = data.get("data", [])
    if not items:
        print(f"❌ 无图片返回: {json.dumps(data, ensure_ascii=False)[:300]}")
        return []

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for i, item in enumerate(items):
        b64 = item.get("b64_json", "").strip()
        revised = item.get("revised_prompt", "")
        if revised:
            print(f"   ✏️  改写 prompt: {revised[:80]}...")

        if not b64:
            print(f"  ⚠️ 第 {i+1} 张无 b64_json 数据")
            continue

        img_bytes = base64.b64decode(b64)

        # 确定文件名
        if n == 1 and filename:
            fname = filename
        elif filename and n > 1:
            stem, ext = os.path.splitext(filename)
            if not ext:
                ext = ".png"
            fname = f"{stem}-{i+1}{ext}"
        else:
            fname = f"zairouter-{int(time.time())}-{i+1}.{output_format}"

        filepath = output_dir / fname
        filepath.write_bytes(img_bytes)
        saved.append(str(filepath))
        print(f"  ✅ 已保存: {filepath} ({len(img_bytes)//1024}KB)")

    return saved


def generate_series(config_path: str):
    """从 JSON 配置批量生成系列图。

    配置格式:
    {
      "output_dir": "./output",
      "size": "1024x1024",
      "quality": "high",
      "cards": [
        {"title": "封面", "prompt": "...", "filename": "01.png"},
        {"title": "图2", "prompt": "...", "filename": "02.png", "n": 2}
      ]
    }
    """
    with open(config_path) as f:
        config = json.load(f)

    cards = config.get("cards", [])
    output_dir = config.get("output_dir", "output")
    size = config.get("size", "1024x1024")
    quality = config.get("quality", "high")
    output_format = config.get("output_format", "png")

    total = len(cards)
    all_saved = []

    for i, card in enumerate(cards, 1):
        prompt = card.get("prompt", "")
        filename = card.get("filename", f"{i:02d}.png")
        n = card.get("n", 1)
        card_size = card.get("size", size)
        card_quality = card.get("quality", quality)

        print(f"\n{'='*50}")
        print(f"📷 [{i}/{total}] {card.get('title', '无标题')}")

        saved = generate(
            prompt=prompt,
            size=card_size,
            quality=card_quality,
            output_format=output_format,
            n=n,
            output_dir=output_dir,
            filename=filename,
        )
        all_saved.extend(saved)

        if i < total:
            print("  ⏳ 等待 2s ...")
            time.sleep(2)

    print(f"\n🎉 系列图完成！共 {total} 组，{len(all_saved)} 张")
    print(f"   保存目录: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="zairouter GPT-Image-2 图片生成客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
尺寸快捷映射（ZAI Router max 边 ≤ 3840）:
  1:1            1024x1024     (正方形，默认)
  1:1-2k         2048x2048     (正方形 2K)
  21:9           1248x528      (电影宽幅，封面图)
  21:9-2k        2688x1152     (宽幅 2K)
  21:9-4k        3840x1648     (宽幅 4K)
  16:9           1024x576
  16:9-4k        3840x2160     (4K 横版，实测通过)
  9:16-4k        2160x3840     (4K 竖版，实测通过)
  3:4            768x1024      (小红书竖版)

示例:
  python zairouter_client.py --prompt "一只猫" --size 1:1 --output cat.png
  python zairouter_client.py --prompt "一只猫" --n 4 --output-dir ./cats
  python zairouter_client.py --prompt "..." --size 21:9-4k --output cover.png
  python zairouter_client.py --config cards.json
        """,
    )
    parser.add_argument("--prompt", help="生成提示词")
    parser.add_argument("--size", default="1:1",
                        help="尺寸 (1:1, 1:1-2k, 21:9, 21:9-2k, 21:9-4k, 16:9, 16:9-4k, 或直接写 WxH)")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high"])
    parser.add_argument("--output-format", default="png", choices=["png", "jpeg", "webp"])
    parser.add_argument("--n", type=int, default=1, help="一次生成几张")
    parser.add_argument("--output", default="", help="输出文件名 (单张时使用)")
    parser.add_argument("--output-dir", default=".", help="输出目录")
    parser.add_argument("--config", help="批量生成 JSON 配置文件")
    parser.add_argument("--check", action="store_true", help="检查 API key")
    args = parser.parse_args()

    if args.check:
        key = _api_key()
        print(f"✅ ZAI_API_KEY 已配置 ({key[:8]}...{key[-4:]})")
    elif args.config:
        generate_series(args.config)
    elif args.prompt:
        generate(
            prompt=args.prompt,
            size=args.size,
            quality=args.quality,
            output_format=args.output_format,
            n=args.n,
            output_dir=args.output_dir,
            filename=args.output,
        )
    else:
        parser.print_help()
