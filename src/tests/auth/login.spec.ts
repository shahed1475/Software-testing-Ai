import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/LoginPage';
import { HomePage } from '../../pages/HomePage';
import { DashboardPage } from '../../pages/DashboardPage';
import { TagManager } from '../../utils/TagManager';

test.describe('Login Functionality', () => {
  let loginPage: LoginPage;
  let homePage: HomePage;
  let dashboardPage: DashboardPage;
  const tagManager = TagManager.getInstance();

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    homePage = new HomePage(page);
    dashboardPage = new DashboardPage(page);
    
    // Navigate to login page before each test
    await loginPage.navigateToLogin();
  });

  test.afterEach(async ({ page }) => {
    // Take screenshot on failure
    if (test.info().status !== test.info().expectedStatus) {
      await page.screenshot({ 
        path: `test-results/login-failure-${Date.now()}.png`,
        fullPage: true 
      });
    }
  });

  // @smoke @ui @auth @critical
  test('should display login form elements @smoke @ui @auth @critical', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should display login form elements',
      tags: ['smoke', 'ui', 'auth', 'critical'],
      file: __filename,
      priority: 'critical',
      category: 'functional',
      browser: ['chrome', 'firefox', 'safari']
    });

    // Validate that all login form elements are present
    await loginPage.validateLoginFormElements();
    
    // Check individual elements
    expect(await loginPage.isUsernameFieldVisible()).toBe(true);
    expect(await loginPage.isPasswordFieldVisible()).toBe(true);
    expect(await loginPage.isLoginButtonVisible()).toBe(true);
  });

  // @auth @critical @smoke @e2e
  test('should login with valid credentials @auth @critical @smoke @e2e', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should login with valid credentials',
      tags: ['auth', 'critical', 'smoke', 'e2e'],
      file: __filename,
      priority: 'critical',
      category: 'functional',
      browser: ['chrome', 'firefox', 'safari']
    });

    // Perform login with valid credentials
    await loginPage.login('testuser@example.com', 'password123');
    
    // Verify successful login by checking URL or dashboard elements
    await expect(page).toHaveURL(/dashboard|home/);
    
    // Verify user is logged in by checking dashboard elements
    await dashboardPage.waitForDashboardLoad();
    await dashboardPage.validateDashboardElements();
  });

  // @auth @high @regression @security
  test('should show error for invalid credentials @auth @high @regression @security', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should show error for invalid credentials',
      tags: ['auth', 'high', 'regression', 'security'],
      file: __filename,
      priority: 'high',
      category: 'functional',
      browser: ['chrome', 'firefox']
    });

    // Attempt login with invalid credentials
    await loginPage.login('invalid@example.com', 'wrongpassword');
    
    // Verify error message is displayed
    expect(await loginPage.isErrorMessageVisible()).toBe(true);
    
    const errorMessage = await loginPage.getErrorMessage();
    expect(errorMessage).toContain('Invalid credentials');
  });

  // @auth @medium @regression
  test('should show error for empty username @auth @medium @regression', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should show error for empty username',
      tags: ['auth', 'medium', 'regression'],
      file: __filename,
      priority: 'medium',
      category: 'functional'
    });

    // Attempt login with empty username
    await loginPage.enterPassword('password123');
    await loginPage.clickLoginButton();
    
    // Verify validation error
    expect(await loginPage.isErrorMessageVisible()).toBe(true);
    
    const errorMessage = await loginPage.getErrorMessage();
    expect(errorMessage).toContain('Username is required');
  });

  // @auth @medium @regression
  test('should show error for empty password @auth @medium @regression', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should show error for empty password',
      tags: ['auth', 'medium', 'regression'],
      file: __filename,
      priority: 'medium',
      category: 'functional'
    });

    // Attempt login with empty password
    await loginPage.enterUsername('testuser@example.com');
    await loginPage.clickLoginButton();
    
    // Verify validation error
    expect(await loginPage.isErrorMessageVisible()).toBe(true);
    
    const errorMessage = await loginPage.getErrorMessage();
    expect(errorMessage).toContain('Password is required');
  });

  // @auth @ui @low @accessibility
  test('should toggle password visibility @auth @ui @low @accessibility', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'should toggle password visibility',
      tags: ['auth', 'ui', 'low', 'accessibility'],
      file: __filename,
      priority: 'low',
      category: 'functional'
    });

    // Enter password
    await loginPage.enterPassword('secretpassword');
    
    // Toggle password visibility
    await loginPage.togglePasswordVisibility();
    
    // Verify password is visible (implementation depends on your app)
    // This is a placeholder - adjust based on your actual implementation
    const passwordField = await loginPage.getPasswordFieldType();
    expect(passwordField).toBe('text');
    
    // Toggle back to hidden
    await loginPage.togglePasswordVisibility();
    const hiddenPasswordField = await loginPage.getPasswordFieldType();
    expect(hiddenPasswordField).toBe('password');
  });

  test('should handle remember me functionality', async ({ page }) => {
    // Check remember me option
    await loginPage.checkRememberMe();
    
    // Perform login
    await loginPage.login('testuser@example.com', 'password123');
    
    // Verify successful login
    await expect(page).toHaveURL(/dashboard|home/);
    
    // Note: In a real test, you might want to verify that the user
    // remains logged in after browser restart or session timeout
  });

  test('should navigate to forgot password page', async ({ page }) => {
    // Click forgot password link
    await loginPage.clickForgotPassword();
    
    // Verify navigation to forgot password page
    await expect(page).toHaveURL(/forgot-password|reset-password/);
  });

  test('should navigate to sign up page', async ({ page }) => {
    // Click sign up link
    await loginPage.clickSignUp();
    
    // Verify navigation to sign up page
    await expect(page).toHaveURL(/signup|register/);
  });

  test('should handle login with different user roles', async ({ page }) => {
    // Test admin user login
    await loginPage.login('admin@example.com', 'adminpass123');
    await expect(page).toHaveURL(/dashboard|admin/);
    
    // Verify admin privileges
    await dashboardPage.waitForDashboardLoad();
    expect(await dashboardPage.hasAdminPrivileges()).toBe(true);
  });

  test('should handle social login options', async () => {
    // Check if social login options are available
    const hasSocialLogin = await loginPage.hasSocialLoginOptions();
    
    if (hasSocialLogin) {
      // Test Google login button presence
      expect(await loginPage.isGoogleLoginVisible()).toBe(true);
      
      // Test Facebook login button presence  
      expect(await loginPage.isFacebookLoginVisible()).toBe(true);
      
      // Note: Actual social login testing would require additional setup
      // and might be better handled in integration tests
    }
  });

  test('should validate form field constraints', async () => {
    // Test username field constraints
    await loginPage.enterUsername('a'); // Too short
    await loginPage.clickLoginButton();
    
    let errorMessage = await loginPage.getErrorMessage();
    expect(errorMessage).toContain('Username must be at least');
    
    // Test password field constraints
    await loginPage.clearUsername();
    await loginPage.enterUsername('validuser@example.com');
    await loginPage.enterPassword('123'); // Too short
    await loginPage.clickLoginButton();
    
    errorMessage = await loginPage.getErrorMessage();
    expect(errorMessage).toContain('Password must be at least');
  });

  test('should handle login form submission with Enter key', async ({ page }) => {
    // Enter credentials
    await loginPage.enterUsername('testuser@example.com');
    await loginPage.enterPassword('password123');
    
    // Submit form using Enter key
    await page.keyboard.press('Enter');
    
    // Verify successful login
    await expect(page).toHaveURL(/dashboard|home/);
  });

  test('should clear form fields', async () => {
    // Enter some data
    await loginPage.enterUsername('testuser@example.com');
    await loginPage.enterPassword('password123');
    
    // Clear fields
    await loginPage.clearUsername();
    await loginPage.clearPassword();
    
    // Verify fields are empty
    expect(await loginPage.getUsernameValue()).toBe('');
    expect(await loginPage.getPasswordValue()).toBe('');
  });

  test('should handle multiple failed login attempts', async () => {
    // Attempt multiple failed logins
    for (let i = 0; i < 3; i++) {
      await loginPage.login('invalid@example.com', 'wrongpassword');
      
      // Verify error message
      expect(await loginPage.isErrorMessageVisible()).toBe(true);
      
      // Clear form for next attempt
      await loginPage.clearUsername();
      await loginPage.clearPassword();
    }
    
    // After multiple failures, account might be locked
    // This depends on your application's security implementation
    await loginPage.login('invalid@example.com', 'wrongpassword');
    const errorMessage = await loginPage.getErrorMessage();
    
    // Check for account lockout message (adjust based on your app)
    expect(errorMessage).toMatch(/locked|blocked|too many attempts/i);
  });

  test('should maintain login state across page navigation', async ({ page }) => {
    // Login successfully
    await loginPage.login('testuser@example.com', 'password123');
    await expect(page).toHaveURL(/dashboard|home/);
    
    // Navigate to home page
    await homePage.navigateToHome();
    
    // Verify user is still logged in
    expect(await homePage.isUserLoggedIn()).toBe(true);
    
    // Navigate back to dashboard
    await homePage.navigateToDashboard();
    await dashboardPage.waitForDashboardLoad();
    
    // Verify dashboard loads properly for logged-in user
    await dashboardPage.validateDashboardElements();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await loginPage.login('testuser@example.com', 'password123');
    await expect(page).toHaveURL(/dashboard|home/);
    
    // Navigate to dashboard and logout
    await dashboardPage.waitForDashboardLoad();
    await dashboardPage.logout();
    
    // Verify logout by checking URL
    await expect(page).toHaveURL(/login|home|\/$/, { timeout: 10000 });
    
    // Verify user is no longer logged in
    await homePage.navigateToHome();
    expect(await homePage.isUserLoggedIn()).toBe(false);
  });
});

test.describe('Login Accessibility', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.navigateToLogin();
  });

  test('should have proper form labels and accessibility attributes', async ({ page }) => {
    // Check for proper labels
    const usernameLabel = page.locator('label[for*="username"], label[for*="email"]');
    const passwordLabel = page.locator('label[for*="password"]');
    
    await expect(usernameLabel).toBeVisible();
    await expect(passwordLabel).toBeVisible();
    
    // Check for ARIA attributes
    const usernameField = page.locator('input[type="email"], input[type="text"]').first();
    const passwordField = page.locator('input[type="password"]');
    
    // Verify required attributes
    await expect(usernameField).toHaveAttribute('required');
    await expect(passwordField).toHaveAttribute('required');
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Tab through form elements
    await page.keyboard.press('Tab'); // Username field
    await expect(page.locator('input[type="email"], input[type="text"]').first()).toBeFocused();
    
    await page.keyboard.press('Tab'); // Password field
    await expect(page.locator('input[type="password"]')).toBeFocused();
    
    await page.keyboard.press('Tab'); // Login button
    await expect(page.locator('button[type="submit"], .login-btn')).toBeFocused();
  });
});

test.describe('Login Performance', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
  });

  test('should load login page within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await loginPage.navigateToLogin();
    await loginPage.waitForLoginPageLoad();
    
    const loadTime = Date.now() - startTime;
    
    // Assert page loads within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle login submission within acceptable time', async ({ page }) => {
    await loginPage.navigateToLogin();
    
    const startTime = Date.now();
    
    await loginPage.login('testuser@example.com', 'password123');
    await expect(page).toHaveURL(/dashboard|home/);
    
    const loginTime = Date.now() - startTime;
    
    // Assert login completes within 5 seconds
    expect(loginTime).toBeLessThan(5000);
  });
});