# llm-models recommend Command - Complete ✅

**Date**: 2026-03-02
**Status**: ✅ **Integration Complete**

## What Was Added

Added a `recommend` subcommand to `/llm-models` that shows the same dual data source display format as `llm-api` and `llm-cli` skills.

## Usage

```bash
# Show model recommendation for a specific domain
llm-models recommend --domain code_generation --prompt "Write a binary search function"

# Available domains
llm-models recommend --domain {code_generation,code_review,architecture,testing,documentation,debugging}
```

## Sample Output

```
🔍 ============================================================================
MODEL SELECTION FOR: CODE_REVIEW
============================================================================

📡 INTERNET BENCHMARK DATA
------------------------------------------------------------------------------
  🥇 Primary: Qwen/Qwen3.5-397B-A17B-TEE
     Provider: Qwen
     Score: 650.0/100
     Reason: Score: 650.0/100

  🥈 Fallback: deepseek-ai/DeepSeek-V3
     Provider: deepseek-ai
     Score: 634.0/100

💻 LOCAL EVALUATION DATA
------------------------------------------------------------------------------
  ⚠️  No local evaluation data available
  💡 Run: llm-models evaluate --task code_review --quick

🎯 RECOMMENDATION
------------------------------------------------------------------------------
  ✅ Using BENCHMARK data: Qwen/Qwen3.5-397B-A17B-TEE
     Score: 650.0/100 (internet benchmarks)
     Source: HumanEval, MBPP, MMLU, SWE-bench

============================================================================
```

## Implementation Details

### File Modified

**`src/commands/llm_models.py`**

1. **`recommend_models()` function** (lines 511-545)
   - Maps domain string to Domain enum
   - Loads API keys for providers
   - Gets router with benchmark data
   - Calls `display_model_selection_with_both_sources()`

2. **CLI subcommand parser** (lines 603-606)
   ```python
   recommend_parser = subparsers.add_parser("recommend", help="Show model recommendation (benchmark + local data)")
   recommend_parser.add_argument("--domain", "-d", required=True, choices=[...])
   recommend_parser.add_argument("--prompt", "-p", default="", help="Optional prompt context")
   ```

3. **Command handler** (lines 647-651)
   ```python
   elif args.command == "recommend":
       asyncio.run(recommend_models(domain=args.domain, prompt=args.prompt))
   ```

### Key Design Decision

Used **local imports** inside `recommend_models()` to avoid linter conflicts:
```python
async def recommend_models(domain: str, prompt: str = "") -> None:
    # Import here to avoid linter conflicts
    from src.csf.llm_providers.dynamic_model_router import Domain as DomainEnum, get_router
    # ...
```

This prevents ruff from removing or reordering the imports.

## Benefits

1. **Consistency** - Same dual data source format across all LLM skills (llm-api, llm-cli, llm-models)
2. **Transparency** - See both internet benchmarks and your local evaluation results
3. **Smart preference** - Uses local data when available (more accurate for your environment)
4. **Helpful guidance** - Shows hints when local data is missing

## Integration Complete ✅

The `llm-models recommend` command is now fully integrated with the Dynamic Model Router's dual data source system, matching the functionality in llm-api and llm-cli skills.
