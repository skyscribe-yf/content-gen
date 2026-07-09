"""
廉价图片生成客户端 — 用于要求不高的低质量图片

⚠️  高质量图片请用 xabc_client.py；本脚本只走廉价 API

支持的提供商（按价格排序）:
  minimax   MiniMax Image 01,  $0.0035/张  — 最便宜
  nanobanana Gemini 2.5 Flash, ~$0.02/张   — 性价比均衡
  sparkpix  SparkPix Image,    $0.008/张   — 亚秒级出图

环境变量（自动从项目根 .env 读取）:
  MINIMAX_API_KEY     — MiniMax/Image 01 的 API Key
  NANOBANANA_API_KEY  — Nano Banana (reapi / PiAPI / apimodels) 的 API Key
  NANOBANANA_BASE_URL — Nano Banana API 地址（默认 reapi）
  SPARKPIX_API_KEY    — SparkPix API Key
  SPARKPIX_BASE_URL   — SparkPix API 地址（默认 apimodels）

用法:
  # 单张生成（默认 minimax）
  python cheap_img_client.py --prompt "渐变色的抽象背景" --provider minimax

  # 指定提供商和尺寸
  python cheap_img_client.py --prompt "小红书封面" --provider nanobanana --size 3:4

  # 批量系列图（从 JSON 配置）
  python cheap_img_client.py --config ../content/example-series-cheap.json

  # 查看所有提供商余额/状态
  python cheap_img_client.py --check
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


# ── .env 自动加载 ──

def _load_dotenv():
    """从项目根 .env 文件加载变量到 os.environ（不覆盖已有值）"""
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


_load_dotenv()


# ── 提供商配置 ──

PROVIDERS = {
    "minimax": {
        "base_url": "https://api.minimaxi.com",
        "key_env": "MINIMAX_API_KEY",
        "price": "$0.0035/张",
    },
    "nanobanana": {
        "base_url": "https://reapi.ai",
        "key_env": "NANOBANANA_API_KEY",
        "base_url_env": "NANOBANANA_BASE_URL",
        "price": "~$0.02/张",
    },
    "sparkpix": {
        "base_url": "https://apimodels.app",
        "key_env": "SPARKPIX_API_KEY",
        "base_url_env": "SPARKPIX_BASE_URL",
        "price": "$0.008/张",
    },
}


def _get_key(provider: str) -> str:
    cfg = PROVIDERS[provider]
    key = os.environ.get(cfg["key_env"], "").strip()
    if not key:
        sys.exit(f"❌ 请在 .env 中设置 {cfg['key_env']}")
    return key


def _get_base_url(provider: str) -> str:
    cfg = PROVIDERS[provider]
    custom = os.environ.get(cfg.get("base_url_env", ""), "").strip()
    return custom or cfg["base_url"]


# ── MiniMax Image 01 ──

def minimax_generate(prompt: str, size: str = "3:4", resolution: str = "1K",
                     n: int = 1, output_dir: str = ".") -> list[str]:
    key = _get_key("minimax")
    base = _get_base_url("minimax")

    resp = requests.post(
        f"{base}/v1/image_generation",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "image-01",
            "prompt": prompt,
            "aspect_ratio": size,
            "n": n,
            "response_format": "url",
            "prompt_optimizer": True,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    # MiniMax 直接返回结果，无需轮询
    base_resp = data.get("data", {})
    images = base_resp.get("image_urls", []) or []

    if not images:
        # ponytail: 也检查嵌套格式
        images = [
            item.get("url", "") if isinstance(item, dict) else str(item)
            for item in (base_resp.get("images", []) or data.get("images", []))
        ]
        images = [u for u in images if u]

    if not images:
        sys.exit(f"❌ 无图片返回: {json.dumps(data, ensure_ascii=False)[:300]}")

    # 保存
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, url in enumerate(images):
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        path = output_dir / f"cheap-minimax-{int(time.time())}-{i+1}.png"
        path.write_bytes(r.content)
        saved.append(str(path))
        print(f"  ✅ 已保存: {path} ({len(r.content)//1024}KB)")

    return saved


# ── Nano Banana (Gemini 2.5 Flash Image) ──

def nanobanana_generate(prompt: str, size: str = "3:4", n: int = 1,
                        output_dir: str = ".") -> list[str]:
    key = _get_key("nanobanana")
    base = _get_base_url("nanobanana")

    resp = requests.post(
        f"{base}/api/v1/images/generations",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "gemini-2.5-flash-image-preview",
            "prompt": prompt,
            "size": size,
            "n": n,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    # 异步模式：拿到 task_id 后轮询
    task_id = data.get("task_id") or data.get("id")
    if task_id and not data.get("data"):
        print(f"  📤 异步任务: {task_id}")
        for _ in range(90):
            time.sleep(2)
            r = requests.get(
                f"{base}/api/v1/tasks/{task_id}",
                headers={"Authorization": f"Bearer {key}"},
                timeout=30,
            )
            r.raise_for_status()
            status = r.json()
            if status.get("status") in ("completed", "succeeded"):
                data = status
                break
            if status.get("status") in ("failed", "error"):
                sys.exit(f"❌ 任务失败: {status}")
            print(f"  ⏳ 状态: {status.get('status')}...")

    return _save_urls(data, "nanobanana", output_dir)


# ── SparkPix Image ──

def sparkpix_generate(prompt: str, size: str = "3:4", n: int = 1,
                      output_dir: str = ".") -> list[str]:
    key = _get_key("sparkpix")
    base = _get_base_url("sparkpix")

    resp = requests.post(
        f"{base}/api/v1/images/generations",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "sparkpix-image",
            "prompt": prompt,
            "size": size,
            "n": n,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    # 异步轮询
    task_id = data.get("task_id") or data.get("id")
    if task_id and not data.get("data"):
        print(f"  📤 异步任务: {task_id}")
        for _ in range(60):
            time.sleep(2)
            r = requests.get(
                f"{base}/api/v1/tasks/{task_id}",
                headers={"Authorization": f"Bearer {key}"},
                timeout=30,
            )
            r.raise_for_status()
            status = r.json()
            if status.get("status") in ("completed", "succeeded"):
                data = status
                break
            if status.get("status") in ("failed", "error"):
                sys.exit(f"❌ 任务失败: {status}")

    return _save_urls(data, "sparkpix", output_dir)


# ── 通用保存 ──

def _save_urls(data: dict, provider: str, output_dir: str) -> list[str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    items = data.get("data", [])
    for i, item in enumerate(items):
        url = item.get("url", "") if isinstance(item, dict) else str(item)
        b64 = item.get("b64_json", "") if isinstance(item, dict) else ""

        if b64:
            img_bytes = base64.b64decode(b64)
        elif url:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            img_bytes = r.content
        else:
            continue

        path = output_dir / f"cheap-{provider}-{int(time.time())}-{i+1}.png"
        path.write_bytes(img_bytes)
        saved.append(str(path))
        print(f"  ✅ 已保存: {path} ({len(img_bytes)//1024}KB)")

    if not saved:
        print("⚠️ 无图片返回")
    return saved


# ── 批量系列图 ──

def generate_series(config_path: str, provider: str = "minimax"):
    with open(config_path) as f:
        config = json.load(f)

    series_title = config.get("series_title", "系列")
    cards = config.get("cards", [])
    output_dir = config.get("output_dir", "output")
    size = config.get("size", "3:4")
    resolution = config.get("resolution", "1K")

    total = len(cards)
    all_saved = []

    gen_fn = {
        "minimax": lambda p: minimax_generate(p, size, resolution, 1, output_dir),
        "nanobanana": lambda p: nanobanana_generate(p, size, 1, output_dir),
        "sparkpix": lambda p: sparkpix_generate(p, size, 1, output_dir),
    }[provider]

    for i, card in enumerate(cards, 1):
        prompt = card.get("prompt", "")
        filename = card.get("filename", f"{i:02d}.png")
        print(f"\n{'='*50}")
        print(f"📷 [{i}/{total}] {card.get('title', '无标题')}")

        saved = gen_fn(prompt)

        # 重命名
        for j, path in enumerate(saved):
            if j == 0 and filename:
                new_path = str(Path(output_dir) / filename)
                Path(path).rename(new_path)
                all_saved.append(new_path)
            else:
                all_saved.append(path)

    print(f"\n🎉 系列图完成！共 {total} 组，{len(all_saved)} 张")
    print(f"   保存目录: {output_dir}")


# ── 状态检查 ──

def check_providers():
    print("提供商状态:\n")
    for name, cfg in PROVIDERS.items():
        key = os.environ.get(cfg["key_env"], "").strip()
        status = "✅ 已配置" if key else "❌ 未配置"
        print(f"  {name:12s}  {status}  ({cfg['price']})  环境变量: {cfg['key_env']}")
    print()


# ── CLI ──

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="廉价图片生成客户端（低质量/低成本）")
    parser.add_argument("--prompt", help="生成提示词")
    parser.add_argument("--provider", default="minimax",
                        choices=["minimax", "nanobanana", "sparkpix"],
                        help="提供商（默认 minimax 最便宜）")
    parser.add_argument("--size", default="3:4",
                        help="宽高比，如 1:1 3:4 16:9 9:16（默认 3:4）")
    parser.add_argument("--resolution", default="1K", choices=["1K", "2K"],
                        help="分辨率，仅 minimax 支持（默认 1K）")
    parser.add_argument("--n", type=int, default=1, help="生成数量")
    parser.add_argument("--output-dir", default=".", help="输出目录")
    parser.add_argument("--config", help="批量生成 JSON 配置文件")
    parser.add_argument("--check", action="store_true", help="检查提供商配置状态")
    args = parser.parse_args()

    if args.check:
        check_providers()
    elif args.config:
        generate_series(args.config, args.provider)
    elif args.prompt:
        fn = {
            "minimax": lambda: minimax_generate(args.prompt, args.size, args.resolution, args.n, args.output_dir),
            "nanobanana": lambda: nanobanana_generate(args.prompt, args.size, args.n, args.output_dir),
            "sparkpix": lambda: sparkpix_generate(args.prompt, args.size, args.n, args.output_dir),
        }[args.provider]
        print(f"📤 使用 {args.provider} ({PROVIDERS[args.provider]['price']}) 生成图片...")
        fn()
    else:
        parser.print_help()
