"""Geometry helpers: simplification, normalization, bounding box (ENG_SPEC §3.2)."""

import numpy as np


def douglas_peucker(points: np.ndarray, tolerance: float) -> np.ndarray:
    """Reduce vertex count while preserving shape (Douglas-Peucker algorithm)."""
    if points.shape[0] < 3:
        return points
    points = np.asarray(points, dtype=float)
    if points.ndim == 1:
        return points
    n = points.shape[0]
    if n <= 2:
        return points

    # Find point with maximum distance from line between first and last
    p0, p1 = points[0], points[-1]
    if np.all(p0 == p1):
        return points[:1]
    line_vec = p1 - p0
    line_len = np.linalg.norm(line_vec)
    if line_len < 1e-12:
        return points[:1]
    seg_vecs = points[1:-1] - p0
    # Perp distance: cross product length / line_len
    cross = np.abs(
        seg_vecs[:, 0] * line_vec[1] - seg_vecs[:, 1] * line_vec[0]
    )
    dists = cross / line_len
    idx = np.argmax(dists)
    max_dist = dists[idx]

    if max_dist <= tolerance:
        return np.array([p0, p1])
    idx_actual = idx + 1
    left = douglas_peucker(points[: idx_actual + 1], tolerance)
    right = douglas_peucker(points[idx_actual:], tolerance)
    return np.vstack([left[:-1], right])


def bounding_box(points: np.ndarray) -> tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) for a set of points."""
    pts = np.asarray(points)
    if pts.size == 0:
        return (0.0, 0.0, 0.0, 0.0)
    if pts.ndim == 1:
        return (float(pts[0]), 0.0, float(pts[0]), 0.0)
    min_x, min_y = np.min(pts[:, 0]), np.min(pts[:, 1])
    max_x, max_y = np.max(pts[:, 0]), np.max(pts[:, 1])
    return (float(min_x), float(min_y), float(max_x), float(max_y))


def centroid(points: np.ndarray) -> tuple[float, float]:
    """Return (center_x, center_y) for a set of 2D points."""
    pts = np.asarray(points)
    if pts.size == 0:
        return (0.0, 0.0)
    if pts.ndim == 1:
        return (float(pts[0]), 0.0)
    return (float(np.mean(pts[:, 0])), float(np.mean(pts[:, 1])))


def normalize_coordinates(
    points: np.ndarray,
    *,
    origin_center: bool = True,
    scale_to_meters: float = 1.0,
) -> np.ndarray:
    """Convert to consistent coordinate system: optional center, optional scale."""
    pts = np.asarray(points, dtype=float).copy()
    if pts.size == 0:
        return pts
    if pts.ndim == 1:
        return pts * scale_to_meters
    pts *= scale_to_meters
    if origin_center:
        min_x, min_y, max_x, max_y = bounding_box(pts)
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        pts[:, 0] -= cx
        pts[:, 1] -= cy
    return pts
