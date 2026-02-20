"""Stage 1: LLM-generated SVG (ENG_SPEC §3.1)."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from openai import OpenAI

from constellate_labs.models import SvgResult


def _project_root() -> Path:
    """Project root (repo root, same level as src/). Resolved from this file's location."""
    # .../src/constellate_labs/pipeline/stage1_llm_svg.py -> .../ (project root)
    return Path(__file__).resolve().parents[4]


def _default_svg_files_dir() -> Path:
    """Top-level svg_files directory in the project (same level as src/)."""
    return _project_root() / "svg_files"


@dataclass
class OpenAILLMConfig:
    """
    Configuration for the OpenAI Responses API (Stage 1 LLM).
    Use with build_llm_call() to get a callable for generate_svg(llm_call=...).
    """
    model: str = "gpt-4o"
    api_key: str | None = None
    base_url: str | None = None


def _call_openai(config: OpenAILLMConfig, prompt: str) -> str:
    """Call OpenAI Responses API and return the output text."""
    kwargs = {}
    if config.api_key is not None:
        kwargs["api_key"] = config.api_key
    if config.base_url is not None:
        kwargs["base_url"] = config.base_url
    client = OpenAI(**kwargs)
    response = client.responses.create(
        model=config.model,
        input=prompt,
    )
    return response.output_text or ""


def build_llm_call(config: OpenAILLMConfig) -> Callable[[str], str]:
    """
    Build a callable that invokes the OpenAI Responses API.
    Use as generate_svg(..., llm_call=build_llm_call(config)).
    """

    def _call(prompt: str) -> str:
        return _call_openai(config, prompt)

    return _call


def _extract_svg_from_response(text: str) -> str | None:
    """Extract first valid SVG block from LLM response (e.g. markdown code block)."""
    match = re.search(r"```(?:svg|xml)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"<svg[\s\S]*?</svg>", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(0)
    if "<svg" in text and "</svg>" in text:
        start = text.index("<svg")
        end = text.index("</svg>") + len("</svg>")
        return text[start:end]
    return None


def _validate_svg_basic(svg: str) -> bool:
    """Basic sanity check: has <svg and </svg>, no null bytes."""
    if not svg or "\x00" in svg:
        return False
    return "<svg" in svg.lower() and "</svg>" in svg.lower()


def generate_svg(
    prompt: str,
    *,
    llm_call: Callable[[str], str] | None = None,
    canvas_width: int = 100,
    canvas_height: int = 100,
    svg_files_dir: str | Path | None = None,
) -> SvgResult:
    """
    Convert natural language prompt to SVG via the OpenAI LLM.
    Pass llm_call=build_llm_call(OpenAILLMConfig(...)) to use the OpenAI API.
    The generated SVG is always written to the svg_files folder (default: top-level "svg_files").
    """
    if llm_call is None:
        raise ValueError(
            "LLM is not configured. Pass llm_call=build_llm_call(OpenAILLMConfig(...)) "
            "to generate_svg or run_pipeline, or set OPENAI_API_KEY and use build_llm_call(OpenAILLMConfig())."
        )
    system_prompt = (
        "You are a helpful assistant that generates SVG graphics. "
        "Given a description, output only valid SVG markup (2D only, no 3D). "
        f"Use viewBox and dimensions consistent with a canvas of {canvas_width}x{canvas_height}. "
        "Prefer simple paths and shapes. Output the SVG inside a markdown code block."
    )
    user_content = f"Generate an SVG for: {prompt}"
    full_prompt = f"{system_prompt}\n\n{user_content}"
    response = llm_call(full_prompt)
    raw_svg = _extract_svg_from_response(response)
    if raw_svg is None or not _validate_svg_basic(raw_svg):
        raise ValueError(
            "LLM did not return valid SVG. Ensure the model outputs SVG markup (e.g. inside a markdown code block)."
        )

    # Always save SVG to the svg_files folder (top-level in project, same level as src)
    svg_dir = Path(svg_files_dir) if svg_files_dir is not None else _default_svg_files_dir()
    svg_dir.mkdir(parents=True, exist_ok=True)
    svg_file = svg_dir / "stage1_output.svg"
    svg_file.write_text(raw_svg, encoding="utf-8")

    metadata = {
        "prompt": prompt,
        "canvas_width": canvas_width,
        "canvas_height": canvas_height,
        "svg_path": str(svg_file.resolve()),
    }
    return SvgResult(svg_content=raw_svg, metadata=metadata)
