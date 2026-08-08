#!/usr/bin/env python3
"""Render 微信视频号竖屏成片 from timeline.json + voice audio.

Pipeline (Linux, no 剪映):
  1. Pillow: build 1080×1920 scene frames (dark bg + centered card + titles)
  2. Write SRT subtitles from paragraphs
  3. ffmpeg: concat stills by duration + mux audio + burn subs → mp4

Example:
  python scripts/shipinhao_render.py \\
    --timeline content/2026-07-10-优化器/shipinhao/timeline.json \\
    --audio content/2026-07-10-优化器/shipinhao/voice.wav \\
    --out content/2026-07-10-优化器/shipinhao/final.mp4
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BG = (0x1A, 0x1A, 0x2E)
ORANGE = (0xFF, 0x6B, 0x35)
WHITE = (255, 255, 255)
CYAN = (0x58, 0xC4, 0xDD)
MUTED = (180, 185, 200)

# Three-band layout — text never sits on the illustration
# ┌──────────── top band: brand + title ────────────┐  y=0..TOP
# │              middle: image only                   │  y=TOP..BOTTOM
# └──────── bottom band: hard-subtitles only ────────┘  y=BOTTOM..H
TOP_BAND = 260
BOTTOM_BAND = 320
IMAGE_TOP = TOP_BAND
IMAGE_BOTTOM = H - BOTTOM_BAND
IMAGE_AREA_H = IMAGE_BOTTOM - IMAGE_TOP  # ~1340
# Use nearly full width; source cards are ~1254px so we stay near 1:1
IMAGE_MAX_W = 1040
IMAGE_MAX_H = min(1100, IMAGE_AREA_H - 20)

# Full-bleed 9:16 frames: reserve bottom strip only for burned subtitles
SUB_SAFE_H = 300  # px from bottom — ASS lives here, never over main art

# Encode: one-pass, high bitrate (still-image slideshows under-allocate bits with CRF-only)
VIDEO_CRF = "14"
VIDEO_MAXRATE = "8M"
VIDEO_BUFSIZE = "16M"
VIDEO_PRESET = "slow"
AUDIO_BITRATE = "192k"


def _find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else None,
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else None,
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ]
    for path in candidates:
        if path and Path(path).is_file():
            try:
                # TTC: index 0 usually SC/JP depending on file; NotoSansCJK works with 0
                return ImageFont.truetype(path, size=size, index=0)
            except OSError:
                continue
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        cur = ""
        for ch in para:
            trial = cur + ch
            bbox = draw.textbbox((0, 0), trial, font=font)
            if bbox[2] - bbox[0] <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines or [""]


def _text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    cx: int,
    y: int,
    fill: tuple,
    max_w: int,
    line_gap: int = 12,
    stroke_fill: tuple | None = (0, 0, 0),
    stroke_width: int = 2,
) -> int:
    lines = _wrap(draw, text, font, max_w)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = cx - tw // 2
        kwargs = {"font": font, "fill": fill}
        if stroke_fill and stroke_width:
            kwargs["stroke_width"] = stroke_width
            kwargs["stroke_fill"] = stroke_fill
        draw.text((x, y), line, **kwargs)
        y += th + line_gap
    return y


def _draw_brand(draw: ImageDraw.ImageDraw, brand: str, font: ImageFont.ImageFont) -> None:
    bb = draw.textbbox((0, 0), brand, font=font)
    bw = bb[2] - bb[0]
    draw.text((W - bw - 36, 28), brand, font=font, fill=MUTED)


def _draw_top_title(
    draw: ImageDraw.ImageDraw,
    title: str,
    subtitle: str,
    font_title: ImageFont.ImageFont,
    font_sub: ImageFont.ImageFont,
    *,
    title_color: tuple = WHITE,
) -> None:
    """Titles live only in the top band — never over the illustration."""
    y = 72
    if title:
        y = _text_block(
            draw,
            title,
            font_title,
            W // 2,
            y,
            title_color,
            W - 100,
            line_gap=10,
            stroke_width=0,
            stroke_fill=None,
        )
    if subtitle:
        _text_block(
            draw,
            subtitle,
            font_sub,
            W // 2,
            y + 16,
            CYAN,
            W - 120,
            line_gap=8,
            stroke_width=0,
            stroke_fill=None,
        )


def _fit_cover(src: Image.Image, tw: int, th: int) -> Image.Image:
    """Scale image to cover tw×th (center crop). Prefer for native 9:16 sources."""
    src = src.convert("RGB")
    sw, sh = src.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    src = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return src.crop((left, top, left + tw, top + th))


def _bottom_sub_scrim(height: int = SUB_SAFE_H) -> Image.Image:
    """Dark gradient from transparent → solid for subtitle legibility."""
    band = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    px = band.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        # ease-in: mostly transparent at top of band, solid near bottom
        a = int(255 * (t ** 1.6))
        for x in range(W):
            px[x, y] = (12, 12, 22, a)
    return band


def render_scene(scene: dict, base_dir: Path, out_path: Path) -> None:
    """Render one 1080×1920 frame."""
    kind = scene.get("kind", "image")
    top_title = scene.get("title", "")
    subtitle = scene.get("subtitle", "")
    brand = scene.get("brand", "数解AI")

    font_brand = _find_font(26, bold=False)
    font_title = _find_font(52, bold=True)
    font_sub = _find_font(32, bold=False)
    font_hero = _find_font(72, bold=True)
    font_body = _find_font(42, bold=True)

    # --- full-bleed 9:16 art (phone native) ---
    if kind == "fullbleed":
        path = base_dir / scene["image"]
        if not path.is_file():
            raise FileNotFoundError(path)
        # Fill full canvas; bottom scrim only for ASS (no extra titles — art already has them)
        art = _fit_cover(Image.open(path), W, H)
        canvas = art.convert("RGBA")
        # no bottom black bar — subs are outline-only over the art
        draw = ImageDraw.Draw(canvas)
        bb = draw.textbbox((0, 0), brand, font=font_brand)
        bw = bb[2] - bb[0]
        # semi-transparent brand chip
        draw.rounded_rectangle(
            [W - bw - 52, 28, W - 28, 28 + 36],
            radius=8,
            fill=(10, 10, 18, 140),
        )
        draw.text((W - bw - 40, 32), brand, font=font_brand, fill=MUTED + (255,))
        canvas.convert("RGB").save(out_path, "PNG", optimize=True)
        return

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    _draw_brand(draw, brand, font_brand)

    if kind == "title":
        y = 200
        if top_title:
            y = _text_block(
                draw,
                top_title,
                font_hero,
                W // 2,
                y,
                ORANGE,
                W - 100,
                line_gap=14,
                stroke_width=0,
                stroke_fill=None,
            )
        if subtitle:
            y = _text_block(
                draw,
                subtitle,
                font_sub,
                W // 2,
                y + 28,
                WHITE,
                W - 140,
                stroke_width=0,
                stroke_fill=None,
            )
        if scene.get("image"):
            _paste_card_in_box(
                img,
                base_dir / scene["image"],
                box=(70, max(y + 48, IMAGE_TOP), W - 70, IMAGE_BOTTOM),
            )

    elif kind == "text":
        # Full-screen text card; bottom reserved for subs
        box_top = 200
        box_bot = H - SUB_SAFE_H - 40
        margin = 70
        draw.rounded_rectangle(
            [margin, box_top, W - margin, box_bot],
            radius=28,
            outline=CYAN,
            width=3,
            fill=(24, 24, 42),
        )
        y = box_top + 100
        if top_title:
            y = _text_block(
                draw,
                top_title,
                font_title,
                W // 2,
                y,
                ORANGE,
                W - 200,
                stroke_width=0,
                stroke_fill=None,
            )
            y += 40
        body = scene.get("body", "")
        if body:
            _text_block(
                draw,
                body,
                font_body,
                W // 2,
                y,
                WHITE,
                W - 220,
                line_gap=28,
                stroke_width=0,
                stroke_fill=None,
            )
    else:
        # Image scene: title in top band, image only in middle, bottom empty for subs
        _draw_top_title(draw, top_title, subtitle, font_title, font_sub)
        if scene.get("image"):
            _paste_card_in_box(
                img,
                base_dir / scene["image"],
                box=(50, IMAGE_TOP, W - 50, IMAGE_BOTTOM),
            )
        draw.line([(80, TOP_BAND - 8), (W - 80, TOP_BAND - 8)], fill=(40, 45, 70), width=1)
        draw.line([(80, IMAGE_BOTTOM + 8), (W - 80, IMAGE_BOTTOM + 8)], fill=(40, 45, 70), width=1)

    img.save(out_path, "PNG", optimize=True)


def _paste_card_in_box(
    canvas: Image.Image,
    path: Path,
    box: tuple[int, int, int, int],
) -> None:
    """Fit illustration inside box, centered — never leave the box."""
    if not path.is_file():
        raise FileNotFoundError(path)
    left, top, right, bottom = box
    max_w = max(1, right - left)
    max_h = max(1, bottom - top)
    # clamp to global image max
    max_w = min(max_w, IMAGE_MAX_W)
    max_h = min(max_h, IMAGE_MAX_H)

    card = Image.open(path).convert("RGB")
    card.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

    # rounded-ish shadow plate behind card
    cx = (left + right) // 2
    cy = (top + bottom) // 2
    x = cx - card.width // 2
    y = cy - card.height // 2

    # soft border plate
    pad = 10
    plate = Image.new("RGB", (card.width + pad * 2, card.height + pad * 2), (28, 30, 48))
    canvas.paste(plate, (x - pad, y - pad))
    canvas.paste(card, (x, y))


def _audio_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def _allocate_durations(scenes: list[dict], total: float) -> list[float]:
    weights = []
    for s in scenes:
        if "duration" in s:
            weights.append(None)  # fixed later
        else:
            w = float(s.get("weight", 1.0))
            weights.append(w)
    fixed_sum = sum(float(s["duration"]) for s in scenes if "duration" in s)
    free = max(total - fixed_sum, 0.5)
    free_w = sum(w for w in weights if w is not None) or 1.0
    durs = []
    for s, w in zip(scenes, weights):
        if "duration" in s:
            durs.append(float(s["duration"]))
        else:
            durs.append(free * (w / free_w))
    # renormalize tiny drift
    scale = total / sum(durs)
    return [d * scale for d in durs]


def _srt_timestamp(sec: float) -> str:
    if sec < 0:
        sec = 0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - math.floor(sec)) * 1000))
    if ms >= 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _wrap_sub_text(text: str, max_chars: int = 20, max_lines: int = 6) -> list[str]:
    """Wrap Chinese/mixed text; keep full content (no silent truncation)."""
    text = text.strip()
    lines: list[str] = []
    cur = ""
    for ch in text:
        cur += ch
        if len(cur) >= max_chars and ch in "，。？！、；,:.?! ":
            lines.append(cur.strip())
            cur = ""
        elif len(cur) >= max_chars + 2:
            lines.append(cur)
            cur = ""
    if cur.strip():
        lines.append(cur.strip())
    if not lines:
        return [text]
    # if still too many lines, widen rather than drop text
    if len(lines) > max_lines:
        wider = max_chars + 4
        return _wrap_sub_text(text, max_chars=wider, max_lines=max_lines + 2)
    return lines

def write_srt(subs: list[dict], path: Path) -> None:
    """subs: [{start, end, text}, ...] — kept for debugging."""
    parts = []
    for i, item in enumerate(subs, 1):
        parts.append(str(i))
        parts.append(f"{_srt_timestamp(item['start'])} --> {_srt_timestamp(item['end'])}")
        parts.append("\n".join(_wrap_sub_text(item["text"])))
        parts.append("")
    path.write_text("\n".join(parts), encoding="utf-8")


def _ass_timestamp(sec: float) -> str:
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))  # centiseconds
    if cs >= 100:
        cs = 0
        s += 1
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass(subs: list[dict], path: Path) -> None:
    """ASS with PlayRes 1080×1920 so MarginV maps to real bottom band."""
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,36,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,2,48,48,72,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for item in subs:
        lines = _wrap_sub_text(item["text"], max_chars=20, max_lines=6)
        # ASS line break
        body = r"\N".join(lines)
        events.append(
            f"Dialogue: 0,{_ass_timestamp(item['start'])},{_ass_timestamp(item['end'])},"
            f"Default,,0,0,0,,{body}"
        )
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def build_subs_from_paragraphs(paragraphs: list[str], total: float) -> list[dict]:
    weights = [max(len(p), 1) for p in paragraphs]
    tw = sum(weights)
    t = 0.0
    subs = []
    for p, w in zip(paragraphs, weights):
        dur = total * (w / tw)
        subs.append({"start": t, "end": t + dur, "text": p})
        t += dur
    if subs:
        subs[-1]["end"] = total
    return subs


def render(timeline: dict, audio: Path, out_mp4: Path, work: Path) -> None:
    base_dir = Path(timeline.get("base_dir", ".")).resolve()
    scenes = timeline["scenes"]
    total = _audio_duration(audio)
    durs = _allocate_durations(scenes, total)

    frames_dir = work / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    frame_paths = []
    for i, (scene, dur) in enumerate(zip(scenes, durs)):
        fp = frames_dir / f"scene_{i:02d}.png"
        print(f"  frame {i}: {dur:.2f}s  {scene.get('title') or scene.get('kind')}", file=sys.stderr)
        render_scene(scene, base_dir, fp)
        frame_paths.append((fp, dur))

    # concat demuxer list
    list_path = work / "concat.txt"
    with list_path.open("w", encoding="utf-8") as f:
        for fp, dur in frame_paths:
            f.write(f"file '{fp.resolve()}'\n")
            f.write(f"duration {dur:.4f}\n")
        # concat quirk: repeat last file
        f.write(f"file '{frame_paths[-1][0].resolve()}'\n")

    # subtitles — ASS with real 1080×1920 PlayRes (SRT+force_style uses 384×288 and mis-places MarginV)
    ass_path = work / "subs.ass"
    srt_path = work / "subs.srt"  # debug copy
    if timeline.get("subtitles"):
        subs = []
        t = 0.0
        for item, dur in zip(timeline["subtitles"], durs[: len(timeline["subtitles"])]):
            text = item if isinstance(item, str) else item.get("text", "")
            d = item.get("duration", dur) if isinstance(item, dict) else dur
            subs.append({"start": t, "end": t + d, "text": text})
            t += d
        if abs(t - total) > 0.05 and subs:
            scale = total / t
            for s in subs:
                s["start"] *= scale
                s["end"] *= scale
            subs[-1]["end"] = total
    elif timeline.get("paragraphs"):
        subs = build_subs_from_paragraphs(timeline["paragraphs"], total)
    else:
        texts = [
            s.get("subtitle") or s.get("title") or s.get("body") or "" for s in scenes
        ]
        subs = build_subs_from_paragraphs(texts, total)
    write_ass(subs, ass_path)
    write_srt(subs, srt_path)

    # Single-pass: concat frames + burn ASS + mux audio (avoid double H.264)
    ass_esc = (
        str(ass_path.resolve())
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    # keyint=30: refresh full frame every 1s so still cards stay sharp
    x264_params = "keyint=30:min-keyint=30:scenecut=0:ref=4:aq-mode=3"
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-i",
        str(audio),
        "-vf",
        f"fps=30,format=yuv420p,ass={ass_esc}",
        "-c:v",
        "libx264",
        "-preset",
        VIDEO_PRESET,
        "-crf",
        VIDEO_CRF,
        "-maxrate",
        VIDEO_MAXRATE,
        "-bufsize",
        VIDEO_BUFSIZE,
        "-x264-params",
        x264_params,
        "-c:a",
        "aac",
        "-b:a",
        AUDIO_BITRATE,
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    print(
        f"encoding HQ single-pass (crf={VIDEO_CRF}, maxrate={VIDEO_MAXRATE}, preset={VIDEO_PRESET})…",
        file=sys.stderr,
    )
    subprocess.check_call(cmd)
    print(f"done → {out_mp4}", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="Render 视频号 9:16 mp4")
    p.add_argument("--timeline", required=True, help="timeline.json path")
    p.add_argument("--audio", required=True, help="voice.wav/mp3")
    p.add_argument("--out", required=True, help="output mp4")
    p.add_argument("--keep-work", action="store_true", help="keep temp frames")
    args = p.parse_args()

    timeline_path = Path(args.timeline)
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    if "base_dir" not in timeline:
        # default: article dir = parent of shipinhao
        timeline["base_dir"] = str(timeline_path.parent.parent)

    audio = Path(args.audio)
    out = Path(args.out)

    if args.keep_work:
        work = out.parent / "_render_work"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        render(timeline, audio, out, work)
    else:
        with tempfile.TemporaryDirectory(prefix="shipinhao_") as td:
            render(timeline, audio, out, Path(td))


if __name__ == "__main__":
    main()
