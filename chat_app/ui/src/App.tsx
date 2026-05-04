import { useCallback, useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { postChat, postReset } from "./api";
import type { UiMessage } from "./types";

function newId(): string {
  return crypto.randomUUID();
}

export default function App() {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const onSubmit = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;
    setError(null);
    setInput("");
    const assistantId = newId();
    setMessages((m) => [
      ...m,
      { id: newId(), role: "user", text },
      { id: assistantId, role: "assistant", text: "", pending: true },
    ]);
    setSending(true);
    try {
      const res = await postChat(text);
      setMessages((m) =>
        m.map((msg) =>
          msg.id === assistantId
            ? { ...msg, text: res.assistant_message, pending: false }
            : msg,
        ),
      );
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      setMessages((m) => m.filter((x) => x.id !== assistantId));
    } finally {
      setSending(false);
    }
  }, [input, sending]);

  const onReset = async () => {
    setError(null);
    try {
      await postReset();
      setMessages([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void onSubmit();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1 className="title">Chat</h1>
        <button type="button" className="reset" onClick={() => void onReset()} disabled={sending}>
          Reset
        </button>
      </header>
      {error ? (
        <div className="error-banner" role="alert">
          {error}
        </div>
      ) : null}
      <div className="messages" aria-live="polite">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`bubble bubble-${msg.role}${msg.pending ? " bubble-pending" : ""}`}
          >
            {msg.pending ? <span className="pending-dots">Thinking…</span> : msg.text}
          </div>
        ))}
        <div ref={bottomRef} className="scroll-anchor" />
      </div>
      <footer className="composer">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Message (Enter to send, Shift+Enter for newline)"
          rows={3}
          disabled={sending}
          aria-label="Message"
        />
        <button type="button" className="send" onClick={() => void onSubmit()} disabled={sending || !input.trim()}>
          Send
        </button>
      </footer>
    </div>
  );
}
