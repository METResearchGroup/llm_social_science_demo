# How to run the chat app

This runbook covers **local development** for the demo under `chat_app/`: a FastAPI backend (`chat_app/backend`) and a Vite + React + TypeScript UI (`chat_app/ui`). You need **two terminal sessions** (backend + UI).

More context on behavior and API contracts lives in [`chat_app/README.md`](../../chat_app/README.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python 3.12+ matches the repo root `pyproject.toml`)
- Node.js and npm (for the UI)

From the **repository root**, install Python deps (creates/uses `.venv` via uv):

```bash
uv sync
```

Install UI dependencies once (or after `package.json` / lockfile changes):

```bash
cd chat_app/ui && npm install
```

## Environment

1. Copy the example env file:

   ```bash
   cp chat_app/backend/.env.example chat_app/backend/.env
   ```

2. Edit `chat_app/backend/.env` and set **`OPENAI_API_KEY`** (required). Do not commit this file; it is ignored via `*.env`.

Optional variables (defaults shown in `.env.example`):

| Variable | Purpose |
|----------|---------|
| `CORS_ORIGINS` | Comma-separated browser origins allowed by the backend (default `http://localhost:5173`) |

The Responses API model id is hardcoded in `chat_app/backend/app.py` as **`gpt-5-nano`** (`OPENAI_CHAT_MODEL`); it is not configurable via environment variables.

Settings load `chat_app/backend/.env` relative to the **repository root** when you run uvicorn from the root as below.

## Start the backend

**Terminal A — from repository root:**

```bash
uv run uvicorn chat_app.backend.app:app --reload --port 8000
```

You should see something like: `Uvicorn running on http://127.0.0.1:8000`.

Quick check (optional):

```bash
curl -s http://localhost:8000/api/health | jq
```

Expect `"ok": true` and `"conversation_id": null` until the first chat request creates a conversation.

## Start the UI

**Terminal B:**

```bash
cd chat_app/ui && npm run dev
```

Open **http://localhost:5173** in a browser.

The Vite dev server listens on **5173** and proxies **`/api`** to **http://localhost:8000** (see `chat_app/ui/vite.config.ts`). The UI calls paths such as `/api/chat`; those requests hit the FastAPI app only when the backend is up on port 8000.

## Using the app

- Type a message and click **Send** (Enter sends; Shift+Enter adds a newline).
- Use **Reset** to discard the OpenAI conversation server-side and clear the on-screen transcript.

### Streaming

The UI uses **streaming** by default (`POST /api/chat/stream`). Replies grow in the assistant bubble as chunks arrive. While a reply is in flight, **Stop** aborts the request; partial text stays in the bubble and you can send again or continue the thread.

## If port 8000 is already in use

Another process may be bound to `8000`. Either stop that process or run this backend on a different port, for example:

```bash
uv run uvicorn chat_app.backend.app:app --reload --port 8001
```

If you change the backend port, the stock Vite proxy still points at `8000`, so either free `8000` or adjust `chat_app/ui/vite.config.ts` `server.proxy["/api"]` to match your backend URL for local dev.

## Smoke tests (optional)

Backend tests use mocks and do not call OpenAI:

```bash
OPENAI_API_KEY=test uv run pytest chat_app/backend/tests -q
```

UI typecheck and production build:

```bash
cd chat_app/ui && npx tsc --noEmit && npm run build
```

## Reference curls (backend on 8000)

```bash
curl -s http://localhost:8000/api/health | jq

curl -s -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"user_message":"say hi in three words"}' | jq

curl -s -X POST http://localhost:8000/api/reset | jq
```
