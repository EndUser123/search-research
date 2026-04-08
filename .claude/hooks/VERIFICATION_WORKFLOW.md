# Verification Workflow Documentation

**Version**: 1.0.0
**Last Updated**: 2026-03-10
**Related Tasks**: TASK-001, TASK-002, TASK-003, TASK-005, TASK-009

## Table of Contents

1. [Quick Start](#quick-start)
2. [Tier Selection Guide](#tier-selection-guide)
3. [Skill Verification](#skill-verification)
4. [Hook Verification](#hook-verification)
5. [Workflow Verification](#workflow-verification)
6. [Common Patterns](#common-patterns)
7. [Troubleshooting](#troubleshooting)
8. [Reference Materials](#reference-materials)

---

## Quick Start

### What is Verification?

Verification is the process of proving that code, hooks, or skills work as intended through **empirical evidence**. The verification system uses a 3-tier approach to catch issues at different levels:

- **Tier 1 (Component)**: Unit tests pass
- **Tier 2 (Integration)**: Hooks integrate correctly
- **Tier 3 (E2E)**: Actual workflow execution succeeds

### Basic Usage

#### Verify a Skill

```bash
# Using the /verify skill
/verify skill:arch

# Manual verification workflow
pytest .claude/skills/arch/tests/ -v              # Tier 1
python .claude/hooks/tests/test_hook_registration.py  # Tier 2
/arch "test prompt"                                # Tier 3
```

#### Verify a Hook

```bash
# Using the /verify skill
/verify hook:breadcrumb_init

# Manual verification workflow
pytest .claude/hooks/tests/test_breadcrumb.py -v  # Tier 1
echo '{"tool_name":"Test","tool_input":{}}' | python .claude/hooks/breadcrumb_init.py  # Tier 2
# Test actual hook behavior in workflow           # Tier 3
```

#### Quick Component Test Only

```bash
# Test a single file (component tests only)
/verify src/handoff.py
pytest tests/test_handoff.py -v
```

### When to Use Each Tier

| Scenario | Required Tiers | Example |
|----------|---------------|---------|
| Changed a function in a skill | Tier 1 only | Fixed bug in `/arch` logic |
| Modified hook behavior | Tier 1 + Tier 2 | Updated breadcrumb trigger |
| Added new skill or feature | All 3 tiers | Created `/new-skill` |
| Fixed router integration | Tier 2 + Tier 3 | Hook chain wasn't calling skill |
| Changed workflow logic | Tier 3 only | Modified skill invocation flow |

---

## Tier Selection Guide

### Tier 1: Component Tests

**Purpose**: Verify individual functions and classes work correctly in isolation.

**When to use**:
- You changed function logic
- You fixed a bug in isolated code
- You added new utility functions
- You refactored code (behavior unchanged)

**What it tests**:
- Function inputs/outputs
- Error handling
- Edge cases
- Data transformations

**How to run**:
```bash
# For skills
pytest .claude/skills/<skill>/tests/ -v

# For hooks
pytest .claude/hooks/tests/test_<hook>.py -v

# For features
pytest tests/ -k <feature> -v
```

**Evidence required**:
- Test output showing pass/fail
- Number of tests passed
- Execution time

**Example output**:
```
=== Tier 1: Component Tests ===
Status: ✅ PASS
Command: pytest tests/test_arch.py -v

Results:
- test_arch_activation PASSED
- test_arch_intent_detection PASSED
- test_arch_fallback PASSED

3 passed in 0.15s
```

---

### Tier 2: Integration Checks

**Purpose**: Verify that hooks integrate correctly with the router system and hook chains execute properly.

**When to use**:
- You modified hook registration
- You changed router behavior
- You added/removed hooks from chains
- You modified hook input/output format

**What it tests**:
- Hook registration in routers
- Hook chain execution
- Router decision logic
- Hook input/output protocol

**How to run**:
```bash
# Check hook registration
python .claude/hooks/tests/test_hook_registration.py

# Check specific router
python .claude/hooks/UserPromptSubmit_router.py --check

# Test hook chain execution
echo '{"tool_name":"Read","tool_input":{"file_path":"test.txt"}}' | python .claude/hooks/PreToolUse_write_router.py
```

**Evidence required**:
- Hook appears in router output
- Hook processes input without exceptions
- Hook chain completes
- Router makes correct decision

**Example output**:
```
=== Tier 2: Integration Check ===
Status: ✅ PASS

Checks:
- Hook registration: ✅ breadcrumb_init in UserPromptSubmit_router.py
- Router execution: ✅ Router processes hook correctly
- Hook chain: ✅ All hooks in chain execute without exceptions
- Input/output: ✅ Hook accepts valid input, returns valid output
```

---

### Tier 3: E2E Tests

**Purpose**: Verify that actual workflows execute successfully from start to finish.

**When to use**:
- You created a new skill
- You modified skill invocation logic
- You changed workflow execution paths
- You need to verify multi-step processes

**What it tests**:
- Skill invocation works
- UserPromptSubmit → skill → response flow
- Tool sequences execute correctly
- Multi-stage workflows complete
- State changes persist

**How to run**:
```bash
# For skills: invoke via CLI
/arch "test prompt"

# Check E2E tracker
python .claude/hooks/PostToolUse_e2e_tracker.py --check

# View E2E execution log
cat .claude/state/e2e_executions_<session_id>.jsonl
```

**Evidence required**:
- Skill executes without errors
- E2E tracker logs workflow
- Expected state changes occur
- Response generated successfully

**Example output**:
```
=== Tier 3: E2E Test ===
Status: ✅ PASS

Invocation: /arch "analyze this code"

Evidence:
- UserPromptSubmit: ✅ Captured at 2026-03-10T14:30:15Z
- Skill execution: ✅ Completed in 0.23s
- Response generation: ✅ Completed
- E2E tracker: ✅ Workflow logged to e2e_executions_<session>.jsonl

E2E Tracker Entry:
{
  "workflow_type": "skill_invocation",
  "target": "arch",
  "stages": [
    {"stage": "capture", "status": "passed"},
    {"stage": "execution", "status": "passed"},
    {"stage": "response", "status": "passed"}
  ],
  "session_id": "...",
  "terminal_id": "...",
  "timestamp": "2026-03-10T14:30:15Z"
}
```

---

## Skill Verification

### Complete Skill Verification Workflow

Use this workflow when creating or significantly modifying a skill.

#### Step 1: Tier 1 - Component Tests

Verify the skill's core logic works:

```bash
# Run skill's unit tests
pytest .claude/skills/<skill>/tests/ -v

# Example: /arch skill
pytest .claude/skills/code/tests/ -v
```

**Expected evidence**:
```
tests/test_arch.py::test_arch_activation PASSED
tests/test_arch.py::test_arch_intent_detection PASSED
tests/test_arch.py::test_arch_fallback PASSED
3 passed in 0.15s
```

#### Step 2: Tier 2 - Integration Check

Verify the skill integrates with the system:

```bash
# Check skill is registered
ls .claude/skills/<skill>/SKILL.md

# Check skill appears in router (if applicable)
grep -r "<skill>" .claude/hooks/*router.py

# Verify skill metadata
python -c "
import yaml
with open('.claude/skills/<skill>/SKILL.md') as f:
    data = yaml.safe_load(f.split('---')[1])
    print('Name:', data.get('name'))
    print('Category:', data.get('category'))
    print('Triggers:', data.get('triggers'))
"
```

**Expected evidence**:
- SKILL.md file exists
- Skill has valid frontmatter
- Skill is discoverable (if triggered)

#### Step 3: Tier 3 - E2E Test

Verify the skill executes end-to-end:

```bash
# Invoke the skill
/verify skill:<skill>

# Or invoke directly
/<skill> "test prompt"

# Check E2E tracker
python .claude/hooks/PostToolUse_e2e_tracker.py --check

# View execution log
cat .claude/state/e2e_executions_*.jsonl | tail -5
```

**Expected evidence**:
```
Skill execution completed in 0.23s
E2E tracker: Workflow logged to e2e_executions_<session>.jsonl
Response generated successfully
```

### Skill Verification Checklist

Use this checklist before marking a skill as verified:

**Tier 1 (Component)**:
- [ ] All unit tests pass
- [ ] Test coverage >80% for new code
- [ ] Edge cases handled
- [ ] Error conditions tested

**Tier 2 (Integration)**:
- [ ] SKILL.md exists with valid frontmatter
- [ ] Skill triggers work correctly
- [ ] Skill aliases resolve
- [ ] Integration reciprocation (suggest: targets exist)

**Tier 3 (E2E)**:
- [ ] Skill executes without errors
- [ ] E2E tracker logs workflow
- [ ] Expected state changes occur
- [ ] Response generated successfully

### Using /verify skill

The `/verify` skill automates the 3-tier workflow:

```bash
# Verify a skill
/verify skill:arch

# Expected output structure
[VERIFY] Running 3-tier verification for skill:arch...

=== Tier 1: Component Tests ===
Status: ✅ PASS
[Test output...]

=== Tier 2: Integration Check ===
Status: ✅ PASS
[Integration checks...]

=== Tier 3: E2E Test ===
Status: ✅ PASS
[E2E execution evidence...]

## Overall Status: ✅ VERIFIED
```

---

## Hook Verification

### Complete Hook Verification Workflow

Use this workflow when creating or modifying hooks.

#### Step 1: Tier 1 - Component Tests

Verify the hook's core logic:

```bash
# Run hook's unit tests
pytest .claude/hooks/tests/test_<hook>.py -v

# Example: breadcrumb_init hook
pytest .claude/hooks/tests/test_breadcrumb.py -v
```

**Expected evidence**:
```
tests/test_breadcrumb.py::test_breadcrumb_init PASSED
tests/test_breadcrumb.py::test_breadcrumb_session_context PASSED
2 passed in 0.10s
```

#### Step 2: Tier 2 - Integration Check

Verify the hook integrates with the router:

```bash
# Check hook registration
python .claude/hooks/tests/test_hook_registration.py

# Test hook in router context
echo '{"test":"data"}' | python .claude/hooks/<hook>.py

# Verify hook chain execution
echo '{"tool_name":"Test","tool_input":{}}' | python .claude/hooks/UserPromptSubmit_router.py
```

**Expected evidence**:
```
Hook registration: ✅ breadcrumb_init registered
Hook execution: ✅ Processes input without errors
Router integration: ✅ Hook appears in router dispatch
```

#### Step 3: Tier 3 - E2E Test

Verify the hook works in actual workflows:

```bash
# Trigger the hook event
# For UserPromptSubmit hooks: Send a message
# For PreToolUse hooks: Use a tool
# For PostToolUse hooks: Complete a tool call
# For Stop hooks: Complete a response

# Check evidence store
python -c "
from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
events = load_scoped_tool_events(session_id='', scope=SCOPE_SESSION_FRESH, limit=10)
for e in events:
    print(e['name'], e.get('success'))
"
```

**Expected evidence**:
```
Hook triggered in workflow
Evidence store shows tool events
Hook processed events correctly
No hook exceptions in logs
```

### Hook Verification Checklist

**Tier 1 (Component)**:
- [ ] Unit tests pass
- [ ] Hook logic tested
- [ ] Error handling verified
- [ ] Edge cases covered

**Tier 2 (Integration)**:
- [ ] Hook registered in router or settings.json
- [ ] Hook processes valid input
- [ ] Hook returns valid output
- [ ] Hook chain executes

**Tier 3 (E2E)**:
- [ ] Hook triggers on correct event
- [ ] Evidence store captures events
- [ ] Multi-terminal isolation works
- [ ] No false positives/negatives

### Testing Multi-Terminal Isolation

Hooks must work correctly across multiple concurrent terminal sessions:

```bash
# Terminal 1: Start session
export CLAUDE_SESSION_ID=session-1
# Trigger hook

# Terminal 2: Start concurrent session
export CLAUDE_SESSION_ID=session-2
# Trigger hook

# Verify isolation
python -c "
from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
events_1 = load_scoped_tool_events(session_id='session-1', scope=SCOPE_SESSION_FRESH, limit=20)
events_2 = load_scoped_tool_events(session_id='session-2', scope=SCOPE_SESSION_FRESH, limit=20)
assert len(events_1) > 0, 'Session 1 has no events'
assert len(events_2) > 0, 'Session 2 has no events'
print('✅ Sessions isolated')
"
```

---

## Workflow Verification

### Verifying Multi-Step Workflows

Workflows involve multiple tool calls or stages. Verify them end-to-end.

#### Example: Feature Development Workflow

```bash
# Tier 1: Test individual components
pytest tests/test_feature.py -v

# Tier 2: Verify integration points
python -c "
# Check router configuration
import json
with open('.claude/settings.json') as f:
    settings = json.load(f)
    assert 'hooks' in settings
    print('✅ Hooks configured')
"

# Tier 3: Execute full workflow
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes
echo "feature code" > feature.py

# 3. Run tests
pytest tests/ -v

# 4. Commit changes
git add feature.py
git commit -m "Add new feature"

# 5. Verify E2E tracker
python .claude/hooks/PostToolUse_e2e_tracker.py --check
```

### Tool Sequence Validation

Verify that tool sequences execute correctly:

```bash
# Define expected tool sequence
expected_tools = ["Glob", "Read", "Edit", "Bash"]

# Run workflow
# [Execute tools...]

# Check evidence store
python -c "
from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
events = load_scoped_tool_events(session_id='', scope=SCOPE_SESSION_FRESH, limit=10)
actual_tools = [e['name'] for e in events]
expected = ['Glob', 'Read', 'Edit', 'Bash']
assert actual_tools == expected, f'Tool mismatch: {actual_tools}'
print('✅ Tool sequence validated')
"
```

### Evidence Collection Best Practices

When verifying workflows, collect evidence at each stage:

```bash
# Stage 1: Preparation
echo "=== Stage 1: Preparation ===" > verification.log
git status >> verification.log
git log -1 --oneline >> verification.log

# Stage 2: Execution
echo "=== Stage 2: Execution ===" >> verification.log
pytest tests/ -v >> verification.log 2>&1

# Stage 3: Verification
echo "=== Stage 3: Verification ===" >> verification.log
python .claude/hooks/PostToolUse_e2e_tracker.py --check >> verification.log

# Review evidence
cat verification.log
```

---

## Common Patterns

### Pattern 1: Feature Development Workflow

When developing a new feature:

1. **Plan** (if required by gate):
   ```bash
   /plan "Add feature X"
   ```

2. **Implement** (TDD):
   ```bash
   # Write tests first
   pytest tests/test_feature.py -v

   # Implement feature
   # [Write code...]

   # Verify tests pass
   pytest tests/test_feature.py -v
   ```

3. **Integrate**:
   ```bash
   # Check hook registration (if needed)
   python .claude/hooks/tests/test_hook_registration.py

   # Verify integration
   pytest tests/integration/test_feature.py -v
   ```

4. **Verify E2E**:
   ```bash
   # Test full workflow
   # [Execute workflow...]

   # Check E2E tracker
   python .claude/hooks/PostToolUse_e2e_tracker.py --check
   ```

**Evidence required**:
- Tier 1: Unit tests pass
- Tier 2: Integration tests pass
- Tier 3: E2E tracker shows workflow completion

### Pattern 2: Bug Fix Workflow

When fixing a bug:

1. **Investigate**:
   ```bash
   # Read relevant code
   /trace "bug location"

   # Check test failure
   pytest tests/test_failing.py -v
   ```

2. **Fix**:
   ```bash
   # Apply fix
   # [Edit code...]

   # Verify fix locally
   pytest tests/test_failing.py -v
   ```

3. **Verify E2E**:
   ```bash
   # Test in actual workflow
   # [Reproduce bug scenario...]

   # Confirm fix works
   ```

**Evidence required**:
- Tier 1: Failing test now passes
- Tier 2: Integration still works
- Tier 3: Bug no longer occurs in workflow

### Pattern 3: Hook Development Workflow

When developing a new hook:

1. **Implement**:
   ```bash
   # Create hook file
   # [Write hook code...]

   # Write unit tests
   pytest .claude/hooks/tests/test_new_hook.py -v
   ```

2. **Register**:
   ```bash
   # Register in router or settings.json
   # [Update router...]

   # Verify registration
   python .claude/hooks/tests/test_hook_registration.py
   ```

3. **Test in Context**:
   ```bash
   # Test hook in isolation
   echo '{"test":"data"}' | python .claude/hooks/new_hook.py

   # Test in router context
   echo '{"tool_name":"Test","tool_input":{}}' | python .claude/hooks/PreToolUse_router.py
   ```

4. **Verify E2E**:
   ```bash
   # Trigger hook in actual workflow
   # [Execute workflow that triggers hook...]

   # Check evidence store
   python -c "
from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
events = load_scoped_tool_events(session_id='', scope=SCOPE_SESSION_FRESH, limit=10)
print([e['name'] for e in events])
"
   ```

**Evidence required**:
- Tier 1: Hook unit tests pass
- Tier 2: Hook registered and processes input
- Tier 3: Hook triggers correctly in workflow

---

## Troubleshooting

### Common Issues

#### Issue 1: Tier Mismatch (Tier 1 passes, Tier 2 fails)

**Symptoms**:
- Unit tests pass
- Hook chain doesn't execute
- Router doesn't call hook

**Diagnosis**:
```bash
# Check hook registration
python .claude/hooks/tests/test_hook_registration.py

# Check router configuration
grep -r "hook_name" .claude/hooks/*router.py

# Verify hook export
python -c "import hook_file; print(dir(hook_file))"
```

**Common causes**:
- Hook not registered in router
- Hook function not exported
- Router priority incorrect
- Hook missing required function

**Solutions**:
1. Add hook to router dispatch
2. Export `process_prompt()` or `run()` function
3. Adjust `HOOK_PRIORITY` in router
4. Implement required hook interface

#### Issue 2: Tier 2 passes, Tier 3 fails

**Symptoms**:
- Hook executes in isolation
- Workflow doesn't complete
- E2E tracker missing events

**Diagnosis**:
```bash
# Check E2E tracker
python .claude/hooks/PostToolUse_e2e_tracker.py --check

# View E2E log
cat .claude/state/e2e_executions_*.jsonl | tail -10

# Check evidence store
python -c "
from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
events = load_scoped_tool_events(session_id='', scope=SCOPE_SESSION_FRESH, limit=10)
print(f'Events: {len(events)}')
for e in events:
    print(f'  {e[\"name\"]}: {e.get(\"success\")}')
"
```

**Common causes**:
- Skill doesn't invoke
- Workflow exception not caught
- E2E tracker not installed
- Session ID mismatch

**Solutions**:
1. Verify skill invocation logic
2. Add exception handling in workflow
3. Install E2E tracker hook
4. Check session ID propagation

#### Issue 3: False Positive Blocking

**Symptoms**:
- Hook blocks legitimate action
- Verification fails incorrectly
- Error message unclear

**Diagnosis**:
```bash
# Check hook logs
python .claude/hooks/shared_utils.py logs --limit 50

# Enable verbose mode
export HOOK_VERBOSE=true
# [Re-trigger hook...]

# Check bypass status
echo $CONSTITUTIONAL_HOOKS_BYPASS
```

**Common causes**:
- Hook pattern too aggressive
- Edge case not handled
- Configuration incorrect
- Bug in hook logic

**Solutions**:
1. Adjust hook detection patterns
2. Add edge case handling
3. Check hook configuration
4. Report bug if hook logic is incorrect

#### Issue 4: Multi-Terminal Isolation Failure

**Symptoms**:
- Terminal 1 sees Terminal 2's events
- Evidence store returns wrong session data
- State corruption between terminals

**Diagnosis**:
```bash
# Check session IDs
echo $CLAUDE_SESSION_ID
echo $CLAUDE_TERMINAL_ID

# View evidence store
python -c "
from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
events = load_scoped_tool_events(session_id='', scope=SCOPE_SESSION_FRESH, limit=20)
for e in events:
    print(f'{e[\"session_id\"]}/{e[\"terminal_id\"]}: {e[\"name\"]}')
"
```

**Common causes**:
- Session ID not propagated
- Terminal ID not unique
- Evidence store query missing filters

**Solutions**:
1. Verify session ID in all hook calls
2. Generate unique terminal ID per session
3. Use `resolve_session_id()` with proper parameters

### Debug Tips

#### Enable Verbose Logging

```bash
# Enable verbose mode for hooks
export HOOK_VERBOSE=true

# Enable debug mode for specific hook
export SPECIFIC_HOOK_DEBUG=true

# Check logs
python .claude/hooks/shared_utils.py logs --limit 100
```

#### Test Hooks in Isolation

```bash
# Test hook with synthetic input
echo '{"tool_name":"Read","tool_input":{"file_path":"test.txt"}}' | python .claude/hooks/hook_name.py

# Check exit code
echo $?  # 0 = allow, 2 = block

# View output
# Should see JSON with "allow": true/false
```

#### Verify Evidence Store

```bash
# Check evidence store schema
python -c "
import sqlite3
conn = sqlite3.connect('.claude/hooks/session_data/evidence.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print(cursor.fetchall())
"

# Check recent events
python -c "
from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
events = load_scoped_tool_events(session_id='', scope=SCOPE_SESSION_FRESH, limit=5)
for e in events:
    print(f'{e[\"name\"]}: {e.get(\"command\", \"\")[:50]}')
"
```

#### Verify E2E Tracker

```bash
# Check E2E tracker status
python .claude/hooks/PostToolUse_e2e_tracker.py --check

# View recent executions
cat .claude/state/e2e_executions_*.jsonl | tail -5 | python -m json.tool

# Check log rotation
ls -lh .claude/state/e2e_executions_*.jsonl
```

---

## Reference Materials

### Evidence Tiers

Reference: `.claude/skills/evidence-tiers/SKILL.md`

| Tier | Ceiling | Sources |
|------|---------|---------|
| 1 | 95% | Execution artifacts, logs, test output |
| 2 | 85% | Official docs, specs, peer-reviewed |
| 3 | 75% | Static analysis, logical derivation |
| 4 | 50% | Comments, unverified claims, speculation |

**Rules**:
- High-stakes decisions require Tier 1 or 2
- Mixed tiers: ceiling = lowest tier used
- Tier 4 alone: flag as [UNVERIFIED]

### Verification Components

**TASK-000: Evidence Store**
- File: `.claude/hooks/evidence_store.py`
- Purpose: Session-scoped evidence storage
- API: `load_scoped_tool_events()`, `load_turn_scoped_events()`, `resolve_session_id()`

**TASK-002: Completion Claim Verification**
- File: `.claude/hooks/StopHook_unverified_stance.py`
- Purpose: Block premature "fixed"/"tested" claims
- Patterns: "all tests pass", "issue is fixed", "verified"

**TASK-003: E2E Workflow Tracker**
- File: `.claude/hooks/PostToolUse_e2e_tracker.py`
- Purpose: Track actual workflow execution
- Storage: `state/e2e_executions_{session_id}.jsonl`

**TASK-005: /verify Skill**
- Directory: `.claude/skills/verify/`
- Purpose: 3-tier verification orchestrator
- Usage: `/verify skill:<name>`, `/verify hook:<name>`

**TASK-009: Integration Test Suite**
- Directory: `.claude/hooks/tests/integration/`
- Purpose: E2E tests for verification system
- Tests: Skill invocation, hook chains, verify skill

### Related Skills

- `/trace` - Deep manual verification
- `/testing-skills` - Skill QA
- `/evidence-tiers` - Evidence quality assessment

### Environment Variables

```bash
# Hook bypass
export CONSTITUTIONAL_HOOKS_BYPASS=1

# Verification hooks
export UNVERIFIED_STANCE_ENABLED=true
export UNVERIFIED_STANCE_MODE=warn  # or block

# Evidence store
export EVIDENCE_DB_JOURNAL_MODE=WAL

# E2E tracker
export E2E_TRACKER_ENABLED=true

# Debug
export HOOK_VERBOSE=true
export STRAWBERRY_VALIDATOR_VERBOSE=true
```

### File Locations

```
.claude/
├── hooks/
│   ├── evidence_store.py              # TASK-000
│   ├── StopHook_unverified_stance.py  # TASK-002
│   ├── PostToolUse_e2e_tracker.py     # TASK-003
│   ├── tests/
│   │   ├── test_*.py                  # Tier 1 tests
│   │   └── integration/
│   │       └── test_*_e2e.py          # Tier 3 tests
│   └── session_data/
│       ├── evidence.db                # Evidence store
│       └── e2e_executions_*.jsonl     # E2E logs
└── skills/
    ├── verify/                        # TASK-005
    │   └── SKILL.md
    └── evidence-tiers/
        └── SKILL.md
```

---

## Quick Reference Card

### Verification Commands

```bash
# Skill verification
/verify skill:<name>

# Hook verification
/verify hook:<name>

# Manual verification
pytest tests/ -v                                    # Tier 1
python .claude/hooks/tests/test_hook_registration.py  # Tier 2
/<skill> "test"                                    # Tier 3

# Check evidence
python .claude/hooks/PostToolUse_e2e_tracker.py --check
cat .claude/state/e2e_executions_*.jsonl | tail -5

# Enable debug
export HOOK_VERBOSE=true
```

### Evidence Checklist

**Tier 1 (Component)**:
- [ ] Test output shows pass/fail
- [ ] All tests pass
- [ ] Execution time reasonable

**Tier 2 (Integration)**:
- [ ] Hook registered in router
- [ ] Hook processes input
- [ ] Hook chain executes
- [ ] No exceptions in logs

**Tier 3 (E2E)**:
- [ ] Workflow executes
- [ ] E2E tracker logs event
- [ ] Expected state changes
- [ ] Response generated

### Troubleshooting Steps

1. **Check logs**: `python .claude/hooks/shared_utils.py logs --limit 50`
2. **Test in isolation**: `echo '{"test":"data"}' | python hook.py`
3. **Verify evidence**: `python -c "from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events; print(load_scoped_tool_events(session_id='', scope=SCOPE_SESSION_FRESH, limit=5))"`
4. **Check E2E**: `python .claude/hooks/PostToolUse_e2e_tracker.py --check`
5. **Enable verbose**: `export HOOK_VERBOSE=true`

---

**Document Version**: 1.0.0
**Last Updated**: 2026-03-10
**Maintained By**: Verification System (TASK-001, TASK-002, TASK-003, TASK-005, TASK-009)
