# NotebookLM Skill Export

This directory contains NotebookLM skill files in multiple formats.

## Formats Available

### nlm-skill/
- `SKILL.md` - Main skill file for Claude Code, OpenCode, Gemini CLI, Antigravity, Codex
- `references/` - Additional reference documentation

This is the standard skill directory structure used by all automated installations.

### AGENTS_SECTION.md
- Section format for AGENTS.md (copy/paste into your AGENTS.md)

## Installation

### Claude Code
```bash
cp -r nlm-skill ~/.claude/skills/
```

### OpenCode
```bash
cp -r nlm-skill ~/.config/opencode/skills/
```

### Gemini CLI / Codex / Agents (cross-tool compatible)
```bash
cp -r nlm-skill ~/.agents/skills/
```

### Antigravity
```bash
cp -r nlm-skill ~/.gemini/antigravity/skills/
```

Or for project-level installation, copy to:
- Claude Code: `.claude/skills/`
- OpenCode: `.opencode/skills/`
- Gemini CLI / Codex: `.agents/skills/`
- Antigravity: `.agents/skills/`

## Automated Installation

Instead of manual copying, you can use:
```bash
nlm skill install <tool>
```

Where `<tool>` is: claude-code, cursor, agents, opencode, antigravity, cline, openclaw, cc-claw.

> **Note:** `agents` replaces the old `gemini-cli` and `codex` entries. The `.agents/skills/`
> path is the cross-tool compatible alias supported by Gemini CLI (v0.33.1+), Codex, and others.
