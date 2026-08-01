# Ensemble Refactoring Test — Results & Ranking

## Prompt
Design a refactoring PLAN for `fetch_transcript_chain` (200+ lines, 5 nested closures, mutable global, duplicated success handling, mixed concerns, 3 inline special cases).

## Rankings

### 1. ChatGPT — EXCELLENT (best overall)
- Extracts all 5 closures to module level with full typed signatures
- Introduces `TranscriptCandidate` intermediate type to eliminate duplication
- Single `finalize_successful_transcript()` owns translation + caching + result building
- `StageExecution` frozen dataclass replaces _stage_started/_stage_completed
- `FailureReason` enum, `TranscriptStage` type, `TranscriptFetchContext`
- Each extraction has explicit "Why this helps" rationale
- Cleanest type design — every extraction has explicit purpose

### 2. HuggingChat (Kimi K3) — EXCELLENT (best structural insight)
- **Characterization tests first** (Step 0) — pin behavior before touching anything
- `SourceSpec` row concept: each source has `fetch` + `admission` + `normalize` + `on_failure` hooks
- Special cases become per-row policy instead of `if source ==` branches
- `_WHISPER_ENABLED` splits into config read + injected `CircuitBreaker` class
- Mechanical extraction rule: "captures → parameters, mutations → return values"
- Protocols: `AttemptLogger`, `TranscriptCache`, `RateLimiter` — all injectable
- **Best structural insight:** "NLM duplication dies structurally, not textually" — once NLM is a normal chain member, the duplication disappears automatically
- Lasting discipline articulated: "new source-specific `if` → new `SourceSpec` hook"

### 3. Gemini — VERY GOOD (best architecture diagram)
- Orchestrator Pattern with ASCII flowchart showing the split
- `ExecutionContext` frozen dataclass replaces mutable global
- `FallbackStage` Protocol with `can_execute()` + `execute()` — strategy pattern
- `process_and_cache_success()` unifies success handling
- Stage guard table: maps old inline conditions to new `can_execute()` guards
- Clean separation: pure utilities, unified success handler, strategy handlers
- Slightly less detailed than ChatGPT/HuggingChat on the "why" per extraction

### 4. Perplexity — VERY GOOD (most cited sources, best dataclass design)
- `TranscriptRequest`, `RuntimePolicy`, `StepContext` frozen dataclasses
- `TranscriptProvider` Protocol with `fetch()` method
- `build_fallback_plan()` returns tuple of steps (declarative)
- `normalize_provider_success()` + `to_transcript_result()` split normalization from result building
- Cited GitHub, StackOverflow, DataCamp, YouTube sources
- `RuntimePolicy` dataclass is the cleanest expression of "replace mutable global with frozen config"
- Slightly verbose — more code blocks than necessary

## Convergence analysis

**All 4 models agree on:**
1. Extract all 5 closures to module level
2. Replace `_WHISPER_ENABLED` global with an immutable context/config object
3. Unify success handling into one function (eliminates the ~20 line duplication)
4. Use a strategy/protocol pattern for per-source behavior (eliminates inline `if source ==`)
5. The orchestrator should be ~30-40 lines: validate → build context → iterate stages → finalize

**Unique contributions:**
- ChatGPT: `TranscriptCandidate` intermediate type (cleanest dedup mechanism)
- HuggingChat: characterization tests first + `SourceSpec` row hooks + `CircuitBreaker`
- Gemini: architecture diagram + `FallbackStage` Protocol with `can_execute()`
- Perplexity: `RuntimePolicy` dataclass + `build_fallback_plan()` declarative step builder

## Recommendation

**Implement a merged plan** combining:
- HuggingChat's Step 0 (characterization tests first) + `SourceSpec` hooks + `CircuitBreaker`
- ChatGPT's `TranscriptCandidate` intermediate type + `StageExecution` dataclass
- Gemini's `FallbackStage` Protocol with `can_execute()` + `execute()`
- Perplexity's `RuntimePolicy` frozen dataclass

The convergence is strong — all 4 models independently arrived at the same 5 structural changes. This is not model echo-chamber; it's a genuine design consensus.
