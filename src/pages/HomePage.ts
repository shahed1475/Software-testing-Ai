import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * HomePage class representing the home/landing page functionality
 * Extends BasePage to inherit common page operations
 */
export class HomePage extends BasePage {
  // Navigation elements
  private readonly navigationBar: Locator;
  private readonly logo: Locator;
  private readonly homeLink: Locator;
  private readonly aboutLink: Locator;
  private readonly servicesLink: Locator;
  private readonly contactLink: Locator;
  private readonly loginLink: Locator;
  private readonly signUpLink: Locator;
  private readonly userProfileDropdown: Locator;
  private readonly logoutButton: Locator;

  // Main content elements
  private readonly heroSection: Locator;
  private readonly heroTitle: Locator;
  private readonly heroSubtitle: Locator;
  private readonly ctaButton: Locator;
  private readonly featuresSection: Locator;
  private readonly featureCards: Locator;
  private readonly testimonialSection: Locator;
  private readonly footerSection: Locator;

  // Search and filters
  private readonly searchBox: Locator;
  private readonly searchButton: Locator;
  private readonly filterDropdown: Locator;
  private readonly sortDropdown: Locator;

  // User-specific elements
  private readonly welcomeMessage: Locator;
  private readonly userDashboardLink: Locator;
  private readonly notificationBell: Locator;
  private readonly cartIcon: Locator;

  constructor(page: Page) {
    super(page);
    
    // Initialize navigation locators
    this.navigationBar = page.locator('[data-testid="navigation-bar"], .navbar, nav');
    this.logo = page.locator('[data-testid="logo"], .logo, .brand');
    this.homeLink = page.locator('[data-testid="home-link"], a[href="/"], a[href="/home"]');
    this.aboutLink = page.locator('[data-testid="about-link"], a[href*="about"]');
    this.servicesLink = page.locator('[data-testid="services-link"], a[href*="services"]');
    this.contactLink = page.locator('[data-testid="contact-link"], a[href*="contact"]');
    this.loginLink = page.locator('[data-testid="login-link"], a[href*="login"]');
    this.signUpLink = page.locator('[data-testid="signup-link"], a[href*="signup"], a[href*="register"]');
    this.userProfileDropdown = page.locator('[data-testid="user-profile"], .user-menu, .profile-dropdown');
    this.logoutButton = page.locator('[data-testid="logout-button"], a[href*="logout"], button:has-text("Logout")');

    // Initialize main content locators
    this.heroSection = page.locator('[data-testid="hero-section"], .hero, .banner');
    this.heroTitle = page.locator('[data-testid="hero-title"], .hero h1, .banner h1');
    this.heroSubtitle = page.locator('[data-testid="hero-subtitle"], .hero p, .banner p');
    this.ctaButton = page.locator('[data-testid="cta-button"], .cta, .hero button');
    this.featuresSection = page.locator('[data-testid="features-section"], .features');
    this.featureCards = page.locator('[data-testid="feature-card"], .feature-card, .feature');
    this.testimonialSection = page.locator('[data-testid="testimonials"], .testimonials');
    this.footerSection = page.locator('[data-testid="footer"], footer');

    // Initialize search and filter locators
    this.searchBox = page.locator('[data-testid="search-box"], input[type="search"], .search-input');
    this.searchButton = page.locator('[data-testid="search-button"], .search-btn, button[type="submit"]');
    this.filterDropdown = page.locator('[data-testid="filter-dropdown"], .filter-select');
    this.sortDropdown = page.locator('[data-testid="sort-dropdown"], .sort-select');

    // Initialize user-specific locators
    this.welcomeMessage = page.locator('[data-testid="welcome-message"], .welcome');
    this.userDashboardLink = page.locator('[data-testid="dashboard-link"], a[href*="dashboard"]');
    this.notificationBell = page.locator('[data-testid="notifications"], .notification-bell');
    this.cartIcon = page.locator('[data-testid="cart"], .cart-icon');
  }

  /**
   * Navigate to the home page
   */
  async navigateToHome(): Promise<void> {
    this.logger.stepStart('Navigate to Home Page');
    
    try {
      await this.goto('/');
      await this.waitForHomePageLoad();
      this.logger.stepEnd('Navigate to Home Page');
    } catch (error) {
      this.logger.stepFailed('Navigate to Home Page', error as Error);
      throw error;
    }
  }

  /**
   * Wait for home page to be fully loaded
   */
  async waitForHomePageLoad(): Promise<void> {
    this.logger.debug('Waiting for home page to load');
    
    try {
      await this.waitForElement(this.navigationBar);
      await this.waitForElement(this.heroSection);
      
      // Wait for hero content to be visible
      await Promise.race([
        this.waitForElement(this.heroTitle, 5000),
        this.waitForElement(this.logo, 5000),
      ]);
      
      this.logger.debug('Home page loaded successfully');
    } catch (error) {
      this.logger.error('Home page failed to load properly');
      await this.takeScreenshot('home-page-load-failed');
      throw error;
    }
  }

  /**
   * Click on the logo to navigate home
   */
  async clickLogo(): Promise<void> {
    this.logger.stepStart('Click Logo');
    
    try {
      await this.clickElement(this.logo);
      this.logger.userAction('click', 'logo');
      this.logger.stepEnd('Click Logo');
    } catch (error) {
      this.logger.stepFailed('Click Logo', error as Error);
      throw error;
    }
  }

  /**
   * Navigate using the main navigation menu
   * @param linkName - Name of the navigation link to click
   */
  async navigateToSection(linkName: 'home' | 'about' | 'services' | 'contact' | 'login' | 'signup'): Promise<void> {
    this.logger.stepStart('Navigate to Section', { section: linkName });
    
    try {
      const linkMap = {
        home: this.homeLink,
        about: this.aboutLink,
        services: this.servicesLink,
        contact: this.contactLink,
        login: this.loginLink,
        signup: this.signUpLink,
      };

      const targetLink = linkMap[linkName];
      if (!targetLink) {
        throw new Error(`Unknown navigation link: ${linkName}`);
      }

      await this.clickElement(targetLink);
      this.logger.userAction('click', `${linkName} navigation link`);
      this.logger.stepEnd('Navigate to Section');
    } catch (error) {
      this.logger.stepFailed('Navigate to Section', error as Error);
      throw error;
    }
  }

  /**
   * Click the main call-to-action button
   */
  async clickCTAButton(): Promise<void> {
    this.logger.stepStart('Click CTA Button');
    
    try {
      await this.scrollToElement(this.ctaButton);
      await this.clickElement(this.ctaButton);
      this.logger.userAction('click', 'CTA button');
      this.logger.stepEnd('Click CTA Button');
    } catch (error) {
      this.logger.stepFailed('Click CTA Button', error as Error);
      throw error;
    }
  }

  /**
   * Get the hero title text
   */
  async getHeroTitle(): Promise<string> {
    this.logger.stepStart('Get Hero Title');
    
    try {
      const title = await this.getElementText(this.heroTitle);
      this.logger.stepEnd('Get Hero Title', undefined, { title });
      return title;
    } catch (error) {
      this.logger.stepFailed('Get Hero Title', error as Error);
      throw error;
    }
  }

  /**
   * Get the hero subtitle text
   */
  async getHeroSubtitle(): Promise<string> {
    this.logger.stepStart('Get Hero Subtitle');
    
    try {
      const subtitle = await this.getElementText(this.heroSubtitle);
      this.logger.stepEnd('Get Hero Subtitle', undefined, { subtitle });
      return subtitle;
    } catch (error) {
      this.logger.stepFailed('Get Hero Subtitle', error as Error);
      throw error;
    }
  }

  /**
   * Perform search using the search box
   * @param searchTerm - Term to search for
   */
  async performSearch(searchTerm: string): Promise<void> {
    this.logger.stepStart('Perform Search', { searchTerm });
    
    try {
      await this.fillText(this.searchBox, searchTerm);
      await this.clickElement(this.searchButton);
      this.logger.userAction('search', 'search box', searchTerm);
      this.logger.stepEnd('Perform Search');
    } catch (error) {
      this.logger.stepFailed('Perform Search', error as Error);
      throw error;
    }
  }

  /**
   * Apply filter from dropdown
   * @param filterValue - Filter value to select
   */
  async applyFilter(filterValue: string): Promise<void> {
    this.logger.stepStart('Apply Filter', { filterValue });
    
    try {
      await this.selectOption(this.filterDropdown, filterValue);
      this.logger.userAction('select', 'filter dropdown', filterValue);
      this.logger.stepEnd('Apply Filter');
    } catch (error) {
      this.logger.stepFailed('Apply Filter', error as Error);
      throw error;
    }
  }

  /**
   * Apply sort option from dropdown
   * @param sortValue - Sort value to select
   */
  async applySorting(sortValue: string): Promise<void> {
    this.logger.stepStart('Apply Sorting', { sortValue });
    
    try {
      await this.selectOption(this.sortDropdown, sortValue);
      this.logger.userAction('select', 'sort dropdown', sortValue);
      this.logger.stepEnd('Apply Sorting');
    } catch (error) {
      this.logger.stepFailed('Apply Sorting', error as Error);
      throw error;
    }
  }

  /**
   * Get the number of feature cards displayed
   */
  async getFeatureCardCount(): Promise<number> {
    this.logger.stepStart('Get Feature Card Count');
    
    try {
      const count = await this.featureCards.count();
      this.logger.stepEnd('Get Feature Card Count', undefined, { count });
      return count;
    } catch (error) {
      this.logger.stepFailed('Get Feature Card Count', error as Error);
      throw error;
    }
  }

  /**
   * Click on a specific feature card by index
   * @param index - Index of the feature card to click (0-based)
   */
  async clickFeatureCard(index: number): Promise<void> {
    this.logger.stepStart('Click Feature Card', { index });
    
    try {
      const featureCard = this.featureCards.nth(index);
      await this.scrollToElement(featureCard);
      await this.clickElement(featureCard);
      this.logger.userAction('click', `feature card ${index}`);
      this.logger.stepEnd('Click Feature Card');
    } catch (error) {
      this.logger.stepFailed('Click Feature Card', error as Error);
      throw error;
    }
  }

  /**
   * Check if user is logged in
   */
  async isUserLoggedIn(): Promise<boolean> {
    try {
      const hasUserProfile = await this.isElementVisible(this.userProfileDropdown);
      const hasWelcomeMessage = await this.isElementVisible(this.welcomeMessage);
      const hasLoginLink = await this.isElementVisible(this.loginLink);
      
      const isLoggedIn = (hasUserProfile || hasWelcomeMessage) && !hasLoginLink;
      
      this.logger.assertion('User Login Status Check', true, isLoggedIn, isLoggedIn);
      return isLoggedIn;
    } catch (error) {
      this.logger.error('Failed to check user login status:', error);
      return false;
    }
  }

  /**
   * Get welcome message text for logged-in users
   */
  async getWelcomeMessage(): Promise<string | null> {
    try {
      if (await this.isElementVisible(this.welcomeMessage)) {
        const message = await this.getElementText(this.welcomeMessage);
        this.logger.info(`Welcome message found: ${message}`);
        return message;
      }
      return null;
    } catch (error) {
      this.logger.debug('No welcome message found');
      return null;
    }
  }

  /**
   * Click on user profile dropdown
   */
  async clickUserProfile(): Promise<void> {
    this.logger.stepStart('Click User Profile');
    
    try {
      await this.clickElement(this.userProfileDropdown);
      this.logger.userAction('click', 'user profile dropdown');
      this.logger.stepEnd('Click User Profile');
    } catch (error) {
      this.logger.stepFailed('Click User Profile', error as Error);
      throw error;
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    this.logger.stepStart('Logout User');
    
    try {
      // First click on user profile to open dropdown
      await this.clickUserProfile();
      
      // Then click logout button
      await this.clickElement(this.logoutButton);
      this.logger.userAction('click', 'logout button');
      
      // Wait for logout to complete
      await this.waitForUrl(/login|home|\/$/, 10000);
      
      this.logger.stepEnd('Logout User');
    } catch (error) {
      this.logger.stepFailed('Logout User', error as Error);
      throw error;
    }
  }

  /**
   * Navigate to user dashboard
   */
  async navigateToDashboard(): Promise<void> {
    this.logger.stepStart('Navigate to Dashboard');
    
    try {
      await this.clickElement(this.userDashboardLink);
      this.logger.userAction('click', 'dashboard link');
      this.logger.stepEnd('Navigate to Dashboard');
    } catch (error) {
      this.logger.stepFailed('Navigate to Dashboard', error as Error);
      throw error;
    }
  }

  /**
   * Click on notification bell
   */
  async clickNotifications(): Promise<void> {
    this.logger.stepStart('Click Notifications');
    
    try {
      await this.clickElement(this.notificationBell);
      this.logger.userAction('click', 'notification bell');
      this.logger.stepEnd('Click Notifications');
    } catch (error) {
      this.logger.stepFailed('Click Notifications', error as Error);
      throw error;
    }
  }

  /**
   * Click on cart icon
   */
  async clickCart(): Promise<void> {
    this.logger.stepStart('Click Cart');
    
    try {
      await this.clickElement(this.cartIcon);
      this.logger.userAction('click', 'cart icon');
      this.logger.stepEnd('Click Cart');
    } catch (error) {
      this.logger.stepFailed('Click Cart', error as Error);
      throw error;
    }
  }

  /**
   * Scroll to footer section
   */
  async scrollToFooter(): Promise<void> {
    this.logger.stepStart('Scroll to Footer');
    
    try {
      await this.scrollToElement(this.footerSection);
      this.logger.stepEnd('Scroll to Footer');
    } catch (error) {
      this.logger.stepFailed('Scroll to Footer', error as Error);
      throw error;
    }
  }

  /**
   * Validate home page elements are present
   */
  async validatePageElements(): Promise<void> {
    this.logger.stepStart('Validate Home Page Elements');
    
    try {
      await this.assertElementVisible(this.navigationBar, 'Navigation bar should be visible');
      await this.assertElementVisible(this.heroSection, 'Hero section should be visible');
      await this.assertElementVisible(this.footerSection, 'Footer section should be visible');
      
      this.logger.stepEnd('Validate Home Page Elements');
    } catch (error) {
      this.logger.stepFailed('Validate Home Page Elements', error as Error);
      throw error;
    }
  }

  /**
   * Check if search functionality is available
   */
  async isSearchAvailable(): Promise<boolean> {
    try {
      const hasSearchBox = await this.isElementVisible(this.searchBox);
      const hasSearchButton = await this.isElementVisible(this.searchButton);
      
      const isAvailable = hasSearchBox && hasSearchButton;
      
      this.logger.assertion('Search Availability Check', true, isAvailable, isAvailable);
      return isAvailable;
    } catch (error) {
      this.logger.error('Failed to check search availability:', error);
      return false;
    }
  }

  /**
   * Get current search term from search box
   */
  async getCurrentSearchTerm(): Promise<string> {
    try {
      return await this.searchBox.inputValue();
    } catch (error) {
      this.logger.error('Failed to get current search term:', error);
      return '';
    }
  }

  /**
   * Check if features section is visible
   */
  async isFeaturesVisible(): Promise<boolean> {
    try {
      return await this.isElementVisible(this.featuresSection);
    } catch (error) {
      this.logger.debug('Features section visibility check failed');
      return false;
    }
  }

  /**
   * Check if testimonials section is visible
   */
  async isTestimonialsVisible(): Promise<boolean> {
    try {
      return await this.isElementVisible(this.testimonialSection);
    } catch (error) {
      this.logger.debug('Testimonials section visibility check failed');
      return false;
    }
  }
}