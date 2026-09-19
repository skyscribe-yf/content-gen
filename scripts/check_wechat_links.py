#!/usr/bin/env python3
"""校验 weixin.md 里所有 mp.weixin.qq.com/s/ 链接是否存在于台账。

用法: python3 scripts/check_wechat_links.py content/<dir>/weixin.md
"""
import re
import sys
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    md = pathlib.Path(sys.argv[1])
    text = md.read_text(encoding="utf-8")

    known = set()
    data = yaml.safe_load((ROOT / "draft-status.yaml").read_text(encoding="utf-8"))
    for a in data.get("articles", []):
        u = a.get("wechat_url")
        if u:
            known.add(u.rstrip("/"))
        z = a.get("zhihu_url")
        if z:
            known.add(z.rstrip("/"))

    # 各篇 frontmatter wechatUrl 也是事实源
    for f in (ROOT / "content").glob("*/weixin.md"):
        m = re.search(r'wechatUrl:\s*"?(https?://[^"\s]+)"?', f.read_text(encoding="utf-8"))
        if m:
            known.add(m.group(1).rstrip("/"))

    urls = re.findall(r"https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_\-]+", text)
    bad = []
    for u in dict.fromkeys(urls):
        if u.rstrip("/") not in known:
            bad.append(u)

    print(f"{md}: mp 链接 {len(dict.fromkeys(urls))} 条，台账已知 {len(known)} 条")
    if bad:
        print("❌ 未在台账中找到（疑似伪造/失效，会导致 45166）:")
        for u in bad:
            print("   ", u)
        return 1
    print("✅ 全部链接均可溯源")
    return 0


if __name__ == "__main__":
    sys.exit(main())
