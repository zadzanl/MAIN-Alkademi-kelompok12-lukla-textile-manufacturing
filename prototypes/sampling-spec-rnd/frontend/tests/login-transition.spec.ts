import { test, expect } from '@playwright/test';

// This transition test is separate because smoke.spec.ts pre-seeds sessionStorage and cannot catch a hook-order crash during login.
test('login transition renders the authenticated shell without a blank screen', async ({ page }) => {
  const pageErrors: string[] = [];
  page.on('pageerror', error => pageErrors.push(error.message));

  await page.route('**/api/auth/login', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        accessToken: 'test-token',
        expiresIn: 3600,
        actor: {
          actorId: 'test-actor-001',
          displayName: 'Test Admin',
          email: 'test@lukla.local',
          role: 'admin',
          status: 'active',
        },
      }),
    }),
  );

  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Akses portal', exact: true })).toBeVisible();

  await page.getByRole('textbox').first().fill('ADMIN-IT');
  await page.locator('input[type="password"]').fill('Admin#12345');
  await page.getByRole('button', { name: 'Masuk ke Portal' }).click();

  await expect.soft(page.getByRole('heading', { name: 'Akses portal', exact: true })).toBeHidden();
  await expect.soft(page.getByRole('button', { name: 'Keluar dari portal' })).toBeVisible();
  await expect(pageErrors, 'The login transition must not throw a page error.').toEqual([]);
});
