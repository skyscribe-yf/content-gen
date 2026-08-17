"""竖屏整页规划资产（manim_helpers.layout_page/page_stack）回归测试。"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pytest  # noqa: E402
from manim import RoundedRectangle  # noqa: E402
from manim_helpers import (  # noqa: E402
    CARD_FILL,
    FH,
    MAX_PAGE_MARGIN,
    MIN_PAGE_FILL,
    PAGE_BAND,
    PAGE_BOTTOM,
    PAGE_TOP,
    _card,
    layout_page,
    page_stack,
    t,
)


def test_page_band_contract():
    assert 0 < MAX_PAGE_MARGIN <= 0.3
    assert MIN_PAGE_FILL == 1 - 2 * MAX_PAGE_MARGIN == 0.4
    assert PAGE_TOP - PAGE_BOTTOM == pytest.approx(PAGE_BAND)
    assert PAGE_TOP == pytest.approx(FH * 0.32)
    assert PAGE_BOTTOM == pytest.approx(-FH * 0.292)


def test_card_is_solid_filled_rounded_rectangle():
    card = _card("默认卡片", 5.0, 1.0, "#5FC4E8", "#F2F5FA", 28)
    box = card[0]
    assert isinstance(box, RoundedRectangle)
    assert box.fill_opacity == 1.0
    assert box.fill_color.to_hex() == CARD_FILL


def test_page_stack_centers_horizontally():
    a = t("第一行", 30)
    b = t("第二行", 40)
    page = page_stack(a, b, buff=0.8)
    assert page.get_center()[0] == pytest.approx(0.0, abs=1e-6)
    assert a.get_top()[1] > b.get_top()[1]


def test_layout_page_centers_equal_margins():
    card = _card("整页卡", 6.0, 3.6, "#5FC4E8", "#F2F5FA", 40)
    layout_page(card)
    assert card.get_center()[0] == pytest.approx(0.0, abs=1e-6)
    top_margin = PAGE_TOP - card.get_top()[1]
    bottom_margin = card.get_bottom()[1] - PAGE_BOTTOM
    assert top_margin == pytest.approx(bottom_margin, abs=1e-6)
    assert top_margin <= PAGE_BAND * MAX_PAGE_MARGIN + 1e-6


def test_layout_page_rejects_short_page():
    short = page_stack(t("短页", 30), buff=0.5)
    with pytest.raises(ValueError):
        layout_page(short)


def test_layout_page_scales_oversized_page_into_band():
    card = _card("超高一页", 6.0, 10.0, "#5FC4E8", "#F2F5FA", 40)
    layout_page(card)
    assert card.height <= PAGE_BAND + 1e-6
    top_margin = PAGE_TOP - card.get_top()[1]
    bottom_margin = card.get_bottom()[1] - PAGE_BOTTOM
    assert top_margin == pytest.approx(bottom_margin, abs=1e-6)
