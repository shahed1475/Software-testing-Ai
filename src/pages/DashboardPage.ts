import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * DashboardPage class representing the user dashboard functionality
 * Extends BasePage to inherit common page operations
 */
export class DashboardPage extends BasePage {
  // Header elements
  private readonly dashboardHeader: Locator;
  private readonly pageTitle: Locator;
  private readonly userAvatar: Locator;
  private readonly userName: Locator;
  private readonly settingsButton: Locator;
  private readonly helpButton: Locator;
  private readonly logoutButton: Locator;

  // Navigation sidebar
  private readonly sidebar: Locator;
  private readonly overviewTab: Locator;
  private readonly profileTab: Locator;
  private readonly settingsTab: Locator;
  private readonly reportsTab: Locator;
  private readonly analyticsTab: Locator;
  private readonly notificationsTab: Locator;

  // Main content area
  private readonly mainContent: Locator;
  private readonly welcomeCard: Locator;
  private readonly statsContainer: Locator;
  private readonly statCards: Locator;
  private readonly recentActivity: Locator;
  private readonly quickActions: Locator;

  // Statistics cards
  private readonly totalUsersCard: Locator;
  private readonly totalOrdersCard: Locator;
  private readonly revenueCard: Locator;
  private readonly performanceCard: Locator;

  // Quick action buttons
  private readonly createNewButton: Locator;
  private readonly uploadButton: Locator;
  private readonly exportButton: Locator;
  private readonly refreshButton: Locator;

  // Data tables and lists
  private readonly dataTable: Locator;
  private readonly tableHeaders: Locator;
  private readonly tableRows: Locator;
  private readonly paginationControls: Locator;
  private readonly itemsPerPageSelect: Locator;

  // Search and filters
  private readonly searchInput: Locator;
  private readonly filterButton: Locator;
  private readonly sortDropdown: Locator;
  private readonly dateRangePicker: Locator;

  // Modals and overlays
  private readonly modal: Locator;
  private readonly modalTitle: Locator;
  private readonly modalCloseButton: Locator;
  private readonly confirmButton: Locator;
  private readonly cancelButton: Locator;

  // Notifications
  private readonly notificationPanel: Locator;
  private readonly notificationItems: Locator;
  private readonly markAllReadButton: Locator;

  constructor(page: Page) {
    super(page);
    
    // Initialize header locators
    this.dashboardHeader = page.locator('[data-testid="dashboard-header"], .dashboard-header, .header');
    this.pageTitle = page.locator('[data-testid="page-title"], .page-title, h1');
    this.userAvatar = page.locator('[data-testid="user-avatar"], .user-avatar, .avatar');
    this.userName = page.locator('[data-testid="user-name"], .user-name');
    this.settingsButton = page.locator('[data-testid="settings-button"], .settings-btn');
    this.helpButton = page.locator('[data-testid="help-button"], .help-btn');
    this.logoutButton = page.locator('[data-testid="logout-button"], .logout-btn');

    // Initialize sidebar locators
    this.sidebar = page.locator('[data-testid="sidebar"], .sidebar, .navigation');
    this.overviewTab = page.locator('[data-testid="overview-tab"], a[href*="overview"]');
    this.profileTab = page.locator('[data-testid="profile-tab"], a[href*="profile"]');
    this.settingsTab = page.locator('[data-testid="settings-tab"], a[href*="settings"]');
    this.reportsTab = page.locator('[data-testid="reports-tab"], a[href*="reports"]');
    this.analyticsTab = page.locator('[data-testid="analytics-tab"], a[href*="analytics"]');
    this.notificationsTab = page.locator('[data-testid="notifications-tab"], a[href*="notifications"]');

    // Initialize main content locators
    this.mainContent = page.locator('[data-testid="main-content"], .main-content, .content');
    this.welcomeCard = page.locator('[data-testid="welcome-card"], .welcome-card');
    this.statsContainer = page.locator('[data-testid="stats-container"], .stats, .statistics');
    this.statCards = page.locator('[data-testid="stat-card"], .stat-card, .metric-card');
    this.recentActivity = page.locator('[data-testid="recent-activity"], .recent-activity');
    this.quickActions = page.locator('[data-testid="quick-actions"], .quick-actions');

    // Initialize statistics card locators
    this.totalUsersCard = page.locator('[data-testid="total-users"], .users-stat');
    this.totalOrdersCard = page.locator('[data-testid="total-orders"], .orders-stat');
    this.revenueCard = page.locator('[data-testid="revenue"], .revenue-stat');
    this.performanceCard = page.locator('[data-testid="performance"], .performance-stat');

    // Initialize quick action locators
    this.createNewButton = page.locator('[data-testid="create-new"], .create-btn');
    this.uploadButton = page.locator('[data-testid="upload"], .upload-btn');
    this.exportButton = page.locator('[data-testid="export"], .export-btn');
    this.refreshButton = page.locator('[data-testid="refresh"], .refresh-btn');

    // Initialize data table locators
    this.dataTable = page.locator('[data-testid="data-table"], .data-table, table');
    this.tableHeaders = page.locator('[data-testid="table-header"], th');
    this.tableRows = page.locator('[data-testid="table-row"], tbody tr');
    this.paginationControls = page.locator('[data-testid="pagination"], .pagination');
    this.itemsPerPageSelect = page.locator('[data-testid="items-per-page"], .items-per-page');

    // Initialize search and filter locators
    this.searchInput = page.locator('[data-testid="search-input"], .search-input');
    this.filterButton = page.locator('[data-testid="filter-button"], .filter-btn');
    this.sortDropdown = page.locator('[data-testid="sort-dropdown"], .sort-select');
    this.dateRangePicker = page.locator('[data-testid="date-range"], .date-picker');

    // Initialize modal locators
    this.modal = page.locator('[data-testid="modal"], .modal, .dialog');
    this.modalTitle = page.locator('[data-testid="modal-title"], .modal-title');
    this.modalCloseButton = page.locator('[data-testid="modal-close"], .modal-close');
    this.confirmButton = page.locator('[data-testid="confirm-button"], .confirm-btn');
    this.cancelButton = page.locator('[data-testid="cancel-button"], .cancel-btn');

    // Initialize notification locators
    this.notificationPanel = page.locator('[data-testid="notification-panel"], .notifications');
    this.notificationItems = page.locator('[data-testid="notification-item"], .notification');
    this.markAllReadButton = page.locator('[data-testid="mark-all-read"], .mark-read-btn');
  }

  /**
   * Navigate to the dashboard page
   */
  async navigateToDashboard(): Promise<void> {
    this.logger.stepStart('Navigate to Dashboard');
    
    try {
      await this.goto('/dashboard');
      await this.waitForDashboardLoad();
      this.logger.stepEnd('Navigate to Dashboard');
    } catch (error) {
      this.logger.stepFailed('Navigate to Dashboard', error as Error);
      throw error;
    }
  }

  /**
   * Wait for dashboard page to be fully loaded
   */
  async waitForDashboardLoad(): Promise<void> {
    this.logger.debug('Waiting for dashboard to load');
    
    try {
      await this.waitForElement(this.dashboardHeader);
      await this.waitForElement(this.sidebar);
      await this.waitForElement(this.mainContent);
      
      // Wait for key dashboard elements
      await Promise.race([
        this.waitForElement(this.welcomeCard, 5000),
        this.waitForElement(this.statsContainer, 5000),
      ]);
      
      this.logger.debug('Dashboard loaded successfully');
    } catch (error) {
      this.logger.error('Dashboard failed to load properly');
      await this.takeScreenshot('dashboard-load-failed');
      throw error;
    }
  }

  /**
   * Get the current user's name from the dashboard
   */
  async getUserName(): Promise<string> {
    this.logger.stepStart('Get User Name');
    
    try {
      const name = await this.getElementText(this.userName);
      this.logger.stepEnd('Get User Name', undefined, { name });
      return name;
    } catch (error) {
      this.logger.stepFailed('Get User Name', error as Error);
      throw error;
    }
  }

  /**
   * Navigate to a specific dashboard section
   * @param section - The section to navigate to
   */
  async navigateToSection(section: 'overview' | 'profile' | 'settings' | 'reports' | 'analytics' | 'notifications'): Promise<void> {
    this.logger.stepStart('Navigate to Dashboard Section', { section });
    
    try {
      const sectionMap = {
        overview: this.overviewTab,
        profile: this.profileTab,
        settings: this.settingsTab,
        reports: this.reportsTab,
        analytics: this.analyticsTab,
        notifications: this.notificationsTab,
      };

      const targetSection = sectionMap[section];
      if (!targetSection) {
        throw new Error(`Unknown dashboard section: ${section}`);
      }

      await this.clickElement(targetSection);
      this.logger.userAction('click', `${section} tab`);
      
      // Wait for section to load
      await this.page.waitForTimeout(1000);
      
      this.logger.stepEnd('Navigate to Dashboard Section');
    } catch (error) {
      this.logger.stepFailed('Navigate to Dashboard Section', error as Error);
      throw error;
    }
  }

  /**
   * Get statistics from dashboard cards
   */
  async getStatistics(): Promise<Record<string, string>> {
    this.logger.stepStart('Get Dashboard Statistics');
    
    try {
      const stats: Record<string, string> = {};
      
      // Get individual stat values if cards are visible
      if (await this.isElementVisible(this.totalUsersCard)) {
        stats.totalUsers = await this.getElementText(this.totalUsersCard);
      }
      
      if (await this.isElementVisible(this.totalOrdersCard)) {
        stats.totalOrders = await this.getElementText(this.totalOrdersCard);
      }
      
      if (await this.isElementVisible(this.revenueCard)) {
        stats.revenue = await this.getElementText(this.revenueCard);
      }
      
      if (await this.isElementVisible(this.performanceCard)) {
        stats.performance = await this.getElementText(this.performanceCard);
      }
      
      this.logger.stepEnd('Get Dashboard Statistics', undefined, { stats });
      return stats;
    } catch (error) {
      this.logger.stepFailed('Get Dashboard Statistics', error as Error);
      throw error;
    }
  }

  /**
   * Get the count of statistics cards
   */
  async getStatCardCount(): Promise<number> {
    this.logger.stepStart('Get Stat Card Count');
    
    try {
      const count = await this.statCards.count();
      this.logger.stepEnd('Get Stat Card Count', undefined, { count });
      return count;
    } catch (error) {
      this.logger.stepFailed('Get Stat Card Count', error as Error);
      throw error;
    }
  }

  /**
   * Click on a quick action button
   * @param action - The action to perform
   */
  async performQuickAction(action: 'create' | 'upload' | 'export' | 'refresh'): Promise<void> {
    this.logger.stepStart('Perform Quick Action', { action });
    
    try {
      const actionMap = {
        create: this.createNewButton,
        upload: this.uploadButton,
        export: this.exportButton,
        refresh: this.refreshButton,
      };

      const targetButton = actionMap[action];
      if (!targetButton) {
        throw new Error(`Unknown quick action: ${action}`);
      }

      await this.clickElement(targetButton);
      this.logger.userAction('click', `${action} button`);
      this.logger.stepEnd('Perform Quick Action');
    } catch (error) {
      this.logger.stepFailed('Perform Quick Action', error as Error);
      throw error;
    }
  }

  /**
   * Search for data in the dashboard
   * @param searchTerm - Term to search for
   */
  async searchData(searchTerm: string): Promise<void> {
    this.logger.stepStart('Search Dashboard Data', { searchTerm });
    
    try {
      await this.fillText(this.searchInput, searchTerm);
      await this.page.keyboard.press('Enter');
      this.logger.userAction('search', 'dashboard search', searchTerm);
      
      // Wait for search results to load
      await this.page.waitForTimeout(1000);
      
      this.logger.stepEnd('Search Dashboard Data');
    } catch (error) {
      this.logger.stepFailed('Search Dashboard Data', error as Error);
      throw error;
    }
  }

  /**
   * Apply filter to dashboard data
   */
  async applyFilter(): Promise<void> {
    this.logger.stepStart('Apply Dashboard Filter');
    
    try {
      await this.clickElement(this.filterButton);
      this.logger.userAction('click', 'filter button');
      
      // Wait for filter options to appear
      await this.page.waitForTimeout(500);
      
      this.logger.stepEnd('Apply Dashboard Filter');
    } catch (error) {
      this.logger.stepFailed('Apply Dashboard Filter', error as Error);
      throw error;
    }
  }

  /**
   * Sort data using dropdown
   * @param sortOption - Sort option to select
   */
  async sortData(sortOption: string): Promise<void> {
    this.logger.stepStart('Sort Dashboard Data', { sortOption });
    
    try {
      await this.selectOption(this.sortDropdown, sortOption);
      this.logger.userAction('select', 'sort dropdown', sortOption);
      
      // Wait for sorting to apply
      await this.page.waitForTimeout(1000);
      
      this.logger.stepEnd('Sort Dashboard Data');
    } catch (error) {
      this.logger.stepFailed('Sort Dashboard Data', error as Error);
      throw error;
    }
  }

  /**
   * Get the number of rows in the data table
   */
  async getTableRowCount(): Promise<number> {
    this.logger.stepStart('Get Table Row Count');
    
    try {
      const count = await this.tableRows.count();
      this.logger.stepEnd('Get Table Row Count', undefined, { count });
      return count;
    } catch (error) {
      this.logger.stepFailed('Get Table Row Count', error as Error);
      throw error;
    }
  }

  /**
   * Click on a specific table row
   * @param rowIndex - Index of the row to click (0-based)
   */
  async clickTableRow(rowIndex: number): Promise<void> {
    this.logger.stepStart('Click Table Row', { rowIndex });
    
    try {
      const row = this.tableRows.nth(rowIndex);
      await this.clickElement(row);
      this.logger.userAction('click', `table row ${rowIndex}`);
      this.logger.stepEnd('Click Table Row');
    } catch (error) {
      this.logger.stepFailed('Click Table Row', error as Error);
      throw error;
    }
  }

  /**
   * Get data from a specific table cell
   * @param rowIndex - Row index (0-based)
   * @param columnIndex - Column index (0-based)
   */
  async getTableCellData(rowIndex: number, columnIndex: number): Promise<string> {
    this.logger.stepStart('Get Table Cell Data', { rowIndex, columnIndex });
    
    try {
      const cell = this.tableRows.nth(rowIndex).locator('td').nth(columnIndex);
      const data = await this.getElementText(cell);
      this.logger.stepEnd('Get Table Cell Data', undefined, { data });
      return data;
    } catch (error) {
      this.logger.stepFailed('Get Table Cell Data', error as Error);
      throw error;
    }
  }

  /**
   * Navigate to next page in pagination
   */
  async goToNextPage(): Promise<void> {
    this.logger.stepStart('Go to Next Page');
    
    try {
      const nextButton = this.paginationControls.locator('button:has-text("Next"), .next');
      await this.clickElement(nextButton);
      this.logger.userAction('click', 'next page button');
      
      // Wait for page to load
      await this.page.waitForTimeout(1000);
      
      this.logger.stepEnd('Go to Next Page');
    } catch (error) {
      this.logger.stepFailed('Go to Next Page', error as Error);
      throw error;
    }
  }

  /**
   * Navigate to previous page in pagination
   */
  async goToPreviousPage(): Promise<void> {
    this.logger.stepStart('Go to Previous Page');
    
    try {
      const prevButton = this.paginationControls.locator('button:has-text("Previous"), .prev');
      await this.clickElement(prevButton);
      this.logger.userAction('click', 'previous page button');
      
      // Wait for page to load
      await this.page.waitForTimeout(1000);
      
      this.logger.stepEnd('Go to Previous Page');
    } catch (error) {
      this.logger.stepFailed('Go to Previous Page', error as Error);
      throw error;
    }
  }

  /**
   * Change items per page
   * @param itemsPerPage - Number of items to display per page
   */
  async changeItemsPerPage(itemsPerPage: string): Promise<void> {
    this.logger.stepStart('Change Items Per Page', { itemsPerPage });
    
    try {
      await this.selectOption(this.itemsPerPageSelect, itemsPerPage);
      this.logger.userAction('select', 'items per page', itemsPerPage);
      
      // Wait for page to reload with new item count
      await this.page.waitForTimeout(1000);
      
      this.logger.stepEnd('Change Items Per Page');
    } catch (error) {
      this.logger.stepFailed('Change Items Per Page', error as Error);
      throw error;
    }
  }

  /**
   * Open user settings
   */
  async openSettings(): Promise<void> {
    this.logger.stepStart('Open Settings');
    
    try {
      await this.clickElement(this.settingsButton);
      this.logger.userAction('click', 'settings button');
      this.logger.stepEnd('Open Settings');
    } catch (error) {
      this.logger.stepFailed('Open Settings', error as Error);
      throw error;
    }
  }

  /**
   * Open help section
   */
  async openHelp(): Promise<void> {
    this.logger.stepStart('Open Help');
    
    try {
      await this.clickElement(this.helpButton);
      this.logger.userAction('click', 'help button');
      this.logger.stepEnd('Open Help');
    } catch (error) {
      this.logger.stepFailed('Open Help', error as Error);
      throw error;
    }
  }

  /**
   * Logout from dashboard
   */
  async logout(): Promise<void> {
    this.logger.stepStart('Logout from Dashboard');
    
    try {
      await this.clickElement(this.logoutButton);
      this.logger.userAction('click', 'logout button');
      
      // Wait for logout to complete
      await this.waitForUrl(/login|home|\/$/, 10000);
      
      this.logger.stepEnd('Logout from Dashboard');
    } catch (error) {
      this.logger.stepFailed('Logout from Dashboard', error as Error);
      throw error;
    }
  }

  /**
   * Check if modal is open
   */
  async isModalOpen(): Promise<boolean> {
    try {
      return await this.isElementVisible(this.modal);
    } catch (error) {
      this.logger.debug('Modal visibility check failed');
      return false;
    }
  }

  /**
   * Close modal if open
   */
  async closeModal(): Promise<void> {
    this.logger.stepStart('Close Modal');
    
    try {
      if (await this.isModalOpen()) {
        await this.clickElement(this.modalCloseButton);
        this.logger.userAction('click', 'modal close button');
        
        // Wait for modal to close
        await this.waitForElementHidden(this.modal);
      }
      
      this.logger.stepEnd('Close Modal');
    } catch (error) {
      this.logger.stepFailed('Close Modal', error as Error);
      throw error;
    }
  }

  /**
   * Confirm action in modal
   */
  async confirmModalAction(): Promise<void> {
    this.logger.stepStart('Confirm Modal Action');
    
    try {
      await this.clickElement(this.confirmButton);
      this.logger.userAction('click', 'confirm button');
      
      // Wait for modal to close
      await this.waitForElementHidden(this.modal);
      
      this.logger.stepEnd('Confirm Modal Action');
    } catch (error) {
      this.logger.stepFailed('Confirm Modal Action', error as Error);
      throw error;
    }
  }

  /**
   * Cancel action in modal
   */
  async cancelModalAction(): Promise<void> {
    this.logger.stepStart('Cancel Modal Action');
    
    try {
      await this.clickElement(this.cancelButton);
      this.logger.userAction('click', 'cancel button');
      
      // Wait for modal to close
      await this.waitForElementHidden(this.modal);
      
      this.logger.stepEnd('Cancel Modal Action');
    } catch (error) {
      this.logger.stepFailed('Cancel Modal Action', error as Error);
      throw error;
    }
  }

  /**
   * Get notification count
   */
  async getNotificationCount(): Promise<number> {
    this.logger.stepStart('Get Notification Count');
    
    try {
      const count = await this.notificationItems.count();
      this.logger.stepEnd('Get Notification Count', undefined, { count });
      return count;
    } catch (error) {
      this.logger.stepFailed('Get Notification Count', error as Error);
      throw error;
    }
  }

  /**
   * Mark all notifications as read
   */
  async markAllNotificationsRead(): Promise<void> {
    this.logger.stepStart('Mark All Notifications Read');
    
    try {
      await this.clickElement(this.markAllReadButton);
      this.logger.userAction('click', 'mark all read button');
      this.logger.stepEnd('Mark All Notifications Read');
    } catch (error) {
      this.logger.stepFailed('Mark All Notifications Read', error as Error);
      throw error;
    }
  }

  /**
   * Validate dashboard page elements are present
   */
  async validateDashboardElements(): Promise<void> {
    this.logger.stepStart('Validate Dashboard Elements');
    
    try {
      await this.assertElementVisible(this.dashboardHeader, 'Dashboard header should be visible');
      await this.assertElementVisible(this.sidebar, 'Sidebar should be visible');
      await this.assertElementVisible(this.mainContent, 'Main content should be visible');
      
      this.logger.stepEnd('Validate Dashboard Elements');
    } catch (error) {
      this.logger.stepFailed('Validate Dashboard Elements', error as Error);
      throw error;
    }
  }

  /**
   * Check if user has admin privileges
   */
  async hasAdminPrivileges(): Promise<boolean> {
    try {
      // Check for admin-specific elements
      const hasSettingsAccess = await this.isElementVisible(this.settingsButton);
      const hasReportsAccess = await this.isElementVisible(this.reportsTab);
      const hasAnalyticsAccess = await this.isElementVisible(this.analyticsTab);
      
      const isAdmin = hasSettingsAccess && hasReportsAccess && hasAnalyticsAccess;
      
      this.logger.assertion('Admin Privileges Check', true, isAdmin, isAdmin);
      return isAdmin;
    } catch (error) {
      this.logger.error('Failed to check admin privileges:', error);
      return false;
    }
  }

  /**
   * Refresh dashboard data
   */
  async refreshDashboard(): Promise<void> {
    this.logger.stepStart('Refresh Dashboard');
    
    try {
      await this.performQuickAction('refresh');
      
      // Wait for data to refresh
      await this.page.waitForTimeout(2000);
      
      this.logger.stepEnd('Refresh Dashboard');
    } catch (error) {
      this.logger.stepFailed('Refresh Dashboard', error as Error);
      throw error;
    }
  }
}