"""Tests for data models."""

import numpy as np

from constellate_labs.models import (
    FlightShow,
    ProcessedPath,
    Waypoint,
)


def test_waypoint() -> None:
    w = Waypoint(x=1.0, y=2.0, z=10.0, velocity=5.0, timestamp=0.0)
    assert w.x == 1.0 and w.y == 2.0 and w.z == 10.0
    assert w.velocity == 5.0 and w.timestamp == 0.0


def test_processed_path() -> None:
    pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]])
    p = ProcessedPath(points=pts, is_closed=True, metadata={})
    assert p.points.shape == (3, 2)
    assert p.is_closed is True


def test_flight_show() -> None:
    w = Waypoint(0.0, 0.0, 10.0, 5.0, 0.0)
    fs = FlightShow(
        waypoints=[w],
        metadata={},
        constraints={},
        skybrush_format={"version": 1},
    )
    assert len(fs.waypoints) == 1
    assert fs.skybrush_format["version"] == 1
