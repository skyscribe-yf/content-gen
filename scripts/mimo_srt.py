#!/usr/bin/env python3
"""视频 -> 静音切分 -> MiMo ASR (mimo-v2.5-asr) -> SRT 字幕

用法:
    python3 scripts/mimo_srt.py video.mp4 --api-key $MIMO_API_KEY

原理: MiMo ASR 返回纯文本无时间戳，所以先按静音检测把音频切成完整句段，
逐段识别后用段起止时间拼 SRT，避免固定切片切断句子。
检测不到静音（如全程背景音乐）时回退为固定时长切片。
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

API = "https://api.xiaomimimo.com/v1/chat/completions"


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def transcribe(wav_path, api_key, lang):
    with open(wav_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = {
        "model": "mimo-v2.5-asr",
        "messages": [{
            "role": "user",
            "content": [{"type": "input_audio",
                         "input_audio": {"data": f"data:audio/wav;base64,{b64}"}}],
        }],
        "asr_options": {"language": lang},
    }
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"api-key": api_key, "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  重试 {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))


def detect_speech_segments(wav, dur, noise_db, min_silence, min_seg, max_seg):
    """用 silencedetect 找静音间隙，返回 (start, end) 语音段列表；无静音时返回 None"""
    proc = subprocess.run(
        ["ffmpeg", "-i", wav, "-af", f"silencedetect=noise={noise_db}dB:d={min_silence}",
         "-f", "null", "-"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-500:])
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", proc.stderr)]
    ends = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", proc.stderr)]
    segs = []
    prev = 0.0
    for s, e in zip(starts, ends):
        if s > prev:
            segs.append((prev, s))
        prev = e
    if dur > prev:
        segs.append((prev, dur))
    if not segs:
        return None
    # 短段与邻居合并，避免一堆 1 秒碎片
    merged = []
    for s, e in segs:
        if merged and (merged[-1][1] - merged[-1][0] < min_seg or e - s < min_seg):
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    # 无停顿长段截断（兜底，防超单次请求大小上限）
    final = []
    for s, e in merged:
        while e - s > max_seg:
            final.append((s, s + max_seg))
            s += max_seg
        final.append((s, e))
    return final


def fmt(sec):
    ms = round(sec * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--api-key", default=os.environ.get("XIAOMI_MIMO_API_KEY"), help="MiMo API Key（或设 XIAOMI_MIMO_API_KEY 环境变量）")
    ap.add_argument("--lang", default="auto", choices=["auto", "zh", "en"])
    ap.add_argument("--noise", type=float, default=-30.0, help="静音判定分贝阈值，越小越灵敏（全程背景音乐时调到 -35~-40）")
    ap.add_argument("--min-silence", type=float, default=0.4, help="多长的停顿算断句点（秒）")
    ap.add_argument("--min-seg", type=float, default=2.0, help="短于此的语音段并入邻居")
    ap.add_argument("--max-seg", type=float, default=120.0, help="单段上限，超过则截断")
    ap.add_argument("--chunk", type=float, default=60.0, help="检测不到静音时的回退切片秒数")
    ap.add_argument("--out", default="sub.srt")
    args = ap.parse_args()
    if not args.api_key:
        sys.exit("缺少 API Key：用 --api-key 或设 XIAOMI_MIMO_API_KEY")

    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, "a.wav")
        run(["ffmpeg", "-y", "-i", args.video, "-ar", "16000", "-ac", "1", wav])
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
            capture_output=True, text=True).stdout)

        segs = detect_speech_segments(wav, dur, args.noise, args.min_silence, args.min_seg, args.max_seg)
        if segs is None:
            print("未检测到静音，回退为固定切片", file=sys.stderr)
            segs = [(s, min(s + args.chunk, dur)) for s in range(0, int(dur), int(args.chunk))]
        print(f"共 {len(segs)} 段", file=sys.stderr)

        subs = []
        for i, (start, end) in enumerate(segs):
            seg = os.path.join(d, f"s{i}.wav")
            run(["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", wav, seg])
            text = transcribe(seg, args.api_key, args.lang)
            if text:
                subs.append((start, end, text))
            print(f"[{i + 1}/{len(segs)}] {fmt(start)} -> {fmt(end)}: {text}", file=sys.stderr)

    with open(args.out, "w", encoding="utf-8") as f:
        for i, (s, e, t) in enumerate(subs, 1):
            f.write(f"{i}\n{fmt(s)} --> {fmt(e)}\n{t}\n\n")
    print(f"已生成 {args.out}（{len(subs)} 条字幕）")


if __name__ == "__main__":
    main()
