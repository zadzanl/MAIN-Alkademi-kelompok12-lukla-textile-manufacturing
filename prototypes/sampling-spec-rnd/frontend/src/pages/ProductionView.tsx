/**
 * ProductionView — VIEW-04: production line, operators, assignments,
 * 30-minute sewing tally, assembly staging, and progress.
 *
 * Backed by services/opsApi.ts (mock by default). The tally flow mirrors the
 * contract: record → RECORDED, verify → VERIFIED; assemblies land in MENUNGGU_QC
 * for the QC view (VIEW-05).
 *
 * Features:
 * - Line assignment matrix up to 70 sewing stations with station indexing (1..70) and visual grid.
 * - 30-minute interval timing and verified idempotency key submission.
 * - Touch targets ≥ 48px across all clickable elements and controls.
 * - Integrated toast notifications and offline awareness.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LucideIcon } from '../components/Sidebar';
import Modal from '../components/Modal';
import MockModeBanner from '../components/MockModeBanner';
import {
  listLines, createLine,
  listOperators, createOperator,
  listAssignments, assignOperator,
  recordSewingTally, verifySewingTally,
  listAssemblies, createAssembly,
  listProductionProgress,
  isMockOps,
  seedSeventyStations,
  type Line, type Operator, type Assignment, type Assembly, type ProgressItem,
  type AssemblyStatus, type TallyResult, type TallyInput,
} from '../services/opsApi';
import { toast } from '../services/toast';
import { buildStacked } from '../utils/chartData';
import StackedBarChart, { type StackedKey } from '../components/StackedBarChart';
import FloorTerminalView from './FloorTerminalView';

const inputCls = 'w-full min-h-[48px] rounded-[10px] px-3.5 py-2.5 text-[13px] border border-hair-4 bg-white text-ink transition-colors focus:border-brand focus:outline-none';

const STATUS_STYLE: Record<AssemblyStatus, string> = {
  MENUNGGU_QC: 'bg-warn-bg text-warn-2',
  QC_PASS: 'bg-ok-bg text-ok-2',
  REWORK: 'bg-brand-bg text-brand',
  REJECT_SCRAP: 'bg-bad-bg text-bad-4',
};

const STACKED_STATUS_KEYS: StackedKey[] = [
  { key: 'MENUNGGU_QC', label: 'Menunggu QC', color: '#ff9500' },
  { key: 'REWORK', label: 'Repair', color: '#0071e3' },
  { key: 'QC_PASS', label: 'Pass', color: '#34c759' },
  { key: 'REJECT_SCRAP', label: 'Reject', color: '#ff3b30' },
];

const TABS = [
  { id: 'floor', label: 'Line & Operator' },
  { id: 'assign', label: 'Matriks 70 Stasiun' },
  { id: 'tally', label: 'Tally 30 Menit' },
  { id: 'assembly', label: 'Assembly' },
  { id: 'progress', label: 'Progress' },
] as const;
type TabId = typeof TABS[number]['id'];

interface SessionTally { result: TallyResult; input: TallyInput; }

function defaultInterval(): { start: string; end: string; label: string } {
  const now = new Date();
  // Standard benchmark 13:30 - 14:00
  const s = new Date(now);
  s.setHours(13, 30, 0, 0);
  const e = new Date(now);
  e.setHours(14, 0, 0, 0);

  const fmt = (d: Date) => {
    const p = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
  };
  return { start: fmt(s), end: fmt(e), label: '13:30 – 14:00' };
}

const ProductionView: React.FC = () => {
  const [mode, setMode] = useState<'terminal' | 'admin'>('terminal');
  const [tab, setTab] = useState<TabId>('floor');
  const [error, setError] = useState<string | null>(null);

  const [lines, setLines] = useState<Line[]>([]);
  const [operators, setOperators] = useState<Operator[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [assemblies, setAssemblies] = useState<Assembly[]>([]);
  const [progress, setProgress] = useState<ProgressItem[]>([]);
  const [tallies, setTallies] = useState<SessionTally[]>([]);

  // Selected line for the 70 sewing stations matrix
  const [selectedMatrixLine, setSelectedMatrixLine] = useState('');
  const [assignSearch, setAssignSearch] = useState('');

  // modals
  const [showLine, setShowLine] = useState(false);
  const [lineCode, setLineCode] = useState('');
  const [showOperator, setShowOperator] = useState(false);
  const [opName, setOpName] = useState('');
  const [opCode, setOpCode] = useState('');
  const [showAssign, setShowAssign] = useState(false);
  const [assignDraft, setAssignDraft] = useState({
    lineId: '',
    operatorId: '',
    componentCode: 'SLEEVE',
    validFrom: '',
    validThrough: '',
    stationNumber: 1,
  });
  const [showTally, setShowTally] = useState(false);
  const [tallyDraft, setTallyDraft] = useState<TallyInput>(() => {
    const { start, end } = defaultInterval();
    return {
      orderId: '33333333-3333-4333-8333-333333333333',
      cutBatchId: '22222222-2222-4222-8222-222222222222',
      lineId: '',
      componentCode: 'SLEEVE',
      operatorId: '',
      intervalStart: start,
      intervalEnd: end,
      pieces: 14,
      idempotencyKey: `tally-man-${Date.now()}`,
    };
  });
  const [showAssembly, setShowAssembly] = useState(false);
  const [assemblyDraft, setAssemblyDraft] = useState({ orderId: '33333333-3333-4333-8333-333333333333', serialCode: '', componentUnitIds: '' });
  const [verifyTarget, setVerifyTarget] = useState<SessionTally | null>(null);
  const [verifyReason, setVerifyReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const [rl, ro, ra, rasm, rp] = await Promise.all([
      listLines(), listOperators(), listAssignments(), listAssemblies(), listProductionProgress(),
    ]);
    if (rl.ok && rl.data) setLines(rl.data.items);
    if (ro.ok && ro.data) setOperators(ro.data.items);
    if (ra.ok && ra.data) setAssignments(ra.data.items);
    if (rasm.ok && rasm.data) setAssemblies(rasm.data.items);
    if (rp.ok && rp.data) setProgress(rp.data.items);
    const firstErr = [rl, ro, ra, rasm, rp].find(r => !r.ok);
    if (firstErr) {
      const msg = firstErr.error ?? 'Gagal memuat data produksi.';
      setError(msg);
      toast.error(msg);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!selectedMatrixLine && lines.length > 0) {
      setSelectedMatrixLine(lines[0].id);
    }
  }, [lines, selectedMatrixLine]);

  const run = async (fn: () => Promise<{ ok: boolean; error?: string }>, close: () => void, successMsg?: string) => {
    setBusy(true);
    setFormError(null);
    const res = await fn();
    setBusy(false);
    if (!res.ok) {
      const msg = res.error ?? 'Gagal menyimpan.';
      setFormError(msg);
      toast.error(msg);
      return;
    }
    if (successMsg) toast.success(successMsg);
    close();
    await load();
  };

  const lineName = (id: string) => lines.find(l => l.id === id)?.lineCode ?? id.slice(0, 8);
  const operatorName = (id: string) => operators.find(o => o.id === id)?.displayName ?? id.slice(0, 8);
  const pendingQc = assemblies.filter(a => a.status === 'MENUNGGU_QC').length;

  // Filtered assignments for the selected line
  const matrixLineAssignments = useMemo(() => {
    return assignments.filter(a => a.lineId === selectedMatrixLine);
  }, [assignments, selectedMatrixLine]);

  // Construct 70 station slots map
  const seventyStations = useMemo(() => {
    const slots: { stationNumber: number; assignment: Assignment | null; operator: Operator | null }[] = [];
    for (let i = 1; i <= 70; i++) {
      const found = matrixLineAssignments.find(a => a.stationNumber === i);
      const op = found ? operators.find(o => o.id === found.operatorId) ?? null : null;
      slots.push({
        stationNumber: i,
        assignment: found ?? null,
        operator: op,
      });
    }
    return slots;
  }, [matrixLineAssignments, operators]);

  // Filtered slots according to search query
  const filteredStationSlots = useMemo(() => {
    if (!assignSearch.trim()) return seventyStations;
    const q = assignSearch.toLowerCase();
    return seventyStations.filter(s => {
      const name = s.operator?.displayName?.toLowerCase() ?? '';
      const code = s.operator?.employeeCode?.toLowerCase() ?? '';
      const comp = s.assignment?.componentCode?.toLowerCase() ?? '';
      const stStr = `#${s.stationNumber}`;
      return name.includes(q) || code.includes(q) || comp.includes(q) || stStr.includes(q);
    });
  }, [seventyStations, assignSearch]);

  const occupiedStationCount = seventyStations.filter(s => s.assignment !== null).length;

  // Output composition: pieces per component, stacked by assembly status.
  const byComponent = new Map<string, Record<string, number>>();
  for (const p of progress) {
    const comp = p.componentCode || '—';
    const qty = Number(p.quantity?.value) || 0;
    const row = byComponent.get(comp) ?? {};
    row[p.status] = (row[p.status] ?? 0) + qty;
    byComponent.set(comp, row);
  }
  const stackedData = buildStacked(
    [...byComponent.entries()].map(([label, values]) => ({ label, values })),
    STACKED_STATUS_KEYS.map(k => k.key),
  );

  const kpis = [
    { label: 'Line Aktif', value: lines.filter(l => l.active).length },
    { label: 'Operator Terdaftar', value: operators.length },
    { label: 'Tally Sesi Ini', value: tallies.length },
    { label: 'Menunggu QC', value: pendingQc },
  ];

  const handleReseedSeventy = async () => {
    if (!selectedMatrixLine) return;
    setBusy(true);
    seedSeventyStations(selectedMatrixLine);
    await load();
    setBusy(false);
    toast.success(`Matriks 70 stasiun berhasil diaktifkan untuk Line ${lineName(selectedMatrixLine)}.`);
  };

  return (
    <div className="space-y-5">
      {/* View Switcher: Terminal Lantai vs Admin Mode */}
      <div className="inline-flex gap-1 rounded-[14px] bg-panel-2 p-1.5 shadow-xs">
        {([['terminal', 'Terminal Lantai (Mandor)'], ['admin', 'Admin Produksi']] as const).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setMode(id)}
            className={`min-h-[48px] rounded-[10px] px-5 text-[13px] font-bold transition-all ${
              mode === id ? 'bg-white text-ink shadow-sm' : 'text-ink-muted hover:text-ink'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {mode === 'terminal' ? (
        <FloorTerminalView />
      ) : (
        <>
          {/* Header Title */}
          <div className="flex flex-wrap justify-between items-center gap-3">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-ink">Produksi &amp; Tally 30 Menit</h2>
              <p className="text-ink-muted text-sm mt-0.5">
                Line jahit, penugasan stasiun (1–70), pencatatan output interval 30 menit (idempotensi terlindungi), dan staging ke QC
              </p>
            </div>
            <button onClick={load} className="btn-secondary min-h-[48px] !px-4 !py-2.5">
              <LucideIcon name="activity" className="w-4 h-4" /> Refresh
            </button>
          </div>

          {isMockOps && <MockModeBanner detail="data disimpan di memori mock (kontrak OpenAPI terverifikasi)." />}
          {error && (
            <div className="rounded-[14px] border border-bad-bg-2 bg-bad-bg px-4 py-3 text-[13px] text-bad-4">
              {error}
            </div>
          )}

          {/* KPI Strip */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {kpis.map(({ label, value }) => (
              <div key={label} className="bg-white border border-hair rounded-[18px] p-5 text-center shadow-xs">
                <p className="text-xs text-ink-muted uppercase font-bold tracking-wider mb-1">{label}</p>
                <p className="text-[30px] font-extrabold tabular-nums text-ink">{value}</p>
              </div>
            ))}
          </div>

          {/* Tabs Container */}
          <div className="bg-white border border-hair rounded-[18px] overflow-hidden shadow-xs">
            <div className="flex gap-1 p-3 border-b border-panel-2 overflow-x-auto scrollbar-none">
              {TABS.map(t => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`tab min-h-[48px] rounded-[10px] px-5 py-2.5 text-[13px] whitespace-nowrap transition-all font-semibold ${
                    tab === t.id ? 'bg-brand-bg text-brand font-bold shadow-xs' : 'text-ink-muted hover:bg-page'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <div className="p-6">
              {/* ── Floor Tab: lines & operators ────────────────────────────── */}
              {tab === 'floor' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <div>
                        <p className="text-[16px] font-bold text-ink">Line Produksi</p>
                        <p className="text-xs text-ink-muted">Daftar jalur perakitan jahit aktif</p>
                      </div>
                      <button
                        onClick={() => { setLineCode(''); setFormError(null); setShowLine(true); }}
                        className="btn-secondary min-h-[48px] !px-4"
                      >
                        <LucideIcon name="plus" className="w-4 h-4" /> Tambah Line
                      </button>
                    </div>
                    <div className="overflow-x-auto rounded-[12px] border border-hair">
                      <table className="w-full text-[13px]">
                        <thead>
                          <tr>
                            {['Kode Line', 'Status'].map(h => (
                              <th key={h} className="px-4 py-3 text-left text-[11px] font-bold text-ink-muted uppercase tracking-wider bg-panel border-b border-panel-2">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {lines.map(l => (
                            <tr key={l.id} className="border-b border-panel-2 last:border-0 hover:bg-panel">
                              <td className="px-4 py-3 font-bold text-ink">{l.lineCode}</td>
                              <td className="px-4 py-3">
                                <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-bold ${l.active ? 'bg-ok-bg text-ok-2' : 'bg-panel-2 text-ink-muted'}`}>
                                  {l.active ? 'Aktif' : 'Nonaktif'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {lines.length === 0 && <p className="text-center text-ink-muted py-6 text-[13px]">Belum ada line.</p>}
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <div>
                        <p className="text-[16px] font-bold text-ink">Operator Jahit (Tailor)</p>
                        <p className="text-xs text-ink-muted">Operator terdaftar di sistem ERP</p>
                      </div>
                      <button
                        onClick={() => { setOpName(''); setOpCode(''); setFormError(null); setShowOperator(true); }}
                        className="btn-secondary min-h-[48px] !px-4"
                      >
                        <LucideIcon name="plus" className="w-4 h-4" /> Tambah Operator
                      </button>
                    </div>
                    <div className="overflow-x-auto rounded-[12px] border border-hair max-h-[460px]">
                      <table className="w-full text-[13px]">
                        <thead>
                          <tr>
                            {['Nama Operator', 'Kode Karyawan', 'Status'].map(h => (
                              <th key={h} className="px-4 py-3 text-left text-[11px] font-bold text-ink-muted uppercase tracking-wider bg-panel border-b border-panel-2">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {operators.map(o => (
                            <tr key={o.id} className="border-b border-panel-2 last:border-0 hover:bg-panel">
                              <td className="px-4 py-3 font-semibold text-ink">{o.displayName}</td>
                              <td className="px-4 py-3 font-mono text-ink-muted">{o.employeeCode}</td>
                              <td className="px-4 py-3">
                                <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-bold ${o.active ? 'bg-ok-bg text-ok-2' : 'bg-panel-2 text-ink-muted'}`}>
                                  {o.active ? 'Aktif' : 'Nonaktif'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {operators.length === 0 && <p className="text-center text-ink-muted py-6 text-[13px]">Belum ada operator.</p>}
                  </div>
                </div>
              )}

              {/* ── Matriks 70 Stasiun Tab ───────────────────────────────────── */}
              {tab === 'assign' && (
                <div className="space-y-6">
                  {/* Matrix Controls & Capacity Header */}
                  <div className="flex flex-wrap items-center justify-between gap-4 rounded-[14px] bg-panel p-4 border border-hair">
                    <div className="flex flex-wrap items-center gap-4">
                      <label className="flex items-center gap-2 text-[13px] text-ink-muted">
                        <span className="font-bold text-ink">Line:</span>
                        <select
                          value={selectedMatrixLine}
                          onChange={e => setSelectedMatrixLine(e.target.value)}
                          className="min-h-[48px] rounded-[10px] border border-hair-4 bg-white px-3 font-bold text-ink"
                        >
                          {lines.map(l => (
                            <option key={l.id} value={l.id}>{l.lineCode}</option>
                          ))}
                        </select>
                      </label>

                      <div className="flex min-h-[48px] items-center gap-2 rounded-[10px] bg-white px-3 py-2 text-[13px] border border-hair">
                        <span className="font-bold text-ink">Kapasitas Line:</span>
                        <span className="font-extrabold text-brand tabular-nums">{occupiedStationCount} / 70 Stasiun Terisi</span>
                        <span className="text-xs text-ink-faint">({Math.round((occupiedStationCount / 70) * 100)}%)</span>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      <div className="relative min-w-[220px]">
                        <input
                          type="text"
                          value={assignSearch}
                          onChange={e => setAssignSearch(e.target.value)}
                          placeholder="Filter stasiun atau nama..."
                          className="w-full min-h-[48px] rounded-[10px] border border-hair-4 bg-white px-3 text-[13px] text-ink placeholder:text-ink-faint"
                        />
                      </div>

                      <button
                        type="button"
                        onClick={handleReseedSeventy}
                        disabled={busy}
                        className="min-h-[48px] rounded-[10px] border border-brand bg-brand-bg px-4 text-[13px] font-bold text-brand hover:bg-blue-light transition-all active:scale-95"
                      >
                        Aktifkan 70 Stasiun Line (Simulasi)
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setAssignDraft({
                            lineId: selectedMatrixLine,
                            operatorId: operators[0]?.id ?? '',
                            componentCode: 'SLEEVE',
                            validFrom: '',
                            validThrough: '',
                            stationNumber: occupiedStationCount + 1,
                          });
                          setFormError(null);
                          setShowAssign(true);
                        }}
                        className="btn-primary min-h-[48px] !px-4"
                      >
                        <LucideIcon name="plus" className="w-4 h-4" /> Assign Operator
                      </button>
                    </div>
                  </div>

                  {/* 70 Sewing Stations Visual Matrix Grid */}
                  <div>
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="text-[15px] font-bold text-ink">Visual Matrix: Stasiun Jahit 1–70 ({lineName(selectedMatrixLine)})</h3>
                      <span className="text-xs text-ink-muted">Tampilan interaktif stasiun lantai produksi</span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-7 xl:grid-cols-10 gap-2.5 max-h-[440px] overflow-y-auto p-1">
                      {filteredStationSlots.map(slot => {
                        const isAssigned = slot.assignment !== null;
                        return (
                          <div
                            key={slot.stationNumber}
                            onClick={() => {
                              if (!isAssigned) {
                                setAssignDraft({
                                  lineId: selectedMatrixLine,
                                  operatorId: operators[0]?.id ?? '',
                                  componentCode: 'SLEEVE',
                                  validFrom: '',
                                  validThrough: '',
                                  stationNumber: slot.stationNumber,
                                });
                                setShowAssign(true);
                              }
                            }}
                            className={`min-h-[76px] rounded-[12px] p-2 flex flex-col justify-between transition-all select-none ${
                              isAssigned
                                ? 'bg-brand-bg/50 border border-brand/40 hover:bg-brand-bg'
                                : 'bg-panel border border-dashed border-hair-4 hover:border-brand/70 hover:bg-white cursor-pointer'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-1">
                              <span className="font-mono text-[10px] font-bold text-ink">
                                #{String(slot.stationNumber).padStart(2, '0')}
                              </span>
                              {isAssigned && (
                                <span className="rounded-[4px] bg-white px-1 py-0.2 font-mono text-[9px] font-bold text-brand uppercase truncate max-w-[60px]">
                                  {slot.assignment?.componentCode}
                                </span>
                              )}
                            </div>

                            {isAssigned ? (
                              <div className="truncate">
                                <p className="font-bold text-[12px] text-ink truncate leading-tight">
                                  {slot.operator?.displayName}
                                </p>
                                <p className="font-mono text-[10px] text-ink-muted truncate">
                                  {slot.operator?.employeeCode}
                                </p>
                              </div>
                            ) : (
                              <div className="text-center py-1">
                                <span className="text-[11px] font-semibold text-ink-muted">+ Kosong</span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Assignments Detailed Table */}
                  <div>
                    <h3 className="text-[15px] font-bold text-ink mb-3">Tabel Penugasan Operator</h3>
                    <div className="overflow-x-auto rounded-[12px] border border-hair">
                      <table className="w-full text-[13px]">
                        <thead>
                          <tr>
                            {['Stasiun #', 'Line', 'Operator', 'Komponen', 'Berlaku'].map(h => (
                              <th key={h} className="px-4 py-3 text-left text-[11px] font-bold text-ink-muted uppercase tracking-wider bg-panel border-b border-panel-2">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {matrixLineAssignments.map((a, idx) => (
                            <tr key={a.id} className="border-b border-panel-2 last:border-0 hover:bg-panel">
                              <td className="px-4 py-3 font-mono font-bold text-ink">
                                #{String(a.stationNumber ?? idx + 1).padStart(2, '0')}
                              </td>
                              <td className="px-4 py-3 font-semibold text-ink">{lineName(a.lineId)}</td>
                              <td className="px-4 py-3 font-medium text-ink-2">{operatorName(a.operatorId)}</td>
                              <td className="px-4 py-3 font-mono text-ink-muted">{a.componentCode}</td>
                              <td className="px-4 py-3 text-ink-muted text-xs">{a.validFrom} → {a.validThrough}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {matrixLineAssignments.length === 0 && <p className="text-center text-ink-muted py-6 text-[13px]">Belum ada penugasan.</p>}
                  </div>
                </div>
              )}

              {/* ── Tally 30 Menit Tab ───────────────────────────────────────── */}
              {tab === 'tally' && (
                <div className="space-y-4">
                  <div className="flex flex-wrap justify-between items-center gap-3">
                    <div>
                      <p className="text-[16px] font-bold text-ink">Tally Output 30 Menit</p>
                      <p className="text-xs text-ink-muted mt-0.5">
                        Idempotency key menjamin anti-duplikasi tally. Output diverifikasi mandor sebelum menjadi hak upah borongan.
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        const { start, end } = defaultInterval();
                        setTallyDraft(d => ({
                          ...d,
                          lineId: lines[0]?.id ?? '',
                          operatorId: operators[0]?.id ?? '',
                          intervalStart: start,
                          intervalEnd: end,
                          pieces: 14,
                          idempotencyKey: `tally-man-${Date.now()}`,
                        }));
                        setFormError(null);
                        setShowTally(true);
                      }}
                      className="btn-primary min-h-[48px] inline-flex items-center gap-2 !px-4"
                    >
                      <LucideIcon name="plus" className="w-4 h-4" /> Catat Tally 30 Menit
                    </button>
                  </div>

                  <div className="overflow-x-auto rounded-[12px] border border-hair">
                    <table className="w-full text-[13px]">
                      <thead>
                        <tr>
                          {['Tally ID', 'Idempotency Key', 'Komponen', 'Line', 'Operator', 'Pieces', 'Status', 'Aksi'].map(h => (
                            <th key={h} className="px-4 py-3 text-left text-[11px] font-bold text-ink-muted uppercase tracking-wider bg-panel border-b border-panel-2">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {tallies.map(t => (
                          <tr key={t.result.tallyId} className="border-b border-panel-2 last:border-0 hover:bg-panel">
                            <td className="px-4 py-3"><code className="text-xs text-ink-muted">{t.result.tallyId.slice(0, 8)}</code></td>
                            <td className="px-4 py-3 font-mono text-xs text-ink-muted">{t.input.idempotencyKey ? t.input.idempotencyKey.slice(0, 16) + '…' : '—'}</td>
                            <td className="px-4 py-3 font-mono text-ink-muted">{t.input.componentCode}</td>
                            <td className="px-4 py-3 text-ink-2 font-medium">{lineName(t.input.lineId)}</td>
                            <td className="px-4 py-3 text-ink-2 font-medium">{operatorName(t.input.operatorId)}</td>
                            <td className="px-4 py-3 font-mono font-bold">{t.input.pieces} pcs</td>
                            <td className="px-4 py-3">
                              <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-bold ${t.result.status === 'VERIFIED' ? 'bg-ok-bg text-ok-2' : 'bg-warn-bg text-warn-2'}`}>
                                {t.result.status}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <button
                                disabled={t.result.status === 'VERIFIED'}
                                onClick={() => { setVerifyTarget(t); setVerifyReason(''); setFormError(null); }}
                                className="min-h-[48px] px-4 rounded-[10px] border border-hair-4 bg-white text-ink text-[12px] font-bold hover:border-brand disabled:opacity-40 transition-all"
                              >
                                Verifikasi
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {tallies.length === 0 && <p className="text-center text-ink-muted py-8 text-[13px]">Belum ada tally pada sesi ini. Catat dari Terminal Lantai atau tombol Catat Tally.</p>}
                </div>
              )}

              {/* ── Assemblies Tab ───────────────────────────────────────────── */}
              {tab === 'assembly' && (
                <div className="space-y-4">
                  <div className="flex flex-wrap justify-between items-center gap-3">
                    <div>
                      <p className="text-[16px] font-bold text-ink">Assembly &amp; Staging QC</p>
                      <p className="text-xs text-ink-muted mt-0.5">Gabungan komponen terjahit siap dikirim ke stasiun inspeksi QC (VIEW-05)</p>
                    </div>
                    <button
                      onClick={() => { setAssemblyDraft({ orderId: '33333333-3333-4333-8333-333333333333', serialCode: '', componentUnitIds: '' }); setFormError(null); setShowAssembly(true); }}
                      className="btn-secondary min-h-[48px] !px-4"
                    >
                      <LucideIcon name="plus" className="w-4 h-4" /> Assembly Baru
                    </button>
                  </div>

                  <div className="overflow-x-auto rounded-[12px] border border-hair">
                    <table className="w-full text-[13px]">
                      <thead>
                        <tr>
                          {['Serial Code', 'Order ID', 'Jml Komponen', 'Status'].map(h => (
                            <th key={h} className="px-4 py-3 text-left text-[11px] font-bold text-ink-muted uppercase tracking-wider bg-panel border-b border-panel-2">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {assemblies.map(a => (
                          <tr key={a.id} className="border-b border-panel-2 last:border-0 hover:bg-panel">
                            <td className="px-4 py-3 font-bold text-ink">{a.serialCode}</td>
                            <td className="px-4 py-3"><code className="text-xs text-ink-muted">{a.orderId.slice(0, 8)}</code></td>
                            <td className="px-4 py-3 font-mono text-ink-muted">{a.componentUnitIds.length} unit</td>
                            <td className="px-4 py-3">
                              <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-bold ${STATUS_STYLE[a.status]}`}>{a.status}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {assemblies.length === 0 && <p className="text-center text-ink-muted py-8 text-[13px]">Belum ada assembly.</p>}
                </div>
              )}

              {/* ── Progress Tab ─────────────────────────────────────────────── */}
              {tab === 'progress' && (
                <div className="space-y-6">
                  <StackedBarChart
                    data={stackedData}
                    keys={STACKED_STATUS_KEYS}
                    title="Komposisi Output per Komponen"
                    subtitle="Jumlah pieces per komponen, dipecah menurut status QC"
                  />
                  <div className="overflow-x-auto rounded-[12px] border border-hair">
                    <table className="w-full text-[13px]">
                      <thead>
                        <tr>
                          {['Order ID', 'Komponen', 'Jumlah Output', 'Status QC'].map(h => (
                            <th key={h} className="px-4 py-3 text-left text-[11px] font-bold text-ink-muted uppercase tracking-wider bg-panel border-b border-panel-2">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {progress.map((p, i) => (
                          <tr key={i} className="border-b border-panel-2 last:border-0 hover:bg-panel">
                            <td className="px-4 py-3"><code className="text-xs text-ink-muted">{p.orderId.slice(0, 8)}</code></td>
                            <td className="px-4 py-3 font-mono text-ink-muted font-bold">{p.componentCode}</td>
                            <td className="px-4 py-3 font-mono font-bold text-ink">{p.quantity.value} {p.quantity.unit}</td>
                            <td className="px-4 py-3">
                              <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-bold ${STATUS_STYLE[p.status]}`}>{p.status}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {progress.length === 0 && <p className="text-center text-ink-muted py-8 text-[13px]">Belum ada progress.</p>}
                </div>
              )}
            </div>
          </div>

          {/* ── Modal: Tambah Line ────────────────────────────────────────────── */}
          <Modal
            isOpen={showLine}
            title="Tambah Line Produksi"
            onClose={() => setShowLine(false)}
            footer={
              <div className="flex gap-3 justify-end">
                <button onClick={() => setShowLine(false)} className="btn-secondary min-h-[48px] !px-4">Batal</button>
                <button
                  onClick={() => run(() => createLine(lineCode), () => setShowLine(false), 'Line baru berhasil dibuat.')}
                  disabled={busy}
                  className="btn-primary min-h-[48px] !px-5"
                >
                  Simpan Line
                </button>
              </div>
            }
          >
            <div className="space-y-4">
              <label htmlFor="line-code" className="block text-sm font-semibold text-ink">Kode Line</label>
              <input
                id="line-code"
                value={lineCode}
                onChange={e => setLineCode(e.target.value)}
                placeholder="LINE-C"
                className={inputCls}
              />
              {formError && <p className="text-[13px] text-bad-4">{formError}</p>}
            </div>
          </Modal>

          {/* ── Modal: Tambah Operator ────────────────────────────────────────── */}
          <Modal
            isOpen={showOperator}
            title="Tambah Operator Jahit"
            onClose={() => setShowOperator(false)}
            footer={
              <div className="flex gap-3 justify-end">
                <button onClick={() => setShowOperator(false)} className="btn-secondary min-h-[48px] !px-4">Batal</button>
                <button
                  onClick={() => run(() => createOperator(opName, opCode), () => setShowOperator(false), 'Operator baru berhasil ditambahkan.')}
                  disabled={busy}
                  className="btn-primary min-h-[48px] !px-5"
                >
                  Simpan Operator
                </button>
              </div>
            }
          >
            <div className="space-y-4">
              <div>
                <label htmlFor="op-name" className="block text-sm font-semibold text-ink mb-1">Nama Lengkap</label>
                <input id="op-name" value={opName} onChange={e => setOpName(e.target.value)} placeholder="Ahmad Firdaus" className={inputCls} />
              </div>
              <div>
                <label htmlFor="op-code" className="block text-sm font-semibold text-ink mb-1">Kode Karyawan</label>
                <input id="op-code" value={opCode} onChange={e => setOpCode(e.target.value)} placeholder="OPR-071" className={inputCls} />
              </div>
              {formError && <p className="text-[13px] text-bad-4">{formError}</p>}
            </div>
          </Modal>

          {/* ── Modal: Assign Operator ────────────────────────────────────────── */}
          <Modal
            isOpen={showAssign}
            title="Assign Operator ke Stasiun Line"
            onClose={() => setShowAssign(false)}
            footer={
              <div className="flex gap-3 justify-end">
                <button onClick={() => setShowAssign(false)} className="btn-secondary min-h-[48px] !px-4">Batal</button>
                <button
                  onClick={() => run(() => assignOperator(assignDraft.lineId, {
                    operatorId: assignDraft.operatorId,
                    componentCode: assignDraft.componentCode,
                    stationNumber: assignDraft.stationNumber,
                    validFrom: assignDraft.validFrom || new Date().toISOString(),
                    validThrough: assignDraft.validThrough || new Date(Date.now() + 8 * 3600e3).toISOString(),
                  }), () => setShowAssign(false), `Operator berhasil di-assign ke Stasiun #${assignDraft.stationNumber}.`)}
                  disabled={busy}
                  className="btn-primary min-h-[48px] !px-5"
                >
                  Simpan Penugasan
                </button>
              </div>
            }
          >
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="as-line" className="block text-sm font-semibold text-ink mb-1">Line</label>
                  <select id="as-line" value={assignDraft.lineId} onChange={e => setAssignDraft(d => ({ ...d, lineId: e.target.value }))} className={inputCls}>
                    {lines.map(l => <option key={l.id} value={l.id}>{l.lineCode}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="as-station" className="block text-sm font-semibold text-ink mb-1">Nomor Stasiun (1–70)</label>
                  <input
                    id="as-station"
                    type="number"
                    min={1}
                    max={70}
                    value={assignDraft.stationNumber}
                    onChange={e => setAssignDraft(d => ({ ...d, stationNumber: parseInt(e.target.value) || 1 }))}
                    className={inputCls}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="as-op" className="block text-sm font-semibold text-ink mb-1">Operator</label>
                <select id="as-op" value={assignDraft.operatorId} onChange={e => setAssignDraft(d => ({ ...d, operatorId: e.target.value }))} className={inputCls}>
                  {operators.map(o => <option key={o.id} value={o.id}>{o.displayName} ({o.employeeCode})</option>)}
                </select>
              </div>

              <div>
                <label htmlFor="as-comp" className="block text-sm font-semibold text-ink mb-1">Komponen Operasi</label>
                <input id="as-comp" value={assignDraft.componentCode} onChange={e => setAssignDraft(d => ({ ...d, componentCode: e.target.value }))} placeholder="SLEEVE" className={inputCls} />
              </div>
              {formError && <p className="text-[13px] text-bad-4">{formError}</p>}
            </div>
          </Modal>

          {/* ── Modal: Record Tally ───────────────────────────────────────────── */}
          <Modal
            isOpen={showTally}
            title="Catat Tally 30 Menit (Idempotent Submission)"
            onClose={() => setShowTally(false)}
            footer={
              <div className="flex gap-3 justify-end">
                <button onClick={() => setShowTally(false)} className="btn-secondary min-h-[48px] !px-4">Batal</button>
                <button
                  onClick={() => run(async () => {
                    const res = await recordSewingTally({
                      ...tallyDraft,
                      intervalStart: new Date(tallyDraft.intervalStart).toISOString(),
                      intervalEnd: new Date(tallyDraft.intervalEnd).toISOString(),
                    });
                    if (res.ok && res.data) setTallies(prev => [{ result: res.data!, input: tallyDraft }, ...prev]);
                    return res;
                  }, () => setShowTally(false), `Tally 30 menit (${tallyDraft.pieces} pcs) berhasil dicatat dengan Idempotency Key.`)}
                  disabled={busy}
                  className="btn-primary min-h-[48px] !px-5"
                >
                  Simpan Tally
                </button>
              </div>
            }
          >
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="t-order" className="block text-sm font-semibold text-ink mb-1">Order ID</label>
                  <input id="t-order" value={tallyDraft.orderId} onChange={e => setTallyDraft(d => ({ ...d, orderId: e.target.value }))} className={inputCls} />
                </div>
                <div>
                  <label htmlFor="t-batch" className="block text-sm font-semibold text-ink mb-1">Cut Batch ID</label>
                  <input id="t-batch" value={tallyDraft.cutBatchId} onChange={e => setTallyDraft(d => ({ ...d, cutBatchId: e.target.value }))} className={inputCls} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="t-line" className="block text-sm font-semibold text-ink mb-1">Line</label>
                  <select id="t-line" value={tallyDraft.lineId} onChange={e => setTallyDraft(d => ({ ...d, lineId: e.target.value }))} className={inputCls}>
                    {lines.map(l => <option key={l.id} value={l.id}>{l.lineCode}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="t-op" className="block text-sm font-semibold text-ink mb-1">Operator</label>
                  <select id="t-op" value={tallyDraft.operatorId} onChange={e => setTallyDraft(d => ({ ...d, operatorId: e.target.value }))} className={inputCls}>
                    {operators.map(o => <option key={o.id} value={o.id}>{o.displayName} ({o.employeeCode})</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label htmlFor="t-comp" className="block text-sm font-semibold text-ink mb-1">Komponen</label>
                  <input id="t-comp" value={tallyDraft.componentCode} onChange={e => setTallyDraft(d => ({ ...d, componentCode: e.target.value }))} className={inputCls} />
                </div>
                <div>
                  <label htmlFor="t-start" className="block text-sm font-semibold text-ink mb-1">Mulai</label>
                  <input id="t-start" type="datetime-local" value={tallyDraft.intervalStart} onChange={e => setTallyDraft(d => ({ ...d, intervalStart: e.target.value }))} className={inputCls} />
                </div>
                <div>
                  <label htmlFor="t-end" className="block text-sm font-semibold text-ink mb-1">Selesai</label>
                  <input id="t-end" type="datetime-local" value={tallyDraft.intervalEnd} onChange={e => setTallyDraft(d => ({ ...d, intervalEnd: e.target.value }))} className={inputCls} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="t-pieces" className="block text-sm font-semibold text-ink mb-1">Jumlah Output Pieces</label>
                  <input id="t-pieces" type="number" min={1} value={tallyDraft.pieces || ''} onChange={e => setTallyDraft(d => ({ ...d, pieces: parseInt(e.target.value) || 0 }))} className={inputCls} />
                </div>
                <div>
                  <label htmlFor="t-idemp" className="block text-sm font-semibold text-ink mb-1">Idempotency Key</label>
                  <input id="t-idemp" value={tallyDraft.idempotencyKey ?? ''} onChange={e => setTallyDraft(d => ({ ...d, idempotencyKey: e.target.value }))} className={inputCls} />
                </div>
              </div>

              {formError && <p className="text-[13px] text-bad-4">{formError}</p>}
            </div>
          </Modal>

          {/* ── Modal: Tambah Assembly ────────────────────────────────────────── */}
          <Modal
            isOpen={showAssembly}
            title="Buat Assembly Baru"
            onClose={() => setShowAssembly(false)}
            footer={
              <div className="flex gap-3 justify-end">
                <button onClick={() => setShowAssembly(false)} className="btn-secondary min-h-[48px] !px-4">Batal</button>
                <button
                  onClick={() => run(() => createAssembly({
                    orderId: assemblyDraft.orderId,
                    serialCode: assemblyDraft.serialCode,
                    componentUnitIds: assemblyDraft.componentUnitIds.split(/[\s,]+/).map(s => s.trim()).filter(Boolean),
                  }), () => setShowAssembly(false), `Assembly ${assemblyDraft.serialCode} berhasil dibuat dan masuk antrian QC.`)}
                  disabled={busy}
                  className="btn-primary min-h-[48px] !px-5"
                >
                  Simpan Assembly
                </button>
              </div>
            }
          >
            <div className="space-y-4">
              <div>
                <label htmlFor="a-order" className="block text-sm font-semibold text-ink mb-1">Order ID</label>
                <input id="a-order" value={assemblyDraft.orderId} onChange={e => setAssemblyDraft(d => ({ ...d, orderId: e.target.value }))} className={inputCls} />
              </div>
              <div>
                <label htmlFor="a-serial" className="block text-sm font-semibold text-ink mb-1">Serial Code</label>
                <input id="a-serial" value={assemblyDraft.serialCode} onChange={e => setAssemblyDraft(d => ({ ...d, serialCode: e.target.value }))} placeholder="ASM-0002" className={inputCls} />
              </div>
              <div>
                <label htmlFor="a-units" className="block text-sm font-semibold text-ink mb-1">Component Unit IDs (pisahkan spasi/koma)</label>
                <textarea id="a-units" rows={3} value={assemblyDraft.componentUnitIds} onChange={e => setAssemblyDraft(d => ({ ...d, componentUnitIds: e.target.value }))} className={inputCls} />
              </div>
              {formError && <p className="text-[13px] text-bad-4">{formError}</p>}
            </div>
          </Modal>

          {/* ── Modal: Verifikasi Tally ───────────────────────────────────────── */}
          <Modal
            isOpen={verifyTarget !== null}
            title="Verifikasi Tally Mandor"
            onClose={() => setVerifyTarget(null)}
            footer={
              <div className="flex gap-3 justify-end">
                <button onClick={() => setVerifyTarget(null)} className="btn-secondary min-h-[48px] !px-4">Batal</button>
                <button
                  onClick={() => run(async () => {
                    const res = await verifySewingTally(verifyTarget!.result.tallyId, 'APPROVE', verifyReason);
                    if (res.ok && res.data) setTallies(prev => prev.map(t => t.result.tallyId === res.data!.tallyId ? { ...t, result: res.data! } : t));
                    return res;
                  }, () => setVerifyTarget(null), `Tally ${verifyTarget?.result.tallyId.slice(0, 8)} berhasil diverifikasi.`)}
                  disabled={busy}
                  className="btn-primary min-h-[48px] !px-5"
                >
                  Verifikasi Tally
                </button>
              </div>
            }
          >
            <div className="space-y-4">
              <p className="text-[13px] text-ink-2">
                Tally <code className="font-mono font-bold">{verifyTarget?.result.tallyId.slice(0, 8)}</code> · {verifyTarget?.input.pieces} pieces komponen {verifyTarget?.input.componentCode}.
              </p>
              <div>
                <label htmlFor="v-reason" className="block text-sm font-semibold text-ink mb-1">Catatan Verifikasi (opsional)</label>
                <input id="v-reason" value={verifyReason} onChange={e => setVerifyReason(e.target.value)} placeholder="Diverifikasi fisik sesuai potongan kain" className={inputCls} />
              </div>
              {formError && <p className="text-[13px] text-bad-4">{formError}</p>}
            </div>
          </Modal>
        </>
      )}
    </div>
  );
};

export default ProductionView;
