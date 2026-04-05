# Review Bundle: /pre-mortem and /critique
**Generated:** 2026-04-04
**Scope:** P:\.claude\skills\pre-mortem\ and P:\.claude\skills\critique\
**File Count:** 12 total (6 pre-mortem, 5 critique, 1 shared structure)
**Execution Mode:** Single agent (read files directly)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
Both skills are adversarial analysis skills for the Cognitive Steering Framework (CSF).

### Domain & Purpose
- **/pre-mortem** (v6.4): Failure analysis — "It's 6 months later and this failed. Why?" with 8-agent adversarial validation
- **/critique** (v2.1.0): Adaptive adversarial review of skills, plans, and code with phased specialist dispatch

### Scale Metrics
| Skill | Files | Lines (SKILL.md) | Hooks | Tests |
|-------|-------|-----------------|-------|-------|
| pre-mortem | 6 | 524 | 1 (Stop) | 2 test files |
| critique | 5 | 280 | 0 | 2 test files |

---

## 2. ARCHITECTURE OVERVIEW

### /pre-mortem

```
SKILL.md (v6.4, 524 lines)
├── __lib/
│   ├── validation.py       — action mapping, kill criteria, temporal failures, operational verification
│   ├── feedback_loop.py    — feedback loop for generic actions
│   └── test_adversarial_dispatch.py
├── hooks/
│   └── Stop_hook_premortem_quality_gate.py  — validates required sections present
├── tests/
│   ├── test_validation.py
│   └── test_feedback_loop.py
```

**Step 7 dispatch model:**
- 7 agents in parallel (adversarial-compliance, logic, performance, security, testing, quality, qa)
- 1 critic in series after parallel agents complete
- All agents receive `<analysis_path>` (pre-mortem output file)

**Validation layers:**
- `Stop_hook_premortem_quality_gate.py` (lines 29-33): checks for "🔴 WHAT'S ACTUALLY BROKEN" and "🟠 HIGH-RISK" section headers — NOT content accuracy
- `validation.py`: action mapping (action-to-priority), kill criteria, temporal failure modes, operational verification warnings

### /critique

```
SKILL.md (v2.1.0, 280 lines)
├── lib/
│   ├── __init__.py
│   └── critique_io.py    — CritiqueSession (565 lines), file-based work passing
├── tests/
│   ├── test_critique_io.py
│   └── test_critique_io_concurrent.py
```

**Phase model:**
- Phase 1: Read `work.md` (actual source), dispatch specialists in parallel, consolidate to `p1_findings.md`
- Phase 2: Read `work.md` + `p1_findings.md`, meta-critique
- Phase 3: Synthesis → `p3.md`
- Session registry: `sessions.json` (terminal-scoped recovery)

**Completion gate** (SKILL.md:119): verifies at least one specialist JSON exists before proceeding to Phase 2

---

## 3. INPUT/OUTPUT CONTRACT

### /pre-mortem What Each Agent Receives

| Phase | What agents read | Source |
|-------|------------------|--------|
| Steps 1-6 (operator) | CLAUDE.md, plan artifacts, source code | Original |
| Step 7 Phase 1 (7 parallel) | `<analysis_path>` — pre-mortem output | Operator's analysis |
| Step 7 Phase 2 (critic) | `<analysis_path>` + all Phase 1 JSONs | Operator's analysis + agent outputs |

**Critical gap**: Pre-mortem agents read the **operator's analysis** (`premortem_ttl_clock_jump_20260404.md`), NOT the actual source code. Any error in Steps 1-6 propagates to all 8 agents.

### /critique What Each Agent Receives

| Phase | What agents read | Source |
|-------|------------------|--------|
| Step 2 (CritiqueSession) | Original work input → `session_dir/work.md` | User-provided |
| Step 3 Phase 1 (triage + specialists) | `work.md` + `p1_initial_review.md` | **Actual source** |
| Phase 2 (meta-critique) | `work.md` + `p1_findings.md` | Analysis + consolidated findings |

**Key distinction**: critique Phase 1 specialists read `work.md` — the **actual source code** under review. Pre-mortem agents read the operator's interpretation of the source.

---

## 4. TRIAGE AGENT DISPATCH LOGIC (critique Phase 1)

The triage agent runs `phases/p1_initial_review.md` (lines 1-152). Key steps:

**Step 1: Classify target** → skill / code / plan / document / hook / agent

**Step 2: Select 2-4 specialists based on type:**

| Target | Specialists |
|--------|-------------|
| skill | adversarial-critic, adversarial-compliance, adversarial-quality |
| code (Python, JS) | adversarial-security, adversarial-performance, adversarial-logic, adversarial-state-machine, adversarial-io-validation, adversarial-compliance, adversarial-quality, adversarial-testing |
| plan | adversarial-critic, adversarial-compliance |
| document | adversarial-critic, adversarial-quality |
| hook | adversarial-security, adversarial-compliance, adversarial-io-validation |
| agent | adversarial-critic, adversarial-compliance |

**Step 4: Dispatch via Task tool to `P:/{session_dir}/specialists/{name}-findings.json`**

**Step 5: Consolidate** → writes `p1_findings.md` with cited findings (file:line required for code findings per line 142)

---

## 5. EXECUTION AND DATA FLOW

### /pre-mortem
```
Steps 1-6 (operator) → writes analysis to .evidence/premortem_*.md
         ↓
Step 7 Phase 1: 7 parallel agents read <analysis_path> (my analysis, NOT source)
         ↓
Step 7 Phase 2: critic reads <analysis_path> + all Phase 1 JSONs, attempts falsification
         ↓
Quality gate: checks 🔴/🟠 headers present? (NOT content accuracy)
```

### /critique
```
Step 2: CritiqueSession writes work to session_dir/work.md
Step 3 Phase 1: triage reads work.md, classifies, selects specialists, dispatches
         Phase 1 completion gate: at least 1 specialist JSON must exist
Step 4 Phase 2: meta-critique reads work.md + p1_findings.md
Step 5 Phase 3: synthesis reads all phase outputs
         → Skill coverage logged to GTO
```

---

## 6. COMPONENT INVENTORY

### Core Logic
| Component | Path | Responsibility |
|-----------|------|----------------|
| SKILL.md | pre-mortem/SKILL.md | 524-line framework spec |
| SKILL.md | critique/SKILL.md | 280-line phased review spec |
| Stop_hook_premortem_quality_gate | pre-mortem/hooks/ | Post-run section validation |
| validation | pre-mortem/__lib/validation.py | Action mapping, kill criteria, temporal validation |

### Utilities
| Component | Path | Responsibility |
|-----------|------|----------------|
| CritiqueSession | critique/lib/critique_io.py:100 | File-based work passing, session registry, atomic writes |
| _get_terminal_id | critique/lib/critique_io.py:68 | Canonical terminal ID for session isolation |
| CritiqueSession.find_or_create | critique/lib/critique_io.py:196 | Session recovery after compaction |
| validate_action_mapping | pre-mortem/__lib/validation.py:13 | Generic action detection |
| validate_kill_criteria_defined | pre-mortem/__lib/validation.py:255 | Kill criteria presence check |
| validate_temporal_failure_modes | pre-mortem/__lib/validation.py:277 | Step 2.7 turn-number citation validation |

### Infrastructure
| Component | Path | Notes |
|-----------|------|-------|
| sessions.json | critique/.evidence/critique/ | Terminal-scoped registry for session recovery |
| STAGING_ROOT | critique/lib/critique_io.py:64 | P:\.claude\.evidence\critique |
| specialists/ | critique/session_dir/ | Per-session JSON findings from Phase 1 agents |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### /pre-mortem
- **Parallel-then-serial dispatch**: 7 agents parallel, critic serial after (SKILL.md:172-189)
- **Falsification mandate**: critic must attempt empirical reproduction of HIGH findings (SKILL.md:180-186)
- **Evidence requirement**: Step 3.8 requires empirical evidence (test output, code:line, log) before rating HIGH/CRITICAL
- **Section structure enforcement**: quality gate blocks if 🔴/🟠 headers absent (but doesn't validate content)

### /critique
- **File-based work passing**: avoids token costs, enables session recovery
- **Phase completion gate**: Phase 1 must produce specialist JSON before Phase 2 (SKILL.md:119)
- **Source-first**: Phase 1 reads `work.md` (actual source), not analysis output
- **Blinded consumer review**: Phase 1 includes consumer-contract review for stateful targets (SKILL.md:53-63)
- **Skill coverage logging**: Phase 3 writes to GTO skill coverage tracker (critique_io.py:351-371)

---

## 6. KNOWN ISSUES

### Issue 1: Pre-mortem Step 3.8 not enforced at write time
- **Scenario**: Operator rates F2 as HIGH severity without reading `file_lock_manager.py:138`
- **Expected**: Step 3.8 requires empirical evidence before HIGH rating
- **Actual**: No gate blocks HIGH rating without evidence — agents build on unverified premise
- **Impact**: False-positive cluster propagates to all 6 parallel agents
- **Current workaround**: Critic catches it post-dispatch (F2 demoted to NON_REPRODUCIBLE)

### Issue 2: Pre-mortem quality gate only checks section headers, not content
- **Evidence**: `Stop_hook_premortem_quality_gate.py:29-33` — `REQUIRED_SECTIONS = ["🔴 WHAT'S ACTUALLY BROKEN", "🟠 HIGH-RISK"]`
- **What it checks**: Whether those exact strings appear in output
- **What it doesn't check**: Whether HIGH findings cite `file:line` evidence
- **Impact**: Claims without empirical evidence can pass quality gate

### Issue 3: Pre-mortem agents read analysis, not source
- **Evidence**: SKILL.md:163 — `Review pre-mortem at <analysis_path>`
- **Impact**: Any error in Steps 1-6 propagates to all 8 agents
- **Comparison**: critique Phase 1 reads `work.md` (actual source), pre-mortem agents read my analysis

---

## 7. INTEGRATION POINTS

### /pre-mortem Hook Registration
```yaml
# SKILL.md frontmatter (lines 8-14)
hooks:
  Stop:
    - once: true
      hooks:
        - type: command
          command: "python P:/.claude/skills/pre-mortem/hooks/Stop_hook_premortem_quality_gate.py"
          timeout: 30
```

### /critique Skill Integration
- Phase 3 logs skill coverage: `skill_coverage_detector._append_skill_coverage()`
- Routes to `/verify`, `/pre-mortem`, `/reflect` based on findings (SKILL.md:281-287)
- Session recovery: `sessions.json` maps terminal_id → session_dir

---

## 8. AGENT DISPATCH DEFINITIONS

### /pre-mortem Step 7 — Phase 1 (7 parallel agents)

```python
Agent(subagent_type="adversarial-compliance", description="Compliance review", prompt="Review pre-mortem at <analysis_path> for specification violations, solo-dev inappropriate patterns, and constitutional violations. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path.")
Agent(subagent_type="adversarial-logic", description="Logic review", prompt="Review pre-mortem at <analysis_path> for pure logic errors, race conditions, off-by-one bugs, and implementation gaps. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path.")
Agent(subagent_type="adversarial-performance", description="Performance review", prompt="Review pre-mortem at <analysis_path> for performance bottlenecks, timeouts, N+1 patterns, and scalability limits. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path.")
Agent(subagent_type="adversarial-security", description="Security review", prompt="Review pre-mortem at <analysis_path> for security vulnerabilities, data leaks, access control gaps, and injection risks. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path.")
Agent(subagent_type="adversarial-testing", description="Testing review", prompt="Review pre-mortem at <analysis_path> for testing gaps, missing scenarios, brittle tests, and coverage gaps. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path.")
Agent(subagent_type="adversarial-quality", description="Quality review", prompt="Review pre-mortem at <analysis_path> for maintainability risks, tech debt, code smells, and coupling issues. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path.")
Agent(subagent_type="adversarial-qa", description="QA review", prompt="Review pre-mortem at <analysis_path> for missing acceptance criteria, untestable requirements, and validation gaps. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path.")
```

**Key detail**: All agents receive `<analysis_path>` (the pre-mortem output file), NOT the original source code.

### /pre-mortem Step 7 — Phase 2 (critic, serial)

```python
Agent(subagent_type="adversarial-critic", description="Critic review", prompt=""Meta-analysis of pre-mortem at <analysis_path> - consensus gaps, blind spots, bias patterns, and contradiction detection. Provide confidence calibration on findings.

MANDATORY FALSIFICATION: For each finding rated HIGH severity, attempt to empirically reproduce or falsify it before confirming the rating:
- Race conditions: write a minimal Python script to trigger the race. If it fails 3x, demote to MEDIUM and note 'not reproduced'
- Threshold claims (e.g. '900s timeout', '50ms latency'): read the relevant code path and verify the actual threshold value
- Existence claims (e.g. 'no test for X'): verify the code/filepath actually exists or doesn't using grep/glob
- Collision/ID conflicts: write a minimal reproduction. If it doesn't trigger in 3 attempts, demote

Report falsification test output for each HIGH finding. A finding without a falsification attempt remains UNVERIFIED with confidence ceiling 50%."")
```

### /critique Phase 1 — Specialist Dispatch (adaptive)

critique uses a **triage agent** to classify the work and select relevant specialists. The operator runs Phase 1 via:

```
Read P:/.claude/skills/critique/phases/p1_initial_review.md
Read the work: cat "P:/{session_dir}/work.md"
Follow the triage and dispatch instructions in p1_initial_review.md
Write consolidated findings to: P:/{session_dir}/p1_findings.md
```

**Specialist subagent registry** (SKILL.md:27-51):

| Subagent | Best For |
|----------|---------|
| `adversarial-security` | Data access, auth, I/O, injection vectors |
| `adversarial-performance` | Hot paths, loops, DB queries, N+1 |
| `adversarial-logic` | Off-by-one, wrong operators, inverted conditionals |
| `adversarial-state-machine` | Status fields, lifecycle, transitions |
| `adversarial-io-validation` | Path validation, file existence, external calls |
| `adversarial-compliance` | Schema, API contracts, specs |
| `adversarial-quality` | Tech debt, maintainability risks |
| `adversarial-testing` | Missing tests, coverage gaps, brittle tests |
| `adversarial-critic` | Meta-analysis: consensus, blind spots, contradictions |
| `adversarial-rca` | Root cause analysis, causal chains |

---

## 10. FAILURE SCENARIO: How F2 Propagated to All 6 Agents

**Context:** TTL clock-jump vulnerability audit (RCA-007), April 2026.

### The Failure Chain

| Step | What happened | Evidence |
|------|--------------|----------|
| 1 | Operator (me) wrote pre-mortem during Steps 1-6 | `premortem_ttl_clock_jump_20260404.md` |
| 2 | Operator rated F2 as HIGH severity — "Linter reverts TTL fixes" | Pre-mortem output |
| 3 | F2 claimed `acquire_lock` uses `_write_monotonic_ts()` | Pre-mortem F2 premise |
| 4 | **Operator did NOT read `file_lock_manager.py:138`** | Step 3.8 violation |
| 5 | Step 7 dispatched 6 parallel agents — all received `<analysis_path>` | SKILL.md:163 |
| 6 | All 6 agents accepted F2 premise without verification | pm_ttl_critic.json:75-81 |
| 7 | 6 agents built findings on false premise | 100% false-positive rate |
| 8 | Critic (Phase 2) caught the contradiction | pm_ttl_critic.json:83-99 |
| 9 | Critic showed `acquire_lock:138` uses `time.time()`, not `_write_monotonic_ts()` | Falsification evidence |

### What Went Wrong

**Step 3.8 violation**: Pre-mortem's Step 3.8 requires empirical evidence (test output, code:line citation, log excerpt) before rating HIGH/CRITICAL. The operator claimed F2 was HIGH without reading `file_lock_manager.py:138`. The skill had the rule — it just wasn't enforced at write time.

**Quality gate only checks headers**: `Stop_hook_premortem_quality_gate.py:29-33` checks for `🔴 WHAT'S ACTUALLY BROKEN` and `🟠 HIGH-RISK` string presence. It doesn't check whether HIGH findings cite `file:line` evidence. F2 passed the gate because the headers were present.

**Agents read analysis, not source**: SKILL.md:163 — all agents dispatched with `Review pre-mortem at <analysis_path>`. They validated the operator's analysis, not the actual code. The critic would have caught F2 in Phase 2, but by then 6 agents had already built on the false premise.

### The Actual Code (verified by critic)

```python
# file_lock_manager.py:138
now = time.time()  # ← wall-clock, NOT monotonic

# file_lock_manager.py:190
"created": _sanitize_future_ts(_write_monotonic_ts())  # ← producer writes future-clamped monotonic
```

The F2 premise was backwards — `acquire_lock` writes monotonic timestamps but reads `time.time()` (wall-clock). Wait, actually reading again:

Line 151: `now = time.time()` — wall-clock
Line 190: `"created": _sanitize_future_ts(_write_monotonic_ts())` — **stores monotonic** via `_write_monotonic_ts()`

But the consumer at line 159: `age = _get_elapsed(created)` — uses `_get_elapsed()` which handles both clocks. So the **actual bug was in me, not the code**.

### Verified Issue (MONOTONIC_THRESHOLD mismatch)

**`ttl_utils.py:33-35`** — comment says `1e12`, code uses `1e9`:
```python
# Use 1e12 as threshold...  ← comment
MONOTONIC_THRESHOLD = 1e9  ← code
```
Wall-clock timestamp 999,999,999 (Sep 2001) would be misclassified as monotonic, causing `is_expired()` to return False (permanent validity) for state files from 2001.

### Lesson

Pre-mortem Step 3.8 is documented but not enforced at write time. The gate runs post-completion (after Step 7), checking headers not content. A HIGH rating without `file:line` evidence should block Step 7 dispatch — not pass through and get corrected after 6 agents built on the false premise.

---

## 11. COMPARISON: KEY DESIGN DIFFERENCES

| Aspect | /pre-mortem | /critique |
|--------|-------------|-----------|
| Agents read | Analysis file (`<analysis_path>`) | Actual source (`work.md`) |
| Dispatch | Fixed 7 parallel + 1 serial critic | Adaptive via triage agent |
| Quality gate | Section header presence | Phase 1 completion gate (JSON exists) |
| Evidence enforcement | Step 3.8 (documented, not enforced at write time) | Blinded consumer review |
| Session recovery | Via evidence file glob | Via `sessions.json` registry |
| Falsification | Critic mandate (SKILL.md:180-186) | Built into Phase 2 meta-critique |

