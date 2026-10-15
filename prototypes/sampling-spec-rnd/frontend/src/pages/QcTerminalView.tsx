/**
 * QcTerminalView — VIEW-05 touch-first QC inspection terminal.
 *
 * One garment unit, one disposition. Large PASS / REPAIR / REJECT buttons plus a
 * defect taxonomy checklist (shown for REPAIR / REJECT), submitted through
 * inspectUnit (services/opsApi.ts, mock by default; contract-shaped for live).
 *
 * Mirrors prototypes/design-mocks/lukla-ui-mock.html (view-05).
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import MockModeBanner from '../components/MockModeBanner';
import {
  listAssemblies, inspectUnit, isMockOps,
  type Assembly, type AssemblyStatus, type QcDisposition, type Defect,
} from '../services/opsApi';

const TAXONOMY = ['Broken Stitch', 'Puckering', 'Uneven Seam'] as const;

const DISPOSITIONS: { value: QcDisposition; label: string; cls: string; active: string }[] = [
  { value: 'PASS',   label: '(A) PASS',           cls: 'border-ok text-ok-2', active: 'bg-ok text-white border-ok' },
  { value: 'REPAIR', label: '(B) REPAIR',         cls: 'border-warn text-warn-2', active: 'bg-warn text-white border-warn' },
  { value: 'REJECT', label: '(C) SCRAP / REJECT', cls: 'border-bad text-bad-4', active: 'bg-bad text-white border-bad' },
];

const STATUS_STYLE: Record<AssemblyStatus, string> = {
  MENUNGGU_QC: 'bg-warn-bg text-warn-2',
  QC_PASS: 'bg-ok-bg text-ok-2',
  REWORK: 'bg-brand-bg text-brand',
  REJECT_SCRAP: 'bg-bad-bg text-bad-4',
};

const QcTerminalView: React.FC = () => {
  const [assemblies, setAssemblies] = useState<Assembly[]>([]);
  const [disposition, setDisposition] = useState<QcDisposition>('PASS');
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await listAssemblies();
    if (res.ok && res.data) setAssemblies(res.data.items);
    else setError(res.error ?? 'Gagal memuat daftar assembly.');
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const queue = assemblies.filter(a => a.status === 'MENUNGGU_QC');
  const current = queue[0] ?? null;
  const selectedDefects = TAXONOMY.filter(t => checked[t]);

  const reset = () => { setDisposition('PASS'); setChecked({}); setFlash(null); };

  const submit = async () => {
    if (!current) return;
    setBusy(true);
    setError(null);
    const defects: Defect[] = disposition === 'PASS'
      ? []
      : selectedDefects.map(code => ({ componentUnitId: current.componentUnitIds[0] ?? '', code }));
    const res = await inspectUnit({ assemblyId: current.id, disposition, defects });
    setBusy(false);
    if (!res.ok) { setError(res.error ?? 'Gagal menyimpan inspeksi.'); return; }
    setFlash(`✓ ${current.serialCode} → ${disposition}`);
    reset();
    await load();
  };

  return (
    <div className="space-y-5">
      {isMockOps && <MockModeBanner detail="data inspeksi disimpan di memori." />}
      {error && <div className="rounded-[14px] border border-bad-bg-2 bg-bad-bg px-4 py-3 text-[13px] text-bad-4">{error}</div>}
      {flash && <div className="rounded-[14px] border border-ok bg-ok-bg px-4 py-3 text-[13px] font-medium text-ok-2">{flash}</div>}

      {/* Context bar */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 rounded-[16px] border border-hair bg-white px-5 py-4">
        <span className="text-[13px] text-ink-muted">
          <span className="font-medium">Antrian QC:</span> {queue.length} unit
        </span>
        {current ? (
          <>
            <span className="text-[13px] text-ink-muted">
              <span className="font-medium">Order:</span> <code className="font-mono">{current.orderId.slice(0, 8)}</code>
            </span>
            <span className="text-[13px] text-ink-muted">
              <span className="font-medium">Serial:</span> <code className="font-mono">{current.serialCode}</code>
            </span>
            <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-semibold ${STATUS_STYLE[current.status]}`}>
              {current.status}
            </span>
          </>
        ) : (
          <span className="text-[13px] text-ink-muted">Tidak ada unit menunggu QC.</span>
        )}
        <button onClick={load} className="btn-secondary ml-auto">
          <LucideIcon name="activity" className="w-4 h-4" /> Refresh
        </button>
      </div>

      {loading ? (
        <p className="py-10 text-center text-[13px] text-ink-muted">Memuat…</p>
      ) : !current ? (
        <div className="rounded-[18px] border border-dashed border-hair-4 bg-white px-6 py-12 text-center text-[13px] text-ink-muted">
          Semua unit sudah diinspeksi. Buat assembly baru di tab <strong>Produksi &amp; Tally</strong>.
        </div>
      ) : (
        <>
          {/* Disposition */}
          <div className="rounded-[18px] border border-hair bg-white p-5">
            <p className="text-[15px] font-semibold text-ink">Disposition</p>
            <p className="mb-4 text-[12px] text-ink-muted">Pilih hasil inspeksi untuk unit ini.</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {DISPOSITIONS.map(d => (
                <button key={d.value} type="button" onClick={() => setDisposition(d.value)}
                  aria-pressed={disposition === d.value}
                  className={`min-h-[64px] rounded-[14px] border-2 text-[15px] font-semibold transition-transform active:scale-[0.98] ${
                    disposition === d.value ? d.active : `bg-white ${d.cls}`
                  }`}>
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          {/* Defect taxonomy */}
          {disposition !== 'PASS' && (
            <div className="rounded-[18px] border border-hair bg-white p-5">
              <p className="text-[15px] font-semibold text-ink">Defect taxonomy</p>
              <p className="mb-4 text-[12px] text-ink-muted">Pilih semua temuan yang sesuai.</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {TAXONOMY.map(t => (
                  <label key={t}
                    className={`flex min-h-[56px] cursor-pointer items-center gap-3 rounded-[12px] border px-4 text-[14px] ${
                      checked[t] ? 'border-brand bg-brand-bg' : 'border-hair'
                    }`}>
                    <input type="checkbox" checked={!!checked[t]}
                      onChange={e => setChecked(prev => ({ ...prev, [t]: e.target.checked }))} />
                    <span className="font-medium text-ink">{t}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <button type="button" onClick={submit}
            disabled={busy || (disposition !== 'PASS' && selectedDefects.length === 0)}
            className="w-full min-h-[56px] rounded-[14px] bg-brand text-white text-[15px] font-semibold tracking-wide transition-transform active:scale-[0.99] disabled:opacity-40">
            {busy ? 'Menyimpan…' : 'SIMPAN INSPEKSI'}
          </button>
        </>
      )}
    </div>
  );
};

export default QcTerminalView;
