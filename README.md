# Constellate Labs

This is an open-source text-to-drone flight map software. Describe any  object or pattern in text (i.e. "a green dragon") and Constellate Labs turns it into a drone light show flight map that is congruent with Skybrush Studio.

Pipeline steps (see [ENG_SPEC.md](ENG_SPEC.md) for details):
1. LLM-generated SVG
2. Deterministic geometry processing
3. Poisson disk sampling
4. Physical constraint enforcement
5. SkyBrush export

## Requirements
* Python 3.10+
* [uv](https://docs.astral.sh/uv/installation/) for package management
* ruff for linting
* pytest for testing
* pyproject.toml for project dependencies

## Setup

### 1. Clone the repo and enter the project directory.

### 2. Install uv
On Mac this can be handled via
```bash
brew install uv
```

### 3. Create a virtual environment (`.venv`) and install dependencies with uv
The below commands do the following:
* Create a `.venv` file
* Install the dependencies listed in the pyproject.toml
* Syncs the uv lockfile.

For PROD dependencies only:
```bash
uv sync
```

For PROD + DEV dependencies:
```bash
uv sync --extra dev
```

## Development

### Linting (Ruff)

Use the following command to lint:
```bash
uv run ruff check .
```

Use the following command to format:
```bash
uv run ruff format .
```

### Testing (pytest)

Run all tests:
```bash
uv run pytest
```

Run with verbose output:
```bash
uv run pytest -v
```

Run a specific file or directory:
```bash
uv run pytest tests/
```

### Adding dependencies

Production dependency:
```bash
uv add <package>
```
-Dev dependency (e.g. pytest, ruff):
```bash
uv add --dev <package>
```

## Usage

Run the full pipeline from a natural language prompt and write a SkyBrush-compatible JSON file. An LLM must be configured for Stage 1 (no fallback); pass `llm_call=build_llm_call(OpenAILLMConfig(...))` and set `OPENAI_API_KEY` (or pass `api_key` in config).

```python
from constellate_labs import run_pipeline
from constellate_labs.pipeline import OpenAILLMConfig, build_llm_call

config = OpenAILLMConfig(model="gpt-4o")  # or "gpt-5.2" etc.; api_key from env if not set
show = run_pipeline(
    "a simple circle",
    llm_call=build_llm_call(config),
    output_path="show.json",
    show_name="My Show",
    number_of_drones=1,  # optional; default 1
)
```

You can pass more options as keyword arguments (e.g. `canvas_width`, `canvas_height`, `drone_spacing`, `min_distance`, `max_velocity`, `default_altitude`, `drone_placement_expand`). See `experiment_notebooks/02_pipeline_integration_test.ipynb` for a full list.

Stages can also be used individually (see `constellate_labs.pipeline` and `constellate_labs.utils`).

### LLM configuration (Stage 1)

Stage 1 uses the **OpenAI Responses API** (MVP). An LLM must be configured; if `llm_call` is not provided, Stage 1 raises an error.

* **OpenAI**: Use `OpenAILLMConfig(model="gpt-4o", api_key=None, base_url=None)`. `api_key` defaults to `OPENAI_API_KEY`; `base_url` is optional for custom endpoints. Pass `llm_call=build_llm_call(config)` to `generate_svg` or `run_pipeline`.

## Project layout

* `pyproject.toml`
  * project metadata
  * dependencies
  * tool config (ruff, pytest)
* `AGENTS.md`
  * context for AI agents and contributors
* `ENG_SPEC.md`
  * engineering specification and pipeline details
* `tests/`
  * pytest test modules
* `svg_files/`
  * Stage 1 generated SVG output (top-level, same level as `src/`)
* `src/constellate_labs/`
  * `models.py` — data types (Waypoint, ProcessedPath, FlightShow, etc.)
  * `utils/` — geometry, sampling, and validation helpers
  * `pipeline/` — pipeline stages (LLM SVG, geometry, Poisson sampling, constraints, SkyBrush export)
  * `pipeline/runner.py` — `run_pipeline()` entrypoint


## License

MIT. See [LICENSE](LICENSE).
