# Review Bundle: /artifact-audit Skill
**Generated**: 2026-03-26T19:30:00Z
**Scope**: P:/.claude/skills/artifact-audit/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: artifact-audit
- **Description**: Show pending artifact updates grouped by severity - PRD, ARD, CHANGELOG, README status
- **Category**: tracking
- **Trigger**: /artifact-audit, "artifact audit", "pending documentation"
- **Aliases**: /artifact-audit, /artifacts-audit, /audit-artifacts

### Domain & Purpose
Shows pending artifact updates grouped by severity - PRD, ARD, CHANGELOG, README status.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown + Python
- **Key Integration**: artifact-add, artifact-done, /comply, /build

---

## 2. EXECUTION DIRECTIVE

```bash
python P:/.claude/skills/artifact-audit/resources/scripts/artifact_audit.py --project-root P:/
```

---

## 3. ARTIFACT TYPES

| Type | File Patterns |
|------|---------------|
| changelog | CHANGELOG.md, changelog.md, HISTORY.md |
| prd | PRD.md, prd.md, docs/PRD.md |
| ard | ARD.md, ard.md, docs/ARD.md, docs/architecture.md |
| readme | README.md, readme.md |

---

## 4. STATUS ICONS

| Icon | Meaning |
|------|---------|
| ⏳ | Pending (required) |
| ? | Confirm (optional) |
| ✓ | Done |

---

## 5. ENFORCEMENT TIMELINE

| Severity | Warn | Block |
|----------|------|-------|
| Critical | 5 min | 30 min |
| Standard | 30 min | 2 hours |
| Low | Never | Never |

---

## 6. EXIT CODE

Returns 1 if pending items exist, 0 otherwise.

---

## 7. VALIDATION RULES

### Prohibited Actions
- **NEVER claim clean without scanning** - run actual audit
- **NEVER hide critical items** - always show highest severity first

### Required Output Format
- Group by severity level
- Show item_id and summary
- List each artifact with status icon
- Display enforcement timeline

---

## 8. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 131-line SKILL.md |
| Artifact Tracking | EXCELLENT | Severity-based grouping |

### SQA Relevance
- **MEDIUM** — Artifact verification skill
- Tracks PRD/ARD/CHANGELOG/README status
- Enforces documentation compliance
- Severity-based enforcement timeline
