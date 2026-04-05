# Review Bundle: /checkpoint-delete Skill
**Generated**: 2026-03-26T18:55:00Z
**Scope**: P:/.claude/skills/checkpoint-delete/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: checkpoint_delete
- **Description**: Safely delete a checkpoint using the trash recovery system
- **Category**: utility
- **Trigger**: `/checkpoint-delete`
- **Aliases**: `/checkpoint-delete`

### Domain & Purpose
Safely delete checkpoints with recovery capability through trash system. Provides safety net before destructive operations.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown
- **Key Integration**: Checkpoint management system

---

## 2. ARCHITECTURE OVERVIEW

```
         ┌─────────────────────────────────────────────┐
         │         /checkpoint-delete                  │
         │   Move checkpoint → trash for recovery       │
         └──────────────────┬──────────────────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    ▼                       ▼                       ▼
┌──────────┐        ┌──────────────┐      ┌──────────────┐
│ Identify  │        │ Verify exists │      │ Move to trash│
│ checkpoint│        │ in .claude/   │      │ ~/.claude/    │
└──────────┘        │ checkpoints/  │      │ trash/       │
                     └──────────────┘      └──────────────┘
```

---

## 3. PROJECT CONTEXT

### Constitution/Constraints
- Follows fail-fast principle - surface issues immediately
- Evidence-first - verify checkpoint exists before deletion
- Solo-dev appropriate - no enterprise-style background services

### Technical Context
- Checkpoints stored in `P:/.claude/checkpoints/`
- Trash recovery in `~/.claude/trash/`
- Metadata preserved for restoration via `/checkpoint-restore`

---

## 4. WORKFLOW

1. Identify checkpoint to delete (ID or pattern)
2. Verify checkpoint exists in checkpoints directory
3. Move checkpoint file to trash recovery directory
4. Preserve metadata for potential restoration
5. Report completion with trash location

---

## 5. VALIDATION RULES

### Prohibited Actions
- Do NOT permanently delete without moving to trash first
- Do NOT bypass trash system
- Do NOT delete checkpoints without user confirmation

---

## 6. USAGE

```
/checkpoint-delete <checkpoint_id>

# Examples:
/checkpoint-delete ckpt_20260107_120000
/checkpoint-delete ckpt_20260107_*
```

---

## 7. RELATED SKILLS

- `/checkpoint-restore` - Restore deleted checkpoint
- `/checkpoint-list` - List all checkpoints

---

## 8. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Error Handling | GOOD | Verification before deletion |
| Documentation | GOOD | 81-line SKILL.md |
| Safety | EXCELLENT | Trash-based deletion |

### SQA Relevance
- **LOW** — Utility skill for checkpoint management
- Not directly related to quality assurance
