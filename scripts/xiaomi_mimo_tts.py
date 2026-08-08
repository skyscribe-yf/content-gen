#!/usr/bin/env python3
"""Xiaomi MiMo TTS client for 视频号口播.

Uses shell env XIAOMI_MIMO_API_KEY (or MIMO_API_KEY).
API: https://api.xiaomimimo.com/v1/chat/completions

Modes:
  1) Built-in voice  — model mimo-v2.5-tts + --voice
  2) Voice design    — model mimo-v2.5-tts-voicedesign + --design "自然语言描述"
  3) Voice clone     — model mimo-v2.5-tts-voiceclone + --clone-audio sample.wav

Examples:
  # 预置音色
  python scripts/xiaomi_mimo_tts.py \\
    --text-file shipinhao/tts.txt --out voice.wav --voice 白桦

  # 自然语言定制音色（推荐）
  python scripts/xiaomi_mimo_tts.py \\
    --text-file shipinhao/tts.txt --out voice.wav \\
    --design "沉稳的中年中国男声，中低音，知识科普旁白……"

  # 短句试音色
  python scripts/xiaomi_mimo_tts.py \\
    --text "学习率调了一整天，loss还是抖？" \\
    --out trial.wav --design-file shipinhao/voice-design.txt
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.xiaomimimo.com/v1/chat/completions"

MODEL_BUILTIN = "mimo-v2.5-tts"
MODEL_DESIGN = "mimo-v2.5-tts-voicedesign"
MODEL_CLONE = "mimo-v2.5-tts-voiceclone"

# Built-in: mimo_default, 冰糖, 茉莉, 苏打, 白桦, Mia, Chloe, Milo, Dean
DEFAULT_VOICE = "白桦"

# 预置模式：user 消息 = 演绎风格（不是音色本体）
DEFAULT_STYLE = (
    "用沉稳清晰的中文知识科普旁白，语速略快、吐字清楚，"
    "像资深工程师讲解，不要播音腔，不要夸张情绪。"
)

# 音色设计模式：user 消息 = 音色本体描述（越具体越好）
DEFAULT_DESIGN = """\
沉稳的中年中国男声，知识科普短视频旁白。
音色：中低音，干净不沙哑，胸腔共鸣适中，不尖不闷。
语速：适中略快，吐字清晰，句末不拖腔。
情绪：克制、可信、冷静，像资深工程师在白板前讲解，不要播音腔，不要激情演讲，不要卖萌，不要方言。
节奏：重点词（如「方向」「尺度」）可轻微加重，疑问句自然上扬。
"""


def _api_key() -> str:
    key = os.environ.get("XIAOMI_MIMO_API_KEY") or os.environ.get("MIMO_API_KEY")
    if not key:
        raise SystemExit(
            "Missing XIAOMI_MIMO_API_KEY (or MIMO_API_KEY) in environment."
        )
    return key


def _load_spoken_text(args: argparse.Namespace) -> str:
    if args.text_file:
        raw = Path(args.text_file).read_text(encoding="utf-8")
    elif args.text:
        raw = args.text
    else:
        raise SystemExit("Provide --text or --text-file")
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if args.keep_newlines:
        return "\n".join(lines)
    return "".join(lines)


def _load_design(args: argparse.Namespace) -> str | None:
    if args.design_file:
        return Path(args.design_file).read_text(encoding="utf-8").strip()
    if args.design:
        return args.design.strip()
    return None


def _data_uri(path: Path) -> str:
    raw = path.read_bytes()
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        # wav/mp3 common cases
        suf = path.suffix.lower()
        mime = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
        }.get(suf, "application/octet-stream")
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def synthesize(
    text: str,
    *,
    model: str,
    user_content: str,
    voice: str | None = None,
    clone_uri: str | None = None,
    audio_format: str = "wav",
    timeout: int = 300,
) -> bytes:
    """Return raw audio bytes.

    MiMo convention:
      user message      = style / voice-design prompt / (empty for clone)
      assistant message = text to speak
    """
    key = _api_key()
    messages = [
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": text},
    ]

    if model == MODEL_DESIGN:
        audio: dict = {
            "format": audio_format,
            "optimize_text_preview": True,
        }
    elif model == MODEL_CLONE:
        if not clone_uri:
            raise SystemExit("voiceclone requires --clone-audio")
        audio = {"format": audio_format, "voice": clone_uri}
        messages[0]["content"] = user_content or ""
    else:
        # built-in
        audio = {"format": audio_format, "voice": voice or DEFAULT_VOICE}

    payload = {
        "model": model,
        "messages": messages,
        "audio": audio,
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "api-key": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"MiMo TTS HTTP {e.code}: {err[:2000]}") from e

    try:
        b64 = body["choices"][0]["message"]["audio"]["data"]
    except (KeyError, IndexError, TypeError) as e:
        raise SystemExit(
            f"Unexpected response shape: {json.dumps(body, ensure_ascii=False)[:1500]}"
        ) from e

    return base64.b64decode(b64)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Xiaomi MiMo TTS → audio file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
modes:
  default              built-in voice (--voice 白桦)
  --design "..."       natural-language voice design
  --design-file PATH   same, from file
  --clone-audio PATH   clone from a short reference clip
        """.strip(),
    )
    p.add_argument("--text", help="Inline text to speak")
    p.add_argument("--text-file", help="Path to tts.txt")
    p.add_argument("--out", default="voice.wav", help="Output path")
    p.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Built-in voice id (default: {DEFAULT_VOICE})",
    )
    p.add_argument(
        "--design",
        help="Natural-language voice design prompt (switches to voicedesign model)",
    )
    p.add_argument(
        "--design-file",
        help="Read voice design prompt from file",
    )
    p.add_argument(
        "--clone-audio",
        help="Reference audio for voice clone (switches to voiceclone model)",
    )
    p.add_argument(
        "--style",
        default=DEFAULT_STYLE,
        help="Delivery style for built-in / clone modes (user message)",
    )
    p.add_argument(
        "--model",
        default=None,
        help="Override model id (normally auto-selected)",
    )
    p.add_argument(
        "--format",
        dest="audio_format",
        default="wav",
        choices=["wav", "mp3", "pcm16"],
        help="Audio format (default: wav)",
    )
    p.add_argument(
        "--keep-newlines",
        action="store_true",
        help="Keep newlines between paragraphs",
    )
    p.add_argument(
        "--print-default-design",
        action="store_true",
        help="Print the default voice-design prompt and exit",
    )
    args = p.parse_args()

    if args.print_default_design:
        sys.stdout.write(DEFAULT_DESIGN)
        return

    text = _load_spoken_text(args)
    if not text.strip():
        raise SystemExit("Empty text")

    design = _load_design(args)
    clone_path = Path(args.clone_audio) if args.clone_audio else None

    if args.model:
        model = args.model
    elif clone_path:
        model = MODEL_CLONE
    elif design is not None:
        model = MODEL_DESIGN
    else:
        model = MODEL_BUILTIN

    if model == MODEL_DESIGN:
        user_content = design if design else DEFAULT_DESIGN
        voice = None
        clone_uri = None
        mode_note = "design"
    elif model == MODEL_CLONE:
        if not clone_path or not clone_path.is_file():
            raise SystemExit(f"--clone-audio not found: {clone_path}")
        user_content = args.style
        voice = None
        clone_uri = _data_uri(clone_path)
        mode_note = f"clone:{clone_path.name}"
    else:
        user_content = args.style
        voice = args.voice
        clone_uri = None
        mode_note = f"builtin:{voice}"

    fmt = "wav" if args.audio_format == "pcm16" else args.audio_format
    print(
        f"model={model} mode={mode_note} chars={len(text)} → {args.out}",
        file=sys.stderr,
    )
    if model == MODEL_DESIGN:
        preview = user_content.replace("\n", " ")[:80]
        print(f"design: {preview}…", file=sys.stderr)

    audio = synthesize(
        text,
        model=model,
        user_content=user_content,
        voice=voice,
        clone_uri=clone_uri,
        audio_format=fmt,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    print(f"saved {out} ({out.stat().st_size} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
