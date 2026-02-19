"""Stage 3: Poisson disk sampling (ENG_SPEC §3.3)."""

import numpy as np

from constellate_labs.models import ProcessedPath, SamplingResult
from constellate_labs.utils.sampling import poisson_disk_along_path


def sample_waypoints(
    paths: list[ProcessedPath],
    *,
    min_distance: float = 1.0,
    path_resolution: float | None = None,
) -> SamplingResult:
    """
    Sample waypoint positions along processed paths with minimum spacing.
    Concatenates all paths in order and returns positions + ordering.
    """
    if not paths:
        return SamplingResult(
            positions=np.empty((0, 2)),
            ordering=np.array([], dtype=int),
            metadata={"total_waypoints": 0},
        )
    all_positions: list[np.ndarray] = []
    for path in paths:
        pts = poisson_disk_along_path(
            path.points,
            min_distance,
            path_resolution=path_resolution,
        )
        if pts.shape[0] > 0:
            all_positions.append(pts)
    if not all_positions:
        return SamplingResult(
            positions=np.empty((0, 2)),
            ordering=np.array([], dtype=int),
            metadata={"total_waypoints": 0},
        )
    positions = np.vstack(all_positions)
    ordering = np.arange(positions.shape[0])
    spacing = 0.0
    if positions.shape[0] >= 2:
        d = np.linalg.norm(np.diff(positions, axis=0), axis=1)
        spacing = float(np.mean(d))
    metadata = {
        "total_waypoints": positions.shape[0],
        "min_distance": min_distance,
        "average_spacing": spacing,
    }
    return SamplingResult(
        positions=positions,
        ordering=ordering,
        metadata=metadata,
    )
