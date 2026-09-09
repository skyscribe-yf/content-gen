#!/usr/bin/env python3
"""tietu_infographic.py — 贴图素材归档 + OCR + infographic 生成（v2 结构）

流程（对应 docs/tietu-infographic-flow.md）：
  1. 从公众号发表记录（publish-data*.json，item_show_type=8）抓贴图标题/发布时间/图片 URL；
     时间缺失时回填贴图页 send_time / ct。
  2. 下载原图到  content/<YYYY-MM-DD>-tietu/<标题-slug>/  四个产物同目录
  3. 逐张 OCR 提取主要文字 → summary.json
  4. 按 briefs 写 prompt.md 并生成一张 info graphic 图片 → infographic.png

v2 目录约定（2026-09-09）：
  content/2026-09-07-tietu/ollama的峰谷价模式叠加1-3优惠还可以的/
      ├── 01.jpg … 04.jpg    原始素材
      ├── summary.json        识别文案（OCR）
      ├── prompt.md           info graphic 生成 prompt
      └── infographic.png     最终生成图

用法：
  python tietu_infographic.py --download                          # 下载原图到 content/<日期>-tietu/<标题>/
  python tietu_infographic.py --ocr                               # OCR 写 summary.json
  python tietu_infographic.py --infographic --briefs <briefs.json> # 写 prompt.md + 出图
  python tietu_infographic.py --infographic --briefs <b.json> '20260903'  # 仅含该子串的目录

依赖：dim ocr recognize；scripts/yairouter_img.py（API key 需 source ~/.bash_env）。
"""
import argparse
import copy
import datetime
import glob
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

PROJECT = '/home/skyscribe/srcs/content-gen'
CONTENT_ROOT = os.path.join(PROJECT, 'content')
BRIEFS_DEFAULT = os.path.join(PROJECT, 'docs/tietu-infographic-briefs.json')
UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 MicroMessenger/8.0.40'

socket.setdefaulttimeout(30)


def slugify(s):
    return re.sub(r'[\\/:*?"<>|#%\s]+', '-', s).strip('-')[:40] or 'untitled'


def _unesc(s):
    return (s or '').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')


def _num(f):
    m = re.search(r'(\d+)', f)
    return int(m.group(1)) if m else 0


def list_tietu(root=PROJECT):
    """抓 publish-data*.json 中 item_show_type=8 的贴图，合并去重。
    返回 [{title,url,time,imgs}]，imgs 为完整 CDN URL（含 /0?wx_fmt= 等 query）。
    """
    snapshots = [os.path.join(root, 'branding/style-corpus/publish-data.json')] + sorted(
        glob.glob(os.path.join(root, 'branding/style-corpus/publish-data-*.json')), key=_num)
    items = []
    seen = set()
    for snap in snapshots:
        if not os.path.exists(snap):
            continue
        try:
            d = json.load(open(snap))
        except Exception:
            continue
        for e in d.get('publish_list') or []:
            try:
                info = json.loads(_unesc(e.get('publish_info') or '{}'))
            except Exception:
                continue
            t = (info.get('sent_info') or {}).get('time') or 0
            for a in info.get('appmsg_info') or []:
                st = a.get('item_show_type') or (a.get('show_types') or [None])[0]
                if st != 8:
                    continue
                title = a.get('title', '')
                if title in seen:
                    continue
                seen.add(title)
                # 完整 CDN URL：snapshot 里的 cdn_url 可能缺 query；补全端点在 _fetch_page_imgs
                cdn = [(i.get('cdn_url') or '').replace('\\/', '/') for i in (a.get('share_imageinfo') or [])]
                items.append({'title': title, 'url': a.get('content_url', ''),
                              'time': t, 'imgs': cdn, 'msg_id': a.get('msgid', 0)})
    return [i for i in items if i['time']]


def _fetch_page(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'zh-CN,zh;q=0.9'})
    return urllib.request.urlopen(req).read().decode('utf-8', 'ignore')


def _page_imgs(page):
    urls = []
    for m in re.finditer(r'https://mmbiz\.qpic\.cn/[^"\'\\\s<>]+', page):
        c = m.group(0).replace('\\/', '/')
        if c not in urls:
            urls.append(c)
    return urls


def _page_time(page):
    for pat in [r'send_time[\'"]?\s*[:=]\s*[\'"]?(\d+)',
                r"var\s+ct\s*=\s*[\"'](\d{9,11})",
                r'ct\s*=\s*[\'"]?(\d{9,11})']:
        m = re.search(pat, page)
        if m:
            return int(m.group(1))
    return None


def resolve(entry):
    """回填时间 + 用带 query 的完整 CDN URL 替换（裸 URL 可能 HTTP 400）。"""
    out = copy.deepcopy(entry)
    t = entry.get('time')
    imgs = entry.get('imgs') or []
    if not imgs or not t:
        try:
            page = _fetch_page(entry['url'])
        except Exception:
            return out
        if not t:
            t = _page_time(page)
            out['time'] = t or 0
        full = _page_imgs(page)
        if full:
            out['imgs'] = full
    return out


def container_for(date):
    return os.path.join(CONTENT_ROOT, f'{date}-tietu')


def download(items, root=None):
    """下载原图到 content/<日期>-tietu/<标题>/。产物 manifest 记录在 <日期>-tietu/manifest.json。"""
    for r in items:
        if not r.get('time'):
            continue
        dt = datetime.datetime.fromtimestamp(r['time'])
        date = dt.strftime('%Y-%m-%d')
        con = container_for(date)
        sub = os.path.join(con, slugify(r['title']))
        os.makedirs(sub, exist_ok=True)
        # 幂等：已有原图则跳过
        existing = [f for f in os.listdir(sub) if f.lower().endswith('.jpg')]
        if existing:
            # 仍补齐缺失图
            pass
        for i, u in enumerate(r['imgs'], 1):
            fn = f'{i:02d}.jpg'
            if os.path.exists(os.path.join(sub, fn)):
                continue
            full = u if ('?' in u) else u + '?wx_fmt=jpeg'
            for attempt in range(3):
                try:
                    req = urllib.request.Request(full, headers={'User-Agent': UA, 'Referer': 'https://mp.weixin.qq.com/'})
                    data = urllib.request.urlopen(req).read()
                    open(os.path.join(sub, fn), 'wb').write(data)
                    break
                except Exception as e:
                    if attempt == 2:
                        print('  DL FAIL', sub.split('tietu/')[-1][:40], fn, str(e)[:80])
                    time.sleep(1)
            time.sleep(0.2)
        # manifest
        m_path = os.path.join(con, 'manifest.json')
        manifest = json.load(open(m_path)) if os.path.exists(m_path) else []
        if not any(x['title'] == r['title'] for x in manifest):
            manifest.append({'date': date, 'time': dt.strftime('%H:%M'), 'title': r['title'],
                             'url': r['url'], 'dir': slugify(r['title']),
                             'imgs': len([f for f in os.listdir(sub) if f.lower().endswith('.jpg')])})
            json.dump(manifest, open(m_path, 'w'), ensure_ascii=False, indent=1)
        print(dt.strftime('%m-%d %H:%M'), len([f for f in os.listdir(sub) if f.lower().endswith('.jpg')]),
              'of', len(r['imgs']), '->', sub.replace(PROJECT, ''))


def normalize_jpg(root):
    """CDN 常把 PNG 命名成 .jpg，image.read/ocr 报 signature mismatch，转真 JPEG。"""
    from PIL import Image
    n = 0
    for f in glob.glob(os.path.join(root, '*', '*.jpg')) + glob.glob(os.path.join(root, '*.jpg')):
        try:
            im = Image.open(f)
            if im.format == 'PNG':
                im.convert('RGB').save(f, 'JPEG', quality=92)
                n += 1
        except Exception:
            continue
    if n:
        print('normalized', n, 'PNG-as-jpg')


def ocr_all(root=None):
    for cont in sorted(glob.glob(os.path.join(CONTENT_ROOT, '*-tietu'))):
        if not os.path.isdir(cont):
            continue
        for sub in sorted(glob.glob(os.path.join(cont, '*'))):
            if not os.path.isdir(sub):
                continue
            files = sorted(glob.glob(os.path.join(sub, '*.jpg')))
            if not files:
                continue
            sp = os.path.join(sub, 'summary.json')
            cur = json.load(open(sp)) if os.path.exists(sp) else {}
            changed = False
            for f in files:
                base = os.path.basename(f)
                if cur.get(base, '').strip():
                    continue
                r = subprocess.run(['dim', 'ocr', 'recognize', f, '--output-mode', 'text', '--json'],
                                   capture_output=True, text=True, timeout=300)
                try:
                    j = json.loads(r.stdout)
                    cur[base] = j.get('text', '') if isinstance(j, dict) else ''
                except Exception:
                    cur[base] = ''
                changed = True
            if changed:
                json.dump(cur, open(sp, 'w'), ensure_ascii=False, indent=1)
                print('OCR', sub.split('tietu/')[-1][:44], len(files))


def write_prompt(sub, b):
    kps = '\n'.join(f'- {k}' for k in b['keypoints'])
    txt = (f"# {b['title']} — info graphic 生成 prompt\n\n"
           f"## 主故事线\n\n{b['point']}\n\n"
           f"## 要点卡片\n\n{kps}\n\n"
           f"## 视觉要求\n\n"
           f"现代扁平信息图（infographic），白底 + 单色系强对比 + 细网格 + 简单图标/箭头，顶部大标题，"
           f"3-5 张带图标要点卡，数字大号加粗。禁止照片、3D、杂乱堆砌。所有文字标签用简体中文，数字必须与原文一致。\n")
    open(os.path.join(sub, 'prompt.md'), 'w', encoding='utf-8').write(txt)


STYLE = ('Modern flat infographic poster, clean editorial tech-magazine style. '
         'White background, one strong accent color family, thin grid lines, simple flat icons and arrow diagrams. '
         'Clear visual hierarchy: big title bar on top, 3-5 short labeled bullet cards with icons below, '
         'numbers highlighted in large bold type. Minimal, high contrast, professional. '
         'Absolutely no photographs, no 3D, no clutter.')


def generate(briefs_path, only=None):
    generator = os.path.join(PROJECT, 'scripts/yairouter_img.py')
    briefs = json.load(open(briefs_path))
    # 建立 title-slug -> brief 索引，便于按目录匹配
    byslug = {slugify(b['title']): b for b in briefs}
    fails = []
    for cont in sorted(glob.glob(os.path.join(CONTENT_ROOT, '*-tietu'))):
        if not os.path.isdir(cont):
            continue
        for sub in sorted(glob.glob(os.path.join(cont, '*'))):
            if not os.path.isdir(sub):
                continue
            if only and not any(o in sub for o in only):
                continue
            base = os.path.basename(sub)
            b = byslug.get(base) or byslug.get(slugify(base))
            if not b:
                continue
            # prompt.md
            write_prompt(sub, b)
            out = os.path.join(sub, 'infographic.png')
            if os.path.exists(out):
                continue
            kps = '; '.join(b['keypoints'])
            prompt = (f"Infographic poster about: {b['title']}. Main story: {b['point']} "
                      f"Key points to visualize as labeled cards: {kps}. {STYLE} Use Chinese for all text labels.")
            r = subprocess.run(['python3', generator, '--prompt', prompt, '--size', '1024x1024',
                                '--output-dir', sub, '--filename', 'infographic.png'],
                               capture_output=True, text=True, timeout=600)
            if r.returncode != 0 or not os.path.exists(out):
                fails.append(base)
                print('  FAIL', base[:46], (r.stderr or r.stdout).strip()[-160:], flush=True)
            time.sleep(1)
    print('FAILS:', fails if fails else 'none')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--ocr', action='store_true')
    ap.add_argument('--infographic', action='store_true')
    ap.add_argument('--briefs', default=BRIEFS_DEFAULT)
    ap.add_argument('only', nargs='*', help='仅处理目录含这些子串的项')
    a = ap.parse_args()
    if a.download:
        items = list_tietu()
        resolved = [resolve(x) for x in items]
        print('tietu items:', len(resolved), 'sum imgs:', sum(len(x['imgs']) for x in resolved))
        download(resolved)
    if a.ocr:
        normalize_jpg(CONTENT_ROOT)
        ocr_all()
    if a.infographic:
        generate(a.briefs, a.only)


if __name__ == '__main__':
    main()
