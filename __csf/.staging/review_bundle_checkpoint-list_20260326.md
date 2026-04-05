# Review Bundle: /checkpoint-list Skill
**Generated**: 2026-03-26T19:15:00Z
**Scope**: P:/.claude/skills/checkpoint-list/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: checkpoint_list
- **Description**: List/cleanup/validate checkpoints
- **Category**: utility
- **Trigger**: `/checkpoint-list`
- **Aliases**: `/checkpoint-list`

### Domain & Purpose
List all checkpoints with age, commit, and metadata. Supports cleanup and validation modes.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown
- **Key Integration**: Checkpoint management suite

---

## 2. WORKFLOW

1. Scan `P:/.claude/checkpoints/` directory for checkpoint files
2. Read metadata from each checkpoint
3. Calculate age based on timestamp
4. Display list with age, commit info, and metadata
5. If `--cleanup` flag: remove old/invalid checkpoints
6. If `--validate` flag: verify checkpoint integrity

---

## 3. USAGE

```bash
/checkpoint-list
/checkpoint-list --cleanup
/checkpoint-list --validate
```

---

## 4. VALIDATION RULES

### Prohibited Actions
- Do NOT list checkpoints without reading directory
- Do NOT assume checkpoint format without verification

---

## 5. RELATED SKILLS

- `/checkpoint` — Core checkpoint management
- `/checkpoint-restore` — Restore deleted checkpoint
- `/checkpoint-diff` — Compare two checkpoints
- `/checkpoint-delete` — Safely delete checkpoint

---

## 6. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 65-line SKILL.md |
| Safety | GOOD | Evidence-first approach |

### SQA Relevance
- **LOW** — Utility skill for checkpoint management
- Not directly related to quality assurance
