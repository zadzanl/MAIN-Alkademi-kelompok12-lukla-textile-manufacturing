/**
 * DataTable Component — Reusable Table with Tabs, Search, and Filters
 * Matches Garment Backoffice HTML template design
 */

import React from 'react';
import { LucideIcon } from './Sidebar';

interface Tab {
  id: string;
  label: string;
}

interface Column {
  key: string;
  label: string;
  render?: (value: any, row: any) => React.ReactNode;
}

interface DataTableProps {
  title: string;
  subtitle: string;
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  columns: Column[];
  data: any[];
  searchValue: string;
  onSearchChange: (value: string) => void;
  emptyMessage?: string;
}

const DataTable: React.FC<DataTableProps> = ({
  title,
  subtitle,
  tabs,
  activeTab,
  onTabChange,
  columns,
  data,
  searchValue,
  onSearchChange,
  emptyMessage = 'Tidak ada data yang cocok dengan filter.',
}) => {
  return (
    <section className="surface bg-white border border-[#e6e6e9] rounded-[18px] mb-4 overflow-hidden">
      {/* Header */}
      <div className="p-5 flex flex-col lg:flex-row lg:justify-between gap-4">
        <div>
          <h2 className="text-[17px] font-semibold tracking-[-0.02em] text-[#1d1d1f]">
            {title}
          </h2>
          <p className="text-[#6e6e73] text-xs mt-1">{subtitle}</p>
        </div>

        {/* Search */}
        <div className="relative">
          <LucideIcon
            name="search"
            className="absolute left-3 top-3 w-4 h-4 text-[#86868b] pointer-events-none"
          />
          <label htmlFor="table-search" className="sr-only">
            Cari dalam tabel
          </label>
          <input
            id="table-search"
            type="search"
            placeholder="Cari dalam tabel..."
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="field pl-9 w-full lg:w-56 bg-white border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] min-h-[41px] focus:outline-2 focus:outline-[#80baff]"
          />
        </div>
      </div>

      {/* Tabs */}
      <div
        role="tablist"
        aria-label="Filter status"
        className="flex gap-1 px-4 pb-3 overflow-x-auto"
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`tab px-3 py-2 rounded-[9px] text-[13px] whitespace-nowrap transition-all ${
              activeTab === tab.id
                ? 'active bg-[#eaf3fe] text-[#0066cc] font-semibold'
                : 'text-[#626269] hover:bg-[#f5f5f7]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Table */}
      {data.length > 0 ? (
        <div className="table-wrap overflow-x-auto">
          <table className="w-full border-collapse text-left text-[13px]">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className="text-[#77777d] font-medium text-[11px] tracking-[.035em] uppercase bg-[#fafafa] px-4 py-3.5 border-b border-[#f0f0f2] whitespace-nowrap"
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => (
                <tr key={idx}>
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className="px-4 py-3.5 border-b border-[#f0f0f2] whitespace-nowrap last:border-b-0"
                    >
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="px-5 py-8 text-[#6e6e73] text-sm text-center">
          {emptyMessage}
        </p>
      )}
    </section>
  );
};

export default DataTable;
