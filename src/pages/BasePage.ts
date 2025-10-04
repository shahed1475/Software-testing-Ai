import { Page, Locator, expect } from '@playwright/test';
import { Logger } from '../utils/Logger';
import { ConfigManager } from '../utils/ConfigManager';

/**
 * BasePage class provides common functionality for all page objects
 * Implements the Page Object Model pattern with reusable methods
 */
export abstract class BasePage {
  protected readonly page: Page;
  protected readonly logger: Logger;
  protected readonly config: ConfigManager;
  protected readonly baseUrl: string;

  constructor(page: Page) {
    this.page = page;
    this.logger = new Logger(this.constructor.name);
    this.config = ConfigManager.getInstance();
    this.baseUrl = this.config.getBaseUrl();
  }

  /**
   * Navigate to a specific URL or path
   * @param url - Full URL or relative path
   * @param options - Navigation options
   */
  async goto(url?: string, options?: { waitUntil?: 'load' | 'domcontentloaded' | 'networkidle' }): Promise<void> {
    const targetUrl = url ? (url.startsWith('http') ? url : `${this.baseUrl}${url}`) : this.baseUrl;
    
    this.logger.info(`Navigating to: ${targetUrl}`);
    
    try {
      await this.page.goto(targetUrl, {
        waitUntil: options?.waitUntil || 'domcontentloaded',
        timeout: 30000,
      });
      
      await this.waitForPageLoad();
      this.logger.info(`Successfully navigated to: ${targetUrl}`);
    } catch (error) {
      this.logger.error(`Failed to navigate to ${targetUrl}:`, error);
      throw error;
    }
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
      this.logger.warn('Network idle timeout - continuing anyway');
    });
  }

  /**
   * Take a screenshot with optional name
   * @param name - Screenshot name (defaults to timestamp)
   */
  async takeScreenshot(name?: string): Promise<Buffer> {
    const screenshotName = name || `screenshot-${Date.now()}`;
    this.logger.info(`Taking screenshot: ${screenshotName}`);
    
    try {
      const screenshot = await this.page.screenshot({
        path: `test-results/screenshots/${screenshotName}.png`,
        fullPage: true,
      });
      
      this.logger.info(`Screenshot saved: ${screenshotName}.png`);
      return screenshot;
    } catch (error) {
      this.logger.error('Failed to take screenshot:', error);
      throw error;
    }
  }

  /**
   * Wait for an element to be visible
   * @param locator - Element locator
   * @param timeout - Wait timeout in milliseconds
   */
  async waitForElement(locator: Locator, timeout: number = 10000): Promise<void> {
    this.logger.debug(`Waiting for element: ${locator.toString()}`);
    
    try {
      await locator.waitFor({ state: 'visible', timeout });
      this.logger.debug(`Element is visible: ${locator.toString()}`);
    } catch (error) {
      this.logger.error(`Element not found within ${timeout}ms: ${locator.toString()}`);
      await this.takeScreenshot(`element-not-found-${Date.now()}`);
      throw error;
    }
  }

  /**
   * Wait for an element to be hidden
   * @param locator - Element locator
   * @param timeout - Wait timeout in milliseconds
   */
  async waitForElementToBeHidden(locator: Locator, timeout: number = 10000): Promise<void> {
    this.logger.debug(`Waiting for element to be hidden: ${locator.toString()}`);
    
    try {
      await locator.waitFor({ state: 'hidden', timeout });
      this.logger.debug(`Element is hidden: ${locator.toString()}`);
    } catch (error) {
      this.logger.error(`Element still visible after ${timeout}ms: ${locator.toString()}`);
      throw error;
    }
  }

  /**
   * Click an element with retry logic
   * @param locator - Element locator
   * @param options - Click options
   */
  async clickElement(locator: Locator, options?: { force?: boolean; timeout?: number }): Promise<void> {
    this.logger.debug(`Clicking element: ${locator.toString()}`);
    
    try {
      await this.waitForElement(locator, options?.timeout);
      await locator.click({
        force: options?.force || false,
        timeout: options?.timeout || 10000,
      });
      
      this.logger.debug(`Successfully clicked: ${locator.toString()}`);
    } catch (error) {
      this.logger.error(`Failed to click element: ${locator.toString()}`, error);
      await this.takeScreenshot(`click-failed-${Date.now()}`);
      throw error;
    }
  }

  /**
   * Fill text input with clear and type
   * @param locator - Input element locator
   * @param text - Text to fill
   * @param options - Fill options
   */
  async fillText(locator: Locator, text: string, options?: { clear?: boolean; timeout?: number }): Promise<void> {
    this.logger.debug(`Filling text in element: ${locator.toString()}`);
    
    try {
      await this.waitForElement(locator, options?.timeout);
      
      if (options?.clear !== false) {
        await locator.clear();
      }
      
      await locator.fill(text);
      this.logger.debug(`Successfully filled text: ${locator.toString()}`);
    } catch (error) {
      this.logger.error(`Failed to fill text in element: ${locator.toString()}`, error);
      await this.takeScreenshot(`fill-failed-${Date.now()}`);
      throw error;
    }
  }

  /**
   * Get text content from an element
   * @param locator - Element locator
   * @param timeout - Wait timeout
   */
  async getElementText(locator: Locator, timeout?: number): Promise<string> {
    this.logger.debug(`Getting text from element: ${locator.toString()}`);
    
    try {
      await this.waitForElement(locator, timeout);
      const text = await locator.textContent() || '';
      this.logger.debug(`Retrieved text: "${text}" from ${locator.toString()}`);
      return text.trim();
    } catch (error) {
      this.logger.error(`Failed to get text from element: ${locator.toString()}`, error);
      throw error;
    }
  }

  /**
   * Check if element is visible
   * @param locator - Element locator
   */
  async isElementVisible(locator: Locator): Promise<boolean> {
    try {
      const isVisible = await locator.isVisible();
      this.logger.debug(`Element visibility check: ${locator.toString()} = ${isVisible}`);
      return isVisible;
    } catch (error) {
      this.logger.debug(`Element visibility check failed: ${locator.toString()}`);
      return false;
    }
  }

  /**
   * Check if element is enabled
   * @param locator - Element locator
   */
  async isElementEnabled(locator: Locator): Promise<boolean> {
    try {
      const isEnabled = await locator.isEnabled();
      this.logger.debug(`Element enabled check: ${locator.toString()} = ${isEnabled}`);
      return isEnabled;
    } catch (error) {
      this.logger.debug(`Element enabled check failed: ${locator.toString()}`);
      return false;
    }
  }

  /**
   * Select option from dropdown
   * @param locator - Select element locator
   * @param option - Option to select (value, label, or index)
   */
  async selectOption(locator: Locator, option: string | number): Promise<void> {
    this.logger.debug(`Selecting option "${option}" from: ${locator.toString()}`);
    
    try {
      await this.waitForElement(locator);
      
      if (typeof option === 'number') {
        await locator.selectOption({ index: option });
      } else {
        // Try by value first, then by label
        try {
          await locator.selectOption({ value: option });
        } catch {
          await locator.selectOption({ label: option });
        }
      }
      
      this.logger.debug(`Successfully selected option: ${option}`);
    } catch (error) {
      this.logger.error(`Failed to select option "${option}":`, error);
      await this.takeScreenshot(`select-failed-${Date.now()}`);
      throw error;
    }
  }

  /**
   * Hover over an element
   * @param locator - Element locator
   */
  async hoverElement(locator: Locator): Promise<void> {
    this.logger.debug(`Hovering over element: ${locator.toString()}`);
    
    try {
      await this.waitForElement(locator);
      await locator.hover();
      this.logger.debug(`Successfully hovered over: ${locator.toString()}`);
    } catch (error) {
      this.logger.error(`Failed to hover over element: ${locator.toString()}`, error);
      throw error;
    }
  }

  /**
   * Scroll element into view
   * @param locator - Element locator
   */
  async scrollToElement(locator: Locator): Promise<void> {
    this.logger.debug(`Scrolling to element: ${locator.toString()}`);
    
    try {
      await locator.scrollIntoViewIfNeeded();
      this.logger.debug(`Successfully scrolled to: ${locator.toString()}`);
    } catch (error) {
      this.logger.error(`Failed to scroll to element: ${locator.toString()}`, error);
      throw error;
    }
  }

  /**
   * Wait for URL to match pattern
   * @param urlPattern - URL pattern to match
   * @param timeout - Wait timeout
   */
  async waitForUrl(urlPattern: string | RegExp, timeout: number = 10000): Promise<void> {
    this.logger.debug(`Waiting for URL pattern: ${urlPattern.toString()}`);
    
    try {
      await this.page.waitForURL(urlPattern, { timeout });
      const currentUrl = this.page.url();
      this.logger.info(`URL matched pattern. Current URL: ${currentUrl}`);
    } catch (error) {
      const currentUrl = this.page.url();
      this.logger.error(`URL pattern not matched within ${timeout}ms. Current URL: ${currentUrl}`);
      throw error;
    }
  }

  /**
   * Get current page URL
   */
  getCurrentUrl(): string {
    const url = this.page.url();
    this.logger.debug(`Current URL: ${url}`);
    return url;
  }

  /**
   * Get page title
   */
  async getPageTitle(): Promise<string> {
    const title = await this.page.title();
    this.logger.debug(`Page title: ${title}`);
    return title;
  }

  /**
   * Refresh the current page
   */
  async refreshPage(): Promise<void> {
    this.logger.info('Refreshing page');
    
    try {
      await this.page.reload({ waitUntil: 'domcontentloaded' });
      await this.waitForPageLoad();
      this.logger.info('Page refreshed successfully');
    } catch (error) {
      this.logger.error('Failed to refresh page:', error);
      throw error;
    }
  }

  /**
   * Execute JavaScript in the browser context
   * @param script - JavaScript code to execute
   * @param args - Arguments to pass to the script
   */
  async executeScript<T>(script: string, ...args: unknown[]): Promise<T> {
    this.logger.debug(`Executing script: ${script}`);
    
    try {
      const result = await this.page.evaluate(script, ...args);
      this.logger.debug('Script executed successfully');
      return result as T;
    } catch (error) {
      this.logger.error('Script execution failed:', error);
      throw error;
    }
  }

  /**
   * Wait for a specific amount of time
   * @param milliseconds - Time to wait in milliseconds
   */
  async wait(milliseconds: number): Promise<void> {
    this.logger.debug(`Waiting for ${milliseconds}ms`);
    await this.page.waitForTimeout(milliseconds);
  }

  /**
   * Assert that an element is visible
   * @param locator - Element locator
   * @param message - Custom assertion message
   */
  async assertElementVisible(locator: Locator, message?: string): Promise<void> {
    const customMessage = message || `Element should be visible: ${locator.toString()}`;
    this.logger.debug(`Asserting element visibility: ${locator.toString()}`);
    
    try {
      await expect(locator).toBeVisible({ timeout: 10000 });
      this.logger.debug(`Assertion passed: Element is visible`);
    } catch (error) {
      this.logger.error(`Assertion failed: ${customMessage}`);
      await this.takeScreenshot(`assertion-failed-${Date.now()}`);
      throw new Error(customMessage);
    }
  }

  /**
   * Assert that an element contains specific text
   * @param locator - Element locator
   * @param expectedText - Expected text content
   * @param message - Custom assertion message
   */
  async assertElementText(locator: Locator, expectedText: string, message?: string): Promise<void> {
    const customMessage = message || `Element should contain text "${expectedText}": ${locator.toString()}`;
    this.logger.debug(`Asserting element text: ${locator.toString()} should contain "${expectedText}"`);
    
    try {
      await expect(locator).toContainText(expectedText, { timeout: 10000 });
      this.logger.debug(`Assertion passed: Element contains expected text`);
    } catch (error) {
      this.logger.error(`Assertion failed: ${customMessage}`);
      await this.takeScreenshot(`text-assertion-failed-${Date.now()}`);
      throw new Error(customMessage);
    }
  }
}