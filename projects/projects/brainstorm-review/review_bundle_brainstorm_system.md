# Brainstorm System - Architectural Review Bundle

**Generated:** 2026-01-09
**Purpose:** External architectural review of the brainstorm system
**Scope:** Complete source code, dependencies, configuration, and integration points

---

## Table of Contents

1. [Execution Map](#execution-map)
2. [Entry Points](#entry-points)
3. [Core Components](#core-components)
4. [Source Code](#source-code)
5. [External Dependencies](#external-dependencies)
6. [Data Models](#data-models)
7. [Configuration](#configuration)
8. [Integration Points](#integration-points)

---

## Execution Map

### 3-Phase Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BRAINSTORM ORCHESTRATION                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   PHASE 1:       │    │   PHASE 2:       │    │   PHASE 3:       │
│   DIVERGE        │───▶│   DISCUSS        │───▶│   CONVERGE       │
│                  │    │                  │    │                  │
│  • Spawn Agents  │    │  • Debate Arena  │    │  • Clustering    │
│  • Generate Ideas│    │  • PRO/CON/REBUT │    │  • Deduplication │
│  • Parallel Exec │    │  • Judge Scoring │    │  • Synthesis     │
│  • (180s timeout)│    │  • Consensus     │    │  • Ranking       │
└──────────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Optional:        │    │ Optional:        │    │ ConvergenceEngine│
│ Pheromone Trail  │    │ Full Debate      │    │ • Diversity Assur │
│ Replay Buffer    │    │ (3-round format) │    │ • Report Gen     │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

### Agent System

```
┌─────────────────────────────────────────────────────────────────┐
│                         AGENT PERSONAS                          │
├─────────────────┬─────────────────┬─────────────────┬──────────┤
│    Innovator    │    Pragmatist   │      Critic     │  Expert  │
│                 │                 │                 │          │
│ • Novel ideas   │ • Practical     │ • Risk analysis │ • Domain │
│ • Creative      │ • Implementable │ • Flaw detect  │ • Evidenc │
│ • Breakthrough  │ • Execution     │ • Challenge     │ • Research│
│ • temp=0.9      │ • temp=0.5      │ • temp=0.5      │ • temp=0.6│
└─────────────────┴─────────────────┴─────────────────┴──────────┘
```

---

## Entry Points

### 1. Slash Command: `/llm-brainstorm`

**Location:** `P:/__csf.nip/src/commands/nip/brainstorm.md`

**Aliases:** `/brainstorm`, `/bs`, `/idea`, `/ideas`, `/llm-brainstorm`

**Usage Examples:**
```bash
/llm-brainstorm "How to improve remote team productivity"
/llm-brainstorm "Marketing strategy for SaaS" --personas innovator,critic
/llm-brainstorm "Ways to reduce technical debt" --ideas 15
```

**Execution Flow:**
1. Parse user input (topic, personas, num_ideas)
2. Infer topic from context if not provided
3. Validate orchestrator and API providers
4. Run brainstorm session with real AI (no mock mode)
5. Report results with top ideas and next actions
6. Track performance data automatically

### 2. Python API

**Location:** `P:/__csf.nip/src/brainstorm/orchestrator.py`

```python
from src.brainstorm.orchestrator import BrainstormOrchestrator
from src.brainstorm.llm import LLMConfig

config = LLMConfig(default_provider="groq")
orchestrator = BrainstormOrchestrator(llm_config=config)

result = await orchestrator.brainstorm(
    prompt="Optimize vector search backend",
    personas=["innovator", "pragmatist", "critic"],
    num_ideas=10,
    timeout=180.0
)
```

---

## Core Components

### Component Map

```
src/brainstorm/
├── orchestrator.py          # Main coordination (1044 lines)
├── models/
│   └── __init__.py          # Pydantic models (477 lines)
├── agents/
│   ├── base.py              # Abstract Agent (68 lines)
│   ├── innovator.py         # Creative persona (43 lines)
│   ├── pragmatist.py        # Practical persona (34 lines)
│   ├── critic.py            # Critical persona (34 lines)
│   ├── expert.py            # Domain expert (34 lines)
│   └── synthesizer.py       # Integration persona (34 lines)
├── debate/
│   ├── arena.py             # Debate orchestration (593 lines)
│   ├── models.py            # Debate data structures
│   ├── judge.py             # Judge evaluation
│   └── voting.py            # Consensus mechanisms
├── convergence/
│   ├── engine.py            # Pipeline orchestrator (563 lines)
│   ├── clustering.py        # Semantic clustering
│   ├── ranking.py           # Multi-criteria ranking
│   └── synthesizer.py       # Idea combination
├── memory/
│   ├── brainstorm_memory.py # 3-layer system (418 lines)
│   ├── session.py           # L1: Session cache
│   ├── disk_cache.py        # L2: Disk cache (72h TTL)
│   └── cks_integration.py    # L3: CKS semantic search
├── performance/
│   └── model_tracker.py     # SQLite tracking (420 lines)
├── llm/
│   └── llm_client.py        # DGATELLMClient (412 lines)
├── pheromone/
│   └── trail.py             # Path learning (optional)
└── replay/
    └── buffer.py            # Successful idea reuse (optional)
```

---

## Source Code

### 1. Orchestrator (`orchestrator.py`)

**Purpose:** Main coordination of 3-phase workflow

**Key Parameters:**
```python
def __init__(
    self,
    memory: BrainstormMemory | None = None,
    enable_full_debate: bool = True,
    llm_config=None,
    enable_performance_tracking: bool = True,
    enable_pheromone_trail: bool = False,      # OPTIONAL
    enable_replay_buffer: bool = False,        # OPTIONAL
):
```

**Phase Timeouts:**
- DIVERGE_TIMEOUT = 180.0s (idea generation is slow with real LLMs)
- DISCUSS_TIMEOUT = 240.0s (evaluation/debate)
- CONVERGE_TIMEOUT = 60.0s (ranking/filtering)

**Main Method:**
```python
async def brainstorm(
    self,
    prompt: str,
    personas: list[str] | None = None,
    timeout: float = 180.0,
    num_ideas: int = 10,
    constraints: list[str] | None = None,
    goals: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> BrainstormResult:
```

**Workflow:**
1. Create BrainstormContext from prompt
2. Spawn agents for requested personas
3. Get pheromone guidance (if enabled)
4. Get replay candidates (if enabled)
5. **Phase 1 (Diverge):** Parallel idea generation from all agents
6. **Phase 2 (Discuss):** Adversarial debate OR basic evaluation
7. **Phase 3 (Converge):** Clustering, deduplication, synthesis, ranking
8. Deposit pheromones from successful session
9. Store high-scoring ideas in replay buffer
10. Track model performance

**Agent Classes:**
```python
agent_classes = {
    "expert": ExpertAgent,
    "critic": CriticAgent,
    "innovator": InnovatorAgent,
    "pragmatist": PragmatistAgent,
    "synthesizer": SynthesizerAgent,
}
```

---

### 2. Agent System

**Base Agent (`agents/base.py`):**
```python
class Agent(ABC):
    def __init__(self, name: str, description: str, llm_config: LLMConfig):
        self.name = name
        self.llm_client = DGATELLMClient(llm_config)
        self.system_prompt = self._get_default_system_prompt()

    @abstractmethod
    async def generate_ideas(self, context: BrainstormContext) -> list[Idea]:
        raise NotImplementedError()

    @abstractmethod
    async def evaluate_idea(self, idea: Idea) -> Evaluation:
        raise NotImplementedError()
```

**Persona Agents:**

| Agent   | Temperature | Focus                  | Idea Count (per agent) |
|---------|-------------|------------------------|------------------------|
| Innovator | 0.9      | Creative, breakthrough | min(6, num_ideas // 3) |
| Pragmatist | 0.5     | Practical, execution   | min(6, num_ideas // 3) |
| Critic    | 0.5     | Risk-aware             | min(5, num_ideas // 3) |
| Expert    | 0.6     | Evidence-based         | min(5, num_ideas // 3) |
| Synthesizer | 0.7    | Integrated solutions   | min(5, num_ideas // 3) |

**Example: Innovator**
```python
class InnovatorAgent(Agent):
    def __init__(self, llm_config=None):
        super().__init__(
            name="Innovator",
            description="Creative thinker who generates novel ideas",
            llm_config=llm_config
        )

    def _get_default_system_prompt(self) -> str:
        return """You are a creative innovator who excels at thinking outside the box."""

    async def generate_ideas(self, context: BrainstormContext) -> list[Idea]:
        ideas = []
        num_ideas = min(6, max(4, context.num_ideas // 3))
        for i in range(num_ideas):
            prompt = self._build_innovator_prompt(context, i)
            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.9,  # High for creativity
                max_tokens=800,
                persona=self.name
            )
            idea = Idea(
                content=response.content,
                persona=self.name,
                reasoning_path=[f"Generated via {response.provider}"],
                score=75.0,
                metadata={"provider": response.provider}
            )
            ideas.append(idea)
        return ideas
```

---

### 3. Debate System (`debate/arena.py`)

**Purpose:** Adversarial debate for stress-testing ideas

**3-Round Format:**
1. **Round 1 (PRO):** Expert/Pragmatist support the idea
2. **Round 2 (CON):** Critic challenges the idea
3. **Round 3 (REBUTTAL):** Innovator/Synthesizer counter-arguments

**Configuration:**
```python
@dataclass
class DebateConfig:
    num_rounds: int = 3
    round_timeout: float = 30.0
    judge_weight: float = 0.6      # Judge score influence
    consensus_weight: float = 0.4  # Agent voting influence
    voting_strategy: str = "weighted"  # majority, weighted, unanimous, borda
    enable_refinement: bool = True
    quality_threshold: float = 60.0
```

**Final Score Calculation:**
```python
final_score = judge_score * judge_weight + consensus_score * consensus_weight
```

**Agent Selection by Round:**
- PRO: Expert, Pragmatist
- CON: Critic
- REBUTTAL: Innovator, Synthesizer

---

### 4. Convergence Engine (`convergence/engine.py`)

**Purpose:** Advanced pipeline for clustering, deduplication, synthesis, and ranking

**Pipeline Steps:**
```python
async def converge(
    self,
    ideas: list[Idea],
    evaluations: dict[str, Evaluation] | None = None,
    config: ConvergenceConfig | None = None,
) -> tuple[list[ConvergedIdea], ConvergenceReport]:
```

**Configuration:**
```python
@dataclass
class ConvergenceConfig:
    enable_clustering: bool = True
    enable_deduplication: bool = True
    enable_synthesis: bool = True
    similarity_threshold: float = 0.75      # For clustering
    complementarity_threshold: float = 0.65 # For synthesis
    ranking_strategy: RankingStrategy = BALANCED
    top_k: int = 10
    diversity_threshold: float = 0.3
```

**Phases:**
1. **Clustering:** Group similar ideas (semantic similarity)
2. **Deduplication:** Remove redundant ideas within clusters
3. **Synthesis:** Create hybrid ideas from complementary clusters
4. **Ranking:** Multi-criteria ranking (novelty, feasibility, impact)
5. **Diversity Assurance:** Ensure final set has diverse perspectives
6. **Reporting:** Generate comprehensive convergence report

**Ranking Strategies:**
- WEIGHTED_SUM: Linear combination of criteria
- MULTIPLICATIVE: Product of criteria (penalizes low scores)
- PARETO: Pareto frontier identification
- DIVERSITY_FIRST: Prioritize diverse perspectives
- BALANCED: Combined quality + diversity

---

### 5. Memory System (`memory/brainstorm_memory.py`)

**Purpose:** Three-layer memory with automatic layer traversal

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    THREE-LAYER MEMORY                        │
├─────────────┬─────────────────┬─────────────────────────────┤
│ L1: SESSION │ L2: DISK CACHE  │ L3: CKS INTEGRATION         │
│             │                 │                             │
│ • Fast      │ • Persistent     │ • Semantic search           │
│ • Temporary │ • 72h TTL        │ • Vector embeddings         │
│ • In-memory │ • SQLite         │ • CKS backend               │
└─────────────┴─────────────────┴─────────────────────────────┘
```

**Layer Behavior:**
- **L1 (Session):** Fast in-memory cache, cleared on session end
- **L2 (Disk):** Persistent cache with 72h TTL, SQLite storage
- **L3 (CKS):** Long-term storage with semantic search capability

**Write Pattern:**
```python
async def store(self, key: str, value: Any, layer: int = 1, propagate: bool = True):
    # Store in target layer
    # If propagate=True, cascade to higher layers
```

**Read Pattern:**
```python
async def retrieve(self, key: str) -> Any | None:
    # Check L1 → L2 → L3 in order
    # Promote found values to higher layers
```

---

### 6. LLM Client (`llm/llm_client.py`)

**Purpose:** Direct integration with llm_providers

**Key Features:**
- Direct provider access (no zen_integration layer for LLM calls)
- Automatic retry with exponential backoff
- Cost tracking and rate limiting
- API key management via zen_integration APIKeyManager

**Configuration:**
```python
@dataclass
class LLMConfig:
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    cost_tracking_enabled: bool = True
    rate_limit_requests: int | None = None
    default_provider: str = "groq"
```

**API Key Priority:**
1. zen_integration APIKeyManager (preferred)
2. Environment variables (fallback)

**Provider Environment Variables:**
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `DASHSCOPE_API_KEY` (Qwen)
- `OPENROUTER_API_KEY`
- `ZAI_CLAUDE_API_KEY`
- `ANTHROPIC_API_KEY`

---

### 7. Performance Tracking (`performance/model_tracker.py`)

**Purpose:** Track model performance for intelligent model selection

**Database:** SQLite at `P:/__csf.nip/data/model_performance.db`

**Schema:**
```sql
CREATE TABLE model_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    provider TEXT NOT NULL,
    session_id TEXT NOT NULL,
    persona TEXT NOT NULL,
    ideas_generated INTEGER DEFAULT 0,
    avg_idea_score REAL DEFAULT 0.0,
    top_idea_score REAL DEFAULT 0.0,
    avg_latency_ms REAL DEFAULT 0.0,
    total_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    user_satisfaction REAL,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    task_category TEXT,
    quality_rating REAL DEFAULT 0.0
)
```

**Metrics Tracked:**
- Ideas generated per session
- Average idea quality score
- Top idea score
- Average latency
- Total tokens used
- Total cost in USD
- User satisfaction (if rated)
- Task category (for category-specific stats)

**Query Methods:**
- `get_model_stats(model_name, min_sessions=3)` - Aggregated stats per model
- `get_top_models(provider, limit)` - Top performing models
- `get_stats_by_category(category, limit)` - Performance by task type

---

## External Dependencies

### Required Python Packages

```python
# Data validation
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# Async
import asyncio

# Database
import sqlite3

# Path handling
from pathlib import Path
```

### Internal Dependencies

```python
# LLM Providers
from llm_providers import ProviderFactory, ProviderConfig
from llm_providers.unified_manager import UnifiedProviderManager

# API Key Management
from zen_integration.api_key_manager import APIKeyManager

# CKS Integration (L3 memory)
from src.brainstorm.memory.cks_integration import CKSLayer
```

### Environment Variables Required

```bash
# Primary LLM providers
GROQ_API_KEY=sk-...
GEMINI_API_KEY=...
OPENROUTER_API_KEY=sk-...

# Optional providers
ANTHROPIC_API_KEY=sk-...
DASHSCOPE_API_KEY=...
ZAI_CLAUDE_API_KEY=...
```

---

## Data Models

### Core Models (`models/__init__.py`)

**Idea:**
```python
class Idea(BaseModel):
    id: str  # UUID4
    content: str  # min_length=10
    persona: str
    reasoning_path: List[str]
    score: float  # 0-100
    next_action: Optional[str]
    estimated_minutes: int  # 5-480
    metadata: Dict[str, Any]
```

**Evaluation:**
```python
class Evaluation(BaseModel):
    idea_id: str
    novelty_score: float  # 0-100
    feasibility_score: float  # 0-100
    impact_score: float  # 0-100
    overall_score: float  # 0-100 (weighted combination)
    arguments_pro: List[str]
    arguments_con: List[str]
    evaluator: Optional[str]
```

**BrainstormContext:**
```python
class BrainstormContext(BaseModel):
    topic: str  # min_length=5
    num_ideas: int  # 1-100, default=10
    personas: List[str]  # default=["innovator", "pragmatist", "critic"]
    constraints: List[str]
    goals: List[str]
    timeout_seconds: Optional[int]
    metadata: Dict[str, Any]
```

**BrainstormResult:**
```python
class BrainstormResult(BaseModel):
    ideas: List[Idea]
    evaluations: Dict[str, Evaluation]
    context: BrainstormContext
    session_id: str  # UUID4
    timestamp: datetime
    metadata: Dict[str, Any]
```

---

## Configuration

### Provider Configuration

**Location:** `P:/__csf.nip/config/zen/providers.yaml`

**Required Structure:**
```yaml
providers:
  groq:
    enabled: true
    api_key: "${GROQ_API_KEY}"
    model_metadata:
      llama-3.3-70b-versatile:
        cost_per_1k_tokens: 0.00059
        context_length: 128000
        avg_latency_ms: 500
```

### Orchestrator Configuration

**Defaults:**
```python
DIVERGE_TIMEOUT = 180.0  # 3 minutes
DISCUSS_TIMEOUT = 240.0  # 4 minutes
CONVERGE_TIMEOUT = 60.0  # 1 minute
```

**Optional Features (default: disabled):**
- `enable_pheromone_trail`: Path learning from successful sessions
- `enable_replay_buffer`: Reuse of high-scoring ideas
- `enable_performance_tracking`: Model performance tracking (enabled by default in real mode)

---

## Integration Points

### 1. Zen Integration

**API Key Management:**
```python
from zen_integration.api_key_manager import APIKeyManager

api_manager = APIKeyManager()
provider = api_manager.providers["groq"]
api_key = provider.api_key
model_metadata = provider.model_metadata
```

### 2. CKS (Constitutional Knowledge System)

**L3 Memory Integration:**
```python
from src.brainstorm.memory.cks_integration import CKSLayer

l3 = CKSLayer(fallback_to_disk=True)
await l3.store(key, value)
results = await l3.find_similar(query, top_k=5)
```

### 3. Model Performance Database

**Location:** `P:/__csf.nip/data/model_performance.db`

**Usage:**
```python
tracker = ModelPerformanceTracker()
await tracker.record_session(metrics)
stats = tracker.get_model_stats(model_name="llama-3.3-70b")
```

---

## Key Design Decisions

### 1. Why Pheromone Trail is Optional

The pheromone trail feature is experimental meta-learning that requires multiple sessions to build useful data. The core workflow (Diverge → Discuss → Converge) works without it. Pheromone trails provide:
- Suggested personas based on historical success
- Exploration guidance for new topics
- Path learning from previous high-quality sessions

### 2. Why Replay Buffer is Optional

The replay buffer allows reusing successful ideas from previous sessions. It requires:
- Multiple sessions to populate
- Semantic similarity matching
- Effectiveness tracking

For single sessions or new topics, the replay buffer adds overhead without benefit.

### 3. Real AI Only (No Mock Mode)

The brainstorm system requires real LLM providers:
- Mock mode is disabled by default
- `llm_providers` module is required
- API keys must be configured
- Performance tracking only works with real models

### 4. Three-Layer Memory

The memory system provides:
- **L1 (Session):** Fast cache for current session only
- **L2 (Disk):** 72h TTL for cross-session persistence
- **L3 (CKS):** Long-term semantic search capability

Write-through caching ensures data propagates to higher layers automatically.

---

## Testing Notes

### Unit Test Locations

- `tests/test_brainstorm_orchestrator.py`
- `tests/test_debate_arena.py`
- `tests/test_convergence_engine.py`
- `tests/test_memory_layers.py`
- `tests/test_model_tracker.py`

### Test Database

Uses temporary databases for testing:
- `:memory:` for SQLite tests
- Temp directories for disk cache tests

---

## Performance Characteristics

### Expected Latency

| Phase | Duration | Notes |
|-------|----------|-------|
| Diverge | 60-180s | Depends on num_ideas and agent count |
| Discuss | 30-120s | Full debate vs basic evaluation |
| Converge | 5-30s | Clustering and ranking are fast |
| **Total** | **95-330s** | **~1.5-5.5 minutes** |

### Cost Estimates

Assuming Groq Llama 3.3 70B ($0.00059/1K tokens):
- 10 ideas × 3 personas = 30 LLM calls
- ~500 tokens/call × 30 = 15,000 tokens
- Estimated cost: **~$0.01 per session**

---

## End of Review Bundle

**For questions or clarification, contact the development team.**

**Source Repository:** `P:/__csf.nip/src/brainstorm/`
