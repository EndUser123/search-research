# Pre-Mortem: Dynamic Skill Suggestions for /main Health Check

**Target**: `P:\.claude\skills\main\scripts\main_health.py`
**Date**: 2026-03-28
**Analyst**: Claude (solo dev)

---

## Step 0: Project Constraints (from CLAUDE.md)

- Solo developer environment, 75-85% reliability target
- Fail fast, surface problems immediately
- Truthfulness > agreement
- Evidence-first verification
- Investigation before diagnosis
- Subagent delegation for non-trivial work
- Hooks handle enforcement structurally
- Sequential file operations (one at a time to avoid race conditions)
- Pattern changes need test corpus to prevent "fixed one, broke three"

---

## Step 0.7: Kill Criteria

- If pattern matching produces false positives (wrong suggestions) >20% of the time → refine patterns
- If suggestion overhead adds >200ms to health check run time → defer to --suggest flag only
- If SUGGESTION_MAP grows >50 entries → redesign to GTO-based approach
- If 3+ checks silently fail to produce suggestions → rollback to static suggest array

---

## Step 1: Failure Scenario

**"It's 6 months later and the dynamic skill suggestions feature has FAILED. The /main health check is giving terrible advice — suggesting the wrong skills, missing critical issues, and users have lost trust in /main output. Why?"**

---

## Step 1.5: Fix Side Effects (NEW risks from this fix)

The implementation adds:
- `HealthFinding` dataclass — frozen=True means immutable, no future extension without refactor
- `_SUGGESTION_MAP` dict — grows over time, potential maintenance burden
- Inline `💡 Run` output — changes user-facing output format
- `--suggest` flag — new CLI surface, must be documented
- JSON field added — backward compat but consumers may not handle new field gracefully

---

## Step 2: Brainstorm Causes (10+)

### People
1. **Pattern drift**: Check outputs change over time (e.g., "orphaned" → "unused env var"), breaking pattern matches
2. **Skill name churn**: Skills get renamed/deprecated but SUGGESTION_MAP still references old names
3. **Over-trust**: Users blindly follow suggestions without understanding context

### Process
4. **No pattern testing**: SUGGESTION_MAP patterns tested manually, no automated regression suite
5. **Map bitrot**: As more checks are added, SUGGESTION_MAP doesn't keep pace
6. **No feedback loop**: Failed suggestions aren't tracked or analyzed
7. **Documentation gap**: --suggest flag and inline display not documented in SKILL.md

### Tech
8. **Pattern collision**: Two patterns for same check can both match, producing duplicate/conflicting suggestions
9. **Case sensitivity bugs**: Pattern matching uses `.lower()` but check outputs may have mixed-case strings not being searched
10. **Healthy check false positive**: Suggestions appear for healthy checks if status="warning" but check is actually passing
11. **Details message mismatch**: Patterns match generic text that appears in multiple checks' outputs
12. **Performance regression**: SUGGESTION_MAP lookup adds O(n) to every check's run_check() — 16 entries now, but grows
13. **Frozen dataclass rigidity**: HealthFinding.frozen=True prevents easy debugging via modification
14. **Unused pattern variable**: `_match_suggestions` binds `pattern` in loop but never uses it — Pyright warning indicates dead code

### External
15. **Skill unavailable**: Suggested skill doesn't exist or has different trigger in user's environment
16. **Check output format change**: Health check scripts change their output format, breaking all pattern matches

---

## Step 2.5: Cascade Analysis (risks ≥6)

### CRIT-001: Pattern collision causes duplicate suggestions
- Pattern "timeout" and "syntax" both could match same output → user sees duplicates
- And then: User ignores all suggestions as noise
- And then: Real issues go unaddressed
- **Risk 8** (L=3, I=3, both checks use `suggestions[:3]` cap mitigates)

### CRIT-002: Check output format change silently breaks all patterns
- Any health check script output format change breaks all SUGGESTION_MAP patterns for that check
- And then: All suggestions for that check disappear silently
- And then: Users don't know something is wrong
- **Risk 9** (L=3, I=3, low visibility)

---

## Step 2.6: AI/LLM-Specific Failure Modes

- **Context overflow**: SUGGESTION_MAP grows large, SUGGESTION_MAP lookup code becomes harder to reason about
- **Suggestion quality**: LLM may suggest skills that technically match pattern but are wrong for context
- **Pattern gaming**: User could intentionally trigger misleading patterns to manipulate suggestions

---

## Step 2.7: Temporal Failure Modes

- **Context loss**: 50 turns later, the rationale for a specific pattern mapping is forgotten
- **Constraint drift**: CLAUDE.md principles change but SUGGESTION_MAP not updated
- **Contradiction**: Same check suggests different skills depending on how output is parsed

---

## Step 3: Categorization

| ID | Category | Description |
|----|----------|-------------|
| 1,2,3 | People | Pattern/skill churn, over-trust |
| 4,5,6,7 | Process | No testing, bitrot, no feedback, docs |
| 8,9,10,11,12,13,14 | Tech | Collision, case, false positive, perf, frozen, unused var |
| 15,16 | External | Unavailable skill, output format change |

---

## Step 3.5: Reference Class Forecasting

- Similar "mapping tables" in codebase (e.g., GAP_TYPE_TO_CATEGORIES in gap_skill_mapper.py) — tend to grow beyond original design
- Pattern-based routing in hooks (PreToolUse routing) — proved brittle when patterns don't match actual output
- Evidence: skill_deps check uses "SKILL DIR NOT FOUND" which is a very specific string — changes in script output break it

---

## Step 3.6: Success Theater Detection

- Suggestion count metric ("3 suggestions shown") looks productive but doesn't measure if suggestions were actually useful
- JSON field `suggestions` added — presence doesn't mean quality
- Map size (16 entries) suggests completeness but coverage is unknown

---

## Step 3.8: Operational Verification

- Verified: Python syntax is valid (no SyntaxError)
- Verified: `python main_health.py --quick --suggest` produces output with SKILL SUGGESTIONS section
- Verified: Inline `💡 Run` appears for non-healthy checks
- Verified: JSON output includes `suggestions` field
- NOT verified: Pattern matching accuracy against real check outputs
- NOT verified: Whether suggested skills actually resolve the issues

---

## Step 4: Risk Ratings

| ID | Risk | L | I | Score | Notes |
|----|------|---|---|-------|-------|
| CRIT-001 | Pattern collision | 3 | 3 | 9 | Duplicate suggestions |
| CRIT-002 | Output format change breaks all patterns | 3 | 3 | 9 | Silent failure |
| 4 | No pattern testing | 3 | 2 | 6 | Future bug risk |
| 7 | Documentation gap | 2 | 3 | 6 | User confusion |
| 10 | Healthy check false positive | 2 | 3 | 6 | Wrong advice |
| 14 | Unused pattern variable | 1 | 2 | 2 | Code smell |
| 15 | Skill unavailable | 1 | 2 | 2 | Runtime error |

---

## Step 4.5: Dependency Cascades

- CRIT-001 and CRIT-002 are independent (structural, not causal)
- Skip Step 4.5

---

## Step 5: Prevent Top 3 + Map to Actions

**CRIT-001** → Add deduplication in `_match_suggestions` (already capped at 3, but no dedup within same skill)
**CRIT-002** → Add pattern coverage test — run health checks, verify SUGGESTION_MAP patterns actually match
**RISK-4** → Add unit test for `_match_suggestions` with mock check outputs

---

## Step 6: Warning Signs to Monitor

- New health check added but SUGGESTION_MAP not updated → gap between checks and suggestions
- Users reporting "suggestion was wrong" → pattern mismatch
- Health check script modification → potential pattern break
- SUGGESTION_MAP > 30 entries → redesign needed

---

## Step 7: Adversarial Validation

[TO BE RUN — dispatching 8 agents in parallel]
