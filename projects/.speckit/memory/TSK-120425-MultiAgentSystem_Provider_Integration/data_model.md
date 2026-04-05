# MultiAgentSystem Provider Integration Data Model

## Entity Definitions

### Provider
Represents an external AI provider that can be used for agent analysis.

```python
class Provider:
    id: str                    # Unique provider identifier (e.g., "openrouter", "gemini_cli")
    name: str                  # Human-readable provider name
    provider_type: ProviderType # Enum: CLI, REST_API, TASK_TOOL
    capabilities: List[str]     # List of capabilities (e.g., ["reasoning", "coding", "analysis"])
    models: List[Model]         # Available models for this provider
    status: ProviderStatus      # Enum: AVAILABLE, UNAVAILABLE, ERROR
    authentication: Authentication # Authentication configuration
    performance_metrics: ProviderMetrics # Performance tracking
    rate_limits: RateLimits     # Rate limiting configuration
    fallback_priority: int      # Priority in fallback chain (1=highest)
    health_check_url: str       # Optional health check endpoint
    config: ProviderConfig      # Provider-specific configuration
```

#### ProviderType Enum
```python
class ProviderType(Enum):
    CLI = "cli"                    # Command-line interface tools
    REST_API = "rest_api"          # REST API endpoints
    TASK_TOOL = "task_tool"        # Internal task tools
```

#### ProviderStatus Enum
```python
class ProviderStatus(Enum):
    AVAILABLE = "available"        # Provider is ready to use
    UNAVAILABLE = "unavailable"    # Provider not detected or configured
    ERROR = "error"                # Provider detected but has errors
    RATE_LIMITED = "rate_limited"  # Provider temporarily rate limited
    AUTHENTICATION_FAILED = "auth_failed"  # Authentication issues
```

### Model
Represents a specific AI model available through a provider.

```python
class Model:
    id: str                  # Model identifier (e.g., "minimax-m2-free")
    name: str                # Human-readable model name
    provider_id: str         # Foreign key to Provider
    model_type: ModelType    # Enum: REASONING, CODING, ANALYSIS, HYBRID
    capabilities: List[str]  # Specific model capabilities
    max_tokens: int          # Maximum token limit
    temperature_range: Tuple[float, float]  # Valid temperature range
    context_window: int      # Context window size
    cost_per_token: float    # Cost per token (if applicable)
    specialization: str       # Primary specialization area
    performance_score: float # Relative performance score
```

#### ModelType Enum
```python
class ModelType(Enum):
    REASONING = "reasoning"      # Advanced reasoning models
    CODING = "coding"           # Code generation and programming
    ANALYSIS = "analysis"       # Data analysis and pattern recognition
    HYBRID = "hybrid"           # Multi-purpose models
    CONVERSATION = "conversation"  # Conversational AI models
```

### Agent
Enhanced agent entity with multi-provider support.

```python
class Agent:
    id: str                          # Unique agent identifier
    role: AgentRole                   # Enum: ANALYST, SECURITY_EXPERT, CRITICAL_THINKER
    specialization: str                # Agent specialization description
    preferred_providers: List[str]    # Preferred providers (ordered by priority)
    available_providers: List[str]    # Actually available providers
    current_provider: str             # Currently selected provider
    status: AgentStatus               # Enum: IDLE, BUSY, ERROR, OFFLINE
    performance_metrics: AgentMetrics # Performance tracking per provider
    provider_preferences: Dict[str, ProviderPreference]  # Provider-specific settings
    fallback_chain: List[str]         # Provider fallback order
    last_analysis: AnalysisResult     # Most recent analysis result
```

#### AgentRole Enum
```python
class AgentRole(Enum):
    ANALYST = "analyst"
    SECURITY_EXPERT = "security_expert"
    CRITICAL_THINKER = "critical_thinker"
```

#### AgentStatus Enum
```python
class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
```

### AnalysisRequest
Represents a request for multi-agent analysis.

```python
class AnalysisRequest:
    id: str                      # Unique request identifier
    problem: str                 # Problem statement to analyze
    evidence: List[str]          # Evidence items for analysis
    requested_agents: List[str]  # Specific agents to use (optional)
    priority: RequestPriority    # Enum: LOW, MEDIUM, HIGH, CRITICAL
    analysis_type: AnalysisType  # Enum: SECURITY, PERFORMANCE, GENERAL
    max_duration: int            # Maximum analysis duration in seconds
    timeout_per_agent: int       # Timeout per individual agent
    context: Dict[str, Any]      # Additional context metadata
    created_at: datetime         # Request creation timestamp
    started_at: datetime         # Analysis start timestamp
    completed_at: datetime       # Analysis completion timestamp
```

#### RequestPriority Enum
```python
class RequestPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
```

#### AnalysisType Enum
```python
class AnalysisType(Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_REVIEW = "code_review"
    GENERAL = "general"
    COMPREHENSIVE = "comprehensive"
```

### AnalysisResult
Represents the result of an agent analysis.

```python
class AnalysisResult:
    id: str                      # Unique result identifier
    request_id: str              # Foreign key to AnalysisRequest
    agent_id: str                # Agent that performed analysis
    provider_id: str             # Provider used for analysis
    model_id: str                # Specific model used
    findings: List[str]          # Key findings from analysis
    confidence_level: float      # Confidence score (0.0-1.0)
    recommended_actions: List[str] # Recommended actions
    risk_assessment: str         # Risk level: LOW/MEDIUM/HIGH/CRITICAL
    evidence_quality_score: float # Quality of provided evidence (0.0-1.0)
    specialist_insights: str     # Domain-specific insights
    reasoning_summary: str       # Summary of analytical approach
    execution_time: float        # Time taken for analysis (seconds)
    token_usage: TokenUsage      # Token usage statistics
    success: bool                # Whether analysis completed successfully
    error_message: str           # Error message if analysis failed
    metadata: Dict[str, Any]     # Additional metadata
    timestamp: datetime          # Result timestamp
```

### TokenUsage
Tracks token usage for cost and rate limiting.

```python
class TokenUsage:
    input_tokens: int            # Tokens used in input
    output_tokens: int           # Tokens generated in output
    total_tokens: int            # Total tokens used
    estimated_cost: float        # Estimated cost in USD
    model_pricing: ModelPricing  # Pricing information used
```

## Relationships

### Primary Relationships

#### Provider ↔ Model (One-to-Many)
```python
# Provider has many Models
Provider.models: List[Model]  # One-to-many relationship
Model.provider_id: str       # Foreign key to Provider.id
```

#### Provider ↔ Agent (Many-to-Many)
```python
# Agents can use multiple providers
Agent.available_providers: List[str]  # Provider IDs agent can use
Agent.preferred_providers: List[str]  # Preferred provider order

# Provider capability matching
Provider.capabilities: List[str]  # What provider can do
Agent.role: AgentRole            # What agent needs
```

#### Agent ↔ AnalysisResult (One-to-Many)
```python
# Agent produces many analysis results
Agent.id: str                   # Agent identifier
AnalysisResult.agent_id: str    # Foreign key to Agent.id
```

#### AnalysisRequest ↔ AnalysisResult (One-to-Many)
```python
# One request can have multiple agent results
AnalysisRequest.id: str         # Request identifier
AnalysisResult.request_id: str   # Foreign key to AnalysisRequest.id
```

### Relationship Diagram
```
Provider (1) ←→ (N) Model
    ↑
    | (uses)
    N
    ↓
Agent (N) ←→ (N) AnalysisResult
    ↑
    | (produces)
    1
    ↓
AnalysisRequest (1) ←→ (N) AnalysisResult
```

## Data Integrity Rules

### Provider Integrity
1. **Provider Uniqueness**: Provider.id must be unique across system
2. **Model Validation**: All models must belong to a valid provider
3. **Authentication Security**: API keys must be encrypted at rest
4. **Health Status**: Provider status must be validated before use
5. **Capability Matching**: Provider capabilities must match agent requirements

### Agent Integrity
1. **Agent Uniqueness**: Agent.id must be unique
2. **Provider Availability**: Only available providers can be in fallback chain
3. **Role Validation**: Agent role must be from predefined AgentRole enum
4. **Fallback Chain**: Fallback chain must include at least Claude Code as final fallback
5. **Performance Tracking**: Performance metrics must be updated after each analysis

### Analysis Integrity
1. **Request Validation**: AnalysisRequest must have valid problem statement
2. **Result Consistency**: AnalysisResult must reference valid request and agent
3. **Confidence Range**: Confidence_level must be between 0.0 and 1.0
4. **Token Accuracy**: Token usage must accurately reflect actual API usage
5. **Timestamp Consistency**: All timestamps must be chronological and valid

### Referential Integrity
```sql
-- Foreign key constraints
ALTER TABLE Model ADD CONSTRAINT fk_model_provider
    FOREIGN KEY (provider_id) REFERENCES Provider(id);

ALTER TABLE AnalysisResult ADD CONSTRAINT fk_result_agent
    FOREIGN KEY (agent_id) REFERENCES Agent(id);

ALTER TABLE AnalysisResult ADD CONSTRAINT fk_result_request
    FOREIGN KEY (request_id) REFERENCES AnalysisRequest(id);

ALTER TABLE AnalysisResult ADD CONSTRAINT fk_result_provider
    FOREIGN KEY (provider_id) REFERENCES Provider(id);

ALTER TABLE AnalysisResult ADD CONSTRAINT fk_result_model
    FOREIGN KEY (model_id) REFERENCES Model(id);
```

## Validation Rules

### Provider Validation
```python
def validate_provider(provider: Provider) -> List[str]:
    errors = []

    # Required fields
    if not provider.id or not provider.id.isidentifier():
        errors.append("Provider ID must be a valid identifier")

    if not provider.name or len(provider.name.strip()) == 0:
        errors.append("Provider name is required")

    # Capability validation
    if not provider.capabilities:
        errors.append("Provider must have at least one capability")

    # Authentication validation
    if provider.provider_type == ProviderType.REST_API and not provider.authentication:
        errors.append("REST API providers require authentication configuration")

    # Fallback priority validation
    if provider.fallback_priority < 1:
        errors.append("Fallback priority must be >= 1")

    return errors
```

### Agent Validation
```python
def validate_agent(agent: Agent) -> List[str]:
    errors = []

    # Required fields
    if not agent.id or not agent.id.isidentifier():
        errors.append("Agent ID must be a valid identifier")

    if agent.role not in AgentRole:
        errors.append("Agent role must be a valid AgentRole enum value")

    # Provider validation
    if not agent.preferred_providers:
        errors.append("Agent must have at least one preferred provider")

    # Fallback chain validation
    claude_code_available = "claude_code" in agent.available_providers
    if not claude_code_available:
        errors.append("Agent fallback chain must include Claude Code")

    # Performance metrics validation
    for provider_id, metrics in agent.performance_metrics.items():
        if provider_id not in agent.available_providers:
            errors.append(f"Performance metrics for unavailable provider: {provider_id}")

    return errors
```

### AnalysisResult Validation
```python
def validate_analysis_result(result: AnalysisResult) -> List[str]:
    errors = []

    # Required fields
    if not result.agent_id or not result.request_id:
        errors.append("Agent ID and Request ID are required")

    # Confidence validation
    if not (0.0 <= result.confidence_level <= 1.0):
        errors.append("Confidence level must be between 0.0 and 1.0")

    # Evidence quality validation
    if not (0.0 <= result.evidence_quality_score <= 1.0):
        errors.append("Evidence quality score must be between 0.0 and 1.0")

    # Findings validation
    if not result.findings and result.success:
        errors.append("Successful analysis must have findings")

    # Token usage validation
    if result.token_usage:
        if result.token_usage.total_tokens != (result.token_usage.input_tokens + result.token_usage.output_tokens):
            errors.append("Token usage totals must be consistent")

    return errors
```

## Data Migration Rules

### Provider Migration
```python
# Migration from old system to new provider system
def migrate_providers():
    # Create default providers
    providers = [
        Provider(
            id="claude_code",
            name="Claude Code Task Tool",
            provider_type=ProviderType.TASK_TOOL,
            capabilities=["analysis", "reasoning", "coding"],
            fallback_priority=5  # Last resort
        ),
        Provider(
            id="gemini_cli",
            name="Gemini CLI",
            provider_type=ProviderType.CLI,
            capabilities=["large_context_analysis", "reasoning"],
            fallback_priority=2
        ),
        Provider(
            id="openrouter",
            name="OpenRouter",
            provider_type=ProviderType.REST_API,
            capabilities=["reasoning", "coding", "analysis"],
            fallback_priority=1  # First choice
        )
    ]

    # Migrate existing agent configurations
    for agent in existing_agents:
        agent.available_providers = detect_available_providers()
        agent.preferred_providers = create_default_fallback_chain()

    return providers
```

## Performance Considerations

### Indexing Strategy
```sql
-- Performance indexes
CREATE INDEX idx_provider_status ON Provider(status);
CREATE INDEX idx_provider_type ON Provider(provider_type);
CREATE INDEX idx_agent_status ON Agent(status);
CREATE INDEX idx_analysis_request_created ON AnalysisRequest(created_at);
CREATE INDEX idx_analysis_result_agent ON AnalysisResult(agent_id);
CREATE INDEX idx_analysis_result_request ON AnalysisResult(request_id);
```

### Data Partitioning
```sql
-- Partition large tables by date
CREATE TABLE AnalysisRequest_2025_01 PARTITION OF AnalysisRequest
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE AnalysisRequest_2025_02 PARTITION OF AnalysisRequest
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

### Caching Strategy
```python
# Cache frequently accessed data
@cache_result(ttl=300)  # 5 minutes
def get_available_providers() -> List[Provider]:
    return Provider.objects.filter(status=ProviderStatus.AVAILABLE).all()

@cache_result(ttl=600)  # 10 minutes
def get_provider_capabilities(provider_id: str) -> List[str]:
    provider = Provider.objects.get(id=provider_id)
    return provider.capabilities
```

This data model provides a comprehensive foundation for the MultiAgentSystem provider integration with proper entity relationships, integrity constraints, validation rules, and performance considerations.