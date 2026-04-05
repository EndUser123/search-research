# Review Bundle: /s Skill (Strategy)

**Generated**: 2026-03-19
**Scope**: `P:\.claude\skills\s\`
**File Count**: ~90 files (60+ Python, 15+ Markdown, tests/)
**Execution Mode**: 4-agent parallel (comprehensive coverage)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: `/s` - Strategy (General-Purpose Strategic Thinking Engine)
- **Version**: 2.7.0 (2026-03-14)
- **Purpose**: Multi-persona brainstorming for strategic decisions, options analysis, and tradeoff evaluation
- **Location**: `P:\.claude\skills\s\`
- **Primary Language**: Python 3.12+

### Domain & Purpose
The `/s` skill is a general-purpose strategic thinking engine that applies multi-persona brainstorming to any situation requiring multi-perspective analysis. It uses a BrainstormOrchestrator to coordinate agents through a 3-phase workflow (Diverge → Discuss → Converge), producing ranked options with tradeoffs and decision memos.

**Key Use Cases:**
- Architecture decisions (multiple options)
- Risk assessment and pre-mortem analysis
- Product roadmap planning
- Technical debt prioritization
- Strategic alternatives exploration

### Scale Metrics
- **LOC**: ~15,000+ lines of Python code
- **Major Subsystems**: 7 (Agents, Convergence, Debate, Memory, Pheromone, Replay, Reasoning)
- **Deployment Scope**: Local CLI tool (Claude Code skill)
- **Change Frequency**: Active development (v2.7.0 released 2026-03-14)

### Your Environment
- **OS**: Windows 11
- **Shell**: bash (Unix-style paths)
- **Primary Languages**: Python 3.12+
- **Package Managers**: uv (Python dependency management)
- **Key Dependencies**:
  - `rich` (terminal UI)
  - `pydantic` (data validation)
  - `asyncio` (async/await patterns)
  - CSF LLM providers (`P:/__csf/src/llm/`)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                     /s SKILL ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  User Invocation                                              │
│  └─> scripts/run_heavy.py (CLI entry point)                 │
│      │                                                        │
│      ├─> Argument parsing (flags, personas, topic)          │
│      │                                                        │
│      ├─> Provider Health Gate (LLM availability check)      │
│      │                                                        │
│      └─> lib/orchestrator.py (BrainstormOrchestrator)      │
│          │                                                    │
│          ├─> Phase 1: DIVERGE (lib/agents/)                 │
│          │    ├─> InnovatorAgent (Cynefin framework)        │
│          │    ├─> PragmatistAgent (Inversion technique)     │
│          │    └─> FuturistAgent (Scenario planning)         │
│          │                                                    │
│          ├─> Phase 2: DISCUSS (lib/debate/)                │
│          │    ├─> DebateArena (adversarial debate)          │
│          │    └─> Voting (weighted consensus)               │
│          │                                                    │
│          ├─> Phase 3: CONVERGE (lib/convergence/)           │
│          │    ├─> Clustering (semantic grouping)            │
│          │    ├─> Deduplication (redundancy removal)        │
│          │    ├─> Synthesis (hybrid ideas)                 │
│          │    └─> Ranking (multi-criteria scoring)         │
│          │                                                    │
│          └─> OUTPUT (Rich tables, decision memo)            │
│                                                               │
│  ENHANCEMENTS (optional):                                    │
│  ├─> lib/pheromone/ (path learning from past sessions)     │
│  ├─> lib/replay/ (reuse successful ideas)                  │
│  ├─> lib/got/ (Graph-of-Thought node analysis)             │
│  └─> lib/tot/ (Tree-of-Thought branching)                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Core Systems

| System | Purpose | Location | Key Classes |
|--------|---------|----------|-------------|
| **Agents** | Persona-based idea generation | `lib/agents/` | Innovator, Pragmatist, Critic, Expert, Futurist, Synthesizer |
| **Orchestrator** | 3-phase workflow coordination | `lib/orchestrator.py` | BrainstormOrchestrator |
| **Convergence** | Clustering, synthesis, ranking | `lib/convergence/` | ConvergenceEngine, IdeaClustering, AdvancedRanker |
| **Debate** | Adversarial discussion framework | `lib/debate/` | DebateArena, Judge, Voting |
| **Memory** | Persistent session storage | `lib/memory/` | BrainstormMemory, CKS integration |
| **Scheduler** | Confidence-based turn-taking | `lib/scheduler.py` | ConfidenceScheduler, SchedulingStrategy |
| **Display** | Rich terminal output | `scripts/display.py` | LeaderboardRegistry, model listing |

### Main Entry Points

**CLI Entry**: `scripts/run_heavy.py`
- Parses command-line arguments (`--topic`, `--personas`, `--debate-mode`, etc.)
- Runs provider health gate
- Invokes BrainstormOrchestrator
- Formats output via Rich tables

**Orchestrator Entry**: `lib/orchestrator.py:BrainstormOrchestrator.brainstorm()`
- Main async method implementing 3-phase workflow
- Returns `BrainstormResult` with ideas, evaluations, metrics

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

**Normal Flow** (user runs `/s "topic"`):
1. Parse arguments and extract topic
2. Run provider health gate (check API availability)
3. Initialize BrainstormOrchestrator with config
4. **Phase 1 (Diverge)**: Spawn agents → parallel idea generation (600s timeout)
5. **Phase 2 (Discuss)**: Evaluate ideas → optional adversarial debate (600s timeout)
6. **Phase 3 (Converge)**: Cluster → deduplicate → synthesize → rank (180s timeout)
7. Output results: Rich tables + decision memo + next command hints

**With Recall** (`/s "topic" --recall`):
1. Query CHS/CKS for similar past sessions
2. Include top-ranked snippets as context
3. Proceed with normal flow using historical context

**With Debate** (`/s "topic" --debate-mode full`):
1. Phases 1 and 3 same as normal
2. Phase 2 runs 3-round adversarial debate:
   - Round 1: PRO arguments (affirmative)
   - Round 2: CON arguments (negative)
   - Round 3: REBUTTAL (counter-arguments)
3. Judge-weighted voting determines winner

### State Management

**Session State**: Stored in `BrainstormContext` object
- `topic`: The main problem/question
- `personas`: List of active agent personas
- `constraints`: Optional requirements list
- `goals`: Optional success criteria
- `fresh_mode`: Prevent anchoring bias (don't read existing docs)
- `metadata`: Additional context

**Idea State**: Tracked through 3-phase pipeline
- Generated (Diverge) → Evaluated (Discuss) → Ranked (Converge)
- Each idea has: `id`, `content`, `persona`, `score`, `reasoning_path`, `metadata`

**Persistent Storage**:
- **L1**: In-memory (session-scoped)
- **L2**: Disk cache (JSON files)
- **L3**: CKS (Constitutional Knowledge System) - optional integration

### Error Handling

**Fail-Open Policy**: Brainstorm continues even if some agents fail
- Agent failures → logged, empty ideas returned
- LLM timeouts → exponential backoff retry (3 attempts)
- Provider rate limits → provider excluded from round-robin rotation
- Debate failures → fallback to basic evaluation

**Retry Logic** (P0-6 fix):
- Max 3 retries with exponential backoff
- Initial backoff: 1.0s
- Max backoff: 30.0s
- Transient errors trigger retry (429, timeout, connection)
- Empty responses trigger retry (fast-fail to avoid timeout)

---

## 4. COMPONENT INVENTORY

### Core Logic Components

**`lib/orchestrator.py`** (1445 lines)
- **Responsibility**: Main workflow coordination
- **Inputs**: Topic, personas, constraints, goals
- **Outputs**: BrainstormResult (ideas + evaluations + metrics)
- **Key Methods**:
  - `brainstorm()`: Main 3-phase workflow
  - `_phase_diverge()`: Parallel idea generation
  - `_phase_discuss()`: Evaluation + debate
  - `_phase_converge()`: Clustering, synthesis, ranking
- **Known Limitations**:
  - Mock agents for testing (no API keys required)
  - Phase timeouts are generous (600s for diverge/discuss)

**`lib/agents/base.py`** (622 lines)
- **Responsibility**: Abstract base class for all brainstorming agents
- **Key Classes**: `Agent`, `AgentLLMClient`
- **Features**:
  - Prompt injection sanitization (P0-3 fix)
  - Exponential backoff retry (P0-6 fix)
  - Confidence computation for scheduling
  - Round-robin provider rotation
- **Known Limitations**:
  - Requires external LLM providers (groq, chutes, openrouter, etc.)
  - Fallback to groq if no providers detected

**`lib/convergence/engine.py`** (563 lines)
- **Responsibility**: Full convergence pipeline orchestrator
- **Key Classes**: `ConvergenceEngine`, `ConvergedIdea`, `ConvergenceConfig`
- **Features**:
  - Optional clustering (semantic grouping)
  - Optional deduplication (redundancy removal)
  - Optional synthesis (hybrid ideas from clusters)
  - Multi-criteria ranking (BALANCED strategy)
  - Diversity assurance (greedy selection)
- **Known Limitations**:
  - Clustering requires evaluations (can't cluster raw ideas)

**`lib/scheduler.py`** (328 lines)
- **Responsibility**: Confidence-based turn-taking for multi-agent coordination
- **Key Classes**: `ConfidenceScheduler`, `SchedulingStrategy`, `TurnOrder`
- **Strategies**:
  - `PRIORITY_BASED`: High confidence agents speak first
  - `ROUND_ROBIN`: Original order maintained
  - `WEIGHTED_RANDOM`: Probabilistic based on confidence
- **Known Limitations**:
  - Requires agents to implement `_compute_idea_confidence()`

**`lib/debate/arena.py`**
- **Responsibility**: Adversarial debate framework
- **Key Classes**: `DebateArena`, `DebateConfig`
- **Features**:
  - Multi-round debate (configurable, default 3 rounds)
  - Judge-weighted voting
  - Consensus calculation
  - Refinement of winning arguments

### Utilities/Helpers

**`lib/models.py`**
- Dataclasses: `Idea`, `Evaluation`, `BrainstormContext`, `BrainstormResult`
- Serialization: Pydantic-based `.model_dump()` for storage

**`lib/memory/brainstorm_memory.py`**
- 3-layer caching: L1 (memory), L2 (disk), L3 (CKS)
- Async storage operations
- Session persistence

**`lib/agents/*.py`** (Innovator, Pragmatist, Critic, Expert, Futurist, Synthesizer)
- Persona-specific prompts and thinking styles
- Each agent inherits from `Agent` base class
- Implements `generate_ideas()` and `evaluate_idea()`

### Configuration

**`scripts/run_heavy.py`**
- CLI argument parsing
- Provider health gate
- LLM config initialization
- Progress reporting

**`scripts/leaderboard_registry.py`**
- LMArena live data fetching (7-day cache)
- Provider model enumeration (12-hour cache)
- Model ID validation
- Cache conflict detection (>24h difference warning)

**`scripts/display.py`** (751 lines - recently enhanced)
- Rich table formatting
- Provider column width: 20 chars (was 15, P0 fix)
- Cache timestamp display with age indicators
- Model ID validation (tracks invalid models)
- API key availability filtering (shows "(needs key)")
- Async timeout protection (30-second provider fetch timeout)

### Infrastructure

**Testing** (`tests/`, `test_*.py` files)
- Unit tests for agents, convergence, scheduler
- Integration tests for 3-phase workflow
- Mock agent testing (no API keys required)
- Test isolation and cleanup patterns

**Documentation**
- `SKILL.md`: Complete skill definition (350 lines, v2.7.0)
- `references/strategy-advanced.md`: Advanced features (GoT, ToT, recall)
- `CHANGELOG.md`: Version history
- `HANDOFF.md`: Session handoff documentation

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Multi-Persona Divergence**: Different thinking styles (Innovator, Pragmatist, Critic) generate diverse options
2. **Adversarial Discussion**: Ideas are stress-tested through debate, not just accepted
3. **Convergence Quality**: Clustering, deduplication, synthesis ensure high-quality final set
4. **LLM-Generated Code**: All code is AI-generated under human direction (CSF philosophy)

### Technology Constraints

- **Python 3.12+**: Type hints required, `ruff` for linting, `pytest` for testing
- **Async/Await**: All I/O operations (LLM calls) must be async
- **Rich Terminal UI**: Output formatted with Rich library (tables, colors, progress)
- **No Team Coordination**: Solo-dev model (no multi-terminal locking required)

### Performance SLAs

- **Diverge Phase**: 600s timeout (10 minutes for parallel generation)
- **Discuss Phase**: 600s timeout (10 minutes for debate/evaluation)
- **Converge Phase**: 180s timeout (3 minutes for ranking)
- **LLM Call Timeout**: 30s for provider API fetch (display.py)

### Things That Must NOT Change

- **3-Phase Workflow**: Diverge → Discuss → Converge is core to the skill's value proposition
- **Multi-Persona Approach**: Single-persona brainstorming defeats the purpose
- **Director Model**: User provides direction, AI agents implement (CSF constitutional constraint)
- **No Background Services**: All execution is user-triggered, no autonomous daemons
- **Multi-Terminal Friendly**: Each `/s` invocation is independent (no shared state coordination needed)

---

## 6. KNOWN ISSUES

| Issue | Expected | Actual | Impact | Workaround |
|-------|----------|--------|-------|------------|
| **P0-1**: Provider column truncation | Full provider names visible | "openrouter" → "openrout…" | User can't identify provider | FIXED: width increased to 20 |
| **P0-2**: No cache freshness indicators | Know data age | No timestamps | User doesn't know if data is stale | FIXED: timestamps added |
| **P0-3**: Models displayed that don't exist | Only valid models | Invalid models in leaderboard | Confusion, broken workflows | FIXED: validation + warning |
| **P0-4**: API calls can hang indefinitely | Timeout protection | No timeout | User waits forever | FIXED: 30s timeout added |
| **P0-5**: Models shown without API key | "needs key" indicator | No indication | User tries unavailable models | FIXED: API key filtering |
| **P0-6**: Cache conflicts detected | Synced caches | Out-of-sync timestamps | Mismatched data | FIXED: warning >24h diff |
| **P1**: Ruff E402 errors (module level imports) | Clean lint | E402 on sys.path.insert | CI fails | FIXED: `# noqa: E402` added |
| **P1**: Ruff B007 errors (unused vars) | Clean lint | Loop vars unused | Code quality | FIXED: Changed to `_` |
| **P2**: Pyright warnings (none.lower) | Clean type check | Warning on None | Type safety | FIXED: null check added |

---

## 7. INTEGRATION POINTS

### Where New Solutions Can Plug In

**Custom Agents** (`lib/agents/`):
- Inherit from `Agent` base class
- Implement `generate_ideas()` and `evaluate_idea()`
- Optionally implement `_compute_idea_confidence()` for scheduling
- Register in `orchestrator.py:_spawn_agents()` agent_classes dict

**Custom Convergence Strategies** (`lib/convergence/ranking.py`):
- Add new `RankingStrategy` enum value
- Implement scoring logic in `AdvancedRanker`
- Configure in `ConvergenceConfig`

**Custom Memory Backends** (`lib/memory/`):
- Implement storage interface
- Add to `BrainstormMemory` layer system
- Configure in orchestrator initialization

**Provider Integration** (`P:/__csf/src/llm/providers/`):
- Add new provider to ProviderFactory
- Register in provider registry
- Configure API key in `APIKeyManager`

### Data Exchange Contracts

**Input to `/s`**:
```python
{
    "topic": str,           # Required: main problem/question
    "personas": list[str],  # Optional: ["innovator", "pragmatist", "critic"]
    "constraints": list[str], # Optional: requirements
    "goals": list[str],     # Optional: success criteria
    "fresh_mode": bool,     # Optional: prevent anchoring bias
    "metadata": dict        # Optional: additional context
}
```

**Output from `/s`**:
```python
{
    "session_id": str,
    "ideas": list[Idea],
    "evaluations": dict[str, Evaluation],
    "top_ideas": list[Idea],
    "metrics": {
        "diverge_duration": float,
        "discuss_duration": float,
        "converge_duration": float,
        "total_duration": float,
        "ideas_generated": int,
        "evaluations_performed": int,
        "debates_conducted": int,
        "agents_spawned": int,
        "errors": list[str]
    },
    "value_map": {
        "top_opportunities": list[dict],
        "expected_upside": str,
        "confidence": float
    },
    "decision_memo": {
        "decision": str,
        "alternatives": list[str],
        "why_not": dict[str, str],
        "risks": list[str],
        "rollback": str
    }
}
```

---

## 8. APPENDIX: FILE STRUCTURE

```
P:\.claude\skills\s\
├── SKILL.md                    # Main skill definition (350 lines)
├── HANDOFF.md                  # Session handoff documentation
├── plan.md                     # Pre-mortem improvements (6 priority items)
├── CHANGELOG.md                # Version history
├── IMPROVEMENTS.md             # Historical improvements log
│
├── scripts/                    # Entry points and utilities
│   ├── run_heavy.py           # CLI entry point (1452 lines)
│   ├── display.py             # Rich display, model listing (751 lines)
│   ├── leaderboard_registry.py # LMArena data, model validation
│   └── progress_reporter.py   # Progress tracking
│
├── lib/                        # Core implementation
│   ├── orchestrator.py        # Main workflow coordinator (1445 lines)
│   ├── models.py              # Dataclasses (Idea, Evaluation, etc.)
│   ├── scheduler.py           # Confidence-based turn-taking (328 lines)
│   │
│   ├── agents/                # Persona-based brainstorming agents
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract base class (622 lines)
│   │   ├── innovator.py       # Cynefin framework
│   │   ├── pragmatist.py      # Inversion technique
│   │   ├── critic.py          # Devil's advocate + Hanlon
│   │   ├── expert.py          # Chesterton's fence
│   │   ├── futurist.py        # Scenario planning
│   │   └── synthesizer.py     # Cross-framework integration
│   │
│   ├── convergence/           # Clustering, synthesis, ranking
│   │   ├── __init__.py
│   │   ├── engine.py          # ConvergenceEngine (563 lines)
│   │   ├── clustering.py      # Semantic clustering
│   │   ├── synthesizer.py     # Hybrid idea generation
│   │   ├── ranking.py         # Multi-criteria ranking
│   │   └── synthesizer.py     # Synthesis logic
│   │
│   ├── debate/                # Adversarial debate framework
│   │   ├── __init__.py
│   │   ├── arena.py           # DebateArena
│   │   ├── judge.py           # Judge scoring
│   │   ├── models.py          # Debate dataclasses
│   │   └── voting.py          # Consensus calculation
│   │
│   ├── memory/                # Persistent storage
│   │   ├── __init__.py
│   │   ├── brainstorm_memory.py # 3-layer cache
│   │   ├── cks_integration.py   # CKS L3 storage
│   │   ├── disk_cache.py        # L2 disk storage
│   │   └── session.py           # Session management
│   │
│   ├── pheromone/             # Path learning (experimental)
│   │   ├── __init__.py
│   │   ├── trail.py           # PheromoneTrail
│   │   └── models.py          # Pheromone dataclasses
│   │
│   ├── replay/               # Idea reuse (experimental)
│   │   ├── __init__.py
│   │   ├── buffer.py          # ReplayBuffer
│   │   └── models.py          # Replay dataclasses
│   │
│   ├── reasoning/            # Graph/Tree-of-Thought
│   │   ├── __init__.py
│   │   ├── base.py           # Base reasoning classes
│   │   ├── graph_of_thought.py
│   │   ├── tree_of_thought.py
│   │   └── chain_of_thought.py
│   │
│   ├── got/                  # Graph-of-Thought enhancement
│   │   ├── __init__.py
│   │   ├── planner.py        # GotPlanner (node extraction)
│   │   └── analyzer.py       # GotEdgeAnalyzer (relationship analysis)
│   │
│   ├── tot/                  # Tree-of-Thought enhancement
│   │   ├── __init__.py
│   │   └── generator.py      # BranchGenerator (branching scenarios)
│   │
│   └── utils/                # Helper utilities
│       ├── __init__.py
│       └── log_rotation.py   # Log file management
│
├── tests/                     # Test suite
│   ├── test_*.py             # Unit and integration tests
│   ├── test_integration_3phase_workflow.py
│   ├── test_advanced_features_integration.py
│   └── test_confidence_scheduler.py
│
└── references/               # Documentation
    └── strategy-advanced.md  # Advanced features guide
```

---

## SUMMARY

The `/s` skill is a sophisticated multi-agent brainstorming system implementing a 3-phase workflow (Diverge → Discuss → Converge) with ~15,000 lines of Python code across 90+ files. It provides strategic thinking capabilities through persona-based agents, adversarial debate, and advanced convergence algorithms. Recent enhancements (P0 fixes) have addressed reliability issues including display formatting, cache freshness, model validation, timeout protection, and API key filtering. The skill is production-ready with comprehensive testing, documentation, and CSF constitutional compliance.

**Key Strengths:**
- Multi-perspective analysis (6 personas)
- Adversarial debate framework (3-round PRO/CON/REBUTTAL)
- Advanced convergence (clustering, synthesis, ranking)
- Rich terminal UI with progress tracking
- Optional enhancements (GoT, ToT, pheromone trail, replay buffer)

**Known Limitations:**
- Requires external LLM providers (groq, chutes, openrouter, etc.)
- Long timeouts (10+ minutes for diverge/discuss phases)
- Complex architecture (may be overkill for simple decisions)
- Solo-dev model (no team collaboration features)

**Integration Points:**
- Custom agents via `Agent` base class
- Custom convergence strategies via `RankingStrategy`
- Custom memory backends via `BrainstormMemory`
- Provider integration via CSF LLM provider framework

---

## 9. IMPLEMENTATION DETAILS: RECENT P0 FIXES (display.py)

### P0-1: Provider Column Width Fix (Line 410)

**Problem**: Provider names were being truncated (e.g., "openrouter" → "openrout…")

**Fix**:
```python
# Before (line 410):
table.add_column("Provider", style="yellow", width=15)

# After (line 410):
table.add_column("Provider", style="yellow", width=20)  # Changed from width=15
```

### P0-2: Cache Timestamp Display (Lines 696-736)

**Problem**: Users couldn't tell how fresh the cached data was

**Fix**: Added `format_timestamp()` function with age indicators
```python
def format_timestamp(ts: float | None) -> str:
    """Format cache timestamp with human-readable age indicator.

    Args:
        ts: Unix timestamp or None

    Returns:
        Formatted string like "2026-03-19 14:30 (2h ago)"
    """
    if ts is None:
        return "Unknown"

    dt = datetime.fromtimestamp(ts)
    age_hours = (time.time() - ts) / 3600

    if age_hours < 1:
        age_str = f"{int(age_hours * 60)}m ago"
    elif age_hours < 24:
        age_str = f"{int(age_hours)}h ago"
    else:
        age_str = f"{int(age_hours / 24)}d ago"

    return f"{dt.strftime('%Y-%m-%d %H:%M')} ({age_str})"
```

**Usage in display**:
```python
console.print(f"[dim]Leaderboard: {format_timestamp(leaderboard_cache_time)}[/dim]")
console.print(f"[dim]Provider data: {format_timestamp(model_cache_time)}[/dim]")
```

### P0-3: Model ID Validation (Lines 562-619)

**Problem**: Models displayed in leaderboard might not exist in provider data

**Fix**: Track invalid models and show warning
```python
# Track models not in provider data
invalid_model_ids = []

for _, entries in leaderboard_data.items():
    for entry in entries:
        model_info = model_info_map.get(entry.model_id)
        if model_info:
            display_models_map[entry.model_id] = (provider, model_info)
        else:
            invalid_model_ids.append(entry.model_id)  # Track missing models

# Show warning if invalid models found
if invalid_model_ids:
    console.print(
        f"[yellow]Warning: {len(invalid_model_ids)} models from leaderboard not found in "
        f"provider data: {', '.join(invalid_model_ids[:5])}{'...' if len(invalid_model_ids) > 5 else ''}[/yellow]"
    )
```

### P0-4: Timeout Protection (Lines 204-216, 526-532)

**Problem**: API calls could hang indefinitely

**Fix**: Wrapped async operations in `asyncio.wait_for()` with 30-second timeout
```python
# Leaderboard fetch with timeout (lines 204-216)
try:
    await asyncio.wait_for(
        asyncio.gather(
            fetch_leaderboard_data(),
        ),
        timeout=30.0,  # 30 second timeout
    )
except asyncio.TimeoutError:
    console.print("[yellow]Warning: Leaderboard API fetch timed out after 30 seconds[/yellow]")
    # Use cached data if available
    ...

# Provider fetch with timeout (lines 526-532)
try:
    await asyncio.wait_for(
        asyncio.gather(
            fetch_provider("openrouter", enumerate_openrouter_models),
            fetch_provider("chutes", enumerate_chutes_models),
            fetch_provider("groq", enumerate_groq_models),
        ),
        timeout=30.0,  # 30 second timeout
    )
except asyncio.TimeoutError:
    console.print("[yellow]Warning: Provider API fetch timed out after 30 seconds[/yellow]")
```

### P0-5: API Key Filtering (Lines 635-641, 425-433)

**Problem**: Users might try to use models they don't have API keys for

**Fix**: Check APIKeyManager and show "(needs key)" indicator
```python
# Check available API keys (lines 635-641)
available_providers: set[str] = set()
api_manager = APIKeyManager()
for provider_name in ["openrouter", "chutes", "groq"]:
    config = api_manager.get_provider(provider_name)
    if config and config.api_key:
        available_providers.add(provider_name)

# Display with "(needs key)" indicator (lines 425-433)
if (
    available_providers is not None
    and api_provider
    and api_provider.lower() not in available_providers
):
    api_provider_display = f"{api_provider} (needs key)"
else:
    api_provider_display = api_provider or "Unknown"
```

### P0-6: Cache Conflict Detection (Lines 738-751)

**Problem**: Caches could become out of sync

**Fix**: Compare timestamps and show warning if one cache is >24h newer
```python
# Check for cache conflicts (lines 738-751)
if model_cache_time and leaderboard_cache_time:
    age_diff_hours = (model_cache_time - leaderboard_cache_time) / 3600

    if age_diff_hours > 24:  # Provider cache more than 1 day newer
        console.print(
            f"[yellow]Warning: Provider cache is {int(age_diff_hours)}h newer than "
            f"leaderboard cache. Data may be mismatched.[/yellow]"
        )
    elif age_diff_hours < -24:  # Leaderboard cache more than 1 day newer
        console.print(
            f"[yellow]Warning: Leaderboard cache is {int(-age_diff_hours)}h newer than "
            f"provider cache. Data may be mismatched.[/yellow]"
        )
```

### Cache Configuration

**File locations**:
- Leaderboard cache: `~/.claude/lma_arena_leaderboard.json` (7-day expiry)
- Provider cache: `~/.claude/llm-api-models.json` (12-hour expiry, shared with `/ai-api`)

**Cache expiry constants**:
```python
LEADERBOARD_CACHE_EXPIRY_DAYS = 7
MODELS_CACHE_EXPIRY_HOURS = 12
```

---

## 10. APPENDIX A: SKILL.MD (Full Skill Definition)

```markdown
---
id: s
name: s
description: Exploratory strategy with multi-persona brainstorming, GoT+ToT enhancement, and outcome scenario analysis
category: strategy
output_template: Template 1 (Strict Analysis Format)
extends:
  - PART C (Truthfulness) - Honest strategic assessment
  - PART P (Testing Workflow) - Options validation before implementation
triggers:
  - /s
  - "strategic analysis"
  - "brainstorm options"
  - "multi-option tradeoff"
aliases:
  - /s
suggest:
  - /r
  - /q
  - /nse
  - /arch
workflow_steps:
  - step_parse_args: Extract topic and flags from user prompt; handle --help/--list/unknown flags
  - step_resolve_context: Check if topic is a filesystem path; set --context-path if so
  - step_run_script: Execute run_heavy.py with resolved args
  - step_display_results: Present ranked ideas, decision memo, and next-step hints
---

# /s - Strategy

## Purpose

General-purpose strategic thinking engine for any situation requiring multi-perspective analysis.

- Uses real `BrainstormOrchestrator` execution
- Produces ranked options, tradeoffs, decision memo, and next-step hints
- **Multi-terminal friendly**: Works across concurrent sessions without coordination
- **No TTL, no stale data issues**: Generates fresh ideas each run, immune to context staleness
- Deterministic checks are intentionally out of scope; run `/r` first
- Owns exploratory cognitive checks from DUF decomposition (red-team, bias mirror, value-reveal)
- Uses multiple ideation techniques per persona:
  - **SCAMPER**: Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse
  - **Lateral Thinking**: Challenge assumptions, random entry points
  - **Six Thinking Hats**: Multiple perspectives (facts, feelings, caution, benefits, creativity, process)
  - **First Principles**: Break down to fundamental truths
  - **Reverse Engineering**: Work backwards from desired outcome

**Core principle**: `/s` applies fresh strategic thinking to the topic you provide. Use it to generate options, analyze tradeoffs, and explore strategic alternatives for any decision or plan.

## Supported Flags (show this when `--list` or `--help` is requested):
--recall                  Search previous brainstorm sessions on similar topics
--recall --persona NAME   Filter recall by persona (INNOVATOR/PRAGMATIST/CRITIC/EXPERT)
--recall --min-impact N   Filter recall to sessions with impact score ≥ N (0.0–1.0)
--context-path PATH       Prepend directory contents as project context
--output FORMAT           Output format: json | markdown | text (default: markdown)
--personas CSV            Comma-separated persona list to activate
--timeout N               Script timeout in seconds (default: 300)
--ideas N                 Target number of ideas to generate (default: 10)
--fresh-mode              Prevent anchoring bias by skipping existing docs
--local-llm-repetition N  Run brainstorm N times with different cognitive variations
--local-only              Skip external LLMs, use local agents only
--provider-tier TIERS     Filter providers by tier: T1,T2,T3 (default: all)
--debate-mode MODE        Adversarial debate: none | fast | full (default: none)
--enable-pheromone-trail  [EXPERIMENTAL] Learn from previous sessions
--enable-replay-buffer    [EXPERIMENTAL] Improved idea generation via replay
--quiet                   [OUTPUT] Suppress progress reporting (only show final results)

## Scope Boundary

- `/r`: deterministic remember + refine (what did we forget, predictable improvements, deterministic pre-mortem, plan validation)
- `/s`: exploratory multi-persona strategy (high-upside options, adversarial tradeoffs, and uncertainty handling)
```

*(Full SKILL.md is 350 lines; key sections shown above)*

---

## 11. APPENDIX B: CORE CODE EXAMPLES

### BrainstormOrchestrator Main Workflow (lib/orchestrator.py)

```python
async def brainstorm(
    self,
    prompt: str,
    personas: list[str] | None = None,
    timeout: float = 180.0,
    num_ideas: int = 10,
    constraints: list[str] | None = None,
    goals: list[str] | None = None,
    fresh_mode: bool = False,
    metadata: dict[str, Any] | None = None,
) -> BrainstormResult:
    """
    Execute a complete brainstorming session through all 3 phases.

    Returns:
        BrainstormResult with all generated ideas and evaluations
    """
    # Create context
    self.context = BrainstormContext(
        topic=prompt.strip(),
        num_ideas=num_ideas,
        personas=personas or ["innovator", "pragmatist", "critic"],
        constraints=constraints or [],
        goals=goals or [],
        timeout_seconds=int(timeout),
        fresh_mode=fresh_mode,
        metadata=metadata or {},
    )

    # Phase 1: Diverge
    ideas = await self._phase_diverge(
        context=self.context,
        timeout=min(self.DIVERGE_TIMEOUT, timeout * 0.6),
    )

    # Phase 2: Discuss
    evaluations = await self._phase_discuss(
        ideas=ideas,
        context=self.context,
        timeout=min(self.DISCUSS_TIMEOUT, timeout * 0.35),
    )

    # Phase 3: Converge
    await self._phase_converge(
        result=result,
        timeout=min(self.CONVERGE_TIMEOUT, timeout * 0.05),
    )

    return result
```

### Agent Base Class with Confidence Scheduling (lib/agents/base.py)

```python
class Agent(ABC):
    """Abstract base class for all brainstorming agents."""

    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        llm_config: LLMConfig | None = None,
    ):
        """Initialize the agent with LLM client."""
        self.name = name or self.__class__.__name__
        self.description = description or f"Agent implementing {self.name} persona"
        self.llm_client = AgentLLMClient(llm_config)
        self.system_prompt = self._get_default_system_prompt()

    @abstractmethod
    async def generate_ideas(self, context: BrainstormContext) -> list[Idea]:
        """Generate ideas based on the provided context."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement generate_ideas()")

    @abstractmethod
    async def evaluate_idea(self, idea: Idea) -> Evaluation:
        """Evaluate a single idea from the agent's perspective."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement evaluate_idea()")

    async def _compute_idea_confidence(self, idea: Idea) -> tuple[float, str]:
        """
        Compute agent's confidence in an idea for turn-based coordination.

        Returns:
            Tuple of (confidence: float, rationale: str)
        """
        # Prompt for confidence evaluation
        confidence_prompt = f"""Evaluate your confidence in this idea on a scale of 0.0 to 1.0.

IDEA:
Content: {idea.content}
Persona: {idea.persona}
Reasoning Path: {idea.reasoning_path if idea.reasoning_path else "Not provided"}

Rate your confidence based on:
1. SPECIFICITY: Is the idea concrete and actionable, or vague and abstract?
2. CONSISTENCE: Is the reasoning internally coherent and logical?
3. RELEVANCE: How directly does this address the core problem/topic?
4. UNIQUENESS: Does this offer a distinct perspective or is it redundant?

Respond in JSON format:
{{
  "confidence": <float between 0.0 and 1.0>,
  "rationale": "<brief explanation>"
}}
"""
        # ... (LLM call and parsing logic)
```

### Confidence Scheduler (lib/scheduler.py)

```python
class ConfidenceScheduler:
    """Confidence-based scheduler for multi-agent turn-taking."""

    async def schedule_turns(
        self,
        agents: list[Agent],
        context: BrainstormContext | None = None,
        idea_context: Idea | None = None,
    ) -> list[TurnOrder]:
        """
        Schedule turn order for agents based on their confidence scores.

        Returns:
            List of TurnOrder objects sorted by the selected strategy.
        """
        # Compute confidence scores for all agents
        agent_confidences: list[tuple[Agent, float]] = []
        for agent in agents:
            confidence = await self._compute_agent_confidence(agent, context, idea_context)
            agent_confidences.append((agent, confidence))

        # Filter agents below threshold
        filtered_agents = [
            (agent, conf)
            for agent, conf in agent_confidences
            if conf >= self.min_confidence_threshold
        ]

        # Schedule based on strategy
        if self.strategy == SchedulingStrategy.PRIORITY_BASED:
            return self._schedule_priority_based(filtered_agents)
        elif self.strategy == SchedulingStrategy.ROUND_ROBIN:
            return self._schedule_round_robin(filtered_agents)
        elif self.strategy == SchedulingStrategy.WEIGHTED_RANDOM:
            return self._schedule_weighted_random(filtered_agents)
```

### Convergence Engine Pipeline (lib/convergence/engine.py)

```python
async def converge(
    self,
    ideas: list[Idea],
    evaluations: dict[str, Evaluation] | None = None,
    config: ConvergenceConfig | None = None,
) -> tuple[list[ConvergedIdea], ConvergenceReport]:
    """
    Run the full convergence pipeline.

    Returns:
        Tuple of (converged_ideas, report)
    """
    # Phase 1: Clustering (optional)
    clusters = []
    if self.config.enable_clustering:
        clusters = await self.clustering.cluster_ideas(current_ideas, evaluations)

    # Phase 2: Deduplication (optional)
    if self.config.enable_deduplication and self.config.enable_clustering:
        current_ideas, deduplication_map = await self.clustering.deduplicate(
            ideas=current_ideas,
            clusters=clusters,
        )

    # Phase 3: Synthesis (optional)
    synthesized_ideas: list[SynthesizedIdea] = []
    if self.config.enable_synthesis and clusters:
        for cluster in clusters:
            if cluster.size >= 2:  # Only synthesize from clusters with 2+ ideas
                syn_from_cluster = await self.synthesizer.synthesize(
                    cluster=cluster,
                    max_results=self.config.max_synthesis_per_cluster,
                    evaluations=evaluations,
                )
                synthesized_ideas.extend(syn_from_cluster)

    # Phase 4: Ranking
    ranked = await self.ranker.rank(
        ideas=current_ideas,
        evaluations=evaluations,
        top_k=self.config.top_k * 2,
        criteria=RankingCriteria(strategy=self.config.ranking_strategy),
    )

    # Phase 5: Diversity Assurance
    final_ranked = self._ensure_diversity(
        ranked_ideas=ranked,
        top_k=self.config.top_k
    )

    return converged, report
```

---

## 12. FULL WINDOWS PATH

**Review Bundle Location**:
```
P:\__csf\.staging\review_bundle_s_20260319.md
```

**Alternative formats (same directory)**:
- `P:/__csf/.staging/review_bundle_s_20260319.md` (forward slashes)
- `\\wsl.localhost\P\__csf\.staging\review_bundle_s_20260319.md` (WSL access)
