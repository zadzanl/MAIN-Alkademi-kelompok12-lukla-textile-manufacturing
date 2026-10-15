import React, { useState, useRef, useEffect } from 'react';
import { LucideIcon } from '../components/Sidebar';
import { getToken } from '../services/authSession';

export interface ActionShortcut {
  id: string;
  title: string;
  description: string;
  url: string;
  view?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  shortcuts?: ActionShortcut[];
  toolsUsed?: string[];
  timestamp: string;
}

interface CopilotViewProps {
  isDark: boolean;
  onNavigate: (view: string) => void;
}

const COPILOT_ENDPOINT = '/api/v1/copilot/chat';

function configuredCopilotToken(): string | null {
  const env = typeof import.meta !== 'undefined' ? import.meta.env : undefined;
  const token = env?.VITE_COPILOT_TOKEN?.trim();
  return token || null;
}

function copilotAuthorization(): string | null {
  const token = configuredCopilotToken() ?? getToken();
  // The root API accepts signed JWTs. Prototype auth sessions are opaque tokens
  // and must not be presented as JWTs because they cannot carry tenant claims.
  if (!token || token.split('.').length !== 3) return null;
  return `Bearer ${token}`;
}

const PRESET_SUGGESTIONS = [
  'Stok Kain Fleece',
  'Potong Order ORD-104',
  'Tally Sewing Line 2',
  'Throughput Harian',
  'Status QC Sample v2',
];

const CopilotView: React.FC<CopilotViewProps> = ({ isDark, onNavigate }) => {
  const [selectedRole, setSelectedRole] = useState('Owner');
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Halo! Saya Asisten AI Operasional Lukla. Tanyakan status produksi, ketersediaan bahan baku, rekonsiliasi cutting, atau rekap throughput harian.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (messageText: string) => {
    const textToSend = messageText.trim();
    if (!textToSend || isLoading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const history = [...messages, userMsg]
        .filter((message) => message.id !== 'welcome')
        .slice(-10)
        .map(({ id, sender, text, shortcuts, timestamp }) => ({ id, sender, text, shortcuts, timestamp }));
      const authorization = copilotAuthorization();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Roles': selectedRole,
      };
      if (authorization) headers.Authorization = authorization;

      const resp = await fetch(COPILOT_ENDPOINT, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: textToSend, history, roles: [selectedRole], stream: false }),
      });

      if (!resp.ok) {
        throw new Error(`Inference request failed with HTTP ${resp.status}`);
      }

      const data = await resp.json() as { reply?: string; shortcuts?: ActionShortcut[]; tools_used?: string[] };
      if (!data.reply) {
        throw new Error('Inference response did not contain a reply');
      }
      const reply = data.reply;
      setMessages((prev) => [...prev, {
        id: String(Date.now() + 1),
        sender: 'assistant',
        text: reply,
        shortcuts: data.shortcuts,
        toolsUsed: data.tools_used,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Unknown inference error';
      setMessages((prev) => [...prev, {
        id: String(Date.now() + 1),
        sender: 'assistant',
        text: `Tidak dapat menghubungi layanan inference: ${detail}. Periksa backend dan konfigurasi .env.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    }

    setIsLoading(false);
  };

  const handleShortcutClick = (sc: ActionShortcut) => {
    if (sc.view) {
      onNavigate(sc.view);
    } else if (sc.url.startsWith('#')) {
      onNavigate(sc.url.replace('#', ''));
    } else if (sc.url.startsWith('/cutting/new') || sc.url.startsWith('/app/materials?action=cutting')) {
      onNavigate('warehouse');
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] max-w-5xl mx-auto px-4 py-3">
      {/* Top Header Card */}
      <div
        className="rounded-2xl p-4 mb-3 border shrink-0 transition-colors"
        style={{
          background: isDark ? '#141417' : '#ffffff',
          borderColor: isDark ? '#27272a' : '#e4e4e7',
          boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.3)' : '0 2px 10px rgba(0,0,0,0.04)',
        }}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-sm"
              style={{
                background: isDark
                  ? 'linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)'
                  : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                color: '#ffffff',
              }}
            >
              <LucideIcon name="sparkles" className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight" style={{ color: isDark ? '#f4f4f5' : '#18181b' }}>
                  Lukla Intelligence
                </h1>
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold"
                  style={{
                    background: isDark ? 'rgba(34, 197, 94, 0.15)' : 'rgba(34, 197, 94, 0.12)',
                    color: isDark ? '#4ade80' : '#16a34a',
                    border: isDark ? '1px solid rgba(34, 197, 94, 0.25)' : '1px solid rgba(34, 197, 94, 0.2)',
                  }}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Live Gateway
                </span>
              </div>
              <p className="text-xs" style={{ color: isDark ? '#a1a1aa' : '#71717a' }}>
                Strict Read-Only Intelligence · Action Shortcut Navigation Protocol
              </p>
            </div>
          </div>

          {/* Role Filter Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium" style={{ color: isDark ? '#a1a1aa' : '#71717a' }}>
              Peran:
            </span>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              aria-label="Pilih Peran Operasional"
              className="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors outline-none cursor-pointer"
              style={{
                background: isDark ? '#1f1f23' : '#f4f4f5',
                color: isDark ? '#f4f4f5' : '#18181b',
                borderColor: isDark ? '#3f3f46' : '#d4d4d8',
              }}
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

        {/* Suggestion Chips */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t overflow-x-auto text-xs" style={{ borderColor: isDark ? '#27272a' : '#f4f4f5' }}>
          <span className="text-[11px] font-semibold shrink-0" style={{ color: isDark ? '#71717a' : '#a1a1aa' }}>
            Saran Cepat:
          </span>
          <div className="flex items-center gap-1.5">
            {PRESET_SUGGESTIONS.map((sug) => (
              <button
                key={sug}
                type="button"
                onClick={() => handleSend(sug)}
                className="px-2.5 py-1 rounded-full text-[11px] font-medium transition-all shrink-0 border"
                style={{
                  background: isDark ? '#1f1f23' : '#f4f4f5',
                  color: isDark ? '#d4d4d8' : '#3f3f46',
                  borderColor: isDark ? '#27272a' : '#e4e4e7',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = isDark ? '#6366f1' : '#818cf8';
                  e.currentTarget.style.color = isDark ? '#a5b4fc' : '#4f46e5';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = isDark ? '#27272a' : '#e4e4e7';
                  e.currentTarget.style.color = isDark ? '#d4d4d8' : '#3f3f46';
                }}
              >
                {sug}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Message Stream */}
      <div
        className="flex-1 rounded-2xl p-4 mb-3 border overflow-y-auto space-y-3.5 transition-colors"
        style={{
          background: isDark ? '#0d0d10' : '#fafafa',
          borderColor: isDark ? '#27272a' : '#e4e4e7',
        }}
      >
        {messages.map((m) => {
          const isUser = m.sender === 'user';
          return (
            <div key={m.id} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
              <div className="flex items-start gap-2 max-w-[85%]">
                {!isUser && (
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 shadow-sm"
                    style={{
                      background: isDark ? '#312e81' : '#e0e7ff',
                      color: isDark ? '#c7d2fe' : '#4338ca',
                    }}
                  >
                    <LucideIcon name="sparkles" className="w-3.5 h-3.5" />
                  </div>
                )}
                <div>
                  <div
                    className="rounded-2xl px-4 py-2.5 text-xs sm:text-[13px] leading-relaxed shadow-sm"
                    style={
                      isUser
                        ? {
                            background: isDark ? '#4338ca' : '#18181b',
                            color: '#ffffff',
                            borderBottomRightRadius: '4px',
                          }
                        : {
                            background: isDark ? '#18181b' : '#ffffff',
                            color: isDark ? '#f4f4f5' : '#18181b',
                            border: isDark ? '1px solid #27272a' : '1px solid #e4e4e7',
                            borderBottomLeftRadius: '4px',
                          }
                    }
                  >
                    {m.text}
                  </div>

                  {/* Tool telemetry tags */}
                  {m.toolsUsed && m.toolsUsed.length > 0 && (
                    <div className="flex items-center gap-1.5 mt-1.5 px-1">
                      <span className="text-[10px] font-mono" style={{ color: isDark ? '#71717a' : '#a1a1aa' }}>
                        Tools:
                      </span>
                      {m.toolsUsed.map((tool) => (
                        <span
                          key={tool}
                          className="text-[10px] font-mono px-1.5 py-0.5 rounded border"
                          style={{
                            background: isDark ? '#141417' : '#f4f4f5',
                            color: isDark ? '#a1a1aa' : '#71717a',
                            borderColor: isDark ? '#27272a' : '#e4e4e7',
                          }}
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Action Shortcuts Protocol */}
                  {m.shortcuts && m.shortcuts.length > 0 && (
                    <div className="mt-2.5 space-y-2">
                      <span className="text-[10px] uppercase font-bold tracking-wider block" style={{ color: isDark ? '#818cf8' : '#4f46e5' }}>
                        ⚡ Tautan Aksi Cepat (Audited Nav):
                      </span>
                      {m.shortcuts.map((sc) => (
                        <button
                          key={sc.id}
                          type="button"
                          onClick={() => handleShortcutClick(sc)}
                          className="w-full flex items-center justify-between p-2.5 rounded-xl border text-left transition-all group"
                          style={{
                            background: isDark ? '#18181b' : '#f5f9ff',
                            borderColor: isDark ? '#312e81' : '#bfdbfe',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = isDark ? '#6366f1' : '#3b82f6';
                            e.currentTarget.style.transform = 'translateY(-1px)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = isDark ? '#312e81' : '#bfdbfe';
                            e.currentTarget.style.transform = 'none';
                          }}
                        >
                          <div>
                            <div className="font-semibold text-xs" style={{ color: isDark ? '#c7d2fe' : '#1e40af' }}>
                              {sc.title}
                            </div>
                            <div className="text-[11px]" style={{ color: isDark ? '#94a3b8' : '#3b82f6' }}>
                              {sc.description}
                            </div>
                          </div>
                          <span
                            className="text-sm font-bold transition-transform group-hover:translate-x-1"
                            style={{ color: isDark ? '#818cf8' : '#2563eb' }}
                          >
                            →
                          </span>
                        </button>
                      ))}
                    </div>
                  )}

                  <span className="text-[10px] mt-1 block px-1" style={{ color: isDark ? '#52525b' : '#a1a1aa' }}>
                    {m.timestamp}
                  </span>
                </div>
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-center gap-2 text-xs italic px-2" style={{ color: isDark ? '#a1a1aa' : '#71717a' }}>
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
            <span>Menghubungi endpoint Lukla Intelligence Gateway...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Composer */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend(input);
        }}
        className="flex items-center gap-2 p-2 rounded-xl border transition-colors shrink-0"
        style={{
          background: isDark ? '#141417' : '#ffffff',
          borderColor: isDark ? '#27272a' : '#e4e4e7',
          boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.3)' : '0 2px 10px rgba(0,0,0,0.04)',
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Tanyakan status pesanan ORD-104, stok kain fleece, atau efisiensi sewing..."
          disabled={isLoading}
          className="flex-1 px-3 py-2 text-xs sm:text-[13px] bg-transparent outline-none transition-colors"
          style={{
            color: isDark ? '#f4f4f5' : '#18181b',
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-40"
          style={{
            background: isDark ? '#4f46e5' : '#18181b',
            color: '#ffffff',
          }}
        >
          <span>Kirim</span>
          <span className="text-sm">↵</span>
        </button>
      </form>
    </div>
  );
};

export default CopilotView;
