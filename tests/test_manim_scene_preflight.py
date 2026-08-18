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


def test_existing_memory_scene_exposes_known_timing_regressions():
    scene = ROOT / "content/2026-07-04-ai-memory-crash/shipinhao"
    result = analyze_scene(scene)
    codes = {issue["code"] for issue in result["issues"]}
    assert not result["ok"]
    assert "action_overrun" in codes
    assert "at_not_on_boundary" in codes


def test_existing_deepseek_scene_exposes_tall_card_and_serial_reveals():
    scene = ROOT / "content/2026-07-11-deepseek-moe/shipinhao"
    result = analyze_scene(scene)
    codes = {issue["code"] for issue in result["issues"]}
    assert "high_card_small_text" in codes
    assert "serial_animation" in codes


def test_strict_mode_promotes_nested_scene_warnings():
    scene = ROOT / "content/2026-07-11-deepseek-moe/shipinhao"
    result = analyze_scene(scene, strict=True)
    nested = [issue for item in result["scenes"] for issue in item["issues"]]
    assert nested
    assert all(issue["severity"] == "error" for issue in nested)


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
