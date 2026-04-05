# Behavioral Enforcement Implementation - Complete

**Date**: 2026-03-10
**Purpose**: Prevent lazy behavioral patterns and giving up on problems

---

## What Was Implemented

### P0 (Critical) - Complete

#### 1. Stop Hook: Verification Gate Enforcement
**File**: `P:\.claude\hooks\stop\Stop_verification_gate.py`

**Anti-patterns prevented**:
- BEHAV-001: Premature solution jump without verification
- BEHAV-002: Acceptance of first plausible explanation
- BEHAV-003: Insufficient verification before claims
- BEHAV-004: Jumping between diagnostic approaches

**Detection patterns**:
- "I think X is the cause" (without test evidence)
- "Let's fix it" (before completing Solution Proposal Gate)
- Single hypothesis testing (need 3+)
- Multiple diagnostic approaches without systematic testing

**Enforcement**: Blocks response with corrective actions

---

#### 2. /diagnose Skill: Structured Diagnostics
**Files**:
- `P:\.claude\skills\diagnose\SKILL.md`
- `P:\.claude\skills\diagnose\skill.json`

**Protocol enforced**:
1. List 3+ hypotheses upfront
2. For EACH hypothesis: test → mark RULED OUT/CONFIRMED
3. Only proceed when all but one ruled out OR one confirmed
4. Document diagnostic path

**Output template**:
```markdown
## Diagnostic Investigation
**Issue**: [description]

**Hypotheses**:
H1: [description]
H2: [description]
H3: [description]

**Test Results**:
H1: Test `[command]` → Result `[output]` → RULED OUT/CONFIRMED
H2: Test `[command]` → Result `[output]` → RULED OUT/CONFIRMED
H3: Test `[command]` → Result `[output]` → RULED OUT/CONFIRMED

**Conclusion**: H[confirmed] is the root cause
**Next Step**: [proposed fix]
```

---

### P1 (High) - Complete

#### 3. PreToolUse Hook: Tool Parameter Validation
**File**: `P:\.claude\hooks\pre\PreToolUse_tool_check.py`

**Validations**:
- **Edit tool**: replace_all must be boolean, not string "false"
- **Agent tool**: Requires subagent_type, model optional
- **Bash tool**: Detects invasive operations, requires detection commands first
- **Write tool**: Warns if file exists (should Read first)

**Example error**:
```
TOOL VALIDATION FAILED
Tool: Edit
Errors Found:
  1. replace_all: must be boolean (True/False or omit), not string 'false'

Suggested Fixes:
  1. Use replace_all=False or omit entirely (defaults to False)
```

---

#### 4. Response Template: Investigation Format
**File**: `P:\.claude\templates\investigation_response.md`

**Template structure**:
```markdown
## Investigation: [Title]

### Issue Description
[1-2 sentences]

### Discovery Phase
[What you checked FIRST]

### Hypothesis Testing
[Test → Result → Conclusion]

### Evidence Collected
[Files read, commands run, outputs]

### Root Cause
[Backed by evidence]

### Next Action
[Specific, not "investigate further"]
```

**Anti-patterns prevented**:
- Reading documentation first before verification
- Assuming APIs exist without checking
- Inventing parameters that "should" exist

---

#### 5. PostToolWrite Hook: Documentation Validation
**File**: `P:\.claude\hooks\post\PostToolWrite_doc_validator.py`

**Anti-patterns detected**:
- "This should fix it" without testing
- "That's the optimal solution" without verification
- "I think" or "probably" without test output

**Enforcement**: Non-blocking warnings (reminders to verify)

---

## How They Work Together

### Layer 1: Response Prevention (Stop Hook)
Blocks responses that:
- Make claims without testing
- Propose solutions without verification
- Accept first plausible explanation
- Jump between diagnostic approaches

### Layer 2: Tool Validation (PreToolUse Hook)
Prevents tool usage errors:
- Wrong parameter types (string vs boolean)
- Missing required parameters
- Invasive operations without detection
- File overwrites without reading first

### Layer 3: Structured Workflow (/diagnose Skill)
Enforces systematic investigation:
- 3+ hypotheses upfront
- Test each systematically
- Document findings
- Only conclude after testing

### Layer 4: Response Quality (PostToolWrite + Template)
Guides response format:
- Discovery before documentation
- Evidence-backed claims
- Specific next actions
- No "I think" without tests

---

## Protocol Integration

All mechanisms enforce protocols from `MEMORY.md`:

### Verification First Protocol
> Never claim X causes Y without testing it first.

**Enforced by**: Stop hook, PostToolWrite hook, /diagnose skill

### Solution Proposal Gate
> 6 checkboxes before any solution proposal.

**Enforced by**: Stop hook, /diagnose skill

### Structured Diagnostic Protocol
> List 3+ hypotheses, test each systematically.

**Enforced by**: /diagnose skill, Stop hook

### Tool Usage Checklist
> Read docs → Identify parameters → Check types.

**Enforced by**: PreToolUse hook, investigation template

---

## Behavioral Anti-Patterns Coverage

| Anti-Pattern | Detection | Prevention | Enforcement |
|--------------|-----------|------------|-------------|
| BEHAV-001: Premature solution jump | Stop hook patterns | /diagnose skill protocol | Response blocked |
| BEHAV-002: Single hypothesis | /diagnose skill required | 3+ hypotheses upfront | Skill incomplete |
| BEHAV-003: Claims without testing | Stop hook patterns | Verification First protocol | Response blocked |
| BEHAV-004: Diagnostic jumping | Stop hook patterns | Structured protocol | Response blocked |
| BEHAV-005: Tool parameter errors | PreToolUse validation | Parameter type checks | Tool blocked |
| BEHAV-006: Documentation before verification | Template guidance | Discovery-first flow | Quality reminder |

---

## Usage Examples

### Before (Lazy Behavior)
```
User: Why is pytest hanging?
Assistant: I think it's the pytest-testmon plugin. Let's disable it.
```

### After (Enforced Behavior)
```
User: Why is pytest hanging?
Assistant: ## Diagnostic Investigation

**Issue**: pytest hangs indefinitely when running test suite

**Hypotheses**:
H1: pytest-testmon plugin interference
H2: Missing tot_tracer module
H3: Hook interference during collection
H4: Recursive test imports

**Test Results**:
H1: Test `pytest tests/ -v -p no:testmon` → Tests complete in 0.15s → RULED OUT
H2: Test `grep -r "tot_tracer" tests/` → No matches → RULED OUT
H3: Test `mv .claude/hooks .claude/hooks.bak` → Still hangs → RULED OUT
H4: Test `pytest --collect-only` → Hangs at same point → CONFIRMED

**Conclusion**: H4 - test collection has circular import
**Next Step**: Analyze test import graph with `pytest --collect-only --verbose`
```

---

## Future Enhancements (P2)

### Not Yet Implemented
- PostToolWrite_doc_validator.py: Advanced documentation validation
- Response template system: Auto-format responses to templates
- Hook coordination: Prevent hook conflicts

### Requirements
- Hook performance testing (avoid slowdowns)
- False positive tuning (reduce noise)
- Integration with existing workflow

---

## Verification Checklist

To verify implementation is working:

- [ ] Stop hook triggers on "I think" without tests
- [ ] /diagnose skill requires 3+ hypotheses
- [ ] PreToolUse catches replace_all="false" string
- [ ] PostToolWrite warns on "should fix" without testing
- [ ] Investigation template promotes discovery-first flow

---

## Impact Assessment

**Expected improvements**:
- 70-90% reduction in unverified claims
- Systematic hypothesis testing in all investigations
- Tool parameter errors eliminated
- Clearer, evidence-backed responses

**Potential risks**:
- False positives (over-blocking)
- Slower initial responses (more upfront work)
- Learning curve for new protocols

**Mitigation**:
- Hook tuning based on false positive reports
- Template examples for quick reference
- Progressive enforcement (warnings → blocking)

---

---

## Registration Status

All hooks registered in `P:\.claude\settings.json`:

### Stop Hook (Line 194-198)
```json
{
  "type": "command",
  "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/stop/Stop_verification_gate.py --timeout 5.0",
  "timeout": 5
}
```

### PreToolUse Hook (Line 121-125)
```json
{
  "type": "command",
  "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/pre/PreToolUse_tool_check.py --timeout 5.0",
  "timeout": 5
}
```

### PostToolUse Hook (Line 138-142)
```json
{
  "type": "command",
  "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/post/PostToolWrite_doc_validator.py --timeout 5.0",
  "timeout": 5
}
```

### Environment Variables (Line 52-56)
```json
"VERIFICATION_GATE_ENABLED": "true",
"VERIFICATION_GATE_MODE": "block",
"TOOL_CHECK_ENABLED": "true",
"DOC_VALIDATOR_ENABLED": "true"
```

---

## How to Disable

If any hook causes issues:

```bash
# Disable verification gate (Stop hook)
export VERIFICATION_GATE_ENABLED=false

# Disable tool parameter check (PreToolUse hook)
export TOOL_CHECK_ENABLED=false

# Disable documentation validator (PostToolUse hook)
export DOC_VALIDATOR_ENABLED=false

# Or disable all constitutional hooks
export CONSTITUTIONAL_HOOKS_BYPASS=1
```

---

**Status**: ✅ P0 and P1 implementation complete and registered
**Next**: Field testing and tuning based on usage patterns
