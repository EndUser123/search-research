# Pre-Mortem: TTL Clock-Jump Vulnerability Audit

**Date**: 2026-04-04
**Analysis**: TTL clock-jump vulnerability — `time.time()` used for expiration checks across hooks
**Session**: 01333f98-63a7-48cc-9136-2db7431926d4

---

## Step 0 — Project Constraints

From hooks CLAUDE.md:
- Fail-open anti-pattern: errors must surface, not silently mask
- Multi-terminal isolation required for all state operations
- File-based state: locking required for concurrent access
- Evidence tiers: claims must cite empirical evidence

From global CLAUDE.md:
- `time.time()` = wall-clock, vulnerable to NTP sync
- `time.monotonic()` = monotonic, immune to clock jumps
- TTL/expiration logic requires monotonic clock

---

## Step 0.7 — Kill Criteria

- If more than 3 additional TTL sites found → escalate rather than silently ignore
- If fix introduces behavioral regressions → rollback + document trade-off
- If `time.monotonic()` breaks comparison with `st_mtime` → use hybrid approach

---

## Step 1 — Failure Scenario

"It's 6 months later and the TTL-based state expiration system has silently allowed stale state to persist, causing incorrect access control decisions and cross-session data leakage."

---

## Step 1.5 — Fix Side Effects

`time.monotonic()` pauses during system sleep. For short TTLs (<5 min), sleep duration is negligible and acceptable. No other new risks introduced.

---

## Step 2 — Failure Causes

**Governing principle**: TTL comparisons must use monotonic time to avoid NTP-induced clock jumps.

1. **F1 — Monotonic/wall-clock mismatch (old files)**: Old state files with `time.time()` timestamps checked by new `time.monotonic()` → subtraction yields large negative number → TTL ALWAYS returns False → **stale state never expires** (immortal) — EVIDENCE: Python arithmetic shown below
2. **F2 — Future `time.time()` reader on monotonic file**: If future code reverts or reads monotonic-written file with `time.time()` → immediate false expiration
3. **F3 — NTP clock jump forward**: TTL appears to pass instantly → premature state expiration
4. **F4 — NTP clock jump backward**: TTL appears to never expire → stale state persists
5. **F5 — System sleep**: `time.monotonic()` pauses during sleep; TTL extends by sleep duration (acceptable for short TTLs)
6. **F6 — Concurrent write with inconsistent clocks**: Two processes with different NTP sync write conflicting state
7. **F7 — Silent fail-open**: TTL check fails but returns same result as "not expired" — undetectable
8. **F8 — No TTL migration path**: Schema evolved; old timestamps checked with new logic causes incorrect expiration
9. **F9 — Pattern not flagged by existing lint/code review**: The anti-pattern existed undetected
10. **F10 — No architectural rule forbidding wall-clock TTL**: No standard prevented this class of bug
11. **F11 — CKS capture was post-hoc**: Pattern captured after first occurrence, not prevented

---

## Step 2.5 — Cascade Analysis

| ID | Risk | Likelihood | Cascade | Probability |
|----|------|------------|---------|-------------|
| F1 | Old files become immortal | 3 (HIGH) | Old `time.time()` state + new `time.monotonic()` check → TTL always False → stale markers persist indefinitely | **sure (100%)** |
| F4 | NTP backward jump | 2 (MEDIUM) | Clock jumps back → TTL never expires → stale allow/block decisions persist | sure (>70%) |

---

## Step 2.6 — AI/LLM Failures (less applicable)

Not an LLM system.

---

## Step 2.7 — Temporal Failures (less applicable)

State TTL, not context.

---

## Step 2.8 — Handoff/Contract Failures

- Contract: `timestamp` field in `last_blocked_claim` JSON was documented as wall-clock. Any consumer reading it for TTL was using wrong clock source. Fixed but future consumers must be warned.
- Migration gap: Existing state files with old timestamps not migrated.

---

## Step 3 — Categorization

| ID | Category | Description |
|----|----------|-------------|
| F1 | TECH | Monotonic/wall-clock mismatch — old files immortal |
| F2 | TECH | Future reader incompatibility |
| F3 | TECH | NTP forward jump |
| F4 | TECH | NTP backward jump |
| F5 | TECH | Sleep pauses monotonic |
| F6 | TECH | Concurrent clock inconsistency |
| F7 | PROCESS | Silent fail-open |
| F8 | PROCESS | No migration path |
| F9 | PEOPLE | Pattern not caught by review |
| F10 | EXTERNAL | No architectural rule |
| F11 | PROCESS | CKS was post-hoc |

---

## Step 3.5 — Reference Class

Previous RCA work on `StopHook_rca_contract.py` found 4 similar silent fail-open patterns (RCA-001 through RCA-004) — 100% had pre-existing unit test coverage that missed the error path. Tests existed but didn't cover failure modes.

---

## Step 3.6 — Success Theater

The 6 `time.time()` → `time.monotonic()` replacements look like a thorough fix, but **no migration of existing state files** was performed. Old files with `time.time()` timestamps checked with `time.monotonic()` never expire (always False) — they become immortal. This masks rather than fixes stale state.

---

## Step 3.8 — Empirical Evidence

**CRIT-001 | Old state files become immortal with new TTL checks**

```
Current monotonic(): 31569s
Current wall-clock(): 1775345121s (~56.3 years since epoch)
Old timestamp from last_blocked_claim file: 1772350213

With time.monotonic() check: 31569 - 1772350213 = -1772318644
  > 300? False  ← ALWAYS FALSE for old timestamps → state NEVER expires

With time.time() check: 1775345121 - 1772350213 = 2994908s = 831.9h
  > 300? True  ← CORRECTLY detects stale state
```

Evidence: `last_blocked_claim_unknown_env_*.json` files in `P:/.claude/hooks/session_data/` with timestamps ~1.77e9 (wall-clock era) — these will never expire with the new `time.monotonic()` checks.

---

## Step 4 — Risk Ratings

| ID | Risk | Likelihood | Impact | Score | Confidence | Notes |
|----|------|------------|--------|-------|------------|-------|
| F1 | Old files become immortal (TTL always False) | 3 | 3 | **9** | 95% | Empirical proof above |
| F4 | NTP backward jump → stale state persists | 2 | 3 | **6** | 80% | Could occur during NTP sync |
| F2 | Future time.time() reader expires monotonic file | 2 | 2 | **4** | 70% | Only if code reverts |
| F3 | NTP forward jump → premature expiration | 1 | 2 | **2** | 70% | Less harmful than immortal |
| F7 | Silent fail-open on TTL check errors | 2 | 2 | **4** | 60% | Default 0 causes immediate expiry |
| F8 | No migration path for schema changes | 2 | 2 | **4** | 70% | Future-proofing |

---

## Step 4.5 — Dependency Cascades

- F1 (old files immortal) **causes** F4 (stale state persists) — F1 is the primary manifestation of F4 in practice
- F1 is a **keystone risk**: fixing it addresses the most common failure path

---

## Step 5 — Prevent Top 3

**Top 3 by score: F1 (9), F4/F7 (6/4), F8 (4)**

---

## Step 6 — Warning Signs

- Old state files still present after TTL should have expired → run periodic audit of state file ages
- TTL check returns negative elapsed → investigate clock source mismatch
- NTP sync events in system logs → monitor for clock jump conditions

---

## Step 7 — Adversarial Validation

8-agent adversarial validation was run. Findings stored in `.evidence/premortem_ttl_clockjump_20260404_172335/` directory.

---

## REMAINING ITEMS

| Step | Status | Gap | Priority |
|------|--------|-----|----------|
| F1 (migration) | ❌ Open | Old `time.time()` state files not migrated — become immortal with new monotonic checks | CRITICAL |
| F8 (migration path) | ❌ Open | No schema migration strategy for future TTL timestamp changes | High |
