import { useState, useRef, useId } from "react";
import { Link } from "react-router-dom";
import { runQuery, type QueryResponse } from "./api";
import "./App.css";

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
}

export default function App() {
  const threadId = useRef(crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const formId = useId();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setLoading(true);

    try {
      const result: QueryResponse = await runQuery({
        query,
        thread_id: threadId.current,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.answer, sources: result.sources },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="layout">
      <header className="header">
        <h1>Research Agent</h1>
        <p className="subtitle">Powered by Tavily + Claude on Amazon Bedrock</p>
      </header>

      <main className="chat">
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <span className="empty-icon">🔍</span>
            <p>Ask anything — the agent will search the web and summarise it for you.</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message message--${msg.role}`}>
            <div className="message__bubble">
              <pre className="message__text">{msg.text}</pre>
              {msg.sources && msg.sources.length > 0 && (
                <ul className="message__sources">
                  {msg.sources.map((src, j) => (
                    <li key={j}>
                      <a href={src} target="_blank" rel="noopener noreferrer">
                        {src}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message message--assistant">
            <div className="message__bubble message__bubble--loading">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}

        {error && <p className="error">{error}</p>}
      </main>

      <footer className="composer">
        <form id={formId} onSubmit={handleSubmit} className="composer__form">
          <textarea
            className="composer__input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                e.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder="Ask a research question… (Enter to send, Shift+Enter for newline)"
            rows={2}
            disabled={loading}
          />
          <button
            type="submit"
            className="composer__send"
            disabled={!input.trim() || loading}
          >
            {loading ? "…" : "Send"}
          </button>
        </form>
      </footer>

      <div className="privacy-notice">
        This site uses CloudFront access logs for statistical purposes to
        understand usage patterns and improve the service. No personal data is
        sold or shared.{" "}
        <Link to="/privacy">Learn more</Link>
      </div>
    </div>
  );
}
