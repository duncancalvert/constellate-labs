"""Stage 1: LLM-generated SVG (ENG_SPEC §3.1)."""

import re
from typing import Callable

from constellate_labs.models import SvgResult


def _default_llm_adapter(prompt: str) -> str:
    """Placeholder when no LLM is configured: return a simple circle SVG."""
    return _fallback_circle_svg()


def _fallback_circle_svg() -> str:
    """Return a minimal valid SVG (circle) for testing/fallback."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="none" stroke="green" stroke-width="2"/>
</svg>"""


def _extract_svg_from_response(text: str) -> str | None:
    """Extract first valid SVG block from LLM response (e.g. markdown code block)."""
    # Try code block first
    match = re.search(r"```(?:svg|xml)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Try <svg>...</svg>
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
) -> SvgResult:
    """
    Convert natural language prompt to SVG via LLM (or fallback).
    """
    llm = llm_call or _default_llm_adapter
    system_prompt = (
        "You are a helpful assistant that generates SVG graphics. "
        "Given a description, output only valid SVG markup (2D only, no 3D). "
        f"Use viewBox and dimensions consistent with a canvas of {canvas_width}x{canvas_height}. "
        "Prefer simple paths and shapes. Output the SVG inside a markdown code block."
    )
    user_content = f"Generate an SVG for: {prompt}"
    full_prompt = f"{system_prompt}\n\n{user_content}"
    response = llm(full_prompt)
    raw_svg = _extract_svg_from_response(response)
    if raw_svg is None or not _validate_svg_basic(raw_svg):
        raw_svg = _fallback_circle_svg()
    metadata = {
        "prompt": prompt,
        "canvas_width": canvas_width,
        "canvas_height": canvas_height,
    }
    return SvgResult(svg_content=raw_svg, metadata=metadata)
