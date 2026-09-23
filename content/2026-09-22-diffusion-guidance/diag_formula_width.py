#!/usr/bin/env python3
"""按出现顺序列出所有公式的宽度与序号 + 上下文，用于定位过宽公式。"""
import re
from pathlib import Path

h = Path("weixin.html").read_text(encoding="utf-8")
k = 0
for m in re.finditer(r"<svg[^>]*>.*?</svg>", h, re.S):
    wm = re.search(r"width:\s*([\d.]+)ex", m.group(0))
    if not wm:
        continue
    k += 1
    w = float(wm.group(1))
    seg = h[max(0, m.start() - 1200):m.start()]
    ctx = re.sub(r"<[^>]+>", "", seg)
    ctx = re.sub(r"\s+", " ", ctx).strip()[-60:]
    mark = " ⚠️" if w > 30 else ""
    print(f"#{k:2} {w:6.1f}ex{mark}   …{ctx}")
