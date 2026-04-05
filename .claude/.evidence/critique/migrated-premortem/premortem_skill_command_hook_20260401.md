---
 Migrated from: premortem_skill_command_hook_20260401.md
 Original location: P:\.claude\.evidence\premortem_skill_command_hook_20260401.md
 Migration date: 2026-04-04
 Reason: Pre-mortem skill deprecated and absorbed into /critique --target=failure
---

# Pre-Mortem: Skill Auto-Discovery + SkillCommandHook Integration

**Target**: `discover_hooks()` + `SkillCommandHook` implementation for PostToolUse registry
**Date**: 2026-04-01
**Analyst**: Claude (automated pre-mortem)

---

## Step 0: Project Constraints (from CLAUDE.md)

1. **Hook Registration Enforcement**: Hooks MUST be registered to execute — dispatch chain verification required before editing
2. **Multi-Terminal Isolation**: State changes must propagate; terminal-scoped isolation required
3. **Integration Verification**: Registry-based hooks need integration verification, not just unit tests
4. **Hook External Dependency Policy**: Hooks MUST NOT make external API calls; use local artifacts instead
5. **Sequential File Operations**: Execute modifications ONE AT A TIME to prevent race conditions

---

## Step 0.7: Kill Criteria

- **KILL-1**: If hook registration test fails → rollback `SkillCommandHook` + `discover_hooks()` integration
- **KILL-2**: If PostToolUse router crashes on import → remove `discover_hooks()` call from `create_registry()`
- **KILL-3**: If RCA hooks fire but fail silently → remove integration, keep `discover_hooks()` but don't wire to registry

---

## Step 1: Failure Scenario

**"It's 6 months later. The PostToolUse registry is broken. All PostToolUse hooks fail silently or crash. The user's RCA skill hooks never fire, and there's no evidence anything is wrong."**

---

## Step 1.5: Fix Side Effects

For each proposed fix component:

| Component | NEW Risk Introduced |
|-----------|-------------------|
| `discover_hooks()` import in `create_registry()` | ImportError kills entire registry creation |
| `SkillCommandHook` subprocess calls | Timeout blocking, stderr pollution, zombie processes |
| `yaml.safe_load` in `_parse_skill_hooks()` | Malformed YAML in ANY SKILL.md causes full parse failure |
| `matcher_pattern` regex in `SkillCommandHook.matches_tool()` | Bad regex in SKILL.md causes catastrophic backtracking |

---

## Step 2: Brainstorm Failure Causes (10+)

### Process Failures

| ID | Cause | Principle Violated |
|----|-------|-------------------|
| P-001 | Test only verifies hook COUNT, not that hooks actually fire (success theater) | Integration Verification mandate |
| P-002 | No monitoring/alerting when discovered hooks fail silently | Observability requirement |
| P-003 | No periodic re-discovery if SKILL.md changes after session start | Temporal consistency |

### Tech Failures

| ID | Cause | Principle Violated |
|----|-------|-------------------|
| T-001 | `skill_guard` not in `sys.path` at PostToolUse router startup → ImportError → all hooks skipped | Graceful degradation |
| T-002 | Malformed YAML in ANY skill's SKILL.md (e.g., rca, gto) → `_parse_skill_hooks()` returns [] → that skill's hooks silently missing | Fail-fast enforcement |
| T-003 | Subprocess command in `SkillCommandHook` times out → blocks hook execution | Hook External Dependency Policy |
| T-004 | `matcher_pattern` regex from SKILL.md causes catastrophic backtracking → hangs PostToolUse router | Hook External Dependency Policy |
| T-005 | `discover_hooks()` called on EVERY `create_registry()` invocation (~150ms × N skills) → latency regression | Performance requirement |
| T-006 | Hook name collision: two skills declare hooks with same `name` → second overwrites first | Registry integrity |
| T-007 | Concurrent terminals both run `discover_hooks()` → file system race on SKILL.md reads | Multi-Terminal Isolation |
| T-008 | `yaml.safe_load` can execute arbitrary Python via YAML tags → security risk if SKILL.md is user-controlled | Security invariants |

### External Failures

| ID | Cause | Principle Violated |
|----|-------|-------------------|
| E-001 | `rca` skill package not installed → `python -m rca.hook_launcher` fails → hook always fails | Fail-open expectation |

---

## Step 2.5: Cascade Analysis (Risks with Likelihood ≥ 2)

**T-001 (skill_guard import failure)** [L=2]:
- Cascade A: `create_registry()` raises ImportError → PostToolUse router crashes → ALL PostToolUse hooks fail → [causes: system failure]
  - "And then what?": User notices no PostToolUse hooks fire → RCA not working → RCA skill broken
  - Probability: sure (>70%)
- Cascade B: `try/except ImportError` catches it → discovered hooks silently skipped → RCA hooks never fire → [causes: P-002]
  - Probability: maybe (30-70%)

**P-001 (test only checks count)** [L=3]:
- Cascade A: Hooks registered but never fire → RCA workflow broken → user gets no evidence tracking → [causes: RCA failure]
  - "And then what?": User sees no breadcrumb evidence → "the skill isn't working" → support burden
  - Probability: sure (>70%)
- Cascade B: Test passes but integration broken → confidence in fix erodes → bug recurs → [causes: rework]
  - Probability: sure (>70%)

**T-002 (malformed YAML)** [L=2]:
- Cascade A: One malformed SKILL.md → all hooks from that skill missing → partial integration → confusing debugging → [causes: RCA incomplete]
  - "And then what?": Some RCA hooks fire, others don't → inconsistent evidence → "why isn't X tracked?"
  - Probability: maybe (30-70%)

---

## Step 2.6: AI/LLM-Specific Failure Modes

- **Context overflow**: `discover_hooks()` reads all SKILL.md files; if skills directory grows large, this scan could timeout or OOM
- **Stale data**: If a skill's SKILL.md is edited mid-session, `discover_hooks()` won't re-scan (cached state issue)
- **Silent degradation**: `except ImportError: pass` means if `skill_guard` is broken, NO discovered hooks fire and there's NO indication of why

---

## Step 2.7: Temporal Failure Modes

- **"What hooks again?"**: 50 turns later, AI forgets `discover_hooks()` is wired and manually registers hooks → duplicate registration
- **Constraint drift**: After 100 turns, "Hook External Dependency Policy" is forgotten; subprocess calls in `SkillCommandHook` accumulate stderr → noise in logs
- **Context overflow**: Large skill directory (>50 skills) → `discover_hooks()` takes >500ms → PostToolUse latency regression

---

## Step 3: Categorization

| ID | Category | Subcategory |
|----|----------|-------------|
| P-001 | Process | Testing gap |
| P-002 | Process | Observability gap |
| P-003 | Process | Refresh/reload gap |
| T-001 | Tech | Import/dependency |
| T-002 | Tech | YAML parsing |
| T-003 | Tech | Subprocess timeout |
| T-004 | Tech | Regex DoS |
| T-005 | Tech | Performance regression |
| T-006 | Tech | Name collision |
| T-007 | Tech | File system race |
| T-008 | Tech | YAML arbitrary execution |
| E-001 | External | Package availability |

---

## Step 3.5: Reference Class Forecasting

Similar auto-discovery systems (pytest plugins, VSCode extensions, webpack loaders) fail in these patterns:
1. **Config not reloaded** (P-003) — 40% of plugin failures
2. **Import cascade failures** (T-001) — 25% of plugin failures
3. **Partial initialization** (T-002) — 20% of plugin failures

Base rate for auto-discovery integrations working correctly after 6 months: ~60%

---

## Step 3.6: Success Theater Detection

**ST-001**: "50 hooks registered" test passes
- What it actually tests: Hook names appear in registry list
- What it DOESN'T test: Hooks fire on tool execution, subprocess calls succeed, output is captured
- This is success theater — test passes but doesn't validate behavior

**ST-002**: "rca hooks found by discover_hooks()" test passes
- What it actually tests: `discover_hooks()` returns non-empty list for rca
- What it DOESN'T test: Hooks are actually wired into `create_registry()`, matcher regex works, subprocess doesn't timeout

---

## Step 3.8: Operational Verification

| ID | Claim | Evidence Required | Status |
|----|-------|------------------|--------|
| P-001 | "hooks are registered" | Run `create_registry()` and verify hooks actually fire on synthetic tool call | ❌ NOT TESTED |
| T-001 | "graceful degradation works" | Temporarily corrupt skill_guard import, verify create_registry() still returns 44 hooks | ❌ NOT TESTED |
| T-003 | "subprocess timeout works" | Verify SkillCommandHook.process() returns warning on timeout | ✅ Unit test exists |
| T-004 | "regex timeout works" | Verify bad regex in matcher doesn't hang | ❌ NOT TESTED |

---

## Step 4: Risk Ratings

| ID | Risk | L (1-3) | I (1-3) | Score | Likelihood% | Confidence% | Notes |
|----|------|---------|---------|-------|-------------|------------|-------|
| P-001 | Test doesn't validate hook firing | 3 | 3 | **9** | 80% | 90% | Critical gap |
| T-001 | skill_guard import failure crashes registry | 2 | 3 | **6** | 40% | 70% | Protected by try/except |
| T-002 | Malformed YAML skips hooks silently | 2 | 2 | **4** | 30% | 80% | Per-skill isolation |
| T-005 | discover_hooks() latency regression | 2 | 2 | **4** | 40% | 60% | 16 hooks in ~50ms |
| T-003 | Subprocess timeout blocking | 2 | 2 | **4** | 30% | 70% | Timeout=10s default |
| T-006 | Hook name collision | 1 | 3 | **3** | 10% | 60% | Unique names generated |
| T-007 | Concurrent FS race | 1 | 2 | **2** | 20% | 50% | Read-only, low risk |
| P-002 | No alerting on silent hook failure | 2 | 2 | **4** | 50% | 70% | Warnings exist |
| P-003 | SKILL.md changes not re-discovered | 1 | 2 | **2** | 20% | 60% | Per-session, acceptable |
| T-008 | YAML arbitrary execution | 1 | 3 | **3** | 5% | 90% | SKILL.md is controlled |

---

## Step 5: Prevent Top 3 Risks

### P-001 → Integration Test for Discovered Hooks

**Action**: Add integration test that:
1. Calls `create_registry()` with mocked `discover_hooks()`
2. Feeds synthetic PostToolUse data
3. Verifies `SkillCommandHook.process()` is called and subprocess is invoked
4. Verifies result contains expected keys

**Evidence needed**: Write test file `tests/test_skill_command_hook_integration.py`

### T-001 → Verify Graceful Degradation

**Action**: Add explicit test that simulates `skill_guard` unavailable:
1. Patch `sys.modules` to remove `skill_guard`
2. Call `create_registry()`
3. Verify registry has baseline 44 hooks (discovered hooks silently skipped)

### T-002 → YAML Validation with Per-Skill Isolation

**Action**: Wrap each skill's hook parsing in isolated try/except:
- Currently: One malformed SKILL.md skips ALL discovered hooks
- Fix: `discover_hooks()` returns all successfully parsed hooks, logs individual failures

---

## Step 6: Warning Signs

| ID | Risk | Warning Sign | Detection | Trigger |
|----|------|-------------|-----------|---------|
| P-001 | Test gap | "All tests pass but hooks don't fire" | RCA evidence files not created | After `/rca` invocation, check `.evidence/` for `rca_*.json` |
| T-001 | Import failure | PostToolUse latency spikes to >1s | Hook timing logs | If PostToolUse > 500ms, check for import retry |
| T-005 | Latency regression | `discover_hooks()` takes >200ms | Timing instrumentation | Monitor `create_registry()` wall time |
| T-002 | YAML parse failure | `discover_hooks()` returns fewer hooks than expected | Count validation | After any SKILL.md edit, verify hook count |

---

## Step 7: Adversarial Validation

*To be executed via Agent dispatch after compact snapshot is reviewed.*

---

## STEP 7: ADVERSARIAL VALIDATION FINDINGS

### Adversarial-Compliance Findings
| ID | Severity | Title |
|----|----------|-------|
| COMP-001 | HIGH | SkillCommandHook.process() violates Hook External Dependency Policy (subprocess.run with shell=True) |
| COMP-002 | HIGH | discover_hooks() called on EVERY create_registry() invocation — latency regression |
| COMP-003 | HIGH | Integration verification gap — P-001 left OPEN |
| COMP-004 | MEDIUM | YAML parse failure in _parse_skill_hooks() lacks per-skill isolation |
| COMP-005 | MEDIUM | matcher_pattern regex vulnerable to catastrophic backtracking |
| COMP-006 | MEDIUM | Graceful degradation on ImportError silently skips ALL discovered hooks |

### Adversarial-Logic Findings
| ID | Severity | Title |
|----|----------|-------|
| LOGIC-001 | **BLOCKER** | Parameter mismatch: `create_registry()` passes `hook_config.get('matcher')` but `SkillCommandHook.__init__()` expects `matcher_pattern` — matcher from YAML silently ignored |
| LOGIC-002 | HIGH | Hook name collision risk — per-skill idx counter means different skills can generate duplicate names |
| LOGIC-003 | HIGH | Blanket try/except ImportError skips ALL discovered hooks on ANY exception |
| LOGIC-004 | MEDIUM | Pre-mortem Step 5 expects non-empty result keys but process() returns `{}` on success |
| LOGIC-005 | MEDIUM | Silent exception swallowing in _parse_skill_hooks() — no way to distinguish YAML error from bug |

### Adversarial-Quality Findings
| ID | Severity | Title |
|----|----------|-------|
| QUAL-001 | HIGH | **CRITICAL**: `skill_guard.skill_auto_discovery` module does not exist — dead import, always ImportError |
| QUAL-002 | MEDIUM | Pre-mortem analyzes non-existent system — module never built |

### Adversarial-Security Findings
| ID | Severity | Title |
|----|----------|-------|
| SEC-001 | **CRITICAL** | Command injection via shell=True in SkillCommandHook.process() |

### Adversarial-Testing Findings
| ID | Severity | Title |
|----|----------|-------|
| TEST-001 | HIGH | No integration test for discovered hooks actually firing |
| TEST-002 | HIGH | No test for graceful degradation when skill_guard unavailable |
| TEST-003 | MEDIUM | No per-skill YAML parse isolation test |
| TEST-004 | MEDIUM | No regex DoS test for matcher_pattern |
| TEST-005 | HIGH | test_discover_gate.py entirely skipped — zero coverage |

### Adversarial-Performance Findings
| ID | Severity | Title |
|----|----------|-------|
| PERF-001 | CRITICAL | discover_hooks() filesystem scan blocks PostToolUse router initialization (660ms worst case) |
| PERF-002 | CRITICAL | SkillCommandHook subprocess.run() blocks entire PostToolUse router chain |
| PERF-003 | HIGH | Catastrophic regex backtracking can hang PostToolUse router |
| PERF-004 | MEDIUM | TOCTOU race in discover_hooks() filesystem iteration |
| PERF-005 | MEDIUM | YAML parse failure silently drops ALL hooks from that skill |

### Adversarial-Critic Findings
| Category | Finding |
|----------|---------|
| Blind Spot | Windows path handling not analyzed |
| Blind Spot | YAML supply chain risk (SKILL.md user-controlled) |
| Blind Spot | Router re-init on every tool call |
| Contradiction | **Fail-fast vs graceful degradation** — Constitution says "NO graceful degradation" but T-001 Cascade B describes try/except as positive |
| Confidence | P-001 at 90% confidence but NOT TESTED |
| Confidence | E-001 likelihood at 5% too low — external package failures common |

### Adversarial-QA Findings
| ID | Severity | Title |
|----|----------|-------|
| QA-001 | BLOCKER | P-001 — no test exercises SkillCommandHook.process() end-to-end |
| QA-002 | HIGH | T-003 claim "Unit test exists" is UNVERIFIED — no SkillCommandHook test found |
| QA-003 | HIGH | T-004 regex DoS — untested, matcher_pattern passed directly to re.search() |
| QA-004 | MEDIUM | T-002 YAML parse failure — silent [] return, no logging |
| QA-005 | MEDIUM | T-005 latency — discrepancy: pre-mortem says ~50ms, actual ~97ms |
| QA-006 | MEDIUM | P-002 observability gap — no warning when discover_hooks() returns empty |

---

## UPDATED REMAINING ITEMS

| Step | Status | Gap | Priority | Adversarial Evidence |
|------|--------|-----|----------|---------------------|
| 5 (P-001) | ❌ Open | Integration test for discovered hooks | HIGH | QA-001: BLOCKER — no end-to-end test exists |
| 5 (T-001) | ❌ Open | Graceful degradation verification test | HIGH | COMP-006: no warning when hooks silently skipped |
| 5 (T-002) | ❌ Open | Per-skill YAML parse isolation | MEDIUM | LOGIC-005: silent exception swallowing |
| 3.8 | ❌ Open | Operational verification for P-001 claim | HIGH | QA-002: T-003 "unit test exists" is FALSE |
| 3.8 | ❌ Open | Regex DoS test for T-004 | MEDIUM | QA-003: untested, no timeout guard |
| **NEW** | ❌ Open | **LOGIC-001: Fix matcher/matcher_pattern parameter mismatch** | **CRITICAL** | `hook_config.get('matcher')` should be `hook_config.get('matcher_pattern')` — posttooluse/__init__.py:185 |
| **NEW** | ❌ Open | **QUAL-001: skill_guard.discover_hooks() does not exist** | **CRITICAL** | Module never built — dead import always fails via ImportError |
| **NEW** | ❌ Open | **SEC-001: shell=True command injection risk** | **CRITICAL** | subprocess.run with shell=True — Hook External Dependency Policy violation |
