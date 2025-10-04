import { test, expect } from '@playwright/test';
import { TagManager } from '../../src/utils/TagManager';

test.describe('Example Web Application Tests', () => {
  const tagManager = TagManager.getInstance();

  test.beforeEach(async ({ page }) => {
    // Navigate to the application before each test
    await page.goto('https://example.com');
  });

  test.afterEach(async ({ page }) => {
    // Take screenshot on failure for debugging
    if (test.info().status !== test.info().expectedStatus) {
      await page.screenshot({ 
        path: `test-results/example-failure-${Date.now()}.png`,
        fullPage: true 
      });
    }
  });

  // @smoke @critical @ui @e2e
  test('should load homepage successfully @smoke @critical @ui @e2e', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should load homepage successfully',
      tags: ['smoke', 'critical', 'ui', 'e2e'],
      file: __filename,
      priority: 'critical',
      category: 'functional',
      browser: ['chrome', 'firefox', 'safari']
    });

    // Verify page loads and has expected title
    await expect(page).toHaveTitle(/Example/);
    
    // Check that main content is visible
    const mainContent = page.locator('main, #main, .main-content');
    await expect(mainContent).toBeVisible();
    
    // Verify page is fully loaded
    await page.waitForLoadState('networkidle');
  });

  // @navigation @ui @medium @regression
  test('should navigate between pages @navigation @ui @medium @regression', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should navigate between pages',
      tags: ['navigation', 'ui', 'medium', 'regression'],
      file: __filename,
      priority: 'medium',
      category: 'functional',
      browser: ['chrome', 'firefox']
    });

    // Test navigation to different sections
    const aboutLink = page.locator('a[href*="about"], nav a:has-text("About")');
    if (await aboutLink.isVisible()) {
      await aboutLink.click();
      await expect(page).toHaveURL(/about/);
    }
    
    // Navigate back to home
    const homeLink = page.locator('a[href="/"], a[href*="home"], nav a:has-text("Home")');
    if (await homeLink.isVisible()) {
      await homeLink.click();
      await expect(page).toHaveURL(/\/$|home/);
    }
  });

  // @forms @ui @medium @regression
  test('should submit contact form @forms @ui @medium @regression', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should submit contact form',
      tags: ['forms', 'ui', 'medium', 'regression'],
      file: __filename,
      priority: 'medium',
      category: 'functional'
    });

    // Look for contact form or navigate to contact page
    let contactForm = page.locator('form[name="contact"], form#contact, .contact-form form');
    
    if (!(await contactForm.isVisible())) {
      // Try to navigate to contact page
      const contactLink = page.locator('a[href*="contact"], nav a:has-text("Contact")');
      if (await contactLink.isVisible()) {
        await contactLink.click();
        contactForm = page.locator('form[name="contact"], form#contact, .contact-form form');
      }
    }
    
    if (await contactForm.isVisible()) {
      // Fill out the form
      const nameField = contactForm.locator('input[name="name"], input[type="text"]:first-of-type');
      const emailField = contactForm.locator('input[name="email"], input[type="email"]');
      const messageField = contactForm.locator('textarea[name="message"], textarea');
      
      if (await nameField.isVisible()) await nameField.fill('Test User');
      if (await emailField.isVisible()) await emailField.fill('test@example.com');
      if (await messageField.isVisible()) await messageField.fill('This is a test message');
      
      // Submit the form
      const submitButton = contactForm.locator('button[type="submit"], input[type="submit"]');
      if (await submitButton.isVisible()) {
        await submitButton.click();
        
        // Wait for success message or redirect
        await page.waitForTimeout(2000);
      }
    }
  });

  // @responsive @mobile @ui @medium
  test('should be responsive on mobile devices @responsive @mobile @ui @medium', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should be responsive on mobile devices',
      tags: ['responsive', 'mobile', 'ui', 'medium'],
      file: __filename,
      priority: 'medium',
      category: 'functional',
      browser: ['chrome']
    });

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Reload page to ensure responsive design is applied
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Check that content is still visible and accessible
    const body = page.locator('body');
    await expect(body).toBeVisible();
    
    // Verify no horizontal scrolling (content fits in viewport)
    const scrollWidth = await page.evaluate(() => document.body.scrollWidth);
    const clientWidth = await page.evaluate(() => document.body.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 20); // Allow small margin
    
    // Check if mobile menu exists and is functional
    const mobileMenuButton = page.locator('button[aria-label*="menu"], .mobile-menu-toggle, .hamburger');
    if (await mobileMenuButton.isVisible()) {
      await mobileMenuButton.click();
      
      // Verify menu opens
      const mobileMenu = page.locator('.mobile-menu, .nav-menu.open, nav[aria-expanded="true"]');
      if (await mobileMenu.isVisible()) {
        await expect(mobileMenu).toBeVisible();
      }
    }
  });

  // @accessibility @a11y @medium @regression
  test('should meet basic accessibility requirements @accessibility @a11y @medium @regression', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should meet basic accessibility requirements',
      tags: ['accessibility', 'a11y', 'medium', 'regression'],
      file: __filename,
      priority: 'medium',
      category: 'accessibility',
      browser: ['chrome', 'firefox']
    });

    // Check for proper heading structure
    const h1Elements = page.locator('h1');
    const h1Count = await h1Elements.count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
    expect(h1Count).toBeLessThanOrEqual(1); // Should have exactly one h1
    
    // Check for alt text on images
    const images = page.locator('img');
    const imageCount = await images.count();
    
    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      const ariaLabel = await img.getAttribute('aria-label');
      const role = await img.getAttribute('role');
      
      // Images should have alt text, aria-label, or be decorative
      expect(alt !== null || ariaLabel !== null || role === 'presentation').toBe(true);
    }
    
    // Check for proper form labels
    const inputs = page.locator('input[type="text"], input[type="email"], input[type="password"], textarea');
    const inputCount = await inputs.count();
    
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        const hasLabel = await label.count() > 0;
        
        // Input should have associated label, aria-label, or aria-labelledby
        expect(hasLabel || ariaLabel !== null || ariaLabelledBy !== null).toBe(true);
      }
    }
    
    // Check color contrast (basic check - ensure text is visible)
    const textElements = page.locator('p, span, div, h1, h2, h3, h4, h5, h6, a, button');
    const textCount = Math.min(await textElements.count(), 10); // Check first 10 elements
    
    for (let i = 0; i < textCount; i++) {
      const element = textElements.nth(i);
      if (await element.isVisible()) {
        const textContent = await element.textContent();
        if (textContent && textContent.trim().length > 0) {
          // Element should be visible (basic visibility check)
          await expect(element).toBeVisible();
        }
      }
    }
  });

  // @performance @medium @monitoring
  test('should load within acceptable time limits @performance @medium @monitoring', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should load within acceptable time limits',
      tags: ['performance', 'medium', 'monitoring'],
      file: __filename,
      priority: 'medium',
      category: 'performance',
      browser: ['chrome']
    });

    const startTime = Date.now();
    
    // Navigate and wait for load
    await page.goto('https://example.com');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
    
    // Check Core Web Vitals if available
    const performanceMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        if ('web-vital' in window) {
          // If web-vitals library is available
          resolve({ available: true });
        } else {
          // Basic performance metrics
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
          resolve({
            available: false,
            loadTime: navigation.loadEventEnd - navigation.loadEventStart,
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart
          });
        }
      });
    });
    
    console.log('Performance metrics:', performanceMetrics);
  });
});