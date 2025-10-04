import * as nodemailer from 'nodemailer';
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
  environment: string;
  browser?: string;
  project?: string;
}

export interface TestFailure {
  title: string;
  file: string;
  error: string;
  screenshot?: string;
  trace?: string;
}

export interface NotificationData {
  summary: TestSummary;
  failures: TestFailure[];
  reportUrl?: string;
  allureUrl?: string;
  runId?: string;
  branch?: string;
  commit?: string;
  actor?: string;
}

/**
 * NotificationService - Handles sending notifications via Slack and Email
 * Integrates with test results and reporting systems
 */
export class NotificationService {
  private static instance: NotificationService;
  private logger: Logger;
  private config: ConfigManager;

  private constructor() {
    this.logger = Logger.getInstance();
    this.config = ConfigManager.getInstance();
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  /**
   * Send notifications for test results
   */
  public async sendTestResults(data: NotificationData): Promise<void> {
    const notificationConfig = this.config.getNotificationConfig();

    try {
      // Send Slack notification if enabled
      if (notificationConfig.slack.enabled && notificationConfig.slack.webhookUrl) {
        await this.sendSlackNotification(data, notificationConfig.slack);
      }

      // Send email notification if enabled
      if (notificationConfig.email.enabled && notificationConfig.email.to.length > 0) {
        await this.sendEmailNotification(data, notificationConfig.email);
      }

      this.logger.info('Test result notifications sent successfully');
    } catch (error) {
      this.logger.error(`Failed to send notifications: ${error}`);
      throw error;
    }
  }

  /**
   * Send Slack notification
   */
  private async sendSlackNotification(
    data: NotificationData,
    slackConfig: { webhookUrl: string; channel: string }
  ): Promise<void> {
    try {
      const { summary, failures } = data;
      const status = summary.failed === 0 ? 'success' : 'failure';
      const statusEmoji = status === 'success' ? '✅' : '❌';
      const color = status === 'success' ? 'good' : 'danger';

      // Calculate success rate
      const successRate = summary.total > 0 ? ((summary.passed / summary.total) * 100).toFixed(1) : '0';

      // Format duration
      const durationMinutes = Math.round(summary.duration / 60000);
      const durationText = durationMinutes > 0 ? `${durationMinutes}m` : `${Math.round(summary.duration / 1000)}s`;

      const payload = {
        channel: slackConfig.channel,
        username: 'Playwright Test Bot',
        icon_emoji: ':test_tube:',
        attachments: [
          {
            color: color,
            title: `${statusEmoji} Playwright Test Results`,
            fields: [
              {
                title: 'Summary',
                value: `• Total: ${summary.total}\n• Passed: ${summary.passed}\n• Failed: ${summary.failed}\n• Skipped: ${summary.skipped}${summary.flaky > 0 ? `\n• Flaky: ${summary.flaky}` : ''}`,
                short: true
              },
              {
                title: 'Details',
                value: `• Success Rate: ${successRate}%\n• Duration: ${durationText}\n• Environment: ${summary.environment}${summary.browser ? `\n• Browser: ${summary.browser}` : ''}${summary.project ? `\n• Project: ${summary.project}` : ''}`,
                short: true
              }
            ],
            footer: 'Playwright Test Framework',
            ts: Math.floor(summary.endTime.getTime() / 1000)
          }
        ]
      };

      // Add failure details if there are any
      if (failures.length > 0) {
        const failureText = failures.slice(0, 5).map(failure => 
          `• ${failure.title}\n  📁 ${failure.file}\n  ❌ ${failure.error.substring(0, 100)}${failure.error.length > 100 ? '...' : ''}`
        ).join('\n\n');

        payload.attachments.push({
          color: 'danger',
          title: `❌ Failed Tests (${failures.length})`,
          text: failureText + (failures.length > 5 ? `\n\n... and ${failures.length - 5} more failures` : ''),
          mrkdwn_in: ['text']
        });
      }

      // Add action buttons
      const actions = [];
      if (data.reportUrl) {
        actions.push({
          type: 'button',
          text: 'View Report',
          url: data.reportUrl,
          style: 'primary'
        });
      }
      if (data.allureUrl) {
        actions.push({
          type: 'button',
          text: 'Allure Report',
          url: data.allureUrl
        });
      }
      if (data.runId) {
        actions.push({
          type: 'button',
          text: 'GitHub Actions',
          url: `https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${data.runId}`
        });
      }

      if (actions.length > 0) {
        payload.attachments.push({
          color: 'good',
          actions: actions
        });
      }

      // Send to Slack
      const response = await fetch(slackConfig.webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Slack API error: ${response.status} ${response.statusText}`);
      }

      this.logger.info('Slack notification sent successfully');
    } catch (error) {
      this.logger.error(`Failed to send Slack notification: ${error}`);
      throw error;
    }
  }

  /**
   * Send email notification
   */
  private async sendEmailNotification(
    data: NotificationData,
    emailConfig: {
      smtpHost: string;
      smtpPort: number;
      username: string;
      password: string;
      from: string;
      to: string[];
    }
  ): Promise<void> {
    try {
      const { summary, failures } = data;
      const status = summary.failed === 0 ? 'PASSED' : 'FAILED';
      const statusColor = status === 'PASSED' ? '#28a745' : '#dc3545';

      // Create transporter
      const transporter = nodemailer.createTransporter({
        host: emailConfig.smtpHost,
        port: emailConfig.smtpPort,
        secure: emailConfig.smtpPort === 465,
        auth: {
          user: emailConfig.username,
          pass: emailConfig.password
        }
      });

      // Calculate success rate
      const successRate = summary.total > 0 ? ((summary.passed / summary.total) * 100).toFixed(1) : '0';

      // Format duration
      const durationMinutes = Math.round(summary.duration / 60000);
      const durationText = durationMinutes > 0 ? `${durationMinutes} minutes` : `${Math.round(summary.duration / 1000)} seconds`;

      // Generate HTML content
      const htmlContent = this.generateEmailHTML(data, status, statusColor, successRate, durationText);

      // Email options
      const mailOptions = {
        from: emailConfig.from,
        to: emailConfig.to.join(', '),
        subject: `🎭 Playwright Test Results - ${status} (${successRate}% success rate)`,
        html: htmlContent,
        attachments: []
      };

      // Add screenshots as attachments if available
      if (failures.length > 0) {
        failures.forEach((failure, index) => {
          if (failure.screenshot) {
            mailOptions.attachments.push({
              filename: `failure-${index + 1}-screenshot.png`,
              path: failure.screenshot,
              cid: `screenshot${index + 1}`
            });
          }
        });
      }

      // Send email
      await transporter.sendMail(mailOptions);
      this.logger.info(`Email notification sent to: ${emailConfig.to.join(', ')}`);
    } catch (error) {
      this.logger.error(`Failed to send email notification: ${error}`);
      throw error;
    }
  }

  /**
   * Generate HTML content for email
   */
  private generateEmailHTML(
    data: NotificationData,
    status: string,
    statusColor: string,
    successRate: string,
    durationText: string
  ): string {
    const { summary, failures } = data;

    return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Playwright Test Results</title>
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background-color: #f4f4f4; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; padding: 20px 0; border-bottom: 2px solid #eee; }
        .status { font-size: 24px; font-weight: bold; color: ${statusColor}; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: ${statusColor}; }
        .metric-label { font-size: 14px; color: #666; margin-top: 5px; }
        .failures { margin-top: 30px; }
        .failure { background: #fff5f5; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; border-radius: 4px; }
        .failure-title { font-weight: bold; color: #dc3545; margin-bottom: 5px; }
        .failure-file { font-size: 12px; color: #666; margin-bottom: 10px; }
        .failure-error { background: #f8f8f8; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; }
        .links { margin-top: 30px; text-align: center; }
        .button { display: inline-block; padding: 10px 20px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🎭 Playwright Test Results</h1>
          <div class="status">${status}</div>
          <p>Test run completed on ${summary.endTime.toLocaleString()}</p>
        </div>

        <div class="summary">
          <div class="metric">
            <div class="metric-value">${summary.total}</div>
            <div class="metric-label">Total Tests</div>
          </div>
          <div class="metric">
            <div class="metric-value" style="color: #28a745;">${summary.passed}</div>
            <div class="metric-label">Passed</div>
          </div>
          <div class="metric">
            <div class="metric-value" style="color: #dc3545;">${summary.failed}</div>
            <div class="metric-label">Failed</div>
          </div>
          <div class="metric">
            <div class="metric-value" style="color: #ffc107;">${summary.skipped}</div>
            <div class="metric-label">Skipped</div>
          </div>
          ${summary.flaky > 0 ? `
          <div class="metric">
            <div class="metric-value" style="color: #fd7e14;">${summary.flaky}</div>
            <div class="metric-label">Flaky</div>
          </div>
          ` : ''}
          <div class="metric">
            <div class="metric-value">${successRate}%</div>
            <div class="metric-label">Success Rate</div>
          </div>
          <div class="metric">
            <div class="metric-value">${durationText}</div>
            <div class="metric-label">Duration</div>
          </div>
        </div>

        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0;">
          <strong>Environment Details:</strong><br>
          • Environment: ${summary.environment}<br>
          ${summary.browser ? `• Browser: ${summary.browser}<br>` : ''}
          ${summary.project ? `• Project: ${summary.project}<br>` : ''}
          ${data.branch ? `• Branch: ${data.branch}<br>` : ''}
          ${data.commit ? `• Commit: ${data.commit}<br>` : ''}
          ${data.actor ? `• Triggered by: ${data.actor}<br>` : ''}
        </div>

        ${failures.length > 0 ? `
        <div class="failures">
          <h2>❌ Failed Tests (${failures.length})</h2>
          ${failures.slice(0, 10).map((failure, index) => `
          <div class="failure">
            <div class="failure-title">${failure.title}</div>
            <div class="failure-file">📁 ${failure.file}</div>
            <div class="failure-error">${failure.error}</div>
            ${failure.screenshot ? `<p><em>Screenshot attached as failure-${index + 1}-screenshot.png</em></p>` : ''}
          </div>
          `).join('')}
          ${failures.length > 10 ? `<p><em>... and ${failures.length - 10} more failures</em></p>` : ''}
        </div>
        ` : ''}

        <div class="links">
          ${data.reportUrl ? `<a href="${data.reportUrl}" class="button">View HTML Report</a>` : ''}
          ${data.allureUrl ? `<a href="${data.allureUrl}" class="button">View Allure Report</a>` : ''}
          ${data.runId ? `<a href="https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${data.runId}" class="button">View GitHub Actions</a>` : ''}
        </div>

        <div class="footer">
          <p>Generated by Playwright Test Automation Framework</p>
          <p>This is an automated message. Please do not reply to this email.</p>
        </div>
      </div>
    </body>
    </html>
    `;
  }

  /**
   * Send simple notification (for quick alerts)
   */
  public async sendSimpleNotification(
    title: string,
    message: string,
    type: 'success' | 'warning' | 'error' = 'success'
  ): Promise<void> {
    const notificationConfig = this.config.getNotificationConfig();

    try {
      // Send to Slack if enabled
      if (notificationConfig.slack.enabled && notificationConfig.slack.webhookUrl) {
        const emoji = type === 'success' ? '✅' : type === 'warning' ? '⚠️' : '❌';
        const color = type === 'success' ? 'good' : type === 'warning' ? 'warning' : 'danger';

        const payload = {
          channel: notificationConfig.slack.channel,
          username: 'Playwright Test Bot',
          icon_emoji: ':test_tube:',
          attachments: [
            {
              color: color,
              title: `${emoji} ${title}`,
              text: message,
              footer: 'Playwright Test Framework',
              ts: Math.floor(Date.now() / 1000)
            }
          ]
        };

        await fetch(notificationConfig.slack.webhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      this.logger.info(`Simple notification sent: ${title}`);
    } catch (error) {
      this.logger.error(`Failed to send simple notification: ${error}`);
    }
  }

  /**
   * Test notification configuration
   */
  public async testNotifications(): Promise<{ slack: boolean; email: boolean }> {
    const results = { slack: false, email: false };
    const notificationConfig = this.config.getNotificationConfig();

    // Test Slack
    if (notificationConfig.slack.enabled && notificationConfig.slack.webhookUrl) {
      try {
        await this.sendSimpleNotification(
          'Test Notification',
          'This is a test message from Playwright Test Framework',
          'success'
        );
        results.slack = true;
        this.logger.info('Slack notification test successful');
      } catch (error) {
        this.logger.error(`Slack notification test failed: ${error}`);
      }
    }

    // Test Email
    if (notificationConfig.email.enabled && notificationConfig.email.to.length > 0) {
      try {
        const testData: NotificationData = {
          summary: {
            total: 1,
            passed: 1,
            failed: 0,
            skipped: 0,
            flaky: 0,
            duration: 5000,
            startTime: new Date(),
            endTime: new Date(),
            environment: 'test'
          },
          failures: []
        };

        await this.sendEmailNotification(testData, notificationConfig.email);
        results.email = true;
        this.logger.info('Email notification test successful');
      } catch (error) {
        this.logger.error(`Email notification test failed: ${error}`);
      }
    }

    return results;
  }
}