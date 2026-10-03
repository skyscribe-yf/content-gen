#!/usr/bin/env python3
"""论文 SVG → 正文 PNG（playwright chromium 高倍截图，白底）

用法：.venv-mdnice/bin/python convert_paper_figures.py
产物：01-engram-arch.png / 02-engram-system.png / 03-engram-ablation.png
      04-v41-flash-arch.png / 05-engram-scaling.png（与 weixin.md 同级）
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "svg_src"
MAP = {
    "engram_arch.svg": "01-engram-arch.png",
    "Engram_system.svg": "02-engram-system.png",
    "sensitivity_analysis.svg": "03-engram-ablation.png",
    "arch_full.svg": "04-v41-flash-arch.png",
    "scaling_law.svg": "05-engram-scaling.png",
}
SCALE = 2.5  # 输出清晰度倍率

with sync_playwright() as p:
    browser = p.chromium.launch()
    for svg, out in MAP.items():
        page = browser.new_page(device_scale_factor=SCALE)
        page.goto(f"file://{SRC / svg}")
        el = page.locator("svg").first
        box = el.bounding_box()
        page.set_viewport_size({"width": int(box["width"]) + 20,
                                "height": int(box["height"]) + 20})
        el.screenshot(path=str(ROOT / out), style="background-color: white;")
        print(f"{out}: {box['width']:.0f}x{box['height']:.0f} @x{SCALE}")
        page.close()
    browser.close()
