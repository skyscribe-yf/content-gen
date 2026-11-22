#!/usr/bin/env python3
"""修剪 S2 内一处 1.58s 句间静音（c04「全错，同理。」→ c05「这不是偶发故障。」）。

B5 门禁：成品最长静音 <1.5s。silencedetect 定位 s2.wav 静音 16.01-17.39s（1.38s），
但成品（aac）实测 1.575s 超限。切除 [16.20, 16.45] 0.25s（静音区中部，离语音缘 ≥0.19s）：
- s2.wav 新时长 75.32 - 0.25 = 75.07s
- SB：start ≥ 16.45 的 clip 全部 -0.25；c05（start 16.31 落在切除区）置 16.95
  （语音 17.14s 恢复，字幕提前 0.19s 入场，与其他 clip 行为一致）
"""
import json, subprocess
from pathlib import Path

TT = Path("content/2026-09-13-grpo-math/shipinhao/tts")
CUT_A, CUT_B = 16.20, 16.45
SHIFT = CUT_B - CUT_A

def dur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                 "-of","csv=p=0",str(p)],capture_output=True,text=True,check=True).stdout.strip())

old = dur(TT/"s2.wav")
# 切两段再拼接（重编码到 24k 单声道，与 tts_split 输出一致）
subprocess.run(["ffmpeg","-y","-v","error","-ss","0","-to",f"{CUT_A}","-i",str(TT/"s2.wav"),
                "-ar","24000","-ac","1","/tmp/s2_a.wav"],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{CUT_B}","-i",str(TT/"s2.wav"),
                "-ar","24000","-ac","1","/tmp/s2_b.wav"],check=True)
with open("/tmp/s2_list.txt","w") as f:
    f.write("file '/tmp/s2_a.wav'\nfile '/tmp/s2_b.wav'\n")
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i","/tmp/s2_list.txt",
                "-c","copy",str(TT/"s2.wav")],check=True)
new = dur(TT/"s2.wav")
print(f"s2.wav: {old:.2f}s -> {new:.2f}s (切除 {SHIFT}s)")

# 重写 SB：S2 段 clip 平移
sb = json.loads((TT/"sentence-boundaries.json").read_text(encoding="utf-8"))
seg = next(s_ for s_ in sb["segments"] if s_["id"] == "S2")
for c in seg["clips"]:
    if c["start"] >= CUT_B:
        c["start"] = round(c["start"] - SHIFT, 3)
        c["end"] = round(c["end"] - SHIFT, 3)
    elif c["start"] >= CUT_A:
        c["start"] = 16.95   # c05：切除区内，手动置到语音恢复前 0.19s
# c04.end 跟随 c05.start
for i, c in enumerate(seg["clips"]):
    if i + 1 < len(seg["clips"]):
        c["end"] = seg["clips"][i+1]["start"]
    else:
        c["end"] = round(new, 3)
seg["duration"] = round(new, 3)
(TT/"sentence-boundaries.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")
print("S2 duration ->", seg["duration"], " clips:", len(seg["clips"]))
print("c04:", [c for c in seg["clips"] if c["id"]=="S2-c04"][0])
print("c05:", [c for c in seg["clips"] if c["id"]=="S2-c05"][0])
print("c06:", [c for c in seg["clips"] if c["id"]=="S2-c06"][0])
bad = 0
for s_ in sb["segments"]:
    for c in s_["clips"]:
        if c["start"] > s_["duration"] + 1e-6 or c["end"] < c["start"] - 1e-6:
            print(f"  ⚠ 越界 {c['id']}"); bad += 1
print(f"越界 {bad}")
# 复扫修剪后静音
r = subprocess.run(["ffmpeg","-v","info","-i",str(TT/"s2.wav"),
                    "-af","silencedetect=noise=-35dB:d=1.5","-f","null","-"],
                   capture_output=True,text=True)
print("s2.wav ≥1.5s 静音事件:", r.stderr.count("silence_start"))
