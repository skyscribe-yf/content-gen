"""
apimart.ai GPT-Image-2 图片生成客户端（首选后端）

⚠️  本工具为项目首选图片生成后端，优先于 xabcimg。

用法:
  # 单张生成（API key 自动从 .env 读取）
  python apimart_client.py \
    --prompt "小红书风格知识科普卡片..." \
    --size 16:9 --resolution 2k

  # 批量系列图（从 JSON 配置）
  python apimart_client.py --config ../content/example-series-apimart.json

  # 查询任务状态
  python apimart_client.py --status task_01KPQ7J7DWB7QZ3WCEK3YVPBRA

环境变量:
  API_MART_KEY  — 必填，自动从项目根 .env 文件读取

默认参数（成本控制）:
  - size: 1:1（正方形，最便宜）
  - resolution: 1k
  若用户未显式指定 size/resolution，一律用这两个值。
  需要更高分辨率（2k/4k）时，必须先告知费用差异并要求确认。

API 流程:
  1. POST /v1/images/generations → 返回 task_id
  2. 立即写入 output_dir/.apimart-tasks.json，后续重跑先复用未失败 task
  3. GET  /v1/tasks/{task_id}    → 轮询直到 completed
  4. 从 result.images[0].url[0]  下载图片

文档: https://docs.apimart.ai/cn/api-reference/images/gpt-image-2/generation
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("需要 requests: pip install requests")

BASE_URL = "https://api.apimart.ai/v1"
POLL_INTERVAL = 3  # 秒
POLL_TIMEOUT = 300  # 5分钟超时（4K 图可能较慢）

# ── size × resolution 完整对照表 ──────────────────────────────
# key = (size, resolution), value = 实际像素
SIZE_MAP = {
    # 1k
    ("1:1",  "1k"): "1024x1024",
    ("3:2",  "1k"): "1536x1024",
    ("2:3",  "1k"): "1024x1536",
    ("4:3",  "1k"): "1024x768",
    ("3:4",  "1k"): "768x1024",
    ("16:9", "1k"): "1024x576",
    ("9:16", "1k"): "576x1024",
    ("2:1",  "1k"): "1536x768",
    ("1:2",  "1k"): "768x1536",
    ("3:1",  "1k"): "1536x512",
    ("1:3",  "1k"): "512x1536",
    ("21:9", "1k"): "1915x821",
    ("9:21", "1k"): "821x1915",
    # 2k
    ("1:1",  "2k"): "2048x2048",
    ("3:2",  "2k"): "2048x1360",
    ("2:3",  "2k"): "1360x2048",
    ("4:3",  "2k"): "2048x1536",
    ("3:4",  "2k"): "1536x2048",
    ("16:9", "2k"): "2048x1152",
    ("9:16", "2k"): "1152x2048",
    ("2:1",  "2k"): "2688x1344",
    ("1:2",  "2k"): "1344x2688",
    ("3:1",  "2k"): "3072x1024",
    ("1:3",  "2k"): "1024x3072",
    ("21:9", "2k"): "2688x1152",
    ("9:21", "2k"): "1152x2688",
    # 4k
    ("1:1",  "4k"): "2880x2880",
    ("3:2",  "4k"): "3520x2336",
    ("2:3",  "4k"): "2336x3520",
    ("4:3",  "4k"): "3312x2480",
    ("3:4",  "4k"): "2480x3312",
    ("16:9", "4k"): "3840x2160",
    ("9:16", "4k"): "2160x3840",
    ("2:1",  "4k"): "3840x1920",
    ("1:2",  "4k"): "1920x3840",
    ("3:1",  "4k"): "3840x1280",
    ("1:3",  "4k"): "1280x3840",
    ("21:9", "4k"): "3840x1648",
    ("9:21", "4k"): "1648x3840",
}

VALID_SIZES = sorted({k[0] for k in SIZE_MAP})
VALID_RESOLUTIONS = ["1k", "2k", "4k"]
MANIFEST_NAME = ".apimart-tasks.json"
FAILED_STATUSES = {"failed", "cancelled", "expired", "error"}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _task_inner(task_data: dict) -> dict:
    return task_data.get("data", task_data)


def _task_status(task_data: dict) -> str:
    return _task_inner(task_data).get("status", "")


def _prompt_fingerprint(
    prompt: str,
    size: str,
    resolution: str,
    n: int,
    image_urls: list[str] | None = None,
    official_fallback: bool = False,
) -> str:
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "n": n,
        "size": size,
        "resolution": resolution,
        "image_urls": image_urls or [],
        "official_fallback": official_fallback,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _manifest_path(output_dir: str | Path) -> Path:
    return Path(output_dir) / MANIFEST_NAME


def _load_manifest(output_dir: str | Path) -> dict:
    path = _manifest_path(output_dir)
    if not path.exists():
        return {"version": 1, "tasks": []}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        sys.exit(f"❌ {path} 已损坏，拒绝提交新任务以避免重复扣费: {exc}")
    data.setdefault("version", 1)
    data.setdefault("tasks", [])
    return data


def _save_manifest(output_dir: str | Path, manifest: dict):
    path = _manifest_path(output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    tmp.replace(path)


def _find_manifest_task(manifest: dict, fingerprint: str) -> dict | None:
    for task in reversed(manifest.get("tasks", [])):
        if task.get("fingerprint") == fingerprint:
            return task
    return None


def _upsert_manifest_task(output_dir: str | Path, record: dict):
    manifest = _load_manifest(output_dir)
    tasks = manifest.setdefault("tasks", [])
    tasks[:] = [t for t in tasks if t.get("fingerprint") != record.get("fingerprint")]
    tasks.append(record)
    _save_manifest(output_dir, manifest)


def _update_manifest_task(output_dir: str | Path, fingerprint: str, **fields):
    manifest = _load_manifest(output_dir)
    task = _find_manifest_task(manifest, fingerprint)
    if not task:
        return
    task.update(fields)
    task["updated_at"] = _now_iso()
    _save_manifest(output_dir, manifest)


def _extract_task_id(resp: dict) -> str | None:
    items = resp.get("data", [])
    if isinstance(items, dict):
        items = [items]
    if not items:
        return None
    return items[0].get("task_id") or items[0].get("id")


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


def _api_key() -> str:
    _load_dotenv()
    key = os.environ.get("API_MART_KEY", "").strip()
    if not key:
        sys.exit("❌ 请在项目根目录 .env 文件中设置 API_MART_KEY=xxx")
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def _api(path: str, method: str = "GET", **kwargs) -> dict:
    """调用 apimart API"""
    url = f"{BASE_URL}{path}"
    resp = requests.request(method, url, headers=_headers(), timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json()


def submit_generate(
    prompt: str,
    size: str = "1:1",
    resolution: str = "1k",
    n: int = 1,
    image_urls: list[str] | None = None,
    official_fallback: bool = False,
) -> dict:
    """提交图片生成任务，返回含 task_id 的响应"""
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "n": n,
        "size": size,
        "resolution": resolution,
    }
    if image_urls:
        payload["image_urls"] = image_urls
    if official_fallback:
        payload["official_fallback"] = True
    return _api("/images/generations", method="POST", json=payload)


def poll_task(task_id: str, on_status=None) -> dict:
    """轮询任务直到完成，返回完整任务数据"""
    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        data = _api(f"/tasks/{task_id}")
        if on_status:
            on_status(data)
        inner = _task_inner(data)
        status = inner.get("status", "")
        if status == "completed":
            return data
        if status == "failed":
            err = inner.get("error", {})
            sys.exit(f"❌ 任务 {task_id} 失败: {err.get('message', data)}")
        progress = inner.get("progress", "?")
        print(f"  ⏳ 任务 {task_id} 状态: {status} ({progress}%)，{POLL_INTERVAL}s 后重试...")
        time.sleep(POLL_INTERVAL)
    sys.exit(f"❌ 任务 {task_id} 超时 ({POLL_TIMEOUT}s)")


def save_results(task_data: dict, output_dir: str = ".") -> list[str]:
    """从完成的任务中下载并保存图片"""
    inner = task_data.get("data", task_data)
    images = inner.get("result", {}).get("images", [])
    if not images:
        print("⚠️ 任务完成但无图片返回")
        return []

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for i, img in enumerate(images):
        urls = img.get("url", [])
        if not urls:
            print(f"  ⚠️ 第 {i+1} 张图无 URL")
            continue
        img_url = urls[0]
        resp = requests.get(img_url, timeout=120)
        resp.raise_for_status()
        img_bytes = resp.content

        task_id = inner.get("id", "unknown")
        filename = f"{task_id}_{i+1}.png"
        filepath = output_dir / filename
        filepath.write_bytes(img_bytes)
        saved.append(str(filepath))
        print(f"  ✅ 已保存: {filepath} ({len(img_bytes)//1024}KB)")

    # 打印费用
    cost = inner.get("cost", 0)
    credits = inner.get("credits_cost", 0)
    if cost:
        print(f"  💰 费用: ${cost:.4f} (credits: {credits})")

    return saved


def generate_and_save(
    prompt: str,
    output_dir: str = ".",
    size: str = "1:1",
    resolution: str = "1k",
    n: int = 1,
    image_urls: list[str] | None = None,
    official_fallback: bool = False,
    filename: str | None = None,
) -> list[str]:
    """一键：复用已有 task 或提交 → 轮询 → 保存"""
    fingerprint = _prompt_fingerprint(prompt, size, resolution, n, image_urls, official_fallback)
    manifest = _load_manifest(output_dir)
    cached = _find_manifest_task(manifest, fingerprint)
    if cached and cached.get("status") not in FAILED_STATUSES:
        saved_paths = [p for p in cached.get("saved_paths", []) if Path(p).exists() and Path(p).stat().st_size > 0]
        if saved_paths:
            print(f"⏭️  已有生成结果，跳过提交: {saved_paths[0]}")
            return saved_paths
        task_id = cached.get("task_id")
        if not task_id:
            sys.exit(f"❌ {MANIFEST_NAME} 里已有同 prompt 的非失败记录但缺少 task_id，拒绝重新提交以避免重复扣费")
        print(f"♻️  复用已提交任务 {task_id}（status={cached.get('status', 'unknown')}），不重新提交")
        task_data = poll_task(
            task_id,
            on_status=lambda data: _update_manifest_task(output_dir, fingerprint, status=_task_status(data)),
        )
        saved = save_results(task_data, output_dir)
        _update_manifest_task(output_dir, fingerprint, status="completed", saved_paths=saved)
        return saved

    pixels = SIZE_MAP.get((size, resolution), "unknown")
    print(f"📤 提交生成任务 (size={size}, resolution={resolution}, pixels={pixels}, n={n})")
    resp = submit_generate(prompt, size, resolution, n, image_urls, official_fallback)
    task_id = _extract_task_id(resp)
    if not task_id:
        sys.exit(f"❌ 提交失败（无 task_id）: {resp}")
    _upsert_manifest_task(output_dir, {
        "fingerprint": fingerprint,
        "task_id": task_id,
        "status": "submitted",
        "filename": filename,
        "size": size,
        "resolution": resolution,
        "n": n,
        "submitted_at": _now_iso(),
        "updated_at": _now_iso(),
    })
    print(f"  任务 {task_id} 已提交")

    task_data = poll_task(
        task_id,
        on_status=lambda data: _update_manifest_task(output_dir, fingerprint, status=_task_status(data)),
    )
    saved = save_results(task_data, output_dir)
    _update_manifest_task(output_dir, fingerprint, status="completed", saved_paths=saved)
    return saved


def get_task_status(task_id: str) -> dict:
    """查询任务状态"""
    return _api(f"/tasks/{task_id}")


def generate_series(config_path: str):
    """从 JSON 配置批量生成系列图"""
    with open(config_path) as f:
        config = json.load(f)

    series_title = config.get("series_title", "系列")
    cards = config.get("cards", [])
    output_dir = config.get("output_dir", "output")
    size = config.get("size", "1:1")
    resolution = config.get("resolution", "1k")

    total = len(cards)
    all_saved = []

    for i, card in enumerate(cards, 1):
        prompt = card.get("prompt", "")
        n = card.get("n", 1)
        filename = card.get("filename", f"{i:02d}.png")
        card_size = card.get("size", size)
        card_res = card.get("resolution", resolution)
        final_path = Path(output_dir) / filename

        print(f"\n{'='*50}")
        print(f"📷 [{i}/{total}] {card.get('title', '无标题')}")
        print(f"   Prompt: {prompt[:80]}...")

        if final_path.exists() and final_path.stat().st_size > 0:
            print(f"⏭️  已存在，跳过: {final_path}")
            all_saved.append(str(final_path))
            continue

        saved = generate_and_save(
            prompt=prompt,
            output_dir=output_dir,
            size=card_size,
            resolution=card_res,
            n=n,
            filename=filename,
        )

        # 重命名为配置中的 filename
        renamed = []
        for j, path in enumerate(saved):
            if j == 0 and filename:
                new_path = Path(output_dir) / filename
                if Path(path).resolve() != new_path.resolve():
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    Path(path).replace(new_path)
                renamed.append(str(new_path))
            else:
                renamed.append(path)
        all_saved.extend(renamed)
        fingerprint = _prompt_fingerprint(prompt, card_size, card_res, n)
        _update_manifest_task(output_dir, fingerprint, status="completed", filename=filename, saved_paths=renamed)

    print(f"\n🎉 系列图生成完毕！共 {total} 组，{len(all_saved)} 张")
    print(f"   保存目录: {output_dir}")


def print_size_table():
    """打印 size × resolution 完整对照表"""
    print("┌─────────┬──────────────────┬──────────────────┬──────────────────┐")
    print("│  size   │       1k         │       2k         │       4k         │")
    print("├─────────┼──────────────────┼──────────────────┼──────────────────┤")
    for sz in VALID_SIZES:
        row = [sz]
        for res in VALID_RESOLUTIONS:
            pixels = SIZE_MAP.get((sz, res), "—")
            row.append(f"{pixels:>16}")
        print(f"│ {row[0]:>7} │ {row[1]:>16} │ {row[2]:>16} │ {row[3]:>16} │")
    print("└─────────┴──────────────────┴──────────────────┴──────────────────┘")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="apimart.ai GPT-Image-2 图片生成客户端（首选后端）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
size × resolution 对照表:
  用 --sizes 查看完整像素对照表

常用组合:
  公众号封面   --size 16:9 --resolution 2k  (2048x1152)
  小红书卡片   --size 3:4  --resolution 1k  (768x1024)
  电影宽幅     --size 21:9 --resolution 2k  (2688x1152)
  正方形       --size 1:1  --resolution 1k  (1024x1024, 默认最便宜)
        """,
    )
    parser.add_argument("--prompt", help="生成提示词")
    parser.add_argument("--size", default="1:1", choices=VALID_SIZES,
                        help="画面比例 (默认 1:1)")
    parser.add_argument("--resolution", default="1k", choices=VALID_RESOLUTIONS,
                        help="分辨率 (默认 1k，最便宜)")
    parser.add_argument("--n", type=int, default=1, help="生成数量 (1-10)")
    parser.add_argument("--image-urls", nargs="*", help="参考图 URL（图生图模式）")
    parser.add_argument("--official-fallback", action="store_true",
                        help="使用官方渠道兜底")
    parser.add_argument("--output-dir", default=".", help="输出目录")
    parser.add_argument("--config", help="批量生成 JSON 配置文件")
    parser.add_argument("--status", help="查询任务状态 (task_id)")
    parser.add_argument("--sizes", action="store_true",
                        help="显示 size × resolution 完整对照表")
    args = parser.parse_args()

    if args.sizes:
        print_size_table()
    elif args.status:
        data = get_task_status(args.status)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.config:
        generate_series(args.config)
    elif args.prompt:
        generate_and_save(
            prompt=args.prompt,
            output_dir=args.output_dir,
            size=args.size,
            resolution=args.resolution,
            n=args.n,
            image_urls=args.image_urls,
            official_fallback=args.official_fallback,
        )
    else:
        parser.print_help()
