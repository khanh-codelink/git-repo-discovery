# Git Repo Discovery

FastAPI backend for Git Repo Discovery.

## Prerequisites

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Supabase project URL and anon key

## Setup

Clone the repository and enter its directory, then install the project and its development dependencies:

```sh
uv sync
```

Create a local environment file from the provided template:

```sh
cp .env-example .env
```

Set `SUPABASE_URL` and `SUPABASE_KEY` in `.env` to your Supabase project URL and anon key. The API requires both values when it starts.

## Start the development server

From the repository root, run:

```sh
uv run uvicorn src.git_repo_discovery.api.index:app --reload
```

The API is available at <http://127.0.0.1:8000>. Open <http://127.0.0.1:8000/docs> for the interactive API documentation. The root endpoint at <http://127.0.0.1:8000/> returns a basic health status.
