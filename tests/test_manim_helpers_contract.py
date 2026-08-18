"""Regression tests for the shared geometry primitives used by new scenes."""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from manim_helpers import (  # noqa: E402
    CARD_TEXT_LINE_SPACING,
    CARD_TEXT_MAX_FS,
    _card,
    dynamic_slot,
    stable_row,
    t,
)


def test_tall_card_wraps_before_using_tiny_single_line_text():
    card = _card("AIME 2024 正确率从 15.6% 冲到 77.9%", 2.4, 3.1,
                 "#5FC4E8", "#F2F5FA", fs=30)
    box, label = card
    assert label.width <= box.width * 0.76 + 1e-6
    assert label.height <= box.height * 0.72 + 1e-6
    # A tall card must use more than a tiny one-line glyph row.
    assert label.height > 0.7


def test_dynamic_slot_and_static_label_share_a_baseline():
    slot = dynamic_slot(1.45, height=0.7)
    label = _card("步骤", 1.4, 0.9, "#5FC4E8", "#F2F5FA", fs=24)
    row = stable_row(label, slot, buff=0.35)
    assert slot.width == pytest.approx(1.45)
    assert slot.get_center()[1] == pytest.approx(label.get_center()[1])
    assert row.get_left()[0] < row.get_right()[0]


def test_card_font_uses_vertical_space_with_shared_cap_and_line_gap():
    label = "每个 token 只选 8 个"
    short = _card(label, 2.4, 1.0, "#5FC4E8", "#F2F5FA", fs=24)[1]
    tall = _card(label, 2.4, 3.1, "#5FC4E8", "#F2F5FA", fs=24)[1]
    assert tall.font_size > short.font_size
    assert tall.font_size <= CARD_TEXT_MAX_FS
    assert "\n" in tall.original_text
    tight = t(tall.original_text, tall.font_size, line_spacing=0)
    assert CARD_TEXT_LINE_SPACING > 0
    assert tall.height > tight.height
