import { Page, Locator } from '@playwright/test';

export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto(url: string) {
    await this.page.goto(url);
  }

  async takeScreenshot(name: string) {
    await this.page.screenshot({ path: `artifacts/${name}.png` });
  }
}

export class HomePage extends BasePage {
  readonly title: Locator;
  readonly navigationMenu: Locator;
  readonly searchBox: Locator;
  readonly loginButton: Locator;

  constructor(page: Page) {
    super(page);
    this.title = this.page.locator('h1');
    this.navigationMenu = this.page.locator('[data-testid="nav-menu"]');
    this.searchBox = this.page.locator('[data-testid="search-input"]');
    this.loginButton = this.page.locator('[data-testid="login-button"]');
  }

  async search(query: string) {
    await this.searchBox.fill(query);
    await this.searchBox.press('Enter');
  }

  async clickLogin() {
    await this.loginButton.click();
  }
}

export class LoginPage extends BasePage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);
    this.emailInput = this.page.locator('[data-testid="email-input"]');
    this.passwordInput = this.page.locator('[data-testid="password-input"]');
    this.submitButton = this.page.locator('[data-testid="submit-button"]');
    this.errorMessage = this.page.locator('[data-testid="error-message"]');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}

export class DashboardPage extends BasePage {
  readonly welcomeMessage: Locator;
  readonly userProfile: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    super(page);
    this.welcomeMessage = this.page.locator('[data-testid="welcome-message"]');
    this.userProfile = this.page.locator('[data-testid="user-profile"]');
    this.logoutButton = this.page.locator('[data-testid="logout-button"]');
  }

  async logout() {
    await this.logoutButton.click();
  }
}