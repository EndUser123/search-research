# Review Bundle: /checkpoint-diff Skill
**Generated**: 2026-03-26T19:15:00Z
**Scope**: P:/.claude/skills/checkpoint-diff/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: checkpoint_diff
- **Description**: Compare two checkpoints with commits, files, and metadata
- **Category**: utility
- **Trigger**: `/checkpoint-diff`
- **Aliases**: `/checkpoint-diff`

### Domain & Purpose
Compare two checkpoints showing commits, files, and metadata changes.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown
- **Key Integration**: Checkpoints stored in `P:/.claude/checkpoints/`

---

## 2. WORKFLOW

1. Identify two checkpoints to compare
2. Read metadata from both checkpoint files
3. Extract commits with change detection
4. Compare file counts and modified file lists
5. Display structured diff showing commits, types, messages, files

---

## 3. OUTPUT SHOWS

- Commits (with change detection)
- Types
- Messages
- Modified files (with count diff)
- Validation checklist

---

## 4. USAGE

```bash
/checkpoint-diff checkpoint1 checkpoint2
/checkpoint-diff --latest manual_20260107_120000
```

---

## 5. VALIDATION RULES

### Prohibited Actions
- Do NOT speculate about differences without reading checkpoint files
- Do NOT assume checkpoint IDs exist without verification

---

## 6. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 71-line SKILL.md |
| Evidence-based | GOOD | Actual differences shown |

### SQA Relevance
- **LOW** — Utility skill for checkpoint comparison
- Not directly related to quality assurance
