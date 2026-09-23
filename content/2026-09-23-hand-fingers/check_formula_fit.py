#!/usr/bin/env python3
"""用 Playwright 在真实视口（手机宽度 375px）里量每条公式的实际渲染宽度与容器宽度，
判断哪些公式会横向滚动。这比按 ex 估算可靠。"""
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

html = Path("weixin.html").read_text(encoding="utf-8")
# 用一个手机视口渲染
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 375, "height": 800})
    pg.set_content(html, wait_until="load")
    pg.wait_for_timeout(2500)
    data = pg.evaluate("""() => {
      const out = [];
      document.querySelectorAll('svg').forEach((s, i) => {
        const svgW = s.getBoundingClientRect().width;
        const box = s.closest('section') || s.parentElement;
        const boxW = box ? box.getBoundingClientRect().width : 0;
        out.push({i, svgW: Math.round(svgW), boxW: Math.round(boxW),
                  scrolls: svgW > boxW + 1});
      });
      const b = document.body.getBoundingClientRect();
      return {bodyW: Math.round(b.width), items: out};
    }""")
    b.close()

print(f"视口 375px；body 宽 {data['bodyW']}px")
bad = [d for d in data["items"] if d["scrolls"]]
print(f"公式 {len(data['items'])} 条；会横向滚动的: {len(bad)} 条")
for d in data["items"]:
    tag = " ⚠️ 横向滚动" if d["scrolls"] else ""
    print(f"  #{d['i']:2} svg {d['svgW']:4}px / 容器 {d['boxW']:4}px{tag}")
