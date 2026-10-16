/**
 * StackedBarChart — hand-rolled stacked columns for composition analysis.
 *
 * Each column is one category (e.g. a component code); each segment is one key
 * (e.g. an assembly status). No charting dependency.
 *
 * KNOWN CEILING (deliberate): static render, per-segment value via `title`
 * tooltip only. Renders an empty state instead of throwing on bad data.
 *
 * Dark mode: each key carries a light `color` and optional `darkColor`. Both are
 * exposed as CSS variables and selected via Tailwind's `.dark` class, so no
 * theme prop-drilling is required (mirrors the CSS-variable layer in index.css).
 */

import React from 'react';
import type { StackedRow } from '../utils/chartData';

export interface StackedKey {
  key: string;
  label: string;
  color: string;
  darkColor?: string;
}

const SEGMENT_CLASS = '[background-color:var(--seg-light)] dark:[background-color:var(--seg-dark)]';

const segmentVars = (k: StackedKey): React.CSSProperties => ({
  '--seg-light': k.color,
  '--seg-dark': k.darkColor ?? k.color,
} as React.CSSProperties);

interface StackedBarChartProps {
  data: StackedRow[];
  keys: StackedKey[];
  title: string;
  subtitle: string;
  badge?: string;
}

const CHART_HEIGHT = 180;
const MIN_SEG_H = 2;

const StackedBarChart: React.FC<StackedBarChartProps> = ({
  data,
  keys,
  title,
  subtitle,
  badge = 'Komposisi',
}) => {
  const rows = Array.isArray(data) ? data : [];
  const safeKeys = Array.isArray(keys) ? keys : [];
  const max = Math.max(...rows.map(r => r.total), 0);

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

      {rows.length === 0 || max <= 0 ? (
        <p className="text-center text-ink-muted py-10 text-[13px]">
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
            {rows.map((row, idx) => (
              <div key={`${row.label}-${idx}`} className="flex-1 h-full flex items-end justify-center">
                <div
                  className="w-full max-w-[48px] flex flex-col-reverse rounded-t-[6px] overflow-hidden"
                  title={`${row.label}: ${row.total.toLocaleString('id-ID')}`}
                >
                  {safeKeys.map(k => {
                    const v = row.segments[k.key] ?? 0;
                    if (v <= 0) return null;
                    const h = Math.max(MIN_SEG_H, Math.round((v / max) * CHART_HEIGHT));
                    return (
                      <div
                        key={k.key}
                        className={SEGMENT_CLASS}
                        style={{ height: h, ...segmentVars(k) }}
                        title={`${row.label} · ${k.label}: ${v.toLocaleString('id-ID')}`}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-between gap-2 mt-2">
            {rows.map((row, idx) => (
              <div
                key={`${row.label}-label-${idx}`}
                className="flex-1 text-center text-[11px] text-ink-2 truncate"
                title={row.label}
              >
                {row.label}
              </div>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-4 mt-4 pt-3 border-t border-panel">
            {safeKeys.map(k => (
              <div key={k.key} className="flex items-center gap-1.5">
                <div className={`w-3 h-3 rounded-sm ${SEGMENT_CLASS}`} style={segmentVars(k)} />
                <span className="text-[11px] text-ink-muted">{k.label}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
};

export default StackedBarChart;
