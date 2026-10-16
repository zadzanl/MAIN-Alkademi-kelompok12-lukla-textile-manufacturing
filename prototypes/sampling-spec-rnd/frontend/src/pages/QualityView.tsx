/**
 * QualityView — VIEW-05: QC queue, defect routing, and analytics.
 *
 * Classifies assemblies Pass / Repair / Reject through inspectUnit
 * (services/opsApi.ts, mock by default). Routing per the contract:
 *   PASS   -> QC_PASS     (eligible for payroll)
 *   REPAIR -> REWORK      (original operator, no double pay)
 *   REJECT -> REJECT_SCRAP
 *
 * Includes:
 * - Touch-optimized mode toggle (Terminal QC vs. Antrian & Riwayat).
 * - Real-time Pareto chart of defect frequency (80/20 rule).
 * - Defect taxonomy support with required defect validation on REPAIR/REJECT.
 * - Garment serial code lookup/filter field ('SN-401-XXXX').
 * - Touch targets >= 48px on all interactive controls.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LucideIcon } from '../components/Sidebar';
import Modal from '../components/Modal';
import MockModeBanner from '../components/MockModeBanner';
import {
  listAssemblies,
  inspectUnit,
  isMockOps,
  listMockInspections,
  type Assembly,
  type AssemblyStatus,
  type QcDisposition,
  type Defect,
  type QcInspection,
} from '../services/opsApi';
import { buildPareto } from '../utils/chartData';
import ParetoChart from '../components/ParetoChart';
import QcTerminalView, { DEFECT_TAXONOMY } from './QcTerminalView';

const inputCls = 'w-full min-h-[48px] rounded-[10px] border border-hair-4 bg-page px-3 text-[13px] text-ink focus:border-brand focus:bg-white focus:outline-none';

const STATUS_STYLE: Record<AssemblyStatus, string> = {
  MENUNGGU_QC: 'bg-warn-bg text-warn-2 border border-warn/30',
  QC_PASS: 'bg-ok-bg text-ok-2 border border-ok/30',
  REWORK: 'bg-brand-bg text-brand border border-brand/30',
  REJECT_SCRAP: 'bg-bad-bg text-bad-4 border border-bad/30',
};

const DISPOSITIONS: { value: QcDisposition; label: string; route: string }[] = [
  { value: 'PASS', label: '(A) PASS', route: '→ QC_PASS (layak payroll)' },
  { value: 'REPAIR', label: '(B) REPAIR', route: '→ REWORK (operator asal, tanpa gaji ganda)' },
  { value: 'REJECT', label: '(C) SCRAP / REJECT', route: '→ REJECT_SCRAP (afkir unit)' },
];

const FILTERS: { id: 'ALL' | AssemblyStatus; label: string }[] = [
  { id: 'ALL', label: 'Semua Status' },
  { id: 'MENUNGGU_QC', label: 'Menunggu QC' },
  { id: 'REWORK', label: 'Repair (Rework)' },
  { id: 'QC_PASS', label: 'QC Pass' },
  { id: 'REJECT_SCRAP', label: 'Scrap / Reject' },
];

interface DefectRow {
  componentUnitId: string;
  code: string;
  notes: string;
}

const emptyDefect = (unitId = ''): DefectRow => ({
  componentUnitId: unitId,
  code: '',
  notes: '',
});

const QualityView: React.FC = () => {
  const [mode, setMode] = useState<'terminal' | 'queue'>('terminal');
  const [assemblies, setAssemblies] = useState<Assembly[]>([]);
  const [inspections, setInspections] = useState<QcInspection[]>([]);
  const [filter, setFilter] = useState<'ALL' | AssemblyStatus>('MENUNGGU_QC');
  const [searchSerial, setSearchSerial] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Modal inspection states
  const [target, setTarget] = useState<Assembly | null>(null);
  const [disposition, setDisposition] = useState<QcDisposition>('PASS');
  const [defects, setDefects] = useState<DefectRow[]>([emptyDefect()]);
  const [busy, setBusy] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await listAssemblies();
    if (res.ok && res.data) {
      setAssemblies(res.data.items);
    } else {
      setError(res.error ?? 'Gagal memuat daftar assembly.');
    }
    setInspections(listMockInspections());
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Filtered assemblies
  const visible = useMemo(() => {
    let list = filter === 'ALL' ? assemblies : assemblies.filter(a => a.status === filter);
    if (searchSerial.trim()) {
      const q = searchSerial.trim().toUpperCase();
      list = list.filter(
        a => a.serialCode.toUpperCase().includes(q) || a.orderId.toUpperCase().includes(q)
      );
    }
    return list;
  }, [assemblies, filter, searchSerial]);

  // Pareto aggregation of defect frequencies across recorded inspections
  const defectCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const insp of inspections) {
      for (const d of insp.defects ?? []) {
        const code = (d.code ?? '').trim();
        if (!code) continue;
        counts.set(code, (counts.get(code) ?? 0) + 1);
      }
    }
    return counts;
  }, [inspections]);

  const paretoData = useMemo(() => {
    return buildPareto(
      [...defectCounts.entries()].map(([label, value]) => ({ label, value }))
    );
  }, [defectCounts]);

  const openInspect = (a: Assembly) => {
    setTarget(a);
    setDisposition('PASS');
    setDefects([emptyDefect(a.componentUnitIds[0] ?? '')]);
    setFormError(null);
  };

  const submitModalInspection = async () => {
    if (!target) return;

    // Filter valid defect rows
    const payload: Defect[] = defects
      .filter(d => d.componentUnitId.trim() || d.code.trim())
      .map(d => ({
        componentUnitId: d.componentUnitId.trim(),
        code: d.code.trim(),
        notes: d.notes.trim() || undefined,
      }));

    // Required defect validation on REPAIR / REJECT
    if (disposition !== 'PASS' && payload.length === 0) {
      setFormError('Disposisi REPAIR atau REJECT wajib menyertakan minimal satu defect.');
      return;
    }

    setBusy(true);
    setFormError(null);

    const res = await inspectUnit({
      assemblyId: target.id,
      disposition,
      defects: disposition === 'PASS' ? [] : payload,
    });

    setBusy(false);
    if (!res.ok) {
      setFormError(res.error ?? 'Gagal menyimpan inspeksi.');
      return;
    }

    setTarget(null);
    await load();
  };

  const updateDefect = (idx: number, patch: Partial<DefectRow>) => {
    setDefects(prev => prev.map((d, i) => (i === idx ? { ...d, ...patch } : d)));
  };

  const count = (s: AssemblyStatus) => assemblies.filter(a => a.status === s).length;

  return (
    <div className="space-y-6">
      {/* ── Mode Navigation Bar (Terminal QC vs Antrian & Riwayat) ──────── */}
      <div className="inline-flex gap-1.5 rounded-[14px] bg-panel-2 p-1.5 shadow-xs">
        {([['terminal', 'Terminal QC (Touch)'], ['queue', 'Antrian & Riwayat (Tabel & Pareto)']] as const).map(
          ([id, label]) => (
            <button
              key={id}
              onClick={() => setMode(id)}
              className={`min-h-[48px] rounded-[11px] px-5 text-[14px] font-semibold transition-all ${
                mode === id
                  ? 'bg-white text-ink shadow-sm'
                  : 'text-ink-muted hover:text-ink'
              }`}
            >
              {label}
            </button>
          )
        )}
      </div>

      {mode === 'terminal' ? (
        <QcTerminalView />
      ) : (
        <>
          {/* Header */}
          <div className="flex flex-wrap justify-between items-center gap-3">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-ink">
                Quality Control &amp; Routing
              </h2>
              <p className="text-ink-muted text-sm mt-1">
                Inspeksi assembly: Pass / Repair / Reject — status menentukan rute tindakan &amp; eligibility payroll berikutnya
              </p>
            </div>
            <button onClick={load} className="btn-secondary !min-h-[48px] px-4 font-semibold">
              <LucideIcon name="activity" className="w-4 h-4" /> Refresh
            </button>
          </div>

          {isMockOps && <MockModeBanner detail="Data inspeksi disimpan di memori lokal stasiun." />}

          {error && (
            <div
              role="alert"
              className="rounded-[16px] border border-bad-bg-2 bg-bad-bg px-5 py-4 text-[13px] text-bad-4 font-medium"
            >
              {error}
            </div>
          )}

          {/* Metric Summary Strip */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Menunggu QC', value: count('MENUNGGU_QC'), cls: 'text-warn-2', bg: 'bg-warn-bg' },
              { label: 'Pass (QC_PASS)', value: count('QC_PASS'), cls: 'text-ok-2', bg: 'bg-ok-bg' },
              { label: 'Repair (REWORK)', value: count('REWORK'), cls: 'text-brand', bg: 'bg-brand-bg' },
              { label: 'Reject (SCRAP)', value: count('REJECT_SCRAP'), cls: 'text-bad-4', bg: 'bg-bad-bg' },
            ].map(({ label, value, cls, bg }) => (
              <div key={label} className="bg-white border border-hair rounded-[18px] p-5 text-center shadow-xs">
                <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider mb-2 ${bg} ${cls}`}>
                  {label}
                </span>
                <p className={`text-[32px] font-bold tracking-tight ${cls}`}>{value}</p>
              </div>
            ))}
          </div>

          {/* Pareto Chart */}
          <ParetoChart
            data={paretoData}
            title="Pareto Frekuensi Cacat QC (80/20 Rule)"
            subtitle="Kode defect paling sering — 20% penyebab menghasilkan 80% total cacat garmen"
            unit="cacat"
          />

          {/* Filter, Search & Assembly Table */}
          <div className="bg-white border border-hair rounded-[18px] overflow-hidden shadow-xs">
            {/* Filter Tabs & Search */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 p-4 border-b border-panel-2">
              <div className="flex gap-1.5 overflow-x-auto pb-1 lg:pb-0">
                {FILTERS.map(f => (
                  <button
                    key={f.id}
                    onClick={() => setFilter(f.id)}
                    className={`min-h-[48px] rounded-[11px] px-4 text-[13px] font-semibold whitespace-nowrap transition-all ${
                      filter === f.id
                        ? 'bg-brand text-white shadow-xs'
                        : 'text-ink-muted hover:bg-page hover:text-ink'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>

              {/* Garment Serial Code Search Input */}
              <div className="relative w-full lg:w-72">
                <input
                  type="text"
                  value={searchSerial}
                  onChange={e => setSearchSerial(e.target.value)}
                  placeholder="Cari Serial ('SN-401-XXXX')..."
                  className="w-full min-h-[48px] rounded-[11px] border border-hair-4 bg-page px-3.5 text-[13px] font-mono font-medium text-ink focus:border-brand focus:bg-white focus:outline-none"
                  aria-label="Cari serial garment"
                />
                {searchSerial && (
                  <button
                    type="button"
                    onClick={() => setSearchSerial('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-ink-muted hover:text-ink"
                    aria-label="Hapus pencarian"
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>

            {/* Table Content */}
            <div className="p-5">
              {loading ? (
                <p className="text-center text-ink-muted py-8 text-[13px]">Memuat data assembly…</p>
              ) : visible.length === 0 ? (
                <div className="text-center py-10">
                  <p className="text-ink-muted text-[13px]">
                    {searchSerial ? `Tidak ditemukan assembly dengan kata kunci "${searchSerial}".` : 'Tidak ada assembly pada filter ini.'}
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-[13px]">
                    <thead>
                      <tr>
                        {['Serial Code', 'Order ID', 'Komponen', 'Status Saat Ini', 'Aksi QC'].map(h => (
                          <th
                            key={h}
                            className="px-4 py-3 text-left text-[11px] font-bold text-ink-muted uppercase tracking-wider bg-panel border-b border-panel-2 whitespace-nowrap"
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {visible.map(a => (
                        <tr key={a.id} className="border-b border-panel-2 last:border-0 hover:bg-page/50 transition-colors">
                          <td className="px-4 py-3 font-mono font-semibold text-ink text-[14px]">
                            {a.serialCode}
                          </td>
                          <td className="px-4 py-3">
                            <code className="text-xs font-mono text-ink-muted">{a.orderId}</code>
                          </td>
                          <td className="px-4 py-3 font-mono text-ink-2">
                            {a.componentUnitIds.length} pcs
                          </td>
                          <td className="px-4 py-3">
                            <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-bold ${STATUS_STYLE[a.status]}`}>
                              {a.status}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <button
                              onClick={() => openInspect(a)}
                              className="btn-secondary !min-h-[48px] px-4 text-[13px] font-semibold"
                            >
                              <LucideIcon name="activity" className="w-4 h-4 text-brand" />
                              Inspeksi Unit
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* ── Inspect Modal ──────────────────────────────────────────────── */}
          <Modal
            isOpen={target !== null}
            title="Inspeksi Garment Assembly"
            onClose={() => setTarget(null)}
            footer={
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setTarget(null)}
                  className="btn-secondary !min-h-[48px] px-5"
                >
                  Batal
                </button>
                <button
                  type="button"
                  onClick={submitModalInspection}
                  disabled={busy}
                  className="btn-primary !min-h-[48px] px-6 font-semibold"
                >
                  {busy ? 'Menyimpan…' : 'Simpan Inspeksi'}
                </button>
              </div>
            }
          >
            <div className="space-y-4">
              <div className="rounded-[12px] bg-panel-2 p-3 text-[13px] text-ink-2">
                <p>
                  Unit Serial: <strong className="font-mono text-ink text-[14px]">{target?.serialCode}</strong> · Order:{' '}
                  <code className="font-mono">{target?.orderId}</code> · {target?.componentUnitIds.length} komponen
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink mb-2">
                  Pilih Disposisi QC
                </label>
                <div className="space-y-2">
                  {DISPOSITIONS.map(d => (
                    <label
                      key={d.value}
                      className={`flex min-h-[48px] items-center gap-3 rounded-[12px] border-2 px-3.5 py-2.5 cursor-pointer text-[13px] transition-all ${
                        disposition === d.value
                          ? 'border-brand bg-brand-bg text-brand font-semibold'
                          : 'border-hair bg-white text-ink hover:bg-page'
                      }`}
                    >
                      <input
                        type="radio"
                        name="disposition"
                        value={d.value}
                        checked={disposition === d.value}
                        onChange={() => {
                          setDisposition(d.value);
                          setFormError(null);
                        }}
                        className="w-4 h-4 accent-brand cursor-pointer"
                      />
                      <span className="font-bold">{d.label}</span>
                      <span className="text-ink-muted text-xs ml-auto">{d.route}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Defect section for REPAIR / REJECT */}
              {disposition !== 'PASS' && (
                <div className="pt-2 border-t border-panel-2">
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <span className="text-sm font-semibold text-ink">
                        Defect Terdeteksi (Wajib Diisi)
                      </span>
                      <p className="text-[11px] text-ink-muted">
                        Pilih kode defect dari taxonomy standar
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setDefects(prev => [...prev, emptyDefect(target?.componentUnitIds[0] ?? '')])}
                      className="btn-secondary !min-h-[48px] px-3 text-xs font-semibold"
                    >
                      + Tambah Baris
                    </button>
                  </div>

                  {/* Taxonomy quick chips */}
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {DEFECT_TAXONOMY.map(tax => (
                      <button
                        key={tax}
                        type="button"
                        onClick={() => {
                          setDefects(prev => {
                            // If first row has empty code, fill it
                            if (prev.length === 1 && !prev[0].code) {
                              return [{ ...prev[0], code: tax }];
                            }
                            // Otherwise append
                            return [...prev, { componentUnitId: target?.componentUnitIds[0] ?? '', code: tax, notes: '' }];
                          });
                          setFormError(null);
                        }}
                        className="min-h-[36px] px-2.5 rounded-lg border border-hair text-[11px] font-semibold text-ink bg-page hover:bg-white hover:border-brand transition-colors"
                      >
                        + {tax}
                      </button>
                    ))}
                  </div>

                  <div className="space-y-2">
                    {defects.map((d, idx) => (
                      <div key={idx} className="flex gap-2 items-center">
                        <input
                          value={d.componentUnitId}
                          onChange={e => updateDefect(idx, { componentUnitId: e.target.value })}
                          list="unit-ids"
                          placeholder="Component Unit ID"
                          aria-label="Component Unit ID"
                          className={inputCls + ' flex-1'}
                        />
                        <input
                          value={d.code}
                          onChange={e => updateDefect(idx, { code: e.target.value })}
                          list="defect-taxonomy-list"
                          placeholder="Kode defect (misal: Broken Stitch)"
                          aria-label="Kode defect"
                          className={inputCls + ' flex-1'}
                        />
                        <button
                          type="button"
                          onClick={() => setDefects(prev => prev.filter((_, i) => i !== idx))}
                          disabled={defects.length <= 1}
                          aria-label="Hapus baris defect"
                          className="min-w-[48px] min-h-[48px] rounded-[10px] border border-hair text-bad-4 flex items-center justify-center hover:bg-bad-bg disabled:opacity-30"
                        >
                          <LucideIcon name="x" className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Datalists */}
                  <datalist id="defect-taxonomy-list">
                    {DEFECT_TAXONOMY.map(t => (
                      <option key={t} value={t} />
                    ))}
                  </datalist>

                  {target && target.componentUnitIds.length > 0 && (
                    <datalist id="unit-ids">
                      {target.componentUnitIds.map(u => (
                        <option key={u} value={u} />
                      ))}
                    </datalist>
                  )}
                </div>
              )}

              {formError && (
                <div className="rounded-[10px] bg-bad-bg border border-bad-bg-2 p-3 text-[13px] text-bad-4 font-medium">
                  {formError}
                </div>
              )}
            </div>
          </Modal>
        </>
      )}
    </div>
  );
};

export default QualityView;
