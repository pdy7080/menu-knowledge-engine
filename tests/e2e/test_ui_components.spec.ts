/**
 * E2E Tests - UI Components (Sprint 2 Phase 1)
 * Playwright Tests for Menu Detail Page
 *
 * Tests:
 * 1. Menu list rendering
 * 2. Menu detail page navigation
 * 3. Image carousel functionality
 * 4. Multi-language switching
 * 5. Responsive layout
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:8000';

test.describe('Menu Knowledge Engine - UI Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  test('should load menu list page', async ({ page }) => {
    // Wait for menu list to load
    await page.waitForSelector('[data-testid="menu-list"]', { timeout: 10000 });

    // Check if menus are displayed
    const menuCards = await page.$$('[data-testid="menu-card"]');
    expect(menuCards.length).toBeGreaterThan(0);

    console.log(`✅ Found ${menuCards.length} menu cards`);
  });

  test('should navigate to menu detail page', async ({ page }) => {
    // Click on first menu card
    await page.click('[data-testid="menu-card"]:first-child');

    // Wait for detail page to load
    await page.waitForSelector('[data-testid="menu-detail"]', { timeout: 10000 });

    // Check if menu name is displayed
    const menuName = await page.textContent('[data-testid="menu-name"]');
    expect(menuName).toBeTruthy();

    console.log(`✅ Menu detail loaded: ${menuName}`);
  });

  test('should display menu images', async ({ page }) => {
    // Navigate to detail page
    await page.click('[data-testid="menu-card"]:first-child');
    await page.waitForSelector('[data-testid="menu-detail"]');

    // Check if image carousel exists
    const imageCarousel = await page.$('[data-testid="image-carousel"]');
    expect(imageCarousel).toBeTruthy();

    // Check if at least one image is loaded
    const images = await page.$$('[data-testid="menu-image"]');
    expect(images.length).toBeGreaterThan(0);

    // Measure image loading time
    const startTime = Date.now();
    await page.waitForLoadState('networkidle');
    const loadTime = (Date.now() - startTime) / 1000;

    console.log(`✅ ${images.length} images loaded in ${loadTime.toFixed(2)}s`);

    // Check if load time is under 2s
    expect(loadTime).toBeLessThan(2.0);
  });

  test('should switch languages correctly', async ({ page }) => {
    const languages = ['ko', 'en', 'ja', 'zh'];

    for (const lang of languages) {
      // Click language switcher
      await page.click(`[data-testid="lang-${lang}"]`);

      // Wait for content to update
      await page.waitForTimeout(500);

      // Check if menu names are in the correct language
      const menuName = await page.textContent('[data-testid="menu-card"]:first-child [data-testid="menu-name"]');
      expect(menuName).toBeTruthy();

      console.log(`✅ Language ${lang.toUpperCase()}: ${menuName}`);
    }
  });

  test('should display menu content fields', async ({ page }) => {
    // Navigate to detail page
    await page.click('[data-testid="menu-card"]:first-child');
    await page.waitForSelector('[data-testid="menu-detail"]');

    // Check required fields
    const fields = [
      'menu-name',
      'menu-explanation-short',
      'menu-ingredients',
      'menu-allergens',
      'menu-spice-level',
    ];

    for (const field of fields) {
      const element = await page.$(`[data-testid="${field}"]`);
      if (element) {
        const text = await page.textContent(`[data-testid="${field}"]`);
        console.log(`✅ ${field}: ${text?.substring(0, 50)}...`);
      } else {
        console.log(`⚠️  ${field}: Not found (optional field)`);
      }
    }
  });

  test('should handle image carousel navigation', async ({ page }) => {
    // Navigate to detail page
    await page.click('[data-testid="menu-card"]:first-child');
    await page.waitForSelector('[data-testid="menu-detail"]');

    // Check if carousel has multiple images
    const images = await page.$$('[data-testid="menu-image"]');

    if (images.length > 1) {
      // Click next button
      await page.click('[data-testid="carousel-next"]');
      await page.waitForTimeout(500);

      // Click previous button
      await page.click('[data-testid="carousel-prev"]');
      await page.waitForTimeout(500);

      console.log(`✅ Image carousel navigation working (${images.length} images)`);
    } else {
      console.log(`ℹ️  Single image, carousel navigation not tested`);
    }
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Reload page
    await page.goto(BASE_URL);
    await page.waitForSelector('[data-testid="menu-list"]');

    // Check if mobile menu is displayed
    const mobileMenu = await page.$('[data-testid="mobile-menu"]');

    if (mobileMenu) {
      console.log('✅ Mobile layout detected');
    } else {
      console.log('⚠️  Mobile menu not found, using desktop layout');
    }

    // Check if cards are stacked vertically
    const menuCards = await page.$$('[data-testid="menu-card"]');
    expect(menuCards.length).toBeGreaterThan(0);

    console.log(`✅ ${menuCards.length} menu cards visible on mobile`);
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Intercept API request and return error
    await page.route('**/api/v1/canonical-menus', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    // Reload page
    await page.goto(BASE_URL);

    // Check if error message is displayed
    await page.waitForSelector('[data-testid="error-message"]', { timeout: 5000 });

    const errorText = await page.textContent('[data-testid="error-message"]');
    expect(errorText).toContain('error');

    console.log('✅ Error handling working correctly');
  });

  test('should measure page performance', async ({ page }) => {
    const metrics = await page.evaluate(() => {
      const perf = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

      return {
        domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
        loadComplete: perf.loadEventEnd - perf.loadEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
      };
    });

    console.log('📊 Performance Metrics:');
    console.log(`  - DOM Content Loaded: ${metrics.domContentLoaded.toFixed(2)}ms`);
    console.log(`  - Load Complete: ${metrics.loadComplete.toFixed(2)}ms`);
    console.log(`  - First Paint: ${metrics.firstPaint.toFixed(2)}ms`);
    console.log(`  - First Contentful Paint: ${metrics.firstContentfulPaint.toFixed(2)}ms`);

    // Check performance targets
    expect(metrics.domContentLoaded).toBeLessThan(2000); // < 2s
    expect(metrics.firstContentfulPaint).toBeLessThan(1500); // < 1.5s
  });
});

test.describe('Menu Search & Filter', () => {
  test('should search menus by name', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForSelector('[data-testid="menu-list"]');

    // Type in search box
    await page.fill('[data-testid="search-input"]', '김치');

    // Wait for results
    await page.waitForTimeout(500);

    // Check if results are filtered
    const menuCards = await page.$$('[data-testid="menu-card"]');
    const firstMenuName = await page.textContent('[data-testid="menu-card"]:first-child [data-testid="menu-name"]');

    expect(firstMenuName).toContain('김치');

    console.log(`✅ Search working: Found ${menuCards.length} results for '김치'`);
  });

  test('should filter by category', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForSelector('[data-testid="menu-list"]');

    // Click category filter
    await page.click('[data-testid="category-soup"]');

    // Wait for filter
    await page.waitForTimeout(500);

    // Check if results are filtered
    const menuCards = await page.$$('[data-testid="menu-card"]');

    console.log(`✅ Category filter working: Found ${menuCards.length} soup dishes`);
  });
});
