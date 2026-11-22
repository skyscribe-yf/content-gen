#!/usr/bin/env python3
"""修正 GAE 视频号段落切分：MiniMax 句子时间戳跨段 → 段边界错位。

修正边界（ASR + silencedetect 双重定位，均落在段尾标点后的自然停顿）：
  S1/S2: 语音 44.35s（停顿 43.88-44.35），S2 头「为什么不能总账照发？」
  S2/S3: 语音 102.30s（句间停顿 102.20-102.30），S3 头「第一步，造一把单步尺子」
  S3/S4: 语音 163.90s（停顿 163.58-163.90），S4 头「有了一把尺子」
  S4/S5: 语音 213.95s（停顿 213.44-213.95），S5 头「把数值放进去」
  S5/S6: 语音 272.90s（句间停顿 272.70-272.90），S6 头「λ等于1」
切点取停顿中点（不切碎音节）；SB 插值用语音起点。
"""
import json, re, subprocess, sys
from pathlib import Path

WD = Path("content/2026-08-25-gae/shipinhao")
TT = WD / "tts"
TAG_RE = re.compile(r"\((breath|sighs|gasps|laughs|pause)\)|<#[\d.]+#>")

def clean(s): return re.sub(r"\s+", "", TAG_RE.sub("", s))

SPLIT_CHARS = "。？！；"
SECONDARY = "，、——"

def split_clips(text: str, limit: int = 26) -> list[str]:
    """按 。？！； 断句，超限再按 ，—— 拆（与 tts_sb_create 同规则）。"""
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

# (段i语音起点global, 切点global)
BOUNDS = [(0.00, 0.00), (44.35, 44.11), (102.30, 102.25), (163.90, 163.74),
          (213.95, 213.70), (272.90, 272.80), (None, None)]

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
# 全局拼接文本 + 每句 char 区间
joined, soff = "", []
for s in sub:
    soff.append(len(joined)); joined += clean(s["text"])
# 每段 char 区间（段头10字定位）
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
    c0, c1 = seg_char[si], seg_char[si+1]          # 段内 char 区间（全局坐标）
    seg_text = clean(line)
    t_start, t_end = BOUNDS[si][0], BOUNDS[si+1][0]  # 段语音起止（global）
    seg_dur = dur_of(TT/f"s{si+1}.wav")
    # 收集与本段相交的句子 → (句内char起, 句内char止, 段时间起, 段时间止) 段内相对
    sent_info = []
    for j, s in enumerate(sub):
        js, je = soff[j], soff[j] + len(clean(s["text"]))
        if je <= c0 or js >= c1:
            continue
        a, b = max(js, c0), min(je, c1)            # 交集 char（全局）
        # 时间：句内按 char 比例映射到 [max(tb,t_start), min(te,t_end)]
        tb, te = s["time_begin"]/1000.0, s["time_end"]/1000.0
        ta = tb + (a - js)/(je - js)*(te - tb) if je > js else tb
        tbv = te + (b - je)/(je - js)*(te - tb) if je > js else te
        ta, tbv = max(ta, t_start), min(tbv, t_end)
        sent_info.append((a - c0, b - c0, ta - t_start, tbv - t_start, j))
    # clip 起点 = 所属句子内 char 比例插值
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
        # 单调 + 不越段
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
