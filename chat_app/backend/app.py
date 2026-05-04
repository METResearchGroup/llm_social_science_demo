from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("chat_app.backend")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="chat_app/backend/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")


settings = Settings()
client = OpenAI(api_key=settings.openai_api_key)

_conversation_id: Optional[str] = None
_lock = asyncio.Lock()


class ChatRequest(BaseModel):
    user_message: str = Field(min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    assistant_message: str
    conversation_id: str


class ResetResponse(BaseModel):
    conversation_id: str


class HealthResponse(BaseModel):
    ok: bool
    conversation_id: Optional[str]
    model: str


app = FastAPI(title="chat_app backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


async def _ensure_conversation() -> str:
    global _conversation_id
    if _conversation_id is not None:
        return _conversation_id
    async with _lock:
        if _conversation_id is None:
            try:
                conv = await asyncio.to_thread(client.conversations.create)
            except OpenAIError as e:
                logger.exception("conversations.create failed")
                raise HTTPException(status_code=502, detail=f"openai error: {e}") from e
            _conversation_id = conv.id
        return _conversation_id


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(ok=True, conversation_id=_conversation_id, model=settings.openai_model)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    conv_id = await _ensure_conversation()
    try:
        response = await asyncio.to_thread(
            client.responses.create,
            model=settings.openai_model,
            conversation=conv_id,
            input=[{"role": "user", "content": req.user_message}],
        )
    except OpenAIError as e:
        logger.exception("responses.create failed")
        raise HTTPException(status_code=502, detail=f"openai error: {e}") from e
    text = getattr(response, "output_text", None) or ""
    return ChatResponse(assistant_message=text, conversation_id=conv_id)


@app.post("/api/reset", response_model=ResetResponse)
async def reset() -> ResetResponse:
    global _conversation_id
    async with _lock:
        old = _conversation_id
        _conversation_id = None
        if old is not None:
            try:
                await asyncio.to_thread(client.conversations.delete, old)
            except OpenAIError:
                logger.warning("conversations.delete failed for %s; continuing", old)
        try:
            conv = await asyncio.to_thread(client.conversations.create)
        except OpenAIError as e:
            logger.exception("conversations.create failed during reset")
            raise HTTPException(status_code=502, detail=f"openai error: {e}") from e
        _conversation_id = conv.id
        return ResetResponse(conversation_id=_conversation_id)
