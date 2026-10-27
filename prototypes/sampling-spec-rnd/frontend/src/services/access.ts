/**
 * access.ts — Single source of truth for frontend role authorization.
 *
 * Authorization uses EXACT canonical role membership. The legacy `isX` flags in
 * App.tsx accept aliases (e.g. `qc`, `finance`, `owner`) for branding and
 * captions only; they must never grant access or select navigation.
 *
 * Unknown or missing roles are "roleless": they may only reach Settings and
 * Copilot. Copilot is additionally soft-gated server-side.
 */

export const CANONICAL_ROLES = [
  'admin',
  'Owner',
  'Sample',
  'Warehouse',
  'Mandor',
  'Tailor',
  'QCInspector',
  'FinancePayroll',
  'client',
] as const;

export type CanonicalRole = (typeof CANONICAL_ROLES)[number];

/** Roles an Admin IT may assign when approving a registration. `client` is excluded. */
export const ASSIGNABLE_ROLES = [
  'admin',
  'Owner',
  'Sample',
  'Warehouse',
  'Mandor',
  'Tailor',
  'QCInspector',
  'FinancePayroll',
] as const;

export type AssignableRole = (typeof ASSIGNABLE_ROLES)[number];

export type NavKey =
  | 'admin'
  | 'client'
  | 'qc'
  | 'finance'
  | 'owner'
  | 'sample'
  | 'warehouse'
  | 'mandor'
  | 'tailor';

const ROLELESS_VIEWS: readonly string[] = ['settings', 'copilot'];
/** Settings and Copilot are reachable by every role (Copilot is soft-gated server-side). */
const SHARED_VIEWS: readonly string[] = ['settings', 'copilot'];
const ROLELESS_LANDING = 'settings';

const VIEW_MATRIX: Record<CanonicalRole, readonly string[] | 'all'> = {
  admin: 'all',
  client: ['sample-versions', 'production', 'warehouse'],
  QCInspector: ['quality', 'production', 'spec-list'],
  FinancePayroll: ['payroll', 'reports', 'ledger', 'overview'],
  Owner: ['overview', 'reports', 'ledger', 'payroll', 'warehouse', 'spec-versions'],
  Sample: [
    'sample-versions',
    'stopwatch',
    'active-studies',
    'time-studies',
    'study-list',
    'spec-versions',
    'spec-list',
    'drift-analysis',
  ],
  Warehouse: ['warehouse'],
  Mandor: ['production', 'spec-list', 'active-studies'],
  Tailor: ['production'],
};

const LANDING_VIEW: Record<CanonicalRole, string> = {
  admin: 'overview',
  client: 'sample-versions',
  QCInspector: 'quality',
  FinancePayroll: 'payroll',
  Owner: 'overview',
  Sample: 'sample-versions',
  Warehouse: 'warehouse',
  Mandor: 'production',
  Tailor: 'production',
};

const ROLE_LABEL: Record<CanonicalRole, string> = {
  admin: 'Admin IT',
  Owner: 'Owner / Eksekutif',
  Sample: 'Tim Sample',
  Warehouse: 'Gudang / Warehouse',
  Mandor: 'Kepala Produksi / Mandor',
  Tailor: 'Penjahit / Tailor',
  QCInspector: 'QC Inspector',
  FinancePayroll: 'Finance & Payroll',
  client: 'Klien B2B',
};

const NAV_KEY: Record<CanonicalRole, NavKey> = {
  admin: 'admin',
  client: 'client',
  QCInspector: 'qc',
  FinancePayroll: 'finance',
  Owner: 'owner',
  Sample: 'sample',
  Warehouse: 'warehouse',
  Mandor: 'mandor',
  Tailor: 'tailor',
};

/** Exact canonical membership. Aliases such as `qc` or `owner` are NOT known roles. */
export function isKnownRole(role?: string | null): boolean {
  return typeof role === 'string' && (CANONICAL_ROLES as readonly string[]).includes(role);
}

/**
 * Views a role may open. `'all'` means every view. Roleless/unknown roles are
 * limited to Settings and Copilot.
 */
export function allowedViewsForRole(role?: string | null): ReadonlySet<string> | 'all' {
  if (!isKnownRole(role)) return new Set(ROLELESS_VIEWS);
  const views = VIEW_MATRIX[role as CanonicalRole];
  if (views === 'all') return 'all';
  return new Set([...views, ...SHARED_VIEWS]);
}

/** First view shown after login. Roleless/unknown roles land on Settings. */
export function landingViewForRole(role?: string | null): string {
  if (!isKnownRole(role)) return ROLELESS_LANDING;
  return LANDING_VIEW[role as CanonicalRole];
}

/** Human-readable label for the admin role selector. Unknown roles echo back. */
export function roleLabel(role: string): string {
  return isKnownRole(role) ? ROLE_LABEL[role as CanonicalRole] : role;
}

/** Navigation chapter key for a role. `null` means roleless. */
export function navKeyForRole(role?: string | null): NavKey | null {
  if (!isKnownRole(role)) return null;
  return NAV_KEY[role as CanonicalRole];
}
