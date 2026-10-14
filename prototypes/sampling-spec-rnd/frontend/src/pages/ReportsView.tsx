/**
 * ReportsView — Aggregate reports: time study stats, material costing, rate card summary
 * Bridge to Manufacturing Execution: final approved data ready for mandor / production line
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import type { TimeStudy, SampleVersion } from '../types';

const API = 'http://localhost:8009/api/sampling-spec-rnd';

const fmtMs  = (ms: number)   => ms ? `${Math.round(ms).toLocaleString('id-ID')} ms` : '—';
const fmtRp  = (n: number)    => `Rp ${n.toLocaleString('id-ID')}`;
const fmtPct = (n: number)    => `${n.toFixed(1)}%`;

const RATE_PER_MIN_IDR = 500; // floor rate

const rateCard = (meanMs: number, allowance: number) => {
  const allowanceFactor = 1 + allowance / 100;
  const stdTimeMin = (meanMs / 1000 / 60) * allowanceFactor;
  return Math.round(stdTimeMin * RATE_PER_MIN_IDR);
};

interface Props { onExportCSV: (data: any[], filename: string) => void; }

const ReportsView: React.FC<Props> = ({ onExportCSV }) => {
  const [studies, setStudies]   = useState<TimeStudy[]>([]);
  const [svList, setSvList]     = useState<SampleVersion[]>([]);
  const [loading, setLoading]   = useState(false);
  const [activeTab, setActiveTab] = useState<'timestudy'|'costing'|'ratecards'|'handoff'>('timestudy');

  const fetchAll = useCallback(async () => {
    setLoading(true);
    const [rs, rv] = await Promise.all([
      fetch(`${API}/studies/all?tenant_id=tenant-001`),
      fetch(`${API}/sample-versions/all?tenant_id=tenant-001`),
    ]);
    if (rs.ok) { const j = await rs.json(); setStudies(j.data ?? []); }
    if (rv.ok) { const j = await rv.json(); setSvList(j.data ?? []); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // ── derived data ──────────────────────────────────────────────────────────

  const completedStudies = studies.filter(s => s.status === 'completed');
  const rateCards = completedStudies
    .filter(s => s.mean_cycle_time > 0)
    .map(s => ({
      process_id:   s.process_id,
      process_name: s.process_name,
      operator_id:  s.operator_id,
      mean_ms:      s.mean_cycle_time,
      std_dev_ms:   s.std_dev_cycle_time,
      samples:      s.total_cycles,
      cv_pct:       s.std_dev_cycle_time > 0 && s.mean_cycle_time > 0
                      ? (s.std_dev_cycle_time / s.mean_cycle_time) * 100 : 0,
      rate_idr:     rateCard(s.mean_cycle_time, 15),
      reliable:     (s.std_dev_cycle_time / s.mean_cycle_time) < 0.2,
    }));

  const approvedSVs = svList.filter(sv => sv.status === 'approved' || sv.status === 'converted');
  const costingData = approvedSVs.map(sv => {
    const matCost = (sv.materials ?? []).reduce((s, m) => s + (m.total_cost || m.estimated_usage * m.unit_cost), 0);
    const sewCost = (sv.components ?? []).reduce((s, c) => s + (c.rate_card_idr || 0), 0);
    return {
      article_id:     sv.article_id,
      article_name:   sv.article_name,
      client_id:      sv.client_id,
      version:        sv.version_label,
      status:         sv.status,
      material_cost:  matCost,
      sewing_cost:    sewCost,
      total_cost:     matCost + sewCost,
      order_id:       sv.converted_to_order_id || '—',
    };
  });

  // handoff data = approved specs ready to pass to manufacturing
  const handoffData = approvedSVs.map(sv => ({
    article_id:        sv.article_id,
    article_name:      sv.article_name,
    client_id:         sv.client_id,
    version:           sv.version_label,
    status:            sv.status,
    components_count:  sv.components?.length ?? 0,
    materials_count:   sv.materials?.length ?? 0,
    approved_by:       sv.approved_by ?? '—',
    approved_at:       sv.approved_at ? new Date(sv.approved_at).toLocaleDateString('id-ID') : '—',
    order_id:          sv.converted_to_order_id ?? '—',
  }));

  const TABS = [
    { id: 'timestudy', label: 'Studi Waktu' },
    { id: 'ratecards',  label: 'Rate Card' },
    { id: 'costing',    label: 'Estimasi Biaya' },
    { id: 'handoff',    label: 'Handoff Produksi' },
  ] as const;

  // ── summary kpis ─────────────────────────────────────────────────────────

  const kpis = [
    { label: 'Total Studi',      value: studies.length },
    { label: 'Selesai',          value: completedStudies.length },
    { label: 'Rate Card Tersedia', value: rateCards.length },
    { label: 'Siap ke Produksi', value: handoffData.length },
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">Laporan & Handoff Produksi</h2>
          <p className="text-[#6e6e73] text-sm mt-1">Agregat data R&D → acuan mandor & line produksi</p>
        </div>
        <button onClick={fetchAll}
          className="border border-[#d5d5da] bg-white text-[#0066cc] rounded-[10px] px-4 py-2.5 font-semibold text-[13px] hover:bg-[#eaf3fe] inline-flex items-center gap-2">
          <LucideIcon name="activity" className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map(({ label, value }) => (
          <div key={label} className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 text-center">
            <p className="text-xs text-[#6e6e73] uppercase tracking-wider mb-1">{label}</p>
            <p className="text-[30px] font-semibold text-[#1d1d1f]">{value}</p>
          </div>
        ))}
      </div>

      {/* Tab switcher */}
      <div className="bg-white border border-[#e6e6e9] rounded-[18px] overflow-hidden">
        <div className="flex gap-1 p-3 border-b border-[#f0f0f2] overflow-x-auto">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`tab rounded-[9px] px-4 py-2 text-[13px] whitespace-nowrap transition-all ${
                activeTab === t.id ? 'bg-[#eaf3fe] text-[#0066cc] font-semibold' : 'text-[#626269] hover:bg-[#f5f5f7]'
              }`}>{t.label}</button>
          ))}
        </div>

        <div className="p-5">

          {/* Time Study Report */}
          {activeTab === 'timestudy' && (
            <>
              <div className="flex justify-between items-center mb-4">
                <p className="text-[15px] font-semibold text-[#1d1d1f]">Ringkasan Studi Waktu</p>
                <button onClick={() => onExportCSV(studies, 'report_time_studies')}
                  className="border border-[#d5d5da] bg-white text-[#0066cc] rounded-[10px] px-3 py-1.5 text-[12px] font-semibold hover:bg-[#f4f8fd] inline-flex items-center gap-1">
                  <LucideIcon name="download" className="w-3.5 h-3.5" /> Ekspor
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px] border-collapse">
                  <thead>
                    <tr>
                      {['Proses','Status','Siklus','Rata-rata','Std Dev','CV%','Min','Max'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2] whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {studies.map(s => (
                      <tr key={s.study_id} className="border-b border-[#f0f0f2] last:border-0">
                        <td className="px-4 py-3 font-medium text-[#1d1d1f]">{s.process_name}</td>
                        <td className="px-4 py-3">
                          <span className={`pill rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                            s.status==='completed'?'bg-[#e8f5e9] text-[#34c759]':
                            s.status==='in_progress'?'bg-[#fff4e6] text-[#ff9500]':'bg-[#e8f2ff] text-[#0066cc]'
                          }`}>{s.status}</span>
                        </td>
                        <td className="px-4 py-3 font-mono text-[#626269]">{s.total_cycles ?? 0}/{s.target_sample_size}</td>
                        <td className="px-4 py-3 font-mono">{fmtMs(s.mean_cycle_time)}</td>
                        <td className="px-4 py-3 font-mono text-[#6e6e73]">{fmtMs(s.std_dev_cycle_time)}</td>
                        <td className={`px-4 py-3 font-semibold ${
                          s.mean_cycle_time>0 && s.std_dev_cycle_time/s.mean_cycle_time>0.2 ? 'text-[#ff9500]':'text-[#34c759]'
                        }`}>
                          {s.mean_cycle_time > 0 ? fmtPct((s.std_dev_cycle_time/s.mean_cycle_time)*100) : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono text-[#6e6e73]">{fmtMs(s.min_cycle_time)}</td>
                        <td className="px-4 py-3 font-mono text-[#6e6e73]">{fmtMs(s.max_cycle_time)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {studies.length === 0 && <p className="text-center text-[#6e6e73] py-6">Belum ada data studi waktu.</p>}
              </div>
            </>
          )}

          {/* Rate Cards */}
          {activeTab === 'ratecards' && (
            <>
              <div className="flex justify-between items-center mb-4">
                <div>
                  <p className="text-[15px] font-semibold text-[#1d1d1f]">Rate Card per Proses</p>
                  <p className="text-xs text-[#6e6e73] mt-0.5">Hanya studi selesai · Allowance bawaan 15% · IDR {RATE_PER_MIN_IDR}/menit</p>
                </div>
                <button onClick={() => onExportCSV(rateCards, 'rate_cards')}
                  className="border border-[#d5d5da] bg-white text-[#0066cc] rounded-[10px] px-3 py-1.5 text-[12px] font-semibold hover:bg-[#f4f8fd] inline-flex items-center gap-1">
                  <LucideIcon name="download" className="w-3.5 h-3.5" /> Ekspor
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px] border-collapse">
                  <thead>
                    <tr>
                      {['Proses','Operator','Sampel','Rata-rata','CV%','Rate Card','Reliabel'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2] whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rateCards.map((r, i) => (
                      <tr key={i} className="border-b border-[#f0f0f2] last:border-0">
                        <td className="px-4 py-3 font-medium text-[#1d1d1f]">{r.process_name}</td>
                        <td className="px-4 py-3 text-[#6e6e73]">{r.operator_id || '—'}</td>
                        <td className="px-4 py-3 font-mono text-[#6e6e73]">{r.samples}</td>
                        <td className="px-4 py-3 font-mono">{fmtMs(r.mean_ms)}</td>
                        <td className={`px-4 py-3 font-semibold ${r.cv_pct > 20 ? 'text-[#ff9500]' : 'text-[#34c759]'}`}>{fmtPct(r.cv_pct)}</td>
                        <td className="px-4 py-3 font-semibold text-[#0071e3]">{fmtRp(r.rate_idr)}/pcs</td>
                        <td className="px-4 py-3">
                          {r.reliable
                            ? <span className="text-[#34c759] font-semibold text-xs">✓ Ya</span>
                            : <span className="text-[#ff9500] font-medium text-xs">⚠ CV tinggi</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {rateCards.length === 0 && <p className="text-center text-[#6e6e73] py-6">Selesaikan studi waktu terlebih dahulu untuk membuat rate card.</p>}
              </div>
            </>
          )}

          {/* Costing */}
          {activeTab === 'costing' && (
            <>
              <div className="flex justify-between items-center mb-4">
                <div>
                  <p className="text-[15px] font-semibold text-[#1d1d1f]">Estimasi Biaya Produksi</p>
                  <p className="text-xs text-[#6e6e73] mt-0.5">Dari sample version yang sudah disetujui</p>
                </div>
                <button onClick={() => onExportCSV(costingData, 'costing_report')}
                  className="border border-[#d5d5da] bg-white text-[#0066cc] rounded-[10px] px-3 py-1.5 text-[12px] font-semibold hover:bg-[#f4f8fd] inline-flex items-center gap-1">
                  <LucideIcon name="download" className="w-3.5 h-3.5" /> Ekspor
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px] border-collapse">
                  <thead>
                    <tr>
                      {['Artikel','Client','Versi','Bahan','Jahit','Total','Order ID'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-[11px] font-medium text-[#6e6e73] uppercase tracking-wider bg-[#fafafa] border-b border-[#f0f0f2] whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {costingData.map((c, i) => (
                      <tr key={i} className="border-b border-[#f0f0f2] last:border-0">
                        <td className="px-4 py-3 font-medium text-[#1d1d1f]">{c.article_name}</td>
                        <td className="px-4 py-3 text-[#6e6e73]">{c.client_id}</td>
                        <td className="px-4 py-3 font-mono text-xs text-[#6e6e73]">{c.version}</td>
                        <td className="px-4 py-3">{fmtRp(c.material_cost)}</td>
                        <td className="px-4 py-3">{fmtRp(c.sewing_cost)}</td>
                        <td className="px-4 py-3 font-semibold text-[#0071e3]">{fmtRp(c.total_cost)}</td>
                        <td className="px-4 py-3 text-[#6e6e73] text-xs">{c.order_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {costingData.length === 0 && <p className="text-center text-[#6e6e73] py-6">Belum ada sample version yang disetujui.</p>}
              </div>
            </>
          )}

          {/* Handoff */}
          {activeTab === 'handoff' && (
            <>
              <div className="mb-4">
                <p className="text-[15px] font-semibold text-[#1d1d1f]">Data Handoff ke Produksi</p>
                <p className="text-xs text-[#6e6e73] mt-0.5">
                  Artikel yang sudah disetujui dan siap dijadikan acuan mandor & penjahit di line produksi
                </p>
              </div>
              {handoffData.length > 0 ? (
                <div className="space-y-3">
                  {handoffData.map((h, i) => (
                    <div key={i} className={`border rounded-[14px] p-4 ${
                      h.status === 'converted' ? 'border-[#34c759] bg-[#f0fbf4]' : 'border-[#e6e6e9] bg-white'
                    }`}>
                      <div className="flex flex-wrap justify-between items-start gap-3">
                        <div>
                          <p className="font-semibold text-[#1d1d1f]">{h.article_name}</p>
                          <p className="text-xs text-[#6e6e73] mt-0.5">
                            {h.article_id} · Client: {h.client_id} · {h.version}
                          </p>
                        </div>
                        <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-semibold ${
                          h.status === 'converted' ? 'bg-[#e8f5e9] text-[#34c759]' : 'bg-[#e8f2ff] text-[#0066cc]'
                        }`}>{h.status}</span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
                        {[
                          { label: 'Komponen', value: `${h.components_count} bagian` },
                          { label: 'Bahan',    value: `${h.materials_count} item` },
                          { label: 'Disetujui oleh', value: h.approved_by },
                          { label: 'Order ID', value: h.order_id },
                        ].map(({ label, value }) => (
                          <div key={label}>
                            <p className="text-[10px] text-[#6e6e73] uppercase tracking-wider">{label}</p>
                            <p className="text-[13px] font-medium text-[#1d1d1f] mt-0.5">{value}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                  <button onClick={() => onExportCSV(handoffData, 'handoff_production')}
                    className="mt-2 border border-[#d5d5da] bg-white text-[#0066cc] rounded-[10px] px-4 py-2.5 font-semibold text-[13px] inline-flex items-center gap-2 hover:bg-[#f4f8fd]">
                    <LucideIcon name="download" className="w-4 h-4" /> Ekspor Handoff CSV
                  </button>
                </div>
              ) : (
                <div className="text-center text-[#6e6e73] py-10">
                  <p className="text-lg">Belum ada artikel siap handoff.</p>
                  <p className="text-sm mt-1">Selesaikan alur: Buat Sample Version → Ajukan → Setujui → Konversi ke Order.</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportsView;
