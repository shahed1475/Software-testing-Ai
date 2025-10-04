import * as dotenv from 'dotenv';
import * as path from 'path';
import * as fs from 'fs';
import { Logger } from './Logger';

// Load environment variables
dotenv.config();

/**
 * Configuration interface for type safety
 */
export interface TestConfig {
  baseUrl: string;
  environment: 'dev' | 'staging' | 'prod' | 'local';
  browser: {
    headless: boolean;
    slowMo: number;
    timeout: number;
    viewport: {
      width: number;
      height: number;
    };
  };
  api: {
    baseUrl: string;
    timeout: number;
    retries: number;
  };
  database: {
    host?: string;
    port?: number;
    username?: string;
    password?: string;
    database?: string;
  };
  reporting: {
    screenshots: boolean;
    videos: boolean;
    traces: boolean;
    allure: boolean;
  };
  notifications: {
    slack: {
      enabled: boolean;
      webhookUrl?: string;
      channel?: string;
    };
    email: {
      enabled: boolean;
      smtp: {
        host?: string;
        port?: number;
        secure?: boolean;
        username?: string;
        password?: string;
      };
      recipients?: string[];
    };
  };
  parallel: {
    workers: number;
    retries: number;
  };
}

/**
 * ConfigManager class for handling application configuration
 * Implements singleton pattern for global access
 */
export class ConfigManager {
  private static instance: ConfigManager;
  private config: TestConfig;
  private logger: Logger;

  private constructor() {
    this.logger = new Logger('ConfigManager');
    this.config = this.loadConfiguration();
    this.validateConfiguration();
  }

  /**
   * Get singleton instance of ConfigManager
   */
  public static getInstance(): ConfigManager {
    if (!ConfigManager.instance) {
      ConfigManager.instance = new ConfigManager();
    }
    return ConfigManager.instance;
  }

  /**
   * Load configuration from environment variables and config files
   */
  private loadConfiguration(): TestConfig {
    const environment = (process.env.TEST_ENV || 'local') as TestConfig['environment'];
    
    // Load environment-specific config file if exists
    const configPath = path.join(process.cwd(), 'src', 'config', `config.${environment}.json`);
    let fileConfig = {};
    
    if (fs.existsSync(configPath)) {
      try {
        const configContent = fs.readFileSync(configPath, 'utf-8');
        fileConfig = JSON.parse(configContent);
        this.logger.info(`Loaded configuration from: ${configPath}`);
      } catch (error) {
        this.logger.warn(`Failed to load config file ${configPath}:`, error);
      }
    }

    // Default configuration
    const defaultConfig: TestConfig = {
      baseUrl: process.env.BASE_URL || 'http://localhost:3000',
      environment,
      browser: {
        headless: process.env.HEADLESS !== 'false',
        slowMo: parseInt(process.env.SLOW_MO || '0', 10),
        timeout: parseInt(process.env.BROWSER_TIMEOUT || '30000', 10),
        viewport: {
          width: parseInt(process.env.VIEWPORT_WIDTH || '1280', 10),
          height: parseInt(process.env.VIEWPORT_HEIGHT || '720', 10),
        },
      },
      api: {
        baseUrl: process.env.API_BASE_URL || 'http://localhost:3000/api',
        timeout: parseInt(process.env.API_TIMEOUT || '10000', 10),
        retries: parseInt(process.env.API_RETRIES || '3', 10),
      },
      database: {
        host: process.env.DB_HOST,
        port: process.env.DB_PORT ? parseInt(process.env.DB_PORT, 10) : undefined,
        username: process.env.DB_USERNAME,
        password: process.env.DB_PASSWORD,
        database: process.env.DB_NAME,
      },
      reporting: {
        screenshots: process.env.SCREENSHOTS !== 'false',
        videos: process.env.VIDEOS === 'true',
        traces: process.env.TRACES === 'true',
        allure: process.env.ALLURE_REPORTS === 'true',
      },
      notifications: {
        slack: {
          enabled: process.env.SLACK_NOTIFICATIONS === 'true',
          webhookUrl: process.env.SLACK_WEBHOOK_URL,
          channel: process.env.SLACK_CHANNEL,
        },
        email: {
          enabled: process.env.EMAIL_NOTIFICATIONS === 'true',
          smtp: {
            host: process.env.SMTP_HOST,
            port: process.env.SMTP_PORT ? parseInt(process.env.SMTP_PORT, 10) : undefined,
            secure: process.env.SMTP_SECURE === 'true',
            username: process.env.SMTP_USERNAME,
            password: process.env.SMTP_PASSWORD,
          },
          recipients: process.env.EMAIL_RECIPIENTS?.split(',').map(email => email.trim()),
        },
      },
      parallel: {
        workers: parseInt(process.env.WORKERS || '4', 10),
        retries: parseInt(process.env.RETRIES || '2', 10),
      },
    };

    // Merge default config with file config
    const mergedConfig = this.deepMerge(defaultConfig, fileConfig);
    
    this.logger.info('Configuration loaded successfully', {
      environment: mergedConfig.environment,
      baseUrl: mergedConfig.baseUrl,
      headless: mergedConfig.browser.headless,
      workers: mergedConfig.parallel.workers,
    });

    return mergedConfig;
  }

  /**
   * Deep merge two objects
   */
  private deepMerge(target: any, source: any): any {
    const result = { ...target };
    
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.deepMerge(target[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    
    return result;
  }

  /**
   * Validate configuration values
   */
  private validateConfiguration(): void {
    const errors: string[] = [];

    // Validate base URL
    if (!this.config.baseUrl) {
      errors.push('Base URL is required');
    }

    // Validate browser timeout
    if (this.config.browser.timeout <= 0) {
      errors.push('Browser timeout must be greater than 0');
    }

    // Validate viewport dimensions
    if (this.config.browser.viewport.width <= 0 || this.config.browser.viewport.height <= 0) {
      errors.push('Viewport dimensions must be greater than 0');
    }

    // Validate parallel workers
    if (this.config.parallel.workers <= 0) {
      errors.push('Number of workers must be greater than 0');
    }

    // Validate Slack configuration if enabled
    if (this.config.notifications.slack.enabled && !this.config.notifications.slack.webhookUrl) {
      errors.push('Slack webhook URL is required when Slack notifications are enabled');
    }

    // Validate email configuration if enabled
    if (this.config.notifications.email.enabled) {
      if (!this.config.notifications.email.smtp.host) {
        errors.push('SMTP host is required when email notifications are enabled');
      }
      if (!this.config.notifications.email.recipients?.length) {
        errors.push('Email recipients are required when email notifications are enabled');
      }
    }

    if (errors.length > 0) {
      this.logger.error('Configuration validation failed:', errors);
      throw new Error(`Configuration validation failed: ${errors.join(', ')}`);
    }

    this.logger.info('Configuration validation passed');
  }

  /**
   * Get the complete configuration object
   */
  public getConfig(): TestConfig {
    return { ...this.config };
  }

  /**
   * Get base URL for the application
   */
  public getBaseUrl(): string {
    return this.config.baseUrl;
  }

  /**
   * Get API base URL
   */
  public getApiBaseUrl(): string {
    return this.config.api.baseUrl;
  }

  /**
   * Get current environment
   */
  public getEnvironment(): string {
    return this.config.environment;
  }

  /**
   * Check if running in headless mode
   */
  public isHeadless(): boolean {
    return this.config.browser.headless;
  }

  /**
   * Get browser timeout
   */
  public getBrowserTimeout(): number {
    return this.config.browser.timeout;
  }

  /**
   * Get viewport configuration
   */
  public getViewport(): { width: number; height: number } {
    return { ...this.config.browser.viewport };
  }

  /**
   * Get number of parallel workers
   */
  public getWorkers(): number {
    return this.config.parallel.workers;
  }

  /**
   * Get number of retries
   */
  public getRetries(): number {
    return this.config.parallel.retries;
  }

  /**
   * Get notification configuration
   */
  public getNotificationConfig(): {
    slack: { enabled: boolean; webhookUrl: string; channel: string };
    email: { enabled: boolean; smtpHost: string; smtpPort: number; username: string; password: string; from: string; to: string[] };
  } {
    return {
      slack: {
        enabled: this.config.notifications.slack.enabled,
        webhookUrl: this.config.notifications.slack.webhookUrl || '',
        channel: this.config.notifications.slack.channel || '#test-results'
      },
      email: {
        enabled: this.config.notifications.email.enabled,
        smtpHost: this.config.notifications.email.smtp.host || 'smtp.gmail.com',
        smtpPort: this.config.notifications.email.smtp.port || 587,
        username: this.config.notifications.email.smtp.username || '',
        password: this.config.notifications.email.smtp.password || '',
        from: this.config.notifications.email.smtp.username || '',
        to: this.config.notifications.email.recipients || []
      }
    };
  }

  /**
   * Get issue tracker URL
   */
  public getIssueTrackerUrl(): string {
    return process.env.ISSUE_TRACKER_URL || 'https://github.com/your-org/your-repo/issues';
  }

  /**
   * Get test management system URL
   */
  public getTestManagementUrl(): string {
    return process.env.TMS_URL || 'https://your-tms.com/testcases';
  }

  /**
   * Get test timeout
   */
  public getTimeout(): number {
    return this.config.browser.timeout;
  }

  /**
   * Check if screenshots are enabled
   */
  public areScreenshotsEnabled(): boolean {
    return this.config.reporting.screenshots;
  }

  /**
   * Check if videos are enabled
   */
  public areVideosEnabled(): boolean {
    return this.config.reporting.videos;
  }

  /**
   * Check if traces are enabled
   */
  public areTracesEnabled(): boolean {
    return this.config.reporting.traces;
  }

  /**
   * Check if Allure reports are enabled
   */
  public isAllureEnabled(): boolean {
    return this.config.reporting.allure;
  }

  /**
   * Get Slack configuration
   */
  public getSlackConfig(): TestConfig['notifications']['slack'] {
    return { ...this.config.notifications.slack };
  }

  /**
   * Get email configuration
   */
  public getEmailConfig(): TestConfig['notifications']['email'] {
    return { ...this.config.notifications.email };
  }

  /**
   * Get database configuration
   */
  public getDatabaseConfig(): TestConfig['database'] {
    return { ...this.config.database };
  }

  /**
   * Get API configuration
   */
  public getApiConfig(): TestConfig['api'] {
    return { ...this.config.api };
  }

  /**
   * Update configuration at runtime
   */
  public updateConfig(updates: Partial<TestConfig>): void {
    this.config = this.deepMerge(this.config, updates);
    this.validateConfiguration();
    this.logger.info('Configuration updated', updates);
  }

  /**
   * Get configuration value by path
   */
  public get<T>(path: string): T | undefined {
    const keys = path.split('.');
    let current: any = this.config;
    
    for (const key of keys) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        return undefined;
      }
    }
    
    return current as T;
  }

  /**
   * Check if configuration value exists
   */
  public has(path: string): boolean {
    return this.get(path) !== undefined;
  }

  /**
   * Get environment-specific test data path
   */
  public getTestDataPath(filename: string): string {
    const testDataDir = path.join(process.cwd(), 'src', 'fixtures', this.config.environment);
    return path.join(testDataDir, filename);
  }

  /**
   * Load test data from JSON file
   */
  public loadTestData<T>(filename: string): T {
    const filePath = this.getTestDataPath(filename);
    
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const data = JSON.parse(content);
      this.logger.debug(`Loaded test data from: ${filePath}`);
      return data as T;
    } catch (error) {
      this.logger.error(`Failed to load test data from ${filePath}:`, error);
      throw error;
    }
  }

  /**
   * Check if running in CI environment
   */
  public isCI(): boolean {
    return !!(process.env.CI || process.env.GITHUB_ACTIONS || process.env.GITLAB_CI || process.env.JENKINS_URL);
  }

  /**
   * Get CI environment name
   */
  public getCIEnvironment(): string | null {
    if (process.env.GITHUB_ACTIONS) return 'GitHub Actions';
    if (process.env.GITLAB_CI) return 'GitLab CI';
    if (process.env.JENKINS_URL) return 'Jenkins';
    if (process.env.CI) return 'Generic CI';
    return null;
  }
}