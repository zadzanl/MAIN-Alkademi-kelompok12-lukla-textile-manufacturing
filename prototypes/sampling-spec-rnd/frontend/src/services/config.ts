/**
 * config.ts — Single source of truth for API endpoints and data mode.
 *
 * SAMPLING_BASE defaults to the local backend (port 8009). Override with
 * VITE_API_URL, e.g. /api/sampling-spec-rnd to route through the Vite dev proxy.
 *
 * DATA_MODE reflects the ops/ledger/payroll services: they run in "mock"
 * (in-memory) until VITE_LEDGER_MODE=live is set. The sampling endpoints
 * (studies/specs/sample-versions) always talk to the live backend.
 */
/**
 * Vite injects `import.meta.env` in the browser. Under Node (unit tests run via
 * `node --test`) `import.meta.env` is undefined, so read it through this guard to
 * keep the service modules importable outside Vite.
 */
const env: Partial<ImportMetaEnv> = (import.meta as { env?: ImportMetaEnv }).env ?? {};

export const SAMPLING_BASE =
  env.VITE_API_URL || 'http://localhost:8009/api/sampling-spec-rnd';

export const AUTH_BASE =
  env.VITE_AUTH_URL || 'http://localhost:8009/api/auth';

export const LEDGER_BASE = env.VITE_LEDGER_API_URL || '/api/v1';

export const LEDGER_TOKEN = env.VITE_LEDGER_TOKEN || '';

export const DATA_MODE: 'mock' | 'live' =
  env.VITE_LEDGER_MODE === 'live' ? 'live' : 'mock';

export const isMockData = DATA_MODE === 'mock';
