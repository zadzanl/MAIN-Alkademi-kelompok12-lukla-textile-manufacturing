/**
 * problem.ts — Pure error-body parsing (no fetch / no import.meta).
 *
 * Normalises the error shapes this codebase produces into one readable string:
 *   - FastAPI HTTPException: { "detail": "..." }
 *   - FastAPI validation:    { "detail": [ { loc, msg }, ... ] }
 *   - Lukla RFC 7807:        { "code": "...", "detail": "...", "title": "..." }
 *   - plain-text / non-JSON bodies
 *
 * Kept dependency-free so it is unit-testable under `node --test`.
 */
export function extractDetail(raw: unknown, status: number): string {
  if (typeof raw === 'string' && raw.trim()) return raw;

  if (raw && typeof raw === 'object') {
    const problem = raw as { detail?: unknown; title?: unknown };
    const detail = problem.detail ?? problem.title;

    if (typeof detail === 'string' && detail.trim()) return detail;

    if (Array.isArray(detail)) {
      const messages = detail.map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          const entry = item as { loc?: unknown; msg?: unknown };
          const loc = Array.isArray(entry.loc) ? entry.loc.join('.') : '';
          const msg = String(entry.msg);
          return loc ? `${loc}: ${msg}` : msg;
        }
        return String(item);
      });
      if (messages.length) return messages.join('; ');
    }
  }

  return `HTTP ${status}`;
}
