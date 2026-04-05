# System Health Recovery - Data Model

## Entity Definitions

### 1. TaskMaster Database Schema

#### Task Entity
```sql
CREATE TABLE task (
    id TEXT PRIMARY KEY,                    -- UUID-based unique identifier
    tsk_id TEXT UNIQUE NOT NULL,            -- TaskMaster task ID (TSK-DDMMYY-DESC)
    title TEXT NOT NULL,                    -- Human-readable task title
    description TEXT,                       -- Detailed task description
    status TEXT DEFAULT 'active',           -- Current task status
    priority TEXT,                          -- Task priority level
    phase TEXT,                             -- Project phase
    task_type TEXT,                         -- Type of task
    assigned_to TEXT,                       -- Assignee identifier
    estimated_duration REAL,               -- Estimated completion time
    actual_duration REAL,                  -- Actual completion time
    created_at TEXT NOT NULL,              -- Creation timestamp
    started_at TEXT,                        -- Start timestamp
    completed_at TEXT,                      -- Completion timestamp
    last_activity TEXT NOT NULL,           -- Last activity timestamp
    source TEXT,                           -- Task source or origin
    parent_task_id TEXT,                   -- Parent task reference
    tags TEXT,                             -- Task tags (JSON array)
    acceptance_criteria TEXT,              -- Acceptance criteria
    verification_status TEXT,              -- Verification status
    completion_percentage REAL,           -- Progress percentage
    migration_date TEXT,                   -- Migration timestamp
    entities TEXT,                         -- Related entities (JSON)
    validation_rules TEXT,                 -- Validation rules (JSON)
    state_management TEXT,                 -- State management data
    auto_closure_enabled INTEGER,          -- Auto-closure flag
    closure_conditions TEXT,               -- Closure conditions
    last_state_check TEXT,                 -- Last state check timestamp
    state_transition_history TEXT,         -- State transitions (JSON)
    workflow_automation TEXT,              -- Automation configuration
    automation_metadata TEXT,              -- Automation metadata
    completion_triggers TEXT,              -- Completion triggers
    auto_closure_confirmed INTEGER,        -- Auto-closure confirmation
    closure_verification_required INTEGER, -- Verification requirement
    ai_complexity_score REAL,             -- AI complexity assessment
    predicted_duration REAL,               -- AI-predicted duration
    github_pr_number INTEGER,              -- Associated PR number
    evidence_count INTEGER,               -- Evidence count
    atomicity_score REAL,                 -- Task atomicity score
    is_atomic BOOLEAN,                    -- Atomic task flag
    dependency_depth INTEGER              -- Dependency depth
);
```

#### Schema Migrations Entity
```sql
CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,              -- Migration version
    description TEXT,                      -- Migration description
    applied_at TEXT NOT NULL,             -- Application timestamp
    checksum TEXT,                         -- Migration checksum
    rollback_available INTEGER DEFAULT 1   -- Rollback availability
);
```

### 2. Vector Store Database Schema

#### ChromaDB Collections Entity
```sql
-- ChromaDB uses its own schema, but here's the conceptual model:

Collection {
    id: string (primary key),
    name: string (unique),
    metadata: dictionary,
    embedding_function: reference,
    created_at: timestamp,
    updated_at: timestamp
}

Embedding {
    id: string (primary key),
    collection_id: foreign key,
    vector: array[float],                  -- 768-dimensional embedding
    document: string,
    metadata: dictionary,
    created_at: timestamp
}
```

#### Vector Store Configuration Entity
```sql
CREATE TABLE vector_store_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_type TEXT NOT NULL,              -- 'chroma', 'faiss', 'pgvector'
    connection_string TEXT,                -- Database connection string
    collection_name TEXT,                  -- Default collection name
    embedding_dimension INTEGER DEFAULT 768, -- Vector dimensions
    metadata TEXT,                         -- Additional configuration (JSON)
    created_at TEXT NOT NULL,             -- Creation timestamp
    updated_at TEXT,                       -- Last update timestamp
    is_active INTEGER DEFAULT 1           -- Active status
);
```

### 3. Knowledge Base Database Schemas

#### Library Knowledge Database Entity
```sql
CREATE TABLE library_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    library_name TEXT NOT NULL,            -- Library/package name
    version TEXT,                          -- Version information
    category TEXT,                         -- Category (web, ml, data, etc.)
    usage_pattern TEXT,                    -- Common usage patterns
    best_practices TEXT,                   -- Best practices documentation
    common_issues TEXT,                    -- Known issues and solutions
    integration_notes TEXT,                -- Integration guidelines
    examples TEXT,                         -- Code examples
    references TEXT,                       -- External references
    last_updated TEXT NOT NULL,            -- Last update timestamp
    created_at TEXT NOT NULL,             -- Creation timestamp
    metadata TEXT                          -- Additional metadata (JSON)
);
```

#### Standards Knowledge Database Entity
```sql
CREATE TABLE standards_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    standard_id TEXT UNIQUE NOT NULL,      -- Standard identifier
    title TEXT NOT NULL,                   -- Standard title
    category TEXT,                         -- Category (security, performance, etc.)
    description TEXT,                      -- Standard description
    compliance_level TEXT,                 -- Compliance level (required, recommended)
    validation_rules TEXT,                 -- Validation rules
    implementation_notes TEXT,             -- Implementation guidance
    testing_requirements TEXT,             -- Testing requirements
    references TEXT,                       -- External references
    version TEXT,                          -- Standard version
    effective_date TEXT,                   -- Effective date
    created_at TEXT NOT NULL,             -- Creation timestamp
    updated_at TEXT,                       -- Last update timestamp
    metadata TEXT                          -- Additional metadata (JSON)
);
```

#### Orchestrator Knowledge Database Entity
```sql
CREATE TABLE orchestrator_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT UNIQUE NOT NULL,       -- Pattern identifier
    pattern_name TEXT NOT NULL,            -- Pattern name
    category TEXT,                         -- Category (coordination, workflow, etc.)
    description TEXT,                      -- Pattern description
    prerequisites TEXT,                    -- Required prerequisites
    implementation_steps TEXT,             -- Implementation steps
    coordination_rules TEXT,               -- Coordination rules
    agent_roles TEXT,                      -- Agent role definitions
    communication_protocols TEXT,          -- Communication patterns
    error_handling TEXT,                   -- Error handling procedures
    optimization_notes TEXT,               -- Optimization guidelines
    created_at TEXT NOT NULL,             -- Creation timestamp
    updated_at TEXT,                       -- Last update timestamp
    metadata TEXT                          -- Additional metadata (JSON)
);
```

### 4. Health Check Monitoring Schema

#### Health Check Results Entity
```sql
CREATE TABLE health_check_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_id INTEGER NOT NULL,             -- Health check identifier
    check_name TEXT NOT NULL,              -- Health check name
    component TEXT NOT NULL,               -- Component being checked
    status TEXT NOT NULL,                  -- Status (healthy, warning, error)
    message TEXT,                          -- Status message
    details TEXT,                          -- Detailed results (JSON)
    execution_time_ms REAL,               -- Execution time in milliseconds
    timestamp TEXT NOT NULL,              -- Check execution timestamp
    session_id TEXT,                      -- Session identifier
    metadata TEXT                          -- Additional metadata (JSON)
);
```

#### Component Status Entity
```sql
CREATE TABLE component_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT UNIQUE NOT NULL,   -- Component name
    current_status TEXT NOT NULL,          -- Current status
    last_check_timestamp TEXT NOT NULL,   -- Last check timestamp
    consecutive_failures INTEGER DEFAULT 0, -- Consecutive failure count
    last_failure_message TEXT,            -- Last failure message
    uptime_percentage REAL DEFAULT 100,   -- Uptime percentage
    metadata TEXT                          -- Additional metadata (JSON)
);
```

## Relationships

### TaskMaster Relationships
```
Task (1) → (0..n) Task          -- Self-referential parent-child relationship
Task (1) → (0..1) Schema_Migration  -- Tasks can create migrations
Task (1) → (0..n) Evidence      -- Tasks can have evidence
```

### Vector Store Relationships
```
Collection (1) → (0..n) Embedding  -- Collections contain embeddings
Vector_Store_Config (1) → (0..n) Collection  -- Configuration defines collections
```

### Knowledge Base Relationships
```
Library_Knowledge (1) → (0..n) Standards_Knowledge  -- Libraries may follow standards
Library_Knowledge (1) → (0..n) Orchestrator_Knowledge  -- Libraries used in patterns
Standards_Knowledge (1) → (0..n) Orchestrator_Knowledge  -- Patterns follow standards
```

### Health Check Relationships
```
Health_Check_Result (1) → (1) Component_Status  -- Results update component status
Component_Status (1) → (0..n) Health_Check_Result  -- Status has history of results
```

## Data Integrity

### Primary Keys
- All entities have defined primary keys
- UUIDs used for TaskMaster task IDs
- Auto-incrementing integers for most other entities

### Foreign Keys
- Parent-child relationships in TaskMaster
- Component references in health checks
- Collection references in vector stores

### Unique Constraints
- TaskMaster tsk_id must be unique
- Library names must be unique within library knowledge
- Standard IDs must be unique
- Pattern IDs must be unique

## Validation Rules

### TaskMaster Validation
```json
{
    "task_id_format": "TSK-DDMMYY-.*",
    "status_values": ["active", "in_progress", "completed", "blocked", "cancelled"],
    "priority_values": ["low", "medium", "high", "critical"],
    "completion_percentage": {"min": 0, "max": 100},
    "duration_positive": true
}
```

### Vector Store Validation
```json
{
    "embedding_dimension": {"min": 1, "max": 2048},
    "collection_name": "required",
    "store_type": ["chroma", "faiss", "pgvector"]
}
```

### Knowledge Base Validation
```json
{
    "library_name": "required",
    "standard_id": "required",
    "pattern_id": "required",
    "category": "required"
}
```

### Health Check Validation
```json
{
    "status_values": ["healthy", "warning", "error"],
    "execution_time_ms": {"min": 0},
    "timestamp": "iso_format_required"
}
```

## Indexes

### TaskMaster Indexes
```sql
CREATE INDEX idx_task_status ON task(status);
CREATE INDEX idx_task_priority ON task(priority);
CREATE INDEX idx_task_created_at ON task(created_at);
CREATE INDEX idx_task_last_activity ON task(last_activity);
CREATE INDEX idx_task_parent_id ON task(parent_task_id);
CREATE INDEX idx_task_tsk_id ON task(tsk_id);
```

### Vector Store Indexes
```sql
-- Vector indexing handled by ChromaDB/FAISS internally
CREATE INDEX idx_vector_store_type ON vector_store_config(store_type);
CREATE INDEX idx_vector_store_active ON vector_store_config(is_active);
```

### Knowledge Base Indexes
```sql
-- Library Knowledge
CREATE INDEX idx_library_name ON library_knowledge(library_name);
CREATE INDEX idx_library_category ON library_knowledge(category);
CREATE INDEX idx_library_updated ON library_knowledge(last_updated);

-- Standards Knowledge
CREATE INDEX idx_standards_id ON standards_knowledge(standard_id);
CREATE INDEX idx_standards_category ON standards_knowledge(category);
CREATE INDEX idx_standards_compliance ON standards_knowledge(compliance_level);

-- Orchestrator Knowledge
CREATE INDEX idx_pattern_id ON orchestrator_knowledge(pattern_id);
CREATE INDEX idx_pattern_category ON orchestrator_knowledge(category);
```

### Health Check Indexes
```sql
CREATE INDEX idx_health_check_component ON health_check_results(component);
CREATE INDEX idx_health_check_timestamp ON health_check_results(timestamp);
CREATE INDEX idx_health_check_status ON health_check_results(status);
CREATE INDEX idx_component_status_name ON component_status(component_name);
CREATE INDEX idx_component_status_last_check ON component_status(last_check_timestamp);
```

## Migration Scripts

### TaskMaster Migration (Version 001)
```sql
-- Add created_date column (alias for created_at)
ALTER TABLE task ADD COLUMN created_date TEXT GENERATED ALWAYS AS (created_at) VIRTUAL;

-- Add AI enhancement columns
ALTER TABLE task ADD COLUMN ai_complexity_score REAL DEFAULT NULL;
ALTER TABLE task ADD COLUMN predicted_duration REAL DEFAULT NULL;
ALTER TABLE task ADD COLUMN github_pr_number INTEGER DEFAULT NULL;
ALTER TABLE task ADD COLUMN evidence_count INTEGER DEFAULT 0;

-- Add atomicity tracking
ALTER TABLE task ADD COLUMN atomicity_score REAL DEFAULT NULL;
ALTER TABLE task ADD COLUMN is_atomic BOOLEAN DEFAULT FALSE;
ALTER TABLE task ADD COLUMN dependency_depth INTEGER DEFAULT 0;
```

### Knowledge Base Initialization
```sql
-- Create knowledge base tables if they don't exist
-- (See entity definitions above for complete schema)

-- Insert initial standards data
INSERT INTO standards_knowledge (standard_id, title, category, description, compliance_level) VALUES
('CSF-NIP-001', 'Database Schema Integrity', 'database', 'All databases must have valid schemas and proper migrations', 'required'),
('CSF-NIP-002', 'Vector Store Availability', 'ai', 'Vector stores must be initialized and accessible', 'required'),
('CSF-NIP-003', 'Health Check Compliance', 'monitoring', 'All components must pass health checks', 'required');
```

## Data Privacy and Security

### Sensitive Data Handling
- No personal data stored in these schemas
- API keys and credentials stored in separate secure configuration
- Database access controlled by system permissions

### Access Controls
- Read-only access for health check monitoring
- Write access required for migrations and updates
- Administrative access for schema changes

### Audit Trail
- All schema migrations logged
- Health check results retained for historical analysis
- Configuration changes tracked with timestamps

## Performance Considerations

### Query Optimization
- Strategic indexes for common query patterns
- JSON metadata for flexible, extensible data storage
- Partitioning strategies for large health check result sets

### Scalability
- Vector stores designed for high-dimensional similarity search
- Knowledge bases support incremental updates
- Health check results support time-based partitioning

### Caching
- Component status cached to avoid repeated database queries
- Vector embeddings cached for improved performance
- Knowledge base queries cached for common patterns

## Integration Points

### External Systems
- TaskMaster integrates with Git workflows
- Vector stores connect to AI/ML pipelines
- Knowledge bases support external standard references

### APIs
- RESTful endpoints for health check data
- GraphQL interface for knowledge base queries
- Streaming updates for real-time monitoring

### Monitoring
- Metrics exported for system observability
- Alerting integration for critical failures
- Dashboard integration for system health visualization