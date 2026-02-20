"""Tests for pipeline stages and runner."""

import json
from pathlib import Path

import numpy as np
import pytest

from constellate_labs.models import ProcessedPath
from constellate_labs.pipeline import (
    OpenAILLMConfig,
    build_llm_call,
    enforce_constraints,
    export_skybrush,
    generate_svg,
    process_geometry,
    run_pipeline,
    sample_waypoints,
)


def test_stage1_requires_llm() -> None:
    """generate_svg raises when llm_call is not configured."""
    with pytest.raises(ValueError, match="LLM is not configured"):
        generate_svg("a green dragon", llm_call=None)


def test_stage1_custom_llm(tmp_path: Path) -> None:
    def mock_llm(prompt: str) -> str:
        return '```svg\n<svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40"/></svg>\n```'

    result = generate_svg("circle", llm_call=mock_llm, svg_files_dir=tmp_path)
    assert "circle" in result.svg_content
    assert result.metadata["prompt"] == "circle"
    svg_file = tmp_path / "stage1_output.svg"
    assert svg_file.exists()
    assert "circle" in svg_file.read_text()


def test_build_llm_call_openai_returns_callable() -> None:
    config = OpenAILLMConfig(model="gpt-4o")
    callable_ = build_llm_call(config)
    assert callable(callable_)


def test_stage2_process_geometry() -> None:
    svg = """<?xml version="1.0"?>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="40"/>
    </svg>"""
    result = process_geometry(svg)
    assert len(result.paths) >= 1
    assert result.bounding_box[0] <= result.bounding_box[2]
    assert result.bounding_box[1] <= result.bounding_box[3]


def test_stage3_sample_waypoints() -> None:
    path = ProcessedPath(
        points=np.array([[0.0, 0.0], [5.0, 0.0], [5.0, 5.0]]),
        is_closed=False,
        metadata={},
    )
    result = sample_waypoints([path], min_distance=1.0)
    assert result.positions.shape[0] >= 2
    assert result.positions.shape[1] == 2
    assert result.metadata["total_waypoints"] == result.positions.shape[0]


def test_stage4_enforce_constraints() -> None:
    positions = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    result = enforce_constraints(positions, max_velocity=10.0)
    assert len(result.waypoints) == 3
    assert result.waypoints[0].z == 10.0
    assert len(result.velocity_profile) == 3


def test_stage5_export_skybrush() -> None:
    positions = np.array([[0.0, 0.0], [1.0, 0.0]])
    constraint_result = enforce_constraints(positions)
    flight_show = export_skybrush(constraint_result, show_name="Test")
    assert flight_show.skybrush_format["name"] == "Test"
    assert "trajectories" in flight_show.skybrush_format
    assert len(flight_show.skybrush_format["trajectories"]) >= 1
    pts = flight_show.skybrush_format["trajectories"][0]["points"]
    assert len(pts) == 2


def test_run_pipeline_e2e(tmp_path: Path) -> None:
    def mock_llm(prompt: str) -> str:
        return '```svg\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40"/></svg>\n```'

    out = tmp_path / "show.json"
    show = run_pipeline(
        "a simple circle",
        llm_call=mock_llm,
        output_path=str(out),
        svg_files_dir=tmp_path,
    )
    assert len(show.waypoints) >= 1
    assert show.skybrush_format["trajectories"]
    assert out.read_text()
    data = json.loads(out.read_text())
    assert data["name"] == "Constellate Show"
    assert "trajectories" in data
    # Stage 1 SVG is always saved to svg_files dir (we passed tmp_path for test)
    assert (tmp_path / "stage1_output.svg").exists()
