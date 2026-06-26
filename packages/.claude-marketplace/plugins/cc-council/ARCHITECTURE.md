# cc-council Architecture

## Overview

Local-first multi-LLM council system for Claude Code on Windows 11. Implements Karpathy-style deliberation with transport-agnostic design.

## Module Boundaries

```
cc-council/
├── .claude-plugin/plugin.json       # Plugin manifest
├── council_core/                   # Transport-agnostic core (NO Claude Code deps)
│   ├── contracts/                  # Data contracts and types
│   ├── engine/                     # Deliberation engine and state machine
│   ├── providers/                  # ai-api transport adapter
│   ├── persistence/                # SQLite state management
│   └── policy/                     # Consensus and gating policies
├── commands/                       # CLI commands (council-plan, etc.)
├── hooks/                          # Claude Code hook adapters
├── agents/                         # Prompt definitions for council roles
└── tests/                          # Test suite
```

**Boundary Enforcement:**
- `council_core/` imports NOTHING from `commands/`, `hooks/`, or `agents/`
- `council_core/` imports NOTHING from Claude Code hook APIs
- Provider adapters only import from `council_core/contracts/` and standard library
- Hook adapters ONLY call into `council_core/engine.py` public API

## Deliberation Protocol

### Stage 1: Gating/Classification
- Heuristic gating based on prompt complexity
- Keywords: "compare", "analyze", "evaluate", "review", "@council" prefix
- Length threshold: > 200 chars
- Result: `should_use_council: bool, reason: str`

### Stage 2: Independent Drafts
- 3 models generate independent responses
- Concurrent execution (max concurrency = provider limit)
- Anonymization: stored by model ID but presented as "Response A/B/C" during review
- Timeout: 30s per draft

### Stage 3: Anonymized Peer Review
- Single reviewer model (reuses first draft model)
- Reviews receive anonymized drafts
- Rankings: 1-5 scale per draft
- Critiques: brief text per draft
- Output: JSON with rankings and critiques

### Stage 4: Synthesis
- Chairman model (third model by default)
- Synthesis prompt includes:
  - Original prompt
  - All drafts
  - Review feedback
  - Contradiction flags
- Output: final answer + contradiction notes

### Stage 5: Consensus
- Calculate consensus ratio from review rankings
- Variance-based: variance 0 = 1.0 consensus, variance 4+ = 0.0
- Append to provenance metadata

## Persistence Model

### State Machine
```
IDLE → CLASSIFYING → DRAFTING → REVIEWING → SYNTHESIZING → COMPLETED
                                    ↓
                                 FAILED
                                    ↓
                                 ABORTED
```

### SQLite Schema
```sql
sessions: id, prompt, state, created_at, updated_at,
          gating_reason, failure_reason, total_rounds,
          models_used, duration_ms

drafts: id, session_id, model, role, content, metadata, created_at

reviews: id, session_id, model, role, rankings (JSON),
         critiques (JSON), created_at

synthesis: id, session_id, model, role, content,
           contradiction_notes (JSON), created_at
```

### Recovery
- On startup: scan for non-terminal sessions with `updated_at < now() - 5min`
- Mark as FAILED with reason "Session timeout - recovered as failed"
- Return original prompt to user on recovery

## Provider Model

### Interface (contracts/provider.py)
```python
class ProviderAdapter(ABC):
    async def health_check() -> ProviderHealth
    async def generate(model, prompt, max_tokens, timeout_ms, system_prompt) -> str
    async def get_model_capabilities(model) -> ModelCapability
    async def list_models() -> list[str]
    def get_concurrency_limit() -> int
```

### ai-api Adapter (providers/aiapi.py)
- Wraps cc-skills-ai-api transport layer
- Uses SDK clients for configured providers (z.ai, MiniMax, opencode-go, etc.)
- Resolves provider from model name via `_provider_hint_for_model()`
- Concurrency: 3 (configurable)
- Resource constraints modeled via capability flags

## Claude Code Integration

### Hook Adapter (hooks/user-prompt-submit.py)
- Event: `UserPromptSubmit`
- Entry: `data["prompt"]`, `data["session_id"]`
- Exit: JSON output with action ("replace" | "original")

### Command Entrypoints
- `/council-plan` - Manual council invocation
- `/council-review` - Inspect session metadata
- `/council-debug` - State diagnostics
- `/council-decide` - Direct single-model fallback

### Output Format
```json
{
  "action": "replace" | "original",
  "prompt": "...",
  "provenance": {
    "session_id": "...",
    "models_used": ["llama3:8b", "mistral:7b", "phi3:mini"],
    "consensus_ratio": 0.67,
    "total_rounds": 1,
    "duration_ms": 4500
  },
  "reason": "string (only on failure)"
}
```

## Known Limitations

1. **Single-round deliberation**: v1 implements one draft → review → synthesis cycle. Multi-round debate deferred.
2. **Simple contradiction detection**: Keyword-based only. LLM-based semantic contradiction detection in v2.
3. **Heuristic gating**: No learned classifier. Fixed keywords and length thresholds.
4. **Transport dependency**: Requires cc-skills-ai-api plugin for SDK access.
5. **Windows 11 only**: Path handling and process management untested on macOS/Linux.
6. **No distributed execution**: All models must be on localhost. No remote model support.
7. **Synthesis model selection**: Fixed to third model. No adaptive selection logic.
8. **Consensus metric**: Variance-based but not calibrated. May not correlate with actual answer quality.

## Why This Architecture

- **Transport-agnostic core**: Enables future provider additions without rewriting deliberation logic
- **SQLite persistence**: Durable state survives crashes, enables recovery and audit trails
- **Separate hook adapter**: Plugin usable via commands even if hooks disabled
- **Anonymized review**: Prevents model identity bias in peer feedback
- **Resource-aware provider**: Treats local models as resource-constrained, not quota-limited APIs
- **Minimal v1 scope**: Single-round, 3 models, simple consensus — buildable and testable in one iteration