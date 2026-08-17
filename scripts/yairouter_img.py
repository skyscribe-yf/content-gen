"""
yairouter 高质量图片生成客户端 — gpt-image-2（自动 fallback grok-imagine-image-quality）

yairouter API 配置（实测 2026-08-07）：
  端点: https://api.yairouter.com/v1/images/generations
  模型: gpt-image-2（默认）/ grok-imagine-image-quality（备选）
  认证: Authorization: Bearer $YAI_API_KEY（shell 环境变量优先，.env 兜底）
  质量: high

⚠️ 已知问题：
  1. 上游 API 忽略 size 参数（实测请求任意 size 均返回 1254x1254 / 1536x1024 /
     1024x1536 等随机尺寸），详见 docs/yairouter-gpt-image-2-experiment.md。
     本工具按实际输出保存，不做裁剪。
  2. 2026-08-15 实测：gpt-image-2 对该 team 返回 404 无权限 + size 参数被 400 拒绝
     （"Argument not supported: size"）；grok-imagine-image-quality 可用，但要求
     response_format=b64_json（Zero Data Retention team 无 URL 格式）、不支持 size
     参数、输出固定 1024x1024 JPEG。脚本在 gpt-image-2 失败时自动 fallback 到
     grok，并把 JPEG 字节转成真 PNG 保存。

✅ 质量核查：每张生成后自动读取实际尺寸并与请求尺寸比对，不符时
打印 ⚠️ 通知；批量模式结束时汇总不符清单。

用法:
  # 单张生成
  python yairouter_img.py --prompt "..." --size 1024x1536 --output card.png

  # 显式指定 grok 模型（跳过 gpt-image-2 探测）
  python yairouter_img.py --prompt "..." --model grok-imagine-image-quality --output card.png

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
    key = os.environ.get("YAI_API_KEY", "").strip()
    if not key:
        sys.exit("❌ 请设置 YAI_API_KEY 环境变量（export YAI_API_KEY=...）或在 .env 中配置")
    return key


# 尺寸映射：小红书 3:4 竖版
SIZE_MAP = {
    "3:4": "1024x1536",
    "1:1": "1024x1024",
    "16:9": "1792x1024",
    "2.35:1": "1792x768",
}

# 备选模型：gpt-image-2 不可用时自动 fallback
FALLBACK_MODEL = "grok-imagine-image-quality"
# grok 模型：不支持 size 参数、要求 b64_json、输出固定 1024x1024 JPEG
GROK_OUTPUT_SIZE = "1024x1024"

# 尺寸核查记录（批量模式汇总用）
_size_mismatches: list[tuple[str, str, str]] = []


def _check_size(filepath: Path, requested: str) -> bool:
    """质量核查：读取实际图片尺寸，与请求尺寸不符时通知用户。

    上游已知忽略 size 参数（见 docs/yairouter-gpt-image-2-experiment.md），
    因此尺寸不符不是脚本 bug，但仍需显式告知用户，避免误用。
    """
    try:
        from PIL import Image
        with Image.open(filepath) as im:
            actual = f"{im.width}x{im.height}"
    except ImportError:
        print(f"  ⚠️ 缺少 Pillow，无法核查尺寸: {filepath}")
        return False

    req = requested.lower()
    if actual != req:
        print(f"  ⚠️ 尺寸不符: 请求 {req}，实际 {actual}（上游忽略 size 参数）")
        _size_mismatches.append((str(filepath), req, actual))
        return False
    print(f"  ✅ 尺寸核查通过: {actual}")
    return True


def generate(
    prompt: str,
    size: str = "1024x1536",
    quality: str = "high",
    n: int = 1,
    output_dir: str = ".",
    filename: str = "",
    model: str = "gpt-image-2",
) -> list[str]:
    """生成图片并保存。gpt-image-2 失败时自动 fallback 到 grok-imagine-image-quality。"""
    key = _api_key()

    # 解析尺寸
    if size in SIZE_MAP:
        size = SIZE_MAP[size]

    def _payload(m):
        p = {"model": m, "prompt": prompt, "n": n, "quality": quality}
        if m == FALLBACK_MODEL:
            # grok：Zero Data Retention team 只能用 b64_json，不支持 size
            p["response_format"] = "b64_json"
        else:
            p["size"] = size
        return p

    print(f"📤 提交 {model} (size={size if model != FALLBACK_MODEL else GROK_OUTPUT_SIZE}, quality={quality}, n={n})")
    print(f"   Prompt: {prompt[:80]}...")

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json=_payload(model),
        timeout=180,
    )

    # gpt-image-2 失败（404 无权限 / 400 参数拒绝等）→ 自动 fallback grok
    if resp.status_code != 200 and model != FALLBACK_MODEL:
        print(f"❌ {model} 返回 {resp.status_code}: {resp.text[:200]}")
        print(f"🔄 自动改用 {FALLBACK_MODEL} 重试...")
        model = FALLBACK_MODEL
        resp = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=_payload(model),
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
        # grok 返回 JPEG 字节：扩展名是 .png 时转成真 PNG，避免微信上传格式不匹配
        if fname.lower().endswith(".png"):
            try:
                from PIL import Image
                import io
                im = Image.open(io.BytesIO(img_bytes))
                if im.format != "PNG":
                    buf = io.BytesIO()
                    im.convert("RGB").save(buf, "PNG")
                    img_bytes = buf.getvalue()
                    print(f"  🔄 {fname}: {im.format} 字节 → 真 PNG")
            except Exception:
                pass
        filepath.write_bytes(img_bytes)
        saved.append(str(filepath))
        print(f"  ✅ 已保存: {filepath} ({len(img_bytes)//1024}KB)")
        _check_size(filepath, GROK_OUTPUT_SIZE if model == FALLBACK_MODEL else size)

    return saved


def generate_series(config_path: str):
    """从 cards.json 批量生成系列图"""
    with open(config_path) as f:
        config = json.load(f)

    cards = config.get("cards", [])
    output_dir = config.get("output_dir", "output")
    # gpt-image-2 不用 model/quality 字段，直接用默认；cards.json 可覆盖
    size = config.get("size", "1024x1536")
    quality = config.get("quality", "high")
    default_model = config.get("model", "gpt-image-2")

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
            model=card.get("model", default_model),
        )
        all_saved.extend(saved)

        # 限速：避免 API 限流
        if i < total:
            print("  ⏳ 等待 3s 避免限流...")
            time.sleep(3)

    print(f"\n🎉 系列图完成！共 {total} 组，{len(all_saved)} 张")
    print(f"   保存目录: {output_dir}")

    if _size_mismatches:
        print(f"\n⚠️ 尺寸核查: {len(_size_mismatches)} 张与请求尺寸不符（上游忽略 size 参数）:")
        for path, req, actual in _size_mismatches:
            print(f"   - {path}  请求 {req} → 实际 {actual}")
        print("   如需精确尺寸，请裁剪或换用支持尺寸的生成方式（见 docs/yairouter-gpt-image-2-experiment.md）")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="yairouter 图片生成（gpt-image-2，自动 fallback grok-imagine-image-quality）")
    parser.add_argument("--prompt", help="生成提示词")
    parser.add_argument("--size", default="1024x1536", help="尺寸 (默认 1024x1536；grok 模型忽略此参数)")
    parser.add_argument("--model", default="gpt-image-2", choices=["gpt-image-2", "grok-imagine-image-quality"], help="模型 (默认 gpt-image-2，失败自动 fallback grok)")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"])
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--filename", default="", help="输出文件名")
    parser.add_argument("--config", help="cards.json 批量生成")
    parser.add_argument("--check", action="store_true", help="检查 API key")
    args = parser.parse_args()

    if args.check:
        key = _api_key()
        print(f"✅ YAI_API_KEY 已配置 ({key[:8]}...{key[-4:]})")
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
            model=args.model,
        )
    else:
        parser.print_help()
