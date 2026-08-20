#!/usr/bin/env python3
"""口播录音一键处理：修音 → 一致性补偿 → 时长 → 停顿分析 → 字幕时间戳。

口播模式（替代 MiniMax TTS 克隆）专用脚本。作者按 tts.txt 逐段录音后，
本脚本一次性完成：
  1. 修音   recordings/sN.wav -> tts/sN.wav（去噪 + 响度统一 + 降高频毛刺）
  2. 一致性 波形+频谱分析各段 -> 选最佳段为锚 -> 频段补偿 -> 段间响度/动态统一
  3. 时长   ffprobe 每段 -> 打印 VOICE_DUR（复制进 scenes.py）
  4. 停顿    silencedetect 每段 -> tts/pauses.json（句子级停顿边界，build 字幕对齐用）

用法:
  python3 scripts/voice_process.py content/<日期>-<主题>/shipinhao

前置:
  shipinhao/recordings/s1.wav..sN.wav   作者原始分段录音（与 tts.txt 每段对应）
  shipinhao/tts.txt                     配音稿（每段一行，字幕基准）

产物:
  tts/s1..sN.wav       修音+一致性补偿后的分段（manim_video_build.py 直接消费）
  tts/pauses.json      每段句子级停顿边界
  tts/consistency.json 每段频段能量 + 补偿量（体检报告）
  VOICE_DUR 打印       复制进 scenes.py

一致性补偿（2026-08-16 新增，解决「某段声音能量不集中/发虚/发闷」）:
  - 波形分析: astats 测每段整体 RMS（能量）
  - 频谱分析: 按 4 个语音关键频段(低/中低/中高/高)分别 bandpass 后测 RMS，
             得到每段频谱能量分布 -> 定位「发虚(中频弱)/发闷(高频缺)/偏亮(高频多)」
  - 选锚段: 综合「频段最均衡(能量最集中) + 整体能量不过弱」的一段
  - 补偿: 每段各频段增益向锚段对齐（差 >3dB 才补，避免过度处理），
         再 loudnorm 统一响度(LRA) -> 段间听感一致
  - --no-consistency 可关闭；--consistency-report 只看报告不动音频

    注意:
  - 停顿/质量分析优先基于【裁剪后录音】trim/sN.wav（Web 录音室生成；去掉头尾准备静音且仍未经过 loudnorm）。没有最新 trim 文件时回退 raw；loudnorm/afftdn 会抬底噪把真实静音填满，不能拿最终 clean 音频测停顿
  - 频谱一致性分析基于【修音后】clean（对干净信号判断频段，避免噪声干扰）；停顿仍从 raw 取
  - 停顿阈值：静音 >=0.35s 视为句间停顿（真人句子之间自然留白；更短的是句内微停顿）
  - 录音质量参考：每段语音占比与最长静音段输出，供作者判断哪段该重录
  - 修音滤镜链可调（见 DEFAULT_FILTER），默认适合手机/桌面麦录音
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path


# 修音滤镜链：高通去隆隆声 -> afftdn 去噪（nf 噪声底）-> 提亮（presence + 减高频衰减）-> 响度统一
# 2026-08-19 用户反馈「口播修音后发闷」：原 highshelf 8.5kHz -3dB 压掉空气感/齿音区是主因。
# 改为 9kHz -1.5dB（保留轻微去毛刺）+ 3.2kHz presence +2dB（清晰度/临场感，不刺耳）。
# nf=-25 适中（过高会吃掉齿音/s音）；录音底噪大时调到 -30
DEFAULT_FILTER = (
    "highpass=f=60,"
    "afftdn=nf=-25,"
    "highshelf=f=9000:g=-1.5:width=1.2,"
    "equalizer=f=3200:t=q:w=1.0:g=+2,"
    "loudnorm=I=-16:TP=-1.5:LRA=11"
)
SILENCE_DB = -30      # 静音判定阈值（2026-08-17：-35 漏检 8% 真实停顿，RLHF 02:06 处 0.37s 停顿未检出导致字幕不同步）
SILENCE_MIN = 0.35    # 句间停顿最短静音时长（s）

# 语音关键频段（用于频谱能量分析 + 一致性补偿）：(名称, 中心频率, Q带宽)
#   低    80-250Hz   基频/胸腔
#   中低  250-1kHz   元音能量（主承载）
#   中高  1k-4kHz    辅音/清晰度（「发虚」通常这里弱）
#   高    4k-8kHz    齿音/空气感（「发闷」通常这里缺）
FREQ_BANDS = [
    ("low", 160, 0.9),
    ("mid_low", 500, 0.9),
    ("mid_high", 2000, 0.9),
    ("high", 5600, 1.0),
]
# 补偿触发阈值(dB)：某段某频段相对锚段差超过此值才补偿，避免过度处理
EQ_THRESHOLD_DB = 3.0
# 补偿上限(dB)：单频段最大补/减量，防止失真
EQ_MAX_GAIN_DB = 6.0


def run(cmd: list[str], **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def dur_of(path: Path) -> float:
    return float(
        run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)]).stdout.strip()
    )


def silence_analysis(path: Path) -> list[float]:
    """返回该段内句间停顿边界（每次>=SILENCE_MIN 的静音结束时刻，即下一句起点）。"""
    r = run(["ffmpeg", "-i", str(path), "-af",
             f"silencedetect=noise={SILENCE_DB}dB:d={SILENCE_MIN}", "-f", "null", "-"])
    gaps = re.findall(r"silence_start: ([0-9.]+)\n.*?silence_end: ([0-9.]+)", r.stderr, re.DOTALL)
    starts = [float(e) for _, e in gaps]
    return sorted({round(s, 3) for s in starts if s > 0.05})


def load_manual_boundaries(wd: Path) -> dict:
    """Read Web-studio corrections without making CLI users depend on them."""
    path = wd / "recordings" / "manual-boundaries.json"
    if not path.exists():
        return {"segments": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {"segments": {}}
    return data if isinstance(data, dict) and isinstance(data.get("segments"), dict) else {"segments": {}}


def prepared_manual_clips(
    manual: dict,
    seg: str,
    script: str,
    source_duration: float,
    output_duration: float,
) -> list[dict]:
    """Validate and scale a Web-confirmed text/audio map for the final WAV.

    The source is the reviewed trim WAV; the output is its cleaned 44.1 kHz
    counterpart.  They normally have equal duration, but using an explicit scale
    avoids an AAC/resampling rounding error shifting subtitles at the end.
    """
    candidate = manual.get("segments", {}).get(seg)
    if not isinstance(candidate, dict) or not isinstance(candidate.get("clips"), list):
        return []
    try:
        recorded_duration = float(candidate["source_duration"])
    except (KeyError, TypeError, ValueError):
        return []
    if recorded_duration <= 0 or source_duration <= 0 or output_duration <= 0:
        return []
    clips: list[dict] = []
    previous_end = 0.0
    for item in candidate["clips"]:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            return []
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            return []
        if not 0.0 <= start < end <= recorded_duration + 0.01 or start < previous_end - 0.01:
            return []
        clips.append({"id": str(item.get("id", "")), "start": start, "end": end, "text": item["text"]})
        previous_end = end
    if not clips or re.sub(r"\s+", "", "".join(clip["text"] for clip in clips)) != re.sub(r"\s+", "", script):
        return []
    # The reviewed WAV itself is authoritative if an old metadata duration differs slightly.
    scale = output_duration / source_duration
    return [
        {
            **clip,
            "start": round(clip["start"] * scale, 3),
            "end": round(clip["end"] * scale, 3),
        }
        for clip in clips
    ]


def voice_ratio(path: Path) -> tuple[float, float]:
    """语音占比 与 最长静音段，作录音质量参考（笔记本内置麦常 <15% 不可用）。"""
    dur = dur_of(path)
    r = run(["ffmpeg", "-i", str(path), "-af",
             f"silencedetect=noise={SILENCE_DB}dB:d=0.30", "-f", "null", "-"])
    gaps = re.findall(r"silence_start: ([0-9.]+)\n.*?silence_end: ([0-9.]+)", r.stderr, re.DOTALL)
    sil = sum(float(e) - float(s) for s, e in gaps)
    longest = max((float(e) - float(s) for s, e in gaps), default=0.0)
    return (1.0 - sil / dur if dur > 0 else 0.0), longest


def band_rms(path: Path, center: float, q: float) -> float:
    """测某频段能量（RMS dBFS）：bandpass 后 astats 取整体 RMS。"""
    r = run(["ffmpeg", "-i", str(path),
             "-af", (f"bandpass=f={center}:width_type=q:width={q},"
                     "astats=measure_overall=RMS_level:metadata=1"),
             "-f", "null", "-"])
    m = re.search(r"RMS level dB\s*:\s*(-?[0-9.]+)", r.stderr)
    return float(m.group(1)) if m else -99.0


def overall_rms(path: Path) -> float:
    """测整段整体 RMS（dBFS），代表能量。"""
    r = run(["ffmpeg", "-i", str(path),
             "-af", "astats=measure_overall=RMS_level:metadata=1", "-f", "null", "-"])
    m = re.search(r"RMS level dB\s*:\s*(-?[0-9.]+)", r.stderr)
    return float(m.group(1)) if m else -99.0


def analyze_spectrum(path: Path) -> dict:
    """返回每段频谱能量分布 {band: rms_db} 与整体能量。"""
    spec = {name: band_rms(path, c, q) for name, c, q in FREQ_BANDS}
    spec["overall"] = overall_rms(path)
    return spec


def spectrum_flatness(spec: dict) -> float:
    """频谱均衡度：各频段相对能量（减掉整体偏移后）的方差。越小越「集中/均衡」。"""
    vals = [spec[name] for name, _, _ in FREQ_BANDS]
    mean = sum(vals) / len(vals)
    return math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))


def choose_anchor(specs: dict[str, dict]) -> str:
    """选最佳锚段：频谱最均衡(flatness 最小) 且 整体能量不过弱(< -28dB 视为发虚弃选)。"""
    candidates = [(name, s) for name, s in specs.items() if s["overall"] > -28.0]
    if not candidates:
        candidates = list(specs.items())
    best, _ = min(candidates, key=lambda ns: spectrum_flatness(ns[1]))
    return best


def compensation_gains(spec, anchor_spec: dict) -> dict[str, float]:
    """每段相对锚段，各频段需补偿的增益(dB)。差>阈值才补，|增益|<=上限。"""
    gains: dict[str, float] = {}
    for name, _, _ in FREQ_BANDS:
        diff = anchor_spec[name] - spec[name]  # 锚段比本段高 -> 本段该补
        if abs(diff) > EQ_THRESHOLD_DB:
            gains[name] = max(-EQ_MAX_GAIN_DB, min(EQ_MAX_GAIN_DB, diff))
        else:
            gains[name] = 0.0
    return gains


def build_eq_chain(gains: dict[str, float]) -> str:
    """把频段补偿增益转成 equalizer 滤镜链（peaking EQ，只在需要补的频段生效）。"""
    parts = []
    for name, center, q in FREQ_BANDS:
        g = round(gains[name], 1)
        if g == 0.0:
            continue
        parts.append(f"equalizer=f={center}:width_type=q:width={q}:g={g}")
    return ",".join(parts)


def consistency_report(specs: dict[str, dict], anchor: str,
                       gains: dict[str, dict[str, float]]) -> str:
    """打印一致性体检报告。"""
    lines = []
    lines.append(f"一致性锚段: {anchor or "(跳过)"}（频谱最均衡）")
    lines.append("频段能量(dBFS)  |  低160 | 中低500 | 中高2k | 高5.6k | 整体")
    for name, s in specs.items():
        g = gains[name]
        active = {b: round(g[b], 1) for b, _, _ in FREQ_BANDS if g[b] != 0.0}
        lines.append(
            f"  {name:3s}      |  {s["low"]:5.1f} | {s["mid_low"]:6.1f} | "
            f"{s["mid_high"]:6.1f} | {s["high"]:5.1f} | {s["overall"]:5.1f}   "
            + (f"补偿{active}" if active else "无需")
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir", help="shipinhao 工作目录（含 tts.txt / recordings/）")
    ap.add_argument("--rec-dir", default="recordings", help="原始录音目录（相对 workdir）")
    ap.add_argument("--out-dir", default="tts", help="修音输出目录（相对 workdir）")
    ap.add_argument("--filter", default=DEFAULT_FILTER, help="修音滤镜链")
    ap.add_argument("--no-consistency", action="store_true",
                    help="跳过段间一致性补偿（默认开启）")
    ap.add_argument("--consistency-report", action="store_true",
                    help="只做波形/频谱分析并打印报告，不改音频产物")
    ap.add_argument("--quiet", action="store_true", help="只打印 VOICE_DUR 行")
    args = ap.parse_args()

    wd = Path(args.workdir)
    rec_dir = wd / args.rec_dir
    out_dir = wd / args.out_dir
    tts_txt = wd / "tts.txt"
    if not tts_txt.exists():
        sys.exit(f"缺配音稿 {tts_txt}")
    lines = [ln for ln in tts_txt.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        sys.exit("tts.txt 至少需要 1 个非空段落")
    out_dir.mkdir(parents=True, exist_ok=True)

    # --consistency-report：只读模式，分析现有 tts/sN.wav，打印报告后退出（不改任何产物）
    if args.consistency_report:
        specs_r: dict[str, dict] = {}
        for i in range(1, len(lines) + 1):
            seg = f"S{i}"
            clean = out_dir / f"s{i}.wav"
            if not clean.exists():
                sys.exit(f"只读报告需先跑过完整流程（缺 {clean}）")
            specs_r[seg] = analyze_spectrum(clean)
        anchor_r = choose_anchor(specs_r)
        gains_r = {seg: compensation_gains(s, specs_r[anchor_r]) for seg, s in specs_r.items()}
        print(consistency_report(specs_r, anchor_r, gains_r))
        return

    # 阶段 1+2: 修音 + 频谱分析（先分析，选锚段后统一补偿）
    # Web studio writes trim/sN.wav immediately after each take.  Using it here
    # keeps final tts audio and pauses.json on the same, lead/tail-free timeline
    # that the author reviewed in the browser.  CLI-only users retain the raw
    # recording fallback until they run trim_silence.py.
    clean_paths: dict[str, Path] = {}
    source_paths: dict[str, Path] = {}
    specs: dict[str, dict] = {}
    ratio_info: dict[str, tuple[float, float]] = {}
    for i in range(1, len(lines) + 1):
        seg = f"S{i}"
        raw = rec_dir / f"s{i}.wav"
        if not raw.exists():
            sys.exit(f"缺录音 {raw}（请先录好第 {i} 段再跑本脚本）")
        trimmed = wd / "trim" / f"s{i}.wav"
        source = trimmed if trimmed.exists() and trimmed.stat().st_mtime >= raw.stat().st_mtime else raw
        source_paths[seg] = source
        clean = out_dir / f"s{i}.wav"
        clean_paths[seg] = clean
        # 修音
        run(["ffmpeg", "-y", "-v", "error", "-i", str(source),
             "-af", args.filter, "-ar", "44100", "-ac", "2", str(clean)])
        # 频谱分析基于修音后（对干净信号判断频段，避免噪声干扰）
        specs[seg] = analyze_spectrum(clean)
        ratio_info[seg] = voice_ratio(source)  # 与最终 tts 时间轴保持一致

    # 一致性补偿：选锚段 -> 每段算增益 -> 重新生成 tts/sN.wav
    gains: dict[str, dict[str, float]] = {}
    anchor = ""
    if not args.no_consistency:
        anchor = choose_anchor(specs)
        for seg, s in specs.items():
            gains[seg] = compensation_gains(s, specs[anchor])
        for seg, clean in clean_paths.items():
            g = gains[seg]
            if any(g.values()):
                eq = build_eq_chain(g)
                tmp = clean.with_suffix(".eq.wav")
                run(["ffmpeg", "-y", "-v", "error", "-i", str(clean),
                     "-af", eq, "-ar", "44100", "-ac", "2", str(tmp)])
                tmp.replace(clean)
    else:
        for seg in clean_paths:
            gains[seg] = {b: 0.0 for b, _, _ in FREQ_BANDS}

    # 一致性报告
    if not args.quiet or args.consistency_report:
        print(consistency_report(specs, anchor or "(跳过)", gains))
        print()

    # 阶段 3+4: 时长 + 停顿（时长基于最终 tts/sN.wav；停顿从未 loudnorm 的
    # trim/raw 源取，避免修音把真实静音填满，同时保证坐标与最终音频一致）
    pauses: dict[str, list[float]] = {}
    recorded_manual = load_manual_boundaries(wd)
    final_manual: dict[str, dict] = {}
    durs: list[float] = []
    for i in range(1, len(lines) + 1):
        seg = f"S{i}"
        clean = clean_paths[seg]
        d = dur_of(clean)
        durs.append(round(d, 2))
        ratio, longest = ratio_info[seg]
        manual_clips = prepared_manual_clips(
            recorded_manual, seg, lines[i - 1], dur_of(source_paths[seg]), d,
        )
        st = [clip["start"] for clip in manual_clips[1:]] if manual_clips else silence_analysis(source_paths[seg])
        pauses[seg] = st
        if manual_clips:
            final_manual[seg] = {"source_duration": round(d, 3), "clips": manual_clips}
        if not args.quiet:
            mode = "人工边界" if manual_clips else "自动停顿"
            print(f"{seg}: {d:5.2f}s 语音占比 {ratio*100:.0f}% 最长静音 {longest:.2f}s "
                  f"句停顿 {len(st)} 处 {st}（{mode}）")

    pauses_path = wd / "tts" / "pauses.json"
    pauses_path.write_text(json.dumps(pauses, ensure_ascii=False), encoding="utf-8")
    final_manual_path = wd / "tts" / "manual-boundaries.json"
    if final_manual:
        final_manual_path.write_text(
            json.dumps({"version": 1, "segments": final_manual}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        final_manual_path.unlink(missing_ok=True)
    (wd / "tts" / "consistency.json").write_text(
        json.dumps({"anchor": anchor, "specs": specs, "gains": gains},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"pauses: {pauses_path.name} 已写入（build 脚本字幕对齐用）")
    print("consistency: tts/consistency.json 已写入（体检报告存档）")
    print("VOICE_DUR = {" + ", ".join(f"\"S{i}\": {d}" for i, d in enumerate(durs, 1)) + "}")
    if not args.quiet:
        print("完成 -> " + str(out_dir) + "/s1..sN.wav")


if __name__ == "__main__":
    main()
