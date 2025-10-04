import { test as base, TestInfo } from '@playwright/test';
import { Logger } from './Logger';
import { ConfigManager } from './ConfigManager';

export type TestTag = 
  | 'smoke' 
  | 'regression' 
  | 'api' 
  | 'ui' 
  | 'e2e' 
  | 'integration' 
  | 'unit'
  | 'critical' 
  | 'high' 
  | 'medium' 
  | 'low'
  | 'auth' 
  | 'dashboard' 
  | 'login' 
  | 'search' 
  | 'checkout'
  | 'mobile' 
  | 'desktop' 
  | 'tablet'
  | 'chrome' 
  | 'firefox' 
  | 'safari' 
  | 'edge'
  | 'performance' 
  | 'security' 
  | 'accessibility'
  | 'flaky' 
  | 'skip' 
  | 'wip';

export interface TaggedTest {
  title: string;
  tags: TestTag[];
  file: string;
  project?: string;
  priority?: 'critical' | 'high' | 'medium' | 'low';
  category?: 'functional' | 'non-functional' | 'integration' | 'unit';
  browser?: string[];
  environment?: string[];
}

export interface TagFilter {
  include?: TestTag[];
  exclude?: TestTag[];
  priority?: ('critical' | 'high' | 'medium' | 'low')[];
  category?: ('functional' | 'non-functional' | 'integration' | 'unit')[];
  browser?: string[];
  environment?: string[];
}

/**
 * TagManager - Manages test tags and filtering for organized test execution
 * Supports tagging tests with categories, priorities, and execution contexts
 */
export class TagManager {
  private static instance: TagManager;
  private logger: Logger;
  private config: ConfigManager;
  private taggedTests: Map<string, TaggedTest> = new Map();

  // Predefined tag groups for easy filtering
  public static readonly TAG_GROUPS = {
    SMOKE: ['smoke', 'critical'] as TestTag[],
    REGRESSION: ['regression', 'high', 'medium'] as TestTag[],
    API: ['api', 'integration'] as TestTag[],
    UI: ['ui', 'e2e'] as TestTag[],
    AUTH: ['auth', 'login'] as TestTag[],
    PERFORMANCE: ['performance'] as TestTag[],
    SECURITY: ['security'] as TestTag[],
    ACCESSIBILITY: ['accessibility'] as TestTag[],
    MOBILE: ['mobile'] as TestTag[],
    DESKTOP: ['desktop'] as TestTag[],
    CRITICAL: ['critical', 'smoke'] as TestTag[],
    HIGH_PRIORITY: ['critical', 'high'] as TestTag[],
    FLAKY: ['flaky'] as TestTag[]
  };

  private constructor() {
    this.logger = Logger.getInstance();
    this.config = ConfigManager.getInstance();
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): TagManager {
    if (!TagManager.instance) {
      TagManager.instance = new TagManager();
    }
    return TagManager.instance;
  }

  /**
   * Register a tagged test
   */
  public registerTest(testInfo: TestInfo, tags: TestTag[], options?: {
    priority?: 'critical' | 'high' | 'medium' | 'low';
    category?: 'functional' | 'non-functional' | 'integration' | 'unit';
    browser?: string[];
    environment?: string[];
  }): void {
    const testKey = `${testInfo.file}:${testInfo.title}`;
    
    const taggedTest: TaggedTest = {
      title: testInfo.title,
      tags: tags,
      file: testInfo.file,
      project: testInfo.project?.name,
      priority: options?.priority,
      category: options?.category,
      browser: options?.browser,
      environment: options?.environment
    };

    this.taggedTests.set(testKey, taggedTest);
    this.logger.debug(`Registered test with tags: ${testInfo.title} [${tags.join(', ')}]`);
  }

  /**
   * Get tests by tag filter
   */
  public getTestsByFilter(filter: TagFilter): TaggedTest[] {
    const tests = Array.from(this.taggedTests.values());
    
    return tests.filter(test => {
      // Include filter - test must have at least one of the included tags
      if (filter.include && filter.include.length > 0) {
        const hasIncludedTag = filter.include.some(tag => test.tags.includes(tag));
        if (!hasIncludedTag) return false;
      }

      // Exclude filter - test must not have any of the excluded tags
      if (filter.exclude && filter.exclude.length > 0) {
        const hasExcludedTag = filter.exclude.some(tag => test.tags.includes(tag));
        if (hasExcludedTag) return false;
      }

      // Priority filter
      if (filter.priority && filter.priority.length > 0 && test.priority) {
        if (!filter.priority.includes(test.priority)) return false;
      }

      // Category filter
      if (filter.category && filter.category.length > 0 && test.category) {
        if (!filter.category.includes(test.category)) return false;
      }

      // Browser filter
      if (filter.browser && filter.browser.length > 0 && test.browser) {
        const hasBrowser = filter.browser.some(browser => test.browser!.includes(browser));
        if (!hasBrowser) return false;
      }

      // Environment filter
      if (filter.environment && filter.environment.length > 0 && test.environment) {
        const hasEnvironment = filter.environment.some(env => test.environment!.includes(env));
        if (!hasEnvironment) return false;
      }

      return true;
    });
  }

  /**
   * Get tests by tag group
   */
  public getTestsByGroup(groupName: keyof typeof TagManager.TAG_GROUPS): TaggedTest[] {
    const tags = TagManager.TAG_GROUPS[groupName];
    return this.getTestsByFilter({ include: tags });
  }

  /**
   * Get all registered tests
   */
  public getAllTests(): TaggedTest[] {
    return Array.from(this.taggedTests.values());
  }

  /**
   * Get test statistics by tags
   */
  public getTagStatistics(): Record<TestTag, number> {
    const stats: Record<string, number> = {};
    
    this.taggedTests.forEach(test => {
      test.tags.forEach(tag => {
        stats[tag] = (stats[tag] || 0) + 1;
      });
    });

    return stats as Record<TestTag, number>;
  }

  /**
   * Generate grep pattern for Playwright CLI
   */
  public generateGrepPattern(filter: TagFilter): string {
    const patterns: string[] = [];

    // Include patterns
    if (filter.include && filter.include.length > 0) {
      const includePattern = filter.include.map(tag => `@${tag}`).join('|');
      patterns.push(`(${includePattern})`);
    }

    // Exclude patterns
    if (filter.exclude && filter.exclude.length > 0) {
      const excludePattern = filter.exclude.map(tag => `@${tag}`).join('|');
      patterns.push(`^(?!.*(${excludePattern}))`);
    }

    return patterns.length > 0 ? patterns.join('.*') : '.*';
  }

  /**
   * Validate test tags
   */
  public validateTags(tags: string[]): { valid: TestTag[]; invalid: string[] } {
    const validTags: TestTag[] = [];
    const invalidTags: string[] = [];

    const allValidTags = [
      'smoke', 'regression', 'api', 'ui', 'e2e', 'integration', 'unit',
      'critical', 'high', 'medium', 'low',
      'auth', 'dashboard', 'login', 'search', 'checkout',
      'mobile', 'desktop', 'tablet',
      'chrome', 'firefox', 'safari', 'edge',
      'performance', 'security', 'accessibility',
      'flaky', 'skip', 'wip'
    ];

    tags.forEach(tag => {
      if (allValidTags.includes(tag as TestTag)) {
        validTags.push(tag as TestTag);
      } else {
        invalidTags.push(tag);
      }
    });

    return { valid: validTags, invalid: invalidTags };
  }

  /**
   * Get recommended tags based on test file path and title
   */
  public getRecommendedTags(filePath: string, testTitle: string): TestTag[] {
    const recommendations: TestTag[] = [];
    const lowerPath = filePath.toLowerCase();
    const lowerTitle = testTitle.toLowerCase();

    // File path based recommendations
    if (lowerPath.includes('/auth/') || lowerPath.includes('login')) {
      recommendations.push('auth', 'login');
    }
    if (lowerPath.includes('/api/')) {
      recommendations.push('api', 'integration');
    }
    if (lowerPath.includes('/ui/') || lowerPath.includes('/e2e/')) {
      recommendations.push('ui', 'e2e');
    }
    if (lowerPath.includes('/smoke/')) {
      recommendations.push('smoke', 'critical');
    }
    if (lowerPath.includes('/regression/')) {
      recommendations.push('regression');
    }
    if (lowerPath.includes('/performance/')) {
      recommendations.push('performance');
    }
    if (lowerPath.includes('/security/')) {
      recommendations.push('security');
    }
    if (lowerPath.includes('/accessibility/')) {
      recommendations.push('accessibility');
    }

    // Test title based recommendations
    if (lowerTitle.includes('login') || lowerTitle.includes('auth')) {
      recommendations.push('auth', 'login');
    }
    if (lowerTitle.includes('dashboard')) {
      recommendations.push('dashboard');
    }
    if (lowerTitle.includes('search')) {
      recommendations.push('search');
    }
    if (lowerTitle.includes('checkout') || lowerTitle.includes('payment')) {
      recommendations.push('checkout');
    }
    if (lowerTitle.includes('mobile')) {
      recommendations.push('mobile');
    }
    if (lowerTitle.includes('desktop')) {
      recommendations.push('desktop');
    }

    // Priority based on keywords
    if (lowerTitle.includes('critical') || lowerTitle.includes('smoke')) {
      recommendations.push('critical', 'smoke');
    } else if (lowerTitle.includes('important') || lowerTitle.includes('main')) {
      recommendations.push('high');
    } else {
      recommendations.push('medium');
    }

    // Remove duplicates
    return [...new Set(recommendations)];
  }

  /**
   * Clear all registered tests
   */
  public clearTests(): void {
    this.taggedTests.clear();
    this.logger.debug('Cleared all registered tests');
  }

  /**
   * Export test registry to JSON
   */
  public exportToJSON(): string {
    const data = {
      tests: Array.from(this.taggedTests.values()),
      statistics: this.getTagStatistics(),
      exportedAt: new Date().toISOString()
    };
    return JSON.stringify(data, null, 2);
  }

  /**
   * Import test registry from JSON
   */
  public importFromJSON(jsonData: string): void {
    try {
      const data = JSON.parse(jsonData);
      this.taggedTests.clear();
      
      if (data.tests && Array.isArray(data.tests)) {
        data.tests.forEach((test: TaggedTest) => {
          const testKey = `${test.file}:${test.title}`;
          this.taggedTests.set(testKey, test);
        });
      }
      
      this.logger.info(`Imported ${this.taggedTests.size} tagged tests`);
    } catch (error) {
      this.logger.error(`Failed to import test registry: ${error}`);
      throw error;
    }
  }
}

/**
 * Tagged test decorator for easy test tagging
 */
export function tagged(tags: TestTag[], options?: {
  priority?: 'critical' | 'high' | 'medium' | 'low';
  category?: 'functional' | 'non-functional' | 'integration' | 'unit';
  browser?: string[];
  environment?: string[];
}) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    
    descriptor.value = function(testInfo: TestInfo, ...args: any[]) {
      const tagManager = TagManager.getInstance();
      tagManager.registerTest(testInfo, tags, options);
      return originalMethod.apply(this, [testInfo, ...args]);
    };
    
    return descriptor;
  };
}

/**
 * Extended test with tagging support
 */
export const test = base.extend<{
  tagManager: TagManager;
}>({
  tagManager: async ({}, use) => {
    const tagManager = TagManager.getInstance();
    await use(tagManager);
  }
});

/**
 * Helper functions for common tag combinations
 */
export const TestTags = {
  smoke: (priority: 'critical' | 'high' = 'critical') => 
    ['smoke', priority] as TestTag[],
  
  regression: (priority: 'high' | 'medium' | 'low' = 'medium') => 
    ['regression', priority] as TestTag[],
  
  api: (priority: 'high' | 'medium' | 'low' = 'medium') => 
    ['api', 'integration', priority] as TestTag[],
  
  ui: (priority: 'high' | 'medium' | 'low' = 'medium') => 
    ['ui', 'e2e', priority] as TestTag[],
  
  auth: (priority: 'critical' | 'high' = 'critical') => 
    ['auth', 'login', priority] as TestTag[],
  
  performance: () => 
    ['performance', 'high'] as TestTag[],
  
  security: () => 
    ['security', 'high'] as TestTag[],
  
  accessibility: () => 
    ['accessibility', 'medium'] as TestTag[],
  
  mobile: (priority: 'high' | 'medium' | 'low' = 'medium') => 
    ['mobile', 'ui', priority] as TestTag[],
  
  flaky: () => 
    ['flaky', 'low'] as TestTag[]
};