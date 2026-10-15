/**
 * TimeStudiesView — create/manage time studies (list + filters + CSV export).
 */
import React from 'react';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import { LucideIcon } from '../components/Sidebar';
import type { TimeStudy, ExportCSV } from '../types';

interface TimeStudiesViewProps {
  studies: TimeStudy[];
  tab: string;
  onTabChange: (id: string) => void;
  search: string;
  onSearchChange: (v: string) => void;
  onCreate: () => void;
  onExportCSV: ExportCSV;
}

const TimeStudiesView: React.FC<TimeStudiesViewProps> = ({
  studies, tab, onTabChange, search, onSearchChange, onCreate, onExportCSV,
}) => (
  <div>
    <div className="flex justify-between items-center mb-6">
      <div>
        <h2 className="text-2xl font-semibold text-ink">Manajemen Studi Waktu</h2>
        <p className="text-ink-muted text-sm mt-1">Buat dan kelola studi waktu per proses produksi</p>
      </div>
      <button onClick={onCreate} className="btn-primary inline-flex items-center gap-2">
        <LucideIcon name="plus" className="w-4 h-4" /> Buat Studi Baru
      </button>
    </div>
    <DataTable
      title="Semua Studi Waktu" subtitle={`${studies.length} studi`}
      tabs={[{id:'all',label:'Semua'},{id:'draft',label:'Draft'},{id:'in_progress',label:'Berjalan'},{id:'paused',label:'Pause'},{id:'completed',label:'Selesai'}]}
      activeTab={tab} onTabChange={onTabChange}
      searchValue={search} onSearchChange={onSearchChange}
      columns={[
        { key:'study_id',    label:'ID',        render: v => <code className="text-xs text-ink-muted">{String(v).substring(0,8)}</code> },
        { key:'process_name', label:'Proses' },
        { key:'status',       label:'Status',   render: v => <StatusBadge status={String(v)} /> },
        { key:'total_cycles', label:'Siklus',   render: (v, row:TimeStudy) => `${Number(v??0)}/${row.target_sample_size}` },
        { key:'mean_cycle_time', label:'Rata-rata (ms)', render: v => Number(v) ? Math.round(Number(v)).toLocaleString('id-ID') : '—' },
        { key:'created_at',   label:'Dibuat',   render: v => new Date(String(v)).toLocaleDateString('id-ID') },
      ]}
      data={studies}
    />
    <div className="mt-4 flex gap-3">
      <button onClick={() => onExportCSV(studies,'time_studies')} className="btn-secondary inline-flex items-center gap-2">
        <LucideIcon name="download" className="w-4 h-4" /> Ekspor CSV
      </button>
    </div>
  </div>
);

export default TimeStudiesView;
