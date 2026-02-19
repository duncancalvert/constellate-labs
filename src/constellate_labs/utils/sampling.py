"""Poisson disk–style sampling along paths and 2D region (ENG_SPEC §3.3)."""

import math
import random

import numpy as np


def _discretize_path(points: np.ndarray, segment_length: float) -> np.ndarray:
    """Convert path to dense point sequence with ~segment_length spacing."""
    pts = np.asarray(points, dtype=float)
    if pts.shape[0] < 2:
        return pts
    out: list[np.ndarray] = []
    for i in range(pts.shape[0] - 1):
        a, b = pts[i], pts[i + 1]
        seg_len = np.linalg.norm(b - a)
        if seg_len < 1e-12:
            out.append(a.reshape(1, -1))
            continue
        n = max(1, int(np.ceil(seg_len / segment_length)))
        t = np.linspace(0, 1, n, endpoint=False).reshape(-1, 1)
        out.append((a + t * (b - a)))
    out.append(pts[-1:])
    return np.vstack(out)


def poisson_disk_along_path(
    path_points: np.ndarray,
    min_distance: float,
    *,
    path_resolution: float | None = None,
) -> np.ndarray:
    """
    Sample points along the path with minimum spacing (Poisson-disk style).
    Returns ordered (N, 2) array of (x, y) waypoint positions.
    """
    if path_points is None or path_points.size == 0:
        return np.empty((0, 2))
    path_points = np.asarray(path_points, dtype=float)
    if path_points.ndim == 1:
        path_points = path_points.reshape(-1, 2)
    res = path_resolution or min_distance / 3.0
    dense = _discretize_path(path_points, res)
    if dense.shape[0] == 0:
        return np.empty((0, 2))
    if dense.shape[0] == 1:
        return dense

    r = min_distance
    r2 = r * r
    ordered: list[np.ndarray] = [dense[0]]

    for i in range(1, dense.shape[0]):
        pt = dense[i]
        last = ordered[-1]
        if np.sum((pt - last) ** 2) >= r2:
            ordered.append(pt)
    if dense.shape[0] > 1 and not np.allclose(ordered[-1], dense[-1]):
        ordered.append(dense[-1])
    return np.vstack(ordered)


def poisson_disk_2d(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    min_distance: float,
    n_points: int,
    *,
    margin: float = 0.0,
    rng: random.Random | None = None,
) -> np.ndarray:
    """
    Sample up to n_points in a 2D rectangle with Poisson disk spacing (Bridson-style).
    Works for any region; used to place drone formation positions for any SVG object.
    Returns (N, 2) array with N <= n_points; N may be less if region is too small.
    """
    if n_points <= 0 or min_distance <= 0:
        return np.empty((0, 2))
    lo_x = min_x + margin
    lo_y = min_y + margin
    hi_x = max_x - margin
    hi_y = max_y - margin
    if lo_x >= hi_x or lo_y >= hi_y:
        return np.empty((0, 2))
    rng = rng or random.Random()
    r = min_distance
    cell_size = r / math.sqrt(2)
    nx = max(1, int((hi_x - lo_x) / cell_size))
    ny = max(1, int((hi_y - lo_y) / cell_size))
    grid: dict[tuple[int, int], list[float]] = {}

    def cell(p: tuple[float, float]) -> tuple[int, int]:
        return (int((p[0] - lo_x) / cell_size), int((p[1] - lo_y) / cell_size))

    def in_bounds(x: float, y: float) -> bool:
        return lo_x <= x <= hi_x and lo_y <= y <= hi_y

    def valid(p: tuple[float, float], cx: int, cy: int) -> bool:
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                k = (cx + dx, cy + dy)
                if k in grid:
                    for i in range(0, len(grid[k]), 2):
                        qx, qy = grid[k][i], grid[k][i + 1]
                        if (qx - p[0]) ** 2 + (qy - p[1]) ** 2 < r * r:
                            return False
        return True

    active: list[tuple[float, float]] = []
    # First point random in rectangle
    x0 = lo_x + rng.uniform(0, 1) * (hi_x - lo_x)
    y0 = lo_y + rng.uniform(0, 1) * (hi_y - lo_y)
    active.append((x0, y0))
    c0 = cell((x0, y0))
    grid[c0] = [x0, y0]

    while active and len(active) < n_points:
        idx = rng.randint(0, len(active) - 1)
        px, py = active[idx]
        found = False
        for _ in range(30):
            angle = rng.uniform(0, 2 * math.pi)
            rad = rng.uniform(r, 2 * r)
            qx = px + rad * math.cos(angle)
            qy = py + rad * math.sin(angle)
            if not in_bounds(qx, qy):
                continue
            cq = cell((qx, qy))
            if valid((qx, qy), cq[0], cq[1]):
                active.append((qx, qy))
                if cq not in grid:
                    grid[cq] = []
                grid[cq].extend([qx, qy])
                found = True
                break
        if not found:
            active.pop(idx)

    out: list[tuple[float, float]] = []
    for k in grid:
        for i in range(0, len(grid[k]), 2):
            out.append((grid[k][i], grid[k][i + 1]))
    if not out:
        return np.empty((0, 2))
    return np.array(out[:n_points])
