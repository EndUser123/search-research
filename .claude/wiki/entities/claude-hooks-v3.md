---
title: "Claude Code Hooks Guide v3.0"
version: "3.0"
date: "2026-04"
source: "P:/.claude/docs/claude-hooks-v3.0.md"
sha256: "b3a78ce8b6159d0f714f86bc3d9f72f65b6dc235744feb10dce006af98d296dd"
summary: "Comprehensive reference for Claude Code hooks v3.0 (2.1.89+): 27 hook events, 4 hook types, registration patterns, protocol schemas, exit codes, async hooks, and testing protocols."
tags:
  - claude-code
  - hooks
  - reference
  - automation
  - csf
---

# Claude Code Hooks Guide v3.0

**v3.0 | April 2026 | 2.1.89+ | Reference**

## Overview

Hooks are deterministic automation points firing at lifecycle phases. They provide hard control flow independent of LLM decisions — blocking actions, injecting context, logging activity, enforcing rules.

## Key Changes from v2.1.15

| Aspect | v2.1.15 | v3.0 |
|--------|----------|------|
| Hook events | 16 | **27** |
| Hook types | command, prompt | **command, prompt, http, agent** |
| Config locations | 5 | **6** (+ skill/agent frontmatter) |
| PreToolUse decisions | deny, ask, allow | **deny, ask, allow, defer** |
| New schema fields | hookSpecificOutput | **continue, stopReason, suppressOutput, systemMessage** |

## 27 Hook Events

**Session/tool**: `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`, `SubagentStart`, `SubagentStop`

**Async/monitoring**: `Stop`, `StopFailure`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `InstructionsLoaded`, `Notification`

**Worktree**: `ConfigChange`, `CwdChanged`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`

**Elicitation**: `Elicitation`, `ElicitationResult`

**Compaction**: `PreCompact`, `PostCompact`

## Blocking Phases

Can prevent action: `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `Stop`, `StopFailure`, `SubagentStop`, `TeammateIdle`, `TaskCreated`, `WorktreeCreate`

## Hook Types

- **command**: Subprocess script (JSON via stdin, exit codes 0/2)
- **prompt**: Inject text into prompt context
- **http**: HTTP webhook (POST with JSON body)
- **agent**: Agent subprocess with hook-specific instructions

## Registration

Hooks are configured in `settings.json` under `hooks.<phase>` as an array of matcher/hooks entries.

## Output Format

| Phase | Output |
|-------|--------|
| PreToolUse | `{"continue": bool, "reason": "..."}` |
| Stop | `{"continue": bool, "stopReason": "..."}` |
| PostToolUse | `{"warning": "..."}` or `{}` |
| UserPromptSubmit | Raw text (injected into context) |

## Exit Codes

- **Exit 0**: Allow/pass-through
- **Exit 2**: Block (PreToolUse, Stop, PermissionRequest)

## Sections

1. Core Hook Concepts
2. Hook Lifecycle & Phases
3. Hook Protocol & Schemas
4. Matcher Syntax & Patterns
5. State Management Patterns
6. Hook Registration & Configuration
7. Configuration Scopes & Locations
8. Output Format Specifications
9. Exit Code Behavior & Control Flow
10. Prompt-Based Hooks
11. HTTP and Agent Hooks
12. Async Hooks
13. Common Failure Modes & Recovery
14. Testing & Validation Protocol
15. Advanced Patterns & Strategies
16. Implementation Checklist
17. Complete Code Examples

## Related

[[claude-hooks-conceptual]]@refines
[[hook-architecture]]@refines
[[hooks-operational-guide]]@refines
