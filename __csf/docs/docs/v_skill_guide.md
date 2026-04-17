# /v Skill Review Guide - Sequential Validation Pipeline

**Version:** 1.0.0
**Created:** 2026-02-05
**Purpose:** Single reference document for the `/v` (sequential validation pipeline) skill and related validation commands.

---

## Overview

The `/v` skill is a **sequential validation pipeline with mandatory halt gates** that executes multiple verification stages in order. It is designed to catch issues early, prevent broken code from progressing, and ensure comprehensive validation before deployment.

### What /v Does

- **Sequential execution**: Runs 16 validation stages in a strict order
- **Mandatory halt gates**: Blocks progression on CRITICAL/HIGH findings from blocking stages
- **Multi-stage coverage**: Syntax, quality, security, testing, documentation, deployment
- **State tracking**: Tracks pipeline state across sessions with terminal isolation
- **Hook enforcement**: Uses hooks to enforce stage transitions and halt conditions

### When to Use /v vs Other Validation Commands

| Goal | Primary Skill | When to Use |
|------|--------------|-------------|
| **Full pipeline validation** | `/v <target>` | Before committing code, after implementation |
| **Quick syntax check** | `/vdate-syntax` | Fast syntax validation only |
| **Security scan** | `/vdate-security` | Security vulnerability detection |
| **Quality check** | `/vdate-quality` | Code quality and complexity analysis |
| **Adversarial review** | `/vdate-adversarial` | 7-perspective code review |
| **Deploy verification** | `/vdate-deploy` | Git status and deployment readiness |
| **TDD validation** | `/vdate-tdd` | Test execution and coverage |
| **General verification** | `/verify` | System certification via UAF |

### Key Features

- **Terminal isolation**: Multi-terminal `/v` execution with per-terminal findings
- **Layer 4 quality gate**: Filters adversarial findings by 80%+ confidence
- **Integration check**: Verifies implemented features are wired into the system
- **State management**: Tracks pipeline progress with automatic cleanup
- **Constitutional compliance**: Enforces solo-dev patterns and constraints

---

## Sequential Pipeline

### Pipeline Overview

```
STAGE 1:   Syntax              BLOCKING
STAGE 1.5: Naming              non-blocking
STAGE 2:   Quality (pylint)    BLOCKING
STAGE 2.5: Integration Check   BLOCKING (NEW - catches "implemented but not wired")
STAGE 2.6: Logging             non-blocking
STAGE 2.7: Security (bandit)   BLOCKING
STAGE 2.8: Formatting (ruff)   non-blocking
STAGE 3:   Adversarial Review  BLOCKING (with Layer 4 quality gate)
STAGE 4:   Unit Tests          BLOCKING
STAGE 4.1: Branch Coverage     BLOCKING (<50%)
STAGE 4.5: Regression Tests    BLOCKING
STAGE 5:   Integration Tests   BLOCKING
STAGE 6:   Documentation       non-blocking
STAGE 7:   Pre-commit (mypy)   non-blocking
STAGE 7.5: CVE Scan (pip-audit) BLOCKING (High/Crit)
STAGE 8:   Deploy Verification non-blocking
```

### Critical Rules

1. **Execute stages IN ORDER** - Do not skip or reorder stages
2. **HALT on CRITICAL/HIGH** - Stop pipeline on blocking stage failures
3. **Show ACTUAL output** - Display real tool output, not summaries
4. **Fresh execution** - Never reuse results from previous `/v` runs
5. **Complete each stage** - Do not proceed until current stage completes

### Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          /v SEQUENTIAL PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │ STAGE 1 │ → │ STAGE 2 │ → │ STAGE 3 │ → │ STAGE 4 │ → │ STAGE 5 │      │
│  │ Syntax  │   │ Quality │   │ Adversarial│  │ Tests  │   │ Integ   │      │
│  │ BLOCKING│   │ BLOCKING│   │ BLOCKING│   │ BLOCKING│   │ BLOCKING│      │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘      │
│       │ HALT         │ HALT         │ HALT         │ HALT         │ HALT    │
│       │ on FAIL      │ on FAIL      │ on FAIL      │ on FAIL      │ on FAIL │
│       └──────────────┴──────────────┴──────────────┴──────────────┴───────   │
│                                                                             │
│  Non-Blocking Stages (informational):                                       │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐                     │
│  │ 1.5 Nam │ → │ 2.6 Log │ → │ 2.8 Fmt │ → │ 6 Docs  │ → 7, 7.5, 8         │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Stage Details

### Stage 1: Syntax (BLOCKING)

**Purpose:** Verify Python syntax is valid and files can compile.

**Command:**
```bash
python P:/.claude/skills/v/scripts/stage1_syntax.py <target>
```

**Exit Codes:**
- `0` = PASS → Proceed
- `≠0` = FAIL → HALT

**Checks:**
- Python syntax validity via `compileall`
- Import statement errors
- Basic compilation issues

---

### Stage 1.5: Naming & Standards Compliance (Non-Blocking)

**Purpose:** Validates file naming conventions and Python 2025 standards.

**Command:**
```bash
python P:/.claude/skills/v/scripts/stage1_5_naming.py <target>
```

**Checks:**
- File naming conventions
- Python 2025 standards compliance
- Module structure

**Result:**
- `✅ PASS` or `⚠️ WARN` → Proceed

---

### Stage 2: Quality (BLOCKING)

**Purpose:** Check code quality using pylint and radon.

**Commands:**
```bash
pythonw -m pylint <target> --output-format=text --max-line-length=120 --score=y
python -m radon cc <target> -s --total-average
```

**Thresholds:**
- Pylint ≥7.0 → `✅ PASS`
- Pylint <7.0 → `⚠️ WARN` → Proceed with caution
- Tool fails → `❌ FAIL` → HALT

---

### Stage 2.5: Integration Check (BLOCKING - NEW)

**Purpose:** Verifies that implemented features are actually wired into the system. Catches "implemented but not integrated" gaps.

**MANDATORY REQUIREMENT:** Plan file or chat history reference is REQUIRED. Stage HALTS if no reference provided.

**Command:**
```bash
python P:/.claude/skills/v/scripts/stage2_5_integration.py <target> --plan <plan-file.md>
```

**Checks:**
1. Code exists - Function/class is implemented
2. Call sites - Function is called from integration points
3. Tests pass - Integration/e2e tests succeed
4. Requirements met - All requirements from plan/chat are satisfied

**Plan Discovery Priority:**
1. Same directory (primary) - Look for `plan-*.md` next to target file
2. Centralized plans/ (secondary) - Search `.claude/plans/*.md`
3. README traversal (tertiary) - Follow README.md links
4. TaskList metadata (fallback) - Query task for `plan_id` field
5. CHS search (last resort) - Search chat history
6. FAIL - No requirements source found, HALT Stage 2.5

**Results:**
- `INTEGRATED` → `✅ PASS`
- `NOT INTEGRATED` → `❌ FAIL` → Wire up function or add test
- `PARTIAL` → `⚠️ WARN` → List missing requirements
- `NO REFERENCE` → `❌ FAIL` → HALT - Create plan or document requirements

---

### Stage 2.6: Logging & Telemetry (Non-Blocking)

**Purpose:** Check that target has proper logging and telemetry instrumentation.

**Command:**
```bash
python P:/.claude/skills/v/scripts/stage2_5_logging.py <target>
```

**Checks:**
- Logging presence
- Telemetry instrumentation
- Function-level logging coverage

**Results:**
- Logging present → `✅ PASS`
- Missing logging → `⚠️ WARN` → List functions without logging

---

### Stage 2.7: Security (BLOCKING)

**Purpose:** Static security analysis for common vulnerabilities using bandit.

**Commands:**
```bash
python -m bandit -r <target> -f json -o /tmp/bandit.json
python -m bandit -r <target> -ll
```

**Results:**
- No issues → `✅ PASS`
- Medium severity → `⚠️ WARN` → List findings
- High/Critical → `❌ FAIL` → HALT

---

### Stage 2.8: Formatting (Non-Blocking)

**Purpose:** Check code formatting consistency.

**Command:**
```bash
python P:/.claude/skills/v/scripts/stage2_7_formatting.py <target>
```

**Results:**
- Formatted → `✅ PASS`
- Needs formatting → `⚠️ WARN` → Run `ruff format <target>`
- Error → `❌ FAIL` → HALT

---

### Stage 3: Adversarial Review (BLOCKING with Layer 4 Quality Gate)

**Purpose:** Parallel adversarial code review with 4 specialized agents, filtered through 4 layers.

**CRITICAL:** HALT decision is based on FILTERED findings ONLY, not raw adversarial output.

#### Stage 3 Flow

1. Launch 4 parallel adversarial agents → RAW findings (includes false positives)
2. Layer 1: Filter to changed files only
3. Layer 2: Filter against architectural pillars
4. Layer 3: Validate test quality metrics
5. **Layer 4: Quality Gate (confidence ≥80%)** → FILTERED findings (signal only)
6. **HALT decision based on FILTERED findings**

**DO NOT HALT until Layer 4 completes.**

#### Agents (Parallel Execution)

- **security** - Vulnerabilities, injection, auth issues
- **performance** - Complexity, resource leaks, bottlenecks
- **quality** - Code smells, duplication, maintainability
- **testing** - Coverage gaps, assertion quality, edge cases

#### Prompt Template

```
Analyze ONLY these files: {target_files}

Respond ONLY with valid JSON array:
[
  {
    "id": "AGENT-001",
    "severity": "CRITICAL/HIGH/MEDIUM/LOW",
    "title": "Finding title",
    "description": "Description of the issue",
    "evidence": {"file": "...", "line": N},
    "confidence": 0-100
  }
]
```

#### Filter Layers

**Layer 1: Filter to changed files only**
```bash
python P:/.claude/skills/v/scripts/stage3_layer1_delta.py <findings.json> [findings2.json ...]
```

**Layer 2: Filter against architectural pillars**
```bash
python P:/.claude/skills/v/scripts/stage3_layer2_pillars.py <layer1_output.json>
```

**Layer 3: Validate test quality metrics**
```bash
python P:/.claude/skills/v/scripts/stage3_layer3_assertions.py <layer2_output.json> --test-files <test_files>
```

**Layer 4: Quality Gate (LLM confidence filtering ≥80%)**

```
Task(
    subagent_type="quality-gate",
    prompt="""Review these adversarial findings from layers 1-3.

FINDINGS:
{layer3_filtered_findings}

For each finding:
1. Verify evidence is actionable (file:line exists, code matches)
2. Check if issue is pre-existing vs introduced
3. Apply confidence scoring (only keep ≥80%)
4. Check solo-dev applicability

Output JSON to: P:/.claude/state/quality-gate-{terminal_id}.json
Format: {filtered: [...], rejected: [...], summary: {input: N, output: M, rejection_reasons: [...]}}
""",
    description="Layer 4 quality gate - confidence filtering"
)
```

#### Results Table (FILTERED findings only)

| Condition | Action |
|-----------|--------|
| 0 CRITICAL AND 0 HIGH (filtered) | `✅ PASS` → Proceed |
| ≥1 CRITICAL OR ≥1 HIGH (filtered) | `🛑 HALT` → Stop pipeline |

**IMPORTANT:** This table applies to FILTERED findings (after Layer 4 quality-gate). RAW adversarial findings include false positives and MUST be filtered first.

#### Next Action (when HALT)

```
1 - /tdd Fix SEC-001 path traversal only
2 - /tdd Fix CRITICAL findings
3 - /tdd Fix HIGH findings
4 - /tdd Fix all filtered findings
x - /tdd All
y - /task add All (document only)

Load findings from TaskList entry: "Stage 3: Adversarial Review Findings - {target} [terminal:{current}]"
```

---

### Stage 4: Unit Tests (BLOCKING)

**Purpose:** Verify unit test coverage is complete for target.

**Commands:**
```bash
python -m pytest <target> -v --tb=short -m "unit or not (integration or regression)"
python -m pytest --cov=<target> --cov-fail-under=80
```

**Results:**
- All pass, coverage ≥80% → `✅ PASS`
- Tests fail → `❌ FAIL` → List failures
- Coverage <80% → `⚠️ WARN` → Run `/tdd <target>`
- No tests found → `❌ FAIL` → Run `/tdd <target>`

---

### Stage 4.1: Branch Coverage (BLOCKING <50%)

**Purpose:** Line coverage lies. Branch coverage catches missing edge cases.

**Command:**
```bash
python -m pytest --cov=<target> --cov-branch --cov-report=term-missing
```

**Results:**
- Branch coverage ≥80% → `✅ PASS`
- Branch coverage <80% → `⚠️ WARN` → List uncovered branches
- Branch coverage <50% → `❌ FAIL` → Critical gaps

---

### Stage 4.5: Regression Tests (BLOCKING)

**Purpose:** Run regression suite to catch regressions from changes.

**Command:**
```bash
python -m pytest tests/ -v --tb=short -m "regression"
```

**Results:**
- All pass → `✅ PASS`
- Failures → `❌ FAIL` → List regressions
- No regression tests → `⚠️ WARN` → Proceed

---

### Stage 5: Integration Tests (BLOCKING)

**Purpose:** Run integration tests to verify component interactions.

**Command:**
```bash
python -m pytest tests/ -v --tb=short -m "integration"
```

**Results:**
- All pass → `✅ PASS`
- Failures → `❌ FAIL` → List failures
- No integration tests → `⚠️ WARN` → Proceed

---

### Stage 6: Documentation (Non-Blocking)

**Purpose:** Check documentation quality and coverage.

**Command:**
```bash
python P:/.claude/skills/v/scripts/stage5_docs.py <target>
```

**Results:**
- Docstrings present → `✅ PASS`
- Missing docstrings → `⚠️ WARN` → List missing

---

### Stage 7: Pre-Commit Checks (Non-Blocking)

**Purpose:** Type checking and dead code detection.

**Commands:**
```bash
python -m mypy <target> --explicit-package-bases
python -m vulture <target> --min-confidence 80
```

**Results:**
- No errors → `✅ PASS`
- Errors found → `⚠️ WARN` → List findings

---

### Stage 7.5: Dependency Vulnerabilities (BLOCKING for High/Crit)

**Purpose:** Check for known CVEs in dependencies.

**Command:**
```bash
pip-audit --strict --progress-spinner=off
```

**Results:**
- No vulnerabilities → `✅ PASS`
- Low/Medium CVEs → `⚠️ WARN` → List and recommend updates
- High/Critical CVEs → `❌ FAIL` → HALT, must fix before deploy

---

### Stage 8: Deploy Verification (Non-Blocking/Informational)

**Purpose:** Verify git repository status before deployment.

**Commands:**
```bash
git status
git diff
git log --oneline -5
```

**Results:**
- Clean working state → `✅ PASS` → Pipeline complete
- Uncommitted changes → `ℹ️ INFO` → Show status

---

## Sub-Skills Reference

### /vdate-* Skills

#### /vdate-syntax

**Purpose:** Check Python syntax using compileall.

**Usage:**
```bash
/vdate-syntax file.py
/vdate-syntax file1.py,file2.py
```

**Checks:**
- Python syntax validity
- Import statement errors
- Basic compilation issues

**Exit Codes:**
- `0` = PASS
- `1` = FAIL

---

#### /vdate-security

**Purpose:** Security pattern validation - detects dangerous code patterns.

**Usage:**
```bash
/vdate-security file.py
/vdate-security file1.py,file2.py
```

**Checks:**

**Code Execution:**
- `exec()` - Code execution via exec()
- `eval()` - Code execution via eval()
- `compile()` - Code compilation
- `__import__()` - Dynamic imports

**Command Injection:**
- `os.system()` - Command injection
- `subprocess.call(shell=True)` - Shell injection

**Format String Injection:**
- `input()` with `format()`

**Hardcoded Secrets:**
- `password = "..."`
- `secret = "..."`
- `api_key = "..."`
- `token = "..."`

**Exit Codes:**
- `0` = PASS
- `1` = FAIL

---

#### /vdate-quality

**Purpose:** Code quality check using radon, ruff, AST complexity, and lizard.

**Usage:**
```bash
/vdate-quality file.py
/vdate-quality file.py --threshold 10
```

**Checks:**

1. **Radon (Cyclomatic Complexity)**
   - Measures code complexity via subprocess
   - Flags overly complex functions (A-F grading)

2. **Ruff (Python Linter)**
   - Code style issues
   - Unused imports
   - Potential bugs
   - PEP 8 compliance

3. **AST-based Complexity**
   - Function-level cyclomatic complexity analysis
   - Configurable threshold (default: 15)
   - Provides file:line citations

4. **Lizard (Multi-language CC)**
   - Multi-language complexity analysis
   - Severity ranking: MEDIUM (11-20), HIGH (21+)

**Severity Ranking:**

| Complexity Score | Grade | Severity | Action |
|------------------|-------|----------|--------|
| 1-10 | A/B | - | None |
| 11-15 | C | MEDIUM | Monitor |
| 16-20 | C | MEDIUM | Consider refactor |
| 21-50 | D | HIGH | Should refactor |
| 51+ | E/F | CRITICAL | Must refactor |

**Exit Codes:**
- `0` = PASS
- `1` = FAIL

---

#### /vdate-adversarial

**Purpose:** Adversarial code review - 7 parallel perspectives.

**Usage:**
```bash
/vdate-adversarial file.py
/vdate-adversarial file1.py,file2.py
```

**7 Adversarial Perspectives:**
- **Compliance** - Spec/schema validation
- **Performance** - Bottlenecks, N+1 patterns
- **Quality** - Maintainability risks, technical debt
- **Security** - Data leaks, access control gaps
- **Testing** - Missing test scenarios, coverage gaps
- **Patterns** - Anti-patterns detection
- **Logic** - Race conditions, edge cases

**Implementation:** Calls `run_adversarial_check()` from `hybrid_orchestrator.py`.

**Exit Codes:**
- `0` = PASS (no critical issues)
- `1` = FAIL (issues found)

**Note:** This is a comprehensive review that may take 15-30 seconds depending on file size.

---

#### /vdate-tdd

**Purpose:** TDD validation using pytest.

**Usage:**
```bash
/vdate-tdd file.py
/vdate-tdd tests/
```

**Checks:**
- Test execution via pytest
- Test failures and errors
- Test coverage (if configured)

**Exit Codes:**
- `0` = PASS
- `1` = FAIL

---

#### /vdate-execution

**Purpose:** Execute code to verify it works (Stage 2).

**Usage:**
```bash
/vdate-execution file.py
```

**Checks:**
- Code execution with 10s timeout
- Runtime errors
- Import errors
- Basic functionality verification

**WARNING:** This executes your code! Only use with files you trust.

**Exit Codes:**
- `0` = PASS
- `1` = FAIL

---

#### /vdate-documentation

**Purpose:** Documentation quality check.

**Usage:**
```bash
/vdate-documentation file.py
/vdate-documentation file1.py,file2.py
```

**Checks:**
- Module docstrings (triple-quoted strings)
- Comments presence
- Basic documentation coverage

**Exit Codes:**
- `0` = PASS
- `1` = FAIL

---

#### /vdate-deploy

**Purpose:** Deploy verification using git commands.

**Usage:**
```bash
/vdate-deploy file.py
/vdate-deploy
```

**Checks:**
- Git repository status
- Uncommitted changes
- Branch verification

**Exit Codes:**
- `0` = PASS
- `1` = FAIL

---

### Related Validation Skills

#### /verify

**Purpose:** Verify implementation against specifications via UAF (Unified Analysis Framework).

**Triggers:** `/verify`

**Usage:**
```bash
/verify                    # Changed files this session
/verify src/validators.py  # Specific file
/verify --tier 1           # Syntax only (fast)
/verify --tier 1,2         # Syntax + types (no tests)
/verify --review           # Show metrics, evaluate process
```

**Verification Tiers:**

| Tier | Check | Tool | Fail = |
| ---- | ---------- | ----------------------- | --------------------- |
| 1 | Syntax | `ast.parse()` | Broken code |
| 2 | Types/Lint | `mypy --strict`, `ruff` | Type errors, style |
| 3 | Tests | `pytest <related>` | Functional regression |

**Key Features:**
- System certification through 3 tiers
- Configurable scope and tier selection
- Non-blocking: Warnings don't block, failures do
- TDD compliant verification

---

#### /validate-safety-patterns

**Purpose:** Safety pattern validation with evidence-based reporting.

**Triggers:** `/validate-safety-patterns`

**Usage:**
```bash
/validate-safety-patterns
/validate-safety-patterns --comprehensive
/validate-safety-patterns --category=database
```

**Categories Validated:**
- Database (95% success rate)
- JSON (98% success rate)
- Path (90% success rate)
- Import (92% success rate)
- Hook (100% success rate)

---

#### /validate_spec

**Purpose:** Validate implementation against specification (specify.md).

**Triggers:** `/validate-spec`

**Usage:**
```bash
/validate-spec [--spec path/to/spec.md] [--impl path/to/src]
```

**Severity Thresholds:**

| Coverage | Severity | Recommendation |
| -------- | ----------- | ------------------------------- |
| 95-100% | NOMINAL | Ready to ship |
| 80-94% | MINOR | Add final implementation/tests |
| 50-79% | MAJOR | Return to Phase 2 (ALIGN) |
| <50% | CRITICAL | Significant spec drift detected |

---

## Workflows

### Before Committing Code

```bash
# Full pipeline validation
/v <target>

# Or specific validation stages
/vdate-syntax <target>
/vdate-security <target>
/vdate-quality <target>
/vdate-tdd <target>
```

### After Implementation

```bash
# 1. Run full validation pipeline
/v <target>

# 2. If Stage 3 (Adversarial) fails:
/tdd Fix CRITICAL findings
/tdd Fix HIGH findings

# 3. Re-run validation
/v <target>

# 4. If all stages pass:
/vdate-deploy  # Verify git status
```

### For PR Validation

```bash
# 1. Validate all changes
/v <files>

# 2. Check specification compliance
/validate-spec --spec specify.md --impl src/

# 3. Verify safety patterns
/validate-safety-patterns

# 4. Run deploy verification
/vdate-deploy
```

---

## Terminal Isolation (v2.0)

### Multi-Terminal /v Execution

**Multi-terminal `/v` execution** is supported via terminal-isolated adversarial findings.

### File Naming Convention

Adversarial findings are stored per-terminal:

```
P:/.claude/state/v_findings/{terminal_id}/adversarial-{agent}-{terminal_id}.json
```

- `{terminal_id}`: Unique terminal identifier from `terminal_detection.py`
- `{agent}`: One of `security`, `performance`, `quality`, `testing`
- Single file per agent per terminal (overwrites on each run)
- No accumulation of timestamped files

### Cleanup

- **7-day threshold**: Files older than 7 days are automatically cleaned up
- **Abandoned sessions**: Terminals not reused for 7+ days have findings removed
- **Call**: `state_manager_v.cleanup_adversarial_findings()` (called on session start)

### Migration

Old timestamped files (`adversarial-{agent}-{datetime}.json`) can be safely deleted:

```bash
# Remove old adversarial findings (before terminal isolation)
rm P:/.claude/state/adversarial-*.json
```

New files use terminal-scoped paths and won't interfere with multi-terminal workflows.

---

## Integration Points

### Hooks

The `/v` skill uses multiple hooks for enforcement:

| Hook Phase | Hook File | Purpose |
|-----------|-----------|---------|
| PreToolUse | `PreToolUse_v_gate.py` | Gate Write/Edit operations |
| PreToolUse | `PreToolUse_v_stage_enforcer.py` | Enforce stage order |
| PostToolUse | `PostToolUse_v_halt_enforcer.py` | Enforce halt conditions |
| PostToolUse | `PostToolUse_v_validator.py` | Validate stage completion |
| PostToolUse | `PostToolUse_v_transition.py` | Handle stage transitions |
| PostToolUse | `PostToolUse_v_init.py` | Initialize pipeline state |
| PostToolUse | `PostToolUse_v_session_marker.py` | Mark session state |
| PostToolUse | `PostToolUse_v_stage_tracker.py` | Track stage progress |
| PostToolUse | `PostToolUse_v_state_tracker.py` | Track pipeline state |
| SessionEnd | `SessionEnd_v_cleanup.py` | Cleanup on session end |
| Stop | `StopHook_v_completion_gate.py` | Gate pipeline completion |
| Stop | `StopHook_v_continuation.py` | Handle continuation |

### Scripts

| Script | Purpose |
|--------|---------|
| `stage1_syntax.py` | Syntax validation |
| `stage1_5_naming.py` | Naming and standards compliance |
| `stage2_5_logging.py` | Logging and telemetry check |
| `stage2_7_formatting.py` | Formatting check |
| `stage3_layer1_delta.py` | Layer 1: Filter to changed files |
| `stage3_layer2_pillars.py` | Layer 2: Filter against architectural pillars |
| `stage3_layer3_assertions.py` | Layer 3: Validate test quality metrics |
| `stage3_findings.py` | Create TaskList entry for findings |
| `stage5_docs.py` | Documentation check |

### State Management

State is tracked in:
- `P:/.claude/state/v_findings/{terminal_id}/` - Adversarial findings per terminal
- `P:/.claude/state/v_state.json` - Pipeline state (with terminal isolation)

---

## Quick Reference Table

| Goal | Use | Alternative | Notes |
|------|-----|-------------|-------|
| **Full validation** | `/v <target>` | N/A | 16 stages sequential pipeline |
| **Syntax check** | `/vdate-syntax` | N/A | Fast syntax validation |
| **Security scan** | `/vdate-security` | N/A | Vulnerability detection |
| **Quality check** | `/vdate-quality` | N/A | Complexity and linting |
| **Adversarial review** | `/vdate-adversarial` | `/adversarial-review` | 7-perspective review |
| **TDD validation** | `/vdate-tdd` | `/tdd` | Test execution |
| **Deploy check** | `/vdate-deploy` | N/A | Git status verification |
| **Spec validation** | `/validate-spec` | N/A | Implementation vs spec |
| **Safety patterns** | `/validate-safety-patterns` | N/A | Safety pattern compliance |
| **General verification** | `/verify` | N/A | UAF system certification |

---

## Best Practices

### For Validation

1. **Run full pipeline before committing** - `/v <target>` catches issues early
2. **Respect halt gates** - Don't proceed past CRITICAL/HIGH findings
3. **Use terminal isolation** - Multi-terminal workflows supported
4. **Check integration** - Stage 2.5 ensures implementation is wired
5. **Filter adversarial findings** - Layer 4 quality gate reduces false positives

### For Stage 3 (Adversarial)

1. **Wait for Layer 4** - Don't halt until quality gate completes
2. **Filter before acting** - Only address FILTERED findings (≥80% confidence)
3. **Use TaskList** - Findings persist across compaction with terminal isolation
4. **Fix in priority order** - CRITICAL → HIGH → MEDIUM → LOW

### For Integration Checks

1. **Always provide plan reference** - Stage 2.5 HALTS without it
2. **Co-locate plans with code** - Best practice for plan discovery
3. **Verify requirements coverage** - Check all requirements from plan/chat
4. **Test call sites** - Ensure functions are actually called

### Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **Skipping stages** | Incomplete validation | Run all stages in order |
| **Ignoring halt gates** | Broken code progresses | HALT on CRITICAL/HIGH |
| **Acting on raw findings** | False positives fixed | Wait for Layer 4 filtering |
| **Missing plan reference** | Stage 2.5 HALTS | Provide `--plan <file.md>` |
| **Reusing old results** | Stale validation | Always run fresh `/v` |

---

## Constitutional Compliance

All validation skills MUST filter action items against `SoloDevConstitutionalFilter`.

### Prohibited Patterns (Auto-Filter)

| Pattern | Filter Because | Alternative |
|---------|---------------|-------------|
| `lock ordering`, `acquisition order` | Enterprise bloat | Use single RLock per object |
| `continuous monitoring`, `real-time metrics` | Background service prohibited | Use on-demand checks |
| `self-healing` | Autonomous execution prohibited | Manual fix with approval |
| `autonomous execution` | Autonomous execution prohibited | Step-by-step with confirmation |
| `enterprise-grade`, `scalability requirement` | Enterprise pattern prohibited | Use simple solution |
| `team approval`, `stakeholder consensus` | Consensus process prohibited | Singular dev decides |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-05 | Initial consolidation of /v skill and related validation commands |

---

**See Also:**
- `CLAUDE.md` - Constitutional principles and constraints
- `plan_review_guide.md` - Plan review and improvement skills
- `TDD_SYSTEM.md` - Test-driven development workflow
