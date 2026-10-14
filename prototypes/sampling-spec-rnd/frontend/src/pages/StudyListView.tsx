/**
 * StudyListView — Full list of all time studies with stats + export
 */

import React, { useState, useEffect, useCallback } from 'react';
import DataTable from '../components/DataTable';
import { LucideIcon } from '../components/Sidebar';
import type { TimeStudy } from '../types';

const API = 'http://localhost:8009/api/sampling-spec-rnd';

const fmtMs = (ms: number) => ms ? `${Math.round(ms).toLocaleString('id-ID')} ms` : '—';

const STATUS_STYLE: Record<string, string> = {
  draft:       'bg-[#e8f2ff] text-[#0066cc]',
  in_progress: 'bg-[#e8f5e9] text-[#34c759]',
  paused:      'bg-[#fff4e6] text-[#ff9500]',
  completed:   'bg-[#f0f0f2] text-[#626269]',
  archived:    'bg-[#f0f0f2] text-[#626269]',
};

interface Props { onExportCSV: (data: any[], filename: string) => void; }

const StudyListView: React.FC<Props> = ({ onExportCSV }) => {
  const [studies, setStudies] = useState<TimeStudy[]>([]);
  const [tab, setTab]         = useState('all');
  const [search, setSearch]   = useState('');
  const [loading, setLoading] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/studies/all?tenant_id=tenant-001`);
      if (r.ok) { const j = await r.json(); setStudies(j.data ?? []); }
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const filtered = studies.filter(s => {
    if (tab !== 'all' && s.status !== tab) return false;
    if (search && !s.process_name.toLowerCase().includes(search.toLowerCase()) &&
        !s.process_id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">Daftar Studi Waktu</h2>
          <p className="text-[#6e6e73] text-sm mt-1">{studies.length} total studi waktu tercatat</p>
        </div>
        <button onClick={fetchAll}
          className="border border-[#d5d5da] bg-white text-[#0066cc] rounded-[10px] px-4 py-2.5 font-semibold text-[13px] hover:bg-[#eaf3fe] inline-flex items-center gap-2">
          <LucideIcon name="activity" className="w-4 h-4" /> Refresh
        </button>
      </div>

      <DataTable
        title="Semua Studi Waktu"
        subtitle={`${filtered.length} studi`}
        tabs={[
          { id: 'all',         label: 'Semua' },
          { id: 'draft',       label: 'Draft' },
          { id: 'in_progress', label: 'Berjalan' },
          { id: 'paused',      label: 'Pause' },
          { id: 'completed',   label: 'Selesai' },
        ]}
        activeTab={tab}
        onTabChange={setTab}
        searchValue={search}
        onSearchChange={setSearch}
        columns={[
          { key: 'study_id',     label: 'ID',         render: v => <code className="text-xs text-[#6e6e73]">{v.substring(0,8)}</code> },
          { key: 'process_name', label: 'Proses' },
          { key: 'operator_id',  label: 'Operator',   render: v => v || '—' },
          { key: 'status',       label: 'Status',
            render: v => <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-semibold ${STATUS_STYLE[v]??'bg-[#f0f0f2] text-[#626269]'}`}>{v}</span> },
          { key: 'total_cycles', label: 'Siklus',     render: (v, row: TimeStudy) => `${v??0}/${row.target_sample_size}` },
          { key: 'mean_cycle_time', label: 'Rata-rata', render: v => fmtMs(v) },
          { key: 'std_dev_cycle_time', label: 'Std. Dev', render: v => fmtMs(v) },
          { key: 'created_at',   label: 'Dibuat',
            render: v => new Date(v).toLocaleDateString('id-ID') },
        ]}
        data={filtered}
        emptyMessage="Tidak ada studi yang cocok. Buat studi baru melalui menu Studi Waktu atau Stopwatch."
      />

      <button onClick={() => onExportCSV(filtered, 'study_list')}
        className="border border-[#d5d5da] bg-white text-[#0066cc] rounded-[10px] px-4 py-2.5 font-semibold text-[13px] inline-flex items-center gap-2 hover:bg-[#f4f8fd]">
        <LucideIcon name="download" className="w-4 h-4" /> Ekspor CSV
      </button>
    </div>
  );
};

export default StudyListView;
