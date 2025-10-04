import winston from 'winston';
import path from 'path';

/**
 * Logger utility class for structured logging
 * Uses Winston for flexible and configurable logging
 */
export class Logger {
  private logger: winston.Logger;
  private className: string;

  constructor(className: string = 'Unknown') {
    this.className = className;
    this.logger = this.createLogger();
  }

  /**
   * Create Winston logger instance with custom configuration
   */
  private createLogger(): winston.Logger {
    const logFormat = winston.format.combine(
      winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      winston.format.errors({ stack: true }),
      winston.format.printf(({ timestamp, level, message, stack, ...meta }) => {
        const metaString = Object.keys(meta).length ? JSON.stringify(meta, null, 2) : '';
        const stackString = stack ? `\n${stack}` : '';
        return `[${timestamp}] [${level.toUpperCase()}] [${this.className}] ${message}${metaString}${stackString}`;
      })
    );

    const logger = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: logFormat,
      transports: [
        // Console transport
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            logFormat
          ),
        }),
        
        // File transport for all logs
        new winston.transports.File({
          filename: path.join('reports', 'logs', 'test-execution.log'),
          maxsize: 10 * 1024 * 1024, // 10MB
          maxFiles: 5,
          tailable: true,
        }),
        
        // Separate file for errors
        new winston.transports.File({
          filename: path.join('reports', 'logs', 'errors.log'),
          level: 'error',
          maxsize: 5 * 1024 * 1024, // 5MB
          maxFiles: 3,
          tailable: true,
        }),
      ],
      
      // Handle uncaught exceptions and rejections
      exceptionHandlers: [
        new winston.transports.File({
          filename: path.join('reports', 'logs', 'exceptions.log'),
        }),
      ],
      
      rejectionHandlers: [
        new winston.transports.File({
          filename: path.join('reports', 'logs', 'rejections.log'),
        }),
      ],
    });

    return logger;
  }

  /**
   * Log debug message
   * @param message - Debug message
   * @param meta - Additional metadata
   */
  debug(message: string, meta?: unknown): void {
    this.logger.debug(message, meta);
  }

  /**
   * Log info message
   * @param message - Info message
   * @param meta - Additional metadata
   */
  info(message: string, meta?: unknown): void {
    this.logger.info(message, meta);
  }

  /**
   * Log warning message
   * @param message - Warning message
   * @param meta - Additional metadata
   */
  warn(message: string, meta?: unknown): void {
    this.logger.warn(message, meta);
  }

  /**
   * Log error message
   * @param message - Error message
   * @param error - Error object or additional metadata
   */
  error(message: string, error?: unknown): void {
    if (error instanceof Error) {
      this.logger.error(message, { 
        error: error.message, 
        stack: error.stack,
        name: error.name,
      });
    } else {
      this.logger.error(message, error);
    }
  }

  /**
   * Log test step start
   * @param stepName - Name of the test step
   * @param details - Additional step details
   */
  stepStart(stepName: string, details?: unknown): void {
    this.logger.info(`🚀 STEP START: ${stepName}`, details);
  }

  /**
   * Log test step completion
   * @param stepName - Name of the test step
   * @param duration - Step duration in milliseconds
   * @param details - Additional step details
   */
  stepEnd(stepName: string, duration?: number, details?: unknown): void {
    const durationText = duration ? ` (${duration}ms)` : '';
    this.logger.info(`✅ STEP END: ${stepName}${durationText}`, details);
  }

  /**
   * Log test step failure
   * @param stepName - Name of the test step
   * @param error - Error that caused the failure
   * @param details - Additional step details
   */
  stepFailed(stepName: string, error: Error, details?: unknown): void {
    this.logger.error(`❌ STEP FAILED: ${stepName}`, {
      error: error.message,
      stack: error.stack,
      details,
    });
  }

  /**
   * Log test case start
   * @param testName - Name of the test case
   * @param testInfo - Additional test information
   */
  testStart(testName: string, testInfo?: unknown): void {
    this.logger.info(`🧪 TEST START: ${testName}`, testInfo);
  }

  /**
   * Log test case completion
   * @param testName - Name of the test case
   * @param status - Test status (passed/failed/skipped)
   * @param duration - Test duration in milliseconds
   */
  testEnd(testName: string, status: 'passed' | 'failed' | 'skipped', duration?: number): void {
    const statusEmoji = {
      passed: '✅',
      failed: '❌',
      skipped: '⏭️',
    };
    
    const durationText = duration ? ` (${duration}ms)` : '';
    this.logger.info(`${statusEmoji[status]} TEST ${status.toUpperCase()}: ${testName}${durationText}`);
  }

  /**
   * Log API request
   * @param method - HTTP method
   * @param url - Request URL
   * @param requestData - Request payload
   */
  apiRequest(method: string, url: string, requestData?: unknown): void {
    this.logger.info(`🌐 API REQUEST: ${method.toUpperCase()} ${url}`, {
      method,
      url,
      requestData,
    });
  }

  /**
   * Log API response
   * @param method - HTTP method
   * @param url - Request URL
   * @param status - Response status code
   * @param responseData - Response payload
   * @param duration - Request duration in milliseconds
   */
  apiResponse(method: string, url: string, status: number, responseData?: unknown, duration?: number): void {
    const statusEmoji = status >= 200 && status < 300 ? '✅' : '❌';
    const durationText = duration ? ` (${duration}ms)` : '';
    
    this.logger.info(`${statusEmoji} API RESPONSE: ${method.toUpperCase()} ${url} - ${status}${durationText}`, {
      method,
      url,
      status,
      responseData,
      duration,
    });
  }

  /**
   * Log page navigation
   * @param url - Target URL
   * @param fromUrl - Source URL
   */
  navigation(url: string, fromUrl?: string): void {
    const fromText = fromUrl ? ` from ${fromUrl}` : '';
    this.logger.info(`🧭 NAVIGATION: ${url}${fromText}`);
  }

  /**
   * Log user action
   * @param action - Action performed
   * @param element - Target element
   * @param value - Action value (if applicable)
   */
  userAction(action: string, element: string, value?: string): void {
    const valueText = value ? ` with value "${value}"` : '';
    this.logger.info(`👆 USER ACTION: ${action} on ${element}${valueText}`);
  }

  /**
   * Log assertion
   * @param assertion - Assertion description
   * @param expected - Expected value
   * @param actual - Actual value
   * @param passed - Whether assertion passed
   */
  assertion(assertion: string, expected: unknown, actual: unknown, passed: boolean): void {
    const statusEmoji = passed ? '✅' : '❌';
    const status = passed ? 'PASSED' : 'FAILED';
    
    this.logger.info(`${statusEmoji} ASSERTION ${status}: ${assertion}`, {
      expected,
      actual,
      passed,
    });
  }

  /**
   * Log performance metric
   * @param metric - Metric name
   * @param value - Metric value
   * @param unit - Metric unit
   */
  performance(metric: string, value: number, unit: string = 'ms'): void {
    this.logger.info(`📊 PERFORMANCE: ${metric} = ${value}${unit}`);
  }

  /**
   * Log screenshot capture
   * @param screenshotPath - Path to screenshot file
   * @param context - Screenshot context
   */
  screenshot(screenshotPath: string, context?: string): void {
    const contextText = context ? ` (${context})` : '';
    this.logger.info(`📸 SCREENSHOT: ${screenshotPath}${contextText}`);
  }

  /**
   * Create a child logger with additional context
   * @param childName - Child logger name
   * @param context - Additional context
   */
  child(childName: string, context?: Record<string, unknown>): Logger {
    const childLogger = new Logger(`${this.className}.${childName}`);
    
    if (context) {
      childLogger.logger = childLogger.logger.child(context);
    }
    
    return childLogger;
  }

  /**
   * Set log level dynamically
   * @param level - New log level
   */
  setLevel(level: string): void {
    this.logger.level = level;
    this.logger.info(`Log level changed to: ${level}`);
  }

  /**
   * Get current log level
   */
  getLevel(): string {
    return this.logger.level;
  }
}