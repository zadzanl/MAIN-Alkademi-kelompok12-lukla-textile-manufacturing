/**
 * DriftAnalysisView — Drift severity chart + record & resolve corrective actions
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import Modal from '../components/Modal';
import type { SpecVersion, DriftAnalysis, SpecDrift } from '../types';
import * as api from '../services/api';
import { toast } from '../services/toast';
import { TENANT_ID } from '../services/identity';

const SEV_COLOR: Record<string, { bg: string; text: string; bar: string }> = {
  low:      { bg: 'bg-[#e8f2ff]', text: 'text-[#0066cc]', bar: '#0071e3' },
  medium:   { bg: 'bg-[#fff4e6]', text: 'text-[#ff9500]', bar: '#ff9500' },
  high:     { bg: 'bg-[#ffebee]', text: 'text-[#ff3b30]', bar: '#ff3b30' },
  critical: { bg: 'bg-[#ff3b30]', text: 'text-white',     bar: '#cc0000' },
};

const DriftAnalysisView: React.FC = () => {
  const [specs, setSpecs]             = useState<SpecVersion[]>([]);
  const [selectedId, setSelectedId]   = useState('');
  const [analysis, setAnalysis]       = useState<{ analysis: DriftAnalysis; risk_score: number } | null>(null);
  const [report, setReport]           = useState<{ drifts: SpecDrift[] } | null>(null);
  const [loading, setLoading]         = useState(false);

  // Record drift form
  const [showRecord, setShowRecord]   = useState(false);
  const [driftForm, setDriftForm]     = useState({
    parameter_name: '', specification_limit: '', measured_value: '',
    severity: 'low', corrective_action: '',
  });

  // Resolve drift
  const [showResolve, setShowResolve] = useState(false);
  const [resolveDriftId, setResolveDriftId] = useState('');
  const [resolveAction, setResolveAction]   = useState('');

  const [msg, setMsg] = useState('');

  const fetchSpecs = useCallback(async () => {
    const res = await api.listSpecs(TENANT_ID);
    if (res.success && res.data) setSpecs(res.data);
  }, []);

  useEffect(() => { fetchSpecs(); }, [fetchSpecs]);

  const loadAnalysis = useCallback(async (id: string) => {
    if (!id) return;
    setLoading(true);
    try {
      const [ra, rr] = await Promise.all([
        api.getDriftAnalysis(id),
        api.getDriftReport(id),
      ]);
      if (ra.success && ra.data) setAnalysis(ra.data);
      if (rr.success && rr.data) setReport(rr.data as { drifts: SpecDrift[] });
    } finally { setLoading(false); }
  }, []);

  const handleSelectSpec = (id: string) => {
    setSelectedId(id);
    setAnalysis(null);
    setReport(null);
    loadAnalysis(id);
  };

  const handleRecordDrift = async () => {
    const { parameter_name, specification_limit, measured_value, severity, corrective_action } = driftForm;
    if (!parameter_name || !specification_limit || !measured_value) {
      toast.error('Parameter, Limit Spec, dan Nilai Terukur wajib diisi.'); return;
    }
    const res = await api.recordDrift({
      version_id: selectedId,
      parameter_name,
      specification_limit: Number(specification_limit),
      measured_value: Number(measured_value),
      severity: severity as 'low' | 'medium' | 'high' | 'critical',
      corrective_action,
    });
    if (res.success) {
      setMsg(`✓ ${res.message ?? ''}`); setShowRecord(false);
      setDriftForm({ parameter_name:'', specification_limit:'', measured_value:'', severity:'low', corrective_action:'' });
      loadAnalysis(selectedId);
    } else { toast.error(res.error ?? 'Gagal mencatat drift.'); }
    setTimeout(() => setMsg(''), 4000);
  };

  const handleResolveDrift = async () => {
    if (!resolveAction) { toast.error('Tindakan korektif wajib diisi.'); return; }
    const res = await api.resolveDrift(selectedId, resolveDriftId, resolveAction);
    if (res.success) {
      setMsg(`✓ ${res.message ?? ''}`); setShowResolve(false); setResolveAction('');
      loadAnalysis(selectedId);
    } else { toast.error(res.error ?? 'Gagal menyelesaikan drift.'); }
    setTimeout(() => setMsg(''), 4000);
  };

  const sev = analysis?.analysis?.severity_distribution ?? {};
  const total = Object.values(sev).reduce((s: number, v) => s + (typeof v === 'number' ? v : 0), 0);
  const reportDrifts = report?.drifts ?? [];

  const TREND_COLOR: Record<string, string> = {
    stable:     'text-[#34c759]',
    concerning: 'text-[#ff9500]',
    worsening:  'text-[#ff3b30]',
    critical:   'text-[#ff3b30]',
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">Analisis Drift Spesifikasi</h2>
          <p className="text-[#6e6e73] text-sm mt-1">Pantau penyimpangan parameter dan tindakan korektif</p>
        </div>
        {selectedId && (
          <button onClick={() => setShowRecord(true)}
            className="btn-danger">
            <LucideIcon name="plus" className="w-4 h-4" /> Catat Drift Baru
          </button>
        )}
      </div>

      {msg && (
        <div className="bg-[#e8f5e9] border border-[#34c759] rounded-[10px] px-4 py-2.5 text-[13px] text-[#1a7a34] font-medium">{msg}</div>
      )}

      {/* Spec selector */}
      <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-5">
        <label className="block text-sm font-medium text-[#1d1d1f] mb-2">Pilih Spec Version</label>
        <select value={selectedId} onChange={e => handleSelectSpec(e.target.value)} aria-label="Pilih Spec Version"
          className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]">
          <option value="">— Pilih spec version —</option>
          {specs.map(s => (
            <option key={s.version_id} value={s.version_id}>
              {s.spec_name} v{s.version_number} [{s.status}]
              {(s.critical_drifts ?? 0) > 0 ? ` ⚠ ${s.critical_drifts} kritis` : ''}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-8 text-center text-[#6e6e73]">
          Memuat analisis…
        </div>
      )}

      {analysis && !loading && (
        <>
          {/* Risk score + trend */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {(
              [
                { label: 'Risk Score',   value: `${analysis.risk_score}/100`, highlight: analysis.risk_score > 70, trendCls: '' },
                { label: 'Total Drifts', value: total,                         highlight: false,                    trendCls: '' },
                { label: 'Kritis',       value: sev.critical ?? 0,             highlight: (sev.critical ?? 0) > 0, trendCls: '' },
                { label: 'Trend',        value: analysis.analysis?.trend ?? '—', highlight: false,
                  trendCls: TREND_COLOR[analysis.analysis?.trend as string] ?? 'text-[#1d1d1f]' },
              ] as { label: string; value: string | number; highlight: boolean; trendCls: string }[]
            ).map(({ label, value, highlight, trendCls }) => (
              <div key={label} className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 text-center">
                <p className="text-xs text-[#6e6e73] uppercase tracking-wider mb-2">{label}</p>
                <p className={`text-[28px] font-semibold tracking-tight ${highlight ? 'text-[#ff3b30]' : (trendCls || 'text-[#1d1d1f]')}`}>
                  {String(value)}
                </p>
              </div>
            ))}
          </div>

          {/* Severity distribution bar chart */}
          <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-5">
            <h3 className="text-[15px] font-semibold text-[#1d1d1f] mb-4">Distribusi Severity</h3>
            <div className="space-y-3">
              {['critical','high','medium','low'].map(sev_key => {
                const count = sev[sev_key] ?? 0;
                const pct   = total > 0 ? (count / total) * 100 : 0;
                const c     = SEV_COLOR[sev_key];
                return (
                  <div key={sev_key}>
                    <div className="flex justify-between text-[13px] mb-1">
                      <span className={`font-medium capitalize ${c.text} ${c.bg} px-2 py-0.5 rounded-full text-[11px]`}>{sev_key}</span>
                      <span className="font-semibold text-[#1d1d1f]">{count}</span>
                    </div>
                    <div className="h-2 bg-[#f0f0f2] rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: c.bar }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Per-parameter table */}
          {analysis.analysis?.by_parameter && Object.keys(analysis.analysis.by_parameter).length > 0 && (
            <div className="bg-white border border-[#e6e6e9] rounded-[18px] overflow-hidden">
              <div className="px-5 py-4 border-b border-[#f0f0f2]">
                <h3 className="text-[15px] font-semibold text-[#1d1d1f]">Drift per Parameter</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px] border-collapse">
                  <thead>
                    <tr>
                      {['Parameter','Total Drift','Kritis','Tindakan'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2]">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(analysis.analysis.by_parameter).map(([param, data]: [string, { count: number; critical: number }]) => (
                      <tr key={param} className="border-b border-[#f0f0f2] last:border-0">
                        <td className="px-4 py-3 font-medium text-[#1d1d1f]">{param}</td>
                        <td className="px-4 py-3 text-[#626269]">{data.count}</td>
                        <td className={`px-4 py-3 font-semibold ${data.critical > 0 ? 'text-[#ff3b30]' : 'text-[#6e6e73]'}`}>{data.critical}</td>
                        <td className="px-4 py-3">
                          <button onClick={() => { /* open resolve by param */ }}
                            className="text-xs text-[#0066cc] hover:underline">Tindak lanjut</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Drift list from report */}
          {reportDrifts.length > 0 && (
            <div className="bg-white border border-[#e6e6e9] rounded-[18px] overflow-hidden">
              <div className="px-5 py-4 border-b border-[#f0f0f2]">
                <h3 className="text-[15px] font-semibold text-[#1d1d1f]">Semua Drift Tercatat</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px] border-collapse">
                  <thead>
                    <tr>
                      {['Parameter','Limit','Terukur','Deviasi %','Severity','Status','Aksi'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2] whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {reportDrifts.map((d: SpecDrift) => {
                      const c = SEV_COLOR[d.severity] ?? SEV_COLOR.low;
                      return (
                        <tr key={d.drift_id} className="border-b border-[#f0f0f2] last:border-0">
                          <td className="px-4 py-3 font-medium text-[#1d1d1f]">{d.parameter_name}</td>
                          <td className="px-4 py-3 font-mono text-[#6e6e73]">{d.specification_limit}</td>
                          <td className="px-4 py-3 font-mono text-[#1d1d1f]">{d.measured_value}</td>
                          <td className={`px-4 py-3 font-semibold ${d.deviation_percent > 20 ? 'text-[#ff3b30]' : 'text-[#ff9500]'}`}>
                            {d.deviation_percent?.toFixed(1)}%
                          </td>
                          <td className="px-4 py-3">
                            <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-semibold ${c.bg} ${c.text}`}>{d.severity}</span>
                          </td>
                          <td className="px-4 py-3">
                            {d.resolved
                              ? <span className="text-[#34c759] font-semibold text-xs">✓ Resolved</span>
                              : <span className="text-[#ff9500] text-xs font-medium">Open</span>}
                          </td>
                          <td className="px-4 py-3">
                            {!d.resolved && (
                              <button onClick={() => { setResolveDriftId(d.drift_id); setShowResolve(true); }}
                                className="btn-pill btn-pill-green">
                                Resolve
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {!selectedId && !loading && (
        <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-10 text-center text-[#6e6e73]">
          Pilih spec version di atas untuk melihat analisis drift.
        </div>
      )}

      {/* Record Drift Modal */}
      <Modal isOpen={showRecord} title="Catat Drift Baru" onClose={() => setShowRecord(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button onClick={() => setShowRecord(false)}
              className="border border-[#d5d5da] bg-white text-[#626269] rounded-[10px] px-4 py-2.5 text-[13px]">Batal</button>
            <button onClick={handleRecordDrift}
              className="btn-danger">Catat Drift</button>
          </div>
        }>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#1d1d1f] mb-1">Nama Parameter *</label>
            <input value={driftForm.parameter_name} placeholder="e.g. ketebalan_kain, lebar_jahitan" aria-label="Nama Parameter"
              onChange={e => setDriftForm(f => ({ ...f, parameter_name: e.target.value }))}
              className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[#1d1d1f] mb-1">Limit Spesifikasi *</label>
              <input type="number" value={driftForm.specification_limit} aria-label="Limit Spesifikasi"
                onChange={e => setDriftForm(f => ({ ...f, specification_limit: e.target.value }))}
                className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]" />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#1d1d1f] mb-1">Nilai Terukur *</label>
              <input type="number" value={driftForm.measured_value} aria-label="Nilai Terukur"
                onChange={e => setDriftForm(f => ({ ...f, measured_value: e.target.value }))}
                className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-[#1d1d1f] mb-1">Severity</label>
            <select value={driftForm.severity} onChange={e => setDriftForm(f => ({ ...f, severity: e.target.value }))} aria-label="Severity"
              className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]">
              {['low','medium','high','critical'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-[#1d1d1f] mb-1">Tindakan Korektif</label>
            <textarea rows={2} value={driftForm.corrective_action} aria-label="Tindakan Korektif"
              onChange={e => setDriftForm(f => ({ ...f, corrective_action: e.target.value }))}
              className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]"
              placeholder="Opsional — bisa diisi nanti saat resolve" />
          </div>
        </div>
      </Modal>

      {/* Resolve Modal */}
      <Modal isOpen={showResolve} title="Resolve Drift" onClose={() => setShowResolve(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button onClick={() => setShowResolve(false)}
              className="border border-[#d5d5da] bg-white text-[#626269] rounded-[10px] px-4 py-2.5 text-[13px]">Batal</button>
            <button onClick={handleResolveDrift}
              className="btn-success">Resolve</button>
          </div>
        }>
        <div>
          <label className="block text-sm font-medium text-[#1d1d1f] mb-1">Tindakan Korektif yang Diambil *</label>
          <textarea rows={3} value={resolveAction} aria-label="Tindakan Korektif yang Diambil"
            onChange={e => setResolveAction(e.target.value)}
            className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]"
            placeholder="Jelaskan tindakan yang sudah diambil untuk mengatasi drift ini…" />
        </div>
      </Modal>
    </div>
  );
};

export default DriftAnalysisView;

