import { test, expect } from '@playwright/test';

// Known ceiling: this is one read-only Chromium smoke, not a feature or API suite.
// Upgrade path: add focused scenarios only when their user-visible contract is approved.
test('dashboard loads with a connected backend', async ({ page }) => {
  await page.goto('/');

  // The app reads this full health path through Vite's /api proxy; no JSON body is asserted.
  await expect(
    page.getByRole('heading', { name: 'Sampling & Spec R&D', exact: true }),
  ).toBeVisible();
  await expect(page.getByText('Connected', { exact: true })).toBeVisible();
});