# CWO12 Data Model: ASK Universal Router Implementation

## 🏗️ Entity Definitions

### Command Discovery Entity

#### UniversalCommand
**Description**: Represents a discovered command with comprehensive metadata for routing and discovery operations.

```python
class UniversalCommand:
    id: str                    # Unique command identifier
    name: str                  # Command name (from filename or frontmatter)
    aliases: List[str]         # Alternative command names
    path: str                  # File system path to command file
    category: str              # Command category (utility, analysis, etc.)
    description: str           # Command description
    handles: List[str]         # Intent patterns this command handles
    usage: str                 # Usage instructions
    orchestrator: dict         # Orchestrator configuration
    metadata: dict             # Additional metadata from frontmatter
    discovered_at: datetime    # Discovery timestamp
    last_modified: datetime    # File last modification time
    version: str               # Command version (if specified)
    author: str                # Command author (if specified)
    tags: List[str]            # Command tags for classification
    dependencies: List[str]    # Required dependencies
    capabilities: List[str]    # Command capabilities
    quality_score: float       # Command quality assessment
    performance_metrics: dict  # Historical performance data
    is_active: bool            # Command active status
    discovery_source: str      # Source of command discovery
```

#### CommandRegistry
**Description**: Central registry for all discovered commands with indexing and search capabilities.

```python
class CommandRegistry:
    registry_id: str           # Unique registry identifier
    commands: Dict[str, UniversalCommand]  # All discovered commands
    category_index: Dict[str, List[str]]   # Category-based command index
    handle_index: Dict[str, List[str]]     # Handle-based command index
    alias_index: Dict[str, str]            # Alias to command ID mapping
    performance_index: Dict[str, float]    # Performance-based ranking
    created_at: datetime         # Registry creation timestamp
    last_updated: datetime       # Last update timestamp
    total_commands: int          # Total number of commands
    cache_status: dict          # Cache status and statistics
    index_status: dict          # Index building status
```

### Semantic Routing Entity

#### UserIntent
**Description**: Represents analyzed user intent for routing decisions.

```python
class UserIntent:
    intent_id: str              # Unique intent identifier
    raw_input: str              # Original user input
    processed_input: str        # Cleaned and preprocessed input
    intent_type: str            # Type of intent (command, question, etc.)
    confidence_score: float     # Confidence in intent classification
    entities: List[dict]        # Extracted entities from input
    context_clues: List[str]    # Context-dependent clues
    session_context: dict       # Session context information
    timestamp: datetime         # Intent analysis timestamp
    routing_history: List[dict] # Previous routing decisions for this session
    user_preferences: dict      # User preference influences
```

#### RoutingDecision
**Description**: Represents a routing decision with associated metadata and confidence scores.

```python
class RoutingDecision:
    decision_id: str            # Unique decision identifier
    user_intent_id: str         # Reference to user intent
    selected_command: str       # Selected command ID
    confidence_score: float     # Confidence in routing decision
    alternative_commands: List[dict]  # Alternative command suggestions
    routing_algorithm: str      # Algorithm used for routing
    processing_time: float      # Time taken for routing decision
    context_factors: List[dict] # Factors influencing the decision
    truth_audit_result: dict    # Truth audit validation result
    user_feedback: dict         # User feedback on routing decision
    timestamp: datetime         # Routing decision timestamp
    session_id: str             # Session identifier
```

### Truth Audit Entity

#### ClaimValidation
**Description**: Represents a claim validation result from the truth audit system.

```python
class ClaimValidation:
    validation_id: str          # Unique validation identifier
    claim_text: str             # Original claim text
    claim_type: str             # Type of claim (implementation, capability, etc.)
    validation_score: float     # Overall validation confidence score
    evidence_required: List[str] # Required evidence for validation
    evidence_provided: List[dict] # Provided evidence items
    validation_rules: List[dict] # Rules applied for validation
    blocked: bool               # Whether claim was blocked
    block_reason: str           # Reason for blocking (if applicable)
    override_allowed: bool      # Whether user override is permitted
    validation_timestamp: datetime # Validation timestamp
    validator_version: str      # Version of validator used
```

### Performance Analytics Entity

#### RoutingMetrics
**Description**: Tracks performance metrics for routing operations.

```python
class RoutingMetrics:
    metrics_id: str             # Unique metrics identifier
    session_id: str             # Session identifier
    total_routings: int         # Total number of routings in session
    successful_routings: int    # Number of successful routings
    failed_routings: int        # Number of failed routings
    average_confidence: float   # Average confidence score
    average_processing_time: float # Average processing time
    user_satisfaction_score: float # User satisfaction rating
    most_used_commands: List[dict] # Most frequently used commands
    error_types: Dict[str, int] # Error type distribution
    performance_trends: List[dict] # Performance trend data
    timestamp: datetime         # Metrics collection timestamp
```

## 🔗 Relationships

### Primary Relationships

```
UniversalCommand (1) -----> (N) CommandRegistry
    └─ Commands are registered in central registry

UserIntent (1) -----> (N) RoutingDecision
    └─ Intents result in routing decisions

RoutingDecision (1) -----> (0..1) ClaimValidation
    └─ Routing decisions may require claim validation

UserIntent (N) -----> (1) SessionContext
    └─ Intents are associated with session context

RoutingDecision (N) -----> (1) RoutingMetrics
    └─ Decisions contribute to performance metrics
```

### Relationship Constraints

#### UniversalCommand Relationships
- **One-to-Many**: Each UniversalCommand can have multiple handles and aliases
- **Many-to-One**: Multiple UniversalCommands can belong to one category
- **One-to-One**: Each UniversalCommand has one discovery source

#### UserIntent Relationships
- **One-to-Many**: Each UserIntent can result in multiple RoutingDecisions
- **Many-to-One**: Multiple UserIntents can belong to one session
- **Optional**: UserIntent may or may not have associated ClaimValidation

#### RoutingDecision Relationships
- **One-to-One**: Each RoutingDecision has exactly one UserIntent
- **Optional**: Each RoutingDecision may have one ClaimValidation
- **One-to-Many**: Each RoutingDecision can have multiple alternative suggestions

## 🛡️ Data Integrity Rules

### UniversalCommand Integrity Rules

1. **Unique Identifier Rule**: Each UniversalCommand must have a unique `id`
2. **Path Existence Rule**: `path` must reference an existing file
3. **Category Validity Rule**: `category` must be from predefined category list
4. **Handle Uniqueness Rule**: No two active commands can share identical handles
5. **Alias Uniqueness Rule**: Aliases must be unique across active commands
6. **Version Consistency Rule**: If specified, `version` must follow semantic versioning

### UserIntent Integrity Rules

1. **Non-empty Input Rule**: `raw_input` and `processed_input` cannot be empty
2. **Confidence Range Rule**: `confidence_score` must be between 0.0 and 1.0
3. **Session Context Rule**: `session_id` must reference valid session
4. **Timestamp Validity Rule**: `timestamp` cannot be in the future
5. **Intent Type Validity Rule**: `intent_type` must be from predefined intent types

### RoutingDecision Integrity Rules

1. **Decision Reference Rule**: `decision_id` must be unique
2. **Intent Reference Rule**: `user_intent_id` must reference existing UserIntent
3. **Command Existence Rule**: `selected_command` must reference existing UniversalCommand
4. **Confidence Validation Rule**: `confidence_score` must be between 0.0 and 1.0
5. **Processing Time Rule**: `processing_time` must be non-negative
6. **Alternative Validity Rule**: All `alternative_commands` must reference existing commands

### ClaimValidation Integrity Rules

1. **Validation Uniqueness**: Each `validation_id` must be unique
2. **Claim Non-emptiness**: `claim_text` cannot be empty
3. **Score Range Rule**: `validation_score` must be between 0.0 and 1.0
4. **Evidence Consistency**: `evidence_provided` must match `evidence_required` structure
5. **Blocking Logic**: If `blocked` is true, `block_reason` must be provided

## ✅ Validation Rules

### Input Validation Rules

#### Command Discovery Validation
```python
def validate_command_file(file_path: str) -> ValidationResult:
    """
    Validates command file structure and content.

    Rules:
    - File must exist and be readable
    - Must contain valid YAML frontmatter
    - Required fields must be present
    - Field values must be of correct type
    """
```

#### User Input Validation
```python
def validate_user_input(input_text: str) -> ValidationResult:
    """
    Validates user input for routing processing.

    Rules:
    - Input cannot be empty or whitespace only
    - Input length must be within reasonable bounds
    - Input must not contain malicious content
    - Input must be processable by NLP pipeline
    """
```

#### Routing Decision Validation
```python
def validate_routing_decision(decision: RoutingDecision) -> ValidationResult:
    """
    Validates routing decision consistency and completeness.

    Rules:
    - Decision must reference valid intent
    - Selected command must exist and be active
    - Confidence score must be justified
    - Processing time must be reasonable
    - Truth audit requirements must be satisfied
    """
```

### Business Logic Validation Rules

#### Semantic Routing Validation
```python
def validate_semantic_routing(intent: UserIntent, command: UniversalCommand) -> ValidationResult:
    """
    Validates semantic routing compatibility.

    Rules:
    - Intent must match command capabilities
    - Confidence score must be above minimum threshold
    - Context compatibility must be verified
    - User preferences must be respected
    """
```

#### Truth Audit Validation
```python
def validate_claim_audit(claim: str, validation: ClaimValidation) -> ValidationResult:
    """
    Validates truth audit process consistency.

    Rules:
    - Evidence requirements must be appropriate for claim type
    - Validation score must be evidence-based
    - Blocking decisions must be justified
    - Override permissions must be consistent with policy
    """
```

### Performance Validation Rules

#### Performance Threshold Validation
```python
def validate_performance_thresholds(metrics: RoutingMetrics) -> ValidationResult:
    """
    Validates performance against defined thresholds.

    Rules:
    - Discovery time must be < 200ms
    - Routing time must be < 100ms
    - Success rate must be > 95%
    - User satisfaction must be > 90%
    - Memory usage must be < 10MB
    """
```

## 📊 Data Access Patterns

### Read Patterns

#### Command Discovery Read Operations
```python
# High-frequency operations
- Get command by ID (O(1) lookup)
- Search commands by handles (O(log n) with index)
- List commands by category (O(log n) with index)
- Resolve aliases to commands (O(1) lookup)

# Medium-frequency operations
- Full text search across descriptions
- Performance-based command ranking
- Capability-based filtering
```

#### Routing Read Operations
```python
# High-frequency operations
- Get session context (O(1) lookup)
- Retrieve routing history (O(k) where k = history size)
- Performance metrics aggregation (O(n) where n = session size)

# Medium-frequency operations
- Cross-session pattern analysis
- User preference analysis
- System performance analytics
```

### Write Patterns

#### Command Discovery Write Operations
```python
# Batch operations
- Initial command discovery (bulk insert)
- Registry rebuilding (bulk delete + insert)
- Cache invalidation (batch updates)

# Incremental operations
- New command registration (single insert)
- Command metadata updates (single update)
- Performance metric updates (single update)
```

#### Routing Write Operations
```python
# High-frequency operations
- Intent logging (single insert)
- Routing decision logging (single insert)
- Performance metrics updates (incremental updates)

# Batch operations
- Session cleanup (batch deletes)
- Analytics aggregation (batch updates)
```

## 🔐 Security Considerations

### Data Protection
1. **Input Sanitization**: All user inputs must be sanitized before processing
2. **Path Validation**: File paths must be validated against directory traversal attacks
3. **YAML Security**: YAML parsing must use safe loading to prevent code injection
4. **Metadata Validation**: All metadata must be validated against defined schemas
5. **Session Isolation**: Session data must be properly isolated between users

### Access Control
1. **Command Access**: Commands must respect existing access control mechanisms
2. **Metadata Privacy**: Sensitive metadata must be protected from unauthorized access
3. **Analytics Privacy**: User analytics must respect privacy preferences
4. **Audit Trail**: All routing decisions must be logged for audit purposes

### Data Retention
1. **Session Data**: Session data should be retained according to privacy policies
2. **Analytics Data**: Performance analytics should follow data retention schedules
3. **Cache Data**: Cached discovery data should have appropriate TTL values
4. **Audit Logs**: Audit logs should be retained for compliance requirements