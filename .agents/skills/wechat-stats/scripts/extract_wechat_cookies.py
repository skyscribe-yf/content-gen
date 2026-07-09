#!/usr/bin/env python3
"""
extract_wechat_cookies.py — 提取微信 MP 平台最小必要的 cookie 集合

工作流:
  1. 登录成功后，通过 agent_browser 获取完整 cookie 列表(CDP getAllCookies)
  2. 逐个移除候选 cookie，测试接口访问
  3. 输出最小 .env 格式的 cookie 字符串

也可以直接从 stdin 读取 "Cookie: ..." header 格式。

用法:
  # 自动模式(在已登录浏览器后用)
  python extract_wechat_cookies.py --auto

  # 配置文件模式
  python extract_wechat_cookies.py --cookie-json /tmp/full_cookies.json

  # StdIN 模式
  echo "cookie_string" | python extract_wechat_cookies.py --stdin

  # 检查现有 cookie
  python extract_wechat_cookies.py --check

输出:
  - 最小 cookie 字符串(.env 格式)
  - 可移除的 cookie 列表
  - 置信度评估(测试次数)
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

# ── 配置 ──
TEST_URL = "https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://mp.weixin.qq.com/",
}

# 各类 cookie 的优先级(可移除性): 越靠前越可能可以移除
REMOVAL_PRIORITY = [
    # 统计/跟踪(大概率可移除)
    "_clck", "_clsk", "pgv_pvid", "ts_uid", "ua_id", "xid",
    "_qimei_uuid", "_qimei_fingerprint", "_qimei_sip",
    "_qimei_guid", "qrtoken", "rand_info",
    # UI/行为状态(通常可移除)
    "appmsglist_action_",  # 前缀匹配(poc_sid 也被捕)
    "poc_sid", "rewardsn",
    # 语言/设置
    "mm_lang",
    # 认证子集(需要保留)
    "wxuin", "wxtokenkey",
    # 核心认证(绝大多数不能移除)
    "bizuin", "data_bizuin", "slave_bizuin",
    "data_ticket", "slave_sid", "slave_user",
]

# ─── 认证检查（两种方式） ───

def is_authenticated_via_requests(cookies: dict, test_url: str = TEST_URL) -> bool:
    """通过 requests 检查（注意：微信 MP 有 TLS 指纹检测，requests 可能始终返回失败）。
    仅作为快速参考，不可靠。"""
    try:
        session = requests.Session()
        resp = session.get(test_url, cookies=cookies, headers=HEADERS, timeout=15, allow_redirects=True)
    except Exception:
        return False

    text = resp.text

    # 检查 HTTP 层面(重定向到登录页 = 未认证)
    if "/cgi-bin/loginpage" in resp.url:
        return False

    # 明确的失败标志
    if "登录超时" in text or "请重新登录" in text:
        return False

    # 成功标志
    success_signals = [
        'id="menu"',
        'main_cc',
        'panel_box',
        'weui-desktop-layout',
    ]
    return any(signal in text for signal in success_signals)


def is_authenticated_via_cdp(cookies: dict, cdp_port: int = None) -> bool:
    """通过 CDP 从浏览器内部检查认证状态（可靠方式）。
    需要浏览器已经打开了 mp.weixin.qq.com 且已注入 cookie。"""
    import json
    import urllib.request
    import asyncio

    if cdp_port is None:
        # 自动发现 CDP 端口
        import glob
        ports = glob.glob("/tmp/agent-browser-chrome-*/DevToolsActivePort")
        if not ports:
            return False
        # 找最新的
        latest = max(ports, key=lambda p: os.path.getmtime(os.path.dirname(p)))
        with open(latest) as f:
            cdp_port = int(f.read().strip())

    try:
        resp = urllib.request.urlopen(f"http://localhost:{cdp_port}/json", timeout=5)
        tabs = json.loads(resp.read())
        tab = next((t for t in tabs if "mp.weixin.qq.com" in t.get("url", "")), None)
        if not tab:
            return False

        import websocket
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)

        # 执行 JS 检查登录态
        check_js = """
        JSON.stringify({
          uin: window.wx?.uin || '0',
          hasMenu: !!document.querySelector('#menu'),
          isLoggedIn: location.href.includes('/cgi-bin/home') && !document.body.innerText.includes('请重新登录')
        })
        """
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": check_js}}))
        msg = json.loads(ws.recv())
        ws.close()

        result = json.loads(msg["result"]["result"]["value"])
        return result.get("isLoggedIn", False) and result.get("hasMenu", False)
    except Exception:
        return False


def find_minimal_cookies(cookies: dict, use_cdp: bool = True) -> tuple:
    """
    找到通过认证的最小 cookie 集合。

    Returns:
        (minimal_cookies: dict, removable: list[str], tested_count: int)
    """
    # Step 1: 确认完整集合能通过
    if use_cdp:
        if not is_authenticated_via_cdp(cookies):
            raise ValueError("完整 cookie 集合未通过认证（CDP），请先确认浏览器已登录")
    else:
        if not is_authenticated_via_requests(cookies):
            raise ValueError("完整 cookie 集合未通过认证（requests），请先确认已登录")

    print("⚠️  注意：最小化请求通过 Python requests 发送，受 TLS 指纹限制可能误判。")
    print("   如遇 problems，请使用 --skip-minimize 跳过最小化，保存完整 cookie 集合。")

    # Step 2: 构建候选移除列表(优先级排序)
    candidates = []
    for pattern in REMOVAL_PRIORITY:
        if pattern.endswith("_"):
            # 前缀匹配
            matches = [k for k in cookies if k.startswith(pattern)]
            candidates.extend(matches)
        elif pattern in cookies:
            candidates.append(pattern)
    # 去重并保持顺序
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)

    remaining = dict(cookies)
    removable = []
    test_count = 1  # 基准已测一次

    # Step 3: 逐个尝试移除
    for key in unique_candidates:
        if key not in remaining:
            continue
        test_set = {k: v for k, v in remaining.items() if k != key}
        test_count += 1
        if is_authenticated(session, test_set, TEST_URL):
            removable.append(key)
            remaining = test_set

    return remaining, removable, test_count


def save_to_env(cookie_dict: dict, env_path: Path) -> str:
    """将 cookie 写入 .env 文件(更新或新增 WECHAT_COOKIE 行)"""
    cookie_str = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
    env_line = f"WECHAT_COOKIE={cookie_str}"

    if not env_path.exists():
        env_path.write_text(env_line + "\n")
        return str(env_path)

    content = env_path.read_text()
    # 查找并替换已有的 WECHAT_COOKIE 行
    pattern = r'^(WECHAT_COOKIE=).*$'
    new_content, count = re.subn(pattern, r'\1' + cookie_str, content, flags=re.MULTILINE)

    if count == 0:
        # 不存在则追加
        new_content = content.rstrip("\n") + "\n" + env_line + "\n"

    env_path.write_text(new_content)
    return str(env_path)


def verify_env_cookie(env_path: Path) -> bool:
    """验证 .env 中的 cookie 是否仍然有效"""
    if not env_path.exists():
        return False
    content = env_path.read_text()
    match = re.search(r'^WECHAT_COOKIE=(.+)$', content, re.MULTILINE)
    if not match:
        return False

    cookie_str = match.group(1).strip()
    pairs = [p.strip() for p in cookie_str.split(";") if "=" in p.strip()]
    cookie_dict = {}
    for p in pairs:
        k, _, v = p.partition("=")
        cookie_dict[k.strip()] = v.strip()

    if not cookie_dict:
        return False

    return is_authenticated_via_requests(cookie_dict)


def main():
    parser = argparse.ArgumentParser(
        description="提取并保存微信 MP 最小 cookie 集合",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自动: 连接本地已打开浏览器(Mac only, AppleScript)
  python extract_wechat_cookies.py --auto

  # 从之前保存的 JSON 提取
  python extract_wechat_cookies.py --cookie-json /tmp/fb-cookies.json

  # 检查 .env 中的 cookie 是否有效
  python extract_wechat_cookies.py --check
        """
    )
    parser.add_argument("--auto", action="store_true", help="尝试从系统浏览器自动获取")
    parser.add_argument("--cookie-json", type=Path, help="从 JSON 文件获取 cookie")
    parser.add_argument("--stdin", action="store_true", help="从 stdin 读取 cookie")
    parser.add_argument("--check", action="store_true", help="仅检查现有 cookie")
    parser.add_argument("--output-only", action="store_true", help="只输出 cookie 字符串，不写入 .env")
    parser.add_argument("--env-path", type=Path, default=None, help=".env 文件路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 默认 env 路径
    if args.env_path is None:
        args.env_path = Path(__file__).resolve().parents[3] / ".env"
        if not args.env_path.exists():
            args.env_path = Path.cwd() / ".env"

    # ── 仅检查 ──
    if args.check:
        if verify_env_cookie(args.env_path):
            print("✅ .env 中的 WECHAT_COOKIE 仍然有效")
            return 0
        else:
            print("❌ .env 中的 cookie 无效或不存在，需要重新获取")
            return 1

    # ── 获取 cookie 数据 ──
    cookies = {}

    if args.cookie_json:
        data = json.loads(args.cookie_json.read_text())
        if isinstance(data, dict):
            # 可能是 {"请求 Cookie": {...}} 嵌套
            for key in data:
                if isinstance(data[key], dict):
                    cookies.update(data[key])
            if not cookies:
                cookies = data
        else:
            print(f"❌ 不支持的 JSON 格式: {type(data)}")
            return 1

    elif args.stdin:
        raw = sys.stdin.read().strip()
        if raw.startswith("{"):
            data = json.loads(raw)
            for key in data:
                if isinstance(data[key], dict):
                    cookies.update(data[key])
            if not cookies:
                cookies = data
        else:
            # "key=val; key2=val2" 格式
            for part in raw.split(";"):
                part = part.strip()
                if "=" in part:
                    k, _, v = part.partition("=")
                    cookies[k.strip()] = v.strip()

    elif args.auto:
        # Mac: 尝试用 AppleScript 获取浏览器 cookie
        if sys.platform != "darwin":
            print("❌ --auto 仅在 macOS 上可用")
            return 1
        try:
            import subprocess
            result = subprocess.run(
                ["osascript", "-e", """
                tell application "Google Chrome"
                    set cookieString to ""
                    repeat with w in windows
                        repeat with t in tabs of w
                            if URL of t contains "mp.weixin.qq.com" then
                                set cookieString to execute t javascript "document.cookie"
                                exit repeat
                            end if
                        end repeat
                        if cookieString is not "" then exit repeat
                    end repeat
                    return cookieString
                end tell
                """],
                capture_output=True, text=True, timeout=10
            )
            raw = result.stdout.strip()
            if not raw or "error" in raw:
                print("❌ 未找到包含 mp.weixin.qq.com 的 Chrome 标签页，请先登录")
                return 1
            for part in raw.split(";"):
                part = part.strip()
                if "=" in part:
                    k, _, v = part.partition("=")
                    cookies[k.strip()] = v.strip()
        except Exception as e:
            print(f"❌ 自动获取失败: {e}")
            print(f"   请确保 Chrome 已打开并登录 mp.weixin.qq.com")
            return 1
    else:
        parser.print_help()
        return 0

    if not cookies:
        print("❌ 未能获得任何 cookie")
        return 1

    print(f"📋 获得 {len(cookies)} 个 cookie")

    # ── 运行最小化算法 ──
    try:
        session = requests.Session()
        minimal, removable, tested = find_minimal_cookies(cookies, session)
    except ValueError as e:
        print(f"❌ {e}")
        return 1

    # ── 输出结果 ──
    cookie_str = "; ".join(f"{k}={v}" for k, v in minimal.items())

    if args.verbose:
        print(f"\n{'='*60}")
        print(f"原始 cookie 数: {len(cookies)}")
        print(f"最小 cookie 数: {len(minimal)}")
        print(f"已移除: {removable}")
        print(f"测试次数: {tested}")
        print(f"{'='*60}")

    if args.output_only:
        print(cookie_str)
        return 0

    # ── 保存到 .env ──
    env_path = save_to_env(minimal, args.env_path)

    if args.verbose:
        print(f"\n✅ 已保存到 {env_path}")
        print(f"   WECHAT_COOKIE=\"{cookie_str[:80]}...\"")
        if removable:
            print(f"   可移除的: {removable}")
    else:
        print(cookie_str)
        print(f"\n=> 已写入 {env_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
