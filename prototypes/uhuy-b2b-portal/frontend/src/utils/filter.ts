/**
 * Shared text-match predicate for the header global search and per-table search.
 * A blank query matches everything; otherwise any provided field containing the
 * query (case-insensitive substring) counts as a hit.
 */
export function matchesQuery(query: string, ...fields: (string | undefined | null)[]): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return fields.some(field => (field ?? '').toLowerCase().includes(q));
}
