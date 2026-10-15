/**
 * ActiveStudiesView — Real-time monitor of in_progress time studies
 * Shows live progress bars, control buttons (pause/resume/complete)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import type { TimeStudy } from '../types';
import * as api from '../services/api';
import { TENANT_ID } from '../services/identity';

const fmtMs = (ms: number) => {
  if (!ms) return '—';
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
};

const ActiveStudiesView: React.FC = () => {
  const [studies, setStudies] = useState<TimeStudy[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState('');

  const fetchStudies = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.listStudies(TENANT_ID);
      if (res.success && res.data) setStudies(res.data);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    fetchStudies();
    // poll every 10s
    const timer = setInterval(fetchStudies, 10_000);
    return () => clearInterval(timer);
  }, [fetchStudies]);

  const action = async (study_id: string, verb: 'start'|'pause'|'resume'|'complete') => {
    const run = {
      start: api.startStudy,
      pause: api.pauseStudy,
      resume: api.resumeStudy,
      complete: api.completeStudy,
    }[verb];
    const res = await run(study_id);
    setActionMsg(res.success ? (res.message ?? '') : (res.error ?? ''));
    fetchStudies();
    setTimeout(() => setActionMsg(''), 3000);
  };

  const active  = studies.filter(s => s.status === 'in_progress');
  const paused  = studies.filter(s => s.status === 'paused');
  const draft   = studies.filter(s => s.status === 'draft');

  const StudyCard: React.FC<{ study: TimeStudy }> = ({ study }) => {
    const pct = Math.min(100, Math.round(((study.total_cycles ?? 0) / study.target_sample_size) * 100));
    const statusColor =
      study.status === 'in_progress' ? 'border-l-ok' :
      study.status === 'paused'      ? 'border-l-warn' : 'border-l-brand';

    return (
      <div className={`bg-white border border-hair border-l-4 ${statusColor} rounded-[14px] p-5`}>
        <div className="flex justify-between items-start gap-3 mb-3">
          <div className="min-w-0">
            <p className="font-semibold text-ink truncate">{study.process_name}</p>
            <p className="text-xs text-ink-muted mt-0.5">
              ID: {study.study_id.substring(0,8)} · Operator: {study.operator_id || '—'}
            </p>
          </div>
          <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-semibold whitespace-nowrap ${
            study.status === 'in_progress' ? 'bg-ok-bg text-ok' :
            study.status === 'paused'      ? 'bg-warn-bg text-warn' : 'bg-brand-bg text-brand'
          }`}>{study.status}</span>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-3 mb-3">
          <div className="flex-1 h-2 bg-panel-2 rounded-full overflow-hidden">
            <div className="h-full bg-brand rounded-full transition-all" style={{ width: `${pct}%` }} />
          </div>
          <span className="text-[13px] font-semibold text-ink whitespace-nowrap">
            {study.total_cycles ?? 0}/{study.target_sample_size} ({pct}%)
          </span>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3 mb-4 text-center">
          {[
            { label: 'Rata-rata', value: fmtMs(study.mean_cycle_time) },
            { label: 'Min',       value: fmtMs(study.min_cycle_time) },
            { label: 'Max',       value: fmtMs(study.max_cycle_time) },
          ].map(({ label, value }) => (
            <div key={label} className="bg-page rounded-[10px] px-2 py-2">
              <p className="text-[10px] text-ink-muted uppercase tracking-wider">{label}</p>
              <p className="text-[13px] font-semibold text-ink mt-0.5 font-mono">{value}</p>
            </div>
          ))}
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 flex-wrap">
          {study.status === 'draft' && (
            <button onClick={() => action(study.study_id, 'start')}
              className="btn-success !py-1.5 !px-3 !text-xs rounded-lg">
              ▶ Mulai
            </button>
          )}
          {study.status === 'in_progress' && (
            <>
              <button onClick={() => action(study.study_id, 'pause')}
                className="btn-primary !py-1.5 !px-3 !text-xs rounded-lg !bg-warn-2 !shadow-none">
                ⏸ Pause
              </button>
              <button onClick={() => action(study.study_id, 'complete')}
                className="btn-secondary !py-1.5 !px-3 !text-xs">
                ✓ Selesai
              </button>
            </>
          )}
          {study.status === 'paused' && (
            <>
              <button onClick={() => action(study.study_id, 'resume')}
                className="bg-brand text-white rounded-[9px] px-3 py-1.5 text-[12px] font-semibold hover:bg-brand">
                ▶ Lanjutkan
              </button>
              <button onClick={() => action(study.study_id, 'complete')}
                className="btn-secondary !py-1.5 !px-3 !text-xs">
                ✓ Selesai
              </button>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold text-ink">Studi Aktif</h2>
          <p className="text-ink-muted text-sm mt-1">Monitor & kontrol studi waktu yang sedang berjalan</p>
        </div>
        <button onClick={fetchStudies}
          className="btn-secondary">
          <LucideIcon name="activity" className="w-4 h-4" /> Refresh
        </button>
      </div>

      {actionMsg && (
        <div className="bg-ok-bg border border-ok rounded-[10px] px-4 py-2.5 text-[13px] text-ok-2 font-medium">
          ✓ {actionMsg}
        </div>
      )}

      {/* In progress */}
      {active.length > 0 && (
        <section>
          <p className="text-sm font-semibold text-ink-muted uppercase tracking-wider mb-3">Berjalan ({active.length})</p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {active.map(s => <StudyCard key={s.study_id} study={s} />)}
          </div>
        </section>
      )}

      {/* Paused */}
      {paused.length > 0 && (
        <section>
          <p className="text-sm font-semibold text-ink-muted uppercase tracking-wider mb-3">Dijeda ({paused.length})</p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {paused.map(s => <StudyCard key={s.study_id} study={s} />)}
          </div>
        </section>
      )}

      {/* Draft */}
      {draft.length > 0 && (
        <section>
          <p className="text-sm font-semibold text-ink-muted uppercase tracking-wider mb-3">Draft Siap Dimulai ({draft.length})</p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {draft.map(s => <StudyCard key={s.study_id} study={s} />)}
          </div>
        </section>
      )}

      {!loading && active.length === 0 && paused.length === 0 && draft.length === 0 && (
        <div className="bg-white border border-hair rounded-[18px] p-10 text-center text-ink-muted">
          Tidak ada studi yang aktif. Buat studi baru di menu <strong>Studi Waktu</strong>.
        </div>
      )}
    </div>
  );
};

export default ActiveStudiesView;

