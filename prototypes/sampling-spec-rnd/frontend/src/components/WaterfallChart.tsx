/**
 * WaterfallChart — hand-rolled floating-bar waterfall for cost accumulation
 * (e.g. base wages → +meal → +bonus → total). No charting dependency.
 *
 * KNOWN CEILING (deliberate): static render, value via on-bar label and `title`
 * tooltip only, no dark-mode variant (mirrors components/Chart.tsx). Renders an
 * empty state instead of throwing on bad data.
 */

import React from 'react';
import type { WaterfallBar } from '../utils/chartData';

interface WaterfallChartProps {
  data: WaterfallBar[];
  title: string;
  subtitle: string;
  badge?: string;
  /** Formats raw values for labels; defaults to Indonesian grouping. */
  formatValue?: (n: number) => string;
}

const CHART_HEIGHT = 180;
const MIN_BAR_H = 3;

const defaultFormat = (n: number) => n.toLocaleString('id-ID');

const WaterfallChart: React.FC<WaterfallChartProps> = ({
  data,
  title,
  subtitle,
  badge = 'Akumulasi',
  formatValue = defaultFormat,
}) => {
  const bars = Array.isArray(data) ? data : [];
  const values = bars.flatMap(b => [b.start, b.end]);
  const maxVal = Math.max(...values, 0);
  const minVal = Math.min(...values, 0);
  const range = maxVal - minVal;

  const barColor = (b: WaterfallBar) => {
    if (b.kind === 'total') return '#1d1d1f';
    return b.value < 0 ? '#ff3b30' : '#0071e3';
  };

  return (
    <section className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 shadow-sm">
      <div className="flex justify-between items-start gap-3 mb-6">
        <div>
          <h2 className="text-[17px] font-semibold text-[#111827] tracking-tight">{title}</h2>
          <p className="text-[12px] text-[#6b7280] mt-0.5">{subtitle}</p>
        </div>
        <span className="bg-[#dbeafe] text-[#1d4ed8] rounded-full px-3 py-1 text-[11px] font-semibold whitespace-nowrap">
          {badge}
        </span>
      </div>

      {bars.length === 0 || range <= 0 ? (
        <p className="text-center text-[#6e6e73] py-10 text-[13px]">
          Belum ada data untuk ditampilkan.
        </p>
      ) : (
        <>
          <div
            className="flex items-end justify-between gap-2"
            style={{ height: CHART_HEIGHT }}
            role="img"
            aria-label={title}
          >
            {bars.map((b, idx) => {
              const lo = Math.min(b.start, b.end);
              const hi = Math.max(b.start, b.end);
              const bottom = ((lo - minVal) / range) * CHART_HEIGHT;
              const height = Math.max(MIN_BAR_H, ((hi - lo) / range) * CHART_HEIGHT);
              const label = b.kind === 'total'
                ? formatValue(b.value)
                : `${b.value >= 0 ? '+' : '−'}${formatValue(Math.abs(b.value))}`;
              return (
                <div key={`${b.label}-${idx}`} className="relative flex-1 h-full flex justify-center">
                  <span
                    className="absolute text-[11px] font-semibold text-[#374151] whitespace-nowrap"
                    style={{ bottom: bottom + height + 4 }}
                  >
                    {label}
                  </span>
                  <div
                    className="absolute w-full max-w-[48px] rounded-[3px]"
                    style={{ bottom, height, backgroundColor: barColor(b) }}
                    title={`${b.label}: ${b.kind === 'total' ? '' : b.value >= 0 ? '+' : '−'}${formatValue(Math.abs(b.value))}`}
                  />
                </div>
              );
            })}
          </div>

          <div className="flex justify-between gap-2 mt-2">
            {bars.map((b, idx) => (
              <div
                key={`${b.label}-label-${idx}`}
                className="flex-1 text-center text-[11px] text-[#374151] truncate"
                title={b.label}
              >
                {b.label}
              </div>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-4 mt-4 pt-3 border-t border-[#f3f4f6]">
            {[
              { color: '#0071e3', label: 'Penambahan' },
              { color: '#ff3b30', label: 'Pengurangan' },
              { color: '#1d1d1f', label: 'Total' },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
                <span className="text-[11px] text-[#6b7280]">{label}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
};

export default WaterfallChart;
