# Development

## Layout

```
backend/app          FastAPI application
backend/tests        pytest suite
frontend/src         Next.js dashboard
scripts/dev.sh       Linux and macOS startup
scripts/dev.ps1      Windows startup
scripts/test.sh      Backend tests plus frontend typecheck and lint
```

## Environment

Copy `.env.example` to `.env`. Variables use the `QUBIT_` prefix.

| Variable | Purpose |
| --- | --- |
| `QUBIT_SECRET_KEY` | Session signing material. Set a long random value. |
| `QUBIT_ADMIN_USERNAME` | First account name, used only when the database is empty |
| `QUBIT_ADMIN_PASSWORD` | First account password, at least 8 characters |
| `QUBIT_HOST` | Bind address. Keep `127.0.0.1` |
| `QUBIT_PORT` | API port, default `8000` |
| `QUBIT_DATABASE_URL` | `sqlite:///...` only |
| `QUBIT_MEDIA_DIR` | Upload storage |
| `QUBIT_MAX_UPLOAD_BYTES` | Upload ceiling |
| `QUBIT_CORS_ORIGINS` | Browser origins for direct API calls |
| `QUBIT_TOKEN_TTL_HOURS` | Session lifetime |
| `QUBIT_LOG_LEVEL` | Python log level |

Changing the admin password in `.env` does not update an existing database. From `backend/`:

```bash
../backend/.venv/bin/python -m app.cli reset-admin --password 'a-new-password'
```

The generated password file `backend/data/initial-admin-password.txt` appears only when the server had to invent a password. Delete it after saving the password somewhere else.

## Backend

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
cd backend && .venv/bin/python -m pytest
cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Ubuntu needs the `python3-venv` package to create the virtualenv. FFmpeg must provide `ffmpeg` and `ffprobe` on `PATH`.

## Dashboard

```bash
cd frontend
npm install
npm run dev
npm run typecheck
npm run lint
npm run build
```

The dev server proxies `/backend/*` to `http://127.0.0.1:8000`. Override the target with `API_PROXY_TARGET`. The status socket uses `NEXT_PUBLIC_API_PORT` when the API is not on 8000.

## Windows notes

Install Python 3.11+, Node.js 18+, and FFmpeg, then open a new terminal. `scripts/dev.ps1` looks for the `py` launcher and for `python.exe` outside the Microsoft Store alias. It creates `backend\.venv`, installs dependencies, and opens two windows: the API and the dashboard. If the first run happened before Python existed, the script replaces an `.env` whose password is blank.

Display code in `backend/app/services/displays/windows.py` is the Win32 path. It has not been executed in the Linux test environment. Playback is not part of this phase, and a future playback window has to run in an interactive user session rather than as a service with no desktop.

## CI

`.github/workflows/ci.yml` installs FFmpeg, runs pytest, then typechecks, lints, and builds the dashboard.

## Things the tests do not prove

- A physical HDMI or DisplayPort panel
- The Windows display enumeration path
- GPU decode
- Frame-accurate multi-output sync
- Behavior of a Colorlight or NovaStar processor
