#!/usr/bin/env python3
"""品牌图 → 圆角透明 PNG（Manim 尾卡用，融合深蓝画布背景）。

用法：
  python3 scripts/make_round_logo.py avatar-sjai.png \
      --out content/<日期>-<主题>/shipinhao/avatar-sjai-round.png

说明：
  - 原图是方形深蓝底（#030B23 级），与 Manim 画布 #16213E 有色差，
    直接 ImageMobject 会露方框边缘；圆角透明后自然融合
  - 圆角半径默认 12% 边长，保留底部品牌文字
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def make_round(path: Path, out: Path, radius_ratio: float = 0.12) -> None:
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    radius = int(w * radius_ratio)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    result.paste(im, (0, 0), mask)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.save(out)
    print(f"saved {out} ({w}x{h}, radius {radius})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="品牌图路径（如 avatar-sjai.png）")
    ap.add_argument("--out", default=None, help="输出路径（默认 <输入名>-round.png 于同目录）")
    ap.add_argument("--radius", type=float, default=0.12, help="圆角半径占边长的比例（默认 0.12）")
    args = ap.parse_args()

    src = Path(args.input)
    dst = Path(args.out) if args.out else src.with_name(f"{src.stem}-round{src.suffix}")
    make_round(src, dst, args.radius)
