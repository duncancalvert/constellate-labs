"""Stage 4: Physical constraint enforcement (ENG_SPEC §3.4)."""

import numpy as np

from constellate_labs.models import ConstraintResult, Waypoint
from constellate_labs.utils.validation import (
    check_acceleration,
    check_velocity,
    clamp_to_bounds,
)


def enforce_constraints(
    positions: np.ndarray,
    *,
    max_velocity: float = 10.0,
    max_acceleration: float = 5.0,
    default_altitude: float = 10.0,
    bounds: tuple[float, float, float, float] | None = None,
    safety_margin: float = 0.5,
) -> ConstraintResult:
    """
    Validate and adjust waypoints for velocity, acceleration, and bounds.
    Assigns timestamps and velocities; clamps to bounds with margin.
    """
    positions = np.asarray(positions, dtype=float)
    report: list[str] = []
    if positions.size == 0:
        return ConstraintResult(
            waypoints=[],
            velocity_profile=[],
            validation_report=report,
            metadata={},
        )
    if positions.ndim == 1:
        positions = positions.reshape(-1, 2)
    n = positions.shape[0]
    if bounds is not None:
        positions = clamp_to_bounds(
            positions,
            bounds[0],
            bounds[1],
            bounds[2],
            bounds[3],
            margin=safety_margin,
        )
        report.append("Applied bounds clamping with safety margin.")

    # Build timestamps from constant velocity assumption
    dists = np.linalg.norm(np.diff(positions, axis=0), axis=1)
    dists = np.concatenate([[0.0], dists])
    times = np.cumsum(dists / max_velocity)
    timestamps = times.tolist()
    velocity_profile = [max_velocity] * n
    ok_vel, vel_violations = check_velocity(positions, np.array(timestamps), max_velocity)
    if not ok_vel:
        report.append(f"Velocity violations at segments: {vel_violations[:10]}")
    ok_acc, acc_violations = check_acceleration(
        positions, np.array(timestamps), max_acceleration
    )
    if not ok_acc:
        report.append(f"Acceleration violations at vertices: {acc_violations[:10]}")

    waypoints = [
        Waypoint(
            x=float(positions[i, 0]),
            y=float(positions[i, 1]),
            z=default_altitude,
            velocity=velocity_profile[i],
            timestamp=timestamps[i],
        )
        for i in range(n)
    ]
    metadata = {
        "max_velocity": max_velocity,
        "max_acceleration": max_acceleration,
        "duration_seconds": timestamps[-1] if timestamps else 0.0,
    }
    return ConstraintResult(
        waypoints=waypoints,
        velocity_profile=velocity_profile,
        validation_report=report,
        metadata=metadata,
    )
