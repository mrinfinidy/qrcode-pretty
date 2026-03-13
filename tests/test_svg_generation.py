"""Tests for SVG drawer functions."""

import pytest
from qrcode_pretty.svg_utils import (
    has_neighbor,
    svg_draw_square,
    svg_draw_rounded,
    svg_draw_vertical_bars,
    svg_draw_horizontal_bars,
    svg_draw_circle,
)

# 5x5 cross pattern: center row and center column are filled
CROSS_MATRIX = [
    [False, False, True, False, False],
    [False, False, True, False, False],
    [True,  True,  True, True,  True ],
    [False, False, True, False, False],
    [False, False, True, False, False],
]


class TestHasNeighbor:
    def test_center_has_all_four_neighbors(self):
        assert has_neighbor(CROSS_MATRIX, 2, 2, "N", 5) is True
        assert has_neighbor(CROSS_MATRIX, 2, 2, "S", 5) is True
        assert has_neighbor(CROSS_MATRIX, 2, 2, "E", 5) is True
        assert has_neighbor(CROSS_MATRIX, 2, 2, "W", 5) is True

    def test_top_edge_has_no_north_neighbor(self):
        assert has_neighbor(CROSS_MATRIX, 0, 2, "N", 5) is False

    def test_top_edge_has_south_neighbor(self):
        assert has_neighbor(CROSS_MATRIX, 0, 2, "S", 5) is True

    def test_invalid_direction_returns_false(self):
        assert has_neighbor(CROSS_MATRIX, 2, 2, "X", 5) is False


class TestSvgDrawSquare:
    def test_returns_rect_element(self):
        result = svg_draw_square(10, 20, 10, "#000")
        assert result.startswith("<rect")
        assert 'x="10"' in result
        assert 'y="20"' in result
        assert 'width="10"' in result
        assert 'height="10"' in result
        assert 'fill="#000"' in result


class TestSvgDrawCircle:
    def test_returns_circle_element(self):
        result = svg_draw_circle(20, 20, 10, "#000")
        assert result.startswith("<circle")
        assert 'fill="#000"' in result

    def test_circle_centered_in_box(self):
        result = svg_draw_circle(0, 0, 10, "#000")
        assert 'cx="5.0"' in result
        assert 'cy="5.0"' in result
        assert 'r="5.0"' in result


class TestSvgDrawRounded:
    def test_center_module_no_rounded_corners(self):
        # All 4 neighbors present — should be a plain square (no arc commands)
        result = svg_draw_rounded(20, 20, 10, "#000", CROSS_MATRIX, 2, 2, 5)
        assert "<path" in result
        assert "A " not in result

    def test_top_module_has_rounded_north_corners(self):
        # Top of the cross: no N neighbor, no W or E neighbors either
        # NW and NE corners should be rounded (arc commands present)
        result = svg_draw_rounded(20, 0, 10, "#000", CROSS_MATRIX, 0, 2, 5)
        assert "<path" in result
        assert "A " in result

    def test_returns_path_element(self):
        result = svg_draw_rounded(0, 0, 10, "#000", CROSS_MATRIX, 2, 2, 5)
        assert result.startswith("<path")
        assert 'fill="#000"' in result


class TestSvgDrawVerticalBars:
    def test_center_module_returns_two_rects(self):
        # Has both N and S neighbors: both halves are plain rectangles
        result = svg_draw_vertical_bars(20, 20, 10, "#000", CROSS_MATRIX, 2, 2, 5)
        assert result is not None
        assert result.count("<rect") == 2

    def test_top_module_has_rounded_top(self):
        # No N neighbor: top half uses a path with arc
        result = svg_draw_vertical_bars(20, 0, 10, "#000", CROSS_MATRIX, 0, 2, 5)
        assert result is not None
        assert "<path" in result
        assert "A " in result

    def test_returns_non_empty_string(self):
        result = svg_draw_vertical_bars(20, 20, 10, "#000", CROSS_MATRIX, 2, 2, 5)
        assert result is not None
        assert len(result) > 0


class TestSvgDrawHorizontalBars:
    def test_center_module_returns_two_rects(self):
        # Has both W and E neighbors: both halves are plain rectangles
        result = svg_draw_horizontal_bars(20, 20, 10, "#000", CROSS_MATRIX, 2, 2, 5)
        assert result is not None
        assert result.count("<rect") == 2

    def test_leftmost_module_has_rounded_left(self):
        # No W neighbor: left half uses a path with arc
        result = svg_draw_horizontal_bars(0, 20, 10, "#000", CROSS_MATRIX, 2, 0, 5)
        assert result is not None
        assert "<path" in result
        assert "A " in result

    def test_returns_non_empty_string(self):
        result = svg_draw_horizontal_bars(20, 20, 10, "#000", CROSS_MATRIX, 2, 2, 5)
        assert result is not None
        assert len(result) > 0
