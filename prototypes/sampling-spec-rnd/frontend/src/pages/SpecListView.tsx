/**
 * SpecListView — Full list of spec versions with action buttons
 */

import React, { useState, useEffect, useCallback } from 'react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import { LucideIcon } from '../components/Sidebar';
import type { SpecVersion, SpecDrift, ExportCSV } from '../types';

const API = 'http://localhost:8009/api/sampling-spec-rnd';

const STATUS_STYLE: Record<string, string> = {
  draft:      'bg-[#e8f2ff] text-[#0066cc]',
  review:     'bg-[#fff4e6] text-[#ff9500]',
  approved:   'bg-[#e8f5e9] text-[#34c759]',
  active:     'bg-[#e8f5e9] text-[#34c759]',
  superseded: 'bg-[#f0f0f2] text-[#626269]',
  archived:   'bg-[#f0f0f2] text-[#626269]',
};

interface Props { onExportCSV: ExportCSV; }

const SpecListView: React.FC<Props> = ({ onExportCSV }) => {
  const [specs, setSpecs]       = useState<SpecVersion[]>([]);
  const [tab, setTab]           = useState('all');
  const [search, setSearch]     = useState('');
  const [selected, setSelected] = useState<SpecVersion | null>(null);
  const [detail, setDetail]     = useState<SpecVersion | null>(null);
  const [actionMsg, setActionMsg] = useState('');

  const fetchAll = useCallback(async () => {
    const r = await fetch(`${API}/specs/all?tenant_id=tenant-001`);
    if (r.ok) { const j = await r.json(); setSpecs(j.data ?? []); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const openDetail = async (spec: SpecVersion) => {
    setSelected(spec);
    const r = await fetch(`${API}/specs/${spec.version_id}/data`);
    if (r.ok) { const j = await r.json(); setDetail(j.data); }
  };

  const doAction = async (spec: SpecVersion, path: string, extra?: Record<string, string>) => {
    const q = extra ? '?' + new URLSearchParams(extra) : '';
    const r = await fetch(`${API}/specs/${spec.version_id}/${path}${q}`, { method: 'POST' });
    const j = await r.json();
    setActionMsg(j.message ?? j.detail ?? '');
    fetchAll();
    setTimeout(() => setActionMsg(''), 3000);
  };

  const filtered = specs.filter(s => {
    if (tab !== 'all' && s.status !== tab) return false;
    if (search && !s.spec_name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">Daftar Versi Spec</h2>
          <p className="text-[#6e6e73] text-sm mt-1">{specs.length} spec version tercatat</p>
        </div>
      </div>

      {actionMsg && (
        <div className="bg-[#e8f5e9] border border-[#34c759] rounded-[10px] px-4 py-2.5 text-[13px] text-[#1a7a34] font-medium">✓ {actionMsg}</div>
      )}

      <DataTable
        title="Semua Spec Version"
        subtitle={`${filtered.length} spec`}
        tabs={[
          { id: 'all',      label: 'Semua' },
          { id: 'draft',    label: 'Draft' },
          { id: 'review',   label: 'Review' },
          { id: 'approved', label: 'Disetujui' },
          { id: 'active',   label: 'Aktif' },
        ]}
        activeTab={tab}
        onTabChange={setTab}
        searchValue={search}
        onSearchChange={setSearch}
        columns={[
          { key: 'spec_id',    label: 'Spec ID' },
          { key: 'spec_name',  label: 'Nama Spec' },
          { key: 'version_number', label: 'Versi' },
          { key: 'status',     label: 'Status',
            render: v => <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-semibold ${STATUS_STYLE[String(v)]??'bg-[#f0f0f2] text-[#626269]'}`}>{String(v)}</span> },
          { key: 'total_drifts',    label: 'Drifts',  render: v => Number(v ?? 0) },
          { key: 'critical_drifts', label: 'Kritis',
            render: v => { const n = Number(v); return <span className={n > 0 ? 'text-[#ff3b30] font-semibold' : ''}>{n}</span>; } },
          { key: 'created_by', label: 'Dibuat oleh', render: v => v ? String(v) : '—' },
          {
            key: 'version_id', label: 'Aksi',
            render: (_, row: SpecVersion) => (
              <div className="flex gap-2 flex-wrap">
                <button onClick={() => openDetail(row)}
                  className="btn-pill btn-pill-gray">
                  Detail
                </button>
                {row.status === 'draft' && (
                  <button onClick={() => doAction(row, 'submit-review', { reviewer_id: 'reviewer-001' })}
                    className="btn-pill btn-pill-orange">
                    Submit Review
                  </button>
                )}
                {row.status === 'review' && (
                  <button onClick={() => doAction(row, 'approve', { approver_id: 'manager-001' })}
                    className="btn-pill btn-pill-green">
                    Setujui
                  </button>
                )}
                {row.status === 'approved' && (
                  <button onClick={() => doAction(row, 'activate')}
                    className="btn-pill btn-pill-dark !bg-[#0071e3]">
                    Aktifkan
                  </button>
                )}
              </div>
            ),
          },
        ]}
        data={filtered}
        emptyMessage="Belum ada spec version. Buat spec baru melalui menu Versi Spec."
      />

      <button onClick={() => onExportCSV(filtered, 'spec_list')}
        className="btn-secondary">
        <LucideIcon name="download" className="w-4 h-4" /> Ekspor CSV
      </button>

      {/* Detail modal */}
      <Modal isOpen={!!selected} title={`Detail Spec — ${selected?.spec_name} v${selected?.version_number}`}
        onClose={() => { setSelected(null); setDetail(null); }}>
        {detail ? (
          <div className="space-y-4 text-[13px]">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Spec ID',      value: detail.spec_id },
                { label: 'Version ID',   value: detail.version_id?.substring(0,12) + '…' },
                { label: 'Status',       value: detail.status },
                { label: 'Dibuat oleh',  value: detail.created_by },
                { label: 'Disetujui oleh', value: detail.approved_by || '—' },
                { label: 'Total Drifts', value: detail.total_drifts ?? 0 },
                { label: 'Critical',     value: detail.critical_drifts ?? 0 },
                { label: 'Catatan',      value: detail.notes || '—' },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-[11px] text-[#6e6e73] uppercase tracking-wider">{label}</p>
                  <p className="font-medium text-[#1d1d1f] mt-0.5">{String(value)}</p>
                </div>
              ))}
            </div>
            {detail.process_steps?.length > 0 && (
              <div>
                <p className="text-[11px] text-[#6e6e73] uppercase tracking-wider mb-1">Langkah Proses</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {detail.process_steps.map((s: string, i: number) => (
                    <li key={i} className="text-[#1d1d1f]">{s}</li>
                  ))}
                </ul>
              </div>
            )}
            {detail.drifts?.length > 0 && (
              <div>
                <p className="text-[11px] text-[#6e6e73] uppercase tracking-wider mb-2">Daftar Drift ({detail.drifts.length})</p>
                {detail.drifts.map((d: SpecDrift) => (
                  <div key={d.drift_id} className={`rounded-[10px] px-3 py-2 mb-2 text-[12px] ${
                    d.severity === 'critical' ? 'bg-[#ffebee] text-[#ff3b30]' :
                    d.severity === 'high'     ? 'bg-[#fff4e6] text-[#ff9500]' : 'bg-[#f5f5f7] text-[#626269]'
                  }`}>
                    <span className="font-semibold">{d.parameter_name}</span>: limit {d.specification_limit} → measured {d.measured_value} ({d.deviation_percent?.toFixed(1)}% dev) · {d.severity}
                    {d.resolved && <span className="ml-2 text-[#34c759] font-semibold">✓ Resolved</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="text-[#6e6e73] text-sm text-center py-4">Memuat data…</p>
        )}
      </Modal>
    </div>
  );
};

export default SpecListView;

