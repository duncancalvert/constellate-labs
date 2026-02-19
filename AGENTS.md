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


## Conventions
* Keep Ruff and pytest config in `pyproject.toml` under `[tool.ruff]` and `[tool.pytest.ini_options]`.
* Use `*` for bullet lists
* Keep the README updated when new code is written and it materially changes how a user may interact with the code
