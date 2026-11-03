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

Anything that uses `src.config` or `LLMService` also needs `GITHUB_TOKEN` and the Azure OpenAI settings: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_MODEL_NAME` and `AZURE_OPENAI_DEPLOYMENT_NAME`. `AZURE_OPENAI_API_VERSION` is optional. Settings are loaded when first used, and a missing value raises a validation error naming the field.

## Run tests

Run the test suite from the repository root:

```sh
uv run pytest
```

Run only the unit or integration tests:

```sh
uv run pytest src/tests/unit
uv run pytest src/tests/integration
```

## Start the development server

From the repository root, run:

```sh
uv run uvicorn src.main:app --reload
```

or

```sh
uv run uvicorn src.main:app \
  --reload \
  --env-file .env.development
```

The API is available at <http://127.0.0.1:8000>. Open <http://127.0.0.1:8000/docs> for the interactive API documentation. The root endpoint at <http://127.0.0.1:8000/> returns a basic health status.

## Azure container deployment

The Docker image uses Python 3.13 and listens on port 3000 by default. Local environment files are excluded from the image; supply settings at runtime.

Build and run locally:

```sh
docker build --platform linux/amd64 -t git-repo-discovery .
docker run --rm -p 3000:3000 --env-file .env git-repo-discovery
```

The API is available at <http://localhost:3000>.

Build locally with Docker and push to the `gitdiscover` Azure Container Registry (no Azure-hosted build required). Install the Azure CLI, start Docker, and sign in to the subscription containing the registry:

```sh
az login
bash build-and-push.sh
```

The script builds for `linux/amd64`, authenticates Docker to the registry, tags the image using the registry's login server, and pushes `git-repo-discovery:latest`. Your Azure account needs permission to push images to `gitdiscover`.

To push a versioned tag instead:

```sh
bash build-and-push.sh v1.0.0
```

For Azure Container Apps, set the ingress target port to `3000`. For Azure App Service using a classic custom container, set `WEBSITES_PORT=3000`; for a sidecar-enabled app, set the container's target port to `3000`. Configure the required environment variables or secrets in Azure. The optional `PORT` environment variable overrides the listening port; keep the Azure target port aligned with it.

### GitHub Actions deployment to Azure Container Apps

[.github/workflows/azure-deploy.yml](.github/workflows/azure-deploy.yml) builds the existing Dockerfile on pushes to `main` or a manual **Actions > Build and deploy to Azure > Run workflow** run. It pushes a commit-tagged `linux/amd64` image to Azure Container Registry (ACR), deploys its immutable digest to an existing Container App, and checks `GET /`. Change the branch trigger if your default branch is not `main`.

This workflow targets **Azure Container Apps**, not Azure App Service. It updates the image without replacing runtime environment variables or secrets. It does not create infrastructure or run database migrations.

#### 1. Create the Azure resources

In the [Azure portal](https://portal.azure.com), create or select a resource group, an ACR (Basic SKU is sufficient), a Container Apps environment, and a Container App in the same subscription. The registry name must be globally unique; `gitdiscover` is the name used by the local build script, but the workflow accepts any registry name.

For a new Container App, first use the public image `mcr.microsoft.com/azuredocs/containerapps-helloworld:latest` with external HTTP ingress targeting port `80`. This lets you create the app before its private image exists. Keep **single revision mode** so new revisions receive traffic automatically. Before the first workflow run, change the ingress target port to `3000` and configure the app settings below. The placeholder image will stop serving on the new port until the real app is deployed.

Enable the Container App's **Settings > Identity > System assigned** identity. Copy its object/principal ID. On the ACR's **Access control (IAM)** page, grant that identity **AcrPull**, scoped to the registry. Configure the Container App's registry authentication to use that managed identity, not an ACR admin password. With Azure CLI installed and after `az login`:

```sh
az extension add --name containerapp --upgrade
az containerapp registry set \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_CONTAINER_APP_NAME \
  --server YOUR_REGISTRY_LOGIN_SERVER \
  --identity system
```

Find the registry login server on **ACR > Overview** (for example, `gitdiscover.azurecr.io`); use the actual value shown, not a guessed hostname. These role instructions assume ACR's **RBAC Registry Permissions** mode. For an ABAC-enabled registry, use **Container Registry Repository Reader** for the app and **Container Registry Repository Writer** for the workflow identity instead of `AcrPull` and `AcrPush`.

#### 2. Configure passwordless GitHub access to Azure

In **Microsoft Entra ID > App registrations > New registration**, register an application for this workflow. On its **Overview** page, copy the application (client) ID and directory (tenant) ID. No client secret is needed.

Under **Certificates & secrets > Federated credentials > Add credential**, choose **GitHub Actions deploying Azure resources**, enter the GitHub owner and repository, choose entity type **Environment**, and enter `production`. The credential must match:

```text
Issuer:   https://token.actions.githubusercontent.com
Subject:  repo:YOUR_GITHUB_OWNER/YOUR_REPOSITORY:environment:production
Audience: api://AzureADTokenExchange
```

On the resource group's **Access control (IAM)** page, assign the application's service principal **Contributor**, scoped to that resource group. On the registry's IAM page, assign it **AcrPush**, scoped to that registry. This workflow identity is separate from the Container App's pull identity. Contributor does not let the workflow grant roles; a resource owner or role-assignment administrator must perform the initial role assignments.

In GitHub, create **Settings > Environments > production**. Limit deployment branches to `main` (and optionally require approval); if you allow manual deployment from another branch, explicitly allow it here too. Add the following environment secrets and variables. Azure IDs are identifiers rather than passwords, but this workflow reads them from GitHub secrets.

| GitHub environment secret | Where to find it |
| --- | --- |
| `AZURE_CLIENT_ID` | Entra ID > App registrations > your workflow application > Overview > Application (client) ID. |
| `AZURE_TENANT_ID` | The same Overview page > Directory (tenant) ID. |
| `AZURE_SUBSCRIPTION_ID` | Azure portal > Subscriptions > subscription containing the resources > Subscription ID. |

| GitHub environment variable | Where to find it |
| --- | --- |
| `AZURE_RESOURCE_GROUP` | Azure portal > Resource groups > the group containing both ACR and the Container App > name. |
| `AZURE_ACR_NAME` | ACR > Overview > registry name, for example `gitdiscover`; not the login server URL. |
| `AZURE_CONTAINER_APP_NAME` | Container Apps > your app > Overview > app name. |

Do not configure `AZURE_CREDENTIALS`, an Azure client secret, or an ACR password; login uses GitHub OIDC and image pulls use managed identity.

#### 3. Configure application environment variables in Azure

Add sensitive values under **Container App > Settings > Secrets**, using names such as `github-token`, `supabase-key`, and `azure-openai-api-key`. Then add the environment variables under **Application > Containers > Edit and deploy > Environment variables**, selecting **Secret reference** for sensitive values. Save/deploy the configuration before running the workflow. Never bake these values into the Docker image or pass them as build arguments.

| Runtime environment variable | Required? | Where to find the value |
| --- | --- | --- |
| `GITHUB_TOKEN` | Yes; secret reference | GitHub account Settings > Developer settings > Personal access tokens. Use a PAT with read access to the repositories you want to search; private repositories need explicit repository access and any required organization authorization. This is not the automatic Actions `GITHUB_TOKEN`. |
| `SUPABASE_URL` | Yes | Supabase project > Settings > API (or Connect) > Project URL, normally `https://<project-ref>.supabase.co`. |
| `SUPABASE_KEY` | Yes; secret reference | Supabase project > Settings > API Keys > legacy `anon` key, as used by this app's existing setup. It needs access to the app tables through your RLS policies. Do not switch to the elevated `service_role` key without reviewing authorization. |
| `AZURE_OPENAI_API_KEY` | Yes; secret reference | Azure OpenAI resource > Resource Management > Keys and Endpoint (also available in the Azure AI Foundry portal). |
| `AZURE_OPENAI_ENDPOINT` | Yes | The same Keys and Endpoint page; use the resource endpoint, for example `https://<resource>.openai.azure.com/`. |
| `AZURE_OPENAI_MODEL_NAME` | Yes | Azure AI Foundry > your Azure OpenAI deployment > underlying model name, for example `gpt-4.1-mini`. |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Yes | The deployment name you chose in Azure AI Foundry; it may differ from the underlying model name. |
| `AZURE_OPENAI_API_VERSION` | Optional, recommended | A supported Azure OpenAI API version for your deployment; find supported versions in the [Azure OpenAI API reference](https://learn.microsoft.com/azure/ai-foundry/openai/reference). The code defaults to `2023-06-01-preview`, which may be too old for your chosen model. Use `ENDPOINT_VERSION`, not `AZURE_OPENAI_API_VERSION`. |
| `FE_APP_DOMAIN` | Needed for your hosted frontend's CORS | Your frontend's origin, for example `https://your-frontend.vercel.app`; include the scheme, without a path or trailing slash. |
| `PORT` | Optional | Defaults to `3000` in the image. If overridden, also change the Container App ingress target port. `WEBSITES_PORT` is not needed for Container Apps. |
| `DATABASE_URL` | Migrations only; secret | Supabase > Connect > Session pooler > PostgreSQL connection string on port `5432`. Not needed by this deployment workflow or the running API. |

Run `uv run alembic upgrade head` separately with `DATABASE_URL` before using database-backed routes on a new database. Then push to `main` or run the workflow manually. The Actions run summary shows the deployed URL; visit `/docs` to inspect the API. A successful root health check only confirms the HTTP server responds, not that GitHub, OpenAI, or database credentials work.

## Database migrations

Alembic manages the Supabase tables created by this backend (`summaries` and `comparisons`). Migrations live in `alembic/versions/` and are written by hand, because the app uses `supabase-py` rather than SQLAlchemy models, so `--autogenerate` has nothing to compare against.

Set `DATABASE_URL` in `.env` to the session pooler connection string from the Supabase dashboard (**Connect** → **Session pooler**, port 5432). The direct connection only works over IPv6, and the transaction pooler (port 6543) is not suited to migrations. URL-encode special characters in the password.

```sh
uv run alembic upgrade head          # apply all migrations
uv run alembic current               # show the applied revision
uv run alembic downgrade -1          # roll back the latest migration
uv run alembic upgrade head --sql    # print the SQL without running it
uv run alembic revision -m "describe the change"   # start a new migration
```

Alembic records the applied revision in `alembic.alembic_version`, a separate schema the Supabase Data API does not expose.
