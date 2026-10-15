/**
 * identity.ts — Single source for tenant / actor identity.
 *
 * Every call used to hardcode `tenant-001`, `admin`, `reviewer-001`, etc. in
 * the page components. Centralising them here means the switch to a real
 * session/JWT (auth phase) is a one-file change instead of a repo-wide sweep.
 *
 * Known ceiling: these are static placeholders until auth lands.
 */
export const TENANT_ID = 'tenant-001';

export const DEFAULT_ACTOR = 'admin';
export const REVIEWER_ID = 'reviewer-001';
export const APPROVER_ID = 'manager-001';

export function actor(): string {
  return DEFAULT_ACTOR;
}
