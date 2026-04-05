-- TSK-006 Persistent Learning Agent Ecosystem - PostgreSQL Database Initialization
-- Version: 1.0.0
-- Created: 2025-12-21
-- Compatible with PostgreSQL 12+

-- Create Database and User (uncomment and run as superuser if needed)
-- CREATE DATABASE tsk006;
-- CREATE USER tsk006_user WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE tsk006 TO tsk006_user;
-- ALTER USER tsk006_user CREATEDB;

-- Use the database
-- \c tsk006;

-- Create Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create Enum Types
CREATE TYPE session_status AS ENUM ('active', 'inactive', 'completed', 'error');
CREATE TYPE severity_level AS ENUM ('debug', 'info', 'warning', 'error', 'critical');
CREATE TYPE operation_type AS ENUM ('create', 'update', 'delete', 'query', 'store');

-- Agent Sessions Table
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_name VARCHAR(100) NOT NULL,
    context JSONB,
    system_prompt TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status session_status DEFAULT 'active',
    metadata JSONB
);

-- Performance Metrics Table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES agent_sessions (session_id) ON DELETE CASCADE,
    task_id VARCHAR(100),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    metric_unit VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Routing Decisions Table
CREATE TABLE IF NOT EXISTS routing_decisions (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES agent_sessions (session_id) ON DELETE CASCADE,
    task_context JSONB,
    selected_agent VARCHAR(100) NOT NULL,
    routing_strategy VARCHAR(50),
    confidence_score DOUBLE PRECISION,
    execution_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent Performance History Table
CREATE TABLE IF NOT EXISTS agent_performance_history (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(100),
    success BOOLEAN NOT NULL,
    execution_time_ms INTEGER,
    quality_score DOUBLE PRECISION,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Critic Evaluations Table
CREATE TABLE IF NOT EXISTS critic_evaluations (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES agent_sessions (session_id) ON DELETE CASCADE,
    evaluation_type VARCHAR(100) NOT NULL,
    criteria JSONB,
    scores JSONB,
    overall_score DOUBLE PRECISION,
    feedback TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- CKS Integration Logs Table
CREATE TABLE IF NOT EXISTS cks_integration_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES agent_sessions (session_id) ON DELETE SET NULL,
    operation_type operation_type NOT NULL,
    query TEXT,
    response_data JSONB,
    execution_time_ms INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System Configuration Table
CREATE TABLE IF NOT EXISTS system_configuration (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(50) DEFAULT 'string',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Sessions Table
CREATE TABLE IF NOT EXISTS user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    session_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP WITH TIME ZONE,
    total_interactions INTEGER DEFAULT 0,
    session_metadata JSONB
);

-- Agent Usage Statistics Table
CREATE TABLE IF NOT EXISTS agent_usage_stats (
    id BIGSERIAL PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL,
    stat_date DATE NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    avg_session_duration DOUBLE PRECISION DEFAULT 0,
    success_rate DOUBLE PRECISION DEFAULT 0,
    avg_quality_score DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (role_name, stat_date)
);

-- Error Logs Table
CREATE TABLE IF NOT EXISTS error_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES agent_sessions (session_id) ON DELETE SET NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    severity severity_level DEFAULT 'error',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT
);

-- Knowledge Patterns Table
CREATE TABLE IF NOT EXISTS knowledge_patterns (
    id BIGSERIAL PRIMARY KEY,
    pattern_name VARCHAR(200) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL,
    pattern_data JSONB NOT NULL,
    usage_count INTEGER DEFAULT 0,
    success_rate DOUBLE PRECISION DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System Health Metrics Table
CREATE TABLE IF NOT EXISTS system_health_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance Optimization
CREATE INDEX IF NOT EXISTS idx_agent_sessions_created_at ON agent_sessions (created_at);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_role_name ON agent_sessions (role_name);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_status ON agent_sessions (status);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_session_id ON performance_metrics (session_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics (timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_metric_name ON performance_metrics (metric_name);
CREATE INDEX IF NOT EXISTS idx_routing_decisions_session_id ON routing_decisions (session_id);
CREATE INDEX IF NOT EXISTS idx_routing_decisions_timestamp ON routing_decisions (timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_performance_history_agent_name ON agent_performance_history (agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_performance_history_timestamp ON agent_performance_history (timestamp);
CREATE INDEX IF NOT EXISTS idx_critic_evaluations_session_id ON critic_evaluations (session_id);
CREATE INDEX IF NOT EXISTS idx_cks_integration_logs_session_id ON cks_integration_logs (session_id);
CREATE INDEX IF NOT EXISTS idx_cks_integration_logs_timestamp ON cks_integration_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_cks_integration_logs_operation_type ON cks_integration_logs (operation_type);
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs (severity);
CREATE INDEX IF NOT EXISTS idx_error_logs_resolved ON error_logs (resolved);
CREATE INDEX IF NOT EXISTS idx_knowledge_patterns_pattern_type ON knowledge_patterns (pattern_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_patterns_usage_count ON knowledge_patterns (usage_count);
CREATE INDEX IF NOT EXISTS idx_agent_usage_stats_role_date ON agent_usage_stats (role_name, stat_date);

-- GIN Indexes for JSONB Columns
CREATE INDEX IF NOT EXISTS idx_agent_sessions_context_gin ON agent_sessions USING GIN (context);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_metadata_gin ON agent_sessions USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_routing_decisions_task_context_gin ON routing_decisions USING GIN (task_context);
CREATE INDEX IF NOT EXISTS idx_critic_evaluations_criteria_gin ON critic_evaluations USING GIN (criteria);
CREATE INDEX IF NOT EXISTS idx_critic_evaluations_scores_gin ON critic_evaluations USING GIN (scores);
CREATE INDEX IF NOT EXISTS idx_cks_integration_logs_response_data_gin ON cks_integration_logs USING GIN (response_data);
CREATE INDEX IF NOT EXISTS idx_knowledge_patterns_pattern_data_gin ON knowledge_patterns USING GIN (pattern_data);

-- Initialize System Configuration
INSERT INTO system_configuration (config_key, config_value, config_type, description) VALUES
('system_version', '1.0.0', 'string', 'TSK-006 system version'),
('max_concurrent_agents', '50', 'integer', 'Maximum number of concurrent agents'),
('default_session_timeout', '3600', 'integer', 'Default session timeout in seconds'),
('cks_integration_enabled', 'true', 'boolean', 'Whether CKS integration is enabled'),
('performance_tracking_enabled', 'true', 'boolean', 'Whether performance tracking is enabled'),
('critic_system_enabled', 'true', 'boolean', 'Whether critic system is enabled'),
('default_learning_rate', '0.1', 'float', 'Default learning rate for routing'),
('cache_ttl', '3600', 'integer', 'Default cache TTL in seconds'),
('log_level', 'INFO', 'string', 'Default log level'),
('security_mode', 'production', 'string', 'Security mode (development/staging/production)'),
('database_version', '1.0.0', 'string', 'Database schema version'),
('created_at', CURRENT_TIMESTAMP, 'timestamp', 'Database creation timestamp')
ON CONFLICT (config_key) DO NOTHING;

-- Create Functions for Automatic Timestamp Updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create Triggers
CREATE TRIGGER update_system_configuration_updated_at
    BEFORE UPDATE ON system_configuration
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create Views for Common Queries
CREATE OR REPLACE VIEW active_agent_sessions AS
SELECT
    session_id,
    role_name,
    created_at,
    last_activity,
    EXTRACT(EPOCH FROM (last_activity - created_at))/60 as session_duration_minutes
FROM agent_sessions
WHERE status = 'active'
AND last_activity > CURRENT_TIMESTAMP - INTERVAL '1 hour';

CREATE OR REPLACE VIEW daily_agent_stats AS
SELECT
    role_name,
    DATE(created_at) as session_date,
    COUNT(*) as total_sessions,
    AVG(EXTRACT(EPOCH FROM (last_activity - created_at))/60) as avg_duration_minutes,
    (COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*)) as completion_rate
FROM agent_sessions
GROUP BY role_name, DATE(created_at);

CREATE OR REPLACE VIEW system_performance_summary AS
SELECT
    'total_sessions' as metric,
    COUNT(*)::text as value
FROM agent_sessions
UNION ALL
SELECT
    'active_sessions' as metric,
    COUNT(*)::text as value
FROM agent_sessions
WHERE status = 'active'
UNION ALL
SELECT
    'avg_session_duration' as metric,
    ROUND(AVG(EXTRACT(EPOCH FROM (last_activity - created_at))/60), 2)::text as value
FROM agent_sessions
WHERE status IN ('completed', 'inactive')
UNION ALL
SELECT
    'total_errors' as metric,
    COUNT(*)::text as value
FROM error_logs
WHERE resolved = FALSE;

-- Create Stored Procedures for Common Operations
CREATE OR REPLACE FUNCTION update_agent_session_activity(p_session_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE agent_sessions
    SET last_activity = CURRENT_TIMESTAMP
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_agent_performance_summary(p_agent_name VARCHAR(100), p_days INTEGER DEFAULT 7)
RETURNS TABLE (
    total_tasks BIGINT,
    successful_tasks BIGINT,
    success_rate DOUBLE PRECISION,
    avg_execution_time DOUBLE PRECISION,
    avg_quality_score DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_tasks,
        COUNT(CASE WHEN success = TRUE THEN 1 END) as successful_tasks,
        (COUNT(CASE WHEN success = TRUE THEN 1 END) * 100.0 / COUNT(*)) as success_rate,
        AVG(execution_time_ms) as avg_execution_time,
        AVG(quality_score) as avg_quality_score
    FROM agent_performance_history
    WHERE agent_name = p_agent_name
    AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days;
END;
$$ LANGUAGE plpgsql;

-- Create Partitioned Tables for High Volume Data (Optional)
-- Uncomment for production environments with high data volume

-- Partition error_logs by month
-- CREATE TABLE error_logs_y2024m01 PARTITION OF error_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Partition performance_metrics by week
-- CREATE TABLE performance_metrics_y2024w01 PARTITION OF performance_metrics
--     FOR VALUES FROM ('2024-01-01') TO ('2024-01-08');

-- Grant Permissions
-- GRANT USAGE ON SCHEMA public TO tsk006_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tsk006_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tsk006_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO tsk006_user;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA public TO tsk006_user;

-- Database is now initialized and ready for use
SELECT 'PostgreSQL database initialized successfully for TSK-006 Agent Ecosystem' as status;