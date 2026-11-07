#!/usr/bin/env python3
"""封面核验（通用版，按 AGENTS.md「封面标题显眼度规格」的口径）：
  1) 21:9 比例；
  2) 文字块总高 ≤ 25% 画面高；
  3) 每行字高 ≥ 8% 画面高（防字形被裁）。

用法:
  python3 scripts/check_cover.py [图片路径|文章目录]
缺省用当前目录的 00-cover.png。退出码 0 = PASS。

判据说明：短标题（每行 4 字）不满足「横向跨度 ≥45%」的旧启发式，
故文字行按行高判定；白色/暖白发光字（2026-11-07 起封面由金色改为白→暖白）。
"""
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

_args = [a for a in sys.argv[1:] if not a.startswith("--")]
if _args:
    p = Path(_args[0])
    img_path = (p / "00-cover.png") if p.is_dir() else p
else:
    img_path = Path.cwd() / "00-cover.png"


def components(mask):
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for sy in range(H):
        for sx in range(W):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            q = deque([(sy, sx)])
            seen[sy, sx] = True
            pts = []
            while q:
                y, x = q.popleft()
                pts.append((y, x))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
            ys = [p[0] for p in pts]
            xs = [p[1] for p in pts]
            out.append((min(ys), max(ys), min(xs), max(xs), len(pts)))
    return out


im = Image.open(img_path).convert("RGB")
W, H = im.size
a = np.asarray(im).astype(float)
r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]


def detect(mask):
    comps = components(mask)
    glyphs = [c for c in comps
              if 0.045 * H <= (c[1] - c[0] + 1) <= 0.30 * H
              and 0.010 * W <= (c[3] - c[2] + 1) <= 0.13 * W
              and c[4] > 80]
    return comps, glyphs


# 白色 / 暖白发光字（2026-11-08 起封面由金色改为白→暖白）
comps, glyphs = detect((r > 205) * (g > 200) * (b > 170))
if not glyphs:
    # 旧金色封面口径（2026-11-08 前：R,G 高、B 明显低）——复检旧篇时自动回退
    comps, glyphs = detect((r > 200) * (g > 155) * (b < 150))
    if glyphs:
        print("（未检出白/暖白文字，按旧金色封面口径复检）")
print(f"{img_path}: {W}x{H} 比例 {W/H:.3f}；候选文字块 {len(glyphs)} 个（总连通域 {len(comps)}）")

fails = []
ratio = W / H
ok_ratio = abs(ratio - 21 / 9) < 0.02
print(f"  {'✓' if ok_ratio else '✗'} 21:9 比例（{ratio:.3f}）")
if not ok_ratio:
    fails.append("封面比例非 21:9")

if not glyphs:
    print("  ✗ 未检测到文字块")
    fails.append("未检测到文字块")
else:
    glyphs.sort(key=lambda c: c[0])
    lines, cur = [], [glyphs[0]]
    for c in glyphs[1:]:
        if (c[0] + c[1]) / 2 - (cur[-1][0] + cur[-1][1]) / 2 < 0.12 * H:
            cur.append(c)
        else:
            lines.append(cur)
            cur = [c]
    lines.append(cur)
    for i, ln in enumerate(lines, 1):
        top = min(c[0] for c in ln)
        bot = max(c[1] for c in ln)
        h = bot - top + 1
        pct = h / H * 100
        ok = pct >= 8.0
        print(f"  {'✓' if ok else '✗'} 第 {i} 行 字高 {h}px = {pct:.1f}% of H（≥8%）")
        if not ok:
            fails.append(f"第 {i} 行字高不足 8%")
    top = min(c[0] for c in glyphs)
    bot = max(c[1] for c in glyphs)
    total = (bot - top + 1) / H * 100
    ok = total <= 25.0
    print(f"  {'✓' if ok else '✗'} 整块文字高 {(bot-top+1)}px = {total:.1f}% of H（≤25%）")
    if not ok:
        fails.append("文字块高超过 25%")

print("PASS" if not fails else "FAIL: " + "; ".join(fails))
sys.exit(0 if not fails else 1)
