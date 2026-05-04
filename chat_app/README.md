# Chat app (demo)

Minimal ChatGPT-style UI with a FastAPI backend and a Vite + React + TypeScript SPA. The backend keeps one OpenAI **Conversation** id in memory; each turn uses the Responses API with that conversation (full response in v1, not streamed).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python 3.12+)
- Node.js and npm

## Environment

Copy the example env file and set your API key:

```bash
cp chat_app/backend/.env.example chat_app/backend/.env
# Edit chat_app/backend/.env — set OPENAI_API_KEY (required)
```

Variables:

| Variable | Required | Default |
|----------|----------|---------|
| `OPENAI_API_KEY` | yes | — |
| `CORS_ORIGINS` | no | `http://localhost:5173` (comma-separated list allowed) |

The chat model is fixed in code (`gpt-5-nano`; see `OPENAI_CHAT_MODEL` in `chat_app/backend/app.py`).

## Run the backend

From the **repository root**:

```bash
uv run uvicorn chat_app.backend.app:app --reload --port 8000
```

Expect: `Uvicorn running on http://127.0.0.1:8000`.

## Run the UI

```bash
cd chat_app/ui && npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to `http://localhost:8000`.

## API (curl)

Health:

```bash
curl -s http://localhost:8000/api/health | jq
```

Chat:

```bash
curl -s -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"user_message":"say hi in three words"}' | jq
```

Reset (new conversation id):

```bash
curl -s -X POST http://localhost:8000/api/reset | jq
```

## Tests

From repo root (dummy key is enough for mocked tests):

```bash
OPENAI_API_KEY=test uv run pytest chat_app/backend/tests -q
```

## UI checks

```bash
cd chat_app/ui && npx tsc --noEmit
cd chat_app/ui && npm run build
```

## Streaming

The UI sends turns to **`POST /api/chat/stream`** (Server-Sent Events). The legacy **`POST /api/chat`** JSON endpoint is unchanged.

Response headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`.

Wire format: frames separated by `\n\n`. Each frame is a single line `data: <json>` where `<json>` is one of:

- `{"type":"delta","text":"<chunk>"}` — append `text` to the assistant bubble.
- `{"type":"done","conversation_id":"<id>","assistant_message":"<full text>"}` — terminal success; replace bubble with `assistant_message`.
- `{"type":"error","detail":"<message>"}` — terminal error.

Validation or upstream errors before the stream opens return normal FastAPI **`400`/`502`** with a JSON body (no SSE).

Example (use **`-N`** so curl does not buffer the stream):

```bash
curl -N -s -X POST http://localhost:8000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"user_message":"count to 5 slowly"}'
```

Example frames (abbreviated):

```text
data: {"type": "delta", "text": "1"}

data: {"type": "delta", "text": "\n2"}

data: {"type": "done", "conversation_id": "conv_...", "assistant_message": "1\n2\n..."}
```
