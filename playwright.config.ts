import { defineConfig, devices } from '@playwright/test';
import * as path from 'path';

/**
 * Playwright Test Automation Framework Configuration
 * 
 * Features:
 * - Multi-browser testing (Chromium, Firefox, WebKit)
 * - Parallel execution with configurable workers
 * - Comprehensive reporting (HTML, JSON, JUnit, Allure)
 * - Environment-specific configurations
 * - Mobile device testing
 * - CI/CD optimized settings
 */

export default defineConfig({
  // Test directory structure
  testDir: './src/tests',
  
  // Global test settings
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 3 : 1,
  workers: process.env.CI ? 2 : undefined,
  
  // Timeout configurations
  timeout: 30 * 1000, // 30 seconds per test
  expect: {
    timeout: 10 * 1000, // 10 seconds for assertions
  },
  
  // Global test setup
  globalSetup: require.resolve('./src/utils/global-setup.ts'),
  globalTeardown: require.resolve('./src/utils/global-teardown.ts'),
  
  // Reporters configuration
  reporter: [
    ['html', { outputFolder: 'reports/playwright-html-report', open: 'never' }],
    ['json', { outputFile: 'reports/test-results.json' }],
    ['junit', { outputFile: 'reports/junit-results.xml' }],
    ['allure-playwright', { outputFolder: 'allure-results' }],
    ['./src/utils/ReportGenerator.ts'], // Custom HTML reporter
    ['./src/utils/AllureReporter.ts'], // Enhanced Allure reporter
    ['list'], // Console output
  ],
  
  // Global test configuration
  use: {
    // Base URL from environment or default
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    
    // Browser context options
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    
    // Tracing and debugging
    trace: process.env.CI ? 'retain-on-failure' : 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Action timeouts
    actionTimeout: 15 * 1000,
    navigationTimeout: 30 * 1000,
    
    // Test artifacts
    testIdAttribute: 'data-testid',
  },

  // Browser projects configuration
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
      testMatch: /.*\.spec\.ts/,
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      testMatch: /.*\.spec\.ts/,
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
      testMatch: /.*\.spec\.ts/,
    },
    
    // Mobile browsers
    {
      name: 'mobile-chrome',
      use: { 
        ...devices['Pixel 5'],
        hasTouch: true,
      },
      testMatch: /.*\.mobile\.spec\.ts/,
    },
    {
      name: 'mobile-safari',
      use: { 
        ...devices['iPhone 12'],
        hasTouch: true,
      },
      testMatch: /.*\.mobile\.spec\.ts/,
    },
    
    // API testing project
    {
      name: 'api',
      testMatch: /.*\.api\.spec\.ts/,
      use: {
        baseURL: process.env.API_BASE_URL || 'http://localhost:3000/api',
      },
    },
    
    // Smoke tests (tagged)
    {
      name: 'smoke',
      testMatch: /.*\.spec\.ts/,
      grep: /@smoke/,
      use: { ...devices['Desktop Chrome'] },
    },
    
    // Regression tests (tagged)
    {
      name: 'regression',
      testMatch: /.*\.spec\.ts/,
      grep: /@regression/,
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Web server configuration (optional)
  webServer: process.env.SKIP_WEB_SERVER ? undefined : {
    command: 'npm run start',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
  
  // Output directory
  outputDir: 'test-results/',
  
  // Metadata
  metadata: {
    framework: 'Playwright Test Automation Framework',
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
  },
});