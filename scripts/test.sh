#!/usr/bin/env bash
# Run the Phase 1 backend tests and the dashboard typecheck.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x backend/.venv/bin/python ]]; then
  python3 -m venv backend/.venv
  backend/.venv/bin/python -m pip install --upgrade pip
  backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
fi

(cd backend && "$ROOT/backend/.venv/bin/python" -m pytest)
(cd frontend && npm run typecheck && npm run lint)
