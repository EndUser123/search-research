# SKILL PACK: av (Skill Improvement Tool)

**Generated:** 2026-04-23
**Source:** P:/.claude/skills/av/
**Mode:** full (implementation included)

---

## FILE INDEX

| File | Description |
|------|-------------|
| `SKILL.md` | Main skill (46758 bytes) |
| `index.html` | HTML artifact page |
| `pipeline.html` | Pipeline visualization |
| `eval_sets/default.json` | Evaluation set |
| `references/validation-checklist.md` | 6-section validation checklist |
| `references/output-package-and-architecture.md` | Hook package architecture |
| `references/hook-templates.md` | 7 hook generation templates |
| `references/integration-checklist.md` | Integration verification |

---

## av/SKILL.md

### Frontmatter

```yaml
---
name: av
description: Analyze and improve skills - generates complete hook files automatically
version: "1.0.0"
status: stable
category: meta
triggers:
  - /av
aliases:
  - /av
  - /improve-skill
suggest:
  - /hooks-edit
---
```

### Execution Directive

**When invoked, IMMEDIATELY:**

1. READ `P:/.claude/skills/<skill>/SKILL.md`
2. READ `P:/.claude/docs/claude-hooks-v2.1.15.md` (lines 808-835 for skill hooks)
3. CLASSIFY skill type (EXECUTION / KNOWLEDGE / PROCEDURE)
4. RUN validation checklist (6 sections)
5. ANALYZE complexity for recommendation
6. DETECT hook needs from skill pattern
7. GENERATE packages based on skill type
8. SHOW packages with RECOMMENDATION based on analysis
9. WAIT for user choice
10. WRITE selected package(s)
11. SANITY CHECK (AUTOMATIC)

### Skill Type Classification

| Type | Characteristics | Required Elements |
|------|-----------------|-------------------|
| **EXECUTION** | Runs external tool/CLI, delegates to subagent | Execution directive, anti-substitution block, registry entry |
| **KNOWLEDGE** | Provides reference info, definitions, patterns | Context sections, no execution required |
| **PROCEDURE** | Multi-step workflow with decision points | Steps with success criteria, phase gates |

### Complexity Score Guide

```
Score <= 0  -> SIMPLE mode, no hooks needed
Score 1-3   -> Optional hooks, user preference
Score >= 4  -> HOOKS recommended for reliability
```

**Needs hooks:** /tdd, /rca, /deploy, /v (multi-phase, state, enforcement)
**No hooks needed:** /standards, /explain, /brainstorm, /summarize (knowledge, simple)

### Validation Checklist (Sections 0-F)

| Section | Focus | Key Checks |
|---------|-------|------------|
| 0 | Skill Type | EXECUTION / KNOWLEDGE / PROCEDURE classification |
| A | Execution Directive | First 30 lines, full paths, anti-substitution block |
| B | Structure | Prose:Code <= 2:1, quick reference table, error handling |
| C | Evidence | No excuse patterns, no temporal hedging |
| D | Hook Detection | File ops -> validator, multi-phase -> transitions |
| E | Execution Registry | EXECUTION skills must register |
| F | Layer 1 Governance | PROCEDURE skills need governance markers |

### Hook Templates (7 total)

| Template | Purpose | When to Use |
|----------|---------|-------------|
| 1: PostToolUse Validator | Validate tool output for errors | File/Bash operations |
| 2: State Manager | Workflow state with expiration | Multi-phase workflows |
| 3: PreToolUse Gate | Block tools not allowed in current phase | Phase enforcement |
| 4: PostToolUse Transition | Advance workflow phase after steps | State transitions |
| 5: Execution Skill SKILL.md | Template for EXECUTION type skills | External tool invocation |
| 6: Knowledge Skill SKILL.md | Template for KNOWLEDGE type skills | Reference/documentation |
| 7: Procedure Skill SKILL.md | Template for PROCEDURE type skills | Multi-step workflows |

### Why Two Skills?

PreToolUse gates CAN check for feature flags, but PostToolUse hooks CANNOT:
- PreToolUse sees tool_input (the command user typed)
- PostToolUse only sees tool_response (result after execution)
- No way for PostToolUse to know if user originally typed --hooks

**Two-skill solution:**
```
P:/.claude/skills/
├── main/              # Simple mode (no hooks)
└── main-hooks/        # Hooks mode (all hooks active)
```

### When NOT to Add Hooks

- KNOWLEDGE skills (reference-only, no execution)
- Simple single-command skills with no state
- Skills where instruction-following is sufficient
- Exploratory/research skills with flexible paths

---

## references/validation-checklist.md

6-section validation checklist:
- Section 0: Skill Type Classification
- Section A: Execution Directive
- Section B: Structure
- Section C: Evidence
- Section D: Hook Detection
- Section E: Execution Registry
- Section F: Layer 1 Governance

---

## references/hook-templates.md

Templates 1-4: Python hook files
Templates 5-7: SKILL.md templates

**Template 1: PostToolUse Validator**
```python
import json, sys
from pathlib import Path

def validate_output(data: dict) -> dict:
    tool_name = data.get("tool_name", "")
    tool_output = data.get("tool_output", "")
    return {}

def main():
    input_data = json.loads(sys.stdin.read())
    result = validate_output(input_data)
    print(json.dumps(result))
    sys.exit(0)
```

**Template 2: State Manager**
```python
from pathlib import Path
import hashlib, json, time

instance_id = hashlib.md5(str(Path.cwd()).encode()).hexdigest()[:8]
STATE_DIR = Path("P:/.claude/hooks/state")
STATE_FILE = STATE_DIR / f"{SKILL_NAME}_{instance_id}.json"
```

**Template 3: PreToolUse Gate** — exit(2) to block, exit(0) to allow

**Template 4: PostToolUse Transition** — advances workflow phase

---

## HOW TO USE THIS PACK

- av is an EXECUTION type skill (generates hook files)
- Complexity scoring: Multi-phase +3, State +3, Enforcement +2, Single -2, Doc -2
- Score >=4 = hooks recommended; Score <=0 = simple mode
- $ARGUMENTS is NOT available in type:command hooks (use stdin JSON parsing)
- Execution skills must register in `StopHook_skill_execution_gate.py`


---

## references/integration-checklist.md

# Integration Checklist & Complete Example

## Complete Example Output

```python
#!/usr/bin/env python3
"""
"""
import json, sys
from pathlib import Path

def validate_output(data: dict) -> dict:
    tool_name = data.get("tool_name", "")
    tool_output = data.get("tool_output", "")

    if tool_name == "Bash":
        if any(err in tool_output.lower() for err in ["error", "failed", "not found"]):
            return {
                "hookSpecificOutput": {
                }
            }

    return {}

def main():
    input_data = json.loads(sys.stdin.read())
    result = validate_output(input_data)
    print(json.dumps(result))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

**COMPLETE, WORKING, READY TO USE.** No manual copying needed.

---

## Integration Checklist (Auto-Generated)

```markdown

## Files Created

## Frontmatter Hooks Registration
- PreToolUse gate blocks Write/Edit during restricted phases
- PostToolUse validator checks Bash command output for errors
- PostToolUse transition advances workflow phases automatically

Hooks use \$CLAUDE_PROJECT_DIR for portable path references.

## Testing Steps
2. Check: Frontmatter hooks load automatically
3. Verify: PreToolUse gate restricts tools by phase
4. Confirm: Validator catches errors
5. Test: Transition advances phases correctly
6. Logs: P:/.claude/logs/hooks.jsonl

## Rollback (if needed)
```bash
# Restore original

# Remove generated hooks
```

## Customization Points
Edit these files to customize validation:
```

---

## Hook Location Convention

**Frontmatter Hooks (recommended for skill-scoped hooks):**
- Hooks defined in SKILL.md frontmatter under `hooks:` key
- Scoped to skill lifecycle - only run when skill is active
- Auto-cleanup when skill completes
- Hook files stored in `.claude/skills/{skill}/hooks/`
- Uses `$CLAUDE_PROJECT_DIR` for portable path references
- Documented in: https://code.claude.com/docs/en/hooks (Hooks in skills and agents)

**Legacy hooks** (still supported):
- Hooks in `.claude/hooks/` root
- Used for cross-cutting concerns (TDD, constitutional enforcement)
- Registered in `~/.claude/settings.json` or `.claude/settings.json`
