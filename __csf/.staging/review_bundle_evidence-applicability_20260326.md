# Review Bundle: /evidence-applicability Skill
**Generated**: 2026-03-26T19:25:00Z
**Scope**: P:/.claude/skills/evidence-applicability/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: evidence-applicability
- **Description**: Evidence must apply to the claim's context, not just support its content
- **Category**: verification
- **Trigger**: 'git show', 'the file says', 'the code does', 'the spec requires', 'documentation states'
- **Aliases**: `/evidence-context`

### Domain & Purpose
Ensures evidence cited for claims actually applies to the claim's context. Real evidence + correct content + wrong context = invalid claim.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown
- **Key Integration**: Truthfulness/constitution enforcement

---

## 2. EVIDENCE ALIGNMENT CHECKS

| Dimension | Question | Mismatch Signals |
|-----------|----------|------------------|
| Temporal | Is this current enough for a present-tense claim? | `git show <old-commit>:`, old logs, cached results |
| Scope | Is this from the same system/branch/project? | Cross-project grep, different repo, other branch |
| Authority | Is this canonical, not draft/deprecated? | "proposed", "draft", "v1" when v2 exists |
| Identity | Is this the actual entity, not similar-named? | Same function name in different module |

---

## 3. RULE

Present-tense claims require present-state evidence. Historical evidence supports "was" claims, not "is" claims.

---

## 4. ANTI-PATTERNS

| Pattern | Problem |
|---------|---------|
| `git show abc123:file` → "The file says..." | Historical commit ≠ current state |
| `grep -r "pattern" P:/` finds match → "Project X has..." | May be different project than discussed |
| Read `docs/draft-spec.md` → "The spec requires..." | Draft ≠ authoritative |
| Found `utils.py:parse()` → "The parse function does..." | May be different parse() than intended |

---

## 5. REQUIRED VERIFICATION

1. Find evidence (git show, grep, read)
2. CHECK: Does this evidence apply to my claim's context?
3. If mismatch: qualify the claim ("In commit X...", "Draft spec says...", "A different module's parse()...")

---

## 6. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 68-line SKILL.md |
| Constitution Alignment | EXCELLENT | Truthfulness enforcement |

### SQA Relevance
- **HIGH** — Verification/constitution enforcement skill
- Ensures evidence context alignment
- Prevents false claims based on misapplied evidence
