#!/usr/bin/env python3
"""修正 grpo-math 视频号段落切分：MiniMax 句子时间戳跨段 → S3/S4 边界错位。

ASR 验证结论（head/tail 逐段抽验）：S1/S2、S2/S3、S4/S5、S5/S6 边界全部正确；
唯一错位 S3/S4：s4.wav 开头混入 S3 尾句「但长度这件事，还藏着更荒唐的第三堵。」
（切点 168.15 落在句中）。正确切点 = 停顿 171.32-171.63 中点 171.47s，S4 语音起点 171.63s。
其余边界沿用 tts_split 切点（ASR 验证段头段尾内容对齐，切点落在句中停顿）。
"""
import json, re, subprocess, sys
from pathlib import Path

WD = Path("content/2026-09-13-grpo-math/shipinhao")
TT = WD / "tts"
TAG_RE = re.compile(r"\((breath|sighs|gasps|laughs|pause)\)|<#[\d.]+#>")

def clean(s): return re.sub(r"\s+", "", TAG_RE.sub("", s))

SPLIT_CHARS = "。？！；"
SECONDARY = "，、——"

def split_clips(text: str, limit: int = 26) -> list[str]:
    parts, buf = [], ""
    for ch in text:
        buf += ch
        if ch in SPLIT_CHARS:
            parts.append(buf); buf = ""
    if buf: parts.append(buf)
    out = []
    for p in parts:
        if len(p) <= limit:
            out.append(p); continue
        seg = ""
        for ch in p:
            seg += ch
            if ch in SECONDARY and len(seg) >= limit * 0.6:
                out.append(seg); seg = ""
        if seg: out.append(seg)
    return out

def dur_of(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],
                 capture_output=True,text=True,check=True).stdout.strip())

# (段i语音起点global, 切点global)；S3/S4 为 ASR+silencedetect 修正值，其余沿用 tts_split
BOUNDS = [(0.00, 0.00), (43.90, 43.75), (119.30, 119.07),
          (171.63, 171.47), (228.70, 228.51), (268.50, 268.32), (None, None)]

lines = (WD/"tts.txt").read_text(encoding="utf-8").strip().split("\n")
sub = json.loads((TT/"full.subtitle.json").read_text(encoding="utf-8"))
FULL_END = dur_of(TT/"full.wav")
BOUNDS[-1] = (FULL_END, FULL_END)

# ---- 1. 重切 s1..s6.wav ----
for i in range(len(lines)):
    a, b = BOUNDS[i][1], BOUNDS[i+1][1]
    out = TT/f"s{i+1}.wav"
    subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{a:.3f}","-to",f"{b:.3f}",
                    "-i",str(TT/"full.wav"),"-ar","24000","-ac","1",str(out)],check=True)
    print(f"s{i+1}.wav  [{a:.2f}, {b:.2f}]  dur={dur_of(out):.2f}")

# ---- 2. 重建 sentence-boundaries.json ----
joined, soff = "", []
for s in sub:
    soff.append(len(joined)); joined += clean(s["text"])
seg_char = []
for line in lines:
    probe = clean(line)[:10]
    pos = joined.find(probe)
    if pos < 0:
        for k in range(len(probe), 2, -1):
            pos = joined.find(probe[:k])
            if pos >= 0: break
    seg_char.append(pos)
seg_char.append(len(joined))

segments = []
for si, line in enumerate(lines):
    seg_id = f"S{si+1}"
    c0, c1 = seg_char[si], seg_char[si+1]
    seg_text = clean(line)
    t_start, t_end = BOUNDS[si][0], BOUNDS[si+1][0]
    seg_dur = dur_of(TT/f"s{si+1}.wav")
    sent_info = []
    for j, s in enumerate(sub):
        js, je = soff[j], soff[j] + len(clean(s["text"]))
        if je <= c0 or js >= c1:
            continue
        a, b = max(js, c0), min(je, c1)
        tb, te = s["time_begin"]/1000.0, s["time_end"]/1000.0
        ta = tb + (a - js)/(je - js)*(te - tb) if je > js else tb
        tbv = te + (b - je)/(je - js)*(te - tb) if je > js else te
        ta, tbv = max(ta, t_start), min(tbv, t_end)
        sent_info.append((a - c0, b - c0, ta - t_start, tbv - t_start, j))
    clips = []
    cpos = 0
    for ctext in split_clips(seg_text):
        p = seg_text.find(ctext, cpos)
        if p < 0:
            print(f"  ⚠ {seg_id} clip「{ctext[:12]}」未定位", file=sys.stderr); continue
        owner = None
        for cs, ce, t0, t1, j in sent_info:
            if cs <= p < ce or (owner is None and cs <= p):
                owner = (cs, ce, t0, t1)
            elif cs > p:
                break
        if owner is None: owner = sent_info[-1]
        cs, ce, t0, t1 = owner
        frac = 0.0 if ce == cs else (p - cs)/(ce - cs)
        start = t0 + frac*(t1 - t0)
        if clips: start = max(start, clips[-1]["start"])
        start = min(max(start, 0.0), seg_dur)
        clips.append({"id": f"{seg_id}-c{len(clips)+1:02d}", "start": round(start,3), "end": 0.0, "text": ctext})
        cpos = p + len(ctext)
    for i, c in enumerate(clips):
        c["end"] = round(clips[i+1]["start"],3) if i+1 < len(clips) else round(seg_dur,3)
    segments.append({"id": seg_id, "duration": round(seg_dur,3), "clips": clips})

out = TT/"sentence-boundaries.json"
out.write_text(json.dumps({"source":"tts.txt","segments":segments}, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nVOICE_DUR = {" + ", ".join(f'"S{i+1}": {s["duration"]:.2f}' for i,s in enumerate(segments)) + "}")
bad = 0
for s in segments:
    for c in s["clips"]:
        if c["start"] > s["duration"] + 1e-6 or c["end"] < c["start"] - 1e-6:
            print(f"  ⚠ 越界 {c['id']} {c['start']}-{c['end']} (dur {s['duration']})"); bad += 1
print(f"写回 {out}（{sum(len(s['clips']) for s in segments)} clips，越界 {bad}）")
for s in segments:
    print(f"  {s['id']} dur={s['duration']:.2f} clips={len(s['clips'])}  first={s['clips'][0]['start']:.2f} last_end={s['clips'][-1]['end']:.2f}")
