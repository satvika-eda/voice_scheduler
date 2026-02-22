# Architecture Overview

This scaffold separates responsibilities clearly:

- `backend/` (FastAPI): handles VAPI transcription integration, OpenAI conversational logic, Google OAuth + Calendar creation.
- `frontend/` (React): VAPI Web SDK integration for real-time audio capture and streaming; UI components and status display.
- `vapi_config/`: prompt and tool schema used by the voice agent when calling VAPI or other realtime audio tools.
- `deploy/`: deployment manifests (Render, Docker, ngrok helper).

Suggestions:
- Use `Redis` for session persistence in production.
- Use `python-dateutil` or `dateparser` for robust natural-language datetime parsing.
- Add tests for the calendar module with Google API mocked (see `backend/tests/`).
- Secure `.env` and never commit secrets; use platform secret stores in deployment.
- Add a CI pipeline to run unit tests and linting.

