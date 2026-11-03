#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
registry_name="gitdiscover"
image_name="git-repo-discovery"
image_tag="${1:-latest}"

for executable in docker az; do
    if ! command -v "$executable" >/dev/null 2>&1; then
        printf 'Required command not found: %s\n' "$executable" >&2
        exit 1
    fi
done

docker info >/dev/null
registry_server="$(az acr show --name "$registry_name" --query loginServer --output tsv)"
if [[ -z "$registry_server" ]]; then
    printf 'Could not resolve the login server for registry %s.\n' "$registry_name" >&2
    exit 1
fi

local_image="${image_name}:${image_tag}"
remote_image="${registry_server}/${local_image}"

az acr login --name "$registry_name"
docker build --platform linux/amd64 --tag "$local_image" "$project_root"
docker tag "$local_image" "$remote_image"
docker push "$remote_image"

printf 'Pushed %s\n' "$remote_image"