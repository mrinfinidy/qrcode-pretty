"""Tests for horizontal bars SVG path generation."""

import pytest
from qrcode_pretty.svg_utils import svg_draw_horizontal_bars

ISOLATED = [
    [False, False, False],
    [False, True,  False],
    [False, False, False],
]

LEFT_NEIGHBOR = [
    [False, False, False],
    [True,  True,  False],
    [False, False, False],
]

RIGHT_NEIGHBOR = [
    [False, False, False],
    [False, True,  True],
    [False, False, False],
]

BOTH_NEIGHBORS = [
    [False, False, False],
    [True,  True,  True],
    [False, False, False],
]


class TestHorizontalBarsIsolated:
    def test_returns_output(self):
        result = svg_draw_horizontal_bars(0, 0, 10, "#000", ISOLATED, 1, 1, 3)
        assert result is not None
        assert len(result) > 0

    def test_both_ends_rounded(self):
        # No W or E neighbor: both halves use arcs, no plain rects
        result = svg_draw_horizontal_bars(0, 0, 10, "#000", ISOLATED, 1, 1, 3)
        assert result is not None
        assert "<rect" not in result
        assert result.count("<path") == 2
        assert "A " in result


class TestHorizontalBarsLeftNeighbor:
    def test_right_end_rounded_left_end_flat(self):
        # Has W neighbor (left is flat rect), no E neighbor (right is arc)
        result = svg_draw_horizontal_bars(10, 0, 10, "#000", LEFT_NEIGHBOR, 1, 1, 3)
        assert result is not None
        assert result.count("<rect") == 1
        assert result.count("<path") == 1


class TestHorizontalBarsRightNeighbor:
    def test_left_end_rounded_right_end_flat(self):
        # No W neighbor (left is arc), has E neighbor (right is flat rect)
        result = svg_draw_horizontal_bars(0, 0, 10, "#000", RIGHT_NEIGHBOR, 1, 1, 3)
        assert result is not None
        assert result.count("<rect") == 1
        assert result.count("<path") == 1


class TestHorizontalBarsBothNeighbors:
    def test_no_rounded_ends(self):
        # Both W and E neighbors: both halves are plain rects, no arcs
        result = svg_draw_horizontal_bars(10, 0, 10, "#000", BOTH_NEIGHBORS, 1, 1, 3)
        assert result is not None
        assert result.count("<rect") == 2
        assert "<path" not in result
