#!/usr/bin/env python3
"""更新公众号草稿（draft/update）：换封面 thumb + 按位置替换正文图片 URL。

背景：wechat-api.ts 只支持 draft/add（每次存一篇新稿）；换封面/换图需要
draft/update。本脚本复用发布通道（vps-us SOCKS5 隧道 + .baoyu-skills/.env），
不新增通道。

用法:
  python3 scripts/update_draft_media.py <文章目录> --draft-media-id <id>
  python3 scripts/update_draft_media.py <文章目录> --title-contains "换个更强的老师"
  python3 scripts/update_draft_media.py <文章目录> --draft-media-id <id> --dry-run

流程:
  1) timeout 包住 ssh -N -D 建 SOCKS5 隧道（到点自退，不手工 kill）
  2) curl（清 https_proxy + ALL_PROXY=socks5h）取 access_token
  3) draft/batchget 找草稿（media_id 精确匹配，或标题包含匹配）
  4) material/add_material 上传封面（thumb_media_id）
  5) media/uploadimg 按 weixin.md 图片顺序上传正文图（url 列表）
  6) 按位置替换 content 里旧 mmbiz URL，draft/update 写回
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SSH_HOST = "root@vps-us"
SSH_PORT = 22
TUNNEL_TTL = 900  # 隧道最长存活秒数（timeout 自退）
API = "https://api.weixin.qq.com/cgi-bin"


def load_env():
    env_file = ROOT / ".baoyu-skills" / ".env"
    env = dict(os.environ)
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


class WechatApi:
    def __init__(self, env):
        self.env = env
        self.port = self._free_port()
        self.tunnel = subprocess.Popen(
            ["timeout", str(TUNNEL_TTL), "ssh", "-N", "-T",
             "-D", f"127.0.0.1:{self.port}",
             "-o", "ExitOnForwardFailure=yes",
             "-o", "ServerAliveInterval=30",
             "-p", str(SSH_PORT), SSH_HOST],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)
        self.token = self._token()

    @staticmethod
    def _free_port():
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        p = s.getsockname()[1]
        s.close()
        return p

    def _curl(self, args, timeout=120):
        """走隧道的 curl：清 https_proxy（专用变量优先级高于 ALL_PROXY，实踩 40164）。"""
        cmd = ["curl", "-s", "-m", str(timeout)]
        e = dict(self.env)
        for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
            e.pop(k, None)
        e["ALL_PROXY"] = f"socks5h://127.0.0.1:{self.port}"
        cmd += args
        r = subprocess.run(cmd, capture_output=True, text=True, env=e, timeout=timeout + 10)
        return r.stdout

    def _token(self):
        appid = self.env.get("WECHAT_APP_ID", "")
        secret = self.env.get("WECHAT_APP_SECRET", "")
        if not appid or not secret:
            sys.exit("❌ .baoyu-skills/.env 缺 WECHAT_APP_ID/WECHAT_APP_SECRET")
        for attempt in range(6):
            out = self._curl([f"{API}/token?grant_type=client_credential&appid={appid}&secret={secret}"], timeout=40)
            try:
                d = json.loads(out)
            except json.JSONDecodeError:
                d = {}
            if d.get("access_token"):
                return d["access_token"]
            print(f"  … token 重试 {attempt + 1}/6: {out[:120]}")
            time.sleep(4)
        sys.exit("❌ token 获取失败（隧道或白名单问题）")

    # ── API ──
    def batchget(self, count=20):
        out = self._curl(["-X", "POST", f"{API}/draft/batchget?access_token={self.token}",
                          "-H", "Content-Type: application/json",
                          "-d", json.dumps({"offset": 0, "count": count, "no_content": 0})])
        return json.loads(out)

    def uploadimg(self, path):
        out = self._curl(["-F", f"media=@{path}", "-F", "filename=image",
                          f"{API}/media/uploadimg?access_token={self.token}"], timeout=180)
        d = json.loads(out)
        if "url" not in d:
            sys.exit(f"❌ uploadimg 失败 {path}: {out[:200]}")
        return d["url"]

    def add_material(self, path):
        out = self._curl(["-F", f"media=@{path}", "-F", "filename=cover",
                          f"{API}/material/add_material?access_token={self.token}&type=image"], timeout=180)
        d = json.loads(out)
        if "media_id" not in d:
            sys.exit(f"❌ add_material 失败 {path}: {out[:200]}")
        return d["media_id"]

    def draft_update(self, media_id, index, article):
        out = self._curl(["-X", "POST", f"{API}/draft/update?access_token={self.token}",
                          "-H", "Content-Type: application/json",
                          "-d", json.dumps({"media_id": media_id, "index": index,
                                            "articles": article}, ensure_ascii=False)])
        return json.loads(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("article_dir")
    ap.add_argument("--draft-media-id")
    ap.add_argument("--title-contains")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cover-only", action="store_true", help="只换封面 thumb，正文图与 content 不动")
    args = ap.parse_args()

    d = Path(args.article_dir).resolve()
    md = (d / "weixin.md").read_text(encoding="utf-8")
    body = md.split("---", 2)[-1].split("🔥 **热门文章**")[0]
    img_refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body)
    img_paths = [d / p for p in img_refs]
    missing = [p.name for p in img_paths if not p.exists()]
    if missing and not args.cover_only:
        sys.exit(f"❌ 缺图片: {missing}")
    cover = d / "00-cover.png"
    if not cover.exists():
        sys.exit("❌ 缺 00-cover.png")

    print(f"文章目录: {d.name}")
    print(f"正文图 {len(img_paths)} 张: {[p.name for p in img_paths]}")
    print(f"封面: {cover.name}")

    env = load_env()
    api = WechatApi(env)
    print("✅ token + 隧道就绪")

    # 找草稿
    target = None
    for it in api.batchget().get("item", []):
        for idx, a in enumerate(it.get("content", {}).get("news_item", [])):
            t = a.get("title", "")
            if args.draft_media_id:
                hit = it.get("media_id") == args.draft_media_id
            elif args.title_contains:
                hit = args.title_contains in t
            else:
                sys.exit("❌ 需要 --draft-media-id 或 --title-contains")
            if hit:
                target = (it, idx, a)
                break
        if target:
            break
    if not target:
        sys.exit("❌ 草稿箱里没找到目标草稿")
    it, idx, old = target
    print(f"✅ 找到草稿 …{it['media_id'][-14:]} | {old.get('title', '')[:40]}")

    content = old.get("content", "")
    old_urls = re.findall(r"https?://mmbiz[^\"'\s)]+", content)
    print(f"草稿正文已有 mmbiz 图 {len(old_urls)} 张")
    if not args.cover_only and len(old_urls) != len(img_paths):
        sys.exit(f"❌ 图片数不符：草稿 {len(old_urls)} vs 本地 {len(img_paths)}——中止，避免错位替换")

    # 上传
    new_thumb = api.add_material(str(cover))
    print(f"✅ 新封面 thumb_media_id: …{new_thumb[-14:]}")

    if args.cover_only:
        new_content = content
        print("（--cover-only：只换封面，正文图不动）")
    else:
        new_urls = [api.uploadimg(str(p)) for p in img_paths]
        for p in img_paths:
            print(f"✅ 上传 {p.name}")
        new_content = content
        for old_u, new_u in zip(old_urls, new_urls):
            new_content = new_content.replace(old_u, new_u)
        if new_content == content:
            sys.exit("❌ content 未发生变化——URL 替换失败")

    article = {
        "title": old.get("title", ""),
        "thumb_media_id": new_thumb,
        "author": old.get("author", ""),
        "digest": old.get("digest", ""),
        "content": new_content,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    if old.get("content_source_url"):
        article["content_source_url"] = old["content_source_url"]

    if args.dry_run:
        print("（--dry-run：不上传写回，跳过 draft/update）")
        print(json.dumps({"thumb": new_thumb, "urls": len(new_urls)}, ensure_ascii=False))
        return

    r = api.draft_update(it["media_id"], idx, article)
    print(f"draft/update 返回: {json.dumps(r, ensure_ascii=False)}")
    if r.get("errcode") in (None, 0):
        print(f"\n✅ 草稿已更新: {it['media_id']}")
        print(f"   封面 media_id: {new_thumb}")
    else:
        sys.exit(f"❌ draft/update 失败: {r}")


if __name__ == "__main__":
    main()
