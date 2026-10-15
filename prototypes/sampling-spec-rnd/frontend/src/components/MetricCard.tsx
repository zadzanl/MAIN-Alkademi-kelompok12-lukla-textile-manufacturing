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
  blue:   { border: 'border-t-[3px] border-t-brand', valueCls: 'text-brand dark:text-brand-soft' },
  green:  { border: 'border-t-[3px] border-t-ok', valueCls: 'text-ok-2 dark:text-ok' },
  orange: { border: 'border-t-[3px] border-t-warn', valueCls: 'text-warn-2 dark:text-warn' },
  red:    { border: 'border-t-[3px] border-t-bad', valueCls: 'text-bad-4 dark:text-bad' },
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
      className={`bg-white border border-hair rounded-[18px] p-5 sm:p-6 min-h-[140px] flex flex-col justify-between shadow-sm ${ac?.border ?? ''}`}
    >
      {/* Label — dark, readable */}
      <p className="text-[13px] font-semibold text-ink-2 mb-3 uppercase tracking-wide leading-tight">
        {label}
      </p>

      {/* Value */}
      {loading ? (
        <div className="animate-pulse">
          <div className="h-10 bg-panel-2 rounded-lg w-16 mb-2" />
        </div>
      ) : (
        <p
          className={`text-[40px] font-bold tracking-tight leading-none ${
            ac ? ac.valueCls : 'text-ink'
          }`}
        >
          {value}
        </p>
      )}

      {/* Note — muted but still legible */}
      <p className="text-[12px] text-ink-muted mt-3 leading-snug">{note}</p>
    </article>
  );
};

export default MetricCard;
