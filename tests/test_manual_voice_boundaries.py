"""Regression tests for Web-confirmed oral-recording boundaries."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import manim_video_build
import voice_process


class ManualVoiceBoundaryTest(unittest.TestCase):
    def test_voice_process_scales_confirmed_boundaries_to_clean_audio(self) -> None:
        manual = {
            "segments": {
                "S1": {
                    "source_duration": 10.0,
                    "clips": [
                        {"id": "s1-c01", "start": 2.0, "end": 8.0, "text": "甲。乙。"},
                        {"id": "s1-c02", "start": 8.0, "end": 10.0, "text": "丙。"},
                    ],
                }
            }
        }

        clips = voice_process.prepared_manual_clips(manual, "S1", "甲。乙。丙。", 10.0, 5.0)

        self.assertEqual([(clip["start"], clip["end"]) for clip in clips], [(1.0, 4.0), (4.0, 5.0)])

    def test_manual_alignment_has_priority_over_automatic_pauses(self) -> None:
        manual = {
            "segments": {
                "S1": {
                    "source_duration": 10.0,
                    "clips": [
                        {"id": "s1-c01", "start": 0.0, "end": 6.0, "text": "甲。乙。"},
                        {"id": "s1-c02", "start": 6.0, "end": 10.0, "text": "丙。"},
                    ],
                }
            }
        }

        entries = manim_video_build.build_srt(
            {"S1": "甲。乙。丙。"},
            {"S1": 5.1},
            0.1,
            pauses={"S1": [1.0, 2.0, 3.0]},
            manual_alignment=manual,
        )

        self.assertEqual(entries, [(0.0, 3.0, "甲。乙。"), (3.0, 5.0, "丙。")])


if __name__ == "__main__":
    unittest.main()
