#!/usr/bin/env python3
"""MiniMax TTS 用于视频号口播（TTS 模式）。

Uses shell env MINIMAX_API_KEY.
API (国内版): https://api.minimaxi.com

默认音色：MiniMax 预设精英男声 male-qn-jingying（2026-08-26 用户拍板为默认，
不再默认克隆作者音色）。克隆模式仍可用：
  1. 上传参考音频  POST /v1/files/upload   (mp3/m4a/wav, 10s~5min, ≤20MB)
  2. 音色克隆      POST /v1/voice_clone    → 生成 voice_id（¥9.9 在首次合成时收取）
  3. 逐段合成      POST /v1/t2a_v2         → speech-2.8-turbo 克隆音色朗读

voice_id 缓存在参考音频旁 (.minimax_voice_id)，重复运行跳过克隆。
克隆音色 7 天内使用过即永久保留；7 天未用会被删除（需重新克隆）。

表现力控制（MiniMax 无自然语言指令位）:
  - 文本内插拟声标签: (laughs) (sighs) (breath) (gasps) (pause) 等，2.8 系列支持
  - --emotion 参数: calm / happy / sad / angry / fearful / surprised / fluent 等

用法:
  # 默认：精英男声（不传音色参数）
  python scripts/minimax_tts.py \\
    --text-file shipinhao/tts.txt --out shipinhao/tts/full.wav --subtitle

  # 显式指定预设音色
  python scripts/minimax_tts.py \\
    --text "大家好" --out trial.wav --voice-id male-qn-jingying

  # 克隆作者音色（旧默认，仅当明确要求时）
  python scripts/minimax_tts.py \\
    --text-file shipinhao/tts.txt --out shipinhao/tts/full.wav \\
    --clone-audio branding/my-voice-denoised.wav
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

API_BASE = "https://api.minimaxi.com"
MODEL = "speech-2.8-turbo"  # 默认 turbo（2026-08-12 用户定稿：便宜且克隆+时间戳兼容）；hd 用 --model speech-2.8-hd


def _api_key() -> str:
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        raise SystemExit("Missing MINIMAX_API_KEY in environment.")
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def _upload(api_key: str, path: Path) -> int:
    url = f"{API_BASE}/v1/files/upload"
    with open(path, "rb") as f:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            data={"purpose": "voice_clone"},
            files={"file": (path.name, f)},
            timeout=120,
        )
    body = resp.json()
    if resp.status_code != 200 or body.get("base_resp", {}).get("status_code") != 0:
        raise SystemExit(
            f"MiniMax upload failed ({resp.status_code}): "
            f"{json.dumps(body, ensure_ascii=False)[:1000]}"
        )
    return body["file"]["file_id"]


def _clone(api_key: str, file_id: int, voice_id: str) -> None:
    url = f"{API_BASE}/v1/voice_clone"
    payload = {"file_id": file_id, "voice_id": voice_id}
    resp = requests.post(url, headers=_headers(), json=payload, timeout=300)
    body = resp.json()
    status = body.get("base_resp", {}).get("status_code")
    if status != 0:
        msg = body.get("base_resp", {}).get("status_msg", "")
        hint = (
            "（错误 2038 = 无复刻权限，请到 MiniMax 开放平台检查账号实名/认证状态）"
            if status == 2038
            else ""
        )
        raise SystemExit(f"MiniMax voice clone failed ({status}): {msg} {hint}")


def _get_voice_id(clone_path: Path) -> str:
    """Clone once, cache voice_id next to the reference audio."""
    cache = clone_path.parent / ".minimax_voice_id"
    if cache.is_file():
        vid = cache.read_text(encoding="utf-8").strip()
        if vid:
            return vid

    api_key = _api_key()
    print(f"uploading {clone_path.name}…", file=sys.stderr)
    file_id = _upload(api_key, clone_path)
    voice_id = "author-video-voice-01"  # 8-256 chars, starts with letter
    print(f"cloning (voice_id={voice_id})…", file=sys.stderr)
    _clone(api_key, file_id, voice_id)
    cache.write_text(voice_id, encoding="utf-8")
    print(
        f"cloned OK — voice_id cached at {cache}（首次合成收取 ¥9.9 克隆费）",
        file=sys.stderr,
    )
    return voice_id


def synthesize(
    text: str,
    *,
    model: str = MODEL,
    voice_id: str,
    emotion: str | None = None,
    speed: float = 1.0,
    pitch: float = 0.0,
    audio_format: str = "wav",
    sample_rate: int = 24000,
    subtitle: bool = False,
    timeout: int = 300,
) -> tuple[bytes, list | None]:
    """Return (audio bytes, subtitle list or None).
    subtitle=True 时请求句子级时间戳（subtitle_file，毫秒），供整段生成后切分。
    1 汉字按 2 字符计费。pitch 单位半音（-12~+12，正值更亮）。"""
    voice_setting: dict = {"voice_id": voice_id, "speed": speed, "vol": 1.0, "pitch": int(pitch)}
    if emotion:
        voice_setting["emotion"] = emotion
    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "subtitle_enable": subtitle,
        "voice_setting": voice_setting,
        "audio_setting": {
            "format": audio_format,
            "sample_rate": sample_rate,
            "channel": 1,
        },
    }
    resp = requests.post(
        f"{API_BASE}/v1/t2a_v2", headers=_headers(), json=payload, timeout=timeout
    )
    body = resp.json()
    status = body.get("base_resp", {}).get("status_code")
    if status != 0:
        raise SystemExit(
            f"MiniMax T2A failed ({status}): "
            f"{body.get('base_resp', {}).get('status_msg', '')} "
            f"{json.dumps(body, ensure_ascii=False)[:500]}"
        )
    try:
        audio = bytes.fromhex(body["data"]["audio"])
    except (KeyError, ValueError) as e:
        raise SystemExit(
            f"Unexpected response: {json.dumps(body, ensure_ascii=False)[:1000]}"
        ) from e
    sub = None
    if subtitle:
        sf = body.get("data", {}).get("subtitle_file")
        if not sf:
            raise SystemExit("subtitle_enable=true but no subtitle_file in response")
        sub = requests.get(sf, timeout=60).json()
    return audio, sub


def main() -> None:
    p = argparse.ArgumentParser(
        description="MiniMax TTS (voice clone) → audio file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--text", help="Inline text to speak")
    p.add_argument("--text-file", help="Path to tts.txt (每行一段)")
    p.add_argument("--out", default="voice.wav", help="Output path")
    p.add_argument(
        "--model",
        default=MODEL,
        help=f"MiniMax 模型（默认 {MODEL}；speech-2.8-turbo 更便宜）",
    )
    p.add_argument(
        "--clone-audio",
        help="Reference audio for voice clone (10s~5min, mp3/m4a/wav, ≤20MB)",
    )
    p.add_argument(
        "--voice-id",
        default="male-qn-jingying",
        help="MiniMax 预设音色 voice_id（默认 male-qn-jingying 精英男声，2026-08-26 用户拍板）；与 --clone-audio 互斥",
    )
    p.add_argument(
        "--emotion",
        choices=["calm", "happy", "sad", "angry", "fearful", "surprised", "fluent"],
        help="情绪参数（默认不设，模型自动判断）",
    )
    p.add_argument("--speed", type=float, default=1.0, help="语速 0.5-2.0 (默认 1.0)")
    p.add_argument("--pitch", type=float, default=0.0,
                   help="音高偏移（半音，-12~+12；正=更亮/更高，默认 0）")
    p.add_argument(
        "--format",
        dest="audio_format",
        default="wav",
        choices=["wav", "mp3", "pcm", "flac"],
    )
    p.add_argument("--sample-rate", type=int, default=24000, help="采样率 (默认 24000)")
    p.add_argument("--subtitle", action="store_true",
                   help="请求 word 级时间戳，保存到 <out>.subtitle.json（整段生成后按时间戳切分用）")
    args = p.parse_args()

    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8").strip()
    elif args.text:
        text = args.text.strip()
    else:
        raise SystemExit("Provide --text or --text-file")

    if args.voice_id and args.clone_audio:
        raise SystemExit("--voice-id 与 --clone-audio 互斥，二选一")
    if args.clone_audio:
        clone_path = Path(args.clone_audio)
        if not clone_path.is_file():
            raise SystemExit(f"--clone-audio not found: {clone_path}")
        voice_id = _get_voice_id(clone_path)
    else:
        voice_id = args.voice_id  # 默认 male-qn-jingying 精英男声
    print(
        f"model={args.model} voice={voice_id} chars={len(text)} speed={args.speed} "
        f"pitch={args.pitch} → {args.out}",
        file=sys.stderr,
    )

    audio, sub = synthesize(
        text,
        model=args.model,
        voice_id=voice_id,
        emotion=args.emotion,
        speed=args.speed,
        pitch=args.pitch,
        audio_format=args.audio_format,
        sample_rate=args.sample_rate,
        subtitle=args.subtitle,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    if sub is not None:
        (out.with_name(out.stem + ".subtitle.json")).write_text(
            json.dumps(sub, ensure_ascii=False), encoding="utf-8"
        )
        print(f"subtitle saved: {out.with_name(out.stem + '.subtitle.json')} ({len(sub)} words)", file=sys.stderr)
    print(f"saved {out} ({out.stat().st_size} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
