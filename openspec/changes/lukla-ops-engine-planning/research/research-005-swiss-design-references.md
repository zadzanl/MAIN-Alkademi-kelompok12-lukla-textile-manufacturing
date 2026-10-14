# Research 005 — Swiss Design Reference Screenshots

**Date:** 2026-10-14
**Purpose:** Visual reference set for integrating Swiss/International Typographic Style principles into `artifacts/design_guideline.md` and for the per-screen HTML layout mocks (`VIEW-01`…`VIEW-06`).
**Sources:** frappe.io (marketing/product, light-only site) and docs.fastino.ai (Mintlify docs, dark-by-default under dark system theme; light variants forced via `prefers-color-scheme` emulation).

## Capture log

| File | Source URL | Layout type | Swiss design traits visible |
|---|---|---|---|
| `frappe-home-hero.png` | https://frappe.io | hero | Oversized grotesque statement type ("Framework + Apps"), off-white field, black text, asymmetric whitespace, zero decoration |
| `frappe-home-section.png` | https://frappe.io (scrolled) | numbered index grid | Roman-numeral section labels (I.–VII.), numbered list items, hairline rules, strict multi-column grid — strongest Swiss artifact in the set |
| `frappe-framework.png` | https://frappe.io/framework | product page | Centered typographic statement, single blue accent, generous margins (retaken 10:23 after cookie-banner removal) |
| `frappe-erpnext.png` | https://frappe.io/erpnext | product page | Same system as framework page; product screenshot as the only non-typographic element (retaken 10:27) |
| `frappe-pricing.png` | https://frappe.io/pricing | pricing cards | Restrained card grid, blue accent reserved for CTA/featured plan, no gradients (retaken 10:26) |
| `frappe-blog.png` | https://frappe.io/blog | list index | Type-led list, date/title hierarchy via weight not color (retaken 10:18) |
| `fastino-docs-home.png` | https://docs.fastino.ai/introduction | docs-sidebar (dark) | Three-column anatomy: nav sidebar / content / "On this page"; hairline dividers |
| `fastino-docs-home-light.png` | same, light variant | docs-sidebar (light) | Same anatomy in light mode; near-white content field, single green accent |
| `fastino-docs-quickstart.png` | https://docs.fastino.ai/quickstart | prose-guide (dark) | Numbered steps, tabbed code blocks, monospace tokens |
| `fastino-docs-quickstart-light.png` | same, light variant | prose-guide (light) | Step flow legibility in light mode; code blocks as the darkest element on the page |
| `fastino-docs-api.png` | https://docs.fastino.ai/api-reference/inference/overview | api-reference (dark) | Dense endpoint listing, HTTP-method badges as the only color coding |
| `fastino-docs-api-light.png` | same, light variant | api-reference (light) | Param/endpoint density reference for data-heavy ERP screens |

## Theme notes

- **frappe.io is light-only** — no dark mode or theme toggle observed on any captured page.
- **docs.fastino.ai (Mintlify) defaults to the system theme.** The original captures were dark because the browser session reported a dark system theme. Light variants (`-light.png`) were produced with Playwright `page.emulateMedia({ colorScheme: 'light' })`; the site also has a manual "Theme preference" switch (system/light/dark) in the header.
- Retake status: `frappe-framework.png`, `frappe-pricing.png`, `frappe-blog.png`, `frappe-erpnext.png` were retaken in a second pass to remove a cookie-consent banner. `frappe-home-hero.png` was captured before banner handling was in place and may include consent UI at the viewport edge.

## Patterns worth borrowing for an ERP dashboard

1. **Numbered section indices** (`frappe-home-section.png`) — Roman/arabic numerals + hairline rules map directly onto our already-numbered `VIEW-01`…`VIEW-06` information architecture; use for sidebar grouping and page section headers.
2. **One accent color, spent sparingly** (`frappe-pricing.png`, `frappe-framework.png`) — blue appears only on primary CTAs and active states; maps onto the existing Apple Blue `#007AFF` in the guideline without conflict.
3. **Hairlines and whitespace over cards and shadows** (`frappe-home-section.png`) — the grid does the separating, not chrome. This is the main tension with the current glassmorphism direction and should be resolved as an explicit blend rule (Swiss structure, Apple material only where depth is functional: modals, popovers, navbar).
4. **Three-column docs anatomy** (`fastino-docs-home-light.png`) — nav / content / context rail fits dense master-detail screens: `VIEW-02` sample tracker (list / detail / revision history) and `VIEW-06` finance (ledger / entry / audit trail).
5. **Stepped task flows** (`fastino-docs-quickstart-light.png`) — numbered steps with exactly one code/action block per step; pattern for QC disposition flow (`VIEW-05`) and receive→issue material flows (`VIEW-03`).
6. **Type-led hierarchy** (`frappe-home-hero.png`) — page titles carry the hierarchy; no icons or color needed. Apply to view headers across all six screens.
7. **Reference density done cleanly** (`fastino-docs-api-light.png`) — two-column parameter tables, monospace identifiers, method badges as the sole color code; template for the warehouse stock grid (`VIEW-03`) and payroll statement (`VIEW-06`).

## Candidates ranked for "simple, straightforward, slightly colour-accented Swiss"

1. **frappe-home-section.png** — purest Swiss: numbered grid, hairlines, grotesque type, almost no color.
2. **fastino-docs-home-light.png** — best structural match for an app shell: sidebar + content + context rail, single accent.
3. **frappe-pricing.png** — best example of accent-color discipline on a card-based layout, closest to our dashboard cards.
