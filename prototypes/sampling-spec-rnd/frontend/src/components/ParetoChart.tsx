/**
 * ParetoChart — hand-rolled 80/20 chart (bars ranked desc + cumulative line).
 *
 * No charting dependency: bars are divs, the cumulative curve is a responsive
 * SVG polyline (viewBox 0 0 100 100, preserveAspectRatio="none").
 *
 * KNOWN CEILING (deliberate): static render, value shown via `title` tooltip
 * and on-bar label only (no hover/zoom), and no dark-mode variant — it mirrors
 * components/Chart.tsx. Renders an empty state instead of throwing on bad data.
 */

import React from 'react';
import type { ParetoPoint } from '../utils/chartData';

interface ParetoChartProps {
  data: ParetoPoint[];
  title: string;
  subtitle: string;
  badge?: string;
  /** Short unit shown after the raw value, e.g. "cacat". */
  unit?: string;
}

const CHART_HEIGHT = 180;
const MIN_BAR_H = 4;

const ParetoChart: React.FC<ParetoChartProps> = ({
  data,
  title,
  subtitle,
  badge = '80/20',
  unit = '',
}) => {
  const points = Array.isArray(data) ? data : [];
  const max = Math.max(...points.map(p => p.value), 0);

  const polyline = points
    .map((p, i) => {
      const x = ((i + 0.5) / points.length) * 100;
      const y = (1 - p.cumulativePct / 100) * 100;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');

  return (
    <section className="bg-white border border-hair rounded-[18px] p-5 shadow-sm">
      <div className="flex justify-between items-start gap-3 mb-6">
        <div>
          <h2 className="text-[17px] font-semibold text-ink tracking-tight">{title}</h2>
          <p className="text-[12px] text-ink-muted mt-0.5">{subtitle}</p>
        </div>
        <span className="bg-brand-bg-5 text-brand rounded-full px-3 py-1 text-[11px] font-semibold whitespace-nowrap">
          {badge}
        </span>
      </div>

      {points.length === 0 || max <= 0 ? (
        <p className="text-center text-ink-muted py-10 text-[13px]">
          Belum ada data defect untuk dianalisis.
        </p>
      ) : (
        <>
          <div
            className="relative flex items-end justify-between gap-2"
            style={{ height: CHART_HEIGHT }}
            role="img"
            aria-label={title}
          >
            <svg
              className="absolute inset-0 pointer-events-none"
              width="100%"
              height={CHART_HEIGHT}
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <polyline
                points={polyline}
                fill="none"
                stroke="#0071e3"
                strokeWidth="2"
                vectorEffect="non-scaling-stroke"
              />
            </svg>

            {points.map((p, idx) => {
              const barH = Math.max(MIN_BAR_H, Math.round((p.value / max) * CHART_HEIGHT));
              return (
                <div key={`${p.label}-${idx}`} className="relative flex-1 h-full flex items-end justify-center">
                  <span
                    className="absolute text-[11px] font-semibold text-ink-2 whitespace-nowrap"
                    style={{ bottom: barH + 4 }}
                  >
                    {p.value.toLocaleString('id-ID')}{unit ? ` ${unit}` : ''}
                  </span>
                  <div
                    className="w-full max-w-[48px] rounded-t-[6px] rounded-b-[2px] bg-brand"
                    style={{ height: barH, minHeight: MIN_BAR_H }}
                    title={`${p.label}: ${p.value}${unit ? ` ${unit}` : ''} · ${p.sharePct}% · kumulatif ${p.cumulativePct}%`}
                  />
                </div>
              );
            })}
          </div>

          <div className="flex justify-between gap-2 mt-2">
            {points.map((p, idx) => (
              <div
                key={`${p.label}-label-${idx}`}
                className="flex-1 text-center text-[11px] text-ink-2 truncate"
                title={p.label}
              >
                {p.label}
              </div>
            ))}
          </div>

          <div className="flex items-center gap-4 mt-4 pt-3 border-t border-panel">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#0071e3' }} />
              <span className="text-[11px] text-ink-muted">Frekuensi</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-0.5" style={{ backgroundColor: '#0071e3' }} />
              <span className="text-[11px] text-ink-muted">Kumulatif %</span>
            </div>
          </div>
        </>
      )}
    </section>
  );
};

export default ParetoChart;
