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
* Stage 1 LLM: `LLMConfig` and `build_llm_call()` support on-prem (OpenAI-compatible) and GCP Vertex AI / Model Garden; GCP support is included in production dependencies.
* Reusable helpers live in `src/constellate_labs/utils/` (geometry, sampling, validation).
* Data models are in `src/constellate_labs/models.py`. Keep stages modular and use utils for shared logic.

## Conventions
* Keep Ruff and pytest config in `pyproject.toml` under `[tool.ruff]` and `[tool.pytest.ini_options]`.
* Use `*` for bullet lists.
* Keep the README.md, ENG_SPEC.md, and AGENTS.md files updated when new code is written and it may change the documentation in those documents.
