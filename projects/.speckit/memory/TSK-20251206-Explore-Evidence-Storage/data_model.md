# Data Model: Enhanced /explore Command with TaskMaster Evidence Storage

## Entity Definitions

### 1. ExploreAnalysis (Primary Entity)
**Description**: Core entity representing an explore command analysis session

**Attributes**:
```python
class ExploreAnalysis:
    analysis_id: str              # Unique identifier (UUID format)
    timestamp: datetime            # Analysis execution timestamp
    target_directory: str          # Path to analyzed directory
    tools_used: List[str]          # List of analysis tools executed
    focus_areas: List[str]         # Analysis focus (security, performance, etc.)
    session_id: str               # Claude session identifier
    user_query: str               # Original user query/request
    retention_days: int           # Custom retention period (default: 3)
    status: AnalysisStatus         # Current analysis status
```

**Status Enum**:
```python
class AnalysisStatus(Enum):
    INITIATED = "initiated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
```

### 2. EvidenceStorage
**Description**: Evidence file storage and metadata

**Attributes**:
```python
class EvidenceStorage:
    evidence_id: str              # Unique evidence identifier
    analysis_id: str              # Foreign key to ExploreAnalysis
    file_path: str               # Local file system path
    storage_format: str          # JSON, msgpack, etc.
    file_size: int               # File size in bytes
    compression_used: bool        # Whether compression is applied
    checksum: str                # SHA-256 checksum for integrity
    created_at: datetime         # File creation timestamp
    expires_at: datetime         # File expiration timestamp
```

### 3. TaskMasterIntegration
**Description**: TaskMaster task integration for evidence tracking

**Attributes**:
```python
class TaskMasterIntegration:
    task_id: str                  # TaskMaster task identifier
    analysis_id: str              # Foreign key to ExploreAnalysis
    task_type: str               # "evidence_collection", "analysis_storage"
    task_status: str              # TaskMaster task status
    priority: int                 # Task priority (1-10)
    assigned_to: str              # Assigned agent/system
    created_at: datetime         # Task creation timestamp
    completed_at: Optional[datetime]  # Task completion timestamp
```

### 4. AnalysisResult
**Description**: Structured analysis results and findings

**Attributes**:
```python
class AnalysisResult:
    result_id: str               # Unique result identifier
    analysis_id: str              # Foreign key to ExploreAnalysis
    tool_name: str               # Analysis tool name
    result_type: str             # "security", "performance", "architecture"
    findings_summary: str        # Executive summary of findings
    detailed_results: dict       # Detailed tool-specific results
    confidence_score: float      # Result confidence (0.0-1.0)
    severity_level: str          # "low", "medium", "high", "critical"
    recommendations: List[str]   # Actionable recommendations
    execution_time: float        # Tool execution time in seconds
    success: bool                # Whether analysis succeeded
```

### 5. CrossToolReference
**Description**: Cross-tool integration and reference tracking

**Attributes**:
```python
class CrossToolReference:
    reference_id: str            # Unique reference identifier
    analysis_id: str              # Foreign key to ExploreAnalysis
    referencing_tool: str        # Tool accessing this analysis
    access_timestamp: datetime   # When tool accessed the analysis
    access_purpose: str          # Purpose of access (validation, enhancement, etc.)
    integration_success: bool    # Whether integration was successful
    notes: str                   # Additional integration notes
```

## Relationships

### Primary Relationships
```
ExploreAnalysis (1) ---------> (N) EvidenceStorage
    |
    +---------> (1) TaskMasterIntegration
    |
    +---------> (N) AnalysisResult
    |
    +---------> (N) CrossToolReference
```

### Relationship Definitions

#### ExploreAnalysis → EvidenceStorage
- **Type**: One-to-Many
- **Cascade**: Delete evidence when analysis is removed
- **Constraint**: All evidence must belong to a valid analysis

#### ExploreAnalysis → TaskMasterIntegration
- **Type**: One-to-One
- **Purpose**: Track TaskMaster task for each analysis
- **Constraint**: Each analysis has exactly one TaskMaster task

#### ExploreAnalysis → AnalysisResult
- **Type**: One-to-Many
- **Purpose**: Store results from multiple analysis tools
- **Constraint**: Results must be linked to valid analysis

#### ExploreAnalysis → CrossToolReference
- **Type**: One-to-Many
- **Purpose**: Track cross-tool access and integration
- **Constraint**: References must be linked to valid analysis

## Data Integrity Rules

### 1. Uniqueness Constraints
```sql
-- Primary key constraints
PRIMARY KEY (analysis_id) ON ExploreAnalysis
PRIMARY KEY (evidence_id) ON EvidenceStorage
PRIMARY KEY (result_id) ON AnalysisResult
PRIMARY KEY (reference_id) ON CrossToolReference

-- Unique constraints
UNIQUE (task_id) ON TaskMasterIntegration
UNIQUE (file_path) ON EvidenceStorage
```

### 2. Foreign Key Constraints
```sql
-- Foreign key relationships
FOREIGN KEY (analysis_id) REFERENCES ExploreAnalysis(analysis_id)
FOREIGN KEY (analysis_id) REFERENCES ExploreAnalysis(analysis_id) ON DELETE CASCADE
FOREIGN KEY (analysis_id) REFERENCES ExploreAnalysis(analysis_id)
FOREIGN KEY (analysis_id) REFERENCES ExploreAnalysis(analysis_id)
```

### 3. Data Validation Rules
```python
# Validation constraints
validate_timestamp(timestamp)  # Must be valid datetime
validate_directory_path(path)   # Must be valid directory path
validate_uuid_format(id)        # Must be valid UUID format
validate_confidence_score(score)  # Must be 0.0-1.0
validate_severity_level(level)   # Must be predefined severity
```

### 4. Business Rules

#### Retention Policy
- **Default Retention**: 3 days from creation timestamp
- **Custom Retention**: User-specified retention period (1-30 days)
- **Automatic Cleanup**: Expired analyses automatically removed
- **Manual Override**: Force cleanup with admin privileges

#### Storage Limits
- **Max File Size**: 100MB per evidence file
- **Max Analysis Size**: 1GB total per analysis
- **Compression Threshold**: Files >1MB automatically compressed
- **Storage Quota**: 10GB total evidence storage

#### Access Control
- **Owner Access**: Original session has full access
- **Cross-Tool Access**: Allowed with tracking
- **Public Access**: Read-only after 24 hours
- **Admin Access**: Full access to all analyses

## Validation Rules

### 1. Input Validation
```python
def validate_explore_analysis(data):
    """Validate explore analysis input data"""
    required_fields = ['target_directory', 'tools_used', 'user_query']
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValidationError(f"Missing required field: {field}")

    if not os.path.exists(data['target_directory']):
        raise ValidationError("Target directory does not exist")

    if not isinstance(data['tools_used'], list) or len(data['tools_used']) == 0:
        raise ValidationError("Tools used must be a non-empty list")
```

### 2. Integrity Validation
```python
def validate_analysis_integrity(analysis_id):
    """Validate analysis data integrity"""
    analysis = get_explore_analysis(analysis_id)

    # Check evidence files exist
    for evidence in analysis.evidence_storage:
        if not os.path.exists(evidence.file_path):
            raise IntegrityError(f"Evidence file missing: {evidence.file_path}")

        # Validate checksum
        if not validate_file_checksum(evidence.file_path, evidence.checksum):
            raise IntegrityError(f"Evidence file corrupted: {evidence.file_path}")

    # Check TaskMaster task exists
    if not taskmaster_task_exists(analysis.taskmaster_integration.task_id):
        raise IntegrityError(f"TaskMaster task missing: {analysis.taskmaster_integration.task_id}")
```

### 3. Performance Validation
```python
def validate_storage_performance():
    """Validate storage system performance"""
    metrics = get_storage_metrics()

    if metrics['average_query_time'] > 100:  # 100ms threshold
        raise PerformanceError("Storage query performance below threshold")

    if metrics['storage_utilization'] > 0.9:  # 90% threshold
        raise PerformanceError("Storage utilization approaching limit")

    if metrics['cleanup_success_rate'] < 0.95:  # 95% threshold
        raise PerformanceError("Automated cleanup success rate below threshold")
```

## Data Format Specifications

### 1. JSON Schema for Evidence Storage
```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "analysis_id": {"type": "string", "format": "uuid"},
        "timestamp": {"type": "string", "format": "date-time"},
        "target_directory": {"type": "string"},
        "tools_used": {
            "type": "array",
            "items": {"type": "string"}
        },
        "results": {
            "type": "array",
            "items": {"$ref": "#/definitions/AnalysisResult"}
        }
    },
    "required": ["analysis_id", "timestamp", "target_directory", "tools_used"]
}
```

### 2. File Naming Convention
```
Evidence files: {analysis_id}_{tool_name}_{timestamp}.json
Analysis folders: YYYY-MM-DD/{analysis_id}/
Cleanup logs: cleanup_YYYY-MM-DD.log
```

### 3. Metadata Format
```python
metadata = {
    "version": "1.0",
    "created_by": "explore_command",
    "schema_version": "2025.12.06",
    "compression": "gzip",
    "encryption": "none",
    "integrity_checksum": "sha256"
}
```

## Migration Strategy

### 1. Schema Evolution
- **Version Control**: All schema changes tracked with version numbers
- **Backward Compatibility**: Support for previous versions during transition
- **Migration Scripts**: Automated migration for data format changes
- **Rollback Capability**: Ability to rollback schema changes if needed

### 2. Data Migration
```python
def migrate_legacy_evidence():
    """Migrate legacy evidence files to new format"""
    legacy_files = find_legacy_evidence_files()

    for file_path in legacy_files:
        try:
            # Convert to new format
            new_data = convert_legacy_format(file_path)

            # Validate new data
            validate_explore_analysis(new_data)

            # Store in new location
            store_new_format(new_data)

            # Update metadata
            update_migration_metadata(file_path, new_data['analysis_id'])

        except Exception as e:
            log_migration_error(file_path, e)
            continue
```

This data model provides a robust foundation for the enhanced /explore command's evidence storage system while maintaining data integrity, performance, and scalability requirements.