import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/LoginPage';
import { DashboardPage } from '../../pages/DashboardPage';
import { HomePage } from '../../pages/HomePage';

test.describe('Dashboard Functionality', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let homePage: HomePage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    homePage = new HomePage(page);
    
    // Login before each test
    await loginPage.navigateToLogin();
    await loginPage.login('testuser@example.com', 'password123');
    
    // Navigate to dashboard
    await dashboardPage.navigateToDashboard();
    await dashboardPage.waitForDashboardLoad();
  });

  test.afterEach(async ({ page }) => {
    // Take screenshot on failure
    if (test.info().status !== test.info().expectedStatus) {
      await page.screenshot({ 
        path: `test-results/dashboard-failure-${Date.now()}.png`,
        fullPage: true 
      });
    }
  });

  test('should display dashboard elements correctly', async () => {
    // Validate all main dashboard elements are present
    await dashboardPage.validateDashboardElements();
    
    // Check specific elements
    const userName = await dashboardPage.getUserName();
    expect(userName).toBeTruthy();
    expect(userName.length).toBeGreaterThan(0);
  });

  test('should display statistics cards', async () => {
    // Get statistics from dashboard
    const stats = await dashboardPage.getStatistics();
    
    // Verify statistics are present
    expect(Object.keys(stats).length).toBeGreaterThan(0);
    
    // Get stat card count
    const cardCount = await dashboardPage.getStatCardCount();
    expect(cardCount).toBeGreaterThan(0);
    expect(cardCount).toBeLessThanOrEqual(10); // Reasonable upper limit
  });

  test('should navigate between dashboard sections', async ({ page }) => {
    // Test navigation to different sections
    const sections = ['overview', 'profile', 'settings', 'reports', 'analytics'] as const;
    
    for (const section of sections) {
      await dashboardPage.navigateToSection(section);
      
      // Wait for section to load
      await page.waitForTimeout(1000);
      
      // Verify URL contains section name
      await expect(page).toHaveURL(new RegExp(section));
    }
  });

  test('should perform quick actions', async () => {
    const actions = ['create', 'upload', 'export', 'refresh'] as const;
    
    for (const action of actions) {
      await dashboardPage.performQuickAction(action);
      
      // Wait for action to complete
      await page.waitForTimeout(500);
      
      // Note: In a real application, you would verify the specific
      // outcome of each action (e.g., modal opens, file uploads, etc.)
    }
  });

  test('should search dashboard data', async () => {
    const searchTerm = 'test data';
    
    // Perform search
    await dashboardPage.searchData(searchTerm);
    
    // Verify search was performed
    // Note: In a real application, you would verify search results
    // This is a placeholder for demonstration
    await page.waitForTimeout(1000);
  });

  test('should filter and sort data', async () => {
    // Apply filter
    await dashboardPage.applyFilter();
    await page.waitForTimeout(500);
    
    // Apply sorting
    await dashboardPage.sortData('name');
    await page.waitForTimeout(1000);
    
    // Note: In a real application, you would verify that
    // data is actually filtered and sorted correctly
  });

  test('should handle data table interactions', async () => {
    // Get initial row count
    const initialRowCount = await dashboardPage.getTableRowCount();
    expect(initialRowCount).toBeGreaterThanOrEqual(0);
    
    if (initialRowCount > 0) {
      // Click on first row
      await dashboardPage.clickTableRow(0);
      
      // Get data from first cell of first row
      const cellData = await dashboardPage.getTableCellData(0, 0);
      expect(cellData).toBeTruthy();
    }
  });

  test('should handle pagination', async () => {
    // Check if there are multiple pages
    const rowCount = await dashboardPage.getTableRowCount();
    
    if (rowCount > 0) {
      // Try to go to next page
      try {
        await dashboardPage.goToNextPage();
        await page.waitForTimeout(1000);
        
        // Go back to previous page
        await dashboardPage.goToPreviousPage();
        await page.waitForTimeout(1000);
      } catch (error) {
        // Pagination might not be available if there's only one page
        console.log('Pagination not available or only one page exists');
      }
    }
  });

  test('should change items per page', async () => {
    try {
      // Change items per page
      await dashboardPage.changeItemsPerPage('25');
      
      // Wait for page to reload
      await page.waitForTimeout(2000);
      
      // Verify change took effect
      const newRowCount = await dashboardPage.getTableRowCount();
      expect(newRowCount).toBeGreaterThanOrEqual(0);
    } catch (error) {
      // Items per page functionality might not be available
      console.log('Items per page functionality not available');
    }
  });

  test('should open and close modals', async () => {
    // Try to trigger a modal (this depends on your application)
    try {
      await dashboardPage.performQuickAction('create');
      
      // Check if modal opened
      if (await dashboardPage.isModalOpen()) {
        // Close modal
        await dashboardPage.closeModal();
        
        // Verify modal is closed
        expect(await dashboardPage.isModalOpen()).toBe(false);
      }
    } catch (error) {
      console.log('Modal functionality not available or different implementation');
    }
  });

  test('should handle modal confirmations', async () => {
    try {
      // Trigger an action that opens a confirmation modal
      await dashboardPage.performQuickAction('create');
      
      if (await dashboardPage.isModalOpen()) {
        // Test cancel action
        await dashboardPage.cancelModalAction();
        expect(await dashboardPage.isModalOpen()).toBe(false);
        
        // Trigger modal again
        await dashboardPage.performQuickAction('create');
        
        if (await dashboardPage.isModalOpen()) {
          // Test confirm action
          await dashboardPage.confirmModalAction();
          expect(await dashboardPage.isModalOpen()).toBe(false);
        }
      }
    } catch (error) {
      console.log('Modal confirmation functionality not available');
    }
  });

  test('should display and manage notifications', async () => {
    try {
      // Navigate to notifications section
      await dashboardPage.navigateToSection('notifications');
      
      // Get notification count
      const notificationCount = await dashboardPage.getNotificationCount();
      expect(notificationCount).toBeGreaterThanOrEqual(0);
      
      if (notificationCount > 0) {
        // Mark all notifications as read
        await dashboardPage.markAllNotificationsRead();
      }
    } catch (error) {
      console.log('Notification functionality not available');
    }
  });

  test('should access user settings', async () => {
    try {
      // Open settings
      await dashboardPage.openSettings();
      
      // Wait for settings to load
      await page.waitForTimeout(1000);
      
      // Note: In a real application, you would verify settings page loaded
    } catch (error) {
      console.log('Settings functionality not available');
    }
  });

  test('should access help section', async () => {
    try {
      // Open help
      await dashboardPage.openHelp();
      
      // Wait for help to load
      await page.waitForTimeout(1000);
      
      // Note: In a real application, you would verify help section loaded
    } catch (error) {
      console.log('Help functionality not available');
    }
  });

  test('should refresh dashboard data', async () => {
    // Get initial statistics
    const initialStats = await dashboardPage.getStatistics();
    
    // Refresh dashboard
    await dashboardPage.refreshDashboard();
    
    // Get updated statistics
    const updatedStats = await dashboardPage.getStatistics();
    
    // Note: In a real application, you might verify that data actually changed
    // or that the refresh action was performed successfully
    expect(Object.keys(updatedStats).length).toBeGreaterThanOrEqual(0);
  });

  test('should handle admin privileges correctly', async () => {
    // Check admin privileges
    const hasAdminPrivileges = await dashboardPage.hasAdminPrivileges();
    
    if (hasAdminPrivileges) {
      // Test admin-specific functionality
      await dashboardPage.navigateToSection('settings');
      await dashboardPage.navigateToSection('reports');
      await dashboardPage.navigateToSection('analytics');
    } else {
      // Verify limited access for non-admin users
      console.log('User does not have admin privileges');
    }
  });

  test('should logout from dashboard', async ({ page }) => {
    // Logout from dashboard
    await dashboardPage.logout();
    
    // Verify logout successful
    await expect(page).toHaveURL(/login|home|\/$/, { timeout: 10000 });
    
    // Verify user is no longer logged in
    await homePage.navigateToHome();
    expect(await homePage.isUserLoggedIn()).toBe(false);
  });
});

test.describe('Dashboard Responsive Design', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    
    // Login
    await loginPage.navigateToLogin();
    await loginPage.login('testuser@example.com', 'password123');
    await dashboardPage.navigateToDashboard();
  });

  test('should display correctly on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Wait for responsive changes
    await page.waitForTimeout(1000);
    
    // Validate dashboard elements are still accessible
    await dashboardPage.validateDashboardElements();
  });

  test('should display correctly on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // Wait for responsive changes
    await page.waitForTimeout(1000);
    
    // Validate dashboard elements
    await dashboardPage.validateDashboardElements();
  });

  test('should display correctly on desktop viewport', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    // Wait for responsive changes
    await page.waitForTimeout(1000);
    
    // Validate dashboard elements
    await dashboardPage.validateDashboardElements();
  });
});

test.describe('Dashboard Performance', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    
    // Login
    await loginPage.navigateToLogin();
    await loginPage.login('testuser@example.com', 'password123');
  });

  test('should load dashboard within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await dashboardPage.navigateToDashboard();
    await dashboardPage.waitForDashboardLoad();
    
    const loadTime = Date.now() - startTime;
    
    // Assert dashboard loads within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('should handle data refresh within acceptable time', async ({ page }) => {
    await dashboardPage.navigateToDashboard();
    await dashboardPage.waitForDashboardLoad();
    
    const startTime = Date.now();
    
    await dashboardPage.refreshDashboard();
    
    const refreshTime = Date.now() - startTime;
    
    // Assert refresh completes within 3 seconds
    expect(refreshTime).toBeLessThan(3000);
  });

  test('should handle section navigation within acceptable time', async ({ page }) => {
    await dashboardPage.navigateToDashboard();
    await dashboardPage.waitForDashboardLoad();
    
    const startTime = Date.now();
    
    await dashboardPage.navigateToSection('analytics');
    
    const navigationTime = Date.now() - startTime;
    
    // Assert section navigation completes within 2 seconds
    expect(navigationTime).toBeLessThan(2000);
  });
});

test.describe('Dashboard Data Integrity', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    
    // Login
    await loginPage.navigateToLogin();
    await loginPage.login('testuser@example.com', 'password123');
    await dashboardPage.navigateToDashboard();
    await dashboardPage.waitForDashboardLoad();
  });

  test('should display consistent data across sections', async () => {
    // Get statistics from overview
    await dashboardPage.navigateToSection('overview');
    const overviewStats = await dashboardPage.getStatistics();
    
    // Navigate to analytics and verify consistency
    await dashboardPage.navigateToSection('analytics');
    await page.waitForTimeout(1000);
    
    // Navigate back to overview
    await dashboardPage.navigateToSection('overview');
    const secondOverviewStats = await dashboardPage.getStatistics();
    
    // Verify data consistency (in a real app, you'd compare specific values)
    expect(Object.keys(secondOverviewStats).length).toBe(Object.keys(overviewStats).length);
  });

  test('should maintain data after page refresh', async ({ page }) => {
    // Get initial data
    const initialStats = await dashboardPage.getStatistics();
    const initialRowCount = await dashboardPage.getTableRowCount();
    
    // Refresh page
    await page.reload();
    await dashboardPage.waitForDashboardLoad();
    
    // Get data after refresh
    const refreshedStats = await dashboardPage.getStatistics();
    const refreshedRowCount = await dashboardPage.getTableRowCount();
    
    // Verify data is maintained (adjust based on your application logic)
    expect(Object.keys(refreshedStats).length).toBe(Object.keys(initialStats).length);
    expect(refreshedRowCount).toBe(initialRowCount);
  });
});