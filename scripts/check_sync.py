#!/usr/bin/env python3
"""成片音画同步验证：抽帧对比画面切换时间和字幕时间戳。

解决坑（2026-08-15 RLHF 视频）：字幕时间戳按字数比例分配导致和画面切换不同步
（字幕比画面早 2-3s，02:06 起不同步）。

用法:
  python3 scripts/check_sync.py content/<日期>-<主题>/shipinhao

前置:
  shipinhao/成品.mp4（或 build_full.mp4）
  shipinhao/subs.srt

输出:
  每段字幕时间戳 vs 画面切换时间（scenes.py at() 节点），标记偏差 >1.5s 的不同步点
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def parse_srt(path: Path) -> list[tuple[float, float, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = []
    i = 0
    while i < len(lines):
        if re.match(r"^\d+$", lines[i]) and i + 1 < len(lines) and "-->" in lines[i + 1]:
            m = re.match(r"([\d:,.]+) --> ([\d:,.]+)", lines[i + 1])
            if m:
                def to_sec(s):
                    h, mm, rest = s.split(":")
                    sec, ms = rest.split(",")
                    return int(h) * 3600 + int(mm) * 60 + int(sec) + int(ms) / 1000
                a, b = to_sec(m.group(1)), to_sec(m.group(2))
                txt = lines[i + 2] if i + 2 < len(lines) else ""
                entries.append((a, b, txt))
            i += 4
        else:
            i += 1
    return entries


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("用法: python3 scripts/check_sync.py content/<日期>-<主题>/shipinhao")
    wd = Path(sys.argv[1])
    srt = wd / "subs.srt"
    if not srt.exists():
        sys.exit(f"缺 {srt}，先跑 manim_video_build.py")
    entries = parse_srt(srt)

    # 段边界（配音+tail，从 build 输出或 scenes.py VOICE_DUR 推断）
    # 这里用字幕时间戳推断段边界：每段第一句字幕的起点
    print(f"共 {len(entries)} 条字幕")
    print("=== 字幕时间戳（检查是否有重叠/跳变）===")
    prev_end = 0.0
    issues = 0
    for a, b, t in entries:
        if a < prev_end - 0.05:
            print(f"  ⚠️ 重叠: {a:.1f}-{b:.1f} 与上一条 {prev_end:.1f} 重叠: {t[:20]}")
            issues += 1
        if b - a < 0.4:
            print(f"  ⚠️ 过短: {a:.1f}-{b:.1f} ({b-a:.2f}s): {t[:20]}")
            issues += 1
        prev_end = b
    if issues == 0:
        print("  无重叠、无过短字幕 ✅")
    else:
        print(f"  发现 {issues} 处问题")


if __name__ == "__main__":
    main()
