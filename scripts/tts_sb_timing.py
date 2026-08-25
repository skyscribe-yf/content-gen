#!/usr/bin/env python3
"""MiMo ASR 细窗重定位 sentence-boundaries.json 的 clip 时间戳（av-sync.md 第 4 节方法）。

台词文本未变 → 复用旧 SB 的 clips 文本结构，只为新配音重算每个 clip 的 start。
方法：
  1. 每段 sN.wav 用 2s 窗（步进 1.5s）ASR 粗扫，构建「时间→文本」地图
  2. 每个 clip 的开头 8 字在粗扫地图中定位 → 粗位置
  3. 粗位置前后细窗（0.5s 步进 0.25s）ASR 确认句子起点（0.25s 精度）
  4. end = 下一 clip 起点（段末 clip = 段时长），写回 sentence-boundaries.json

用法:
  python3 scripts/tts_sb_timing.py content/<日期>-<主题>/shipinhao
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mimo_srt import transcribe


def clean(s: str) -> str:
    return re.sub(r"\s+", "", s)


def dur_of(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def coarse_scan(wav: Path, key: str, win: float = 2.0, step: float = 1.5):
    """2s 窗粗扫全段 → [(窗起点, 文本)]。"""
    dur = dur_of(wav)
    entries = []
    t = 0.0
    while t < dur - 0.5:
        end = min(t + win, dur)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-to", str(end),
             "-i", str(wav), "-ac", "1", "-ar", "16000", tmp],
            check=True,
        )
        try:
            text = transcribe(tmp, key, "zh")
        except Exception as e:
            print(f"  ⚠ 窗 {t:.1f}s ASR 失败: {e}", file=sys.stderr)
            text = ""
        finally:
            Path(tmp).unlink(missing_ok=True)
        entries.append((t, clean(text)))
        t += step
    return entries


def locate_probe(probe: str, map_entries: list[tuple[float, str]]) -> float | None:
    """clip 开头文字首次出现的窗起点（粗定位）。"""
    best_t, best_pos = None, -1
    for t, text in map_entries:
        pos = text.find(probe)
        if pos >= 0 and (best_t is None or pos < best_pos or (pos == best_pos and t < best_t)):
            best_t, best_pos = t, pos
    return best_t


def refine_start(wav: Path, key: str, approx: float, probe: str, dur: float,
                 win: float = 1.0, step: float = 0.25, max_back: float = 1.5) -> float:
    """在 approx 附近向前细扫，找 probe 首次出现的窗起点（0.25s 精度）。"""
    best = None
    t = max(0.0, approx - max_back)
    while t <= min(approx + win, dur - 0.3):
        end = min(t + win, dur)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-to", str(end),
             "-i", str(wav), "-ac", "1", "-ar", "16000", tmp],
            check=True,
        )
        try:
            text = clean(transcribe(tmp, key, "zh"))
        except Exception as e:
            print(f"  ⚠ 细窗 {t:.2f}s ASR 失败: {e}", file=sys.stderr)
            text = ""
        finally:
            Path(tmp).unlink(missing_ok=True)
        if probe in text:
            best = t
            break
        t += step
    if best is None:
        return approx
    return best


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("workdir", help="shipinhao 工作目录（含 tts/）")
    ap.add_argument("--probe-len", type=int, default=8, help="clip 开头匹配字数（默认 8）")
    args = ap.parse_args()

    wd = Path(args.workdir)
    tts_dir = wd / "tts"
    key = __import__("os").environ.get("XIAOMI_MIMO_API_KEY") or __import__("os").environ.get("MIMO_API_KEY")
    if not key:
        raise SystemExit("缺少 XIAOMI_MIMO_API_KEY")

    sb = json.loads((tts_dir / "sentence-boundaries.json").read_text(encoding="utf-8"))
    old = json.loads(sb["source"]) if False else None  # keep structure
    for seg in sb["segments"]:
        seg_id = seg["id"]
        wav = tts_dir / f"{seg_id}.wav"
        if not wav.exists():
            raise SystemExit(f"缺 {wav}")
        dur = dur_of(wav)
        print(f"=== {seg_id} ({dur:.1f}s, {len(seg['clips'])} clips) 粗扫…", file=sys.stderr)
        coarse = coarse_scan(wav, key)
        starts = []
        clips = seg["clips"]
        for i, clip in enumerate(clips):
            probe = clean(clip["text"])[: args.probe_len]
            approx = locate_probe(probe, coarse)
            if approx is None:
                # 前一句末尾可能被并入 → 用上一 clip 起点近似
                approx = starts[-1] if starts else 0.0
                print(f"  ⚠ {clip['id']}「{probe}」粗定位失败，用 {approx:.2f}", file=sys.stderr)
            start = refine_start(wav, key, approx, probe, dur)
            # 单调性：不得早于上一 clip（ASR 噪声可能提前命中）
            if starts and start < starts[-1]:
                start = starts[-1]
            starts.append(start)
            clip["start"] = round(start, 3)
            print(f"  {clip['id']} → {start:6.2f}s  {clip['text'][:16]}", file=sys.stderr)
        # end = 下一 clip 起点；段末 = 段时长
        for i, clip in enumerate(clips):
            clip["end"] = round(starts[i + 1], 3) if i + 1 < len(clips) else round(dur, 3)
        seg["duration"] = round(dur, 3)
        # 保证单调
        for a, b in zip(starts, starts[1:]):
            if b < a:
                print(f"  ⚠ {seg_id} 非单调 {a} → {b}", file=sys.stderr)

    out = tts_dir / "sentence-boundaries.json"
    out.write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写回 {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
