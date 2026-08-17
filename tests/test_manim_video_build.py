"""scripts/manim_video_build.py 的字幕时间轴与拆句回归测试（2026-08-16 GRPO 字幕同步事故）。"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from manim_video_build import (  # noqa: E402
    build_srt,
    sentence_boundary_alignment,
    split_long,
)


def test_split_long_keeps_english_number_tokens_whole():
    # DeepSeekMath / 77.9% / 2024 曾在字幕里被硬切成两半
    chunks = split_long("GRPO 的起点，是 2024 年 DeepSeek 的 DeepSeekMath。")
    joined = "".join(chunks)
    assert "DeepSeekMath" in joined
    assert all(len(c) <= 30 for c in chunks)

    chunks = split_long("AIME 2024 正确率从 15.6% 冲到 77.9%，")
    assert chunks == ["AIME 2024 正确率从 15.6% 冲到", "77.9%，"]


def test_sentence_boundary_alignment_normalizes_list_segments():
    data = {
        "source": "tts.txt",
        "segments": [
            {
                "id": "s1",
                "duration": 10.0,
                "clips": [
                    {"id": "s1-c01", "start": 0.0, "end": 4.0, "text": "一二。"},
                    {"id": "s1-c02", "start": 4.0, "end": 9.9, "text": "三四。"},
                ],
            }
        ],
    }
    normalized = sentence_boundary_alignment(data)
    assert normalized == {
        "segments": {
            "S1": {
                "source_duration": 10.0,
                "clips": data["segments"][0]["clips"],
            }
        }
    }


def test_build_srt_prefers_sentence_boundaries_over_pauses():
    sentence_ts = sentence_boundary_alignment(
        {
            "segments": [
                {
                    "id": "s1",
                    "duration": 9.9,
                    "clips": [
                        {"id": "c1", "start": 0.0, "end": 4.0, "text": "一二。"},
                        {"id": "c2", "start": 4.0, "end": 9.9, "text": "三四。"},
                    ],
                }
            ]
        }
    )
    # pauses 故意给出不同的边界；正确实现必须优先 sentence_ts，而不是用停顿重分文本
    entries = build_srt(
        {"S1": "一二。三四。"},
        {"S1": 10.0},  # 视频段长 = 9.9 配音 + 0.1 tail
        0.1,
        subtitle_ts=None,
        pauses={"S1": [2.0, 5.0]},
        manual_alignment=None,
        sentence_ts=sentence_ts,
    )
    assert [(round(s, 3), round(e, 3), t) for s, e, t in entries] == [
        (0.0, 4.0, "一二。"),
        (4.0, 9.9, "三四。"),
    ]


def test_build_srt_merges_pure_punctuation_clip_into_previous():
    sentence_ts = sentence_boundary_alignment(
        {
            "segments": [
                {
                    "id": "s1",
                    "duration": 1.2,
                    "clips": [
                        {"id": "c1", "start": 0.0, "end": 1.0, "text": "反思"},
                        {"id": "c2", "start": 1.0, "end": 1.2, "text": "。"},
                    ],
                }
            ]
        }
    )
    entries = build_srt(
        {"S1": "反思。"},
        {"S1": 1.3},
        0.1,
        subtitle_ts=None,
        pauses=None,
        manual_alignment=None,
        sentence_ts=sentence_ts,
    )
    assert entries == [(0.0, 1.2, "反思。")]


def test_build_srt_pauses_still_work_as_fallback():
    entries = build_srt(
        {"S1": "一二。三四。"},
        {"S1": 10.0},
        0.1,
        subtitle_ts=None,
        pauses={"S1": [4.0]},
        manual_alignment=None,
        sentence_ts=None,
    )
    assert entries[0][0] == 0.0
    assert abs(entries[-1][1] - 9.9) < 0.01
    assert "".join(t for _, _, t in entries) == "一二。三四。"
