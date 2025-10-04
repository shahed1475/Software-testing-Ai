import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * LoginPage class representing the login page functionality
 * Extends BasePage to inherit common page operations
 */
export class LoginPage extends BasePage {
  // Page elements
  private readonly usernameInput: Locator;
  private readonly passwordInput: Locator;
  private readonly loginButton: Locator;
  private readonly forgotPasswordLink: Locator;
  private readonly rememberMeCheckbox: Locator;
  private readonly errorMessage: Locator;
  private readonly successMessage: Locator;
  private readonly loadingSpinner: Locator;
  private readonly signUpLink: Locator;
  private readonly showPasswordButton: Locator;
  private readonly loginForm: Locator;

  constructor(page: Page) {
    super(page);
    
    // Initialize locators
    this.usernameInput = page.locator('[data-testid="username-input"], #username, input[name="username"]');
    this.passwordInput = page.locator('[data-testid="password-input"], #password, input[name="password"]');
    this.loginButton = page.locator('[data-testid="login-button"], #login-btn, button[type="submit"]');
    this.forgotPasswordLink = page.locator('[data-testid="forgot-password-link"], a[href*="forgot"]');
    this.rememberMeCheckbox = page.locator('[data-testid="remember-me"], #remember-me, input[name="remember"]');
    this.errorMessage = page.locator('[data-testid="error-message"], .error, .alert-error');
    this.successMessage = page.locator('[data-testid="success-message"], .success, .alert-success');
    this.loadingSpinner = page.locator('[data-testid="loading-spinner"], .spinner, .loading');
    this.signUpLink = page.locator('[data-testid="signup-link"], a[href*="signup"], a[href*="register"]');
    this.showPasswordButton = page.locator('[data-testid="show-password"], .show-password, .toggle-password');
    this.loginForm = page.locator('[data-testid="login-form"], #login-form, form');
  }

  /**
   * Navigate to the login page
   * @param path - Optional custom login path
   */
  async navigateToLogin(path: string = '/login'): Promise<void> {
    this.logger.stepStart('Navigate to Login Page');
    
    try {
      await this.goto(path);
      await this.waitForLoginPageLoad();
      this.logger.stepEnd('Navigate to Login Page');
    } catch (error) {
      this.logger.stepFailed('Navigate to Login Page', error as Error);
      throw error;
    }
  }

  /**
   * Wait for login page to be fully loaded
   */
  async waitForLoginPageLoad(): Promise<void> {
    this.logger.debug('Waiting for login page to load');
    
    try {
      await this.waitForElement(this.loginForm);
      await this.waitForElement(this.usernameInput);
      await this.waitForElement(this.passwordInput);
      await this.waitForElement(this.loginButton);
      
      this.logger.debug('Login page loaded successfully');
    } catch (error) {
      this.logger.error('Login page failed to load properly');
      await this.takeScreenshot('login-page-load-failed');
      throw error;
    }
  }

  /**
   * Enter username in the username field
   * @param username - Username to enter
   */
  async enterUsername(username: string): Promise<void> {
    this.logger.stepStart('Enter Username', { username });
    
    try {
      await this.fillText(this.usernameInput, username);
      this.logger.userAction('fill', 'username input', username);
      this.logger.stepEnd('Enter Username');
    } catch (error) {
      this.logger.stepFailed('Enter Username', error as Error);
      throw error;
    }
  }

  /**
   * Enter password in the password field
   * @param password - Password to enter
   */
  async enterPassword(password: string): Promise<void> {
    this.logger.stepStart('Enter Password');
    
    try {
      await this.fillText(this.passwordInput, password);
      this.logger.userAction('fill', 'password input', '[HIDDEN]');
      this.logger.stepEnd('Enter Password');
    } catch (error) {
      this.logger.stepFailed('Enter Password', error as Error);
      throw error;
    }
  }

  /**
   * Click the login button
   */
  async clickLoginButton(): Promise<void> {
    this.logger.stepStart('Click Login Button');
    
    try {
      await this.clickElement(this.loginButton);
      this.logger.userAction('click', 'login button');
      this.logger.stepEnd('Click Login Button');
    } catch (error) {
      this.logger.stepFailed('Click Login Button', error as Error);
      throw error;
    }
  }

  /**
   * Perform complete login action
   * @param username - Username for login
   * @param password - Password for login
   * @param options - Login options
   */
  async login(username: string, password: string, options?: {
    rememberMe?: boolean;
    waitForNavigation?: boolean;
    expectedUrl?: string;
  }): Promise<void> {
    this.logger.stepStart('Perform Login', { 
      username, 
      rememberMe: options?.rememberMe,
      expectedUrl: options?.expectedUrl,
    });
    
    try {
      // Enter credentials
      await this.enterUsername(username);
      await this.enterPassword(password);
      
      // Handle remember me checkbox if specified
      if (options?.rememberMe) {
        await this.toggleRememberMe(true);
      }
      
      // Click login button
      await this.clickLoginButton();
      
      // Wait for login to complete
      await this.waitForLoginCompletion();
      
      // Wait for navigation if specified
      if (options?.waitForNavigation && options?.expectedUrl) {
        await this.waitForUrl(options.expectedUrl);
      }
      
      this.logger.stepEnd('Perform Login');
    } catch (error) {
      this.logger.stepFailed('Perform Login', error as Error);
      await this.takeScreenshot('login-failed');
      throw error;
    }
  }

  /**
   * Wait for login completion (either success or error)
   */
  async waitForLoginCompletion(): Promise<void> {
    this.logger.debug('Waiting for login completion');
    
    try {
      // Wait for either success navigation, error message, or loading to disappear
      await Promise.race([
        this.page.waitForURL(/dashboard|home|profile/, { timeout: 10000 }).catch(() => {}),
        this.waitForElement(this.errorMessage, 5000).catch(() => {}),
        this.waitForElementToBeHidden(this.loadingSpinner, 10000).catch(() => {}),
      ]);
      
      this.logger.debug('Login completion detected');
    } catch (error) {
      this.logger.warn('Login completion timeout - continuing anyway');
    }
  }

  /**
   * Check if login was successful
   */
  async isLoginSuccessful(): Promise<boolean> {
    try {
      const currentUrl = this.getCurrentUrl();
      const hasSuccessMessage = await this.isElementVisible(this.successMessage);
      const hasErrorMessage = await this.isElementVisible(this.errorMessage);
      const isOnLoginPage = currentUrl.includes('/login');
      
      const isSuccessful = !isOnLoginPage || hasSuccessMessage || !hasErrorMessage;
      
      this.logger.assertion('Login Success Check', true, isSuccessful, isSuccessful);
      return isSuccessful;
    } catch (error) {
      this.logger.error('Failed to check login success:', error);
      return false;
    }
  }

  /**
   * Get error message text if present
   */
  async getErrorMessage(): Promise<string | null> {
    try {
      if (await this.isElementVisible(this.errorMessage)) {
        const errorText = await this.getElementText(this.errorMessage);
        this.logger.info(`Error message found: ${errorText}`);
        return errorText;
      }
      return null;
    } catch (error) {
      this.logger.debug('No error message found');
      return null;
    }
  }

  /**
   * Get success message text if present
   */
  async getSuccessMessage(): Promise<string | null> {
    try {
      if (await this.isElementVisible(this.successMessage)) {
        const successText = await this.getElementText(this.successMessage);
        this.logger.info(`Success message found: ${successText}`);
        return successText;
      }
      return null;
    } catch (error) {
      this.logger.debug('No success message found');
      return null;
    }
  }

  /**
   * Toggle remember me checkbox
   * @param checked - Whether to check or uncheck
   */
  async toggleRememberMe(checked: boolean): Promise<void> {
    this.logger.stepStart('Toggle Remember Me', { checked });
    
    try {
      const isCurrentlyChecked = await this.rememberMeCheckbox.isChecked();
      
      if (isCurrentlyChecked !== checked) {
        await this.clickElement(this.rememberMeCheckbox);
        this.logger.userAction('click', 'remember me checkbox');
      }
      
      this.logger.stepEnd('Toggle Remember Me');
    } catch (error) {
      this.logger.stepFailed('Toggle Remember Me', error as Error);
      throw error;
    }
  }

  /**
   * Click forgot password link
   */
  async clickForgotPassword(): Promise<void> {
    this.logger.stepStart('Click Forgot Password');
    
    try {
      await this.clickElement(this.forgotPasswordLink);
      this.logger.userAction('click', 'forgot password link');
      this.logger.stepEnd('Click Forgot Password');
    } catch (error) {
      this.logger.stepFailed('Click Forgot Password', error as Error);
      throw error;
    }
  }

  /**
   * Click sign up link
   */
  async clickSignUp(): Promise<void> {
    this.logger.stepStart('Click Sign Up');
    
    try {
      await this.clickElement(this.signUpLink);
      this.logger.userAction('click', 'sign up link');
      this.logger.stepEnd('Click Sign Up');
    } catch (error) {
      this.logger.stepFailed('Click Sign Up', error as Error);
      throw error;
    }
  }

  /**
   * Toggle password visibility
   */
  async togglePasswordVisibility(): Promise<void> {
    this.logger.stepStart('Toggle Password Visibility');
    
    try {
      if (await this.isElementVisible(this.showPasswordButton)) {
        await this.clickElement(this.showPasswordButton);
        this.logger.userAction('click', 'show password button');
      } else {
        this.logger.warn('Show password button not found');
      }
      
      this.logger.stepEnd('Toggle Password Visibility');
    } catch (error) {
      this.logger.stepFailed('Toggle Password Visibility', error as Error);
      throw error;
    }
  }

  /**
   * Clear login form
   */
  async clearForm(): Promise<void> {
    this.logger.stepStart('Clear Login Form');
    
    try {
      await this.fillText(this.usernameInput, '', { clear: true });
      await this.fillText(this.passwordInput, '', { clear: true });
      
      // Uncheck remember me if checked
      if (await this.rememberMeCheckbox.isChecked()) {
        await this.clickElement(this.rememberMeCheckbox);
      }
      
      this.logger.stepEnd('Clear Login Form');
    } catch (error) {
      this.logger.stepFailed('Clear Login Form', error as Error);
      throw error;
    }
  }

  /**
   * Check if login form is valid (all required fields filled)
   */
  async isFormValid(): Promise<boolean> {
    try {
      const usernameValue = await this.usernameInput.inputValue();
      const passwordValue = await this.passwordInput.inputValue();
      const isButtonEnabled = await this.isElementEnabled(this.loginButton);
      
      const isValid = usernameValue.length > 0 && passwordValue.length > 0 && isButtonEnabled;
      
      this.logger.assertion('Form Validity Check', true, isValid, isValid);
      return isValid;
    } catch (error) {
      this.logger.error('Failed to check form validity:', error);
      return false;
    }
  }

  /**
   * Wait for loading to complete
   */
  async waitForLoadingToComplete(): Promise<void> {
    this.logger.debug('Waiting for loading to complete');
    
    try {
      if (await this.isElementVisible(this.loadingSpinner)) {
        await this.waitForElementToBeHidden(this.loadingSpinner);
      }
      this.logger.debug('Loading completed');
    } catch (error) {
      this.logger.debug('No loading spinner found or timeout');
    }
  }

  /**
   * Validate login page elements are present
   */
  async validatePageElements(): Promise<void> {
    this.logger.stepStart('Validate Login Page Elements');
    
    try {
      await this.assertElementVisible(this.usernameInput, 'Username input should be visible');
      await this.assertElementVisible(this.passwordInput, 'Password input should be visible');
      await this.assertElementVisible(this.loginButton, 'Login button should be visible');
      
      this.logger.stepEnd('Validate Login Page Elements');
    } catch (error) {
      this.logger.stepFailed('Validate Login Page Elements', error as Error);
      throw error;
    }
  }

  /**
   * Get current username value
   */
  async getCurrentUsername(): Promise<string> {
    try {
      return await this.usernameInput.inputValue();
    } catch (error) {
      this.logger.error('Failed to get current username:', error);
      return '';
    }
  }

  /**
   * Check if remember me is checked
   */
  async isRememberMeChecked(): Promise<boolean> {
    try {
      return await this.rememberMeCheckbox.isChecked();
    } catch (error) {
      this.logger.debug('Remember me checkbox not found or not checkable');
      return false;
    }
  }
}