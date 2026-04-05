# Tier Workflow Details

## Step 0: Search for Context (Pre-Verification)

**Before running verification, search for related work:**

```bash
# Find similar features or prior verifications
/search "{target} verification" --backend chs,cks

# Find related requirements or patterns
/search "{target} requirements" --backend chs,cks,code

# Find similar issues or solutions
/search "{target_type} issues" --backend chs,cks
```

**Search accelerates verification by:**
- Grounding verification in actual project patterns
- Finding similar prior verifications to learn from
- Identifying related requirements and dependencies
- Discovering common issues and their solutions

## Step 1: Detect Verification Target

Parse input to determine target type:

```python
# Input patterns
/verify skill:arch           -> Target: skill "arch"
/verify hook:init            -> Target: hook "*init*.py"
/verify feature:e2e          -> Target: feature "e2e"
/verify src/handoff.py       -> Target: code file (default: component tests)

# Target types
skill:   .claude/skills/<name>/SKILL.md
hook:    .claude/hooks/*<name>*.py
feature: Feature flag or workflow
code:    Any .py file (component tests only)
```

## Step 2: Run Tier 0 (Checklist Verification)

**What**: Fast-fail verification to catch configuration and structural issues before running expensive tests

```python
from verify.tiers.tier0_checklist import run_checklist_verification

checklist_result = run_checklist_verification(
    target_type="skill",  # or "hook" or "feature"
    target_path=".claude/skills/arch/SKILL.md"
)
```

**Expected output**:
```markdown
### Tier 0: Checklist Verification
**Status**: PASS
**Duration**: 0.3s
**Items Checked**: 5
**Items Passed**: 5
**Findings**:
- Problem statement documented
- Context analysis complete
- Solution proposed
- Risks identified
- Test coverage planned
```

**Fast-fail behavior**: If Tier 0 checklist fails, verification stops (Tiers 1-3 not executed)

## Step 3: Run Tier 1 (Component Tests)

```bash
# For skills
pytest .claude/skills/<skill>/tests/ -v

# For hooks
pytest .claude/hooks/tests/test_<hook>.py -v

# For features
pytest tests/ -k <feature> -v
```

**Expected output**:
```markdown
### Tier 1: Component Tests
**Status**: PASS
**Command**: pytest tests/test_arch.py -v
**Evidence**:
- test_arch_activation PASSED
- test_arch_intent_detection PASSED
- test_arch_fallback PASSED
```

## Step 4: Run Tier 2 (Integration Check)

```bash
# Check hook registration
python .claude/hooks/tests/test_hook_registration.py

# Check router execution
python .claude/hooks/<router>_router.py --check

# Verify hook chain executes
echo '{"tool_name":"Test","tool_input":{}}' | python .claude/hooks/<hook>.py
```

**Expected output**:
```markdown
### Tier 2: Integration Check
**Status**: PASS
**Checks**:
- Hook registration: Registered in Stop_router.py
- Router execution: Router processes hook correctly
- Hook chain: All hooks in chain execute without exceptions
```

## Step 5: Run Tier 3 (E2E Test)

```bash
# For skills: Invoke via Skill tool
echo '{"skill":"arch","prompt":"test"}' | python -c '...'

# For features: Run workflow
pytest tests/test_e2e_<feature>.py -v

# Check E2E tracker
python .claude/hooks/PostToolUse_e2e_tracker.py --check
```

**Expected output**:
```markdown
### Tier 3: E2E Test
**Status**: PASS
**Invocation**: /arch "test prompt"
**Evidence**:
- UserPromptSubmit: Captured
- Skill execution: Completed in 0.15s
- Response generation: Completed
- E2E tracker: Workflow logged to e2e_executions_{session}.jsonl
```
