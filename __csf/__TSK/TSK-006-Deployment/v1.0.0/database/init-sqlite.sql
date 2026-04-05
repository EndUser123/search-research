-- TSK-006 Persistent Learning Agent Ecosystem - SQLite Database Initialization
-- Version: 1.0.0
-- Created: 2025-12-21

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- Agent Sessions Table
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id TEXT PRIMARY KEY,
    role_name TEXT NOT NULL,
    context TEXT,
    system_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',
    metadata TEXT
);

-- Performance Metrics Table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    task_id TEXT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES agent_sessions (session_id) ON DELETE CASCADE
);

-- Routing Decisions Table
CREATE TABLE IF NOT EXISTS routing_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    task_context TEXT,
    selected_agent TEXT NOT NULL,
    routing_strategy TEXT,
    confidence_score REAL,
    execution_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES agent_sessions (session_id) ON DELETE CASCADE
);

-- Agent Performance History Table
CREATE TABLE IF NOT EXISTS agent_performance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    task_type TEXT,
    success BOOLEAN,
    execution_time_ms INTEGER,
    quality_score REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Critic Evaluations Table
CREATE TABLE IF NOT EXISTS critic_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    evaluation_type TEXT NOT NULL,
    criteria TEXT,
    scores TEXT,
    overall_score REAL,
    feedback TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES agent_sessions (session_id) ON DELETE CASCADE
);

-- CKS Integration Logs Table
CREATE TABLE IF NOT EXISTS cks_integration_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    operation_type TEXT NOT NULL,
    query TEXT,
    response_data TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES agent_sessions (session_id) ON DELETE SET NULL
);

-- System Configuration Table
CREATE TABLE IF NOT EXISTS system_configuration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type TEXT DEFAULT 'string',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Sessions Table (for tracking user interactions)
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    total_interactions INTEGER DEFAULT 0,
    session_metadata TEXT
);

-- Agent Usage Statistics Table
CREATE TABLE IF NOT EXISTS agent_usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL,
    date DATE NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    avg_session_duration REAL DEFAULT 0,
    success_rate REAL DEFAULT 0,
    avg_quality_score REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_name, date)
);

-- Error Logs Table
CREATE TABLE IF NOT EXISTS error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    severity TEXT DEFAULT 'error',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    FOREIGN KEY (session_id) REFERENCES agent_sessions (session_id) ON DELETE SET NULL
);

-- Knowledge Patterns Table (for learned patterns)
CREATE TABLE IF NOT EXISTS knowledge_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_data TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Health Metrics Table
CREATE TABLE IF NOT EXISTS system_health_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    status TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance Optimization
CREATE INDEX IF NOT EXISTS idx_agent_sessions_created_at ON agent_sessions (created_at);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_role_name ON agent_sessions (role_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_session_id ON performance_metrics (session_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics (timestamp);
CREATE INDEX IF NOT EXISTS idx_routing_decisions_session_id ON routing_decisions (session_id);
CREATE INDEX IF NOT EXISTS idx_routing_decisions_timestamp ON routing_decisions (timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_performance_history_agent_name ON agent_performance_history (agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_performance_history_timestamp ON agent_performance_history (timestamp);
CREATE INDEX IF NOT EXISTS idx_critic_evaluations_session_id ON critic_evaluations (session_id);
CREATE INDEX IF NOT EXISTS idx_cks_integration_logs_session_id ON cks_integration_logs (session_id);
CREATE INDEX IF NOT EXISTS idx_cks_integration_logs_timestamp ON cks_integration_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs (severity);
CREATE INDEX IF NOT EXISTS idx_knowledge_patterns_pattern_type ON knowledge_patterns (pattern_type);

-- Initialize System Configuration
INSERT OR IGNORE INTO system_configuration (config_key, config_value, config_type, description) VALUES
('system_version', '1.0.0', 'string', 'TSK-006 system version'),
('max_concurrent_agents', '50', 'integer', 'Maximum number of concurrent agents'),
('default_session_timeout', '3600', 'integer', 'Default session timeout in seconds'),
('cks_integration_enabled', 'true', 'boolean', 'Whether CKS integration is enabled'),
('performance_tracking_enabled', 'true', 'boolean', 'Whether performance tracking is enabled'),
('critic_system_enabled', 'true', 'boolean', 'Whether critic system is enabled'),
('default_learning_rate', '0.1', 'float', 'Default learning rate for routing'),
('cache_ttl', '3600', 'integer', 'Default cache TTL in seconds'),
('log_level', 'INFO', 'string', 'Default log level'),
('security_mode', 'production', 'string', 'Security mode (development/staging/production)');

-- Create Triggers for Automatic Timestamp Updates
CREATE TRIGGER IF NOT EXISTS update_system_configuration_timestamp
    AFTER UPDATE ON system_configuration
    FOR EACH ROW
BEGIN
    UPDATE system_configuration SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Create Views for Common Queries
CREATE VIEW IF NOT EXISTS active_agent_sessions AS
SELECT
    session_id,
    role_name,
    created_at,
    last_activity,
    (julianday('now') - julianday(created_at)) * 24 * 60 as session_duration_minutes
FROM agent_sessions
WHERE status = 'active'
AND datetime(last_activity) > datetime('now', '-1 hour');

CREATE VIEW IF NOT EXISTS daily_agent_stats AS
SELECT
    role_name,
    date(created_at) as session_date,
    COUNT(*) as total_sessions,
    AVG((julianday(last_activity) - julianday(created_at)) * 24 * 60) as avg_duration_minutes,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as completion_rate
FROM agent_sessions
GROUP BY role_name, date(created_at);

CREATE VIEW IF NOT EXISTS system_performance_summary AS
SELECT
    'total_sessions' as metric,
    COUNT(*) as value
FROM agent_sessions
UNION ALL
SELECT
    'active_sessions' as metric,
    COUNT(*) as value
FROM agent_sessions
WHERE status = 'active'
UNION ALL
SELECT
    'avg_session_duration' as metric,
    AVG((julianday(last_activity) - julianday(created_at)) * 24 * 60) as value
FROM agent_sessions
WHERE status IN ('completed', 'inactive')
UNION ALL
SELECT
    'total_errors' as metric,
    COUNT(*) as value
FROM error_logs
WHERE resolved = FALSE;

-- Database is now initialized and ready for use
SELECT 'SQLite database initialized successfully for TSK-006 Agent Ecosystem' as status;