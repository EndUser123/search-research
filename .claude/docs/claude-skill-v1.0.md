---
name: claude-skill-v1.0
description: Claude Skill Authoring Standard — covers skill anatomy, triggering, runtime isolation, artifact conventions, progressive disclosure, and skill quality standards. Use when creating, reviewing, or improving Claude Code skills.
version: 1.0.0
category: reference
enforcement: strict
audience: skill authors, skill reviewers
---

# Claude Skill Authoring Standard v1.0

Standards for writing production-quality Claude Code skills. Applies to all skills in `.claude/skills/`, `skills/`, and plugin skills under `.claude/plugins/`.

---

## Terminal ID & Artifact Isolation Standard

### What Terminal ID Is

Every Claude Code terminal session gets a unique, stable identifier called `terminal_id`. It's produced by `canonical_terminal_id()` in `core/terminal_id.py` and resolves in priority order:

1. `CLAUDE_TERMINAL_ID` env var — explicit override (used for testing)
2. `WT_SESSION` env var — Windows Terminal's session UUID (the production source on Windows 11)
3. `ConEmuServerPID` env var — fallback for ConEmu terminals
4. `console_unknown` — last resort (should never happen in practice)

The result is always prefixed `console_`, e.g. `console_1c309c3a-1fef-477f-b394-d22cc53057e4`.

### How It's Used for Artifacts

All skill runtime artifacts are written to:

```
{project_root}/.claude/.artifacts/{terminal_id}/{skill_name}/
```

Examples:
- `/refactor` → `.claude/.artifacts/console_abc123/refactor/`
- `/pre-mortem` → `.claude/.artifacts/console_abc123/pre-mortem/`
- `/similarity` → `.claude/.artifacts/console_abc123/similarity/`

**Skills MUST NOT write state to their own directory or the package root.**

### Three Problems It Solves

**1. Multi-terminal isolation.** A solo developer typically has 5-7 terminals open simultaneously, each running different skills. Without `terminal_id` scoping, terminal A's `/refactor` findings would collide with terminal B's `/refactor` findings at the same path. With `terminal_id`, each terminal gets its own artifact subtree — no file locks, no merge conflicts, no cross-contamination.

**2. Immunity to stale data.** Each terminal session gets a fresh UUID from `WT_SESSION`. Old artifacts from previous sessions live in separate `console_{old-uuid}/` directories. Skills never accidentally read stale output from a prior session because the path includes the current session's ID. Old directories can be garbage-collected independently without affecting live work.

**3. Immunity to workflow interruption from compact events.** Claude Code periodically compacts conversation context to stay within the context window. This destroys in-memory state — variables, function results, conversation history. But artifacts written to disk under `.claude/.artifacts/{terminal_id}/` survive compaction. After a compact, the skill can re-read its artifacts from disk and resume where it left off. The `WT_SESSION` value is stable across compactions within the same terminal, so the path remains consistent even when conversation memory is lost.

### Implementation Pattern

```python
import os
from pathlib import Path

def resolve_artifacts_dir(skill_name: str) -> Path:
    # Try canonical resolver first (core.terminal_id package)
    try:
        import core.terminal_id as tid
        terminal_id = tid.canonical_terminal_id()
    except ImportError:
        # Local fallback matching the same priority chain
        terminal_id = (
            os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
            or os.environ.get("WT_SESSION", "").strip()
            or os.environ.get("ConEmuServerPID", "").strip()
        )
        terminal_id = f"console_{terminal_id}" if terminal_id else "console_unknown"

    base = Path.cwd().resolve() / ".claude" / ".artifacts"
    return base / terminal_id / skill_name
```

### Exception: Cross-Terminal Shared State

Not all artifacts should be terminal-isolated. Append-only logs consumed across terminals (e.g., `skill_coverage/` history) use a shared path without `terminal_id` nesting:

```
.claude/.artifacts/skill_coverage/{target_key}.jsonl
```

**Rule:** If the artifact is consumed within the same task (findings, plans, test results), isolate by terminal. If it's a history log consumed across sessions (coverage tracking, changelogs), keep it shared.

---

## Skill Anatomy

### Required File Structure

```
skill-name/
├── SKILL.md              # Required — skill definition
├── scripts/              # Optional — bundled executables
│   └── *.py, *.sh        #   Must be executable without installation
├── references/           # Optional — loaded as needed
│   └── *.md              #   Long docs (>300 lines) go here
├── assets/               # Optional — templates, icons, fonts
└── hooks/                # Optional — skill-private hooks
    └── *.py              #   Registered locally, not globally
```

### SKILL.md Frontmatter

Every skill requires valid YAML frontmatter:

```yaml
---
name: skill-name
description: When to trigger, what it does. Primary triggering mechanism.
version: 0.1.0
category: orchestration|reference|execution|analysis
enforcement: strict|advisory
workflow_steps:           # Only for orchestration skills
  - step1
  - step2
triggers:                 # Explicit user phrases
  - '/skill-name'
  - 'do the thing'
---
```

**Required frontmatter fields:** `name`, `description`
**Optional but expected:** `version`, `category`, `enforcement`, `triggers`

### SKILL.md Body Structure

1. **Purpose** — what the skill does, why it exists (1-2 sentences)
2. **When to Use** — trigger contexts, not trigger phrases (see below)
3. **Workflow** — step-by-step execution guide (numbered steps)
4. **Reference** — detailed docs, tables, examples (progressive disclosure)
5. **Integration** — how it composes with other skills/agents/hooks

### Description vs Triggers

The `description` field is the primary triggering mechanism. It describes **when** to use the skill in concrete context. It should be "pushy" — not just a passive description.

**Good description:**
> "Review code for quality issues, adherence to project standards, and best practices. Make sure to invoke this whenever the user asks to review code, mentions a PR, or says 'check this' — even if they don't use the word 'review'."

**Bad description:**
> "Code review skill."

The `triggers` field lists explicit phrase matches. The `description` field drives contextual triggering via the skill catalog.

### Skill Categories

| Category | When to Use | Example |
|----------|-------------|---------|
| `orchestration` | Coordinates sub-skills or agents | skill-craft, cco |
| `execution` | Runs external commands, CLIs | ai-pcli, research |
| `analysis` | Deep inspection, review | adversarial-review, mcp-agent-analyzer |
| `reference` | Lookup tables, standards | claude-agents-v1.0, claude-mcp-v1.0 |
| `knowledge` | Research, synthesis | /search, /research |

### Progressive Disclosure

Skills use a three-level loading system:

| Level | Trigger | Size Limit |
|-------|---------|------------|
| Metadata | Always in context | ~100 words (name + description) |
| SKILL.md body | Skill triggers | <500 lines ideal |
| Bundled resources | As needed | Unlimited |

When SKILL.md approaches 400 lines, add a "Detailed Reference" section at the bottom with pointers to `references/*.md` files. Load reference files only when the user navigates to them.

---

## Triggering Standards

### Imperative Form for Actions

Instructions in the skill body use **imperative mood** (direct commands), not third-person descriptions:

✅ `Run the validation script and check the output`
❌ `The validation script is run and the output is checked`

### No Third-Person Trigger Phrases

Avoid describing user behavior in third person:

✅ `Runs when the user says '/audit' or asks to review a skill`
❌ `Runs when the user says "I want you to audit this skill"`

### Contextual Triggers in Description

The `description` field should include real-world context cues:

```yaml
description: |
  Analyze a skill for agent architecture gaps, MCP integration
  opportunities, and skill composition patterns. Invoke when:
  - A skill is being reviewed for the first time
  - Skill-craft routes a skill to the Agent Review phase
  - The user asks "should this skill use agents?" or
    "what MCP servers could this skill use?"
  - Adding a new capability to an existing skill
```

---

## Runtime Behavior

### Skill-Private Hooks

Skills may include hooks in a `hooks/` subdirectory. These are registered locally (not globally) and apply only when this skill is active.

**Registration pattern** (in hook file):
```python
# hooks/my_hook.py
def register_local(skill_name: str):
    """Called by skill-craft to register skill-private hooks."""
    # Register with skill-specific path prefix
    pass
```

### Artifact Writing

All runtime artifacts go to `.claude/.artifacts/{terminal_id}/{skill_name}/`. Never write to:
- The skill's own directory
- The package root
- Global `.claude/` directories (except for shared cross-session logs)

### Shell Execution

For skills that run external commands:

1. **Always capture output** — don't assume success
2. **Check exit codes** — non-zero means failure
3. **Timeout long operations** — default 120s, configurable
4. **Report individual failures** — don't fail silently if parallel tasks have mixed results

### Error Handling

| Error Type | Response |
|------------|----------|
| CLI not found | Report clearly, suggest installation |
| Auth failure | Run login automatically, report if it fails again |
| Rate limit | Wait with backoff, report if still failing after 3 attempts |
| Network timeout | Retry once, then report failure with what was attempted |

**Never silently swallow errors.** Report what happened and what the user can do about it.

---

## Quality Standards

### SKILL.md Line Count

- **Ideal:** <350 lines
- **Warning:** 350-450 lines (add progressive disclosure)
- **Hard limit:** 500 lines (certification gate will fail above this)

If approaching 400 lines, refactor to move detailed reference material to `references/` files.

### Naming Conventions

- Skill names: `kebab-case` (e.g., `skill-craft`, `doc-to-skill`)
- Agent names: `kebab-case` in file names, `camelCase` in `name:` field
- Hook names: `snake_case` (e.g., `stop_router.py`)
- Script names: `snake_case` for Python, `kebab-case` for shell

### Documentation Quality

Every skill should include:
1. **One real usage example** — actual input, expected output
2. **Output format specification** — what does success look like?
3. **Error state specification** — what does failure look like?
4. **Integration points** — what other skills/hooks/agents does it compose with?

---

## Skill Review Checklist

Before declaring a skill ready for production:

- [ ] SKILL.md has valid YAML frontmatter (name, description required)
- [ ] Description uses imperative mood, not third-person description
- [ ] All `triggers:` phrases are tested (skill actually fires on them)
- [ ] SKILL.md body is under 500 lines
- [ ] Reference files exist for any section over 300 lines
- [ ] All bundled scripts are executable and tested
- [ ] Artifact paths use `{terminal_id}/{skill_name}/` isolation
- [ ] Error states are documented (what can go wrong, how to recover)
- [ ] Integration points are documented (what skills/agents/hooks it calls)
- [ ] At least one real usage example in the body

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-21 | Initial standard — terminal_id isolation, artifact conventions, skill anatomy, progressive disclosure, triggering standards |