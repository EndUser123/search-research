---
doc_type: architecture
tracks:
  - ".claude/hooks/*.py"
  - ".claude/hooks/hook_tracker.py"
  - ".claude/settings.json"
significance:
  min_lines_changed: 5
  exclude_tests: true
sync_trigger: write
---

# Hook Architecture Document

**Last updated:** 2026-03-16
**Version:** 2.6
**Purpose:** Map constitutional enforcement hooks, identify gaps, track recommendations

> **2026-03-17 Audit:** Ghost file references resolved. 17 stale file paths corrected — 4 moved/renamed (updated paths), 6 archived (marked ⚠️), 4 fully removed (retired with no replacement), 2 merged into existing hooks, 1 documentation reference fixed (standards.md → verification_tiers.md). See enforcement map Status column for current state of each hook.

---

## Overview

Claude Code hooks provide **deterministic control**. This document maps the constitutional hook infrastructure added for enforcing CLAUDE.md rules structurally.

For detailed detection patterns (TAV, Regex, etc.), see: [docs/HOOK_DETECTION_PATTERNS.md](docs/HOOK_DETECTION_PATTERNS.md).

---

## Constitutional Infrastructure Module

### `hook_tracker.py` - Shared Infrastructure

All constitutional hooks use this shared module for consistent behavior:

| Function                                 | Purpose                                                                      |
| ---------------------------------------- | ---------------------------------------------------------------------------- |
| `is_hook_self_operation(command)`        | Allow commands that modify hooks themselves (Catch-22 prevention)            |
| `is_bypass_enabled()`                    | Check `CONSTITUTIONAL_HOOKS_BYPASS` environment variable                     |
| `is_test_pattern(command)`               | Detect test commands (pytest env, test probes) to exclude from logging       |
| `log_block(hook, tool, command, reason)` | Log to `logs/constructional_blocks.jsonl` for analysis (skips test patterns) |
| `get_session_summary()`                  | Get session violation counts for Stop hook notification                      |

**Bypass mechanism:**

```bash
export CONSTITUTIONAL_HOOKS_BYPASS=1  # Disable all constitutional hooks
```

### `cc_diagnostic_logger.py` - Structured Logging Infrastructure

All constitutional hooks use standardized JSONL logging for enforcement decisions and orchestration tracking. *(Renamed from buffered_logger.py.)*

| Function | Purpose |
|----------|---------|
| `get_enforcement_logger()` | Get logger for enforcement decisions (blocks, warnings) |
| `get_hook_invocation_logger()` | Get logger for router orchestration |
| `create_hook_entry(hook_name, hook_type, decision, ...)` | Create standardized log entry |
| `create_router_entry(router_name, hook_type, tool_name, ...)` | Create router orchestration entry |
| `get_session_id()` | Auto-populate session ID from environment |
| `get_terminal_id()` | Auto-populate terminal ID for session isolation |

**Log files:**
- `logs/enforcement.jsonl` — Enforcement decisions (7-day retention)
- `logs/diagnostics/hook_invocations.jsonl` — Router orchestration (1-day retention)
- `logs/diagnostics/decisions.jsonl` — Decision audit trail (3-day retention)

**See:** `docs/LOGGING_STANDARD.md` for complete schema documentation

---

## Notification Strategy

**Triggered by:** Stop.py IN_PROCESS_GATES (after every response)

| Threshold            | Display       | Example                            |
| -------------------- | ------------- | ---------------------------------- |
| CRITICAL block (any) | Immediate     | 🚨 HOOK ALERT: 1 CRITICAL block(s) |
| WARN ≥3/session      | Next response | ⚠️ Hook violations this session: 5 |
| WARN <3/session      | Silent        | (no notification)                  |
| Full analysis        | Weekly        | `analyze_blocks.py`                |

**Rationale:**

- CRITICAL blocks (Catch-22, eval/exec) need immediate attention
- WARN pattern spike (3+) indicates emerging problem worth flagging
- Below threshold = noise, don't interrupt flow
- Weekly deep-dive for trends and pattern adjustment

---

## Constitutional Enforcement Map

| Constitutional Rule   | Hook                                      | Event       | Mode      | Source                        | Status   |
| --------------------- | ----------------------------------------- | ----------- | --------- | ----------------------------- | -------- |
| Anti-Sycophancy       | constitutional_enforcer.py                | Stop        | BLOCK     | CLAUDE.md Part A              | ✅ Active |
| Evidence Tiers        | empirical_claims_gate.py                  | Stop        | BLOCK     | verification_tiers.md          | ⚠️ Archived (disabled in router) |
| Uninvestigated Qs     | Stop_pre_clarification_gate.py            | Stop        | SOFT      | CLAUDE.md Part D (v2.0)       | ⚠️ Archived (see investigation-ledger/) |
| Success Validation    | stop_success_validator.py                 | Stop        | BLOCK     | verification_tiers.md          | ⚠️ Archived (disabled in router) |
| Spec Compliance       | StopHook_spec_compliance.py               | Stop        | BLOCK     | CLAUDE.md Spec Compliance     | ❌ Removed |
| Green State Axiom     | StopHook_green_state_validator.py         | Stop        | WARN      | CLAUDE.md Green State         | ❌ Removed |
| Anti-Hallucination    | posttooluse/truth_validator_hook.py       | PostToolUse | BLOCK     | CLAUDE.md Part M              | ✅ Active (moved from truth_validator.py) |
| Vague Directive       | PreToolUse_vague_directive_gate.py        | PreToolUse  | BLOCK     | CLAUDE.md Vague Directive     | ⚠️ Archived |
| Complex Shell         | shell_complexity_gate.py                  | PreToolUse  | WARN      | CLAUDE.md J.5                 | ⚠️ Archived |
| Unparseable Cmd       | unparseable_command_gate.py               | PreToolUse  | SELECTIVE | CLAUDE.md C.1                 | ⚠️ Archived |
| Catch-22 Detection    | recursive_failure_detector.py             | PreToolUse  | BLOCK     | CLAUDE.md D.5                 | ✅ Active |
| Architecture Evidence | architecture_evidence_gate.py             | Stop        | SELECTIVE | verification_tiers.md          | ⚠️ Archived (disabled in router) |
| Effectiveness Priority| constitutional_enforcer.py                | Stop        | BLOCK     | CLAUDE.md Efficiency          | ✅ Active (merged from StopHook_closure_enforcer.py) |
| Lazy Fix Detection    | Stop.py (`anti_sycophancy_quality`)       | Stop        | SOFT      | userPreferences Mode 1        | ✅ Active |
| Behavioral Quality    | Stop_reasoning_quality_gate.py            | Stop        | SOFT      | userPreferences Investigation | ✅ Active (renamed from StopHook_behavioral_quality_gate) |
| Investigation Ledger  | investigation-ledger/Stop_*               | Stop        | BLOCK     | verification_tiers.md          | ✅ Active |
| Assumption Audit v2   | assumption_audit_v2.py                    | Stop        | BLOCK     | verification_tiers.md          | ✅ Active |
| Historical Claims     | Stop_historical_claims_gate.py            | Stop        | BLOCK     | CLAUDE.md Historical Claims   | ⚠️ Archived |

> **Legend:** ✅ Active = file exists and runs | ⚠️ Archived = logic preserved in `_archive/` but not active | ❌ Removed = fully retired, no replacement
>
> **Removed rows** (no file or replacement): `PreToolUse_tdd_gate.py` (TDD Mandate), `StopHook_reality_check.py` (Reality Verification / Complete Solutions), `StopHook_investigation_required` (Investigation Required), `posttooluse/tool_thrashing_tracker` (Tool Thrashing) — all archived and retired.

---

## Mode Definitions

| Mode      | Behavior                                              |
| --------- | ----------------------------------------------------- |
| BLOCK     | Prevents action                                       |
| WARN      | Logs but allows                                       |
| SELECTIVE | BLOCK severe, WARN moderate                           |
| SOFT      | Injects LLM self-prompt for reflection (doesn't block)|
| TRACK     | Silent state tracking for other hooks to consume      |

---

## Evidence Scope Notes (2026-02)

- `PostToolUse_router.py` writes tool sequence entries with both `session_id` and `terminal_id`.
- `assumption_audit_v2.py` now reads tool evidence via filtered sequence loading (`session_id` + `terminal_id`) instead of unscoped global reads.
- `tool_sequence_manager.py` remains a single file store (`session_data/current_tool_sequence.json`) but consumers now apply scope filters to avoid cross-session contamination.
- `empirical_claims_gate.py` caches observed paths per session/prompt hash (`EMPIRICAL_OBSERVATION_CACHE_TTL_SECONDS`, default 1800) to reduce repeated false misses on already-observed paths.

> **2026-05-07:** `Stop_router.py` has been consolidated into Stop.py as in-process gates. Notification strategy now triggered by Stop.py IN_PROCESS_GATES.

---

## Constitutional Hooks Detail

### shell_complexity_gate.py

**Enforces:** CLAUDE.md Part J.5 (File Modification Protocol)

**Patterns detected (log-only, does not block):**

- Multiline python -c (escaped newlines)
- python -c with >200 chars
- Complex sed substitutions (>30 char patterns)
- Heredocs (EOF, END, cat <<)
- Multiline echo/printf (3+ lines)
- echo -e with >100 chars

**Why log-only:** Complex shell patterns are prone to escaping failures but not inherently malicious. Warning allows developer discretion while providing guidance.

### unparseable_command_gate.py

**Enforces:** CLAUDE.md Part C.1 (Fundamental Unsolvability)

**HARD BLOCK patterns (security-relevant):**

- `eval()` - enables arbitrary expression execution
- `exec()` - enables arbitrary code execution
- Complex `$()` command substitution (>20 chars) - enables injection

**WARNING patterns (logged but allowed):**

- `python -c`, `bash -c`, `sh -c` - executes arbitrary code
- Complex backtick substitution
- `find -exec` with placeholder
- `xargs` with interpreter

**Safe pattern whitelist:**

- Simple version checks (python -c "print(...)")
- Short command substitutions (which, pwd, date)
- Internal hook operations (hook_tracker, session_summary, enhancement_router)

**File mutation blocks (.py scatter prevention):**

- Blocks: `open('test.py', 'w')`, `open('random.py', 'w')`, scattered .py writes
- Allows: canonical paths (tests/, src/, scripts/, .staging/, config/, tools/, \_\_csf.nip/)

### recursive_failure_detector.py

**Enforces:** CLAUDE.md Part D.5 (Catch-22 Detection)

**Behavior:**

- Tracks command failures per session
- Computes normalized command hash (strips variable content)
- Blocks after 2+ similar failures within 10 minutes
- Shows recent error snippets in block message

**Companion:** `posttooluse/failure_recorder_hook.py` (PostToolUse) records failures for detection *(previously failure_recorder.py at root)*

---

## Proven Patterns

### Syntactic-Empirical Hybrid Detection (The TAV Standard)

**Purpose:** Detect historical fabrications and "fake state transitions" by cross-referencing linguistic "tells" with the evidence ledger.

**Mechanism (Trigger-Audit-Verdict):**
1. **Syntactic Trigger:** Fast regex identifies phrases like "I ran tests" or "it worked before."
2. **Layered Audit:** If triggered, the hook cross-references the **Unified Evidence Ledger** (`evidence_items`) using exact matching, heuristic mapping, and optional ML/embeddings.
3. **Verdict:** Confirmed (Allow), Contradicted (Hard Block), or Silent (Soft Block).

**Used in:** `Stop_historical_claims_gate.py` ⚠️ *Archived — TAV pattern preserved in `_archive/` for re-implementation reference*

### Companion Hook Pattern

**Purpose:** Detect patterns across tool execution by pairing PreToolUse check with PostToolUse recording.

**Example:** `recursive_failure_detector.py` + `posttooluse/failure_recorder_hook.py` *(previously failure_recorder.py at root — moved to posttooluse/)*

```python
# PreToolUse (check before execution)
def check_for_catch22(tool: str, command: str) -> dict:
    cmd_hash = compute_command_hash(command)
    failure_count = count_similar_failures(tool, cmd_hash)
    if failure_count >= FAILURE_THRESHOLD:
        return {"block": True, "message": f"Catch-22: {failure_count} failures"}
    return {"allow": True}

# PostToolUse (record after execution)
def record_failure(tool: str, command: str, exit_code: int):
    if exit_code != 0:
        cmd_hash = compute_command_hash(command)
        save_failure(tool, cmd_hash, extract_error(output))
```

**Use cases:**

- Catch-22 loop detection
- Repeated error tracking
- Rate limiting
- Temporal pattern analysis

### Constitutional Hook Template

All three constitutional hooks follow this pattern:

```python
from hook_tracker import log_block, is_hook_self_operation, is_bypass_enabled

def check_command(command: str) -> dict:
    # 1. Self-exemption for hook maintenance
    if is_hook_self_operation(command):
        return {"allow": True}

    # 2. Bypass for explicit override
    if is_bypass_enabled():
        return {"allow": True}

    # 3. Perform check, log if blocking
    if violation_detected:
        log_block("hook_name", "Bash", command, "reason")
        return {"block": True, "message": "..."}

    return {"allow": True}
```

**Key principles:**

- Self-exemption prevents Catch-22 when fixing hooks
- Bypass allows explicit user override
- Logging provides audit trail and analysis data
- Mode matching ensures consistency across layers

### Speculative Claim Detection

**Updated 2026-01-14** *(originally in `empirical_claims_gate.py`, now via `assumption_audit_v2.py`):*
Detects and blocks hedged language that makes empirical assertions without observation.

- **Patterns**: "Assuming X exists", "Based on code structure", "It appears to handle"
- **Reasoning**: Prevents the agent from evading evidence requirements by using "seems to" or "likely" to describe behavior they haven't actually observed.

### Path Grounding Check (Entity-Based Verification)

**Added 2026-01-17** *(originally in `empirical_claims_gate.py`, now via `assumption_audit_v2.py`):*
Entity-based path grounding verification (v1.3.0).

**Why it's more robust than regex claim detection:**
- Path extraction is **deterministic** (easy to match `commands/` or `P:/.claude/...`)
- Works **regardless of claim phrasing** ("it's looking for...", "expects...", "finds...")
- Low false positives (legitimate paths will have been read)

**How it works:**
1. **Extract path references** from response (`commands/`, `skills/duf`, `.claude/hooks`, etc.)
2. **Extract system component terms** (`skill routing`, `command discovery`, etc.)
3. **Compare against tool call history** - what was actually Read/Glob/Grep'd
4. **Block if ungrounded** - path was referenced but not observed

**Covered patterns:**
| Pattern Type | Examples |
|--------------|----------|
| Full paths | `P:/.claude/commands/`, `C:/Users/...` |
| Relative dirs | `commands/`, `skills/`, `hooks/` |
| Config refs | `.claude/skills/duf/SKILL.md` |
| System terms | "skill routing", "command discovery", "hook system" |

**Integration:**
- Runs after phantom skill check, before regex claim detection
- Provides layered defense with speculative claim detection

### Stop_pre_clarification_gate.py (Uninvestigated Question Detector) ⚠️ *Archived*

> **Status (2026-03-16):** This hook has been archived. Uninvestigated-question detection is now handled by `investigation-ledger/Stop_investigation_validator.py`. The design patterns documented below remain valid as reference.

**Added 2026-01-24 (v2.0.0)** - Complete rewrite from regex to structural detection.

**Enforces:** CLAUDE.md Part D (Investigation Gate), User Preferences (Investigate-First)

**Why structural is superior to regex:**

| Approach | "Have pytest?" | "Is X installed?" | New phrasing | Maintenance |
|----------|---------------|-------------------|--------------|-------------|
| Regex (v1) | ❌ Missed | ❌ Missed | ❌ Needs pattern | Endless |
| Structural (v2) | ✅ Caught | ✅ Caught | ✅ Auto-caught | Zero |

**Structural detection logic:**

```python
def should_trigger(response: str, tools_used: list) -> bool:
    # 1. Response contains question?
    question = extract_question_portion(response)
    if not question:
        return False  # No question, nothing to check

    # 2. User preference question? (appropriate to ask)
    if is_user_preference_question(question):
        return False  # "Would you like...", "Do you prefer..." are fine

    # 3. Investigation tools used?
    if any(t['name'] in INVESTIGATION_TOOLS for t in tools_used):
        return False  # Already investigated

    # 4. Question without investigation = trigger
    return True
```

**LLM self-prompt (SOFT mode):**

Instead of hard blocking, injects a self-reflection prompt:

```
**UNINVESTIGATED QUESTION CHECK**

You asked the user a question without first using investigation tools:
> "Have pytest available in your PATH?"

**Answer honestly:**
1. Is this verifiable via tools? (which, cat, Read, grep, --version)
2. If verifiable: Why didn't you check first?
3. If NOT verifiable (user preference/context): That's fine.

Principle: "Before proposing ANY solution: Identify → Read → Map → Check"
```

**Why self-prompt works:**
- LLM already knows if question is lazy - just needs honest reflection
- Zero additional cost (Claude Code IS the LLM)
- Handles nuance better than hard block (user preference Qs are legitimate)
- Educational: teaches the pattern rather than just blocking

**Investigation tools recognized:**
- Read, read_file, Grep, grep, Search, search, Glob, glob
- Bash (when containing: cat, head, tail, grep, find, which, where, --version, --help)
- list_directory, WebFetch, WebSearch

**User preference patterns (excluded):**
- "Would you like...", "Do you want...", "Do you prefer..."
- "Should I...", "How would you like..."
- "What is your preference/goal/budget/timeline?"

**Companion hook:** `empirical_claims_gate.py` ⚠️ *Archived* — was disabled in router; claim detection now via `assumption_audit_v2.py`

**Log file:** `logs/uninvestigated_question.log`
**Env:** `PRE_CLARIFICATION_GATE_ENABLED` (default: true)

---

## Gaps and Opportunities

| Gap                             | Impact | Status      | Recommendation                                                                       |
| ------------------------------- | ------ | ----------- | ------------------------------------------------------------------------------------ |
| Diagnostic Integration          | MEDIUM | Open        | Integrate `hook_diagnostics.py` with `hook_tracker.py` for unified problem detection |
| YAML Config for Patterns        | LOW    | Not Started | Move hardcoded patterns to YAML for easier modification                              |
| Companion Pattern Documentation | LOW    | Fixed       | Documented in Proven Patterns section                                                |
| CKS Knowledge Persistence       | LOW    | Partial     | Ingest hook architecture into CKS for session-boundary awareness                     |

---

## Hook Registration Summary

**From `settings.json`:**

Constitutional hooks registered at Layer 0 for Bash tool:

- `recursive_failure_detector.py` (timeout: 3s, critical: true) — ✅ Active

> **Archived (removed from settings.json):** `shell_complexity_gate.py` and `unparseable_command_gate.py` were previously registered here but have been archived to `_archive/`. Their logic is preserved but no longer runs automatically.

Active hooks run before other bash hooks (`bash_router` at Layer 1).

---

## Related Files

| File                                        | Purpose                                                                     |
| ------------------------------------------- | --------------------------------------------------------------------------- |
| `hook_tracker.py`                           | Shared infrastructure for constitutional hooks                              |
| `posttooluse/failure_recorder_hook.py`      | PostToolUse companion for recursive_failure_detector *(was failure_recorder.py at root)* |
| `cc_diagnostic_logger.py`                   | Structured JSONL logging for enforcement decisions *(was buffered_logger.py)* |
| `hook_diagnostics.py`                       | Universal diagnostics (not yet integrated)                                  |
| `tdd_diagnostics.py`                        | TDD-specific problem detection                                              |
| `archive/TDD_PROBLEMS_AND_FIXES.md`         | TDD problem recovery documentation                                          |
| `investigation-ledger/Stop_investigation_validator.py` | Replaces archived Stop_pre_clarification_gate                    |

---

**Constitutional Enforcement is Non-Negotiable.**

---

## Behavioral Protocol Contracts (Phase 0 Baseline)

**Added 2026-02-07:** Evidence tier and confidence ceiling contracts for behavioral hooks modernization.

### Evidence Tier Taxonomy (Resolved Decision #2)

**Source:** CLAUDE.md v8.0 Evidence Tiers (lines 34-45)

| Tier | Ceiling | Sources | Use Case |
|------|---------|---------|----------|
| 1 | 95% | Execution artifacts, logs, test output | High-stakes enforcement |
| 2 | 85% | Official docs, specs, peer-reviewed | Technical decisions |
| 3 | 75% | Static analysis, logical derivation | Architecture analysis |
| 4 | 50% | Comments, unverified claims | Flag as [UNVERIFIED] |

**Rules:**
- High-stakes requires Tier 1/2
- Mixed tiers: ceiling = lowest tier used
- Tier 4 alone: flag as [UNVERIFIED]

**Implementation:** Reference CLAUDE.md tiers in behavioral_protocol.py; no new taxonomy needed.

### Confidence Ceiling Protocol

**Purpose:** Prevent overconfident enforcement on weak evidence.

**Protocol:**
```python
from behavioral_protocol import calculate_confidence_ceiling

# Tier 1: Execution artifacts, logs
ceiling = 0.95

# Tier 2: Official docs, specs
ceiling = 0.85

# Tier 3: Static analysis, derivation
ceiling = 0.75

# Tier 4: Comments, unverified
ceiling = 0.50

# Mixed tiers: lowest wins
ceiling = min(tier_ceilings)

# Flag unverified
if lowest_tier == 4 and len(tier_sources) == 1:
    confidence_label = "[UNVERIFIED]"
```

**Implementation Location:** `P:/.claude/hooks/__lib/behavioral_protocol.py` (Phase 1)

### Feature Flag Storage (Resolved Decision #4)

**Resolution:** Both `settings.json` (source of truth) + environment variables (override)

**Pattern:**
```python
# 1. settings.json as default/source of truth
{
  "BEHAVIORAL_GOAL_ANCHOR_ENABLED": true,
  "INPROCESS_HOOK_DISPATCH_ENABLED": false
}

# 2. Environment variable override (if set, takes precedence)
# Example: BEHAVIORAL_GOAL_ANCHOR_ENABLED=false
```

**Rationale:**
- Solo-dev: defaults in file, override in terminal when needed
- Testing: set env var without editing config
- Documentation: settings.json is discoverable, env vars are explicit

**Implementation:**
- Read settings.json on startup
- Check os.environ for override (if present, use env value)
- Fallback to settings.json default if env var not set

### Baseline Metrics (Phase 0)

**Date:** 2026-02-07
**Sample:** N=20,990 entries (7 days of hook_decisions_*.jsonl)

| Metric | Baseline | Target (Success Criteria) | Gap |
|--------|----------|----------------------------|-----|
| Stop Router Calls | 5,268 | - | - |
| Block Decisions | 0 | - | - |
| Response Length p95 | 2,001 chars | <200ms latency | Measure in ms |
| Claim Snippet Coverage | 74% | 95% compliance | +21% |
| False Positive Rate | Baseline TBD | -40% reduction | TBD |

**Test File:** `P:/.claude/hooks/tests/test_hook_baseline_metrics.py`

**Baseline Report Command:**
```bash
cd P:\.claude\hooks && python tests/test_hook_baseline_metrics.py
```

### Rollback Time Target

**Success Criterion #5:** Rollback time < 5 minutes via flags only

**Verification:**
- Phase 1: < 2 minutes (goal anchor consolidation)
- Phase 2: < 1 minute (deterministic enforcement)
- Phase 3: < 3 minutes (in-process migration)

**Rollback Methods:**
- Feature flags: `BEHAVIORAL_*_ENABLED=false`, `INPROCESS_HOOK_DISPATCH_ENABLED=false`
- Nuclear option: `git revert HEAD` or `git reset --hard <commit-hash>`

---

## Proven Patterns
