#!/usr/bin/env python3
"""整段 TTS 音频按台词分段切分（MiniMax --subtitle 时间戳方案）。

用法:
  python3 scripts/tts_split.py content/<日期>-<主题>/shipinhao \
      --full tts/full.wav --subtitle tts/full.subtitle.json

流程（2026-08-12 定稿，替代逐段 TTS）:
  1. full.txt = tts.txt 5-6 段合并（含段尾过渡句），minimax_tts.py --subtitle 一次生成
  2. 本脚本: 每段台词开头 10 字在时间戳文本中定位 → 段边界 = 前后句时间戳中点
  3. 切出 tts/s1..s6.wav（覆盖旧文件），打印 VOICE_DUR 供 scenes.py 更新

注意:
  - 时间戳 time_begin/time_end 单位毫秒；segment 的 text 为句子级
  - 边界取「前句 time_end 与后句 time_begin 中点」落在静音区；勿用 begin-0.2（会吞前句尾音）
  - 切分验证: 每段开头 0.2s 窗口 RMS < -30dB 属正常起音（含 0.1s 静音+辅音），勿用 0.3s 窗口误报
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def clean(s: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]", "", s)


def locate_segment(sub, offsets, probe: str) -> int:
    """台词开头 probe 在时间戳拼接文本中的偏移 → segment 索引。"""
    joined = ""  # 重建拼接串（调用方已算 offsets，这里按同样规则拼）
    pos = -1
    for k in range(len(probe), 2, -1):
        pos = joined.find(probe[:k])
        if pos >= 0:
            break
    return max(j for j, o in enumerate(offsets) if o <= pos)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir", help="shipinhao 工作目录（含 tts.txt）")
    ap.add_argument("--full", default="tts/full.wav", help="整段音频（相对 workdir）")
    ap.add_argument("--subtitle", default="tts/full.subtitle.json", help="时间戳 JSON（相对 workdir）")
    ap.add_argument("--out-dir", default="tts", help="切分输出目录（相对 workdir）")
    ap.add_argument("--quiet", action="store_true", help="只打印 VOICE_DUR 行")
    args = ap.parse_args()

    wd = Path(args.workdir)
    lines = (wd / "tts.txt").read_text(encoding="utf-8").strip().split("\n")
    if len(lines) < 2:
        raise SystemExit("tts.txt 至少 2 段")

    sub = json.loads((wd / args.subtitle).read_text(encoding="utf-8"))
    dur = float(
        subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(wd / args.full)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    )

    joined, offsets = "", []
    for seg in sub:
        offsets.append(len(joined))
        joined += clean(seg["text"])

    bounds = [0.0]
    for i in range(1, len(lines)):
        probe = clean(lines[i])[:10]
        pos = joined.find(probe)
        if pos < 0:  # 模糊回退：最长前缀
            for k in range(len(probe), 2, -1):
                pos = joined.find(probe[:k])
                if pos >= 0:
                    break
        if pos < 0:
            raise SystemExit(f"第 {i+1} 段开头「{probe}」在时间戳文本中未定位（检查台词与 full.txt 是否一致）")
        si = max(j for j, o in enumerate(offsets) if o <= pos)
        prev_end = sub[si - 1]["time_end"] / 1000 if si > 0 else 0.0
        cur_begin = sub[si]["time_begin"] / 1000
        bounds.append(max(bounds[-1] + 1.0, (prev_end + cur_begin) / 2.0))
    bounds.append(dur)

    out_dir = wd / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    durs = []
    for i in range(len(lines)):
        a, b = bounds[i], bounds[i + 1]
        seg = out_dir / f"s{i + 1}.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-to", str(b),
             "-i", str(wd / args.full), "-c", "copy", str(seg)],
            check=True,
        )
        durs.append(round(b - a, 2))
        if not args.quiet:
            print(f"S{i+1}: {a:7.2f} ~ {b:7.2f}  ({b-a:5.2f}s)")

    print("VOICE_DUR = {" + ", ".join(f'"S{i}": {d}' for i, d in enumerate(durs, 1)) + "}")
    if not args.quiet:
        print(f"总时长 {dur:.1f}s · 切分完成 → {out_dir}/s1..s{len(lines)}.wav")


if __name__ == "__main__":
    main()
