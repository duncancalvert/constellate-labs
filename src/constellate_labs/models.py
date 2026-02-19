"""Data models for the Constellate Labs pipeline (ENG_SPEC §4.2)."""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class Waypoint:
    """Single drone position with timing and velocity."""

    x: float  # meters
    y: float  # meters
    z: float  # meters (altitude)
    velocity: float  # m/s
    timestamp: float  # seconds from start


@dataclass
class ProcessedPath:
    """Normalized 2D path from geometry processing (Stage 2)."""

    points: np.ndarray  # shape (N, 2) for (x, y)
    is_closed: bool
    metadata: dict[str, Any]


@dataclass
class FlightShow:
    """Complete show: waypoints plus SkyBrush-compatible structure."""

    waypoints: list[Waypoint]
    metadata: dict[str, Any]
    constraints: dict[str, Any]
    skybrush_format: dict[str, Any]


@dataclass
class SvgResult:
    """Output of Stage 1: LLM-generated SVG."""

    svg_content: str
    metadata: dict[str, Any]


@dataclass
class GeometryResult:
    """Output of Stage 2: processed paths and metadata."""

    paths: list[ProcessedPath]
    bounding_box: tuple[float, float, float, float]  # min_x, min_y, max_x, max_y
    metadata: dict[str, Any]


@dataclass
class SamplingResult:
    """Output of Stage 3: sampled waypoint positions."""

    positions: np.ndarray  # shape (N, 2) for (x, y)
    ordering: np.ndarray  # indices for traversal order
    metadata: dict[str, Any]


@dataclass
class ConstraintResult:
    """Output of Stage 4: validated waypoints and report."""

    waypoints: list[Waypoint]
    velocity_profile: list[float]
    validation_report: list[str]
    metadata: dict[str, Any]
