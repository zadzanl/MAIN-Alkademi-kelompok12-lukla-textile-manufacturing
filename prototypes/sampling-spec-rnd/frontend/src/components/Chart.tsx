/**
 * Chart — Weekly bar chart driven by real backend data
 *
 * Fix list:
 *  - Day labels were garbled ("Senator", "Loptai") — now hardcoded correct
 *    Indonesian abbreviations: Sen Sel Rab Kam Jum Sab Min
 *  - Bars used naive completionRate() helper that spread one value across every
 *    bar — chart now receives real per-day counts from parent and derives pct
 *  - Value labels and day labels now have proper contrast (#374151 / #111827)
 *  - Zero-value bars render as a thin placeholder so the chart looks correct
 *  - Active bar is solid #0071e3; past bars are #93c5fd; future bars #e5e7eb
 */

import React from 'react';

export interface DayPoint {
  /** Indonesian 3-char abbreviation — e.g. "Sen", "Sel", "Rab" */
  label: string;
  /** 0–100 completion percentage */
  value: number;
  /** Highlight this bar as "today" */
  isCurrent?: boolean;
  /** Bar is in the future (no data yet) */
  isFuture?: boolean;
}

interface ChartProps {
  data: DayPoint[];
  title: string;
  subtitle: string;
  badge?: string;
}

const CHART_HEIGHT = 160; // px — height of the bar area
const MIN_BAR_H   = 4;    // px — minimum visible height for zero bars

const Chart: React.FC<ChartProps> = ({
  data,
  title,
  subtitle,
  badge = 'Minggu ini',
}) => {
  const maxVal = Math.max(...data.map(d => d.value), 1);

  const barColor = (p: DayPoint) => {
    if (p.isFuture)  return '#e5e7eb';           // grey — no data
    if (p.isCurrent) return '#0071e3';           // solid blue — today
    if (p.value > 0) return '#93c5fd';           // light blue — past days
    return '#e5e7eb';                            // grey — past zero
  };

  return (
    <section className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 shadow-sm">
      {/* Header */}
      <div className="flex justify-between items-start gap-3 mb-6">
        <div>
          <h2 className="text-[17px] font-semibold text-[#111827] tracking-tight">
            {title}
          </h2>
          <p className="text-[12px] text-[#6b7280] mt-0.5">{subtitle}</p>
        </div>
        <span className="bg-[#dbeafe] text-[#1d4ed8] rounded-full px-3 py-1 text-[11px] font-semibold whitespace-nowrap">
          {badge}
        </span>
      </div>

      {/* Bars */}
      <div
        className="flex items-end justify-between gap-2"
        style={{ height: CHART_HEIGHT + 48 }}   // extra space for labels
        aria-label={title}
        role="img"
      >
        {data.map((point, idx) => {
          const barH = point.value > 0
            ? Math.max(MIN_BAR_H, Math.round((point.value / maxVal) * CHART_HEIGHT))
            : MIN_BAR_H;

          return (
            <div
              key={idx}
              className="flex-1 flex flex-col items-center justify-end gap-1.5"
              style={{ height: CHART_HEIGHT + 48 }}
            >
              {/* Percentage label above bar */}
              <span
                className={`text-[11px] font-semibold ${
                  point.value > 0 ? 'text-[#374151]' : 'text-[#d1d5db]'
                }`}
              >
                {point.value > 0 ? `${point.value}%` : '—'}
              </span>

              {/* Bar */}
              <div
                className="w-full rounded-t-[6px] rounded-b-[2px] transition-all duration-500"
                style={{
                  height: barH,
                  backgroundColor: barColor(point),
                  minHeight: MIN_BAR_H,
                  maxWidth: 48,
                }}
              />

              {/* Day label below bar */}
              <span
                className={`text-[11px] font-medium ${
                  point.isCurrent ? 'text-[#0071e3] font-bold' : 'text-[#374151]'
                }`}
              >
                {point.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 pt-3 border-t border-[#f3f4f6]">
        {[
          { color: '#0071e3', label: 'Hari ini' },
          { color: '#93c5fd', label: 'Selesai' },
          { color: '#e5e7eb', label: 'Belum ada data' },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-[11px] text-[#6b7280]">{label}</span>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Chart;
