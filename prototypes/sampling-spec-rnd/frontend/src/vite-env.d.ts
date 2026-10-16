/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  /** Signed JWT accepted by the root Lukla API for Copilot tool calls. */
  readonly VITE_COPILOT_TOKEN?: string;
  readonly VITE_LEDGER_MODE?: string;
  readonly VITE_LEDGER_API_URL?: string;
  readonly VITE_LEDGER_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
