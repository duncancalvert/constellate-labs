"""Stage 2: Deterministic geometry processing (ENG_SPEC §3.2)."""

import xml.etree.ElementTree as ET
import numpy as np

from constellate_labs.models import GeometryResult, ProcessedPath
from constellate_labs.utils.geometry import (
    bounding_box,
    douglas_peucker,
    normalize_coordinates,
)


def _parse_svg_path_d(path_d: str) -> np.ndarray:
    """
    Parse SVG path 'd' attribute into polyline points using svgpathtools.
    """
    try:
        from svgpathtools import parse_path
    except ImportError:
        return np.empty((0, 2))
    path = parse_path(path_d)
    points: list[tuple[float, float]] = []
    for seg in path:
        n = 10
        for i in range(n + 1):
            t = i / n
            p = seg.point(t)
            points.append((p.real, p.imag))
    return np.array(points) if points else np.empty((0, 2))


def _extract_paths_from_svg(svg_content: str) -> list[tuple[np.ndarray, bool]]:
    """
    Extract (points, is_closed) for each path/polygon/polyline/circle in SVG.
    """
    results: list[tuple[np.ndarray, bool]] = []
    try:
        root = ET.fromstring(svg_content)
    except ET.ParseError:
        return results
    ns = {"svg": "http://www.w3.org/2000/svg"}
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "path":
            d = elem.get("d")
            if d:
                pts = _parse_svg_path_d(d)
                if pts.shape[0] >= 2:
                    closed = d.strip().upper().endswith("Z")
                    results.append((pts, closed))
        elif tag == "polygon":
            points_str = elem.get("points")
            if points_str:
                pts = _parse_points_attr(points_str)
                if pts.shape[0] >= 2:
                    results.append((pts, True))
        elif tag == "polyline":
            points_str = elem.get("points")
            if points_str:
                pts = _parse_points_attr(points_str)
                if pts.shape[0] >= 2:
                    results.append((pts, False))
        elif tag == "circle":
            cx = float(elem.get("cx", 0))
            cy = float(elem.get("cy", 0))
            r = float(elem.get("r", 1))
            n = max(16, int(2 * np.pi * r / 2))
            t = np.linspace(0, 2 * np.pi, n, endpoint=False)
            pts = np.column_stack([cx + r * np.cos(t), cy + r * np.sin(t)])
            results.append((pts, True))
        elif tag == "rect":
            x = float(elem.get("x", 0))
            y = float(elem.get("y", 0))
            w = float(elem.get("width", 1))
            h = float(elem.get("height", 1))
            pts = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]])
            results.append((pts, True))
    return results


def _parse_points_attr(points_str: str) -> np.ndarray:
    """Parse SVG points attribute (e.g. '0,0 1,1 2,2')."""
    points: list[tuple[float, float]] = []
    for part in points_str.replace(",", " ").split():
        part = part.strip()
        if not part:
            continue
        vals = part.split()
        if len(vals) >= 2:
            points.append((float(vals[0]), float(vals[1])))
        elif len(vals) == 1:
            try:
                x = float(vals[0])
                if points:
                    points.append((x, points[-1][1]))
                else:
                    points.append((x, 0.0))
            except ValueError:
                pass
    return np.array(points) if points else np.empty((0, 2))


def process_geometry(
    svg_content: str,
    *,
    simplification_tolerance: float = 0.5,
    origin_center: bool = True,
    scale_to_meters: float = 0.01,
) -> GeometryResult:
    """
    Parse SVG and return normalized paths (ProcessedPath list) and bounding box.
    """
    raw_paths = _extract_paths_from_svg(svg_content)
    paths: list[ProcessedPath] = []
    all_points: list[np.ndarray] = []

    for pts, is_closed in raw_paths:
        if pts.size < 4:
            continue
        pts = normalize_coordinates(
            pts,
            origin_center=False,
            scale_to_meters=scale_to_meters,
        )
        pts = douglas_peucker(pts, simplification_tolerance)
        if pts.shape[0] < 2:
            continue
        if origin_center:
            # Will center after we have bbox
            pass
        all_points.append(pts)
        paths.append(
            ProcessedPath(
                points=pts,
                is_closed=is_closed,
                metadata={"simplification_tolerance": simplification_tolerance},
            )
        )

    if not all_points:
        return GeometryResult(
            paths=[],
            bounding_box=(0.0, 0.0, 0.0, 0.0),
            metadata={"path_count": 0},
        )

    combined = np.vstack(all_points)
    min_x, min_y, max_x, max_y = bounding_box(combined)
    if origin_center:
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        for p in paths:
            p.points[:, 0] -= cx
            p.points[:, 1] -= cy
        min_x, max_x = min_x - cx, max_x - cx
        min_y, max_y = min_y - cy, max_y - cy

    total_length = sum(
        np.sum(np.linalg.norm(np.diff(p.points, axis=0), axis=1)) for p in paths
    )
    metadata = {
        "path_count": len(paths),
        "simplification_tolerance": simplification_tolerance,
        "total_path_length": float(total_length),
    }
    return GeometryResult(
        paths=paths,
        bounding_box=(min_x, min_y, max_x, max_y),
        metadata=metadata,
    )
