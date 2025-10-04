import { TestResult, FullResult, Reporter, Suite, TestCase } from '@playwright/test/reporter';
import * as fs from 'fs';
import * as path from 'path';
import { Logger } from './Logger';
import { ConfigManager } from './ConfigManager';

export interface TestSummary {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  flaky: number;
  duration: number;
  startTime: Date;
  endTime: Date;
}

export interface TestFailure {
  testTitle: string;
  testFile: string;
  error: string;
  screenshot?: string;
  trace?: string;
  duration: number;
}

export interface CustomReportData {
  summary: TestSummary;
  failures: TestFailure[];
  environment: {
    browser: string;
    os: string;
    nodeVersion: string;
    playwrightVersion: string;
  };
  configuration: {
    baseUrl: string;
    timeout: number;
    retries: number;
    workers: number;
  };
}

export class ReportGenerator implements Reporter {
  private logger: Logger;
  private config: ConfigManager;
  private startTime: Date = new Date();
  private endTime: Date = new Date();
  private testResults: TestResult[] = [];
  private reportData: CustomReportData;

  constructor() {
    this.logger = Logger.getInstance();
    this.config = ConfigManager.getInstance();
    
    this.reportData = {
      summary: {
        total: 0,
        passed: 0,
        failed: 0,
        skipped: 0,
        flaky: 0,
        duration: 0,
        startTime: this.startTime,
        endTime: this.endTime
      },
      failures: [],
      environment: {
        browser: process.env.BROWSER || 'chromium',
        os: process.platform,
        nodeVersion: process.version,
        playwrightVersion: require('@playwright/test/package.json').version
      },
      configuration: {
        baseUrl: this.config.getBaseUrl(),
        timeout: this.config.getTimeout(),
        retries: this.config.getRetries(),
        workers: this.config.getWorkers()
      }
    };
  }

  onBegin(config: any, suite: Suite): void {
    this.startTime = new Date();
    this.reportData.summary.startTime = this.startTime;
    
    this.logger.info('Test execution started', {
      totalTests: suite.allTests().length,
      workers: config.workers,
      projects: config.projects.map((p: any) => p.name)
    });
  }

  onTestEnd(test: TestCase, result: TestResult): void {
    this.testResults.push(result);
    
    // Update summary
    this.reportData.summary.total++;
    
    switch (result.status) {
      case 'passed':
        this.reportData.summary.passed++;
        break;
      case 'failed':
        this.reportData.summary.failed++;
        this.addFailure(test, result);
        break;
      case 'skipped':
        this.reportData.summary.skipped++;
        break;
      case 'timedOut':
        this.reportData.summary.failed++;
        this.addFailure(test, result);
        break;
    }

    // Check for flaky tests
    if (result.retry > 0 && result.status === 'passed') {
      this.reportData.summary.flaky++;
    }

    this.logger.info(`Test completed: ${test.title}`, {
      status: result.status,
      duration: result.duration,
      retry: result.retry
    });
  }

  onEnd(result: FullResult): void {
    this.endTime = new Date();
    this.reportData.summary.endTime = this.endTime;
    this.reportData.summary.duration = this.endTime.getTime() - this.startTime.getTime();

    this.logger.info('Test execution completed', {
      status: result.status,
      duration: this.reportData.summary.duration,
      summary: this.reportData.summary
    });

    // Generate custom reports
    this.generateHtmlReport();
    this.generateJsonReport();
    this.generateJunitReport();
    
    // Send notifications if configured
    this.sendNotifications();
  }

  private addFailure(test: TestCase, result: TestResult): void {
    const failure: TestFailure = {
      testTitle: test.title,
      testFile: test.location.file,
      error: result.error?.message || 'Unknown error',
      duration: result.duration,
      screenshot: this.getScreenshotPath(result),
      trace: this.getTracePath(result)
    };

    this.reportData.failures.push(failure);
  }

  private getScreenshotPath(result: TestResult): string | undefined {
    const attachment = result.attachments.find(a => a.name === 'screenshot');
    return attachment?.path;
  }

  private getTracePath(result: TestResult): string | undefined {
    const attachment = result.attachments.find(a => a.name === 'trace');
    return attachment?.path;
  }

  private generateHtmlReport(): void {
    try {
      const reportsDir = path.join(process.cwd(), 'reports');
      if (!fs.existsSync(reportsDir)) {
        fs.mkdirSync(reportsDir, { recursive: true });
      }

      const htmlContent = this.generateHtmlContent();
      const htmlPath = path.join(reportsDir, 'custom-report.html');
      
      fs.writeFileSync(htmlPath, htmlContent, 'utf8');
      
      this.logger.info(`Custom HTML report generated: ${htmlPath}`);
    } catch (error) {
      this.logger.error('Failed to generate HTML report', { error });
    }
  }

  private generateHtmlContent(): string {
    const { summary, failures, environment, configuration } = this.reportData;
    const passRate = summary.total > 0 ? ((summary.passed / summary.total) * 100).toFixed(2) : '0';
    
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Playwright Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }
        .summary-card.passed { border-left-color: #28a745; }
        .summary-card.failed { border-left-color: #dc3545; }
        .summary-card.skipped { border-left-color: #ffc107; }
        .summary-card.flaky { border-left-color: #fd7e14; }
        .summary-card h3 { margin: 0 0 10px 0; color: #333; }
        .summary-card .number { font-size: 2em; font-weight: bold; color: #007bff; }
        .passed .number { color: #28a745; }
        .failed .number { color: #dc3545; }
        .skipped .number { color: #ffc107; }
        .flaky .number { color: #fd7e14; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .info-card { background: #f8f9fa; padding: 15px; border-radius: 8px; }
        .info-card h3 { margin-top: 0; color: #007bff; }
        .failures { margin-top: 30px; }
        .failure { background: #fff5f5; border: 1px solid #fed7d7; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        .failure h4 { color: #e53e3e; margin-top: 0; }
        .failure .file { color: #666; font-size: 0.9em; margin-bottom: 10px; }
        .failure .error { background: #f7fafc; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.9em; white-space: pre-wrap; }
        .progress-bar { width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s ease; }
        .timestamp { color: #666; font-size: 0.9em; }
        .no-failures { text-align: center; color: #28a745; font-style: italic; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 Playwright Test Report</h1>
            <p class="timestamp">Generated on ${this.endTime.toLocaleString()}</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${passRate}%"></div>
            </div>
            <p><strong>Pass Rate: ${passRate}%</strong></p>
        </div>

        <div class="section">
            <h2>📊 Test Summary</h2>
            <div class="summary">
                <div class="summary-card">
                    <h3>Total Tests</h3>
                    <div class="number">${summary.total}</div>
                </div>
                <div class="summary-card passed">
                    <h3>Passed</h3>
                    <div class="number">${summary.passed}</div>
                </div>
                <div class="summary-card failed">
                    <h3>Failed</h3>
                    <div class="number">${summary.failed}</div>
                </div>
                <div class="summary-card skipped">
                    <h3>Skipped</h3>
                    <div class="number">${summary.skipped}</div>
                </div>
                <div class="summary-card flaky">
                    <h3>Flaky</h3>
                    <div class="number">${summary.flaky}</div>
                </div>
                <div class="summary-card">
                    <h3>Duration</h3>
                    <div class="number">${Math.round(summary.duration / 1000)}s</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🔧 Environment & Configuration</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>Environment</h3>
                    <p><strong>Browser:</strong> ${environment.browser}</p>
                    <p><strong>OS:</strong> ${environment.os}</p>
                    <p><strong>Node.js:</strong> ${environment.nodeVersion}</p>
                    <p><strong>Playwright:</strong> ${environment.playwrightVersion}</p>
                </div>
                <div class="info-card">
                    <h3>Configuration</h3>
                    <p><strong>Base URL:</strong> ${configuration.baseUrl}</p>
                    <p><strong>Timeout:</strong> ${configuration.timeout}ms</p>
                    <p><strong>Retries:</strong> ${configuration.retries}</p>
                    <p><strong>Workers:</strong> ${configuration.workers}</p>
                </div>
            </div>
        </div>

        ${failures.length > 0 ? `
        <div class="section failures">
            <h2>❌ Test Failures (${failures.length})</h2>
            ${failures.map(failure => `
                <div class="failure">
                    <h4>${failure.testTitle}</h4>
                    <div class="file">📁 ${failure.testFile}</div>
                    <div class="error">${failure.error}</div>
                    <p><strong>Duration:</strong> ${failure.duration}ms</p>
                    ${failure.screenshot ? `<p><strong>Screenshot:</strong> ${failure.screenshot}</p>` : ''}
                    ${failure.trace ? `<p><strong>Trace:</strong> ${failure.trace}</p>` : ''}
                </div>
            `).join('')}
        </div>
        ` : `
        <div class="section">
            <h2>✅ Test Failures</h2>
            <div class="no-failures">🎉 No test failures! All tests passed successfully.</div>
        </div>
        `}
    </div>
</body>
</html>`;
  }

  private generateJsonReport(): void {
    try {
      const reportsDir = path.join(process.cwd(), 'reports');
      if (!fs.existsSync(reportsDir)) {
        fs.mkdirSync(reportsDir, { recursive: true });
      }

      const jsonPath = path.join(reportsDir, 'test-results.json');
      fs.writeFileSync(jsonPath, JSON.stringify(this.reportData, null, 2), 'utf8');
      
      this.logger.info(`JSON report generated: ${jsonPath}`);
    } catch (error) {
      this.logger.error('Failed to generate JSON report', { error });
    }
  }

  private generateJunitReport(): void {
    try {
      const reportsDir = path.join(process.cwd(), 'reports');
      if (!fs.existsSync(reportsDir)) {
        fs.mkdirSync(reportsDir, { recursive: true });
      }

      const junitContent = this.generateJunitXml();
      const junitPath = path.join(reportsDir, 'junit-results.xml');
      
      fs.writeFileSync(junitPath, junitContent, 'utf8');
      
      this.logger.info(`JUnit report generated: ${junitPath}`);
    } catch (error) {
      this.logger.error('Failed to generate JUnit report', { error });
    }
  }

  private generateJunitXml(): string {
    const { summary, failures } = this.reportData;
    const timestamp = this.startTime.toISOString();
    const duration = (summary.duration / 1000).toFixed(3);

    let xml = `<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="Playwright Tests" tests="${summary.total}" failures="${summary.failed}" skipped="${summary.skipped}" time="${duration}" timestamp="${timestamp}">
  <testsuite name="All Tests" tests="${summary.total}" failures="${summary.failed}" skipped="${summary.skipped}" time="${duration}">`;

    // Add test cases (simplified - in real implementation you'd iterate through actual test results)
    for (let i = 0; i < summary.passed; i++) {
      xml += `
    <testcase name="Passed Test ${i + 1}" classname="PassedTests" time="1.0"/>`;
    }

    failures.forEach((failure, index) => {
      xml += `
    <testcase name="${this.escapeXml(failure.testTitle)}" classname="${this.escapeXml(failure.testFile)}" time="${(failure.duration / 1000).toFixed(3)}">
      <failure message="${this.escapeXml(failure.error)}" type="AssertionError">
        ${this.escapeXml(failure.error)}
      </failure>
    </testcase>`;
    });

    for (let i = 0; i < summary.skipped; i++) {
      xml += `
    <testcase name="Skipped Test ${i + 1}" classname="SkippedTests" time="0.0">
      <skipped/>
    </testcase>`;
    }

    xml += `
  </testsuite>
</testsuites>`;

    return xml;
  }

  private escapeXml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  private async sendNotifications(): Promise<void> {
    try {
      const notificationConfig = this.config.getNotificationConfig();
      
      if (notificationConfig.slack.enabled) {
        await this.sendSlackNotification();
      }
      
      if (notificationConfig.email.enabled) {
        await this.sendEmailNotification();
      }
    } catch (error) {
      this.logger.error('Failed to send notifications', { error });
    }
  }

  private async sendSlackNotification(): Promise<void> {
    try {
      const { summary } = this.reportData;
      const passRate = summary.total > 0 ? ((summary.passed / summary.total) * 100).toFixed(2) : '0';
      const status = summary.failed > 0 ? '❌ FAILED' : '✅ PASSED';
      const color = summary.failed > 0 ? '#dc3545' : '#28a745';

      const slackMessage = {
        text: `Playwright Test Results ${status}`,
        attachments: [
          {
            color: color,
            fields: [
              {
                title: 'Test Summary',
                value: `Total: ${summary.total} | Passed: ${summary.passed} | Failed: ${summary.failed} | Skipped: ${summary.skipped}`,
                short: false
              },
              {
                title: 'Pass Rate',
                value: `${passRate}%`,
                short: true
              },
              {
                title: 'Duration',
                value: `${Math.round(summary.duration / 1000)}s`,
                short: true
              }
            ],
            footer: 'Playwright Test Framework',
            ts: Math.floor(this.endTime.getTime() / 1000)
          }
        ]
      };

      // Note: In a real implementation, you would use a Slack webhook or API
      this.logger.info('Slack notification prepared', { message: slackMessage });
    } catch (error) {
      this.logger.error('Failed to send Slack notification', { error });
    }
  }

  private async sendEmailNotification(): Promise<void> {
    try {
      const { summary } = this.reportData;
      const passRate = summary.total > 0 ? ((summary.passed / summary.total) * 100).toFixed(2) : '0';
      const status = summary.failed > 0 ? 'FAILED' : 'PASSED';

      const emailContent = {
        subject: `Playwright Test Results - ${status}`,
        html: `
          <h2>Playwright Test Execution Results</h2>
          <p><strong>Status:</strong> ${status}</p>
          <p><strong>Pass Rate:</strong> ${passRate}%</p>
          
          <h3>Summary:</h3>
          <ul>
            <li>Total Tests: ${summary.total}</li>
            <li>Passed: ${summary.passed}</li>
            <li>Failed: ${summary.failed}</li>
            <li>Skipped: ${summary.skipped}</li>
            <li>Duration: ${Math.round(summary.duration / 1000)}s</li>
          </ul>
          
          <p>Execution completed at: ${this.endTime.toLocaleString()}</p>
        `
      };

      // Note: In a real implementation, you would use an email service
      this.logger.info('Email notification prepared', { content: emailContent });
    } catch (error) {
      this.logger.error('Failed to send email notification', { error });
    }
  }

  // Utility methods for external use
  public getTestSummary(): TestSummary {
    return this.reportData.summary;
  }

  public getFailures(): TestFailure[] {
    return this.reportData.failures;
  }

  public getReportData(): CustomReportData {
    return this.reportData;
  }
}