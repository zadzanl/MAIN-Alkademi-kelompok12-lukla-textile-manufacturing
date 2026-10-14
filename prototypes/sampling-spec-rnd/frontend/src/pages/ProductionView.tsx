/**
 * ProductionView — VIEW-04: production line, operators, assignments,
 * 30-minute sewing tally, assembly staging, and progress.
 *
 * Backed by services/opsApi.ts (mock by default). The tally flow mirrors the
 * contract: record → RECORDED, verify → VERIFIED; assemblies land in MENUNGGU_QC
 * for the QC view (VIEW-05).
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import Modal from '../components/Modal';
import {
  listLines, createLine,
  listOperators, createOperator,
  listAssignments, assignOperator,
  recordSewingTally, verifySewingTally,
  listAssemblies, createAssembly,
  listProductionProgress,
  isMockOps,
  type Line, type Operator, type Assignment, type Assembly, type ProgressItem,
  type AssemblyStatus, type TallyResult, type TallyInput,
} from '../services/opsApi';
import FloorTerminalView from './FloorTerminalView';

const inputCls = 'w-full rounded-[10px] px-3 py-2.5 text-[13px]';

const STATUS_STYLE: Record<AssemblyStatus, string> = {
  MENUNGGU_QC: 'bg-[#fff4e6] text-[#b86800]',
  QC_PASS: 'bg-[#e8f5e9] text-[#1a7a34]',
  REWORK: 'bg-[#e8f2ff] text-[#0066cc]',
  REJECT_SCRAP: 'bg-[#ffebee] text-[#dc2626]',
};

const TABS = [
  { id: 'floor', label: 'Line & Operator' },
  { id: 'assign', label: 'Penugasan' },
  { id: 'tally', label: 'Tally 30 Menit' },
  { id: 'assembly', label: 'Assembly' },
  { id: 'progress', label: 'Progress' },
] as const;
type TabId = typeof TABS[number]['id'];

interface SessionTally { result: TallyResult; input: TallyInput; }

function defaultInterval(): { start: string; end: string } {
  const now = new Date();
  now.setMinutes(now.getMinutes() < 30 ? 0 : 30, 0, 0);
  const end = new Date(now.getTime() + 30 * 60 * 1000);
  const fmt = (d: Date) => {
    const p = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
  };
  return { start: fmt(now), end: fmt(end) };
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

  // modals
  const [showLine, setShowLine] = useState(false);
  const [lineCode, setLineCode] = useState('');
  const [showOperator, setShowOperator] = useState(false);
  const [opName, setOpName] = useState('');
  const [opCode, setOpCode] = useState('');
  const [showAssign, setShowAssign] = useState(false);
  const [assignDraft, setAssignDraft] = useState({ lineId: '', operatorId: '', componentCode: 'SLEEVE', validFrom: '', validThrough: '' });
  const [showTally, setShowTally] = useState(false);
  const [tallyDraft, setTallyDraft] = useState<TallyInput>(() => {
    const { start, end } = defaultInterval();
    return { orderId: '33333333-3333-4333-8333-333333333333', cutBatchId: '22222222-2222-4222-8222-222222222222', lineId: '', componentCode: 'SLEEVE', operatorId: '', intervalStart: start, intervalEnd: end, pieces: 0 };
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
    if (firstErr) setError(firstErr.error ?? 'Gagal memuat data produksi.');
  }, []);

  useEffect(() => { load(); }, [load]);

  const run = async (fn: () => Promise<{ ok: boolean; error?: string }>, close: () => void) => {
    setBusy(true);
    setFormError(null);
    const res = await fn();
    setBusy(false);
    if (!res.ok) { setFormError(res.error ?? 'Gagal menyimpan.'); return; }
    close();
    await load();
  };

  const lineName = (id: string) => lines.find(l => l.id === id)?.lineCode ?? id.slice(0, 8);
  const operatorName = (id: string) => operators.find(o => o.id === id)?.displayName ?? id.slice(0, 8);
  const pendingQc = assemblies.filter(a => a.status === 'MENUNGGU_QC').length;

  const kpis = [
    { label: 'Line Aktif', value: lines.filter(l => l.active).length },
    { label: 'Operator', value: operators.length },
    { label: 'Tally Sesi Ini', value: tallies.length },
    { label: 'Menunggu QC', value: pendingQc },
  ];

  return (
    <div className="space-y-5">
      <div className="inline-flex gap-1 rounded-[12px] bg-[#f0f0f2] p-1">
        {([['terminal', 'Terminal Lantai'], ['admin', 'Admin']] as const).map(([id, label]) => (
          <button key={id} onClick={() => setMode(id)}
            className={`min-h-[40px] rounded-[9px] px-4 text-[13px] font-semibold transition-all ${mode === id ? 'bg-white text-[#1d1d1f] shadow-sm' : 'text-[#626269]'}`}>
            {label}
          </button>
        ))}
      </div>

      {mode === 'terminal' ? <FloorTerminalView /> : (
      <>
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">Produksi &amp; Tally 30 Menit</h2>
          <p className="text-[#6e6e73] text-sm mt-1">Line, operator, penugasan, output per 30 menit, dan staging assembly ke QC</p>
        </div>
        <button onClick={load} className="btn-secondary"><LucideIcon name="activity" className="w-4 h-4" /> Refresh</button>
      </div>

      {isMockOps && (
        <div className="rounded-[14px] border border-[#d5d5da] bg-[#f4f8fd] px-4 py-3 text-[12.5px] text-[#334155]">
          Mode mock aktif — data disimpan di memori. Set <code className="font-mono">VITE_LEDGER_MODE=live</code> untuk service asli.
        </div>
      )}
      {error && <div className="rounded-[14px] border border-[#fecaca] bg-[#fee2e2] px-4 py-3 text-[13px] text-[#dc2626]">{error}</div>}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map(({ label, value }) => (
          <div key={label} className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 text-center">
            <p className="text-xs text-[#6e6e73] uppercase tracking-wider mb-1">{label}</p>
            <p className="text-[30px] font-semibold text-[#1d1d1f]">{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white border border-[#e6e6e9] rounded-[18px] overflow-hidden">
        <div className="flex gap-1 p-3 border-b border-[#f0f0f2] overflow-x-auto">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`tab rounded-[9px] px-4 py-2 text-[13px] whitespace-nowrap transition-all ${
                tab === t.id ? 'bg-[#eaf3fe] text-[#0066cc] font-semibold' : 'text-[#626269] hover:bg-[#f5f5f7]'
              }`}>{t.label}</button>
          ))}
        </div>

        <div className="p-5">
          {/* Floor: lines & operators */}
          {tab === 'floor' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <div className="flex justify-between items-center mb-3">
                  <p className="text-[15px] font-semibold text-[#1d1d1f]">Line Produksi</p>
                  <button onClick={() => { setLineCode(''); setFormError(null); setShowLine(true); }} className="btn-secondary !py-1.5 !px-3 !text-xs">
                    <LucideIcon name="plus" className="w-3.5 h-3.5" /> Line
                  </button>
                </div>
                <table className="w-full text-[13px]">
                  <thead><tr>{['Kode', 'Status'].map(h => (
                    <th key={h} className="px-3 py-2 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2]">{h}</th>
                  ))}</tr></thead>
                  <tbody>
                    {lines.map(l => (
                      <tr key={l.id} className="border-b border-[#f0f0f2] last:border-0">
                        <td className="px-3 py-2.5 font-medium text-[#1d1d1f]">{l.lineCode}</td>
                        <td className="px-3 py-2.5">
                          <span className={`pill rounded-full px-2 py-0.5 text-[11px] font-semibold ${l.active ? 'bg-[#e8f5e9] text-[#1a7a34]' : 'bg-[#f0f0f2] text-[#626269]'}`}>
                            {l.active ? 'Aktif' : 'Nonaktif'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {lines.length === 0 && <p className="text-center text-[#6e6e73] py-6 text-[13px]">Belum ada line.</p>}
              </div>

              <div>
                <div className="flex justify-between items-center mb-3">
                  <p className="text-[15px] font-semibold text-[#1d1d1f]">Operator</p>
                  <button onClick={() => { setOpName(''); setOpCode(''); setFormError(null); setShowOperator(true); }} className="btn-secondary !py-1.5 !px-3 !text-xs">
                    <LucideIcon name="plus" className="w-3.5 h-3.5" /> Operator
                  </button>
                </div>
                <table className="w-full text-[13px]">
                  <thead><tr>{['Nama', 'Kode', 'Status'].map(h => (
                    <th key={h} className="px-3 py-2 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2]">{h}</th>
                  ))}</tr></thead>
                  <tbody>
                    {operators.map(o => (
                      <tr key={o.id} className="border-b border-[#f0f0f2] last:border-0">
                        <td className="px-3 py-2.5 font-medium text-[#1d1d1f]">{o.displayName}</td>
                        <td className="px-3 py-2.5 font-mono text-[#6e6e73]">{o.employeeCode}</td>
                        <td className="px-3 py-2.5">
                          <span className={`pill rounded-full px-2 py-0.5 text-[11px] font-semibold ${o.active ? 'bg-[#e8f5e9] text-[#1a7a34]' : 'bg-[#f0f0f2] text-[#626269]'}`}>
                            {o.active ? 'Aktif' : 'Nonaktif'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {operators.length === 0 && <p className="text-center text-[#6e6e73] py-6 text-[13px]">Belum ada operator.</p>}
              </div>
            </div>
          )}

          {/* Assignments */}
          {tab === 'assign' && (
            <>
              <div className="flex justify-between items-center mb-4">
                <p className="text-[15px] font-semibold text-[#1d1d1f]">Penugasan Operator ke Line</p>
                <button onClick={() => { setAssignDraft({ lineId: lines[0]?.id ?? '', operatorId: operators[0]?.id ?? '', componentCode: 'SLEEVE', validFrom: '', validThrough: '' }); setFormError(null); setShowAssign(true); }} className="btn-secondary !py-1.5 !px-3 !text-xs">
                  <LucideIcon name="plus" className="w-3.5 h-3.5" /> Assign
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px]">
                  <thead><tr>{['Line', 'Operator', 'Komponen', 'Berlaku'].map(h => (
                    <th key={h} className="px-3 py-2 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2]">{h}</th>
                  ))}</tr></thead>
                  <tbody>
                    {assignments.map(a => (
                      <tr key={a.id} className="border-b border-[#f0f0f2] last:border-0">
                        <td className="px-3 py-2.5 font-medium text-[#1d1d1f]">{lineName(a.lineId)}</td>
                        <td className="px-3 py-2.5 text-[#334155]">{operatorName(a.operatorId)}</td>
                        <td className="px-3 py-2.5 font-mono text-[#6e6e73]">{a.componentCode}</td>
                        <td className="px-3 py-2.5 text-[#6e6e73] text-xs">{a.validFrom} → {a.validThrough}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {assignments.length === 0 && <p className="text-center text-[#6e6e73] py-6 text-[13px]">Belum ada penugasan.</p>}
              </div>
            </>
          )}

          {/* Tally */}
          {tab === 'tally' && (
            <>
              <div className="flex justify-between items-center mb-4">
                <div>
                  <p className="text-[15px] font-semibold text-[#1d1d1f]">Tally Output 30 Menit</p>
                  <p className="text-xs text-[#6e6e73] mt-0.5">Satu tally = idempotency + alokasi komponen + snapshot rate + unit menunggu QC</p>
                </div>
                <button onClick={() => { const { start, end } = defaultInterval(); setTallyDraft(d => ({ ...d, lineId: lines[0]?.id ?? '', operatorId: operators[0]?.id ?? '', intervalStart: start, intervalEnd: end, pieces: 0 })); setFormError(null); setShowTally(true); }} className="btn-primary inline-flex items-center gap-2">
                  <LucideIcon name="plus" className="w-4 h-4" /> Catat Tally
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px]">
                  <thead><tr>{['Tally ID', 'Komponen', 'Line', 'Operator', 'Pieces', 'Status', 'Aksi'].map(h => (
                    <th key={h} className="px-3 py-2 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2]">{h}</th>
                  ))}</tr></thead>
                  <tbody>
                    {tallies.map(t => (
                      <tr key={t.result.tallyId} className="border-b border-[#f0f0f2] last:border-0">
                        <td className="px-3 py-2.5"><code className="text-xs text-[#64748b]">{t.result.tallyId.slice(0, 8)}</code></td>
                        <td className="px-3 py-2.5 font-mono text-[#6e6e73]">{t.input.componentCode}</td>
                        <td className="px-3 py-2.5 text-[#334155]">{lineName(t.input.lineId)}</td>
                        <td className="px-3 py-2.5 text-[#334155]">{operatorName(t.input.operatorId)}</td>
                        <td className="px-3 py-2.5 font-mono">{t.input.pieces}</td>
                        <td className="px-3 py-2.5">
                          <span className={`pill rounded-full px-2 py-0.5 text-[11px] font-semibold ${t.result.status === 'VERIFIED' ? 'bg-[#e8f5e9] text-[#1a7a34]' : 'bg-[#fff4e6] text-[#b86800]'}`}>
                            {t.result.status}
                          </span>
                        </td>
                        <td className="px-3 py-2.5">
                          <button disabled={t.result.status === 'VERIFIED'}
                            onClick={() => { setVerifyTarget(t); setVerifyReason(''); setFormError(null); }}
                            className="btn-secondary !py-1.5 !px-3 !text-xs disabled:opacity-40">Verifikasi</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {tallies.length === 0 && <p className="text-center text-[#6e6e73] py-6 text-[13px]">Belum ada tally pada sesi ini.</p>}
              </div>
            </>
          )}

          {/* Assemblies */}
          {tab === 'assembly' && (
            <>
              <div className="flex justify-between items-center mb-4">
                <p className="text-[15px] font-semibold text-[#1d1d1f]">Assembly &amp; Staging QC</p>
                <button onClick={() => { setAssemblyDraft({ orderId: '33333333-3333-4333-8333-333333333333', serialCode: '', componentUnitIds: '' }); setFormError(null); setShowAssembly(true); }} className="btn-secondary !py-1.5 !px-3 !text-xs">
                  <LucideIcon name="plus" className="w-3.5 h-3.5" /> Assembly
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px]">
                  <thead><tr>{['Serial', 'Order', 'Komponen', 'Status'].map(h => (
                    <th key={h} className="px-3 py-2 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2]">{h}</th>
                  ))}</tr></thead>
                  <tbody>
                    {assemblies.map(a => (
                      <tr key={a.id} className="border-b border-[#f0f0f2] last:border-0">
                        <td className="px-3 py-2.5 font-medium text-[#1d1d1f]">{a.serialCode}</td>
                        <td className="px-3 py-2.5"><code className="text-xs text-[#64748b]">{a.orderId.slice(0, 8)}</code></td>
                        <td className="px-3 py-2.5 font-mono text-[#6e6e73]">{a.componentUnitIds.length}</td>
                        <td className="px-3 py-2.5">
                          <span className={`pill rounded-full px-2 py-0.5 text-[11px] font-semibold ${STATUS_STYLE[a.status]}`}>{a.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {assemblies.length === 0 && <p className="text-center text-[#6e6e73] py-6 text-[13px]">Belum ada assembly.</p>}
              </div>
            </>
          )}

          {/* Progress */}
          {tab === 'progress' && (
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead><tr>{['Order', 'Komponen', 'Jumlah', 'Status'].map(h => (
                  <th key={h} className="px-3 py-2 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2]">{h}</th>
                ))}</tr></thead>
                <tbody>
                  {progress.map((p, i) => (
                    <tr key={i} className="border-b border-[#f0f0f2] last:border-0">
                      <td className="px-3 py-2.5"><code className="text-xs text-[#64748b]">{p.orderId.slice(0, 8)}</code></td>
                      <td className="px-3 py-2.5 font-mono text-[#6e6e73]">{p.componentCode}</td>
                      <td className="px-3 py-2.5 font-mono">{p.quantity.value} {p.quantity.unit}</td>
                      <td className="px-3 py-2.5">
                        <span className={`pill rounded-full px-2 py-0.5 text-[11px] font-semibold ${STATUS_STYLE[p.status]}`}>{p.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {progress.length === 0 && <p className="text-center text-[#6e6e73] py-6 text-[13px]">Belum ada progress.</p>}
            </div>
          )}
        </div>
      </div>

      {/* ── New line ─────────────────────────────────────────────────────────── */}
      <Modal isOpen={showLine} title="Tambah Line" onClose={() => setShowLine(false)}
        footer={<div className="flex gap-3 justify-end">
          <button onClick={() => setShowLine(false)} className="btn-secondary">Batal</button>
          <button onClick={() => run(() => createLine(lineCode), () => setShowLine(false))} disabled={busy} className="btn-primary">Simpan</button>
        </div>}>
        <div className="space-y-3">
          <label htmlFor="line-code" className="block text-sm font-medium text-[#1d1d1f]">Kode Line</label>
          <input id="line-code" value={lineCode} onChange={e => setLineCode(e.target.value)} placeholder="LINE-B" className={inputCls} />
          {formError && <p className="text-[13px] text-[#dc2626]">{formError}</p>}
        </div>
      </Modal>

      {/* ── New operator ─────────────────────────────────────────────────────── */}
      <Modal isOpen={showOperator} title="Tambah Operator" onClose={() => setShowOperator(false)}
        footer={<div className="flex gap-3 justify-end">
          <button onClick={() => setShowOperator(false)} className="btn-secondary">Batal</button>
          <button onClick={() => run(() => createOperator(opName, opCode), () => setShowOperator(false))} disabled={busy} className="btn-primary">Simpan</button>
        </div>}>
        <div className="space-y-3">
          <div><label htmlFor="op-name" className="block text-sm font-medium text-[#1d1d1f] mb-1">Nama</label>
            <input id="op-name" value={opName} onChange={e => setOpName(e.target.value)} className={inputCls} /></div>
          <div><label htmlFor="op-code" className="block text-sm font-medium text-[#1d1d1f] mb-1">Kode Karyawan</label>
            <input id="op-code" value={opCode} onChange={e => setOpCode(e.target.value)} placeholder="OPR-003" className={inputCls} /></div>
          {formError && <p className="text-[13px] text-[#dc2626]">{formError}</p>}
        </div>
      </Modal>

      {/* ── Assign operator ──────────────────────────────────────────────────── */}
      <Modal isOpen={showAssign} title="Assign Operator" onClose={() => setShowAssign(false)}
        footer={<div className="flex gap-3 justify-end">
          <button onClick={() => setShowAssign(false)} className="btn-secondary">Batal</button>
          <button onClick={() => run(() => assignOperator(assignDraft.lineId, {
            operatorId: assignDraft.operatorId, componentCode: assignDraft.componentCode,
            validFrom: assignDraft.validFrom || new Date().toISOString(),
            validThrough: assignDraft.validThrough || new Date(Date.now() + 8 * 3600e3).toISOString(),
          }), () => setShowAssign(false))} disabled={busy} className="btn-primary">Simpan</button>
        </div>}>
        <div className="space-y-3">
          <div><label htmlFor="as-line" className="block text-sm font-medium text-[#1d1d1f] mb-1">Line</label>
            <select id="as-line" value={assignDraft.lineId} onChange={e => setAssignDraft(d => ({ ...d, lineId: e.target.value }))} className={inputCls}>
              {lines.map(l => <option key={l.id} value={l.id}>{l.lineCode}</option>)}
            </select></div>
          <div><label htmlFor="as-op" className="block text-sm font-medium text-[#1d1d1f] mb-1">Operator</label>
            <select id="as-op" value={assignDraft.operatorId} onChange={e => setAssignDraft(d => ({ ...d, operatorId: e.target.value }))} className={inputCls}>
              {operators.map(o => <option key={o.id} value={o.id}>{o.displayName} ({o.employeeCode})</option>)}
            </select></div>
          <div><label htmlFor="as-comp" className="block text-sm font-medium text-[#1d1d1f] mb-1">Komponen</label>
            <input id="as-comp" value={assignDraft.componentCode} onChange={e => setAssignDraft(d => ({ ...d, componentCode: e.target.value }))} className={inputCls} /></div>
          {formError && <p className="text-[13px] text-[#dc2626]">{formError}</p>}
        </div>
      </Modal>

      {/* ── Record tally ─────────────────────────────────────────────────────── */}
      <Modal isOpen={showTally} title="Catat Tally 30 Menit" onClose={() => setShowTally(false)}
        footer={<div className="flex gap-3 justify-end">
          <button onClick={() => setShowTally(false)} className="btn-secondary">Batal</button>
          <button onClick={() => run(async () => {
            const res = await recordSewingTally({
              ...tallyDraft,
              intervalStart: new Date(tallyDraft.intervalStart).toISOString(),
              intervalEnd: new Date(tallyDraft.intervalEnd).toISOString(),
            });
            if (res.ok && res.data) setTallies(prev => [{ result: res.data!, input: tallyDraft }, ...prev]);
            return res;
          }, () => setShowTally(false))} disabled={busy} className="btn-primary">Simpan</button>
        </div>}>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label htmlFor="t-order" className="block text-sm font-medium text-[#1d1d1f] mb-1">Order ID</label>
              <input id="t-order" value={tallyDraft.orderId} onChange={e => setTallyDraft(d => ({ ...d, orderId: e.target.value }))} className={inputCls} /></div>
            <div><label htmlFor="t-batch" className="block text-sm font-medium text-[#1d1d1f] mb-1">Cut Batch ID</label>
              <input id="t-batch" value={tallyDraft.cutBatchId} onChange={e => setTallyDraft(d => ({ ...d, cutBatchId: e.target.value }))} className={inputCls} /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label htmlFor="t-line" className="block text-sm font-medium text-[#1d1d1f] mb-1">Line</label>
              <select id="t-line" value={tallyDraft.lineId} onChange={e => setTallyDraft(d => ({ ...d, lineId: e.target.value }))} className={inputCls}>
                {lines.map(l => <option key={l.id} value={l.id}>{l.lineCode}</option>)}
              </select></div>
            <div><label htmlFor="t-op" className="block text-sm font-medium text-[#1d1d1f] mb-1">Operator</label>
              <select id="t-op" value={tallyDraft.operatorId} onChange={e => setTallyDraft(d => ({ ...d, operatorId: e.target.value }))} className={inputCls}>
                {operators.map(o => <option key={o.id} value={o.id}>{o.displayName}</option>)}
              </select></div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label htmlFor="t-comp" className="block text-sm font-medium text-[#1d1d1f] mb-1">Komponen</label>
              <input id="t-comp" value={tallyDraft.componentCode} onChange={e => setTallyDraft(d => ({ ...d, componentCode: e.target.value }))} className={inputCls} /></div>
            <div><label htmlFor="t-start" className="block text-sm font-medium text-[#1d1d1f] mb-1">Mulai</label>
              <input id="t-start" type="datetime-local" value={tallyDraft.intervalStart} onChange={e => setTallyDraft(d => ({ ...d, intervalStart: e.target.value }))} className={inputCls} /></div>
            <div><label htmlFor="t-end" className="block text-sm font-medium text-[#1d1d1f] mb-1">Selesai</label>
              <input id="t-end" type="datetime-local" value={tallyDraft.intervalEnd} onChange={e => setTallyDraft(d => ({ ...d, intervalEnd: e.target.value }))} className={inputCls} /></div>
          </div>
          <div><label htmlFor="t-pieces" className="block text-sm font-medium text-[#1d1d1f] mb-1">Pieces</label>
            <input id="t-pieces" type="number" min={1} value={tallyDraft.pieces || ''} onChange={e => setTallyDraft(d => ({ ...d, pieces: parseInt(e.target.value) || 0 }))} className={inputCls} /></div>
          {formError && <p className="text-[13px] text-[#dc2626]">{formError}</p>}
        </div>
      </Modal>

      {/* ── New assembly ─────────────────────────────────────────────────────── */}
      <Modal isOpen={showAssembly} title="Buat Assembly" onClose={() => setShowAssembly(false)}
        footer={<div className="flex gap-3 justify-end">
          <button onClick={() => setShowAssembly(false)} className="btn-secondary">Batal</button>
          <button onClick={() => run(() => createAssembly({
            orderId: assemblyDraft.orderId,
            serialCode: assemblyDraft.serialCode,
            componentUnitIds: assemblyDraft.componentUnitIds.split(/[\s,]+/).map(s => s.trim()).filter(Boolean),
          }), () => setShowAssembly(false))} disabled={busy} className="btn-primary">Simpan</button>
        </div>}>
        <div className="space-y-3">
          <div><label htmlFor="a-order" className="block text-sm font-medium text-[#1d1d1f] mb-1">Order ID</label>
            <input id="a-order" value={assemblyDraft.orderId} onChange={e => setAssemblyDraft(d => ({ ...d, orderId: e.target.value }))} className={inputCls} /></div>
          <div><label htmlFor="a-serial" className="block text-sm font-medium text-[#1d1d1f] mb-1">Serial Code</label>
            <input id="a-serial" value={assemblyDraft.serialCode} onChange={e => setAssemblyDraft(d => ({ ...d, serialCode: e.target.value }))} placeholder="ASM-0002" className={inputCls} /></div>
          <div><label htmlFor="a-units" className="block text-sm font-medium text-[#1d1d1f] mb-1">Component Unit IDs (pisahkan spasi/koma)</label>
            <textarea id="a-units" rows={3} value={assemblyDraft.componentUnitIds} onChange={e => setAssemblyDraft(d => ({ ...d, componentUnitIds: e.target.value }))} className={inputCls} /></div>
          {formError && <p className="text-[13px] text-[#dc2626]">{formError}</p>}
        </div>
      </Modal>

      {/* ── Verify tally ─────────────────────────────────────────────────────── */}
      <Modal isOpen={verifyTarget !== null} title="Verifikasi Tally" onClose={() => setVerifyTarget(null)}
        footer={<div className="flex gap-3 justify-end">
          <button onClick={() => setVerifyTarget(null)} className="btn-secondary">Batal</button>
          <button onClick={() => run(async () => {
            const res = await verifySewingTally(verifyTarget!.result.tallyId, 'APPROVE', verifyReason);
            if (res.ok && res.data) setTallies(prev => prev.map(t => t.result.tallyId === res.data!.tallyId ? { ...t, result: res.data! } : t));
            return res;
          }, () => setVerifyTarget(null))} disabled={busy} className="btn-primary">Verifikasi</button>
        </div>}>
        <div className="space-y-3">
          <p className="text-[13px] text-[#334155]">Tally <code className="font-mono">{verifyTarget?.result.tallyId.slice(0, 8)}</code> · {verifyTarget?.input.pieces} pieces.</p>
          <div><label htmlFor="v-reason" className="block text-sm font-medium text-[#1d1d1f] mb-1">Catatan (opsional)</label>
            <input id="v-reason" value={verifyReason} onChange={e => setVerifyReason(e.target.value)} className={inputCls} /></div>
          {formError && <p className="text-[13px] text-[#dc2626]">{formError}</p>}
        </div>
      </Modal>
      </>
      )}
    </div>
  );
};

export default ProductionView;
