/**
 * Ledger API client — Lukla Operations Engine (immutable double-entry core).
 *
 * Contract source of truth:
 *   backend/app/api/v1/ledger.py + openspec/.../contracts/openapi.yaml
 *   GET  /api/v1/ledger/entries?cursor=&pageSize=      -> LedgerPage
 *   POST /api/v1/ledger/transactions                   -> LedgerTransaction  (Idempotency-Key header)
 *   POST /api/v1/ledger/transactions/{id}/reversals    -> LedgerTransaction  (Idempotency-Key header)
 *
 * KNOWN CEILING (deliberate): the ledger service requires a Bearer JWT
 * (roles Owner/FinancePayroll + tenant claim) and sends no CORS headers, so
 * this build runs in MOCK mode by default. To talk to the real service set:
 *   VITE_LEDGER_MODE=live
 *   VITE_LEDGER_API_URL=http://localhost:8000/api/v1
 *   VITE_LEDGER_TOKEN=<signed JWT>
 * Request/response shapes are kept identical to the contract, so switching
 * modes requires no UI change. The real service also needs CORS + a token
 * issuer before the browser can call it (revisit in the auth phase).
 */

export type LedgerDirection = 'DEBIT' | 'CREDIT';

export interface LedgerEntry {
  accountCode: string;
  direction: LedgerDirection;
  amountMinor: number;
}

export interface LedgerTransaction {
  id: string;
  tenantId: string;
  entries: LedgerEntry[];
  reversalOf: string | null;
}

export interface LedgerPage {
  items: LedgerTransaction[];
  nextCursor: string | null;
}

export interface PostTransactionInput {
  transactionType: string;
  currency: string;
  entries: LedgerEntry[];
}

export interface LedgerResult<T> {
  ok: boolean;
  data?: T;
  error?: string;
}

const MODE: 'mock' | 'live' =
  (import.meta.env.VITE_LEDGER_MODE as string) === 'live' ? 'live' : 'mock';
const LIVE_BASE = (import.meta.env.VITE_LEDGER_API_URL as string) || '/api/v1';
const LIVE_TOKEN = (import.meta.env.VITE_LEDGER_TOKEN as string) || '';
const TENANT_ID = '11111111-1111-1111-1111-111111111111';

/** True when the UI is backed by the in-memory mock instead of the live service. */
export const isMockLedger = MODE === 'mock';

/** Idempotency-Key: 16–200 chars per the contract. */
export function newIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID().replace(/-/g, '');
  }
  return `idem-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}

// ─── Mock store ────────────────────────────────────────────────────────────────
let mockStore: LedgerTransaction[] = seed();

function seed(): LedgerTransaction[] {
  const tx = (id: string, entries: LedgerEntry[], reversalOf: string | null = null): LedgerTransaction =>
    ({ id, tenantId: TENANT_ID, entries, reversalOf });
  return [
    tx('a1000000-0000-4000-8000-000000000001', [
      { accountCode: '1100', direction: 'DEBIT', amountMinor: 150000 },
      { accountCode: '4000', direction: 'CREDIT', amountMinor: 150000 },
    ]),
    tx('a1000000-0000-4000-8000-000000000002', [
      { accountCode: '5100', direction: 'DEBIT', amountMinor: 87500 },
      { accountCode: '2100', direction: 'CREDIT', amountMinor: 87500 },
    ]),
    tx('a1000000-0000-4000-8000-000000000003', [
      { accountCode: '1100', direction: 'DEBIT', amountMinor: 150000 },
      { accountCode: '4000', direction: 'CREDIT', amountMinor: 150000 },
    ]),
  ];
}

export function sumMinor(entries: LedgerEntry[], direction: LedgerDirection): number {
  return entries
    .filter(e => e.direction === direction)
    .reduce((total, e) => total + e.amountMinor, 0);
}

// ─── Public API ────────────────────────────────────────────────────────────────

export async function getLedgerEntries(pageSize = 50, cursor?: string): Promise<LedgerResult<LedgerPage>> {
  if (MODE === 'live') return liveGet(pageSize, cursor);

  const start = cursor ? Number(cursor) || 0 : 0;
  const items = mockStore.slice(start, start + pageSize);
  const nextCursor = start + pageSize < mockStore.length ? String(start + pageSize) : null;
  return { ok: true, data: { items, nextCursor } };
}

export async function appendLedgerTransaction(input: PostTransactionInput): Promise<LedgerResult<LedgerTransaction>> {
  const invalid = validate(input.entries);
  if (invalid) return { ok: false, error: invalid };

  if (MODE === 'live') return livePost<LedgerTransaction>('/ledger/transactions', input);

  const created: LedgerTransaction = {
    id: newIdempotencyKey().slice(0, 36),
    tenantId: TENANT_ID,
    entries: input.entries,
    reversalOf: null,
  };
  mockStore = [created, ...mockStore];
  return { ok: true, data: created };
}

export async function reverseLedgerTransaction(
  transactionId: string,
  reason: string,
): Promise<LedgerResult<LedgerTransaction>> {
  if (!reason.trim()) return { ok: false, error: 'Alasan reversal wajib diisi.' };

  if (MODE === 'live') {
    return livePost<LedgerTransaction>(`/ledger/transactions/${transactionId}/reversals`, { reason });
  }

  const original = mockStore.find(t => t.id === transactionId);
  if (!original) return { ok: false, error: 'Transaksi tidak ditemukan.' };

  const created: LedgerTransaction = {
    id: newIdempotencyKey().slice(0, 36),
    tenantId: TENANT_ID,
    entries: original.entries.map(e => ({
      ...e,
      direction: e.direction === 'DEBIT' ? 'CREDIT' : 'DEBIT',
    })),
    reversalOf: original.id,
  };
  mockStore = [created, ...mockStore];
  return { ok: true, data: created };
}

// ─── Validation (mirrors the server invariant) ─────────────────────────────────

function validate(entries: LedgerEntry[]): string | null {
  if (entries.length < 2) return 'Transaksi membutuhkan minimal 2 baris (debit & kredit).';
  if (entries.some(e => !e.accountCode.trim())) return 'Setiap baris wajib punya kode akun.';
  if (entries.some(e => !Number.isFinite(e.amountMinor) || e.amountMinor <= 0)) {
    return 'Nominal setiap baris harus lebih dari 0.';
  }
  const debit = sumMinor(entries, 'DEBIT');
  const credit = sumMinor(entries, 'CREDIT');
  if (debit !== credit) {
    return 'Transaksi tidak balance: total debit harus sama dengan total kredit.';
  }
  return null;
}

// ─── Live transport ────────────────────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (LIVE_TOKEN) headers.Authorization = `Bearer ${LIVE_TOKEN}`;
  return headers;
}

async function readProblem(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (body && typeof body === 'object') {
      const { code, detail } = body as { code?: unknown; detail?: unknown };
      if (typeof detail === 'string') return typeof code === 'string' ? `${code}: ${detail}` : detail;
    }
  } catch {
    /* response was not JSON */
  }
  return `HTTP ${res.status}`;
}

async function liveGet(pageSize: number, cursor?: string): Promise<LedgerResult<LedgerPage>> {
  try {
    const params = new URLSearchParams({ pageSize: String(pageSize) });
    if (cursor) params.set('cursor', cursor);
    const res = await fetch(`${LIVE_BASE}/ledger/entries?${params.toString()}`, { headers: authHeaders() });
    if (!res.ok) return { ok: false, error: await readProblem(res) };
    return { ok: true, data: (await res.json()) as LedgerPage };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

async function livePost<T>(path: string, body: unknown): Promise<LedgerResult<T>> {
  try {
    const res = await fetch(`${LIVE_BASE}${path}`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Idempotency-Key': newIdempotencyKey() },
      body: JSON.stringify(body),
    });
    if (!res.ok) return { ok: false, error: await readProblem(res) };
    return { ok: true, data: (await res.json()) as T };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}
