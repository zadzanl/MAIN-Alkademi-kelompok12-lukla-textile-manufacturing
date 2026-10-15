/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_PORTAL_API_URL?: string;
  readonly VITE_PORTAL_AUTH_URL?: string;
  readonly VITE_PORTAL_SCOPE?: string;
  readonly VITE_APP_NAME?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
