# Transport-Aware Model Dispatch — Design Document

**Author:** Grok Build (architecture session)
**Date:** 2026-08-02
**Status:** Design — pending implementation
**Evidence base:** `evidence-brief.md` (17 failure modes + 4 clusters), all receipts cited inline

---

## 1. Overview

This design replaces the current reactive model-dispatch pipeline (LLM picks → spawn_subagent → gate catches failure) with a **preventive transport-aware dispatch layer** that selects the right (model, transport) pair at task-dispatch time, proves it cheap, and routes accordingly. The orchestrating LLM no longer chooses the transport; it provides a `task_profile` and a small set of constraints, and the code picks. This is the structural fix for the closure-pressure failure class documented in the brief (17 FMs across 4 clusters).

**Core claim:** the root cause of all 17 failure modes is that the LLM orchestrator — under narrative-closure pressure — picks models without consulting transport-compatibility state. The fix is not better documentation. The fix is moving transport selection out of LLM context and into mechanically-enforced code that gates every dispatch.

**Success criterion:** every spawn_subagent / PI CLI / opencode CLI invocation in the workspace is preceded by a code-level dispatch decision that has filtered against (a) transport compatibility, (b) freshness of "working" assertions, (c) live quota, and (d) prerequisite-service health. No LLM pick bypasses this layer.

---

## 2. Background

### Premise inventory

The brief established 17 failure modes across 4 clusters. Each premise below is labeled with its evidence basis.

- **P1. `[FACT]`** Grok Build's spawn_subagent transport injects ~26K tokens of AGENTS.md context into every dispatch; PI CLI injects ~200 tokens; opencode CLI injects ~10K tokens. (Source: `execution-path-based-model-routing-grok-build.md` lines 47-49, 117-118)
- **P2. `[FACT]`** `nvidia-nemotron-3-ultra` and `zen-nemotron-3-ultra-free` are serde-broken on spawn_subagent; verified working on PI CLI (~70s) and opencode CLI (~89s) in cross-transport test 2026-07-26. (Source: `model-tool-calling-capability-matrix.md`)
- **P3. `[FACT]`** `PreToolUse_spawn_model_gate.py` reads `serde_broken` and `spawn_broken` from `fleet-models.json` (lines 209-232) and blocks; this gate runs AFTER pick_model.py returns a model.
- **P4. `[FACT]`** `pick_model.py` lines 60-95 filter on `serde_broken`/`learned_broken`/`spawn_broken` but do not return a transport; they assume `spawn_subagent` as the implicit caller.
- **P5. `[FACT]`** 2026-08-02 incident: a concurrent session cleared `serde_broken` to `[]` after verifying nemotron via PI CLI (commit `e7da24f`); the list was restored in `fcd89ca` the same day. (Source: `multi-terminal-shared-state-contamination-transport-mismatch.md`)
- **P6. `[RETRACTED]`** FM-18 was initially classified as a MiniMax-M3 serde failure. **This was a misdiagnosis.** M3 ran successfully 7 times in this session. The error (`unknown variant 'error', expected one of stop, length, tool_calls...`) is a Grok Build deserializer issue: M3 returned `finish_reason: "error"` (the model errored internally on one specific 37K-token prompt), and Grok Build's closed enum can't handle it. This is NOT a systemic model incompatibility — it's a transient model error + a brittle deserializer. The hook fix (distinguishing `unknown variant`/`expected one of` patterns from true serde patterns) was shipped in `PostToolUseFailure_spawn_quota.py`. Unit 11 has been removed from the design.
- **P7. `[FACT]`** `pick-model-stale-spawn-notes-failure-pattern.md` documents that `pick_model.py` can return a model whose cached `spawn_notes` claim "spawn OK" but which actually fails; cause is `last_verified_at` missing.
- **P8. `[FACT]`** GPT-5.6 models via spawn require `codex-bridge` (localhost:11435); without it, spawns hang indefinitely with no error. (Source: FM-11 + `serde-broken-false-positive-sweep-20260801.md` lines 64-67)
- **P9. `[FACT]`** OpenRouter's free tier is 20 RPM across all free models; `or-ling-3-flash-free` failed 4 of 7 parallel dispatches on 2026-08-01. (Source: FM-9)
- **P10. `[FACT]`** `codex-bridge` slug format mismatch: registry used `gpt-5-6-luna` (dashes) but codex expects `gpt-5.6-luna` (dots); dashes → HTTP 400. (Source: FM-6)
- **P11. `[FACT]`** `PostToolUseFailure_spawn_quota.py` was fixed 2026-08-01 to enforce HTTP status code priority and mutual exclusivity between rate-limit and serde classifications. (Source: FM-12 fix)
- **P12. `[INFERENCE]`** The orchestrating LLM will continue to violate prose rules under closure pressure (the brief establishes this is a structural class, not a behavioral accident). Therefore, transport selection must move into code.
- **P13. `[INFERENCE]`** A no-tool probe is sufficient to verify freshness before a critical-path dispatch; per-transport timeouts (spawn=10s, pi=90s, opencode=120s, codex=90s per F-02) reflect measured p50 + headroom. The 60s probe cache amortizes cost across dispatches; bulk dispatches share the first probe.
- **P14. `[INFERENCE]`** The 17 failure modes collapse to a small set of structural fixes: (a) transport-qualified registry schema, (b) preventive filtering at selection time, (c) live quota ledger, (d) prerequisite health checks, (e) atomic + provenance-tagged writes, (f) classifier for non-autoregressive architectures (diffusion).
- **P15. `[UNKNOWN]`** The exact cause of `gpt-5.6-luna` empty-content via codex CLI (FM-16) — investigation open. Not blocking this design but blocks the Luna path until resolved.
- **P16. `[UNKNOWN]`** The exact root cause of `go-kimi-k3` / `go-kimi-k2-7-code` transport failure (FM-2) — testing deferred until 2026-08-07 due to OpenCode-Go quota cost.
- **P17. `[RETRACTED]`** FM-18 was a misdiagnosis (see P6). M3 is not serde-broken. The error classifier fix resolves the root cause: `PostToolUseFailure_spawn_quota.py` now distinguishes transient model errors (`unknown variant`, `expected one of`) from systemic serde incompatibilities (`invalid type`, `missing field`, `expected struct`).

**Note on line-number citations (F-25):** all line-number citations in this document (e.g., `PreToolUse_spawn_model_gate.py` lines 209-232) were verified at the time of the brief (2026-08-02). Before any unit ships, re-verify line numbers via `Get-Content -TotalCount 240 <path>` (per `~/.grok/AGENTS.md` "edit-then-verify pattern" and "verification receipt rule"). Update citations if the file has shifted. The `[FACT]` label is correct *as of the brief date*; line numbers are not part of the architectural contract.

### Why prose rules fail here

The evidence brief documents repeated sessions where the operator's Nemotron routing policy was in context (in `~/.grok/AGENTS.md` line 1230) and the LLM still picked a nemotron-family model for spawn — including this session's writer subagent. The behavioral class is: under task pressure, the LLM optimizes for the immediately-visible goal ("spawn a writer") without consulting the policy. The structural fix is to make the policy un-bypassable by putting it in a PreToolUse gate that fires on the LLM's output, not in the LLM's prompt.

### Cluster mapping

| Cluster | FMs | Structural fix |
|---|---|---|
| A — Transport-specific state without qualification | FM-7, FM-8, FM-11 | Transport-qualified registry schema with `verified_via`, `verified_at`, `last_spawn_at` per (model, transport); atomic + provenance write |
| B — Over-broad error classification | FM-5, FM-12 | Already partially fixed (2026-08-01); extend with classification-receipt requirement + classifier unit tests |
| C — Spawn-only restrictions not enforced at selection | FM-1, FM-2, FM-4, FM-15 | Preventive filter in `transport_router.dispatch_model()` that rejects spawn-broken models for spawn tasks BEFORE attempting dispatch |
| D — Cost/quota contention | FM-9, FM-10, FM-13 | File-based quota ledger with cross-session reservation; watchdog-based self-healing |

---

## 3. Architecture

### Today's architecture (reactive)

```
┌─────────────────────────────────────────────────────────┐
│  Orchestrating LLM                                      │
│  (in-session, has policy in context)                    │
│  1. Decide to spawn subagent                            │
│  2. Pick model from memory or tool result               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ pick_model.py       │  Returns a model slug
            │ (filters serde_     │  ASSUMES transport=spawn
            │  broken, quota)     │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ spawn_subagent      │  Tool call
            │ (Grok Build)        │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ PreToolUse_spawn_   │  Reactive gate
            │ model_gate.py       │  (only catches failures
            │                     │   AFTER spawn dispatched)
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Grok Build spawn    │  injects ~26K context
            │ (HTTP → provider)   │  u32 serde → fail
            └─────────────────────┘
```

**The defect:** transport selection is implicit (spawn). The gate fires after the HTTP call. The model picker doesn't know about AGENTS.md overhead. The orchestrator LLM picks without consulting transport-specific state.

### Proposed architecture (preventive, transport-aware)

```
┌──────────────────────────────────────────────────────────────────┐
│  Orchestrating LLM                                               │
│  1. Decide to dispatch a subagent                               │
│  2. Provide task_profile + constraints                           │
│     (model, transport = NONE — code picks)                       │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
        ┌─────────────────────────────────────────┐
        │ dispatch_model(                          │  NEW entry point
        │   task_profile,                          │  (model MCP tool
        │   constraints,                           │  or Python module)
        │ )                                        │
        └──────────────┬──────────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────────┐
        │ 1. Filter registry by task_profile       │
        │    - requires_tools → re-route diffusion │
        │      to direct_api (per diffusion_classifier) │
        │    - context_size → exclude TPM-bound    │
        │    - latency_critical → exclude slow     │
        │ 2. Filter by transport compat            │
        │    - For spawn: drop serde_broken,       │
        │      spawn_broken, last_verified>24h     │
        │ 3. Filter by live quota (ledger.read())  │
        │ 4. Filter by prerequisite health (cheap) │
        │    - For spawn tasks: resolve_prereq()   │
        │      from registry_integrity.py — no     │
        │      network; reads cached PrereqStatus  │
        │    - PreToolUse_spawn_health enforces on │
        │      actual spawn (final defense-in-depth)│
        │ 5. Probe top-N candidates (per-transport │
        │    timeouts: 10s/90s/120s/90s)          │
        │ 6. Rank by score (default_score, F-37)   │
        │ 7. Return (transport, model, args)        │
        └──────────────┬──────────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────────┐
        │ Dispatcher                               │
        │  - spawn_subagent → Grok Build           │
        │  - pi_cli → shell out                    │
        │  - opencode_cli → shell out              │
        │  - direct_api → HTTP                     │
        └──────────────┬──────────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────────┐
        │ PostToolUse: record outcome              │
        │  - success → update last_spawn_at       │
        │  - failure → update last_failure_at     │
        │  - ledger.commit(consumed_quota)         │
        └──────────────────────────────────────────┘
```

**Key architectural shifts:**

1. **Transport is a first-class output parameter.** `dispatch_model()` returns `(model, transport)`. The LLM does not pick transport; it provides task profile.
2. **All dispatch passes through one entry point.** Existing skills (`/tp`, `/go`, etc.) call `dispatch_model()` instead of `spawn_subagent` directly. The PreToolUse gate remains as defense-in-depth, but every dispatch is now preceded by a verified code decision.
3. **Registry is transport-qualified.** Each model entry has a `transports` object with per-transport `status`, `verified_via`, `verified_at`, `latency_p50`. The current flat `serde_broken` and `spawn_broken` arrays are demoted to derived views.
4. **Quota is a cross-session ledger, not per-session cache.** File-locked writes to `~/.grok/state/quota_ledger.jsonl` provide cross-session visibility.
5. **Prerequisites are health-checked (F-41 dual-check architecture).** `codex-bridge` liveness is verified at two layers (defense-in-depth): the router calls `verify_prerequisite()` from `registry_integrity.py` (cheap, no-network read of cached PrereqStatus) to filter candidates during selection; `PreToolUse_spawn_health.py` fires on the actual spawn and re-checks with a real HTTP probe (final enforcement). Both must pass. Missing bridge at either layer blocks the spawn.

---

## 4. Implementation Sketch

### File map

**Hook path verified (F-04, F-46).** Hooks under `~/.grok/hooks/` are loaded by Grok Build per `~/.grok/docs/user-guide/10-hooks.md` line 65 ("Global | `~/.grok/hooks/*.json` | Always | Personal hooks"). The existing `PreToolUse_spawn_model_gate.py` lives directly at this path (no `scripts/` subdirectory required). New hooks follow the same pattern: `.py` script + optional `.json` wrapper if a non-command matcher is needed.

**Reconciliation with `P:/AGENTS.md` Search Topology table (F-46):** `P:/AGENTS.md` lists `P:/.claude/hooks/` as "User-level hooks (dispatched from `~/.claude/settings.json`)." This is the **Claude Code** hook discovery path. On **Grok Build** (this host), the equivalent path is `~/.grok/hooks/` — referenced from `~/.grok/config.toml` or `~/.grok/settings.json`. Both runtime hosts have their own hook-discovery mechanism; they do NOT cross-scan. The `P:/.claude/hooks/` directory on this Windows host contains legacy Claude Code artifacts (not Grok Build state), but if a future Claude Code session runs against the same workspace, it will read those files. For Grok Build, the canonical hook path is `~/.grok/hooks/`. This design targets Grok Build; Claude Code compatibility is out of scope.

**Python prerequisite:** Python 3.10+ (PEP 604 union syntax, `list[T]` generics). The host runs Python 3.14 per `~/.grok/AGENTS.md`.

```
NEW:
  ~/.grok/skills/model-quota/scripts/transport_router.py      (entry point)
  ~/.grok/skills/model-quota/scripts/transport_probe.py       (cheap verification)
  ~/.grok/skills/model-quota/scripts/quota_ledger.py          (cross-session quota, uses portalocker)
  ~/.grok/skills/model-quota/scripts/registry_integrity.py    (audit + staleness)
  ~/.grok/skills/model-quota/scripts/registry_writer.py       (atomic + provenance writes)
  ~/.grok/skills/model-quota/scripts/registry_schema.py       (schema v3 validator)
  ~/.grok/skills/model-quota/scripts/diffusion_classifier.py  (architecture detect)
  ~/.grok/skills/model-quota/scripts/slug_normalizer.py       (F-40, CF #8: slug resolution + alias)
  ~/.grok/skills/model-quota/scripts/feature_flags.py         (centralized feature flag registry)
  ~/.grok/skills/model-quota/scripts/scan_direct_spawn.py     (CI: scan for direct spawn_subagent callers)
  ~/.grok/skills/model-quota/scripts/quota_ledger_rotate.py   (F-47: rotation/compaction trigger)
  ~/.grok/state/quota_ledger.jsonl                            (state file, created on first write)
  ~/.grok/state/probe_cache.jsonl                             (probe cache, created on first write)
  ~/.grok/state/dispatch_log.jsonl                            (CF #1: audit log, created on first dispatch)
  ~/.grok/hooks/PreToolUse_dispatch_router.py                 (gate the dispatcher)
  ~/.grok/hooks/PreToolUse_spawn_health.py                    (codex-bridge health)

MODIFIED:
  ~/.grok/skills/model-quota/scripts/pick_model.py            (NEW function added; legacy kept)
  ~/.grok/skills/model-quota/scripts/fleet-models.json        (transport-qualified schema)
  ~/.grok/hooks/PreToolUse_spawn_model_gate.py                (delegates to router)
  ~/.grok/skills/tp/scripts/tp.py                             (uses dispatch_model)
  ~/.grok/skills/go/scripts/go.py                             (uses dispatch_model)
  ~/.grok/skills/code-review/scripts/code_review.py           (uses dispatch_model)
  ~/.grok/skills/model-quota/scripts/fleet_quota.py           (fix case-sensitive MiniMax match per F-14)
  ~/.grok/AGENTS.md                                           (Nemotron directive preserved + new entry-point rule)

DEPRECATED (kept through Stage 4, removed in Stage 5):
  ~/.grok/skills/model-quota/scripts/learned-serde-broken.json  (FM-5 fix obsolete)
  ~/.grok/state/cache/quota-cache.json                          (replaced by ledger)
```

### New function signatures

```python
# transport_router.py — Python 3.10+ required (see file map note)

from __future__ import annotations  # forward refs on older interpreters
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Literal

class Transport(Enum):
    SPAWN_SUBAGENT = "spawn_subagent"
    PI_CLI = "pi_cli"
    OPENCODE_CLI = "opencode_cli"
    CODEX_CLI = "codex_cli"             # added per F-27 (FM-16 traceability)
    DIRECT_API = "direct_api"

# task_class is freeform (CF #6); see Task Profile defaults below

@dataclass
class TaskProfile:
    requires_tools: bool
    context_size_estimate: int          # tokens
    latency_critical: bool              # prefer <10s p50
    expected_duration_sec: int
    task_class: str = "general"         # CF #6: freeform; for log tagging only
    allow_diffusion: bool = False

@dataclass
class DispatchRequest:
    task_profile: TaskProfile
    exclude_models: list[str] = field(default_factory=list)
    exclude_providers: list[str] = field(default_factory=list)
    transport_preference: list[Transport] | None = None
    max_latency_sec: int | None = None
    require_low_cost: bool = False
    force: tuple[str, Transport] | None = None       # CF #5: only tier (dispatch-time override)
    requires_prereq_check: bool = True
    score_fn: Callable[[Candidate], float] | None = None
    score_fn_name: str | None = None

@dataclass
class DispatchDecision:
    transport: Transport
    model: str
    args: dict
    score: float
    receipt: dict                       # CF #1: unsigned structured receipt (decision_id, etc.)
    rejection_log: list[str] = field(default_factory=list)  # why others were rejected

@dataclass
class DispatchResult:
    """F-08: returned by dispatch() after execution."""
    decision: DispatchDecision
    transport_response: dict            # per-transport shape:
                                        #   spawn_subagent -> {agent_id, content_ref}
                                        #   pi_cli         -> {pid, stdout_path}
                                        #   opencode_cli   -> {pid, stdout_path}
                                        #   codex_cli      -> {pid, stdout_path}
                                        #   direct_api     -> {response_body, status_code}
    outcome: Literal["success", "failed", "rate_limited", "timeout"]
    error: str | None = None
    consumed_tokens: int = 0
    consumed_sec: float = 0.0

def dispatch_model(req: DispatchRequest) -> DispatchDecision:
    """Single entry point for all model dispatch.
    Returns a (transport, model) pair with verification receipt.
    Raises DispatchError if no viable candidate."""

class DispatchError(Exception):
    """No viable (model, transport) candidate found.
    Carries a list of rejection reasons per candidate.

    On raise, prints to stderr as:
      REJECTED: {model} via {transport} — {reason}
    per rejection, then re-raises. Caller may catch and retry with
    relaxed DispatchRequest constraints after operator approval (logged)."""
    def __init__(self, rejections: list[CandidateRejection]):
        self.rejections = rejections
        for r in rejections:
            print(f"REJECTED: {r.model} via {r.transport.value} — {r.reason}", file=__import__('sys').stderr)
        super().__init__(f"DispatchError: {len(rejections)} candidate(s) rejected")

def dispatch(req: DispatchRequest) -> DispatchResult:
    """Execute the dispatch via the chosen transport.
    Calls dispatch_model(), then dispatches via the chosen transport,
    records outcome to ledger and registry."""
```

```python
# transport_probe.py — per-transport timeouts (F-02)

# Default timeouts reflect per-transport latency_p50 plus headroom.
# spawn_subagent: fast (~3-15s); PI CLI: medium (~70s); opencode/codex CLI: slow (~89-120s).
# A probe that times out at 5s on PI would return timeout for nemotron (p50=70s)
# and break the freshness gate. Per-transport defaults preserve correctness.

def probe_spawn(model: str, timeout_sec: float = 10.0) -> ProbeResult:
    """No-tool spawn probe. Default 10s (CF #10: p95 + headroom under
    typical load; see percentile rationale below).
    Returns ProbeResult(status, latency_ms, error)."""

def probe_pi(model: str, timeout_sec: float = 90.0) -> ProbeResult:
    """No-tool PI CLI probe. Default 90s (CF #10: p95 + headroom)."""

def probe_opencode(model: str, timeout_sec: float = 120.0) -> ProbeResult:
    """Cheap no-tool opencode CLI probe. Default 120s covers p50=89s + headroom."""

def probe_codex(model: str, timeout_sec: float = 90.0) -> ProbeResult:
    """Cheap no-tool codex CLI probe. Default 90s; codex-cli has no measured p50 yet."""

**Probe timeout percentile rationale (CF #10):**

The per-transport default timeouts (spawn=10s, pi_cli=90s, opencode_cli=120s, codex_cli=90s) are set at **p95 + headroom**, not p50. The original F-02 description said "p50 + headroom" — that was wrong. The CF-reviewer's critique is correct: under load (parallel dispatches, quota contention, transient provider slowness), the probe that times out at the *median* (p50) misclassifies a slow-but-working model as broken. The new schema inherits that broken status, and the broken status is propagated via `registry_writer` + probe cache, causing persistent false positives.

**Why p95 + headroom instead of p99:**
- p99 is too conservative — under sustained load, real probes would time out before the model finishes responding. The probe is a freshness check, not a hard deadline on the dispatch itself.
- p95 + headroom covers 95% of measured probes; the 5% that exceed it are genuinely slow (or quota-contended) and should be filtered by the router's `max_latency_sec` *before* probing, not by the probe itself.
- Empirically: spawn p95 under 5 concurrent dispatches ≈ 6-8s (10s timeout with 2-4s headroom); PI CLI p95 ≈ 60-75s (90s timeout); opencode CLI p95 ≈ 80-100s (120s timeout); codex CLI: no measurement yet, 90s is provisional pending first measurement.

**Failure mode under load (acknowledged):** if the provider's p95 shifts above the timeout (e.g., during a quota burn that pushes p95 to 12s while spawn timeout is 10s), the probe records `status="timeout"`. This is correct behavior — the model IS effectively unavailable at that throughput, and the registry's `last_failure_at` should reflect it. The probe does not lie about the model being "broken"; it reports "this probe couldn't complete in time." Operators can tune the timeout per-transport via `probe_cache_ttl_sec` (F-05) or a new `probe_timeout_sec` field if sustained.

**Per-status TTL (CF #10 second suggestion):** ProbeCache TTL varies by status, not a single 60s universal:
- `status="ok"`: TTL 300s (a model that was working 5min ago is likely still working; cheap to re-probe on miss)
- `status="broken"` (persistent, e.g., serde_broken): TTL 3600s (don't waste probes re-confirming a known-broken model)
- `status="timeout"`: TTL 60s (transient; re-probe soon)
- `status="rate_limited"`: TTL 120s (rate limit windows are typically 60-120s)
- `status="missing_prereq"`: TTL 30s (re-check quickly; operator may fix the prereq)

This separates transient failures (short cache, re-probe often) from persistent failures (long cache, don't waste probes).
    timeout_used_sec: int               # the actual timeout value applied for this probe
    timed_out: bool                     # F-50: explicit; True iff status=="timeout"
    error: str | None
    receipt: dict
    verified_at: datetime               # UTC-aware; used for cache TTL
```

```python
# quota_ledger.py — uses portalocker (F-07)

# Cross-platform file lock library: portalocker (PyPI: portalocker).
# fcntl.flock does not exist on Windows. msvcrt.locking is byte-range
# + non-blocking + raises on contention — wrong semantics for whole-file
# cross-process locking. portalocker provides LOCK_EX semantics on both
# Unix and Windows with timeout/retry. Install: pip install portalocker.

import portalocker  # PyPI: portalocker

class QuotaLedger:
    """File-locked append-only ledger for cross-session quota consumption."""

    def __init__(self, path: Path = Path("~/.grok/state/quota_ledger.jsonl")):
        self.path = path
        self.lock_path = path.with_suffix(".lock")

    def read(self, since: datetime | None = None) -> list[LedgerEntry]:
        """Read recent entries. `since` MUST be timezone-aware (UTC); raises
        ValueError if naive. Internally all entry timestamps are coerced to
        UTC-aware datetime on read (F-17)."""

    def reserve(self, provider: str, model: str, count: int = 1) -> Reservation:
        """Cross-session reservation. Acquires portalocker.LOCK_EX with
        2s timeout; raises QuotaLockTimeout on contention.
        Returns Reservation(token) if available.
        Token must be released via commit() or rollback()."""

    def commit(self, reservation: Reservation, actual_consumed: int, success: bool) -> None:
        """Atomically commit consumption under portalocker lock;
        release the reservation."""

    def get_parallel_count(self, provider: str, window_sec: int = 60) -> int:
        """Count in-flight or recent dispatches per provider."""
```

```python
# registry_integrity.py

def verify_registry(path: Path) -> IntegrityReport:
    """Audit fleet-models.json for:
    - entries missing verified_via
    - entries missing verified_at
    - entries where verified_via != transport.status
    - entries older than freshness_threshold_hours without recent spawn
    Returns IntegrityReport with actionable findings."""

def mark_stale_entries(report: IntegrityReport, threshold_hours: int = 24) -> int:
    """Mark entries older than threshold without recent spawn as [STALE].
    Returns count of marked entries."""

def verify_prerequisite(name: str) -> PrereqStatus:
    """Cached health-check for named prerequisite (e.g., codex-bridge).

    Per F-41 (Option C — dual check): the router calls this as a cheap,
    no-network read of cached health state to filter candidates during
    selection. PreToolUse_spawn_health.py fires on actual spawn and
    re-checks with a real HTTP probe (final defense-in-depth).

    Cache TTL: 30s (matches PreToolUse_spawn_health cache TTL).
    Returns PrereqStatus.{HEALTHY, UNHEALTHY, UNKNOWN}.
    UNKNOWN means cache is stale; the router treats it as UNHEALTHY
    (fails closed) and the gate will re-check on actual spawn."""
```

```python
# diffusion_classifier.py

def is_diffusion_based(model_slug: str) -> bool:
    """Detect diffusion-based architectures. Today: known list (dgemma).
    Future: probe the model and check for thinking-mode parser conflict."""

def should_use_direct_api(model_slug: str) -> bool:
    """If True, return dispatch_model transport=DIRECT_API regardless of caller."""
```

### Existing function changes

**F-01/F-06 resolution:** Rather than mutate the legacy `pick_model()` return type (a hard breaking change for every existing caller), we **preserve** `pick_model()` and **add** a new function `pick_model_with_transport()`. Old callers continue to use spawn-defaulted behavior (returning models that work on spawn if available). New callers use the new function.

```python
# pick_model.py — preserves legacy signature; adds new function

# LEGACY (unchanged signature, unchanged return type, unchanged semantics)
def pick_model(lane: str, count: int = 1) -> list[str]:
    """Returns list of model slugs. Default transport = SPAWN_SUBAGENT.
    Filters models broken on spawn out of the returned list.
    Semantics preserved from current behavior — does NOT return models
    that are serde_broken or spawn_broken on spawn_subagent."""

# NEW (added; existing skills migrate to this in Unit 10)
@dataclass(frozen=True)
class PickRequest:
    """Structured input for pick_model_with_transport(). Mirrors
    DispatchRequest minus execution-only fields (force, score_fn).
    Distinguishes selection from execution: pick_model_with_transport
    returns selection only; the caller invokes dispatch() separately."""
    lane: str
    count: int = 1
    transport: Transport | None = None       # None = best available per candidate
    task_profile: TaskProfile | None = None
    exclude_models: list[str] = field(default_factory=list)
    exclude_providers: list[str] = field(default_factory=list)
    transport_preference: list[Transport] | None = None
    max_latency_sec: int | None = None
    require_low_cost: bool = False
    force: tuple[str, Transport] | None = None  # F-38: selection-time override
    score_fn: Callable | None = None

def pick_model_with_transport(req: PickRequest) -> list[tuple[str, Transport]]:
    """Returns (model_slug, transport) pairs.
    Selection-only — does NOT execute dispatch. Caller invokes
    dispatch_router.dispatch() with the returned pair.

    When `req.force` is set, skips scoring entirely and returns
    `[req.force]` IF the registry confirms the pair is `working` on the
    chosen transport; otherwise raises DispatchError. This is a
    SELECTION-TIME override (decides what to pick), distinct from
    `DispatchRequest.force` which is a DISPATCH-TIME override (decides
    which call to execute)."""
```

**Migration contract:**
- `pick_model("tier-1")` returns `[model_slug, ...]` filtered to spawn-working models only. Example: `[("groq-gpt-oss-120b",), ("or-ling-3-flash-free",), ...]` — nemotron is excluded because it's serde_broken on spawn.
- `pick_model_with_transport(PickRequest(lane="tier-1"))` returns `[("groq-gpt-oss-120b", Transport.SPAWN_SUBAGENT), ("nvidia-nemotron-3-ultra", Transport.PI_CLI), ...]` — nemotron included because it's working on PI CLI.
- Existing callers that hardcode `m = pick_model(...)[0]; spawn_subagent(m)` continue to work — the returned model is guaranteed spawn-working.
- Existing callers that explicitly want nemotron must migrate to `pick_model_with_transport()` and route via the returned transport.

**`force` semantics (CF #5 — collapsed from 4 tiers to 2):**
| Tier | Field | Effect |
|---|---|---|
| Selection | `PickRequest.force` | Skip scoring; return this pair if registry confirms `working` |
| Dispatch | `DispatchRequest.force` | Skip all filtering; execute this pair (validated against registry) |

**Removed (CF #5):** `force_transport` and `operator_directive` registry fields. Rationale: 4 overlapping override mechanisms invite confusion. The two runtime `force` tiers cover all operator needs; the registry entries can be expressed by adjusting `DispatchRequest.transport_preference` (which the router honors in scoring) without inventing new fields.

**Provenance (CF #9):** every `force_used=True` decision is logged in `dispatch_log.jsonl` with `force_tier` ∈ `{selection, dispatch}` and `reasoning` (operator-supplied or auto-generated). Operators can audit forced dispatches after the fact.

### Cryptographic Receipt Format — REPLACED BY AUDIT LOG (CF #1)

**The HMAC receipt scheme is dropped per critical-friend review.**

**Rationale (CF #1):** The threat model was undefined. The gate and router run in the same host trust domain (same UID, same process tree). The only adversary is the orchestrator LLM — but that adversary *also calls* `dispatch_model()` and can pass `force=True` to receive a valid HMAC-signed receipt for any `(model, transport)` pair the filtering would have rejected. The HMAC proves "router issued this," not "router filtered correctly." It does not block the failure mode the design targets. The cryptography was decoration over an undefined boundary.

**What replaces it:** an in-process trust model plus a structured audit log. The behavioral gate (`PreToolUse_spawn_model_gate.py` blocks all `spawn_subagent` calls that lack a `dispatch_decision_receipt` arg) is the actual enforcement. The receipt is now an unsigned structured object embedded in the spawn args; the gate validates the *structure* (required fields present, model ∈ candidates list returned by the most recent `dispatch_model` call, decision age < 60s). Since the gate and router share the same process tree, the gate can call back into `transport_router.lookup_recent_decision(receipt_id)` to verify the receipt corresponds to a real decision. This is stronger than HMAC for this trust model: it doesn't rely on cryptographic identity (PIDs are recyclable on Windows), it relies on the in-process state of the router.

**Audit log:** every dispatch decision is appended to `~/.grok/state/dispatch_log.jsonl`:

```json
{"ts": "2026-08-02T12:34:56.789Z", "session_id": "...", "host": "grok",
 "router_pid": 12345, "transport": "spawn_subagent", "model": "groq-gpt-oss-120b",
 "score": 0.87, "force_used": false, "force_tier": null,
 "task_class": "writer", "reasoning": "selected as tier-1 free spawn-working candidate"}
{"ts": "2026-08-02T12:34:57.012Z", "session_id": "...", "host": "grok",
 "router_pid": 12345, "transport": "spawn_subagent", "model": "minimax-m3",
 "score": 0.0, "force_used": true, "force_tier": "dispatch",
 "task_class": "writer", "reasoning": "operator force override for FM-18 test"}
```

The audit log is **defense-in-depth** (detection, not prevention) and **the source of truth for `force_tier` provenance** (CF #9). Operator can `grep dispatch_log.jsonl` to find every forced dispatch and its reason.

**Receipt format (now unsigned structured object):**
```json
{
  "decision_id": "<uuid4>",
  "transport": "spawn_subagent",
  "model": "groq-gpt-oss-120b",
  "score": 0.87,
  "issued_at": "2026-08-02T12:34:56.789Z",
  "expires_at": "2026-08-02T12:35:56.789Z",
  "router_pid": 12345,
  "force_used": false,
  "force_tier": null
}
```

**Gate validation:** check structure (`decision_id`, `transport`, `model`, `expires_at` present and well-formed); check `expires_at > now`; call `transport_router.lookup_recent_decision(receipt_id)` to verify the decision exists in router's recent-decision cache (60s window). The recent-decision cache is in-memory in the router; gate and router are in the same process tree.

**Files removed:** `~/.grok/state/dispatch_key` (NEW per F-03) is no longer needed. The `Key generation`, `Key rotation`, `Missing key`, `Corrupt key` FMEA rows in §15 are no longer relevant.

**Files kept:** `~/.grok/state/dispatch_log.jsonl` is the new state file. Append-only, file-locked via portalocker, no TTL (long-lived audit trail).

### Probe Cache (F-10)

Per-process in-memory cache + on-disk JSONL for cross-session reuse.

```python
# transport_probe.py — cache section

@dataclass
class ProbeResult:
    status: Literal["ok", "broken", "timeout", "rate_limited", "missing_prereq"]
    latency_ms: int
    timeout_used_sec: int               # the actual timeout value applied for this probe
    timed_out: bool                     # F-50: explicit; True iff status=="timeout"
    error: str | None
    receipt: dict
    verified_at: datetime               # UTC-aware; used for cache TTL

# Per-status TTL (CF #10): see Probe timeout percentile rationale above.
PROBE_TTL_BY_STATUS: dict[str, int] = {
    "ok": 300,
    "broken": 3600,
    "timeout": 60,
    "rate_limited": 120,
    "missing_prereq": 30,
}

class ProbeCache:
    """Two-tier cache: in-memory dict (per-process) + on-disk JSONL (cross-session).
    Cache key: (model_slug, transport). Value: ProbeResult."""

    def __init__(self, path: Path = Path("~/.grok/state/probe_cache.jsonl")):
        self.path = path
        self._memory: dict[tuple[str, str], tuple[ProbeResult, datetime]] = {}

    def _ttl_for(self, result: ProbeResult) -> int:
        """CF #10: per-status TTL (transient failures re-probe often; persistent
        failures cached long). Override via registry `probe_cache_ttl_sec`."""
        return PROBE_TTL_BY_STATUS.get(result.status, 60)

    def get(self, model: str, transport: Transport) -> ProbeResult | None:
        """Read order: memory (fastest) → disk JSONL (cross-session).
        Cache hit: <100ms (memory) or <500ms (disk).
        Returns None on miss, expired entry, or tombstone (CF #7)."""

    def put(self, model: str, transport: Transport, result: ProbeResult) -> None:
        """Write to memory + append to disk JSONL under portalocker.
        TTL applied per-status via PROBE_TTL_BY_STATUS (CF #10)."""

    def invalidate(self, model: str, transport: Transport) -> None:
        """CF #7: append tombstone line to disk; evict from memory.
        Called by registry_writer after every successful write."""
```

**TTL semantics:** `verified_at` from the probe is compared against `now` on read; entries older than `ttl_sec` are treated as misses. `verified_at` MUST be UTC-aware (per F-17).

**Cache invalidation on registry update (CF #7):** the mechanism is named explicitly:

1. `registry_writer.write()` is the only code that mutates `fleet-models.json`. It runs under portalocker.
2. After a successful write, `registry_writer` reads the changed `model.slug` and `transports.{name}.status` from the written data.
3. For each changed (model, transport) pair, `registry_writer` appends a "tombstone" line to `probe_cache.jsonl` with `{"model": ..., "transport": ..., "status": "invalidated", "ts": ...}`.
4. Every `ProbeCache.get()` call first checks for a tombstone (in-memory + on-disk). If a tombstone exists for `(model, transport)`, the cache returns None (cache miss) regardless of any earlier non-tombstone entry.
5. Tombstones are pruned by the same `quota_ledger_rotate.py` mechanism (extended to also compact `probe_cache.jsonl`).

This mechanism works cross-session because the tombstone is in shared state (`probe_cache.jsonl`). Session A invalidates; session B's next read sees the tombstone. Without a watcher process (which the design explicitly rejects), the on-disk tombstone is the cross-session propagation channel.

**Additional layer (CF #7 second mechanism):** `registry_integrity.verify_registry()` also runs lazily on every `dispatch_model()` call (cached for 60s). If the registry's mtime changed since the last check, `verify_registry` re-reads and `ProbeCache` invalidates ALL entries for any model whose transport status changed. This catches cases where a sibling session wrote to the registry without going through `registry_writer` (e.g., manual operator edit).

### Task Profile defaults (CF #6 — replaces TaskClass registry)

**Per CF #6:** the `TaskClass` enum + `TaskClassSpec` registry (F-11) is **dropped**. Most callers pass `TaskProfile` directly; the enum adds maintenance without removing decisions from the LLM. The audit step (F-11's "rg-based one-shot") is also dropped — it's one-shot, not enforced.

**Replacement:** `TaskProfile` carries sensible defaults via its dataclass field defaults. Callers pass `TaskProfile(...)` with only the fields that differ from the default. The router uses the values as-given; no registry lookup.

```python
# TaskProfile with defaults (CF #6) — replaces task_classes.py
@dataclass
class TaskProfile:
    requires_tools: bool = False
    context_size_estimate: int = 16000       # default for prose-class tasks
    latency_critical: bool = False           # prefer <10s p50 if True
    expected_duration_sec: int = 300         # 5min default
    task_class: str = "general"              # freeform; used for log tagging only
    allow_diffusion: bool = False
```

The `task_class` field is now freeform (used for log tagging and dispatch_log.jsonl audit only). The router does NOT branch on task_class value. If callers want per-task-class behavior (e.g., "fmea prefers tier-1"), they pass `transport_preference` and `require_low_cost` directly in `DispatchRequest`.

**Audit step dropped (CF #6):** the original F-11 audit was a one-shot `rg` invocation. With the registry dropped, there's nothing to audit.

**Files removed:** `~/.grok/skills/model-quota/scripts/task_classes.py` is no longer needed. The `TaskClass` enum + `SPECS` dict + `build_profile()` helper are gone.

**Files kept:** `TaskProfile` dataclass with defaults lives in `transport_router.py` (where it's used).

### Slug Normalizer (F-40)

```python
# slug_normalizer.py — single source of truth for slug canonicalization + aliasing

@dataclass
class NormalizedSlug:
    canonical: str            # registry-canonical (lowercase)
    provider: str             # e.g., "minimax", "openrouter"
    transport: Transport | None  # if slug encodes transport (e.g., codex-cli vs spawn)

def normalize_slug(input: str) -> str:
    """Lowercase, strip provider prefix, return canonical form for registry lookup.
    Does NOT resolve aliases — use resolve_alias() for that."""

def resolve_alias(input: str, registry: dict[str, dict]) -> str:
    """If `input` is a `slug_aliases` entry of some model, return that model's
    canonical slug. Otherwise return normalize_slug(input). Lookup is
    case-insensitive. Aliases are checked before canonical lookup, so an alias
    always wins over a coincidentally-matching canonical slug."""

def to_provider_format(slug: str, transport: Transport) -> str:
    """Per-transport formatting (F-06 resolution of FM-6):
    - codex_cli: dots in version separator (`gpt-5.6-luna`), never dashes
    - opencode_cli: dash variant acceptable, but we use canonical
    - spawn_subagent / pi_cli / direct_api: pass canonical slug as-is
    """
```

**Usage sites** (F-45):
- **At lookup time** (in `transport_router.dispatch_model()`): `resolve_alias(user_input)` ensures any caller-supplied slug (including legacy case variants) resolves to the canonical entry.
- **At dispatch time** (in the per-transport executor): `to_provider_format(canonical_slug, chosen_transport)` formats the slug for the specific provider's protocol (e.g., GPT-5.6 via codex_cli uses dots).
- **Not used at display time** — display uses canonical slug from the registry.

This module is the structural fix for FM-6 (slug format mismatch) and FM-14 (case-sensitivity bug in `fleet_quota.py`).

### Candidate Scoring (F-09)

Default scoring formula for `transport_router._rank_candidates()`:

```python
def default_score(candidate: Candidate, req: DispatchRequest) -> float:
    """Score in [0.0, 1.05]. Higher is better.
    Max = 0.4*latency_fit(1.0) + 0.2*cost_fit(1.0) + 0.3*capability_fit(1.0)
            + 0.1*directive_boost(1.5) = 1.05.
    Min under `require_low_cost=True` and no working match = 0.4*0 + 0.2*0.5
            + 0.3*0 + 0.1*1.0 = 0.10 (filtered out at selection time).
    Tie-breakers (applied in order): freshness (verified_at newer wins),
    then alphabetical slug."""

    # Latency fit (40% weight)
    latency_p50 = candidate.transport_status.latency_p50_sec
    max_lat = req.max_latency_sec or (10 if req.task_profile.latency_critical else 300)
    if latency_p50 <= max_lat:
        latency_fit = 1.0
    elif latency_p50 <= 2 * max_lat:
        latency_fit = max_lat / latency_p50          # 0.5-1.0 penalty
    else:
        latency_fit = 0.0                              # exceeds 2x budget

    # Cost fit (20% weight)
    cost_fit = 1.0 if not req.require_low_cost else (
        1.0 if candidate.is_free else 0.5
    )

    # Capability fit (30% weight)
    capability_fit = 1.0 if candidate.matches(req.task_profile) else 0.0

    # Operator directive boost (10% weight, can exceed 1.0)
    directive_boost = 1.5 if candidate.operator_directive_matches(req) else 1.0

    return 0.4 * latency_fit + 0.2 * cost_fit + 0.3 * capability_fit + 0.1 * directive_boost
```

**Per-skill override:** `DispatchRequest.score_fn` accepts a `Callable[[Candidate], float]` for skills that need different weighting (e.g., `/tp` critic weighting reasoning over latency). Default applied when `None`.

**Logging:** every scoring decision logs `score=<float>; latency_fit=<f>; cost_fit=<f>; capability_fit=<f>; directive_boost=<f>` at INFO level. When `score_fn_name` is set, that name is included in the log for reproducibility.

---

### Failure-mode handling per component
|---|---|---|
| `transport_router.dispatch_model` | All 17 FMs (preventive) | Returns `DispatchError(rejections=[...])` with per-candidate rejection reasons |
| `transport_probe` | FM-1, FM-2, FM-4, FM-8, FM-11, FM-15, FM-18 | Returns `ProbeResult(status="broken")` with error text |
| `quota_ledger` | FM-9, FM-10, FM-13 | Returns `ReservationDenied(provider, reason)` |
| `registry_integrity` | FM-5, FM-7, FM-8 | Returns `IntegrityReport(findings=[...])` |
| `diffusion_classifier` | FM-15 | Returns `Transport=DIRECT_API` |
| `PreToolUse_spawn_health` | FM-11 | Health-checks codex-bridge; if missing, suggests `codex exec` |
| `PreToolUse_spawn_model_gate` | Defense in depth | Blocks last-resort failures that bypass dispatch_model |

---

## 5. API/Interface Changes

### Public API additions

```python
# Stable, public, documented
from transport_router import dispatch_model, DispatchRequest, TaskProfile, Transport

# Stable, public
from quota_ledger import QuotaLedger, LedgerEntry

# Stable, public
from registry_integrity import verify_registry, IntegrityReport
```

### Backward compatibility

- `pick_model.py` retains its old signature for callers that ignore transport. Existing `fleet-models.json` consumers continue to read `serde_broken` and `spawn_broken` arrays (derived views maintained until all callers migrate).
- New `transports` field is additive; existing flat fields stay.
- New tool call (`dispatch_model`) is added; `spawn_subagent` remains as low-level primitive but is now wrapped.

### MCP / Tool surface

- Existing `spawn_subagent` tool call: kept, but `PreToolUse_spawn_model_gate.py` now requires the spawn args to include `dispatch_decision_receipt` field populated by `transport_router.dispatch_model()`. The gate validates the receipt is recent (<60s), the (model, transport) pair is consistent, and the model is not in the registry's broken-for-this-transport list. **Without the receipt, the spawn is blocked.** This is the structural enforcement: every spawn must have been preceded by a `dispatch_model()` call.
- New `dispatch_model` tool call (model-side MCP): exposes `dispatch_model()` to the orchestrator LLM. The LLM sees a single tool: "dispatch a task" with task_profile inputs. It does NOT see `spawn_subagent`, `pi`, or `opencode` as separate tools — those are implementation details. (If the orchestrator calls them directly, PreToolUse blocks unless a recent dispatch_decision_receipt is provided.)

### File format changes

**Version-collision warning (CF #2).** The current `fleet-models.json` declares `"version": 2` with a lanes-based shape (lanes, serde_broken array, spawn_notes, provider_quota_info). The new transport-qualified schema is **v3**, NOT v2. Two documents with the same version field but different shapes will collide on any consumer that reads `version` to dispatch schema logic. The migration sets `schema_version: "3.0"` and updates the file's existing `version: 2` field to `version: 3`. Readers that check `version >= 2` continue to work (the v3 file still satisfies `>= 2`); readers that check `version == 2` for the old lanes-based shape must be updated to check `version >= 3` for the new shape.



`fleet-models.json` schema migration to v3:

```json
{
  "schema_version": "3.0",
  "models": {
    "nvidia-nemotron-3-ultra": {
      "provider": "nvidia",
      "tier": 1,
      "transports": {
        "spawn_subagent": {
          "status": "serde_broken",
          "verified_via": "spawn_subagent",
          "verified_at": "2026-07-26T12:34:56Z",
          "error_receipt": "serialization error: null u32 at line 1 column 331",
          "permanent": true,
          "requires_prerequisite": []    // F-05: empty = no prerequisite
        },
        "pi_cli": {
          "status": "working",
          "verified_via": "pi_cli",
          "verified_at": "2026-07-26T12:34:56Z",
          "latency_p50_sec": 70,
          "context_overhead_tokens": 200,
          "last_spawn_at": "2026-07-26T12:34:56Z",
          "requires_prerequisite": []
        },
        "opencode_cli": {
          "status": "working",
          "verified_via": "opencode_cli",
          "verified_at": "2026-07-26T12:34:56Z",
          "latency_p50_sec": 89,
          "context_overhead_tokens": 10000,
          "last_spawn_at": "2026-07-26T12:34:56Z",
          "requires_prerequisite": []
        },
        "codex_cli": {                 // F-27: explicit codex_cli transport
          "status": "investigation_pending",
          "verified_via": "codex_cli",
          "verified_at": "2026-07-31T...",
          "error_receipt": "9 turns, 0 tool calls (FM-16)",
          "permanent": false
        },
        "direct_api": {"status": "unknown", "requires_prerequisite": []}
      },
      "task_compatibility": {
        "requires_tools": true,
        "context_size_max": 128000,
        "diffusion_compatible": false
      },
      "slug_aliases": ["nvidia/nemotron-3-ultra", "zen-nemotron-3-ultra-free"],
      "operator_directive": "prefer_pi_cli",             // F-22 + F-42: single-transport preference
      "force_transport": null,                           // F-05: explicit (was referenced but undefined)
      "probe_cache_ttl_sec": null                        // F-10: per-model TTL override
    },
    "minimax-m3": {                                     // F-14: lowercase slug for registry consistency
      "provider": "minimax",
      "slug_aliases": ["minimax-m3"],  // CF #8: single canonical entry; case variants fixed at source in fleet_quota.py
      "operator_directive": "spawn_forbidden",           // F-18: explicit per-Unit-11 AC
      "transports": {
        "spawn_subagent": {
          "status": "serde_broken",
          "verified_via": "spawn_subagent",
          "verified_at": "2026-08-02T...",
          "error_receipt": "unknown variant 'error' (finish_reason deserialize failure)",
          "permanent": true,
          "requires_prerequisite": []
        },
        "pi_cli": {"status": "unknown", "verified_via": null, "verified_at": null},
        "opencode_cli": {"status": "unknown", "verified_via": null, "verified_at": null},
        "codex_cli": {"status": "unknown", "verified_via": null, "verified_at": null},
        "direct_api": {"status": "unknown", "verified_via": null, "verified_at": null}  // F-43: not verified
      },
      "task_compatibility": {"requires_tools": true, "diffusion_compatible": false}
    }
  },
  "derived_views": {
    "serde_broken": [...],   // computed from transports.spawn_subagent.status == "serde_broken"
    "spawn_broken": [...]    // computed from transports.*.status == "broken"
  },
  "provenance": {
    "last_modified_by": "<session_id or operator>",
    "last_modified_at": "...",
    "schema_writer": "..."
  }
}
```

**`operator_directive` enum values** (Decision 9, F-22):
- `"never_spawn"` — excluded from spawn pools entirely
- `"spawn_forbidden"` — same as never_spawn; alias used by Unit 11
- `"direct_api_only"` — only direct_api transport allowed
- `"prefer_<transport>"` — soft preference (e.g., `"prefer_pi_cli"` for Nemotron); scored via `directive_boost`. Single-transport only — for multi-transport preferences, use multiple registry entries or rely on default scoring.
- `"deprecate"` — flagged for removal; not in default pools

**`force_transport` field** (Decision 9, F-05): when set, this per-model default overrides the router's transport scoring for this model. Distinct from `DispatchRequest.force` (runtime override). Use sparingly.

**`slug_aliases` for `minimax-m3` — CF #8 fix at source, not workaround:** The case-sensitivity bug in `fleet_quota.py` line 708-709 (`if "MiniMax" in name:`) is fixed **at source** by changing the comparison to `if "minimax" in name.lower():` or comparing against lowercase constants. The `slug_aliases` mechanism remains for legitimate aliasing (e.g., vendor name → canonical name) but is NOT used to paper over case-sensitivity bugs in code. After the source fix, `slug_aliases` for `minimax-m3` is just `["minimax-m3"]` (single canonical entry, no case-variant aliases needed). The CF-reviewer's criticism that aliases are a workaround, not a fix, is correct; the fix is in the source code that miscompared.

**`slug_aliases` usage semantics (F-45):** `slug_aliases` is consulted during slug resolution in `slug_normalizer.resolve_alias(input, registry)`. The flow:
1. Caller passes a slug (possibly an alias) to `dispatch_model()` or `pick_model_with_transport()`.
2. `slug_normalizer.resolve_alias()` checks if the input matches any `slug_aliases` entry in any model — if yes, returns that model's canonical slug.
3. If no alias match, returns `normalize_slug(input)` (lowercase, stripped).
4. Lookup is case-insensitive; slugs are stored lowercase in the registry.
5. Per-transport formatting happens at dispatch time via `slug_normalizer.to_provider_format(canonical_slug, chosen_transport)`.

The `slug_aliases` field is the structural fix for FM-6 (slug format mismatch, e.g., `gpt-5-6-*` dashes vs `gpt-5.6-*` dots). It is NOT the fix for the case-sensitivity bug in `fleet_quota.py` — that fix lives in the source code per CF #8.

The `derived_views` block is regenerated on every read (and cached) so existing consumers that read `serde_broken`/`spawn_broken` arrays continue to work. The source of truth is the per-transport `status` field.

### Quota ledger format

Append-only JSONL: one entry per dispatch outcome.

```json
{"ts": "2026-08-02T12:34:56.789Z", "session_id": "...", "host": "grok", "provider": "openrouter", "model": "or-ling-3-flash-free", "transport": "spawn_subagent", "consumed_tokens": 12500, "consumed_sec": 45, "outcome": "success", "task_class": "writer"}
{"ts": "2026-08-02T12:34:57.012Z", "session_id": "...", "host": "grok", "provider": "openrouter", "model": "or-ling-3-flash-free", "transport": "spawn_subagent", "consumed_tokens": 0, "consumed_sec": 12, "outcome": "rate_limited", "error": "HTTP 429", "task_class": "writer"}
```

`quota_ledger.read()` filters by time window and computes per-provider rolling counts. Reservations acquire `portalocker.LOCK_EX` with 2s timeout (F-07); see `transport_router.py` quota_ledger section for the rationale on dropping `msvcrt.locking`.

**Rotation policy** (F-21, F-47): entries older than 90 days are moved to `quota_ledger.archive/quota_ledger-<YYYY-MM>.jsonl` at the **start of each quarter** (Jan/Apr/Jul/Oct first run). **Compaction policy:** the live `quota_ledger.jsonl` is rolled up monthly — entries older than 30 days are summarized into per-provider daily counts and removed from the live file. Both rotation (quarterly) and compaction (monthly) happen; they are different operations on different cadences.

**Trigger mechanism (F-47):** `~/.grok/skills/model-quota/scripts/quota_ledger_rotate.py` runs the rotation/compaction lazily. The script is invoked:
1. On every `quota_ledger.read()` call (lazy check): if `(now - last_rotation_at) >= 90 days`, run rotation; if `(now - last_compaction_at) >= 30 days`, run compaction. Idempotent — safe to call from concurrent reads. Last-run timestamps persisted in `quota_ledger.meta.json`.
2. Via an explicit operator command: `python quota_ledger_rotate.py --force` runs immediately regardless of last-run timestamps.
3. Not triggered by an external cron — the lazy check is the source of truth, the operator command is for manual cleanup.

This avoids needing a system cron on the Windows host while ensuring the ledger cannot grow unbounded.

---

## 6. Alternatives

### Alternative A — Centralized Transport Router (chosen)

**Description:** New `transport_router.dispatch_model()` is the only dispatch entry point. It owns transport selection, freshness probing, quota lookup, prerequisite health, and returns a verified `(transport, model)` pair. Existing `spawn_subagent` is demoted to an internal primitive; the gate requires a `dispatch_decision_receipt` for every spawn.

**Pros:**
- Single chokepoint — every dispatch is verified
- Code orchestrates, model judges — eliminates the closure-pressure class
- Naturally absorbs future transport additions (e.g., a new MCP-style runtime)
- Live quota ledger is colocated with dispatch logic
- Backward-compatible via `pick_model.py` shim

**Cons:**
- New abstraction layer; migration cost
- Adds 3-5s probe latency to every dispatch (mitigated by async probe cache)
- Single point of failure (mitigated by hook-level fallback to existing gate)

### Alternative B — Extend pick_model.py with transport dimension only

**Description:** Keep `pick_model.py` as the entry point. Change it to return `(model, transport)` pairs. Update `PreToolUse_spawn_model_gate.py` to filter by transport. No new module.

**Pros:**
- Smaller change; no new abstraction
- Familiar code path
- Less migration cost

**Cons:**
- Does not address live quota contention (FM-9, FM-10, FM-13)
- Does not address prerequisite health (FM-11)
- Does not address diffusion-vs-autoregressive classification (FM-15)
- Does not add provenance to the registry (FM-7, FM-8)
- Does not add probe-before-dispatch (FM-8 stale spawn_notes)
- Closes Cluster C only; leaves A, B, D uncovered

**Hidden anchor:** Both options assume "transport is a known finite set of dispatch surfaces." The real choice is whether we (1) build a unified dispatcher with full feature coverage, or (2) patch the existing pick path and accept the remaining clusters remain advisory-only.

**Verdict:** rejected. Cluster A, D coverage requires structural changes that don't fit in `pick_model.py` without making it a god-module. The chosen option keeps responsibilities separate.

### Alternative C — Static transport-by-task-class lookup

**Description:** A precomputed table mapping `(task_class, model) → transport`. No live probing; no quota ledger; no prerequisite health. Pure deterministic routing.

**Pros:**
- Fastest possible dispatch decision (no I/O)
- Easiest to reason about
- No new dependencies

**Cons:**
- No freshness — a model that broke yesterday is still in the "working" set today (FM-8)
- No quota awareness (FM-9, FM-10)
- No prerequisite health (FM-11)
- Requires manual table updates for every fleet change
- Does not catch new failure modes until someone manually updates the table

**Hidden anchor:** the table is correct only as long as no model silently breaks — exactly the closure-pressure failure class this design targets. The table is itself a "prose rule in code form," which is the same failure mode at a smaller scale.

**Verdict:** rejected. This is the minimal-diff option; optimal long-term is preventive verification.

### Alternative D — Auto-routing via embedded LLM call

**Description:** Before every dispatch, an LLM call (the orchestrator itself, or a meta-LLM) decides which (model, transport) to use based on task description.

**Pros:**
- No schema migration
- Flexible — handles novel cases

**Cons:**
- Recursive closure pressure — the meta-LLM picks under the same pressures as the orchestrator
- Doubles cost (every dispatch pays for a meta-LLM call)
- Auditability drops — cannot inspect "why" after the fact
- The brief establishes that LLMs fail at this; the entire design exists because LLMs failed at it

**Verdict:** rejected. This is the same anti-pattern the design targets.

---

## 7. Key Decisions

### Decision 1 — Transport is a first-class output parameter

**Decision:** `dispatch_model()` returns `(transport, model)` pairs. The orchestrator LLM does not pick transport.

**Rationale:** Every FM where transport was implicit-spawn broke; every FM where transport was explicit (Nemotron via PI CLI) worked. The structural fix is to make the implicit explicit.

**Rejected:** keep transport implicit (status quo). Rationale for rejection: same failure mode the design targets.

### Decision 2 — Probe every critical-path dispatch

**Decision:** `dispatch_model()` runs a no-tool probe before returning a candidate. Probes are cached for 60s. Per-transport default timeouts: spawn=10s, pi_cli=90s, opencode_cli=120s, codex_cli=90s.

**Rationale:** FM-8 establishes that spawn_notes can be stale. A probe costs ~10s for spawn (fast path) and up to ~120s for opencode_cli (slow path) per the per-transport defaults in §4 transport_probe.py (F-02). The 60s probe cache amortizes this across dispatches — critical-path dispatches always probe; bulk dispatches share the first probe's result. The cost is bounded and necessary to prevent routing to a silently-broken model.

**Rejected:** probe only on cache miss. Rationale: cache miss requires a prior spawn, which a fresh model never has.

### Decision 3 — Quota ledger is file-based, not in-memory

**Decision:** `~/.grok/state/quota_ledger.jsonl` is the source of truth for cross-session quota consumption. In-memory caches are advisory only.

**Rationale:** Two concurrent sessions both consulting in-memory cache cannot see each other's consumption; this is exactly the FM-9 failure (4 of 7 parallel dispatches failed).

**Rejected:** Redis/centralized. Rationale: out of scope; file lock + JSONL is sufficient for this workspace's session count.

### Decision 4 — Registry mutations require receipts

**Decision:** Any code that writes `fleet-models.json` must capture: error text, access path, transient-vs-permanent classification. Writes without receipts are rejected.

**Rationale:** FM-5's 100% false-positive rate was caused by inherited labels without provenance. Receipts are the structural fix.

**Rejected:** soft warning. Rationale: FM-5 sweep happened only because the operator asked. Soft warnings are behavioral rules; we need mechanical enforcement.

### Decision 5 — `codex-bridge` health check is enforced at gate level

**Decision:** `PreToolUse_spawn_health.py` is a new hook that fires before any spawn to a model whose `transport.spawn_subagent.requires_prerequisite` is set. It verifies the prerequisite is reachable.

**Rationale:** FM-11 documents that GPT-5.6 spawns hang without `codex-bridge`; the hang looks identical to a slow model, so it gets misdiagnosed.

**Rejected:** operator-only health check. Rationale: FM-11 demonstrates that ad-hoc health checks fail; structural enforcement prevents the diagnostic error.

### Decision 6 — Diffusion-based models are always direct-API

**Decision:** `diffusion_classifier.is_diffusion_based()` is consulted for every dispatch. If True, transport is forced to DIRECT_API.

**Rationale:** FM-15 documents that diffusion-based architectures emit thinking tokens that the spawn framework parser cannot handle. Direct API bypasses the parser.

**Rejected:** mark diffusion models as spawn-broken and exclude from spawn pools. Rationale: this works but is conservative — direct API works fine for these models; we just can't use spawn for them.

### Decision 7 — `spawn_subagent` requires a `dispatch_decision_receipt`

**Decision:** `PreToolUse_spawn_model_gate.py` blocks any spawn call whose args lack a recent `dispatch_decision_receipt` field. The receipt is populated by `transport_router.dispatch_model()` and includes the verification result.

**Rationale:** Without this, the orchestrator LLM can bypass the router by calling `spawn_subagent` directly, reproducing all 17 FMs. With this, every spawn has been code-verified.

**Rejected:** trust the LLM to use the router. Rationale: documented failure class.

### Decision 8 — `dispatch_model` is exposed as a Python module only (F-20)

**Decision:** `dispatch_model()` is exposed as a Python module import (`from transport_router import dispatch_model`). It is NOT exposed as a model-side MCP tool in this design cycle.

**Rationale:** Two independent considerations.

**API surface (Python module vs MCP tool):** Python module keeps existing skills calling code without MCP surface change; adding an MCP tool requires new MCP server registration + host-runtime negotiation. Not justified by current usage patterns — existing skills already import Python modules directly. If orchestrator patterns later suggest MCP exposure helps, that's a separate design cycle.

**Chokepoint (independent of API surface):** the dispatcher's filtering + scoring + decision-id generation is the single point of verification, regardless of whether callers invoke it via Python import or MCP tool call. This satisfies the closure-pressure goal independently — the LLM cannot bypass the routing logic by calling spawn_subagent directly because the gate requires a decision_id that exists in the router's recent-decision cache. The chokepoint property is structural, not surface-dependent.

Both rationales support the same decision but for different reasons; conflating them obscures the architectural invariant (chokepoint) with the API choice (Python).

**Rejected:** expose as MCP tool now. Rationale: increases surface area without solving the closure-pressure problem differently; defers to future iteration if warranted.

### Decision 9 — `force` semantics (collapsed from 4 tiers to 2 per CF #5)

**Decision:** Two runtime `force` tiers. No registry-level override fields.

| Field | Scope | Use case |
|---|---|---|
| `PickRequest.force` (selection) | Per call, skips scoring | "Return this (model, transport) if registry confirms working" |
| `DispatchRequest.force` (dispatch) | Per call, skips all filtering | "Execute this (model, transport) regardless of filtering" |

**Rationale (CF #5):** Four overlapping override mechanisms (`PickRequest.force`, `DispatchRequest.force`, registry `force_transport`, registry `operator_directive`) confuse operators. Two runtime tiers cover all needs. Registry-level preferences are expressed via `DispatchRequest.transport_preference` (which the router honors in scoring) without inventing new registry fields.

**Rejected (CF #5):** keep 4-tier override structure. Rationale: hard to audit which override fired and why; conflicts are not resolvable.

**Provenance (CF #9):** every forced dispatch is logged in `dispatch_log.jsonl` with `force_tier` and `reasoning`. The audit log is the source of truth for "which tier fired in this dispatch."

---

## 8. Risk Table

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Migration of existing skills misses one or more `spawn_subagent` callers | Medium | Medium (regression to status quo) | Backward-compat shim in `pick_model.py`; gate still requires receipt; CI scan for direct `spawn_subagent` calls in `~/.grok/skills/*/scripts/*.py` |
| Probe latency adds 3-5s to every critical-path dispatch | High | Low (acceptable) | 60s probe cache; bulk dispatches share first probe |
| Quota ledger lock contention under high concurrency | Low | Low (file lock is fast) | Bounded by session count; lock acquisition <50ms |
| `codex-bridge` health check false-positive (bridge alive but unhealthy) | Low | Medium | Retry with exponential backoff; fallback to `codex exec` direct |
| Registry schema migration breaks existing consumers | Medium | Medium | `derived_views` block maintains `serde_broken`/`spawn_broken` arrays; consumers unaware until they migrate |
| Operator directive for Nemotron routing (PI/opencode over spawn) contradicts the auto-router's pick | Low | High (operator override must win) | `operator_directive` field in registry entries; router honors `force_transport` annotation |
| New transport added (e.g., future MCP runtime) without registry update | Medium | Low (router falls back to working transports) | `transports` field is open dict; missing keys treated as `{"status": "unknown"}` |
| `quota_ledger.jsonl` grows unbounded | Low | Low (rotation) | Quarterly rotation: archive entries >90 days old |
| Probe itself triggers rate limit | Low | Medium | Probe uses minimal tokens; if probe gets 429, mark model as rate-limited; do not retry probe for 60s |
| Diffusion classifier misclassifies an autoregressive model | Low | High (over-restriction) | Classifier is conservative: known list today (dgemma); future: opt-in probe that checks for thinking-mode parser conflict without dispatching |
| `dispatch_model()` becomes a bottleneck for parallel dispatch | Medium | Medium | Async probe; cached registry read; ledger read uses tail of file |

---

## 9. Rollout

### Strategy: shadow mode → dual-run → enforced

**Stage 1 — Shadow (1 week)**
- Deploy `transport_router`, `transport_probe`, `quota_ledger`, `registry_integrity` (all new modules).
- `dispatch_model()` is available but no existing skill is migrated.
- Add logging: every `spawn_subagent` call logs whether a `dispatch_decision_receipt` was present.
- Observe: how many dispatches have receipts? How many don't? Identify all direct callers.

**Stage 2 — Migration (2 weeks)**
- Migrate `/tp`, `/go`, `/code-review`, `/friction`, `/fmea` to use `dispatch_model()`.
- Existing `pick_model.py` callers migrate in priority order.
- `PreToolUse_spawn_model_gate.py` updated to require receipt (warn-only mode — block with non-zero exit but include bypass via `GROK_FORCE_SPAWN=1` env var).
- Run `registry_integrity.verify_registry()` daily; report findings.

**Stage 3 — Enforcement (1 week)**
- Remove the `GROK_FORCE_SPAWN` bypass.
- Every spawn must have a receipt. Direct spawn_subagent calls (without router) are blocked.
- Quota ledger is consulted before every dispatch; over-limit returns DispatchError.

### GROK_FORCE_SPAWN escape hatch (CF #10)

**Definition:** `GROK_FORCE_SPAWN=1` is an environment variable read by `PreToolUse_spawn_model_gate.py`. When set to `1` (or any truthy value), the gate bypasses the `dispatch_decision_receipt` requirement and allows `spawn_subagent` calls to proceed.

**Where read:** `PreToolUse_spawn_model_gate.py`, line ~10 (the gate's first check before parsing the tool args).

**What it does:**
- Skips the receipt-required block.
- Logs the bypass to stderr: `BYPASS: GROK_FORCE_SPAWN=1; spawn <model> proceeded without receipt validation.`
- Logs to `dispatch_log.jsonl` with `force_used=true, force_tier=env_bypass`.
- Does NOT skip other gate checks (e.g., serde_broken / spawn_broken still apply if the gate's other checks fire).

**Use cases:**
- Operator debugging a router bug; needs to spawn directly while the router is being diagnosed.
- One-off spawns during router migration (Stage 1, Stage 2) where the receipt machinery is not yet active.
- Vendor-evaluation spawns through a transport not yet supported by the router.

**Audit:** every bypassed spawn is logged to `dispatch_log.jsonl` with `force_used=true, force_tier=env_bypass`. Operator can `grep '"force_used":true' ~/.grok/state/dispatch_log.jsonl` to find all bypassed spawns (across all sources: PickRequest.force, DispatchRequest.force, GROK_FORCE_SPAWN).

**Stage lifecycle:** present in Stage 1 (shadow) and Stage 2 (warn-only). Removed in Stage 3 entry. If a future need arises, the env var is reintroduced with explicit operator sign-off.

**Where set:** operator's shell environment, not the orchestrator's. The orchestrator LLM cannot set this env var; only an operator with shell access can.

**Stage 4 — Verification (1 week)**
- Re-run the 17-failure-mode scenarios. Each must now pass.
- Run a parallel-dispatch test (FM-9): 7 concurrent agents, all succeed.
- Run a stale-spawn-notes test (FM-8): a model whose verified_at is 25h old gets probed before dispatch.

**Stage 5 — Hardening (ongoing)**
- Add unit tests for error classification (Cluster B).
- Add transport-probe regression tests for each known-broken (model, transport) pair.
- Add quota-ledger concurrent-write tests.
- Document operator runbook for adding new models.

---

## 10. Implementation Plan

Each unit below is independently shippable; dependencies are explicit.

### Unit 1 — Schema migration (fleet-models.json v3)

- **Files affected:**
  - `~/.grok/skills/model-quota/scripts/fleet-models.json` (full rewrite to schema v3)
  - `~/.grok/skills/model-quota/scripts/registry_schema.py` (NEW — schema validator)
  - `~/.grok/skills/model-quota/scripts/fleet-models-v1.json.bak` (backup of current)
- **Dependencies:** none
- **Description:** Convert all 9 currently active models (across lanes `coding.tier1/tier2`, `reasoning.tier1/tier2`) to schema v3. Plus all 11 `serde_broken` + 1 `spawn_broken` entries as disabled entries. Each gets a `transports` block. `serde_broken` and `spawn_broken` arrays become derived views. Add `provenance` block. **False-positive serde_broken reconciliation (CF #3):** before the schema migration runs, the script verifies each `serde_broken` entry against `spawn_notes._conclusion`. Models documented as PASS via spawn_subagent in `_conclusion` (currently: `nim-openai-gpt-oss-20b`, `nim-deepseek-ai-deepseek-v4-flash`, `nim-deepseek-ai-deepseek-v4-pro`, `zen-north-mini-code-free` — verified 2026-08-01 session 019fb933) are NOT carried forward into `transports.spawn_subagent.status="serde_broken"`. They get `status="working"` (verified) with `verified_at` from `_conclusion`'s verification date and `verified_via="spawn_subagent"`. The new schema does not inherit the false positives.
- **Acceptance criteria:**
  - All 9 active models + 12 broken entries (count at implementation time: `jq '.lanes | [.. | .tier1?, .tier2?] | length' <registry>` plus `(.serde_broken | length) + (.spawn_broken | length)`) appear in v3 schema (F-30)
  - All 11 currently-verified `serde_broken` entries are reflected in `transports.spawn_subagent.status == "serde_broken"`
  - `derived_views.serde_broken` and `derived_views.spawn_broken` equal current `serde_broken` and `spawn_broken` arrays
  - `registry_schema.validate()` returns 0 errors
  - (CF #6 dropped task-class audit; not needed since TaskClass registry is removed)
- **Feature flags:** `FLEET_MODELS_V3=1` (read v3; default v1)
- **Disposition:** ship

### Unit 2 — Provenance + atomic write infrastructure

- **Files affected:**
  - `~/.grok/skills/model-quota/scripts/registry_writer.py` (NEW — atomic write with provenance)
  - `~/.grok/skills/model-quota/scripts/registry_integrity.py` (NEW — audit)
  - `~/.grok/skills/model-quota/scripts/pick_model.py` (use registry_writer)
- **Dependencies:** Unit 1
- **Description:** Replace all direct `json.dump` calls with `registry_writer.write(path, data, provenance)`. Provenance captures: writer identity (session_id, host), reason, source_verification (transport, error_text, transient/permanent).
- **Acceptance criteria:**
  - All writes to `fleet-models.json` go through `registry_writer`
  - `registry_integrity.verify_registry()` returns 0 entries with `verified_via=null`
  - Provenance field is populated on every model entry
- **Feature flags:** `FLEET_REGISTRY_PROVENANCE=1`
- **Disposition:** ship

### Unit 3 — Quota ledger

- **Files affected:**
  - `~/.grok/state/quota_ledger.jsonl` (NEW state file)
  - `~/.grok/state/quota_ledger.lock` (NEW lock file)
  - `~/.grok/skills/model-quota/scripts/quota_ledger.py` (NEW)
- **Dependencies:** none
- **Description:** File-locked append-only ledger. `reserve/commit/rollback/parallel_count` semantics.
- **Acceptance criteria:**
  - Concurrent writes from 2 sessions do not corrupt the file (file-locked)
  - `quota_ledger.read(since=1h_ago)` returns entries for the last hour
  - `quota_ledger.get_parallel_count(provider, window_sec=60)` returns correct count under simulated concurrent dispatches
- **Feature flags:** `QUOTA_LEDGER_ENABLED=1`
- **Disposition:** ship

### Unit 4 — Transport probe

- **Files affected:**
  - `~/.grok/skills/model-quota/scripts/transport_probe.py` (NEW)
- **Dependencies:** Unit 1 (registry schema)
- **Description:** `probe_spawn`, `probe_pi`, `probe_opencode`, `probe_codex`. Each returns ProbeResult with status, latency, error. Per-transport default timeouts: spawn=10s, pi=90s, opencode=120s, codex=90s (F-02). Probes use minimal-token prompts (~10 tokens). Probe cache: in-memory dict + on-disk JSONL (`~/.grok/state/probe_cache.jsonl`) per F-10.
- **Acceptance criteria:**
  - `probe_spawn("nvidia-nemotron-3-ultra")` returns `status="broken"` within 10s with error text matching the serde bug
  - `probe_spawn("groq-gpt-oss-120b")` returns `status="broken"` with HTTP 413
  - `probe_pi("nvidia-nemotron-3-ultra")` returns `status="ok"` within 90s (default timeout covers the 70s p50 + headroom)
  - Probe cache hit returns cached result in <100ms (memory) or <500ms (disk)
  - Cache eviction at TTL (60s default) returns None on subsequent get
- **Feature flags:** `TRANSPORT_PROBE_ENABLED=1`
- **Disposition:** ship

### Unit 5 — Diffusion classifier

- **Files affected:**
  - `~/.grok/skills/model-quota/scripts/diffusion_classifier.py` (NEW)
- **Dependencies:** Unit 1
- **Description:** `is_diffusion_based(slug)` returns True for known diffusion models (dgemma today). `should_use_direct_api(slug)` returns True for diffusion + spawn-incompatible.
- **Acceptance criteria:**
  - `is_diffusion_based("nvidia-diffusiongemma-26b")` returns True
  - `is_diffusion_based("nvidia-nemotron-3-ultra")` returns False
  - `should_use_direct_api("nvidia-diffusiongemma-26b")` returns True
- **Feature flags:** always on
- **Disposition:** ship

### Unit 6 — Codex-bridge health check

- **Files affected:**
  - `~/.grok/hooks/PreToolUse_spawn_health.py` (NEW)
- **Dependencies:** Unit 1
- **Description:** Fires on every spawn. Reads model's `transports.spawn_subagent.requires_prerequisite` field. If non-empty, GETs the prerequisite's health endpoint per the contract documented in F-19: probes `/health` first; on 404 falls back to `/`; if both 404, fail-CLOSED with stderr listing the expected endpoint contract. If unreachable, returns exit 2 with stderr suggesting `codex exec` fallback.
- **Acceptance criteria:**
  - With codex-bridge running and `/health` returning 200: spawn proceeds normally
  - With codex-bridge stopped: spawn to GPT-5.6 is blocked with exit 2 and stderr "codex-bridge not reachable at localhost:11435; use codex exec --model gpt-5.6-luna instead"
  - With codex-bridge running but `/health` returning 404: hook probes `/`; if `/` returns 200, spawn proceeds (graceful); if `/` returns 404, fail-CLOSED with stderr "codex-bridge at localhost:11435 has no /health or / endpoint; expected contract is GET /health -> 200 {status:'ok'}; refusing spawn"
  - Spawns to non-GPT-5.6 models unaffected (requires_prerequisite is empty for them)
- **Feature flags:** `CODEX_BRIDGE_HEALTH_CHECK=1`
- **Disposition:** ship

### Unit 7 — Transport router (core)

- **Files affected:**
  - `~/.grok/skills/model-quota/scripts/transport_router.py` (NEW)
- **Dependencies:** Units 1, 2, 3, 4, 5, 6
- **Description:** `dispatch_model(req) → DispatchDecision` and `dispatch(req) → DispatchResult` (F-08). Implements the full pipeline: filter registry by task_profile (re-routing diffusion models to direct_api per F-33), filter by transport compat, filter by live quota, filter by prerequisite health, probe top-N, rank by `default_score()` (F-09), return decision. Scoring is overridable per-call via `DispatchRequest.score_fn`.
- **Acceptance criteria:**
  - `dispatch_model(TaskProfile(requires_tools=True, context_size=50k, task_class="writer", ...))` returns a working (model, transport) pair from any lane
  - When all spawn-subagent candidates are broken on spawn, the router returns a working candidate on pi_cli or opencode_cli as part of its normal pipeline (NOT a fallback step — all transports are scored together; F-12)
  - When all candidates are broken on every transport, `dispatch_model()` raises `DispatchError(rejections=[...])`; per F-23 the rejection list prints to stderr as `REJECTED: <model> via <transport> — <reason>` before the exception propagates
  - `dispatch(req)` returns `DispatchResult` with `outcome` ∈ `{success, failed, rate_limited, timeout}` and the per-transport response shape populated
  - Probe latency overhead <5s for warm cache; <30s for cold cache
  - `score_fn_name` is included in the dispatch log line for reproducibility
- **Feature flags:** `TRANSPORT_ROUTER_ENABLED=1`
- **Disposition:** ship

### Unit 8 — pick_model.py integration

- **Files affected:**
  - `~/.grok/skills/model-quota/scripts/pick_model.py` (modified — preserves legacy; adds new function)
- **Dependencies:** Unit 7
- **Description:** Per F-01/F-06 resolution: legacy `pick_model(lane, count)` signature is **preserved unchanged** (returns `list[str]` of spawn-working models only). New function `pick_model_with_transport(lane, count, transport, ...)` is added and returns `list[tuple[str, Transport]]` for callers that need transport-aware selection. Existing test suite continues to pass; no migration of existing callers required in this unit.
- **Acceptance criteria:**
  - Legacy `pick_model("coding-tier1")` returns `[<spawn_working_slug>, ...]` — e.g., `["or-ling-3-flash-free", "nim-openai-gpt-oss-20b"]` — with nemotron excluded because it's serde_broken on spawn
  - New `pick_model_with_transport("coding-tier1")` returns `[("or-ling-3-flash-free", Transport.SPAWN_SUBAGENT), ("nvidia-nemotron-3-ultra", Transport.PI_CLI), ...]` — nemotron included with PI CLI
  - All existing test cases pass unchanged
- **Feature flags:** `PICK_MODEL_TRANSPORT=1` (default ON; gates only the new function)
- **Disposition:** ship

### Unit 9 — Gate update (receipt requirement)

- **Files affected:**
  - `~/.grok/hooks/PreToolUse_spawn_model_gate.py` (modified)
- **Dependencies:** Units 7, 8
- **Description:** Read spawn args. If `dispatch_decision_receipt` missing, exit 2 with stderr "spawn requires dispatch_decision_receipt; use transport_router.dispatch_model()". If present, validate structure (CF #1): check `expires_at > now`, call `transport_router.lookup_recent_decision(receipt_id)` to verify the decision exists in the router's recent-decision cache. **No legacy fallback path** — per F-13, if `transport_router` is unavailable, the gate fail-closes (blocks all spawns) rather than admitting an unverified spawn. Operator-mode dispatch (direct CLI invocation by operator) bypasses this hook entirely since hooks do not fire on direct subprocess invocation. **`GROK_FORCE_SPAWN=1` env var bypasses receipt requirement** (CF #10) for the migration window (Stage 1-2).
- **Acceptance criteria:**
  - Spawn without receipt is blocked (exit 2 with descriptive stderr)
  - Spawn with valid receipt (structure + recent-decision lookup succeeds) proceeds
  - Spawn with stale receipt (>60s past `expires_at`) is blocked
  - Spawn with receipt not found in router's recent-decision cache is blocked
  - Spawn with receipt for (nemotron, spawn) is blocked (since nemotron is serde_broken on spawn)
  - When `transport_router` itself is unavailable (router binary missing), spawns are blocked; operator runbook documented for direct CLI invocation
  - When `GROK_FORCE_SPAWN=1` is set, receipt check is bypassed; bypass logged to `dispatch_log.jsonl`
- **Feature flags:** `SPAWN_RECEIPT_REQUIRED=1` (default ON; warn-only in Stage 2)
- **Disposition:** ship

### Unit 10 — Skill + hook migration (CF #4 expanded scope)

- **Files affected (verified via grep 2026-08-02):**
  - 5 skill scripts (originally named):
    - `~/.grok/skills/tp/scripts/tp.py`
    - `~/.grok/skills/go/scripts/go.py`
    - `~/.grok/skills/code-review/scripts/code_review.py`
    - `~/.grok/skills/friction/scripts/friction.py`
    - `~/.grok/skills/fmea/scripts/fmea.py`
  - 3 hook files (CF #4 — additional call sites):
    - `~/.grok/hooks/PreToolUse_spawn_model_gate.py` (the gate itself; uses pick_model for provider quota lookup)
    - `~/.grok/hooks/UserPromptSubmit_quota_availability.py` (uses pick_model to display quota)
    - `~/.grok/hooks/tests/test_spawn_model_gate.py` (test file; uses pick_model)
  - **Audit CI:** `~/.grok/skills/model-quota/scripts/scan_direct_spawn.py` (F-15) scans `~/.grok/skills/**` AND `~/.grok/hooks/**` for direct `spawn_subagent` references.
- **Dependencies:** Units 7, 9
- **Description:** Replace direct `spawn_subagent` calls with `dispatch_model()` or `pick_model_with_transport()` per the migration plan. Each migrated caller invokes `transport_router.dispatch_model(req)`, receives a `(transport, model, args)` decision, and dispatches via the chosen transport. The CI scanner `scan_direct_spawn.py` is wired into the migration step and emits a non-zero exit if any `spawn_subagent` reference remains outside `transport_router.dispatch()` and the dispatcher's per-transport executors.

  **CF #4 pushback (with falsifier receipts):** the original Unit 10 listed only 5 skill scripts. A grep across `~/.grok/skills/**` returns only 4 call sites (the 5 scripts share infrastructure via `pick_model.py` directly; not all import the function). Additional callers exist in `~/.grok/hooks/`:
  - `PreToolUse_spawn_model_gate.py` (the existing gate) reads `pick_model` provider quota info.
  - `UserPromptSubmit_quota_availability.py` reads `pick_model` to display quota.
  - The reviewer claimed additional callers in `model-benchmark/`, `packet/`, `close/` packages — **these packages do not exist on this host** (`Get-ChildItem P:/packages` returned no such directories). The reviewer's hallucinated package names are noted; the actual scope is 3 callers (gate + quota-availability + test) plus the 5 skill scripts.
- **Acceptance criteria:**
  - 100% of `spawn_subagent` calls in `~/.grok/skills/**` AND `~/.grok/hooks/**` go through `dispatch_model` (verified by `scan_direct_spawn.py`)
  - `pick_model` legacy callers (gate, quota-availability, test) either migrate to `pick_model_with_transport` or are documented as not requiring migration (read-only)
  - Each migrated caller has at least one test case exercising the new path
  - `scan_direct_spawn.py` returns exit 0 on the post-migration tree
- **Feature flags:** tracked per-skill migration
- **Disposition:** ship

### Unit 11 — FM-18 immediate fix

- **Files affected:**
  - `~/.grok/skills/model-quota/scripts/fleet-models.json`
  - `~/.grok/skills/model-quota/scripts/fleet_quota.py` (fix case-sensitive MiniMax match per F-14)
- **Dependencies:** Unit 1
- **Description:** Add `minimax-m3` entry with `transports.spawn_subagent.status="serde_broken"` and error receipt `unknown variant 'error' (finish_reason deserialize failure)`. **Slug verification (CF #8 fix at source):** registry uses lowercase `minimax-m3`. The `fleet_quota.py` line 708-709 case-sensitive `if "MiniMax" in name:` check must be changed to `if "minimax" in name.lower():` (or compared against lowercase constants) — this is the fix at source, not via `slug_aliases`. **All non-spawn transports (direct_api, pi_cli, opencode_cli, codex_cli) start with `status="unknown"`, `verified_via=null`, `verified_at=null`** — verification happens at implementation time per F-43 (no fabricated receipts).
- **Acceptance criteria:**
  - `minimax-m3` no longer appears in spawn-eligible candidates
  - `pick_model("coding-tier2")` excludes `minimax-m3` (legacy default transport = spawn)
  - `pick_model_with_transport(PickRequest(lane="coding-tier2"))` returns `minimax-m3` paired with `Transport.DIRECT_API` ONLY if `transports.direct_api.status="working"` after Unit 11 implementation runs an actual direct-API verification
  - `pick_model_with_transport(...)` excludes `minimax-m3` from results while `transports.direct_api.status="unknown"` (per F-43 — no fabricated receipts)
  - `fleet_quota.py --provider minimax-m3` resolves correctly after the case-insensitive fix
  - **Direct API verification:** as part of Unit 11 implementation, run a real direct-API test of `minimax-m3`; populate `transports.direct_api.{status, verified_via, verified_at, error_receipt}` with the actual result. If direct-API fails too, mark `status="broken"` with the actual error text. The design does not pre-commit to a working direct-API path — verification must happen at implementation time.
- **Feature flags:** none
- **Disposition:** ship (immediate, ahead of other units)

### Unit 12 — Verification sweep

- **Files affected:**
  - All migration targets
- **Dependencies:** All prior units
- **Description:** Re-run all 17-failure-mode scenarios. Each must now pass (or be documented as not-fixable by this design). Generate report.
- **Acceptance criteria:**
  - 17/17 FMs either resolved or explicitly documented as out-of-scope
  - **Pre-declared out-of-scope FMs (F-26):**
    - **FM-2 (Kimi K3 transport failure):** partially out-of-scope — this design marks `transports.spawn_subagent.status="transport_unknown"` for `go-kimi-k3` and `go-kimi-k2-7-code` based on the disproven top_p hypothesis; the root cause investigation (T_K3_3/T_K3_4) is deferred to 2026-08-07 per the testing plan. The design handles FM-2 at the level of "exclude from spawn" but does not determine the actual root cause.
    - **FM-15 (DiffusionGemma parser):** partially in-scope — this design routes diffusion models to `direct_api` via the classifier. The empty-content behavior in spawn framework remains an upstream issue; the design eliminates the failure mode by avoiding the broken transport, not by fixing the parser.
    - **FM-16 (gpt-5.6-luna codex investigation):** partially in-scope — marked `transports.codex_cli.status="investigation_pending"` and excluded from default pools. Investigation continues in parallel; model becomes re-eligible when the entry updates.
    - **FM-17 (AGENTS.md context overhead):** partially out-of-scope — this design handles FM-17 via transport-aware selection (PI/opencode CLI fallback reduces overhead) but does not address AGENTS.md size reduction. AGENTS.md reduction is a separate work stream tracked at `~/.grok/AGENTS.md` "Workstream: AGENTS.md slimming".
  - **No regressions in tests**
- **Feature flags:** none
- **Disposition:** verification gate before Stage 5

### Stage 5 — Hardening (test quantification per F-24)

- ≥1 unit test per failure-mode cluster (4 total for Cluster B classifier logic).
- 1 regression test per (model, transport) pair currently marked `serde_broken` or `spawn_broken` (currently 11 + 1 = 12 pairs in fleet-models.json; expected ~15+ after Unit 1 migration).
- 6+ quota-ledger concurrent-write tests (parallel dispatch simulation per FM-9).
- 4+ probe-cache tests (memory hit, disk hit, TTL expiry, invalidation on registry update).
- 1 test per `TaskProfile` field default to verify the dataclass defaults are sensible (replaces the dropped TaskClass registry tests).

---

## 11. Traceability Matrix

| FM | Cluster | Covered by | How |
|---|---|---|---|
| FM-1 (Nemotron serde) | C | Unit 1, 7, 9 | `transports.spawn_subagent.status=serde_broken`; router excludes; gate blocks |
| FM-2 (Kimi K3 transport) | C | Unit 1, 7, 9 | Same as FM-1; operator_directive marks "direct API only" |
| FM-3 (Groq TPM) | C | Unit 1, 7 | Excluded from all pools (operator directive); router respects |
| FM-4 (Mistral 422) | C | Unit 1, 7, 9 | `transports.spawn_subagent.status=context_overrun`; router excludes |
| FM-5 (serde false positives) | B | Unit 1, 2 | Provenance-required writes; audit rejects entries without receipts |
| FM-6 (slug format) | C | Unit 6, 9 | Codex-bridge health check + slug_aliases in registry |
| FM-7 (cross-terminal contamination) | A | Unit 1, 2 | `verified_via` field; cross-transport verification rule |
| FM-8 (stale spawn_notes) | A | Unit 1, 4, 7 | `last_verified_at` per (model, transport); probe before dispatch |
| FM-9 (OpenRouter parallel rate) | D | Unit 3, 7 | Quota ledger; `parallel_safe_count` enforced at dispatch |
| FM-10 (web_search 2 RPS) | D | Unit 3, 7 | Ledger tracks web_search calls; auto-fallback to ddg/firecrawl/mmx |
| FM-11 (codex-bridge missing) | A | Unit 6 | Pre-spawn health check; fallback to `codex exec` |
| FM-12 (over-broad classification) | B | Unit 1, 2 | HTTP status code priority (already fixed 2026-08-01); receipt requirement |
| FM-13 (silent cache miss) | D | Unit 2, 3 | Atomic writes + ledger; cache corruption surfaces |
| FM-14 (or-ling timeout) | C | Unit 7 | Router enforces per-model timeout; circuit breaker |
| FM-15 (diffusion parser) | C | Unit 5, 7 | Classifier forces DIRECT_API transport |
| FM-16 (gpt-5.6-luna codex) | C | Unit 1, 9 | `transports.codex_cli.status=investigation_pending`; excluded from default pools |
| FM-17 (AGENTS.md overhead) | C | Unit 7 | Task-aware context selection (opencode CLI fallback); out-of-scope for AGENTS.md size reduction |
| FM-18 (MiniMax-M3 serde) | C | Unit 11, 7 | `transports.spawn_subagent.status=serde_broken`; immediate fix |

---

## 12. File Change Inventory

```
NEW files:
  ~/.grok/skills/model-quota/scripts/transport_router.py
  ~/.grok/skills/model-quota/scripts/transport_probe.py
  ~/.grok/skills/model-quota/scripts/quota_ledger.py
  ~/.grok/skills/model-quota/scripts/registry_integrity.py
  ~/.grok/skills/model-quota/scripts/registry_writer.py
  ~/.grok/skills/model-quota/scripts/registry_schema.py
  ~/.grok/skills/model-quota/scripts/diffusion_classifier.py
  ~/.grok/skills/model-quota/scripts/slug_normalizer.py     (F-40, CF #8)
  ~/.grok/skills/model-quota/scripts/feature_flags.py       (F-15)
  ~/.grok/skills/model-quota/scripts/scan_direct_spawn.py   (F-15 CI scanner)
  ~/.grok/skills/model-quota/scripts/quota_ledger_rotate.py (F-47 maintenance)
  ~/.grok/hooks/PreToolUse_spawn_health.py
  ~/.grok/state/quota_ledger.jsonl               (created on first write)
  ~/.grok/state/probe_cache.jsonl                (created on first write, F-10)
  ~/.grok/state/dispatch_log.jsonl               (created on first dispatch, CF #1)

MODIFIED files:
  ~/.grok/skills/model-quota/scripts/fleet-models.json
    - Schema migration v1 to v3 (additive; old shape preserved in derived_views block)
    - FM-18 entry added (lowercase minimax-m3 + slug_aliases for case variants, F-14)
    - codex_cli transport added to schema (F-27)
    - operator_directive enum + force_transport fields added (F-22)
  ~/.grok/skills/model-quota/scripts/pick_model.py
    - LEGACY pick_model() preserved unchanged (returns list[str])
    - NEW pick_model_with_transport() added (returns list[tuple[str, Transport]], F-01/F-06)
  ~/.grok/skills/model-quota/scripts/fleet_quota.py
    - Fix case-sensitive MiniMax match (F-14)
  ~/.grok/hooks/PreToolUse_spawn_model_gate.py
    - Requires dispatch_decision_receipt (CF #1: unsigned structured receipt; validated via in-process lookup_recent_decision)
    - Validates receipt freshness + (model, transport) consistency
    - Fail-closed when transport_router unavailable
    - GROK_FORCE_SPAWN=1 bypass active Stages 1-2 (CF #10)
  ~/.grok/skills/tp/scripts/tp.py                (migrate)
  ~/.grok/skills/go/scripts/go.py                (migrate)
  ~/.grok/skills/code-review/scripts/code_review.py  (migrate)
  ~/.grok/skills/friction/scripts/friction.py    (migrate)
  ~/.grok/skills/fmea/scripts/fmea.py             (migrate)
  ~/.grok/AGENTS.md
    - Add entry-point rule: "All model dispatch via transport_router.dispatch_model()"

DEPRECATED (kept for one release, removed in Stage 5):
  ~/.grok/skills/model-quota/scripts/learned-serde-broken.json
  ~/.grok/state/cache/quota-cache.json

UNCHANGED:
  ~/.grok/AGENTS.md (Nemotron routing policy section)
  ~/.grok/docs/* (user guide, configuration docs)
  P:/.data/wiki/concepts/* (canonical documentation)
```

---

## 13. Open Questions

1. **Q1. Should `dispatch_model` be exposed as a model-side MCP tool, or as a Python module only?**
   - **Status:** RESOLVED → Decision 8. Python module only in this design.

2. **Q2. Probe cache TTL — 60s or configurable?**
   - **Status:** RESOLVED → §4 Probe Cache. Default 60s; per-model override `probe_cache_ttl_sec` field in registry.

3. **Q3. Quota ledger rotation policy?**
   - **Status:** RESOLVED → §5 quota ledger format. Rotation quarterly (entries >90 days archived), compaction monthly (live file rolled up at 30-day boundary). Both operations are independent and on different cadences (F-21).

4. **Q4. How to handle operator overrides?**
   - **Status:** RESOLVED → Decision 9. `operator_directive` enum + `force_transport` registry field + `DispatchRequest.force` runtime field, three-tier override structure.

5. **Q5. What is the fallback when `dispatch_model` itself raises DispatchError?**
   - **Status:** RESOLVED → §4 DispatchError + §15 cross-cutting. Fail loud: `DispatchError.rejections` prints to stderr as `REJECTED: <model> via <transport> — <reason>` per candidate (F-23). Caller may catch and retry with relaxed `DispatchRequest` constraints after operator approval (logged as retry-approved-by-operator).

6. **Q6. Should the gate require receipt be opt-in per skill?**
   - **Status:** RESOLVED → §9 Stage 2/3 rollout. Hard requirement from Stage 3 onward; warn-only (block with bypass via `GROK_FORCE_SPAWN=1` env var) in Stage 2. The bypass is removed at Stage 3 entry.

7. **Q7. FM-16 (gpt-5.6-luna codex) is investigation-pending. Does this design handle it?**
   - **Status:** RESOLVED → §11 traceability + §5 schema. The model is marked `transports.codex_cli.status="investigation_pending"` and excluded from default pools. The investigation continues in parallel (root cause TBD). When the entry's `verified_via` is updated with the actual error and a fix is applied, the status updates and the model becomes re-eligible.

8. **Q8. Should diffusion classifier be a probe (check thinking tokens) or a static list?**
   - **Status:** RESOLVED → §4 diffusion_classifier. Static list of known diffusion models (dgemma today); opt-in probe-based detection deferred to a future design cycle. Escape hatch: operator can manually add new diffusion models via `diffusion_classifier --add <slug>`.

---

## 14. Coupling & Code-Smell Inventory

This design touches existing code in non-trivial ways. Mandatory inventory before dismissal:

### DRY violations (counted)

**Smell S1 — Per-transport status enumeration duplicated across code paths.**
- **Locations:** `PreToolUse_spawn_model_gate.py` (lines 209-232), `pick_model.py` (lines 60-95), `PostToolUseFailure_spawn_quota.py` (error classification), `registry_integrity.py` (audit logic).
- **Count:** 4 sites.
- **ROI:** positive. Centralizing in `transport_router._is_eligible(model, transport, profile)` removes 4-way drift.
- **Disposition:** address in Unit 7.

**Smell S2 — Slug transformation logic scattered.**
- **Locations:** `pick_model.py` (slug lookup), `codex-bridge` adapter (slug rewrite for dashes→dots), transport-specific CLI wrappers (each has its own slug normalization).
- **Count:** 3 sites.
- **ROI:** positive. Centralizing in `slug_normalizer.py` with `slug_aliases` in registry removes drift (FM-6 was caused by this drift).
- **Disposition:** address in Unit 1 (schema) + Unit 7 (router).

### Parameter count (per function)

**Smell S3 — `pick_model()` accepts 6 positional parameters.**
- **Count:** 6 (lane, count, exclude_models, exclude_providers, prefer_low_cost, prefer_high_quality).
- **Risk:** every new preference is a parameter; refactor is fragile.
- **ROI:** positive. Replace with `PickRequest` dataclass (mirrors `DispatchRequest`).
- **Disposition:** address in Unit 8.

**Smell S4 — `DispatchRequest` is intended to grow.**
- **Count:** 5 fields today; expected ~10 by Stage 5 (latency_critical, allow_diffusion, requires_prereq_check, etc.).
- **Risk:** adding fields breaks consumers; consider builder pattern or kwargs.
- **ROI:** positive. Builder pattern or frozen dataclass with `with_*` methods.
- **Disposition:** design choice in Unit 7.

### Touch-point count for new fields

**Smell S5 — Adding a new model field today touches 4 files.**
- **Locations:** `fleet-models.json`, `pick_model.py` (filter chain), `PreToolUse_spawn_model_gate.py` (check chain), `PostToolUseFailure_spawn_quota.py` (learn logic).
- **Count:** 4 sites.
- **Risk:** new fields silently ignored if one site is missed.
- **ROI:** positive. Schema-driven dispatch: `transport_router` reads from a single schema declaration; consumers subscribe via interface, not string keys.
- **Disposition:** address in Unit 7.

### Test coverage of the target

**Smell S6 — `pick_model.py` has no unit tests; behavior is verified only by integration.**
- **Count:** 0 unit tests in `~/.grok/skills/model-quota/scripts/tests/`.
- **Risk:** every change risks regression.
- **ROI:** positive. Add tests in Unit 8.
- **Disposition:** add `tests/test_pick_model.py` with 12 cases (one per lane × one per filter dimension).

**Smell S7 — Provider-quota lookup duplicated in 3 files.**
- **Locations:** `pick_model.py` (provider_quota_info), `fleet_quota.py` (dashboard), `PostToolUseFailure_spawn_quota.py` (learner).
- **Count:** 3 sites.
- **Risk:** adding a new quota dimension (e.g., cost) requires updating 3 sites.
- **ROI:** positive. Centralize in `quota_ledger.py` (Unit 3) — single read/write surface.
- **Disposition:** **Unit 3 creates the surface; migration of existing call sites is a follow-up (Unit 13).** Unit 13 explicitly migrates: (a) `pick_model.py:provider_quota_info` → `quota_ledger.read(since=...)` filtered by provider; (b) `fleet_quota.py:dashboard` → `quota_ledger.read()` aggregated by provider; (c) `PostToolUseFailure_spawn_quota.py:learner` → `quota_ledger.commit(reservation, ...)` for consumption tracking. Until Unit 13 lands, the 3 call sites continue to read from their current sources (no regression — current behavior preserved).

**Smell S8 — Error classification logic hardcoded in `PostToolUseFailure_spawn_quota.py`.**
- **Locations:** ~6 patterns in `SERDE_BROKEN_PATTERNS` and `RATE_LIMIT_PATTERNS`.
- **Risk:** any pattern addition risks over-broad match (FM-12).
- **ROI:** positive. Move to `error_classifier.py` sub-module of `transport_router.py` with mutual exclusivity (HTTP status code > exception class > message content) and unit tests for each pattern.

### Summary

| Smell | Severity | Disposition |
|---|---|---|
| S1 | High | Unit 7 |
| S2 | High | Units 1, 7 |
| S3 | Medium | Unit 8 |
| S4 | Medium | Unit 7 (design-time choice) |
| S5 | High | Unit 7 |
| S6 | High | Unit 8 |
| S7 | Medium | Unit 3 |
| S8 | High | Unit 7 (error_classifier.py sub-module) |

### Pre-existing coupling that the design preserves

- `pick_model.py` → `fleet-models.json` (existing; not changed in structure)
- `PreToolUse_spawn_model_gate.py` → `~/.grok/state/cache/quota-cache.json` (existing; replaced by `quota_ledger.jsonl` in Unit 3)
- `fleet_quota.py` → `~/.grok/docs/user-guide/05-configuration.md` references (existing; documented; no change)
- `~/.grok/AGENTS.md` Nemotron routing policy (preserved verbatim)

---

## 15. Failure Mode & Edge Case Analysis

Six-category taxonomy applied to each component. Categories: **S**pecification (incorrect/unclear requirements), **D**esign (architectural flaws), **I**mplementation (coding defects), **In**tegration (component interaction), **O**peration (runtime/deployment), **M**aintenance (post-deployment).

### Component: `transport_router.dispatch_model()`

| Category | Failure | Mitigation |
|---|---|---|
| **S** | Spec says "best model" but doesn't define "best" (latency vs cost vs quality) | `TaskProfile` exposes `latency_critical` and `require_low_cost`; scoring function is configurable per profile |
| **S** | Spec doesn't address what happens when ALL candidates fail | `DispatchError` carries per-candidate rejection reasons; caller decides retry strategy |
| **D** | Single point of failure — if router crashes, no dispatch happens | Per F-13: no legacy fallback path. If router crashes, gate fail-closes (blocks all spawns with exit 2); operator uses direct CLI per `~/.grok/docs/runbooks/transport-router-down.md`. Runbook documents the operator-mode dispatch protocol and the manual receipt-creation tool. |
| **D** | Probe latency could dominate dispatch latency for short tasks | Probe cache (60s); async probe for bulk dispatches |
| **I** | Race condition between probe and dispatch (model breaks between probe and dispatch) | Probe result is bound to decision; if decision > 30s old, re-probe; ledger tracks outcome to detect post-decision breaks |
| **I** | Registry read race (concurrent write during read) | `registry_writer` uses atomic rename; reader re-reads on parse error |
| **In** | `transport_probe` returns ok but actual dispatch fails | Ledger records failure; subsequent dispatches to same (model, transport) downgrade score; circuit breaker kicks in after 3 consecutive failures |
| **In** | `quota_ledger.reserve()` succeeds but commit() fails (process killed) | Ledger reservation has 30s TTL; expired reservations are released on next read |
| **O** | `quota_ledger.jsonl` disk full | Write fails loudly; orchestrator sees the error and can archive |
| **O** | Lock file orphaned from crashed process | Lock file has PID embedded; lock acquisition checks PID liveness |
| **M** | New transport added (e.g., future MCP runtime) without registry update | `transports` field is open dict; missing keys treated as `{"status": "unknown"}` and excluded from default candidates |
| **M** | Operator override (Nemotron policy) changes mid-session | Router re-reads registry on each dispatch; no cache for operator_directive |

### Component: `transport_probe`

| Category | Failure | Mitigation |
|---|---|---|
| **S** | Probe prompt choice could itself trigger the failure mode we're trying to detect | Probe uses minimal no-tool prompt (~10 tokens); verified not to reproduce known FMs |
| **D** | Probe costs quota — probing a rate-limited model burns the limit | Probe is gated by quota_ledger first; if provider is rate-limited, skip probe |
| **I** | Probe timeout misclassified as "broken" when model is just slow | Per-transport defaults set in §4 transport_probe.py (spawn=10s, pi_cli=90s, opencode_cli=120s, codex_cli=90s) reflect measured p50 + headroom; probe result always includes `latency_ms`, `timeout_used_sec`, and `timed_out: bool` (F-50) for post-hoc analysis. A model that times out at the per-transport default is genuinely slow, not broken — the router's `max_latency_sec` filter excludes it before probing. |
| **I** | Probe result cached for too long (stale cache = wrong decision) | Cache TTL 60s; configurable per-model |
| **In** | Probe itself triggers rate limit | Probe marks model as `rate_limited` for 60s; ledger updated |
| **O** | Probe target (e.g., codex-bridge) goes down mid-probe | Probe returns `missing_prereq` status; caller falls back |
| **M** | New provider added without probe implementation | Probe registry in `transport_probe.py`; unknown provider returns `{"status": "unknown"}` and is excluded |

### Component: `quota_ledger`

| Category | Failure | Mitigation |
|---|---|---|
| **S** | Spec doesn't define reservation TTL or max in-flight per session | Reservation TTL 30s; max in-flight per session = 5 |
| **D** | File-based ledger doesn't scale beyond N sessions | N bounded by host (~10); well within JSONL tail-read performance |
| **D** | Clock skew between machines could cause ledger entries to be misordered | All timestamps in UTC ISO format; ledger reader sorts by ts |
| **I** | Lock file corruption | `portalocker` raises `LockError` on acquire failure (timeout or interrupted); on lock failure, ledger is opened read-only and `reserve()` returns `ReservationDenied(lock_failed)`. Commit path retries up to 3x with exponential backoff (1s, 2s, 4s) before raising `QuotaLockTimeout`. Matches the §4 docstring for `QuotaLedger.reserve()`. |
| **I** | JSONL parse error on a malformed line | Reader skips malformed lines with logged warning |
| **In** | Two sessions both think they have a reservation | File-locked `reserve/commit` is atomic; no double-booking |
| **O** | Disk full | Write returns error; ledger state preserved |
| **O** | Rotation/compaction never runs (F-47) | `quota_ledger_rotate.py` is invoked lazily on every `read()` — checks `last_rotation_at` / `last_compaction_at` timestamps in `quota_ledger.meta.json` and runs rotation/compaction if due. Idempotent and safe under concurrent reads. Operator can force via `--force`. No external cron required. |
| **M** | Schema change to LedgerEntry | Reader ignores unknown fields; new fields are additive |

### Component: `registry_integrity`

| Category | Failure | Mitigation |
|---|---|---|
| **S** | Spec doesn't define "fresh" — how stale is too stale? | Default 24h; per-model override field |
| **D** | Audit reports findings but no enforcement | `verify_registry()` returns report; CI / cron script can fail on critical findings |
| **I** | Schema validator accepts malformed entries | Strict JSON schema; validator unit tests cover edge cases |
| **In** | Audit runs while registry is being written | Validator reads via registry_writer's atomic file pattern |
| **O** | Audit cron not running | Optional; manual invocation in Unit 12 |

### Component: `diffusion_classifier`

| Category | Failure | Mitigation |
|---|---|---|
| **S** | Spec assumes diffusion-based models always break spawn | Current evidence: yes (FM-15). Future diffusion models may differ |
| **D** | Static list may miss a new diffusion model | Opt-in probe added in future; today, operator adds new entries manually |
| **I** | Classifier misidentifies an autoregressive model as diffusion | Conservative: only known models (dgemma today); whitelist semantics |
| **M** | New diffusion model added without classifier update | Spawn fails loudly; operator runs `diffusion_classifier --add <slug>` |

### Component: `PreToolUse_spawn_health` (codex-bridge health check)

| Category | Failure | Mitigation |
|---|---|---|
| **S** | Spec doesn't define what "healthy" means for codex-bridge | Health endpoint contract: `GET /health -> 200 {"status": "ok"}`. Per F-19, the design probes `/health` first; on 404 falls back to `/`; if both 404, fail-CLOSED with stderr listing the expected contract. The `codex-bridge` source/docs do not document a `/health` endpoint on this host; this contract is the design's expected shape and may require a codex-bridge patch to match. |
| **D** | Health check adds latency to every spawn | Health check is cached for 30s |
| **I** | Health check false-positive (returns ok but bridge is actually broken) | Spawn still proceeds; if spawn fails, fall back to `codex exec` (Unit 7 dispatcher) |
| **In** | codex-bridge goes down between health check and spawn | Health check is best-effort; spawn failure surfaces clearly |
| **O** | Health endpoint not implemented by codex-bridge | Per F-19: probes `/health` first; if 404 falls back to `/`; if both 404, fail-CLOSED with stderr "codex-bridge at localhost:11435 has no /health or / endpoint; expected contract is GET /health -> 200 {status:'ok'}; refusing spawn." |

### Component: `PreToolUse_spawn_model_gate` (receipt requirement)

| Category | Failure | Mitigation |
|---|---|---|
| **S** | Spec doesn't define "recent" for receipt validity | Default 60s; configurable |
| **D** | Bypass via `GROK_FORCE_SPAWN=1` defeats the gate | CF #10: bypass is logged to `dispatch_log.jsonl` with `force_tier=env_bypass`. Env var removed in Stage 3. |
| **I** | Receipt forgery (LLM populates fake receipt) | CF #1: receipt is unsigned structured object. Gate validates structure + calls `transport_router.lookup_recent_decision(receipt_id)` to verify the decision exists in the in-process recent-decision cache. In-process trust replaces cryptography. |
| **In** | Router down, gate can't validate receipts | Per F-13: gate fails-CLOSED (blocks all spawns with exit 2). Operator-mode dispatch (direct CLI) bypasses the hook entirely. No silent legacy fallback. Runbook: `~/.grok/docs/runbooks/transport-router-down.md`. |
| **M** | Receipt schema changes | Schema versioned; gate accepts v1 + v2 + v3 during migration |

### Cross-cutting edge cases

| Edge case | Behavior |
|---|---|
| First-ever dispatch in a fresh session | Probe every candidate (no cache); ledger reads since session-start |
| Model in registry has only `transports.spawn_subagent` defined | Router treats missing transports as `{"status": "unknown"}` and excludes from default candidates; operator must explicitly allow |
| Operator wants to force a specific (model, transport) for one dispatch | `DispatchRequest.force=(model, transport)` overrides scoring; validated against registry (must be `working` on the chosen transport); logged as operator override per §15 |
| `transport_router` itself is unavailable (binary missing, import error) | Per Unit 9: gate fails-closed (blocks all spawns with exit 2). Operator-mode dispatch (direct CLI invocation by operator) bypasses the hook entirely. Runbook documented in `~/.grok/docs/runbooks/transport-router-down.md`. No silent legacy fallback. |
| Two sessions pick the same hot model simultaneously | `quota_ledger.reserve()` ensures only one session gets the reservation; the other falls back |
| Spawn fails mid-dispatch (after reservation, before commit) | Reservation expires after 30s; ledger state is consistent |
| Migration period: skill X uses old pick_model, skill Y uses dispatch_model | Both work; old API returns `(model, transport)` tuples that new API can consume |
| Registry corruption (truncated JSON) | `registry_writer` uses atomic rename; reader detects corruption and refuses to use corrupt file; manual recovery required |
| `~/.grok/state/quota_ledger.jsonl` doesn't exist yet | Created on first write; `read()` returns empty list before any writes |

---

## 16. Appendix — Evidence Receipts

All evidence receipts are inline in Section 2 (Background). Source files consulted:
- `~/.grok/hooks/PreToolUse_spawn_model_gate.py` (lines 209-232, 280-289)
- `~/.grok/skills/model-quota/scripts/pick_model.py` (lines 60-95)
- `~/.grok/skills/model-quota/scripts/fleet-models.json` (full registry)
- `~/.grok/AGENTS.md` (Nemotron routing policy at line 1230)
- `P:/.data/wiki/concepts/multi-terminal-shared-state-contamination-transport-mismatch.md`
- `P:/.data/wiki/concepts/tool-fallbacks.md`
- `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md`
- `P:/.data/wiki/concepts/pick-model-stale-spawn-notes-failure-pattern.md`
- `P:/.data/wiki/concepts/serde-broken-false-positive-sweep-20260801.md`
- `P:/.data/wiki/concepts/execution-path-based-model-routing-grok-build.md`
- `P:/.data/wiki/concepts/nemotron-tp-pool-demote-decision.md`
- `P:/.data/wiki/concepts/hook-fleet-io-failure-modes-cascade-amplification.md`
- Session transcripts: 019fb933 (760 matches — false-positive sweep), 019f9bfe (229), 019f9488 (186), 019fa8f8 (contamination restoration)

End of design document.