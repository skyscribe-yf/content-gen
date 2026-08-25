#!/usr/bin/env python3
"""Manim 文章视频 → 视频号成品一键构建（mux 配音 + concat + 字幕 + 烧录）。

约定工作目录（shipinhao/，见 .agents/skills/manim-article-video/SKILL.md）：
  scenes.py          Manim 场景（S1..SN，竖屏 config + pad_to_voice）
  tts.txt            配音稿（每段一行，与 tts/sN.wav 一一对应，是字幕基准）
  tts/s1.wav..sN.wav 逐段配音（TTS 模式 minimax_tts.py 生成；口播模式 voice_process.py 修音）
  tts/pauses.json    口播模式停顿边界（voice_process.py 生成，字幕停顿对齐兜底用）
  tts/sentence-boundaries.json
                     口播/TTS 最终句级时间戳（每条 clip 的 start/end 与语音逐句对应，字幕优先使用）
  media/...          Manim 渲染输出（先跑 manim render -qm）

用法：
  python3 scripts/manim_video_build.py content/<日期>-<主题>/shipinhao \
      [--speed 1.0] [--tail 0.1] [--out 成品.mp4]

说明：
  - 段间无缝衔接靠 --tail（默认 0.1s）；用户嫌停顿改小、嫌太赶改大
  - 语速用 ffmpeg atempo 后处理（无需重生成 TTS / 重渲染 Manim）
  - 字幕：优先 tts/sentence-boundaries.json 的逐句 start/end；没有时才退回口播停顿驱动切分
  - ASS 时间戳是【厘秒】h:mm:ss.cc（不是毫秒！写错会被放大 10 倍导致字幕错位）
"""
from __future__ import annotations

import argparse
import json
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


def _hard_cut_text(s: str, limit: int = 26) -> list[str]:
    """超限硬切，但不在英文/数字串内部切断（DeepSeekMath、77.9%、2024 等）。
    切点优先落在英文/数字串之前，保证词串完整。"""
    if len(s) <= limit:
        return [s]
    limit = min(limit, len(s) - 1)
    cut = limit
    for i in range(limit, max(limit - 12, 1) - 1, -1):
        a, b = s[i - 1], s[i]
        a_word = a.isascii() and (a.isalnum() or a in ".%+-/")
        b_word = b.isascii() and (b.isalnum() or b in ".%+-/")
        if not (a_word and b_word):
            cut = i
            break
    # 中文长句刚好超过上限时，按上限切可能留下 3～7 字的闪现尾条。
    # 英文/数字混排仍保留原来的词边界策略（例如 AIME 百分比字幕）。
    ascii_ratio = sum(1 for ch in s if ch.isascii()) / len(s)
    if len(s) - cut < 8 and ascii_ratio < 0.35:
        target = max(1, len(s) // 2)
        cut = target
        for i in range(target, max(target - 12, 1) - 1, -1):
            a, b = s[i - 1], s[i]
            a_word = a.isascii() and (a.isalnum() or a in ".%+-/")
            b_word = b.isascii() and (b.isalnum() or b in ".%+-/")
            if not (a_word and b_word):
                cut = i
                break
    return [s[:cut]] + _hard_cut_text(s[cut:], limit)


def split_long(text: str, limit: int = 26) -> list[str]:
    """>26 字按句号拆；单句仍超限按逗号拆；仍超限按词边界切（75 号字一行约 13 字，防字幕折 3 行）。
    英文/数字串（DeepSeekMath、77.9%、2024）不拆断；纯标点段并入前一条（2026-08-15 B4 修复）。"""
    if len(text) <= limit:
        return [text]
    parts = [p for p in re.split(r"(?<=[。！？；])", text) if p.strip()]
    out: list[str] = []
    for p in parts:
        if len(p) > limit:
            subs = [s for s in re.split(r"(?<=[，、：])", p) if s.strip()]
            for s in subs:
                if len(s) > limit:
                    out.extend(_hard_cut_text(s, limit))
                else:
                    out.append(s)
        else:
            out.append(p)
    out = [p.strip() for p in out if p.strip()]
    if len(out) > 1:
        merged: list[str] = []
        for p in out:
            # 纯标点段，或 ≤8 字且不以句号结尾的短段（"而是："、"等显存、"等连接碎片）
            # → 并入前一条，避免 0.4s 级闪字幕（2026-08-18 修复）
            if merged and (all(ch in "。！？；，、：…—「」" for ch in p)
                           or (len(p) <= 8 and not p.endswith(("。", "！", "？", "；")))):
                if len(merged[-1]) + len(p) <= limit:
                    merged[-1] += p
                else:
                    # 标点并入会让前条超限：从尾部分出「尾词+标点」成新条，避免孤立标点
                    prev = merged[-1]
                    cut = -1
                    for i in range(len(prev) - 1, -1, -1):
                        if prev[i] in " ，。！？；、：—" and len(prev) - i - 1 + len(p) <= limit:
                            cut = i
                            break
                    if cut < 0:
                        cut = max(0, len(prev) - (limit - len(p)))
                    merged[-1] = prev[:cut + 1].rstrip()
                    merged.append((prev[cut + 1:] + p).lstrip())
            else:
                merged.append(p)
        out = merged
    return out


# MiniMax 拟声标签（speech-2.8 系列 22 个）——字幕剥离：防止标签上屏，且避免标签字符污染字幕时长分配
_TAG_RE = __import__("re").compile(
    r"\((?:laughs|chuckle|coughs|clear-throat|groans|breath|pant|inhale|exhale|gasps|sniffs|"
    r"sighs|snorts|burps|lip-smacking|humming|hissing|emm|whistles|sneezes|crying|applause)\)\s?"
    r"|<#\d+(?:\.\d+)?#>\s?"
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


def _merge_split_word_slots(
    slots: list[tuple[float, float, str]],
) -> list[tuple[float, float, str]]:
    """合并 ASR 在词中间切开的相邻字幕槽。

    逐句边界来自录音标注，但 ASR 仍可能把 ``SFT baseline`` 切成
    ``SFT ba`` + ``seline``，或把「数学」「变成」切成单字。字幕不能
    在英文词中间换屏，也不应让单字字幕闪现。
    """
    out: list[tuple[float, float, str]] = []
    for begin, end, text in slots:
        if out:
            prev_begin, prev_end, prev_text = out[-1]
            contiguous = abs(begin - prev_end) <= 0.02
            prev_last = prev_text[-1:] if prev_text else ""
            cur_first = text[:1] if text else ""
            english_word = (
                prev_last.isascii() and prev_last.isalpha()
                and cur_first.isascii() and cur_first.isalpha()
            )
            single_cjk = (
                len(prev_text.strip()) <= 2 and len(text.strip()) == 1
                and all("\u4e00" <= ch <= "\u9fff" for ch in (prev_text.strip() + text.strip()))
            )
            if contiguous and (english_word or single_cjk):
                out[-1] = (prev_begin, end, prev_text + text)
                continue
        out.append((begin, end, text))
    return out


def manual_alignment_slots(
    manual_alignment: dict | None,
    seg: str,
    text: str,
    audio_duration: float,
) -> list[tuple[float, float, str]]:
    """Return Web-confirmed slots, scaled to the final rendered audio duration.

    A slot may deliberately include multiple punctuation blocks.  Long on-screen
    text still splits within that *same* confirmed time span, so display limits
    never alter the author-confirmed audio/text correspondence.
    """
    if not isinstance(manual_alignment, dict):
        return []
    segments = manual_alignment.get("segments")
    if not isinstance(segments, dict):
        return []
    candidate = segments.get(seg)
    if not isinstance(candidate, dict) or not isinstance(candidate.get("clips"), list):
        return []
    try:
        source_duration = float(candidate["source_duration"])
    except (KeyError, TypeError, ValueError):
        return []
    if source_duration <= 0 or audio_duration <= 0:
        return []

    slots: list[tuple[float, float, str]] = []
    previous_end = 0.0
    for item in candidate["clips"]:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            return []
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            return []
        if not 0.0 <= start < end <= source_duration + 0.01 or start < previous_end - 0.01:
            return []
        slots.append((start, end, strip_tts_tags(item["text"])))
        previous_end = end
    if not slots or "".join(slot[2] for slot in slots) != text:
        return []
    scale = audio_duration / source_duration
    scaled = [(start * scale, min(audio_duration, end * scale), slot_text) for start, end, slot_text in slots]
    return _merge_split_word_slots(scaled)


def sentence_boundary_alignment(data: dict | None) -> dict | None:
    """把 tts/sentence-boundaries.json 规整成 manual_alignment_slots 接受的格式。

    sentence-boundaries.json 的 segments 是列表 [{id, duration, clips:[{start,end,text}]}]；
    这里转成 {"segments": {"S1": {"source_duration":..., "clips": [...]}}}，
    使 build_srt 可以复用同一条「逐句时间戳」路径。
    """
    if not isinstance(data, dict) or not isinstance(data.get("segments"), list):
        return None
    out: dict[str, dict] = {}
    for seg in data["segments"]:
        if not isinstance(seg, dict):
            return None
        try:
            seg_id = str(seg["id"]).upper()
            duration = float(seg["duration"])
            clips = seg["clips"]
        except (KeyError, TypeError, ValueError):
            return None
        if not isinstance(clips, list):
            return None
        out[seg_id] = {"source_duration": duration, "clips": clips}
    return {"segments": out}


def _merge_pure_punct_entries(entries: list[tuple[float, float, str]]) -> list[tuple[float, float, str]]:
    """纯标点字幕（孤立「。」等）并入前一条：语音把「反思。」拆成 clips「反思」+「。」时，
    sentence-boundaries 会产出 0.12s 的纯标点碎片，不能单独上屏（2026-08-16 GRPO 反馈）。"""
    out: list[tuple[float, float, str]] = []
    for begin, end, text in entries:
        stripped = text.strip()
        if out and stripped and all(ch in "。！？；，、：…—「」" for ch in stripped):
            prev_begin, _, prev_text = out[-1]
            out[-1] = (prev_begin, end, prev_text + stripped)
        else:
            out.append((begin, end, text))
    return out


def validate_sentence_ts(sentence_ts: dict, voices_map: dict[str, str],
                         pauses: dict | None = None) -> None:
    """加固：SB 与配音文本一致性 + 边界单调性 + pauses 漂移告警。

    2026-08-18 事故根因：sentence-boundaries.json 直接拿 pauses 当字幕边界，
    静音阈值太粗导致 S8 中部漂 ~2s，无校验直接进成品。此校验 fail-fast。
    """
    problems: list[str] = []
    for seg, info in sentence_ts["segments"].items():
        text = strip_tts_tags(voices_map.get(seg, ""))
        clips = info["clips"]
        joined = "".join(c["text"] for c in clips)
        if text.replace(" ", "") != joined.replace(" ", ""):
            problems.append(
                f"{seg}: SB 文本与配音不一致（SB {len(joined)} 字 vs 配音 {len(text)} 字），"
                "SB 已过期，禁止使用")
        prev_end = 0.0
        for c in clips:
            if c["start"] < prev_end - 1e-6 or c["end"] < c["start"]:
                problems.append(f"{seg} {c['id']}: 边界乱序 {c['start']:.2f}-{c['end']:.2f}")
            prev_end = c["end"]
        if clips and clips[-1]["end"] > info["source_duration"] + 0.05:
            problems.append(
                f"{seg}: 末边界 {clips[-1]['end']:.2f}s 超段时长 {info['source_duration']:.2f}s")
    if problems:
        raise SystemExit("✗ sentence-boundaries.json 校验失败：\n  " + "\n  ".join(problems))
    if pauses:
        for seg, info in sentence_ts["segments"].items():
            p = pauses.get(seg)
            if not p:
                continue
            for c in info["clips"]:
                if c["start"] < 0.05:  # 第一句起点固定 0.0，非漂移信号
                    continue
                if min(abs(c["start"] - x) for x in p) > 0.4:
                    print(f"⚠️ {seg}: SB 边界 {c['start']:.2f}s 与 pauses 漂移 >0.4s，"
                          "请人工复核（pauses 静音阈值可能过粗）")
                    break


def build_srt(segments: dict[str, str], seg_dur: dict[str, float], tail: float,
              subtitle_ts: list | None = None,
              pauses: dict[str, list[float]] | None = None,
              manual_alignment: dict | None = None,
              sentence_ts: dict | None = None) -> list[tuple[float, float, str]]:
    """段内字幕按字数比例分布，段间连续。返回 [(start, end, text)]。

    时间戳优先级（越高越贴合真实语音节奏）:
      1. manual_alignment（Web 人工确认）：作者确认的音频/标点块对应关系
      2. sentence_ts（tts/sentence-boundaries.json）：逐句 start/end 与语音严格对应
      3. pauses（口播模式，tts/pauses.json）：真人停顿边界驱动字幕块
      4. subtitle_ts（TTS 模式，full.subtitle.json）：官方句子级时间戳对齐
      5. 无时间戳：纯字数比例分布
    """
    entries: list[tuple[float, float, str]] = []
    t = 0.0      # 累计视频时间
    audio_t = 0.0  # 累计配音时间（full audio 时间轴）
    seen_sents: set[float] = set()  # 已归属的句子 time_begin（跨段句去重，2026-08-18）
    for seg, text in segments.items():
        text = strip_tts_tags(text)  # 双保险：字幕文本永不含拟声标签
        vd = seg_dur[seg]
        ad = vd - tail  # 配音实际占用

        manual_slots = manual_alignment_slots(manual_alignment, seg, text, ad)
        if not manual_slots:
            manual_slots = manual_alignment_slots(sentence_ts, seg, text, ad)
        if manual_slots:
            for begin, end, slot_text in manual_slots:
                chunks = split_long(slot_text)
                total = sum(len(chunk) for chunk in chunks) or 1
                progress = 0.0
                for chunk in chunks:
                    chunk_begin = t + begin + progress * (end - begin)
                    progress += len(chunk) / total
                    chunk_end = t + begin + progress * (end - begin)
                    if chunk_end > chunk_begin and chunk:
                        entries.append((chunk_begin, chunk_end, chunk))
            t += vd
            audio_t += ad
            continue

        if pauses is not None and pauses.get(seg):
            # 口播模式（2026-08-17 重写）：停顿驱动切分——每个真实停顿都是字幕边界。
            # 旧算法「先按标点切文本，再均匀采样停顿点」会跳过 28% 的真实停顿
            # （RLHF 实测 96 个停顿跳过 27 个），导致字幕跨过说话者的自然停顿，
            # 观众听到停顿但字幕还在 → 不同步（00:44 是典型案例）。
            #
            # 新算法：先取所有停顿作为时间槽，再把文本按字符比例分配到各槽，
            # 在自然标点处对齐——0 个停顿被跳过。
            def split_sent(s):
                if len(s) <= 26:
                    return [s]
                sub = [p for p in re.split(r"(?<=[。！？])", s) if p.strip()]
                if len(sub) > 1:
                    out = []
                    for x in sub:
                        out.extend(split_sent(x))
                    return out
                parts = [p for p in re.split(r"(?<=[，、：])", s) if p.strip()]
                if len(parts) <= 1:
                    # 无标点可拆：26 字附近找词边界硬切（防无限递归 + 不拆断英文/数字串）
                    def hard_cut(t, limit=26):
                        if len(t) <= limit:
                            return [t]
                        # 英文/数字占比高（如 AIME 2024 正确率从 15.6% 冲到 77.9%，）显示宽度窄，
                        # 放宽到 30 字符（折 2 行安全），避免切出 77.9%， 这类过短碎片（2026-08-16）
                        ascii_ratio = sum(1 for c in t if c.isascii()) / len(t)
                        if ascii_ratio > 0.35:
                            limit = 30
                        limit = min(limit, len(t) - 1)  # 防越界（放宽后 limit 可能 > len(t)-1）
                        cut = limit
                        for i in range(limit, max(limit - 10, 1) - 1, -1):
                            a, b = t[i - 1], t[i]
                            a_word = a.isascii() and (a.isalnum() or a in ".%+-/")
                            b_word = b.isascii() and (b.isalnum() or b in ".%+-/")
                            if not (a_word and b_word):
                                cut = i
                                break
                        return [t[:cut]] + hard_cut(t[cut:], limit)
                    return hard_cut(s)
                out = []
                cur = ""
                for p in parts:
                    if len(cur) + len(p) <= 26:
                        cur += p
                    else:
                        if cur:
                            out.append(cur)
                        if len(p) > 26:
                            out.extend(split_sent(p))
                            cur = ""  # 修复：append 后必须清空，否则下段重复入列（2026-08-16 字幕重复）
                        else:
                            cur = p
                if cur:
                    out.append(cur)
                return out or [s]
            stops = sorted(set([0.0] + [s for s in pauses[seg] if 0.0 <= s < ad] + [ad]))
            if len(stops) >= 2:
                # ① 把文本拆成原子（按所有标点），用于在停顿槽内对齐
                atoms = [a for a in re.split(r"(?<=[。！？；，、：])", text) if a.strip()]
                if not atoms:
                    atoms = [text]
                total_chars = sum(len(a) for a in atoms)
                total_dur = stops[-1] - stops[0]
                # 原子字符累计边界
                atom_bounds = [0]
                for a in atoms:
                    atom_bounds.append(atom_bounds[-1] + len(a))
                # ② 每个停顿对应的「期望字符位置」= 按时间比例映射
                # 优先对齐原子（标点）边界；若最近原子边界距离 > 4 字符，允许在原子内部硬切
                # （中文可单字切；英文/数字串保留完整，切点取最近的非字母数字边界）
                seg_boundaries = [0]
                for k in range(1, len(stops)):
                    target = total_chars * (stops[k] - stops[0]) / total_dur if total_dur > 0 else total_chars
                    best = seg_boundaries[-1]
                    best_dist = abs(atom_bounds[min(best, len(atom_bounds) - 1)] - target)
                    for i in range(seg_boundaries[-1] + 1, len(atom_bounds)):
                        d = abs(atom_bounds[i] - target)
                        if d < best_dist:
                            best_dist = d
                            best = i
                        elif d > best_dist:
                            break
                    if k < len(stops) - 1:
                        best = max(best, seg_boundaries[-1] + 1)  # 每槽至少 1 个原子
                        # 长原子硬切：目标位置严格落在 atoms[best-1] 内部才切
                        # （target 已越过原子结尾时不切，整个原子归本槽）
                        if best_dist > 4.0 and best - 1 >= seg_boundaries[-1] \
                                and atom_bounds[best - 1] < target < atom_bounds[best]:
                            # 在 atoms[best-1] 内部切：先把 atoms 从 best-1 处拆开，再重算边界
                            atom = atoms[best - 1]
                            loc = int(round(target)) - atom_bounds[best - 1]  # 原子内局部切点
                            loc = max(1, min(loc, len(atom) - 1))
                            # 英文保护：切点若在字母/数字串中间，移到该串结尾
                            def is_word(ch):
                                # 字母数字 + 数字串常见标点（. % + - /）视为同一词，防拆断 77.9%/1.3B/DeepSeekMath
                                return ch.isascii() and (ch.isalnum() or ch in ".%+-/")
                            while loc < len(atom) and is_word(atom[loc - 1]) and is_word(atom[loc]):
                                loc += 1
                            # 切点若落在单词开头（loc-1 非词、loc 是词）→ 左移到词前；
                            # 勿把「单词结尾后」（loc-1 是词、loc 非词）左移回词内（2026-08-16 DeepSeekMath 拆断）
                            while loc > 1 and not is_word(atom[loc - 1]) and is_word(atom[loc]):
                                loc -= 1
                            atoms[best - 1:best] = [atom[:loc], atom[loc:]]
                            atom_bounds = [0]
                            for a in atoms:
                                atom_bounds.append(atom_bounds[-1] + len(a))
                            total_chars = atom_bounds[-1]
                            best = seg_boundaries[-1] + 1
                    else:
                        best = len(atoms)  # 末边界 = 全部原子
                    seg_boundaries.append(best)
                # ③ 构建 (begin, end, text) 三元组
                raw_slots = []
                for k in range(len(stops) - 1):
                    si = seg_boundaries[k]
                    ei = seg_boundaries[k + 1]
                    if ei <= si:
                        ei = min(si + 1, len(atoms))
                    blk = "".join(atoms[si:ei]).strip()
                    raw_slots.append((stops[k], stops[k + 1], blk))
                # ④ 超过 26 字的槽：在标点处拆分，时间按字数比例分配
                final_slots = []
                for (vb, ve, txt) in raw_slots:
                    if len(txt) <= 26:
                        final_slots.append((vb, ve, txt))
                    else:
                        sub_blks = split_sent(txt)
                        sub_total = sum(len(sb) for sb in sub_blks) or 1
                        acc = 0.0
                        for sb in sub_blks:
                            w = len(sb) / sub_total
                            sb_begin = vb + acc * (ve - vb)
                            acc += w
                            sb_end = vb + acc * (ve - vb)
                            final_slots.append((sb_begin, sb_end, sb))
                # ⑤ 合并空文本或过短槽（<0.5s）到前一条——前提：合并后不超 26 字
                merged = []
                for (vb, ve, txt) in final_slots:
                    # 纯标点槽（孤立「。」等）或 <0.5s 槽 → 并入前一条（前提：不超 26 字）；
                    # 超限时重平衡：从尾部切出「尾词+标点」成条，避免孤立标点
                    punct_only = bool(txt) and all(ch in "。！？；，、：…—「」" for ch in txt)
                    too_short = (not txt or ve - vb < 0.5 or punct_only)
                    if too_short and merged:
                        prev_text = merged[-1][2]
                        if len(prev_text) + len(txt) <= 26:
                            merged[-1] = (merged[-1][0], ve, prev_text + txt)
                        elif punct_only and prev_text:
                            cut = -1
                            for i in range(len(prev_text) - 1, -1, -1):
                                if prev_text[i] in " ，。！？；、：—" and len(prev_text) - i - 1 + len(txt) <= 26:
                                    cut = i
                                    break
                            if cut < 0:
                                cut = max(0, len(prev_text) - (26 - len(txt)))
                            merged[-1] = (merged[-1][0], vb, prev_text[:cut + 1].rstrip())
                            merged.append((vb, ve, (prev_text[cut + 1:] + txt).lstrip()))
                        else:
                            merged.append((vb, ve, txt))
                    else:
                        merged.append((vb, ve, txt))
                # ⑥ 首条仍过短（前向合并到第二条）
                if len(merged) >= 2 and merged[0][1] - merged[0][0] < 0.5:
                    if len(merged[0][2]) + len(merged[1][2]) <= 26:
                        merged[1] = (merged[0][0], merged[1][1],
                                     merged[0][2] + merged[1][2])
                        merged.pop(0)
                for (vb, ve, txt) in merged:
                    v_begin = t + vb
                    v_end = t + ve
                    if v_end > v_begin and txt:
                        entries.append((v_begin, v_end, txt))
            else:
                # 无停顿点：按句号切分 + 字数比例分配
                sentences = [s for s in re.split(r"(?<=[。！？；])", text) if s.strip()]
                if not sentences:
                    sentences = [text]
                blocks = []
                for s in sentences:
                    blocks.extend(split_sent(s))
                total = sum(len(b) for b in blocks) or 1
                acc = 0.0
                for blk in blocks:
                    w = len(blk) / total
                    v_begin = t + acc * ad
                    acc += w
                    v_end = t + acc * ad
                    if v_end <= v_begin:
                        continue
                    entries.append((v_begin, v_end, blk))
            t += vd
            audio_t += ad
            continue

        if subtitle_ts is not None:
            # 该段在 full audio 时间轴上的句子。
            # 归属规则（2026-08-18 修复跨段句碎片）：句子归属第一个匹配段
            # （放宽 ±0.5s 吸收 tts_split 段边界与 ffprobe 实测的 ~0.1s 差），
            # v_end 不截断（跨段句的语音实际在段内，字幕跨段显示与语音同步）；
            # seen_sents 去重，避免句子被相邻两段重复处理。
            sents = []
            for s in subtitle_ts:
                sb = s["time_begin"] / 1000.0
                if sb in seen_sents:
                    continue
                if audio_t - 0.5 <= sb < audio_t + ad + 0.5:
                    seen_sents.add(sb)
                    sents.append((sb, s["time_end"] / 1000.0, strip_tts_tags(s["text"])))
            if sents:
                for s_begin, s_end, s_text in sents:
                    v_begin = t + max(0.0, s_begin - audio_t)
                    v_end = t + (s_end - audio_t)
                    if v_end <= v_begin:
                        continue
                    chunks = split_long(s_text)
                    total = sum(len(c) for c in chunks) or 1
                    acc = 0.0
                    span = v_end - v_begin
                    for c in chunks:
                        w = len(c) / total
                        a = v_begin + acc * span
                        acc += w
                        b = v_begin + acc * span
                        entries.append((a, b, c))
                t += vd
                audio_t += ad
                continue

        # 无时间戳 fallback：按字数比例分布
        start = t + 0.25
        chunks = split_long(text)
        total = sum(len(c) for c in chunks) or 1
        acc = 0.0
        for c in chunks:
            w = len(c) / total
            a = start + acc * ad
            acc += w
            b = start + acc * ad
            entries.append((a, b, c))
        t += vd
        audio_t += ad
    return _merge_pure_punct_entries(entries)


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
    def wrap_line(txt: str, per_line: int = 13) -> str:
        # 手动按 per_line 字折行（libass 对中文不自动折行，长字幕会超出画面被裁）。
        # 最多折 2 行：若片段 ≤ 2*per_line，在中间找一个可断点（中文标点 > 英文空格 > 字符）
        # 拆成 2 行，每行尽量 ≤ per_line，不拆断英文单词。
        if len(txt) <= per_line:
            return txt
        if len(txt) <= 2 * per_line:
            # 折 2 行：在中间附近找可断点
            mid = len(txt) // 2
            # 在 [mid-3, mid+3] 范围内找中文标点或空格
            best = -1
            for i in range(mid, -1, -1):
                if txt[i] in "，。！？；、：—– ":
                    best = i
                    break
            if best < 0:
                for i in range(mid, len(txt)):
                    if txt[i] in "，。！？；、：—– ":
                        best = i
                        break
            if best < 0:
                # 无标点/空格：避免拆断英文单词，回退到单词边界
                m = re.search(r'[A-Za-z]+$', txt[:mid])
                if m and m.start() > 0:
                    best = m.start()
                else:
                    best = mid
            return txt[:best + 1] + "\\N" + txt[best + 1:]
        # 超过 2 行容量（>26 字）：在标点/空格处拆成多行，但尽量少行
        lines = []
        cur = ""
        for ch in txt:
            cur += ch
            if len(cur) >= per_line:
                break_at = -1
                for i in range(len(cur) - 1, -1, -1):
                    if cur[i] in "，。！？；、：—– ":
                        break_at = i
                        break
                if break_at >= 0:
                    lines.append(cur[:break_at + 1])
                    cur = cur[break_at + 1:]
                else:
                    m = re.search(r'[A-Za-z]+$', cur)
                    if m and m.start() > 0:
                        lines.append(cur[:m.start()])
                        cur = cur[m.start():]
                    else:
                        lines.append(cur)
                        cur = ""
        if cur:
            lines.append(cur)
        return "\\N".join(lines)

    events = [
        f"Dialogue: 0,{ass_ts(a)},{ass_ts(b)},Default,,0,0,0,,{r'{\fad(60,40)}' if fade else ''}{wrap_line(txt)}"
        for a, b, txt in entries
    ]
    with open(out, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")


def self_test() -> None:
    assert strip_tts_tags("(breath) 为什么 loss 一直抖？(inhale) 但别慌。") == "为什么 loss 一直抖？但别慌。"
    assert strip_tts_tags("(sighs)(breath) 连写标签") == "连写标签"
    assert strip_tts_tags("无标签文本") == "无标签文本"
    assert "DeepSeekMath" in "".join(split_long("GRPO 的起点，是 2024 年 DeepSeek 的 DeepSeekMath。"))
    assert split_long("AIME 2024 正确率从 15.6% 冲到 77.9%，") == ["AIME 2024 正确率从 15.6% 冲到", "77.9%，"]
    merged = _merge_pure_punct_entries([(0.0, 1.0, "反思"), (1.0, 1.2, "。")])
    assert merged == [(0.0, 1.2, "反思。")]
    entries = build_srt({"S1": "(breath) 一二三四五六七八九十"}, {"S1": 10.0}, 0.1)
    assert entries[0][2] == "一二三四五六七八九十"
    # 口播模式：停顿边界驱动字幕（seg_dur 10s, tail 0.1 → ad=9.9）
    pe = build_srt({"S1": "一二三。四五六。七八九。"}, {"S1": 10.0}, 0.1, pauses={"S1": [3.3, 6.6]})
    # 停顿切 3 块，字幕应落在对应的停顿区间内，且最后一块结束于 t+ad
    assert abs(pe[0][0] - 0.0) < 1e-6, pe
    assert abs(pe[-1][1] - 9.9) < 1e-6, pe
    assert abs(pe[1][0] - 3.3) < 1e-6 or abs(pe[2][0] - 3.3) < 1e-6, pe
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
        actual = dur_of(wd / f"build_{seg}.mp4")
        seg_dur[seg] = actual  # 用实际段时长（AAC 编码 padding 后略超 vd），字幕时间轴与 concat 严格一致
        print(f"{seg}: 配音 {ad:.2f}s → 视频 {vd:.2f}s（实际 {actual:.2f}s）")

    # 4) concat（ts 中转：ffmpeg concat demuxer 直接拼 mp4 会改写第 2+ 段的 AAC
    #    （edit list/priming 处理），导致段内音画漂移——先转 mpegts 再拼，字节保留）
    for seg in segments:
        run(["ffmpeg", "-y", "-v", "error", "-i", str(wd / f"build_{seg}.mp4"),
             "-c", "copy", "-f", "mpegts", str(wd / f"build_{seg}.ts")])
    concat_txt = wd / "concat.txt"
    concat_txt.write_text("".join(f"file 'build_{s}.ts'\n" for s in segments), encoding="utf-8")
    full = wd / "build_full.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(concat_txt), "-c", "copy", str(full)])

    # 5) 字幕 SRT + ASS（优先用 TTS 句子级时间戳对齐，修复对白漂移）
    voices_map = {seg: v for seg, v in zip(segments, voices)}
    # 字幕时间戳：Web 人工确认边界 > 口播真实停顿 > TTS 句子级时间戳。
    manual_alignment = None
    manual_json = wd / "tts" / "manual-boundaries.json"
    if manual_json.exists():
        try:
            manual_alignment = json.loads(manual_json.read_text(encoding="utf-8"))
            print(f"口播字幕时间戳: {manual_json.name}（人工确认优先）")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ 读取 {manual_json} 失败（{e}），退回自动停顿对齐")
    pauses = None
    pause_json = wd / "tts" / "pauses.json"
    if pause_json.exists():
        try:
            pauses = json.loads(pause_json.read_text(encoding="utf-8"))
            print(f"口播字幕时间戳: {pause_json.name}（兜底：无逐句时间戳时用）")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ 读取 {pause_json} 失败（{e}），退回其他时间戳策略")
    sentence_ts = None
    sentence_json = wd / "tts" / "sentence-boundaries.json"
    if sentence_json.exists():
        try:
            sentence_ts = sentence_boundary_alignment(json.loads(sentence_json.read_text(encoding="utf-8")))
            if sentence_ts:
                validate_sentence_ts(sentence_ts, voices_map, pauses)
                print(f"字幕时间戳: {sentence_json.name}（逐句 start/end，最高自动优先级）")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ 读取 {sentence_json} 失败（{e}），字幕退回停顿/字数比例")
    sub_ts = None
    sub_json = wd / "tts" / "full.subtitle.json"
    if sub_json.exists():
        try:
            sub_ts = json.loads(sub_json.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ 读取 {sub_json} 失败（{e}），字幕退回字数比例分布")
    entries = build_srt(voices_map, seg_dur, args.tail, sub_ts, pauses, manual_alignment, sentence_ts)
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
