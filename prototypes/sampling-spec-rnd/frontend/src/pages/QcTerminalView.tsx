/**
 * QcTerminalView — VIEW-05 touch-first QC inspection terminal.
 *
 * Touch-optimized for factory floor inspectors:
 * - Garment serial code scanner & input field ('SN-401-XXXX') with barcode keyboard wedge support.
 * - Large touch buttons (min-h 72px): (A) PASS, (B) REPAIR, (C) SCRAP / REJECT.
 * - Defect taxonomy checklist (Broken Stitch, Puckering, Uneven Seam, Open Seam, Needle Hole, Oil Stain, etc.).
 * - Required defect validation on REPAIR / REJECT dispositions (prevent submit without selected defects).
 * - Real-time Defect Frequency Pareto Chart (80/20 rule) reflecting cumulative inspection history.
 * - Touch targets >= 48px for all interactive elements per Apple Design system tokens.
 *
 * Backed by services/opsApi.ts (mock by default; contract-shaped for live).
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { LucideIcon } from '../components/Sidebar';
import MockModeBanner from '../components/MockModeBanner';
import ParetoChart from '../components/ParetoChart';
import { buildPareto } from '../utils/chartData';
import {
  listAssemblies,
  inspectUnit,
  createAssembly,
  isMockOps,
  listMockInspections,
  type Assembly,
  type AssemblyStatus,
  type QcDisposition,
  type Defect,
  type QcInspection,
} from '../services/opsApi';

export const DEFECT_TAXONOMY = [
  'Broken Stitch',
  'Puckering',
  'Uneven Seam',
  'Open Seam',
  'Needle Hole',
  'Oil Stain',
  'Shading Mismatch',
  'Raw Edge',
] as const;

export type DefectTaxonomyItem = typeof DEFECT_TAXONOMY[number];

interface DispositionOption {
  value: QcDisposition;
  label: string;
  sublabel: string;
  badge: string;
  cls: string;
  activeCls: string;
}

const DISPOSITIONS: DispositionOption[] = [
  {
    value: 'PASS',
    label: '(A) PASS',
    sublabel: 'Lolos QC · Layak Masuk Payroll',
    badge: 'QC_PASS',
    cls: 'border-ok/40 text-ok-2 hover:bg-ok-bg/50',
    activeCls: 'bg-ok text-white border-ok shadow-md ring-2 ring-ok/30',
  },
  {
    value: 'REPAIR',
    label: '(B) REPAIR',
    sublabel: 'Rework Operator Asal · Tanpa Gaji Ganda',
    badge: 'REWORK',
    cls: 'border-warn/40 text-warn-2 hover:bg-warn-bg/50',
    activeCls: 'bg-warn text-white border-warn shadow-md ring-2 ring-warn/30',
  },
  {
    value: 'REJECT',
    label: '(C) SCRAP / REJECT',
    sublabel: 'Barang Cacat/Afkir · Dikeluarkan dari Batch',
    badge: 'REJECT_SCRAP',
    cls: 'border-bad/40 text-bad-4 hover:bg-bad-bg/50',
    activeCls: 'bg-bad text-white border-bad shadow-md ring-2 ring-bad/30',
  },
];

const STATUS_STYLE: Record<AssemblyStatus, string> = {
  MENUNGGU_QC: 'bg-warn-bg text-warn-2 border border-warn/30',
  QC_PASS: 'bg-ok-bg text-ok-2 border border-ok/30',
  REWORK: 'bg-brand-bg text-brand border border-brand/30',
  REJECT_SCRAP: 'bg-bad-bg text-bad-4 border border-bad/30',
};

function generateTempId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `unit-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

const QcTerminalView: React.FC = () => {
  const [assemblies, setAssemblies] = useState<Assembly[]>([]);
  const [inspections, setInspections] = useState<QcInspection[]>([]);
  const [selectedAssemblyId, setSelectedAssemblyId] = useState<string | null>(null);
  const [disposition, setDisposition] = useState<QcDisposition>('PASS');
  const [checkedDefects, setCheckedDefects] = useState<Record<string, boolean>>({});
  const [defectNotes, setDefectNotes] = useState<string>('');
  const [serialInput, setSerialInput] = useState<string>('');
  const [showPareto, setShowPareto] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(true);
  const [busy, setBusy] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

  const scanInputRef = useRef<HTMLInputElement>(null);

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

  // Queue of assemblies waiting for QC inspection
  const queue = assemblies.filter(a => a.status === 'MENUNGGU_QC');

  // Maintain active inspected unit
  const current = assemblies.find(a => a.id === selectedAssemblyId)
    ?? queue[0]
    ?? null;

  // Sync selected assembly ID when current changes
  useEffect(() => {
    if (current && (!selectedAssemblyId || !assemblies.some(a => a.id === selectedAssemblyId))) {
      setSelectedAssemblyId(current.id);
    }
  }, [current, selectedAssemblyId, assemblies]);

  const selectedDefectList = DEFECT_TAXONOMY.filter(t => !!checkedDefects[t]);

  const resetForm = () => {
    setDisposition('PASS');
    setCheckedDefects({});
    setDefectNotes('');
    setSerialInput('');
  };

  // Find currentIndex in queue
  const currentIndex = current ? queue.findIndex(a => a.id === current.id) : -1;

  const navigateQueue = (step: number) => {
    if (queue.length === 0) return;
    const nextIdx = (currentIndex + step + queue.length) % queue.length;
    setSelectedAssemblyId(queue[nextIdx].id);
    resetForm();
    setFlash(null);
  };

  // Serial code scanner & lookup handler
  const handleScanSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = serialInput.trim().toUpperCase();
    if (!query) return;

    setError(null);
    const existing = assemblies.find(
      a => a.serialCode.toUpperCase() === query || a.id.toUpperCase() === query
    );

    if (existing) {
      setSelectedAssemblyId(existing.id);
      resetForm();
      setFlash(`Unit serial ${existing.serialCode} berhasil dimuat.`);
      return;
    }

    // Auto-create/register unit on the fly if not yet in database
    setBusy(true);
    const orderId = query.startsWith('SN-402') ? 'ORD-402' : 'ORD-401';
    const createRes = await createAssembly({
      orderId,
      serialCode: query,
      componentUnitIds: [generateTempId(), generateTempId()],
    });
    setBusy(false);

    if (createRes.ok && createRes.data) {
      setFlash(`✓ Unit baru ${createRes.data.serialCode} berhasil didaftarkan dan dimuat ke terminal.`);
      resetForm();
      await load();
      setSelectedAssemblyId(createRes.data.id);
    } else {
      setError(createRes.error ?? `Gagal mendaftarkan unit ${query}.`);
    }
  };

  // Submit inspection with required defect validation on REPAIR/REJECT
  const submitInspection = async () => {
    if (!current) return;

    // Strict validation: REPAIR and REJECT require at least one defect
    if (disposition !== 'PASS' && selectedDefectList.length === 0) {
      setError('Disposisi REPAIR atau REJECT wajib memilih minimal satu defect dari taxonomy.');
      return;
    }

    setBusy(true);
    setError(null);

    const payloadDefects: Defect[] = disposition === 'PASS'
      ? []
      : selectedDefectList.map(code => ({
          componentUnitId: current.componentUnitIds[0] ?? generateTempId(),
          code,
          notes: defectNotes.trim() || undefined,
        }));

    const res = await inspectUnit({
      assemblyId: current.id,
      disposition,
      defects: payloadDefects,
    });

    setBusy(false);

    if (!res.ok) {
      setError(res.error ?? 'Gagal menyimpan hasil inspeksi.');
      return;
    }

    const nextFlash = `✓ ${current.serialCode} → Disposisi: ${disposition} ${
      disposition === 'PASS' ? '(Lolos QC)' : `(${selectedDefectList.length} defect)`
    }`;
    setFlash(nextFlash);
    resetForm();
    await load();

    // Re-focus scanner input for subsequent unit
    if (scanInputRef.current) {
      scanInputRef.current.focus();
    }
  };

  // Defect Pareto aggregation from inspections
  const defectCounts = new Map<string, number>();
  for (const insp of inspections) {
    for (const d of insp.defects ?? []) {
      const code = (d.code ?? '').trim();
      if (!code) continue;
      defectCounts.set(code, (defectCounts.get(code) ?? 0) + 1);
    }
  }

  const paretoData = buildPareto(
    [...defectCounts.entries()].map(([label, value]) => ({ label, value }))
  );

  const isDefectRequired = disposition !== 'PASS';
  const hasValidationViolation = isDefectRequired && selectedDefectList.length === 0;

  return (
    <div className="space-y-6">
      {isMockOps && (
        <MockModeBanner detail="Data inspeksi QC tersimpan di memori lokal stasiun." />
      )}

      {error && (
        <div
          role="alert"
          className="flex items-center gap-3 rounded-[16px] border border-bad-bg-2 bg-bad-bg px-5 py-4 text-[14px] font-medium text-bad-4 shadow-sm"
        >
          <LucideIcon name="x" className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {flash && (
        <div
          role="status"
          className="flex items-center justify-between rounded-[16px] border border-ok/40 bg-ok-bg px-5 py-4 text-[14px] font-medium text-ok-2 shadow-sm"
        >
          <div className="flex items-center gap-3">
            <LucideIcon name="check-circle" className="w-5 h-5 flex-shrink-0 text-ok" />
            <span>{flash}</span>
          </div>
          <button
            type="button"
            onClick={() => setFlash(null)}
            className="min-h-[48px] min-w-[48px] flex items-center justify-center rounded-lg hover:bg-ok/10 text-ok-2 text-xs"
            aria-label="Tutup notifikasi"
          >
            ✕
          </button>
        </div>
      )}

      {/* ── 1. Garment Serial Code Scanner / Input ────────────────────────── */}
      <div className="rounded-[18px] border border-hair bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div>
            <h2 className="text-[17px] font-semibold text-ink flex items-center gap-2">
              <LucideIcon name="search" className="w-5 h-5 text-brand" />
              Scanner Serial Garment
            </h2>
            <p className="text-[12px] text-ink-muted">
              Scan barcode fisik (contoh: <code className="font-mono font-medium text-ink">SN-401-0891</code>) atau masukkan kode serial manual.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowPareto(prev => !prev)}
              className="btn-secondary !min-h-[48px] px-3.5 text-[12px]"
              aria-expanded={showPareto}
            >
              <LucideIcon name="bar-chart-3" className="w-4 h-4 text-brand" />
              {showPareto ? 'Sembunyikan Pareto' : 'Lihat Pareto Defect'}
            </button>
            <button
              type="button"
              onClick={load}
              className="btn-secondary !min-h-[48px] px-3.5 text-[12px]"
              title="Refresh data dari server"
            >
              <LucideIcon name="activity" className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        <form onSubmit={handleScanSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <input
              ref={scanInputRef}
              type="text"
              value={serialInput}
              onChange={e => setSerialInput(e.target.value)}
              placeholder="Contoh: SN-401-0891 atau scan barcode..."
              className="w-full min-h-[48px] rounded-[12px] border border-hair-4 bg-page px-4 font-mono text-[15px] font-semibold tracking-wider text-ink focus:border-brand focus:bg-white focus:outline-none"
              aria-label="Kode serial garment"
            />
          </div>
          <button
            type="submit"
            disabled={busy || !serialInput.trim()}
            className="btn-primary !min-h-[48px] px-6 text-[14px] font-semibold shadow-sm disabled:opacity-40"
          >
            <LucideIcon name="search" className="w-4 h-4" />
            Cari / Scan Serial
          </button>
        </form>

        {/* Quick select chips for queue */}
        {queue.length > 0 && (
          <div className="mt-4 pt-3 border-t border-panel-2">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
                Pilih Cepat Antrian ({queue.length} Unit Menunggu):
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {queue.map(item => {
                const isSelected = current?.id === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setSelectedAssemblyId(item.id);
                      resetForm();
                      setFlash(null);
                    }}
                    className={`min-h-[48px] px-4 rounded-[12px] font-mono text-[13px] font-semibold transition-all flex items-center gap-2 border ${
                      isSelected
                        ? 'border-brand bg-brand text-white shadow-sm ring-2 ring-brand/30'
                        : 'border-hair bg-white text-ink hover:border-brand-soft hover:bg-page'
                    }`}
                  >
                    <span>{item.serialCode}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                        isSelected ? 'bg-white/20 text-white' : 'bg-panel-2 text-ink-muted'
                      }`}
                    >
                      {item.orderId.slice(0, 7)}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* ── 2. Active Garment Inspection Card ──────────────────────────────── */}
      {loading ? (
        <div className="rounded-[18px] border border-hair bg-white p-12 text-center text-ink-muted">
          <p className="text-[14px]">Memuat antrian garment...</p>
        </div>
      ) : !current ? (
        <div className="rounded-[18px] border border-dashed border-hair-4 bg-white p-12 text-center">
          <div className="w-12 h-12 mx-auto rounded-full bg-ok-bg text-ok flex items-center justify-center mb-3">
            <LucideIcon name="check-circle" className="w-6 h-6" />
          </div>
          <h3 className="text-[17px] font-semibold text-ink">Semua Unit Telah Diinspeksi</h3>
          <p className="text-[13px] text-ink-muted mt-1 max-w-md mx-auto">
            Tidak ada unit assembly yang menunggu QC saat ini. Scan serial code baru di atas atau buat batch baru di modul Produksi.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Garment Header Card */}
          <div className="rounded-[18px] border border-hair bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-brand">
                  Unit Garment Aktif
                </span>
                <div className="flex items-baseline gap-3 mt-1">
                  <h1 className="font-mono text-[28px] font-bold tracking-tight text-ink">
                    {current.serialCode}
                  </h1>
                  <span className={`pill rounded-full px-3 py-1 text-[11px] font-bold ${STATUS_STYLE[current.status]}`}>
                    {current.status}
                  </span>
                </div>
                <p className="text-[13px] text-ink-muted mt-1">
                  Order ID: <code className="font-mono font-medium text-ink">{current.orderId}</code> ·{' '}
                  Komponen Terpasang: <strong className="text-ink">{current.componentUnitIds.length} pcs</strong>
                </p>
              </div>

              {/* Prev / Next controls */}
              {queue.length > 1 && (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => navigateQueue(-1)}
                    className="btn-secondary !min-h-[48px] px-3.5 text-[13px] font-semibold"
                    title="Unit sebelumnya dalam antrian"
                    aria-label="Unit sebelumnya"
                  >
                    ← Sebelumnya
                  </button>
                  <span className="text-[12px] font-semibold font-mono text-ink-muted px-2">
                    {currentIndex >= 0 ? currentIndex + 1 : '—'} / {queue.length}
                  </span>
                  <button
                    type="button"
                    onClick={() => navigateQueue(1)}
                    className="btn-secondary !min-h-[48px] px-3.5 text-[13px] font-semibold"
                    title="Unit berikutnya dalam antrian"
                    aria-label="Unit berikutnya"
                  >
                    Berikutnya →
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* ── 3. Large Touch Buttons: (A) PASS, (B) REPAIR, (C) REJECT ─── */}
          <div className="rounded-[18px] border border-hair bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-[17px] font-semibold text-ink">Pilih Disposisi QC</h3>
                <p className="text-[12px] text-ink-muted">
                  Tekan salah satu hasil inspeksi untuk unit <span className="font-mono font-bold text-ink">{current.serialCode}</span>.
                </p>
              </div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-faint">
                Touch Targets ≥ 72px
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {DISPOSITIONS.map(d => {
                const isSelected = disposition === d.value;
                return (
                  <button
                    key={d.value}
                    type="button"
                    onClick={() => {
                      setDisposition(d.value);
                      setError(null);
                    }}
                    aria-pressed={isSelected}
                    className={`min-h-[76px] rounded-[16px] border-2 p-4 text-left transition-all active:scale-[0.98] flex flex-col justify-between ${
                      isSelected ? d.activeCls : `bg-white ${d.cls}`
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[18px] font-bold tracking-tight">
                        {d.label}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                          isSelected ? 'bg-white/25 text-white' : 'bg-panel text-ink-2'
                        }`}
                      >
                        {d.badge}
                      </span>
                    </div>
                    <span
                      className={`text-[12px] font-medium mt-2 leading-tight ${
                        isSelected ? 'text-white/90' : 'text-ink-muted'
                      }`}
                    >
                      {d.sublabel}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ── 4. Defect Taxonomy Checklist (Shown for REPAIR/REJECT) ─────── */}
          {isDefectRequired && (
            <div className="rounded-[18px] border border-hair bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-[17px] font-semibold text-ink">
                      Defect Taxonomy Checklist
                    </h3>
                    <span className="rounded-full bg-bad-bg px-2.5 py-0.5 text-[11px] font-bold text-bad-4">
                      Wajib Diisi untuk {disposition}
                    </span>
                  </div>
                  <p className="text-[12px] text-ink-muted mt-0.5">
                    Pilih minimal 1 jenis cacat yang ditemukan pada garment.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      const all: Record<string, boolean> = {};
                      DEFECT_TAXONOMY.forEach(t => { all[t] = true; });
                      setCheckedDefects(all);
                      setError(null);
                    }}
                    className="min-h-[48px] px-3 rounded-[10px] text-[12px] font-semibold text-brand hover:bg-brand-bg transition-colors"
                  >
                    Pilih Semua
                  </button>
                  <button
                    type="button"
                    onClick={() => setCheckedDefects({})}
                    className="min-h-[48px] px-3 rounded-[10px] text-[12px] font-semibold text-ink-muted hover:bg-page transition-colors"
                  >
                    Bersihkan
                  </button>
                </div>
              </div>

              {hasValidationViolation && (
                <div className="mb-4 rounded-[12px] border border-warn/40 bg-warn-bg px-4 py-3 text-[13px] text-warn-2 font-medium flex items-center gap-2">
                  <span>⚠️</span>
                  <span>
                    Validasi Wajib: Disposisi <strong>{disposition}</strong> memerlukan minimal satu defect yang dipilih dari checklist di bawah.
                  </span>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {DEFECT_TAXONOMY.map(t => {
                  const isChecked = !!checkedDefects[t];
                  return (
                    <label
                      key={t}
                      className={`flex min-h-[52px] cursor-pointer items-center gap-3 rounded-[14px] border-2 px-4 py-2.5 text-[14px] transition-all select-none active:scale-[0.99] ${
                        isChecked
                          ? 'border-brand bg-brand-bg text-brand shadow-xs font-semibold'
                          : 'border-hair bg-white text-ink hover:border-hair-4 hover:bg-page'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={e => {
                          setCheckedDefects(prev => ({ ...prev, [t]: e.target.checked }));
                          setError(null);
                        }}
                        className="w-5 h-5 rounded accent-brand cursor-pointer"
                      />
                      <span className="flex-1 leading-snug">{t}</span>
                    </label>
                  );
                })}
              </div>

              {/* Optional Defect Note */}
              <div className="mt-4 pt-3 border-t border-panel-2">
                <label className="block text-[12px] font-semibold text-ink-muted mb-1.5">
                  Catatan Tambahan QC (Opsional):
                </label>
                <input
                  type="text"
                  value={defectNotes}
                  onChange={e => setDefectNotes(e.target.value)}
                  placeholder="Misal: Bagian ketiak kanan, toleransi lewat 3mm..."
                  className="w-full min-h-[48px] rounded-[10px] border border-hair-4 bg-page px-3 text-[13px] text-ink focus:border-brand focus:bg-white focus:outline-none"
                />
              </div>
            </div>
          )}

          {/* ── 5. Submit Inspection Button ───────────────────────────────── */}
          <div className="pt-2">
            <button
              type="button"
              onClick={submitInspection}
              disabled={busy || hasValidationViolation}
              className={`w-full min-h-[56px] rounded-[16px] text-white text-[16px] font-bold tracking-wide transition-all active:scale-[0.99] shadow-md flex items-center justify-center gap-2 ${
                hasValidationViolation
                  ? 'bg-hair-4 text-ink-faint cursor-not-allowed opacity-50'
                  : disposition === 'PASS'
                  ? 'bg-ok hover:bg-ok-2'
                  : disposition === 'REPAIR'
                  ? 'bg-warn hover:bg-warn-2'
                  : 'bg-bad hover:bg-bad-4'
              }`}
            >
              {busy ? (
                <span>Menyimpan ke Ledger &amp; Riwayat...</span>
              ) : disposition === 'PASS' ? (
                <>
                  <LucideIcon name="check-circle" className="w-5 h-5" />
                  SIMPAN INSPEKSI: (A) PASS → QC_PASS
                </>
              ) : disposition === 'REPAIR' ? (
                <>
                  <LucideIcon name="activity" className="w-5 h-5" />
                  SIMPAN INSPEKSI: (B) REPAIR → REWORK ({selectedDefectList.length} Defect Dipilih)
                </>
              ) : (
                <>
                  <LucideIcon name="x" className="w-5 h-5" />
                  SIMPAN INSPEKSI: (C) REJECT → REJECT_SCRAP ({selectedDefectList.length} Defect Dipilih)
                </>
              )}
            </button>
            {hasValidationViolation && (
              <p className="text-center text-[12px] text-bad-4 font-medium mt-2">
                Pilih minimal satu cacat pada checklist taxonomy di atas untuk mengaktifkan tombol simpan.
              </p>
            )}
          </div>
        </div>
      )}

      {/* ── 6. Defect Frequency Pareto Chart ──────────────────────────────── */}
      {showPareto && (
        <div className="pt-2">
          <ParetoChart
            data={paretoData}
            title="Pareto Frekuensi Cacat QC (80/20 Rule)"
            subtitle="Distribusi kode defect paling sering dari riwayat inspeksi stasiun"
            unit="cacat"
          />
        </div>
      )}
    </div>
  );
};

export default QcTerminalView;
