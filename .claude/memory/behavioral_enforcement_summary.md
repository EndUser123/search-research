# Behavioral Enforcement - Quick Reference

**What was implemented**: Multi-layer enforcement system preventing lazy behavioral patterns and giving up on problems.

**Implementation date**: 2026-03-10

---

## Files Created

| Priority | File | Purpose |
|----------|------|---------|
| P0 | `stop/Stop_verification_gate.py` | Blocks responses with unverified claims |
| P0 | `skills/diagnose/SKILL.md` | Structured diagnostic protocol |
| P0 | `skills/diagnose/skill.json` | Skill manifest |
| P1 | `pre/PreToolUse_tool_check.py` | Validates tool parameters |
| P1 | `templates/investigation_response.md` | Response template |
| P1 | `post/PostToolWrite_doc_validator.py` | Warns on unverified claims after code changes |

---

## How It Works

### Layer 1: Response Prevention (Stop Hook)
**File**: `stop/Stop_verification_gate.py`
**Triggers**: Before response completes
**Blocks**: Unverified claims, premature solutions, single-hypothesis testing

**Example block**:
```
## VERIFICATION GATE VIOLATION DETECTED

Violations Found: 2
  1. BEHAV-003: Claim without verification
  2. BEHAV-001: Premature solution jump

Required Actions:
  1. State hypothesis, design test, show output before claiming
  2. Complete Solution Proposal Gate checklist first
```

---

### Layer 2: Tool Validation (PreToolUse Hook)
**File**: `pre/PreToolUse_tool_check.py`
**Triggers**: Before tool execution
**Validates**: Parameter types, required fields, invasive operations

**Example block**:
```
## TOOL VALIDATION FAILED

Tool: Edit
Errors Found:
  1. replace_all: must be boolean (True/False or omit), not string 'false'

Suggested Fixes:
  1. Use replace_all=False or omit entirely (defaults to False)
```

---

### Layer 3: Structured Workflow (/diagnose Skill)
**File**: `skills/diagnose/SKILL.md`
**Triggers**: User invokes `/diagnose`
**Enforces**: 3+ hypotheses → systematic testing → documented conclusion

**Required output format**:
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

### Layer 4: Response Quality (PostToolWrite + Template)
**Files**: `post/PostToolWrite_doc_validator.py`, `templates/investigation_response.md`
**Triggers**: After code changes
**Warns**: "Should fix" without testing, "optimal solution" without verification

---

## Behavioral Anti-Patterns Prevented

| Pattern | Detection | Prevention |
|---------|-----------|------------|
| Premature solution jump | "Let's fix it" before testing | Blocked |
| Single hypothesis | Only H1 listed | /diagnose requires 3+ |
| Claims without testing | "I think X is the cause" | Blocked |
| Tool parameter errors | replace_all="false" string | Blocked |
| Documentation before verification | Read docs first | Template guidance |

---

## Protocols Enforced

All mechanisms enforce protocols from `MEMORY.md`:

### Verification First Protocol
> Never claim X causes Y without testing it first.

**Enforced by**: Stop hook, PostToolWrite hook, /diagnose skill

### Solution Proposal Gate
> 6 checkboxes before any solution proposal.

**Enforced by**: Stop hook, /diagnose skill

### Structured Diagnostic Protocol
> List 3+ hypotheses, test each systematically.

**Enforced by**: /diagnose skill

### Tool Usage Checklist
> Read docs → Identify parameters → Check types.

**Enforced by**: PreToolUse hook, investigation template

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

**Test Results**:
H1: `pytest tests/ -v -p no:testmon` → Tests complete in 0.15s → RULED OUT
H2: `grep -r "tot_tracer" tests/` → No matches → RULED OUT
H3: `mv .claude/hooks .claude/hooks.bak` → Still hangs → RULED OUT
H4: `pytest --collect-only` → Hangs at same point → CONFIRMED

**Conclusion**: H4 - test collection has circular import
**Next Step**: Analyze test import graph with `pytest --collect-only --verbose`
```

---

## Configuration

All hooks registered in `P:\.claude/settings.json`:

**Environment variables**:
```json
"VERIFICATION_GATE_ENABLED": "true",
"VERIFICATION_GATE_MODE": "block",
"TOOL_CHECK_ENABLED": "true",
"DOC_VALIDATOR_ENABLED": "true"
```

**Hook registration**:
- Stop: Line 194-198
- PreToolUse: Line 121-125
- PostToolUse: Line 138-142

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

## Expected Impact

**Improvements**:
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

**Status**: ✅ Complete and active
**Documentation**: `behavioral_enforcement_implementation.md` for full details
