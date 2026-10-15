import React, { useState } from 'react';

export interface ActionShortcut {
  id: string;
  title: string;
  description: string;
  url: string;
  icon?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  shortcuts?: ActionShortcut[];
  timestamp: string;
}

interface CopilotChatWidgetProps {
  userRoles: string[];
  tenantId: string;
  apiEndpoint?: string;
}

export const CopilotChatWidget: React.FC<CopilotChatWidgetProps> = ({
  userRoles,
  tenantId,
  apiEndpoint = '/api/v1/copilot/chat'
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Halo! Saya Asisten AI Operasional Lukla. Tanyakan status produksi, ketersediaan bahan baku, atau rekap throughput harian.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userText = input;
    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({ message: userText, roles: userRoles })
      });

      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }

      const data = await response.json();
      const botMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'assistant',
        text: data.reply,
        shortcuts: data.shortcuts,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          sender: 'assistant',
          text: 'Maaf, terjadi gangguan saat menghubungi mesin operasional.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-[420px] rounded-xl border border-neutral-200 bg-white shadow-xl overflow-hidden font-sans">
      {/* Header */}
      <div className="bg-neutral-900 text-white p-4 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-sm">Lukla Operations Copilot</h2>
          <p className="text-xs text-neutral-400">Strict Read-Only Intelligence</p>
        </div>
        <div className="flex items-center gap-1.5">
          {userRoles.map((role) => (
            <span key={role} className="px-2 py-0.5 rounded text-[10px] font-medium bg-neutral-800 text-neutral-300">
              {role}
            </span>
          ))}
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-neutral-50">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-sm shadow-sm ${
                m.sender === 'user'
                  ? 'bg-neutral-900 text-white rounded-br-none'
                  : 'bg-white text-neutral-800 border border-neutral-200 rounded-bl-none'
              }`}
            >
              {m.text}
            </div>

            {/* Action Shortcuts (Hyperlinks to Audited Forms) */}
            {m.shortcuts && m.shortcuts.length > 0 && (
              <div className="mt-2 space-y-1.5 w-[90%]">
                <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                  Tautan Aksi Cepat:
                </span>
                {m.shortcuts.map((sc) => (
                  <a
                    key={sc.id}
                    href={sc.url}
                    className="flex items-center justify-between p-2 rounded-lg bg-blue-50 border border-blue-200 hover:bg-blue-100 transition-colors text-blue-900 text-xs font-medium group"
                  >
                    <div>
                      <div className="font-semibold">{sc.title}</div>
                      <div className="text-[11px] text-blue-700">{sc.description}</div>
                    </div>
                    <span className="text-blue-500 group-hover:translate-x-0.5 transition-transform">→</span>
                  </a>
                ))}
              </div>
            )}

            <span className="text-[10px] text-neutral-400 mt-1 px-1">{m.timestamp}</span>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-neutral-400 italic">
            <span className="animate-pulse">Menghubungi endpoint Lukla...</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSendMessage} className="p-3 border-t border-neutral-200 bg-white flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Tanyakan status pesanan, bahan, atau line..."
          className="flex-1 px-3 py-2 text-xs border border-neutral-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-900"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-4 py-2 bg-neutral-900 text-white rounded-lg text-xs font-medium hover:bg-neutral-800 disabled:opacity-50"
        >
          Kirim
        </button>
      </form>
    </div>
  );
};
