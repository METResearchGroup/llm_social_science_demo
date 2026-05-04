import type { ChatResponse, HealthResponse, ResetResponse, StreamChatHandlers, StreamEvent } from "./types";

export async function postChat(user_message: string): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_message }),
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  return res.json() as Promise<ChatResponse>;
}

export async function postReset(): Promise<ResetResponse> {
  const res = await fetch("/api/reset", { method: "POST" });
  if (!res.ok) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  return res.json() as Promise<ResetResponse>;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch("/api/health");
  if (!res.ok) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  return res.json() as Promise<HealthResponse>;
}

export async function streamChat(user_message: string, handlers: StreamChatHandlers): Promise<void> {
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ user_message }),
    signal: handlers.signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let sep: number;
      while ((sep = buf.indexOf("\n\n")) !== -1) {
        const frame = buf.slice(0, sep);
        buf = buf.slice(sep + 2);
        const line = frame.split("\n").find((l) => l.startsWith("data:"));
        if (!line) continue;
        const payload = line.slice(5).trim();
        if (!payload) continue;
        const evt = JSON.parse(payload) as StreamEvent;
        if (evt.type === "delta") handlers.onDelta(evt.text);
        else if (evt.type === "done") handlers.onDone(evt);
        else if (evt.type === "error") handlers.onError(evt.detail);
      }
    }
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      handlers.onAbort?.();
      return;
    }
    throw e;
  }
}
