# Constellate Labs

This is an open-source text-to-drone flight map software. Describe any  object or pattern in text (i.e. "a green dragon") and Constellate Labs turns it into a drone light show flight map that is congruent with Skybrush Studio.

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

### Step 3: Create a virtual environment and install dependencies with uv (uv uses a `.venv` in the project by default):
This does the following:
* Creates a `.venv` file
* Installs the dependencies listed in the pyproject.toml
* Syncs the uv lockfile.

For PROD dependencies only:
```bash
uv sync
```

For PROD + DEV dependencies:
```bash
uv sync --extra dev
```

3. (Optional) Use the venv directly:

   ```bash
   source .venv/bin/activate   # macOS/Linux
   # or: .venv\Scripts\activate  # Windows
   ```

   Or run commands via uv so the project env is used automatically:

   ```bash
   uv run python -c "print('hello')"
   ```

## Development

### Linting (Ruff)

- Lint:
  ```bash
  uv run ruff check .
  ```
- Format:
  ```bash
  uv run ruff format .
  ```

### Tests (pytest)

- Run all tests:
  ```bash
  uv run pytest
  ```
- Run with verbose output:
  ```bash
  uv run pytest -v
  ```
- Run a specific file or directory:
  ```bash
  uv run pytest tests/
  ```

### Adding dependencies

- Production dependency:
  ```bash
  uv add <package>
  ```
- Dev dependency (e.g. pytest, ruff):
  ```bash
  uv add --dev <package>
  ```

## Project layout

- `pyproject.toml` — project metadata, dependencies, and tool config (Ruff, pytest)
- `AGENTS.md` — context for AI agents and contributors
- `tests/` — pytest test suite

## License

MIT. See [LICENSE](LICENSE).
