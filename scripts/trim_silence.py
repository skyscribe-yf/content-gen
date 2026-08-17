#!/usr/bin/env python3
"""口播录音裁剪静音：自动去掉每段头尾静音，输出 VOICE_DUR。

解决两个坑（2026-08-15 RLHF 视频）：
  1. 开头微弱环境声被误判为语音起点（S6 2.86s 静音残留）
     → 用「第一个明显语音段」作为起点（跳过开头 <0.5s 的微弱声）
  2. 尾部静音残留（S2 6.3s）
     → 裁剪终点用「最后一个语音结束点」，不是「最后一个静音开始」

用法:
  python3 scripts/trim_silence.py content/<日期>-<主题>/shipinhao

前置:
  shipinhao/recordings/s1.wav..sN.wav   原始分段录音

产物:
  shipinhao/trim/s1..sN.wav             裁剪后的干净音频
  shipinhao/trim/voice_dur.json         每段实际时长（复制进 scenes.py VOICE_DUR）
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SILENCE_DB = -35
LEAD_MIN = 0.5   # 开头静音 <0.5s 视为无准备静音（语音从 0 开始）


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def speech_bounds(path: Path) -> tuple[float, float] | None:
    """返回 (语音起点, 语音终点)，只裁掉真正贴住音频两端的静音。"""
    out = run(["ffmpeg", "-hide_banner", "-i", str(path),
               "-af", f"silencedetect=noise={SILENCE_DB}dB:d=0.15", "-f", "null", "-"]).stderr
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    gaps = [(start, end) for start, end in zip(starts, ends) if end > start]
    if not gaps:
        return None
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(path)]).stdout.strip())
    # 绝不能把段内停顿当成首尾静音：只有静音段贴住 0 / duration 才可裁。
    first_start, first_end = gaps[0]
    speech_start = first_end if first_start <= 0.05 and first_end >= LEAD_MIN else 0.0
    last_start, last_end = gaps[-1]
    speech_end = last_start if last_end >= dur - 0.05 and dur - last_start >= LEAD_MIN else dur
    return speech_start, speech_end


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("用法: python3 scripts/trim_silence.py content/<日期>-<主题>/shipinhao")
    wd = Path(sys.argv[1])
    rec_dir = wd / "recordings"
    trim_dir = wd / "trim"
    trim_dir.mkdir(exist_ok=True)

    tts_txt = wd / "tts.txt"
    if not tts_txt.exists():
        sys.exit(f"缺配音稿 {tts_txt}")
    segments = [line for line in tts_txt.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not segments:
        sys.exit("tts.txt 没有可处理的非空段落")

    results: dict[str, float] = {}
    # The script is the source of truth.  Do not retain the former S1..S8 cap:
    # a recording studio project can contain any number of tts.txt lines.
    for n, _ in enumerate(segments, 1):
        src = rec_dir / f"s{n}.wav"
        if not src.exists():
            print(f"缺 {src}，跳过")
            continue
        b = speech_bounds(src)
        if not b:
            # A tightly trimmed take can have no detectable head/tail silence.
            # Keep it rather than silently omitting a valid script segment.
            source_dur = float(run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "csv=p=0", str(src),
            ]).stdout.strip())
            b = (0.0, source_dur)
            print(f"s{n}: 未测到首尾静音，保留完整录音")
        start, end = b
        start = max(0.0, round(start - 0.1, 3))
        end = min(round(end + 0.1, 3), float(run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", str(src),
        ]).stdout.strip()))
        dur = round(end - start, 3)
        out = trim_dir / f"s{n}.wav"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(src), "-ss", str(start), "-to", str(end), "-c", "copy", str(out)])
        results[f"S{n}"] = dur
        print(f"s{n}: [{start} ~ {end}] = {dur}s")

    total = sum(results.values())
    print(f"TOTAL: {total:.1f}s = {total/60:.2f}min")
    with open(trim_dir / "voice_dur.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("voice_dur.json 已写入（复制进 scenes.py VOICE_DUR）")


if __name__ == "__main__":
    main()
