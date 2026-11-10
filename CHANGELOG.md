# Changelog

## Unreleased

- The Windows startup script searches for a real Python 3.11+ install and stops with install instructions when only the Microsoft Store alias is present.
- Media upload no longer lets FFmpeg or FFprobe read the API console, which stalled a drop on Windows. The library sends the file straight to the API and shows sending progress, then an inspection state.

## 0.1.0 — Phase 1 foundation

- Added the FastAPI service with SQLite, local sessions, roles, health checks, and an audit log.
- Added media upload, FFprobe inspection, thumbnails, SHA-256 checks, and an optional libx264 proxy.
- Added read-only display detection for Linux xrandr and Windows Win32, plus desktop bounds.
- Added a WebSocket host monitor and a Next.js control surface for the working routes.
- Left playback, canvas editing, profiles, AI, controller protocols, and multi-computer control unimplemented and labeled as such.
