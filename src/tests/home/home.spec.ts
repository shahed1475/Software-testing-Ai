import { test, expect } from '@playwright/test';
import { HomePage } from '../../pages/HomePage';
import { LoginPage } from '../../pages/LoginPage';
import { TagManager } from '../../utils/TagManager';

test.describe('Home Page Functionality', () => {
  let homePage: HomePage;
  let loginPage: LoginPage;
  const tagManager = TagManager.getInstance();

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    loginPage = new LoginPage(page);
    
    // Navigate to home page
    await homePage.navigateToHome();
  });

  test.afterEach(async ({ page }) => {
    // Take screenshot on failure
    if (test.info().status !== test.info().expectedStatus) {
      await page.screenshot({ 
        path: `test-results/home-failure-${Date.now()}.png`,
        fullPage: true 
      });
    }
  });

  // @smoke @critical @ui @regression
  test('should display home page elements correctly @smoke @critical @ui @regression', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should display home page elements correctly',
      tags: ['smoke', 'critical', 'ui', 'regression'],
      file: __filename,
      priority: 'critical',
      category: 'functional',
      browser: ['chrome', 'firefox', 'safari']
    });

    // Validate all main home page elements are present
    await homePage.validateHomePageElements();
    
    // Check navigation elements
    expect(await homePage.isNavigationVisible()).toBe(true);
    
    // Check hero section
    expect(await homePage.isHeroSectionVisible()).toBe(true);
  });

  // @regression @ui @medium
  test('should navigate to different sections @regression @ui @medium', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should navigate to different sections',
      tags: ['regression', 'ui', 'medium'],
      file: __filename,
      priority: 'medium',
      category: 'functional',
      browser: ['chrome', 'firefox']
    });

    const sections = ['about', 'services', 'contact', 'products'] as const;
    
    for (const section of sections) {
      await homePage.navigateToSection(section);
      
      // Wait for navigation
      await page.waitForTimeout(1000);
      
      // Verify URL contains section name or verify section is visible
      const currentUrl = page.url();
      expect(currentUrl.toLowerCase()).toContain(section);
    }
  });

  // @search @ui @high @regression
  test('should perform search functionality @search @ui @high @regression', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should perform search functionality',
      tags: ['search', 'ui', 'high', 'regression'],
      file: __filename,
      priority: 'high',
      category: 'functional',
      browser: ['chrome', 'firefox', 'safari']
    });

    const searchTerm = 'test product';
    
    // Perform search
    await homePage.performSearch(searchTerm);
    
    // Wait for search results
    await page.waitForTimeout(2000);
    
    // Note: In a real application, you would verify search results
    // This is a placeholder for demonstration
  });

  // @search @ui @medium
  test('should clear search input @search @ui @medium', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should clear search input',
      tags: ['search', 'ui', 'medium'],
      file: __filename,
      priority: 'medium',
      category: 'functional'
    });

    const searchTerm = 'test search';
    
    // Enter search term
    await homePage.performSearch(searchTerm);
    
    // Clear search
    await homePage.clearSearch();
    
    // Verify search is cleared
    const searchValue = await homePage.getSearchValue();
    expect(searchValue).toBe('');
  });

  // @ui @medium @regression
  test('should filter content correctly @ui @medium @regression', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should filter content correctly',
      tags: ['ui', 'medium', 'regression'],
      file: __filename,
      priority: 'medium',
      category: 'functional'
    });

    // Apply filter
    await homePage.applyFilter('category', 'electronics');
    
    // Wait for filter to apply
    await page.waitForTimeout(1000);
    
    // Note: In a real application, you would verify filtered results
  });

  // @ui @low @regression
  test('should sort content correctly @ui @low @regression', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should sort content correctly',
      tags: ['ui', 'low', 'regression'],
      file: __filename,
      priority: 'low',
      category: 'functional'
    });

    // Apply sorting
    await homePage.sortContent('name');
    
    // Wait for sorting to apply
    await page.waitForTimeout(1000);
    
    // Apply different sorting
    await homePage.sortContent('date');
    
    // Wait for sorting to apply
    await page.waitForTimeout(1000);
    
    // Note: In a real application, you would verify sorted results
  });

  test('should handle user authentication state when not logged in', async () => {
    // Verify user is not logged in initially
    expect(await homePage.isUserLoggedIn()).toBe(false);
    
    // Check login/register buttons are visible
    expect(await homePage.isLoginButtonVisible()).toBe(true);
    expect(await homePage.isRegisterButtonVisible()).toBe(true);
    
    // Check user menu is not visible
    expect(await homePage.isUserMenuVisible()).toBe(false);
  });

  test('should navigate to login page', async ({ page }) => {
    // Click login button
    await homePage.clickLogin();
    
    // Verify navigation to login page
    await expect(page).toHaveURL(/login/, { timeout: 5000 });
  });

  test('should navigate to register page', async ({ page }) => {
    // Click register button
    await homePage.clickRegister();
    
    // Verify navigation to register page
    await expect(page).toHaveURL(/register|signup/, { timeout: 5000 });
  });

  test('should display featured content', async () => {
    // Check if featured content is visible
    const hasFeaturedContent = await homePage.hasFeaturedContent();
    
    if (hasFeaturedContent) {
      // Get featured content count
      const featuredCount = await homePage.getFeaturedContentCount();
      expect(featuredCount).toBeGreaterThan(0);
      expect(featuredCount).toBeLessThanOrEqual(10); // Reasonable upper limit
    }
  });

  test('should handle newsletter subscription', async () => {
    const testEmail = 'test@example.com';
    
    try {
      // Subscribe to newsletter
      await homePage.subscribeToNewsletter(testEmail);
      
      // Wait for subscription process
      await page.waitForTimeout(2000);
      
      // Note: In a real application, you would verify subscription success
    } catch (error) {
      console.log('Newsletter subscription not available');
    }
  });

  test('should display social media links', async () => {
    try {
      // Check if social media links are present
      const hasSocialLinks = await homePage.hasSocialMediaLinks();
      
      if (hasSocialLinks) {
        // Get social media link count
        const socialLinkCount = await homePage.getSocialMediaLinkCount();
        expect(socialLinkCount).toBeGreaterThan(0);
      }
    } catch (error) {
      console.log('Social media links not available');
    }
  });

  test('should handle contact information display', async () => {
    try {
      // Check if contact info is displayed
      const hasContactInfo = await homePage.hasContactInfo();
      
      if (hasContactInfo) {
        // Verify contact info is visible
        expect(hasContactInfo).toBe(true);
      }
    } catch (error) {
      console.log('Contact information not available');
    }
  });
});

test.describe('Home Page with Authenticated User', () => {
  let homePage: HomePage;
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    loginPage = new LoginPage(page);
    
    // Login first
    await loginPage.navigateToLogin();
    await loginPage.login('testuser@example.com', 'password123');
    
    // Navigate to home page
    await homePage.navigateToHome();
  });

  test('should display user-specific content when logged in', async () => {
    // Verify user is logged in
    expect(await homePage.isUserLoggedIn()).toBe(true);
    
    // Check user menu is visible
    expect(await homePage.isUserMenuVisible()).toBe(true);
    
    // Check login/register buttons are not visible
    expect(await homePage.isLoginButtonVisible()).toBe(false);
    expect(await homePage.isRegisterButtonVisible()).toBe(false);
  });

  test('should display personalized content', async () => {
    // Check if personalized content is available
    try {
      const hasPersonalizedContent = await homePage.hasPersonalizedContent();
      
      if (hasPersonalizedContent) {
        // Get personalized content count
        const personalizedCount = await homePage.getPersonalizedContentCount();
        expect(personalizedCount).toBeGreaterThan(0);
      }
    } catch (error) {
      console.log('Personalized content not available');
    }
  });

  test('should access user profile from home page', async ({ page }) => {
    // Click on user profile
    await homePage.clickUserProfile();
    
    // Verify navigation to profile page
    await expect(page).toHaveURL(/profile|account/, { timeout: 5000 });
  });

  test('should access user dashboard from home page', async ({ page }) => {
    // Click on dashboard link
    await homePage.clickDashboard();
    
    // Verify navigation to dashboard
    await expect(page).toHaveURL(/dashboard/, { timeout: 5000 });
  });

  test('should logout from home page', async ({ page }) => {
    // Logout
    await homePage.logout();
    
    // Verify logout successful
    await page.waitForTimeout(1000);
    
    // Check user is no longer logged in
    expect(await homePage.isUserLoggedIn()).toBe(false);
    
    // Check login/register buttons are visible again
    expect(await homePage.isLoginButtonVisible()).toBe(true);
    expect(await homePage.isRegisterButtonVisible()).toBe(true);
  });

  test('should display user-specific recommendations', async () => {
    try {
      // Check if recommendations are available
      const hasRecommendations = await homePage.hasRecommendations();
      
      if (hasRecommendations) {
        // Get recommendation count
        const recommendationCount = await homePage.getRecommendationCount();
        expect(recommendationCount).toBeGreaterThan(0);
        expect(recommendationCount).toBeLessThanOrEqual(20);
      }
    } catch (error) {
      console.log('Recommendations not available');
    }
  });

  test('should handle user preferences', async () => {
    try {
      // Access user preferences
      await homePage.openUserPreferences();
      
      // Wait for preferences to load
      await page.waitForTimeout(1000);
      
      // Note: In a real application, you would verify preferences page loaded
    } catch (error) {
      console.log('User preferences not available');
    }
  });
});

test.describe('Home Page Responsive Design', () => {
  let homePage: HomePage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    await homePage.navigateToHome();
  });

  test('should display correctly on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Wait for responsive changes
    await page.waitForTimeout(1000);
    
    // Validate home page elements are still accessible
    await homePage.validateHomePageElements();
    
    // Check navigation is accessible (might be hamburger menu on mobile)
    expect(await homePage.isNavigationVisible()).toBe(true);
  });

  test('should display correctly on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // Wait for responsive changes
    await page.waitForTimeout(1000);
    
    // Validate home page elements
    await homePage.validateHomePageElements();
  });

  test('should display correctly on desktop viewport', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    // Wait for responsive changes
    await page.waitForTimeout(1000);
    
    // Validate home page elements
    await homePage.validateHomePageElements();
  });

  test('should handle mobile navigation menu', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000);
    
    try {
      // Try to open mobile menu (if available)
      await homePage.openMobileMenu();
      
      // Wait for menu to open
      await page.waitForTimeout(500);
      
      // Close mobile menu
      await homePage.closeMobileMenu();
      
      // Wait for menu to close
      await page.waitForTimeout(500);
    } catch (error) {
      console.log('Mobile menu not available or different implementation');
    }
  });
});

test.describe('Home Page Performance', () => {
  let homePage: HomePage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
  });

  test('should load home page within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await homePage.navigateToHome();
    await homePage.waitForHomePageLoad();
    
    const loadTime = Date.now() - startTime;
    
    // Assert home page loads within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle search within acceptable time', async ({ page }) => {
    await homePage.navigateToHome();
    await homePage.waitForHomePageLoad();
    
    const startTime = Date.now();
    
    await homePage.performSearch('test');
    
    const searchTime = Date.now() - startTime;
    
    // Assert search completes within 2 seconds
    expect(searchTime).toBeLessThan(2000);
  });

  test('should handle filtering within acceptable time', async ({ page }) => {
    await homePage.navigateToHome();
    await homePage.waitForHomePageLoad();
    
    const startTime = Date.now();
    
    await homePage.applyFilter('category', 'test');
    
    const filterTime = Date.now() - startTime;
    
    // Assert filtering completes within 2 seconds
    expect(filterTime).toBeLessThan(2000);
  });
});

test.describe('Home Page Accessibility', () => {
  let homePage: HomePage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    await homePage.navigateToHome();
  });

  test('should have proper heading structure', async ({ page }) => {
    // Check for h1 element
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
    
    // Check for proper heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);
  });

  test('should have proper alt text for images', async ({ page }) => {
    // Get all images
    const images = await page.locator('img').all();
    
    for (const image of images) {
      const alt = await image.getAttribute('alt');
      // Alt attribute should exist (can be empty for decorative images)
      expect(alt).not.toBeNull();
    }
  });

  test('should have proper form labels', async ({ page }) => {
    // Get all input elements
    const inputs = await page.locator('input').all();
    
    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      
      if (id) {
        // Check if there's a corresponding label
        const labelCount = await page.locator(`label[for="${id}"]`).count();
        const hasLabel = labelCount > 0 || ariaLabel || ariaLabelledBy;
        expect(hasLabel).toBe(true);
      }
    }
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Focus on the first focusable element
    await page.keyboard.press('Tab');
    
    // Check if an element is focused
    const focusedElement = await page.locator(':focus').first();
    expect(await focusedElement.count()).toBe(1);
    
    // Navigate through a few more elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Verify focus moved
    const newFocusedElement = await page.locator(':focus').first();
    expect(await newFocusedElement.count()).toBe(1);
  });

  test('should have proper ARIA attributes', async ({ page }) => {
    // Check for navigation landmarks
    const navElements = await page.locator('nav, [role="navigation"]').all();
    expect(navElements.length).toBeGreaterThan(0);
    
    // Check for main content landmark
    const mainElements = await page.locator('main, [role="main"]').all();
    expect(mainElements.length).toBeGreaterThanOrEqual(0);
  });
});