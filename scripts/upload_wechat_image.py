#!/usr/bin/env python3
"""
上传图片到微信公众号素材库（通过 VPS SSH SOCKS5 隧道）。

微信公众号 API 有 IP 白名单限制，本脚本通过 SSH 动态端口转发
将 HTTPS 请求路由到白名单内的 VPS，无需在 VPS 上部署任何服务。

用法:
  python upload_wechat_image.py <图片路径>
  python upload_wechat_image.py content/collection-covers/大模型原理-合集封面.png

凭证:
  - WECHAT_APP_ID / WECHAT_APP_SECRET → 环境变量
  - 未设置时自动从 .baoyu-skills/.env 读取

远程配置:
  - 复用 baoyu-post-to-wechat 的 EXTEND.md 中 remote_publish_host/user
  - 默认: VPS_HOST=vps, VPS_USER=root, SOCKS_PORT=10999

依赖: curl, ssh, python3
"""
import subprocess
import json
import sys
import os
import signal

# ── 配置（可从环境变量覆盖）──────────────────────────────
APP_ID = os.environ.get("WECHAT_APP_ID", "")
APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "")
VPS_HOST = os.environ.get("VPS_HOST", "vps")
VPS_USER = os.environ.get("VPS_USER", "root")
SOCKS_PORT = int(os.environ.get("SOCKS_PORT", "10999"))

# ── 自动读取 .env ───────────────────────────────────────
def _load_env():
    global APP_ID, APP_SECRET
    candidates = [
        ".baoyu-skills/.env",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".baoyu-skills", ".env"),
    ]
    for p in candidates:
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line.startswith("WECHAT_APP_ID=") and not APP_ID:
                    APP_ID = line.split("=", 1)[1]
                if line.startswith("WECHAT_APP_SECRET=") and not APP_SECRET:
                    APP_SECRET = line.split("=", 1)[1]


def upload(image_path: str) -> str:
    """上传图片到微信素材库，返回图片 URL。"""
    _load_env()

    if not APP_ID or not APP_SECRET:
        sys.exit("ERROR: WECHAT_APP_ID / WECHAT_APP_SECRET 未设置，且 .baoyu-skills/.env 未找到")

    if not os.path.exists(image_path):
        sys.exit(f"ERROR: 文件不存在: {image_path}")

    print(f"上传: {image_path}")
    print(f"启动 SSH SOCKS5 隧道 → {VPS_USER}@{VPS_HOST}:{SOCKS_PORT} ...")

    tunnel = subprocess.Popen(
        ["ssh", "-N", "-D", str(SOCKS_PORT),
         "-o", "StrictHostKeyChecking=accept-new",
         "-o", "ConnectTimeout=10",
         f"{VPS_USER}@{VPS_HOST}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    # 确保 Ctrl+C 时清理隧道
    def cleanup(*_):
        tunnel.terminate()
        tunnel.wait()
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    import time; time.sleep(2)

    def curl(*args):
        return subprocess.run(
            ["curl", "-s", "--proxy", f"socks5h://127.0.0.1:{SOCKS_PORT}"] + list(args),
            capture_output=True, text=True,
        )

    try:
        # 1. 获取 access_token
        print("获取 access_token ...")
        resp = curl(
            f"https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
        )
        data = json.loads(resp.stdout)
        if "access_token" not in data:
            sys.exit(f"获取 token 失败: {resp.stdout}")
        token = data["access_token"]

        # 2. 上传图片
        print("上传中 ...")
        resp = curl(
            "-X", "POST",
            f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}",
            "-F", f"media=@{image_path}",
        )
        result = json.loads(resp.stdout)
        if "url" not in result:
            sys.exit(f"上传失败: {resp.stdout}")

        url = result["url"]
        print(f"✅ 上传成功!")
        print(f"   {url}")
        return url

    finally:
        cleanup()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(f"用法: python {sys.argv[0]} <图片路径>")
    upload(sys.argv[1])
