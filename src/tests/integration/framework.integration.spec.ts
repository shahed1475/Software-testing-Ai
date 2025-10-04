import { test, expect } from '@playwright/test';
import { TagManager } from '../../utils/TagManager';
import { NotificationService } from '../../utils/NotificationService';
import { ReportGenerator } from '../../utils/ReportGenerator';
import { AllureReporter } from '../../utils/AllureReporter';
import { ConfigManager } from '../../utils/ConfigManager';
import { TestDataLoader } from '../../utils/TestDataLoader';

test.describe('Framework Integration Tests', () => {
  const tagManager = TagManager.getInstance();
  let notificationService: NotificationService;
  let reportGenerator: ReportGenerator;
  let allureReporter: AllureReporter;
  let configManager: ConfigManager;
  let testDataLoader: TestDataLoader;

  test.beforeAll(async () => {
    // Initialize framework components
    notificationService = new NotificationService();
    reportGenerator = new ReportGenerator();
    allureReporter = new AllureReporter();
    configManager = new ConfigManager();
    testDataLoader = new TestDataLoader();
  });

  test.beforeEach(async () => {
    // Clear any previous test registrations
    tagManager.clearRegistry();
  });

  // @integration @critical @framework @smoke
  test('should integrate TagManager with test execution @integration @critical @framework @smoke', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'TagManager Integration Test',
      tags: ['integration', 'critical', 'framework', 'smoke'],
      file: __filename,
      priority: 'critical',
      category: 'integration',
      browser: ['chrome']
    });

    // Test tag registration and filtering
    const testData = [
      {
        title: 'Test 1',
        tags: ['smoke', 'critical'],
        file: 'test1.spec.ts',
        priority: 'critical' as const,
        category: 'functional' as const
      },
      {
        title: 'Test 2',
        tags: ['regression', 'medium'],
        file: 'test2.spec.ts',
        priority: 'medium' as const,
        category: 'functional' as const
      }
    ];

    // Register multiple tests
    testData.forEach(test => tagManager.registerTest(test));

    // Test filtering functionality
    const smokeTests = tagManager.getTestsByTags(['smoke']);
    expect(smokeTests).toHaveLength(1);
    expect(smokeTests[0].title).toBe('Test 1');

    const criticalTests = tagManager.getTestsByPriority('critical');
    expect(criticalTests).toHaveLength(2); // Including the current test

    // Test grep pattern generation
    const grepPattern = tagManager.generatePlaywrightGrep(['smoke', 'critical']);
    expect(grepPattern).toContain('@smoke|@critical');

    // Test statistics
    const stats = tagManager.getTagStatistics();
    expect(stats.totalTests).toBeGreaterThan(0);
    expect(stats.tagDistribution).toHaveProperty('smoke');
    expect(stats.tagDistribution).toHaveProperty('critical');
  });

  // @integration @reporting @medium @framework
  test('should integrate ReportGenerator with AllureReporter @integration @reporting @medium @framework', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Reporting Integration Test',
      tags: ['integration', 'reporting', 'medium', 'framework'],
      file: __filename,
      priority: 'medium',
      category: 'integration',
      browser: ['chrome']
    });

    // Test report generation integration
    const testResults = {
      passed: 5,
      failed: 2,
      skipped: 1,
      total: 8,
      duration: 120000,
      timestamp: new Date().toISOString()
    };

    // Generate HTML report
    const htmlReport = await reportGenerator.generateHTMLReport(testResults, []);
    expect(htmlReport).toContain('Test Results Summary');
    expect(htmlReport).toContain('5'); // passed tests
    expect(htmlReport).toContain('2'); // failed tests

    // Test Allure integration
    allureReporter.startSuite('Integration Test Suite');
    allureReporter.startTest('Sample Test', ['integration', 'reporting']);
    allureReporter.addStep('Step 1: Initialize', 'passed');
    allureReporter.addStep('Step 2: Execute', 'passed');
    allureReporter.endTest('passed');
    allureReporter.endSuite();

    // Verify Allure metadata
    const allureData = allureReporter.getAllureData();
    expect(allureData.suites).toHaveLength(1);
    expect(allureData.suites[0].name).toBe('Integration Test Suite');
    expect(allureData.suites[0].tests).toHaveLength(1);
  });

  // @integration @config @medium @framework
  test('should integrate ConfigManager with environment settings @integration @config @medium @framework', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Config Integration Test',
      tags: ['integration', 'config', 'medium', 'framework'],
      file: __filename,
      priority: 'medium',
      category: 'integration'
    });

    // Test configuration management
    const defaultConfig = configManager.getConfig();
    expect(defaultConfig).toHaveProperty('baseURL');
    expect(defaultConfig).toHaveProperty('timeout');
    expect(defaultConfig).toHaveProperty('retries');

    // Test environment-specific configuration
    configManager.setEnvironment('staging');
    const stagingConfig = configManager.getConfig();
    expect(stagingConfig.baseURL).toContain('staging');

    configManager.setEnvironment('production');
    const prodConfig = configManager.getConfig();
    expect(prodConfig.baseURL).toContain('prod');

    // Test custom configuration override
    configManager.updateConfig({ timeout: 60000 });
    const updatedConfig = configManager.getConfig();
    expect(updatedConfig.timeout).toBe(60000);
  });

  // @integration @data @medium @framework
  test('should integrate TestDataLoader with test execution @integration @data @medium @framework', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Data Loader Integration Test',
      tags: ['integration', 'data', 'medium', 'framework'],
      file: __filename,
      priority: 'medium',
      category: 'integration'
    });

    // Test data loading functionality
    const testData = await testDataLoader.loadTestData('users');
    expect(testData).toBeDefined();
    expect(Array.isArray(testData)).toBe(true);

    // Test environment-specific data
    const stagingData = await testDataLoader.loadEnvironmentData('staging');
    expect(stagingData).toHaveProperty('baseURL');
    expect(stagingData).toHaveProperty('apiEndpoints');

    // Test data validation
    const userData = await testDataLoader.loadTestData('users');
    if (userData && userData.length > 0) {
      const firstUser = userData[0];
      expect(firstUser).toHaveProperty('email');
      expect(firstUser).toHaveProperty('password');
    }

    // Test data filtering
    const adminUsers = await testDataLoader.getFilteredData('users', { role: 'admin' });
    expect(Array.isArray(adminUsers)).toBe(true);
  });

  // @integration @notifications @low @framework
  test('should integrate NotificationService with test results @integration @notifications @low @framework', async () => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Notification Integration Test',
      tags: ['integration', 'notifications', 'low', 'framework'],
      file: __filename,
      priority: 'low',
      category: 'integration'
    });

    // Test notification service integration
    const testResults = {
      passed: 3,
      failed: 1,
      skipped: 0,
      total: 4,
      duration: 45000,
      timestamp: new Date().toISOString(),
      environment: 'staging',
      browser: 'chrome'
    };

    // Test Slack notification (mock)
    const slackResult = await notificationService.sendSlackNotification(
      'Test execution completed',
      testResults
    );
    expect(slackResult.success).toBe(true);

    // Test email notification (mock)
    const emailResult = await notificationService.sendEmailNotification(
      'test@example.com',
      'Test Results',
      testResults
    );
    expect(emailResult.success).toBe(true);

    // Test notification formatting
    const formattedMessage = notificationService.formatTestResults(testResults);
    expect(formattedMessage).toContain('3 passed');
    expect(formattedMessage).toContain('1 failed');
    expect(formattedMessage).toContain('staging');
  });

  // @integration @e2e @high @framework
  test('should perform end-to-end framework integration @integration @e2e @high @framework', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'End-to-End Framework Integration',
      tags: ['integration', 'e2e', 'high', 'framework'],
      file: __filename,
      priority: 'high',
      category: 'integration',
      browser: ['chrome']
    });

    // Simulate a complete test workflow
    
    // 1. Load configuration
    const config = configManager.getConfig();
    expect(config).toBeDefined();

    // 2. Load test data
    const testData = await testDataLoader.loadTestData('users');
    
    // 3. Execute a simple test with page interaction
    await page.goto('https://example.com');
    await page.waitForLoadState('networkidle');
    
    // 4. Generate test results
    const testResults = {
      passed: 1,
      failed: 0,
      skipped: 0,
      total: 1,
      duration: 5000,
      timestamp: new Date().toISOString(),
      testName: 'End-to-End Framework Integration',
      tags: ['integration', 'e2e', 'high', 'framework']
    };

    // 5. Generate reports
    const htmlReport = await reportGenerator.generateHTMLReport(testResults, []);
    expect(htmlReport).toContain('Test Results Summary');

    // 6. Record in Allure
    allureReporter.startSuite('E2E Integration Suite');
    allureReporter.startTest('Framework Integration Test', ['integration', 'e2e']);
    allureReporter.addStep('Load Configuration', 'passed');
    allureReporter.addStep('Load Test Data', 'passed');
    allureReporter.addStep('Execute Page Test', 'passed');
    allureReporter.addStep('Generate Reports', 'passed');
    allureReporter.endTest('passed');
    allureReporter.endSuite();

    // 7. Send notifications
    await notificationService.sendSlackNotification(
      'E2E Integration Test Completed',
      testResults
    );

    // 8. Verify tag statistics
    const stats = tagManager.getTagStatistics();
    expect(stats.totalTests).toBeGreaterThan(0);
    expect(stats.tagDistribution).toHaveProperty('integration');
    expect(stats.tagDistribution).toHaveProperty('framework');

    // 9. Test framework cleanup
    const exportedRegistry = tagManager.exportRegistry();
    expect(exportedRegistry).toBeDefined();
    expect(exportedRegistry.tests).toBeDefined();
    expect(Array.isArray(exportedRegistry.tests)).toBe(true);
  });

  test.afterAll(async () => {
    // Cleanup after all tests
    tagManager.clearRegistry();
    
    // Generate final integration report
    const finalStats = tagManager.getTagStatistics();
    console.log('Integration Test Statistics:', finalStats);
  });
});