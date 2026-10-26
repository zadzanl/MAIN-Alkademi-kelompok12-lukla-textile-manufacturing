# Tasks: ERP-Standard Login UI

## 1. Additive error plumbing (both apps)
- [ ] 1.1 `services/http.ts`: add `requestId` to `ApiError` and extract it from the
      RFC-7807 body.
- [ ] 1.2 `services/problem.ts`: add `extractRequestId(raw)` helper.
- [ ] 1.3 `services/authApi.ts` (3009) / `services/portalApi.ts` (3010): return optional
      `code`/`status`/`requestId` on `ApiResult` (additive only).
- [ ] 1.4 New `services/authErrorCopy.ts` (both apps): pure `Problem.code` → copy mapper
      plus feedback tone.

## 2. Config + env
- [ ] 2.1 `services/config.ts` (both): add `APP_ENV` and `APP_VERSION`.
- [ ] 2.2 `.env.example` (both): document `VITE_APP_ENV` and `VITE_APP_VERSION`.

## 3. Internal login page (3009)
- [ ] 3.1 Rewrite `pages/PortalAuthView.tsx` as split brand/form layout with org
      identity, env/version badge, security panel, SSO placeholder, legal footer, and
      contract error messaging. Keep the `Akses portal` heading, all field ids/labels,
      validation, and auth flow.

## 4. External login page (3010)
- [ ] 4.1 Rewrite `pages/PortalLoginView.tsx` with the same structure, indigo accent,
      ribbon, and external marker preserved.

## 5. Tests
- [ ] 5.1 Add `tests/authErrorCopy.test.ts` in both apps (pure mapper regression).

## 6. Verification
- [ ] 6.1 `npm run type-check`, `npm run lint`, `npm run test` in both apps.
- [ ] 6.2 `npm run test:e2e` in 3009 (smoke passes unchanged).
- [ ] 6.3 Browser check both apps at 375 / 768 / 1440 px; report evidence source.
- [ ] 6.4 `git diff --check` and `python scripts/check_workspace_hygiene.py`.
