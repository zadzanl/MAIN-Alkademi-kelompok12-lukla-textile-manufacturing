/**
 * StudyListView — Full list of all time studies with stats + export
 */

import React, { useState, useEffect, useCallback } from 'react';
import DataTable from '../components/DataTable';
import { LucideIcon } from '../components/Sidebar';
import type { TimeStudy, ExportCSV } from '../types';
import * as api from '../services/api';
import { TENANT_ID } from '../services/identity';
import { matchesQuery } from '../utils/filter';

const fmtMs = (ms: number) => ms ? `${Math.round(ms).toLocaleString('id-ID')} ms` : '—';

const STATUS_STYLE: Record<string, string> = {
  draft:       'bg-brand-bg text-brand',
  in_progress: 'bg-ok-bg text-ok',
  paused:      'bg-warn-bg text-warn',
  completed:   'bg-panel-2 text-ink-muted',
  archived:    'bg-panel-2 text-ink-muted',
};

interface Props { onExportCSV: ExportCSV; globalSearch?: string; }

const StudyListView: React.FC<Props> = ({ onExportCSV, globalSearch = '' }) => {
  const [studies, setStudies] = useState<TimeStudy[]>([]);
  const [tab, setTab]         = useState('all');
  const [search, setSearch]   = useState('');

  const fetchAll = useCallback(async () => {
    const res = await api.listStudies(TENANT_ID);
    if (res.success && res.data) setStudies(res.data);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const filtered = studies.filter(s =>
    (tab === 'all' || s.status === tab) &&
    matchesQuery(search, s.process_name, s.process_id) &&
    matchesQuery(globalSearch, s.process_name, s.process_id)
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-ink">Daftar Studi Waktu</h2>
          <p className="text-ink-muted text-sm mt-1">{studies.length} total studi waktu tercatat</p>
        </div>
        <button onClick={fetchAll}
          className="btn-secondary">
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
          { key: 'study_id',     label: 'ID',         render: v => <code className="text-xs text-ink-muted">{String(v).substring(0,8)}</code> },
          { key: 'process_name', label: 'Proses' },
          { key: 'operator_id',  label: 'Operator',   render: v => v ? String(v) : '—' },
          { key: 'status',       label: 'Status',
            render: v => <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-semibold ${STATUS_STYLE[String(v)]??'bg-panel-2 text-ink-muted'}`}>{String(v)}</span> },
          { key: 'total_cycles', label: 'Siklus',     render: (v, row: TimeStudy) => `${Number(v ?? 0)}/${row.target_sample_size}` },
          { key: 'mean_cycle_time', label: 'Rata-rata', render: v => fmtMs(Number(v)) },
          { key: 'std_dev_cycle_time', label: 'Std. Dev', render: v => fmtMs(Number(v)) },
          { key: 'created_at',   label: 'Dibuat',
            render: v => new Date(String(v)).toLocaleDateString('id-ID') },
        ]}
        data={filtered}
        emptyMessage="Tidak ada studi yang cocok. Buat studi baru melalui menu Studi Waktu atau Stopwatch."
      />

      <button onClick={() => onExportCSV(filtered, 'study_list')}
        className="btn-secondary">
        <LucideIcon name="download" className="w-4 h-4" /> Ekspor CSV
      </button>
    </div>
  );
};

export default StudyListView;

