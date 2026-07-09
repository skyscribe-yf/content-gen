#!/usr/bin/env python3
"""零依赖 VPS 发布脚本 — 把 markdown 发布到微信草稿箱"""

import json, os, sys, struct, zlib, urllib.request, urllib.error

# ── 读取配置 ──
def load_env():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        for line in open(env_file):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()
APPID = os.environ.get("WECHAT_APP_ID")
SECRET = os.environ.get("WECHAT_APP_SECRET")

# ── 微信 API ──
def api_get(path):
    req = urllib.request.Request(f"https://api.weixin.qq.com{path}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def api_post(path, data):
    req = urllib.request.Request(
        f"https://api.weixin.qq.com{path}",
        data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def get_token():
    ret = api_get(f"/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}")
    if "access_token" not in ret:
        print("❌ 获取 token 失败:", ret)
        sys.exit(1)
    return ret["access_token"]

# ── 生成默认封面（纯标准库 PNG，零依赖） ──
def make_png(w, h, r, g, b):
    raw = b""
    for y in range(h):
        raw += b"\x00"
        for x in range(w):
            raw += bytes([r, g, b])
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")

def upload_cover(token, filepath="default_cover.png"):
    """上传封面图到微信永久素材，返回 media_id"""
    if not os.path.exists(filepath):
        print("  生成默认封面...")
        png = make_png(900, 500, 74, 107, 247)  # 深蓝 #4a6cf7
        with open(filepath, "wb") as f:
            f.write(png)

    return _upload_material(token, filepath)

def _upload_material(token, filepath):
    """上传图片到微信永久素材，返回 media_id"""
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    fname = os.path.basename(filepath)
    ext = os.path.splitext(fname)[1].lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}.get(ext, "image/png")
    with open(filepath, "rb") as f:
        img_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{fname}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + img_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        ret = json.loads(r.read())
    if "media_id" in ret:
        print(f"  ✅ 封面上传成功 media_id: {ret['media_id'][:20]}...")
        return ret["media_id"]
    print(f"  ⚠️ 上传封面失败: {ret}，跳过封面")
    return ""

def upload_content_image(token, filepath):
    """上传图片到微信 CDN（正文用，不占永久素材名额），返回 CDN URL"""
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    fname = os.path.basename(filepath)
    ext = os.path.splitext(fname)[1].lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}.get(ext, "image/png")
    with open(filepath, "rb") as f:
        img_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{fname}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + img_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        ret = json.loads(r.read())
    if "url" in ret:
        print(f"  ✅ {fname} → {ret['url'][:50]}...")
        return ret["url"]
    print(f"  ⚠️ 上传失败 {fname}: {ret}")
    return ""

# ── 解析 Markdown ──
def parse_md(filepath):
    title = author = digest = ""
    body_lines = []
    yaml_done = False
    in_yaml = False
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            # 只处理最开头的 YAML 块（第一个 --- 到第二个 --- 之间）
            if not yaml_done:
                if line.strip() == "---" and not in_yaml:
                    in_yaml = True
                    continue
                if line.strip() == "---" and in_yaml:
                    in_yaml = False
                    yaml_done = True
                    continue
                if in_yaml:
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip('"')
                    elif line.startswith("author:"):
                        author = line.split(":", 1)[1].strip().strip('"')
                    elif line.startswith("digest:"):
                        digest = line.split(":", 1)[1].strip().strip('"')
                    continue
            body_lines.append(line)
    if not title:
        title = os.path.splitext(os.path.basename(filepath))[0]
    return title, author or "数解AI", digest, "".join(body_lines)

# ── 极简 md → 微信 HTML ──
def md_to_html(md, img_urls=None):
    """极简 md→微信 HTML，img_urls 是本地路径→CDN URL 的映射"""
    img_urls = img_urls or {}
    html = []
    in_code = False
    for line in md.split("\n"):
        if line.startswith("```"):
            if in_code:
                html.append("</code></pre>")
                in_code = False
            else:
                html.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            html.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue
        if not line.strip():
            continue
        # 图片行: ![alt](path)
        import re
        m = re.match(r'!\[(.*?)\]\((.*?)\)', line.strip())
        if m:
            alt, src = m.group(1), m.group(2)
            cdn_url = img_urls.get(src, src)
            html.append(f'<p style="text-align:center;margin:15px 0"><img src="{cdn_url}" alt="{alt}" style="max-width:100%;border-radius:6px"></p>')
            continue
        if line.startswith("## "):
            html.append(f'<h2 style="font-size:18px;border-left:4px solid #4a6cf7;padding-left:10px;margin:20px 0 10px">{line[3:]}</h2>')
        elif line.startswith("### "):
            html.append(f'<h3 style="font-size:16px;font-weight:600;margin:15px 0 8px">{line[4:]}</h3>')
        elif line.startswith("- "):
            html.append(f'<p style="font-size:15px;margin:5px 0 5px 15px">• {line[2:]}</p>')
        elif line.startswith("|"):
            html.append(f'<p style="font-size:14px;color:#666;margin:5px 0">{line}</p>')
        else:
            html.append(f'<p style="font-size:15px;line-height:1.75;margin:10px 0">{line}</p>')
    return "\n".join(html)

# ── 创建草稿 ──
def create_draft(token, title, author, digest, html, thumb_id=""):
    article = {
        "title": title,
        "author": author,
        "digest": digest or title,
        "content": html,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    if thumb_id:
        article["thumb_media_id"] = thumb_id
    body = {"articles": [article]}
    ret = api_post(f"/cgi-bin/draft/add?access_token={token}", body)
    if "media_id" in ret:
        print(f"\n✅ 草稿创建成功！")
        print(f"   去 https://mp.weixin.qq.com → 草稿箱 → 预览并发布")
        return True
    print(f"❌ 创建草稿失败: {ret}")
    return False

def file_hash(path):
    """文件内容的简单 hash，用于防重复发布"""
    return str(os.path.getmtime(path)) + "|" + str(os.path.getsize(path))

if __name__ == "__main__":
    if not APPID or not SECRET:
        print("❌ 请设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")
        sys.exit(1)
    md_file = sys.argv[1] if len(sys.argv) > 1 else "/root/wechat-publish/weixin.md"
    if not os.path.exists(md_file):
        print(f"❌ 文件不存在: {md_file}")
        sys.exit(1)

    # 防重复：记录已发布的文件 hash
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".published")
    h = file_hash(md_file)
    if os.path.exists(log_file):
        published = set(open(log_file).read().splitlines())
        if h in published:
            print(f"⏭️  这个文件已经发布过了，跳过。如需重发，删除 {log_file}")
            sys.exit(0)

    print("🔑 获取 token...")
    token = get_token()
    print("📖 解析 markdown...")
    title, author, digest, body = parse_md(md_file)
    print(f"   标题: {title}")

    # 上传正文图片
    import re
    img_urls = {}
    img_dir = os.path.dirname(os.path.abspath(md_file))
    for m in re.finditer(r'!\[.*?\]\((.*?)\)', body):
        src = m.group(1)
        # 解析相对路径
        if not src.startswith("http"):
            local_path = os.path.normpath(os.path.join(img_dir, src))
            if os.path.exists(local_path) and local_path not in img_urls:
                print(f"🖼️  上传图片: {os.path.basename(local_path)}")
                cdn = upload_content_image(token, local_path)
                if cdn:
                    img_urls[src] = cdn

    # 上传封面（用第一张正文图或默认）
    print("🖼️  上传封面...")
    cover_img = next((os.path.normpath(os.path.join(img_dir, s)) for s in img_urls if not s.startswith("http")), None)
    cover_id = upload_cover(token, cover_img) if cover_img and os.path.exists(cover_img) else upload_cover(token)

    print("🔄 转换 HTML...")
    html = md_to_html(body, img_urls)
    print("📤 创建草稿...")
    ok = create_draft(token, title, author, digest, html, cover_id)
    if ok:
        with open(log_file, "a") as f:
            f.write(h + "\n")
