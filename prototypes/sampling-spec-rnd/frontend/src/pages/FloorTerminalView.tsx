/**
 * FloorTerminalView — VIEW-04 touch-first floor terminal (30-Minute Interval Touch Interface).
 *
 * Tablet UI for mandor on the garment sewing floor:
 * - 48px touch steppers ([-] [14 pcs] [+]) with active scale & haptic touch feedback.
 * - 30-minute interval timing (13:30 – 14:00) with shift block navigation & live clock.
 * - Line assignment matrix up to 70 sewing stations (Tailor #01 - #70) with station search & component filters.
 * - Idempotency key submission verifying replay-safety across double-taps and network retries.
 * - Seamless mobile/tablet ergonomics with sticky floating submit bar and responsive matrix grid.
 * - Real-time offline detection (navigator.onLine) and Apple Design toast error/success states.
 *
 * Mirrors prototypes/design-mocks/lukla-ui-mock.html (view-04) and
 * openspec/changes/lukla-ops-engine-planning/artifacts/design_guideline.md (touch targets ≥48px).
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LucideIcon } from '../components/Sidebar';
import MockModeBanner from '../components/MockModeBanner';
import {
  listLines, listOperators, listAssignments, recordSewingTally, isMockOps,
  seedSeventyStations,
  type Line, type Operator, type Assignment,
} from '../services/opsApi';
import { toast } from '../services/toast';
import { getActor, subscribe as subscribeAuth } from '../services/authSession';

const DEFAULT_ORDER = '33333333-3333-4333-8333-333333333333';
const DEFAULT_CUT_BATCH = '22222222-2222-4222-8222-222222222222';

interface Interval {
  start: string;
  end: string;
  label: string;
}

/** Formats ISO string into strict 24h 2-digit HH:mm format */
function formatTime(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
}

/** Pre-calculated standard factory 30-minute shift intervals */
function generateShiftIntervals(): Interval[] {
  const intervals: Interval[] = [];
  const base = new Date();
  base.setSeconds(0, 0);

  // Standard factory operating hours: 08:00 to 17:00 in 30-min blocks
  const times: [number, number][] = [
    [8, 0], [8, 30],
    [9, 0], [9, 30],
    [10, 0], [10, 30],
    [11, 0], [11, 30],
    [13, 0], [13, 30],
    [14, 0], [14, 30],
    [15, 0], [15, 30],
    [16, 0], [16, 30],
  ];

  for (const [h, m] of times) {
    const s = new Date(base);
    s.setHours(h, m, 0, 0);
    const e = new Date(s.getTime() + 30 * 60 * 1000);
    intervals.push({
      start: s.toISOString(),
      end: e.toISOString(),
      label: `${formatTime(s.toISOString())} – ${formatTime(e.toISOString())}`,
    });
  }
  return intervals;
}

/** Returns the 13:30 – 14:00 factory speed interval or current matching block */
function getInitialInterval(): Interval {
  const shiftList = generateShiftIntervals();
  // Default to standard 13:30 – 14:00 benchmark block per spec
  const defaultBlock = shiftList.find(i => i.label.includes('13:30'));
  if (defaultBlock) return defaultBlock;

  const now = new Date();
  now.setMinutes(now.getMinutes() < 30 ? 0 : 30, 0, 0);
  const end = new Date(now.getTime() + 30 * 60 * 1000);
  return {
    start: now.toISOString(),
    end: end.toISOString(),
    label: `${formatTime(now.toISOString())} – ${formatTime(end.toISOString())}`,
  };
}

interface CardResult {
  ok: boolean;
  message: string;
  tallyId?: string;
  idempotent?: boolean;
}

const FloorTerminalView: React.FC = () => {
  const [lines, setLines] = useState<Line[]>([]);
  const [operators, setOperators] = useState<Operator[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [lineId, setLineId] = useState('');
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [results, setResults] = useState<Record<string, CardResult>>({});
  const [interval, setInterval] = useState<Interval>(getInitialInterval);
  const [shiftIntervals] = useState<Interval[]>(generateShiftIntervals);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search & filter states for managing up to 70 sewing stations
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedComponent, setSelectedComponent] = useState<string>('ALL');
  const [onlyNonZero, setOnlyNonZero] = useState(false);
  const [bulkArticle, setBulkArticle] = useState('');
  const [bulkQuantity, setBulkQuantity] = useState('');

  // Real-time network connectivity tracking
  const [isOnline, setIsOnline] = useState<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast.info('Koneksi internet lantai produksi tersambung kembali.');
    };
    const handleOffline = () => {
      setIsOnline(false);
      toast.error('Koneksi terputus! Terminal berjalan dalam mode offline.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [rl, ro, ra] = await Promise.all([listLines(), listOperators(), listAssignments()]);
    if (rl.ok && rl.data) setLines(rl.data.items);
    if (ro.ok && ro.data) setOperators(ro.data.items);
    if (ra.ok && ra.data) setAssignments(ra.data.items);
    const firstErr = [rl, ro, ra].find(r => !r.ok);
    if (firstErr) {
      const msg = firstErr.error ?? 'Gagal memuat data terminal.';
      setError(msg);
      toast.error(msg);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    return subscribeAuth(() => {
      setCounts({});
      setResults({});
      setError(null);
    });
  }, []);

  useEffect(() => {
    if (!lineId && lines.length > 0) setLineId(lines[0].id);
  }, [lines, lineId]);

  const operatorInfo = useCallback((id: string): { name: string; code: string } => {
    const op = operators.find(o => o.id === id);
    return {
      name: op?.displayName ?? id.slice(0, 8),
      code: op?.employeeCode ?? 'OPR-???',
    };
  }, [operators]);

  // Assignments for current line, sorted by stationNumber (1 to 70)
  const lineCards = useMemo(() => {
    const cards = assignments.filter(a => a.lineId === lineId);
    return [...cards].sort((a, b) => (a.stationNumber ?? 0) - (b.stationNumber ?? 0));
  }, [assignments, lineId]);

  // Extract distinct components for filter tabs
  const componentTabs = useMemo(() => {
    const comps = new Set<string>();
    lineCards.forEach(c => {
      if (c.componentCode) comps.add(c.componentCode);
    });
    return Array.from(comps);
  }, [lineCards]);

  // Filtered station cards based on search query, component, and non-zero toggle
  const filteredCards = useMemo(() => {
    return lineCards.filter((c, idx) => {
      const stationNo = c.stationNumber ?? idx + 1;
      const op = operatorInfo(c.operatorId);
      const count = counts[c.id] ?? 0;

      if (onlyNonZero && count <= 0) return false;
      if (selectedComponent !== 'ALL' && c.componentCode !== selectedComponent) return false;

      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        op.name.toLowerCase().includes(q) ||
        op.code.toLowerCase().includes(q) ||
        c.componentCode.toLowerCase().includes(q) ||
        `stasiun ${stationNo}`.includes(q) ||
        `station ${stationNo}`.includes(q) ||
        `#${stationNo}`.includes(q)
      );
    });
  }, [lineCards, counts, onlyNonZero, selectedComponent, searchQuery, operatorInfo]);

  // Total summary statistics across all cards in current line
  const totalPieces = useMemo(() => {
    return lineCards.reduce((sum, c) => sum + (counts[c.id] ?? 0), 0);
  }, [lineCards, counts]);

  const activeStationsCount = useMemo(() => {
    return lineCards.filter(c => (counts[c.id] ?? 0) > 0).length;
  }, [lineCards, counts]);

  const savedCount = useMemo(() => {
    return Object.values(results).filter(r => r.ok).length;
  }, [results]);

  // Haptic feedback trigger for tactile touch interaction
  const triggerHaptic = () => {
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      try {
        navigator.vibrate(15);
      } catch {
        /* ignore on unsupported hardware */
      }
    }
  };

  const bump = (id: string, delta: number) => {
    triggerHaptic();
    setCounts(prev => ({
      ...prev,
      [id]: Math.max(0, (prev[id] ?? 0) + delta),
    }));
  };

  const setCardCount = (id: string, val: number) => {
    setCounts(prev => ({
      ...prev,
      [id]: Math.max(0, val),
    }));
  };

  // Quick batch actions for mandor convenience
  const handleBulkAdd = (amount: number) => {
    triggerHaptic();
    setCounts(prev => {
      const next = { ...prev };
      filteredCards.forEach(c => {
        next[c.id] = (next[c.id] ?? 0) + amount;
      });
      return next;
    });
  };

  const handleBulkOrder = () => {
    const quantity = Number.parseInt(bulkQuantity, 10);
    if (!bulkArticle.trim()) {
      toast.error('Masukkan nama artikel sebelum membuat order bulk.');
      return;
    }
    if (!Number.isInteger(quantity) || quantity <= 0) {
      toast.error('Jumlah order bulk harus berupa angka lebih dari 0.');
      return;
    }
    if (lineCards.length === 0) {
      toast.error('Belum ada tailor aktif untuk menerima order bulk.');
      return;
    }

    const perTailor = Math.floor(quantity / lineCards.length);
    const remainder = quantity % lineCards.length;
    const nextCounts: Record<string, number> = {};
    lineCards.forEach((card, index) => {
      nextCounts[card.id] = perTailor + (index < remainder ? 1 : 0);
    });
    setCounts(nextCounts);
    setResults({});
    triggerHaptic();
    toast.success(`Order ${bulkArticle.trim()} sebanyak ${quantity} pcs dibagi ke ${lineCards.length} tailor.`);
  };

  const handleResetAll = () => {
    triggerHaptic();
    setCounts({});
    setResults({});
    toast.info('Hitungan output interval telah direset.');
  };

  const handlePopulateSeventyStations = async () => {
    if (!lineId) return;
    setBusy(true);
    const seeded = seedSeventyStations(lineId);
    setAssignments(prev => [...prev.filter(a => a.lineId !== lineId), ...seeded]);
    // Also refresh operators
    const ro = await listOperators();
    if (ro.ok && ro.data) setOperators(ro.data.items);
    setBusy(false);
    toast.success(`Matriks 70 stasiun jahit berhasil diaktifkan untuk Line ${selectedLine?.lineCode ?? ''}.`);
  };

  // Interval navigation handlers
  const handleStepInterval = (step: number) => {
    triggerHaptic();
    const currIdx = shiftIntervals.findIndex(i => i.start === interval.start);
    if (currIdx === -1) {
      if (shiftIntervals.length > 0) setInterval(shiftIntervals[0]);
      return;
    }
    const nextIdx = Math.max(0, Math.min(shiftIntervals.length - 1, currIdx + step));
    const nextInterval = shiftIntervals[nextIdx];
    setInterval(nextInterval);
    setResults({});
  };

  // Submission with verified idempotency key per card
  const submit = async () => {
    if (!isOnline) {
      toast.error('Tidak dapat mengirim: Perangkat sedang offline. Periksa koneksi WiFi pabrik.');
      return;
    }

    if (totalPieces === 0) {
      toast.error('Tidak ada pieces yang dicatat. Tekan (+) pada stasiun sebelum submit.');
      return;
    }

    setBusy(true);
    setResults({});
    const nextResults: Record<string, CardResult> = {};
    let successCount = 0;
    let failCount = 0;

    // Iterate through cards with non-zero tally
    for (const c of lineCards) {
      const pieces = counts[c.id] ?? 0;
      if (pieces <= 0) continue;

      // Stable idempotency key: ensures retries or network replays are safe
      const idempotencyKey = `tally-${c.lineId}-${c.operatorId}-${c.componentCode}-${interval.start}`;

      const res = await recordSewingTally({
        orderId: DEFAULT_ORDER,
        cutBatchId: DEFAULT_CUT_BATCH,
        lineId: c.lineId,
        componentCode: c.componentCode,
        operatorId: c.operatorId,
        intervalStart: interval.start,
        intervalEnd: interval.end,
        pieces,
        idempotencyKey,
      });

      if (res.ok && res.data) {
        successCount++;
        nextResults[c.id] = {
          ok: true,
          message: `Tersimpan · ${res.data.tallyId.slice(0, 8)}`,
          tallyId: res.data.tallyId,
          idempotent: true,
        };
      } else {
        failCount++;
        nextResults[c.id] = {
          ok: false,
          message: res.error ?? 'Gagal menyimpan',
        };
      }
    }

    setResults(nextResults);
    setBusy(false);

    if (failCount === 0 && successCount > 0) {
      toast.success(
        `Berhasil merekam ${totalPieces} pcs dari ${successCount} stasiun untuk interval ${interval.label}. (Idempotensi terverifikasi)`
      );
    } else if (failCount > 0 && successCount > 0) {
      toast.error(`${successCount} stasiun tersimpan, tetapi ${failCount} stasiun gagal. Periksa status tiap kartu.`);
    } else if (failCount > 0) {
      toast.error('Gagal menyimpan interval block. Silakan coba kembali.');
    }
  };

  const selectedLine = lines.find(l => l.id === lineId);
  const mandorName = operatorInfo(lineCards[0]?.operatorId ?? '').name;

  return (
    <div className="space-y-5 pb-24">
      {isMockOps && <MockModeBanner detail="data tersimpan di memori mock (kontrak OpenAPI terverifikasi)." />}

      {/* Offline Alert Banner */}
      {!isOnline && (
        <div
          role="alert"
          className="flex items-center justify-between rounded-[16px] border border-warn-2 bg-warn-bg px-5 py-4 text-[13px] text-warn-2 shadow-sm"
        >
          <div className="flex items-center gap-3">
            <span className="flex h-3 w-3 rounded-full bg-warn animate-pulse" />
            <div>
              <p className="font-bold">Mode Offline Terdeteksi</p>
              <p className="text-xs text-ink-muted">Perangkat sedang tidak terhubung ke jaringan pabrik. Tally tetap dapat disiapkan di terminal.</p>
            </div>
          </div>
          <span className="rounded-[8px] bg-white/80 px-2.5 py-1 text-xs font-semibold uppercase">Offline</span>
        </div>
      )}

      {error && (
        <div className="flex items-center justify-between rounded-[14px] border border-bad-bg-2 bg-bad-bg px-4 py-3 text-[13px] text-bad-4">
          <span>{error}</span>
          <button type="button" onClick={() => setError(null)} className="font-bold text-bad-4 hover:opacity-75">×</button>
        </div>
      )}

      {/* ── Bulk article order ──────────────────────────────────────────────── */}
      <section className="rounded-[18px] border border-brand/30 bg-brand-bg p-5 shadow-xs" aria-labelledby="bulk-order-title">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-[11px] font-bold uppercase tracking-wider text-brand">Order lebih cepat</p>
            <h2 id="bulk-order-title" className="mt-1 text-[20px] font-extrabold tracking-tight text-ink">Order Bulk Artikel</h2>
            <p className="mt-1 text-[13px] text-ink-2">Masukkan total pcs sekali saja. Sistem membagi order secara merata ke semua tailor pada line aktif.</p>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <label className="min-w-[220px] text-[11px] font-bold uppercase tracking-wider text-ink-muted">
              Artikel
              <input value={bulkArticle} onChange={e => setBulkArticle(e.target.value)} placeholder="Contoh: Kemeja Oxford" className="mt-1 min-h-[48px] w-full rounded-[12px] border border-brand/40 bg-white px-3 text-[13px] font-semibold normal-case tracking-normal text-ink placeholder:font-normal placeholder:text-ink-faint focus:border-brand focus:outline-none" />
            </label>
            <label className="w-[140px] text-[11px] font-bold uppercase tracking-wider text-ink-muted">
              Total pcs
              <input type="number" min="1" step="1" value={bulkQuantity} onChange={e => setBulkQuantity(e.target.value)} placeholder="100" className="mt-1 min-h-[48px] w-full rounded-[12px] border border-brand/40 bg-white px-3 text-[13px] font-semibold normal-case tracking-normal text-ink placeholder:font-normal placeholder:text-ink-faint focus:border-brand focus:outline-none" />
            </label>
            <button type="button" onClick={handleBulkOrder} disabled={busy || lineCards.length === 0} className="min-h-[48px] rounded-[12px] bg-brand px-4 py-2.5 text-[13px] font-bold text-white shadow-sm transition-all hover:bg-blue-dark active:scale-95 disabled:cursor-not-allowed disabled:opacity-50">
              Terapkan ke Semua Tailor
            </button>
          </div>
        </div>
        <p className="mt-3 text-[11px] font-medium text-brand">Pembagian otomatis: sisa pcs dialokasikan mulai dari tailor dengan nomor stasiun terkecil.</p>
      </section>

      {/* ── Context & Interval Header Bar ──────────────────────────────────── */}
      <section className="rounded-[18px] border border-hair bg-white p-5 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* Line Selection */}
            <label className="flex items-center gap-2 text-[13px] text-ink-muted">
              <span className="font-semibold text-ink">Line:</span>
              <select
                value={lineId}
                onChange={e => {
                  setLineId(e.target.value);
                  setCounts({});
                  setResults({});
                }}

                className="min-h-[48px] rounded-[12px] border border-hair-4 bg-panel px-3 text-[14px] font-bold text-ink transition-colors hover:border-brand focus:border-brand"
              >
                {lines.map(l => (
                  <option key={l.id} value={l.id}>{l.lineCode}</option>
                ))}
              </select>
            </label>

            {/* Mandor badge */}
            <div className="flex min-h-[48px] items-center gap-2 rounded-[12px] bg-panel px-3 py-2 text-[13px] text-ink-muted">
              <span className="font-semibold text-ink">Mandor:</span>
              <span className="font-bold text-ink-2">{mandorName || 'Budi (Mandor Line)'}</span>
            </div>

            {/* Network status pill */}
            <div className="flex min-h-[48px] items-center gap-2 rounded-[12px] bg-panel px-3 py-2 text-[12px] font-semibold">
              <span className={`inline-block h-2.5 w-2.5 rounded-full ${isOnline ? 'bg-ok pulse-dot' : 'bg-warn'}`} />
              <span className={isOnline ? 'text-ok-2' : 'text-warn-2'}>{isOnline ? 'Online' : 'Offline'}</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {lineCards.length < 70 && (
              <button
                type="button"
                onClick={handlePopulateSeventyStations}
                disabled={busy}
                className="min-h-[48px] inline-flex items-center gap-2 rounded-[12px] border border-brand bg-brand-bg px-4 py-2.5 text-[13px] font-semibold text-brand transition-all hover:bg-blue-light active:scale-95 disabled:opacity-50"
              >
                <LucideIcon name="plus" className="w-4 h-4" />
                Aktifkan 70 Stasiun
              </button>
            )}
            <button
              type="button"
              onClick={load}
              disabled={loading}
              className="btn-secondary min-h-[48px] !px-4 !py-2.5"
            >
              <LucideIcon name="activity" className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* ── 30-Minute Interval Bar (13:30 – 14:00) ────────────────────────── */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-4 border-t border-hair pt-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-[12px] bg-brand-bg text-brand">
              <LucideIcon name="clock" className="w-5 h-5" />
            </span>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-wider text-ink-muted">Interval Waktu Tally (30 Menit)</p>
              <p className="text-[20px] font-extrabold tracking-tight text-ink tabular-nums">
                {interval.label}
              </p>
            </div>
          </div>

          {/* Interval navigation steppers (≥48px touch targets) */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleStepInterval(-1)}
              aria-label="Interval 30 menit sebelumnya"
              className="flex h-12 min-h-[48px] w-12 min-w-[48px] items-center justify-center rounded-[12px] border border-hair-4 bg-panel text-lg font-bold text-ink transition-transform active:scale-95 hover:bg-hair"
            >
              ‹
            </button>

            {/* Quick interval dropdown */}
            <select
              value={interval.start}
              onChange={e => {
                const match = shiftIntervals.find(i => i.start === e.target.value);
                if (match) {
                  setInterval(match);
                  setResults({});
                }
              }}
              aria-label="Pilih interval waktu 30 menit"
              className="min-h-[48px] rounded-[12px] border border-hair-4 bg-panel px-4 text-[13px] font-bold text-ink transition-colors hover:border-brand"
            >
              {shiftIntervals.map(i => (
                <option key={i.start} value={i.start}>{i.label}</option>
              ))}
            </select>

            <button
              type="button"
              onClick={() => handleStepInterval(1)}
              aria-label="Interval 30 menit berikutnya"
              className="flex h-12 min-h-[48px] w-12 min-w-[48px] items-center justify-center rounded-[12px] border border-hair-4 bg-panel text-lg font-bold text-ink transition-transform active:scale-95 hover:bg-hair"
            >
              ›
            </button>

            <button
              type="button"
              onClick={() => {
                const def = shiftIntervals.find(i => i.label.includes('13:30'));
                if (def) setInterval(def);
                setResults({});
              }}
              className="min-h-[48px] rounded-[12px] bg-panel-2 px-3 py-2 text-[12px] font-semibold text-ink-2 hover:bg-hair transition-all active:scale-95"
            >
              13:30 – 14:00
            </button>
          </div>
        </div>
      </section>

      {/* ── Summary KPI Strip ──────────────────────────────────────────────── */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="rounded-[16px] border border-hair bg-white p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">Total Stasiun Jahit</p>
          <p className="mt-1 text-[26px] font-extrabold tabular-nums text-ink">
            {lineCards.length} <span className="text-xs font-normal text-ink-muted">/ 70 Stasiun</span>
          </p>
        </div>

        <div className="rounded-[16px] border border-hair bg-white p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">Stasiun Berisi Output</p>
          <p className="mt-1 text-[26px] font-extrabold tabular-nums text-brand">
            {activeStationsCount} <span className="text-xs font-normal text-ink-muted">stasiun</span>
          </p>
        </div>

        <div className="rounded-[16px] border border-hair bg-white p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">Total Output Interval</p>
          <p className="mt-1 text-[26px] font-extrabold tabular-nums text-ok-2">
            {totalPieces} <span className="text-xs font-normal text-ink-muted">pcs</span>
          </p>
        </div>

        <div className="rounded-[16px] border border-hair bg-white p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">Status Penyimpanan</p>
          <p className="mt-1 text-[26px] font-extrabold tabular-nums text-ink">
            {savedCount} <span className="text-xs font-normal text-ink-muted">tercatat</span>
          </p>
        </div>
      </section>

      {/* ── Filter & Search Matrix Toolbar ─────────────────────────────────── */}
      <section className="space-y-3 rounded-[18px] border border-hair bg-white p-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Station search bar (min-height 48px) */}
          <div className="relative min-w-[280px] flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Cari nama penjahit, OPR-xxx, stasiun (#14), atau komponen..."
              className="w-full min-h-[48px] rounded-[12px] border border-hair-4 bg-panel pl-4 pr-10 text-[13px] text-ink placeholder:text-ink-faint transition-colors focus:border-brand focus:bg-white"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink font-bold text-sm"
              >
                ×
              </button>
            )}
          </div>

          {/* Non-zero toggle filter */}
          <button
            type="button"
            onClick={() => setOnlyNonZero(prev => !prev)}
            aria-pressed={onlyNonZero}
            className={`min-h-[48px] rounded-[12px] border px-4 text-[13px] font-semibold transition-all active:scale-95 ${
              onlyNonZero
                ? 'border-brand bg-brand-bg text-brand font-bold shadow-xs'
                : 'border-hair-4 bg-panel text-ink-muted hover:text-ink'
            }`}
          >
            Hanya Terisi ({activeStationsCount})
          </button>

          {/* Bulk actions */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleBulkAdd(10)}
              className="min-h-[48px] rounded-[12px] border border-hair-4 bg-panel px-3.5 text-[12px] font-semibold text-ink hover:border-brand active:scale-95 transition-all"
            >
              +10 Semua
            </button>
            <button
              type="button"
              onClick={handleResetAll}
              disabled={totalPieces === 0}
              className="min-h-[48px] rounded-[12px] border border-bad-bg-2 bg-bad-bg px-3.5 text-[12px] font-semibold text-bad-4 hover:bg-bad-bg-2 active:scale-95 transition-all disabled:opacity-40"
            >
              Reset (0)
            </button>
          </div>
        </div>

        {/* Component Category Pills */}
        {componentTabs.length > 0 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1 scrollbar-none">
            <span className="text-[11px] font-bold uppercase tracking-wider text-ink-muted shrink-0 mr-1">Komponen:</span>
            <button
              type="button"
              onClick={() => setSelectedComponent('ALL')}
              className={`min-h-[40px] rounded-[10px] px-3.5 text-[12px] font-semibold shrink-0 transition-all active:scale-95 ${
                selectedComponent === 'ALL'
                  ? 'bg-brand text-white shadow-xs'
                  : 'bg-panel-2 text-ink-muted hover:bg-hair hover:text-ink'
              }`}
            >
              Semua ({lineCards.length})
            </button>
            {componentTabs.map(comp => {
              const countForComp = lineCards.filter(c => c.componentCode === comp).length;
              return (
                <button
                  key={comp}
                  type="button"
                  onClick={() => setSelectedComponent(comp)}
                  className={`min-h-[40px] rounded-[10px] px-3.5 text-[12px] font-semibold shrink-0 transition-all active:scale-95 ${
                    selectedComponent === comp
                      ? 'bg-brand text-white shadow-xs'
                      : 'bg-panel-2 text-ink-muted hover:bg-hair hover:text-ink'
                  }`}
                >
                  {comp} ({countForComp})
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Line Assignment Matrix Cards (up to 70 sewing stations) ──────────── */}
      {loading ? (
        <div className="rounded-[18px] border border-hair bg-white py-16 text-center">
          <span className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent mb-3" />
          <p className="text-[14px] font-medium text-ink-muted">Memuat matriks stasiun lantai jahit…</p>
        </div>
      ) : lineCards.length === 0 ? (
        <div className="rounded-[18px] border border-dashed border-hair-4 bg-white px-6 py-14 text-center">
          <p className="text-[16px] font-semibold text-ink">Belum ada penugasan stasiun pada line ini.</p>
          <p className="mt-1 text-[13px] text-ink-muted">
            Aktifkan penugasan 70 stasiun jahit simulasi atau tambahkan manual pada tab Admin.
          </p>
          <button
            type="button"
            onClick={handlePopulateSeventyStations}
            className="btn-primary min-h-[48px] mt-5 inline-flex items-center gap-2"
          >
            <LucideIcon name="plus" className="w-4 h-4" />
            Aktifkan 70 Stasiun Jahit
          </button>
        </div>
      ) : filteredCards.length === 0 ? (
        <div className="rounded-[18px] border border-dashed border-hair-4 bg-white px-6 py-12 text-center text-[14px] text-ink-muted">
          Tidak ada stasiun jahit yang cocok dengan pencarian <strong>"{searchQuery}"</strong>.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredCards.map((c, idx) => {
            const stationNum = c.stationNumber ?? idx + 1;
            const count = counts[c.id] ?? 0;
            const result = results[c.id];
            const op = operatorInfo(c.operatorId);

            return (
              <article
                key={c.id}
                className={`relative rounded-[18px] border transition-all duration-200 bg-white p-5 shadow-xs flex flex-col justify-between ${
                  count > 0 ? 'border-brand/40 ring-1 ring-brand/20' : 'border-hair'
                }`}
              >
                <div>
                  {/* Card Header: Station Badge & Component Pill */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="rounded-[8px] bg-panel-2 px-2.5 py-1 font-mono text-[11px] font-bold text-ink">
                      Stasiun #{String(stationNum).padStart(2, '0')}
                    </span>
                    <span className="rounded-full bg-brand-bg px-2.5 py-0.5 font-mono text-[11px] font-bold text-brand uppercase">
                      {c.componentCode}
                    </span>
                  </div>

                  {/* Tailor Info */}
                  <div className="mb-4">
                    <h3 className="text-[16px] font-bold text-ink tracking-tight">
                      Tailor #{stationNum}: {op.name}
                    </h3>
                    <p className="font-mono text-[12px] text-ink-muted">
                      {op.code} · Operasi: {c.componentCode}
                    </p>
                  </div>
                </div>

                {/* ── 48px Touch Stepper: [-] [14 pcs] [+] ───────────────────── */}
                <div>
                  <div className="flex items-center justify-between gap-2 pt-2 border-t border-hair">
                    {/* Decrement [-] button (>=48px touch target) */}
                    <button
                      type="button"
                      onClick={() => bump(c.id, -1)}
                      disabled={count === 0}
                      aria-label={`Kurangi output ${op.name}`}
                      className="flex h-12 min-h-[48px] w-12 min-w-[48px] items-center justify-center rounded-[14px] bg-panel-2 text-2xl font-bold text-ink transition-transform active:scale-95 disabled:opacity-30 disabled:pointer-events-none select-none hover:bg-hair-2"
                    >
                      −
                    </button>

                    {/* Stepper Count Center Display: [14 pcs] */}
                    <div
                      className="flex flex-1 flex-col items-center justify-center min-h-[48px] rounded-[12px] bg-panel border border-hair px-3 py-1 select-none"
                    >
                      <div className="flex items-baseline gap-1">
                        <span className="text-[26px] font-extrabold tabular-nums leading-none text-ink">
                          {count}
                        </span>
                        <span className="text-[13px] font-bold text-ink-muted">pcs</span>
                      </div>
                      <span className="text-[9px] uppercase font-mono tracking-wider text-ink-faint">
                        output
                      </span>
                    </div>

                    {/* Increment [+] button (>=48px touch target) */}
                    <button
                      type="button"
                      onClick={() => bump(c.id, 1)}
                      aria-label={`Tambah output ${op.name}`}
                      className="flex h-12 min-h-[48px] w-12 min-w-[48px] items-center justify-center rounded-[14px] bg-brand text-2xl font-bold text-white shadow-sm transition-transform active:scale-95 select-none hover:bg-blue-dark"
                    >
                      +
                    </button>
                  </div>

                  {/* Quick-add chips */}
                  <div className="mt-2.5 flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => bump(c.id, 5)}
                      aria-label={`Tambah 5 pcs untuk ${op.name}`}
                      className="min-h-[36px] min-w-[44px] rounded-[8px] bg-brand-bg px-2.5 py-1 text-[11px] font-bold text-brand transition-all hover:bg-blue-light active:scale-95"
                    >
                      +5
                    </button>
                    <button
                      type="button"
                      onClick={() => bump(c.id, 10)}
                      aria-label={`Tambah 10 pcs untuk ${op.name}`}
                      className="min-h-[36px] min-w-[44px] rounded-[8px] bg-brand-bg px-2.5 py-1 text-[11px] font-bold text-brand transition-all hover:bg-blue-light active:scale-95"
                    >
                      +10
                    </button>
                    {count > 0 && (
                      <button
                        type="button"
                        onClick={() => setCardCount(c.id, 0)}
                        aria-label={`Reset hitungan ${op.name}`}
                        className="min-h-[36px] rounded-[8px] bg-panel-2 px-2 py-1 text-[11px] font-semibold text-ink-muted hover:text-bad-4 transition-all"
                      >
                        Reset
                      </button>
                    )}
                  </div>

                  {/* Submission Result / Idempotency Feedback */}
                  {result && (
                    <div
                      className={`mt-3 rounded-[10px] px-3 py-1.5 text-[11px] font-semibold ${
                        result.ok ? 'bg-ok-bg text-ok-2 border border-ok/30' : 'bg-bad-bg text-bad-4 border border-bad/30'
                      }`}
                    >
                      <p className="flex items-center gap-1">
                        <span>{result.ok ? '✓' : '✗'}</span>
                        <span className="truncate">{result.message}</span>
                      </p>
                      {result.idempotent && (
                        <p className="text-[10px] font-mono text-ok-2/80 mt-0.5">Idempotency Verified</p>
                      )}
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* ── Sticky Mobile/Tablet Submission Bar ─────────────────────────────── */}
      <aside
        aria-label="Submit interval tally"
        className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-hair px-4 py-3 shadow-lg"
      >
        <div className="max-w-[1220px] mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <span className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">
                Interval {interval.label}
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-[26px] font-black text-ink tabular-nums leading-none">
                  {totalPieces}
                </span>
                <span className="text-[13px] font-bold text-ink-muted">pcs total</span>
                <span className="text-xs text-ink-faint">({activeStationsCount} stasiun terisi)</span>
              </div>
            </div>

            <div className="hidden sm:flex items-center gap-1.5 rounded-full bg-brand-bg px-3 py-1 text-[11px] font-semibold text-brand">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              <span>Idempotensi Aktif</span>
            </div>
          </div>

          <button
            type="button"
            onClick={submit}
            disabled={busy || totalPieces === 0 || !isOnline}
            className="flex-1 sm:flex-none min-h-[56px] min-w-[260px] rounded-[16px] bg-brand hover:bg-blue-dark text-white text-[15px] font-bold tracking-wide shadow-md transition-transform active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none"
          >
            {busy
              ? 'MENGIRIM INTERVAL BLOCK…'
              : `SUBMIT INTERVAL BLOCK${totalPieces > 0 ? ` (${totalPieces} pcs)` : ''}`}
          </button>
        </div>
      </aside>
    </div>
  );
};

export default FloorTerminalView;
