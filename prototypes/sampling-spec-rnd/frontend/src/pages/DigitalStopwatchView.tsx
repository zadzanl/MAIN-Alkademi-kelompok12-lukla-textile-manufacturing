/**
 * DigitalStopwatchView — Digital Stopwatch for Time Study per Component
 * PRD: Stopwatch digital untuk mengukur durasi pengerjaan standar per komponen jahitan.
 * Data time study digunakan sebagai acuan rate card (ongkos jahit/potong).
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import type { TimeStudy } from '../types';
import * as api from '../services/api';
import { toast } from '../services/toast';
import { TENANT_ID } from '../services/identity';

// ─── helpers ──────────────────────────────────────────────────────────────────

const fmtMs = (ms: number): string => {
  const totalSec = Math.floor(ms / 1000);
  const mins     = Math.floor(totalSec / 60);
  const secs     = totalSec % 60;
  const centis   = Math.floor((ms % 1000) / 10);
  return `${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}.${String(centis).padStart(2,'0')}`;
};

const rateCardFromMs = (meanMs: number, allowancePct: number = 15): number => {
  // Simple rate card: (mean_time_sec / 60) × rate_per_minute_idr
  // Using IDR 500/min as floor rate for garment finishing
  const RATE_PER_MIN_IDR = 500;
  const allowanceFactor  = 1 + allowancePct / 100;
  const stdTimeMin       = (meanMs / 1000 / 60) * allowanceFactor;
  return Math.round(stdTimeMin * RATE_PER_MIN_IDR);
};

interface LapRecord {
  id: number;
  element_name: string;
  cycle_time_ms: number;
  is_abnormal: boolean;
  notes: string;
  timestamp: string;
}

// ─── component ────────────────────────────────────────────────────────────────

const DigitalStopwatchView: React.FC = () => {
  // Stopwatch state
  const [running, setRunning]           = useState(false);
  const [elapsed, setElapsed]           = useState(0);         // ms
  const [startTime, setStartTime]       = useState<number>(0);
  const [laps, setLaps]                 = useState<LapRecord[]>([]);
  const [lapCounter, setLapCounter]     = useState(1);
  const intervalRef                     = useRef<number | null>(null);

  // Form state
  const [elementName, setElementName]   = useState('');
  const [lapNote, setLapNote]           = useState('');
  const [isAbnormal, setIsAbnormal]     = useState(false);
  const [allowancePct, setAllowancePct] = useState(15);

  // Study binding
  const [studies, setStudies]           = useState<TimeStudy[]>([]);
  const [selectedStudyId, setSelectedStudyId] = useState('');
  const [saving, setSaving]             = useState(false);
  const [saveMsg, setSaveMsg]           = useState('');

  // Create new study inline
  const [showNewStudy, setShowNewStudy] = useState(false);
  const [newStudyForm, setNewStudyForm] = useState({
    process_id: '', process_name: '', operator_id: 'OPR-001', target_sample_size: 30,
  });

  // ── fetch studies ────────────────────────────────────────────────────────────

  const fetchStudies = useCallback(async () => {
    try {
      const res = await api.listStudies(TENANT_ID);
      if (res.success && res.data) setStudies(res.data);
    } catch { /* offline */ }
  }, []);

  useEffect(() => { fetchStudies(); }, [fetchStudies]);

  // ── stopwatch tick ──────────────────────────────────────────────────────────

  useEffect(() => {
    if (running) {
      intervalRef.current = window.setInterval(() => {
        setElapsed(Date.now() - startTime);
      }, 10);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [running, startTime]);

  // ── controls ────────────────────────────────────────────────────────────────

  const handleStart = () => {
    setStartTime(Date.now() - elapsed);
    setRunning(true);
  };
  const handlePause = () => setRunning(false);
  const handleReset = () => { setRunning(false); setElapsed(0); };

  const handleLap = () => {
    if (!running && elapsed === 0) return;
    const lap: LapRecord = {
      id:             lapCounter,
      element_name:   elementName || `Komponen ${lapCounter}`,
      cycle_time_ms:  elapsed,
      is_abnormal:    isAbnormal,
      notes:          lapNote,
      timestamp:      new Date().toISOString(),
    };
    setLaps(prev => [...prev, lap]);
    setLapCounter(c => c + 1);
    // auto-reset for next cycle
    setElapsed(0);
    setStartTime(Date.now());
    setLapNote('');
    setIsAbnormal(false);
  };

  const removeLap = (id: number) => setLaps(prev => prev.filter(l => l.id !== id));

  // ── stats ────────────────────────────────────────────────────────────────────

  const normalLaps  = laps.filter(l => !l.is_abnormal);
  const meanMs      = normalLaps.length ? normalLaps.reduce((s,l) => s + l.cycle_time_ms, 0) / normalLaps.length : 0;
  const minMs       = normalLaps.length ? Math.min(...normalLaps.map(l => l.cycle_time_ms)) : 0;
  const maxMs       = normalLaps.length ? Math.max(...normalLaps.map(l => l.cycle_time_ms)) : 0;
  const stdDev      = normalLaps.length > 1
    ? Math.sqrt(normalLaps.reduce((s,l) => s + Math.pow(l.cycle_time_ms - meanMs, 2), 0) / (normalLaps.length - 1))
    : 0;
  const cv          = meanMs > 0 ? (stdDev / meanMs) * 100 : 0;
  const rateCard    = rateCardFromMs(meanMs, allowancePct);

  // ── save to backend ──────────────────────────────────────────────────────────

  const handleSaveToStudy = async () => {
    if (!selectedStudyId) { toast.error('Pilih studi waktu terlebih dahulu.'); return; }
    if (laps.length === 0) { toast.error('Belum ada lap yang direkam.'); return; }
    setSaving(true); setSaveMsg('');
    let successCount = 0;
    // 1. start the study if still draft
    const study = studies.find(s => s.study_id === selectedStudyId);
    if (study?.status === 'draft') {
      await api.startStudy(selectedStudyId);
    }
    // 2. push each lap as a sample
    for (const lap of laps) {
      const res = await api.addSample({
        study_id: selectedStudyId,
        cycle_time_ms: lap.cycle_time_ms,
        element_name: lap.element_name,
        is_abnormal: lap.is_abnormal,
        notes: lap.notes,
      });
      if (res.success) successCount++;
    }
    setSaveMsg(`${successCount}/${laps.length} sampel tersimpan ke studi.`);
    setSaving(false);
    fetchStudies();
  };

  const handleCreateStudy = async () => {
    const { process_id, process_name, operator_id, target_sample_size } = newStudyForm;
    if (!process_id || !process_name) { toast.error('Process ID dan Nama Proses wajib diisi.'); return; }
    const res = await api.createStudy({
      tenant_id: TENANT_ID, process_id, process_name, operator_id, target_sample_size,
    });
    if (res.success && res.data) {
      setSelectedStudyId(res.data.study_id);
      setShowNewStudy(false);
      fetchStudies();
    } else { toast.error(res.error ?? 'Gagal membuat studi.'); }
  };

  // ─────────────────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold text-ink">Stopwatch Digital</h2>
        <p className="text-ink-muted text-sm mt-1">Ukur waktu standar per komponen jahitan → acuan rate card</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

        {/* ── Left: stopwatch + controls ────────────────────────────────── */}
        <div className="xl:col-span-1 space-y-4">

          {/* Clock face */}
          <div className="bg-white border border-hair rounded-[18px] p-6 text-center">
            <p className="text-xs font-semibold text-ink-muted uppercase tracking-wider mb-3">Waktu Berjalan</p>
            <div className={`font-mono text-[52px] font-semibold tracking-tight leading-none mb-1 transition-colors ${
              running ? 'text-brand' : elapsed > 0 ? 'text-warn' : 'text-ink'
            }`}>
              {fmtMs(elapsed)}
            </div>
            <p className="text-xs text-ink-muted">mm:ss.cs</p>

            {/* Buttons */}
            <div className="flex gap-3 justify-center mt-5">
              {!running ? (
                <button onClick={handleStart}
                  className="bg-ok text-white rounded-full w-14 h-14 text-2xl font-bold shadow-md hover:bg-ok transition-colors"
                  aria-label="Mulai">▶</button>
              ) : (
                <button onClick={handlePause}
                  className="bg-warn text-white rounded-full w-14 h-14 text-2xl font-bold shadow-md hover:bg-warn-2 transition-colors"
                  aria-label="Pause">⏸</button>
              )}
              <button onClick={handleLap} disabled={!running && elapsed === 0}
                className="bg-brand text-white rounded-full w-14 h-14 text-sm font-bold shadow-md hover:bg-brand transition-colors disabled:opacity-40"
                aria-label="Lap">LAP</button>
              <button onClick={handleReset}
                className="bg-page border border-hair text-ink-muted rounded-full w-14 h-14 text-xl font-bold hover:bg-hair transition-colors"
                aria-label="Reset">↺</button>
            </div>
          </div>

          {/* Lap metadata */}
          <div className="bg-white border border-hair rounded-[18px] p-5 space-y-3">
            <p className="text-sm font-semibold text-ink">Detail Komponen Saat Ini</p>
            <div>
              <label className="block text-xs text-ink-muted mb-1">Nama Komponen</label>
              <input value={elementName} onChange={e => setElementName(e.target.value)} aria-label="Nama Komponen"
                placeholder="e.g. Pasang Kerah, Jahit Lengan Kiri…"
                className="w-full border border-hair-2 rounded-[10px] px-3 py-2 text-[13px] focus:outline-2 focus:outline-brand-soft" />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">Catatan</label>
              <input value={lapNote} onChange={e => setLapNote(e.target.value)} aria-label="Catatan"
                placeholder="Kondisi abnormal, mesin macet, dst."
                className="w-full border border-hair-2 rounded-[10px] px-3 py-2 text-[13px] focus:outline-2 focus:outline-brand-soft" />
            </div>
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input type="checkbox" checked={isAbnormal} onChange={e => setIsAbnormal(e.target.checked)}
                className="w-4 h-4 rounded" />
              <span className="text-[13px] text-bad font-medium">Tandai sebagai Abnormal</span>
            </label>
            <div>
              <label className="block text-xs text-ink-muted mb-1">Allowance (%)</label>
              <input type="number" min={0} max={50} value={allowancePct} aria-label="Allowance (%)"
                onChange={e => setAllowancePct(parseInt(e.target.value)||0)}
                className="w-24 border border-hair-2 rounded-[10px] px-3 py-2 text-[13px] focus:outline-2 focus:outline-brand-soft" />
            </div>
          </div>

          {/* Stats summary */}
          <div className="bg-white border border-hair rounded-[18px] p-5 space-y-3">
            <p className="text-sm font-semibold text-ink">Statistik Real-time</p>
            {[
              { label: 'Jumlah Lap (Normal)',  value: `${normalLaps.length} / ${laps.length}` },
              { label: 'Rata-rata (ms)',        value: meanMs > 0 ? Math.round(meanMs).toLocaleString('id-ID') : '—' },
              { label: 'Min / Max (ms)',        value: minMs > 0 ? `${Math.round(minMs).toLocaleString('id-ID')} / ${Math.round(maxMs).toLocaleString('id-ID')}` : '—' },
              { label: 'Std. Dev (ms)',         value: stdDev > 0 ? Math.round(stdDev).toLocaleString('id-ID') : '—' },
              { label: 'CV (%)',                value: cv > 0 ? `${cv.toFixed(1)}%` : '—' },
              { label: `Rate Card (IDR) +${allowancePct}%`, value: rateCard > 0 ? `Rp ${rateCard.toLocaleString('id-ID')}/pcs` : '—', highlight: true },
            ].map(({ label, value, highlight }) => (
              <div key={label} className="flex justify-between text-[13px]">
                <span className="text-ink-muted">{label}</span>
                <span className={`font-semibold ${highlight ? 'text-brand' : 'text-ink'}`}>{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Right: lap list + save ─────────────────────────────────────── */}
        <div className="xl:col-span-2 space-y-4">

          {/* Lap table */}
          <div className="bg-white border border-hair rounded-[18px] overflow-hidden">
            <div className="px-5 py-4 border-b border-panel-2 flex justify-between items-center">
              <div>
                <h3 className="text-[15px] font-semibold text-ink">Rekaman Lap</h3>
                <p className="text-xs text-ink-muted mt-0.5">{laps.length} lap dicatat</p>
              </div>
              {laps.length > 0 && (
                <button onClick={() => { setLaps([]); setLapCounter(1); }}
                  className="text-xs text-bad font-semibold hover:underline">
                  Hapus Semua
                </button>
              )}
            </div>
            {laps.length === 0 ? (
              <div className="px-5 py-10 text-center text-ink-muted text-sm">
                Tekan <strong>LAP</strong> setelah stopwatch berjalan untuk merekam siklus.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-[13px] border-collapse">
                  <thead>
                    <tr>
                      {['#','Komponen','Waktu (ms)','Waktu','Status','Catatan',''].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-[11px] font-medium text-ink-muted uppercase tracking-wider bg-panel border-b border-panel-2 whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {laps.map((lap, idx) => {
                      const isAbove = meanMs > 0 && lap.cycle_time_ms > meanMs * 1.3;
                      return (
                        <tr key={lap.id} className="border-b border-panel-2 last:border-0">
                          <td className="px-4 py-3 text-ink-muted">{idx + 1}</td>
                          <td className="px-4 py-3 font-medium text-ink">{lap.element_name}</td>
                          <td className={`px-4 py-3 font-mono font-semibold ${lap.is_abnormal ? 'text-bad' : isAbove ? 'text-warn' : 'text-ok'}`}>
                            {Math.round(lap.cycle_time_ms).toLocaleString('id-ID')}
                          </td>
                          <td className="px-4 py-3 font-mono text-ink-muted">{fmtMs(lap.cycle_time_ms)}</td>
                          <td className="px-4 py-3">
                            {lap.is_abnormal ? (
                              <span className="pill bg-bad-bg text-bad rounded-full px-2 py-1 text-[11px] font-semibold">Abnormal</span>
                            ) : (
                              <span className="pill bg-ok-bg text-ok rounded-full px-2 py-1 text-[11px] font-semibold">Normal</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-ink-muted max-w-[120px] truncate">{lap.notes || '—'}</td>
                          <td className="px-4 py-3">
                            <button onClick={() => removeLap(lap.id)} aria-label="Hapus lap"
                              className="text-bad hover:text-bad-4 font-bold">×</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Save to backend */}
          <div className="bg-white border border-hair rounded-[18px] p-5">
            <p className="text-[15px] font-semibold text-ink mb-4">Simpan ke Studi Waktu</p>
            <div className="flex flex-col sm:flex-row gap-3">
              <select value={selectedStudyId} onChange={e => setSelectedStudyId(e.target.value)} aria-label="Pilih Studi Waktu"
                className="flex-1 border border-hair-2 rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-brand-soft">
                <option value="">— Pilih Studi Waktu —</option>
                {studies.filter(s => s.status !== 'completed' && s.status !== 'archived').map(s => (
                  <option key={s.study_id} value={s.study_id}>
                    {s.process_name} [{s.status}] — {s.total_cycles ?? 0}/{s.target_sample_size} sampel
                  </option>
                ))}
              </select>
              <button onClick={() => setShowNewStudy(v => !v)}
                className="btn-secondary">
                + Studi Baru
              </button>
            </div>

            {showNewStudy && (
              <div className="mt-4 p-4 bg-page rounded-[12px] space-y-3">
                <p className="text-xs font-semibold text-ink-muted uppercase tracking-wider">Buat Studi Baru</p>
                <div className="grid grid-cols-2 gap-3">
                  {([
                    { id: 'process_id',   label: 'ID Proses', ph: 'PROC-001' },
                    { id: 'process_name', label: 'Nama Proses', ph: 'Pasang Kerah' },
                    { id: 'operator_id',  label: 'ID Operator', ph: 'OPR-001' },
                  ] as { id: 'process_id' | 'process_name' | 'operator_id'; label: string; ph: string }[]).map(({ id, label, ph }) => (
                    <div key={id} className={id === 'process_name' ? 'col-span-2' : ''}>
                      <label className="block text-xs text-ink-muted mb-1">{label}</label>
                      <input value={newStudyForm[id]} placeholder={ph} aria-label={label}
                        onChange={e => setNewStudyForm(f => ({ ...f, [id]: e.target.value }))}
                        className="w-full border border-hair-2 rounded-[10px] px-3 py-2 text-[13px] bg-white focus:outline-2 focus:outline-brand-soft" />
                    </div>
                  ))}
                  <div>
                    <label className="block text-xs text-ink-muted mb-1">Target Sampel</label>
                    <input type="number" value={newStudyForm.target_sample_size} aria-label="Target Sampel"
                      onChange={e => setNewStudyForm(f => ({ ...f, target_sample_size: parseInt(e.target.value)||30 }))}
                      className="w-full border border-hair-2 rounded-[10px] px-3 py-2 text-[13px] bg-white focus:outline-2 focus:outline-brand-soft" />
                  </div>
                </div>
                <button onClick={handleCreateStudy}
                  className="btn-primary !py-2">
                  Buat & Pilih
                </button>
              </div>
            )}

            {saveMsg && (
              <div className="mt-3 bg-ok-bg border border-ok rounded-[10px] px-4 py-2.5 text-[13px] text-ok-2 font-medium">
                ✓ {saveMsg}
              </div>
            )}

            <div className="flex gap-3 mt-4">
              <button onClick={handleSaveToStudy} disabled={saving || laps.length === 0}
                className="btn-primary">
                {saving ? 'Menyimpan…' : <><LucideIcon name="download" className="w-4 h-4" /> Simpan {laps.length} Lap ke Studi</>}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DigitalStopwatchView;

