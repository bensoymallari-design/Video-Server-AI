# Qubit AI Media Server

Phase 1 foundation for a local, AI-assisted LED and multi-display media server. This build runs a Next.js control surface and a FastAPI service on the same computer. It stores media, inspects it with FFprobe, and reads the operating-system display layout. It does not play video to an output, call a language model, or talk to an LED processor.

The Git remote for this work is [Video-Server-AI](https://github.com/bensoymallari-design/Video-Server-AI). A separate repository named Qubit-AI-Media-Server was not created.

## What this build does

- Username and password sessions, with admin, operator, and viewer roles
- Health checks for the database, FFmpeg, and FFprobe
- Media upload for MP4, MOV, MKV, WebM, JPG, PNG, and WebP
- FFprobe metadata, a JPEG thumbnail, SHA-256 integrity checks, and an optional software H.264 proxy
- Read-only display detection: `xrandr` on Linux, Win32 monitor APIs on Windows
- Host CPU, memory, disk, and display-count monitoring over a WebSocket
- An audit log for sign-in, upload, transcode, delete, and integrity checks
- A dark control surface that labels later phases as unavailable

## What this build does not do

- Fullscreen or synchronized playback
- Display-mode changes
- Canvas editing, event profiles, or layer mapping
- AI planning or tool execution
- Colorlight or NovaStar communication
- Multi-computer control, an installer, or Windows startup registration

Pixel placement for a future canvas is not guessed by a model. Phase 1 only reports the desktop the operating system already has.

## Run it

Requirements: Python 3.11 or newer, Node.js 22, FFmpeg, and FFprobe. Linux display detection also needs `xrandr`. Windows display detection uses the Win32 APIs and does not need `xrandr`.

```bash
./scripts/dev.sh
```

On Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000). The API health check is [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health). The first launch writes `.env` and prints the administrator password. That file stays on the machine.

Use `127.0.0.1` for both the page and the API. The live status socket connects to port 8000 on the same hostname as the page so the session cookie is sent.

## Security

The API binds to `127.0.0.1` unless `QUBIT_HOST` is changed. Sessions use an HttpOnly cookie. The AI surface does not exist, and no route runs a shell command from request text. Display detection is read-only. Uploaded media and the SQLite database are git-ignored.

Change the generated password before anyone else can reach the machine. A non-loopback bind still has no TLS in this phase; put a proxy in front of it before exposing it beyond the computer.

## Tests

```bash
./scripts/test.sh
```

Backend tests live in `backend/tests` and need FFmpeg. See [DEVELOPMENT.md](DEVELOPMENT.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [ROADMAP.md](ROADMAP.md).

A license has not been chosen yet.
