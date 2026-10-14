/**
 * Chart Component — Weekly Bar Chart
 * Matches Garment Backoffice HTML template design
 */

import React from 'react';

interface ChartDataPoint {
  label: string;
  value: number;
  isCurrent?: boolean;
}

interface ChartProps {
  data: ChartDataPoint[];
  title: string;
  subtitle: string;
  badge?: string;
}

const Chart: React.FC<ChartProps> = ({ data, title, subtitle, badge = 'Minggu ini' }) => {
  const maxValue = Math.max(...data.map((d) => d.value), 1);

  return (
    <section className="surface bg-white border border-[#e6e6e9] rounded-[18px] p-5">
      {/* Header */}
      <div className="flex justify-between items-start gap-3 mb-8">
        <div>
          <h2 className="text-[17px] font-semibold tracking-[-0.02em] text-[#1d1d1f]">
            {title}
          </h2>
          <p className="text-[#6e6e73] text-xs mt-1">{subtitle}</p>
        </div>
        <span className="pill blue bg-[#e8f2ff] text-[#0066cc] rounded-full px-2.5 py-1.5 text-[11px] font-semibold whitespace-nowrap">
          {badge}
        </span>
      </div>

      {/* Bar Chart */}
      <div
        className="h-44 flex items-end justify-between gap-3"
        aria-label={title}
        role="img"
      >
        {data.map((point, idx) => {
          const heightPercent = (point.value / maxValue) * 100;
          const heightPx = (point.value / maxValue) * 176; // 176px = 44 * 4 (tailwind h-44)

          return (
            <div
              key={idx}
              className="flex-1 h-full flex flex-col justify-end items-center gap-2"
            >
              {/* Value label */}
              <span className="text-xs text-[#6e6e73] font-medium">
                {point.value}%
              </span>

              {/* Bar */}
              <div
                className={`w-full max-w-12 rounded-t-[5px] rounded-b-[2px] transition-all duration-300 ${
                  point.isCurrent ? 'bg-[#0071e3]' : 'bg-[#c6ddfa]'
                }`}
                style={{ height: `${heightPx}px` }}
                role="presentation"
              />

              {/* Day label */}
              <span className="text-xs text-[#6e6e73]">{point.label}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default Chart;
