import { useState, useRef, useId, useEffect } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { runQuery, type QueryResponse, type Step } from "./api";

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
    <div className="flex flex-col h-[100dvh] max-w-[800px] mx-auto">
      <header className="px-6 pt-5 pb-4 border-b border-border flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-semibold tracking-[-0.01em]">Research Agent</h1>
          <p className="text-[0.8rem] text-text-muted mt-px">Hybrid RAG (FAISS + Bedrock) + Tavily • Claude on Amazon Bedrock</p>
        </div>

        <div className="flex gap-2 flex-shrink-0 mt-1">
          <button
            type="button"
            onClick={openCorpusModal}
            title="See the private documents the agent can search. Click any to open the original file."
            className="bg-transparent text-text-muted border border-border rounded-[12px] text-xs px-3 py-1.5 cursor-pointer whitespace-nowrap transition-all hover:text-text hover:border-accent hover:bg-[rgba(108,138,255,0.06)] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            📚 View internal documents
          </button>

          <button
            type="button"
            onClick={handleNewChat}
            disabled={loading || messages.length === 0}
            title="Clear the conversation and show the demo examples again"
            className="bg-transparent text-text-muted border border-border rounded-[12px] text-xs px-3 py-1.5 cursor-pointer whitespace-nowrap transition-all hover:text-text hover:border-accent hover:bg-[rgba(108,138,255,0.06)] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            New chat
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-4 scroll-smooth">
        {messages.length === 0 && !loading && (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-text-muted text-center">
            <span className="text-[2.5rem]">🔍</span>
            <p className="max-w-[48ch]">
              Ask anything. The agent searches a small internal research corpus (RAG) +
              the live web (Tavily) and shows you the exact steps it took.
            </p>

            <div className="mt-2 w-full max-w-[520px] flex flex-col gap-2 px-2">
              <div className="text-[0.7rem] text-text-muted uppercase tracking-[0.04em] text-left">Quick demo examples (click to try):</div>

              <button
                type="button"
                className="text-left bg-surface-2 border border-border rounded-[12px] text-text text-[0.82rem] px-3 py-2 cursor-pointer transition-colors hover:border-accent hover:bg-[rgba(108,138,255,0.06)] flex flex-col gap-0.5"
                onClick={() => {
                  setInput(
                    "According to Nexara Daniel Ltd internal FY2026 planning assumptions, what is the base case ARR target and what are the main UK-specific risks?"
                  );
                }}
              >
                📄 Internal only (RAG)
                <span className="text-[0.7rem] text-text-muted">Pulls from private financial documents (earnings, capex, planning notes)</span>
              </button>

              <button
                type="button"
                className="text-left bg-surface-2 border border-border rounded-[12px] text-text text-[0.82rem] px-3 py-2 cursor-pointer transition-colors hover:border-accent hover:bg-[rgba(108,138,255,0.06)] flex flex-col gap-0.5"
                onClick={() => {
                  setInput(
                    "What are the latest UK policy developments or incentives for AI data centre energy efficiency and grid connections in 2026?"
                  );
                }}
              >
                🌐 Web + internal (Tavily)
                <span className="text-[0.7rem] text-text-muted">Relies on live web search for current public information</span>
              </button>

              <div className="mt-1 text-[0.72rem] leading-tight text-text-muted text-left border-t border-border pt-2">
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
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={[
                "max-w-[80%] px-4 py-3 rounded-[12px] border text-[0.9rem] leading-[1.6]",
                msg.role === "user"
                  ? "bg-user-bubble border-[#2a4a7f]"
                  : "bg-assistant-bubble border-border",
              ].join(" ")}
            >
              {msg.role === "assistant" ? (
                <div className="message-markdown">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              ) : (
                <pre className="whitespace-pre-wrap break-words font-inherit text-[0.9rem]">{msg.text}</pre>
              )}

              {/* Sources (web URLs + internal document names) */}
              {msg.sources && msg.sources.length > 0 && (
                <ul className="mt-2.5 pt-2.5 border-t border-border list-none flex flex-col gap-0.5 text-[0.75rem]">
                  {msg.sources.map((src, j) => {
                    const isUrl = /^https?:\/\//i.test(src);
                    return (
                      <li key={j}>
                        {isUrl ? (
                          <a href={src} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline break-all">
                            {src}
                          </a>
                        ) : (
                          <span className="text-text">📄 {src}</span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}

              {/* Steps & decisions from the LangGraph run */}
              {msg.steps && msg.steps.length > 0 && (
                <details className="mt-3 pt-2.5 border-t border-border group">
                  <summary className="cursor-pointer text-xs text-text-muted select-none hover:text-text">
                    Show agent steps ({msg.steps.length})
                  </summary>
                  <ol className="mt-2 mb-1 pl-[18px] text-[0.78rem] leading-[1.45] text-text-muted list-decimal">
                    {msg.steps.map((s, j) => (
                      <li
                        key={j}
                        className={[
                          "mb-[2px]",
                          s.skipped ? "opacity-60 italic" : "",
                          s.error ? "text-error" : "",
                        ].join(" ")}
                      >
                        <span className="font-mono font-semibold text-accent">{s.node}</span>
                        {s.detail && <span className="text-text-muted">: {s.detail}</span>}
                      </li>
                    ))}
                  </ol>
                  <div className="mt-1 text-[0.7rem] text-text-muted opacity-80">
                    The graph always runs retrieve (local corpus) → search (web) → analyse → finalise.
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] px-4 py-[14px] rounded-[12px] border border-border bg-assistant-bubble">
              <div className="loading-dots flex gap-1.5">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          </div>
        )}

        {error && (
          <p className="text-error text-[0.85rem] text-center px-4 py-2 bg-[rgba(255,107,107,0.08)] border border-[rgba(255,107,107,0.2)] rounded-[12px]">
            {error}
          </p>
        )}
      </main>

      <footer className="p-4 border-t border-border">
        <form id={formId} onSubmit={handleSubmit} className="flex gap-2.5 items-end">
          <textarea
            ref={textareaRef}
            className="flex-1 bg-surface border border-border rounded-[12px] text-[0.9rem] px-3.5 py-2.5 text-text resize-none leading-[1.5] focus:border-accent outline-none placeholder:text-text-muted disabled:opacity-50"
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
            className="bg-accent hover:bg-accent-hover disabled:opacity-40 text-white border-0 rounded-[12px] px-5 h-[42px] text-[0.9rem] font-medium cursor-pointer whitespace-nowrap transition-colors disabled:cursor-not-allowed"
            disabled={!input.trim() || loading}
          >
            {loading ? "…" : "Send"}
          </button>
        </form>
      </footer>

      <div className="text-center text-[0.72rem] text-text-muted px-4 pt-2 pb-3 border-t border-border">
        This site uses CloudFront access logs for statistical purposes to
        understand usage patterns and improve the service. No personal data is
        sold or shared.{" "}
        <Link to="/privacy" className="underline hover:text-text">Learn more</Link>
      </div>

      {/* Internal documents modal */}
      {showCorpus && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-[100] p-4"
          onClick={() => setShowCorpus(false)}
          role="presentation"
        >
          <div
            className="bg-surface border border-border rounded-[12px] w-full max-w-[560px] p-5 shadow-[0_10px_30px_rgba(0,0,0,0.35)]"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="corpus-title"
          >
            <div className="flex items-center justify-between mb-2.5">
              <h2 id="corpus-title" className="text-base font-semibold m-0">Internal documents</h2>
              <button
                type="button"
                onClick={() => setShowCorpus(false)}
                aria-label="Close"
                className="bg-none border-0 text-text-muted text-[1.6rem] leading-none cursor-pointer px-1 hover:text-text"
              >
                ×
              </button>
            </div>

            <p className="text-[0.82rem] text-text-muted mb-3.5 leading-[1.4]">
              These documents are <strong>not on the public web</strong>. They are the private corpus the agent can
              search with RAG. Click any document to open it.
            </p>

            {corpusLoading ? (
              <div className="text-sm text-text-muted py-3 text-center">Loading documents…</div>
            ) : corpusDocs.length === 0 ? (
              <div className="text-sm text-text-muted py-3 text-center">No documents found.</div>
            ) : (
              <ul className="list-none m-0 mb-4 p-0 border border-border rounded-[12px] overflow-hidden">
                {corpusDocs.map((doc) => (
                  <li
                    key={doc.name}
                    onClick={() => openCorpusDocument(doc.name)}
                    className="flex items-center justify-between px-3 py-2.5 cursor-pointer border-b border-border bg-surface-2 text-[0.9rem] last:border-b-0 hover:bg-[rgba(108,138,255,0.08)]"
                  >
                    <span className="text-text font-medium break-all">
                      {doc.type === "pdf" ? "📄" : "📝"} {doc.name}
                    </span>
                    <span className="text-[0.7rem] text-text-muted bg-surface px-1.5 py-px rounded uppercase tracking-[0.03em] ml-3 flex-shrink-0">
                      {doc.type}
                    </span>
                  </li>
                ))}
              </ul>
            )}

            <button
              type="button"
              onClick={() => setShowCorpus(false)}
              className="w-full bg-accent hover:bg-accent-hover text-white border-0 rounded-[12px] py-2 text-sm font-medium cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
