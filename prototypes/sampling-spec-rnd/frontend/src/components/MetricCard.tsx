/**
 * MetricCard Component — KPI Display
 * Matches Garment Backoffice HTML template design
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
    <article className="surface bg-white border border-[#e6e6e9] rounded-[18px] p-5 sm:p-6 min-h-[135px]">
      <p className="text-[#6e6e73] text-sm mb-4">{label}</p>
      
      {loading ? (
        <div className="animate-pulse">
          <div className="h-9 bg-gray-200 rounded w-20 mb-2" />
        </div>
      ) : (
        <p className="kpi-value text-[30px] font-semibold tracking-[-0.045em] leading-tight mb-2">
          {value}
        </p>
      )}
      
      <p className="text-[#6e6e73] text-xs mt-2">{note}</p>
    </article>
  );
};

export default MetricCard;
