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

### 5. Qwen (web, thinking mode) — EXCELLENT (best extraction reasoning)

Nonce: Q8B4F1D3. Full response: `P:/tmp/ensemble-qwen-response.txt`

- **Best closure extraction insight:** splits closures into two categories — pure functions → module-level, side-effecting closures → methods on a `TranscriptOrchestrator` class. Correctly identifies that the 3 side-effecting closures share state and should be grouped via `__init__` injection.
- `_finalize_success` for dedup (same convergence as all others)
- `TranscriptStage` Protocol with `is_applicable(ctx)` per stage
- Concrete stage classes with per-stage admission table (WhisperStage, NLMStage, GenericFallbackStage, ExpensiveFallbackStage)
- `FetchContext` frozen dataclass with `cheap_attempts`/`cost_budget_remaining` — makes expensive-gate logic explicit in the context, not scattered as booleans
- Summary design decisions table
- **Unique:** `TranscriptOrchestrator` class pattern for side-effecting closures (not free functions); reasoning: "Bundling them into an orchestrator class makes shared state explicit via __init__ injection, which kills the race condition on the global"
- **Weakness:** No characterization tests; code blocks partially fragmented in browser rendering

### 6. Grok (web) — VERY GOOD (best policy object design)

Nonce: G2F9E5A1. Full response: `P:/tmp/ensemble-grok-response.txt`

- Clean table for all 5 closure extractions with `StageTracker` protocol grouping for timing helpers
- `_finalize_success` for dedup
- `TranscriptStage` Protocol with `should_run`/`execute`
- Policy objects for special cases: `WhisperAdmissionPolicy`, `FallbackGatingPolicy`
- `PipelineContext` dataclass
- 5-category improvement summary (separation of concerns, testability, extensibility, concurrency safety, readability)
- **Unique:** `StageTracker` protocol for grouping timing helpers; named policy objects that read configuration flags (never mutable globals)
- **Weakness:** Less structural depth than Qwen/ChatGPT; no characterization tests; faster response (4s) but slightly shallower reasoning

### Duck.ai — BLOCKED (CAPTCHA)
Prompt submitted successfully (nonce D7A3F2E8) but DuckDuckGo served a CAPTCHA ("Select all squares containing a duck"). Response pending CAPTCHA resolution.

## Updated convergence analysis (6 models)

**All 6 models agree on:**
1. Extract all 5 closures (pure → module-level functions)
2. Replace `_WHISPER_ENABLED` global with an immutable context/config object
3. Unify success handling into one `_finalize_success` function
4. Use a strategy/protocol pattern for per-source behavior (`TranscriptStage` Protocol)
5. The orchestrator should be ~20-40 lines: validate → build context → iterate stages → finalize

**Updated unique contributions (6 models):**
- ChatGPT: `TranscriptCandidate` intermediate type (cleanest dedup mechanism)
- HuggingChat: characterization tests first + `SourceSpec` row hooks + `CircuitBreaker`
- Gemini: architecture diagram + `FallbackStage` Protocol with `can_execute()`
- Perplexity: `RuntimePolicy` dataclass + `build_fallback_plan()` declarative step builder
- Qwen: `TranscriptOrchestrator` class for side-effecting closures (shared-state reasoning)
- Grok: `StageTracker` protocol + named policy objects (`WhisperAdmissionPolicy`, `FallbackGatingPolicy`)

## Recommendation

**Implement a merged plan** combining:
- HuggingChat's Step 0 (characterization tests first) + `SourceSpec` hooks + `CircuitBreaker`
- ChatGPT's `TranscriptCandidate` intermediate type + `StageExecution` dataclass
- Gemini's `FallbackStage` Protocol with `can_execute()` + `execute()`
- Perplexity's `RuntimePolicy` frozen dataclass
- Qwen's `TranscriptOrchestrator` class for grouping side-effecting closures
- Grok's `StageTracker` protocol + policy objects

The convergence is extremely strong — all 6 models independently arrived at the same 5 structural changes. This is not model echo-chamber; it's a genuine design consensus across heterogeneous architectures.
