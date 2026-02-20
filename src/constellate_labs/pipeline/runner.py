"""Pipeline runner: run all stages from prompt to SkyBrush (ENG_SPEC §2)."""

from pathlib import Path
from typing import Callable

from constellate_labs.models import FlightShow
from constellate_labs.pipeline.stage1_llm_svg import generate_svg
from constellate_labs.pipeline.stage2_geometry import process_geometry
from constellate_labs.pipeline.stage3_poisson import sample_waypoints
from constellate_labs.pipeline.stage4_constraints import enforce_constraints
from constellate_labs.pipeline.stage5_skybrush import export_skybrush, write_skybrush_file


def run_pipeline(
    prompt: str,
    *,
    llm_call: Callable[[str], str] | None = None,
    output_path: str | Path | None = None,
    show_name: str = "Constellate Show",
    number_of_drones: int = 1,
    **stage_kwargs: object,
) -> FlightShow:
    """
    Run the full pipeline: prompt → SVG → geometry → sampling → constraints → SkyBrush.
    Optionally write the result to output_path.
    """
    # Stage 1: LLM-generated SVG (always saved to top-level svg_files folder; default from project root)
    svg_files_dir = stage_kwargs.get("svg_files_dir")
    if svg_files_dir is not None:
        svg_files_dir = Path(svg_files_dir)
    svg_result = generate_svg(
        prompt,
        llm_call=llm_call,
        canvas_width=stage_kwargs.get("canvas_width", 100),
        canvas_height=stage_kwargs.get("canvas_height", 100),
        svg_files_dir=svg_files_dir,
    )

    # Stage 2: Deterministic geometry processing
    geom_result = process_geometry(
        svg_result.svg_content,
        simplification_tolerance=stage_kwargs.get("simplification_tolerance", 0.5),
        origin_center=stage_kwargs.get("origin_center", True),
        scale_to_meters=stage_kwargs.get("scale_to_meters", 0.01),
    )

    # Stage 3: Poisson disk sampling
    sampling_result = sample_waypoints(
        geom_result.paths,
        min_distance=stage_kwargs.get("min_distance", 1.0),
        path_resolution=stage_kwargs.get("path_resolution"),
    )

    # Stage 4: Physical constraint enforcement
    bounds = geom_result.bounding_box
    constraint_result = enforce_constraints(
        sampling_result.positions,
        max_velocity=stage_kwargs.get("max_velocity", 10.0),
        max_acceleration=stage_kwargs.get("max_acceleration", 5.0),
        default_altitude=stage_kwargs.get("default_altitude", 10.0),
        bounds=(bounds[0], bounds[1], bounds[2], bounds[3]),
        safety_margin=stage_kwargs.get("safety_margin", 0.5),
    )

    # Stage 5: SkyBrush export (bounding box from geometry for Poisson placement)
    flight_show = export_skybrush(
        constraint_result,
        show_name=show_name,
        description=stage_kwargs.get("description", f"Generated from: {prompt}"),
        number_of_drones=stage_kwargs.get("number_of_drones", number_of_drones),
        drone_spacing=stage_kwargs.get("drone_spacing", 5.0),
        bounding_box_xy=geom_result.bounding_box,
        drone_placement_margin=stage_kwargs.get("drone_placement_margin", 0.0),
        drone_placement_expand=stage_kwargs.get("drone_placement_expand", 2.0 * stage_kwargs.get("drone_spacing", 5.0)),
    )

    if output_path is not None:
        write_skybrush_file(flight_show, output_path, as_json=True)

    return flight_show
