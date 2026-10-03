#!/usr/bin/env python3
"""封面文字块高度核查（口径：整块文字高 ≤ 画面高 1/4）。

判据（与「标题横贯全幅、由若干汉字组成」对应）：
  1. 金色发光字 = 高亮偏黄（R,G 高、B 明显低）；
  2. 用连通域把画面切成「块」，只保留尺寸像汉字的块
     （高 25–200px、宽 10–260px，按画面高度自适应）；
  3. 统计这些汉字块的 y 范围 → 整块文字高度占画面比例。

这样可以把「金属旋钮高光 / 火花」这类大色斑排除掉（它们不是汉字尺寸的连通域）。
对照基准：篇 2 已发封面台账口径 = 文字块约 21% of H。
"""
import sys
from collections import deque

import numpy as np
from PIL import Image


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
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            ys = [p[0] for p in pts]
            xs = [p[1] for p in pts]
            out.append((min(ys), max(ys), min(xs), max(xs), len(pts)))
    return out


p = sys.argv[1] if len(sys.argv) > 1 else "00-cover.png"
a = np.asarray(Image.open(p).convert("RGB")).astype(float)
H, W, _ = a.shape
r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
m = (r > 200) * (g > 155) * (b < 150)
comps = components(m)
glyphs = [c for c in comps
          if 0.03 * H <= (c[1] - c[0] + 1) <= 0.28 * H
          and 0.004 * W <= (c[3] - c[2] + 1) <= 0.16 * W
          and c[4] > 60]
print(f"{p}: {W}x{H} 比例 {W/H:.3f}；候选汉字块 {len(glyphs)} 个（总连通域 {len(comps)}）")
if not glyphs:
    print("  未检测到汉字尺寸的块")
    sys.exit(0)
glyphs.sort(key=lambda c: c[0])
# 按纵向聚集：相邻汉字块中心差 < 0.12H 视为同一行
lines, cur = [], [glyphs[0]]
for c in glyphs[1:]:
    if (c[0] + c[1]) / 2 - (cur[-1][0] + cur[-1][1]) / 2 < 0.12 * H:
        cur.append(c)
    else:
        lines.append(cur)
        cur = [c]
lines.append(cur)
# 只保留「横贯型」文字行：横向跨度 ≥ 45% 画面宽（标题横贯全幅；
# 背景火花/金属高光是局部斑块，跨度很小）——这一步把噪声行剔掉。
# 再剔背景装饰带：字符数 < 10 的行是背景图形（如被照亮的一排卡片），
# 真标题一行至少十几个字符块（09-25 本篇实测：卡片带 7 块 / 标题 39 块）。
title_lines = []
for ln in lines:
    x0 = min(c[2] for c in ln)
    x1 = max(c[3] for c in ln)
    span = (x1 - x0 + 1) / W
    if span >= 0.45 and len(ln) >= 10:
        title_lines.append(ln)
        top = min(c[0] for c in ln)
        bot = max(c[1] for c in ln)
        print(f"  文字行 y={top}-{bot} 高 {bot-top+1}px = {(bot-top+1)/H*100:.1f}% of H；"
              f"{len(ln)} 字块；横向跨度 {span*100:.0f}%")
if not title_lines:
    print("  未检测到横贯型文字行")
    sys.exit(0)
top = min(c[0] for ln in title_lines for c in ln)
bot = max(c[1] for ln in title_lines for c in ln)
pct = (bot - top + 1) / H * 100
print(f"  整块文字高 {bot-top+1}px = {pct:.1f}% of H  → " +
      ("✓ 达标 (≤25%)" if pct <= 25 else "✗ 超标 (>25%)"))
