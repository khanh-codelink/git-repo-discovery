# Git Repo Discovery

FastAPI backend for Git Repo Discovery.

## Automatically Ruff and Lint check

```
uv sync
pre-commit install

# Optional, run the hooks once on the whole codebase to clean it up:
pre-commit run --all-files
```

Once done, every commit will trigger the Ruff and Lint format when pushing to any remote branchs.

## Prerequisites

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/), a recent version (run `uv self update` if yours is older than 0.12)
- Supabase project URL and anon key

## Setup

Clone the repository and install the project and its development dependencies:

```sh
git clone https://github.com/khanh-codelink/git-repo-discovery.git
cd git-repo-discovery
uv sync
```

`uv sync` creates `.venv` and installs the project into it in editable mode, so code under `src/` is importable as the `src` package from anywhere in the project:

```python
from src.llm import LLMService
from src.config import settings
```

Always import project modules with the `src.` prefix. `from llm import ...` or relative imports such as `from .src.llm import ...` will not resolve.

> If you use conda, run `conda deactivate` first, or stick to `uv sync` / `uv run`. An active conda environment makes `uv pip` install into conda instead of `.venv`.

In VS Code, the committed `.vscode/settings.json` selects `.venv/bin/python` as the interpreter. If imports still show as unresolved, run **Python: Select Interpreter** and pick `.venv/bin/python`.

Create a local environment file from the provided template:

```sh
cp .env-example .env
cp .env-example .env.development
```

Set `SUPABASE_URL` and `SUPABASE_KEY` in `.env` to your Supabase project URL and anon key. The API requires both values when it starts.

Anything that uses `src.config` or `LLMService` also needs `GITHUB_TOKEN` and the Azure OpenAI settings: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_MODEL_NAME` and `AZURE_OPENAI_DEPLOYMENT_NAME`. `AZURE_OPENAI_ENDPOINT_VERSION` is optional. Settings are loaded when first used, and a missing value raises a validation error naming the field.

## Start the development server

From the repository root, run:

```sh
uv run uvicorn src.git_repo_discovery.api.index:app --reload
```

or

```sh
uv run uvicorn src.git_repo_discovery.api.index:app \
  --reload \
  --env-file .env.development
```

The API is available at <http://127.0.0.1:8000>. Open <http://127.0.0.1:8000/docs> for the interactive API documentation. The root endpoint at <http://127.0.0.1:8000/> returns a basic health status.

## Run local scripts

Scripts in `src/local_scripts/` are run as modules from the repository root, so that `.env` is found and `src.*` imports resolve:

```sh
uv run python -m src.local_scripts.git_api
```
