"""Tests for validation utils."""

import numpy as np

from constellate_labs.utils.validation import (
    check_acceleration,
    check_velocity,
    clamp_to_bounds,
)


def test_check_velocity_ok() -> None:
    positions = np.array([[0, 0], [1, 0], [2, 0]])
    timestamps = np.array([0.0, 1.0, 2.0])
    ok, violations = check_velocity(positions, timestamps, max_velocity=2.0)
    assert ok is True
    assert violations == []


def test_check_velocity_violation() -> None:
    positions = np.array([[0, 0], [10, 0]])
    timestamps = np.array([0.0, 0.5])
    ok, violations = check_velocity(positions, timestamps, max_velocity=5.0)
    assert ok is False
    assert 0 in violations


def test_clamp_to_bounds() -> None:
    pts = np.array([[0, 0], [15, 15], [-5, -5]])
    out = clamp_to_bounds(pts, 0, 0, 10, 10, margin=0)
    assert out[0, 0] == 0 and out[0, 1] == 0
    assert out[1, 0] == 10 and out[1, 1] == 10
    assert out[2, 0] == 0 and out[2, 1] == 0


def test_check_acceleration_ok() -> None:
    positions = np.array([[0, 0], [1, 0], [2, 0]])
    timestamps = np.array([0.0, 1.0, 2.0])
    ok, violations = check_acceleration(positions, timestamps, max_acceleration=10.0)
    assert ok is True
