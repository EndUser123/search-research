# TSK-NSE-ENHANCEMENT: Data Models and Entities

## Entity Definitions

### NSEContext (Enhanced)
```python
@dataclass
class NSEContext:
    """Enhanced context information for NSE recommendation generation"""
    # Core Fields
    action: str
    description: str

    # Development State
    dev_state: DevState = DevState.IDLE

    # File System Context
    current_files: List[str] = None
    project_path: str = ""
    working_directory: str = ""

    # Git Context
    git_context: Optional['GitContext'] = None

    # Session Context
    session_id: str = ""
    session_context: Optional['SessionContext'] = None

    # CKS Context
    cks_context: Optional['CKSContext'] = None

    # Metadata
    timestamp: float = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        # Initialize collections and defaults
        if self.current_files is None:
            self.current_files = []
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}
```

### GitContext
```python
@dataclass
class GitContext:
    """Git repository analysis context"""
    repository_path: str
    current_branch: str
    current_commit: str
    is_clean: bool
    has_uncommitted_changes: bool

    # Recent Commits (last 10)
    recent_commits: List['GitCommit'] = None

    # File Changes
    modified_files: List[str] = None
    added_files: List[str] = None
    deleted_files: List[str] = None

    # Analysis Results
    development_activity: str = ""  # ACTIVE, MODERATE, LOW
    recent_patterns: List[str] = None

    def __post_init__(self):
        if self.recent_commits is None:
            self.recent_commits = []
        if self.modified_files is None:
            self.modified_files = []
        if self.added_files is None:
            self.added_files = []
        if self.deleted_files is None:
            self.deleted_files = []
        if self.recent_patterns is None:
            self.recent_patterns = []
```

### GitCommit
```python
@dataclass
class GitCommit:
    """Individual git commit information"""
    commit_hash: str
    author: str
    timestamp: float
    message: str

    # Analysis
    files_changed: int
    insertions: int
    deletions: int
    commit_type: str  # FEATURE, FIX, REFACTOR, TEST, etc.

    # Context
    related_patterns: List[str] = None

    def __post_init__(self):
        if self.related_patterns is None:
            self.related_patterns = []
```

### CKSContext
```python
@dataclass
class CKSContext:
    """Cognitive Knowledge System integration context"""
    available: bool
    patterns_found: int
    confidence_boost: float

    # Pattern Matching Results
    matched_patterns: List['CKSPattern'] = None
    semantic_similarity: float = 0.0

    # Historical Context
    historical_scenarios: List['HistoricalScenario'] = None
    success_patterns: List[str] = None

    # Integration Status
    integration_errors: List[str] = None

    def __post_init__(self):
        if self.matched_patterns is None:
            self.matched_patterns = []
        if self.historical_scenarios is None:
            self.historical_scenarios = []
        if self.success_patterns is None:
            self.success_patterns = []
        if self.integration_errors is None:
            self.integration_errors = []
```

### CKSPattern
```python
@dataclass
class CKSPattern:
    """Individual CKS pattern match"""
    pattern_id: str
    pattern_type: str
    relevance_score: float
    confidence: float

    # Content
    content: str
    context: str

    # Metadata
    source_entries: List[str] = None
    usage_count: int = 0
    success_rate: float = 0.0

    def __post_init__(self):
        if self.source_entries is None:
            self.source_entries = []
```

### SessionContext
```python
@dataclass
class SessionContext:
    """Session management context for persistent NSE analysis"""
    session_id: str
    created_at: float
    last_activity: float

    # Persistent Context
    previous_recommendations: List['NSERecommendation'] = None
    user_preferences: Dict[str, Any] = None
    learned_patterns: List[str] = None

    # Project Context
    project_state: Dict[str, Any] = None
    development_history: List[str] = None

    def __post_init__(self):
        if self.previous_recommendations is None:
            self.previous_recommendations = []
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.learned_patterns is None:
            self.learned_patterns = []
        if self.project_state is None:
            self.project_state = {}
        if self.development_history is None:
            self.development_history = []
```

### NSERecommendation (Enhanced)
```python
@dataclass
class NSERecommendation:
    """Enhanced NSE recommendation result"""
    # Core Fields
    action: str
    description: str
    next_step: str
    priority: Priority
    confidence: float
    reasoning: str
    estimated_effort: str

    # Enhanced Context
    context_sources: List[str] = None
    enhancement_factors: List[str] = None

    # Dependencies
    dependencies: List[str] = None
    tags: List[str] = None

    # Metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.context_sources is None:
            self.context_sources = []
        if self.enhancement_factors is None:
            self.enhancement_factors = []
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
```

### PluginResult (Enhanced)
```python
@dataclass
class PluginResult:
    """Enhanced result from individual plugin processing"""
    plugin_name: str
    plugin_version: str
    success: bool
    message: str

    # Results
    data: Dict[str, Any] = None
    findings: List[str] = None
    recommendations: List[str] = None

    # Performance
    processing_time_ms: float
    memory_usage_mb: float = 0.0

    # Quality
    confidence: float = 0.0
    priority_boost: int = 0

    # Metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.findings is None:
            self.findings = []
        if self.recommendations is None:
            self.recommendations = []
        if self.metadata is None:
            self.metadata = {}
```

### CacheEntry
```python
@dataclass
class CacheEntry:
    """Cache entry for NSE analysis results"""
    key: str
    value: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = 0.0

    # Cache Metadata
    cache_type: str  # CONTEXT, RECOMMENDATION, PATTERN
    size_bytes: int = 0
    hit_rate: float = 0.0

    def __post_init__(self):
        if self.last_accessed == 0.0:
            self.last_accessed = time.time()
```

### Configuration
```python
@dataclass
class NSEConfig:
    """NSE system configuration"""
    # Performance Settings
    plugin_timeout_ms: int = 5000
    cache_ttl_seconds: int = 3600
    max_cache_size_mb: int = 100

    # Quality Settings
    confidence_threshold: float = 0.7
    min_plugin_confidence: float = 0.5

    # Integration Settings
    git_enabled: bool = True
    cks_enabled: bool = True
    session_enabled: bool = True

    # Plugin Settings
    plugin_priorities: Dict[str, int] = None
    enabled_plugins: List[str] = None

    # Output Settings
    verbose_output: bool = False
    show_plugin_details: bool = True

    def __post_init__(self):
        if self.plugin_priorities is None:
            self.plugin_priorities = {
                "SecurityPriorityPlugin": 1,
                "PerformancePlugin": 2,
                "CodeQualityPlugin": 3
            }
        if self.enabled_plugins is None:
            self.enabled_plugins = list(self.plugin_priorities.keys())
```

## Relationships

### Primary Relationships
1. **NSEContext** 1→1 **GitContext** - Each NSE analysis includes Git repository state
2. **NSEContext** 1→1 **CKSContext** - Each NSE analysis includes CKS integration results
3. **NSEContext** 1→1 **SessionContext** - Each NSE analysis can enhance session context
4. **GitContext** 1→N **GitCommit** - Repository contains multiple recent commits
5. **CKSContext** 1→N **CKSPattern** - Analysis finds multiple matching patterns
6. **SessionContext** 1→N **NSERecommendation** - Session tracks recommendation history

### Secondary Relationships
7. **NSERecommendation** N→N **PluginResult** - Recommendations enhanced by multiple plugins
8. **CKSPattern** N→1 **HistoricalScenario** - Patterns reference historical success cases
9. **CacheEntry** 1→1 **Any** - Cache can store any NSE data type

### Data Flow Relationships
10. **NSEConfig** 1→1 **NSEEngine** - Configuration controls engine behavior
11. **CacheEntry** N→1 **NSEContext** - Multiple cache entries support context analysis

## Data Integrity Rules

### Primary Keys and Uniqueness
- `session_id` must be unique across all sessions
- `commit_hash` must be unique within repository context
- `pattern_id` must be unique within CKS context
- `cache_key` must be unique within cache namespace

### Foreign Key Constraints
- `NSEContext.session_id` must reference valid `SessionContext.session_id`
- `GitCommit.repository_path` must match `GitContext.repository_path`
- `CKSPattern.pattern_id` must exist in CKS system

### Data Validation Rules
- `confidence` values must be between 0.0 and 1.0
- `priority` must be valid Priority enum value
- `processing_time_ms` must be non-negative
- `cache_ttl_seconds` must be positive

### Referential Integrity
- Session context must exist if `session_id` is provided
- Git context must be valid if `git_enabled` is true
- CKS context must indicate availability if `cks_enabled` is true

### Business Rules
- Recommendations with confidence < threshold should be filtered out
- Cache entries past TTL should be automatically expired
- Session inactivity should trigger cleanup after configured period
- Plugin execution should respect timeout constraints

## Validation Rules

### Input Validation
- All file paths must be valid and accessible
- Git repository must exist if git analysis is requested
- Action and description must not be empty strings
- Configuration values must be within acceptable ranges

### Output Validation
- Recommendations must have valid priority and confidence
- Plugin results must include processing time metrics
- Cache entries must have valid expiration times
- Context objects must include required metadata

### State Validation
- Session state must be consistent across accesses
- Git context must reflect current repository state
- CKS context must accurately represent system availability
- Cache consistency must be maintained across operations