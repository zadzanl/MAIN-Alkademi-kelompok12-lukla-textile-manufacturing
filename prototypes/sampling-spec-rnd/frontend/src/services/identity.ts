/**
 * identity.ts — Single source for tenant / actor identity.
 *
 * Every call used to hardcode `tenant-001`, `admin`, `reviewer-001`, etc. in
 * the page components. Now that the portal auth gate exists, `actor()` reads
 * the signed-in user from the session; the static constants remain as safe
 * fallbacks for unauthenticated/dev contexts.
 *
 * Known ceiling: TENANT_ID is still a fixed placeholder. When multi-tenant
 * sessions land, read it from the actor context too.
 */
import { getActor } from './authSession';

export const TENANT_ID = 'tenant-001';

export const DEFAULT_ACTOR = 'admin';
export const REVIEWER_ID = 'reviewer-001';
export const APPROVER_ID = 'manager-001';

export function actor(): string {
  return getActor()?.displayName ?? DEFAULT_ACTOR;
}
