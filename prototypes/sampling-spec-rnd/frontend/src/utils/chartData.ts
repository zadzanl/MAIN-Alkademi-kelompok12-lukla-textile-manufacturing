/**
 * Pure aggregation helpers for the hand-rolled charts (Pareto, Stacked Bar,
 * Waterfall). No React, no DOM, no dependencies — so the geometry can be
 * unit-tested with `node --test` (see tests/chartData.test.ts).
 *
 * KNOWN CEILING (deliberate): these functions normalise their inputs
 * defensively (non-finite -> 0, missing keys -> 0, non-arrays -> []). They are
 * total: they never throw, so a malformed payload degrades to an empty chart
 * instead of crashing the view.
 */

export interface CategoryDatum {
  label: string;
  value: number;
}

export interface ParetoPoint {
  label: string;
  value: number;
  /** Share of the total for this single category, 0–100. */
  sharePct: number;
  /** Running cumulative share, 0–100. */
  cumulativePct: number;
}

export interface StackedRow {
  label: string;
  /** Value per key (missing keys are 0). */
  segments: Record<string, number>;
  /** Sum of all segment values. */
  total: number;
}

export interface WaterfallStep {
  label: string;
  /** Positive/negative delta, or the absolute value when kind === 'total'. */
  delta: number;
  kind?: 'delta' | 'total';
}

export interface WaterfallBar {
  label: string;
  /** Bottom of the floating bar in value space. */
  start: number;
  /** Top of the floating bar in value space. */
  end: number;
  /** Signed value of this step. */
  value: number;
  kind: 'delta' | 'total';
}

function toFinite(n: unknown): number {
  const v = typeof n === 'number' ? n : Number(n);
  return Number.isFinite(v) ? v : 0;
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}

/**
 * Rank categories descending and compute the cumulative share, the classic
 * 80/20 "vital few" view. Non-positive categories are dropped (they carry no
 * signal and would distort the cumulative curve). An empty or all-zero input
 * returns [] so callers can render an empty state.
 */
export function buildPareto(data: CategoryDatum[]): ParetoPoint[] {
  if (!Array.isArray(data)) return [];

  const cleaned = data
    .map(d => ({ label: String(d?.label ?? ''), value: toFinite(d?.value) }))
    .filter(d => d.value > 0)
    .sort((a, b) => (b.value - a.value) || a.label.localeCompare(b.label));

  const total = cleaned.reduce((sum, d) => sum + d.value, 0);
  if (total <= 0) return [];

  let running = 0;
  return cleaned.map(d => {
    running += d.value;
    return {
      label: d.label,
      value: d.value,
      sharePct: round1((d.value / total) * 100),
      cumulativePct: round1((running / total) * 100),
    };
  });
}

/**
 * Turn `[{ label, values }]` into stacked rows for the given keys. Unknown keys
 * in a row are ignored; absent keys become 0. Never throws.
 */
export function buildStacked(
  data: { label: string; values: Record<string, number> }[],
  keys: string[],
): StackedRow[] {
  if (!Array.isArray(data)) return [];
  const safeKeys = Array.isArray(keys) ? keys : [];

  return data.map(row => {
    const values = row?.values ?? {};
    const segments: Record<string, number> = {};
    let total = 0;
    for (const key of safeKeys) {
      const v = toFinite(values[key]);
      segments[key] = v;
      total += v;
    }
    return { label: String(row?.label ?? ''), segments, total };
  });
}

/**
 * Build floating-bar geometry for a waterfall. Each `delta` step starts where
 * the previous ended; a `total` step is anchored to zero (a summary column).
 * An empty input returns [].
 */
export function buildWaterfall(steps: WaterfallStep[]): WaterfallBar[] {
  if (!Array.isArray(steps)) return [];

  let running = 0;
  return steps.map(step => {
    const kind: 'delta' | 'total' = step?.kind === 'total' ? 'total' : 'delta';
    const value = toFinite(step?.delta);
    if (kind === 'total') {
      running = value;
      return { label: String(step?.label ?? ''), start: 0, end: value, value, kind };
    }
    const start = running;
    running += value;
    return { label: String(step?.label ?? ''), start, end: running, value, kind };
  });
}
