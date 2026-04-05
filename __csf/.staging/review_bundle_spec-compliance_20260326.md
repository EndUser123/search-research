# Review Bundle: /spec-compliance Skill
**Generated**: 2026-03-26T19:20:00Z
**Scope**: P:/.claude/skills/spec-compliance/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: spec-compliance
- **Description**: Protocol for following specifications exactly and when/how to request deviations
- **Category**: quality
- **Trigger**: 'implement to spec', 'according to spec', 'specification requires', 'design spec', 'architecture doc'
- **Aliases**: `/spec-compliance`

### Domain & Purpose
Ensures explicit specifications (architecture docs, design specs, task requirements) are followed exactly, with proper deviation approval workflow.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown
- **Key Integration**: Constitution-driven enforcement

---

## 2. DEFAULT BEHAVIOR

- FOLLOW specifications exactly
- Implement what was specified, not what seems "better"
- Specifications represent deliberated decisions—don't second-guess without evidence

---

## 3. SPEC DEVIATION WORKFLOW

Before any spec deviation, present:

```
⚠️ SPEC DEVIATION REQUEST

Spec requires: [exact requirement from spec]
I propose: [alternative approach]

Evidence for deviation:
- [Concrete evidence, not assumptions]
- [Actual investigation results]

Risk if spec is correct: [what breaks by not following]
Risk if I'm correct: [what's lost by following spec]

AWAITING APPROVAL before proceeding.
```

---

## 4. INVESTIGATION REQUIREMENT

Before concluding a spec is suboptimal:

1. **READ the full spec** - not just the part being implemented
2. **INVESTIGATE the codebase** - verify assumptions about what exists
3. **IDENTIFY spec rationale** - why might this have been specified?
4. **FIND counter-evidence** - what would prove the spec wrong?

**If investigation not completed → follow spec exactly.**

---

## 5. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 80-line SKILL.md |
| Constitution Alignment | EXCELLENT | Follows spec exactly |

### SQA Relevance
- **MEDIUM** — Quality enforcement skill
- Ensures spec compliance
- Prevents unauthorized deviations
- Supports long-term maintainability
