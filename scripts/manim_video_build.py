#!/usr/bin/env python3
"""Manim 文章视频 → 视频号成品一键构建（mux 配音 + concat + 字幕 + 烧录）。

约定工作目录（shipinhao/，见 .agents/skills/manim-article-video/SKILL.md）：
  scenes.py          Manim 场景（S1..SN，竖屏 config + pad_to_voice）
  tts.txt            配音稿（每段一行，与 tts/sN.wav 一一对应，是字幕基准）
  tts/s1.wav..sN.wav 逐段配音（xiaomi_mimo_tts.py 生成）
  media/...          Manim 渲染输出（先跑 manim render -qm）

用法：
  python3 scripts/manim_video_build.py content/<日期>-<主题>/shipinhao \
      [--speed 1.0] [--tail 0.1] [--out 成品.mp4]

说明：
  - 段间无缝衔接靠 --tail（默认 0.1s）；用户嫌停顿改小、嫌太赶改大
  - 语速用 ffmpeg atempo 后处理（无需重生成 TTS / 重渲染 Manim）
  - 字幕：拆长句（>40 字按标点）+ 段内按字数比例分配时间
  - ASS 时间戳是【厘秒】h:mm:ss.cc（不是毫秒！写错会被放大 10 倍导致字幕错位）
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

FONTS_DIR = "/usr/share/fonts/opentype/noto"
ASS_STYLE = (
    "Style: Default,Noto Sans CJK SC,75,&H0000FFFF,&H0000FFFF,&H00000000,"
    "&H64000000,0,0,0,0,100,100,0,0,1,3,1,2,60,60,210,1"
)  # 1080×1920 竖屏：黄色字、MarginV=210（品牌栏上方；safe_margin 缩放后≈236px）


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kw)


def dur_of(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)], text=True)
    return float(out.strip())


def split_long(text: str, limit: int = 26) -> list[str]:
    """>26 字按句号拆；单句仍超限按逗号拆；仍超限 26 字一刀（75 号字一行约 13 字，防字幕折 3 行）。"""
    if len(text) <= limit:
        return [text]
    parts = [p for p in re.split(r"(?<=[。！？；])", text) if p.strip()]
    out: list[str] = []
    for p in parts:
        if len(p) > limit:
            subs = [s for s in re.split(r"(?<=[，、：])", p) if s.strip()]
            for s in subs:
                if len(s) > limit:
                    out.extend(s[i:i + limit] for i in range(0, len(s), limit))
                else:
                    out.append(s)
        else:
            out.append(p)
    return out


# MiniMax 拟声标签（speech-2.8 系列 22 个）——字幕剥离：防止标签上屏，且避免标签字符污染字幕时长分配
_TAG_RE = __import__("re").compile(
    r"\((?:laughs|chuckle|coughs|clear-throat|groans|breath|pant|inhale|exhale|gasps|sniffs|"
    r"sighs|snorts|burps|lip-smacking|humming|hissing|emm|whistles|sneezes|crying|applause)\)\s?"
)


def strip_tts_tags(s: str) -> str:
    return _TAG_RE.sub("", s).replace("  ", " ").strip()


def srt_ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ass_ts(sec: float) -> str:
    """ASS 时间 = 厘秒（h:mm:ss.cc）。"""
    cs = int(round(sec * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def parse_srt_ts(s: str) -> float:
    h, m, rest = s.split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def build_srt(segments: dict[str, str], seg_dur: dict[str, float], tail: float) -> list[tuple[float, float, str]]:
    """段内字幕按字数比例分布，段间连续。返回 [(start, end, text)]。"""
    entries: list[tuple[float, float, str]] = []
    t = 0.0
    for seg, text in segments.items():
        text = strip_tts_tags(text)  # 双保险：字幕文本永不含拟声标签
        vd = seg_dur[seg]
        ad = vd - tail  # 配音实际占用
        start = t + 0.25
        chunks = split_long(text)
        total = sum(len(c) for c in chunks)
        acc = 0.0
        for c in chunks:
            w = len(c) / total
            a = start + acc * ad
            acc += w
            b = start + acc * ad
            entries.append((a, b, c))
        t += vd
    return entries


PUNCT = "，。！？、；：\"\"''…—·"


def typewriter_events(entries):
    """打字机效果：每条字幕拆成前缀事件（第 i 个事件显示前 i 组文本，字逐个出现）。
    标点并入前字（不单独成事件），空格只占时间不显示。"""
    out = []
    for a, b, txt in entries:
        groups = []  # [(text, weight)]
        for ch in txt:
            if ch in PUNCT and groups:
                groups[-1][0] += ch
                groups[-1][1] += 1
            elif ch == " ":
                if groups:
                    groups[-1][1] += 1
            else:
                groups.append([ch, 1])
        total = sum(w for _, w in groups)
        if total == 0:
            continue
        t = a
        prefix = ""
        for text, w in groups:
            prefix += text
            dur = (b - a) * w / total
            out.append((t, t + dur, prefix))
            t += dur
    return out


def write_srt(entries, out: Path):
    with open(out, "w", encoding="utf-8") as f:
        for n, (a, b, txt) in enumerate(entries, 1):
            f.write(f"{n}\n{srt_ts(a)} --> {srt_ts(b)}\n{txt}\n\n")


def write_ass(entries, out: Path, typewriter: bool = False, fade: bool = True):
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{ASS_STYLE}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    if typewriter:
        entries = typewriter_events(entries)
        fade = False  # 打字机已逐字出现，不再叠加淡入
    events = [
        f"Dialogue: 0,{ass_ts(a)},{ass_ts(b)},Default,,0,0,0,,{'{\\fad(150,80)}' if fade else ''}{txt.replace(chr(10), '\\N')}"
        for a, b, txt in entries
    ]
    with open(out, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")


def self_test() -> None:
    assert strip_tts_tags("(breath) 为什么 loss 一直抖？(inhale) 但别慌。") == "为什么 loss 一直抖？但别慌。"
    assert strip_tts_tags("(sighs)(breath) 连写标签") == "连写标签"
    assert strip_tts_tags("无标签文本") == "无标签文本"
    entries = build_srt({"S1": "(breath) 一二三四五六七八九十"}, {"S1": 10.0}, 0.1)
    assert entries[0][2] == "一二三四五六七八九十"
    tw = typewriter_events([(0.0, 1.0, "你好，世界")])
    assert tw[0][2] == "你" and tw[-1][2] == "你好，世界"  # 前缀累积，标点并入前字
    assert tw[-1][1] == 1.0  # 末事件结束于原字幕结束
    print("self-test passed")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir", nargs="?", help="shipinhao 工作目录（含 scenes.py / tts.txt / tts/）")
    ap.add_argument("--speed", type=float, default=1.0, help="配音语速（atempo 后处理，默认 1.0 原速）")
    ap.add_argument("--tail", type=float, default=0.1, help="段尾缓冲秒数（默认 0.1，段间无缝）")
    ap.add_argument("--out", default="成品.mp4", help="输出文件名")
    ap.add_argument("--video-dir", default=None,
                    help="Manim 渲染输出目录（默认自动探测 media/videos/scenes/ 下含 S1.mp4 的目录）")
    ap.add_argument("--safe-margin", type=float, default=0.08,
                    help="安全边距：内容缩放比例（默认 0.08 = 四周留 8% 边距，防手机圆角/播放器 UI 裁边）")
    ap.add_argument("--typewriter", action="store_true",
                    help="逐字打字机字幕（默认关闭：整行一次出现 + 150ms 快速淡入）")
    ap.add_argument("--no-typewriter", action="store_true",
                    help="旧参数兼容：默认已是整行字幕，此参数不再生效")
    ap.add_argument("--self-test", action="store_true", help="运行内置自检后退出")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.workdir:
        ap.error("缺少 workdir 参数")

    wd = Path(args.workdir)
    tts_dir = wd / "tts"
    tts_txt = wd / "tts.txt"

    # 1) 段清单：tts.txt 每行一段（字幕基准），wav 必须一一对应
    if not tts_txt.exists():
        sys.exit(f"缺配音稿 {tts_txt}（每段一行，与 tts/sN.wav 对应）")
    voices = [strip_tts_tags(ln) for ln in tts_txt.read_text(encoding="utf-8").splitlines() if ln.strip()]
    n = len(voices)
    print(f"共 {n} 段配音稿")

    # 2) 探测 Manim 渲染目录
    if args.video_dir:
        vdir = Path(args.video_dir)
    else:
        cands = sorted((wd / "media/videos/scenes").glob("*/")) if (wd / "media/videos/scenes").exists() else []
        vdir = next((c for c in reversed(cands) if (c / "S1.mp4").exists()), None)
        if vdir is None:
            sys.exit("未找到 Manim 渲染输出（media/videos/scenes/*/S1.mp4），先跑 manim render")
    print(f"Manim 视频: {vdir}")

    # 3) 逐段：语速处理 + 44.1k 立体声 + mux + 截断到 配音+tail
    segments = [f"S{i}" for i in range(1, n + 1)]
    seg_dur: dict[str, float] = {}
    for i, seg in enumerate(segments, 1):
        wav = tts_dir / f"s{i}.wav"
        if not wav.exists():
            sys.exit(f"缺配音 {wav}")
        a_src = tts_dir / "speed" / f"s{i}.wav"
        a_src.parent.mkdir(exist_ok=True)
        # 统一走重采样路径：44.1kHz 立体声（24kHz mono 提升一档，speed=1.0 时 atempo 无副作用）
        run(["ffmpeg", "-y", "-v", "error", "-i", str(wav),
             "-filter:a", f"atempo={args.speed}", "-ar", "44100", "-ac", "2", str(a_src)])
        ad = dur_of(a_src)
        vd = ad + args.tail
        seg_dur[seg] = vd
        run(["ffmpeg", "-y", "-v", "error", "-i", str(vdir / f"{seg}.mp4"), "-i", str(a_src),
             "-filter_complex", "[1:a]apad[a]", "-map", "0:v", "-map", "[a]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(vd),
             str(wd / f"build_{seg}.mp4")])
        print(f"{seg}: 配音 {ad:.2f}s → 视频 {vd:.2f}s")

    # 4) concat
    concat_txt = wd / "concat.txt"
    concat_txt.write_text("".join(f"file 'build_{s}.mp4'\n" for s in segments), encoding="utf-8")
    full = wd / "build_full.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(concat_txt), "-c", "copy", str(full)])

    # 5) 字幕 SRT + ASS
    voices_map = {seg: v for seg, v in zip(segments, voices)}
    entries = build_srt(voices_map, seg_dur, args.tail)
    srt_path = wd / "subs.srt"
    ass_path = wd / "subs.ass"
    write_srt(entries, srt_path)
    write_ass(entries, ass_path, typewriter=args.typewriter)
    print(f"字幕: {srt_path.name} / {ass_path.name} ({len(entries)} 条)")

    # 6) 烧录
    out = wd / args.out
    run(["ffmpeg", "-y", "-v", "error", "-i", str(full),
         "-vf", f"ass={ass_path}:fontsdir={FONTS_DIR}",
         "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-c:a", "copy",
         str(out)])

    # 7) 安全边距：内容缩小居中，四周留背景色（防手机圆角/UI 遮挡边缘内容）
    if args.safe_margin > 0:
        W, H = 1080, 1920
        scale = 1.0 - args.safe_margin
        sw = int(W * scale / 2) * 2   # 偶数宽高，libx264 要求
        sh = int(H * scale / 2) * 2
        safe_out = wd / f"{args.out}.safe.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(out),
             "-vf", f"scale={sw}:{sh}:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x16213E",
             "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-c:a", "copy",
             str(safe_out)])
        safe_out.replace(out)
        print(f"安全边距: 内容 {scale:.0%} 居中，四周各留 {int(W * args.safe_margin / 2)}px")
    total = dur_of(out)
    print(f"成品: {out}（{total:.1f}s）")

    # 7) 验证：最长静音段（应 < 1s 左右，段间无空白）
    sd = subprocess.run(
        ["ffmpeg", "-i", str(out), "-af", "silencedetect=noise=-35dB:d=0.5", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    gaps = re.findall(r"silence_start: ([\d.]+)\n.*?silence_end: ([\d.]+)", sd, re.S)
    longest = max((float(e) - float(s) for s, e in gaps), default=0)
    print(f"验证: 最长静音段 {longest:.2f}s（段间缓冲 {args.tail}s，句子停顿属正常）")


if __name__ == "__main__":
    main()
