#!/usr/bin/env python3
"""段边界修正（2026-11-09）：MiniMax 官方时间戳跨段并句 → 按 silencedetect 真实停顿重切。

问题：full.subtitle.json 的粗句把 S3 尾句与 S4 首句并入同一句（107.459-124.124s）、
S4 尾句与 S5 首句并入同一粗句（163.058-173.837s），scripts/tts_split.py 的
「段首 10 字定位 + 前后句中点」启发式把词切错 4-7 秒（S3 丢尾句悬念、S4 头尾错位）。

修法：
1. ffmpeg silencedetect 定位两个段界处的真实停顿（111.95s / 170.145s，见下 B34/B45）；
2. 用 ffmpeg 按真实停顿重切 tts/s3.wav、s4.wav、s5.wav（s1/s2/s6 原切分正确，不动）；
3. 重跑本脚本：把跨段粗句在真实边界处拆成伪句，按字符比例重算全部 clip 时间，
   写回 tts/sentence-boundaries.json（字幕 + at_clip 共用），顺带修正所有段
   ~0.1s 的系统性偏移（sb_create 以段首句 time_begin 为锚，实际段起点早 ~0.1s）。

用法（shipinhao 目录内）：
    python3 fix_boundaries.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent.parent / "scripts"))
from tts_sb_create import split_clips, find_sub, clean  # noqa: E402

B34 = 111.95   # S3/S4 真实边界（gap 115.751-116.568 中点，语音-run 速率映射验证）
B45 = 170.145  # S4/S5 真实边界（gap 170.008-170.278 中点，语音-run 速率映射验证）
SEG_STARTS = [0.0, 22.88, 60.36, B34, B45, 219.46]
SEG_DURS = [22.955, 37.547, 51.590, 58.195, 49.315, 57.963]  # 重切后 ffprobe 实测


def main() -> None:
    tts_dir = HERE / "tts"
    sub = json.loads((tts_dir / "full.subtitle.json").read_text(encoding="utf-8"))

    # 1) 跨段粗句在真实边界处拆成伪句
    ps: list[tuple[str, float, float]] = []
    for i, s in enumerate(sub):
        tb, te = s["time_begin"] / 1000, s["time_end"] / 1000
        txt = clean(s["text"])
        if i == 10:  # S3 尾 + S4 头
            k = txt.find("投影？") + len("投影？")
            ps.append((txt[:k], tb, B34))
            ps.append((txt[k:], B34, te))
        elif i == 15:  # S4 尾 + S5 头
            k = txt.find("日常。") + len("日常。")
            ps.append((txt[:k], tb, B45))
            ps.append((txt[k:], B45, te))
        else:
            ps.append((txt, tb, te))

    joined = "".join(p[0] for p in ps)
    offsets, o = [], 0
    for p in ps:
        offsets.append(o)
        o += len(p[0])

    tts_lines = (HERE / "tts.txt").read_text(encoding="utf-8").strip().split("\n")
    segments = []
    for si, line in enumerate(tts_lines):
        seg_id, seg_text = f"S{si + 1}", clean(line)
        start, dur = SEG_STARTS[si], SEG_DURS[si]
        pos = joined.find(seg_text)
        assert pos >= 0, f"{seg_id} 未定位"
        sent_info = []
        for j, (txt, tb, te) in enumerate(ps):
            s0, s1 = offsets[j], offsets[j] + len(txt)
            lo, hi = max(s0, pos), min(s1, pos + len(seg_text))
            if lo < hi:
                f0 = (lo - s0) / len(txt)
                f1 = (hi - s0) / len(txt)
                sent_info.append((lo - pos, hi - pos,
                                  tb + f0 * (te - tb) - start,
                                  tb + f1 * (te - tb) - start))
        clips, cpos = [], 0
        for ctext in split_clips(seg_text):
            cpos = find_sub(seg_text, ctext, cpos)
            assert cpos >= 0, f"{seg_id} clip 未定位: {ctext[:12]}"
            owner = None
            for ts, te_c, t0, t1 in sent_info:
                if ts <= cpos <= te_c or (owner is None and ts <= cpos):
                    owner = (ts, te_c, t0, t1)
                elif ts > cpos:
                    break
            ts, te_c, t0, t1 = owner if owner else sent_info[-1]
            frac = 0.0 if te_c == ts else (cpos - ts) / (te_c - ts)
            clips.append({"id": f"{seg_id}-c{len(clips) + 1:02d}",
                          "start": round(t0 + frac * (t1 - t0), 3), "end": 0.0, "text": ctext})
            cpos += len(ctext)
        for i, c in enumerate(clips):
            c["end"] = round(clips[i + 1]["start"], 3) if i + 1 < len(clips) else round(dur, 3)
        segments.append({"id": seg_id, "duration": round(dur, 3), "clips": clips})

    out = {"source": "tts.txt", "segments": segments}
    (tts_dir / "sentence-boundaries.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写回 {tts_dir / 'sentence-boundaries.json'}（{len(segments)} 段）")


if __name__ == "__main__":
    main()
