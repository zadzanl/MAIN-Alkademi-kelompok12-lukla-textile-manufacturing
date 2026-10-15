# Sampling & Spec R&D Frontend

React frontend for time-study recording and specification management in the Lukla Operations Engine. Built with Vite + React 18 + TypeScript + Tailwind CSS, tablet-first, with a semantic token design system and full light/dark theming.

## Quick Start

```bash
npm install
npm run dev          # http://localhost:3009
npm run type-check   # tsc --noEmit
npm run lint         # eslint (0 warnings)
npm test             # node --test
npm run build        # production build -> dist/
npm run preview
```

The dev server runs on **port 3009** and proxies `/api` to the backend on **port 8009** (see `vite.config.ts`).

## Project Structure

```
prototypes/sampling-spec-rnd/frontend/
├── src/
│   ├── components/      # Shared UI (Sidebar, Header, DataTable, MetricCard, Modal, charts, …)
│   ├── pages/           # One file per view (see below)
│   ├── services/        # API clients: api, http, ledgerApi, opsApi, payrollApi, config, identity, toast, problem, query
│   ├── types/           # TypeScript types (index.ts, api.ts)
│   ├── utils/           # chartData.ts, filter.ts
│   ├── lib/             # uuid.ts
│   ├── styles/          # (empty) — global styles live in src/index.css
│   ├── App.tsx          # Layout, routing between views, modals
│   └── main.tsx         # Entry point
├── tests/               # node:test unit/contract tests
├── index.html
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
└── vite.config.ts
```

### Views (`src/pages/`)
`SampleVersionView`, `DigitalStopwatchView`, `ActiveStudiesView`, `ProductionView` (floor terminal),
`StudyListView`, `SpecListView`, `DriftAnalysisView`, `ReportsView`, `QualityView` (QC terminal),
`LedgerView`, `PayrollView`, `FloorTerminalView`, `QcTerminalView`.

## Design System

Single source of truth: **`src/index.css`** (Tailwind layers are declared last to preserve cascade order).

- **Semantic color tokens**: `--c-ink`, `--c-brand`, `--c-ok`, `--c-warn`, `--c-bad`, `--c-panel`, `--c-hair`, … defined in `:root` and overridden under `.dark`. Exposed to Tailwind as `text-ink`, `bg-panel`, `border-hair`, etc. via `tailwind.config.js`.
- **Dark mode**: class strategy — `.dark` is toggled on `<html>` (persisted in `localStorage`).
- **Brand**: Apple-style blue `#0071e3`.
- **Motion**: page-turn navigation (`.page-turn`), sidebar chapter reveal (`.animate-slideDown`), theme cross-fade. Respects `prefers-reduced-motion`.
- **Touch targets**: minimum 48px for factory tablets.

## Backend Integration

- Dev proxy: `/api` → `http://localhost:8009` (`vite.config.ts`).
- Sampling endpoints base: `VITE_API_URL` (default `/api/sampling-spec-rnd`).
- Ledger/ops/payroll services run in **mock mode** by default; set `VITE_LEDGER_MODE=live` plus `VITE_LEDGER_API_URL` and `VITE_LEDGER_TOKEN` for live data (see `src/services/config.ts`).

## Accessibility

- Semantic HTML, `aria-label` on icon-only controls, `role="dialog"` with focus management in `Modal`, visible focus rings, `aria-live` status text, and `sr-only` labels.

## License

Proprietary — Alkademi
