# Implementation Plan: /t Command Refinements for Adaptive Testing Depth

**Plan ID:** plan-20260225-t-command-refinements
**Created:** 2025-02-25
**Status:** Draft
**Author:** Plan-Workflow Builder

## Executive Summary

Implement `/t` command refinements for adaptive testing depth with smarter change detection, director ergonomics, and safer fallback. This plan creates a NEW `/t` command as an independent skill that provides enhanced testing intelligence beyond the existing `/test` command.

**Key Finding:** The `/t` command does NOT currently exist. This is a net-new feature creating a separate skill at `P:/__claude/skills/t/SKILL.md` (not an alias - independent skill with its own implementation).

**Architectural Decision:** `/t` is its own skill that shares common infrastructure with `/test` (like `test_health_check.py`) but implements distinct behavior for adaptive testing depth.

---

## 1. Problem Statement

### 1.1 What Problem Do These Refinements Solve?

**Current State:**
- `/test` command provides comprehensive coverage analysis but runs uniformly regardless of change scope
- No explicit git state mode detection (assumes git is available)
- Fixed depth (T1 + T2 always run as hard failures)
- Output format optimized for developers, not directors/decision-makers
- No deterministic risk scoring for test prioritization

**Desired State:**
- `/t` command (independent skill) adapts depth based on change size and git state
- Explicit mode detection: `no_git` | `unstaged` | `staged` | `last_commit` | `full_scan`
- Adaptive strictness: High risk changes → T1+T2 hard fails, Low risk → T2 as warnings
- Director-friendly summary tables with AI-ready orders for coverage gaps
- Safer no-git fallback using `testing.yml` configuration

### 1.2 Why Are These Refinements Needed?

**User Pain Points:**
1. **Over-testing small changes:** Running full test suite for 3-line wastes time
2. **Under-testing large changes:** Quick smoke test misses edge cases in refactors
3. **Director friction:** Non-technical stakeholders can't quickly assess risk
4. **Git dependency breaks:** Multi-terminal environments have unreliable git state
5. **No risk prioritization:** All findings treated equally, masking critical issues

**Business Value:**
- **Developer productivity:** 30-50% faster testing cycles through adaptive depth
- **Stakeholder visibility:** Directors get actionable summaries without reading code
- **Better coverage:** High-risk changes get appropriate scrutiny
- **Multi-terminal safety:** System works reliably across git worktrees

---

## 2. Context Analysis

### 2.1 Current /test Command Architecture

**Location:** `P:\.claude\skills\test\SKILL.md`

**Key Components:**

| Component | Type | Location | Purpose |
|-----------|------|----------|---------|
| Test Discovery | Pattern-based | SKILL.md:87-94 | Find test files via glob patterns |
| Test Classification | Manual | SKILL.md:101-119 | Unit, Integration, Edge Case, Error Path, Regression |
| Health Check | Python utility | `P:\.claude\skills\test_health_check.py` | Detect slow tests, bad paths, collection errors |
| Solo-Dev Pattern Scan | Grep-based | SKILL.md:232-264 | Detect constitutional violations |
| Pytest Coverage | Shell command | SKILL.md:268-303 | Real coverage % via pytest-cov |
| Gap Analysis | Manual mapping | SKILL.md:307-348 | Map code components to test coverage |

### 2.1.1 /t vs /test: Key Differences

**IMPORTANT:** `/t` is a **separate, independent skill**—not an alias, not a wrapper.

| Aspect | `/test` command | `/t` command (PROPOSED) |
|--------|----------------|-------------------------|
| **Skill file** | `P:/.claude/skills/test/SKILL.md` | `P:/.claude/skills/t/SKILL.md` (net-new) |
| **Purpose** | General test coverage analysis | Adaptive testing depth with smarter detection |
| **Depth control** | Fixed (always runs full T1+T2) | Adaptive based on risk score (tier + size + kind) |
| **Change detection** | Manual module specification | Automatic git state detection |
| **Risk scoring** | None (all findings equal) | Deterministic 0-1 score prioritizes critical issues |
| **Strictness** | T1+T2 always hard failures | Adaptive: high risk = hard fail, low risk = warning |
| **Director ergonomics** | Developer-focused output | Decision summary tables + AI-ready gap messages |
| **No-git fallback** | Fails without git repository | Uses `testing.yml` configuration for safer fallback |
| **Shared infrastructure** | — | ✅ Reuses `test_health_check.py` and discovery logic |

**Architectural relationship:**
- `/t` imports and calls `/test` infrastructure functions (like `test_health_check.py`)
- `/t` has its own adaptive logic, risk scoring, and director ergonomics
- Both skills coexist—users invoke `/t` for smart testing, `/test` for manual analysis
- This is code reuse, not aliasing—similar to how multiple commands might share `cks_integration.py`

**Allowed APIs:**
- `Bash` tool: Run pytest, git commands, health check script
- `Grep` tool: Search for test patterns, solo-dev violations
- `Glob` tool: Find test files
- `Read` tool: Read test files for classification
- `Task` tool: Spawn parallel subagents for health check
- `Edit/Write` tools: Create `.test_gaps.json` for `/tdd` integration

### 2.2 TestingContext Structure (PROPOSED)

**Current:** No explicit dataclass (context inferred from workflow)

**Proposed Structure:**
```python
@dataclass
class TestingContext:
    """Context for /t command execution."""
    # Git state detection
    git_state: GitState  # no_git | unstaged | staged | last_commit | full_scan
    git_root: Optional[Path]
    branch_name: Optional[str]

    # Target scope
    target_path: Path
    changed_files: List[Path]  # Files changed in current git state

    # Configuration
    testing_yml_path: Optional[Path]  # Path to testing.yml if exists

    # Results
    modules_tested: List[str]
    modules_skipped: List[str]
    coverage_report: Optional[Dict]
```

### 2.3 ModuleRisk Calculation (PROPOSED)

**Current:** Risk inferred from tier classification (implicit)

**Proposed Structure:**
```python
@dataclass
class ModuleRisk:
    """Risk assessment for a module."""
    module_name: str

    # Existing tier classification
    tier: str  # T1 (functional) | T2 (coverage) | T3 (edge case)

    # NEW: Change metadata
    change_size: int  # Lines changed (additions + deletions)
    change_kind: str  # bugfix | feature | refactor | config | docs

    # NEW: Deterministic risk score (0-1)
    risk_score: float  # Derived from tier + size + kind

    # NEW: Adaptive strictness
    t1_strictness: str  # hard_fail | soft_fail | skip
    t2_strictness: str  # hard_fail | soft_fail | skip
```

**Risk Score Formula:**
```python
# Deterministic calculation (no ML, no LLM)
base_score = {
    'T1': 0.3,  # Functional tests: baseline risk
    'T2': 0.5,  # Coverage tests: higher risk
    'T3': 0.7,  # Edge cases: highest risk
}[tier]

size_multiplier = min(change_size / 1000, 2.0)  # Cap at 2x for large changes
kind_multiplier = {
    'bugfix': 1.5,
    'feature': 1.2,
    'refactor': 1.3,
    'config': 0.8,
    'docs': 0.5,
}[change_kind]

risk_score = min(base_score * size_multiplier * kind_multiplier, 1.0)

# Adaptive strictness based on risk
if risk_score >= 0.7:
    t1_strictness = 'hard_fail'
    t2_strictness = 'hard_fail'
elif risk_score >= 0.4:
    t1_strictness = 'hard_fail'
    t2_strictness = 'soft_fail'  # Warning, not blocker
else:
    t1_strictness = 'soft_fail'
    t2_strictness = 'skip'  # Don't run T2 for trivial changes
```

### 2.4 testing.yml Schema (PROPOSED)

**Current:** No testing.yml schema exists

**Proposed Schema:**
```yaml
# testing.yml - Project-specific testing configuration
discovery:
  # Where to find test files (used when git unavailable)
  roots:
    - tests/
    - src/**/tests/
    - test/

  # Patterns to exclude from test discovery
  exclude:
    - "**/venv/**"
    - "**/.venv/**"
    - "**/node_modules/**"
    - "**/__pycache__/**"

# NEW: Representative functions for LLM test generation
representative_functions:
  module_auth:
    - login()      # Entry point for auth flow
    - logout()     # Boundary of auth session
    - authenticate()  # Core business logic

  module_database:
    - connect()    # Connection setup
    - query()      # Core operation
    - disconnect() # Cleanup

# Tier thresholds for adaptive depth
tiers:
  T1_functional:
    description: "Core functionality tests"
    risk_threshold: 0.4  # Run if risk_score >= 0.4

  T2_coverage:
    description: "Coverage and edge case tests"
    risk_threshold: 0.7  # Run if risk_score >= 0.7
```

### 2.5 Allowed APIs

**For /t command implementation:**

| API | Usage | Restrictions |
|-----|-------|--------------|
| `Bash` | Run pytest, git commands, health check | Always use absolute paths |
| `Grep` | Find test patterns, solo-dev violations | Use `-C` for context |
| `Glob` | Find test files, testing.yml | Always verify results exist |
| `Read` | Read test files for classification | Read full file, not snippets |
| `Task` | Spawn parallel health check subagents | Use haiku model for speed |
| `Write` | Create `.test_gaps.json` | Always validate JSON schema |
| `Edit` | Not recommended (risk of corruption) | Use Write instead |

**Forbidden APIs:**
- **WebSearch:** Test analysis is local-only
- **Skill tool:** /t should not invoke other skills directly
- **Playwright:** No browser automation for test discovery

### 2.6 Anti-patterns to Avoid

| Anti-pattern | Why Wrong | Correct Approach |
|--------------|-----------|------------------|
| **Synthesizing test results** | Violates "evidence-based" rule | Always run actual pytest/bash commands |
| **Hard-coded git paths** | Breaks in worktrees | Use `git rev-parse --git-dir` to detect |
| **Assuming pytest available** | May not be installed | Check via `pytest --version` first |
| **Listing all files** | Too slow (7500+ files) | Use changed_files from git diff |
| **Running full test suite** | 48GB+ memory usage | Use `--collect-only` for detection |
| **Ignoring solo-dev violations** | Constitutional violations = wrong tests | Always scan, report as gaps |
| **Generating LLM prompts inline** | Skill-level task, not inline | Use representative_functions from testing.yml |

---

## 3. Existing Implementation Discovery

### 3.1 What Code Already Exists?

**Reusable Assets:**

1. **Test Health Check Utility** (`P:\.claude\skills\test_health_check.py`)
   - Lines 102-145: `check_slow_tests_missing_markers()` - Finds slow tests without markers
   - Lines 148-186: `check_hardcoded_paths()` - Detects worktree-specific paths
   - Lines 189-209: `check_conftest_marker()` - Validates conftest.py configuration
   - Lines 212-282: `check_pytest_collection_errors()` - Detects INTERNALERROR, SystemExit
   - Lines 285-312: `run_health_check()` - Orchestrates all checks
   - Lines 315-381: `format_health_check_report()` - Pretty-print results

   **Reuse Strategy:** Import directly in `/t` workflow:
   ```python
   import sys
   from pathlib import Path
   skills_dir = Path(__file__).parent.parent.parent.parent / ".claude" / "skills"
   sys.path.insert(0, str(skills_dir))
   from test_health_check import run_health_check, format_health_check_report
   ```

2. **Test Discovery Patterns** (`P:\.claude\skills\test\SKILL.md`)
   - Lines 130-134: Test file patterns (test_*.py, *_integration.py)
   - Lines 138-144: Test classification table (Unit, Integration, Edge Case, Error Path)
   - Lines 238-247: Forbidden solo-dev patterns table

   **Reuse Strategy:** Copy pattern tables to new `testing_patterns.py` module

3. **Gap File Schema** (`P:\.claude\skills\test\SKILL.md:459-486`)
   - Existing `.test_gaps.json` schema for `/tdd` integration
   - Fields: target, timestamp, pytest_coverage, solo_dev_violations, gaps, status

   **Reuse Strategy:** Extend with new fields for `/t` refinements:
   ```json
   {
     "git_state": "unstaged",
     "risk_score": 0.75,
     "adaptive_strictness": {"T1": "hard_fail", "T2": "hard_fail"},
     ...existing fields
   }
   ```

### 3.2 What Can We Reuse?

**High Reuse (copy-paste with modifications):**
- Test classification patterns
- Solo-dev violation patterns
- Health check utility (import as-is)
- Gap file schema (extend, don't break)

**Medium Reuse (adapt to new context):**
- Pytest coverage invocation (add mode detection)
- Test discovery workflow (add git state filtering)

**No Reuse (net-new implementation):**
- Git state detection (no existing code)
- Risk scoring algorithm (net-new formula)
- Director summary tables (new output format)
- testing.yml schema (new configuration)

### 3.3 Integration Points

**Existing Skills to Integrate:**

| Skill | Integration Point | Data Flow |
|-------|-------------------|-----------|
| `/tdd` | `.test_gaps.json` | `/t` writes → `/tdd` reads |
| `/verify` | Pytest results | Share pytest JSON output |
| `/qa` | Coverage reports | Pass-through coverage data |
| `/comply` | Solo-dev violations | Violations → comply checks |

---

## 4. Test Discovery

### 4.1 What Test Scenarios Exist?

**From codebase analysis:**

| Scenario Type | Example | Count |
|---------------|---------|-------|
| Unit tests | `test_mark_cleared_blocks_add` | ~2000+ tests across projects |
| Integration tests | `test_stop_hook_flow` | ~150 tests |
| Edge case tests | `test_empty_input` | ~50 tests |
| Error path tests | `test_corrupted_json` | ~80 tests |
| Slow tests (with @pytest.mark.slow) | E2E, race conditions | ~30 tests |

**Test File Patterns (from existing /test skill):**

| Pattern | Meaning | Example |
|---------|---------|---------|
| `test_<function>()` | Unit test for single function | `test_mark_cleared()` |
| `test_*_integration()` | Integration test | `test_router_integration()` |
| `test_*edge*` | Edge case test | `test_empty_input_edge()` |
| `test_*error*` | Error path test | `test_corrupted_json_error()` |
| `test_*regression*` | Regression test | `test_reproduce_bug_123()` |

### 4.2 What Needs to Be Tested?

**New /t Command Test Scenarios:**

| Scenario | Description | Priority |
|----------|-------------|----------|
| **Git state detection** | Correctly identifies no_git, unstaged, staged, last_commit | HIGH |
| **Change size calculation** | Accurately counts lines changed (additions + deletions) | HIGH |
| **Risk score formula** | Produces deterministic scores in [0,1] range | HIGH |
| **Adaptive strictness** | T1/T2 enforcement changes based on risk_score | HIGH |
| **No-git fallback** | Uses testing.yml roots/exclude when git unavailable | MEDIUM |
| **Director summary table** | Generates decision-friendly output format | MEDIUM |
| **AI-ready orders** | Converts gaps to LLM prompt format | MEDIUM |
| **testing.yml parsing** | Loads representative_functions correctly | LOW |

**Edge Cases to Test:**

| Edge Case | Expected Behavior |
|-----------|-------------------|
| Empty git repo (no commits) | `git_state = no_git` |
| Worktree without .git | `git_state = no_git`, use testing.yml |
| No changed files | `git_state = full_scan`, test all modules |
| Single-line change | `change_size = 1`, `risk_score` low, T2 skip |
| 1000+ line refactor | `change_size = 1000+`, `risk_score` high, T1+T2 hard fail |
| No testing.yml | Use default patterns (tests/, src/**/tests/) |
| Invalid testing.yml | Gracefully degrade to defaults |

---

## 5. Proposed Solution

### 5.1 Design for Each Refinement

#### Refinement 1: Smarter Change Detection (Stateless)

**Implementation Location:** `P:\.claude\skills\test\git_state_detector.py` (NEW)

**Algorithm:**
```python
def detect_git_state(cwd: Path) -> GitState:
    """
    Detect git repository state using explicit mode detection.
    Returns: GitState enum (no_git | unstaged | staged | last_commit | full_scan)
    """
    # Step 1: Check if git is available
    try:
        git_dir = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=cwd,
            capture_output=True,
            timeout=5
        )
        if git_dir.returncode != 0:
            return GitState.NO_GIT
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return GitState.NO_GIT

    # Step 2: Check for unstaged changes
    unstaged = subprocess.run(
        ['git', 'diff', '--name-only'],
        cwd=cwd,
        capture_output=True,
        timeout=5
    )
    if unstaged.stdout.strip():
        return GitState.UNSTAGED

    # Step 3: Check for staged changes
    staged = subprocess.run(
        ['git', 'diff', '--staged', '--name-only'],
        cwd=cwd,
        capture_output=True,
        timeout=5
    )
    if staged.stdout.strip():
        return GitState.STAGED

    # Step 4: Check if last commit exists
    try:
        last_commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=cwd,
            capture_output=True,
            timeout=5
        )
        if last_commit.returncode == 0:
            # Check if working tree is clean
            status = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=cwd,
                capture_output=True,
                timeout=5
            )
            if not status.stdout.strip():
                return GitState.LAST_COMMIT  # Clean tree, test last commit
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Step 5: Fallback to full scan
    return GitState.FULL_SCAN
```

**Storage on TestingContext:**
```python
@dataclass
class TestingContext:
    git_state: GitState  # Store detected mode
    git_root: Optional[Path]
    # ... other fields
```

**Surfacing in Output:**
```markdown
## Test Coverage Report: notification_queue.py

**Git State:** unstaged (5 files changed)
**Branch:** feature/add-notifications
**Mode:** Testing changed files only (adaptive depth)
```

**Using testing.yml for no-git fallback:**
```python
def get_test_roots_from_config(cwd: Path) -> List[Path]:
    """Load test roots from testing.yml, use defaults if missing."""
    config_path = cwd / "testing.yml"
    default_roots = [Path("tests"), Path("src") / "tests"]

    if not config_path.exists():
        return default_roots

    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return [Path(p) for p in config.get("discovery", {}).get("roots", default_roots)]
    except (yaml.YAMLError, KeyError, IOError):
        return default_roots  # Gracefully degrade
```

#### Refinement 2: Adaptive Depth (Deterministic)

**Implementation Location:** `P:\.claude\skills\test\risk_calculator.py` (NEW)

**Data Structures:**
```python
from enum import Enum
from dataclasses import dataclass

class GitState(Enum):
    NO_GIT = "no_git"
    UNSTAGED = "unstaged"
    STAGED = "staged"
    LAST_COMMIT = "last_commit"
    FULL_SCAN = "full_scan"

class ChangeKind(Enum):
    BUGFIX = "bugfix"
    FEATURE = "feature"
    REFACTOR = "refactor"
    CONFIG = "config"
    DOCS = "docs"

@dataclass
class ModuleRisk:
    module_name: str
    tier: str  # T1 | T2 | T3
    change_size: int  # Lines changed
    change_kind: ChangeKind
    risk_score: float  # 0-1
    t1_strictness: str  # hard_fail | soft_fail | skip
    t2_strictness: str  # hard_fail | soft_fail | skip
```

**Risk Score Algorithm:**
```python
def calculate_risk_score(module: str, tier: str, change_size: int, change_kind: ChangeKind) -> float:
    """
    Derive deterministic risk score (0-1) from tier + size + kind.
    NO ML, NO LLM - pure formula.
    """
    # Base score from tier
    tier_scores = {"T1": 0.3, "T2": 0.5, "T3": 0.7}
    base_score = tier_scores.get(tier, 0.5)

    # Size multiplier (cap at 2x for changes >1000 lines)
    size_multiplier = min(change_size / 1000.0, 2.0)

    # Kind multiplier
    kind_multipliers = {
        ChangeKind.BUGFIX: 1.5,
        ChangeKind.FEATURE: 1.2,
        ChangeKind.REFACTOR: 1.3,
        ChangeKind.CONFIG: 0.8,
        ChangeKind.DOCS: 0.5,
    }
    kind_multiplier = kind_multipliers.get(change_kind, 1.0)

    # Calculate and cap at 1.0
    risk_score = min(base_score * size_multiplier * kind_multiplier, 1.0)
    return round(risk_score, 2)
```

**Adaptive Strictness:**
```python
def determine_strictness(risk_score: float) -> tuple[str, str]:
    """
    Adjust strictness: High risk → T1+T2 hard fails, Low risk → T2 as warnings.
    Returns: (t1_strictness, t2_strictness)
    """
    if risk_score >= 0.7:
        return ("hard_fail", "hard_fail")
    elif risk_score >= 0.4:
        return ("hard_fail", "soft_fail")  # T2 is warning, not blocker
    else:
        return ("soft_fail", "skip")  # Trivial changes, skip T2
```

**Integration with Test Execution:**
```python
def run_adaptive_tests(module_risks: List[ModuleRisk]) -> TestResults:
    """Run tests with adaptive strictness based on risk."""
    results = []

    for risk in module_risks:
        # Determine which tests to run
        if risk.t1_strictness != "skip":
            result = run_t1_tests(risk.module_name)
            results.append({
                "module": risk.module_name,
                "tier": "T1",
                "strictness": risk.t1_strictness,
                "result": result,
                "should_block": risk.t1_strictness == "hard_fail" and result.failed
            })

        if risk.t2_strictness != "skip":
            result = run_t2_tests(risk.module_name)
            results.append({
                "module": risk.module_name,
                "tier": "T2",
                "strictness": risk.t2_strictness,
                "result": result,
                "should_block": risk.t2_strictness == "hard_fail" and result.failed
            })

    return results
```

#### Refinement 3: Director Ergonomics

**Implementation Location:** `P:\.claude\skills\test\director_formatter.py` (NEW)

**Decision Summary Table:**
```python
def format_decision_summary(module_risks: List[ModuleRisk], test_results: List[TestResult]) -> str:
    """
    Generate decision summary table showing module/tier/action/reason.
    Optimized for director-level visibility.
    """
    lines = ["## Testing Decision Summary", ""]
    lines.append("| Module | Tier | Action | Reason |")
    lines.append("|--------|------|--------|--------|")

    for risk in module_risks:
        result = find_result(test_results, risk.module_name, risk.tier)

        if result.failed and risk.risk_score >= 0.7:
            action = "BLOCKED"
            reason = f"Critical risk ({risk.risk_score:.2f}), {risk.change_kind} ({risk.change_size} lines)"
        elif result.failed and risk.risk_score < 0.4:
            action = "WARNING"
            reason = f"Low risk ({risk.risk_score:.2f}), non-blocking"
        elif risk.t2_strictness == "skip":
            action = "SKIPPED"
            reason = f"Low risk ({risk.risk_score:.2f}), T2 not required"
        else:
            action = "PASS"
            reason = "All tests passed"

        lines.append(f"| {risk.module_name} | {risk.tier} | {action} | {reason} |")

    return "\n".join(lines)
```

**Coverage Gaps as AI-Ready Orders:**
```python
def format_coverage_gaps_ai(gaps: List[TestGap]) -> str:
    """
    Convert gaps to AI-ready orders: "Ask LLM: Add tests for edge cases X, Y, Z"
    """
    lines = ["## Coverage Gaps (AI-Ready Orders)", ""]

    # Group gaps by module
    by_module = {}
    for gap in gaps:
        by_module.setdefault(gap.module, []).append(gap)

    for module, module_gaps in by_module.items():
        lines.append(f"### Module: {module}")

        # Generate AI prompt
        edge_cases = [g.description for g in module_gaps if g.type == "edge_case"]
        error_paths = [g.description for g in module_gaps if g.type == "error_path"]

        if edge_cases:
            lines.append(f"**Ask LLM:** Add edge case tests for: {', '.join(edge_cases)}")

        if error_paths:
            lines.append(f"**Ask LLM:** Add error path tests for: {', '.join(error_paths)}")

        lines.append("")

    return "\n".join(lines)
```

**Example Output:**
```markdown
## Testing Decision Summary

| Module | Tier | Action | Reason |
|--------|------|--------|--------|
| notification_queue.py | T1 | PASS | All tests passed |
| notification_queue.py | T2 | WARNING | Low risk (0.35), non-blocking |
| router.py | T1 | BLOCKED | Critical risk (0.82), refactor (850 lines) |
| scheduler.py | T1 | SKIPPED | Low risk (0.25), T1 not required |
| scheduler.py | T2 | SKIPPED | Low risk (0.25), T2 not required |

## Coverage Gaps (AI-Ready Orders)

### Module: notification_queue.py
**Ask LLM:** Add edge case tests for: empty input, future timestamp, corrupted JSON
**Ask LLM:** Add error path tests for: invalid JSON format, file permission denied

### Module: router.py
**Ask LLM:** Add edge case tests for: concurrent access, race condition
**Ask LLM:** Add error path tests for: network timeout, invalid response
```

#### Refinement 4: Safer No-Git Fallback

**Implementation Location:** `P:\.claude\skills\test\git_state_detector.py` (extend)

**Trigger Condition:**
```python
def detect_git_state(cwd: Path) -> GitState:
    """Only trigger no_git when git rev-parse FAILS (not when diffs are empty)."""
    try:
        # This MUST succeed for git mode
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=cwd,
            capture_output=True,
            timeout=5,
            check=True  # Raise exception if git fails
        )
        # If we get here, git is available - check for diffs
        # ... existing logic
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Git NOT available - use testing.yml fallback
        return GitState.NO_GIT
```

**Combine with testing.yml:**
```python
def get_test_targets_no_git_mode(cwd: Path) -> List[Path]:
    """
    When git_state = no_git, combine discovery.roots/exclude from testing.yml.
    """
    config = load_testing_yml(cwd)

    # Get roots from config or use defaults
    roots = config.get("discovery", {}).get("roots", ["tests", "src/tests"])
    exclude_patterns = config.get("discovery", {}).get("exclude", [])

    # Find all test files
    test_files = []
    for root in roots:
        for pattern in ["test_*.py", "*_test.py", "*_integration.py"]:
            test_files.extend(Path(cwd).glob(f"{root}/**/{pattern}"))

    # Apply exclusions
    excluded = []
    for test_file in test_files:
        if any(any(test_file.match(ep) for ep in exclude_patterns)):
            continue
        excluded.append(test_file)

    return excluded
```

**Mark git_state in output:**
```python
def format_git_state_warning(context: TestingContext) -> str:
    """Print warning when git_state = no_git."""
    if context.git_state == GitState.NO_GIT:
        return (
            f"**WARNING:** Git not available or not a git repository.\n"
            f"Using testing.yml configuration for test discovery.\n"
            f"Roots: {context.testing_roots}\n"
            f"Excludes: {context.testing_excludes}\n"
        )
    return ""
```

#### Refinement 5: Minimal LLM Hooks (Phase 1)

**Implementation Location:** `P:\.claude\skills\test\testing_yml_loader.py` (NEW)

**Define REPRESENTATIVE_FUNCS mapping in testing.yml:**
```yaml
# testing.yml - NEW SECTION
representative_functions:
  # Key: module_name (derived from file path)
  # Value: list of function names to test

  module_auth:
    - login()      # Entry point for auth flow
    - logout()     # Boundary of auth session
    - authenticate()  # Core business logic

  module_database:
    - connect()    # Connection setup
    - query()      # Core operation
    - disconnect() # Cleanup

  module_notification:
    - enqueue()    # Add to queue
    - dequeue()    # Remove from queue
    - process()    # Handle notification
```

**Replace hardcoded main_function lookup:**
```python
# OLD (hardcoded, inflexible):
def find_main_function(module_path: Path) -> Optional[str]:
    """Look for main() or run() function."""
    content = module_path.read_text()
    if "def main(" in content:
        return "main"
    elif "def run(" in content:
        return "run"
    return None

# NEW (configured in testing.yml):
def find_representative_functions(module_name: str, cwd: Path) -> List[str]:
    """
    Load representative functions from testing.yml.
    Returns: List of function names to generate tests for.
    """
    config = load_testing_yml(cwd)
    return config.get("representative_functions", {}).get(module_name, [])
```

**LLM can safely update testing.yml:**
```python
# Director-level task (NOT /t subtask):
# 1. LLM reads existing testing.yml
# 2. LLM analyzes module to identify key functions
# 3. LLM updates representative_functions section
# 4. /t uses updated config on next run
```

### 5.2 Phase Breakdown

#### Phase 1A: Mode Detection + TestingContext.git_state

**Goal:** Add explicit git state detection and store on TestingContext.

**Files to Create:**
1. `P:\.claude\skills\test\git_state_detector.py` (NEW)
   - `detect_git_state(cwd: Path) -> GitState`
   - `get_changed_files(cwd: Path, git_state: GitState) -> List[Path]`
   - `get_test_targets_no_git_mode(cwd: Path) -> List[Path]`

2. `P:\.claude\skills\test\testing_context.py` (NEW)
   - `TestingContext` dataclass
   - `GitState` enum
   - `ChangeKind` enum

**Files to Modify:**
1. `P:\.claude\skills\test\SKILL.md`
   - Add "Step 0: Git State Detection" to workflow
   - Add `TestingContext` to "Your Workflow" section
   - Add git_state to response format

**Success Criteria:**
- ✅ `detect_git_state()` correctly identifies all 5 modes (no_git, unstaged, staged, last_commit, full_scan)
- ✅ TestingContext.git_state is populated and surfaced in output
- ✅ No-git fallback uses testing.yml roots/exclude

#### Phase 1B: Adaptive Depth (Tier + Change Size)

**Goal:** Add change_size, change_kind to ModuleRisk and implement adaptive strictness.

**Files to Create:**
1. `P:\.claude\skills\test\risk_calculator.py` (NEW)
   - `ModuleRisk` dataclass with change_size, change_kind, risk_score
   - `calculate_risk_score()` - deterministic formula
   - `determine_strictness()` - adaptive T1/T2 enforcement
   - `run_adaptive_tests()` - execute tests with strictness

2. `P:\.claude\skills\test\change_analyzer.py` (NEW)
   - `calculate_change_size(path: Path, git_state: GitState) -> int`
   - `infer_change_kind(path: Path, git_state: GitState) -> ChangeKind`

**Files to Modify:**
1. `P:\.claude\skills\test\SKILL.md`
   - Add "Step 1.5: Calculate Risk Score" to workflow
   - Add risk_score to response format
   - Document adaptive strictness behavior

**Success Criteria:**
- ✅ Risk scores are deterministic (same input → same score)
- ✅ High risk (≥0.7) → T1+T2 hard fails
- ✅ Low risk (<0.4) → T2 warnings or skipped

#### Phase 1C: Director Ergonomics + AI-Ready Output

**Goal:** Add decision summary tables and AI-ready gap orders.

**Files to Create:**
1. `P:\.claude\skills\test\director_formatter.py` (NEW)
   - `format_decision_summary()` - decision table
   - `format_coverage_gaps_ai()` - AI-ready orders

2. `P:\.claude\skills\test\testing_yml_loader.py` (NEW)
   - `load_testing_yml()` - load config
   - `get_representative_functions()` - replace hardcoded main_function

**Files to Modify:**
1. `P:\.claude\skills\test\SKILL.md`
   - Add "Step 7: Generate Director Summary" to workflow
   - Add decision table to response format
   - Add AI-ready orders section

**Example testing.yml to Create:**
2. `P:\.claude\skills\test\testing.yml.example` (NEW)
   - Document discovery.roots/exclude schema
   - Document representative_functions schema
   - Document tier thresholds

**Success Criteria:**
- ✅ Decision summary table shows module/tier/action/reason
- ✅ Coverage gaps formatted as "Ask LLM: Add tests for..."
- ✅ representative_functions loaded from testing.yml

---

## 6. Implementation Plan

### 6.1 Phase 1A: Mode Detection + TestingContext.git_state

**Step 1: Create data structures**
```bash
# Create testing_context.py with GitState enum and TestingContext dataclass
touch P:/.claude/skills/test/testing_context.py
```

**Step 2: Implement git state detector**
```bash
# Create git_state_detector.py with detection logic
touch P:/.claude/skills/test/git_state_detector.py
```

**Step 3: Update SKILL.md workflow**
```markdown
## Your Workflow (UPDATED)

1. **DETECT GIT STATE** — Determine mode: no_git | unstaged | staged | last_commit | full_scan
2. **LOAD TESTING CONFIG** — Read testing.yml for roots/exclude (if no_git)
3. **DISCOVER TESTS** — Find all test files related to target
4. **CLASSIFY TESTS** — Categorize as Unit, Integration, Edge Case, Error Path, Regression
5. **CALCULATE RISK SCORE** — Derive from tier + size + kind
6. **RUN ADAPTIVE TESTS** — Execute with adaptive strictness
7. **GENERATE DIRECTOR SUMMARY** — Decision table + AI-ready orders
```

**Step 4: Add tests**
```python
# P:\.claude\skills\test\tests\test_git_state_detector.py (NEW)
def test_detect_no_git():
    """Return NO_GIT when git rev-parse fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        assert detect_git_state(Path(tmpdir)) == GitState.NO_GIT

def test_detect_unstaged():
    """Return UNSTAGED when git diff shows changes."""
    # ... implementation

def test_no_git_fallback():
    """Use testing.yml roots when git unavailable."""
    # ... implementation
```

**Estimated Time:** 4-6 hours

### 6.2 Phase 1B: Adaptive Depth (Tier + Change Size)

**Step 1: Create risk calculator**
```bash
# Create risk_calculator.py with deterministic formula
touch P:/.claude/skills/test/risk_calculator.py
```

**Step 2: Create change analyzer**
```bash
# Create change_analyzer.py to calculate change_size and infer change_kind
touch P:/.claude/skills/test/change_analyzer.py
```

**Step 3: Update SKILL.md**
```markdown
### Step 1.5: Calculate Risk Score (NEW)

For each module to test:
1. Calculate change_size (lines added + deleted)
2. Infer change_kind (bugfix | feature | refactor | config | docs)
3. Compute risk_score = tier_score × size_multiplier × kind_multiplier
4. Determine T1/T2 strictness based on risk_score

**Adaptive Strictness Rules:**
- risk_score ≥ 0.7 → T1+T2 hard_fail (blocking)
- 0.4 ≤ risk_score < 0.7 → T1 hard_fail, T2 soft_fail (warning)
- risk_score < 0.4 → T1 soft_fail, T2 skip (don't run)
```

**Step 4: Add tests**
```python
# P:\.claude\skills\test\tests\test_risk_calculator.py (NEW)
def test_risk_score_deterministic():
    """Same inputs produce same risk_score."""
    risk1 = calculate_risk_score("auth", "T1", 100, ChangeKind.BUGFIX)
    risk2 = calculate_risk_score("auth", "T1", 100, ChangeKind.BUGFIX)
    assert risk1 == risk2

def test_high_risk_hard_fail():
    """Risk ≥ 0.7 → T1+T2 hard_fail."""
    strictness = determine_strictness(0.75)
    assert strictness == ("hard_fail", "hard_fail")

def test_low_risk_skip_t2():
    """Risk < 0.4 → T2 skip."""
    strictness = determine_strictness(0.3)
    assert strictness == ("soft_fail", "skip")
```

**Estimated Time:** 6-8 hours

### 6.3 Phase 1C: Director Ergonomics + AI-Ready Output

**Step 1: Create director formatter**
```bash
# Create director_formatter.py with decision table and AI orders
touch P:/.claude/skills/test/director_formatter.py
```

**Step 2: Create testing.yml loader**
```bash
# Create testing_yml_loader.py to load config
touch P:/.claude/skills/test/testing_yml_loader.py
```

**Step 3: Create testing.yml.example**
```bash
# Document testing.yml schema with examples
touch P:/.claude/skills/test/testing.yml.example
```

**Step 4: Update SKILL.md**
```markdown
## Response Format (UPDATED)

### Director Summary Table

| Module | Tier | Action | Reason |
|--------|------|--------|--------|
| notification_queue.py | T1 | PASS | All tests passed |
| router.py | T1 | BLOCKED | Critical risk (0.82), refactor (850 lines) |

### Coverage Gaps (AI-Ready Orders)

**Ask LLM:** Add edge case tests for: empty input, future timestamp
**Ask LLM:** Add error path tests for: invalid JSON format, file permission denied
```

**Step 5: Add tests**
```python
# P:\.claude\skills\test\tests\test_director_formatter.py (NEW)
def test_decision_summary_format():
    """Generate decision table with correct columns."""
    # ... implementation

def test_ai_ready_orders():
    """Format gaps as 'Ask LLM: Add tests for...'"""
    # ... implementation
```

**Estimated Time:** 4-6 hours

**Total Estimated Time:** 14-20 hours across all phases

---

## 7. Risks, Success Criteria, Dependencies

### 7.1 Top Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Git state detection unreliable** | HIGH (wrong test scope) | MEDIUM | Add extensive tests, use timeouts, validate git commands |
| **Risk score formula produces unexpected results** | MEDIUM (wrong strictness) | LOW | Deterministic formula, tested with known edge cases |
| **testing.yml parsing errors** | MEDIUM (fallback to defaults) | LOW | Graceful degradation, validate schema before use |
| **Director summary table misinterpreted** | LOW (UX issue) | MEDIUM | Clear column labels, examples in documentation |
| **Performance degradation** | LOW (slower /t) | LOW | Reuse existing health check, parallel subagents |
| **Multi-terminal git state confusion** | HIGH (wrong files tested) | MEDIUM | Use absolute paths, validate git_dir, test worktrees |

### 7.2 Success Criteria

**Phase 1A Success:**
- ✅ Git state detected correctly in 100% of test cases (5 modes)
- ✅ No-git fallback uses testing.yml when git unavailable
- ✅ TestingContext.git_state surfaced in output

**Phase 1B Success:**
- ✅ Risk scores are deterministic (same input → same output)
- ✅ Adaptive strictness: high risk → T1+T2 hard fail, low risk → T2 skip
- ✅ Change size calculated accurately (lines added + deleted)

**Phase 1C Success:**
- ✅ Decision summary table shows module/tier/action/reason
- ✅ Coverage gaps formatted as "Ask LLM: Add tests for..."
- ✅ representative_functions loaded from testing.yml

**Overall Success:**
- ✅ `/t` command works as independent skill (shares infrastructure with `/test`)
- ✅ All existing `/test` functionality preserved (backward compatible)
- ✅ New features work without git (multi-terminal safe)

### 7.3 Dependencies

**Internal Dependencies:**
- `P:\.claude\skills\test_health_check.py` - Health check utility (reuse)
- `P:\.claude\skills\test\SKILL.md` - Existing test skill documentation (extend)
- `.test_gaps.json` schema - Gap file format (extend, don't break)

**External Dependencies:**
- `git` CLI - Required for git state detection (optional: fallback to testing.yml)
- `pytest` - Required for test execution (existing dependency)
- `pyyaml` - Required for testing.yml parsing (NEW dependency)

**System Dependencies:**
- Python 3.14+ - Existing environment
- Bash/terminal - For running git/pytest commands

**Skill Dependencies:**
- `/tdd` - Consumes `.test_gaps.json` (existing integration)
- `/verify` - Shares pytest results (existing integration)
- `/qa` - Consumes coverage reports (existing integration)

### 7.4 Rollback Strategy

**If Phase 1A Fails:**
- Revert `git_state_detector.py` and `testing_context.py`
- Keep existing `/test` workflow (no mode detection)
- Document limitation: "Git state detection not available, use explicit paths"

**If Phase 1B Fails:**
- Revert `risk_calculator.py` and `change_analyzer.py`
- Keep fixed depth (T1+T2 always hard fail)
- Document limitation: "Adaptive depth not available, all tests run at full strictness"

**If Phase 1C Fails:**
- Revert `director_formatter.py` and `testing_yml_loader.py`
- Keep existing output format (developer-focused)
- Document limitation: "Director summary not available, use existing report format"

**Complete Rollback:**
- Delete new files: `git_state_detector.py`, `testing_context.py`, `risk_calculator.py`, `change_analyzer.py`, `director_formatter.py`, `testing_yml_loader.py`
- Revert `SKILL.md` to previous version
- `/test` continues working as before (backward compatible)

### 7.5 Monitoring and Observability

**Metrics to Track:**
1. **Git state distribution** - How often is each mode triggered?
2. **Risk score distribution** - Are scores clustering in expected ranges?
3. **Adaptive strictness effectiveness** - Does T2 skip actually save time?
4. **No-git fallback frequency** - How often is git unavailable?
5. **Director summary usage** - Are stakeholders using the decision table?

**Logging Strategy:**
```python
# Append to .test_gaps.json
{
  "git_state": "unstaged",
  "risk_score": 0.75,
  "adaptive_strictness": {"T1": "hard_fail", "T2": "hard_fail"},
  "testing_yml_used": false,
  "timestamp": "2025-02-25T14:30:00Z"
}
```

---

## 8. Appendices

### Appendix A: File Structure

```
P:\.claude\skills\test\
├── SKILL.md (MODIFY - add new workflow steps)
├── CHANGELOG.md (MODIFY - document changes)
├── testing.yml.example (NEW - schema documentation)
├── test_health_check.py (EXISTING - reuse)
├── testing_context.py (NEW - data structures)
├── git_state_detector.py (NEW - git state detection)
├── risk_calculator.py (NEW - risk scoring algorithm)
├── change_analyzer.py (NEW - change size/kind analysis)
├── director_formatter.py (NEW - decision table formatting)
├── testing_yml_loader.py (NEW - config loading)
└── tests\
    ├── test_git_state_detector.py (NEW)
    ├── test_risk_calculator.py (NEW)
    ├── test_director_formatter.py (NEW)
    └── test_change_analyzer.py (NEW)
```

### Appendix B: API Contract

**GitStateDetector:**
```python
def detect_git_state(cwd: Path) -> GitState:
    """
    Detect git repository state.
    Returns: GitState enum (NO_GIT | UNSTAGED | STAGED | LAST_COMMIT | FULL_SCAN)
    Raises: subprocess.TimeoutExpired (5 second timeout)
    """

def get_changed_files(cwd: Path, git_state: GitState) -> List[Path]:
    """
    Get list of changed files based on git_state.
    Returns: List of absolute file paths
    """
```

**RiskCalculator:**
```python
def calculate_risk_score(module: str, tier: str, change_size: int, change_kind: ChangeKind) -> float:
    """
    Derive deterministic risk score (0-1) from tier + size + kind.
    Returns: float in range [0, 1]
    """

def determine_strictness(risk_score: float) -> tuple[str, str]:
    """
    Adjust strictness based on risk_score.
    Returns: (t1_strictness, t2_strictness) where each is 'hard_fail' | 'soft_fail' | 'skip'
    """
```

**DirectorFormatter:**
```python
def format_decision_summary(module_risks: List[ModuleRisk], test_results: List[TestResult]) -> str:
    """
    Generate decision summary table (Markdown format).
    Returns: Markdown table string
    """

def format_coverage_gaps_ai(gaps: List[TestGap]) -> str:
    """
    Convert gaps to AI-ready orders (Markdown format).
    Returns: Markdown formatted string with "Ask LLM:" prompts
    """
```

### Appendix C: Testing Strategy

**Unit Tests:**
- `test_git_state_detector.py` - Test all 5 git states, no-git fallback
- `test_risk_calculator.py` - Test deterministic formula, strictness boundaries
- `test_director_formatter.py` - Test table format, AI order generation
- `test_change_analyzer.py` - Test change_size calculation, kind inference

**Integration Tests:**
- `test_t_command_end_to_end.py` - Test full /t workflow with real git repo
- `test_no_git_scenario.py` - Test /t in non-git directory with testing.yml
- `test_adaptive_depth.py` - Test adaptive strictness with various risk scores

**Manual Testing:**
- Test in clean git repo (no changes)
- Test in dirty git repo (unstaged changes)
- Test in staged git repo (staged changes)
- Test in non-git directory (no_git fallback)
- Test in worktree (multi-terminal scenario)

### Appendix D: Glossary

| Term | Definition |
|------|------------|
| **GitState** | Enum representing repository state: NO_GIT, UNSTAGED, STAGED, LAST_COMMIT, FULL_SCAN |
| **TestingContext** | Dataclass holding git state, target path, changed files, configuration |
| **ModuleRisk** | Dataclass holding risk assessment for a module (tier, change_size, change_kind, risk_score) |
| **Adaptive Depth** | Test execution that adapts strictness based on risk_score |
| **T1** | Tier 1 (functional) tests - core functionality |
| **T2** | Tier 2 (coverage) tests - edge cases and error paths |
| **Risk Score** | Deterministic value [0-1] derived from tier + size + kind |
| **Strictness** | Enforcement level: hard_fail (blocker), soft_fail (warning), skip (don't run) |
| **Director Summary** | Decision table optimized for non-technical stakeholders |
| **AI-Ready Orders** | Coverage gaps formatted as LLM prompts |
| **testing.yml** | Project-specific configuration for test discovery and representative functions |

---

## 9. Approval and Sign-Off

**Reviewers:**
- [ ] Architectural Review - Approve design decisions
- [ ] Security Review - Approve git state detection security
- [ ] UX Review - Approve director summary format
- [ ] Testing Review - Approve test coverage strategy

**Implementation Approval:**
- [ ] Phase 1A approved to proceed
- [ ] Phase 1B approved to proceed
- [ ] Phase 1C approved to proceed

**Sign-off:**
- Plan created: 2025-02-25
- Plan approved: TBD
- Implementation start: TBD
- Implementation complete: TBD

---

**END OF PLAN**
