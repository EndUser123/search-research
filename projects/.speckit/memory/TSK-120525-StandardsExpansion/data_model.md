# CSF NIP Standards Expansion Initiative - Data Model
**Project ID**: TSK-120525-StandardsExpansion
**Version**: 1.0
**Last Updated**: 2025-12-05

## Entity Definitions

### Core Entities

#### Standard
```sql
CREATE TABLE standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT NOT NULL UNIQUE,
    language TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '2025',
    category TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('blocker', 'error', 'warning', 'info')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    validation_command TEXT,
    auto_fix_command TEXT,
    evidence_level INTEGER CHECK (evidence_level BETWEEN 1 AND 5),
    tags TEXT, -- JSON array of tags
    example_violation TEXT,
    example_fix TEXT,
    rationale TEXT,
    refs TEXT, -- JSON array of references
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    source TEXT DEFAULT 'cks', -- cks, library, custom, community
    UNIQUE(rule_id, language, version)
);
```

**Fields Description:**
- **rule_id**: Unique identifier following pattern `LANG_###_DESCRIPTION`
- **language**: Programming language (python, typescript, javascript, go, rust, java, cpp, architecture)
- **version**: Standards version (2025, 2024, etc.)
- **category**: Validation category (dependencies, security, performance, etc.)
- **severity**: Impact level (blocker, error, warning, info)
- **validation_command**: Command to validate the standard
- **auto_fix_command**: Command to auto-fix violations
- **evidence_level**: Confidence level (1=low, 5=high)
- **tags**: JSON array of tags for categorization
- **refs**: JSON array of reference URLs
- **source**: Origin of the standard (cks, library, custom, community)

#### Language
```sql
CREATE TABLE languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    file_extensions TEXT, -- JSON array of file extensions
    parser_class TEXT, -- Parser implementation class
    validator_class TEXT, -- Validator implementation class
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Category
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES categories(id),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### ValidationResult
```sql
CREATE TABLE validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    standard_id INTEGER NOT NULL REFERENCES standards(id),
    file_path TEXT NOT NULL,
    line_number INTEGER,
    status TEXT NOT NULL CHECK (status IN ('pass', 'fail', 'skip', 'error')),
    message TEXT,
    details TEXT, -- JSON object with additional details
    execution_time_ms INTEGER,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_standard (session_id, standard_id),
    INDEX idx_validated_at (validated_at)
);
```

### Library Integration Entities

#### LibraryStandard
```sql
CREATE TABLE library_standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    library_name TEXT NOT NULL,
    library_version TEXT,
    standard_type TEXT NOT NULL CHECK (standard_type IN ('best_practice', 'security', 'performance', 'deprecation')),
    rule_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    source_url TEXT,
    confidence_score REAL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    metadata TEXT, -- JSON object with additional metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(library_name, rule_id)
);
```

#### LibraryMetadata
```sql
CREATE TABLE library_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    library_name TEXT NOT NULL UNIQUE,
    version_detected TEXT,
    last_checked TIMESTAMP,
    doc_hash TEXT,
    total_results INTEGER DEFAULT 0,
    key_findings_count INTEGER DEFAULT 0,
    metadata TEXT, -- JSON object with extended metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Plugin System Entities

#### ValidationPlugin
```sql
CREATE TABLE validation_plugins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    class_name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    supported_languages TEXT, -- JSON array of supported languages
    supported_categories TEXT, -- JSON array of supported categories
    configuration TEXT, -- JSON object with plugin configuration
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### PluginExecution
```sql
CREATE TABLE plugin_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_id INTEGER NOT NULL REFERENCES validation_plugins(id),
    session_id TEXT NOT NULL,
    execution_time_ms INTEGER,
    standards_validated INTEGER,
    results TEXT, -- JSON object with execution results
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_plugin_session (plugin_id, session_id)
);
```

### Configuration and Tracking Entities

#### ValidationSession
```sql
CREATE TABLE validation_sessions (
    id TEXT PRIMARY KEY,
    project_root TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('l1', 'l2', 'l3', 'full')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_standards INTEGER DEFAULT 0,
    passed_standards INTEGER DEFAULT 0,
    failed_standards INTEGER DEFAULT 0,
    skipped_standards INTEGER DEFAULT 0,
    error_standards INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    metadata TEXT -- JSON object with session metadata
);
```

#### SystemConfiguration
```sql
CREATE TABLE system_configuration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    data_type TEXT CHECK (data_type IN ('string', 'integer', 'boolean', 'json')),
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Relationships

### Entity Relationship Diagram

```
Languages (1) ←→ (N) Standards (N) ←→ (N) ValidationResults
    ↑                                      ↑
    │                                      │
    │                               ValidationSessions
    │                                      ↑
    │                                      │
Categories (1) ←→ (N) Standards        PluginExecutions
    ↑                                      ↑
    │                                      │
    │                               ValidationPlugins
    │
LibraryMetadata (1) ←→ (N) LibraryStandards
```

### Key Relationships

1. **Standards → Languages**: Each standard belongs to exactly one language
2. **Standards → Categories**: Each standard belongs to exactly one category
3. **Standards → ValidationResults**: One standard can have multiple validation results
4. **ValidationResults → ValidationSessions**: Results are grouped by validation session
5. **LibraryMetadata → LibraryStandards**: One library can have multiple standards
6. **ValidationPlugins → PluginExecutions**: One plugin can have multiple execution records

## Data Integrity Rules

### Primary Constraints
1. **Unique Standards**: No duplicate (rule_id, language, version) combinations
2. **Valid Severity**: Severity must be one of the predefined values
3. **Valid Evidence Level**: Evidence level must be between 1 and 5
4. **Valid Status**: Validation status must be one of the predefined values

### Foreign Key Constraints
1. **Validation Results**: Must reference existing standards
2. **Plugin Executions**: Must reference existing plugins
3. **Categories**: Parent category must exist (if not null)

### Check Constraints
1. **Confidence Score**: Must be between 0.0 and 1.0
2. **Execution Time**: Must be non-negative
3. **Line Numbers**: Must be non-negative (or null)

## Data Validation Rules

### Standards Validation
```python
def validate_standard(standard_data):
    """Validate standard data before insertion"""
    required_fields = ['rule_id', 'language', 'category', 'title', 'description']

    for field in required_fields:
        if not standard_data.get(field):
            raise ValidationError(f"Missing required field: {field}")

    # Validate rule_id format
    if not re.match(r'^[A-Z_]+_[0-9]+_.+$', standard_data['rule_id']):
        raise ValidationError("Invalid rule_id format")

    # Validate severity
    valid_severities = ['blocker', 'error', 'warning', 'info']
    if standard_data['severity'] not in valid_severities:
        raise ValidationError(f"Invalid severity: {standard_data['severity']}")

    # Validate evidence level
    if not (1 <= standard_data['evidence_level'] <= 5):
        raise ValidationError("Evidence level must be between 1 and 5")

    return True
```

### JSON Field Validation
```python
def validate_json_field(field_name, json_data, expected_type=list):
    """Validate JSON fields"""
    if not json_data:
        return []

    try:
        parsed = json.loads(json_data) if isinstance(json_data, str) else json_data
        if not isinstance(parsed, expected_type):
            raise ValidationError(f"Invalid JSON type for {field_name}")
        return parsed
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {field_name}: {e}")
```

## Indexing Strategy

### Primary Indexes
```sql
-- Performance indexes for common queries
CREATE INDEX idx_standards_language ON standards(language);
CREATE INDEX idx_standards_category ON standards(category);
CREATE INDEX idx_standards_severity ON standards(severity);
CREATE INDEX idx_standards_active ON standards(is_active);
CREATE INDEX idx_standards_source ON standards(source);

-- Full-text search for standards
CREATE VIRTUAL TABLE standards_fts USING fts5(
    rule_id, title, description, rationale,
    content='standards',
    tokenize='porter'
);

-- Validation session indexes
CREATE INDEX idx_validation_sessions_started ON validation_sessions(started_at);
CREATE INDEX idx_validation_results_session ON validation_results(session_id);
CREATE INDEX idx_validation_results_standard ON validation_results(standard_id);
```

### Composite Indexes
```sql
-- Complex query optimization
CREATE INDEX idx_standards_lang_cat ON standards(language, category);
CREATE INDEX idx_standards_lang_sev ON standards(language, severity);
CREATE INDEX idx_standards_source_lang ON standards(source, language);
```

## Migration Strategy

### Phase 1: Schema Migration
1. **Backup existing database**: `cp standards_knowledge.db standards_knowledge_backup.db`
2. **Add new columns**: Alter existing tables with new fields
3. **Create new tables**: Add library and plugin system tables
4. **Data migration**: Convert existing data to new format
5. **Validation**: Ensure all constraints are satisfied

### Phase 2: Data Migration
```python
async def migrate_existing_standards():
    """Migrate existing standards to new schema"""
    # Add source field to existing standards
    await db.execute("ALTER TABLE standards ADD COLUMN source TEXT DEFAULT 'cks'")

    # Migrate JSON fields to proper format
    standards = await db.execute("SELECT id, tags, refs FROM standards").fetchall()

    for standard in standards:
        # Fix JSON formatting
        tags = fix_json_field(standard['tags'])
        refs = fix_json_field(standard['refs'])

        await db.execute(
            "UPDATE standards SET tags = ?, refs = ? WHERE id = ?",
            (json.dumps(tags), json.dumps(refs), standard['id'])
        )
```

### Phase 3: Validation
```python
async def validate_migration():
    """Validate migration success"""
    # Check all standards have valid data
    invalid_standards = await db.execute("""
        SELECT COUNT(*) FROM standards
        WHERE rule_id IS NULL OR language IS NULL OR category IS NULL
    """).fetchone()[0]

    if invalid_standards > 0:
        raise MigrationError(f"Found {invalid_standards} invalid standards")

    # Check all constraints are satisfied
    await db.execute("PRAGMA foreign_key_check")
```

## Performance Considerations

### Database Optimization
1. **Connection Pooling**: Use connection pooling for concurrent access
2. **Query Optimization**: Use prepared statements and parameterized queries
3. **Caching**: Cache frequently accessed standards and validation results
4. **Batch Operations**: Use batch inserts for large data imports

### Memory Management
```python
class StandardsDatabase:
    def __init__(self):
        self.connection_pool = []
        self.cache = LRUCache(maxsize=1000)

    async def get_standard_cached(self, rule_id):
        """Get standard with caching"""
        if rule_id in self.cache:
            return self.cache[rule_id]

        standard = await self.get_standard(rule_id)
        self.cache[rule_id] = standard
        return standard
```

## Security Considerations

### Data Protection
1. **Input Validation**: All user inputs validated before database operations
2. **SQL Injection Prevention**: Use parameterized queries exclusively
3. **Access Control**: Implement proper access controls for database operations
4. **Audit Logging**: Log all database modifications for audit trails

### Privacy Protection
```python
def sanitize_validation_result(result):
    """Remove sensitive information from validation results"""
    if 'file_path' in result:
        # Remove user-specific paths
        result['file_path'] = os.path.basename(result['file_path'])

    if 'user_data' in result:
        # Remove any user data
        del result['user_data']

    return result
```

---

**Data Model Owner**: CSF NIP Development Team
**Database System**: SQLite with FTS5
**CWO12 Compliance**: Fully Compliant
**Last Updated**: 2025-12-05