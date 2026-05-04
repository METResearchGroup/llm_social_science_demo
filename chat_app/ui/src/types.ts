export type ChatRequest = { user_message: string };
export type ChatResponse = { assistant_message: string; conversation_id: string };
export type ResetResponse = { conversation_id: string };
export type HealthResponse = { ok: boolean; conversation_id: string | null; model: string };
export type Role = "user" | "assistant";
export type UiMessage = { id: string; role: Role; text: string; pending?: boolean };

export type StreamDeltaEvent = { type: "delta"; text: string };
export type StreamDoneEvent = { type: "done"; conversation_id: string; assistant_message: string };
export type StreamErrorEvent = { type: "error"; detail: string };
export type StreamEvent = StreamDeltaEvent | StreamDoneEvent | StreamErrorEvent;

export type StreamChatHandlers = {
  onDelta: (text: string) => void;
  onDone: (e: StreamDoneEvent) => void;
  onError: (detail: string) => void;
  onAbort?: () => void;
  signal?: AbortSignal;
};
