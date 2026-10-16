/**
 * Toaster — renders the global toast stack (see services/toast.ts).
 * Mounted once in App; every page pushes through `toast.*`.
 */

import React, { useEffect, useState } from 'react';
import { subscribe, dismiss, type ToastItem } from '../services/toast';

const KIND_STYLE: Record<ToastItem['kind'], string> = {
  success: 'border-ok bg-ok-bg text-ok-2',
  error:   'border-bad-bg-2 bg-bad-bg text-bad-4',
  info:    'border-hair-4 bg-brand-bg text-ink-2',
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
          className={`flex items-start gap-3 rounded-[14px] border px-3 py-2 text-[15px] font-medium shadow-sm ${KIND_STYLE[t.kind]}`}
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
