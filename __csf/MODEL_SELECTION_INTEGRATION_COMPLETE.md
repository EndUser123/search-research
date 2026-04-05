# Local + Internet Benchmark Integration - Complete ✅

**Date**: 2026-03-02
**Status**: ✅ **Integration Complete**

## What Was Built

Integrated local evaluation results (`llm-models evaluate`) with the Dynamic Model Router used by `llm-api` and `llm-cli` skills.

## Features

### 1. Dual Data Source Display

When using `llm-api` or `llm-cli`, users will now see **BOTH**:

```
🔍 ===============================================================================
 MODEL SELECTION FOR: CODE_GENERATION
================================================================================

📡 INTERNET BENCHMARK DATA
--------------------------------------------------------------------------------
  🥇 Primary: qwen-coder-2.5
     Provider: qwen
     Score: 85.3/100
     Reason: Top performer on HumanEval, MBPP benchmarks

  🥈 Fallback: gemini-2.0-flash-exp
     Provider: gemini
     Score: 78.1/100

💻 LOCAL EVALUATION DATA
--------------------------------------------------------------------------------
  🥇 qwen-coder-2.5
     Score: 8.7/10
     Evaluations: 5
     Tier: T1 - Excellent

  🥈 gemini-2.0-flash-exp
     Score: 7.2/10
     Evaluations: 3
     Tier: T2 - Good

🎯 RECOMMENDATION
--------------------------------------------------------------------------------
  ✅ Using LOCAL data: qwen-coder-2.5
     Score: 8.7/10 (based on your evaluations)
     Source: Your local test results

  🔄 Internet benchmark would suggest: qwen-coder-2.5
```

### 2. Smart Data Preference

**Priority Order**:
1. **Local evaluation data** (if available) - Your actual test results on your hardware
2. **Internet benchmarks** (fallback) - HumanEval, MBPP, MMLU, SWE-bench

**Rationale**: Local data reflects YOUR environment, network, and configuration.

### 3. Transparency

Always shows **both** data sources so users can:
- See what the internet benchmarks suggest
- See what their local tests show
- Understand why a model was chosen
- Make informed decisions

## Implementation Details

### Files Modified

**`src/csf/llm_providers/dynamic_model_router.py`**

Added 3 new methods:

1. **`load_local_leaderboard(domain)`** - Loads local evaluation results
   - Queries `judge_persistence.get_leaderboard()`
   - Filters by task category
   - Returns ranked models with scores

2. **`get_recommendation_with_local_data(domain)`** - Combines both sources
   - Gets benchmark recommendation
   - Loads local leaderboard
   - Returns comparison dict

3. **`display_model_selection_with_both_sources(domain, prompt)`** - Display function
   - Shows internet benchmark data
   - Shows local evaluation data
   - Displays recommendation with reasoning
   - Used by `llm-api` and `llm-cli` skills

### Usage Example

```python
from src.csf.llm_providers.dynamic_model_router import DynamicModelRouter, Domain

router = DynamicModelRouter()
await router.refresh()

# Display both data sources
router.display_model_selection_with_both_sources(
    domain=Domain.CODE_GENERATION,
    prompt="Write a binary search function"
)
```

## Benefits

1. **Data-Driven Selection** - Use YOUR actual test results, not just internet benchmarks
2. **Environment-Specific** - Reflects YOUR hardware, network, and configuration
3. **Confidence Scores** - Know how well models perform on YOUR specific tasks
4. **Graceful Fallback** - Use benchmarks if no local data exists
5. **Transparency** - See both data sources and understand the choice

## llm-api Integration ✅ COMPLETE

**`llm-api` skill** (`P:/.claude/skills/llm-api/llm_api.py`) - INTEGRATED

**Location**: `_run_domain_review()` function (lines 714-729)

**Implementation**:
```python
# Display model selection with both benchmark and local data
router.display_model_selection_with_both_sources(domain_enum, query)

# Ask for user confirmation
response = input("Continue with recommended model? (Y/n): ").strip().lower()
if response and response != 'y':
    return {
        "error": "User cancelled",
        "findings": [],
        "mode": "domain",
        "domain": domain,
        "cancelled": True
    }
```

**When user runs llm-api with --domain flag**:
1. System fetches benchmark data from internet
2. System loads local evaluation results from llm-models leaderboard
3. Display shows BOTH data sources side-by-side
4. Recommendation prefers local data when available
5. User confirms before proceeding with model execution

## llm-cli Integration ✅ COMPLETE

**`llm-cli` skill** (`P:/.claude/skills/llm-cli/ask_cli.py`) - INTEGRATED

**Location**: `_run_domain_query()` function (lines 2487-2505)

**Implementation**:
```python
# Display model selection with both benchmark and local data
router.display_model_selection_with_both_sources(domain_enum, query)

# Ask for user confirmation
response = input("Continue with recommended models? (Y/n): ").strip().lower()
if response and response != 'y':
    return {
        "domain": domain,
        "error": "User cancelled",
        "results": [],
        "cancelled": True,
    }
```

**When user runs llm-cli with --domain flag**:
1. System fetches benchmark data from internet
2. System loads local evaluation results from llm-models leaderboard
3. Display shows BOTH data sources side-by-side
4. Recommendation prefers local data when available
5. User confirms before running top 2 models in parallel

**Additional cleanup**: Removed unused `ProviderFactory` import (line 87) flagged by linter.

## Summary

✅ **Dual data source system** - Shows both internet benchmarks and local evaluations
✅ **Smart preference** - Uses local data when available (more accurate for you)
✅ **Transparent display** - Users see both sources and understand the choice
✅ **Graceful fallback** - Uses internet benchmarks if no local data exists
✅ **llm-api integration complete** - Shows both data sources with confirmation
✅ **llm-cli integration complete** - Shows both data sources with confirmation

The integration is **complete for both llm-api and llm-cli** and ready for production use!
