"""Tests for geometry utils."""

import numpy as np

from constellate_labs.utils.geometry import (
    bounding_box,
    douglas_peucker,
    normalize_coordinates,
)


def test_bounding_box_empty() -> None:
    assert bounding_box(np.empty((0, 2))) == (0.0, 0.0, 0.0, 0.0)


def test_bounding_box_single_point() -> None:
    pts = np.array([[3.0, 4.0]])
    assert bounding_box(pts) == (3.0, 4.0, 3.0, 4.0)


def test_bounding_box_rect() -> None:
    pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
    assert bounding_box(pts) == (0.0, 0.0, 1.0, 1.0)


def test_douglas_peucker_small() -> None:
    pts = np.array([[0.0, 0.0], [1.0, 1.0]])
    out = douglas_peucker(pts, 0.1)
    assert out.shape[0] >= 2


def test_douglas_peucker_line() -> None:
    pts = np.array([[0.0, 0.0], [0.5, 0.0], [1.0, 0.0]])
    out = douglas_peucker(pts, 0.5)
    assert out.shape[0] == 2


def test_normalize_coordinates() -> None:
    pts = np.array([[10.0, 20.0], [30.0, 40.0]])
    out = normalize_coordinates(pts, origin_center=True, scale_to_meters=1.0)
    assert out.shape == (2, 2)
    min_x, min_y, max_x, max_y = out[:, 0].min(), out[:, 1].min(), out[:, 0].max(), out[:, 1].max()
    assert abs((min_x + max_x) / 2) < 1e-9 and abs((min_y + max_y) / 2) < 1e-9
