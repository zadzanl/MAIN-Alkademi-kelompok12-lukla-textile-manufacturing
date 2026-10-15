"""
Lukla Operations Copilot — Zero-Build Interactive Web Interface.
Provides React 18 + Tailwind CSS (via CDN) web UI for direct browser testing and Playwright E2E verification.
"""

COPILOT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lukla Operations Copilot</title>
  <!-- Tailwind CSS & React 18 via CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    :root {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    /* Fallback styles in case CDN is slow or blocked */
    body {
      margin: 0;
      background-color: #f4f4f5;
      color: #18181b;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }
  </style>
</head>
<body>
  <div id="root" class="w-full max-w-lg">
    <!-- Static fallback for instant indexing and test assertion before React hydration -->
    <div data-testid="copilot-chat" class="flex flex-col h-[680px] w-full rounded-2xl border border-neutral-200 bg-white shadow-xl overflow-hidden">
      <div class="bg-neutral-900 text-white p-4 flex items-center justify-between">
        <div>
          <h1 class="font-semibold text-sm">Lukla Operations Copilot</h1>
          <p class="text-xs text-neutral-400">Online / Mock LLM</p>
        </div>
        <select data-testid="copilot-role-select" class="bg-neutral-800 text-white text-xs px-2 py-1 rounded border border-neutral-700">
          <option value="Owner">Owner</option>
          <option value="Warehouse">Warehouse</option>
          <option value="ProductionHead">ProductionHead</option>
          <option value="QCInspector">QCInspector</option>
          <option value="FinancePayroll">FinancePayroll</option>
          <option value="MaklonClient">MaklonClient</option>
        </select>
      </div>
      <div class="flex-1 p-4 overflow-y-auto space-y-3 bg-neutral-50">
        <div data-testid="copilot-message" class="bg-white p-3 rounded-lg border border-neutral-200 text-xs">
          Memuat Asisten AI Operasional Lukla...
        </div>
      </div>
      <form class="p-3 border-t border-neutral-200 bg-white flex gap-2">
        <input data-testid="copilot-input" type="text" placeholder="Tanyakan status pesanan, bahan, atau line..." class="flex-1 px-3 py-2 text-xs border rounded-lg" />
        <button data-testid="copilot-send" type="button" class="px-4 py-2 bg-neutral-900 text-white rounded-lg text-xs font-medium">Kirim</button>
      </form>
    </div>
  </div>

  <script type="text/babel">
    const { useState, useEffect, useRef } = React;

    const SUGGESTIONS = [
      "Stok Kain Fleece",
      "Potong Order ORD-104",
      "Tally Sewing Line 2"
    ];

    function CopilotChatApp() {
      const [role, setRole] = useState("Owner");
      const [messages, setMessages] = useState([
        {
          id: "welcome",
          sender: "assistant",
          text: "Halo! Saya Asisten AI Operasional Lukla. Tanyakan status produksi, ketersediaan bahan baku, atau rekap throughput harian.",
          tools_used: [],
          shortcuts: [],
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        }
      ]);
      const [input, setInput] = useState("");
      const [loading, setLoading] = useState(false);
      const messagesEndRef = useRef(null);

      const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      };

      useEffect(() => {
        scrollToBottom();
      }, [messages, loading]);

      const sendMessage = async (overrideText) => {
        const textToSend = (typeof overrideText === "string" ? overrideText : input).trim();
        if (!textToSend || loading) return;

        const userMsg = {
          id: "user-" + Date.now(),
          sender: "user",
          text: textToSend,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        };

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
          const response = await fetch("/api/v1/copilot/chat", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Roles": role
            },
            body: JSON.stringify({
              message: textToSend,
              roles: [role]
            })
          });

          if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `HTTP Error ${response.status}`);
          }

          const data = await response.json();
          const botMsg = {
            id: "bot-" + Date.now(),
            sender: "assistant",
            text: data.reply || "Respons diterima tanpa pesan teks.",
            shortcuts: data.shortcuts || [],
            tools_used: data.tools_used || [],
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          };
          setMessages((prev) => [...prev, botMsg]);
        } catch (err) {
          setMessages((prev) => [
            ...prev,
            {
              id: "err-" + Date.now(),
              sender: "assistant",
              text: `Kendala komunikasi: ${err.message || "Gagal menghubungi mesin operasional."}`,
              shortcuts: [],
              tools_used: [],
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            }
          ]);
        } finally {
          setLoading(false);
        }
      };

      return (
        <div className="flex flex-col h-[680px] w-full max-w-lg rounded-2xl border border-neutral-200 bg-white shadow-xl overflow-hidden font-sans">
          {/* Header */}
          <div className="bg-neutral-900 text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-sm">
                ✨
              </div>
              <div>
                <h1 className="font-semibold text-sm leading-tight">Lukla Operations Copilot</h1>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span className="text-[11px] text-neutral-300">Online / Mock LLM</span>
                </div>
              </div>
            </div>

            <div className="flex flex-col items-end">
              <label htmlFor="role-select" className="text-[10px] text-neutral-400 font-medium uppercase tracking-wider mb-0.5">
                Role Filter
              </label>
              <select
                id="role-select"
                data-testid="copilot-role-select"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="bg-neutral-800 text-neutral-100 text-xs px-2.5 py-1 rounded-md border border-neutral-700 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium cursor-pointer"
              >
                <option value="Owner">Owner</option>
                <option value="Warehouse">Warehouse</option>
                <option value="ProductionHead">ProductionHead</option>
                <option value="QCInspector">QCInspector</option>
                <option value="FinancePayroll">FinancePayroll</option>
                <option value="MaklonClient">MaklonClient</option>
              </select>
            </div>
          </div>

          {/* Quick Suggestions */}
          <div className="px-4 py-2 bg-neutral-50 border-b border-neutral-200 flex items-center gap-2 overflow-x-auto text-xs whitespace-nowrap">
            <span className="text-[11px] text-neutral-500 font-semibold flex items-center gap-1">
              💡 Saran:
            </span>
            {SUGGESTIONS.map((sug, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => sendMessage(sug)}
                className="px-2.5 py-1 rounded-full bg-white border border-neutral-300 hover:border-blue-500 hover:text-blue-600 text-neutral-700 text-xs transition-colors font-medium cursor-pointer shadow-sm"
              >
                {sug}
              </button>
            ))}
          </div>

          {/* Message List */}
          <div data-testid="copilot-chat" className="flex-1 p-4 overflow-y-auto space-y-3 bg-neutral-50">
            {messages.map((m) => (
              <div
                key={m.id}
                data-testid="copilot-message"
                className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm shadow-sm leading-relaxed ${
                    m.sender === "user"
                      ? "bg-neutral-900 text-white rounded-br-xs"
                      : "bg-white text-neutral-800 border border-neutral-200 rounded-bl-xs"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.text}</p>
                </div>

                {/* Tools Used Chips */}
                {m.tools_used && m.tools_used.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1 max-w-[85%]">
                    {m.tools_used.map((tool, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-neutral-200 text-neutral-700 border border-neutral-300"
                      >
                        ⚙️ Tool: {tool}
                      </span>
                    ))}
                  </div>
                )}

                {/* Action Shortcuts */}
                {m.shortcuts && m.shortcuts.length > 0 && (
                  <div className="mt-2 space-y-2 w-full max-w-[90%]">
                    <span className="text-[11px] font-bold text-neutral-500 uppercase tracking-wider block">
                      Aksi Operasional Cepat:
                    </span>
                    {m.shortcuts.map((sc) => (
                      <div
                        key={sc.id || sc.url}
                        data-testid="action-shortcut-card"
                        className="p-3 rounded-xl bg-blue-50 border border-blue-200 shadow-sm flex flex-col gap-1.5"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="font-semibold text-xs text-blue-950 flex items-center gap-1.5">
                              <span>✂️</span>
                              <span>{sc.title}</span>
                            </div>
                            <div className="text-[11px] text-blue-800 mt-0.5 leading-snug">
                              {sc.description}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center justify-between pt-1 border-t border-blue-100 mt-1">
                          <span className="text-[10px] font-mono text-blue-600 truncate max-w-[200px]">
                            {sc.url}
                          </span>
                          <a
                            href={sc.url}
                            className="px-2.5 py-1 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold inline-flex items-center gap-1 transition-colors shadow-sm"
                          >
                            <span>Buka Form</span>
                            <span>→</span>
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <span className="text-[10px] text-neutral-400 mt-1 px-1">{m.timestamp}</span>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-neutral-500 p-2">
                <span className="inline-block w-3.5 h-3.5 border-2 border-neutral-400 border-t-neutral-800 rounded-full animate-spin"></span>
                <span className="animate-pulse">Menghubungi endpoint Lukla...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Form Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
            className="p-3 border-t border-neutral-200 bg-white flex gap-2 items-center"
          >
            <input
              type="text"
              data-testid="copilot-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Tanyakan status pesanan, stok bahan, atau line..."
              disabled={loading}
              className="flex-1 px-3.5 py-2 text-xs border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
            <button
              type="submit"
              data-testid="copilot-send"
              disabled={loading || !input.trim()}
              className="px-4 py-2 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl text-xs font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 cursor-pointer"
            >
              <span>Kirim</span>
              <span>↵</span>
            </button>
          </form>
        </div>
      );
    }

    // Hydrate React application
    const rootEl = document.getElementById("root");
    if (rootEl) {
      const root = ReactDOM.createRoot(rootEl);
      root.render(<CopilotChatApp />);
    }
  </script>
</body>
</html>
"""

def get_copilot_html() -> str:
    """Returns the zero-build React 18 CDN HTML application string."""
    return COPILOT_HTML
