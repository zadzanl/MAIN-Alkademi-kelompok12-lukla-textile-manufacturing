/**
 * DataTable — table with tabs, search, filter
 * High-contrast headers + animated tab and row hover
 */
import React from 'react';
import { LucideIcon } from './Sidebar';

interface Tab    { id: string; label: string; }
interface Column { key: string; label: string; render?: (value: any, row: any) => React.ReactNode; }

interface DataTableProps {
  title: string;
  subtitle: string;
  tabs: Tab[];
  activeTab: string;
  onTabChange: (id: string) => void;
  columns: Column[];
  data: any[];
  searchValue: string;
  onSearchChange: (v: string) => void;
  emptyMessage?: string;
}

const DataTable: React.FC<DataTableProps> = ({
  title, subtitle, tabs, activeTab, onTabChange,
  columns, data, searchValue, onSearchChange,
  emptyMessage = 'Tidak ada data yang cocok.',
}) => (
  <section className="surface bg-white border border-[#e2e8f0] rounded-[18px] overflow-hidden mb-4">
    {/* Header row */}
    <div className="p-5 flex flex-col lg:flex-row lg:justify-between gap-4 border-b border-[#f1f5f9]">
      <div>
        <h2 className="text-[16px] font-bold text-[#0f172a]">{title}</h2>
        <p className="text-[12px] font-medium text-[#64748b] mt-0.5">{subtitle}</p>
      </div>
      <div className="relative">
        <LucideIcon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#94a3b8] pointer-events-none" />
        <label htmlFor="tbl-search" className="sr-only">Cari</label>
        <input
          id="tbl-search" type="search"
          placeholder="Cari dalam tabel..."
          value={searchValue}
          onChange={e => onSearchChange(e.target.value)}
          className="pl-9 w-full lg:w-52 rounded-[10px] text-[13px] min-h-[38px]"
        />
      </div>
    </div>

    {/* Tabs */}
    <div role="tablist" aria-label="Filter status" className="flex gap-1 px-4 py-3 overflow-x-auto border-b border-[#f1f5f9]">
      {tabs.map(tab => (
        <button
          key={tab.id} type="button" role="tab"
          aria-selected={activeTab === tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`tab text-[12.5px] px-3 py-1.5 ${activeTab === tab.id ? 'active' : ''}`}
        >
          {tab.label}
        </button>
      ))}
    </div>

    {/* Table */}
    {data.length > 0 ? (
      <div className="overflow-x-auto">
        <table className="w-full text-left text-[13px]">
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col.key} className="px-4 py-3 whitespace-nowrap">{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx}>
                {columns.map(col => (
                  <td key={col.key} className="px-4 py-3 whitespace-nowrap">
                    {col.render ? col.render(row[col.key], row) : (
                      <span className="text-[#334155]">{row[col.key]}</span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <p className="px-5 py-10 text-[13px] font-medium text-[#64748b] text-center">
        {emptyMessage}
      </p>
    )}
  </section>
);

export default DataTable;
