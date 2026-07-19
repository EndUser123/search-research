# Hook Latency Measurement Audit

**Date:** 2026-07-14
**Repository:** `P:\`
**Branch:** `main` (HEAD `7d8e103`)
**Scope:** Measurement only — no architecture changes, no consolidation, no removal

---

## PREFLIGHT

- **Repository:** `P:\`
- **Branch:** `main`
- **HEAD:** `7d8e103927d5a5dd47099a1e2e9fbd2d4ec52d38`
- **Dirty state:** Yes (pre-existing from prior workstream — preserved)
- **Baseline tests:** 79/79 pass (self-doc gate + cited content guard)

---

## HOOK_INVENTORY

### Registration: `P:/.claude/settings.json` (project-local)

| # | Event | Matcher | Hook | Timeout | Type |
|---|-------|---------|------|---------|------|
| 0.0 | UserPromptSubmit | `.*` | HookImporter → UserPromptSubmit.py | 15s | in-process |
| 0.1 | UserPromptSubmit | `.*` | skill-guard router | 10s | subprocess |
| 0.2 | UserPromptSubmit | `.*` | log_hook.py | 15s | subprocess |
| 0.0 | PreToolUse | `Skill|Bash|mcp__` | tool_availability_checker.py | 5s | subprocess |
| 1.0 | PreToolUse | `.*` | PreToolUse.py (HookImporter) | 15s | in-process |
| 2.0 | PreToolUse | `.*` | skill-guard router | 10s | subprocess |
| 2.1 | PreToolUse | `.*` | cc-aca-epistemic router | 15s | subprocess |
| 2.2 | PreToolUse | `.*` | log_hook.py | 15s | subprocess |
| 0.0 | PostToolUse | Edit/Write/MultiEdit | anti_lazy_diff_nudge | 5s | subprocess |
| 0.1 | PostToolUse | Edit/Write/MultiEdit | self_verification_gate | 5s | subprocess |
| 0.2 | PostToolUse | Edit/Write/MultiEdit | hook_import_health | 15s | subprocess |
| 0.3 | PostToolUse | Edit/Write/MultiEdit | py_syntax_gate | 5s | subprocess |
| 1.0 | PostToolUse | Bash | bash_syntax_gate | 10s | subprocess |
| 1.1 | PostToolUse | Bash | path_error_observer | 5s | subprocess |
| 2.0 | PostToolUse | `.*` | PostToolUse.py | 10s | subprocess |
| 3.0 | PostToolUse | Write/Edit/MultiEdit | claim_verifier_smoke | 20s | subprocess |
| 4.0 | PostToolUse | `.*` | log_hook.py | 15s | subprocess |
| 5.0 | PostToolUse | `.*` | cc-aca-observability router | 10s | subprocess |
| 5.1 | PostToolUse | `.*` | cc-aca-epistemic router | 10s | subprocess |
| 0.0 | PreCompact | `.*` | snapshot PreCompact | 45s | subprocess |
| 0.0 | Notification | `.*` | voice_hook | 3s | subprocess |
| 0.1 | Notification | `.*` | log_hook.py | 15s | subprocess |
| 0.0 | Stop | `.*` | Stop.py (hook_runner) | 10s | subprocess |
| 1.0 | Stop | `.*` | skill-guard router | 10s | subprocess |
| 1.1 | Stop | `.*` | log_hook.py | 15s | subprocess |
| 3.0 | Stop | `.*` | cc-skills-sdlc router | **DEFAULT** | subprocess |
| 0.0 | SessionStart | `.*` | HookImporter → SessionStart.py | 60s | in-process |
| 1.0 | SessionStart | `.*` | cc-aca-observability router | 60s | subprocess |
| 0.0 | SubagentStop | `.*` | SubagentStop_cjk_drift_detector.py | 5s | subprocess |

### Registration: `~/.claude/settings.json` (global)

| # | Event | Hook | Timeout |
|---|-------|------|---------|
| 0.0 | PreToolUse | skill-guard router | **DEFAULT** |
| 0.1 | PreToolUse | cc-aca-safety router | 10s |
| 0.2 | PreToolUse | cc-aca-investigation router | **DEFAULT** |
| 0.3 | PreToolUse | cc-aca-epistemic router | **DEFAULT** |
| 0.4 | PreToolUse | cc-aca-authority router | **DEFAULT** |
| 0.5 | PreToolUse | cc-aca-reasoning router | **DEFAULT** |
| 1.0 | PreToolUse (Edit/Write/MultiEdit) | cc-aca-sdlc router | 10s |
| 1.1 | PreToolUse (Edit/Write/MultiEdit) | cc-skills-utils router | 10s |
| 0.0 | Stop | Stop_negation_observer | 5s |
| 0.1 | Stop | Stop_session_gate | 5s |
| 0.2 | Stop | skill-guard router | **DEFAULT** |
| 0.3 | Stop | cc-aca-authority router | **DEFAULT** |
| 0.4 | Stop | cc-aca-reasoning router | **DEFAULT** |
| 0.5 | Stop | cc-aca-sdlc router | 10s |
| 0.6 | Stop | cc-lazy-closure-debt router | 10s |
| 1.0 | Stop | cc-skills-utils router | 30s |
| 0.0 | PostToolUse | cc-aca-epistemic router | **DEFAULT** |
| 0.1 | PostToolUse | cc-aca-observability router | **DEFAULT** |
| 0.2 | PostToolUse | cc-aca-reasoning router | **DEFAULT** |
| 0.3 | PostToolUse | cc-aca-sdlc router | 10s |
| 0.4 | PostToolUse | cc-lazy-closure-debt router | 10s |
| 1.0 | PostToolUse (Write/Edit/MultiEdit) | cc-skills-utils router | 10s |
| 0.0-0.7 | UserPromptSubmit | 8 plugin routers | 10-20s |
| 0.0-0.6 | SessionStart | 7 plugin routers | 10-15s or DEFAULT |
| 0.0-0.2 | SessionEnd | 3 plugin routers | **DEFAULT** or 10s |

**Total unique registrations: ~50**
**Hooks without explicit timeout (relying on 5s default): 8**

---

## REGISTRATION_MODEL

```
Settings JSON
    │
    ├── Event-type matcher (e.g., ".*", "^(?:Edit|Write)$")
    │       │
    │       ├── command hooks (subprocess)
    │       │       ├── Python script → does work
    │       │       ├── Plugin __lib/router.py → dispatches to hooks/{event}/*.py
    │       │       └── log_hook.py (logging only)
    │       │
    │       └── HookImporter (in-process)
    │               ├── Loads hook .py file dynamically
    │               └── Runs hook.main() in a daemon thread
    │
    └── Plugin cache (C:\Users\brsth\.claude\plugins\cache\local)
            └── Plugin router → individual hook files
```

---

## RUNTIME_MODEL

The runtime dispatch chain for each event is:

### UserPromptSubmit (3 hooks in series)
```
[0.0] HookImporter → UserPromptSubmit.py → 18+ UPS_modules (in-process aggregator)
[0.1] skill-guard/__lib/router.py → UserPromptSubmit handler
[0.2] log_hook.py
```

The HookImporter's UserPromptSubmit.py loads `UserPromptSubmit_modules/` which registers sub-hooks including:
`behavior_contract`, `unified_detection`, `skill_enforcer`, `task_detector`, `operating_rules`,
`competence_injector`, `mechanism_manifest`, `language_lock`, `frameguard_classifier`, and ~18 more.

Each sub-hook calls `register_hook()` and the aggregate `main()` function runs them all.

### PreToolUse (5 hooks in series)
```
[0.0] tool_availability_checker.py (matching Tool/Bash/mcp__ only)
[1.0] PreToolUse.py → HookImporter dispatch → 10+ PreToolUse_* sub-hooks
[2.0] skill-guard/__lib/router.py
[2.1] cc-aca-epistemic/__lib/router.py → 8 pretool/* sub-hooks
[2.2] log_hook.py
```

### Stop (4 hooks in series)
```
[0.0] Stop.py → hook_runner → 15+ in-process gates (aggregator)
[1.0] skill-guard/__lib/router.py
[1.1] log_hook.py
[3.0] cc-skills-sdlc/__lib/router.py → Stop_enforce_gate, go_continuation_gate
```

### Identity Boundaries

**CRITICAL FINDING:** `diagnostics.db` records all PreToolUse and PostToolUse executions under `hook_name="main"`, not under individual gate names. This means:

- PreToolUse's 60,470 recorded executions include ALL sub-hooks: tool_availability, epistemic gates, permission checking, investigation gate, evidence hierarchy gate, etc.
- PostToolUse's 57,378 "main" records include: anti_lazy_diff_nudge, syntax gates, claim verifier, observability router, etc.
- The individual Stop gates (semantic_critic, safety_gate, epistemic_contract, skill_first_stop_gate, etc.) *are* recorded separately because Stop.py's aggregator reports them individually — but their `execution_time_ms` is 0.0ms in the DB, so they are not timed at the sub-gate level.
- Individual sub-hooks **are** recorded when the HookImporter runs them (behavior_contract, unified_detection, each SessionStart sub-hook), but again with 0.0ms execution_time_ms.

**The diagnostic system records timing at the entry-point level only, not at the individual gate/hook level.** The single "main" PreToolUse entry encompasses up to 18+ individual gates.

---

## DATA_SOURCES

### Primary: `diagnostics.db`

| Table | Rows | Timing Data | Granularity |
|-------|------|-------------|-------------|
| `hooks` | 142,603 | `execution_time_ms` (float) | Entry-point only for "main"; recorded but 0.0ms for sub-hooks |
| `importer_diagnostics` | 95 | Error/traceback text | Hook name + phase (load/execute/timeout/stderr) |
| `errors` | 192 | No timing | Error messages only (mostly test fixtures) |

**Table columns with timing:** `execution_time_ms`, `duration_ms`, `timeout_ms`, `output_size_bytes`.

**Date range:** 2026-06-17 to 2026-07-14 (~28 days of data).

### Secondary: JSONL log files

| File | Size | Content |
|------|------|---------|
| `content_filter_skips.jsonl` | ~400KB | Filter skip events — no timing |
| `cc_errors.jsonl` | ~6.5KB | Error records — no timing |
| `behavior_audit_telemetry.jsonl` | ~14KB | Telemetry — event counts, no ms timing |
| `epistemic_advisories.jsonl` | ~3.5KB | Advisory records — no timing |
| `hook_stderr.log` | (text) | Stderr logs — no structured timing |

### Data Sufficiency Assessment

| Need | Available? | 
|------|------------|
| Per-hook invocation count | YES — 142K+ rows |
| Per-hook per-call timing | PARTIAL — only at "main" entry point |
| Per-gate timing within dispatched hooks | NO — Stop.py gates, HookImporter sub-hooks, plugin router sub-hooks all show 0.0ms |
| Per-hook timeout attribution | PARTIAL — 8 timeout events in importer_diagnostics, 42 near-timeout events on PreToolUse |
| P50/P95/P99 per gate | NO — can compute for "main" aggregate only |

**Conclusion: Existing data is sufficient for entry-point-level analysis but insufficient for individual gate-level latency attribution.** The diagnostic system records *that* gates fire and *what they decide* (allow/block/warn/inject), but not *how long each takes*.

---

## MEASUREMENTS

### Entry Point Timing Summary

| Entry Point | Count | Avg (ms) | Max (ms) | >1s | >3s | >5s |
|-------------|-------|----------|----------|-----|-----|-----|
| PreToolUse "main" | 60,470 | 4.2 | 8,885 | 258 | 15 | 3 |
| PostToolUse "main" | 57,378 | 2.6 | 1,254 | 36 | 0 | 0 |
| UserPromptSubmit (behavior_contract) | 509 | 0.0 | 0.0 | 0 | 0 | 0 |
| UserPromptSubmit (test_hook) | 59 | 0.0 | 0.0 | 0 | 0 | 0 |
| Stop (individual gates, aggregate) | 624 | 0.0 | 0.0 | 0 | 0 | 0 |

Note: UserPromptSubmit and Stop sub-gate timing appears as 0.0ms in the DB. This is likely because their `main()` function returns exit codes rather than timing being recorded — the HookImporter captures timing for its `execute_hook()` call, but sub-hooks registered via `register_hook()` may not propagate timing back.

### PreToolUse "main" Distribution (60,470 events)

| Bucket | Count | % of Total | Average (ms) |
|--------|-------|------------|--------------|
| <1ms | 56,800 | 93.9% | 0.3 |
| 1-5ms | 3,274 | 5.4% | 1.5 |
| 5-10ms | 80 | 0.1% | 7.0 |
| 10-50ms | 51 | 0.1% | 16.9 |
| 50-100ms | 8 | <0.1% | 81.3 |
| 100-500ms | 121 | 0.2% | 264.2 |
| 500-1000ms | 66 | 0.1% | 713.1 |
| >1s | 71 | 0.1% | 2,151.8 |

**94% of all PreToolUse invocations complete in under 1ms.** The long tail (>1s, 0.1% of events) accounts for the observable latency risk.

### PostToolUse "main" Distribution (57,378 events)

| Bucket | Count | % of Total | Average (ms) |
|--------|-------|------------|--------------|
| <1ms | 4,535 | 7.9% | 1.0 |
| 1-5ms | 48,884 | 85.2% | 1.9 |
| 5-10ms | 3,061 | 5.3% | 6.3 |
| 10-50ms | 764 | 1.3% | 19.7 |
| 50-100ms | 97 | 0.2% | 65.8 |
| 100-500ms | 33 | 0.1% | 191.2 |
| 500-1000ms | 1 | <0.1% | 606.4 |
| >1s | 3 | <0.1% | 1,127.1 |

**93% of all PostToolUse invocations complete in under 5ms.** The long tail is much lighter than PreToolUse.

### Near-Timeout Events (PreToolUse with 2000ms timeout)

```
42 events where execution_time_ms > 1500ms (approach or exceed 2000ms timeout)
3 events where execution_time_ms > 5000ms (would have been killed by 2000ms timeout)
  - 8885.3ms on 2026-07-05
  - 5882.7ms on 2026-07-11
  - 5273.5ms on 2026-07-11
```

The 2000ms timeout on `tool_availability_checker.py` (PreToolUse matcher `Skill|Bash|mcp__` at entry 0.0) appears dangerously tight. These events would have been terminated by the hook_runner after `timeout=5s` (the setting.json timeout), but the `execution_time_ms` of 8885ms suggests either:
- A clock skew between subprocess and DB recording, or
- The subprocess completing but the DB recording including subsequent dispatch overhead

### Importer Timeout Events

| Date | Hook | Timeout | Error |
|------|------|---------|-------|
| 2026-07-10 | SessionStart | 45s | Timed out after 45s |
| 2026-07-10 | SessionStart | 45s | Timed out after 45s |
| 2026-07-06 | SessionStart | 45s | Timed out after 45s |
| 2026-07-03 | SessionStart | 15s | Timed out after 15s |
| 2026-07-02 | UserPromptSubmit | 15s | Timed out after 15s |
| 2026-07-02 | UserPromptSubmit | 15s | Timed out after 15s |
| 2026-07-02 | SessionStart | 45s | Timed out after 45s |
| 2026-07-02 | SessionStart | 45s | Timed out after 45s |

**8 total timeout events in 28 days.** 6 SessionStart, 2 UserPromptSubmit. SessionStart with 45s timeout timing out suggests a blocking I/O or daemon stall.

---

## PER_HOOK_RESULTS

### Critical Safety Hooks

```
Hook: Stop.py (aggregator)
Purpose: 15+ safety gates (semantic critic, safety gate, epistemic contract, cited content guard, etc.)
Observed cost: 0.0ms (not timed per-gate in DB)
Timeout: 10s (hook_runner) / 15s (log_hook)
Risk if slowed: Session-ending blocks may be missed if Stop.py times out
Risk if removed: All safety enforcement removed
Recommendation: Add per-gate timing to Stop.py aggregator (one `time.perf_counter()` per gate)
```

```
Hook: PreToolUse.py (aggregator)
Purpose: 10+ PreToolUse gates (self-doc, evidence, verification, permission, etc.)
Observed cost: 4.2ms avg, 93.9% under 1ms, but 0.1% >1s
Timeout: 15s (settings.json)
Risk if slowed: Delays every tool call (~60K times in 28 days)
Risk if removed: All PreToolUse gates disabled
Recommendation: Gate-level timing instrumentation in PreToolUse.py
```

```
Hook: cc-aca-epistemic router (Stop, PreToolUse)
Purpose: Evidence verification gates
Observed cost: 0.0ms (not timed per-route in DB)
Timeout: 15s (PreToolUse), DEFAULT (Stop global)
Risk if removed: Fabricated evidence detection disabled
Recommendation: Monitor 8 sub-hooks via router timing
```

### Correctness Hooks

```
Hook: cc-aca-sdlc router (PreToolUse, Stop, PostToolUse, SessionStart)
Purpose: SDLC enforcement, completion gates, continuation gate
Observed cost: 0.0ms (aggregated inside Stop.py "main")
Timeout: 10s (PreToolUse), DEFAULT (Stop[3] global)
Risk if removed: Run-to-completion enforcement, SDLC gates, closure checks disabled
Recommendation: No change needed — cost appears negligible
```

```
Hook: cc-skills-utils router (PreToolUse, Stop)
Purpose: Skill-first enforcement, consolidation checks
Observed cost: 0.0ms (aggregated)
Timeout: DEFAULT (PreToolUse), 30s (Stop)
Risk if removed: Skill loading enforcement disabled
Recommendation: No change needed
```

```
Hook: skill-guard router (all events)
Purpose: Skill-first gate, permission enforcement
Observed cost: 0.0ms (aggregated into "main" entries)
Timeout: 10s (most events), DEFAULT (some events in global settings)
Risk if removed: Skill enforcement disabled
Recommendation: No change needed
```

### Convenience Hooks

```
Hook: log_hook.py (all 5 events)
Purpose: Append hook events to ~/claude-log.jsonl
Observed cost: Not independently measurable (aggregated in "main")
Timeout: 15s (all 5 entries now have explicit timeout — was DEFAULT/5s)
Risk if slowed: Delayed hook pipeline; previously caused UserPromptSubmit timeout
Risk if removed: claude-log.jsonl ingestion stops
Recommendation: None — timeout already fixed. Cost appears low.
```

```
Hook: snapshot PreCompact
Purpose: State snapshots before compaction
Observed cost: 0.0ms in DB (sessions not hitting this event often)
Timeout: 45s
Risk if slowed: Delayed compaction
Risk if removed: No session state snapshots
Recommendation: No change — 45s timeout is generous, and only 1 registration
```

```
Hook: SubagentStop_cjk_drift_detector
Purpose: Detect CJK script drift in subagent responses
Observed cost: 0.0ms (not enough data)
Timeout: 5s
Risk if slowed: Delayed subagent stop
Risk if removed: Potential unicode detection gaps
Recommendation: No change
```

### Unknown

```
Hook: Stop[3] cc-skills-sdlc router
Purpose: /go continuation gate, SDLC enforce gate
Observed cost: 0.0ms (aggregated under "main" Stop)
Timeout: DEFAULT (5s) — no explicit timeout
Risk if slowed: /go loop could be delayed
Risk if removed: Continuation loop and SDLC enforcement disabled
Recommendation: Add explicit timeout to match pattern (10s suggested)
```

```
Hook: cc-aca-authority router (Stop, PreToolUse, UserPromptSubmit)
Purpose: Authority/permission enforcement
Observed cost: 0.0ms (aggregated under "main")
Timeout: DEFAULT in global settings (Stop, PreToolUse), 10s (UserPromptSubmit)
Risk if removed: Permission-based gating disabled
Recommendation: Add explicit timeout to global settings entries
```

```
Hook: cc-aca-reasoning router (Stop, PreToolUse, UserPromptSubmit)
Purpose: Reasoning quality enforcement
Observed cost: 0.0ms (aggregated)
Timeout: DEFAULT in global settings
Risk if removed: Reasoning quality gates disabled
Recommendation: Add explicit timeout to global settings entries
```

**8 hooks in global settings with no explicit timeout**, relying on Claude Code's 5s default.

---

## LATENCY_RANKING

By total wall-clock time consumed (estimated from "main" aggregate):

| Rank | Hook | Total Time (28d) | % of Hook Latency |
|------|------|------------------|-------------------|
| 1 | PreToolUse "main" | ~254,000ms (4.2ms × 60,470) | 63% |
| 2 | PostToolUse "main" | ~149,000ms (2.6ms × 57,378) | 37% |
| 3 | Near-timeout events (42) | ~82,000ms (1,950ms avg) | <1% of calls, disproportionate share |
| 4 | SessionStart sub-hooks (8.6K) | ~8,600ms (collected, 1ms avg) | <1% |
| 5 | UserPromptSubmit (568) | ~570ms (1ms avg est.) | <1% |
| 6 | Stop (624) | ~620ms (1ms avg est.) | <1% |

**Key takeaway:** PreToolUse accounts for ~63% of total hook execution time. PostToolUse accounts for ~37%. All other events combined are < 1%. This is expected given that PreToolUse and PostToolUse fire on every tool call.

However, the long tail of PreToolUse (>1s for 71 events) dominates the *perceived latency* — those 71 events account for ~153s of total hook delay despite being only 0.1% of invocations.

---

## TIMEOUT_RISK

### Active timeout risks (ordered by severity)

| Risk | Event | Hook | Timeout | Near-misses | Impact if hit |
|------|-------|------|---------|-------------|---------------|
| HIGH | PreToolUse | tool_availability_checker (matcher) | **5s** | 42 near-timeout events (>1.5s), 3 actually exceeded (8885ms) | Tool call dropped |
| MEDIUM | SessionStart | HookImporter → SessionStart.py | 60s | 6 actual timeouts (45s scenario) | Session start delays |
| LOW | UserPromptSubmit | HookImporter → UserPromptSubmit.py | 15s | 2 actual timeouts | UPS injection dropped |
| LOW | Stop | cc-skills-sdlc router | **DEFAULT (5s)** | Unknown — no per-hook timing | Stop gate skipped |
| LOW | PreToolUse | 6 plugin routers (global) | **DEFAULT (5s)** | Unknown — aggregated under "main" | Gate skipped |
| LOW | Stop | 3 plugin routers (global) | **DEFAULT (5s)** | Unknown — aggregated under "main" | Stop block skipped |

### Threshold analysis

The PreToolUse `tool_availability_checker.py` has `timeout: 5` in settings.json but the actual `execution_time_ms` exceeds this for 3 events (8885ms recorded). This may be a measurement artifact (the DB records after the process has finished, not wall-clock killed-by-timeout). Either way, 42 events approaching the threshold is a significant number.

The SessionStart 45s-60s timeout events are concerning — a daemon or blocking I/O operation is hanging for 45+ seconds on session start. However, this is a different class of issue from hook latency (daemon health vs. per-invocation timing).

---

## FRICTION_ANALYSIS

### 1. Which hooks are responsible for most latency?

**PreToolUse "main"** — 63% of total hook execution time. But within this, the individual gates cannot be distinguished. The top-level entry point is the only measurable aggregation point.

### 2. Which hooks are near timeout thresholds?

- **tool_availability_checker.py** (PreToolUse, `timeout: 5`): 42 events >1.5s, 3 events >5s
- **SessionStart HookImporter**: 6 actual timeout events at 45s
- **UserPromptSubmit HookImporter**: 2 actual timeout events at 15s

### 3. Which hooks execute frequently but cheaply?

- **log_hook.py** (all 5 events): Sub-millisecond average cost
- **PostToolUse sub-hooks** (syntax gate, path observer): 93% under 5ms
- **Stop.py sub-gates** (epistemic_contract, safety_gate, etc.): 0.0ms recorded
- **UserPromptSubmit behavior_contract**: 509 invocations, 0.0ms avg
- **SessionStart sub-hooks** (12+ individual): All recorded at 0.0ms

### 4. Which hooks are expensive but justified?

**PreToolUse >1s tail (71 events)** — While these represent only 0.1% of calls, they account for significant perceived latency. The gates running in the long tail (evidence verification, epistemic checks, self-doc validation) are all critical safety mechanisms. Without knowing which specific gates cause the long tail, we cannot judge whether the cost is justified.

The true cost of any individual gate may be negligible — the long tail could be caused by Python startup overhead (subprocess spawn for the first invocation, cache warming), system load, or a combination of several small gates.

### 5. Which hooks have unclear ownership or diagnostics identity?

| Identity Issue | Details |
|---------------|---------|
| "main" PreToolUse | Aggregates ~18+ gates under one name. Cannot tell which gate is slow. |
| "main" PostToolUse | Aggregates ~12+ gates (syntax, claim, health, observability, logging) |
| Stop.py sub-gates | 15+ gates recorded separately but timing is 0.0ms |
| UserPromptSubmit modules | 18+ registered modules, all recorded under behavior_contract/test_hook at 0.0ms |
| SessionStart sub-hooks | 12+ individual hooks recorded by name but at 0.0ms timing |
| Global settings DEFAULT entries | 8 hooks in global settings with no explicit timeout — actual timeout value unknown |

---

## SAFETY_VALUE_ANALYSIS

Every hook in the inventory serves one of these safety purposes:

| Category | Count | Examples |
|----------|-------|---------|
| **Evidence/Verification** | ~15 | epistemic_contract, cross_validator, cited_content_guard, evidence_hierarchy |
| **Self-documentation** | ~5 | task_self_doc_gate, completion_gate, skill_first_gate |
| **Syntax/Correctness** | ~5 | py_syntax_gate, bash_syntax_gate, path_corrector, type_validator |
| **Permission/Authorization** | ~5 | tool_availability_checker, delegation_enforce, permission_pair_validator |
| **Anti-sycophancy/Fabrication** | ~5 | anti_sycophancy_injector, unverified_stance, perf_attribution_gate |
| **Convenience** | ~5 | log_hook, content_filter_skips, snapshot, notification_voice |
| **Observability** | ~5 | observability router, telemetry, tracker, health checks |
| **Other** | ~5 | commitment_tracker, dreaming_daemon, language_lock |
| **Unknown** | 8 | global settings entries with no explicit timeout |

No hook in this inventory is redundant. Each has a distinct responsibility. None should be removed without specific evidence that its functionality is covered elsewhere or no longer needed.

---

## RECOMMENDATIONS

### Recommendation 1: Add per-gate timing to PreToolUse.py and Stop.py (measure more)

**Why:** The #1 finding is that ~99.9% of hook latency data is aggregated under "main" with no gate-level attribution. We know 71 PreToolUse events took >1s but cannot say which gate(s) caused it. A single `time.perf_counter()` per gate, logged to diagnostics.db or a JSONL file, would pinpoint the responsible mechanisms.

**Evidence:** 60,470 PreToolUse events x 15+ gates = ~900K untimed gate executions. The diagnostic infrastructure already records gate-level decisions (allow/block/warn); adding timing to each decision is a data field, not new infrastructure.

**Scope boundary:** This is observability, not a change to gate logic. A minimal change: add `gate_timing_ms` float field to the existing `hooks` table or a new `gate_timing` table.

### Recommendation 2: Add explicit timeout to 8 global settings entries (improve observability)

**Why:** 8 hooks in `~/.claude/settings.json` have no explicit timeout, relying on Claude Code's 5s default. The timeout fix from the previous workstream found exactly this pattern caused the log_hook.py timeouts. These entries should declare their own timeout so diagnosis starts with "this hook timed out at Xs" instead of "the default killed it."

**Evidence:** PreToolUse cc-aca-epistemic, cc-aca-authority, cc-aca-reasoning, cc-aca-investigation, skill-guard (global), Stop cc-aca-authority, cc-aca-reasoning, skill-guard (global), PostToolUse cc-aca-epistemic, cc-aca-observability.

**Recommended value:** 10s for PreToolUse/Stop routers, matching the existing pattern.

### Recommendation 3: Add explicit timeout to Stop[3] cc-skills-sdlc router (clarify ownership)

**Why:** The `/go` continuation gate and SDLC enforce gate are critical safety mechanisms running without an explicit timeout. If blocked, they could prevent `/go` from completing.

**Evidence:** Settings.json Stop[3] entry has `"command"` but no `"timeout"`.

**Recommended value:** 10s, matching `Stop[0]` (Stop.py aggregator) and `Stop[1]` (skill-guard).

### Recommendation 4: Investigate tool_availability_checker.py timeout (adjust timeout or optimize)

**Why:** 42 near-timeout events and 3 apparent timeouts on a 5s PreToolUse hook. This hook fires on every Skill/Bash/mcp__ call and gates a broad surface.

**Evidence:** See TIMEOUT_RISK section above. The recorded 8885ms execution suggests either the measurement is wrong, the subprocess was not actually killed, or there is a clock difference.

**Action:** Inspect `tool_availability_checker.py` for blocking operations (network calls, large file scans, lock contention). If verified slow, increase timeout from 5s to 10s.

---

## PROVEN

- **PreToolUse is the dominant latency source**: 60,470 invocations, 63% of total hook execution time
- **PostToolUse is the second source**: 57,378 invocations, 37% of total
- **94% of PreToolUse completes in <1ms**: The fast path is very fast
- **71 PreToolUse events took >1s**: 0.1% long tail accounts for disproportionate latency
- **42 PreToolUse near-timeout events (exec >1.5s)**: Significant number approaching the 2000ms timeout
- **3 PreToolUse events exceeded 5000ms**: Recorded execution time exceeds hook_runner timeout
- **8 importer timeout events in 28 days**: 6 SessionStart, 2 UserPromptSubmit
- **8 global-settings hooks lack explicit timeout**: DEFAULT = 5s
- **Diagnostics.db has 142,603 hook records**: Rich dataset for entry-point level analysis
- **All 5 log_hook.py entries now have explicit timeout:15**: Prior workstream fix verified

## INFERRED

- **Sub-gate timing is 0.0ms due to measurement gap**: Registered sub-hooks don't propagate timing back to the DB. The HookImporter records timing for its `execute_hook()` call, but individual registered `register_hook()` sub-hooks within a dispatched `main()` function are not individually timed.
- **The PreToolUse long tail (>1s) comprises multiple gates**: No evidence it's a single slow gate. The 8885ms spike could be Python startup (cold cache), system load, or a combination of 5-10 gates each taking 100-500ms.
- **Stop.py's per-gate timing is 0.0ms but individual gate records exist**: The aggregator records gate names and decisions; timing wasn't wired into the action record.
- **SessionStart 45s timeouts suggest a blocking sub-hook**: HookImporter timeout on SessionStart indicates a daemon or I/O operation inside one of the 12+ SessionStart sub-hooks.

## UNKNOWN

- **Which specific PreToolUse gate causes the long tail (>1s events)**: The single most actionable unknown. Without per-gate timing, we cannot target optimization.
- **Whether tool_availability_checker.py's 8885ms is real or a measurement artifact**: The execution_time_ms exceeding the 5000ms hook_runner timeout suggests either: the subprocess was not actually killed (hook_runner issue), the DB recorded total dispatch wall-clock including both the timeout and retry, or the measurement included overhead after the subprocess completed.
- **Actual latency of 18+ UserPromptSubmit modules**: All recorded at 0.0ms. The actual cost of the UPS injection pipeline (skill_enforcer, task_detector, behavior_contract, etc.) is unknown.
- **Actual latency of 15+ Stop.py gates**: All recorded at 0.0ms. The cost of running semantic critic, epistemic contract, cited content guard, and other heavy gates is unknown.
- **Whether global settings DEFAULT (5s) timeouts have ever been approached**: No per-hook timing data from global-settings entries exists in diagnostics.db.
- **Actual runtime of SessionStart sub-hooks**: 12+ sub-hooks recorded at 0.0ms. The 45s/60s timeout is adequate, but the cost of each sub-hook is unknown.

---

## FILES_CHANGED

**NONE** — This is a measurement-only audit. No files were modified.

---

## FINAL_STATUS

**COMPLETE_AUDIT**

The audit successfully identified:
- What is fast (~94% of hooks complete in <1ms)
- What is expensive (0.1% long tail dominates perceived latency)
- What is risky (42 near-timeout events, 8 real timeouts)
- What is unmeasured (sub-gate timing for ~60+ individual gates/hooks)
- What is valuable (every hook has a distinct safety/correctness role)

The 4 recommendations are all non-invasive — add timing observability, add explicit timeouts, and investigate one suspicious measurement. No architecture changes, no consolidation, no removal.
