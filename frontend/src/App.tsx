import { useState, useRef, useId, useEffect } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { runQuery, type QueryResponse, type Step } from "./api";
import "./App.css";

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
  steps?: Step[];
}

export default function App() {
  const threadId = useRef(crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCorpus, setShowCorpus] = useState(false);
  const [corpusDocs, setCorpusDocs] = useState<Array<{ name: string; type: string; size?: number }>>([]);
  const [corpusLoading, setCorpusLoading] = useState(false);
  const formId = useId();
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const API_BASE = (import.meta.env.VITE_API_URL as string || "").replace(/\/query\/?$/, "");

  useEffect(() => {
    if (!showCorpus) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setShowCorpus(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [showCorpus]);

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
        {
          role: "assistant",
          text: result.answer,
          sources: result.sources,
          steps: result.steps,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  function handleNewChat() {
    setMessages([]);
    setInput("");
    setError(null);
    threadId.current = crypto.randomUUID();
    requestAnimationFrame(() => { textareaRef.current?.focus(); });
  }

  async function openCorpusModal() {
    setShowCorpus(true);
    if (corpusDocs.length > 0) return;

    setCorpusLoading(true);
    try {
      const res = await fetch(`${API_BASE}/corpus`);
      setCorpusDocs(res.ok ? (await res.json() || []) : []);
    } catch {
      setCorpusDocs([]);
    } finally {
      setCorpusLoading(false);
    }
  }

  function openCorpusDocument(name: string) {
    const url = `${API_BASE}/corpus/${encodeURIComponent(name)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="header__main">
          <h1>Research Agent</h1>
          <p className="subtitle">Hybrid RAG (FAISS + Bedrock) + Tavily • Claude on Amazon Bedrock</p>
        </div>

        <div className="header__actions">
          <button
            type="button"
            className="header__action-btn"
            onClick={openCorpusModal}
            title="See the private documents the agent can search. Click any to open the original file."
          >
            📚 View internal documents
          </button>

          <button
            type="button"
            className="header__action-btn"
            onClick={handleNewChat}
            disabled={loading || messages.length === 0}
            title="Clear the conversation and show the demo examples again"
          >
            New chat
          </button>
        </div>
      </header>

      <main className="chat">
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <span className="empty-icon">🔍</span>
            <p>
              Ask anything. The agent searches a small internal research corpus (RAG) +
              the live web (Tavily) and shows you the exact steps it took.
            </p>

            <div className="example-queries">
              <div className="example-queries__label">Quick demo examples (click to try):</div>

              <button
                type="button"
                className="example-btn"
                onClick={() => {
                  setInput(
                    "According to Nexara Daniel Ltd internal FY2026 planning assumptions, what is the base case ARR target and what are the main UK-specific risks?"
                  );
                }}
              >
                📄 Internal only (RAG)
                <span className="example-btn__hint">
                  Pulls from private financial documents (earnings, capex, planning notes)
                </span>
              </button>

              <button
                type="button"
                className="example-btn"
                onClick={() => {
                  setInput(
                    "What are the latest UK policy developments or incentives for AI data centre energy efficiency and grid connections in 2026?"
                  );
                }}
              >
                🌐 Web + internal (Tavily)
                <span className="example-btn__hint">
                  Relies on live web search for current public information
                </span>
              </button>

              <div className="example-explain">
                This is <strong>not</strong> a generic chat interface. Every answer combines
                vector retrieval over a curated private corpus with live web results. The{" "}
                <em>Show agent steps</em> panel makes the retrieval decisions, source selection,
                and reasoning transparent.
                <br />
                The same hybrid + observable retrieval pattern powers real production systems in
                finance research, legal discovery, regulated industry knowledge bases, and
                enterprise "second brain" tools where you need both grounded internal knowledge
                and up-to-date external context, plus auditability.
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message message--${msg.role}`}>
            <div className="message__bubble">
              {msg.role === "assistant" ? (
                <div className="message__markdown">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              ) : (
                <pre className="message__text">{msg.text}</pre>
              )}

              {/* Sources (web URLs + internal document names) */}
              {msg.sources && msg.sources.length > 0 && (
                <ul className="message__sources">
                  {msg.sources.map((src, j) => {
                    const isUrl = /^https?:\/\//i.test(src);
                    return (
                      <li key={j}>
                        {isUrl ? (
                          <a href={src} target="_blank" rel="noopener noreferrer">
                            {src}
                          </a>
                        ) : (
                          <span className="source-doc">📄 {src}</span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}

              {/* Steps & decisions from the LangGraph run (new in hybrid RAG v1) */}
              {msg.steps && msg.steps.length > 0 && (
                <details className="steps">
                  <summary className="steps__summary">Show agent steps ({msg.steps.length})</summary>
                  <ol className="steps__list">
                    {msg.steps.map((s, j) => (
                      <li
                        key={j}
                        className={[
                          "steps__item",
                          s.skipped ? "steps__item--skipped" : "",
                          s.error ? "steps__item--error" : "",
                        ].join(" ")}
                      >
                        <span className="steps__node">{s.node}</span>
                        {s.detail && <span className="steps__detail">: {s.detail}</span>}
                      </li>
                    ))}
                  </ol>
                  <div className="steps__hint">
                    The graph always runs retrieve (local corpus) → search (web) → analyse → finalise.
                  </div>
                </details>
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
            ref={textareaRef}
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

      {/* Internal documents modal — list only. Clicking a row opens the actual file via backend endpoint. */}
      {showCorpus && (
        <div
          className="modal-backdrop"
          onClick={() => setShowCorpus(false)}
          role="presentation"
        >
          <div
            className="modal"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="corpus-title"
          >
            <div className="modal__header">
              <h2 id="corpus-title">Internal documents</h2>
              <button
                type="button"
                className="modal__close"
                onClick={() => setShowCorpus(false)}
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <p className="modal__intro">
              These documents are <strong>not on the public web</strong>. They are the private corpus the agent can
              search with RAG. Click any document to open it.
            </p>

            {corpusLoading ? (
              <div className="corpus-loading">Loading documents…</div>
            ) : corpusDocs.length === 0 ? (
              <div className="corpus-empty">No documents found.</div>
            ) : (
              <ul className="corpus-list simple">
                {corpusDocs.map((doc) => (
                  <li
                    key={doc.name}
                    onClick={() => openCorpusDocument(doc.name)}
                    className="corpus-row"
                  >
                    <span className="corpus-name">
                      {doc.type === "pdf" ? "📄" : "📝"} {doc.name}
                    </span>
                    <span className="corpus-type">{doc.type}</span>
                  </li>
                ))}
              </ul>
            )}

            <button
              type="button"
              className="modal__done"
              onClick={() => setShowCorpus(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
