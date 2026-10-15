/**
 * SpecVersionsView — create/manage spec versions (list + filters + CSV export).
 */
import React from 'react';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import { LucideIcon } from '../components/Sidebar';
import type { SpecVersion, ExportCSV } from '../types';

interface SpecVersionsViewProps {
  specs: SpecVersion[];
  tab: string;
  onTabChange: (id: string) => void;
  search: string;
  onSearchChange: (v: string) => void;
  onCreate: () => void;
  onExportCSV: ExportCSV;
}

const SpecVersionsView: React.FC<SpecVersionsViewProps> = ({
  specs, tab, onTabChange, search, onSearchChange, onCreate, onExportCSV,
}) => (
  <div>
    <div className="flex justify-between items-center mb-6">
      <div>
        <h2 className="text-2xl font-semibold text-ink">Manajemen Versi Spec</h2>
        <p className="text-ink-muted text-sm mt-1">Buat dan kelola spesifikasi teknis produk</p>
      </div>
      <button onClick={onCreate} className="btn-primary inline-flex items-center gap-2">
        <LucideIcon name="plus" className="w-4 h-4" /> Buat Spec Baru
      </button>
    </div>
    <DataTable
      title="Semua Versi Spec" subtitle={`${specs.length} spec version`}
      tabs={[{id:'all',label:'Semua'},{id:'draft',label:'Draft'},{id:'review',label:'Review'},{id:'approved',label:'Disetujui'},{id:'active',label:'Aktif'}]}
      activeTab={tab} onTabChange={onTabChange}
      searchValue={search} onSearchChange={onSearchChange}
      columns={[
        { key:'version_id',    label:'ID',           render: v => <code className="text-xs text-ink-muted">{String(v).substring(0,8)}</code> },
        { key:'spec_name',     label:'Nama Spec' },
        { key:'version_number',label:'Versi' },
        { key:'status',        label:'Status',       render: v => <StatusBadge status={String(v)} /> },
        { key:'total_drifts',  label:'Drifts',       render: v => Number(v ?? 0) },
        { key:'critical_drifts',label:'Kritis',
          render: v => { const n = Number(v); return <span className={n>0?'text-bad font-semibold':''}>{n}</span>; } },
        { key:'created_at',    label:'Dibuat',       render: v => new Date(String(v)).toLocaleDateString('id-ID') },
      ]}
      data={specs}
    />
    <div className="mt-4">
      <button onClick={() => onExportCSV(specs,'spec_versions')} className="btn-secondary inline-flex items-center gap-2">
        <LucideIcon name="download" className="w-4 h-4" /> Ekspor CSV
      </button>
    </div>
  </div>
);

export default SpecVersionsView;
