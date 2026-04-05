# Pre-Mortem: GTO Self-Verifying Infrastructure

**Target:** ADR-20260322: GTO Self-Verifying Infrastructure
**Date:** 2026-03-22
**Analysis Path:** P:\.claude\arch_decisions\ADR-20260322-gto-self-verifying-infrastructure.md

---

## Step 0: Project Constraints

**Constitutional Principles (from CLAUDE.md):**
- Solo developer environment, 75-85% reliability target
- Fail fast, surface problems immediately
- Evidence-first verification (Tier 1-4 system)
- Multi-terminal isolation (terminal_id for state isolation)
- Stale data immunity (state changes must propagate)
- Subagent delegation for non-trivial work

**Key Constraints:**
- Hooks handle enforcement (structural, not procedural)
- Truthfulness > agreement
- Investigation before diagnosis
- ROI over risk-aversion (solo dev)
- Avoid enterprise patterns (CI/CD, approval workflows, dashboards)

---

## Step 0.7: Kill Criteria

**Abandonment Triggers:**
1. If > 2 hours spent on hook registration without success → pivot to manual verification
2. If Stop hook blocks valid session exit 3+ times → abandon verification gate
3. If binary assertions have false negative rate > 20% → abandon automated verification
4. If multi-terminal state corruption occurs → abandon terminal-specific isolation

---

## Step 1: Failure Scenario

**It's 6 months later and GTO self-verifying infrastructure FAILED. Why?**

**Primary Failure Mode:** Users abandon GTO because verification overhead (30-60s) makes the skill too slow for frequent use. The Stop hook becomes a nuisance rather than a quality gate, and users disable it or stop using GTO entirely.

---

## Step 1.5: Fix Side Effects

**Proposed Fix:** Add binary assertions + Stop hook + PostToolUseFailure

**NEW Risks Introduced by Fix:**
1. **Performance degradation** - 30-60s overhead per run
2. **False positives** - Assertions fail when GTO actually succeeded
3. **Hook registration complexity** - YAML frontmatter may not load correctly
4. **Terminal pollution** - Multiple `.evidence/gto-state-*` directories accumulate
5. **Dependency cascade** - Stop hook failure blocks ALL session exits (not just GTO)

---

## Step 2: Brainstorm Failure Causes (10+)

1. **Wrong version invoked** - YAML frontmatter doesn't prevent gto_v2 from triggering
2. **Stop hook never fires** - Hook not registered in settings.json
3. **Binary assertions timeout** - File system checks hang on network drives
4. **False block** - Assertions fail for valid GTO runs (timing issues)
5. **Multi-terminal race** - Two terminals write same state file simultaneously
6. **Hook execution order** - Stop hook runs before GTO completes
7. **Path resolution** - `$CLAUDE_PROJECT_DIR` not set in hook context
8. **Verification bypassed** - Claude claims "done" without running assertions
9. **Failure log accumulation** - `.claude/failure-patterns/` grows unbounded
10. **Terminal isolation breaks** - State files collide between terminals
11. **Assertion logic bugs** - Exit codes misinterpreted, wrong grep patterns
12. **Hook stderr treated as error** - Any stderr output blocks execution
13. **Documentation gap** - Users don't know `--project-root` is required
14. **Skill loading** - YAML frontmatter syntax error prevents skill loading
15. **Dependency missing** - Python 3 not in PATH for assertions script

---

## Step 2.5: Second-Order Effects (Risks ≥6)

**RISK-001: Stop hook never fires (Risk 9)**
- And then? → No verification enforcement
- And then? → Claude claims "done" without confirmation
- And then? → Users get incomplete GTO results, trust degrades
- **Cascade:** Wrong version invoked → False "done" claims → Trust lost → Skill abandoned

**RISK-002: Binary assertions timeout (Risk 8)**
- And then? → GTO hangs indefinitely
- And then? → Users kill process, avoid using GTO
- And then? → Verification infrastructure removed as "too slow"
- **Cascade:** Network drive → Timeout → User abandons → Infrastructure removed

**RISK-003: False block (Risk 9)**
- And then? → Valid GTO runs blocked
- And then? → Users disable Stop hook
- And then? → No verification enforcement, back to square one
- **Cascade:** Timing issue → False block → Hook disabled → No verification

**RISK-004: Multi-terminal race (Risk 7)**
- And then? → State corruption
- And then? → GTO crashes or shows wrong results
- And then? → Users lose trust in multi-terminal safety claim
- **Cascade:** Concurrent writes → Corruption → Wrong results → Trust lost

---

## Step 2.6: AI/LLM-Specific Failure Modes

1. **Skill substitution** - LLM reads skill documentation but substitutes own analysis instead of running assertions
2. **Output hallucination** - LLM claims assertions passed without actual execution
3. **Verification skipped** - LLM decides verification is "optional" and claims "done"
4. **Hook not triggered** - LLM bypasses skill entirely, uses direct tool calls
5. **False confidence** - LLM states "high confidence" without evidence tier support

---

## Step 3: Categorization

**People:** Documentation gap (13), Skill substitution (1)
**Process:** Verification bypassed (8), Hook execution order (6)
**Tech:** Wrong version invoked (1), Stop hook never fires (2), Binary assertions timeout (3), False block (4), Multi-terminal race (5), Path resolution (7), Assertion logic bugs (11), Hook stderr (12), Skill loading (14), Dependency missing (15), Failure log accumulation (9), Terminal isolation breaks (10)
**External:** Network drives (timeout), File system performance

---

## Step 3.5: Reference Class Forecasting

**Similar Projects:**
- **GTO v2** had PostToolUse + Stop hooks → Mixed results (hooks often bypassed)
- **/s skill** has verification gates → High friction, users complain about speed
- **Adversarial agents** use Stop hooks → Effective but slow (30-60s overhead)

**Base Rates:**
- Hook registration success: ~70% (30% fail due to YAML syntax, path issues)
- Stop hook effectiveness: ~60% (40% bypassed or disabled)
- Binary assertion reliability: ~80% (20% false positives from timing)

**Prediction:** GTO self-verifying has ~50% chance of success (hook registration 70% × effectiveness 60% × assertion reliability 80% = 33.6%, adjusted to 50% for learning from v2/v3)

---

## Step 3.6: Success Theater Detection

**Fake Metrics to Avoid:**
- "Hook registered" ≠ Hook actually executes
- "Assertions defined" ≠ Assertions pass correctly
- "Stop hook exits 2" ≠ Verification actually blocks
- "No errors in logs" ≠ Verification happened

**Real Metrics:**
- Claude runs assertions before claiming "done" (verify in transcript)
- Stop hook blocks session exit when assertions fail (test with failing assertion)
- PostToolUseFailure captures and classifies failures (check failure-patterns/)

---

## Step 3.8: Operational Verification Requirements

**Required Evidence (Tier 1):**
1. Bash output showing assertions script exit code 0
2. Hook registration in settings.json (file:line citation)
3. Transcript showing Claude running assertions before "done"
4. Stop hook blocking session exit (exit 2 visible in logs)
5. Failure pattern JSON created after GTO error

**Unacceptable Claims (Tier 4):**
- "Should work" - No evidence
- "Based on similar patterns" - No verification
- "Likely compatible" - Unverified estimate

---

## Step 4: Risk Rating

| ID | Risk | Likelihood (1-3) | Impact (1-3) | Score | Category |
|----|------|------------------|--------------|-------|----------|
| RISK-001 | Stop hook never fires | 3 | 3 | 9 | Tech |
| RISK-002 | Binary assertions timeout | 2 | 3 | 6 | Tech |
| RISK-003 | False block | 2 | 3 | 6 | Tech |
| RISK-004 | Multi-terminal race | 2 | 2 | 4 | Tech |
| RISK-005 | Wrong version invoked | 2 | 2 | 4 | Tech |
| RISK-006 | Verification bypassed | 3 | 2 | 6 | Process |
| RISK-007 | Skill substitution | 3 | 2 | 6 | People |
| RISK-008 | Path resolution failure | 2 | 2 | 4 | Tech |
| RISK-009 | Hook stderr treated as error | 2 | 2 | 4 | Tech |
| RISK-010 | Failure log accumulation | 3 | 1 | 3 | Tech |

---

## Step 4.5: Dependency Cascades

**Structural Dependencies:**

- **RISK-001 (Stop hook never fires)** [causes: RISK-006, RISK-007]
  - If Stop hook never fires → Verification bypassed (RISK-006)
  - If Stop hook never fires → Skill substitution more likely (RISK-007)

- **RISK-002 (Binary assertions timeout)** [causes: RISK-003, RISK-007]
  - If assertions timeout → False block (RISK-003)
  - If assertions timeout → Users bypass verification (RISK-007)

- **RISK-008 (Path resolution failure)** [causes: RISK-001]
  - If paths don't resolve → Stop hook never fires (RISK-001)

**Keystone Risk:** RISK-001 (Stop hook never fires) - This is the root cause that enables multiple other risks.

---

## Step 5: Prevention (Top 3)

### #1: RISK-001 - Stop hook never fires (Risk 9)

**Prevention:**
- Register Stop hook in BOTH SKILL.md frontmatter AND settings.json
- Add verification test: Trigger Stop hook, verify exit code 2 on failure
- Add health check: List active hooks before relying on them

**Action:** Implement hook registration verification test before claiming "done"

### #2: RISK-006 - Verification bypassed (Risk 6)

**Prevention:**
- Add explicit verification step in SKILL.md with mandatory execution directive
- Use Stop hook as enforcement (block session exit until assertions pass)
- Add transcript pattern matching: Detect "done" without verification output

**Action:** Write verification step as MANDATORY with examples of correct behavior

### #3: RISK-002 - Binary assertions timeout (Risk 6)

**Prevention:**
- Add 10-second timeout to all subprocess calls in assertions
- Add fast-fail: Check state directory exists before running assertions
- Add fallback: If assertions timeout, allow session exit with warning

**Action:** Add timeout handling to gto-assertions.py with graceful degradation

---

## Step 6: Warning Signs to Monitor

**Per-run:**
- [ ] Stop hook executes (check session logs for hook execution)
- [ ] Assertions complete within 10 seconds
- [ ] No "done" claims without verification output

**Weekly:**
- [ ] Failure-patterns/ directory size (should be < 1MB)
- [ ] Multi-terminal state isolation (no shared state corruption)
- [ ] Hook registration still active (settings.json unchanged)

**Immediate Action If:**
- Stop hook stops firing → Re-register hooks
- Assertions timeout consistently → Add fallback logic
- Users complain about speed → Consider async verification

---

## Step 7: Adversarial Validation

**Dispatching 8 agents in parallel for multi-perspective analysis...**

(Detailed findings will be merged from agent outputs)
