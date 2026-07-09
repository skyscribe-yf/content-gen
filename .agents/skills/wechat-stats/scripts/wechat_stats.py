#!/usr/bin/env python3
"""
微信公众号数据分析工具 (API 模式)

通过 SSH SOCKS5 隧道调用微信 API 获取公众号运营数据。
API 权限不足时自动跳过，仅展示可用数据。

⚠️ 订阅号大部分 datacube API 不可用，建议使用 Browser 模式。

用法:
  python wechat_stats.py            # 默认近7天
  python wechat_stats.py --days 30  # 近30天
  python wechat_stats.py --json     # JSON 输出
"""
import argparse
import json
import os
import requests
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ── 加载环境变量 ──
def load_env():
    for env_path in [
        Path(__file__).resolve().parents[4] / ".baoyu-skills" / ".env",
        Path(__file__).resolve().parent / ".env",
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

load_env()

APP_ID = os.environ.get("WECHAT_APP_ID", "")
APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "")

# ── SSH 隧道 ──
_ssh_proc = None
SOCKS_PORT = 14433

def start_tunnel():
    global _ssh_proc
    _ssh_proc = subprocess.Popen(
        ["ssh", "-N", "-T", "-D", f"127.0.0.1:{SOCKS_PORT}",
         "-o", "ExitOnForwardFailure=yes",
         "-o", "ServerAliveInterval=30",
         "-o", "ServerAliveCountMax=3",
         "-p", "22", "root@vps"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    return {"http": f"socks5h://127.0.0.1:{SOCKS_PORT}",
            "https": f"socks5h://127.0.0.1:{SOCKS_PORT}"}

def stop_tunnel():
    if _ssh_proc:
        _ssh_proc.terminate()

# ── API 调用 ──
def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return None

def api_post(url, body, proxies):
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=body, headers=headers, proxies=proxies, timeout=15)
    data = safe_json(r)
    if data is None:
        return {"_error": "non-JSON response"}
    if "errcode" in data and data["errcode"] != 0:
        return data
    return data

def get_access_token(proxies):
    if not APP_ID or not APP_SECRET:
        print("❌ 请在 .baoyu-skills/.env 中设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")
        sys.exit(1)
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    r = requests.get(url, proxies=proxies, timeout=15)
    data = safe_json(r)
    if not data or "access_token" not in data:
        print(f"❌ 获取 access_token 失败: {data}")
        sys.exit(1)
    return data["access_token"]

def is_unauthorized(data):
    return data and isinstance(data, dict) and data.get("errcode") == 48001

def has_list(data):
    return data and isinstance(data, dict) and data.get("list")

# ── 主流程 ──
def main():
    parser = argparse.ArgumentParser(description="微信公众号数据分析 (API 模式)")
    parser.add_argument("--days", type=int, default=7, help="查询天数 (默认7)")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    args = parser.parse_args()

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    begin = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    proxies = start_tunnel()
    try:
        at = get_access_token(proxies)
        print(f"✅ Access token 已获取\n")

        if args.json:
            results = {}
        else:
            print(f"📅 数据范围: {begin} ~ {yesterday}\n")

        BASE = "https://api.weixin.qq.com"
        DC = f"{BASE}/datacube"
        CGI = f"{BASE}/cgi-bin"

        # 1. 用户概况
        d = api_post(f"{DC}/getusersummary?access_token={at}", {"begin_date": begin, "end_date": yesterday}, proxies)
        if args.json:
            results["user_summary"] = d
        else:
            print("=== 📊 用户概况 ===")
            if is_unauthorized(d):
                print("  ⚠️ API 未授权 (需要认证服务号)")
            elif has_list(d):
                for i in d["list"][-args.days:]:
                    print(f"  {i['ref_date']}: 新增 {i.get('new_user',0)}, 取关 {i.get('cancel_user',0)}, 净增 {i.get('new_user',0)-i.get('cancel_user',0)}")
            else:
                print("  (无数据)")

        # 2. 累计关注
        d = api_post(f"{DC}/getusercumulate?access_token={at}", {"begin_date": begin, "end_date": yesterday}, proxies)
        if args.json:
            results["user_cumulate"] = d
        else:
            if has_list(d):
                print(f"  累计关注: {d['list'][-1].get('cumulate_user','N/A')}")
            elif not args.json:
                pass  # 已在上方提示

        # 3. 文章日数据
        d = api_post(f"{DC}/getarticlesummary?access_token={at}", {"begin_date": begin, "end_date": yesterday}, proxies)
        if args.json:
            results["article_summary"] = d
        else:
            print("\n=== 📖 文章日数据 ===")
            if is_unauthorized(d):
                print("  ⚠️ API 未授权")
            elif has_list(d):
                for i in d["list"][-args.days:]:
                    print(f"  {i['ref_date']}: 阅读 {i.get('int_page_read_count',0)}, 分享 {i.get('share_count',0)}")
            else:
                print("  (无数据)")

        # 4. 草稿箱 (通常可用)
        d = api_post(f"{CGI}/draft/batchget?access_token={at}", {"offset": 0, "count": 20, "no_content": 1}, proxies)
        if args.json:
            results["drafts"] = d
        else:
            print("\n=== 📝 草稿箱 ===")
            if d and d.get("item"):
                for item in d["item"][:20]:
                    news = item.get("content", {}).get("news_item", [])
                    for ni in news:
                        print(f"  {ni.get('title', '无标题')}")
                print(f"  共 {d.get('total_count', '?')} 篇草稿")
            else:
                print("  (无数据)")

        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))

    finally:
        stop_tunnel()
        if not args.json:
            print("\nDone.")

if __name__ == "__main__":
    main()
