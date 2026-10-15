import { test, expect } from '@playwright/test';

/**
 * Closing Scenario 1: Cross-Client Material Issuance Rejection Modal & Guardrail
 * Source ID: FR-6.2, Closing-01
 * Stable Test ID: UI-PROTO-VIEW03-MISMATCH-MODAL
 *
 * NOTE: This test asserts the client-side presentation and interaction of the ownership guardrail modal.
 * Underlying database RLS and stock balance immutability (SCN-01-API / SCN-01-DB) require the backend service.
 */
test.describe('Closing Scenario 1 — Cross-Client Material Issuance Rejection', () => {
  test('View 03 renders ownership mismatch modal and dismisses on demand', async ({ page }) => {
    // 1. Navigate to the standalone mock UI
    await page.goto('');

    // Verify initial load on Executive Operations Dashboard (View 01)
    await expect(page.locator('#view-01')).toBeVisible();

    // 2. Navigate to View 03 (Warehouse Inventory)
    const view03Nav = page.locator('button[data-view="view-03"]');
    await expect(view03Nav).toBeVisible();
    await view03Nav.click();

    // 3. Verify View 03 section is active
    const view03Section = page.locator('#view-03');
    await expect(view03Section).toBeVisible();
    await expect(page.locator('#title-03')).toHaveText('Multi-Client Warehouse Inventory Grid');

    // 4. Verify the FR-6.2 Cross-Client Ownership Guardrail Modal
    const modalLayer = view03Section.locator('.modal-layer');
    await expect(modalLayer).toBeVisible();

    const modalTitle = page.locator('#dispatch-modal-title');
    await expect(modalTitle).toHaveText('Dispatch Ditolak — Ownership Mismatch');

    const modalLabel = modalLayer.locator('.modal-label');
    await expect(modalLabel).toHaveText('FR-6.2 · Ownership guardrail');

    await expect(modalLayer).toContainText(
      'Stock milik Client A tidak dapat diterbitkan ke Order Client B. Periksa ownership lot dan order sebelum dispatch dilanjutkan.',
    );

    // 5. Verify toolbar collision alert indicator
    const alertIndicator = view03Section.locator('.toolbar span.mono');
    await expect(alertIndicator).toHaveText('Alerts: 0 Collisions');

    // 6. Dismiss modal via 'Mengerti' button
    const dismissBtn = modalLayer.locator('[data-dismiss-modal]');
    await expect(dismissBtn).toHaveText('Mengerti');
    await dismissBtn.click();

    // 7. Verify modal is dismissed (hidden = true)
    await expect(modalLayer).toBeHidden();

    // 8. Verify warehouse table dispatch controls are accessible post-dismissal
    const table = view03Section.locator('table');
    await expect(table).toBeVisible();
    await expect(table.locator('tbody tr')).toHaveCount(2);

    const firstRowDispatch = table.locator('tbody tr').first().locator('button');
    await expect(firstRowDispatch).toHaveText('Dispatch');
  });
});
