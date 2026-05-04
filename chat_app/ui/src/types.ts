export type ChatRequest = { user_message: string };
export type ChatResponse = { assistant_message: string; conversation_id: string };
export type ResetResponse = { conversation_id: string };
export type HealthResponse = { ok: boolean; conversation_id: string | null; model: string };
export type Role = "user" | "assistant";
export type UiMessage = { id: string; role: Role; text: string; pending?: boolean };
