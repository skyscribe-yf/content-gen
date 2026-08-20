"""Tests for the no-Manim static scene preflight gate."""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from manim_timeline import TimelineContract, analyze_scene  # noqa: E402


def test_contract_resolves_sentence_clip_starts():
    scene = ROOT / "content/2026-07-04-ai-memory-crash/shipinhao/scenes.py"
    contract = TimelineContract.for_scene(scene)
    assert contract.start_of("S1-c01") == 0.0
    assert contract.start_of("S1-c03") > contract.start_of("S1-c01")


def test_existing_memory_scene_passes_timing_contract():
    scene = ROOT / "content/2026-07-04-ai-memory-crash/shipinhao"
    result = analyze_scene(scene)
    assert result["ok"]
    assert result["issues"] == []
    assert all(not item["issues"] for item in result["scenes"])


def test_existing_deepseek_scene_passes_layout_and_reveal_contract():
    scene = ROOT / "content/2026-07-11-deepseek-moe/shipinhao"
    result = analyze_scene(scene)
    assert result["ok"]
    assert result["issues"] == []
    assert all(not item["issues"] for item in result["scenes"])


def test_strict_mode_keeps_repaired_scenes_clean():
    scene = ROOT / "content/2026-07-11-deepseek-moe/shipinhao"
    result = analyze_scene(scene, strict=True)
    nested = [issue for item in result["scenes"] for issue in item["issues"]]
    assert result["ok"]
    assert nested == []


def test_checker_reports_missing_pad_and_static_backtrack(tmp_path):
    shipinhao = tmp_path / "shipinhao"
    tts = shipinhao / "tts"
    tts.mkdir(parents=True)
    (tts / "sentence-boundaries.json").write_text(json.dumps({
        "segments": [{"id": "S1", "duration": 4.0, "clips": [
            {"id": "S1-c01", "start": 0.0, "end": 2.0},
            {"id": "S1-c02", "start": 2.0, "end": 4.0},
        ]}],
    }), encoding="utf-8")
    (shipinhao / "scenes.py").write_text(
        "VOICE_DUR = {'S1': 4.0}\n"
        "class S1:\n"
        "    def construct(self):\n"
        "        self.play(FadeIn(x), run_time=1.0)\n"
        "        self.at(0.2)\n",
        encoding="utf-8",
    )
    result = analyze_scene(shipinhao)
    codes = {issue["code"] for issue in result["issues"]}
    assert "action_overrun" in codes
    assert "missing_pad_to_voice" in codes
