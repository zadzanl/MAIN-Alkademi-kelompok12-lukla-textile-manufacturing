/**
 * Toaster — renders the global toast stack (see services/toast.ts).
 * Mounted once in App; every page pushes through `toast.*`.
 */

import React, { useEffect, useState } from 'react';
import { subscribe, dismiss, type ToastItem } from '../services/toast';

const KIND_STYLE: Record<ToastItem['kind'], string> = {
  success: 'border-[#34c759] bg-[#e8f5e9] text-[#1a7a34]',
  error:   'border-[#fecaca] bg-[#fee2e2] text-[#dc2626]',
  info:    'border-[#d5d5da] bg-[#f4f8fd] text-[#334155]',
};

const Toaster: React.FC = () => {
  const [items, setItems] = useState<ToastItem[]>([]);

  useEffect(() => subscribe(setItems), []);

  if (items.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[100] flex w-[min(360px,calc(100vw-2rem))] flex-col gap-2">
      {items.map(t => (
        <div
          key={t.id}
          role="status"
          className={`flex items-start gap-3 rounded-[14px] border px-4 py-3 text-[13px] font-medium shadow-sm ${KIND_STYLE[t.kind]}`}
        >
          <span className="flex-1">{t.message}</span>
          <button
            type="button"
            onClick={() => dismiss(t.id)}
            aria-label="Tutup notifikasi"
            className="shrink-0 leading-none opacity-60 hover:opacity-100"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
};

export default Toaster;
