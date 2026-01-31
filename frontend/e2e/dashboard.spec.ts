import { test, expect } from '@playwright/test';

test.describe('Dashboard E2E Tests', () => {
  test('should load dashboard page', async ({ page }) => {
    await page.goto('/dashboard');

    // ダッシュボードのタイトルが表示されることを確認
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('should navigate between pages', async ({ page }) => {
    await page.goto('/dashboard');

    // ナビゲーションリンクをクリック
    const vulnerabilitiesLink = page.getByRole('link', { name: /脆弱性一覧/i });
    if (await vulnerabilitiesLink.isVisible()) {
      await vulnerabilitiesLink.click();
      await expect(page).toHaveURL(/.*vulnerabilities/);
    }
  });
});
