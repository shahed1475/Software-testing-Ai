import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import { Logger } from './Logger';

export interface User {
  username: string;
  password: string;
  firstName: string;
  lastName: string;
  role: string;
}

export interface Product {
  name: string;
  price: number;
  category: string;
  description: string;
  inStock: boolean;
  sku: string;
}

export interface FormData {
  [key: string]: string | boolean | number;
}

export interface ApiConfig {
  endpoints: { [key: string]: string };
  headers: { [key: string]: string };
}

export interface TestData {
  users: { [key: string]: User };
  products: { [key: string]: Product };
  forms: { [key: string]: FormData };
  api: ApiConfig;
  search: {
    validQueries: string[];
    invalidQueries: string[];
  };
  navigation: {
    mainMenuItems: string[];
    footerLinks: string[];
  };
  timeouts: { [key: string]: number };
  urls: { [key: string]: string };
  environments?: { [key: string]: any };
  tags?: { [key: string]: string[] };
}

/**
 * TestDataLoader - Utility class for loading and managing test data
 * Supports both JSON and YAML formats with caching and validation
 */
export class TestDataLoader {
  private static instance: TestDataLoader;
  private testData: TestData | null = null;
  private logger: Logger;
  private dataPath: string;

  private constructor() {
    this.logger = Logger.getInstance();
    this.dataPath = path.join(process.cwd(), 'src', 'data');
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): TestDataLoader {
    if (!TestDataLoader.instance) {
      TestDataLoader.instance = new TestDataLoader();
    }
    return TestDataLoader.instance;
  }

  /**
   * Load test data from JSON file
   */
  public loadFromJson(filename: string = 'test-data.json'): TestData {
    try {
      const filePath = path.join(this.dataPath, filename);
      
      if (!fs.existsSync(filePath)) {
        throw new Error(`Test data file not found: ${filePath}`);
      }

      const fileContent = fs.readFileSync(filePath, 'utf-8');
      const data = JSON.parse(fileContent);
      
      this.validateTestData(data);
      this.testData = data;
      
      this.logger.info(`Test data loaded successfully from ${filename}`);
      return this.testData;
    } catch (error) {
      this.logger.error(`Failed to load test data from JSON: ${error}`);
      throw error;
    }
  }

  /**
   * Load test data from YAML file
   */
  public loadFromYaml(filename: string = 'test-data.yaml'): TestData {
    try {
      const filePath = path.join(this.dataPath, filename);
      
      if (!fs.existsSync(filePath)) {
        throw new Error(`Test data file not found: ${filePath}`);
      }

      const fileContent = fs.readFileSync(filePath, 'utf-8');
      const data = yaml.parse(fileContent);
      
      this.validateTestData(data);
      this.testData = data;
      
      this.logger.info(`Test data loaded successfully from ${filename}`);
      return this.testData;
    } catch (error) {
      this.logger.error(`Failed to load test data from YAML: ${error}`);
      throw error;
    }
  }

  /**
   * Get all test data
   */
  public getTestData(): TestData {
    if (!this.testData) {
      // Try to load from JSON first, then YAML
      try {
        return this.loadFromJson();
      } catch {
        return this.loadFromYaml();
      }
    }
    return this.testData;
  }

  /**
   * Get user data by key
   */
  public getUser(userKey: string): User {
    const data = this.getTestData();
    const user = data.users[userKey];
    
    if (!user) {
      throw new Error(`User '${userKey}' not found in test data`);
    }
    
    return user;
  }

  /**
   * Get product data by key
   */
  public getProduct(productKey: string): Product {
    const data = this.getTestData();
    const product = data.products[productKey];
    
    if (!product) {
      throw new Error(`Product '${productKey}' not found in test data`);
    }
    
    return product;
  }

  /**
   * Get form data by key
   */
  public getFormData(formKey: string): FormData {
    const data = this.getTestData();
    const form = data.forms[formKey];
    
    if (!form) {
      throw new Error(`Form '${formKey}' not found in test data`);
    }
    
    return form;
  }

  /**
   * Get API configuration
   */
  public getApiConfig(): ApiConfig {
    const data = this.getTestData();
    return data.api;
  }

  /**
   * Get API endpoint by key
   */
  public getApiEndpoint(endpointKey: string): string {
    const apiConfig = this.getApiConfig();
    const endpoint = apiConfig.endpoints[endpointKey];
    
    if (!endpoint) {
      throw new Error(`API endpoint '${endpointKey}' not found in test data`);
    }
    
    return endpoint;
  }

  /**
   * Get search queries
   */
  public getSearchQueries(): { valid: string[]; invalid: string[] } {
    const data = this.getTestData();
    return {
      valid: data.search.validQueries,
      invalid: data.search.invalidQueries
    };
  }

  /**
   * Get navigation items
   */
  public getNavigationItems(): { main: string[]; footer: string[] } {
    const data = this.getTestData();
    return {
      main: data.navigation.mainMenuItems,
      footer: data.navigation.footerLinks
    };
  }

  /**
   * Get timeout value by key
   */
  public getTimeout(timeoutKey: string): number {
    const data = this.getTestData();
    const timeout = data.timeouts[timeoutKey];
    
    if (timeout === undefined) {
      throw new Error(`Timeout '${timeoutKey}' not found in test data`);
    }
    
    return timeout;
  }

  /**
   * Get URL by key
   */
  public getUrl(urlKey: string): string {
    const data = this.getTestData();
    const url = data.urls[urlKey];
    
    if (!url) {
      throw new Error(`URL '${urlKey}' not found in test data`);
    }
    
    return url;
  }

  /**
   * Get environment configuration
   */
  public getEnvironmentConfig(env: string): any {
    const data = this.getTestData();
    
    if (!data.environments) {
      throw new Error('Environment configurations not found in test data');
    }
    
    const envConfig = data.environments[env];
    
    if (!envConfig) {
      throw new Error(`Environment '${env}' not found in test data`);
    }
    
    return envConfig;
  }

  /**
   * Get tags by category
   */
  public getTags(category: string): string[] {
    const data = this.getTestData();
    
    if (!data.tags) {
      throw new Error('Tags not found in test data');
    }
    
    const tags = data.tags[category];
    
    if (!tags) {
      throw new Error(`Tag category '${category}' not found in test data`);
    }
    
    return tags;
  }

  /**
   * Validate test data structure
   */
  private validateTestData(data: any): void {
    const requiredFields = ['users', 'products', 'forms', 'api', 'search', 'navigation', 'timeouts', 'urls'];
    
    for (const field of requiredFields) {
      if (!data[field]) {
        throw new Error(`Required field '${field}' is missing from test data`);
      }
    }

    // Validate users structure
    if (!data.users || typeof data.users !== 'object') {
      throw new Error('Invalid users structure in test data');
    }

    // Validate products structure
    if (!data.products || typeof data.products !== 'object') {
      throw new Error('Invalid products structure in test data');
    }

    // Validate API structure
    if (!data.api.endpoints || !data.api.headers) {
      throw new Error('Invalid API structure in test data');
    }

    this.logger.info('Test data validation passed');
  }

  /**
   * Reload test data (clears cache)
   */
  public reload(): void {
    this.testData = null;
    this.logger.info('Test data cache cleared');
  }

  /**
   * Get random user
   */
  public getRandomUser(): User {
    const data = this.getTestData();
    const userKeys = Object.keys(data.users);
    const randomKey = userKeys[Math.floor(Math.random() * userKeys.length)];
    return this.getUser(randomKey);
  }

  /**
   * Get random product
   */
  public getRandomProduct(): Product {
    const data = this.getTestData();
    const productKeys = Object.keys(data.products);
    const randomKey = productKeys[Math.floor(Math.random() * productKeys.length)];
    return this.getProduct(randomKey);
  }

  /**
   * Get users by role
   */
  public getUsersByRole(role: string): User[] {
    const data = this.getTestData();
    return Object.values(data.users).filter(user => user.role === role);
  }

  /**
   * Get products by category
   */
  public getProductsByCategory(category: string): Product[] {
    const data = this.getTestData();
    return Object.values(data.products).filter(product => product.category === category);
  }

  /**
   * Get in-stock products
   */
  public getInStockProducts(): Product[] {
    const data = this.getTestData();
    return Object.values(data.products).filter(product => product.inStock);
  }

  /**
   * Get out-of-stock products
   */
  public getOutOfStockProducts(): Product[] {
    const data = this.getTestData();
    return Object.values(data.products).filter(product => !product.inStock);
  }
}