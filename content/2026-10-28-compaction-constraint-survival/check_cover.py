#!/usr/bin/env python3
"""封面核验：尺寸 21:9、金色标题文字块高度 ≤ 画面高 1/4、标题逐字核验（人工读图对照）。"""
import sys
from PIL import Image

path = sys.argv[1] if len(sys.argv) > 1 else "00-cover.png"
im = Image.open(path).convert("RGB")
w, h = im.size
print(f"尺寸 {w}x{h}｜比例 {w/h:.4f}（21:9 = {21/9:.4f}）")
if abs(w / h - 21 / 9) > 0.02:
    print("⚠️ 比例不是 21:9")

px = im.load()
import numpy as np

arr = np.asarray(im).astype(int)
r_, g_, b_ = arr[..., 0], arr[..., 1], arr[..., 2]
mask = (r_ > 140) & (g_ > 95) & (b_ < 150) & ((r_ - b_) > 45)
rows = mask.sum(1)
ys = np.where(rows > w * 0.01)[0]
if len(ys) == 0:
    print("❌ 未找到成行分布的金色文字像素（标题可能缺失或颜色不对）")
    sys.exit(1)
bands, start, prev = [], ys[0], ys[0]
for y in ys[1:]:
    if y - prev <= 10:
        prev = y
    else:
        bands.append((start, prev))
        start = prev = y
bands.append((start, prev))
# 只保留像「一行标题」的段落（高度 ≥4% 画面高）
text_bands = [bd for bd in bands if (bd[1] - bd[0] + 1) / h >= 0.04]
if not text_bands:
    print("❌ 未识别出标题文字行")
    sys.exit(1)
top, bottom = text_bands[0][0], text_bands[-1][1]
for i, bd in enumerate(text_bands, 1):
    print(f"  第 {i} 行：y {bd[0]}–{bd[1]}，行高 {(bd[1]-bd[0]+1)/h*100:.1f}% 画面高")
block = bottom - top
print(f"金色文字块：y {top}–{bottom}，高度 {block}px = 画面高度的 {block/h*100:.1f}%（口径 ≤25%）")
print("✅ 通过" if block / h <= 0.25 else "❌ 超口径，需重生封面")
