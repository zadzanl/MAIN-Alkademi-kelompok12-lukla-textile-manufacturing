/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_LEDGER_MODE?: string;
  readonly VITE_LEDGER_API_URL?: string;
  readonly VITE_LEDGER_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
