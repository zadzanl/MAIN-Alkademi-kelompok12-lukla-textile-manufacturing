import { test, expect } from '@playwright/test';

// Known ceiling: this is one read-only Chromium smoke, not a feature or API suite.
// Upgrade path: add focused scenarios only when their user-visible contract is approved.
test('portal auth loads and authenticated dashboard connects', async ({ page }) => {
  // 1. Unauthenticated visit renders the portal auth gate
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'Akses portal', exact: true }),
  ).toBeVisible();

  // 2. Authenticated session renders the dashboard with connected backend
  await page.addInitScript(() => {
    sessionStorage.setItem(
      'portal-auth-session',
      JSON.stringify({
        token: 'smoke-test-token',
        actor: {
          id: 'smoke-actor-001',
          displayName: 'Smoke Tester',
          role: 'rnd_operator',
          tenantId: 'lukla-textile',
        },
      }),
    );
  });

  await page.goto('/');

  // The app reads this full health path through Vite's /api proxy; no JSON body is asserted.
  await expect(
    page.getByRole('heading', { name: 'Overview', exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/Backend terhubung|Connected/i)).toBeVisible();
});

test('sidebar renders dominant AI copilot entry and navigates to copilot view', async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem(
      'portal-auth-session',
      JSON.stringify({
        token: 'smoke-test-token',
        actor: {
          id: 'smoke-actor-001',
          displayName: 'Smoke Tester',
          role: 'rnd_operator',
          tenantId: 'lukla-textile',
        },
      }),
    );
  });

  await page.goto('/');

  // Verify the dominant AI assistant entry exists on sidebar
  const copilotBtn = page.getByRole('button', { name: /Lukla Assistant/i });
  await expect(copilotBtn).toBeVisible();
  await expect(copilotBtn.getByText('AI')).toBeVisible();

  // Navigate to Copilot view
  await copilotBtn.click();
  await expect(page.getByRole('heading', { name: 'Lukla Intelligence' })).toBeVisible();
  await expect(page.getByText('Live Gateway')).toBeVisible();
});