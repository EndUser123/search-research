# Review Bundle: /diagnose Skill
**Generated**: 2026-03-26T19:30:00Z
**Scope**: P:/.claude/skills/diagnose/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: diagnose
- **Description**: Structured diagnostic protocol with hypothesis testing
- **Category**: debugging
- **Trigger**: /diagnose

### Domain & Purpose
Enforces systematic hypothesis testing when investigating issues. Structured Diagnostic Protocol with 3+ hypotheses upfront, systematic testing, and documented diagnostic path.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown
- **Key Integration**: AID bug hunting, /debug

---

## 2. AID INTEGRATION (v1.1.0)

Bug hunting assistance via AI Distiller:

```bash
aid <path> --ai-action prompt-for-bug-hunting
```

**AID `prompt-for-bug-hunting` provides:**
- Quality Analysis: Code quality issues that may indicate bugs
- Edge Case Detection: Boundary conditions, null handling, error paths
- Logical Inconsistencies: Contradictory logic, unreachable code
- Resource Management: Memory leaks, file handle leaks, connection leaks
- Concurrency Issues: Race conditions, deadlocks, thread safety

---

## 3. STRUCTURED DIAGNOSTIC PROTOCOL

1. **List all hypotheses upfront** (minimum 3)
2. **For EACH hypothesis**: design disconfirming test → run test → mark RULED OUT/CONFIRMED
3. **Only proceed** when all but one ruled out OR one confirmed
4. **Document** the diagnostic path

---

## 4. TEMPLATE

```markdown
## Diagnostic Investigation

**Issue**: [brief problem description]

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

## 5. PROTOCOL ENFORCEMENT

This skill REQUIRES:
- [ ] **3+ hypotheses listed** before any testing begins
- [ ] **Each hypothesis has test command** with exact syntax
- [ ] **Each hypothesis has result** with actual output (not "should work")
- [ ] **Each hypothesis marked** RULED OUT or CONFIRMED
- [ ] **Conclusion explicitly states** which hypothesis won
- [ ] **Next step proposed** ONLY after conclusion reached

---

## 6. PROHIBITED BEHAVIORS

DO NOT:
- Jump to solution before listing all hypotheses
- Test only one hypothesis (need 3+)
- Claim "probably" or "likely" without test output
- Skip documenting the diagnostic path
- Accept first plausible explanation

---

## 7. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | EXCELLENT | 196-line SKILL.md with examples |
| Diagnostic Protocol | EXCELLENT | Systematic hypothesis testing |

### SQA Relevance
- **HIGH** — Diagnosis/debugging skill
- Enforces systematic hypothesis testing
- AID integration for bug hunting
- Prevents premature conclusions
- Documents diagnostic path
