# TDD and Test-Hook System Design for Claude Code Hooks

**Author**: System Design Document
**Status**: Draft - Ready for Review
**Last Updated**: 2025-02-12

---

## Executive Summary

This document defines a comprehensive Test-Driven Development (TDD) and test-enforcement system for the Claude Code hooks architecture. The design prioritizes **automation**, **AI-assisted workflows**, and **ergonomics** for a solo technical developer running multi-terminal, long-running sessions.

**Key Decisions**:
- Convention-based discovery (no static CRITICALHOOKS dict maintenance)
- Tiered enforcement (pre-commit → pre-push → CI)
- Auto-scaffolding for critical hooks
- Integration with existing router pattern and `hook_base.py`

---

## 1. Scope: Safety-Critical vs Nice-to-Have

### 1.1 Safety-Critical Categories

Hooks that **MUST NEVER silently regress** because they enforce:

| Category | Description | Examples | Regression Impact |
|----------|-------------|----------|-------------------|
| **Anti-Confabulation** | Detects false claims, hallucinated quotes, unverified assertions | `assumption_audit_v2.py`, `StopHook_cross_validator.py`, `verifycodequotes` | Silent misinformation propagation |
| **Gate Enforcement** | Blocks destructive or unsafe actions | `PreToolUse_directory_policy.py`, `PreToolUse_hook_edit_gate.py`, `credential_filter` | Data loss, security breaches |
| **Constitutional** | Enforces behavioral principles from CLAUDE.md | `constitutional_enforcer.py`, `PreToolUse_tdd_gate.py` | Behavioral drift from principles |
| **Evidence Verification** | Requires empirical evidence for claims | `empirical_claims_gate.py`, `StopHook_truth_evidence_gate.py` | Procedural compliance without problem-solving |
| **Router Wiring** | Ensures hooks are actually registered | Router registration checks | Dead hooks that never execute |

### 1.2 Nice-to-Have Categories

Hooks where regressions are **acceptable** with manual monitoring:

| Category | Description | Examples |
|----------|-------------|----------|
| **Diagnostic** | Logging, metrics, observability | `cc_diagnostic_logger.py`, `telemetry hooks` |
| **Advisory** | Warnings, suggestions, non-blocking | `PreToolUse_long_term_thinking_reminder.py`, `suggestion hints` |
| **Optimization** | Performance improvements, caching | `hook_cache.py`, connection pooling |
| **Experimental** | Beta features, research hooks | `UEEA_ENABLED` experimental features |

---

## 2. Behavioral Contracts for Safety-Critical Hooks

Each safety-critical hook MUST define an explicit behavioral contract in its docstring.

### 2.1 Contract Template

```python
"""
HOOK CONTRACT: [Hook Name]

CRITICALITY: safety-critical
ENFORCEMENT_LAYER: pre-commit, pre-push, CI

INPUT_SPEC:
{
    "field1": type,  # Description
    "field2": type | None,  # Optional field
}

OUTPUT_SPEC (PreToolUse):
{
    "continue": bool,  # True = allow, False = block
    "reason": str,     # Human-readable explanation
}

OUTPUT_SPEC (Stop):
{
    "decision": "block" | "allow",
    "reason": str,
}

INVARIANTS:
1. [First invariant - what must ALWAYS be true]
2. [Second invariant]
3. [Third invariant]

BLOCK_CONDITIONS:  # When does this hook BLOCK?
- [Specific condition 1]
- [Specific condition 2]

ALLOW_CONDITIONS:  # When does this hook ALLOW?
- [Specific condition 1]
- [Specific condition 2]

EDGE_CASES:
- [Edge case 1]: How hook handles it
- [Edge case 2]: How hook handles it
"""
```

### 2.2 Example Contracts

#### Contract 1: Code Quote Verification (assumption_audit_v2.py)

```python
"""
HOOK CONTRACT: assumption_audit_v2.verifycodequotes

CRITICALITY: safety-critical
ENFORCEMENT_LAYER: pre-commit, pre-push, CI

INPUT_SPEC:
{
    "response": str,           # LLM response text
    "transcript": list,        # Conversation history
    "session_id": str,         # Claude Code session identifier
}

OUTPUT_SPEC (Stop):
{
    "decision": "block" | "allow",
    "reason": str,             # Explanation if blocked
    "metadata": {
        "violations": list,    # List of quote violations found
        "quotes_checked": int,
    }
}

INVARIANTS:
1. Every code quote (file_path:line_number) MUST be verified by Read tool
2. Quotes from non-existent files MUST block
3. Quotes from wrong content MUST block (content mismatch)
4. Self-referential explanations ("in my previous response") MUST be exempt

BLOCK_CONDITIONS:
- Quote found without corresponding Read tool in recent tool history
- Read tool found but content doesn't match quoted text
- Quote references file that doesn't exist

ALLOW_CONDITIONS:
- No code quotes present in response
- All code quotes have matching Read evidence
- Meta-conversation detected (self-referential discussion)

EDGE_CASES:
- Multi-line code blocks: Check first line reference
- Fuzzy content matching: Allow 80% similarity threshold
- Deleted files: Block if quote references deleted file

TEST_REQUIRED_MARKERS:
- @pytest.mark.contract
- @pytest.mark.anti_confabulation
"""
```

#### Contract 2: Skill Question Detection (investigate_before_explain.py)

```python
"""
HOOK CONTRACT: investigate_before_explain

CRITICALITY: safety-critical
ENFORCEMENT_LAYER: pre-commit, pre-push, CI

INPUT_SPEC:
{
    "prompt": str,              # User's question
    "response": str,            # LLM's response
    "tools_used": list,         # Tools in response
}

OUTPUT_SPEC (PreToolUse):
{
    "continue": bool,
    "reason": str,
    "suggestion": str | None,   # Suggested investigation command
}

INVARIANTS:
1. ANY question about code structure requires Read/Grep FIRST
2. ANY question about "why X fails" requires investigation BEFORE explanation
3. Diagnostic questions MUST have evidence gathered before answer

BLOCK_CONDITIONS:
- User asks "how does X work" → LLM explains WITHOUT reading X
- User asks "why does Y fail" → LLM speculates WITHOUT running/investigating
- LLM makes claims about behavior WITHOUT tool evidence

ALLOW_CONDITIONS:
- User asks for opinion/design (non-factual question)
- LLM explicitly states "I need to investigate" before explaining
- Meta-discussion about LLM's own behavior

EDGE_CASES:
- "Quick question" shortcut: Still requires investigation
- Follow-up questions: Can reuse previous investigation evidence
- Design questions: Exempt from investigation requirement (creative work)

TEST_REQUIRED_MARKERS:
- @pytest.mark.contract
- @pytest.mark.investigation_gate
"""
```

#### Contract 3: Stop Command Guardrail (PreToolUse_directory_policy.py)

```python
"""
HOOK CONTRACT: deny_root_write

CRITICALITY: safety-critical
ENFORCEMENT_LAYER: pre-commit

INPUT_SPEC:
{
    "tool": str,                # Tool name: "Write" | "Edit" | "MultiEdit"
    "args": {
        "file_path": str,       # Target file path
        # ... other tool args
    }
}

OUTPUT_SPEC (PreToolUse):
{
    "continue": bool,
    "reason": str,
}

INVARIANTS:
1. Writes to /root/, /etc/, /usr/bin/ ALWAYS block
2. Writes to C:/Windows/, C:/Program Files/ ALWAYS block
3. Wildcard writes (Write(../**)) ALWAYS block
4. Override only with explicit CONSTITUTIONAL_HOOKS_BYPASS=1

BLOCK_CONDITIONS:
- file_path starts with protected prefix
- file_path contains wildcard pattern to protected directory

ALLOW_CONDITIONS:
- file_path outside protected directories
- CONSTITUTIONAL_HOOKS_BYPASS=1 set

EDGE_CASES:
- Symlinks to protected dirs: Block (resolve symlinks)
- Worktree-specific paths: Allow (not absolute system paths)
- Case-insensitive paths: Block both /Root/ and /root/

TEST_REQUIRED_MARKERS:
- @pytest.mark.contract
- @pytest.mark.safety
- @pytest.mark.gate
"""
```

#### Contract 4: Router Registration Sanity (hook_registration_test.py)

```python
"""
HOOK CONTRACT: router_registration_check

CRITICALITY: safety-critical
ENFORCEMENT_LAYER: pre-commit

INPUT_SPEC: N/A (static analysis)

OUTPUT_SPEC: Test exit code
- Exit 0: All hooks registered
- Exit 1: Dead hooks found

INVARIANTS:
1. Every *.py hook file in hooks/ MUST be registered somewhere
2. Router hooks MUST have process_prompt() exported
3. Stop hooks MUST have run() exported for in-process or be in settings.json

BLOCK_CONDITIONS:
- Hook file exists but not in any router
- Hook in router but file doesn't exist
- Hook exports wrong function signature

ALLOW_CONDITIONS:
- Test files (test_*.py) exempt from registration
- Archived hooks (_archive_/*.py) exempt
- __init__.py files exempt

EDGE_CASES:
- Conditional hooks (ENABLED=False): Still must be registered
- Router consolidation: Multiple hooks can share one router entry

TEST_REQUIRED_MARKERS:
- @pytest.mark.contract
- @pytest.mark.infrastructure
"""
```

#### Contract 5: Cross-Validator (StopHook_cross_validator.py)

```python
"""
HOOK CONTRACT: cross_validator

CRITICALITY: safety-critical
ENFORCEMENT_LAYER: pre-commit, pre-push, CI

INPUT_SPEC:
{
    "response": str,            # LLM response to check
    "tool_context": {
        "recent_tools": list,   # Recent tool executions
    }
}

OUTPUT_SPEC (Stop):
{
    "decision": "block" | "allow",
    "reason": str,
    "metadata": {
        "verdict": str,         # "BLOCK_UNVERIFIED_FIX" | "WARN_UNVERIFIED_FIX" | "OK"
    }
}

INVARIANTS:
1. "Fixed", "resolved", "done" claims REQUIRE verification
2. Verification = test execution, hook output, or before/after comparison
3. File reads (Read tool) alone DO NOT count as verification
4. Meta-conversation exempt from verification

BLOCK_CONDITIONS:
- Response contains FIXED_CLAIM_PATTERNS
- No VERIFICATION_PATTERNS found
- No recent test execution (Bash with pytest/test)
- Whitelist patterns don't match

ALLOW_CONDITIONS:
- No fixed claim patterns
- Verification evidence present
- Whitelisted (past tense narrative, speculative)
- Meta-conversation detected

EDGE_CASES:
- "This commit fixed" (narrative): Whitelist, allow
- "Should fix" (speculative): Whitelist, allow
- "Tested in previous turn": Check recent_tools

TEST_REQUIRED_MARKERS:
- @pytest.mark.contract
- @pytest.mark.evidence_verification
"""
```

---

## 3. TDD Workflow Shape

### 3.1 AI-Assisted TDD Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT CYCLE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐       ┌──────────────────┐              │
│  │ 1. USER REQUEST  │──────▶│ 2. TDD ASSISTANT │              │
│  │    "Add feature  │       │    Analyzes      │              │
│  │     hook X"      │       │    Requirements  │              │
│  └──────────────────┘       └────────┬─────────┘              │
│                                      │                          │
│                                      ▼                          │
│                          ┌──────────────────────┐              │
│                          │ 3. AUTO-SCAFFOLD     │              │
│                          │    Creates:          │              │
│                          │    - Hook stub       │              │
│                          │    - Test file       │              │
│                          │    - Contract        │              │
│                          └──────────┬───────────┘              │
│                                     │                          │
│                                     ▼                          │
│                          ┌──────────────────────┐              │
│                          │ 4. RED PHASE        │              │
│                          │    Tests written     │              │
│                          │    (fail initially)   │              │
│                          └──────────┬───────────┘              │
│                                     │                          │
│                                     ▼                          │
│                          ┌──────────────────────┐              │
│                          │ 5. GREEN PHASE      │              │
│                          │    AI implements     │              │
│                          │    hook to pass      │              │
│                          └──────────┬───────────┘              │
│                                     │                          │
│                                     ▼                          │
│                          ┌──────────────────────┐              │
│                          │ 6. REFACTOR PHASE   │              │
│                          │    Clean up         │              │
│                          │    while tests pass │              │
│                          └──────────┬───────────┘              │
│                                     │                          │
│                                     ▼                          │
│                          ┌──────────────────────┐              │
│                          │ 7. PRE-COMMIT       │              │
│                          │    Runs tests        │              │
│                          │    Blocks if fail    │              │
│                          └──────────────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 When Tests Are Written

| Scenario | Test Timing | Who Writes | Rationale |
|----------|-------------|------------|-----------|
| **New critical hook** | BEFORE implementation | AI scaffolds, developer reviews | TDD pure: RED → GREEN → REFACTOR |
| **New nice-to-have hook** | AFTER implementation | Developer writes | Pragmatic: document existing behavior |
| **Bug fix in critical hook** | BEFORE fix | AI scaffolds regression test | Prevents re-introduction |
| **Refactoring** | EXISTING tests | No new tests | Existing tests verify behavior preserved |
| **Regex/pattern changes** | BEFORE change | AI scaffolds regression tests | Patterns are fragile; need explicit tests |

### 3.3 AI Scaffolding vs Manual Writing

| Task | AI Scaffolds | Developer Writes |
|------|--------------|------------------|
| Hook stub with contract | ✅ | |
| Unit test skeleton | ✅ | |
| Integration test skeleton | ✅ | |
| Edge case tests | ✅ (pattern-based) | |
| Complex scenario tests | | ✅ (domain knowledge) |
| Regression tests for bugs | ✅ | |
| Performance tests | | ✅ (requires benchmarking) |
| Fuzzing tests | | ✅ (requires tooling) |

---

## 4. Enforcement Layers

### 4.1 Pre-Commit (Fast, Local)

**Location**: `.git/hooks/pre-commit` or `pre-commit` config

**What runs**:
```yaml
# Pre-commit test tiers
critical_fast:
  - test_hook_registration.py      # ~2s  # Dead hook detection
  - test_critical_contracts.py      # ~5s  # Contract validation
  - test_pattern_sanity.py          # ~3s  # Regex smoke tests

selected_by_diff:
  # Only run tests for changed hooks
  - if PreToolUse_directory_policy.py changed:
    - test_deny_root_write.py      # ~2s
  - if assumption_audit_v2.py changed:
    - test_assumption_audit.py     # ~5s
```

**Blocks**:
- ❌ Critical hook modified without test
- ❌ Test fails for critical hook
- ❌ Hook registration broken
- ⚠️ Nice-to-have hook without test (warning only, bypass with `git commit --no-verify`)

**Time budget**: ≤ 10 seconds for typical single-hook change

### 4.2 Pre-Push (Slower, More Complete)

**Location**: `.git/hooks/pre-push`

**What runs**:
```yaml
full_critical_suite:
  - All critical hook tests
  - Integration tests with tool sequences
  - Router wiring tests

nice_to_have_smoke:
  - Test imports for nice-to-have hooks
  - Basic functionality checks
```

**Blocks**:
- ❌ Any critical hook test fails
- ❌ Integration test fails
- ⚠️ Nice-to-have test fails (warn, can bypass)

**Time budget**: ≤ 60 seconds

### 4.3 CI (Full Suite, Can Be Slow)

**What runs**:
```yaml
everything:
  - All pre-commit tests
  - All pre-push tests
  - Edge case coverage tests
  - Performance regression tests
  - Fuzzing tests (if configured)
  - Cross-platform tests (Windows/Linux/macOS)
```

**Blocks**:
- ❌ Any test failure fails CI
- ❌ Coverage below threshold (80% for critical hooks)

**Time budget**: ≤ 5 minutes

---

## 5. Hook/Test Discovery and Mapping

### 5.1 Naming Conventions

```python
# HOOK NAMING
{Event}_{Purpose}.py              # Main hooks
PreToolUse_directory_policy.py
StopHook_cross_validator.py
PostToolUse_edit_verifier.py
UserPromptSubmit_router.py

{Event}_{Purpose}_router.py       # Router consolidates multiple hooks
PreToolUse_write_router.py

# TEST NAMING
test_{HookName}.py                # Unit + integration tests for hook
test_PreToolUse_directory_policy.py
test_StopHook_cross_validator.py

test_{category}_contract.py       # Contract validation tests
test_safety_contracts.py
test_anti_confabulation_contracts.py

test_{feature}_integration.py     # End-to-end tests
test_investigation_integration.py
```

### 5.2 Criticality Declaration

**Method A: Docstring tag (preferred)**

```python
"""
HOOK CONTRACT: deny_root_write

CRITICALITY: safety-critical
TEST_FILE: test_PreToolUse_directory_policy.py
...
"""
```

**Method B: Decorator (optional)**

```python
from __lib.hook_base import critical_hook

@critical_hook(
    test_file="test_PreToolUse_directory_policy.py",
    contract_version=1,
)
def main():
    ...
```

**Method C: Directory convention (fallback)**

```
.claude/hooks/
├── critical/          # Safety-critical hooks (symlinks or actual files)
│   ├── PreToolUse_directory_policy.py -> ../PreToolUse_directory_policy.py
│   ├── StopHook_cross_validator.py -> ../StopHook_cross_validator.py
│   └── ...
├── advisory/          # Nice-to-have hooks
└── experimental/
```

### 5.3 Auto-Discovery Logic

```python
# In test enforcement hook
def discover_tests_for_changed_hooks(changed_files: list[Path]) -> dict[str, list[Path]]:
    """
    Map changed hook files to their required test files.

    Returns:
        {
            "PreToolUse_directory_policy.py": ["test_PreToolUse_directory_policy.py"],
            "StopHook_cross_validator.py": ["test_StopHook_cross_validator.py", "test_cross_validation_integration.py"],
        }
    """
    hook_tests = {}
    hooks_dir = Path(".claude/hooks")
    tests_dir = hooks_dir / "tests"

    for changed_file in changed_files:
        # Skip non-hook files
        if not changed_file.name.startswith(("PreToolUse_", "StopHook", "PostToolUse", "UserPromptSubmit")):
            continue

        # Skip test files, docs, config
        if changed_file.name.startswith("test_") or changed_file.suffix in [".md", ".json"]:
            continue

        # Extract hook base name
        hook_name = changed_file.stem

        # Method 1: Test file with same name
        test_file = tests_dir / f"test_{hook_name}.py"
        if test_file.exists():
            hook_tests[str(changed_file)] = [test_file]
            continue

        # Method 2: Check docstring for TEST_FILE declaration
        test_file = extract_test_file_from_docstring(changed_file)
        if test_file and (tests_dir / test_file).exists():
            hook_tests[str(changed_file)] = [tests_dir / test_file]
            continue

        # Method 3: Check critical/ directory for symlink
        critical_link = hooks_dir / "critical" / changed_file.name
        if critical_link.exists():
            # It's critical, find its test
            test_file = tests_dir / f"test_{hook_name}.py"
            if test_file.exists():
                hook_tests[str(changed_file)] = [test_file]

    return hook_tests
```

### 5.4 Decision Tree for Test Selection

```
┌─────────────────────────────────────────────────────────────┐
│  What changed?                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ONLY test files changed                                    │
│  ├── Run: The changed tests                                │
│  └── Skip: Hook-specific tests (no hook changes)           │
│                                                             │
│  ONLY hook files changed (no tests)                         │
│  ├── If CRITICAL hook:                                     │
│  │   ├── BLOCK: No test exists                             │
│  │   ├── RUN: Existing test (if exists)                    │
│  │   └── SUGGEST: Create test via TDD assistant            │
│  └── If ADVISORY hook:                                     │
│      ├── WARN: No test exists                              │
│      └── RUN: Existing test (if exists)                    │
│                                                             │
│  BOTH hook AND test files changed                           │
│  ├── RUN: Changed tests                                    │
│  ├── RUN: Other tests for changed hooks                    │
│  └── RUN: Related integration tests                        │
│                                                             │
│  Router files changed                                       │
│  ├── RUN: test_hook_registration.py                        │
│  └── RUN: Tests for all hooks in router                    │
│                                                             │
│  settings.json changed                                      │
│  ├── RUN: test_hook_registration.py                        │
│  └── RUN: Tests for newly-enabled hooks                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Failure Modes and Detection

### 6.1 Failure Mode Catalog

| Failure Mode | Description | Detection Layer | Test Required |
|--------------|-------------|-----------------|---------------|
| **Dead Hook** | Hook file exists but never executes | Pre-commit | `test_hook_registration.py` |
| **Broken Regex** | Pattern matches incorrectly/fails silently | Pre-commit | `test_pattern_sanity.py` |
| **Missing Test** | Critical hook without corresponding test | Pre-commit | `test_critical_test_coverage.py` |
| **Shallow Test** | Test doesn't simulate real tool sequences | Pre-push | `test_integration_realistic.py` |
| **Mis-wired Router** | Hook in router but wrong function signature | Pre-commit | `test_router_signatures.py` |
| **State Leak** | Hook state persists across sessions | Pre-push | `test_session_isolation.py` |
| **Timeout** | Hook exceeds execution budget | Pre-push | `test_hook_performance.py` |
| **False Block** | Hook blocks legitimate actions | CI | `test_false_positive_regression.py` |
| **False Allow** | Hook allows violations | CI | `test_false_negative_regression.py` |
| **Meta-confabulation** | Hook doesn't exempt self-referential discussion | Pre-commit | `test_meta_conversation_gate.py` |

### 6.2 Test Specifications per Failure Mode

#### Test 1: Dead Hook Detection

```python
# test_hook_registration.py

def test_all_critical_hooks_registered():
    """Every critical hook file must be registered in a router."""
    hooks_dir = Path(".claude/hooks")
    critical_hooks = get_critical_hook_files(hooks_dir)

    registered_hooks = get_registered_hooks_from_routers()

    for hook_file in critical_hooks:
        hook_name = hook_file.stem
        assert hook_name in registered_hooks, (
            f"Dead hook detected: {hook_file} exists but is not registered. "
            f"Add to router or delete file."
        )

def test_all_registered_hooks_exist():
    """Every registered hook must have a corresponding file."""
    registered = get_registered_hooks_from_settings()
    hooks_dir = Path(".claude/hooks")

    for hook_name in registered:
        hook_file = hooks_dir / hook_name
        assert hook_file.exists(), (
            f"Ghost hook: {hook_name} registered but file doesn't exist. "
            f"Remove from settings.json or create file."
        )
```

#### Test 2: Regex Pattern Sanity

```python
# test_pattern_sanity.py

def test_code_quote_patterns_realistic():
    """Quote detection patterns must match realistic code references."""
    patterns = load_quote_patterns_from_hook("assumption_audit_v2.py")

    # Should match
    assert matches_pattern(patterns, "The fix is in src/main.py:42")
    assert matches_pattern(patterns, "See hooks/PreToolUse_gate.py:125")

    # Should NOT match (not a quote)
    assert not matches_pattern(patterns, "The main.py file is in src/")
    assert not matches_pattern(patterns, "Let's create main.py")

def test_fixed_claim_patterns_not_overbroad():
    """Fixed claim patterns must not match legitimate past-tense narrative."""
    patterns = load_claim_patterns("StopHook_cross_validator.py")

    # Should block
    assert matches_pattern(patterns, "The issue is fixed.")

    # Should NOT block (whitelisted)
    assert not matches_pattern(patterns, "This commit fixed the bug.")
    assert not matches_pattern(patterns, "As I fixed earlier, the issue was...")
```

#### Test 3: Integration Test Realism

```python
# test_integration_realistic.py

@pytest.mark.integration
def test_investigation_gate_with_real_tool_sequence():
    """Investigation gate must detect missing Read in realistic sequence."""
    # Simulate: User asks "how does the router work?"
    # BAD: LLM explains without reading router
    response_bad = "The router dispatches hooks based on priority."
    tools_bad = [{"name": "Edit", "file_path": "test.py"}]

    result = run_hook("investigate_before_explain", {
        "prompt": "How does Stop_router.py work?",
        "response": response_bad,
        "tools_used": tools_bad,
    })

    assert result["continue"] is False, "Should block explanation without investigation"

    # GOOD: LLM reads router first
    tools_good = [
        {"name": "Read", "file_path": ".claude/hooks/Stop_router.py"},
        {"name": "Edit", "file_path": "test.py"},
    ]

    result = run_hook("investigate_before_explain", {
        "prompt": "How does Stop_router.py work?",
        "response": "The router dispatches hooks based on priority.",
        "tools_used": tools_good,
    })

    assert result["continue"] is True, "Should allow after Read"
```

#### Test 4: Router Signature Validation

```python
# test_router_signatures.py

def test_router_hooks_export_process_prompt():
    """All hooks registered in UserPromptSubmit_router must export process_prompt()."""
    router_file = Path(".claude/hooks/UserPromptSubmit_router.py")
    router_code = router_file.read_text()

    # Extract hook imports from router
    hook_names = extract_hook_imports_from_router(router_code)

    for hook_name in hook_names:
        hook_file = Path(f".claude/hooks/{hook_name}.py")
        if not hook_file.exists():
            continue

        hook_code = hook_file.read_text()

        # Check for process_prompt export
        assert "def process_prompt(" in hook_code, (
            f"{hook_file} is registered in router but doesn't export process_prompt(). "
            f"Either add function or remove from router."
        )

def test_stop_hooks_export_run_or_main():
    """All Stop hooks must export run() for in-process or have main()."""
    stop_hooks = glob(".claude/hooks/StopHook*.py")

    for hook_file in stop_hooks:
        hook_code = hook_file.read_text()

        has_run = "def run(" in hook_code
        has_main = "def main(" in hook_code

        assert has_run or has_main, (
            f"{hook_file} must export run() (in-process) or main() (subprocess)"
        )
```

### 6.3 Ergonomics: Avoiding Bypass Fatigue

**Problem**: Overly strict enforcement leads to developers disabling checks.

**Solutions**:

1. **Adaptive Strictness**
   - First commit in session: Warn only, don't block
   - Repeated violations: Block
   - Explicit bypass flag: Allow with warning

2. **Smart Caching**
   - Cache test results for unchanged hooks
   - Only run tests for changed components
   - Parallel test execution

3. **Graceful Degradation**
   - If tests can't run (network down, deps missing): Warn, don't block
   - CI as backstop: Local checks can be looser

4. **Bypass Accountability**
   - Log all bypasses to `state/test_bypasses.jsonl`
   - Weekly review of bypass patterns
   - Auto-suggest test creation after bypass

```python
# Example: Adaptive strictness in pre-commit
def should_block_commit(violation_type: str, user_session_state: dict) -> bool:
    """Decide whether to block or warn based on context."""

    # First-time nice-to-have violation: Warn
    if violation_type == "missing_test_advisory":
        if user_session_state.get("advisory_warnings", 0) == 0:
            user_session_state["advisory_warnings"] = 1
            return False  # Warn only

    # Repeated violation: Block
    if user_session_state.get("advisory_warnings", 0) > 2:
        return True

    return False
```

### 6.4 Time/Latency Budgets

| Layer | Max Latency | Target Latency | Strategy |
|-------|-------------|----------------|----------|
| **Pre-commit** | 30s | 10s | Only test changed hooks, parallel execution |
| **Pre-push** | 120s | 60s | Full critical suite, parallel |
| **CI** | 600s | 300s | Full suite, coverage, cross-platform |

**Optimization Techniques**:

1. **Test Sharding**: Run independent tests in parallel
2. **Incremental Testing**: Only run tests for changed code
3. **Fixture Caching**: Reuse expensive test setup
4. **Binary Scanning**: Skip tests if binary hasn't changed

---

## 7. Concrete Implementation

### 7.1 TDD Assistant Hook

**File**: `P:/.claude/hooks/PreToolUse_tdd_assistant.py`

**Purpose**: When creating/modifying a critical hook, auto-suggest or scaffold tests.

```python
#!/usr/bin/env python3
"""
PreToolUse_tdd_assistant.py - TDD Assistant for Hook Development

TRIGGERS:
- User creates/modifies a file matching: *Hook*.py
- User creates a hook in critical/ directory

BEHAVIOR:
- If no test exists: Suggest test scaffold
- If hook is new: Generate full test stub
- For critical hooks: Block proceeding without test acknowledgment

OUTPUT:
- Injected suggestion for test creation
- Or scaffold command to run
"""

import json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
TESTS_DIR = HOOKS_DIR / "tests"

# Hook templates
CRITICAL_HOOK_TEST_TEMPLATE = '''#!/usr/bin/env python3
"""
Unit and integration tests for {hook_name}.

HOOK CONTRACT: {hook_name}
CRITICALITY: safety-critical
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

def run_hook(tool_name: str, tool_input: dict) -> dict:
    """Helper to run hook via subprocess."""
    hook_path = Path(__file__).parent.parent / "{hook_file}"
    input_data = {{"tool": tool_name, "args": tool_input}}

    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )

    if result.stdout:
        return json.loads(result.stdout)
    return {{}}

# === CONTRACT TESTS ===

def test_hook_exists():
    """Verify hook file exists."""
    hook_path = Path(__file__).parent.parent / "{hook_file}"
    assert hook_path.exists(), "{hook_file} must exist"

def test_hook_executes():
    """Hook should execute without error."""
    result = run_hook("{test_tool}", {{}})
    # Add assertions based on hook behavior

# === BEHAVIORAL TESTS ===

# Add tests for:
# - Block conditions
# - Allow conditions
# - Edge cases
# - Meta-conversation exemption

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

@hook_main
def main():
    """TDD assistant entry point."""
    data = json.loads(sys.stdin.read())

    tool = data.get("tool")
    args = data.get("args", {})
    file_path = args.get("file_path", "")

    # Only trigger on Write/Edit operations
    if tool not in ("Write", "Edit", "MultiEdit"):
        print(json.dumps({"continue": True}))
        return

    # Check if creating/modifying a hook file
    path = Path(file_path)
    if not any(pattern in path.name for pattern in ["Hook", "gate", "validator", "enforcer"]):
        print(json.dumps({"continue": True}))
        return

    # Check if test file exists
    test_file = TESTS_DIR / f"test_{path.stem}.py"

    if not test_file.exists():
        # Generate suggestion
        hook_name = path.stem
        suggestion = f"""
🧪 TDD ASSISTANT: No test found for {hook_name}

Recommended actions:

1. Auto-generate test scaffold:
   python -c "
from pathlib import Path
template = open('P:/.claude/hooks/tests/TDD_DESIGN.md').read()
# Extract and write test template
"

2. Create manually:
   - Create: P:/.claude/hooks/tests/test_{hook_name}.py
   - Include contract tests from TDD_DESIGN.md
   - Add behavioral tests for block/allow conditions

3. Minimum viable test:
   ```python
   def test_hook_exists():
       assert Path('{path.name}').exists()

   def test_hook_runs():
       # Test basic execution
       pass
   ```

For critical hooks, tests are REQUIRED before commit.
Reference: P:/.claude/hooks/tests/TDD_DESIGN.md
"""

        print(json.dumps({
            "continue": True,
            "reason": "TDD suggestion: Create test file",
            "suggestion": suggestion.strip(),
        }))
    else:
        print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
```

### 7.2 Test Enforcement Hook (Pre-Commit)

**File**: `P:/.claude/hooks\tests\test_enforcement.py`

**Purpose**: Pre-commit hook that enforces test presence and passing status.

```python
#!/usr/bin/env python3
"""
Test Enforcement Hook - Pre-commit validation

USAGE:
    .git/hooks/pre-commit: python P:/.claude/hooks/tests/test_enforcement.py

EXIT CODES:
    0: All checks passed
    1: Critical violation (blocks commit)
    2: Advisory violation (warns but allows)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

# Configuration
HOOKS_DIR = Path(".claude/hooks")
TESTS_DIR = HOOKS_DIR / "tests"
CRITICAL_HOOK_PATTERNS = [
    "PreToolUse_directory_policy",
    "StopHook_cross_validator",
    "assumption_audit_v2",
    "empirical_claims_gate",
    "PreToolUse_investigation_gate",
    # Add more critical patterns
]


def get_changed_hooks() -> List[Path]:
    """Get list of changed hook files in this commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )

    if not result.stdout:
        return []

    changed_files = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        path = Path(line)

        # Only consider hooks directory
        if not str(path).startswith(str(HOOKS_DIR)):
            continue

        # Only Python files
        if path.suffix != ".py":
            continue

        # Skip test files, docs, __pycache__
        if any(skip in str(path) for skip in ["test_", ".md", "__pycache__", "__lib__"]):
            continue

        changed_files.append(path)

    return changed_files


def is_critical_hook(hook_path: Path) -> bool:
    """Check if hook is safety-critical."""
    hook_name = hook_path.stem

    # Method 1: Pattern match
    for pattern in CRITICAL_HOOK_PATTERNS:
        if pattern in hook_name:
            return True

    # Method 2: Check docstring
    try:
        content = hook_path.read_text()
        if "CRITICALITY: safety-critical" in content:
            return True
    except Exception:
        pass

    return False


def find_test_file(hook_path: Path) -> Path | None:
    """Find corresponding test file for hook."""
    test_file = TESTS_DIR / f"test_{hook_path.stem}.py"

    if test_file.exists():
        return test_file

    return None


def run_tests(test_file: Path) -> Dict:
    """Run tests for a specific test file."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )

    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "passed": result.returncode == 0,
    }


def main():
    """Pre-commit enforcement entry point."""
    changed_hooks = get_changed_hooks()

    if not changed_hooks:
        # No hook changes, allow commit
        return 0

    violations = []
    warnings = []

    for hook_path in changed_hooks:
        hook_name = hook_path.stem
        is_critical = is_critical_hook(hook_path)
        test_file = find_test_file(hook_path)

        if not test_file:
            if is_critical:
                violations.append({
                    "hook": str(hook_path),
                    "issue": "missing_test",
                    "message": f"Critical hook {hook_name} has no test file. Create {test_file}",
                })
            else:
                warnings.append({
                    "hook": str(hook_path),
                    "issue": "missing_test_advisory",
                    "message": f"Advisory hook {hook_name} has no test file (recommended but not required)",
                })
        else:
            # Run tests
            result = run_tests(test_file)
            if not result["passed"]:
                violations.append({
                    "hook": str(hook_path),
                    "issue": "test_failed",
                    "message": f"Tests for {hook_name} failed. Run: pytest {test_file}",
                    "details": result["stdout"] + result["stderr"],
                })

    # Report results
    if violations:
        print("❌ TEST ENFORCEMENT: Commit BLOCKED", file=sys.stderr)
        print("\nCritical violations:", file=sys.stderr)
        for v in violations:
            print(f"  - {v['message']}", file=sys.stderr)
            if "details" in v:
                print(f"\n  Output:\n{v['details']}", file=sys.stderr)
        print("\nBypass with: git commit --no-verify", file=sys.stderr)
        return 1

    if warnings:
        print("⚠️  TEST ENFORCEMENT: Warnings (commit allowed)", file=sys.stderr)
        for w in warnings:
            print(f"  - {w['message']}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 7.3 Installation Script

**File**: `P:/.claude/hooks\tests\install_test_enforcement.py`

```python
#!/usr/bin/env python3
"""
Install test enforcement hooks for git.

USAGE:
    python P:/.claude/hooks/tests/install_test_enforcement.py
"""

import os
import shutil
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
GIT_HOOKS_DIR = Path(".git/hooks")

# Hooks to install
HOOKS = {
    "pre-commit": SCRIPTS_DIR / "test_enforcement.py",
    "pre-push": SCRIPTS_DIR / "test_enforcement_full.py",  # Optional
}


def install_hooks():
    """Copy hook scripts to .git/hooks."""
    GIT_HOOKS_DIR.mkdir(parents=True, exist_ok=True)

    for hook_name, source_file in HOOKS.items():
        if not source_file.exists():
            print(f"⚠️  Source hook not found: {source_file}")
            continue

        target_file = GIT_HOOKS_DIR / hook_name

        # Backup existing
        if target_file.exists():
            backup = target_file.with_suffix(f"{target_file.suffix}.backup")
            shutil.copy(target_file, backup)
            print(f"📦 Backed up existing {hook_name} to {backup}")

        # Copy new hook
        shutil.copy(source_file, target_file)
        os.chmod(target_file, 0o755)  # Make executable

        print(f"✅ Installed {hook_name} → {target_file}")

    print("\n🧪 Test enforcement hooks installed!")
    print("   Commits will be checked for:")
    print("   - Critical hooks without tests")
    print("   - Failing tests for changed hooks")
    print("\n   Bypass with: git commit --no-verify")


if __name__ == "__main__":
    install_hooks()
```

---

## 8. Summary Checklist

### 8.1 For Hook Development

- [ ] Hook has `CRITICALITY` declared in docstring
- [ ] Hook has `TEST_FILE` reference in docstring
- [ ] Contract section with INPUT_SPEC, OUTPUT_SPEC, INVARIANTS
- [ ] Test file exists: `test_{hook_name}.py`
- [ ] Test includes contract tests
- [ ] Test includes behavioral tests (block/allow conditions)
- [ ] Test includes edge cases
- [ ] Test includes meta-conversation exemption test (if applicable)

### 8.2 For Test Development

- [ ] Test uses `run_hook()` helper for subprocess execution
- [ ] Test marked with `@pytest.mark.contract` for contract tests
- [ ] Test marked with `@pytest.mark.integration` for realistic sequences
- [ ] Test includes assertions for exit codes (0 vs 2 for blocking hooks)
- [ ] Test includes assertions for output format

### 8.3 For Enforcement

- [ ] Pre-commit hook installed
- [ ] Pre-push hook installed (optional)
- [ ] CI configured to run full test suite
- [ ] Time budgets met (pre-commit < 30s, pre-push < 120s, CI < 300s)
- [ ] Bypass logging enabled for accountability

---

## 9. Next Steps

1. **Review**: Validate this design with actual workflow
2. **Prototype**: Implement TDD assistant hook
3. **Iterate**: Refine based on developer experience
4. **Document**: Add to CLAUDE.md as standard practice
5. **Automate**: Add to project initialization templates
