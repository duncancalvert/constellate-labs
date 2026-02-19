"""Stage 5: SkyBrush export (ENG_SPEC §3.5)."""

import json
from pathlib import Path

import numpy as np

from constellate_labs.models import ConstraintResult, FlightShow, Waypoint
from constellate_labs.utils.geometry import bounding_box, centroid
from constellate_labs.utils.sampling import poisson_disk_2d


def _waypoints_to_trajectory(
    waypoints: list[Waypoint],
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    offset_z: float = 0.0,
) -> list[dict]:
    """Map waypoints to SkyBrush-style trajectory points (JSON-serializable)."""
    return [
        {
            "time": w.timestamp,
            "x": w.x + offset_x,
            "y": w.y + offset_y,
            "z": w.z + offset_z,
            "velocity": w.velocity,
        }
        for w in waypoints
    ]


def _drone_offsets_poisson(
    bounding_box_xy: tuple[float, float, float, float],
    number_of_drones: int,
    drone_spacing: float,
    waypoints_xy: list[tuple[float, float]],
    margin: float = 0.0,
    expand: float = 0.0,
) -> list[tuple[float, float]]:
    """
    Place drones using Poisson disk sampling over the object's bounding box
    (ENG_SPEC §3.3). Works for any SVG-derived shape; each drone gets the same
    path translated so its centroid aligns with a sampled position.
    expand: grow bbox on each side to give room for formation (e.g. 2*drone_spacing).
    """
    if number_of_drones <= 0:
        return []
    if number_of_drones == 1:
        return [(0.0, 0.0)]
    min_x, min_y, max_x, max_y = bounding_box_xy
    min_x -= expand
    min_y -= expand
    max_x += expand
    max_y += expand
    positions = poisson_disk_2d(
        min_x, min_y, max_x, max_y,
        min_distance=drone_spacing,
        n_points=number_of_drones,
        margin=margin,
    )
    if positions.shape[0] == 0:
        return [(0.0, 0.0)] * number_of_drones
    path_cx, path_cy = centroid(np.array(waypoints_xy)) if waypoints_xy else (0.0, 0.0)
    offsets = [
        (float(positions[i, 0] - path_cx), float(positions[i, 1] - path_cy))
        for i in range(positions.shape[0])
    ]
    while len(offsets) < number_of_drones:
        offsets.append(offsets[-1] if offsets else (0.0, 0.0))
    return offsets[:number_of_drones]


def _build_skybrush_structure(
    waypoints: list[Waypoint],
    show_name: str = "Constellate Show",
    description: str = "",
    number_of_drones: int = 1,
    drone_spacing: float = 5.0,
    bounding_box_xy: tuple[float, float, float, float] | None = None,
    drone_placement_margin: float = 0.0,
    drone_placement_expand: float = 0.0,
) -> dict:
    """
    Build SkyBrush-compatible show structure (JSON format).
    Drones are placed via 2D Poisson disk sampling over the object's bounding
    box so spacing works for any SVG shape (ENG_SPEC §3.3).
    """
    duration = waypoints[-1].timestamp if waypoints else 0.0
    n = max(1, number_of_drones)
    waypoints_xy = [(w.x, w.y) for w in waypoints] if waypoints else []
    if bounding_box_xy is not None:
        bbox = bounding_box_xy
    elif waypoints_xy:
        bbox = bounding_box(np.array(waypoints_xy))
    else:
        bbox = (0.0, 0.0, 0.0, 0.0)

    if n == 1:
        offsets = [(0.0, 0.0)]
    else:
        offsets = _drone_offsets_poisson(
            bbox,
            n,
            drone_spacing,
            waypoints_xy,
            margin=drone_placement_margin,
            expand=drone_placement_expand,
        )

    trajectories = []
    for i in range(n):
        ox, oy = offsets[i] if i < len(offsets) else (0.0, 0.0)
        points = _waypoints_to_trajectory(waypoints, offset_x=ox, offset_y=oy)
        trajectories.append({
            "type": "trajectory",
            "points": points,
            "drone_index": i,
        })
    return {
        "version": 1,
        "name": show_name,
        "description": description,
        "duration": duration,
        "number_of_drones": n,
        "drone_spacing": drone_spacing,
        "trajectories": trajectories,
        "metadata": {
            "generator": "constellate-labs",
        },
    }


def export_skybrush(
    constraint_result: ConstraintResult,
    *,
    show_name: str = "Constellate Show",
    description: str = "",
    number_of_drones: int = 1,
    drone_spacing: float = 5.0,
    bounding_box_xy: tuple[float, float, float, float] | None = None,
    drone_placement_margin: float = 0.0,
    drone_placement_expand: float = 0.0,
) -> FlightShow:
    """
    Convert validated waypoints to FlightShow with SkyBrush-compatible structure.
    Drones are placed via 2D Poisson disk sampling over the object's bounding
    box so any SVG shape is supported.
    """
    skybrush_format = _build_skybrush_structure(
        constraint_result.waypoints,
        show_name=show_name,
        description=description,
        number_of_drones=number_of_drones,
        drone_spacing=drone_spacing,
        bounding_box_xy=bounding_box_xy,
        drone_placement_margin=drone_placement_margin,
        drone_placement_expand=drone_placement_expand,
    )
    return FlightShow(
        waypoints=constraint_result.waypoints,
        metadata=constraint_result.metadata,
        constraints={
            "max_velocity": constraint_result.metadata.get("max_velocity"),
            "max_acceleration": constraint_result.metadata.get("max_acceleration"),
        },
        skybrush_format=skybrush_format,
    )


def write_skybrush_file(
    flight_show: FlightShow,
    path: str | Path,
    *,
    as_json: bool = True,
) -> None:
    """Write FlightShow to a SkyBrush-compatible file (.json or .skyc)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = dict(flight_show.skybrush_format)
    # Ensure number_of_drones is always present in the written file
    if "number_of_drones" not in data:
        data["number_of_drones"] = len(data.get("trajectories", [])) or 1
    if as_json or path.suffix.lower() == ".json":
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    else:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
