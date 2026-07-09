"""
xabcimg.com 高质量 AI 图片生成客户端

⚠️  仅用于需要 AI 生成的高质量图片，普通信息图请用 xhs_card.py（本地 Pillow，零费用）

用法:
  # 单张生成（session 自动从 .env 读取，无需手动传入）
  python xabc_client.py \
    --prompt "小红书风格知识科普卡片..." \
    --size 1024x1536 --quality high --n 1

  # 批量系列图（从 JSON 配置）
  python xabc_client.py --config ../content/example-series-xabc.json

  # 查询余额
  python xabc_client.py --balance

环境变量:
  XABC_MING_SESSION  — 必填，自动从项目根 .env 文件读取，也可通过环境变量注入

默认参数（成本控制）:
  - size: 1024x1024（最便宜）
  - quality: medium
  若用户未显式指定 size/quality，一律用这两个值。用户要更高质量（high / 更大尺寸）时，
  必须先告知费用并要求确认，得到明确同意后才生成。
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

# ponytail: requests 是 stdlib 之外唯一的依赖，但大部分系统都有
try:
    import requests
except ImportError:
    sys.exit("需要 requests: pip install requests")

BASE_URL = "https://xabcimg.com"
POLL_INTERVAL = 2  # 秒
POLL_TIMEOUT = 180  # 3分钟超时


def _load_dotenv():
    """从项目根 .env 文件加载变量到 os.environ（不覆盖已有值）"""
    # 向上查找项目根（含 .git 或 .env 的目录）
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


def _session() -> str:
    _load_dotenv()
    s = os.environ.get("XABC_MING_SESSION", "").strip()
    if not s:
        sys.exit("❌ 请在项目根目录 .env 文件中设置 XABC_MING_SESSION=xxx")
    return s


def _api(path: str, method: str = "GET", **kwargs) -> dict:
    """调用 xabcimg API"""
    url = f"{BASE_URL}{path}"
    cookies = {"xabcimg_session": _session()}
    resp = requests.request(method, url, cookies=cookies, timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json()


def get_balance() -> dict:
    """查询余额"""
    return _api("/api/balance")


def submit_generate(
    prompt: str,
    model: str = "gpt-image-2",
    size: str = "1024x1024",
    quality: str = "medium",
    n: int = 1,
    output_format: str = "png",
) -> dict:
    """提交生成任务"""
    data = {
        "operation": "generate",
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": str(n),
        "output_format": output_format,
    }
    # API expects multipart/form-data; tuple form ("", value) sends as field not file
    multipart = {k: ("", str(v)) for k, v in data.items()}
    return _api("/api/images", method="POST", files=multipart)


def poll_job(job_id: int) -> dict:
    """轮询任务直到完成"""
    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        job = _api(f"/api/images/{job_id}")
        status = job.get("status", "")
        if status == "succeeded":
            return job
        if status == "failed":
            sys.exit(f"❌ 任务 {job_id} 失败: {job}")
        print(f"  ⏳ 任务 #{job_id} 状态: {status}，{POLL_INTERVAL}s 后重试...")
        time.sleep(POLL_INTERVAL)
    sys.exit(f"❌ 任务 {job_id} 超时 ({POLL_TIMEOUT}s)")


def save_results(job: dict, output_dir: str = ".") -> list[str]:
    """从完成的任务中保存图片"""
    items = job.get("response", {}).get("data", [])
    if not items:
        print("⚠️ 任务完成但无图片返回")
        return []

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for i, item in enumerate(items):
        # 优先 b64_json，其次 url
        b64 = item.get("b64_json", "").strip()
        url = item.get("url", "").strip()

        if b64:
            img_bytes = base64.b64decode(b64)
        elif url:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            img_bytes = resp.content
        else:
            print(f"  ⚠️ 第 {i+1} 张图无数据")
            continue

        fmt = job.get("output_format", "png")
        ext = "jpg" if fmt == "jpeg" else fmt
        filename = f"image-{job['id']}-{i+1}.{ext}"
        filepath = output_dir / filename
        filepath.write_bytes(img_bytes)
        saved.append(str(filepath))
        print(f"  ✅ 已保存: {filepath} ({len(img_bytes)//1024}KB)")

    return saved


def generate_and_save(
    prompt: str,
    output_dir: str = ".",
    model: str = "gpt-image-2",
    size: str = "1024x1024",
    quality: str = "medium",
    n: int = 1,
    output_format: str = "png",
) -> list[str]:
    """一键：提交 → 轮询 → 保存"""
    print(f"📤 提交生成任务 (model={model}, size={size}, quality={quality}, n={n})")
    job = submit_generate(prompt, model, size, quality, n, output_format)
    job_id = job.get("id")
    if not job_id:
        sys.exit(f"❌ 提交失败: {job}")
    print(f"  任务 #{job_id} 已提交")

    job = poll_job(job_id)
    return save_results(job, output_dir)


def generate_series(config_path: str):
    """从 JSON 配置批量生成系列图"""
    with open(config_path) as f:
        config = json.load(f)

    series_title = config.get("series_title", "系列")
    cards = config.get("cards", [])
    output_dir = config.get("output_dir", "output")
    model = config.get("model", "gpt-image-2")
    size = config.get("size", "1024x1024")
    quality = config.get("quality", "medium")
    output_format = config.get("output_format", "png")

    total = len(cards)
    all_saved = []

    for i, card in enumerate(cards, 1):
        prompt = card.get("prompt", "")
        n = card.get("n", 1)
        filename = card.get("filename", f"{i:02d}.png")

        print(f"\n{'='*50}")
        print(f"📷 [{i}/{total}] {card.get('title', '无标题')}")
        print(f"   Prompt: {prompt[:80]}...")

        saved = generate_and_save(
            prompt=prompt,
            output_dir=output_dir,
            model=model,
            size=size,
            quality=quality,
            n=n,
            output_format=output_format,
        )

        # 重命名为配置中的 filename
        for j, path in enumerate(saved):
            if j == 0 and filename:
                new_path = str(Path(output_dir) / filename)
                Path(path).rename(new_path)
                all_saved.append(new_path)
            else:
                all_saved.append(path)

    print(f"\n🎉 系列图生成完毕！共 {total} 组，{len(all_saved)} 张")
    print(f"   保存目录: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="xabcimg.com 图片生成客户端")
    parser.add_argument("--prompt", help="生成提示词")
    parser.add_argument("--model", default="gpt-image-2", help="模型 (默认 gpt-image-2)")
    parser.add_argument("--size", default="1024x1024", help="尺寸 (默认 1024x1024，成本最低)")
    parser.add_argument("--quality", default="medium", choices=["low", "medium", "high", "auto"])
    parser.add_argument("--n", type=int, default=1, help="生成数量 (1-10)")
    parser.add_argument("--format", default="png", choices=["png", "jpeg", "webp"], dest="output_format")
    parser.add_argument("--output-dir", default=".", help="输出目录")
    parser.add_argument("--config", help="批量生成 JSON 配置文件")
    parser.add_argument("--balance", action="store_true", help="查询余额")
    args = parser.parse_args()

    if args.balance:
        data = get_balance()
        credits = data.get("credits_milli", 0)
        print(f"💰 余额: {credits / 1000:.1f} 图点")
    elif args.config:
        generate_series(args.config)
    elif args.prompt:
        generate_and_save(
            prompt=args.prompt,
            output_dir=args.output_dir,
            model=args.model,
            size=args.size,
            quality=args.quality,
            n=args.n,
            output_format=args.output_format,
        )
    else:
        parser.print_help()
