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
  accent?: 'blue' | 'green' | 'orange' | 'red';
}

const ACCENT: Record<string, { border: string; valueCls: string }> = {
  blue:   { border: 'border-t-[3px] border-t-[#0071e3]', valueCls: 'text-[#0071e3]' },
  green:  { border: 'border-t-[3px] border-t-[#34c759]', valueCls: 'text-[#1a7a34]' },
  orange: { border: 'border-t-[3px] border-t-[#ff9500]', valueCls: 'text-[#b86800]' },
  red:    { border: 'border-t-[3px] border-t-[#ff3b30]', valueCls: 'text-[#cc2200]' },
};

const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  note,
  loading = false,
  accent,
}) => {
  const ac = accent ? ACCENT[accent] : null;

  return (
    <article
      className={`bg-white border border-[#e6e6e9] rounded-[18px] p-5 sm:p-6 min-h-[140px] flex flex-col justify-between shadow-sm ${ac?.border ?? ''}`}
    >
      {/* Label — dark, readable */}
      <p className="text-[13px] font-semibold text-[#374151] mb-3 uppercase tracking-wide leading-tight">
        {label}
      </p>

      {/* Value */}
      {loading ? (
        <div className="animate-pulse">
          <div className="h-10 bg-[#e5e7eb] rounded-lg w-16 mb-2" />
        </div>
      ) : (
        <p
          className={`text-[40px] font-bold tracking-tight leading-none ${
            ac ? ac.valueCls : 'text-[#111827]'
          }`}
        >
          {value}
        </p>
      )}

      {/* Note — muted but still legible */}
      <p className="text-[12px] text-[#6b7280] mt-3 leading-snug">{note}</p>
    </article>
  );
};

export default MetricCard;
