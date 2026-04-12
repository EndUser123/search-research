# Problem Statement: Agentic CLI Skills Lack File Output Mechanism

## Context

9 skills invoke external agentic CLIs. Each skill documents CLI invocation in Section 9 but has no defined mechanism to save output to disk.

## Current Behavior

CLI output goes to stdout/JSONL stream. The orchestrating skill receives raw output in context rather than a saved file. User sees internal reasoning steps instead of the final deliverable.

## Desired Behavior

Running a skill produces a saved file at a user-specified path, with no intermediate steps shown.

## Affected Skills (9)

- `P:/.claude/skills/ai-oc-glm51/SKILL.md`
- `P:/.claude/skills/ai-oc-kimi/SKILL.md`
- `P:/.claude/skills/ai-oc-m27/SKILL.md`
- `P:/.claude/skills/ai-oc-nvidia-ds-v32/SKILL.md`
- `P:/.claude/skills/ai-oc-nvidia-gemma/SKILL.md`
- `P:/.claude/skills/ai-oc-terminus/SKILL.md`
- `P:/.claude/skills/ai-copilot/SKILL.md`
- `P:/.claude/skills/ai-gemini/SKILL.md`
- `P:/.claude/skills/ai-vibe/SKILL.md`

## Root Cause

OpenCode has no `--output` flag. Shell redirection (`>`) is the basic mechanism but varies by CLI. No unified wrapper exists to handle per-CLI differences and verify writes.

## Proposed Solution: Unified Wrapper Script

**Location:** `P:/.claude/bin/agentic-cli.ps1`

The wrapper handles:
- CLI-specific invocation differences
- Output redirection to user-specified path
- Write verification
- Returns path-only to Claude Code (token-efficient)

## Implementation Steps

1. Create `P:/.claude/bin/agentic-cli.ps1`
2. Test with one CLI (OpenCode — most common)
3. Update all 9 skills' Section 9 with wrapper invocation
4. Verify write success per invocation
