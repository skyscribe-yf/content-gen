#!/usr/bin/env python3
"""GB300 篇：修复 MiniMax 跨段并句导致的切分错位。

问题：full.subtitle.json 把「段尾句 + 下一段首句」并成一个句子（4 处：句8/13/17/23），
tts_split 按句中点切段 → 每段混入相邻段语音，SB 时间戳错乱（S3/S5 出现 end<start）。
修复：ASR + silencedetect 定位真实段界（均落在段间静音停顿中点）：
  S2/S3 85.80（停顿 85.53-86.12）/ S3/S4 139.85（139.66-140.05）
  S4/S5 186.95（186.75-187.14）/ S5/S6 256.00（255.48-256.13）
做法：按真实段界重切 s1..s6.wav；跨段句在段界处拆成虚拟句，重建 sentence-boundaries.json。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

WD = Path("content/2026-11-14-国产大模型GB300之谜/shipinhao")
TT = WD / "tts"
TOTAL = 325.94  # full.wav ffprobe 实测

# 真实段界（全局秒）：段间停顿中点
BOUNDS = [0.0, 34.92, 85.80, 139.85, 186.95, 256.00, TOTAL]

# 跨段句拆分：句索引 -> (段界全局时间, 前段尾句文本, 后段首句文本)
SPLITS = {
    8:  (85.80,  "天然适合并行，还能跳转到任意位置，逐位置可复现。", "但随机数怎么摆进权重矩阵，才是指纹的关键。"),
    13: (139.85, "报告也很严谨：GB200 和 GB300 共享 152，B200 和 B300 共享 148，读数只能精确到斜杠两边那一档。", "你可能想问：训练要更新权重，初始化那点痕迹，还在吗？"),
    17: (186.95, "而实际观测是 49 到 1385 西格玛，远超偶然上限。", "证据还不止统计。"),
    23: (256.00, "上一代，V3、K2.5、M2.7，读出来还全是 Hopper，从 V4 和 K3 这一代起，才换成 Blackwell。", "所以到底证明了什么？"),
}

TAG_RE = re.compile(r"\([a-zA-Z]+\)|<#[\d.]+#>")


def clean(s: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]", "", TAG_RE.sub("", s))


def find_sub(s: str, sub: str, start: int = 0) -> int:
    pos = s.find(sub, start)
    if pos >= 0:
        return pos
    for k in range(len(sub), 2, -1):
        pos = s.find(sub[:k], start)
        if pos >= 0:
            return pos
    return -1


def ffprobe_dur(p: Path) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
        capture_output=True, text=True, check=True).stdout.strip())


def split_clips(text: str, limit: int = 26) -> list[str]:
    """按 。？！； 断句，超限再按 ，—— 拆（标点保留；与 tts_sb_create 同口径，输入带标点的原文）。"""
    PRIMARY = "。？！；"
    SECONDARY = "，——、"
    parts: list[str] = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in PRIMARY:
            parts.append(buf)
            buf = ""
    if buf:
        parts.append(buf)
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


def main() -> None:
    tts_lines = (WD / "tts.txt").read_text(encoding="utf-8").strip().split("\n")
    sub = json.loads((TT / "full.subtitle.json").read_text(encoding="utf-8"))
    assert len(tts_lines) == 6 and len(BOUNDS) == 7

    # ---------- 1. 重切音频 ----------
    durs = []
    for i in range(6):
        a, b = BOUNDS[i], BOUNDS[i + 1]
        out = TT / f"s{i + 1}.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-to", str(b),
             "-i", str(TT / "full.wav"), "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(out)],
            check=True)
        durs.append(round(b - a, 3))
        print(f"s{i + 1}: {a:.2f} ~ {b:.2f}  ({b - a:.2f}s)  实测 {ffprobe_dur(out):.2f}s")

    # ---------- 2. 重建虚拟句表（跨段句拆分）并按段界归属 ----------
    # 每项: (全局起, 全局止, clean文本)
    vsents = []
    for j, s in enumerate(sub):
        tb, te = s["time_begin"] / 1000, s["time_end"] / 1000
        if j in SPLITS:
            bt, head, tail = SPLITS[j]
            vsents.append((tb, bt, clean(head)))
            vsents.append((bt, te, clean(tail)))
        else:
            vsents.append((tb, te, clean(s["text"])))

    # 段归属：虚拟句中点落在哪个段区间
    seg_vsents: list[list] = [[] for _ in range(6)]
    for tb, te, stext in vsents:
        mid = (tb + te) / 2
        si = max(i for i in range(6) if BOUNDS[i] <= mid)
        seg_vsents[si].append((tb, te, stext))

    # ---------- 3. 按段组装 clips ----------
    segments = []
    for si, line in enumerate(tts_lines):
        seg_id = f"S{si + 1}"
        seg_start, seg_dur = BOUNDS[si], durs[si]
        seg_text = clean(line)  # 无标点：用于 clip 文本匹配
        raw_text = line          # 带标点：用于断句
        # 本段句子锚点（只在本段归属的虚拟句内顺序匹配）
        anchors = []
        pos = 0
        for tb, te, stext in seg_vsents[si]:
            t = find_sub(seg_text, stext, pos)
            if t < 0:
                raise SystemExit(f"{seg_id} 句子「{stext[:15]}」未定位")
            anchors.append((t, t + len(stext), tb - seg_start, te - seg_start))
            pos = t + 1
        if not anchors:
            raise SystemExit(f"{seg_id} 无句子锚点")
        clips = []
        cpos = 0
        for ctext in split_clips(raw_text):
            ctext_c = clean(ctext)
            if not ctext_c:
                continue
            cpos = find_sub(seg_text, ctext_c, cpos)
            if cpos < 0:
                print(f"  ⚠ {seg_id} clip「{ctext[:12]}」未定位，跳过")
                continue
            owner = None
            for ts, te, t0, t1 in anchors:
                if ts <= cpos <= te or (owner is None and ts <= cpos):
                    owner = (ts, te, t0, t1)
                elif ts > cpos:
                    break
            if owner is None:
                owner = anchors[-1]
            ts, te, t0, t1 = owner
            frac = 0.0 if te == ts else (cpos - ts) / (te - ts)
            clips.append({"id": f"{seg_id}-c{len(clips) + 1:02d}",
                          "start": round(t0 + frac * (t1 - t0), 3),
                          "end": 0.0, "text": ctext_c})
            cpos += len(ctext_c)
        for i, clip in enumerate(clips):
            clip["end"] = round(clips[i + 1]["start"], 3) if i + 1 < len(clips) else round(seg_dur, 3)
        segments.append({"id": seg_id, "duration": round(seg_dur, 3), "clips": clips})

    # ---------- 4. 校验 ----------
    ok = True
    for s in segments:
        prev_end = -1
        for c in s["clips"]:
            if c["start"] < -0.001 or c["end"] > s["duration"] + 0.001 or c["end"] < c["start"] - 0.001 or c["start"] < prev_end - 0.001:
                print(f"  ✗ {s['id']} {c['id']} {c['start']}~{c['end']} (dur={s['duration']})")
                ok = False
            prev_end = c["start"]
    n = sum(len(s["clips"]) for s in segments)
    print(f"clips 总数: {n}  校验: {'OK' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)

    out = TT / "sentence-boundaries.json"
    out.write_text(json.dumps({"source": "tts.txt", "segments": segments},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print("写回", out)
    print("VOICE_DUR = {" + ", ".join(f'"{s["id"]}": {s["duration"]}' for s in segments) + "}")


if __name__ == "__main__":
    main()
