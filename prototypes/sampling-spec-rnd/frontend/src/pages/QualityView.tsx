/**
 * QualityView — VIEW-05: QC queue and defect routing.
 *
 * Classifies assemblies Pass / Repair / Reject through inspectUnit
 * (services/opsApi.ts, mock by default). Routing per the contract:
 *   PASS   -> QC_PASS     (eligible for payroll)
 *   REPAIR -> REWORK      (original operator, no double pay)
 *   REJECT -> REJECT_SCRAP
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import Modal from '../components/Modal';
import MockModeBanner from '../components/MockModeBanner';
import {
  listAssemblies, inspectUnit, isMockOps, listMockInspections,
  type Assembly, type AssemblyStatus, type QcDisposition, type Defect, type QcInspection,
} from '../services/opsApi';
import { buildPareto } from '../utils/chartData';
import ParetoChart from '../components/ParetoChart';
import QcTerminalView from './QcTerminalView';

const inputCls = 'w-full rounded-[10px] px-3 py-2.5 text-[13px]';

const STATUS_STYLE: Record<AssemblyStatus, string> = {
  MENUNGGU_QC: 'bg-[#fff4e6] text-[#b86800]',
  QC_PASS: 'bg-[#e8f5e9] text-[#1a7a34]',
  REWORK: 'bg-[#e8f2ff] text-[#0066cc]',
  REJECT_SCRAP: 'bg-[#ffebee] text-[#dc2626]',
};

const DISPOSITIONS: { value: QcDisposition; label: string; route: string }[] = [
  { value: 'PASS', label: 'Pass', route: '→ QC_PASS (layak payroll)' },
  { value: 'REPAIR', label: 'Repair', route: '→ REWORK (operator asal, tanpa gaji ganda)' },
  { value: 'REJECT', label: 'Reject', route: '→ REJECT_SCRAP' },
];

const FILTERS: { id: 'ALL' | AssemblyStatus; label: string }[] = [
  { id: 'ALL', label: 'Semua' },
  { id: 'MENUNGGU_QC', label: 'Menunggu QC' },
  { id: 'REWORK', label: 'Repair' },
  { id: 'QC_PASS', label: 'Pass' },
  { id: 'REJECT_SCRAP', label: 'Reject' },
];

interface DefectRow { componentUnitId: string; code: string; notes: string; }
const emptyDefect = (unitId = ''): DefectRow => ({ componentUnitId: unitId, code: '', notes: '' });

const QualityView: React.FC = () => {
  const [mode, setMode] = useState<'terminal' | 'queue'>('terminal');
  const [assemblies, setAssemblies] = useState<Assembly[]>([]);
  const [inspections, setInspections] = useState<QcInspection[]>([]);
  const [filter, setFilter] = useState<'ALL' | AssemblyStatus>('MENUNGGU_QC');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [target, setTarget] = useState<Assembly | null>(null);
  const [disposition, setDisposition] = useState<QcDisposition>('PASS');
  const [defects, setDefects] = useState<DefectRow[]>([emptyDefect()]);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await listAssemblies();
    if (res.ok && res.data) setAssemblies(res.data.items);
    else setError(res.error ?? 'Gagal memuat daftar assembly.');
    setInspections(listMockInspections());
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const visible = filter === 'ALL' ? assemblies : assemblies.filter(a => a.status === filter);

  // Pareto of defect codes across recorded inspections. Source is mock-only
  // (listMockInspections) — in live mode it is empty until a GET list endpoint
  // exists, so the chart degrades to its empty state rather than erroring.
  const defectCounts = new Map<string, number>();
  for (const insp of inspections) {
    for (const d of insp.defects ?? []) {
      const code = (d.code ?? '').trim();
      if (!code) continue;
      defectCounts.set(code, (defectCounts.get(code) ?? 0) + 1);
    }
  }
  const paretoData = buildPareto(
    [...defectCounts.entries()].map(([label, value]) => ({ label, value })),
  );

  const openInspect = (a: Assembly) => {
    setTarget(a);
    setDisposition('PASS');
    setDefects([emptyDefect(a.componentUnitIds[0] ?? '')]);
    setFormError(null);
  };

  const submit = async () => {
    if (!target) return;
    setBusy(true);
    setFormError(null);
    const payload: Defect[] = defects
      .filter(d => d.componentUnitId.trim() || d.code.trim())
      .map(d => ({ componentUnitId: d.componentUnitId.trim(), code: d.code.trim(), notes: d.notes.trim() || undefined }));
    const res = await inspectUnit({ assemblyId: target.id, disposition, defects: payload });
    setBusy(false);
    if (!res.ok) { setFormError(res.error ?? 'Gagal menyimpan inspeksi.'); return; }
    setTarget(null);
    await load();
  };

  const updateDefect = (idx: number, patch: Partial<DefectRow>) =>
    setDefects(prev => prev.map((d, i) => (i === idx ? { ...d, ...patch } : d)));

  const count = (s: AssemblyStatus) => assemblies.filter(a => a.status === s).length;

  return (
    <div className="space-y-5">
      <div className="inline-flex gap-1 rounded-[12px] bg-[#f0f0f2] p-1">
        {([['terminal', 'Terminal QC'], ['queue', 'Antrian & Riwayat']] as const).map(([id, label]) => (
          <button key={id} onClick={() => setMode(id)}
            className={`min-h-[40px] rounded-[9px] px-4 text-[13px] font-semibold transition-all ${mode === id ? 'bg-white text-[#1d1d1f] shadow-sm' : 'text-[#626269]'}`}>
            {label}
          </button>
        ))}
      </div>

      {mode === 'terminal' ? <QcTerminalView /> : (
      <>
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">Quality Control &amp; Routing</h2>
          <p className="text-[#6e6e73] text-sm mt-1">Inspeksi assembly: Pass / Repair / Reject — status menentukan rute tindakan berikutnya</p>
        </div>
        <button onClick={load} className="btn-secondary"><LucideIcon name="activity" className="w-4 h-4" /> Refresh</button>
      </div>

      {isMockOps && <MockModeBanner detail="data inspeksi disimpan di memori." />}
      {error && <div className="rounded-[14px] border border-[#fecaca] bg-[#fee2e2] px-4 py-3 text-[13px] text-[#dc2626]">{error}</div>}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Menunggu QC', value: count('MENUNGGU_QC'), cls: 'text-[#b86800]' },
          { label: 'Pass', value: count('QC_PASS'), cls: 'text-[#1a7a34]' },
          { label: 'Repair', value: count('REWORK'), cls: 'text-[#0066cc]' },
          { label: 'Reject', value: count('REJECT_SCRAP'), cls: 'text-[#dc2626]' },
        ].map(({ label, value, cls }) => (
          <div key={label} className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 text-center">
            <p className="text-xs text-[#6e6e73] uppercase tracking-wider mb-1">{label}</p>
            <p className={`text-[30px] font-semibold ${cls}`}>{value}</p>
          </div>
        ))}
      </div>

      <ParetoChart
        data={paretoData}
        title="Pareto Defect QC"
        subtitle="Kode defect paling sering — 20% penyebab mayoritas temuan"
        unit="cacat"
      />

      <div className="bg-white border border-[#e6e6e9] rounded-[18px] overflow-hidden">
        <div className="flex gap-1 p-3 border-b border-[#f0f0f2] overflow-x-auto">
          {FILTERS.map(f => (
            <button key={f.id} onClick={() => setFilter(f.id)}
              className={`tab rounded-[9px] px-4 py-2 text-[13px] whitespace-nowrap transition-all ${
                filter === f.id ? 'bg-[#eaf3fe] text-[#0066cc] font-semibold' : 'text-[#626269] hover:bg-[#f5f5f7]'
              }`}>{f.label}</button>
          ))}
        </div>

        <div className="p-5">
          {loading ? (
            <p className="text-center text-[#6e6e73] py-6 text-[13px]">Memuat…</p>
          ) : visible.length === 0 ? (
            <p className="text-center text-[#6e6e73] py-6 text-[13px]">Tidak ada assembly pada filter ini.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead><tr>{['Serial', 'Order', 'Komponen', 'Status', 'Aksi'].map(h => (
                  <th key={h} className="px-3 py-2 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2] whitespace-nowrap">{h}</th>
                ))}</tr></thead>
                <tbody>
                  {visible.map(a => (
                    <tr key={a.id} className="border-b border-[#f0f0f2] last:border-0">
                      <td className="px-3 py-2.5 font-medium text-[#1d1d1f]">{a.serialCode}</td>
                      <td className="px-3 py-2.5"><code className="text-xs text-[#64748b]">{a.orderId.slice(0, 8)}</code></td>
                      <td className="px-3 py-2.5 font-mono text-[#6e6e73]">{a.componentUnitIds.length}</td>
                      <td className="px-3 py-2.5">
                        <span className={`pill rounded-full px-2 py-0.5 text-[11px] font-semibold ${STATUS_STYLE[a.status]}`}>{a.status}</span>
                      </td>
                      <td className="px-3 py-2.5">
                        <button onClick={() => openInspect(a)} className="btn-secondary !py-1.5 !px-3 !text-xs">Inspeksi</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* ── Inspect modal ────────────────────────────────────────────────────── */}
      <Modal isOpen={target !== null} title="Inspeksi Unit" onClose={() => setTarget(null)}
        footer={<div className="flex gap-3 justify-end">
          <button onClick={() => setTarget(null)} className="btn-secondary">Batal</button>
          <button onClick={submit} disabled={busy} className="btn-primary">{busy ? 'Menyimpan…' : 'Simpan'}</button>
        </div>}>
        <div className="space-y-4">
          <p className="text-[13px] text-[#334155]">
            Assembly <code className="font-mono">{target?.serialCode}</code> · {target?.componentUnitIds.length} unit komponen
          </p>

          <div>
            <span className="block text-sm font-medium text-[#1d1d1f] mb-2">Disposisi</span>
            <div className="space-y-2">
              {DISPOSITIONS.map(d => (
                <label key={d.value} className={`flex items-center gap-3 rounded-[10px] border px-3 py-2.5 cursor-pointer text-[13px] ${
                  disposition === d.value ? 'border-[#0071e3] bg-[#eaf3fe]' : 'border-[#e6e6e9]'
                }`}>
                  <input type="radio" name="disposition" value={d.value} checked={disposition === d.value}
                    onChange={() => setDisposition(d.value)} />
                  <span className="font-semibold text-[#1d1d1f]">{d.label}</span>
                  <span className="text-[#6e6e73]">{d.route}</span>
                </label>
              ))}
            </div>
          </div>

          {disposition !== 'PASS' && (
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-[#1d1d1f]">Defect</span>
                <button onClick={() => setDefects(prev => [...prev, emptyDefect(target?.componentUnitIds[0] ?? '')])}
                  className="btn-ghost !py-1 !px-2 !text-xs">+ Tambah</button>
              </div>
              <div className="space-y-2">
                {defects.map((d, idx) => (
                  <div key={idx} className="flex gap-2 items-center">
                    <input value={d.componentUnitId} onChange={e => updateDefect(idx, { componentUnitId: e.target.value })}
                      list="unit-ids" placeholder="Component Unit ID" aria-label="Component Unit ID" className={inputCls + ' flex-1'} />
                    <input value={d.code} onChange={e => updateDefect(idx, { code: e.target.value })}
                      placeholder="Kode defect" aria-label="Kode defect" className={inputCls + ' w-[130px]'} />
                    <button onClick={() => setDefects(prev => prev.filter((_, i) => i !== idx))}
                      disabled={defects.length <= 1} aria-label="Hapus defect"
                      className="btn-ghost !p-2 disabled:opacity-30">
                      <LucideIcon name="x" className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
              {target && target.componentUnitIds.length > 0 && (
                <datalist id="unit-ids">
                  {target.componentUnitIds.map(u => <option key={u} value={u} />)}
                </datalist>
              )}
              <p className="text-[11px] text-[#6e6e73] mt-1">Unit ID mengacu ke komponen assembly; pilih dari daftar atau isi manual.</p>
            </div>
          )}

          {formError && <p className="text-[13px] text-[#dc2626]">{formError}</p>}
        </div>
      </Modal>
      </>
      )}
    </div>
  );
};

export default QualityView;
