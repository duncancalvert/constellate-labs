"""Physical constraint checks and bounds clamping (ENG_SPEC §3.4)."""

import numpy as np


def check_velocity(
    positions: np.ndarray,
    timestamps: np.ndarray,
    max_velocity: float,
) -> tuple[bool, list[int]]:
    """
    Check if segment velocities exceed max_velocity.
    Returns (all_ok, list of segment indices that violate).
    """
    positions = np.asarray(positions)
    timestamps = np.asarray(timestamps)
    violations: list[int] = []
    if positions.shape[0] < 2 or timestamps.shape[0] < 2:
        return (True, [])
    n = min(positions.shape[0], timestamps.shape[0]) - 1
    for i in range(n):
        dt = timestamps[i + 1] - timestamps[i]
        if dt <= 0:
            continue
        disp = positions[i + 1] - positions[i]
        if disp.ndim >= 1:
            dist = np.linalg.norm(disp)
        else:
            dist = abs(disp)
        v = dist / dt
        if v > max_velocity:
            violations.append(i)
    return (len(violations) == 0, violations)


def check_acceleration(
    positions: np.ndarray,
    timestamps: np.ndarray,
    max_acceleration: float,
) -> tuple[bool, list[int]]:
    """
    Check if segment-to-segment acceleration exceeds max.
    Returns (all_ok, list of vertex indices where acceleration violates).
    """
    positions = np.asarray(positions)
    timestamps = np.asarray(timestamps)
    violations: list[int] = []
    if positions.shape[0] < 3 or timestamps.shape[0] < 3:
        return (True, [])
    n = min(positions.shape[0], timestamps.shape[0])
    for i in range(1, n - 1):
        dt1 = timestamps[i] - timestamps[i - 1]
        dt2 = timestamps[i + 1] - timestamps[i]
        if dt1 <= 0 or dt2 <= 0:
            continue
        v1 = (positions[i] - positions[i - 1]) / dt1
        v2 = (positions[i + 1] - positions[i]) / dt2
        v1 = np.asarray(v1)
        v2 = np.asarray(v2)
        acc = (v2 - v1) / ((dt1 + dt2) / 2)
        a = np.linalg.norm(acc)
        if a > max_acceleration:
            violations.append(i)
    return (len(violations) == 0, violations)


def clamp_to_bounds(
    positions: np.ndarray,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    margin: float = 0.0,
) -> np.ndarray:
    """Clamp (x, y) positions to bounds with optional margin."""
    pts = np.asarray(positions, dtype=float).copy()
    if pts.size == 0:
        return pts
    lo_x = min_x + margin
    lo_y = min_y + margin
    hi_x = max_x - margin
    hi_y = max_y - margin
    if pts.ndim == 1:
        pts[0] = np.clip(pts[0], lo_x, hi_x)
        if pts.shape[0] > 1:
            pts[1] = np.clip(pts[1], lo_y, hi_y)
        return pts
    pts[:, 0] = np.clip(pts[:, 0], lo_x, hi_x)
    pts[:, 1] = np.clip(pts[:, 1], lo_y, hi_y)
    return pts
