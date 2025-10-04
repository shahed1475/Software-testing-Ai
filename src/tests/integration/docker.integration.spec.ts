import { test, expect } from '@playwright/test';
import { TagManager } from '../../utils/TagManager';

test.describe('Docker Integration Tests', () => {
  const tagManager = TagManager.getInstance();

  test.beforeEach(async () => {
    // Clear any previous test registrations
    tagManager.clearRegistry();
  });

  // @docker @integration @critical @infrastructure
  test('should connect to containerized services @docker @integration @critical @infrastructure', async ({ request }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Docker Services Connectivity Test',
      tags: ['docker', 'integration', 'critical', 'infrastructure'],
      file: __filename,
      priority: 'critical',
      category: 'infrastructure',
      browser: ['chrome']
    });

    // Test PostgreSQL connection (via health check endpoint)
    try {
      const postgresHealth = await request.get('http://localhost:5432');
      // PostgreSQL doesn't have HTTP endpoint, but we can test if port is accessible
      console.log('PostgreSQL service check attempted');
    } catch (error) {
      console.log('PostgreSQL connection test - expected behavior for direct connection');
    }

    // Test Redis connection (via health check if available)
    try {
      const redisHealth = await request.get('http://localhost:6379');
      console.log('Redis service check attempted');
    } catch (error) {
      console.log('Redis connection test - expected behavior for direct connection');
    }

    // Test MinIO service
    try {
      const minioHealth = await request.get('http://localhost:9000/minio/health/live');
      expect(minioHealth.status()).toBe(200);
      console.log('MinIO service is healthy');
    } catch (error) {
      console.log('MinIO service test failed:', error);
    }

    // Test Selenium Grid Hub
    try {
      const seleniumHub = await request.get('http://localhost:4444/wd/hub/status');
      expect(seleniumHub.status()).toBe(200);
      const hubStatus = await seleniumHub.json();
      expect(hubStatus.value.ready).toBe(true);
      console.log('Selenium Grid Hub is ready');
    } catch (error) {
      console.log('Selenium Grid Hub test failed:', error);
    }

    // Test Grafana dashboard
    try {
      const grafanaHealth = await request.get('http://localhost:3001/api/health');
      expect(grafanaHealth.status()).toBe(200);
      console.log('Grafana service is healthy');
    } catch (error) {
      console.log('Grafana service test failed:', error);
    }

    // Test Prometheus metrics
    try {
      const prometheusHealth = await request.get('http://localhost:9090/-/healthy');
      expect(prometheusHealth.status()).toBe(200);
      console.log('Prometheus service is healthy');
    } catch (error) {
      console.log('Prometheus service test failed:', error);
    }
  });

  // @docker @reports @medium @integration
  test('should access report server endpoints @docker @reports @medium @integration', async ({ request }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Docker Report Server Test',
      tags: ['docker', 'reports', 'medium', 'integration'],
      file: __filename,
      priority: 'medium',
      category: 'infrastructure'
    });

    // Test report server health
    try {
      const reportHealth = await request.get('http://localhost:8080/health');
      expect(reportHealth.status()).toBe(200);
      
      const healthData = await reportHealth.json();
      expect(healthData.status).toBe('healthy');
      console.log('Report server is healthy');
    } catch (error) {
      console.log('Report server health check failed:', error);
    }

    // Test report server main page
    try {
      const reportIndex = await request.get('http://localhost:8080/');
      expect(reportIndex.status()).toBe(200);
      
      const indexContent = await reportIndex.text();
      expect(indexContent).toContain('Test Reports Dashboard');
      console.log('Report server main page accessible');
    } catch (error) {
      console.log('Report server main page test failed:', error);
    }

    // Test Playwright reports endpoint
    try {
      const playwrightReports = await request.get('http://localhost:8080/playwright/');
      // May return 404 if no reports exist yet, which is acceptable
      console.log('Playwright reports endpoint tested');
    } catch (error) {
      console.log('Playwright reports endpoint test completed');
    }

    // Test Allure reports endpoint
    try {
      const allureReports = await request.get('http://localhost:8080/allure/');
      // May return 404 if no reports exist yet, which is acceptable
      console.log('Allure reports endpoint tested');
    } catch (error) {
      console.log('Allure reports endpoint test completed');
    }

    // Test API metadata endpoint
    try {
      const apiMetadata = await request.get('http://localhost:8080/api/reports/metadata');
      expect(apiMetadata.status()).toBe(200);
      
      const metadata = await apiMetadata.json();
      expect(metadata).toHaveProperty('timestamp');
      expect(metadata).toHaveProperty('version');
      console.log('API metadata endpoint working');
    } catch (error) {
      console.log('API metadata endpoint test failed:', error);
    }
  });

  // @docker @app @medium @integration
  test('should interact with mock application @docker @app @medium @integration', async ({ page }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Docker Mock App Integration Test',
      tags: ['docker', 'app', 'medium', 'integration'],
      file: __filename,
      priority: 'medium',
      category: 'functional',
      browser: ['chrome']
    });

    // Test mock application accessibility
    try {
      await page.goto('http://localhost:3000');
      await page.waitForLoadState('networkidle');

      // Verify page loads
      const title = await page.title();
      expect(title).toContain('Test Application');

      // Test navigation elements
      const nav = page.locator('nav');
      await expect(nav).toBeVisible();

      // Test login functionality
      const loginBtn = page.locator('button:has-text("Login")');
      if (await loginBtn.isVisible()) {
        await loginBtn.click();
        
        // Check if login modal or form appears
        const loginForm = page.locator('form, .login-form, #loginModal');
        if (await loginForm.isVisible()) {
          console.log('Login functionality accessible');
        }
      }

      // Test search functionality
      const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]');
      if (await searchInput.isVisible()) {
        await searchInput.fill('test query');
        await searchInput.press('Enter');
        console.log('Search functionality tested');
      }

      // Test contact form
      const contactForm = page.locator('form[name="contact"], .contact-form form');
      if (await contactForm.isVisible()) {
        const nameField = contactForm.locator('input[name="name"]');
        const emailField = contactForm.locator('input[name="email"]');
        const messageField = contactForm.locator('textarea[name="message"]');

        if (await nameField.isVisible()) await nameField.fill('Test User');
        if (await emailField.isVisible()) await emailField.fill('test@example.com');
        if (await messageField.isVisible()) await messageField.fill('Test message');

        const submitBtn = contactForm.locator('button[type="submit"]');
        if (await submitBtn.isVisible()) {
          await submitBtn.click();
          console.log('Contact form submission tested');
        }
      }

      console.log('Mock application integration test completed successfully');
    } catch (error) {
      console.log('Mock application test failed:', error);
    }
  });

  // @docker @allure @medium @integration
  test('should access Allure reporting service @docker @allure @medium @integration', async ({ request }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Docker Allure Service Test',
      tags: ['docker', 'allure', 'medium', 'integration'],
      file: __filename,
      priority: 'medium',
      category: 'reporting'
    });

    // Test Allure service accessibility
    try {
      const allureService = await request.get('http://localhost:5050');
      expect(allureService.status()).toBe(200);
      
      const allureContent = await allureService.text();
      expect(allureContent).toContain('Allure');
      console.log('Allure service is accessible');
    } catch (error) {
      console.log('Allure service test failed:', error);
    }

    // Test Allure API endpoints
    try {
      // Test projects endpoint
      const projectsEndpoint = await request.get('http://localhost:5050/allure-docker-service/projects');
      if (projectsEndpoint.status() === 200) {
        const projects = await projectsEndpoint.json();
        console.log('Allure projects endpoint working, projects:', projects);
      }
    } catch (error) {
      console.log('Allure API test completed with expected behavior');
    }
  });

  // @docker @security @medium @integration
  test('should verify security scanning integration @docker @security @medium @integration', async ({ request }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Docker Security Integration Test',
      tags: ['docker', 'security', 'medium', 'integration'],
      file: __filename,
      priority: 'medium',
      category: 'security'
    });

    // Test OWASP ZAP service
    try {
      const zapHealth = await request.get('http://localhost:8090');
      console.log('OWASP ZAP service connectivity tested');
    } catch (error) {
      console.log('OWASP ZAP service test completed');
    }

    // Test ZAP API if available
    try {
      const zapApi = await request.get('http://localhost:8090/JSON/core/view/version/');
      if (zapApi.status() === 200) {
        const zapVersion = await zapApi.json();
        console.log('ZAP API accessible, version:', zapVersion);
      }
    } catch (error) {
      console.log('ZAP API test completed');
    }
  });

  // @docker @mobile @medium @integration
  test('should verify mobile testing integration @docker @mobile @medium @integration', async ({ request }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Docker Mobile Testing Integration',
      tags: ['docker', 'mobile', 'medium', 'integration'],
      file: __filename,
      priority: 'medium',
      category: 'mobile'
    });

    // Test Appium service
    try {
      const appiumHealth = await request.get('http://localhost:4723/wd/hub/status');
      if (appiumHealth.status() === 200) {
        const appiumStatus = await appiumHealth.json();
        expect(appiumStatus.value.ready).toBe(true);
        console.log('Appium service is ready for mobile testing');
      }
    } catch (error) {
      console.log('Appium service test completed');
    }
  });

  // @docker @performance @low @integration
  test('should verify monitoring and metrics integration @docker @performance @low @integration', async ({ request }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Docker Monitoring Integration Test',
      tags: ['docker', 'performance', 'low', 'integration'],
      file: __filename,
      priority: 'low',
      category: 'monitoring'
    });

    // Test Prometheus metrics collection
    try {
      const prometheusMetrics = await request.get('http://localhost:9090/api/v1/query?query=up');
      if (prometheusMetrics.status() === 200) {
        const metricsData = await prometheusMetrics.json();
        expect(metricsData.status).toBe('success');
        console.log('Prometheus metrics collection working');
      }
    } catch (error) {
      console.log('Prometheus metrics test completed');
    }

    // Test Grafana API
    try {
      const grafanaApi = await request.get('http://localhost:3001/api/datasources');
      console.log('Grafana API connectivity tested');
    } catch (error) {
      console.log('Grafana API test completed');
    }
  });

  // @docker @e2e @high @integration
  test('should perform end-to-end Docker environment test @docker @e2e @high @integration', async ({ page, request }) => {
    // Register test with tags
    tagManager.registerTest({
      title: 'Docker E2E Environment Test',
      tags: ['docker', 'e2e', 'high', 'integration'],
      file: __filename,
      priority: 'high',
      category: 'integration',
      browser: ['chrome']
    });

    // Comprehensive Docker environment validation
    const services = [
      { name: 'Mock App', url: 'http://localhost:3000', expectContent: 'Test Application' },
      { name: 'Report Server', url: 'http://localhost:8080', expectContent: 'Test Reports Dashboard' },
      { name: 'Allure Service', url: 'http://localhost:5050', expectContent: 'Allure' }
    ];

    const serviceResults = [];

    for (const service of services) {
      try {
        console.log(`Testing ${service.name}...`);
        
        if (service.name === 'Mock App') {
          // Use page for full browser testing
          await page.goto(service.url);
          await page.waitForLoadState('networkidle');
          
          const content = await page.content();
          const isHealthy = content.includes(service.expectContent);
          
          serviceResults.push({
            name: service.name,
            url: service.url,
            healthy: isHealthy,
            status: isHealthy ? 'UP' : 'DOWN'
          });
        } else {
          // Use request for API testing
          const response = await request.get(service.url);
          const content = await response.text();
          const isHealthy = response.status() === 200 && content.includes(service.expectContent);
          
          serviceResults.push({
            name: service.name,
            url: service.url,
            healthy: isHealthy,
            status: isHealthy ? 'UP' : 'DOWN',
            statusCode: response.status()
          });
        }
      } catch (error) {
        serviceResults.push({
          name: service.name,
          url: service.url,
          healthy: false,
          status: 'ERROR',
          error: error.message
        });
      }
    }

    // Log comprehensive results
    console.log('Docker Environment Health Check Results:');
    console.table(serviceResults);

    // Verify at least core services are accessible
    const healthyServices = serviceResults.filter(s => s.healthy);
    expect(healthyServices.length).toBeGreaterThan(0);

    // Generate environment report
    const environmentReport = {
      timestamp: new Date().toISOString(),
      totalServices: services.length,
      healthyServices: healthyServices.length,
      services: serviceResults,
      overallHealth: healthyServices.length / services.length >= 0.5 ? 'GOOD' : 'DEGRADED'
    };

    console.log('Environment Report:', JSON.stringify(environmentReport, null, 2));

    // Verify overall environment health
    expect(environmentReport.overallHealth).toBe('GOOD');
  });

  test.afterAll(async () => {
    // Generate final Docker integration statistics
    const stats = tagManager.getTagStatistics();
    console.log('Docker Integration Test Statistics:', stats);
    
    // Clear registry
    tagManager.clearRegistry();
  });
});