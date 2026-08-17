#!/usr/bin/env python3
"""本地 Web 口播录音室：任意 ``shipinhao/tts.txt`` 的逐段录制与交接。

运行::

    python3 scripts/voice_studio.py content/<发布日期>-<主题>/shipinhao

流程：绑定并检测 CM40 → 逐段录音 → 复用现有 ffmpeg 静音算法裁掉首尾静音、
按真实句间停顿切出可试听的短片 → 满意后确认下一段 → 调用
``voice_process.py`` 生成 ``tts/sN.wav``、``tts/pauses.json`` 与一致性报告。

``tts.txt`` 是唯一输入：每个非空行就是一个录音段，数量不设上限；不包含 PPO
或其他文章的任何硬编码。
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import threading
import time
import wave
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import numpy as np
import record_voice
import trim_silence
import voice_process

PORT = 8787
TTS_SPEED = 0.195
ORAL_MARGIN = 1.15
LEAD_SEC = 3.0
SIGNAL_READY_DB = -40.0
STATE_VERSION = 1
# 削波门禁（2026-08-17 GRPO s1/s2 爆破音教训）：
#   - CLIP_SAMPLE_RATIO：全段 0dBFS 满幅样本占比。s2 录音 1.3% 造成明显爆破音，故硬门禁取 0.05%
#     （人声重音瞬态偶发几毫秒平顶属正常，低于阈值不拦）；≥阈值 = 输入增益过高，必须重录
#   - CLIP_PEAK_DB：峰值过低（< -6dB）提醒离麦太远/增益不足，只提醒不拦
#   - CLIP_BLOCK_MSG / CLIP_HINT_MSG：分别对应硬门禁与提醒的界面文案
CLIP_SAMPLE_RATIO = 0.0005
CLIP_PEAK_DB = -6.0
CLIP_BLOCK_MSG = "检测到大量削波（0dB 满幅样本）——输入增益过高，声音会明显发破/发闷。请调低麦克风输入增益（或离麦远一点）后重录本段，否则爆破音会带进成片。"
CLIP_HINT_MSG = "检测到少量削波（0dB 满幅样本）——已经偏满。重录本段时请稍微离麦远一点或调低一点增益，声音会更亮更干净。"

WD: Path
SEGS: list[dict[str, str]] = []
MIC_HINT = "CM40"
LOCK = threading.RLock()
SESSION: dict[str, dict[str, Any]] = {}
RUNTIME: dict[str, Any] = {
    "recording": None,
    "process": None,
    "stop_event": None,
    "mic": {
        "name": "未检测",
        "available": False,
        "input_ready": False,
        "signal_db": None,
        "message": "正在寻找 CM40…",
    },
    "finalize": {"status": "idle", "message": ""},
}


def load_segments(path: Path) -> list[dict[str, str]]:
    """Load every non-empty tts line as a recording segment, with no count cap."""
    if not path.exists():
        raise ValueError(f"缺少台本：{path}")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"台本没有可录制的非空行：{path}")
    return [{"id": f"s{i}", "text": text} for i, text in enumerate(lines, 1)]


def est_dur(text: str) -> int:
    """Soft recording cap: TTS estimate + oral margin + 10 seconds."""
    return max(10, int(len(text.replace(" ", "")) * TTS_SPEED * ORAL_MARGIN) + 10)


def ffprobe_dur(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def build_trim_bounds(raw_path: Path) -> tuple[float, float]:
    """Use the shared trim policy, falling back safely when no silence is found."""
    duration = ffprobe_dur(raw_path)
    if duration <= 0:
        raise ValueError("录音文件为空或无法读取")
    try:
        bounds = trim_silence.speech_bounds(raw_path)
    except (subprocess.SubprocessError, OSError):
        bounds = None
    if bounds is None:
        return 0.0, duration
    start = max(0.0, round(bounds[0] - 0.1, 3))
    end = min(duration, round(bounds[1] + 0.1, 3))
    return (start, end) if end > start else (0.0, duration)


def clipping_stats(path: Path) -> tuple[float, float]:
    """返回 (0dBFS 满幅样本占比, 峰值 dB)。削波 = 输入增益过高，后期无法修复，必须在录音时拦下。"""
    try:
        with wave.open(str(path), "rb") as w:
            n = w.getnframes()
            if n <= 0:
                return 0.0, -99.0
            data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
            peak = float(np.abs(data).max()) if len(data) else 0.0
            if peak <= 0.0:
                return 0.0, -99.0
            ratio = float((np.abs(data) >= 0.999).mean())
            return ratio, 20.0 * math.log10(peak)
    except (OSError, EOFError, ValueError):
        return 0.0, -99.0


def silence_gaps(path: Path, min_duration: float = voice_process.SILENCE_MIN) -> list[tuple[float, float]]:
    """Return speech-relevant gaps using voice_process.py's threshold and duration."""
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", str(path), "-af",
            f"silencedetect=noise={voice_process.SILENCE_DB}dB:d={min_duration}",
            "-f", "null", "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    starts = [float(v) for v in re.findall(r"silence_start: ([0-9.]+)", result.stderr)]
    ends = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", result.stderr)]
    return [(start, end) for start, end in zip(starts, ends) if end > start]


def _best_cut(text: str, previous: int, target: int, latest: int) -> int:
    """Prefer punctuation near a time-proportional character cut without dropping text."""
    if latest <= previous:
        return previous
    target = max(previous + 1, min(target, latest))
    punctuation = "。！？；，、："
    candidates = [i for i in range(previous + 1, latest + 1) if text[i - 1] in punctuation]
    if candidates:
        return min(candidates, key=lambda i: (abs(i - target), -i))
    return target


def make_sentence_clips(
    seg_id: str,
    text: str,
    duration: float,
    pause_ends: list[float],
) -> list[dict[str, Any]]:
    """Map the script to every detected, valid pause boundary for Web review.

    The text remains lossless (concatenating all clip text reconstructs ``text``).  A
    clip boundary is always retained for every real pause so the reviewer can see
    the timing evidence that later drives Manim subtitles.
    """
    if duration <= 0:
        return []
    boundaries = sorted({round(float(v), 3) for v in pause_ends if 0.0 < float(v) < duration})
    stops = [0.0, *boundaries, round(duration, 3)]
    slot_count = len(stops) - 1
    if not text:
        return [
            {"id": f"{seg_id}-c{i:02d}", "start": stops[i], "end": stops[i + 1], "text": ""}
            for i in range(slot_count)
        ]

    # Keep one character for every future non-empty slot when possible.  With
    # pathological noise creating more pauses than characters, timing remains
    # visible and the excess clips deliberately have an empty transcript.
    cuts = [0]
    usable_slots = min(slot_count, len(text))
    for index in range(1, usable_slots):
        remaining = usable_slots - index
        latest = len(text) - remaining
        target = round(len(text) * stops[index] / duration)
        cuts.append(_best_cut(text, cuts[-1], target, latest))
    cuts.append(len(text))

    clips: list[dict[str, Any]] = []
    for index in range(slot_count):
        if index < usable_slots:
            start_char = cuts[index]
            end_char = cuts[index + 1]
            clip_text = text[start_char:end_char]
        else:
            clip_text = ""
        clips.append(
            {
                "id": f"{seg_id}-c{index + 1:02d}",
                "start": round(stops[index], 3),
                "end": round(stops[index + 1], 3),
                "text": clip_text,
            }
        )
    return clips


def state_path() -> Path:
    return WD / "recordings" / "studio-state.json"


def phrase_dir(seg_id: str) -> Path:
    return WD / "recordings" / "phrases" / seg_id


def manual_alignment_path() -> Path:
    """Author-confirmed mapping from one audio segment to arbitrary text blocks."""
    return WD / "recordings" / "manual-boundaries.json"


def _alignment_text(text: str) -> str:
    """Whitespace is editorial only; every spoken character must still be accounted for."""
    return re.sub(r"\s+", "", text)


def punctuation_blocks(text: str) -> list[str]:
    """Keep the existing punctuation cut as the smallest editable script unit.

    The browser may group adjacent blocks onto one audio clip, but it must never
    create a new textual cut inside one of these blocks.  Keeping this helper on
    the server makes that guarantee hold even for a handcrafted API request.
    """
    blocks: list[str] = []
    start = 0
    for match in re.finditer(r"[。！？；，、：]", text):
        blocks.append(text[start:match.end()])
        start = match.end()
    if start < len(text):
        blocks.append(text[start:])
    return [block for block in blocks if block]


def load_manual_alignments() -> dict[str, Any]:
    path = manual_alignment_path()
    if not path.exists():
        return {"version": 1, "segments": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("segments"), dict):
            return data
    except (OSError, ValueError, TypeError):
        pass
    return {"version": 1, "segments": {}}


def save_manual_alignment(seg_id: str, analysis: dict[str, Any]) -> None:
    data = load_manual_alignments()
    data["segments"][seg_id.upper()] = {
        "source_duration": analysis["duration"],
        "clips": [
            {key: clip[key] for key in ("id", "start", "end", "text")}
            for clip in analysis["clips"]
        ],
    }
    manual_alignment_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_manual_alignment(seg_id: str) -> None:
    data = load_manual_alignments()
    if data["segments"].pop(seg_id.upper(), None) is not None:
        manual_alignment_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_alignment(seg_id: str, text: str, duration: float, payload: Any) -> list[dict[str, Any]]:
    """Validate a user-edited map made of consecutive punctuation-level blocks."""
    if not isinstance(payload, list) or not payload:
        raise ValueError("至少保留一个文本块")
    if len(payload) > 120:
        raise ValueError("文本块不能超过 120 个")
    blocks = punctuation_blocks(text)
    clips: list[dict[str, Any]] = []
    previous_end = 0.0
    next_block = 0
    for index, item in enumerate(payload, 1):
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            raise ValueError(f"第 {index} 个文本块格式不正确")  # noqa: TRY004 - API returns actionable validation errors
        try:
            start = round(float(item["start"]), 3)
            end = round(float(item["end"]), 3)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"第 {index} 个文本块的时间格式不正确") from error
        if not 0.0 <= start < end <= duration + 0.001:
            raise ValueError(f"第 {index} 个文本块必须位于 0–{duration:.2f}s 内，且结束晚于开始")
        if start < previous_end - 0.001:
            raise ValueError("文本块不能在时间线上重叠；请从前到后拖动")
        try:
            block_start = int(item["block_start"])
            block_end = int(item["block_end"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"第 {index} 段请选择连续的标点文本块") from error
        if block_start != next_block or not block_start <= block_end < len(blocks):
            raise ValueError("文本块必须从前到后连续覆盖原台本，不能跳过或重叠")
        selected_text = "".join(blocks[block_start:block_end + 1])
        if _alignment_text(item["text"]) != _alignment_text(selected_text):
            raise ValueError(f"第 {index} 段的文字不对应所选标点文本块")
        clips.append({
            "id": f"{seg_id}-c{index:02d}", "start": start, "end": end,
            "text": selected_text, "block_start": block_start, "block_end": block_end,
        })
        previous_end = end
        next_block = block_end + 1
    if next_block != len(blocks):
        raise ValueError("所有标点文本块都必须选择一次")
    return clips


def validate_piece_alignment(
    seg_id: str,
    text: str,
    duration: float,
    source_clips: Any,
    payload: Any,
) -> tuple[list[dict[str, Any]], list[tuple[float, float]]]:
    """Validate queue-style 1–3 audio × 1–3 punctuation-block matching.

    A group retains its original audio ranges; it is only one text/time label for
    downstream subtitles, never an audio-file merge.  A deleted group consumes
    exactly one audio piece and no script block, so the next group starts at the
    same text candidate.
    """
    if not isinstance(source_clips, list) or not source_clips:
        raise ValueError("没有可编辑的音频片段")
    if not isinstance(payload, list) or not payload:
        raise ValueError("请为每个音频片段保留匹配或删除操作")
    blocks = punctuation_blocks(text)
    clips: list[dict[str, Any]] = []
    deleted: list[tuple[float, float]] = []
    audio_index = 0
    text_index = 0

    for group_index, item in enumerate(payload, 1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {group_index} 个匹配单元格式不正确")  # noqa: TRY004 - browser needs a validation message
        try:
            expected_audio = int(item["audio_start"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"第 {group_index} 个匹配单元缺少音频位置") from error
        if expected_audio != audio_index:
            raise ValueError("音频片段必须从前到后连续确认")
        if item.get("delete") is True:
            if audio_index >= len(source_clips):
                raise ValueError("删除的音频片段超出范围")
            source = source_clips[audio_index]
            try:
                start, end = float(source["start"]), float(source["end"])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("原始音频片段时间无效") from error
            if not 0.0 <= start < end <= duration + 0.001:
                raise ValueError("删除的音频片段不在本段时间线内")
            deleted.append((start, end))
            audio_index += 1
            continue

        try:
            audio_count = int(item["audio_count"])
            block_start = int(item["block_start"])
            block_end = int(item["block_end"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"第 {group_index} 个匹配单元缺少连续范围") from error
        text_count = block_end - block_start + 1
        if not 1 <= audio_count <= 3 or not 1 <= text_count <= 3:
            raise ValueError("每个匹配单元只能选择连续 1～3 个音频和 1～3 个标点文本块")
        if audio_index + audio_count > len(source_clips):
            raise ValueError("所选音频片段超出范围")
        if block_start != text_index or block_end >= len(blocks):
            raise ValueError("文本块必须从前到后连续确认")
        source_begin = source_clips[audio_index]
        source_end = source_clips[audio_index + audio_count - 1]
        try:
            start = round(float(source_begin["start"]), 3)
            end = round(float(source_end["end"]), 3)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("原始音频片段时间无效") from error
        if not 0.0 <= start < end <= duration + 0.001:
            raise ValueError("音频片段不在本段时间线内")
        selected_text = "".join(blocks[block_start:block_end + 1])
        clips.append(
            {
                "id": f"{seg_id}-c{len(clips) + 1:02d}",
                "start": start,
                "end": end,
                "text": selected_text,
                "block_start": block_start,
                "block_end": block_end,
                "audio_start": audio_index,
                "audio_count": audio_count,
            }
        )
        audio_index += audio_count
        text_index = block_end + 1

    if audio_index != len(source_clips):
        raise ValueError("每个音频片段都需要确认对应关系或删除")
    if not clips:
        raise ValueError("不能删除整段录音")
    if text_index != len(blocks):
        raise ValueError("所有标点文本块都必须选择一次")
    return clips, sorted(set(deleted))


def selected_gaps(analysis: dict[str, Any], payload: Any) -> list[tuple[float, float]]:
    """Resolve only user-selected, detected silence spans; invalid IDs are ignored."""
    if not isinstance(payload, list):
        return []
    valid = analysis.get("gaps", [])
    chosen: list[tuple[float, float]] = []
    for value in payload:
        if isinstance(value, int) and 0 <= value < len(valid):
            start, end = valid[value]
            if end > start:
                chosen.append((float(start), float(end)))
    return sorted(set(chosen))


def shifted_time(value: float, gaps: list[tuple[float, float]]) -> float:
    """Translate a timestamp after removing non-overlapping silence intervals."""
    return round(value - sum(max(0.0, min(value, end) - start) for start, end in gaps), 3)


def remove_silences(source: Path, gaps: list[tuple[float, float]], duration: float) -> float:
    """Physically remove explicitly rejected intervals from the editable trim WAV."""
    if not gaps:
        return duration
    keep: list[tuple[float, float]] = []
    cursor = 0.0
    for start, end in gaps:
        if start > cursor:
            keep.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < duration:
        keep.append((cursor, duration))
    if not keep:
        raise ValueError("不能删除整段音频")
    filters = [f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]" for i, (start, end) in enumerate(keep)]
    labels = "".join(f"[a{i}]" for i in range(len(keep)))
    if len(keep) == 1:
        graph = filters[0] + ";[a0]anull[out]"
    else:
        graph = ";".join(filters) + f";{labels}concat=n={len(keep)}:v=0:a=1[out]"
    temporary = source.with_suffix(".edited.wav")
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-filter_complex", graph,
         "-map", "[out]", "-c:a", "pcm_s16le", str(temporary)],
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0 or not temporary.exists():
        raise ValueError(result.stderr.strip() or "删除音频片段失败")
    temporary.replace(source)
    return ffprobe_dur(source)


def save_state() -> None:
    payload = {
        "version": STATE_VERSION,
        "segments": [{"id": s["id"], "text": s["text"], **SESSION[s["id"]]} for s in SEGS],
    }
    state_path().parent.mkdir(parents=True, exist_ok=True)
    state_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def initialise_state() -> None:
    global SESSION
    SESSION = {seg["id"]: {"status": "pending", "analysis": None} for seg in SEGS}
    path = state_path()
    if not path.exists():
        return
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
        prior_segments = {item["id"]: item for item in previous.get("segments", [])}
        for seg in SEGS:
            prior = prior_segments.get(seg["id"])
            if (
                prior
                and prior.get("text") == seg["text"]
                and prior.get("status") in {"review", "approved"}
                and (WD / "recordings" / f"{seg['id']}.wav").exists()
            ):
                SESSION[seg["id"]] = {
                    "status": prior["status"],
                    "analysis": prior.get("analysis"),
                    "recorded_at": prior.get("recorded_at"),
                }
    except (OSError, ValueError, TypeError, KeyError):
        # A corrupt, old or different-script state must never block a new session.
        pass


def current_segment_id() -> str | None:
    return next((seg["id"] for seg in SEGS if SESSION[seg["id"]]["status"] != "approved"), None)


def find_segment(seg_id: str) -> dict[str, str] | None:
    return next((seg for seg in SEGS if seg["id"] == seg_id), None)


def choose_mic(cards: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Bind CM40 first; BOYA is its known device-family fallback, never internal mic."""
    wanted = MIC_HINT.lower()
    ranked: list[tuple[int, dict[str, Any]]] = []
    for card in cards:
        identity = " ".join(str(card.get(key, "")) for key in ("name", "desc", "device")).lower()
        if wanted in identity:
            ranked.append((0, card))
        elif wanted == "cm40" and "boya" in identity:
            ranked.append((1, card))
    return min(ranked, key=lambda item: item[0])[1] if ranked else None


def refresh_mic() -> None:
    """Probe the requested microphone in a worker; no other device is silently selected."""
    try:
        cards = record_voice.list_cards()
        mic = choose_mic(cards)
        if mic is None:
            result = {
                "name": f"未找到 {MIC_HINT}", "available": False, "input_ready": False,
                "signal_db": None, "message": f"请连接或选择名为 {MIC_HINT} 的录音设备",
            }
        else:
            signal = record_voice.probe_signal(mic["card"], mic["device"])
            result = {
                "name": mic["name"], "card": mic["card"], "device": mic["device"],
                "available": True, "input_ready": signal > SIGNAL_READY_DB, "signal_db": round(signal, 1),
                "message": (
                    f"{MIC_HINT} 已绑定，输入信号 {signal:.1f} dB"
                    if signal > SIGNAL_READY_DB
                    else f"{MIC_HINT} 已绑定，但未测到足够输入；点击检测时请对麦克风说话"
                ),
            }
    except Exception as error:  # noqa: BLE001 - browser receives an actionable message
        result = {
            "name": f"{MIC_HINT} 检测失败", "available": False, "input_ready": False,
            "signal_db": None, "message": str(error),
        }
    with LOCK:
        RUNTIME["mic"] = result


def run_mic_probe() -> None:
    with LOCK:
        if RUNTIME.get("mic_probing"):
            return
        RUNTIME["mic_probing"] = True

    def job() -> None:
        try:
            refresh_mic()
        finally:
            with LOCK:
                RUNTIME["mic_probing"] = False

    threading.Thread(target=job, daemon=True).start()


def _record_command(mic: dict[str, Any], out: Path) -> list[str]:
    if int(mic["card"]) >= 1000:
        return [
            "pw-record", "--target", str(mic["device"]), "--rate", "48000", "--channels", "2",
            "--volume", "1.0", str(out),
        ]
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "alsa", "-i",
        f"hw:{mic['card']},{mic['device']}", "-ar", "48000", "-ac", "2", "-y", str(out),
    ]


def create_trim(raw: Path, trimmed: Path) -> tuple[float, float]:
    start, end = build_trim_bounds(raw)
    trimmed.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
            "-ss", str(start), "-to", str(end), "-c:a", "pcm_s16le", str(trimmed),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not trimmed.exists():
        raise ValueError(result.stderr.strip() or "ffmpeg 裁剪失败")
    return start, end


def write_phrase_clips(seg_id: str, source: Path, clips: list[dict[str, Any]]) -> None:
    target_dir = phrase_dir(seg_id)
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    for clip in clips:
        if clip["end"] <= clip["start"]:
            continue
        output = target_dir / f"{clip['id'].split('-')[-1]}.wav"
        result = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                "-ss", str(clip["start"]), "-to", str(clip["end"]), "-c:a", "pcm_s16le", str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and output.exists():
            clip["audio"] = clip["id"].split("-")[-1]
        else:
            clip["audio_error"] = result.stderr.strip() or "切分失败"


def analyse_recording(seg_id: str, text: str) -> dict[str, Any]:
    raw = WD / "recordings" / f"{seg_id}.wav"
    if not raw.exists():
        raise ValueError("录音文件没有生成")
    raw_duration = ffprobe_dur(raw)
    if raw_duration <= 0:
        raise ValueError("录音文件为空")
    trimmed = WD / "trim" / f"{seg_id}.wav"
    trim_start, trim_end = create_trim(raw, trimmed)
    duration = ffprobe_dur(trimmed)
    gaps = silence_gaps(trimmed)
    phrase_gaps = [(start, end) for start, end in gaps if start > 0.05 and end < duration - 0.05]
    pause_ends = [end for _, end in phrase_gaps]
    clips = make_sentence_clips(seg_id, text, duration, pause_ends)
    write_phrase_clips(seg_id, trimmed, clips)
    # Keep the physical, automatically cut pieces separate from the logical
    # text mapping.  A later correction may assign 1–3 pieces to one sentence
    # without merging their audio files.
    audio_pieces = [dict(clip) for clip in clips]
    quality_gaps = silence_gaps(trimmed, min_duration=0.30)
    silent_total = sum(end - start for start, end in quality_gaps)
    speech_ratio = max(0.0, 1.0 - silent_total / duration) if duration else 0.0
    longest = max((end - start for start, end in phrase_gaps), default=0.0)
    expected = len(text.replace(" ", "")) * TTS_SPEED
    # 削波检测（2026-08-17 GRPO 教训）：0dB 满幅平顶样本 = 录音时输入增益过高，
    # 后期无法修复，必须在录音室就拦截。在裁剪后 trim 上测（与试听一致），
    # 相对阈值看占比；同时报峰值供「偏满」提醒与 UI 展示。
    clip_ratio, peak_db = clipping_stats(trimmed)
    issues: list[str] = []
    blocking: list[str] = []
    if clip_ratio >= CLIP_SAMPLE_RATIO:
        issues.append(CLIP_BLOCK_MSG)
        blocking.append(CLIP_BLOCK_MSG)
    elif clip_ratio > 0.0:
        issues.append(CLIP_HINT_MSG)
    elif peak_db < CLIP_PEAK_DB:
        issues.append(f"录音峰值偏低（{peak_db:.1f}dB）：可能离麦太远。请靠近 CM40 约 20-30cm，声音会更亮。")
    if speech_ratio < 0.5:
        message = f"语音占比 {speech_ratio:.0%} 偏低：请靠近 CM40，并检查环境噪声"
        issues.append(message)
        blocking.append(message)
    if longest >= 1.5:
        message = f"检测到 {longest:.1f}s 长停顿：可能忘词，必须重录后才能继续"
        issues.append(message)
        blocking.append(message)
    if expected and abs(duration - expected) / expected > 0.35:
        issues.append(f"实录 {duration:.1f}s 与预估 {expected:.0f}s 偏差较大：请确认没有漏句")
    return {
        "raw_duration": round(raw_duration, 3), "duration": round(duration, 3),
        "trim": [round(trim_start, 3), round(trim_end, 3)],
        "speech_ratio": round(speech_ratio, 3), "longest_pause": round(longest, 3),
        "clip_ratio": round(clip_ratio, 6), "peak_db": round(peak_db, 1),
        "gaps": [[round(start, 3), round(end, 3)] for start, end in phrase_gaps],
        "clips": clips, "audio_pieces": audio_pieces, "issues": issues, "blocking": blocking,
    }


def stop_process(process: subprocess.Popen[bytes] | subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def record_job(seg: dict[str, str]) -> None:
    seg_id, text = seg["id"], seg["text"]
    cap = est_dur(text)
    try:
        # Countdown is cancellable; only the actual recording owns the microphone.
        deadline = time.monotonic() + LEAD_SEC
        while time.monotonic() < deadline:
            with LOCK:
                if RUNTIME["stop_event"].is_set():
                    RUNTIME["recording"] = None
                    return
            time.sleep(0.05)

        with LOCK:
            mic = dict(RUNTIME["mic"])
            if not mic.get("available"):
                raise ValueError(f"{MIC_HINT} 未就绪，请先检测设备")
            RUNTIME["recording"]["phase"] = "recording"
        raw = WD / "recordings" / f"{seg_id}.wav"
        raw.parent.mkdir(parents=True, exist_ok=True)
        process = subprocess.Popen(_record_command(mic, raw), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with LOCK:
            RUNTIME["process"] = process
        stop_at = time.monotonic() + cap
        while process.poll() is None and time.monotonic() < stop_at:
            with LOCK:
                if RUNTIME["stop_event"].is_set():
                    break
            time.sleep(0.1)
        stop_process(process)
        with LOCK:
            RUNTIME["process"] = None
            RUNTIME["recording"]["phase"] = "processing"
        analysis = analyse_recording(seg_id, text)
        with LOCK:
            clear_manual_alignment(seg_id)
            SESSION[seg_id] = {"status": "review", "analysis": analysis, "recorded_at": time.time()}
            save_state()
    except Exception as error:  # noqa: BLE001 - retained for browser recovery
        with LOCK:
            SESSION[seg_id] = {"status": "pending", "analysis": None, "error": str(error)}
            save_state()
    finally:
        with LOCK:
            RUNTIME["recording"] = None
            RUNTIME["process"] = None
            RUNTIME["stop_event"] = None


def start_record(seg_id: str) -> tuple[bool, str]:
    with LOCK:
        if RUNTIME["recording"] is not None:
            return False, f"正在录制 {RUNTIME['recording']['seg']}"
        if RUNTIME["finalize"]["status"] == "running":
            return False, "正在生成最终音频，请稍候"
        seg = find_segment(seg_id)
        if seg is None:
            return False, "未知段落"
        # A reviewed or approved segment already has a take, so it is an
        # explicit re-record request even when a later segment is the normal
        # workflow cursor.  Pending segments remain strictly sequential.
        if SESSION[seg_id]["status"] not in {"review", "approved"} and current_segment_id() != seg_id:
            return False, "请先确认当前段落，再进入下一段"
        if not RUNTIME["mic"].get("available"):
            return False, f"{MIC_HINT} 未绑定，请先检测设备"
        if not RUNTIME["mic"].get("input_ready"):
            return False, f"{MIC_HINT} 未检测到输入，请点击“检测输入”并对麦克风说话"
        # A new take invalidates any previous handoff; the finished card must
        # offer regeneration again once the segment is re-approved.
        RUNTIME["finalize"] = {"status": "idle", "message": ""}
        RUNTIME["stop_event"] = threading.Event()
        RUNTIME["recording"] = {
            "seg": seg_id, "phase": "countdown", "started_at": time.time() + LEAD_SEC,
            "cap": est_dur(seg["text"]),
        }
        threading.Thread(target=record_job, args=(seg,), daemon=True).start()
        return True, "倒计时开始"


def stop_recording() -> tuple[bool, str]:
    with LOCK:
        event = RUNTIME.get("stop_event")
        if RUNTIME.get("recording") is None or event is None:
            return False, "当前没有进行中的录音"
        event.set()
        process = RUNTIME.get("process")
    stop_process(process)
    return True, "正在结束录音并生成试听片段"


def approve_segment(seg_id: str) -> tuple[bool, str]:
    with LOCK:
        if current_segment_id() != seg_id:
            return False, "请按顺序确认段落"
        if SESSION[seg_id]["status"] != "review":
            return False, "请先完成录制并试听"
        blocking = SESSION[seg_id].get("analysis", {}).get("blocking", [])
        if blocking:
            return False, "本段有必须修复的录音问题，请重录后再继续"
        SESSION[seg_id]["status"] = "approved"
        save_state()
    return True, "已确认"


def update_alignment(seg_id: str, payload: Any) -> tuple[bool, str]:
    """Persist queue-style mapping and regenerate the review previews."""
    with LOCK:
        if current_segment_id() != seg_id or SESSION[seg_id]["status"] != "review":
            return False, "只能编辑当前待确认段落"
        segment = find_segment(seg_id)
        analysis = SESSION[seg_id].get("analysis")
        if segment is None or not isinstance(analysis, dict):
            return False, "本段没有可编辑的试听数据"
        try:
            source_pieces = analysis.get("audio_pieces", analysis.get("clips"))
            if isinstance(payload.get("pieces"), list):
                clips, removed = validate_piece_alignment(
                    seg_id,
                    segment["text"],
                    float(analysis["duration"]),
                    source_pieces,
                    payload["pieces"],
                )
            else:
                clips = validate_alignment(seg_id, segment["text"], float(analysis["duration"]), payload.get("clips"))
                removed = selected_gaps(analysis, payload.get("delete_gaps"))
            if removed:
                updated_duration = remove_silences(WD / "trim" / f"{seg_id}.wav", removed, float(analysis["duration"]))
                clips = [
                    {
                        **clip,
                        "start": shifted_time(clip["start"], removed),
                        "end": shifted_time(clip["end"], removed),
                    }
                    for clip in clips
                ]
                if any(clip["end"] <= clip["start"] for clip in clips):
                    raise ValueError("删除的音频覆盖了一段已匹配内容；请重新选择")
                analysis["duration"] = round(updated_duration, 3)
                analysis["gaps"] = [
                    [shifted_time(start, removed), shifted_time(end, removed)]
                    for start, end in analysis["gaps"]
                    if not any(float(start) < removed_end and float(end) > removed_start for removed_start, removed_end in removed)
                ]
                audio_pieces = [
                    {
                        **piece,
                        "start": shifted_time(float(piece["start"]), removed),
                        "end": shifted_time(float(piece["end"]), removed),
                    }
                    for piece in source_pieces
                    if (float(piece["start"]), float(piece["end"])) not in removed
                ]
            else:
                audio_pieces = [dict(piece) for piece in source_pieces]
        except ValueError as error:
            return False, str(error)
        write_phrase_clips(seg_id, WD / "trim" / f"{seg_id}.wav", audio_pieces)
        analysis["clips"] = clips
        analysis["audio_pieces"] = audio_pieces
        analysis["manual_alignment"] = True
        save_manual_alignment(seg_id, analysis)
        save_state()
    return True, "已保存：后续字幕与 Manim 将使用这组人工边界"


def final_manifest() -> Path:
    """Persist the exact pause-derived phrase map alongside final pipeline inputs."""
    tts_dir = WD / "tts"
    pauses_path = tts_dir / "pauses.json"
    pauses = json.loads(pauses_path.read_text(encoding="utf-8")) if pauses_path.exists() else {}
    manual_path = tts_dir / "manual-boundaries.json"
    manual = json.loads(manual_path.read_text(encoding="utf-8")) if manual_path.exists() else {"segments": {}}
    manual_segments = manual.get("segments", {}) if isinstance(manual, dict) else {}
    if not isinstance(manual_segments, dict):
        manual_segments = {}
    manifest: dict[str, Any] = {"source": "tts.txt", "segments": []}
    for seg in SEGS:
        audio = tts_dir / f"{seg['id']}.wav"
        duration = ffprobe_dur(audio)
        manual_segment = manual_segments.get(seg["id"].upper())
        clips = manual_segment.get("clips", []) if isinstance(manual_segment, dict) else []
        if not clips:
            clips = make_sentence_clips(seg["id"], seg["text"], duration, pauses.get(seg["id"].upper(), []))
        manifest["segments"].append({"id": seg["id"], "duration": round(duration, 3), "clips": clips})
    out = tts_dir / "sentence-boundaries.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def finalise_job() -> None:
    try:
        script = Path(__file__).with_name("voice_process.py")
        result = subprocess.run([sys.executable, str(script), str(WD)], check=False, capture_output=True, text=True)
        output = (result.stdout + "\n" + result.stderr).strip()
        with LOCK:
            if result.returncode == 0:
                manifest = final_manifest()
                RUNTIME["finalize"] = {
                    "status": "complete",
                    "message": "口播音频已交接给 Manim 流程",
                    "manifest": str(manifest.relative_to(WD)),
                    "log": output[-6000:],
                }
            else:
                RUNTIME["finalize"] = {
                    "status": "error", "message": "voice_process.py 处理失败", "log": output[-6000:],
                }
    except Exception as error:  # noqa: BLE001 - preserve a recoverable UI state
        with LOCK:
            RUNTIME["finalize"] = {"status": "error", "message": "voice_process.py 处理失败", "log": str(error)}


def start_finalise() -> tuple[bool, str]:
    with LOCK:
        if RUNTIME["recording"] is not None:
            return False, "请先完成当前录音"
        if current_segment_id() is not None:
            return False, "请先确认全部段落"
        if RUNTIME["finalize"]["status"] == "running":
            return False, "正在生成最终音频"
        RUNTIME["finalize"] = {"status": "running", "message": "正在修音、做一致性检查并生成字幕停顿时间线…"}
        threading.Thread(target=finalise_job, daemon=True).start()
    return True, "开始生成"


def public_state() -> dict[str, Any]:
    with LOCK:
        recording = RUNTIME["recording"]
        now = time.time()
        segs = []
        current = current_segment_id()
        # While re-recording an already approved segment, it must be the
        # visible card even if the normal cursor is another segment (or None
        # after the whole script was approved).
        active = recording["seg"] if recording else current
        for seg in SEGS:
            session = SESSION[seg["id"]]
            segs.append({
                **seg, "status": session["status"], "analysis": session.get("analysis"),
                "error": session.get("error"), "is_current": active == seg["id"],
            })
        return {
            "segments": segs, "current": current, "completed": current is None,
            "recording": recording,
            "countdown": max(0.0, recording["started_at"] - now) if recording else 0.0,
            "mic": dict(RUNTIME["mic"]), "mic_probing": bool(RUNTIME.get("mic_probing")),
            "finalize": dict(RUNTIME["finalize"]),
        }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, _format: str, *_args: Any) -> None:
        pass

    def _json(self, obj: dict[str, Any], code: int = HTTPStatus.OK) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _payload(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            return data if isinstance(data, dict) else {}
        except (ValueError, OSError):
            return {}

    def _audio(self, source: str, seg_id: str, clip_id: str | None = None) -> None:
        if find_segment(seg_id) is None:
            self._json({"error": "未知段落"}, HTTPStatus.NOT_FOUND)
            return
        if source == "raw":
            path = WD / "recordings" / f"{seg_id}.wav"
        elif source == "trim":
            path = WD / "trim" / f"{seg_id}.wav"
        elif source == "phrase" and clip_id and re.fullmatch(r"c\d{2}", clip_id):
            path = phrase_dir(seg_id) / f"{clip_id}.wav"
        else:
            self._json({"error": "未知音频"}, HTTPStatus.NOT_FOUND)
            return
        if not path.exists():
            self._json({"error": "音频不存在"}, HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Browsers cancel pending <audio> loads when a user switches clips.
            # The response is already complete from the application's point of view.
            return

    def do_GET(self) -> None:
        parts = [part for part in unquote(self.path.split("?", 1)[0]).split("/") if part]
        if not parts:
            body = PAGE.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        elif parts == ["api", "state"]:
            self._json(public_state())
        elif len(parts) in {4, 5} and parts[:2] == ["api", "audio"]:
            self._audio(parts[2], parts[3], parts[4] if len(parts) == 5 else None)
        else:
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parts = [part for part in unquote(self.path.split("?", 1)[0]).split("/") if part]
        if parts == ["api", "mic", "probe"]:
            run_mic_probe()
            self._json({"ok": True})
        elif parts == ["api", "record", "stop"]:
            ok, message = stop_recording()
            self._json({"ok": ok, "message": message}, HTTPStatus.OK if ok else HTTPStatus.CONFLICT)
        elif len(parts) == 3 and parts[:2] == ["api", "record"]:
            ok, message = start_record(parts[2])
            self._json({"ok": ok, "message": message}, HTTPStatus.OK if ok else HTTPStatus.CONFLICT)
        elif len(parts) == 3 and parts[:2] == ["api", "approve"]:
            ok, message = approve_segment(parts[2])
            self._json({"ok": ok, "message": message}, HTTPStatus.OK if ok else HTTPStatus.CONFLICT)
        elif len(parts) == 3 and parts[:2] == ["api", "alignment"]:
            ok, message = update_alignment(parts[2], self._payload())
            self._json({"ok": ok, "message": message}, HTTPStatus.OK if ok else HTTPStatus.CONFLICT)
        elif parts == ["api", "finalize"]:
            ok, message = start_finalise()
            self._json({"ok": ok, "message": message}, HTTPStatus.OK if ok else HTTPStatus.CONFLICT)
        else:
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)


PAGE = r"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>数解 AI · 口播录音室</title><style>
:root{color-scheme:dark;--paper:#12171c;--panel:#1b242c;--line:#33434f;--ink:#edf3f7;--muted:#a8b7c1;--blue:#66b9eb;--yellow:#f2c14e;--green:#69d38c;--red:#ff8181}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.65 ui-sans-serif,system-ui,"Noto Sans CJK SC",sans-serif}.shell{max-width:1120px;margin:auto;padding:26px 18px 54px}.top{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;border-bottom:1px solid var(--line);padding-bottom:20px}.eyebrow{color:var(--yellow);font-size:12px;letter-spacing:.12em;text-transform:uppercase}h1{margin:3px 0;font-size:27px;line-height:1.25}.sub{margin:0;color:var(--muted)}button{border:0;border-radius:8px;background:var(--blue);color:#06131b;font-weight:750;padding:9px 15px;cursor:pointer;font-size:14px}button:hover{filter:brightness(1.1)}button:disabled{background:#45525b;color:#94a0a7;cursor:not-allowed}.ghost{background:transparent;border:1px solid var(--line);color:var(--ink)}.danger{background:var(--red)}.device{min-width:270px;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px}.device-title{font-weight:700}.status{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--muted)}.dot{width:8px;height:8px;border-radius:50%;background:#75828a}.dot.ok{background:var(--green)}.dot.wait{background:var(--yellow)}.layout{display:grid;grid-template-columns:246px minmax(0,1fr);gap:22px;margin-top:24px}.steps{padding:0;margin:0;list-style:none}.steps li{display:flex;gap:10px;align-items:center;padding:10px 9px;border-left:2px solid #40505a;color:var(--muted)}.steps li.current{border-color:var(--yellow);color:var(--ink);background:#1c252b}.steps li.done{border-color:var(--green)}.stepnum{width:25px;height:25px;border-radius:50%;border:1px solid currentColor;text-align:center;line-height:23px;font-size:12px}.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:23px}.card+ .card{margin-top:14px}.label{font-size:12px;letter-spacing:.09em;color:var(--yellow);text-transform:uppercase}.script{font-size:20px;line-height:1.9;margin:12px 0 18px;white-space:pre-wrap}.guide{padding:12px 14px;border-left:3px solid var(--yellow);background:#222c33;color:#d6e0e4}.actions{display:flex;flex-wrap:wrap;gap:9px;margin-top:20px}.meta{font-size:13px;color:var(--muted)}.warn{border-color:#8c6d2d;background:#2b291e}.issues{margin:12px 0;padding-left:20px;color:#ffd092}.timeline{display:flex;height:10px;overflow:hidden;border-radius:5px;background:#3d4b53;margin:16px 0 10px}.clipbar{background:#3d87b3;border-right:1px solid #d8edf8}.clips{display:grid;gap:8px}.clip{padding:10px 12px;border:1px solid var(--line);border-radius:9px;background:#182027}.cliphead{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:var(--muted)}.cliptext{margin:5px 0}.clip audio{width:100%;height:32px}.ready{border-color:#3d8861}.finished{border-color:#3d8861;background:#17261f}.log{max-height:220px;overflow:auto;background:#0d1215;border-radius:8px;padding:12px;font:12px/1.5 ui-monospace,monospace;white-space:pre-wrap;color:#bad0bd}@media(max-width:760px){.top,.layout{display:block}.device{margin-top:16px;min-width:0}.layout{margin-top:16px}.steps{display:flex;overflow:auto;margin-bottom:16px}.steps li{min-width:max-content;border-left:0;border-bottom:2px solid #40505a}.steps li.current{border-color:var(--yellow)}}
</style></head><body><main class="shell"><header class="top"><div><div class="eyebrow">Voice input / Manim handoff</div><h1>口播录音室</h1><p class="sub">逐段确认，真实停顿即为后续字幕与动画的时间锚点。</p></div><aside class="device" id="device"></aside></header><div class="layout"><nav><ol class="steps" id="steps"></ol></nav><section id="content"></section></div></main><script>
const $=s=>document.querySelector(s);let snapshot=null;
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function post(url){const r=await fetch(url,{method:'POST'});const data=await r.json();if(!r.ok)alert(data.message||data.error||'操作失败');return data}
function device(m,probing){const cls=m.input_ready?'ok':m.available?'wait':'';const signal=m.signal_db===null||m.signal_db===undefined?'待检测':m.signal_db+' dB';return `<div class="device-title">🎙 ${esc(m.name||'CM40')}</div><div class="status"><i class="dot ${cls}"></i>${esc(m.message||'检测中')}</div><div class="meta">输入电平：${signal}</div><div class="actions"><button class="ghost" ${probing?'disabled':''} onclick="post('/api/mic/probe')">${probing?'检测中…':'检测输入（请说话）'}</button></div>`}
function steps(state){return state.segments.map((s,i)=>`<li class="${s.is_current?'current ':''}${s.status==='approved'?'done':''}"><span class="stepnum">${s.status==='approved'?'✓':i+1}</span><span>第 ${i+1} 段<br><small>${s.status==='approved'?'已确认':s.status==='review'?'待试听':'待录制'}</small></span></li>`).join('')}
function review(s){const a=s.analysis;const clips=a.clips||[];const bars=clips.map(c=>`<i class="clipbar" style="width:${Math.max(1,(c.end-c.start)/a.duration*100)}%" title="${c.start.toFixed(2)}–${c.end.toFixed(2)}s"></i>`).join('');const issues=(a.issues||[]).map(x=>`<li>${esc(x)}</li>`).join('');const blocked=(a.blocking||[]).length>0;return `<article class="card ${a.issues?.length?'warn':'ready'}"><div class="label">第 ${s.id.slice(1)} 段 · 试听与句级边界</div><p class="meta">裁剪后 ${a.duration}s · 语音占比 ${Math.round(a.speech_ratio*100)}% · 最长停顿 ${a.longest_pause}s</p><audio controls preload="metadata" src="/api/audio/trim/${s.id}"></audio><div class="timeline" title="每个蓝色块是一句（或自然语义短句）；分界来自真实静音结束点">${bars}</div><p class="meta">蓝色分界 = 真实停顿后的下一句起点。这里与最终 <code>tts/pauses.json</code> 使用同一阈值。</p>${issues?`<ul class="issues">${issues}</ul>`:''}<div class="clips">${clips.map((c,i)=>`<div class="clip"><div class="cliphead"><span>句 ${i+1} · ${c.start.toFixed(2)}–${c.end.toFixed(2)}s</span><span>${esc(c.id)}</span></div><div class="cliptext">${esc(c.text||'（无文本：疑似环境噪声触发的停顿）')}</div>${c.audio?`<audio controls preload="none" src="/api/audio/phrase/${s.id}/${c.audio}"></audio>`:''}</div>`).join('')}</div><div class="actions">${s.is_current?`${blocked?'<span class="meta">存在必须修复的问题；请重录此段。</span>':'<button onclick="post(\'/api/approve/'+s.id+'\')">这段满意，下一段</button>'}<button class="ghost" onclick="post('/api/record/${s.id}')">重新录制</button>`:`<span class="meta">已确认。若要重录，请重启本次会话后从此段重新确认。</span>`}</div></article>`}
function activeCard(s,state){if(state.recording&&state.recording.seg===s.id){const phase=state.recording.phase;const count=Math.ceil(state.countdown);return `<article class="card"><div class="label">第 ${s.id.slice(1)} 段 · ${phase==='countdown'?'准备':'录制中'}</div><div class="script">${esc(s.text)}</div><p class="guide">${phase==='countdown'?`准备 <span id="countdown">${count}</span>s 后开始。`: `请自然朗读；每句间停顿 0.3–0.5 秒。软上限 ${state.recording.cap}s。`}</p><div class="actions"><button class="danger" onclick="post('/api/record/stop')">${phase==='processing'?'正在分析…':'结束录音'}</button></div></article>`}if(s.status==='review')return review(s);return `<article class="card"><div class="label">第 ${s.id.slice(1)} 段 · 待录制</div><div class="script">${esc(s.text)}</div><div class="guide">面向 CM40，距离约 20–30cm。每段一口气完成；每句话自然停顿 0.3–0.5 秒。若念错，直接结束后重录本段。</div><p class="meta">建议时长约 ${(s.text.replaceAll(' ','').length*.195).toFixed(0)} 秒；录音软上限 ${Math.floor(s.text.replaceAll(' ','').length*.195*1.15)+10} 秒。</p>${s.error?`<p class="issues">${esc(s.error)}</p>`:''}<div class="actions"><button onclick="post('/api/record/${s.id}')" ${!state.mic.available?'disabled':''}>开始录制</button></div></article>`}
function finished(state){const f=state.finalize;if(f.status==='running')return `<article class="card"><div class="label">最终交接</div><h2>正在修音并生成停顿时间线…</h2><p class="meta">会生成 <code>tts/sN.wav</code>、<code>tts/pauses.json</code> 与一致性报告。</p></article>`;if(f.status==='complete')return `<article class="card finished"><div class="label">已交接</div><h2>可以进入 Manim 场景制作</h2><p>最终音频、逐段时长和句级边界已经就绪：<code>${esc(f.manifest)}</code></p>${f.log?`<pre class="log">${esc(f.log)}</pre>`:''}</article>`;if(f.status==='error')return `<article class="card warn"><div class="label">交接失败</div><h2>${esc(f.message)}</h2><pre class="log">${esc(f.log||'')}</pre><button onclick="post('/api/finalize')">重试生成</button></article>`;return `<article class="card"><div class="label">全部段落已确认</div><h2>生成后续流程需要的音频文件</h2><p>将按现有 <code>voice_process.py</code> 做去噪、响度与频谱一致性处理，并将实际停顿写入 <code>tts/pauses.json</code>。</p><button onclick="post('/api/finalize')">生成制作文件</button></article>`}
let lastRenderKey='';function updateLive(state){const countdown=$('#countdown');if(countdown)countdown.textContent=Math.ceil(state.countdown)}function render(state){snapshot=state;const {countdown,...stable}=state;const key=JSON.stringify(stable);if(key===lastRenderKey){updateLive(state);return}lastRenderKey=key;$('#device').innerHTML=device(state.mic,state.mic_probing);$('#steps').innerHTML=steps(state);const active=state.segments.find(s=>s.is_current);$('#content').innerHTML=active?activeCard(active,state):finished(state);updateLive(state)}
async function refresh(){try{render(await (await fetch('/api/state',{cache:'no-store'})).json())}catch(e){console.error(e)}}setInterval(refresh,800);refresh();
</script></body></html>"""

# Keep the application code separate from the Web editor.  In particular, this
# makes the sentence-block alignment controls practical to maintain without
# touching recording logic whenever the interaction is refined.
PAGE = Path(__file__).with_name("voice_studio.html").read_text(encoding="utf-8")


def main() -> None:
    global WD, SEGS, PORT, MIC_HINT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("workdir", type=Path, help="任意含 tts.txt 的 shipinhao 工作目录")
    parser.add_argument("--port", type=int, default=PORT, help=f"监听端口（默认 {PORT}）")
    parser.add_argument("--mic", default=MIC_HINT, help="录音设备名称匹配词（默认 CM40）")
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()
    WD = args.workdir.resolve()
    PORT = args.port
    MIC_HINT = args.mic
    try:
        SEGS = load_segments(WD / "tts.txt")
    except ValueError as error:
        parser.error(str(error))
    (WD / "recordings").mkdir(exist_ok=True)
    (WD / "trim").mkdir(exist_ok=True)
    initialise_state()
    run_mic_probe()
    url = f"http://127.0.0.1:{PORT}"
    print(f"口播录音室：{url}（{len(SEGS)} 段，台本 {WD / 'tts.txt'}）")
    if not args.no_open:
        threading.Thread(target=lambda: subprocess.run(["xdg-open", url], check=False), daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
