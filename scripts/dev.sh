#!/usr/bin/env bash
# Start the API and the dashboard on loopback.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')"
  cat > .env <<EOF
QUBIT_SECRET_KEY=${secret}
QUBIT_ADMIN_USERNAME=admin
QUBIT_ADMIN_PASSWORD=${password}
QUBIT_HOST=127.0.0.1
QUBIT_PORT=8000
QUBIT_LOG_LEVEL=INFO
EOF
  chmod 600 .env
  echo "Wrote .env"
  echo "Administrator username: admin"
  echo "Administrator password: ${password}"
fi

if [[ ! -x backend/.venv/bin/python ]]; then
  python3 -m venv backend/.venv
fi
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements.txt

if [[ ! -d frontend/node_modules ]]; then
  (cd frontend && npm install)
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

cleanup() {
  trap - EXIT INT TERM
  if [[ -n "${BACK_PID:-}" ]]; then kill "${BACK_PID}" 2>/dev/null || true; fi
  if [[ -n "${FRONT_PID:-}" ]]; then kill "${FRONT_PID}" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

(
  cd backend
  exec "$ROOT/backend/.venv/bin/uvicorn" app.main:app --host "${QUBIT_HOST:-127.0.0.1}" --port "${QUBIT_PORT:-8000}"
) &
BACK_PID=$!

(
  cd frontend
  exec npm run dev
) &
FRONT_PID=$!

echo "API:       http://127.0.0.1:${QUBIT_PORT:-8000}/health"
echo "Dashboard: http://127.0.0.1:3000"
wait
