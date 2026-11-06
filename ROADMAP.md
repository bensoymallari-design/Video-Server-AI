# Roadmap

Phase 1 is the current build. Later phases are not implemented.

## Phase 1 — Working foundation

Done in this tree:

- Monorepo, FastAPI, Next.js, SQLite, configuration, and structured logs
- Local accounts, roles, sessions, and an audit log
- Media upload, FFprobe inspection, thumbnails, integrity checks, and an optional software proxy
- Read-only Linux and Windows display detectors, with desktop bounds
- Host monitoring over a WebSocket
- Health checks and startup scripts
- Automated backend tests and dashboard typecheck, lint, and build

Still outside Phase 1, on purpose:

- Applying a display mode
- Playing media
- A saved canvas or event profile

## Phase 2 — Native playback

- A playback process separate from the API
- One selected display, borderless fullscreen
- Start, stop, pause, scale, and position
- A test pattern
- Output status and dropped-frame counts when the renderer can measure them
- Verify on a physical display. Until that happens, label the result unverified.

## Phase 3 — Canvas and mapping

- Virtual canvas and pixel regions calculated in code
- Crop, scale, rotation, and layers
- Preview
- Versioned event profiles: save, load, duplicate, import, export, validate

## Phase 4 — AI integration

- A configured model client such as Ollama
- A fixed tool registry
- Plans validated before any disruptive change
- Preview and explicit approval
- The model does not calculate pixels and does not receive a shell

## Phase 5 — Controller profiles

- Manual Colorlight and NovaStar profile records
- Cabinet map and sending-port view
- Import and export
- No undocumented manufacturer protocol and no firmware writes
- Where a direct API is missing, the profile says the processor is still configured in the manufacturer tool

## Phase 6 — Multi-PC

- Paired device agents, discovery, and authentication
- Media distribution and a scheduled start
- Health and disconnect handling
- Clock-sync approach with a written accuracy limit
- No claim of frame sync from simultaneous commands

## Phase 7 — Production hardening

- Installer and optional startup in an interactive session
- Crash recovery, backups, and rollback
- Performance and security tests
- Deployment documentation
