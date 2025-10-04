import { TestResult, FullResult, Reporter, Suite, TestCase } from '@playwright/test/reporter';
import { Logger } from './Logger';
import { ConfigManager } from './ConfigManager';

export interface AllureStep {
  name: string;
  status: 'passed' | 'failed' | 'broken' | 'skipped';
  start: number;
  stop: number;
  parameters?: Array<{ name: string; value: string }>;
}

export interface AllureAttachment {
  name: string;
  type: string;
  source: string;
}

export interface AllureTestResult {
  uuid: string;
  name: string;
  fullName: string;
  status: 'passed' | 'failed' | 'broken' | 'skipped';
  start: number;
  stop: number;
  description?: string;
  steps: AllureStep[];
  attachments: AllureAttachment[];
  parameters: Array<{ name: string; value: string }>;
  labels: Array<{ name: string; value: string }>;
  links: Array<{ name: string; url: string; type: string }>;
}

export class AllureReporter implements Reporter {
  private logger: Logger;
  private config: ConfigManager;
  private testResults: Map<string, AllureTestResult> = new Map();
  private suiteStartTime: number = 0;

  constructor() {
    this.logger = Logger.getInstance();
    this.config = ConfigManager.getInstance();
  }

  onBegin(config: any, suite: Suite): void {
    this.suiteStartTime = Date.now();
    
    this.logger.info('Allure reporting started', {
      totalTests: suite.allTests().length,
      outputDir: config.outputDir || 'allure-results'
    });
  }

  onTestBegin(test: TestCase): void {
    const testId = this.generateTestId(test);
    const startTime = Date.now();

    const allureResult: AllureTestResult = {
      uuid: testId,
      name: test.title,
      fullName: `${test.parent.title} > ${test.title}`,
      status: 'skipped',
      start: startTime,
      stop: startTime,
      steps: [],
      attachments: [],
      parameters: this.extractParameters(test),
      labels: this.extractLabels(test),
      links: this.extractLinks(test)
    };

    this.testResults.set(testId, allureResult);

    this.logger.debug(`Allure test started: ${test.title}`, { testId });
  }

  onTestEnd(test: TestCase, result: TestResult): void {
    const testId = this.generateTestId(test);
    const allureResult = this.testResults.get(testId);

    if (!allureResult) {
      this.logger.warn(`Allure result not found for test: ${test.title}`);
      return;
    }

    // Update test result
    allureResult.stop = Date.now();
    allureResult.status = this.mapPlaywrightStatusToAllure(result.status);
    
    // Add description if available
    if (test.annotations.length > 0) {
      const description = test.annotations
        .filter(a => a.type === 'description')
        .map(a => a.description)
        .join('\n');
      if (description) {
        allureResult.description = description;
      }
    }

    // Process attachments
    this.processAttachments(result, allureResult);

    // Add steps from test execution
    this.addTestSteps(result, allureResult);

    // Add error information if test failed
    if (result.error) {
      this.addErrorStep(result.error, allureResult);
    }

    this.logger.debug(`Allure test completed: ${test.title}`, {
      testId,
      status: allureResult.status,
      duration: allureResult.stop - allureResult.start
    });
  }

  onEnd(result: FullResult): void {
    const endTime = Date.now();
    const duration = endTime - this.suiteStartTime;

    this.logger.info('Allure reporting completed', {
      status: result.status,
      duration,
      totalTests: this.testResults.size
    });

    // Generate Allure results
    this.generateAllureResults();
  }

  private generateTestId(test: TestCase): string {
    return `${test.location.file}:${test.location.line}:${test.title}`;
  }

  private mapPlaywrightStatusToAllure(status: string): 'passed' | 'failed' | 'broken' | 'skipped' {
    switch (status) {
      case 'passed':
        return 'passed';
      case 'failed':
        return 'failed';
      case 'timedOut':
        return 'broken';
      case 'skipped':
        return 'skipped';
      default:
        return 'broken';
    }
  }

  private extractParameters(test: TestCase): Array<{ name: string; value: string }> {
    const parameters: Array<{ name: string; value: string }> = [];

    // Extract browser information
    if (test.parent.project()?.name) {
      parameters.push({
        name: 'browser',
        value: test.parent.project().name
      });
    }

    // Extract test file
    parameters.push({
      name: 'testFile',
      value: test.location.file
    });

    // Extract custom parameters from annotations
    test.annotations.forEach(annotation => {
      if (annotation.type === 'parameter') {
        parameters.push({
          name: annotation.description || 'parameter',
          value: String(annotation)
        });
      }
    });

    return parameters;
  }

  private extractLabels(test: TestCase): Array<{ name: string; value: string }> {
    const labels: Array<{ name: string; value: string }> = [];

    // Add suite label
    labels.push({
      name: 'suite',
      value: test.parent.title
    });

    // Add feature label (from test file path)
    const featureName = this.extractFeatureFromPath(test.location.file);
    if (featureName) {
      labels.push({
        name: 'feature',
        value: featureName
      });
    }

    // Add story label (test title)
    labels.push({
      name: 'story',
      value: test.title
    });

    // Add severity (default to normal)
    labels.push({
      name: 'severity',
      value: this.extractSeverity(test)
    });

    // Add tags from annotations
    test.annotations.forEach(annotation => {
      if (annotation.type === 'tag') {
        labels.push({
          name: 'tag',
          value: annotation.description || ''
        });
      }
    });

    // Add browser label
    if (test.parent.project()?.name) {
      labels.push({
        name: 'browser',
        value: test.parent.project().name
      });
    }

    return labels;
  }

  private extractLinks(test: TestCase): Array<{ name: string; url: string; type: string }> {
    const links: Array<{ name: string; url: string; type: string }> = [];

    // Extract links from annotations
    test.annotations.forEach(annotation => {
      if (annotation.type === 'issue') {
        links.push({
          name: `Issue: ${annotation.description}`,
          url: `${this.config.getIssueTrackerUrl()}/${annotation.description}`,
          type: 'issue'
        });
      } else if (annotation.type === 'tms') {
        links.push({
          name: `Test Case: ${annotation.description}`,
          url: `${this.config.getTestManagementUrl()}/${annotation.description}`,
          type: 'tms'
        });
      }
    });

    return links;
  }

  private extractFeatureFromPath(filePath: string): string {
    // Extract feature name from file path
    const pathParts = filePath.split(/[/\\]/);
    const testsIndex = pathParts.findIndex(part => part === 'tests');
    
    if (testsIndex >= 0 && testsIndex < pathParts.length - 1) {
      return pathParts[testsIndex + 1];
    }
    
    return 'unknown';
  }

  private extractSeverity(test: TestCase): string {
    // Look for severity in annotations
    const severityAnnotation = test.annotations.find(a => a.type === 'severity');
    if (severityAnnotation) {
      return severityAnnotation.description || 'normal';
    }

    // Determine severity based on test title keywords
    const title = test.title.toLowerCase();
    if (title.includes('critical') || title.includes('blocker')) {
      return 'critical';
    } else if (title.includes('major') || title.includes('important')) {
      return 'major';
    } else if (title.includes('minor')) {
      return 'minor';
    } else if (title.includes('trivial')) {
      return 'trivial';
    }

    return 'normal';
  }

  private processAttachments(result: TestResult, allureResult: AllureTestResult): void {
    result.attachments.forEach(attachment => {
      const allureAttachment: AllureAttachment = {
        name: attachment.name,
        type: this.getAttachmentType(attachment.name, attachment.contentType),
        source: attachment.path || attachment.body?.toString() || ''
      };

      allureResult.attachments.push(allureAttachment);
    });
  }

  private getAttachmentType(name: string, contentType?: string): string {
    if (contentType) {
      return contentType;
    }

    // Determine type based on name
    if (name.includes('screenshot')) {
      return 'image/png';
    } else if (name.includes('video')) {
      return 'video/webm';
    } else if (name.includes('trace')) {
      return 'application/zip';
    } else if (name.includes('log')) {
      return 'text/plain';
    }

    return 'text/plain';
  }

  private addTestSteps(result: TestResult, allureResult: AllureTestResult): void {
    // Add basic test execution step
    const mainStep: AllureStep = {
      name: 'Test Execution',
      status: this.mapPlaywrightStatusToAllure(result.status),
      start: allureResult.start,
      stop: allureResult.stop
    };

    allureResult.steps.push(mainStep);

    // Add retry information if applicable
    if (result.retry > 0) {
      const retryStep: AllureStep = {
        name: `Retry Attempt ${result.retry}`,
        status: this.mapPlaywrightStatusToAllure(result.status),
        start: allureResult.start,
        stop: allureResult.stop,
        parameters: [
          { name: 'retryCount', value: result.retry.toString() }
        ]
      };

      allureResult.steps.push(retryStep);
    }
  }

  private addErrorStep(error: any, allureResult: AllureTestResult): void {
    const errorStep: AllureStep = {
      name: 'Error Details',
      status: 'failed',
      start: allureResult.stop - 1000, // Approximate error time
      stop: allureResult.stop,
      parameters: [
        { name: 'errorMessage', value: error.message || 'Unknown error' },
        { name: 'errorStack', value: error.stack || 'No stack trace available' }
      ]
    };

    allureResult.steps.push(errorStep);
  }

  private generateAllureResults(): void {
    try {
      const fs = require('fs');
      const path = require('path');
      
      const resultsDir = path.join(process.cwd(), 'allure-results');
      
      // Create results directory if it doesn't exist
      if (!fs.existsSync(resultsDir)) {
        fs.mkdirSync(resultsDir, { recursive: true });
      }

      // Generate environment properties
      this.generateEnvironmentProperties(resultsDir);

      // Generate categories (for grouping failures)
      this.generateCategories(resultsDir);

      // Generate test results
      this.testResults.forEach((result, testId) => {
        const resultFileName = `${result.uuid}-result.json`;
        const resultPath = path.join(resultsDir, resultFileName);
        
        fs.writeFileSync(resultPath, JSON.stringify(result, null, 2), 'utf8');
      });

      this.logger.info(`Allure results generated in: ${resultsDir}`, {
        testCount: this.testResults.size
      });

    } catch (error) {
      this.logger.error('Failed to generate Allure results', { error });
    }
  }

  private generateEnvironmentProperties(resultsDir: string): void {
    const fs = require('fs');
    const path = require('path');

    const environmentData = {
      'Browser': process.env.BROWSER || 'chromium',
      'Base URL': this.config.getBaseUrl(),
      'Environment': process.env.NODE_ENV || 'test',
      'OS': process.platform,
      'Node Version': process.version,
      'Playwright Version': require('@playwright/test/package.json').version,
      'Test Execution Date': new Date().toISOString()
    };

    const envContent = Object.entries(environmentData)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');

    const envPath = path.join(resultsDir, 'environment.properties');
    fs.writeFileSync(envPath, envContent, 'utf8');
  }

  private generateCategories(resultsDir: string): void {
    const fs = require('fs');
    const path = require('path');

    const categories = [
      {
        name: 'Ignored tests',
        matchedStatuses: ['skipped']
      },
      {
        name: 'Infrastructure problems',
        matchedStatuses: ['broken'],
        messageRegex: '.*timeout.*|.*connection.*|.*network.*'
      },
      {
        name: 'Outdated tests',
        matchedStatuses: ['broken'],
        messageRegex: '.*deprecated.*|.*obsolete.*'
      },
      {
        name: 'Product defects',
        matchedStatuses: ['failed']
      },
      {
        name: 'Test defects',
        matchedStatuses: ['broken']
      }
    ];

    const categoriesPath = path.join(resultsDir, 'categories.json');
    fs.writeFileSync(categoriesPath, JSON.stringify(categories, null, 2), 'utf8');
  }

  // Utility methods for adding custom information during test execution
  public static addStep(name: string, status: 'passed' | 'failed' | 'broken' | 'skipped' = 'passed'): void {
    // This would be used within tests to add custom steps
    // Implementation would depend on how you want to integrate with test execution
    console.log(`Allure Step: ${name} - ${status}`);
  }

  public static addAttachment(name: string, content: string | Buffer, type: string = 'text/plain'): void {
    // This would be used within tests to add custom attachments
    // Implementation would depend on how you want to integrate with test execution
    console.log(`Allure Attachment: ${name} - ${type}`);
  }

  public static addParameter(name: string, value: string): void {
    // This would be used within tests to add custom parameters
    console.log(`Allure Parameter: ${name} = ${value}`);
  }

  public static addLabel(name: string, value: string): void {
    // This would be used within tests to add custom labels
    console.log(`Allure Label: ${name} = ${value}`);
  }

  public static addLink(name: string, url: string, type: string = 'link'): void {
    // This would be used within tests to add custom links
    console.log(`Allure Link: ${name} - ${url} (${type})`);
  }
}