#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

uv run --project services/gateway-api --group dev pytest services/gateway-api/tests "$@"
uv run --project services/evaluator --group dev pytest services/evaluator/tests "$@"
