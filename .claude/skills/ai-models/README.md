# LLM Models Command - Unified Model Intelligence

**Purpose**: Integrate three sources of model intelligence into one command-line tool.

## Installation

The alias `llm-models` is now available from the project root (`P:/__csf/`).

## Commands

### 1. `llm-models discover` - Provider API Discovery

Query provider APIs to see what models are available.

```bash
# All models from all providers
llm-models discover

# Specific provider
llm-models discover --provider openrouter

# Free models only
llm-models discover --free-only

# JSON output
llm-models discover --format json
```

**Providers queried**:
- OpenRouter (29+ free models, 100+ total)
- Chutes (363 models with free tier)
- Groq (free tier)
- Mistral

### 2. `llm-models research` - Internet Benchmarks

Search the web for model recommendations and benchmarks.

```bash
# General model research
llm-models research "best coding models 2025"

# Focus on specific area
llm-models research "fast reasoning models" --focus speed

# Use specific research mode
llm-models research "cost effective LLMs" --mode tavily

# GitHub research
llm-models research "model selection patterns" --mode github
```

**Research modes**: `auto`, `tavily`, `serper`, `perplexity`, `github`, `notebooklm`

**Focus areas**: `coding`, `reasoning`, `analysis`, `cost`, `speed`

### 3. `llm-models evaluate` - Run Model Tests

Evaluate models and save results to `judge_results.jsonl`.

```bash
# Quick coding evaluation
llm-models evaluate --task coding --quick

# Test specific models
llm-models evaluate --task reasoning --models qwen/gemma-2-9b groq/llama-3.3-70b

# Full evaluation
llm-models evaluate --task analysis
```

**Status**: ⚠️ Placeholder - evaluation harness not yet implemented.

**Manual format** for now:
```json
{
  "timestamp": "2026-03-01T...",
  "model": "gemma-2-9b",
  "provider": "qwen-cli",
  "task_category": "coding",
  "prompt": "Write a function to...",
  "response": "Here's the implementation...",
  "quality_score": {"overall": 8.5, "accuracy": 9.0, "relevance": 8.0},
  "latency_ms": 1234,
  "tokens": {"prompt": 100, "completion": 500, "total": 600},
  "success": true
}
```

### 4. `llm-models leaderboard` - Local Performance

Analyze your judge_results and show rankings.

```bash
# Overall leaderboard
llm-models leaderboard

# Filter by task
llm-models leaderboard --task coding

# Filter by provider
llm-models leaderboard --provider openrouter

# JSON export
llm-models leaderboard --format json > results.json
```

**Shows**:
- Overall rankings by combined score (quality + pass_rate + consistency + speed)
- Per-category breakdown (coding, reasoning, analysis, etc.)
- Routing recommendations (primary + fallbacks)
- Insights (most consistent, fastest quality, most versatile)

### 5. `llm-models compare` - Gap Analysis

Combine all three sources with intelligent gap detection.

```bash
# Full comparison
llm-models compare

# Focus on specific area
llm-models compare --focus coding

# JSON output
llm-models compare --format json > gaps.json
```

**Analysis includes**:
- Total available models from providers
- Previously tested models
- **Gap 1**: Available but untested models (prioritized by free → cheap)
- **Gap 2**: Tested but not available (legacy/removed models)
- Recommendations for next models to test

## Example Workflow

```bash
# 1. See what's available
llm-models discover --free-only

# 2. Research what's recommended
llm-models research "best free coding models" --focus coding

# 3. Compare with what you've tested
llm-models compare --focus coding

# 4. Test new models (manual until evaluate is implemented)
# [run models and save results to judge_results.jsonl]

# 5. Check updated rankings
llm-models leaderboard --task coding
```

## Data Locations

- **API Keys**: `P:/__csf/src/core/config/api_keys.py` (or environment variables)
- **Judge Results**: `P:/__csf/data/judge_results/judge_results.jsonl`
- **Leaderboard Config**: `P:/__csf/src/llm/providers/utils/judge_persistence.py`

## Integration with Existing Commands

- `llm-leaderboard` → Now aliased as `llm-models leaderboard`
- `/research` skill → Integrated via `llm-models research`
- `model_enumerator.py` → Integrated via `llm-models discover`

## Future Enhancements

- [ ] Auto-evaluation harness (discover → evaluate → leaderboard)
- [ ] Periodic benchmark comparison (your results vs internet benchmarks)
- [ ] Cost tracking (spend per provider/model)
- [ ] A/B testing framework (model A vs model B for same prompts)
- [ ] Intelligent routing (auto-select best model per task type)
