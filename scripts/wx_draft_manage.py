#!/usr/bin/env python3
"""草稿箱管理：batchget 列表 / draft/delete 删除。走 vps-us SOCKS5 隧道（本机出口 IP 不在微信白名单）。

用法：
  python3 scripts/wx_draft_manage.py list
  python3 scripts/wx_draft_manage.py delete <media_id>
凭证：.baoyu-skills/.env 的 WECHAT_APP_ID / WECHAT_APP_SECRET（或环境变量）。
网络：ssh -D 动态端口 + curl --socks5-hostname（不依赖 PySocks）。
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
API = "https://api.weixin.qq.com/cgi-bin"


def load_env():
    for line in (ROOT / ".baoyu-skills" / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def tunnel():
    port = 20000 + (os.getpid() % 20000)
    p = subprocess.Popen(
        ["ssh", "-N", "-T", "-D", f"127.0.0.1:{port}", "-o", "ExitOnForwardFailure=yes",
         "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3",
         "-o", "ControlMaster=no", "-p", "22", "root@vps-us"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(20):
        time.sleep(0.5)
        if p.poll() is not None:
            raise SystemExit(f"ssh exited early (port {port} in use?)")
        r = subprocess.run(
            ["curl", "-s", "-m", "5", "--socks5-hostname", f"127.0.0.1:{port}",
             "https://api.weixin.qq.com/cgi-bin/getcallbackip"],
            capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return p, port
    p.terminate()
    raise SystemExit("SSH tunnel failed")


def curl(url, params=None, data=None):
    """params → 查询串；data → JSON body（POST）。不走 -G，避免 body 被搬进 URL。"""
    from urllib.parse import urlencode
    u = f"{url}?{urlencode(params)}" if params else url
    cmd = ["curl", "-s", "-m", "30", "--socks5-hostname", f"127.0.0.1:{PORT}", u]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(r.stdout)


def main():
    load_env()
    app_id = os.environ.get("WECHAT_APP_ID")
    secret = os.environ.get("WECHAT_APP_SECRET")
    if not app_id or not secret:
        raise SystemExit("missing WECHAT_APP_ID / WECHAT_APP_SECRET")
    p, port = tunnel()
    global PORT
    PORT = port
    try:
        tok = curl(TOKEN_URL, params={"grant_type": "client_credential",
                                      "appid": app_id, "secret": secret})
        if "access_token" not in tok:
            raise SystemExit(f"token error: {tok}")
        at = tok["access_token"]
        action = sys.argv[1] if len(sys.argv) > 1 else "list"
        if action == "list":
            r = curl(f"{API}/draft/batchget",
                     params={"access_token": at},
                     data={"offset": 0, "count": 20, "no_content": 1})
            for it in r.get("item", []):
                c = it.get("content", {})
                mi = it.get("media_id", "")
                print(f"{mi[:20]}…{mi[-6:]}  {c.get('title', '')[:44]}  update={it.get('update_time', '')}")
            print(f"total={r.get('total_count')} errcode={r.get('errcode')}")
        elif action == "delete":
            mi = sys.argv[2]
            r = curl(f"{API}/draft/delete", params={"access_token": at}, data={"media_id": mi})
            print(f"delete {mi[:20]}…{mi[-6:]} → errcode={r.get('errcode')} {r.get('errmsg', '')}")
        else:
            raise SystemExit(__doc__)
    finally:
        p.terminate()


if __name__ == "__main__":
    main()
