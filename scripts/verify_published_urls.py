#!/usr/bin/env python3
"""台账 ↔ 后台核验：逐条抓 draft-status.yaml 里 published 条目的 wechat_url，比对标题。

为什么需要它（2026-10-15 立）：
  1. 「发表记录」（appmsgpublish）**只收录群发记录**，未群发但已发布的文章不在其中
     （作者 2026-10-15 确认：没有群发也是发布了）——所以发表记录不能当「全量已发布」校验源；
     带 wechat_url 的条目一律视为已发布，核验走本脚本直取 mp 页面。
  2. 拟稿标题 ≠ 后台发布标题是常态（作者会在后台改标题）。台账 / frontmatter / 内链文字
     一律以后台 `msg_title` 为准，本脚本把差异逐条列出来。

用法：
  python3 scripts/verify_published_urls.py                 # 全量核验（103 条约 1~2 分钟）
  python3 scripts/verify_published_urls.py --slug 2026-10-12-autodiff
  python3 scripts/verify_published_urls.py --json /tmp/url_verify.json
退出码：0 = 全部抓到标题且一致；1 = 有差异或抓取失败（详情见 stdout）。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.request

import yaml

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")


def fetch_title(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        h = r.read().decode("utf-8", "ignore")
    m = re.search(r"var msg_title = '(.*?)'\.html\(false\)", h) or \
        re.search(r'<meta property="og:title" content="([^"]*)"', h)
    ct = re.search(r'var ct = "(\d+)"', h)
    return {
        "msg_title": html.unescape(m.group(1)) if m else None,
        "deleted": ("该内容已被发布者删除" in h) or ("此内容因违规无法查看" in h),
        "verifyPage": "环境异常" in h[:4000],
        "ct": ct.group(1) if ct else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="draft-status.yaml")
    ap.add_argument("--slug", help="只核验某一条")
    ap.add_argument("--json", help="把逐条结果写到该路径")
    ap.add_argument("--sleep", type=float, default=0.7, help="请求间隔秒（默认 0.7）")
    args = ap.parse_args()

    d = yaml.safe_load(open(args.log, encoding="utf-8"))
    rows, diff, bad = [], [], []
    targets = [a for a in d["articles"] if a.get("wechat_url")
               and (not args.slug or a["slug"] == args.slug)]
    for a in targets:
        rec = {"slug": a["slug"], "ledger_title": a["title"], "url": a["wechat_url"]}
        try:
            rec.update(fetch_title(a["wechat_url"]))
        except Exception as e:  # 网络/反爬
            rec["error"] = str(e)[:120]
        rows.append(rec)
        if not rec.get("msg_title"):
            bad.append(rec)
        elif rec["msg_title"].strip() != a["title"].strip():
            diff.append(rec)
        time.sleep(args.sleep)

    if args.json:
        json.dump(rows, open(args.json, "w"), ensure_ascii=False, indent=1)

    print(f"台账有 URL 的条目 {len(rows)}：标题一致 {len(rows) - len(diff) - len(bad)} / "
          f"不一致 {len(diff)} / 抓取失败 {len(bad)}；已删除或违规 "
          f"{sum(1 for r in rows if r.get('deleted'))}")
    for r in diff:
        print(f"\n⚠️ {r['slug']}\n   台账: {r['ledger_title']}\n   后台: {r['msg_title']}")
    for r in bad:
        print(f"\n❓ {r['slug']} → {r.get('error') or 'no msg_title'}")
    return 0 if not (diff or bad) else 1


if __name__ == "__main__":
    raise SystemExit(main())
