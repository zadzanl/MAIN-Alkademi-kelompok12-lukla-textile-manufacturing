/**
 * query.ts — Pure request-encoding helper (no import.meta / no fetch).
 *
 * Kept dependency-free so the exact query-string rules the sampling client
 * relies on are unit-testable under `node --test`.
 *
 * Rule: drop undefined / null / empty-string; keep false and 0 (they are
 * meaningful for the backend, e.g. is_abnormal=false, cycle_time_ms=0).
 */
export function buildQuery(params?: Record<string, unknown>): string {
  if (!params) return '';
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.append(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : '';
}
