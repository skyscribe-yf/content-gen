#!/usr/bin/env python3
"""用新 full.subtitle.json（MiniMax 官方句子级时间戳）重建 sentence-boundaries.json。

台词文本未变 → 复用旧 SB 的 clip 文本结构；时间戳 = 句子锚点 + 句内文本比例插值。
- 句子级时间戳来自 MiniMax 官方（精确到句子边界）
- 句内 clip 按 clean 文本字符偏移比例插值（TTS 语速句内近似均匀，误差 ~0.1-0.3s）
- 段边界 = tts_split 的段时长（ffprobe s1..s6.wav 实测）

用法:
  python3 scripts/tts_sb_rebuild.py content/<日期>-<主题>/shipinhao
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def clean(s: str) -> str:
    return re.sub(r"\s+", "", s)


def ffprobe_dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def find_sub(s: str, sub: str, start: int = 0) -> int:
    """子串定位，找不到回退最长前缀。返回 -1 表示彻底失败。"""
    pos = s.find(sub, start)
    if pos >= 0:
        return pos
    for k in range(len(sub), 2, -1):
        pos = s.find(sub[:k], start)
        if pos >= 0:
            return pos
    return -1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("workdir", help="shipinhao 工作目录（含 tts/）")
    args = ap.parse_args()

    wd = Path(args.workdir)
    tts_dir = wd / "tts"

    tts_lines = (tts_dir / ".." / "tts.txt").read_text(encoding="utf-8").strip().split("\n")
    # 兼容 tts.txt 在 tts/ 或 shipinhao/ 下
    if len(tts_lines) < 2:
        tts_lines = (tts_dir / "tts.txt").read_text(encoding="utf-8").strip().split("\n")
    sub = json.loads((tts_dir / "full.subtitle.json").read_text(encoding="utf-8"))
    old = json.loads((tts_dir / "sentence-boundaries.json.bak-asr").read_text(encoding="utf-8"))
    # 段边界 = ffprobe 实测段时长（与 tts_split 一致）
    seg_bounds: list[float] = [0.0]
    for i in range(1, len(tts_lines) + 1):
        seg_bounds.append(ffprobe_dur(tts_dir / f"s{i}.wav"))
    print("段时长:", [round(b, 2) for b in seg_bounds[1:]], file=sys.stderr)

    # 段首句 = 段开头 10 字在句子拼接文本中定位（与 tts_split 同款）
    joined, offsets = "", []
    for s in sub:
        offsets.append(len(joined))
        joined += clean(s["text"])
    seg_first = []  # 每段首句在 sub 中的索引
    for line in tts_lines:
        probe = clean(re.sub(r"<#\d+(\.\d+)?#>", "", line))[:10]
        pos = joined.find(probe)
        if pos < 0:
            for k in range(len(probe), 2, -1):
                pos = joined.find(probe[:k])
                if pos >= 0:
                    break
        if pos < 0:
            raise SystemExit(f"段首句定位失败: {probe}")
        seg_first.append(max(j for j, o in enumerate(offsets) if o <= pos))
    seg_first.append(len(sub))  # 哨兵
    print("段首句索引:", seg_first[:-1], file=sys.stderr)

    old_segs = {s["id"]: s for s in old["segments"]}
    for si in range(len(tts_lines)):
        seg_id = f"s{si + 1}"
        a, b = 0.0, seg_bounds[si + 1]  # 段本地时长（seg_bounds[0]=0, [1..]=每段时长）
        seg_text = clean(re.sub(r"<#\d+(\.\d+)?#>", "", tts_lines[si]))
        # 本段句子（全局索引 [seg_first[si], seg_first[si+1])）→ 段本地时间
        sent_info = []
        pos = 0
        for j in range(seg_first[si], seg_first[si + 1]):
            s = sub[j]
            t = find_sub(seg_text, clean(s["text"]), pos)
            if t < 0:
                print(f"  ⚠ {seg_id} 句子「{s['text'][:15]}」在段文本中未定位", file=sys.stderr)
                continue
            t0 = s["time_begin"] / 1000 - sub[seg_first[si]]["time_begin"] / 1000
            t1 = s["time_end"] / 1000 - sub[seg_first[si]]["time_begin"] / 1000
            sent_info.append((t, t + len(clean(s["text"])), t0, t1))
            pos = t + 1
        if not sent_info:
            raise SystemExit(f"{seg_id} 无可用句子锚点")

        clips = old_segs[seg_id]["clips"]
        starts = []
        for clip in clips:
            ctext = clean(clip["text"])
            if not ctext:
                starts.append(starts[-1] if starts else 0.0)
                continue
            # clip 在段文本中的位置
            cpos = find_sub(seg_text, ctext)
            if cpos < 0:
                # 回退：clip 文本可能跨句子边界被拆，用前一 clip 结尾
                print(f"  ⚠ {seg_id} clip「{ctext[:12]}」段内未定位，取前值", file=sys.stderr)
                starts.append(starts[-1] if starts else 0.0)
                continue
            # 找 clip 所属句子（cpos 落在句子区间内；跨句则取前句尾部锚点）
            owner = None
            for j, (ts, te, t0, t1) in enumerate(sent_info):
                if ts <= cpos <= te or (owner is None and ts <= cpos):
                    owner = (ts, te, t0, t1)
                elif ts > cpos:
                    break
            if owner is None:
                owner = sent_info[-1]
            ts, te, t0, t1 = owner
            frac = 0.0 if te == ts else (cpos - ts) / (te - ts)
            starts.append(t0 + frac * (t1 - t0))
        # end = 下一 clip 起点；段末 = 段时长
        for i, clip in enumerate(clips):
            clip["start"] = round(starts[i], 3)
            clip["end"] = round(starts[i + 1], 3) if i + 1 < len(clips) else round(b, 3)
        old_segs[seg_id]["duration"] = round(b, 3)
        # 单调性检查
        bad = [i for i in range(1, len(starts)) if starts[i] < starts[i - 1] - 0.001]
        if bad:
            print(f"  ⚠ {seg_id} 非单调 clip 索引: {bad}", file=sys.stderr)

    out = tts_dir / "sentence-boundaries.json"
    out.write_text(json.dumps(old, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写回 {out}", file=sys.stderr)
    # 打印 S1 全部 clip 供人工抽查
    for clip in old_segs["s1"]["clips"]:
        print(f"  S1 {clip['id']} {clip['start']:6.2f}-{clip['end']:6.2f} {clip['text'][:18]}", file=sys.stderr)


if __name__ == "__main__":
    main()
