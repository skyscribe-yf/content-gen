"""
小红书创作者中心自动发布脚本

通过 CDP (Chrome DevTools Protocol) 操作浏览器，自动上传图片+填文案+发布笔记。

流程：
  1. 打开 creator.xiaohongshu.com（需手动登录一次）
  2. 点击「发布图文笔记」
  3. 通过 CDP DOM.setFileInputFiles 注入本地图片文件
  4. 填入标题和正文
  5. 点击发布

前置条件：
  - agent_browser 已启动并连接 Chrome
  - 已在小红书创作者中心登录

用法：
  # 从 copy.md + cards.json 自动读取内容发布
  python xhs_publish.py --dir content/2026-07-03-梯度下降/xiaohongshu

  # 指定标题、文案、图片
  python xhs_publish.py --title "AI怎么学会东西的" --copy "正文内容" --images 01.png 02.png

  # 检查登录状态
  python xhs_publish.py --check
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("需要 requests: pip install requests")

# ── Chrome CDP 工具 ──

def find_cdp_port():
    """从 Chrome user-data-dir 中读取 CDP 端口"""
    import glob
    # agent_browser 使用的 temp dir
    candidates = glob.glob("/tmp/agent-browser-chrome-*/DevToolsActivePort")
    if not candidates:
        sys.exit("❌ 未找到 Chrome CDP 端口，请先启动 agent_browser")

    # 取最新的
    latest = max(candidates, key=os.path.getmtime)
    with open(latest) as f:
        port = int(f.readline().strip())
    return port


def get_publish_page_url(cdp_port: int) -> tuple[str, str]:
    """获取当前打开的小红书发布页面的 pageId 和 wsUrl"""
    resp = requests.get(f"http://localhost:{cdp_port}/json", timeout=5)
    resp.raise_for_status()
    pages = resp.json()

    for p in pages:
        url = p.get("url", "")
        if "creator.xiaohongshu.com" in url:
            return p["id"], p["webSocketDebuggerUrl"]

    sys.exit("❌ 未找到小红书创作者中心页面，请先用 agent_browser 打开")


def cdp_get_file_input_backend_node_id(ws_url: str) -> int:
    """获取 file input 的 backendNodeId"""
    import asyncio

    async def _get():
        try:
            import websockets
        except ImportError:
            sys.exit("需要 websockets: pip install websockets")

        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            # Get document
            await ws.send(json.dumps({
                "id": 1, "method": "DOM.getDocument",
                "params": {"depth": -1, "pierce": True}
            }))
            doc = json.loads(await ws.recv())
            root_node_id = doc["result"]["root"]["nodeId"]

            # Find file input
            await ws.send(json.dumps({
                "id": 2, "method": "DOM.querySelector",
                "params": {"nodeId": root_node_id, "selector": "input[type='file']"}
            }))
            result = json.loads(await ws.recv())
            node_id = result["result"]["nodeId"]

            # Get backendNodeId
            await ws.send(json.dumps({
                "id": 3, "method": "DOM.describeNode",
                "params": {"nodeId": node_id}
            }))
            desc = json.loads(await ws.recv())
            backend_node_id = desc["result"]["node"]["backendNodeId"]
            return backend_node_id

    return asyncio.run(_get())


def cdp_set_files(ws_url: str, backend_node_id: int, file_paths: list[str]):
    """通过 CDP 注入文件到 file input"""
    import asyncio

    async def _set():
        try:
            import websockets
        except ImportError:
            sys.exit("需要 websockets: pip install websockets")

        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            await ws.send(json.dumps({
                "id": 10,
                "method": "DOM.setFileInputFiles",
                "params": {
                    "files": file_paths,
                    "backendNodeId": backend_node_id
                }
            }))
            result = json.loads(await ws.recv())
            print(f"  CDP setFiles result: {json.dumps(result)[:200]}")

    asyncio.run(_set())


# ── 内容读取 ──

def read_copy_from_md(copy_path: str) -> dict:
    """从 copy.md 读取标题、正文、标签"""
    with open(copy_path) as f:
        content = f.read()

    # 提取文案区（## 文案 之后的代码块或段落）
    title = ""
    body = ""
    in_copy = False

    lines = content.split("\n")
    copy_lines = []

    for line in lines:
        if "文案" in line and "≤300" in line:
            in_copy = True
            continue
        if in_copy:
            if line.startswith("## ") or line.startswith("---"):
                in_copy = False
                continue
            copy_lines.append(line)

    copy_text = "\n".join(copy_lines).strip()

    # 第一行作为标题候选（≤20字）
    first_line = copy_text.split("\n")[0].strip() if copy_text else ""
    # 标题通常是第一句，截断到20字
    if len(first_line) > 20:
        title = first_line[:20]
    else:
        title = first_line

    return {"title": title, "body": copy_text}


def find_images(image_dir: str) -> list[str]:
    """找到目录下所有 png/jpg 图片，按文件名排序"""
    dir_path = Path(image_dir)
    images = sorted([
        str(p) for p in dir_path.iterdir()
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        and p.name != "cover.png"  # 排除封面（封面通常是第一张）
    ])
    return images


# ── 主流程 ──

def check_login(cdp_port: int) -> bool:
    """检查是否已登录小红书创作者中心"""
    resp = requests.get(f"http://localhost:{cdp_port}/json", timeout=5)
    resp.raise_for_status()
    pages = resp.json()

    for p in pages:
        url = p.get("url", "")
        if "creator.xiaohongshu.com" in url and "/login" not in url:
            print(f"✅ 已登录: {p.get('title', '未知页面')}")
            return True

    print("❌ 未登录，请先用 agent_browser 打开 creator.xiaohongshu.com 并登录")
    return False


def publish(
    title: str,
    body: str,
    image_paths: list[str],
    cdp_port: int = None,
):
    """一键发布笔记到小红书"""
    if not cdp_port:
        cdp_port = find_cdp_port()

    print(f"📡 CDP 端口: {cdp_port}")

    # 检查登录
    if not check_login(cdp_port):
        return

    # 获取页面信息
    page_id, ws_url = get_publish_page_url(cdp_port)
    print(f"📄 页面: {page_id}")

    # Step 1: 打开发布页面
    print("\n📌 Step 1: 打开发布页面...")
    # 通过 CDP 执行页面导航
    import asyncio
    try:
        import websockets
    except ImportError:
        sys.exit("需要 websockets: pip install websockets")

    async def _navigate():
        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            await ws.send(json.dumps({
                "id": 1,
                "method": "Page.navigate",
                "params": {"url": "https://creator.xiaohongshu.com/publish/publish?target=image"}
            }))
            await ws.recv()
    asyncio.run(_navigate())
    time.sleep(3)

    # Step 2: 注入图片文件
    print(f"\n📌 Step 2: 上传 {len(image_paths)} 张图片...")
    backend_node_id = cdp_get_file_input_backend_node_id(ws_url)
    print(f"  File input backendNodeId: {backend_node_id}")

    # 验证文件存在
    for p in image_paths:
        if not os.path.exists(p):
            sys.exit(f"❌ 图片不存在: {p}")

    cdp_set_files(ws_url, backend_node_id, image_paths)
    time.sleep(3)
    print("  ✅ 图片上传完成")

    # Step 3: 填入标题和正文
    print(f"\n📌 Step 3: 填入标题和正文...")
    print(f"  标题: {title}")

    async def _fill_content():
        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            # 填标题
            title_js = title.replace("'", "\\'").replace("\n", "\\n")
            body_js = body.replace("'", "\\'").replace("\n", "\\n")

            # 点击标题输入框并填入
            js_code = f"""
            (() => {{
                const titleInput = document.querySelector('input[placeholder*="标题"]');
                if (titleInput) {{
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(titleInput, '{title_js}');
                    titleInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    titleInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}

                // 填正文 - 找到正文输入框（通常是 contenteditable 或第二个 textarea/input）
                const contentInputs = document.querySelectorAll('[contenteditable="true"]');
                if (contentInputs.length > 0) {{
                    const contentArea = contentInputs[0];
                    contentArea.focus();
                    contentArea.innerText = '{body_js}';
                    contentArea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }})()
            """

            await ws.send(json.dumps({
                "id": 20,
                "method": "Runtime.evaluate",
                "params": {"expression": js_code, "returnByValue": True}
            }))
            await ws.recv()

    asyncio.run(_fill_content())
    time.sleep(2)
    print("  ✅ 标题和正文填入完成")

    # Step 4: 点击发布
    print(f"\n📌 Step 4: 点击发布...")

    async def _click_publish():
        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            js_code = """
            (() => {
                const btns = document.querySelectorAll('button');
                for (const btn of btns) {
                    if (btn.textContent.trim() === '发布') {
                        btn.click();
                        return 'clicked 发布';
                    }
                }
                return '发布 button not found';
            })()
            """
            await ws.send(json.dumps({
                "id": 30,
                "method": "Runtime.evaluate",
                "params": {"expression": js_code, "returnByValue": True}
            }))
            result = json.loads(await ws.recv())
            print(f"  {result.get('result', {}).get('result', {}).get('value', 'unknown')}")

    asyncio.run(_click_publish())
    time.sleep(3)
    print("\n✅ 发布完成！去 https://creator.xiaohongshu.com 查看笔记")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书创作者中心自动发布脚本")
    parser.add_argument("--dir", help="小红书内容目录（含 cards.json + copy.md）")
    parser.add_argument("--title", help="笔记标题（≤20字）")
    parser.add_argument("--copy", help="正文内容")
    parser.add_argument("--images", nargs="+", help="图片文件路径列表")
    parser.add_argument("--cdp-port", type=int, help="Chrome CDP 端口（自动检测则省略）")
    parser.add_argument("--check", action="store_true", help="检查登录状态")
    args = parser.parse_args()

    if args.check:
        port = args.cdp_port or find_cdp_port()
        check_login(port)
    elif args.dir:
        # 从目录自动读取
        dir_path = Path(args.dir)
        copy_path = dir_path / "copy.md"
        img_dir = str(dir_path)

        if not copy_path.exists():
            sys.exit(f"❌ 找不到文案文件: {copy_path}")

        copy_data = read_copy_from_md(str(copy_path))
        images = find_images(img_dir)

        if not images:
            sys.exit(f"❌ 目录下没有图片: {img_dir}")

        print(f"📝 标题: {copy_data['title']}")
        print(f"📄 正文: {copy_data['body'][:80]}...")
        print(f"🖼️  图片: {len(images)} 张")

        publish(
            title=copy_data["title"],
            body=copy_data["body"],
            image_paths=images,
            cdp_port=args.cdp_port,
        )
    elif args.title and args.copy and args.images:
        publish(
            title=args.title,
            body=args.copy,
            image_paths=args.images,
            cdp_port=args.cdp_port,
        )
    else:
        parser.print_help()
