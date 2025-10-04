# Multi-stage Dockerfile for Playwright Test Automation Framework
# Supports both development and production environments

# Stage 1: Base image with Node.js and system dependencies
FROM node:18-bullseye-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies required for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r playwright && useradd -r -g playwright -G audio,video playwright \
    && mkdir -p /home/playwright/Downloads \
    && chown -R playwright:playwright /home/playwright \
    && chown -R playwright:playwright /app

# Stage 2: Dependencies installation
FROM base AS dependencies

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install Node.js dependencies
RUN npm ci --only=production && npm cache clean --force

# Install Playwright browsers and dependencies
RUN npx playwright install --with-deps

# Stage 3: Development environment
FROM dependencies AS development

# Install development dependencies
RUN npm ci && npm cache clean --force

# Copy source code
COPY --chown=playwright:playwright . .

# Switch to non-root user
USER playwright

# Expose port for development server (if needed)
EXPOSE 3000 9323

# Default command for development
CMD ["npm", "run", "test"]

# Stage 4: Production/CI environment
FROM dependencies AS production

# Copy source code and build artifacts
COPY --chown=playwright:playwright . .

# Build the project (if needed)
RUN npm run build 2>/dev/null || echo "No build script found"

# Switch to non-root user
USER playwright

# Create directories for reports and artifacts
RUN mkdir -p /app/test-results /app/playwright-report /app/allure-results /app/allure-report

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node --version || exit 1

# Default command for production
CMD ["npm", "run", "test:ci"]

# Stage 5: CI/CD optimized image
FROM production AS ci

# Install additional CI tools
USER root
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Allure CLI for report generation
RUN curl -o allure-2.24.0.tgz -Ls https://github.com/allure-framework/allure2/releases/download/2.24.0/allure-2.24.0.tgz \
    && tar -zxf allure-2.24.0.tgz -C /opt/ \
    && ln -s /opt/allure-2.24.0/bin/allure /usr/bin/allure \
    && rm allure-2.24.0.tgz

# Switch back to non-root user
USER playwright

# Set environment variables for CI
ENV CI=true
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV NODE_ENV=test

# Default command for CI
CMD ["npm", "run", "test:ci"]

# Stage 6: Report server (for serving test reports)
FROM nginx:alpine AS report-server

# Copy custom nginx configuration
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Copy reports from production stage
COPY --from=production /app/playwright-report /usr/share/nginx/html/playwright
COPY --from=production /app/allure-report /usr/share/nginx/html/allure

# Create index page for reports
RUN echo '<!DOCTYPE html>\
<html>\
<head>\
    <title>Test Reports</title>\
    <style>\
        body { font-family: Arial, sans-serif; margin: 40px; }\
        .container { max-width: 800px; margin: 0 auto; }\
        .report-link { display: block; padding: 20px; margin: 10px 0; background: #f5f5f5; text-decoration: none; color: #333; border-radius: 5px; }\
        .report-link:hover { background: #e5e5e5; }\
        h1 { color: #333; text-align: center; }\
    </style>\
</head>\
<body>\
    <div class="container">\
        <h1>🎭 Playwright Test Reports</h1>\
        <a href="/playwright/" class="report-link">\
            <h3>📊 Playwright HTML Report</h3>\
            <p>Standard Playwright test execution report with detailed test results</p>\
        </a>\
        <a href="/allure/" class="report-link">\
            <h3>📈 Allure Report</h3>\
            <p>Enhanced test report with trends, history, and detailed analytics</p>\
        </a>\
    </div>\
</body>\
</html>' > /usr/share/nginx/html/index.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]