-- Initialize Testing AI Database Schema

-- Create database if not exists (handled by docker-compose)
-- CREATE DATABASE IF NOT EXISTS testing_ai;

-- Use the database
-- \c testing_ai;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create enum types
CREATE TYPE test_status AS ENUM ('pending', 'running', 'passed', 'failed', 'skipped', 'error');
CREATE TYPE test_type AS ENUM ('web', 'mobile', 'api', 'security', 'unit', 'integration', 'e2e');
CREATE TYPE environment_type AS ENUM ('development', 'staging', 'production', 'testing');

-- Create test_runs table
CREATE TABLE test_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_name VARCHAR(255) NOT NULL,
    test_type test_type NOT NULL,
    environment environment_type DEFAULT 'testing',
    status test_status DEFAULT 'pending',
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    skipped_tests INTEGER DEFAULT 0,
    error_tests INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    branch_name VARCHAR(255),
    commit_hash VARCHAR(40),
    triggered_by VARCHAR(255),
    configuration JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create test_cases table
CREATE TABLE test_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    test_name VARCHAR(500) NOT NULL,
    test_file VARCHAR(500),
    test_class VARCHAR(255),
    test_method VARCHAR(255),
    status test_status NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds DECIMAL(10,3),
    error_message TEXT,
    stack_trace TEXT,
    screenshot_path VARCHAR(500),
    video_path VARCHAR(500),
    logs TEXT,
    tags TEXT[],
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create test_artifacts table
CREATE TABLE test_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    test_case_id UUID REFERENCES test_cases(id) ON DELETE CASCADE,
    artifact_type VARCHAR(50) NOT NULL, -- 'screenshot', 'video', 'log', 'report', 'trace'
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    storage_location VARCHAR(500), -- S3, MinIO, local path
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create test_environments table
CREATE TABLE test_environments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    type environment_type NOT NULL,
    base_url VARCHAR(500),
    database_url VARCHAR(500),
    api_endpoints JSONB,
    browser_config JSONB,
    mobile_config JSONB,
    credentials JSONB, -- encrypted
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create test_reports table
CREATE TABLE test_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL, -- 'html', 'pdf', 'json', 'xml'
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes for better performance
CREATE INDEX idx_test_runs_status ON test_runs(status);
CREATE INDEX idx_test_runs_type ON test_runs(test_type);
CREATE INDEX idx_test_runs_start_time ON test_runs(start_time);
CREATE INDEX idx_test_runs_environment ON test_runs(environment);
CREATE INDEX idx_test_runs_branch ON test_runs(branch_name);

CREATE INDEX idx_test_cases_run_id ON test_cases(test_run_id);
CREATE INDEX idx_test_cases_status ON test_cases(status);
CREATE INDEX idx_test_cases_name ON test_cases(test_name);
CREATE INDEX idx_test_cases_start_time ON test_cases(start_time);

CREATE INDEX idx_test_artifacts_run_id ON test_artifacts(test_run_id);
CREATE INDEX idx_test_artifacts_case_id ON test_artifacts(test_case_id);
CREATE INDEX idx_test_artifacts_type ON test_artifacts(artifact_type);

CREATE INDEX idx_test_environments_type ON test_environments(type);
CREATE INDEX idx_test_environments_active ON test_environments(is_active);

CREATE INDEX idx_test_reports_run_id ON test_reports(test_run_id);
CREATE INDEX idx_test_reports_type ON test_reports(report_type);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_test_runs_updated_at BEFORE UPDATE ON test_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_environments_updated_at BEFORE UPDATE ON test_environments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default test environments
INSERT INTO test_environments (name, type, base_url, is_active) VALUES
('Local Development', 'development', 'http://localhost:3000', true),
('Staging', 'staging', 'https://staging.example.com', true),
('Production', 'production', 'https://example.com', true);

-- Create views for reporting
CREATE VIEW test_run_summary AS
SELECT 
    tr.id,
    tr.run_name,
    tr.test_type,
    tr.environment,
    tr.status,
    tr.start_time,
    tr.end_time,
    tr.duration_seconds,
    tr.total_tests,
    tr.passed_tests,
    tr.failed_tests,
    tr.skipped_tests,
    tr.error_tests,
    tr.success_rate,
    tr.branch_name,
    tr.commit_hash,
    COUNT(tc.id) as actual_test_count,
    COUNT(CASE WHEN tc.status = 'passed' THEN 1 END) as actual_passed,
    COUNT(CASE WHEN tc.status = 'failed' THEN 1 END) as actual_failed,
    COUNT(CASE WHEN tc.status = 'skipped' THEN 1 END) as actual_skipped,
    COUNT(CASE WHEN tc.status = 'error' THEN 1 END) as actual_errors
FROM test_runs tr
LEFT JOIN test_cases tc ON tr.id = tc.test_run_id
GROUP BY tr.id, tr.run_name, tr.test_type, tr.environment, tr.status, 
         tr.start_time, tr.end_time, tr.duration_seconds, tr.total_tests,
         tr.passed_tests, tr.failed_tests, tr.skipped_tests, tr.error_tests,
         tr.success_rate, tr.branch_name, tr.commit_hash;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO testuser;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO testuser;