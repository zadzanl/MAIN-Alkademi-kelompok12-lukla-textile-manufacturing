# Swiss-neutral visual evidence

Captured 2026-10-16 from the running `http://localhost:3009/` application at 1440×900 CSS pixels, device scale 1, Chromium. The page was opened with the `ui-dark` localStorage preference set to each named mode. Screenshots are full-page captures; no source/API state was fabricated for the images.

- [After: light executive dashboard](after-light-dashboard.png)
- [After: dark executive dashboard](after-dark-dashboard.png)

The parent agent also inspected the rendered executive dashboard with the integrated browser in both modes. A dark-mode chart regression (met-target bars disappearing) was found and corrected before these captures. Interactive browser inspection confirmed the light theme toggle and dashboard rendering; the saved dark screenshot independently confirms restored bar visibility.

**Before-state limitation:** No source-faithful before images were saved before earlier implementation work changed the shared tokens in this dirty checkout. An earlier integrated-browser screenshot showed the pre-dashboard-cleanup dark state (colored facility/ledger gradients, orange throughput bars, colorful KPI values), but the browser image is a session resource rather than a repository file. The pristine pre-theme light and dark states cannot be captured honestly without overwriting unrelated uncommitted changes; they are therefore unavailable. Existing external design references remain at `../lukla-ops-engine-planning/research/research-005-swiss-design-references.md` (relative to the change's parent folder). Do not treat the external reference images as app before screenshots.
