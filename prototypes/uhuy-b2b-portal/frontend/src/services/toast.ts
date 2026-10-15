/**
 * toast.ts — tiny global notification bus.
 *
 * Pages push a message and a single <Toaster /> mounted in App renders it. A
 * module-level store (not React context) keeps callers free of provider wiring:
 * any module can `import { toast } from '../services/toast'` and call it.
 *
 * Known ceiling: in-memory only, auto-dismiss after ttlMs. No persistence/queue
 * limits — fine for operator feedback, revisit only if volume grows.
 */

export type ToastKind = 'success' | 'error' | 'info';

export interface ToastItem {
  id: number;
  kind: ToastKind;
  message: string;
}

type Listener = (items: ToastItem[]) => void;

let items: ToastItem[] = [];
let seq = 0;
const listeners = new Set<Listener>();

function emit(): void {
  const snapshot = [...items];
  listeners.forEach(l => l(snapshot));
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  listener([...items]);
  return () => {
    listeners.delete(listener);
  };
}

export function dismiss(id: number): void {
  items = items.filter(i => i.id !== id);
  emit();
}

export function push(kind: ToastKind, message: string, ttlMs = 4000): number {
  const id = ++seq;
  items = [...items, { id, kind, message }];
  emit();
  if (ttlMs > 0) setTimeout(() => dismiss(id), ttlMs);
  return id;
}

export const toast = {
  success: (message: string) => push('success', message),
  error: (message: string) => push('error', message),
  info: (message: string) => push('info', message),
};
