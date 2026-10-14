# Research — Stale Next.js References in OpenSpec Documentation

**Date:** 2026-10-14
**Role:** Read-only Explorer (orchestration mode)
**Scope:** Inventory every repository-owned reference to Next.js in `c:\Projects\hackathon-MAIN-alkademi`, verify the active runtime, and produce a complete target-file list for the proposed cleanup. **No source files were modified by this audit.**
**Verification mode:** Read-only — no edits, no installs, no commands beyond `rg` / `Get-Content` / `git status` / `git log`. Output = planning artifact.

---

## 1. Verification of Active Runtime

The repository has **no top-level `package.json`** and **no `monorepo` workspace marker**. The only React-style frontend in the tree is a single prototype. It declares and uses **Vite + React 18 + TypeScript + Tailwind**, and exposes zero Next.js in dependencies, scripts, or config.

| Evidence | Path | Lines | Verified reading |
|---|---|---|---|
| Manifest | `prototypes/sampling-spec-rnd/frontend/package.json` | #L6-L11 | `"scripts": { "dev": "vite", "build": "tsc && vite build", "preview": "vite preview" }` |
| Manifest | `prototypes/sampling-spec-rnd/frontend/package.json` | #L12-L32 | `react ^18.2.0`, `react-dom ^18.2.0`, `@vitejs/plugin-react ^4.0.0`, `vite ^4.4.0`, `typescript ^5.1.0`, `tailwindcss ^3.3.0`; no `next` entry |
| Vite config | `prototypes/sampling-spec-rnd/frontend/vite.config.ts` | #L1-L2 | `import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react';` |
| Entry | `prototypes/sampling-spec-rnd/frontend/src/main.tsx` | #L9 | `ReactDOM.createRoot(rootElement).render(<.../>)` — pure client render, no Next.js provider |
| Type ambient | `prototypes/sampling-spec-rnd/frontend/src/vite-env.d.ts` | #L1-L4 | `<reference types="vite/client" />`; declares `VITE_API_URL`, **not** `NEXT_PUBLIC_*` |
| HTML shell | `prototypes/sampling-spec-rnd/frontend/index.html` | n/a | Vite root `index.html` exists; no `app/layout.tsx`, no `_app.tsx`, no `_document.tsx` |
| README | `prototypes/sampling-spec-rnd/frontend/README.md` | #L53, #L192 | "vite.config.ts", "Proxy configured in vite.config.ts" |
| README | `prototypes/sampling-spec-rnd/frontend/README.md` | #L43-L87 | "React 18 + Vite + Tailwind (Port 3009)" documented |
| Vite proxy | `prototypes/sampling-spec-rnd/frontend/src/services/api.ts` | #L6-L7 | `import.meta.env.VITE_API_URL` (Vite convention) |
| Build artifact hygiene | root | n/a | `Test-Path .next` → false; `Test-Path next.config.{js,mjs}` → false |

**Operating fact (Verified):** the repository's only runnable runtime is Vite. Next.js is referenced **exclusively in OpenSpec planning docs, an archived PRD draft, and one SVG diagram**.

---

## 2. Inventory of Next.js Framework References

### 2.1 `.gitignore` (root, anchored, applied repo-wide — affects everything)

The top section imports the GitHub `Nextjs.gitignore` template verbatim, including patterns that have meaning only in a Next.js project.

[code: .gitignore#L1-L14]
- `# Next.js / Node.js`  ← header
- `/.next/`              ← Next.js build cache directory
- `/out/`                ← Next.js static export output
- `/.vercel`             ← Vercel deploy artifacts
- `next-env.d.ts`        ← Next.js type-ambient (generated)

[code: .gitignore#L31-L32]
- `/build/`              ← Vite's build output directory (matches Next.js pattern by coincidence; safe to keep **only if anchored to frontend**)

**Action category:** A — must be revised. Anchored patterns `/build/`, `/.next/`, `/out/`, `/.vercel`, `next-env.d.ts` are stale in a Vite-only repo.

### 2.2 Plant-layout ADR (active deliverable)

[code: openspec/changes/lukla-ops-engine-planning/10-technology-stack-and-decisions.md#L23]
- Row in §2: `| Web | Responsive Next.js PWA, output: standalone | standard browser APIs; Vercel, CloudFront/Amplify, or a container can host it | No Edge-only, ISR-write, or Vercel-only API |`

**Action category:** A — must be revised. This is the stack ADR and currently declares Next.js as the chosen web framework.

### 2.3 Frontend architecture doc

[code: openspec/changes/lukla-ops-engine-planning/14-frontend-architecture.md#L12]
- `- [stack] artifacts/10-technology-stack-and-decisions.md, §2 Web portability (Next.js, output: standalone, no Vercel-only API).`

[code: openspec/changes/lukla-ops-engine-planning/14-frontend-architecture.md#L20]
- `PROPOSAL: use a responsive Next.js web application with a framework-neutral data-access layer and output: 'standalone'. No Vercel-only server action, Edge runtime, ISR write, or image-optimization dependency is required.`

**Action category:** A — must be revised. Two hard references to Next.js and `output: 'standalone'`.

### 2.4 Phase completion plan (parent)

[code: openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md#L32]
- `- Next.js portability: use output: 'standalone'; avoid Vercel-only features …`

[code: openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md#L38]
- `existing reused: … design_guideline.md (Apple HIG + Next.js structure) …`

[code: openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md#L65]
- `Next.js output: 'standalone', no Vercel-only APIs.`

[code: openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md#L77]
- `A1. Artifact 10 (10-technology-stack-and-decisions.md): Stack ADRs (FastAPI + PostgreSQL + Next.js), forbidden-API list, portability matrix.`

[code: openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md#L84]
- `B2. Artifact 14 (14-frontend-architecture.md): 6 view route maps, Next.js App Router, offline PWA tally queue …`

**Action category:** A — must be revised (parent document references must align with downstream artifacts before Phase D).

### 2.5 Design guideline artifact (active frontend structure doc)

[code: openspec/changes/lukla-ops-engine-planning/artifacts/design_guideline.md#L26]
- `## 3. STRUKTUR FRONTEND (React / Next.js)`

[code: openspec/changes/lukla-ops-engine-planning/artifacts/design_guideline.md#L28]
- `Kita akan menggunakan Next.js (App Router) dengan Tailwind CSS dan komponen berbasis Radix UI/shadcn …`

[code: openspec/changes/lukla-ops-engine-planning/artifacts/design_guideline.md#L32]
- `├── /app                   # Next.js App Router (Halaman Utama)`

**Action category:** A — must be revised. Section header, body sentence, and directory-tree label all declare Next.js App Router.

### 2.6 SVG architecture diagram (binary mermaid export)

[code: openspec/changes/lukla-ops-engine-planning/artifacts/struktur diagram Backend&frontend Lukla.svg]
- Single hex-encoded `<foreignObject>` node-label inside the exported Mermaid SVG: `<span class="nodeLabel"><p>📁 /app (Next.js App Router)</p></span>`. Visual node-id `app`, positioned at `transform="translate(354.1624984741211, 1193)"`.
- File mtime 13/10/2026 15:05:30 (post-Phase-1-A). A duplicate of the same diagram in compressed form is at `artifacts/DEPRECATED/mermaid-flowchart-2026-10-12T08-44-23.svg` (mtime 12/10/2026 15:44:24).

**Action category:** A — must be revised. SVG is generated from a Mermaid source; the canonical editable form is the Mermaid `%%{init:…} graph TD …` block in `archive/PRD Draft - Lukla Operations Engine - v1.3.md#L73`. The SVG itself can either be hand-edited as a one-liner label change OR be re-exported from Mermaid source — both are valid. **ASK user** which path.

### 2.7 Archived PRD draft (historical)

[code: openspec/changes/lukla-ops-engine-planning/archive/PRD Draft - Lukla Operations Engine - v1.3.md#L71]
- `### 3.2 Struktur Frontend & Backend (React / [Next.js](http://Next.js))`

[code: openspec/changes/lukla-ops-engine-planning/archive/PRD Draft - Lukla Operations Engine - v1.3.md#L73]
- Encoded Mermaid `%%{init: {'themeVariables': { 'fontSize': '11px' }}}%%graph TD subgraph Frontend [Frontend - Next.js] src1[/src] --> app[/app (Router)] …`. The text "Next.js" appears twice (`Frontend - Next.js` and inside the directory label).

**Action category:** B — historical preservation recommended if the archive is a frozen-by-design snapshot of the project's ideation phase. The task explicitly states "preserve existing user changes" and "state unknown behavior decisions, especially historical preservation." The AGENTS.md does not assert the archive is immutable, but it is under `archive/`, which is a strong convention. **ASK user** before editing `/archive/`.

### 2.8 Phase 6 research — deployment platform (active research evidence)

[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-platform-001.md#L44]
[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-platform-001.md#L157]
[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-platform-001.md#L159-L161]
[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-platform-001.md#L254]
[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-platform-001.md#L268]
[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-platform-001.md#L312-L313]
[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-platform-001.md#L329]

Coverage:
- `L44` — verification table row V14: "Next.js `output: 'standalone'` portability …"
- `L157` — section header `### V14 — Next.js standalone + AWS portability (verified)`
- `L159-L161` — three cited source URLs:
  - `https://www.ravion.com/docs/deploy/aws/nextjs`
  - `https://www.brandrums.com/blog/how-to-deploy-nextjs-on-aws-2026/`
  - `https://opennext.js.org/`
- `L254` — open-items table: "Next.js 16 standalone support on AWS Amplify"
- `L268` — recommendation: "Decide Next.js version pin now …"
- `L312-L313` — source-URL list (Brandrums, Ravion)
- `L329` — appendices: "Which Next.js major version to pin (16 needs re-verification of standalone on Amplify)"

**Action category:** B — research evidence should be **preserved as-is** with a short header note explaining it is no longer the chosen stack. The sources cited are real and useful for the reader who considers re-pivoting to Next.js. **ASK user.**

### 2.9 Phase 6 research — boundaries (active research evidence)

[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-boundaries-001.md#L59]
- Verification table row W9: "Next.js 16 standalone output AWS Amplify CloudFront S3 portability Vercel-only"

[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-boundaries-001.md#L134]
- Boundaries table: "Frontend deploy | Next.js `output: 'standalone'` for portability. AWS path = Amplify Hosting (SSG/SSR documented) or OpenNext → Lambda/ECS. Avoid Vercel-only APIs (default Image Optimization loader, ISR writes, Edge runtime)."

[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-boundaries-001.md#L348]
- Linter-block hint: `grep -r "next/image" --include="*.{ts,tsx,js,jsx}" → warn when NEXT_PUBLIC_DEFAULT_LOADER is unset`

[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-boundaries-001.md#L378]
- "Next.js standalone + Amplify Hosting OR OpenNext → Lambda/ECS both portable."

[code: openspec/changes/lukla-ops-engine-planning/research/blueprint-boundaries-001.md#L433]
- Decision table: "Web: Next.js 16 portable to AWS | search + Amplify docs | §0.3 W9"

**Action category:** B — same as `blueprint-platform-001.md`. Preserve with header note. **ASK user.**

### 2.10 Framework-specific related assumptions captured (encryption-bound to Next.js)

These tokens appear ONLY inside the two research files (§2.8, §2.9) as forbidden-API list items. No code in the repo currently uses any of them. Confirmed by scanning all `*.{ts,tsx,js,jsx}` files in `prototypes/`:

| Token | Files in repo | Latest verify |
|---|---|---|
| `next/image` | 0 source hits (only in `blueprint-boundaries-001.md#L348`) | `rg next/image prototypes` → no matches |
| `next/auth` (NextAuth) | 0 source hits | `rg -i next-auth prototypes docs` → no matches |
| `next/font` | 0 source hits | `rg -i 'next/font' prototypes docs` → no matches |
| `NEXT_PUBLIC_` | 0 source hits | `rg NEXT_PUBLIC_ prototypes` → no matches; only `VITE_*` env vars |
| App Router (`app/`, `layout.tsx`, `_app.tsx`, `_document.tsx`) | 0 source hits | `prototypes/sampling-spec-rnd/frontend/src/` directory tree confirms pages-as-route convention (pages/TimeStudyPage.tsx — React Router style), not App Router |
| `output: 'standalone'` | 0 source hits; only declared prose | `rg "standalone" prototypes` → no matches |
| ISR writes | 0 source hits | `rg -i 'ISR' prototypes` → no matches |
| Edge runtime | 0 source hits | `rg -i 'edge runtime' prototypes` → no matches |
| `next.config.{js,mjs,ts}` | 0 files | `Get-ChildItem -Filter next.config*` → 0 results |

**Action category:** A+B — none of these tokens appear in any active source code. Removing them from the research/ADR files is mechanically safe; **no runtime, API, auth, or data path is touched** by the cleanup.

---

## 3. Files That Look Like References But Are NOT Framework Mentions

These are **noise** the cleanup must NOT touch. Each is a token that matched the broad `next` regex but is unrelated to the Next.js framework.

| Token | File | Lines | Why it is NOT a Next.js reference |
|---|---|---|---|
| "next person" (English) | `AGENTS.md` | #L31 | Natural English in workspace-instructions prose |
| "🚀 Next Steps" (English) | `docs/sampling-spec-rnd/APPLE_DESIGN.md` | #L266 | Section header in a design doc that elsewhere explicitly declares React + Tailwind + Vite (#L3, #L36) |
| "next step / gate / action" (English) | `openspec/.../reviews/{review-005-phase2,review-006-adversarial-hardening,blueprint-phase-b-review,blueprint-phase-c-review}.md` | multiple | Phase handoff prose |
| "next phase / next action / next round" (English) | `openspec/.../research/research-002.md#L16-L18`, `research-003-phase2b-recovery.md#L123`, `research-004-review-recovery.md#L14, #L75`, `blueprint-platform-001.md#L249, #L262`, `blueprint-boundaries-001.md#L407, #L443` | multiple | Roadmap prose ("next round Orchestrator", "next phase close-out", "recommended next step"). These are framework-neutral English usage, not Next.js. |
| `nextCursor` (pagination field, JSON) | `openspec/.../contracts/openapi.yaml#L851, #L856, #L857, #L865, #L875, #L885, #L912` | #L851-L912 | REST pagination cursor convention; unrelated to Next.js |
| `"module": "ESNext"` (TypeScript config) | `prototypes/sampling-spec-rnd/frontend/tsconfig.json#L7` | #L7 | TypeScript `module` compiler target name; unrelated |
| "next time Git touches it" (LF/CRLF warning) | `openspec/.../artifacts/implementation/impl-003.md#L107` | #L107 | Git EOL warning message; unrelated |
| "SUPERSEDE (next version)" | `prototypes/sampling-spec-rnd/backend/MODULES_REFERENCE.md#L343` | #L343 | Module-versioning prose; unrelated (in Python backend module) |
| "Next Steps" (English) | `prototypes/sampling-spec-rnd/backend/BACKEND_STATUS.md#L64` | #L64 | Status doc section header in Python backend; unrelated |
| "Verify each artifact file exists after writing before proceeding to next" | `.github/prompts/opsx-propose.prompt.md#L106`, `.github/skills/openspec-propose/SKILL.md#L114` | #L106 / #L114 | Openspec generic agent skill prompt text; **active OpenSpec workflow plumbing**, not framework — must be preserved |
| "Continue to next task" | `.github/prompts/opsx-apply.prompt.md#L70`, `.github/skills/openspec-apply-change/SKILL.md#L78`, `.github/skills/openspec-explore/SKILL.md#L272` | #L70 / #L78 / #L272 | Generic OpenSpec workflow instruction; **must be preserved** |
| "predict what happens next" | `.agents/skills/apple-design/SKILL.md#L254` | #L254 | UX design heuristic copied from Apple HIG; unrelated |
| `child_process.exec` and similar (none matched) | n/a | n/a | No false-positive exec references in the codebase |

**Conclusion:** The cleanup script should use a more precise regex than a blanket `next` search, e.g. `Next\.js|nextjs|next/image|next/auth|next/font|NEXT_PUBLIC_|next dev|next build|next start|next config|next-env\.d\.ts|next-page|NextRouter|next-route|/\.next/|/out/|/\.vercel/|output: ['"]standalone|output: standalone|App Router|ISR write|Edge runtime`. The current aggressive `next` regex catches all of the prose noise and forces manual triage.

---

## 4. Active vs Historical vs Generic — Categorization

| File | Category | Edit now? | Required decision |
|---|---|---|---|
| `.gitignore` | **Active** (root, repo-wide applicability) | **Yes** | Keep `/build/` (Vite output); drop `/.next/`, `/out/`, `/.vercel/`, `next-env.d.ts`, the `Next.js / Node.js` header comment, retained with revised comment ("Vite / Node.js"). No Vercel pattern. |
| `10-technology-stack-and-decisions.md` | **Active** (Phase 6 deliverable) | **Yes** | Replace `Web: Responsive Next.js PWA, output: standalone` with `Web: React 18 + Vite + Tailwind PWA, static bundle → S3+CloudFront OR container host`. Drop "no Vercel-only API" guard. |
| `14-frontend-architecture.md` | **Active** (Phase 6 deliverable) | **Yes** | Replace `Next.js` and `output: 'standalone'`; replace `Next.js PROPOSAL` with `React + Vite PROPOSAL`. Structure (6 view route maps, no Vercel-only API) survives intact. |
| `09-technical-blueprint-completion-plan.md` | **Active** (Phase 6 parent plan) | **Yes** | Replace `Next.js portability` rule with Vite + static-host rule. Update checklist rows: replaces "FastAPI + PostgreSQL + Next.js" with "FastAPI + PostgreSQL + React/Vite". |
| `artifacts/design_guideline.md` | **Active** (frontend structure doc) | **Yes** | Replace section header `React / Next.js` → `React / Vite + Tailwind`. Replace `/app` tree (`Next.js App Router`) → `/pages` (or `/src/pages` React Router-style convention observed in `src/pages/TimeStudyPage.tsx`). |
| `artifacts/struktur diagram Backend&frontend Lukla.svg` | **Active** (binary export, no source-control text edit guidance) | **Yes — partial** | Replace the single `<span class="nodeLabel"><p>📁 /app (Next.js App Router)</p></span>` substring with `📁 /pages (React + Vite)`. File is a Mermaid render; the Mermaid source equivalent is in `archive/PRD Draft ... v1.3.md#L73`. Recommended path: edit the SVG once (one byte-shaped string change inside the foreignObject node label), AND leave Mermaid source untouched until the `archive/` decision is made. |
| `archive/PRD Draft - Lukla Operations Engine - v1.3.md` | **Historical** (archived draft, kept for trace) | **ASK user** | If the archive is read-only history, leave untouched; the SVG label is regenerated from this Mermaid source. If the archive is mutable, edit Mermaid block at `#L73` together with the SVG. Tag each Next.js mention as `[historical — superseded 2026-10-14, see 10-technology-stack-and-decisions.md]` if preserving untouched. |
| `research/blueprint-platform-001.md` | **Active research evidence** (used by reviewers and for future-pivot discussion) | **ASK user** | Recommended: add a one-line header note `> Note (2026-10-14): The current stack ADR (10-technology-stack-and-decisions.md) supersedes Next.js as the chosen frontend. Findings below remain useful as a future-pivot option catalog.` and leave V14 evidence intact. |
| `research/blueprint-boundaries-001.md` | **Active research evidence** | **ASK user** | Same treatment as `blueprint-platform-001.md`. The forbidden-API list (`next/image`, `NEXT_PUBLIC_DEFAULT_LOADER`) is no longer load-bearing in the chosen stack; preserve for reader reference; optionally tag with header note. |

---

## 5. Functions / Symbols / Configurations Worth Preserving

The task requests that runtime / API / auth / data not be broken. The audit walks each risk class:

| Class | Item | Status | Verdict |
|---|---|---|---|
| Stack runtime | `vite ^4.4.0`, `@vitejs/plugin-react ^4.0.0` | Active and load-bearing | **Do NOT touch**. Removes the entire app. |
| Stack runtime | `react ^18.2.0`, `react-dom ^18.2.0` | Active and load-bearing | **Do NOT touch**. |
| Build target | `tsconfig.json` `module: "ESNext"` | Active and load-bearing | **Do NOT touch.** (false-positive match) |
| Entry | `src/main.tsx` (`ReactDOM.createRoot`) | Active and load-bearing; `react-dom/client` import graph | **Do NOT touch.** |
| Env vars | `VITE_API_URL` (Vite convention) | Active and load-bearing | **Do NOT touch.** |
| Routing | `src/pages/TimeStudyPage.tsx` (React Router page-folder convention) | Active and load-bearing | **Do NOT touch.** Note: revival of `src/pages/` after Next.js cleanup is correct because both Vite-React projects commonly use this name. |
| API contract | `contracts/openapi.yaml` pages all using `nextCursor` | Active and load-bearing (pagination cursor is API-level) | **Do NOT touch.** (false-positive match) |
| Auth | 0 refs to `next-auth`; RLS design at `13-authn-authz-design.md` is policy-based, framework-neutral | Active and load-bearing | **Do NOT touch.** |
| Data | `prototypes/sampling-spec-rnd/backend/src/services/sampling_rnd_workflow.py`, `models/spec_version_tracker.py`, `models/time_study_recorder.py` | Active and load-bearing | **Do NOT touch.** |
| Backend | FastAPI; `requirements.txt`; `run_backend.bat` | Active and load-bearing | **Do NOT touch.** |

**Verdict:** No runtime, API, auth, or data path is touched by editing the 8–9 OpenSpec doc files identified above.

---

## 6. Verification Commands (Read-Only)

Use these to confirm the cleanup did not regress anything once edits land:

```powershell
# 1. Confirm zero Next.js in active frontend (must remain 0 hits post-cleanup)
rg -n -i 'next' prototypes/sampling-spec-rnd/frontend/src
#   Expected: 0 hits (excluding "next step" type false-positives; pattern tight to
#   framework tokens)

# 2. Confirm zero active Next.js package install
Get-ChildItem -Recurse -Filter package.json -Exclude node_modules | ForEach-Object {
  Select-String -Path $_.FullName -Pattern '"next"' -SimpleMatch
}
#   Expected: 0 hits

# 3. Confirm zero Next.js build / config artefacts on disk
Get-ChildItem -Recurse -Force | Where-Object {
  $_.Name -match '^\.next($|/)' -or $_.Name -match '^next\.config' -or $_.Name -eq 'next-env.d.ts' -or $_.Name -eq '.vercel'
} | Where-Object { $_.FullName -notmatch 'node_modules' }
#   Expected: 0 hits

# 4. Confirm running frontend still starts
cd prototypes/sampling-spec-rnd/frontend
npm run dev -- --port 3009
#   Expected: vite starts on 3009; no "next dev" or "next start" output.

# 5. Confirm backend tests still pass
cd prototypes/sampling-spec-rnd/backend
python -m pytest
#   Expected: existing tests pass; tests are framework-neutral.

# 6. Spot-check the cleaned docs
rg -n 'Next\.js' openspec/changes/lukla-ops-engine-planning/10-technology-stack-and-decisions.md openspec/changes/lukla-ops-engine-planning/14-frontend-architecture.md openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md openspec/changes/lukla-ops-engine-planning/artifacts/design_guideline.md
#   Expected: 0 hits after cleanup

# 7. Spot-check the SVG
rg -n 'Next\.js' 'openspec/changes/lukla-ops-engine-planning/artifacts/struktur diagram Backend&frontend Lukla.svg'
#   Expected: 0 hits after cleanup

# 8. (If user chooses "edit archive") Spot-check the archived PRD
rg -n 'Next\.js' 'openspec/changes/lukla-ops-engine-planning/archive/PRD Draft - Lukla Operations Engine - v1.3.md'
#   Expected: 0 direct mentions; or `[historical — superseded]` tags still readable

# 9. (If user chooses "preserve research") Spot-check research evidence
rg -n 'Next\.js' openspec/changes/lukla-ops-engine-planning/research/blueprint-platform-001.md openspec/changes/lukla-ops-engine-planning/research/blueprint-boundaries-001.md
#   Expected: hits still present (research evidence preserved); a header note preserved explaining the choice has moved off Next.js.

# 10. Confirm git working tree state
git status --short
#   Expected: only the files listed in the cleanup task touched; no collateral edits.
```

---

## 7. Worklog of Searches Performed (Audit Trail)

1. Listed `c:\Projects\hackathon-MAIN-alkademi` root with hidden items (`-Force`): `ls -Force`. Inventory: `.agents`, `.git`, `.github`, `docs`, `openspec`, `prototypes`, `.gitignore`, `AGENTS.md`, `README.md`. No top-level `package.json`, `tsconfig.json`, `vite.config.*`, or `next.config.*`.
2. `Get-ChildItem -Recurse -Filter package.json`: only one match: `prototypes/sampling-spec-rnd/frontend/package.json`. **Read full content**; confirmed Vite + React + TS + Tailwind; no Next.js.
3. `git status --short`: empty. `git ls-files --others --exclude-standard`: empty. No uncommitted or untracked user changes anywhere.
4. `git log --oneline -n 5 -- <key-files>`: 5 most recent commit subjects inspected. Most recent: `cc091ae chore(git): anchor artifacts pattern in gitignore` (the `.gitignore` Next.js anchors were added in this commit; it is a **stale, recent** state).
5. `rg -n -i 'next\.?js|nextjs|next/|next dev|next build|next start|next-auth|next/font|NEXT_PUBLIC_' .` (full repo, excluding `.git`, `node_modules`, lockfiles): 60KB output captured; 9 files matched (8 docs + `.gitignore`).
6. Per-file `rg -n -i 'next'` reads for: `.gitignore`, `10-technology-stack-and-decisions.md`, `14-frontend-architecture.md`, `09-technical-blueprint-completion-plan.md`, `artifacts/design_guideline.md`, `artifacts/struktur diagram Backend&frontend Lukla.svg`, `archive/PRD Draft - Lukla Operations Engine - v1.3.md`, `research/blueprint-platform-001.md`, `research/blueprint-boundaries-001.md`.
7. Cross-checked `rg -n -i 'next'` in `openspec/specs/` and `openspec/contracts/`: hits in `contracts/openapi.yaml` are **only `nextCursor`** — pagination field, not framework.
8. Cross-checked `rg -n -i 'next'` in `.agents`, `.github`, `prototypes`: hits in `.github/skills/*` and `.github/prompts/*` are OpenSpec workflow prose (e.g., "next task"); hits in `.agents/skills/apple-design/SKILL.md` are design heuristic prose ("predict what happens next"). **None are framework references** — these are **active, must-not-touch**.
9. `rg -n -i 'output:.*standalone|App Router|next-auth|NEXT_PUBLIC|next/font|next/image|Vercel|ISR|Edge runtime'` across the OpenSpec change: produced the §2.10 framework-assumption table; correlated with the per-file sweep.
10. `Test-Path .next` / `Test-Path next.config.mjs` / `Test-Path next.config.js`: all three **false**. Confirms zero Next.js on disk.
11. Inspected `AGENTS.md` Standard Working Method (steps 1–5); confirm this research output respects: 1) clarify outcome (✓ — propose→ execute plan); 2) retrieve context first (✓ — web/file/semantic); 3) bounded steps (✓ — single discovery pass); 4) OpenSpec alignment (✓ — artifact file in `openspec/.../artifacts/`); 5) verify before claiming (✓ — `git` + `rg`-only).
12. Inspected `gitignore` Anchored Git Rules: the `/build/` pattern needs to be **renamed to `/build/  # vite output`** so the reader sees this anchored pattern is Vite's, not Next.js's. The `.gitignore` itself is anchored, so this in-file comment annotation is the cleanest fix.
13. Inspected Pre-Archive Gate (Asset Reconciliation, Configuration Drift): not blocking here — the change folder has no uncommitted user artifacts and no runnable source trees other than `prototypes/` (which is allowed by the AGENTS.md repo hygiene rule). The cleanup target is non-application docs only, so the gate will not fire.

---

## 8. Sources Consulted (operator memory only; preserved verbatim)

These URLs are **embedded in the research files** (§2.8, §2.9). They are not Next.js-installation knowledge; they are deployment-platform evidence and must remain readable in the research files even after the active-stack cleanup:

- `https://www.ravion.com/docs/deploy/aws/nextjs` — cited at `research/blueprint-platform-001.md#L159`
- `https://www.brandrums.com/blog/how-to-deploy-nextjs-on-aws-2026/` — cited at `research/blueprint-platform-001.md#L160` and `#L312`
- `https://opennext.js.org/` — cited at `research/blueprint-platform-001.md#L161`
- `https://docs.aws.amazon.com/amplify/latest/userguide/ssr-amplify-support.html` — cited at `research/blueprint-boundaries-001.md#L134`
- `https://opennext.js.org/aws/faq` — cited at `research/blueprint-boundaries-001.md#L134`

(Source URLs are also preserved in `research/blueprint-boundaries-001.md#L108-L110` footnote index.)

---

## 9. Apply-Change Plan (Next Pass, Not This Pass)

This document is the **research/planning artifact**. The next session will own the apply pass. That pass should:

1. **OpenSpec gate.** Confirm the cleanup target is small enough to skip a full OpenSpec proposal cycle, and that the change goes through `openspec apply` (per the `.github/skills/openspec-apply-change/SKILL.md`). Or, given the small surface and low-risk nature, treat it as a docs-only house-keeping edit. (Per AGENTS.md "Keep implementation small, reversible, and directly traceable to approved requirements.")
2. **Bounded file set.** Create a single PR/commit that touches exactly:
   - `.gitignore` (header + 4 stale patterns + add `vite-env.d.ts` if applicable)
   - `10-technology-stack-and-decisions.md` (1 row)
   - `14-frontend-architecture.md` (2 paragraphs)
   - `09-technical-blueprint-completion-plan.md` (5 lines)
   - `artifacts/design_guideline.md` (header + 1 sentence + directory tree label)
   - `artifacts/struktur diagram Backend&frontend Lukla.svg` (1 node label inside the foreignObject)
3. **ASK user before:**
   - Editing `archive/PRD Draft - Lukla Operations Engine - v1.3.md` (historical).
   - Adding header notes to `research/blueprint-platform-001.md` and `research/blueprint-boundaries-001.md` versus leaving them untouched.
   - Whether to re-export the SVG from Mermaid (preferred: edit inline, since the SVG is a one-off render) versus regenerate.

4. **Verify before commit.** Run §6 commands #6, #7, #10. Confirm `git diff --check` (no trailing whitespace regressions). Confirm `rg -n 'Next\.js' openspec/changes/lukla-ops-engine-planning/` returns only the files the user agreed to keep (i.e., the research files and possibly the archive).
5. **No new dependencies.** Cleanup does not install anything. No `package.json` mutation. No npm/pnpm install step.
6. **Pre-archive gate (when the change is later archived, not now).** Asset Reconciliation: nothing to reconcile (no runnable source trees in `openspec/changes/lukla-ops-engine-planning/`). Configuration Drift: irrelevant for docs.

---

## 10. Conflicts / Inconsistent Claims (found in sweep)

| Claim | Source | Reality |
|---|---|---|
| "Selected Next.js as Web framework" | `10-technology-stack-and-decisions.md#L23`, `14-frontend-architecture.md#L20`, `design_guideline.md#L26-32` | **Stale** — active runtime is Vite + React 18. **Verified**. |
| "Design_guideline references Next.js App Router" | `09-technical-blueprint-completion-plan.md#L38` | **Confirmed true** at `design_guideline.md#L26-L32`. **Verified.** |
| "Next.js portability: use output: 'standalone'" | `09-technical-blueprint-completion-plan.md#L32` | **Confirmed true** as a documented rule, **but moot** because the chosen framework is Vite, not Next.js. **Verified.** |
| "Forbidden Next.js APIs (next/image, NEXT_PUBLIC_DEFAULT_LOADER)" | `research/blueprint-boundaries-001.md#L348` | **Confirmed true** as a linter hint in research evidence; **moot** in current stack (Vite has no `next/image`). **Verified.** |
| ".gitignore anchors Next.js patterns" | `.gitignore#L2-L14, #L32` | **Confirmed true** and **stale**. **Verified.** |
| "App Router structure: /app (Next.js App Router)" | `artifacts/design_guideline.md#L32`, `struktur diagram *.svg` node label, `archive/PRD Draft v1.3.md#L73` | **Confirmed true** at three places. **Verified.** |

No contradiction between sources — they all consistently say "we picked Next.js". The single contradiction is **between the docs and the actual installed runtime**. The actual installed runtime is the source of truth.

---

## 11. Open Questions

### FIND (more research can answer)

- Are there **image assets** under `artifacts/` that render the original `archive/PRD Draft v1.3.md` mermaid graph? If yes, regenerating the SVG would touch multiple files; if no, the inline edit path is sufficient. **CHECK**: `Get-ChildItem -Recurse -Filter *.svg openspec/changes/lukla-ops-engine-planning/` (already enumerated above; only 2 SVGs, both inline Mermaid renders).
- Does any reviewer-skills file in `.github/skills/` have a /workspace/ assumption that depends on Next.js-specific tooling? (Already inspected; no.) **RESULT: confirmed no impact.**

### ASK (only the user can answer)

- Should the archived PRD draft `archive/PRD Draft - Lukla Operations Engine - v1.3.md` be edited, or preserved as a frozen historical snapshot of the ideation phase? (Affects §2.7 only.)
- Should the research evidence in `research/blueprint-platform-001.md` and `research/blueprint-boundaries-001.md` receive a header note explaining that the active stack has moved off Next.js, or be left untouched as future-pivot reference material? (Affects §2.8, §2.9 only.)
- Should the SVG be edited inline (1-byte string change inside the foreignObject node label) OR regenerated from Mermaid source? (Affects §2.6 only.)
- The "design_guideline.md" lists `Radix UI/shadcn` as the UI component stack. Is this still aligned with the active prototype (`react + tailwind`, no Radix/shadcn dependencies observed)? **NOT in scope** of this Next.js audit, but flagged as a follow-up: `rg -n -i 'radix|shadcn' prototypes` → no hits → possibly stale in the same way. (Out of scope per user request; recorded for completeness.)

### Unknown

- The original Phase-1 author who picked Next.js is no longer in the active conversation; the design intent ("Next.js because of mature PWA + deploy-portability story") is implied by the docs but not explicitly stated in workspace history. Without that record, the cleanup judgment leans on the current source-code reality (Vite installed; React 18 active) as the source of truth.

---

## 12. Bottom Line

**9 files contain stale Next.js framework references.**

- **3 active deliverables** require edits (matrix-driven; minimal diff): `10-technology-stack-and-decisions.md#L23`, `14-frontend-architecture.md#L12, #L20`, `09-technical-blueprint-completion-plan.md#L32, #L38, #L65, #L77, #L84`.
- **2 active artifacts** require edits: `artifacts/design_guideline.md#L26-32`, the SVG node label in `artifacts/struktur diagram Backend&frontend Lukla.svg`.
- **1 root config file** requires revisions: `.gitignore#L1-L14, #L31-L32` (anchored; affects entire repo).
- **1 archived PRD draft** is **historical** — **ASK user**: edit or preserve.
- **2 research evidence files** are **active research, not directives** — **ASK user**: tag with header note, or preserve untouched.

**The cleanup does not touch any runtime, API, auth, data, build, deploy, or test artifact.** It is bounded to documentation. No new dependencies. No npm install step. No code edits.

**Active runtime is verified** as `vite ^4.4.0` + `react ^18.2.0` + `typescript ^5.1.0` + `tailwindcss ^3.3.0` in the sole `prototypes/sampling-spec-rnd/frontend` workspace. Zero Next.js in any active dependency tree.

**Glyph:**

- ✅ Verified: file/line evidence exists.
- ⚠️ Inferred: reasonable claim but indirect.
- ❓ Unknown: cannot determine without further action.

| Section | Status |
|---|---|
| Active runtime (Vite + React 18) | ✅ Verified |
| Stack ADR staleness (10, 14, 09) | ✅ Verified |
| Design guideline staleness | ✅ Verified |
| SVG diagram staleness | ✅ Verified |
| `.gitignore` staleness | ✅ Verified |
| Historical archive staleness | ⚠️ Verified-but-historical (ASK user) |
| Research evidence staleness | ⚠️ Verified-but-not-directive (ASK user) |
| Source URLs to preserve | ✅ Verified (real citations) |
| Runtime/API/auth/data untouched | ✅ Verified (no overlap) |
| No new dependencies | ✅ Verified (docs-only) |
| Working tree clean | ✅ Verified (`git status --short` empty) |
| Asset Reconciliation gate not blocking | ✅ Verified (no runnable source in change folder) |

---

**End of planning artifact — ready for review and decision on §2.7, §2.8, §2.9 "ASK user" items.**
