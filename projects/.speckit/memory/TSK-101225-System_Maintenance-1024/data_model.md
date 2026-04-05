# CSF NIP System Data Model

## Entity Definitions

### HealthCheck
```python
class HealthCheck:
    """Represents a health check plugin instance"""
    health_check_id: str  # Unique identifier
    name: str  # Human-readable name
    category: str  # Plugin category (system, security, performance, etc.)
    status: str  # active, inactive, error
    last_run: datetime  # Last execution timestamp
    last_result: dict  # Result of last health check
    confidence_score: float  # Confidence in check results (0.0-1.0)
    execution_time: float  # Time taken for last execution (seconds)
    error_message: str  # Last error message (if any)
```

### Hook
```python
class Hook:
    """Represents a system hook implementation"""
    hook_id: str  # Unique identifier
    hook_type: str  # pre_tool_use, post_tool_use, user_prompt_submit, etc.
    file_path: str  # Path to hook implementation
    status: str  # active, inactive, error
    last_execution: datetime  # Last execution timestamp
    execution_count: int  # Total execution count
    error_count: int  # Total error count
    last_error: str  # Last error message (if any)
```

### SystemComponent
```python
class SystemComponent:
    """Represents a CSF NIP system component"""
    component_id: str  # Unique identifier
    name: str  # Component name
    component_type: str  # module, plugin, service, tool
    status: str  # healthy, warning, error, unknown
    file_path: str  # Primary file location
    dependencies: list  # List of component dependencies
    health_checks: list  # Associated health check IDs
    metadata: dict  # Additional component information
```

### TaskMasterEntry
```python
class TaskMasterEntry:
    """Represents a task management entry"""
    task_id: str  # TSK format identifier
    title: str  # Task title
    description: str  # Detailed description
    status: str  # active, completed, archived
    priority: str  # critical, high, medium, low
    created_at: datetime  # Creation timestamp
    updated_at: datetime  # Last update timestamp
    artifact_paths: dict  # Paths to associated artifacts
    dependencies: list  # List of dependent task IDs
```

### CWO12Artifact
```python
class CWO12Artifact:
    """Represents a CWO12 compliance artifact"""
    artifact_id: str  # Unique identifier
    artifact_type: str  # plan, tasks, data_model, spec
    file_path: str  # File location
    task_id: str  # Associated task ID
    validation_status: str  # compliant, non_compliant, missing
    confidence_score: float  # Validation confidence (0.0-1.0)
    last_validated: datetime  # Last validation timestamp
    validation_errors: list  # List of validation issues
```

## Relationships

### One-to-Many Relationships
- **SystemComponent** → **HealthCheck** (1:N)
  - A component can have multiple associated health checks
  - Health checks can monitor different aspects of the same component

- **TaskMasterEntry** → **CWO12Artifact** (1:N)
  - A task can have multiple associated artifacts
  - Each artifact type (plan, tasks, data_model) is separate

### Many-to-Many Relationships
- **SystemComponent** ↔ **SystemComponent** (dependencies)
  - Components can depend on multiple other components
  - Circular dependencies must be detected and prevented

- **Hook** ↔ **SystemComponent** (monitoring)
  - Hooks can monitor multiple components
  - Components can be monitored by multiple hooks

### Hierarchical Relationships
- **HealthCheck** → **HealthCheck** (sub-checks)
  - Complex health checks can have sub-checks
  - Parent status depends on child status aggregation

## Data Integrity Rules

### Unique Constraints
1. **health_check_id**: Must be unique across all health checks
2. **hook_id**: Must be unique across all hooks
3. **component_id**: Must be unique across all components
4. **task_id**: Must follow TSK-DDMMYY-Description format
5. **artifact_id**: Must be unique within task context

### Referential Integrity
1. **Foreign Keys**: All references must point to existing entities
2. **Cascade Deletes**: Deleting a component should cascade to its health checks
3. **Orphan Prevention**: Cannot delete entities that have active dependencies

### Business Rules
1. **Health Check Status**: Health checks with >50% error rate are marked as error
2. **Hook Reliability**: Hooks with >10% error rate are automatically disabled
3. **Component Dependencies**: No circular dependencies allowed
4. **CWO12 Compliance**: All active tasks must have complete artifact sets
5. **Task Status**: Tasks cannot be marked complete without all artifacts validated

## Validation Rules

### Field Validation
1. **IDs**: Must match regex patterns (alphanumeric with underscores/hyphens)
2. **Status Fields**: Must be from predefined enumerated values
3. **Timestamps**: Must be valid ISO 8601 datetime strings
4. **Confidence Scores**: Must be float values between 0.0 and 1.0
5. **File Paths**: Must point to existing files or be marked as pending

### Cross-Field Validation
1. **Execution Time**: Must be reasonable (>0 and <300 seconds)
2. **Error Counts**: Cannot exceed execution counts
3. **Dependency Cycles**: Must prevent circular dependencies
4. **Artifact Completeness**: All three artifact types must exist for active tasks

## Indexing Strategy

### Primary Indexes
- health_checks.health_check_id (unique)
- hooks.hook_id (unique)
- components.component_id (unique)
- tasks.task_id (unique)
- artifacts.artifact_id (unique)

### Secondary Indexes
- health_checks.category (for filtering by type)
- health_checks.status (for active health checks)
- hooks.hook_type (for hook type queries)
- components.status (for component health queries)
- tasks.status (for active task queries)
- artifacts.validation_status (for compliance queries)

### Composite Indexes
- (task_id, artifact_type) for artifact lookup within tasks
- (component_id, health_check_id) for component health queries
- (hook_type, status) for active hook queries

## Data Access Patterns

### Read Operations
1. **Health Status Summary**: Aggregate health check results by category
2. **Component Dependencies**: Recursive dependency graph traversal
3. **Hook Performance**: Error rate and execution time statistics
4. **CWO12 Compliance**: Artifact validation status by task
5. **System Overview**: Overall system health and component status

### Write Operations
1. **Health Check Updates**: Status updates after execution
2. **Hook Execution Tracking**: Increment execution and error counters
3. **Component Status Changes**: Update component health status
4. **Task Lifecycle**: Create, update, archive task entries
5. **Artifact Validation**: Update validation status and scores

### Transaction Requirements
1. **Health Check Execution**: Update health check status atomically
2. **Hook Updates**: Update execution counters and last error together
3. **Task Completion**: Validate all artifacts before status change
4. **Component Deletion**: Remove associated health checks atomically

## Performance Considerations

### Query Optimization
1. **Health Check Aggregation**: Pre-computed status summaries
2. **Dependency Graphs**: Cached traversal results
3. **Hook Statistics**: Rolling window for performance metrics
4. **Artifact Validation**: Incremental validation for large artifacts

### Storage Optimization
1. **Historical Data**: Archive old health check results
2. **Error Messages**: Limit error message length and history
3. **Metadata Compression**: Compress large JSON metadata fields
4. **Index Maintenance**: Regular index rebuild and optimization

## Security Considerations

### Access Control
1. **Read Access**: Component-based read permissions
2. **Write Access**: Role-based write permissions
3. **Admin Access**: Full system access for maintenance
4. **Audit Trail**: Log all data modifications

### Data Protection
1. **Sensitive Data**: Encrypt sensitive configuration data
2. **Personal Data**: Minimize personal information storage
3. **Access Logging**: Track all data access attempts
4. **Backup Security**: Encrypt backup files and control access

## Migration Strategy

### Version Control
1. **Schema Versions**: Maintain schema version history
2. **Migration Scripts**: Automated migration between versions
3. **Rollback Procedures**: Ability to rollback failed migrations
4. **Data Validation**: Post-migration data integrity checks

### Compatibility
1. **Backward Compatibility**: Support older client versions
2. **Forward Compatibility**: Prepare for future schema changes
3. **API Stability**: Maintain stable data access interfaces
4. **Deprecation Warnings**: Notify about upcoming changes