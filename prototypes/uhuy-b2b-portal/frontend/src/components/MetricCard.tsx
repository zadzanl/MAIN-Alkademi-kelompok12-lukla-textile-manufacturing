/**
 * MetricCard — KPI display card
 * Fix: high-contrast text — label #374151, value #111827, note #6b7280
 */

import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  note: string;
  loading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  note,
  loading = false,
}) => {
  return (
    <article
      className="bg-white border border-hair rounded-[18px] p-4 sm:p-5 min-h-[140px] flex flex-col justify-between shadow-sm"
    >
      {/* Label — dark, readable */}
      <p className="text-[15px] font-semibold text-ink-2 mb-3 uppercase tracking-wide leading-tight">
        {label}
      </p>

      {/* Value */}
      {loading ? (
        <div className="animate-pulse">
          <div className="h-10 bg-panel-2 rounded-lg w-16 mb-2" />
        </div>
      ) : (
        <p className="text-[44px] font-bold tracking-tight leading-none text-ink">
          {value}
        </p>
      )}

      {/* Note — muted but still legible */}
      <p className="text-[14px] text-ink-muted mt-3 leading-snug">{note}</p>
    </article>
  );
};

export default MetricCard;
