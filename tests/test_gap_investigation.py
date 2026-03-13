"""Tests investigating gap behaviour in SVG generation."""

import pytest
from qrcode_pretty.svg_utils import svg_draw_rounded, svg_draw_horizontal_bars

ALL_NEIGHBORS = [
    [True, True, True],
    [True, True, True],
    [True, True, True],
]

ISOLATED = [
    [False, False, False],
    [False, True,  False],
    [False, False, False],
]


class TestRoundedGaps:
    def test_all_neighbors_produces_no_arcs(self):
        # Every side has a neighbour: all corners are sharp, so no arc commands
        result = svg_draw_rounded(0, 0, 10, "#000", ALL_NEIGHBORS, 1, 1, 3)
        assert "<path" in result
        assert "A " not in result

    def test_isolated_module_produces_all_arcs(self):
        # No neighbours on any side: all four corners are rounded
        result = svg_draw_rounded(0, 0, 10, "#000", ISOLATED, 1, 1, 3)
        assert "<path" in result
        assert result.count("A ") == 4


class TestHorizontalBarsGaps:
    def test_all_neighbors_produces_two_rects(self):
        # Both W and E neighbours present: two plain rectangles, no arcs
        result = svg_draw_horizontal_bars(0, 0, 10, "#000", ALL_NEIGHBORS, 1, 1, 3)
        assert result is not None
        assert result.count("<rect") == 2
        assert "<path" not in result

    def test_isolated_module_produces_two_arcs(self):
        # No W or E neighbours: both halves are arc paths
        result = svg_draw_horizontal_bars(0, 0, 10, "#000", ISOLATED, 1, 1, 3)
        assert result is not None
        assert result.count("<path") == 2
        assert "<rect" not in result
