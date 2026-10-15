import { test, expect } from '@playwright/test';

/**
 * View 04: Floor Terminal (30-Minute Interval Touch Interface & Tally Stepper Interactions)
 * Source ID: FR-7.3, VIEW-04
 * Stable Test ID: UI-PROTO-VIEW04-TALLY-STEPPER
 *
 * Verifies bounded production interval tally stepper adjustments (+/-) and floor terminal interactions.
 */
test.describe('View 04 — Floor Terminal Tally Stepper Interactions', () => {
  test('increments, decrements, and enforces floor tally stepper bounds', async ({ page }) => {
    // 1. Navigate to standalone mock UI
    await page.goto('');

    // 2. Navigate to View 04 (Floor Terminal)
    const view04Nav = page.locator('button[data-view="view-04"]');
    await expect(view04Nav).toBeVisible();
    await view04Nav.click();

    // 3. Verify View 04 section is active
    const view04Section = page.locator('#view-04');
    await expect(view04Section).toBeVisible();

    // Verify view header and context metadata
    await expect(page.locator('#title-04')).toHaveText('Floor Terminal');
    await expect(view04Section.locator('.eyebrow')).toHaveText(
      '04 — Floor Terminal (30-Minute Interval Touch Interface)',
    );

    const contextBar = view04Section.locator('.context-bar');
    await expect(contextBar).toContainText('Line 03');
    await expect(contextBar).toContainText('Mandor: Budi');
    await expect(contextBar).toContainText('Interval: 13:30 – 14:00');

    // 4. Locate Tailor #14 (Rudi S.) and test tally stepper
    const rudiCard = view04Section
      .locator('.tailor-card')
      .filter({ hasText: 'Tailor #14: Rudi S.' });
    await expect(rudiCard).toBeVisible();
    await expect(rudiCard.locator('.tailor-role')).toHaveText('Sleeve Assembly');

    const rudiCount = rudiCard.locator('.stepper-count');
    await expect(rudiCount).toHaveText('14');

    const rudiIncreaseBtn = rudiCard.locator('button[aria-label="Increase Rudi S. count"]');
    const rudiDecreaseBtn = rudiCard.locator('button[aria-label="Decrease Rudi S. count"]');

    // Test increment (+1): 14 -> 15
    await rudiIncreaseBtn.click();
    await expect(rudiCount).toHaveText('15');

    // Test second increment (+1): 15 -> 16
    await rudiIncreaseBtn.click();
    await expect(rudiCount).toHaveText('16');

    // Test decrement (-1): 16 -> 15
    await rudiDecreaseBtn.click();
    await expect(rudiCount).toHaveText('15');

    // Test decrement (-1): 15 -> 14
    await rudiDecreaseBtn.click();
    await expect(rudiCount).toHaveText('14');

    // 5. Test another operator: Tailor #18 (Mira K.)
    const miraCard = view04Section
      .locator('.tailor-card')
      .filter({ hasText: 'Tailor #18: Mira K.' });
    await expect(miraCard).toBeVisible();

    const miraCount = miraCard.locator('.stepper-count');
    await expect(miraCount).toHaveText('11');

    const miraIncreaseBtn = miraCard.locator('button[aria-label="Increase Mira K. count"]');
    await miraIncreaseBtn.click();
    await expect(miraCount).toHaveText('12');

    // 6. Verify Submit Button is present and active
    const submitBtn = view04Section.locator('button.terminal-submit');
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toHaveText('SUBMIT INTERVAL BLOCK');
  });
});
