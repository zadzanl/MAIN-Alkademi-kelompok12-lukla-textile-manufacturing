/**
 * FloorTerminalView — VIEW-04 touch-first floor terminal.
 *
 * Tablet UI for mandor: pick a line, then capture one 30-minute interval block
 * using large +/- steppers (48px touch targets) per assigned operator/component.
 * "Submit Interval Block" records one sewing tally per non-zero card via
 * services/opsApi.ts (mock by default; contract-shaped for live mode).
 *
 * Mirrors prototypes/design-mocks/lukla-ui-mock.html (view-04) and
 * artifacts/design_guideline.md §2.3 (touch targets ≥48px).
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import {
  listLines, listOperators, listAssignments, recordSewingTally, isMockOps,
  type Line, type Operator, type Assignment,
} from '../services/opsApi';

const DEFAULT_ORDER = '33333333-3333-4333-8333-333333333333';
const DEFAULT_CUT_BATCH = '22222222-2222-4222-8222-222222222222';

interface Interval { start: string; end: string }

function currentInterval(): Interval {
  const now = new Date();
  now.setMinutes(now.getMinutes() < 30 ? 0 : 30, 0, 0);
  const end = new Date(now.getTime() + 30 * 60 * 1000);
  return { start: now.toISOString(), end: end.toISOString() };
}

const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });

interface CardResult { ok: boolean; message: string }

const FloorTerminalView: React.FC = () => {
  const [lines, setLines] = useState<Line[]>([]);
  const [operators, setOperators] = useState<Operator[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [lineId, setLineId] = useState('');
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [results, setResults] = useState<Record<string, CardResult>>({});
  const [interval] = useState<Interval>(currentInterval);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [rl, ro, ra] = await Promise.all([listLines(), listOperators(), listAssignments()]);
    if (rl.ok && rl.data) setLines(rl.data.items);
    if (ro.ok && ro.data) setOperators(ro.data.items);
    if (ra.ok && ra.data) setAssignments(ra.data.items);
    const firstErr = [rl, ro, ra].find(r => !r.ok);
    if (firstErr) setError(firstErr.error ?? 'Gagal memuat data terminal.');
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!lineId && lines.length > 0) setLineId(lines[0].id);
  }, [lines, lineId]);

  const operatorName = (id: string) =>
    operators.find(o => o.id === id)?.displayName ?? id.slice(0, 8);

  const cards = assignments.filter(a => a.lineId === lineId);
  const totalPieces = cards.reduce((sum, c) => sum + (counts[c.id] ?? 0), 0);

  const bump = (id: string, delta: number) =>
    setCounts(prev => ({ ...prev, [id]: Math.max(0, (prev[id] ?? 0) + delta) }));

  const submit = async () => {
    setBusy(true);
    setResults({});
    const next: Record<string, CardResult> = {};
    for (const c of cards) {
      const pieces = counts[c.id] ?? 0;
      if (pieces <= 0) continue;
      const res = await recordSewingTally({
        orderId: DEFAULT_ORDER,
        cutBatchId: DEFAULT_CUT_BATCH,
        lineId: c.lineId,
        componentCode: c.componentCode,
        operatorId: c.operatorId,
        intervalStart: interval.start,
        intervalEnd: interval.end,
        pieces,
      });
      next[c.id] = res.ok
        ? { ok: true, message: `Tersimpan · ${res.data?.tallyId.slice(0, 8) ?? ''}` }
        : { ok: false, message: res.error ?? 'Gagal menyimpan' };
    }
    setResults(next);
    setBusy(false);
  };

  const selectedLine = lines.find(l => l.id === lineId);

  return (
    <div className="space-y-5">
      {isMockOps && (
        <div className="rounded-[14px] border border-[#d5d5da] bg-[#f4f8fd] px-4 py-3 text-[12.5px] text-[#334155]">
          Mode mock aktif — data disimpan di memori. Set <code className="font-mono">VITE_LEDGER_MODE=live</code> untuk service asli.
        </div>
      )}
      {error && <div className="rounded-[14px] border border-[#fecaca] bg-[#fee2e2] px-4 py-3 text-[13px] text-[#dc2626]">{error}</div>}

      {/* Context bar */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 rounded-[16px] border border-[#e6e6e9] bg-white px-5 py-4">
        <label className="flex items-center gap-2 text-[13px] text-[#6e6e73]">
          <span className="font-medium">Line</span>
          <select value={lineId} onChange={e => { setLineId(e.target.value); setCounts({}); setResults({}); }}
            className="min-h-[44px] rounded-[10px] px-3 text-[13px] font-semibold text-[#1d1d1f]">
            {lines.map(l => <option key={l.id} value={l.id}>{l.lineCode}</option>)}
          </select>
        </label>
        <span className="text-[13px] text-[#6e6e73]">
          <span className="font-medium">Mandor:</span> {selectedLine ? operatorName(assignments.find(a => a.lineId === lineId)?.operatorId ?? '') : '—'}
        </span>
        <span className="text-[13px] text-[#6e6e73]">
          <span className="font-medium">Interval:</span> {fmtTime(interval.start)} – {fmtTime(interval.end)}
        </span>
        <button onClick={load} className="btn-secondary ml-auto">
          <LucideIcon name="activity" className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Tailor cards */}
      {loading ? (
        <p className="py-10 text-center text-[13px] text-[#6e6e73]">Memuat…</p>
      ) : cards.length === 0 ? (
        <div className="rounded-[18px] border border-dashed border-[#d5d5da] bg-white px-6 py-12 text-center text-[13px] text-[#6e6e73]">
          Belum ada penugasan operator pada line ini. Tambahkan penugasan di tab <strong>Admin</strong>.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {cards.map(c => {
            const count = counts[c.id] ?? 0;
            const result = results[c.id];
            return (
              <div key={c.id} className="rounded-[18px] border border-[#e6e6e9] bg-white p-5">
                <div className="mb-4">
                  <p className="text-[15px] font-semibold text-[#1d1d1f]">{operatorName(c.operatorId)}</p>
                  <p className="font-mono text-[12px] text-[#6e6e73]">{c.componentCode}</p>
                </div>
                <div className="flex items-center justify-between">
                  <button type="button" onClick={() => bump(c.id, -1)} disabled={count === 0}
                    aria-label={`Kurangi ${operatorName(c.operatorId)}`}
                    className="w-12 h-12 rounded-[12px] bg-[#f0f0f2] text-[#1d1d1f] text-2xl font-semibold flex items-center justify-center transition-transform active:scale-95 disabled:opacity-40">
                    −
                  </button>
                  <span className="text-[30px] font-semibold tabular-nums text-[#1d1d1f]">{count}</span>
                  <button type="button" onClick={() => bump(c.id, 1)}
                    aria-label={`Tambah ${operatorName(c.operatorId)}`}
                    className="w-12 h-12 rounded-[12px] bg-[#0071e3] text-white text-2xl font-semibold flex items-center justify-center transition-transform active:scale-95">
                    +
                  </button>
                </div>
                {result && (
                  <p className={`mt-3 text-[12px] font-medium ${result.ok ? 'text-[#1a7a34]' : 'text-[#dc2626]'}`}>
                    {result.ok ? '✓ ' : '✗ '}{result.message}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      <button type="button" onClick={submit} disabled={busy || totalPieces === 0}
        className="w-full min-h-[56px] rounded-[14px] bg-[#0071e3] text-white text-[15px] font-semibold tracking-wide transition-transform active:scale-[0.99] disabled:opacity-40">
        {busy ? 'Mengirim…' : `SUBMIT INTERVAL BLOCK${totalPieces > 0 ? ` (${totalPieces} pcs)` : ''}`}
      </button>
    </div>
  );
};

export default FloorTerminalView;
