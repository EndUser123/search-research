# Claim Verification Hooks - Quick Reference

**Location:** `P:\.claude\hooks\`
**Created:** 2025-01-28
**Context:** Session debugging false temporal attribution claim

---

## Why These Exist

A response claimed "SessionStart_janitor.py was NOT in that list. You just deleted it now." without any git log verification. Investigation revealed two gaps:

1. **Temporal claims escaped** - claiming WHEN something happened without evidence
2. **Scope mismatch** - tools verified file A, but claims made about file B

---

## Hook Execution Order

```
PreToolUse  →  Tool Executes  →  PostToolUse  →  ... repeat ...  →  Stop Phase
                                      │
                                      ▼
                              ToolSequenceManager.append()
                              (stores name, command, output)
                                      │
                                      ▼
                              ┌───────────────────────────────┐
                              │ Stop_historical_claims_gate   │ ← Tier 1: Temporal attribution
                              │ (word intersection check)     │   "You just deleted it now"
                              └───────────────────────────────┘
                                      │
                                      ▼
                              ┌───────────────────────────────┐
                              │ assumption_audit_v2           │ ← Tier 2: Scope verification
                              │ (entity extraction + overlap) │   Claims match evidence?
                              └───────────────────────────────┘
```

**Key insight:** Tool output is now stored in ToolSequenceManager (as of 2025-01-28) so entity extraction can see what was actually observed, not just what files were targeted.

---

## Current Response Flow (2026-02-11)

This stack now uses a proactive + reactive model:

1. **UserPromptSubmit preflight (proactive):**
   - `UserPromptSubmit_router.py` injects an empirical precheck when applicable.
   - Required response structure:
     - `Observed:` facts from tool output
     - `Inferred:` conclusions derived from observed evidence
     - `Unknown:` unverified items
   - Hard rule: causal claims require at least one observed traceback/log line.

2. **Stop hooks (reactive):**
   - `Stop_historical_claims_gate.py` catches temporal attribution claims.
   - `assumption_audit_v2.py` catches claim/evidence scope mismatch.

This significantly reduces post-generation block churn compared to Stop-only enforcement.

---

## The Two Hooks

### Stop_historical_claims_gate.py v3.4 (Syntactic-Empirical Hybrid)

**Catches:** 
- Temporal attribution claims ("I ran tests", "I added that earlier")
- Fake state-transition narratives ("It worked before, but now it fails")
- Hallucinated tool discovery ("I checked earlier with which gh")

**The Hybrid Mechanism:**
1. **Syntactic Layer (The "Tell"):** Fast deterministic regex matches linguistic markers of deception (e.g., "it used to be found").
2. **Empirical Layer (The "Truth"):** Cross-references matched phrases against the **Unified Evidence Ledger**.
3. **Heuristic Layer (The "Bridge"):** Translates raw tool output (Exit code 127) into semantic state (Failure vs Success) to verify claims about specific entities (gh, git, etc.).
4. **Cognitive Layer (The "Enforcement"):** If a claim exists without ledger support, triggers a self-evaluation prompt that exposes missing evidence types.

**Required for State Transitions:** 
Paired evidence (one success + one failure for the same entity) must exist in the session ledger to allow a "now it's failing" narrative.

**If blocked:** 
- Provide the missing evidence (e.g., run `which gh`)
- Or remove the historical claim and admit the current environment failure honestly.

### assumption_audit_v2.py v2.3.1

**Catches:** Scope mismatch between claims and evidence
- Claim about file A when only file B was read
- "All 5 files fixed" when only 2 verified

**Mechanism:** Entity extraction + overlap check (50% threshold for 3+ entities)

**If blocked:** Read/verify the specific files mentioned in the claim

---

## Tuning Parameters

```powershell
# Disable scope checking entirely (rollback)
$env:CLAIM_SCOPE_CHECK_ENABLED = "false"

# Adjust coverage threshold (default 0.5 = 50%)
$env:CLAIM_COVERAGE_THRESHOLD = "0.3"

# Enable debug logging
$env:ASSUMPTION_AUDIT_V2_DEBUG = "true"

# Enable/disable proactive empirical precheck injection
$env:EMPIRICAL_CLAIMS_PRECHECK_ENABLED = "true"

# Unparseable mutation handling:
# - "warn"  = allow with warning + rewrite guidance
# - "block" = hard-block opaque python -c file/config mutations
$env:UNPARSEABLE_MUTATION_MODE = "warn"
```

---

## If False Positive Rate Too High

1. Check logs: `P:\.claude\hooks\logs\assumption_audit_v2.jsonl`
2. Look for `SCOPE_MISMATCH` blocks with legitimate evidence
3. Options:
   - Lower threshold: `CLAIM_COVERAGE_THRESHOLD=0.3`
   - Add words to `COMMON_WORDS` filter
   - Disable temporarily: `CLAIM_SCOPE_CHECK_ENABLED=false`

---

## If Blocks Seem Wrong

The claim entity extraction may miss indirect references:
- "The janitor script" won't match `SessionStart_janitor.py`
- "That function" won't match `cleanup_dead_code()`

**Fix:** Be explicit in claims. Name the actual file/function.

---

## Test Files

```powershell
python P:\.claude\hooks\tests\test_stop_historical_claims.py
python P:\.claude\hooks\tests\test_assumption_audit_v2_scope.py
```

---

## Decision History

- **Original bug:** Temporal claim without git verification
- **First fix:** Stop_historical_claims_gate v3.0 (catches "just deleted")
- **Second fix:** assumption_audit_v2 v2.3.1 (catches scope mismatch)
- **Key insight:** These are different failure modes, both needed

---

## Transcript Reference

Full debugging session: `/mnt/transcripts/2025-01-28-*-temporal-claims-hook-implementation.txt`
