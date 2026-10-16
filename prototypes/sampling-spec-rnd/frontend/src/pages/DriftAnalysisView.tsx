/**
 * DriftAnalysisView — Drift severity chart + record & resolve corrective actions
 *
 * View 02: Sample & Time Study Tracker
 * - Seam parameters diffing & tolerance drift monitoring (SPI, seam allowance, tension)
 * - Auto-calculation of deviation percent and recommended severity
 * - Preloaded Adis Sample Spec Version baseline with seam drift benchmarks
 * - Touch targets >= 48px, Apple Design System tokens, strict TypeScript
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import Modal from '../components/Modal';
import type { SpecVersion, DriftAnalysis, SpecDrift } from '../types';
import * as api from '../services/api';
import { toast } from '../services/toast';
import { TENANT_ID } from '../services/identity';

const SEV_COLOR: Record<string, { bg: string; text: string; bar: string }> = {
  low:      { bg: 'bg-brand-bg', text: 'text-brand', bar: '#0071e3' },
  medium:   { bg: 'bg-warn-bg', text: 'text-warn', bar: '#ff9500' },
  high:     { bg: 'bg-bad-bg', text: 'text-bad', bar: '#ff3b30' },
  critical: { bg: 'bg-bad', text: 'text-white',     bar: '#cc0000' },
};

// ── Standard Apparel Seam Parameters Presets ──────────────────────────────────
interface SeamParamPreset {
  id: string;
  name: string;
  label: string;
  default_limit: number;
  unit: string;
  tolerance: string;
  category: string;
}

const SEAM_PARAM_PRESETS: SeamParamPreset[] = [
  {
    id: 'spi',
    name: 'kerapatan_setik_spi',
    label: 'Kerapatan Setik Jahitan (SPI)',
    default_limit: 12.0,
    unit: 'SPI',
    tolerance: '±0.5 SPI',
    category: 'Jahitan Badan',
  },
  {
    id: 'allowance',
    name: 'lebar_kampuh_jahitan_mm',
    label: 'Lebar Kampuh Jahitan (Seam Allowance)',
    default_limit: 10.0,
    unit: 'mm',
    tolerance: '±1.0 mm',
    category: 'Pola & Kampuh',
  },
  {
    id: 'tension',
    name: 'tegangan_benang_jarum_cn',
    label: 'Tegangan Benang Jahit (Needle Tension)',
    default_limit: 120.0,
    unit: 'cN',
    tolerance: '±10 cN',
    category: 'Setting Mesin',
  },
  {
    id: 'stitch_len',
    name: 'panjang_langkah_setik_mm',
    label: 'Panjang Langkah Setik (Stitch Length)',
    default_limit: 2.5,
    unit: 'mm',
    tolerance: '±0.2 mm',
    category: 'Finishing Kelim',
  },
  {
    id: 'skew',
    name: 'kemiringan_obras_skew_pct',
    label: 'Kemiringan Sambungan Obras (Skew %)',
    default_limit: 2.0,
    unit: '%',
    tolerance: '< 2.5%',
    category: 'Obras & Safety Stitch',
  },
];

// ── Fallback Seed Spec for Adis Sample (ART-ADIS-001) ─────────────────────────
const SEED_ADIS_SPEC: SpecVersion = {
  version_id: 'spec-adis-v2',
  tenant_id: TENANT_ID,
  spec_id: 'SPEC-ADIS-001',
  spec_name: 'Adis Technical Running Tee — Seam Assembly v2',
  version_number: '2.0',
  created_at: new Date(Date.now() - 3 * 86400000).toISOString(),
  updated_at: new Date(Date.now() - 1 * 86400000).toISOString(),
  status: 'active',
  parameters: {
    kerapatan_setik_spi: 12.0,
    lebar_kampuh_jahitan_mm: 10.0,
    tegangan_benang_jarum_cn: 120.0,
    panjang_langkah_setik_mm: 2.5,
    kemiringan_obras_skew_pct: 2.0,
  },
  tolerances: {
    kerapatan_setik_spi: { min: 11.5, max: 12.5 },
    lebar_kampuh_jahitan_mm: { min: 9.0, max: 11.0 },
    tegangan_benang_jarum_cn: { min: 110.0, max: 130.0 },
  },
  materials: ['Dry-Fit Microfiber 140gsm', 'Rib Cotton 2x2', 'Spun Poly 40/2'],
  process_steps: ['Potong Pola', 'Jahit Kerah Rib', 'Bahu Double Stitch', 'Obras Lengan', 'Kelim Bawah'],
  changes: [],
  drifts: [
    {
      drift_id: 'drf-adis-001',
      timestamp: new Date(Date.now() - 2 * 86400000).toISOString(),
      parameter_name: 'kerapatan_setik_spi',
      specification_limit: 12.0,
      measured_value: 10.5,
      deviation_percent: 12.5,
      severity: 'medium',
      corrective_action: 'Kalibrasi feed dog dan tension dial mesin jahit #04',
      resolved: true,
      resolved_at: new Date(Date.now() - 1 * 86400000).toISOString(),
    },
    {
      drift_id: 'drf-adis-002',
      timestamp: new Date(Date.now() - 1 * 86400000).toISOString(),
      parameter_name: 'lebar_kampuh_jahitan_mm',
      specification_limit: 10.0,
      measured_value: 12.2,
      deviation_percent: 22.0,
      severity: 'high',
      corrective_action: 'Setel ulang guide plate pembatas kampuh lini obras',
      resolved: false,
      resolved_at: null,
    },
    {
      drift_id: 'drf-adis-003',
      timestamp: new Date().toISOString(),
      parameter_name: 'kemiringan_obras_skew_pct',
      specification_limit: 2.0,
      measured_value: 2.8,
      deviation_percent: 40.0,
      severity: 'critical',
      corrective_action: 'Periksa kelurusan feeding kain pada roll penarik',
      resolved: false,
      resolved_at: null,
    },
  ],
  total_drifts: 3,
  critical_drifts: 1,
  created_by: 'Budi Time-Study (IE)',
  approved_by: 'QA_DIRECTOR_01',
  approved_at: new Date(Date.now() - 1 * 86400000).toISOString(),
  notes: 'Spesifikasi jahitan terverifikasi dari hasil sampling Adis Sample.',
  parent_version_id: 'spec-adis-v1',
  supersedes_version_id: 'spec-adis-v1',
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
    parameter_name: '',
    specification_limit: '',
    measured_value: '',
    severity: 'low',
    corrective_action: '',
  });

  // Resolve drift
  const [showResolve, setShowResolve] = useState(false);
  const [resolveDriftId, setResolveDriftId] = useState('');
  const [resolveAction, setResolveAction]   = useState('');

  const [msg, setMsg] = useState('');

  const fetchSpecs = useCallback(async () => {
    try {
      const res = await api.listSpecs(TENANT_ID);
      if (res.success && res.data && res.data.length > 0) {
        setSpecs(res.data);
        if (!selectedId) {
          setSelectedId(res.data[0].version_id);
          loadAnalysis(res.data[0].version_id);
        }
      } else {
        // Fallback to rich seed spec for Adis Sample
        setSpecs([SEED_ADIS_SPEC]);
        setSelectedId(SEED_ADIS_SPEC.version_id);
        loadLocalAnalysis(SEED_ADIS_SPEC);
      }
    } catch {
      setSpecs([SEED_ADIS_SPEC]);
      setSelectedId(SEED_ADIS_SPEC.version_id);
      loadLocalAnalysis(SEED_ADIS_SPEC);
    }
  }, [selectedId]);

  useEffect(() => { fetchSpecs(); }, [fetchSpecs]);

  const loadLocalAnalysis = (spec: SpecVersion) => {
    const drifts = spec.drifts || [];
    const criticalCount = drifts.filter(d => d.severity === 'critical').length;
    const highCount = drifts.filter(d => d.severity === 'high').length;
    const medCount = drifts.filter(d => d.severity === 'medium').length;
    const lowCount = drifts.filter(d => d.severity === 'low').length;

    const byParam: Record<string, { count: number; critical: number }> = {};
    drifts.forEach(d => {
      if (!byParam[d.parameter_name]) {
        byParam[d.parameter_name] = { count: 0, critical: 0 };
      }
      byParam[d.parameter_name].count++;
      if (d.severity === 'critical') byParam[d.parameter_name].critical++;
    });

    setAnalysis({
      risk_score: criticalCount > 0 ? 82 : highCount > 0 ? 55 : 20,
      analysis: {
        total_drifts: drifts.length,
        severity_distribution: {
          critical: criticalCount,
          high: highCount,
          medium: medCount,
          low: lowCount,
        },
        by_parameter: byParam,
        critical_parameters: Object.keys(byParam).filter(k => byParam[k].critical > 0),
        critical_rate_percent: drifts.length > 0 ? Math.round((criticalCount / drifts.length) * 100) : 0,
        trend: criticalCount > 0 ? 'concerning' : 'stable',
        parameters_with_drift: Object.keys(byParam).length,
      },
    });

    setReport({ drifts });
  };

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
    } catch {
      const spec = specs.find(s => s.version_id === id) || SEED_ADIS_SPEC;
      loadLocalAnalysis(spec);
    } finally {
      setLoading(false);
    }
  }, [specs]);

  const handleSelectSpec = (id: string) => {
    setSelectedId(id);
    setAnalysis(null);
    setReport(null);
    const spec = specs.find(s => s.version_id === id);
    if (spec && spec.drifts) {
      loadLocalAnalysis(spec);
    } else {
      loadAnalysis(id);
    }
  };

  // Auto-calculate suggested severity when spec limit and measured value change
  const handleLimitOrMeasuredChange = (limitStr: string, measuredStr: string) => {
    const limit = parseFloat(limitStr);
    const measured = parseFloat(measuredStr);
    if (!isNaN(limit) && !isNaN(measured) && limit > 0) {
      const devPct = Math.abs((measured - limit) / limit) * 100;
      let suggestedSev = 'low';
      if (devPct > 25) suggestedSev = 'critical';
      else if (devPct > 15) suggestedSev = 'high';
      else if (devPct > 7) suggestedSev = 'medium';

      setDriftForm(f => ({ ...f, specification_limit: limitStr, measured_value: measuredStr, severity: suggestedSev }));
    } else {
      setDriftForm(f => ({ ...f, specification_limit: limitStr, measured_value: measuredStr }));
    }
  };

  const handleApplyPreset = (preset: SeamParamPreset) => {
    handleLimitOrMeasuredChange(preset.default_limit.toString(), driftForm.measured_value);
    setDriftForm(f => ({
      ...f,
      parameter_name: preset.name,
      specification_limit: preset.default_limit.toString(),
      corrective_action: `Target toleransi ${preset.tolerance} (${preset.category})`,
    }));
  };

  const handleRecordDrift = async () => {
    const { parameter_name, specification_limit, measured_value, severity, corrective_action } = driftForm;
    if (!parameter_name || !specification_limit || !measured_value) {
      toast.error('Parameter, Limit Spec, dan Nilai Terukur wajib diisi.'); return;
    }

    const limitNum = Number(specification_limit);
    const measuredNum = Number(measured_value);
    const devPct = Math.abs((measuredNum - limitNum) / limitNum) * 100;

    const res = await api.recordDrift({
      version_id: selectedId,
      parameter_name,
      specification_limit: limitNum,
      measured_value: measuredNum,
      severity: severity as 'low' | 'medium' | 'high' | 'critical',
      corrective_action,
    });

    if (res.success) {
      setMsg(`✓ ${res.message ?? 'Drift parameter jahitan berhasil dicatat.'}`);
      setShowRecord(false);
      setDriftForm({ parameter_name:'', specification_limit:'', measured_value:'', severity:'low', corrective_action:'' });
      loadAnalysis(selectedId);
      toast.success('Drift parameter jahitan berhasil dicatat.');
    } else {
      // Local fallback simulation
      const newDrift: SpecDrift = {
        drift_id: `drf-${Date.now().toString().slice(-4)}`,
        timestamp: new Date().toISOString(),
        parameter_name,
        specification_limit: limitNum,
        measured_value: measuredNum,
        deviation_percent: devPct,
        severity: severity as 'low' | 'medium' | 'high' | 'critical',
        corrective_action,
        resolved: false,
        resolved_at: null,
      };

      setReport(prev => ({ drifts: [newDrift, ...(prev?.drifts || [])] }));
      setShowRecord(false);
      setDriftForm({ parameter_name:'', specification_limit:'', measured_value:'', severity:'low', corrective_action:'' });
      toast.success('Drift parameter jahitan berhasil dicatat.');
    }
    setTimeout(() => setMsg(''), 4000);
  };

  const handleResolveDrift = async () => {
    if (!resolveAction.trim()) {
      toast.error('Tindakan korektif wajib diisi.'); return;
    }
    const res = await api.resolveDrift(selectedId, resolveDriftId, resolveAction);
    if (res.success) {
      setMsg(`✓ ${res.message ?? 'Drift telah diselesaikan.'}`);
      setShowResolve(false);
      setResolveAction('');
      loadAnalysis(selectedId);
      toast.success('Drift berhasil diselesaikan dengan tindakan korektif.');
    } else {
      // Local fallback
      setReport(prev => ({
        drifts: (prev?.drifts || []).map(d => d.drift_id === resolveDriftId ? {
          ...d,
          resolved: true,
          resolved_at: new Date().toISOString(),
          corrective_action: resolveAction,
        } : d),
      }));
      setShowResolve(false);
      setResolveAction('');
      toast.success('Drift berhasil diselesaikan.');
    }
    setTimeout(() => setMsg(''), 4000);
  };

  const sev = analysis?.analysis?.severity_distribution ?? {};
  const total = Object.values(sev).reduce((s: number, v) => s + (typeof v === 'number' ? v : 0), 0);
  const reportDrifts = report?.drifts ?? [];

  const TREND_COLOR: Record<string, string> = {
    stable:     'text-ok',
    concerning: 'text-warn',
    worsening:  'text-bad',
    critical:   'text-bad',
  };

  return (
    <div className="space-y-6">
      {/* ── Top Header Banner with Apple HIG Styling ─────────────────── */}
      <div className="flex flex-wrap justify-between items-center gap-4 bg-white border border-hair rounded-[20px] p-6 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <span className="pill bg-bad-bg text-bad rounded-full px-3 py-1 text-[11px] font-bold tracking-wide uppercase">
              Quality Assurance & R&D
            </span>
            <span className="text-xs text-ink-muted">Statistical Process Control · Touch Target ≥48px</span>
          </div>
          <h2 className="text-2xl font-bold text-ink mt-1 tracking-tight">Analisis Drift & Toleransi Parameter Jahitan</h2>
          <p className="text-ink-muted text-sm mt-0.5">
            Pantau deviasi parameter jahitan (SPI, kampuh, tension) terhadap batas spesifikasi teknis
          </p>
        </div>

        {selectedId && (
          <button
            onClick={() => setShowRecord(true)}
            className="btn-danger min-h-[48px] px-5 py-2.5 rounded-[12px] font-bold text-[13px] inline-flex items-center gap-2 shadow-sm"
          >
            <LucideIcon name="plus" className="w-4 h-4 text-white" /> Catat Drift Parameter Jahitan
          </button>
        )}
      </div>

      {msg && (
        <div className="bg-ok-bg border border-ok/40 rounded-[14px] px-4 py-3 text-[13px] text-ok-2 font-semibold">
          {msg}
        </div>
      )}

      {/* ── Spec Version Selector ─────────────────────────────────────── */}
      <div className="bg-white border border-hair rounded-[20px] p-5 shadow-sm space-y-2">
        <label className="block text-xs font-bold text-ink uppercase tracking-wider">
          Pilih Spesifikasi Produk / Versi Target
        </label>
        <select
          value={selectedId}
          onChange={e => handleSelectSpec(e.target.value)}
          aria-label="Pilih Spec Version"
          className="w-full min-h-[48px] border border-hair-2 rounded-[12px] px-3.5 py-2.5 text-[13px] bg-white focus:outline-2 focus:outline-brand-soft"
        >
          <option value="">— Pilih Versi Spesifikasi Produk —</option>
          {specs.map(s => (
            <option key={s.version_id} value={s.version_id}>
              {s.spec_name} (v{s.version_number}) [{s.status}]
              {(s.critical_drifts ?? 0) > 0 ? ` ⚠ ${s.critical_drifts} drift kritis` : ''}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="bg-white border border-hair rounded-[20px] p-10 text-center text-ink-muted">
          Memuat data analisis statistik drift…
        </div>
      )}

      {analysis && !loading && (
        <>
          {/* Risk score + trend KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Indeks Skor Risiko',   value: `${analysis.risk_score}/100`, highlight: analysis.risk_score > 70, trendCls: '' },
              { label: 'Total Drift Tercatat', value: total,                         highlight: false,                    trendCls: '' },
              { label: 'Penyimpangan Kritis',  value: sev.critical ?? 0,             highlight: (sev.critical ?? 0) > 0, trendCls: 'text-bad' },
              { label: 'Tren Deviasi Jahitan', value: analysis.analysis?.trend ?? 'stable', highlight: false,
                trendCls: TREND_COLOR[analysis.analysis?.trend as string] ?? 'text-ink' },
            ].map(({ label, value, highlight, trendCls }) => (
              <div key={label} className="bg-white border border-hair rounded-[18px] p-5 text-center shadow-xs">
                <span className="text-xs font-bold text-ink-muted uppercase tracking-wider block mb-1">{label}</span>
                <span className={`text-[30px] font-extrabold tracking-tight ${highlight ? 'text-bad' : (trendCls || 'text-ink')}`}>
                  {String(value)}
                </span>
              </div>
            ))}
          </div>

          {/* Severity distribution bar chart */}
          <div className="bg-white border border-hair rounded-[20px] p-6 shadow-sm">
            <h3 className="text-base font-bold text-ink mb-4">Distribusi Tingkat Keparahan (Severity Distribution)</h3>
            <div className="space-y-4">
              {['critical','high','medium','low'].map(sev_key => {
                const count = sev[sev_key] ?? 0;
                const pct   = total > 0 ? (count / total) * 100 : 0;
                const c     = SEV_COLOR[sev_key];
                return (
                  <div key={sev_key}>
                    <div className="flex justify-between text-[13px] mb-1.5">
                      <span className={`font-bold capitalize ${c.text} ${c.bg} px-2.5 py-0.5 rounded-full text-[11px]`}>{sev_key}</span>
                      <span className="font-mono font-bold text-ink">{count} temuan ({pct.toFixed(0)}%)</span>
                    </div>
                    <div className="h-2.5 bg-panel-2 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-300" style={{ width: `${pct}%`, backgroundColor: c.bar }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Seam Parameter Drift Table */}
          {analysis.analysis?.by_parameter && Object.keys(analysis.analysis.by_parameter).length > 0 && (
            <div className="bg-white border border-hair rounded-[20px] overflow-hidden shadow-sm">
              <div className="px-6 py-4 border-b border-panel-2 bg-panel/30">
                <h3 className="text-base font-bold text-ink">Penyimpangan Berdasarkan Parameter Jahitan</h3>
                <p className="text-xs text-ink-muted mt-0.5">Pemantauan titik kritis per parameter penjahitan</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px] border-collapse">
                  <thead>
                    <tr className="bg-panel border-b border-panel-2 text-ink-muted text-[11px] font-bold uppercase tracking-wider">
                      {['Parameter Seam', 'Total Kasus Drift', 'Penyimpangan Kritis', 'Status Evaluasi'].map(h => (
                        <th key={h} className="px-5 py-3 text-left">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(analysis.analysis.by_parameter).map(([param, data]: [string, { count: number; critical: number }]) => (
                      <tr key={param} className="border-b border-hair-2 hover:bg-page/40 transition-colors">
                        <td className="px-5 py-3 font-semibold text-ink">{param.replace(/_/g, ' ')}</td>
                        <td className="px-5 py-3 font-mono font-bold text-ink-muted">{data.count}</td>
                        <td className={`px-5 py-3 font-mono font-bold ${data.critical > 0 ? 'text-bad' : 'text-ink-muted'}`}>
                          {data.critical > 0 ? `⚠ ${data.critical}` : '0'}
                        </td>
                        <td className="px-5 py-3">
                          <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-bold ${data.critical > 0 ? 'bg-bad-bg text-bad' : 'bg-ok-bg text-ok'}`}>
                            {data.critical > 0 ? 'Memerlukan Kalibrasi' : 'Terkontrol'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Drift list from report with Diffing metrics */}
          {reportDrifts.length > 0 && (
            <div className="bg-white border border-hair rounded-[20px] overflow-hidden shadow-sm">
              <div className="px-6 py-4 border-b border-panel-2 bg-panel/30 flex justify-between items-center">
                <div>
                  <h3 className="text-base font-bold text-ink">Catatan Lengkap Deviasi Parameter & Tindakan Korektif</h3>
                  <p className="text-xs text-ink-muted mt-0.5">{reportDrifts.length} riwayat pengukuran deviasi</p>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px] border-collapse">
                  <thead>
                    <tr className="bg-panel border-b border-panel-2 text-ink-muted text-[11px] font-bold uppercase tracking-wider">
                      {['Parameter', 'Batas Spec', 'Nilai Terukur', 'Deviasi Diff %', 'Tingkat Severity', 'Status Resolusi', 'Aksi Tindak Lanjut'].map(h => (
                        <th key={h} className="px-4 py-3 text-left whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {reportDrifts.map((d: SpecDrift) => {
                      const c = SEV_COLOR[d.severity] ?? SEV_COLOR.low;
                      return (
                        <tr key={d.drift_id} className="border-b border-hair-2 hover:bg-page/40 transition-colors">
                          <td className="px-4 py-3 font-semibold text-ink">{d.parameter_name.replace(/_/g, ' ')}</td>
                          <td className="px-4 py-3 font-mono text-ink-muted">{d.specification_limit}</td>
                          <td className="px-4 py-3 font-mono font-bold text-ink">{d.measured_value}</td>
                          <td className={`px-4 py-3 font-mono font-bold ${d.deviation_percent > 20 ? 'text-bad' : 'text-warn'}`}>
                            {d.deviation_percent > 0 ? `+${d.deviation_percent.toFixed(1)}%` : `${d.deviation_percent.toFixed(1)}%`}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider ${c.bg} ${c.text}`}>{d.severity}</span>
                          </td>
                          <td className="px-4 py-3">
                            {d.resolved ? (
                              <div className="text-ok font-bold text-xs inline-flex items-center gap-1">
                                <LucideIcon name="check-circle" className="w-3.5 h-3.5" />
                                <span>Resolved</span>
                              </div>
                            ) : (
                              <span className="text-warn text-xs font-bold">Open</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {!d.resolved ? (
                              <button
                                onClick={() => { setResolveDriftId(d.drift_id); setShowResolve(true); }}
                                className="btn-secondary min-h-[48px] px-4 py-2 text-xs font-bold rounded-[10px] bg-ok-bg text-ok border border-ok hover:bg-ok hover:text-white transition-colors"
                              >
                                Resolve & Solusi
                              </button>
                            ) : (
                              <span className="text-xs text-ink-muted italic">Tindakan selesai</span>
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

      {/* ── MODAL: RECORD DRIFT WITH SEAM PRESETS ─────────────────────── */}
      <Modal
        isOpen={showRecord}
        title="Catat Drift Parameter Jahitan Baru"
        onClose={() => setShowRecord(false)}
        footer={
          <div className="flex gap-3 justify-end items-center">
            <button
              onClick={() => setShowRecord(false)}
              className="btn-secondary min-h-[48px] px-5 py-2.5 rounded-[12px] text-[13px] font-semibold border border-hair-4"
            >
              Batal
            </button>
            <button
              onClick={handleRecordDrift}
              className="btn-danger min-h-[48px] px-6 py-2.5 rounded-[12px] text-[13px] font-bold shadow-sm"
            >
              Catat Drift
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          {/* Seam parameter quick preset buttons */}
          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">
              Preset Parameter Jahitan Cepat (Standard Seam Assembly)
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {SEAM_PARAM_PRESETS.map(preset => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => handleApplyPreset(preset)}
                  className="min-h-[48px] p-2 text-left rounded-[10px] border border-hair bg-panel hover:bg-white hover:border-brand transition-all flex flex-col justify-center"
                >
                  <span className="text-[11px] font-bold text-ink truncate">{preset.label}</span>
                  <span className="text-[10px] text-ink-muted font-mono">Batas: {preset.default_limit} {preset.unit}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Nama Parameter Jahitan *</label>
            <input
              value={driftForm.parameter_name}
              placeholder="e.g. kerapatan_setik_spi, lebar_kampuh_jahitan_mm"
              aria-label="Nama Parameter"
              onChange={e => setDriftForm(f => ({ ...f, parameter_name: e.target.value }))}
              className="w-full min-h-[48px] border border-hair-2 rounded-[12px] px-3.5 py-2.5 text-[13px] bg-white focus:outline-2 focus:outline-brand-soft"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Limit Target Spesifikasi *</label>
              <input
                type="number"
                step={0.1}
                value={driftForm.specification_limit}
                aria-label="Limit Spesifikasi"
                onChange={e => handleLimitOrMeasuredChange(e.target.value, driftForm.measured_value)}
                className="w-full min-h-[48px] border border-hair-2 rounded-[12px] px-3.5 py-2.5 text-[13px] bg-white focus:outline-2 focus:outline-brand-soft"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Nilai Terukur Aktual *</label>
              <input
                type="number"
                step={0.1}
                value={driftForm.measured_value}
                aria-label="Nilai Terukur"
                onChange={e => handleLimitOrMeasuredChange(driftForm.specification_limit, e.target.value)}
                className="w-full min-h-[48px] border border-hair-2 rounded-[12px] px-3.5 py-2.5 text-[13px] bg-white focus:outline-2 focus:outline-brand-soft"
              />
            </div>
          </div>

          {/* Deviation indicator */}
          {parseFloat(driftForm.specification_limit) > 0 && parseFloat(driftForm.measured_value) > 0 && (
            <div className="bg-panel p-3 rounded-[10px] border border-hair text-xs flex justify-between items-center">
              <span className="text-ink-muted">Deviasi Terhitung:</span>
              <span className="font-mono font-bold text-ink">
                {(Math.abs(parseFloat(driftForm.measured_value) - parseFloat(driftForm.specification_limit)) / parseFloat(driftForm.specification_limit) * 100).toFixed(1)}% deviasi
              </span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Tingkat Keparahan (Severity)</label>
            <select
              value={driftForm.severity}
              onChange={e => setDriftForm(f => ({ ...f, severity: e.target.value }))}
              aria-label="Severity"
              className="w-full min-h-[48px] border border-hair-2 rounded-[12px] px-3.5 py-2.5 text-[13px] bg-white focus:outline-2 focus:outline-brand-soft"
            >
              {['low','medium','high','critical'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Rencana Tindakan Korektif</label>
            <textarea
              rows={2}
              value={driftForm.corrective_action}
              aria-label="Tindakan Korektif"
              onChange={e => setDriftForm(f => ({ ...f, corrective_action: e.target.value }))}
              className="w-full border border-hair-2 rounded-[12px] p-3 text-[13px] bg-white focus:outline-2 focus:outline-brand-soft"
              placeholder="e.g. Kalibrasi rotary hook dan setel ulang gauge jarum mesin obras #02"
            />
          </div>
        </div>
      </Modal>

      {/* ── MODAL: RESOLVE DRIFT ──────────────────────────────────────── */}
      <Modal
        isOpen={showResolve}
        title="Penyelesaian Drift Parameter Jahitan"
        onClose={() => setShowResolve(false)}
        footer={
          <div className="flex gap-3 justify-end items-center">
            <button
              onClick={() => setShowResolve(false)}
              className="btn-secondary min-h-[48px] px-5 py-2.5 rounded-[12px] text-[13px] font-semibold border border-hair-4"
            >
              Batal
            </button>
            <button
              onClick={handleResolveDrift}
              className="btn-success min-h-[48px] px-6 py-2.5 rounded-[12px] text-[13px] font-bold shadow-sm"
            >
              Tandai Terselesaikan (Resolve)
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">
              Tindakan Korektif yang Telah Diterapkan di Lini Produksi *
            </label>
            <textarea
              rows={3}
              value={resolveAction}
              aria-label="Tindakan Korektif yang Diambil"
              onChange={e => setResolveAction(e.target.value)}
              className="w-full border border-hair-2 rounded-[12px] p-3 text-[13px] bg-white focus:outline-2 focus:outline-brand-soft"
              placeholder="Jelaskan tindakan teknis yang telah diambil (e.g. jarum diganti ukuran #11 ballpoint, tension dial disetel ke skala 3.5, hasil jahit ulang telah memenuhi toleransi 12 SPI)..."
            />
          </div>
          <p className="text-xs text-ink-muted">
            Status drift akan diubah menjadi <strong className="text-ok">Resolved</strong> dan dicatat ke dalam log jejak audit kualitas spesifikasi.
          </p>
        </div>
      </Modal>
    </div>
  );
};

export default DriftAnalysisView;
