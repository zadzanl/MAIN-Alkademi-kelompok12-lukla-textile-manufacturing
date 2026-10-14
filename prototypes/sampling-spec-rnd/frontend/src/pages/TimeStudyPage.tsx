/**
 * Time Study Page - Fixed: complete button, counter percentage, list counter
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, Input } from '@/components';
import type { TimeStudy, TimeStudyStats } from '@/types';
import * as api from '@/services/api';

const STATUS_LABEL: Record<string, string> = {
  draft: 'Draf',
  in_progress: 'Berjalan',
  paused: 'Dijeda',
  completed: 'Selesai',
  archived: 'Diarsipkan',
};

const STATUS_COLOR: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-blue-100 text-blue-700',
  paused: 'bg-amber-100 text-amber-700',
  completed: 'bg-green-100 text-green-700',
  archived: 'bg-gray-100 text-gray-400',
};

function StatsPanel({ studyId }: { studyId: string }) {
  const [stats, setStats] = useState<TimeStudyStats | null>(null);
  const [loading, setLoading] = useState(false);
  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.getStudyStats(studyId);
    if (res.success && res.data) setStats(res.data);
    setLoading(false);
  }, [studyId]);
  useEffect(() => { load(); }, [load]);
  if (loading) return <p className="text-sm text-gray-400 animate-pulse mt-3">Memuat statistik...</p>;
  if (!stats || stats.total_samples === 0) return null;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3">
      {[
        { label: 'Total Sampel', value: stats.total_samples },
        { label: 'Rata-rata (ms)', value: stats.mean_cycle_time_ms != null ? stats.mean_cycle_time_ms.toFixed(0) : 'N/A' },
        { label: 'Std Dev', value: stats.std_dev != null ? stats.std_dev.toFixed(1) : 'N/A' },
        { label: 'Min / Maks', value: `${stats.min_cycle_time_ms != null ? stats.min_cycle_time_ms.toFixed(0) : 'N/A'} / ${stats.max_cycle_time_ms != null ? stats.max_cycle_time_ms.toFixed(0) : 'N/A'}` },
      ].map((s) => (
        <div key={s.label} className="bg-white/70 rounded-xl p-3 text-center">
          <p className="text-xs text-gray-500 mb-1">{s.label}</p>
          <p className="text-base font-semibold text-gray-900">{s.value}</p>
        </div>
      ))}
    </div>
  );
}

export default function TimeStudyPage() {
  const [studies, setStudies] = useState<TimeStudy[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [processName, setProcessName] = useState('');
  const [cycleTime, setCycleTime] = useState('');
  const [elementName, setElementName] = useState('manual_entry');
  const [isAbnormal, setIsAbnormal] = useState(false);
  const [error, setError] = useState('');
  const [creatingStudy, setCreatingStudy] = useState(false);
  const [startingId, setStartingId] = useState<string | null>(null);
  const [pausingId, setPausingId] = useState<string | null>(null);
  const [resumingId, setResumingId] = useState<string | null>(null);
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [addingSample, setAddingSample] = useState(false);

  const showError = (msg: string) => { setError(msg); setTimeout(() => setError(''), 6000); };

  const refreshStudy = useCallback(async (studyId: string): Promise<TimeStudy | null> => {
    const res = await api.getStudyData(studyId);
    if (res.success && res.data) {
      const fresh = res.data;
      setStudies((prev) => prev.map((s) => (s.study_id === studyId ? fresh : s)));
      return fresh;
    }
    return null;
  }, []);

  // Always derive selected from studies array so it stays fresh after refreshStudy
  const selected = studies.find((s) => s.study_id === selectedId) ?? null;

  const handleCreate = async () => {
    if (!processName.trim()) return;
    setCreatingStudy(true); setError('');
    try {
      const res = await api.createStudy({
        tenant_id: 'default',
        process_id: `proc_${Date.now()}`,
        process_name: processName.trim(),
        operator_id: 'op_001',
        target_sample_size: 30,
      });
      if (!res.success || !res.data?.study_id) throw new Error(res.error ?? 'Gagal membuat studi');
      const dataRes = await api.getStudyData(res.data.study_id);
      const newStudy: TimeStudy = (dataRes.success && dataRes.data) ? dataRes.data : {
        study_id: res.data.study_id, tenant_id: 'default', process_id: `proc_${Date.now()}`,
        process_name: processName.trim(), created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(), started_at: null, completed_at: null,
        status: 'draft', target_sample_size: 30, samples: [], confidence_level: 0.95,
        allowance_percent: 15, operator_id: 'op_001', department_id: 'dept_001',
        shift: 'A', product_id: 'prod_001', notes: '', total_cycles: 0,
        mean_cycle_time: 0, std_dev_cycle_time: 0, min_cycle_time: 0, max_cycle_time: 0,
      };
      setStudies((prev) => [newStudy, ...prev]);
      setProcessName('');
    } catch (e) { showError(e instanceof Error ? e.message : String(e)); }
    finally { setCreatingStudy(false); }
  };

  const handleStart = async (study: TimeStudy) => {
    setStartingId(study.study_id);
    try {
      const res = await api.startStudy(study.study_id);
      if (!res.success) throw new Error(res.error ?? 'Gagal memulai');
      await refreshStudy(study.study_id);
      setSelectedId(study.study_id);
    } catch (e) { showError(e instanceof Error ? e.message : String(e)); }
    finally { setStartingId(null); }
  };

  const handlePause = async (study: TimeStudy) => {
    setPausingId(study.study_id);
    try {
      const res = await api.pauseStudy(study.study_id);
      if (!res.success) throw new Error(res.error ?? 'Gagal menjeda');
      await refreshStudy(study.study_id);
    } catch (e) { showError(e instanceof Error ? e.message : String(e)); }
    finally { setPausingId(null); }
  };

  const handleResume = async (study: TimeStudy) => {
    setResumingId(study.study_id);
    try {
      const res = await api.resumeStudy(study.study_id);
      if (!res.success) throw new Error(res.error ?? 'Gagal melanjutkan');
      await refreshStudy(study.study_id);
      setSelectedId(study.study_id);
    } catch (e) { showError(e instanceof Error ? e.message : String(e)); }
    finally { setResumingId(null); }
  };

  const handleComplete = async (study: TimeStudy) => {
    setCompletingId(study.study_id);
    try {
      const res = await api.completeStudy(study.study_id);
      if (!res.success) throw new Error(res.error ?? 'Gagal menyelesaikan studi');
      await refreshStudy(study.study_id);
      setSelectedId(null);
    } catch (e) { showError(e instanceof Error ? e.message : String(e)); }
    finally { setCompletingId(null); }
  };

  const handleAddSample = async () => {
    if (!selected || !cycleTime.trim()) return;
    const ms = parseFloat(cycleTime);
    if (isNaN(ms) || ms <= 0) { showError('Waktu siklus harus angka positif'); return; }
    setAddingSample(true);
    try {
      const res = await api.addSample({
        study_id: selected.study_id, cycle_time_ms: ms,
        element_name: elementName || 'manual_entry', is_abnormal: isAbnormal,
      });
      if (!res.success) throw new Error(res.error ?? 'Gagal tambah sampel');
      await refreshStudy(selected.study_id);
      setCycleTime(''); setIsAbnormal(false);
    } catch (e) { showError(e instanceof Error ? e.message : String(e)); }
    finally { setAddingSample(false); }
  };

  const progressPct = selected
    ? Math.min(100, Math.round(((selected.total_cycles ?? 0) / (selected.target_sample_size || 30)) * 100))
    : 0;

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button onClick={() => setError('')} className="ml-4 text-red-400 hover:text-red-600 font-bold">✕</button>
        </div>
      )}

      <Card variant="glass" className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Buat Studi Baru</h2>
        <div className="flex gap-3">
          <Input
            placeholder="Nama Proses (cth: Jalur Perakitan A)"
            value={processName}
            onChange={(e) => setProcessName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            className="flex-1"
          />
          <Button variant="primary" onClick={handleCreate} isLoading={creatingStudy} disabled={!processName.trim()}>
            Buat Studi
          </Button>
        </div>
      </Card>

      {selected && selected.status === 'in_progress' && (
        <Card variant="glass" className="p-6 border-2 border-blue-200">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Tambah Sampel — <span className="text-blue-600">{selected.process_name}</span>
              </h2>
              <p className="text-sm text-gray-500 mt-0.5">
                {selected.total_cycles ?? 0} / {selected.target_sample_size} sampel terkumpul
                {(selected.mean_cycle_time ?? 0) > 0 && (
                  <span className="ml-3 font-medium text-gray-700">
                    Rata-rata: {selected.mean_cycle_time.toFixed(0)} ms
                  </span>
                )}
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              <Button variant="secondary" size="sm" onClick={() => handlePause(selected)} isLoading={pausingId === selected.study_id}>
                ⏸ Jeda
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleComplete(selected)} isLoading={completingId === selected.study_id}>
                ✓ Selesai
              </Button>
            </div>
          </div>
          <div className="flex gap-3 flex-wrap">
            <Input
              type="number"
              placeholder="Waktu Siklus (ms), cth: 1500"
              value={cycleTime}
              onChange={(e) => setCycleTime(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddSample()}
              className="flex-1 min-w-[180px]"
            />
            <Input
              placeholder="Nama Elemen (opsional)"
              value={elementName}
              onChange={(e) => setElementName(e.target.value)}
              className="w-44"
            />
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none self-center">
              <input type="checkbox" checked={isAbnormal} onChange={(e) => setIsAbnormal(e.target.checked)} className="rounded" />
              Abnormal
            </label>
            <Button variant="primary" onClick={handleAddSample} isLoading={addingSample} disabled={!cycleTime.trim()}>
              + Tambah Sampel
            </Button>
          </div>
          <div className="mt-4">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Kemajuan</span>
              <span>{progressPct}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full transition-all duration-500" style={{ width: `${progressPct}%` }} />
            </div>
            {(selected.total_cycles ?? 0) > 0 && (selected.total_cycles ?? 0) < 30 && (
              <p className="text-xs text-amber-600 mt-1">
                ⚠️ Rekomendasi minimal 30 sampel ({30 - (selected.total_cycles ?? 0)} sampel lagi)
              </p>
            )}
          </div>
        </Card>
      )}

      {selected && selected.status === 'paused' && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between">
          <p className="text-amber-800 font-medium">
            ⏸ Studi <span className="font-semibold">{selected.process_name}</span> dijeda · {selected.total_cycles ?? 0} sampel
          </p>
          <div className="flex gap-2">
            <Button variant="primary" size="sm" onClick={() => handleResume(selected)} isLoading={resumingId === selected.study_id}>▶ Lanjutkan</Button>
            <Button variant="danger" size="sm" onClick={() => handleComplete(selected)} isLoading={completingId === selected.study_id}>✓ Selesaikan</Button>
          </div>
        </div>
      )}

      {studies.length > 0 && (
        <Card variant="default" className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Semua Studi ({studies.length})</h2>
          <div className="space-y-3">
            {studies.map((study) => {
              const pct = Math.min(100, Math.round(((study.total_cycles ?? 0) / (study.target_sample_size || 30)) * 100));
              const isActive = selectedId === study.study_id;
              return (
                <div
                  key={study.study_id}
                  className={`rounded-xl border p-4 transition-all cursor-pointer ${isActive ? 'border-blue-300 bg-blue-50' : 'border-gray-100 bg-white/60 hover:bg-white/90'}`}
                  onClick={() => setSelectedId(study.study_id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{study.process_name}</p>
                      <p className="text-sm text-gray-500 mt-0.5">
                        {study.total_cycles ?? 0} / {study.target_sample_size} sampel
                        {(study.mean_cycle_time ?? 0) > 0 && ` · rata-rata ${study.mean_cycle_time.toFixed(0)} ms`}
                      </p>
                      {(study.total_cycles ?? 0) > 0 && (
                        <div className="mt-2 h-1 bg-gray-100 rounded-full overflow-hidden w-32">
                          <div className={`h-full rounded-full ${study.status === 'completed' ? 'bg-green-400' : 'bg-blue-400'}`} style={{ width: `${pct}%` }} />
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4 shrink-0" onClick={(e) => e.stopPropagation()}>
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_COLOR[study.status] ?? 'bg-gray-100 text-gray-600'}`}>
                        {STATUS_LABEL[study.status] ?? study.status}
                      </span>
                      {study.status === 'draft' && (
                        <Button variant="primary" size="sm" onClick={() => handleStart(study)} isLoading={startingId === study.study_id}>▶ Mulai</Button>
                      )}
                      {study.status === 'in_progress' && (
                        <Button variant="secondary" size="sm" onClick={() => setSelectedId(study.study_id)}>+ Sampel</Button>
                      )}
                      {study.status === 'paused' && (
                        <Button variant="secondary" size="sm" onClick={() => handleResume(study)} isLoading={resumingId === study.study_id}>▶ Lanjut</Button>
                      )}
                    </div>
                  </div>
                  {study.status === 'completed' && isActive && <StatsPanel studyId={study.study_id} />}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {studies.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-5xl mb-4">📋</p>
          <p className="text-lg font-medium">Belum ada studi</p>
          <p className="text-sm mt-1">Buat studi pertama di atas untuk mulai merekam waktu siklus</p>
        </div>
      )}
    </div>
  );
}
