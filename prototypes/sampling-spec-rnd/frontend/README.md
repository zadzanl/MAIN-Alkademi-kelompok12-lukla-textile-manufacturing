# Sampling & Spec R&D Frontend

React frontend for time-study recording and specification management in the Lukla Operations Engine. Built with Vite + React 18 + TypeScript + Tailwind CSS, tablet-first, with a semantic token design system and full light/dark theming.

## Advisory browser smoke

This repository includes one non-blocking Playwright Chromium smoke. It starts the
FastAPI backend on `127.0.0.1:8009` and Vite on `127.0.0.1:3009`; both ports must be
free. The smoke is read-only and does not create production data. It intentionally
exposes the current missing `src/pages/SpecVersionPage.tsx` import instead of
repairing application code, so a failed smoke is valid evidence of that existing
application defect.

### Prerequisites

- Node.js 20 or newer (the pinned Playwright version requires Node 20+).
- Python 3.11, or another Python version supported by the pinned backend requirements.
- A local virtual environment; do not install the prototype's backend dependencies globally.

### Windows PowerShell

```powershell
cd prototypes\sampling-spec-rnd\backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\Activate.ps1

cd ..\frontend
npm ci
npx playwright install chromium
npm run test:e2e
```

### Linux/macOS

```bash
cd prototypes/sampling-spec-rnd/backend
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
source .venv/bin/activate

cd ../frontend
npm ci
npx playwright install chromium
npm run test:e2e
```

On Linux, install browser system dependencies with `npx playwright install --with-deps chromium`
if needed. This may require administrator access; CI performs this step on its disposable runner.

`npm run test:e2e` owns both services and stops them when it exits. Do not start
another copy first. `npm run test:e2e -- --list` should list exactly one Chromium
test without starting the services. Reports are written to `playwright-report/` and
failure artifacts to `test-results/`; both are ignored by Git.

The smoke is advisory. A nonzero Playwright exit is retained as failure evidence;
the GitHub job is configured with `continue-on-error: true`. Do not add this advisory
check to required branch rules; repository rules can independently affect merge eligibility.
Open the local report with `npx playwright show-report`. Reports expire after seven
days in CI; startup failures may leave only workflow logs, without browser artifacts.
Use only local test services without production data or secrets in captured reports.
For pre-commit user-visible verification, use an available interactive
browser tool first; otherwise run this automated smoke, and mark verification
unverified if neither option is available. This setup does not replace production
monitoring or a full browser test suite.

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

Lukla Operations Engine
