---
title: "Design a refactoring PLAN for a 200+ line Python function `fetch_transcript_chain(video_id, config, *, skip_notebooklm=F"
date: "2026-08-01"
mode: "COPILOT"
uuid: "49e824c2-ca33-4178-9848-0ca62e5a7947"
entry_count: 1
---

## Human

Design a refactoring PLAN for a 200+ line Python function `fetch_transcript_chain(video_id, config, *, skip_notebooklm=False, admission_metadata=None) -> TranscriptResult` with these problems: (1) 5 nested closures trap pure logic and side-effecting functions inside the orchestrator, (2) mutable global _WHISPER_ENABLED read/written inside the loop body, (3) duplicated success handling between NLM path and generic path (~20 lines), (4) mixed concerns (validation, logging, caching, rate-limiting, translation, orchestration), (5) 3 inline special cases in the fallback loop (Whisper admission, NLM language override, expensive fallback gating). The fallback chain: oEmbed->yt-dlp->yt-dlp+cookies->direct_api->NotebookLM->Selenium->Whisper. Show: which closures to extract, how to eliminate duplication, how to handle special cases without inline conditionals, new function signatures. Explain WHY each change helps.

## Assistant

Refactor `fetch_transcript_chain(...)` into a thin orchestrator plus a small set of extracted pure helpers and policy objects. The key move is to turn the fallback loop from “loop + mutable state + inline special cases + duplicated success code” into “data-driven steps + shared result finalizer + explicit runtime state,” which makes the function easier to test, reason about, and extend.[1][2][3]

## Target shape

Use a functional-core / imperative-shell split: keep the outer function responsible for sequencing providers, logging, cache writes, and external calls, while moving validation, provider-decision logic, step planning, and result normalization into pure functions. This separation improves testability because the business rules become deterministic and no longer depend on hidden closure state or external mutations.[2][3][1]

A good end state is a coordinator that looks conceptually like: build request context, compile a fallback plan, iterate steps, execute provider, finalize first success, otherwise continue. That structure makes the control flow visible at a glance instead of being spread across five nested closures.[4][3][5]

## Extract closures

Extract every closure whose output depends only on arguments into top-level pure helpers, and extract side-effecting closures into explicit collaborator methods. Nested closures are especially costly here because they hide dependencies on outer locals and make state capture ambiguous, which raises maintenance and testing friction.[6][5][2]

Recommended extractions and signatures:

```python
@dataclass(frozen=True)
class TranscriptRequest:
    video_id: str
    config: TranscriptConfig
    skip_notebooklm: bool
    admission_metadata: AdmissionMetadata | None

@dataclass(frozen=True)
class RuntimePolicy:
    whisper_enabled: bool
    expensive_fallbacks_allowed: bool
    nlm_language_override: str | None
    whisper_admission_allowed: bool

@dataclass(frozen=True)
class StepContext:
    request: TranscriptRequest
    policy: RuntimePolicy
    prior_failures: tuple["StepFailure", ...]
```

```python
def build_request(
    video_id: str,
    config: TranscriptConfig,
    *,
    skip_notebooklm: bool = False,
    admission_metadata: AdmissionMetadata | None = None,
) -> TranscriptRequest: ...

def validate_request(request: TranscriptRequest) -> None: ...

def derive_runtime_policy(
    request: TranscriptRequest,
    *,
    whisper_enabled: bool,
) -> RuntimePolicy: ...

def build_fallback_plan(policy: RuntimePolicy) -> tuple["TranscriptStep", ...]: ...

def should_attempt_step(step: "TranscriptStep", ctx: StepContext) -> bool: ...

def normalize_provider_success(
    *,
    step_name: str,
    raw: "ProviderSuccess",
    ctx: StepContext,
) -> "TranscriptSuccess": ...

def to_transcript_result(
    success: "TranscriptSuccess",
    ctx: StepContext,
) -> TranscriptResult: ...

def to_step_failure(
    *,
    step_name: str,
    error: Exception | str,
    retryable: bool,
) -> "StepFailure": ...
```

```python
class TranscriptProvider(Protocol):
    name: str
    def fetch(self, ctx: StepContext) -> "ProviderOutcome": ...
```

The likely closures to extract are: request validation, per-provider invocation wrapper, result post-processing, success/result construction, failure recording, and special-case gating logic. Pulling them out exposes their true inputs and prevents accidental coupling to loop variables or mutable outer scope.[5][2][6]

## Remove duplication

The duplicated success handling between the NotebookLM path and the generic path should become one shared finalization pipeline. When two branches do the same “construct success metadata, maybe translate, maybe cache, log success, return TranscriptResult” work, that code belongs in one function regardless of which provider produced the raw transcript.[3][1][5]

Use a normalized provider contract:

```python
@dataclass(frozen=True)
class ProviderSuccess:
    text: str
    language: str | None
    segments: tuple[TranscriptSegment, ...] | None
    source_url: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ProviderFailure:
    reason: str
    retryable: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

ProviderOutcome = ProviderSuccess | ProviderFailure
```

Then every provider path, including NotebookLM, returns `ProviderOutcome`, and the orchestrator does exactly one thing on success:

```python
outcome = provider.fetch(step_ctx)
if isinstance(outcome, ProviderSuccess):
    success = normalize_provider_success(step_name=provider.name, raw=outcome, ctx=step_ctx)
    persist_success(success, step_ctx)   # cache/log/rate-limit bookkeeping
    return to_transcript_result(success, step_ctx)
```

This helps because it deletes branch-specific success assembly, makes provider differences explicit at the boundary, and ensures translation, caching, and metadata enrichment happen consistently for all successful providers.[1][4][3]

## Replace globals and conditionals

Do not read or write `_WHISPER_ENABLED` inside the loop body. Instead, snapshot it once at entry and carry it in `RuntimePolicy`, or better, inject a `FeatureFlags` or `TranscriptEnvironment` dependency whose state is read once and never mutated by the loop. Hidden global mutation is a classic source of non-local behavior because later iterations behave differently for reasons not visible in the step plan.[2][6][3]

Recommended replacement:

```python
@dataclass(frozen=True)
class TranscriptEnvironment:
    whisper_enabled: bool
    notebooklm_enabled: bool
    expensive_fallbacks_allowed: bool
```

```python
def fetch_transcript_chain(
    video_id: str,
    config: TranscriptConfig,
    *,
    skip_notebooklm: bool = False,
    admission_metadata: AdmissionMetadata | None = None,
    env: TranscriptEnvironment,
    providers: Sequence[TranscriptProvider],
    cache: TranscriptCache,
    logger: TranscriptLogger,
) -> TranscriptResult: ...
```

For the three inline special cases, move each into declarative step policies instead of inline `if` statements. Replacing conditional dispatch with a strategy/policy style keeps the loop generic and shifts step-specific rules into the step definitions themselves.[7][8][3]

Example step model:

```python
@dataclass(frozen=True)
class TranscriptStep:
    name: str
    provider: TranscriptProvider
    gate: Callable[[StepContext], bool] = lambda ctx: True
    transform_ctx: Callable[[StepContext], StepContext] = lambda ctx: ctx
```

Then encode the special cases as policies:

```python
def gate_whisper_admission(ctx: StepContext) -> bool: ...
def apply_nlm_language_override(ctx: StepContext) -> StepContext: ...
def gate_expensive_fallbacks(ctx: StepContext) -> bool: ...
```

Plan definition:

```python
plan = (
    step("oembed", oembed_provider),
    step("yt_dlp", ytdlp_provider),
    step("yt_dlp_cookies", ytdlp_cookies_provider),
    step("direct_api", direct_api_provider),
    step("notebooklm", notebooklm_provider,
         gate=lambda ctx: not ctx.request.skip_notebooklm,
         transform_ctx=apply_nlm_language_override),
    step("selenium", selenium_provider,
         gate=gate_expensive_fallbacks),
    step("whisper", whisper_provider,
         gate=lambda ctx: ctx.policy.whisper_enabled and gate_whisper_admission(ctx)),
)
```

This helps because the loop no longer “knows” provider quirks; it simply applies each step’s gate and context transform. Adding a new fallback becomes appending a new step instead of editing central control flow.[8][7][3]

## Proposed module split

A practical split is four layers: `core.py` for pure planning/normalization/validation, `providers.py` for provider adapters, `policies.py` for gates and feature decisions, and `service.py` for the orchestrator. That arrangement follows the principle of keeping calculations separate from I/O and external coordination.[3][1][2]

Suggested signatures:

```python
# core.py
def validate_request(request: TranscriptRequest) -> None: ...
def derive_runtime_policy(request: TranscriptRequest, *, env: TranscriptEnvironment) -> RuntimePolicy: ...
def build_fallback_plan(registry: ProviderRegistry, policy: RuntimePolicy) -> tuple[TranscriptStep, ...]: ...
def normalize_provider_success(*, step_name: str, raw: ProviderSuccess, ctx: StepContext) -> TranscriptSuccess: ...
def make_final_failure(ctx: StepContext) -> TranscriptResult: ...
```

```python
# policies.py
def gate_whisper_admission(ctx: StepContext) -> bool: ...
def gate_expensive_fallbacks(ctx: StepContext) -> bool: ...
def apply_nlm_language_override(ctx: StepContext) -> StepContext: ...
```

```python
# providers.py
class OEmbedProvider(TranscriptProvider): ...
class YtDlpProvider(TranscriptProvider): ...
class YtDlpCookiesProvider(TranscriptProvider): ...
class DirectApiProvider(TranscriptProvider): ...
class NotebookLmProvider(TranscriptProvider): ...
class SeleniumProvider(TranscriptProvider): ...
class WhisperProvider(TranscriptProvider): ...
```

```python
# service.py
def fetch_transcript_chain(
    video_id: str,
    config: TranscriptConfig,
    *,
    skip_notebooklm: bool = False,
    admission_metadata: AdmissionMetadata | None = None,
    env: TranscriptEnvironment,
    registry: ProviderRegistry,
    cache: TranscriptCache,
    translator: TranscriptTranslator,
    logger: TranscriptLogger,
    limiter: RateLimiter | None = None,
) -> TranscriptResult: ...
```

The orchestrator should then be small enough to read top-to-bottom in under a minute, with almost no branching except “skip step / try step / success / record failure / continue.” That is the clearest sign the mixed concerns have actually been separated rather than merely renamed.[4][5][3]

## Migration order

Refactor in this order to minimize risk: first extract shared success finalization, then replace `_WHISPER_ENABLED` with injected runtime state, then move inline special cases into gates/transforms, then extract pure planning/validation, and only after that split providers into separate classes. Cleaning up repeated behavior and hidden state first gives the highest leverage with the lowest semantic risk.[5][2][3]

Concrete next step: make one no-behavior-change PR that introduces `ProviderSuccess/ProviderFailure`, `normalize_provider_success(...)`, and `to_transcript_result(...)`, then route both NotebookLM and non-NotebookLM success paths through it. Confidence: high, because this is the most localized change and directly removes the known duplication without yet redesigning the whole fallback chain.[1][2][5]
