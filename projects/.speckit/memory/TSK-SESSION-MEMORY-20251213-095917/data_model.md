# Session Memory Persistence - Data Model

**TSK**: TSK-SESSION-MEMORY-20251213-095917
**Version**: 1.0
**Created**: 2025-12-13
**Status**: Ready for Implementation

## Entity Definitions

### 1. CompactionBridge

Core entity that represents a bridge between pre-compaction and post-compaction sessions.

```python
@dataclass
class CompactionBridge:
    bridge_id: str                          # Unique identifier for the bridge
    pre_compact_session_id: str             # Session ID before compaction
    post_compact_session_id: str            # Session ID after compaction
    timestamp: datetime                     # When the bridge was created
    compact_count: int                      # Number of compactions in session

    # Preserved elements
    active_tasks: List[TaskContext]         # Active tasks at compaction time
    chat_patterns: List[ConversationPattern] # Conversation patterns
    evidence_links: List[EvidenceReference]  # Evidence references

    # Restoration metadata
    restoration_success: bool               # Whether restoration succeeded
    missing_elements: List[str]             # Elements that couldn't be restored
    restoration_timestamp: Optional[datetime] # When restoration occurred
    integrity_hash: str                     # Hash for data integrity verification

    # Performance metrics
    preservation_time_ms: float             # Time taken to preserve context
    restoration_time_ms: float              # Time taken to restore context
```

### 2. TaskContext

Represents a task with its session-relevant context information.

```python
@dataclass
class TaskContext:
    task_id: str                           # Unique task identifier
    title: str                             # Task title and description
    description: str                       # Detailed task description
    status: str                            # Current task status
    priority: str                          # Task priority level
    phase: str                             # Current development phase
    task_type: str                         # Type of task (feature, bug, etc.)

    # Progress tracking
    progress: float                        # Completion percentage (0.0-1.0)
    last_activity: datetime                # Last activity timestamp
    time_spent: float                      # Total time spent on task

    # Session relevance
    session_relevance: float               # How relevant this task is to session (0.0-1.0)
    context_criticality: float             # Criticality score for preservation (0.0-1.0)
    session_span: int                      # Number of sessions this task spans

    # Context elements
    context_elements: List[str]            # Key context elements for this task
    dependencies: List[str]                 # Task dependencies
    blockers: List[str]                    # Current blockers

    # State information
    current_state: dict                    # Current task state
    previous_states: List[dict]            # Historical states for rollback
```

### 3. ConversationPattern

Represents a pattern in conversation that should be preserved.

```python
@dataclass
class ConversationPattern:
    pattern_id: str                        # Unique pattern identifier
    pattern_type: str                      # Type of pattern (question, decision, etc.)
    content_summary: str                   # Summary of pattern content
    participants: List[str]                 # Participants in conversation

    # Pattern content
    key_decisions: List[str]               # Important decisions made
    action_items: List[str]                # Action items identified
    context_keywords: List[str]            # Keywords for pattern retrieval

    # Session importance
    session_importance: float              # Importance to current session (0.0-1.0)
    cross_session_relevance: float          # Relevance to future sessions (0.0-1.0)

    # Temporal information
    created_at: datetime                   # When pattern was created
    last_referenced: datetime               # When pattern was last used
    reference_count: int                   # How many times referenced

    # Pattern metadata
    semantic_hash: str                     # Hash for semantic similarity
    vector_embedding: Optional[List[float]] # Vector embedding for similarity search
```

### 4. EvidenceReference

Represents a reference to evidence that should be preserved.

```python
@dataclass
class EvidenceReference:
    evidence_id: str                       # Unique evidence identifier
    evidence_type: str                     # Type of evidence (code, doc, test, etc.)
    relevance_score: float                 # Relevance to session context (0.0-1.0)

    # Evidence content
    evidence_path: str                     # Path to evidence file/location
    evidence_summary: str                  # Summary of evidence content
    key_insights: List[str]                # Key insights from evidence

    # Session context
    session_context: str                   # How evidence relates to session
    cross_session_ref: Optional[str]       # Reference to evidence in other sessions

    # Temporal information
    created_at: datetime                   # When evidence was created
    accessed_at: datetime                  # When evidence was last accessed
    last_validated: datetime               # When evidence was last validated

    # Evidence metadata
    confidence_score: float                # Confidence in evidence (0.0-1.0)
    verification_status: str               # Verification status
    integrity_hash: str                    # Hash for integrity verification
```

### 5. SessionTracking

Tracks session information and compaction history.

```python
@dataclass
class SessionTracking:
    session_id: str                        # Unique session identifier
    task_master_session_id: str            # TaskMaster session ID

    # Session timeline
    started_at: datetime                   # When session started
    last_compaction: Optional[datetime]    # Last compaction timestamp
    ended_at: Optional[datetime]           # When session ended

    # Session statistics
    compaction_count: int                  # Number of compactions in session
    total_context_tokens: int              # Total context tokens processed
    bridge_count: int                      # Number of bridges created

    # Session status
    status: str                            # Current session status
    metadata: dict                         # Additional session metadata

    # Performance metrics
    average_preservation_time: float       # Average preservation time
    average_restoration_time: float        # Average restoration time
    total_memory_usage: float              # Total memory used by session
```

## Relationships

### Primary Relationships

1. **CompactionBridge ↔ TaskContext**
   - One-to-Many: One bridge contains multiple task contexts
   - Foreign Key: `bridge_id` in TaskContext
   - Relationship: Bridge preserves all active tasks during compaction

2. **CompactionBridge ↔ ConversationPattern**
   - One-to-Many: One bridge contains multiple conversation patterns
   - Foreign Key: `bridge_id` in ConversationPattern
   - Relationship: Bridge preserves conversation patterns for context continuity

3. **CompactionBridge ↔ EvidenceReference**
   - One-to-Many: One bridge references multiple evidence items
   - Foreign Key: `bridge_id` in EvidenceReference
   - Relationship: Bridge maintains evidence trail across compaction

4. **TaskContext ↔ SessionTracking**
   - Many-to-One: Multiple tasks belong to one session
   - Foreign Key: `session_id` in TaskContext
   - Relationship: Tasks are tracked within session lifecycle

5. **ConversationPattern ↔ SessionTracking**
   - Many-to-One: Multiple patterns belong to one session
   - Foreign Key: `session_id` in ConversationPattern
   - Relationship: Patterns are associated with session context

### Secondary Relationships

1. **TaskContext ↔ TaskContext (Self-Reference)**
   - Hierarchical: Parent-child task relationships
   - Foreign Key: `parent_task_id` in TaskContext
   - Relationship: Task dependency hierarchy

2. **EvidenceReference ↔ EvidenceReference (Cross-Session)**
   - Associative: Cross-session evidence correlation
   - Foreign Key: `cross_session_ref` in EvidenceReference
   - Relationship: Evidence can reference related evidence in other sessions

## Data Integrity Rules

### 1. Referential Integrity

```sql
-- CompactionBridge must have valid session references
ALTER TABLE compaction_bridge
ADD CONSTRAINT fk_compaction_bridge_pre_session
FOREIGN KEY (pre_compact_session_id) REFERENCES session_tracking(session_id);

ALTER TABLE compaction_bridge
ADD CONSTRAINT fk_compaction_bridge_post_session
FOREIGN KEY (post_compact_session_id) REFERENCES session_tracking(session_id);

-- TaskContext must belong to a session
ALTER TABLE task_context
ADD CONSTRAINT fk_task_context_session
FOREIGN KEY (session_id) REFERENCES session_tracking(session_id);

-- TaskContext parent relationship
ALTER TABLE task_context
ADD CONSTRAINT fk_task_context_parent
FOREIGN KEY (parent_task_id) REFERENCES task_context(task_id);
```

### 2. Domain Constraints

```sql
-- Score ranges must be valid
ALTER TABLE task_context
ADD CONSTRAINT chk_task_context_progress
CHECK (progress >= 0.0 AND progress <= 1.0);

ALTER TABLE task_context
ADD CONSTRAINT chk_task_context_relevance
CHECK (session_relevance >= 0.0 AND session_relevance <= 1.0);

ALTER TABLE conversation_pattern
ADD CONSTRAINT chk_pattern_importance
CHECK (session_importance >= 0.0 AND session_importance <= 1.0);

ALTER TABLE evidence_reference
ADD CONSTRAINT chk_evidence_relevance
CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0);

-- Status constraints
ALTER TABLE task_context
ADD CONSTRAINT chk_task_context_status
CHECK (status IN ('pending', 'active', 'in_progress', 'completed', 'blocked', 'cancelled'));

ALTER TABLE session_tracking
ADD CONSTRAINT chk_session_status
CHECK (status IN ('active', 'completed', 'suspended', 'terminated'));
```

### 3. Unique Constraints

```sql
-- Unique identifiers
ALTER TABLE compaction_bridge
ADD CONSTRAINT uk_compaction_bridge_id UNIQUE (bridge_id);

ALTER TABLE task_context
ADD CONSTRAINT uk_task_context_id UNIQUE (task_id);

ALTER TABLE conversation_pattern
ADD CONSTRAINT uk_conversation_pattern_id UNIQUE (pattern_id);

ALTER TABLE evidence_reference
ADD CONSTRAINT uk_evidence_reference_id UNIQUE (evidence_id);

-- Prevent duplicate active bridges for sessions
ALTER TABLE compaction_bridge
ADD CONSTRAINT uk_active_bridge_per_session
UNIQUE (post_compact_session_id) WHERE restoration_success = TRUE;
```

### 4. Check Constraints

```sql
-- Temporal constraints
ALTER TABLE compaction_bridge
ADD CONSTRAINT chk_compaction_bridge_timeline
CHECK (timestamp <= COALESCE(restoration_timestamp, timestamp));

ALTER TABLE session_tracking
ADD CONSTRAINT chk_session_timeline
CHECK (started_at <= COALESCE(ended_at, started_at));

-- Performance constraints
ALTER TABLE compaction_bridge
ADD CONSTRAINT chk_performance_metrics
CHECK (preservation_time_ms >= 0 AND restoration_time_ms >= 0);

-- Non-negative constraints
ALTER TABLE session_tracking
ADD CONSTRAINT chk_non_negative_counts
CHECK (compaction_count >= 0 AND bridge_count >= 0 AND total_context_tokens >= 0);
```

## Validation Rules

### 1. Business Logic Validation

```python
def validate_compaction_bridge(bridge: CompactionBridge) -> List[str]:
    """Validate CompactionBridge business rules"""
    errors = []

    # Must have at least one active task if restoration succeeded
    if bridge.restoration_success and not bridge.active_tasks:
        errors.append("Successful restoration requires at least one active task")

    # Integrity hash must be present
    if not bridge.integrity_hash:
        errors.append("Integrity hash is required")

    # Preservation and restoration times must be reasonable
    if bridge.preservation_time_ms > 10000:  # 10 seconds
        errors.append("Preservation time exceeds maximum threshold")

    if bridge.restoration_time_ms > 5000:   # 5 seconds
        errors.append("Restoration time exceeds maximum threshold")

    # Session IDs must be different
    if bridge.pre_compact_session_id == bridge.post_compact_session_id:
        errors.append("Pre and post session IDs must be different")

    return errors

def validate_task_context(task: TaskContext) -> List[str]:
    """Validate TaskContext business rules"""
    errors = []

    # Progress must be consistent with status
    if task.status == 'completed' and task.progress < 1.0:
        errors.append("Completed tasks must have 100% progress")

    if task.status == 'pending' and task.progress > 0.0:
        errors.append("Pending tasks must have 0% progress")

    # Must have context elements if session relevance is high
    if task.session_relevance > 0.7 and not task.context_elements:
        errors.append("High session relevance requires context elements")

    # Criticality must be consistent with session relevance
    if abs(task.context_criticality - task.session_relevance) > 0.3:
        errors.append("Context criticality and session relevance should be consistent")

    return errors
```

### 2. Data Consistency Validation

```python
def validate_session_integrity(session_id: str) -> List[str]:
    """Validate session data consistency"""
    errors = []

    # Check for orphaned task contexts
    orphaned_tasks = TaskContext.objects.filter(
        session_id=session_id,
        bridge__isnull=True
    )
    if orphaned_tasks.exists():
        errors.append(f"Found {orphaned_tasks.count()} orphaned task contexts")

    # Check for inconsistent timestamps
    session = SessionTracking.objects.get(session_id=session_id)
    if session.started_at > session.ended_at:
        errors.append("Session end time precedes start time")

    # Check for negative resource counts
    if session.total_context_tokens < 0:
        errors.append("Total context tokens cannot be negative")

    return errors

def validate_bridge_integrity(bridge_id: str) -> List[str]:
    """Validate bridge data integrity"""
    errors = []

    bridge = CompactionBridge.objects.get(bridge_id=bridge_id)

    # Verify integrity hash
    calculated_hash = calculate_bridge_hash(bridge)
    if calculated_hash != bridge.integrity_hash:
        errors.append("Bridge integrity hash mismatch")

    # Check for missing elements
    if bridge.restoration_success and bridge.missing_elements:
        errors.append("Successful restoration cannot have missing elements")

    # Verify temporal consistency
    if bridge.restoration_timestamp and bridge.restoration_timestamp < bridge.timestamp:
        errors.append("Restoration timestamp precedes creation timestamp")

    return errors
```

## Performance Considerations

### 1. Indexing Strategy

```sql
-- Primary indexes
CREATE INDEX idx_compaction_bridge_created_at ON compaction_bridge(created_at);
CREATE INDEX idx_task_context_session_id ON task_context(session_id);
CREATE INDEX idx_conversation_pattern_session_id ON conversation_pattern(session_id);
CREATE INDEX idx_evidence_reference_session_id ON evidence_reference(session_id);

-- Performance indexes
CREATE INDEX idx_task_context_relevance ON task_context(session_relevance) WHERE session_relevance > 0.5;
CREATE INDEX idx_conversation_pattern_importance ON conversation_pattern(session_importance) WHERE session_importance > 0.5;
CREATE INDEX idx_evidence_reference_relevance ON evidence_reference(relevance_score) WHERE relevance_score > 0.5;

-- Cleanup indexes
CREATE INDEX idx_compaction_bridge_cleanup ON compaction_bridge(created_at) WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### 2. Data Retention

```sql
-- Automatic cleanup of old bridges (older than 30 days)
DELETE FROM compaction_bridge
WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
AND restoration_success = TRUE;

-- Archive old session data (older than 90 days)
UPDATE session_tracking
SET status = 'archived'
WHERE ended_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

### 3. Query Optimization

```python
# Efficient session context retrieval
def get_session_context_optimized(session_id: str, limit: int = 100) -> dict:
    """Get session context with optimized queries"""

    # Use indexed queries for high-relevance items
    tasks = TaskContext.objects.filter(
        session_id=session_id,
        session_relevance__gt=0.5
    ).order_by('-session_relevance')[:limit]

    patterns = ConversationPattern.objects.filter(
        session_id=session_id,
        session_importance__gt=0.5
    ).order_by('-session_importance')[:limit]

    evidence = EvidenceReference.objects.filter(
        session_id=session_id,
        relevance_score__gt=0.5
    ).order_by('-relevance_score')[:limit]

    return {
        'tasks': tasks,
        'patterns': patterns,
        'evidence': evidence
    }
```

---

**Data Model Status**: Ready for Implementation
**Validation**: All integrity rules and constraints defined
**Performance**: Optimized indexing and query strategies included
**Next Step**: Database schema creation and migration implementation