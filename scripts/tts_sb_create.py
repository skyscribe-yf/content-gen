#!/usr/bin/env python3
"""从 full.subtitle.json（MiniMax 官方句子级时间戳）创建初始 sentence-boundaries.json。

TTS 流程首次生成 SB（tts_sb_rebuild.py 需要已有 SB 的 clip 文本结构，只重算时间戳）。
- clip 切分：先按 。？！； 断句，超 26 字再按 ，—— 拆（与 build 字幕拆句阈值一致）
- 时间戳：clip 起点 = 所在句子的 time_begin（段本地，相对段首句）；end = 下一 clip 起点或段时长
- 段时长 = ffprobe 实测 sN.wav（与 tts_split 一致）

用法:
  python3 scripts/tts_sb_create.py content/<日期>-<主题>/shipinhao
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SPLIT_CHARS = "。？！；"
SECONDARY = "，、——"


TAG_RE = re.compile(r"\((breath|sighs|gasps|laughs|pause)\)")


def clean(s: str) -> str:
    return re.sub(r"\s+", "", TAG_RE.sub("", s))


def ffprobe_dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def split_clips(text: str, limit: int = 26) -> list[str]:
    """按 。？！； 断句，超限再按 ，—— 拆。标点保留在前段。"""
    parts: list[str] = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in SPLIT_CHARS:
            parts.append(buf)
            buf = ""
    if buf:
        parts.append(buf)
    # 超限再拆
    out: list[str] = []
    for p in parts:
        if len(p) <= limit:
            out.append(p)
            continue
        seg = ""
        for ch in p:
            seg += ch
            if ch in SECONDARY and len(seg) >= limit * 0.6:
                out.append(seg)
                seg = ""
        if seg:
            out.append(seg)
    return out


def find_sub(s: str, sub: str, start: int = 0) -> int:
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
    ap.add_argument("workdir", help="shipinhao 工作目录（含 tts.txt 与 tts/）")
    args = ap.parse_args()

    wd = Path(args.workdir)
    tts_dir = wd / "tts"
    tts_lines = (wd / "tts.txt").read_text(encoding="utf-8").strip().split("\n")
    sub = json.loads((tts_dir / "full.subtitle.json").read_text(encoding="utf-8"))

    # 段边界 = ffprobe 实测段时长
    seg_bounds = [0.0] + [ffprobe_dur(tts_dir / f"s{i}.wav") for i in range(1, len(tts_lines) + 1)]
    print("段时长:", [round(b, 2) for b in seg_bounds[1:]], file=sys.stderr)

    # 段首句定位（与 tts_split 同款：段开头 10 字在句子拼接文本中找）
    joined, offsets = "", []
    for s in sub:
        offsets.append(len(joined))
        joined += clean(s["text"])
    seg_first = []
    for line in tts_lines:
        probe = clean(line)[:10]
        pos = joined.find(probe)
        if pos < 0:
            for k in range(len(probe), 2, -1):
                pos = joined.find(probe[:k])
                if pos >= 0:
                    break
        if pos < 0:
            raise SystemExit(f"段首句定位失败: {probe}")
        seg_first.append(max(j for j, o in enumerate(offsets) if o <= pos))
    seg_first.append(len(sub))

    segments = []
    for si, line in enumerate(tts_lines):
        seg_id = f"S{si + 1}"
        seg_text = clean(line)
        # 段首句可能带 (breath) 标签：锚点时间取标签前（= 段音频起点）
        first_begin = sub[seg_first[si]]["time_begin"] / 1000.0
        if TAG_RE.match(sub[seg_first[si]]["text"]):
            first_begin = 0.0
        seg_dur = seg_bounds[si + 1]
        first_begin = sub[seg_first[si]]["time_begin"] / 1000.0
        # 本段句子（全局索引）→ (段内字符区间, 段内时间)
        sent_info = []
        pos = 0
        for j in range(seg_first[si], seg_first[si + 1]):
            s = sub[j]
            t = find_sub(seg_text, clean(s["text"]), pos)
            if t < 0:
                print(f"  ⚠ {seg_id} 句子「{s['text'][:15]}」未定位", file=sys.stderr)
                continue
            t0 = s["time_begin"] / 1000.0 - first_begin
            t1 = s["time_end"] / 1000.0 - first_begin
            sent_info.append((t, t + len(clean(s["text"])), t0, t1))
            pos = t + 1
        if not sent_info:
            raise SystemExit(f"{seg_id} 无可用句子锚点")

        clips = []
        cpos = 0
        for ctext in split_clips(seg_text):
            cpos = find_sub(seg_text, ctext, cpos)
            if cpos < 0:
                print(f"  ⚠ {seg_id} clip「{ctext[:12]}」未定位，跳过", file=sys.stderr)
                continue
            owner = None
            for ts, te, t0, t1 in sent_info:
                if ts <= cpos <= te or (owner is None and ts <= cpos):
                    owner = (ts, te, t0, t1)
                elif ts > cpos:
                    break
            if owner is None:
                owner = sent_info[-1]
            ts, te, t0, t1 = owner
            frac = 0.0 if te == ts else (cpos - ts) / (te - ts)
            clips.append({"id": f"{seg_id}-c{len(clips) + 1:02d}",
                          "start": round(t0 + frac * (t1 - t0), 3),
                          "end": 0.0, "text": ctext})
            cpos += len(ctext)
        for i, clip in enumerate(clips):
            clip["end"] = round(clips[i + 1]["start"], 3) if i + 1 < len(clips) else round(seg_dur, 3)
        segments.append({"id": seg_id, "duration": round(seg_dur, 3), "clips": clips})

    out = tts_dir / "sentence-boundaries.json"
    out.write_text(json.dumps({"source": "tts.txt", "segments": segments},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写回 {out}", file=sys.stderr)
    for seg in segments:
        for c in seg["clips"]:
            print(f"  {c['id']} {c['start']:6.2f}-{c['end']:6.2f} {c['text'][:20]}", file=sys.stderr)


if __name__ == "__main__":
    main()
