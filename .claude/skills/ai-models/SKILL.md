---
name: ai_models
description: Unified LLM model discovery, research, and performance analysis with gap detection
version: "1.0.0"
status: stable
category: ai
triggers:
  - /ai-models
  - ai-models
args:
  - discover: List available models from provider APIs
  - research: Search web for model benchmarks and recommendations
  - evaluate: Run model evaluation tests
  - leaderboard: Show local performance rankings from judge_results
  - compare: Combine all three with gap analysis
execution:
  directive: Execute ai-models command to discover, research, evaluate, or analyze LLM model performance
  default_args: "--help"
  examples:
    - "/ai-models discover --free-only"
    - "/ai-models research 'best coding models'"
    - "/ai-models evaluate --task coding"
    - "/ai-models leaderboard --task reasoning"
    - "/ai-models compare --focus coding"
do_not:
  - search for implementation files
  - describe what the skill does before executing
  - search for model enumerator code
---

## EXECUTE

**Run the llm-models command with the specified subcommand and arguments:**

```bash
cd P:/__csf && python src/commands/llm_models.py "$@"
```

**Or use the alias:**
```bash
llm-models $@
```

**What it does:**
- **`discover`** - Query provider APIs (OpenRouter, Chutes, Groq, Mistral) for available models
- **`research`** - Search web/internet for model benchmarks and recommendations via /research skill
- **`evaluate`** - Run model evaluation tests to populate judge_results.jsonl
- **`leaderboard`** - Analyze local judge_results for performance rankings and recommendations
- **`compare`** - Combine discovery + research + leaderboard with gap analysis

**When to use:**
- User asks: "What models are available from providers?" → use `discover`
- User asks: "What's the best model for X?" → use `research` or `compare --focus X`
- User asks: "How are our models performing?" → use `leaderboard`
- User asks: "What models should we test next?" → use `compare`
- User asks: "Show me the rankings" → use `leaderboard`

**Expected output:**
- **discover**: Table or JSON of available models with pricing, context length, free/paid status
- **research**: Web search results with model benchmarks, comparisons, and recommendations
- **evaluate**: Evaluation results saved to judge_results.jsonl
- **leaderboard**: Rankings by combined score, routing recommendations, insights
- **compare**: Gap analysis showing untested models to prioritize

**Common usage patterns:**
```bash
# See what's available
/ai-models discover --free-only

# Find gaps
/ai-models compare --focus coding

# Research recommendations
/ai-models research "best coding models 2025" --focus coding

# Check rankings
/ai-models leaderboard --task coding
```

---

## REFERENCE

<details>
<summary>Technical architecture (click to expand)</summary>

### Overview

Integrates three sources of LLM model intelligence:
1. **Provider API Discovery** - `src/llm/providers/utils/model_enumerator.py`
2. **Internet Research** - `/research` skill integration
3. **Local Performance Data** - `src/commands/llm_leaderboard.py` + `src/llm/providers/utils/judge_persistence.py`

### Source Code

**Main script:** `P:/__csf/src/commands/llm_models.py` (445 lines)

**Key functions:**
- `discover_models()` - Queries provider APIs for model listings
- `research_models()` - Invokes /research skill for benchmarks
- `evaluate_models()` - Placeholder for evaluation harness
- `show_leaderboard()` - Analyzes judge_results for rankings
- `compare_models()` - Gap analysis combining all sources

**Dependencies:**
- `src/core/config/api_keys.py` - API key management
- `src/llm/providers/utils/model_enumerator.py` - Model discovery utilities
- `src/llm/providers/utils/judge_persistence.py` - Judge results storage
- `src/commands/llm_leaderboard.py` - Ranking and recommendations

### Data Flow

```
User Request
    ↓
llm-models command
    ↓
┌───────────┬───────────┬───────────┬───────────┬───────────┐
│ discover  │ research  │ evaluate  │ leaderboard│ compare   │
└───────────┴───────────┴───────────┴───────────┴───────────┘
     ↓           ↓           ↓           ↓           ↓
 Provider    Internet   Tests      Local       Combined
 APIs       Research   Run        Data      Analysis
     ↓           ↓           ↓           ↓           ↓
 Available   External   New        Rankings   Gaps to
 Models    Benchmarks Results              Test
```

### Integration Points

- **`/research` skill** - Used by `research` subcommand for web searches
- **`llm-leaderboard`** - Reused as `leaderboard` subcommand
- **API Key Manager** - Provides credentials for provider API calls
- **Judge Persistence** - Reads/writes `P:/__csf/data/judge_results/judge_results.jsonl`

</details>
