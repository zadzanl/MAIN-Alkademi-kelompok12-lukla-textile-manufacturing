/**
 * config.ts — Single source of truth for the UHUY B2B EXTERNAL portal.
 *
 * PORTAL_BASE points at the dedicated external-portal backend (port 8010),
 * separate from the internal Sampling & Spec R&D backend (port 8009). Override
 * with VITE_PORTAL_API_URL / VITE_PORTAL_AUTH_URL, e.g. relative paths to route
 * through the Vite dev proxy.
 *
 * PORTAL_SCOPE marks this build as the external portal. The internal dashboard
 * uses "internal"; every UHUY B2B screen carries the external marker.
 */
/**
 * Vite injects `import.meta.env` in the browser. Under Node (unit tests run via
 * `node --test`) `import.meta.env` is undefined, so read it through this guard to
 * keep the service modules importable outside Vite.
 */
const env: Partial<ImportMetaEnv> = (import.meta as { env?: ImportMetaEnv }).env ?? {};

export const PORTAL_BASE =
  env.VITE_PORTAL_API_URL || 'http://localhost:8010/api/portal';

export const PORTAL_AUTH_BASE =
  env.VITE_PORTAL_AUTH_URL || 'http://localhost:8010/api/portal/auth';

export const PORTAL_SCOPE: 'external' | 'internal' =
  env.VITE_PORTAL_SCOPE === 'internal' ? 'internal' : 'external';

export const isExternalPortal = PORTAL_SCOPE === 'external';

export const APP_NAME = env.VITE_APP_NAME || 'Portal Klien UHUY B2B';
