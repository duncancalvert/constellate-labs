"""Stage 1: LLM-generated SVG (ENG_SPEC §3.1)."""

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Literal

import vertexai
from vertexai.generative_models import GenerativeModel

from constellate_labs.models import SvgResult


@dataclass
class LLMConfig:
    """
    Configurable LLM backend for SVG generation.
    Use with build_llm_call() to get a callable for generate_svg(llm_call=...).
    """
    provider: Literal["on_prem", "gcp"]
    model_name: str
    model_version: str | None = None
    # On-prem (OpenAI-compatible endpoint, e.g. Ollama, LM Studio, vLLM)
    base_url: str = "http://localhost:11434"
    api_key: str | None = None
    # GCP Vertex AI / Model Garden
    project_id: str = ""
    location: str = "us-central1"
    endpoint_id: str | None = None  # reserved for future deployed-endpoint support


def _default_llm_adapter(prompt: str) -> str:
    """
    Placeholder when no LLM is configured: return a simple circle SVG.
    """
    return _fallback_circle_svg()


def _fallback_circle_svg() -> str:
    """
    Return a minimal valid SVG (circle) for testing/fallback
    when an actual LLM call is not configured.
    """
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="none" stroke="green" stroke-width="2"/>
</svg>"""


def _call_on_prem(config: LLMConfig, prompt: str) -> str:
    """Call an OpenAI-compatible chat endpoint (on-prem or local model)."""
    url = config.base_url.rstrip("/") + "/v1/chat/completions"
    model = config.model_name
    if config.model_version:
        model = f"{config.model_name}@{config.model_version}"
    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LLM request failed ({e.code}): {e.read().decode()}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"LLM request failed: {e.reason}") from e
    choices = out.get("choices") or []
    if not choices:
        raise RuntimeError("LLM returned no choices")
    content = choices[0].get("message", {}).get("content") or ""
    return content


def _call_gcp(config: LLMConfig, prompt: str) -> str:
    """Call GCP Vertex AI / Model Garden (GenerativeModel by model name)."""

    if not config.project_id:
        raise ValueError("LLMConfig(provider='gcp') requires project_id")
    vertexai.init(project=config.project_id, location=config.location)
    model_id = config.model_name
    if config.model_version:
        model_id = f"{config.model_name}@{config.model_version}"
    model = GenerativeModel(model_id)
    response = model.generate_content(prompt)
    if not response.candidates or not response.candidates[0].content.parts:
        raise RuntimeError("GCP model returned no content")
    return response.candidates[0].content.parts[0].text


def build_llm_call(config: LLMConfig) -> Callable[[str], str]:
    """
    Build a callable that invokes the configured LLM (on-prem or GCP).
    Use as generate_svg(..., llm_call=build_llm_call(my_config)).
    """
    if config.provider == "on_prem":
        def _call(prompt: str) -> str:
            return _call_on_prem(config, prompt)
        return _call
    if config.provider == "gcp":
        def _call(prompt: str) -> str:
            return _call_gcp(config, prompt)
        return _call
    raise ValueError(f"Unknown LLM provider: {config.provider}")


def _extract_svg_from_response(text: str) -> str | None:
    """
    Extract first valid SVG block from LLM response (e.g. markdown code block).
    """
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
) -> SvgResult:
    """
    Convert natural language prompt to SVG via LLM (or fallback).
    Pass llm_call=build_llm_call(LLMConfig(...)) to use an on-prem or GCP model.
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
