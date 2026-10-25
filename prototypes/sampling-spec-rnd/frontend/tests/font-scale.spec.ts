import { test, expect, type Page } from '@playwright/test';

// Known ceiling: this covers the browser-visible preference contract, not every dashboard view.
// Upgrade path: add a role-specific scale assertion when the authenticated shell contract expands.
const AUTH_SESSION = {
  token: 'smoke-test-token',
  actor: {
    id: 'smoke-actor-001',
    displayName: 'Smoke Tester',
    role: 'rnd_operator',
    tenantId: 'lukla-textile',
  },
};

async function seedSession(page: Page, storedScale?: string) {
  await page.addInitScript(
    ({ session, scale }) => {
      sessionStorage.setItem('portal-auth-session', JSON.stringify(session));
      if (scale !== undefined) localStorage.setItem('ui-font-scale', scale);
    },
    { session: AUTH_SESSION, scale: storedScale },
  );
}

async function openSettings(page: Page) {
  const mobileMenu = page.getByRole('button', { name: 'Buka navigasi', exact: true });
  if (await mobileMenu.isVisible()) await mobileMenu.click();

  const chapter = page.getByRole('button', { name: 'Sistem', exact: true });
  if ((await chapter.getAttribute('aria-expanded')) !== 'true') await chapter.click();
  await page.getByRole('button', { name: 'Pengaturan', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Ukuran Teks', exact: true }),
  ).toBeVisible();
  await page.waitForTimeout(400);
}

const slider = (page: Page) => page.getByLabel('Ukuran teks global');
const output = (page: Page) => page.locator('output');
const scaleHeading = (page: Page) =>
  page.getByRole('heading', { name: 'Ukuran Teks', exact: true });

test('supports the default, all supported values, rendered scaling, and reset', async ({ page }) => {
  await seedSession(page);
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Executive Dashboard', exact: true })).toBeVisible();
  await openSettings(page);

  const control = slider(page);
  const heading = scaleHeading(page);
  await expect(control).toHaveValue('100');
  await expect(output(page)).toHaveText('100%');

  const baselineBox = await heading.boundingBox();
  expect(baselineBox).not.toBeNull();

  await control.fill('150');
  await expect(output(page)).toHaveText('150%');
  await expect.poll(async () => (await heading.boundingBox())?.height ?? 0).toBeGreaterThan(
    (baselineBox?.height ?? 0) * 1.35,
  );
  await expect.poll(async () => (await heading.boundingBox())?.height ?? 0).toBeLessThan(
    (baselineBox?.height ?? 0) * 1.65,
  );

  await control.fill('100');
  await expect(output(page)).toHaveText('100%');
  await expect.poll(async () => (await heading.boundingBox())?.height ?? 0).toBeLessThan(
    (baselineBox?.height ?? 0) * 1.1,
  );

  for (const value of ['75', '100', '125', '150']) {
    await control.fill(value);
    await expect(control).toHaveValue(value);
    await expect(output(page)).toHaveText(`${value}%`);
  }
});

test('restores 125% after reload', async ({ page }) => {
  await seedSession(page);
  await page.goto('/');
  await openSettings(page);

  await slider(page).fill('125');
  await expect(output(page)).toHaveText('125%');
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Executive Dashboard', exact: true })).toBeVisible();
  await openSettings(page);

  await expect(slider(page)).toHaveValue('125');
  await expect(output(page)).toHaveText('125%');
  await expect.poll(() => page.evaluate(() => localStorage.getItem('ui-font-scale'))).toBe('125');
});

test('falls back to 100% for an unsupported stored value', async ({ page }) => {
  await seedSession(page, '125.5');
  await page.goto('/');
  await openSettings(page);

  await expect(slider(page)).toHaveValue('100');
  await expect(output(page)).toHaveText('100%');
});

test('keeps lower Settings content reachable at 150%', async ({ page }) => {
  await seedSession(page);
  await page.goto('/');
  await openSettings(page);

  await slider(page).fill('150');
  await expect(output(page)).toHaveText('150%');
  await expect(slider(page)).toBeInViewport();

  const systemHeading = page.getByRole('heading', { name: 'Informasi Sistem', exact: true });
  await systemHeading.scrollIntoViewIfNeeded();
  await expect(systemHeading).toBeInViewport();

  const mainDimensions = await page.locator('main').evaluate((element) => ({
    clientHeight: element.clientHeight,
    scrollHeight: element.scrollHeight,
  }));
  expect(mainDimensions.scrollHeight).toBeGreaterThan(mainDimensions.clientHeight);
});

test.describe('narrow viewport', () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test('keeps Settings reachable at 150%', async ({ page }) => {
    await seedSession(page);
    await page.goto('/');
    await openSettings(page);

    await slider(page).fill('150');
    const systemHeading = page.getByRole('heading', { name: 'Informasi Sistem', exact: true });
    await systemHeading.scrollIntoViewIfNeeded();
    await expect(systemHeading).toBeInViewport();
  });
});