# Agent guidance for Constellate Labs

This file gives AI agents and contributors consistent context for working on the repo.

## Project

* **Constellate Labs**: Open-source text-to-drone flight map software. Users describe an object or pattern; the system generates a drone light show flight map from that description.

## Tooling

* **Package manager**: [uv](https://docs.astral.sh/uv/)
* **Virtual environment**: Python `venv` (uv creates and uses `.venv` by default)
* **Linting/formatting**: [Ruff](https://docs.astral.sh/ruff/)
* **Tests**: [pytest](https://docs.pytest.org/)

## Commands

* Create venv and install production deps: `uv sync`
* Install production + dev deps: `uv sync --extra dev`
* To lint: `uv run ruff check .` and `uv run ruff format .`
* Run tests: `uv run pytest` or `uv run pytest tests/`
* Add production deps with `uv add <package>`, dev deps with `uv add --dev <package>`.
* Prefer `uv run` for one-off commands so they use the project venv.


## Code layout
* Pipeline stages live in `src/constellate_labs/pipeline/` (stage1_llm_svg through stage5_skybrush, plus runner).
* Stage 1 LLM: `OpenAILLMConfig` and `build_llm_call()` use the OpenAI Responses API (MVP). An LLM must be configured; omitting `llm_call` raises an error. Stage 1 always writes the generated SVG to the top-level `svg_files/` directory (same level as `src/`); override with `svg_files_dir` in `run_pipeline(..., **stage_kwargs)` or `generate_svg(..., svg_files_dir=...)`.
* Reusable helpers live in `src/constellate_labs/utils/` (geometry, sampling, validation).
* Data models are in `src/constellate_labs/models.py`. Keep stages modular and use utils for shared logic.

## Conventions
* Keep Ruff and pytest config in `pyproject.toml` under `[tool.ruff]` and `[tool.pytest.ini_options]`.
* Use `*` for bullet lists.
* All imports should go at the top of the file
* Follow PEP8 Python standards
* Keep the README.md, ENG_SPEC.md, and AGENTS.md files updated when new code is written and it may change the documentation in those documents.
* Ensure function docstrings clearly describe all input parameters (on their own lines), all output values returned, as well as a clear description of what the function is used for
