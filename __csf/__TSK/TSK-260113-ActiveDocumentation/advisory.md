# Advisory Analysis: Active Documentation in CWO12

**Date:** 2026-01-13
**TSK:** TSK-260113-ActiveDocumentation
**Type:** Architecture Advisory

---

## Problem Diagnosis

The core issue: **Documentation is passive, not active**.

**Current State:**
```
CLAUDE.md exists → Agent reads on startup → Agent ignores during execution → Code violates rules
```

**Desired State:**
```
CLAUDE.md exists → Rules embedded in artifacts → Rules enforced in execution → Rules validated in evidence
```

## Does Your Analysis Make Sense?

**Yes.** The diagnosis is accurate. Here is the evidence:

| Component | Current Behavior | Gap |
|-----------|------------------|-----|
| `/specify` | Creates `specify.md` with requirements | Does NOT read CLAUDE.md for project rules |
| `/plan` | Creates `plan.md` with tasks | Does NOT reference embedded rules from spec |
| `/exec` | Executes implementation | TDD gate exists, but no project-rule enforcement |
| Evidence | Stores execution artifacts | Does NOT track "CLAUDE.md validated: YES/NO" |

**Existing Infrastructure:**
- `PreToolUse_tdd_gate.py` enforces TDD cycle
- `spec_validator.py` validates implementation against spec requirements
- `cwo.md` documents the 16-step workflow
- **Missing:** Bridge between CLAUDE.md and execution artifacts

---

## Gaps and Opportunities

### Gap 1: No CLAUDE.md Reader Module
**Current State:** CLAUDE.md is a static file that agents "should" read.

**Opportunity:** Create a structured constraint extractor:
```python
# P:/__csf.nip/src/features/constraints/claude_md_reader.py

class ClaudeMdConstraintReader:
    """Extracts and structures constraints from CLAUDE.md."""

    def extract_constraints(self, project_path: Path) -> ProjectConstraints:
        """Parse CLAUDE.md into structured rules."""
        # Returns: language rules, coverage requirements, naming conventions, etc.
```

### Gap 2: `/specify` Does Not Embed Project Rules
**Current State:** `specify.md` contains user requirements but not project constraints.

**Opportunity:** Modify `/specify` command to inject constraint section:
```markdown
## Project Rules (from CLAUDE.md)
- Language: TypeScript strict mode
- Coverage: 80% minimum
- No 'any' types without TODO
- TDD: RED → GREEN → REFACTOR required
```

### Gap 3: `/plan` Tasks Do Not Reference Rules
**Current State:** Tasks say "implement X" without referencing applicable rules.

**Opportunity:** Each task includes applicable constraints:
```markdown
- [ ] Implement auth endpoint
  - Constraint: TypeScript strict mode (CLAUDE.md)
  - Constraint: PKCE flow for auth (CLAUDE.md)
  - Validation: Run mypy --strict before commit
```

### Gap 4: No Pre-Execution Rule Display
**Current State:** Agent starts coding without seeing active constraints.

**Opportunity:** SessionStart hook displays constraints:
```
════════════════════════════════════════════════════════════
📋 PROJECT CONSTRAINTS ACTIVE (from CLAUDE.md)
════════════════════════════════════════════════════════════
☑ TypeScript strict mode
☑ 80% test coverage minimum
☑ No 'any' types without TODO
☑ TDD cycle required for all source files
════════════════════════════════════════════════════════════
Acknowledge? [yes/no]
```

### Gap 5: Evidence Does Not Track Constraint Compliance
**Current State:** Evidence stores test results but not rule compliance.

**Opportunity:** Add `constraint_validation.json` to evidence:
```json
{
  "claude_md_validated": true,
  "constraints_applied": ["strict_mode", "tdd", "no_any_types"],
  "violations_detected": [],
  "validated_at": "2026-01-13T10:30:00Z"
}
```

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ACTIVE DOCUMENTATION FLOW                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  CLAUDE.md                                                          │
│     │                                                                │
│     ▼                                                                │
│  ┌─────────────────────────┐                                        │
│  │ Constraint Reader       │ ← NEW: Extract structured rules        │
│  │ (claude_md_reader.py)   │                                        │
│  └─────────────────────────┘                                        │
│     │                                                                │
│     ▼                                                                │
│  ┌─────────────────────────┐                                        │
│  │ /specify (modified)     │ ← MODIFIED: Embed rules in spec        │
│  └─────────────────────────┘                                        │
│     │                                                                │
│     ▼                                                                │
│  ┌─────────────────────────┐                                        │
│  │ specify.md              │ ← CONTAINS: User reqs + Project rules  │
│  └─────────────────────────┘                                        │
│     │                                                                │
│     ▼                                                                │
│  ┌─────────────────────────┐                                        │
│  │ /plan (modified)        │ ← MODIFIED: Reference rules per task   │
│  └─────────────────────────┘                                        │
│     │                                                                │
│     ▼                                                                │
│  ┌─────────────────────────┐                                        │
│  │ plan.md                 │ ← CONTAINS: Tasks with rule refs       │
│  └─────────────────────────┘                                        │
│     │                                                                │
│     ▼                                                                │
│  ┌─────────────────────────┐                                        │
│  │ /exec                   │ ← MODIFIED: Validate against rules     │
│  └─────────────────────────┘                                        │
│     │                                                                │
│     ▼                                                                │
│  ┌─────────────────────────┐                                        │
│  │ Evidence                │ ← EXTENDED: Track constraint compliance│
│  └─────────────────────────┘                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| **HIGH** | Constraint Reader Module | 2-3 hours | Enables all downstream improvements |
| **HIGH** | `/specify` modification | 1-2 hours | Rules enter the workflow |
| **HIGH** | SessionStart constraint display | 1 hour | Agent sees rules before coding |
| **MEDIUM** | `/plan` modification | 2-3 hours | Tasks reference applicable rules |
| **MEDIUM** | Evidence tracking | 1-2 hours | Compliance becomes visible |
| **LOW** | DOCUMENTED_CONSTRAINTS.md (optional) | 1 hour | Centralized constraint overrides |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CLAUDE.md parsing fragility | High | Use structured sections with delimiters |
| Agent ignores embedded rules | Medium | Add PreToolUse validation hook |
| Performance overhead | Low | Cache parsed constraints |
| Project-specific override complexity | Medium | Simple override file, not hierarchy |

---

## Proposed Solutions Evaluation

**Quick Fix (Pre-execution reminder):**
- Pros: Low effort, immediate visibility
- Cons: Passive, agent can ignore, not traceable
- Verdict: Useful as supplementary, not sufficient

**Medium Fix (Embed in artifacts):**
- Pros: Rules travel with work, traceable, enforceable
- Cons: Requires modifying `/specify` and `/plan`
- Verdict: **Correct approach** - this is the right architecture

**DOCUMENTED_CONSTRAINTS.md:**
- Pros: Single source of truth, centralized overrides
- Cons: Another file to maintain, duplication with CLAUDE.md
- Verdict: Optional optimization, not required for core fix

---

## Conclusion

The CWO12 workflow is architecturally sound but missing the **documentation-to-execution bridge**.

**What You Actually Need:**

1. **Constraint Reader** - Parse CLAUDE.md into structured rules
2. **Modified `/specify`** - Embed rules in specification
3. **Modified `/plan`** - Reference rules in tasks
4. **SessionStart Hook** - Display constraints before execution
5. **Evidence Extension** - Track constraint validation

**Time Estimate:** 8-12 hours for complete implementation

**Value:** Prevents the "Agent read CLAUDE.md once, then forgot" problem.
