# TSK-120925-Parallel_RCA_System Data Model

## Entity Definitions

### RCA Session Entity
```python
@dataclass
class RCASession:
    """Represents a complete RCA analysis session"""
    session_id: str  # UUID for unique identification
    timestamp: datetime  # ISO 8601 format
    system: str  # "rca" or "rca-v2"
    issue_description: str  # User-provided issue description
    issue_type: str  # Categorized issue type
    user_id: str  # User identifier (if available)
    environment: dict  # Environment context information
    configuration: dict  # System configuration used
    status: str  # "started", "completed", "failed", "cancelled"
```

### Analysis Result Entity
```python
@dataclass
class AnalysisResult:
    """Represents the output of an RCA analysis"""
    session_id: str  # Reference to parent session
    root_cause: str  # Identified root cause
    confidence_score: float  # 0.0 to 1.0 confidence level
    issue_type: str  # Categorized issue type
    severity: str  # "low", "medium", "high", "critical"
    analysis_method: str  # "pyrca", "openrca", "mcp", "hybrid"
    evidence_items: List[EvidenceItem]  # Supporting evidence
    hypotheses: List[Hypothesis]  # Generated hypotheses
    fix_recommendations: List[FixRecommendation]  # Suggested fixes
    prevention_strategies: List[str]  # Prevention recommendations
    execution_time: float  # Analysis duration in seconds
    tools_used: List[str]  # Tools utilized in analysis
```

### Evidence Item Entity
```python
@dataclass
class EvidenceItem:
    """Represents a piece of evidence supporting RCA analysis"""
    evidence_id: str  # Unique identifier
    session_id: str  # Reference to parent session
    evidence_type: str  # "log", "metric", "trace", "code", "configuration"
    source: str  # Source of evidence (tool name or system component)
    content: str  # Evidence content or description
    confidence: float  # Confidence level in evidence relevance
    timestamp: datetime  # When evidence was collected
    metadata: dict  # Additional evidence metadata
    file_path: str  # Related file path (if applicable)
    line_number: int  # Related line number (if applicable)
```

### Hypothesis Entity
```python
@dataclass
class Hypothesis:
    """Represents a hypothesis about the root cause"""
    hypothesis_id: str  # Unique identifier
    session_id: str  # Reference to parent session
    description: str  # Hypothesis description
    evidence_for: List[str]  # Evidence supporting hypothesis
    evidence_against: List[str]  # Evidence contradicting hypothesis
    confidence_score: float  # Confidence in hypothesis accuracy
    likelihood: str  # "high", "medium", "low"
    test_method: str  # How to test this hypothesis
    status: str  # "pending", "confirmed", "rejected", "unknown"
```

### Performance Metrics Entity
```python
@dataclass
class PerformanceMetrics:
    """Performance metrics for RCA session"""
    session_id: str  # Reference to parent session
    execution_time: float  # Total execution time in seconds
    tool_init_time: float  # Time to initialize tools
    analysis_time: float  # Time for core analysis
    peak_memory_usage: float  # Peak memory usage in MB
    peak_cpu_usage: float  # Peak CPU usage percentage
    network_calls: int  # Number of network calls made
    disk_operations: int  # Number of disk operations
    cache_hits: int  # Number of cache hits
    cache_misses: int  # Number of cache misses
    error_count: int  # Number of errors encountered
    retry_count: int  # Number of retry attempts
```

### User Feedback Entity
```python
@dataclass
class UserFeedback:
    """User feedback on RCA session"""
    session_id: str  # Reference to parent session
    user_id: str  # User identifier
    timestamp: datetime  # When feedback was provided
    satisfaction_score: int  # 1-5 satisfaction rating
    accuracy_rating: int  # 1-5 accuracy rating
    helpfulness_rating: int  # 1-5 helpfulness rating
    system_preference: str  # "rca", "rca-v2", "equal", "no_preference"
    comments: str  # User comments and feedback
    recommendations_accepted: bool  # Whether user accepted recommendations
    time_saved_estimate: str  # User estimate of time saved
    would_use_again: bool  # Whether user would use system again
```

### Configuration Entity
```python
@dataclass
class SystemConfiguration:
    """System configuration for RCA analysis"""
    config_id: str  # Unique configuration identifier
    session_id: str  # Reference to parent session
    tool_selection: List[str]  # Selected tools for analysis
    analysis_depth: str  # "quick", "standard", "deep"
    auto_fix_enabled: bool  # Whether auto-fix was enabled
    confidence_threshold: float  # Minimum confidence threshold
    max_execution_time: int  # Maximum execution time in seconds
    parallel_execution: bool  # Whether parallel execution was used
    cache_enabled: bool  # Whether caching was enabled
    mcp_servers: List[str]  # MCP servers used
    pyrca_enabled: bool  # Whether PyRCA was used
    openrca_enabled: bool  # Whether OpenRCA was used
```

## Relationships

### Primary Relationships

#### Session ↔ Analysis Result
```
RCASession (1) ←→ (1) AnalysisResult
- Each session produces exactly one analysis result
- Analysis result cannot exist without session
- Session provides context for analysis result
```

#### Session ↔ Evidence Items
```
RCASession (1) ←→ (N) EvidenceItem
- Session can have multiple evidence items
- Evidence items belong to exactly one session
- Evidence supports or refutes analysis
```

#### Session ↔ Hypotheses
```
RCASession (1) ←→ (N) Hypothesis
- Session can generate multiple hypotheses
- Hypotheses are generated within session context
- Hypotheses compete for root cause selection
```

#### Session ↔ Performance Metrics
```
RCASession (1) ←→ (1) PerformanceMetrics
- Each session has exactly one performance metrics record
- Performance metrics capture session execution characteristics
- Used for system optimization and comparison
```

#### Session ↔ User Feedback
```
RCASession (1) ←→ (0..N) UserFeedback
- Session can have multiple feedback entries
- Users can provide feedback over time
- Used for system improvement and preference analysis
```

#### Session ↔ Configuration
```
RCASession (1) ←→ (1) SystemConfiguration
- Each session uses exactly one configuration
- Configuration determines analysis approach
- Used for reproducibility and system tuning
```

### Secondary Relationships

#### Analysis Result ↔ Evidence Items
```
AnalysisResult (1) ←→ (N) EvidenceItem
- Analysis result references supporting evidence
- Evidence items provide basis for analysis conclusions
- Link established through session relationship
```

#### Analysis Result ↔ Hypotheses
```
AnalysisResult (1) ←→ (N) Hypothesis
- Analysis result contains selected hypothesis
- Other hypotheses are tracked for completeness
- Relationship indicates hypothesis selection process
```

## Data Integrity Rules

### Uniqueness Constraints

#### Session Uniqueness
```python
UNIQUE(session_id)
- Each session_id must be unique across all sessions
- Generated using UUID4 to ensure global uniqueness
- Prevents session ID conflicts in distributed systems
```

#### Evidence Uniqueness
```python
UNIQUE(evidence_id)
- Each evidence_id must be unique within system
- Generated using combination of session_id and sequence
- Ensures evidence traceability and reference integrity
```

#### Hypothesis Uniqueness
```python
UNIQUE(hypothesis_id)
- Each hypothesis_id must be unique within system
- Generated using combination of session_id and sequence
- Prevents hypothesis confusion and duplication
```

### Referential Integrity

#### Session References
```python
FOREIGN KEY(session_id) REFERENCES RCASession(session_id)
- All entities must reference valid session_id
- Cascade delete: removing session removes related entities
- Prevents orphaned entities and data inconsistency
```

#### Evidence Consistency
```python
evidence_items.session_id MUST EXIST in rcasessions
- Evidence items must belong to existing sessions
- Cannot have evidence for non-existent sessions
- Ensures data consistency across entities
```

#### Configuration Consistency
```python
system_configurations.session_id MUST EXIST in rcasessions
- Configuration records must reference valid sessions
- Cannot have configuration for non-existent sessions
- Maintains audit trail of system usage
```

### Validation Rules

#### Score Validation
```python
confidence_score BETWEEN 0.0 AND 1.0
- All confidence scores must be valid probability values
- Applied to: AnalysisResult, EvidenceItem, Hypothesis
- Prevents invalid statistical calculations
```

#### Rating Validation
```python
satisfaction_score BETWEEN 1 AND 5
accuracy_rating BETWEEN 1 AND 5
helpfulness_rating BETWEEN 1 AND 5
- All user ratings must be within valid range
- Ensures meaningful feedback analysis
- Prevents rating system abuse
```

#### Timestamp Validation
```python
timestamp MUST BE valid datetime
- All timestamps must be valid ISO 8601 format
- Applied to: RCASession, EvidenceItem, UserFeedback
- Ensures chronological consistency and analysis
```

#### Status Validation
```python
status IN valid_status_values
- Session status must be from predefined set
- Valid values: "started", "completed", "failed", "cancelled"
- Prevents invalid status transitions
```

### Business Rules

#### Session Lifecycle
```python
session.status transitions:
  "started" → "completed" (normal completion)
  "started" → "failed" (error or timeout)
  "started" → "cancelled" (user cancellation)
  No other transitions allowed
```

#### Analysis Result Requirements
```python
AnalysisResult requirements:
  - Must have at least one evidence item
  - Confidence score cannot be negative
  - Root cause description cannot be empty
  - Must reference valid session_id
```

#### Feedback Collection Rules
```python
UserFeedback constraints:
  - Can only provide feedback for completed sessions
  - Cannot have multiple feedback for same timestamp
  - Satisfaction rating cannot be empty
  - User_id must be valid identifier
```

#### Configuration Consistency
```python
SystemConfiguration rules:
  - Tool selection must reference available tools
  - Analysis depth must be valid option
  - Execution time must be reasonable (>0)
  - Confidence threshold must be between 0.0 and 1.0
```

## Validation Rules

### Data Type Validation
```python
Type Validation Rules:
  - session_id: UUID format string
  - timestamp: ISO 8601 datetime string
  - confidence_score: float between 0.0 and 1.0
  - execution_time: positive float or integer
  - memory_usage: positive float or integer
  - satisfaction_score: integer between 1 and 5
```

### Format Validation
```python
Format Validation Rules:
  - session_id: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
  - timestamp: ISO 8601 with timezone
  - issue_type: predefined category list
  - system: "rca" or "rca-v2"
  - severity: "low", "medium", "high", "critical"
```

### Business Logic Validation
```python
Business Logic Validation:
  - Session cannot be completed without analysis result
  - User feedback cannot be provided for cancelled sessions
  - Performance metrics cannot have negative values
  - Evidence items must belong to same session as analysis
```

### Cross-Entity Validation
```python
Cross-Entity Validation:
  - Evidence items must support or refute related hypotheses
  - Performance metrics must align with tool usage
  - Configuration must match actual tool selection
  - User preferences must align with actual usage patterns
```

## Security Constraints

### Data Privacy
```python
Privacy Protection Rules:
  - Sensitive data in issue_description must be anonymized
  - User personal information must be protected
  - File paths in evidence must be sanitized
  - PII must be removed from metadata
```

### Access Control
```python
Access Control Rules:
  - Users can only access their own sessions
  - Administrators can access all sessions
  - Analytics access requires explicit consent
  - Export capabilities require authorization
```

### Audit Trail
```python
Audit Requirements:
  - All session modifications must be logged
  - User feedback must track source and timestamp
  - Configuration changes must be audited
  - System errors must be recorded with context
```

### Data Retention
```python
Retention Policies:
  - Sessions older than 2 years must be archived
  - User feedback must be retained for 1 year
  - Performance metrics must be aggregated after 6 months
  - Raw evidence items must be deleted after 1 year
```

## Data Quality Metrics

### Completeness Metrics
```python
Completeness Measures:
  - Session completion rate: completed_sessions / total_sessions
  - Evidence coverage: sessions_with_evidence / total_sessions
  - Feedback collection rate: sessions_with_feedback / total_sessions
  - Configuration coverage: sessions_with_config / total_sessions
```

### Accuracy Metrics
```python
Accuracy Measures:
  - Data type validation pass rate
  - Referential integrity violation count
  - Business rule violation count
  - Format validation error rate
```

### Consistency Metrics
```python
Consistency Measures:
  - Cross-entity relationship validation
  - Timestamp consistency checks
  - Status transition validation
  - Score range validation compliance
```

### Performance Metrics
```python
Performance Measures:
  - Query response time < 100ms
  - Insert performance < 10ms per record
  - Export performance < 5 seconds per session
  - Database query optimization score
```

## Storage Architecture

### JSON File Structure
```
data/rca_metrics/
├── sessions/
│   ├── YYYY/
│   │   ├── MM/
│   │   │   ├── session_uuid.json
│   │   │   └── session_uuid.json
│   │   └── ...
│   └── ...
├── analytics/
│   ├── daily_usage_YYYY-MM-DD.json
│   ├── weekly_performance_YYYY-WW.json
│   ├── monthly_summary_YYYY-MM.json
│   └── system_health.json
├── exports/
│   ├── user_feedback_YYYY-MM-DD.csv
│   ├── performance_comparison_YYYY-MM-DD.json
│   └── system_recommendations.json
└── indexes/
    ├── session_by_date.json
    ├── user_by_system.json
    └── issue_type_stats.json
```

### Indexing Strategy
```python
Index Implementation:
- session_by_date: Optimized for date-range queries
- user_by_system: Optimized for user preference analysis
- issue_type_stats: Optimized for issue type analytics
- performance_summary: Optimized for performance analysis
```

### Backup Strategy
```python
Backup Requirements:
- Daily automated backups of all JSON data
- Weekly full backup with compression
- Monthly archive to cold storage
- Immediate backup before any data migration
```

This data model provides a robust foundation for the Parallel RCA System, ensuring data integrity, supporting comprehensive analytics, and enabling evidence-based decision making while maintaining privacy and security standards.