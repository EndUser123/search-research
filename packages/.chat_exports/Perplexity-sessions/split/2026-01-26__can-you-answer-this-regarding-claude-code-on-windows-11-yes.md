---
title: "Can you answer this regarding Claude Code on Windows 11?
Yes, PostToolUse is a valid event type - it's in the lifecycle "
date: "2026-01-26"
mode: "COPILOT"
uuid: "1b7f96fa-4978-430f-9f28-f4367a456514"
entry_count: 4
---

## Human

Can you answer this regarding Claude Code on Windows 11?
Yes, PostToolUse is a valid event type - it's in the lifecycle table in both documents I just read.
The question is whether type: "prompt" works with PostToolUse specifically. The docs listed supported events for prompt hooks as: Stop, SubagentStop, UserPromptSubmit, PreToolUse, PermissionRequest.
But I haven't verified whether that list is exhaustive or just examples. Let me check if there are existing prompt-type hooks in your settings.json for PostToolUse:
read_file
Request
{
  `path`: `P:\\.claude\\settings.json`,
  `length`: 200,
  `offset`: 270
}
Response
[Reading 200 lines from line 270 (total: 1142 lines, 672 remaining)]

          }
        ]
      },
      {
        "matcher": "^(Write|Edit|MultiEdit)$",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/pretooluse_tdd_gate.py",
            "timeout": 3,
            "layer": "1_tdd_gate",
            "critical": true,
            "description": "TDD phase enforcement - blocks impl writes during AWAITING_RED, test edits during RED_CONFIRMED"
          }
        ]
      },
      {
        "matcher": "^Bash$",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/shell_complexity_gate.py",
            "timeout": 3,
            "layer": "0_shell_complexity",
            "critical": true,
            "description": "CLAUDE.md J.5 - Block complex shell patterns, enforce staging protocol"
          },
          {
            "type": "command",
            "command": "python .claude/hooks/unparseable_command_gate.py",
            "timeout": 2,
            "layer": "0_unparseable_command",
            "critical": true,
            "description": "CLAUDE.md C.1 - Block unparseable arbitrary code execution"
          },
          {
            "type": "command",
            "command": "python .claude/hooks/recursive_failure_detector.py",
            "timeout": 3,
            "layer": "0_catch22_detector",
            "critical": true,
            "description": "CLAUDE.md D.5 - Detect Catch-22 loops, block repeated failures"
          },
          {
            "type": "command",
            "command": "python .claude/hooks/PreToolUse_bash_router.py",
            "timeout": 5,
            "layer": "1_bash_router",
            "critical": true,
            "description": "Consolidated router v2.1: command_intent_gate (inline), explore_gate, background_guard, anti_bleed_gate"
          }
        ]
      },
      {
        "matcher": "^(Read|Glob|Grep|WebFetch)$",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/pre_generation_registry.py",
            "timeout": 1,
            "layer": "2a_registry_context",
            "critical": false,
            "description": "Library-First registry suggestions"
          }
        ]
      },
      {
        "matcher": "^(Write|Edit|MultiEdit|Bash)$",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/path_resolution_orchestrator.py",
            "timeout": 5,
            "layer": "2_path_resolution",
            "critical": true,
            "description": "SERIAL path resolution (plan_redirector -> deny_root_write)"
          },
          {
            "type": "command",
            "command": "python .claude/hooks/semantic_file_router.py",
            "timeout": 2,
            "layer": "2c_semantic_routing",
            "critical": false,
            "description": "Advisory semantic routing (TSK vs /reports)"
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "echo",
            "timeout": 1,
            "layer": "99_disler_observability_DISABLED",
            "critical": false,
            "description": "DISABLED: observability server not running"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "^(Write|Edit|MultiEdit|Update)$",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/PostToolUse_file_lock.py",
            "timeout": 2,
            "layer": "00_file_lock_release",
            "critical": false,
            "description": "Release file lock after write operation completes"
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/error_explanation_gate.py",
            "timeout": 3,
            "layer": "0_error_explanation_gate",
            "critical": true,
            "description": "CLAUDE.md D.6 - Block error explanations without verification (pattern-matching prevention)"
          }
        ]
      },
      {
        "matcher": "^(Write|Edit|MultiEdit|NotebookEdit)$",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/PostToolUse_artifact_tracker.py",
            "timeout": 2,
            "layer": "0_artifact_file_tracker",
            "critical": false,
            "description": "Track file changes for artifact tracking"
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/PostToolUse_router.py",
            "timeout": 2,
            "layer": "0_all_router",
            "critical": true,
            "description": "In-process router v2.0: FixValidator, ChangeVerification, FalsificationAssessor, SemanticCompress"
          },
          {
            "type": "command",
            "command": "python .claude/hooks/PostToolUse_system2.py",
            "timeout": 3,
            "layer": "0_system2_debug",
            "critical": false,
            "description": "System 2 debugging - error classification and severity analysis"
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/failure_recorder.py",
            "timeout": 3,
            "layer": "0_failure_recorder",
            "critical": true,
            "description": "Catch-22 companion - Record tool failures for recursive failure detection"
          }
        ]
      },
      {
        "matcher": "^(Write|Edit|MultiEdit|Bash)$",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/post_tool_use_change_propagation.py",
            "timeout": 3,
            "layer": "0_change_propagation",
            "critical": false,
            "description": "Change Propagation - enforce cache clear after structural changes"
          }
        ]
      },
      {
        "matcher": "^(TodoWrite|Skill)$",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/PostToolUse_artifact_taskmaster_sync.py",
            "timeout": 3,
            "layer": "0_artifact_taskmaster_sync",
            "critical": false,
            "description": "Sync artifact tracking from TaskMaster completions"
          }
        ]
All your current PostToolUse hooks use type: "command". I don't see any type: "prompt" examples for PostToolUse in your config.
The simplest way to verify if prompt-type works with PostToolUse is to just test it - add one and see if Claude Code accepts it. Or check the Claude Code source/changelog for definitive answer.
Do you want me to test it, or do you have information on whether it's supported?

## Assistant

I appreciate the detailed context, but I need to clarify what you're asking for here.

You've provided:
1. Your own analysis from reading Claude Code documentation
2. A configuration excerpt from your settings.json showing PostToolUse hooks (all using `type: "command"`)
3. A question about whether `type: "prompt"` works with PostToolUse events

This appears to be **asking me to verify or research Claude Code's official hook system behavior**, rather than asking me to analyze information you've already gathered.

Before I proceed with research, I need to understand your actual goal:

**Are you asking me to:**

1. **Research the Claude Code documentation** to definitively answer whether `type: "prompt"` is supported for PostToolUse events (and provide authoritative sources)?

2. **Help you design a test** to validate this locally in your own Claude Code environment?

3. **Analyze your current hook architecture** and recommend whether adding a prompt-type hook to PostToolUse would fit your workflow?

4. **Something else entirely**?

The distinction matters because:
- Option 1 requires web research for official Claude documentation
- Option 2 is about experimental validation methodology
- Option 3 requires architectural analysis of your existing system
- Each has a very different research/analysis approach

What would be most valuable for you right now?

## Human

1

## Assistant

**No, `type: "prompt"` hooks are not supported for PostToolUse events in Claude Code.**[1][2]

## Official Documentation
Claude Code's reference docs explicitly state that prompt-based hooks (`type: "prompt"`) are **currently only supported for** `Stop` and `SubagentStop` events, where they enable LLM-driven decisions like whether to continue working.  This restriction exists because prompt hooks query an LLM (Haiku) for structured JSON decisions, which fits decision points but not post-execution feedback like PostToolUse.[2][1]

PostToolUse hooks appear in numerous config examples across docs and tutorials, but **all use `type: "command"` exclusively**—for tasks like file locking, artifact tracking, error gating, and formatting.[3][4][5][6][1]

## Hook Type Support
| Hook Event       | `type: "command"` | `type: "prompt"` | Primary Use Case                  |
|------------------|-------------------|------------------|-----------------------------------|
| PostToolUse     | ✅ Supported     | ❌ Not supported| Post-tool cleanup/validation     | [1]
| PreToolUse      | ✅ Supported     | Limited         | Pre-tool permissions             | [1]
| Stop            | ✅ Supported     | ✅ Supported    | Decide if Claude should stop     | [1]
| SubagentStop    | ✅ Supported     | ✅ Supported    | Subagent completion evaluation   | [1]
| UserPromptSubmit| ✅ Supported     | ✅ (listed)     | Prompt validation/context injection | [1][2]

Your config matches this pattern—all PostToolUse hooks are `command`-type for orchestration (e.g., `PostToolUse_router.py`, `failure_recorder.py`).  Adding a `prompt` type would likely be ignored or cause config validation errors.[3][1]

## Alternatives for PostToolUse
Use `command` hooks with embedded LLM calls if needed (e.g., `python script.py` piping JSON to a local/fast model). All documented PostToolUse examples follow this.  Test via `/hooks` UI or direct settings.json edit to confirm.[4][6][3]

## Human

What are practical examples of PreToolUse hooks

## Assistant

PreToolUse hooks run before tool execution and are the primary gatekeeping mechanism in Claude Code, allowing you to inspect, validate, or block tool calls via exit code 2 (with stderr message shown to Claude).[1][2][3]

## Common Use Cases
These hooks excel at safety, validation, and workflow enforcement.[4][5][1]
- Block dangerous shell commands (e.g., `rm -rf`, complex Bash patterns).
- Prevent edits/writes on protected branches or paths.
- Validate tool parameters (e.g., file paths, permissions).
- Enforce TDD phases or complexity limits.
- Route or log tool intents for observability.

## Practical Examples
| Matcher/Tool | Hook Command Example | Purpose | Exit Behavior |
|--------------|----------------------|---------|---------------|
| `"Bash"` | `jq -r '"\\(.tool_input.command) - \\(.tool_input.description)"' >> ~/.claude/bash-log.txt` [1] | Log all Bash commands | Non-blocking (exit 0) |
| `"Write\|Edit\|MultiEdit"` | `[ "$(git branch --show-current)" != "main" ] || { echo '{"block": true, "message": "Cannot edit on main"}' >&2; exit 2; }` [5] | Block writes on main branch | Blocks on main (exit 2) |
| `".*"` or `"Bash"` | `python .claude/hooks/shell_complexity_gate.py` [6] | Block complex/unsafe shell patterns | Blocks unsafe (exit 2) |
| `"Write\|Edit"` | `~/bin/pre_tool_call.rb` (checks paths, lints content) [7] | Path validation & pre-lint | Blocks invalid paths |
| `"mcp__github__create_pull_request"` | `./.claude/hooks/pre-pr-requires-tests.sh` [4] | Require tests before PR | Blocks missing tests |

All examples use `type: "command"` in `~/.claude/settings.json` or `.claude/settings.json`.  Timeouts (1-5s) prevent hangs; `critical: true` ensures blocking on failure.  Your existing PreToolUse hooks (TDD gate, shell gates) align perfectly with these patterns.[2][5][6][1][4]

## Human

find official documentation about "type":"prompt"

## Assistant

## Official Finding: `type: "prompt"` Hook Support

The **official Claude Code documentation explicitly states that prompt-based hooks (`type: "prompt"`) are currently only supported for `Stop` and `SubagentStop` events.**[1]

### Exact Documentation Quote

From the "Prompt-Based Hooks" section:

> "Prompt-based hooks are currently only supported for `Stop` and `SubagentStop` hooks, where they enable intelligent, context-aware decisions."[1]

### Why This Limitation

Prompt hooks query Haiku (fast LLM) for structured JSON decisions (`{"ok": true/false, "reason": "..."}`). This design fits:[1]
- **`Stop`**: Decide if Claude should continue working
- **`SubagentStop`**: Evaluate if subagent completed its task
- **`UserPromptSubmit`**: Listed as "most useful" but NOT officially supported in the schema[1]

PostToolUse isn't supported because it's post-execution feedback—the tool already ran. Prompt-based decisions don't make sense at that stage; command hooks (for cleanup, validation, propagation) are the appropriate model.[1]

### Supported Hook Types by Event

| Event | `type: "command"` | `type: "prompt"` |
|-------|-------------------|------------------|
| PreToolUse | ✅ | ❌ |
| PermissionRequest | ✅ | ❌ |
| PostToolUse | ✅ | ❌ |
| UserPromptSubmit | ✅ | ❌ (despite being listed as "most useful") |
| **Stop** | ✅ | **✅ Supported** [1] |
| **SubagentStop** | ✅ | **✅ Supported** [1] |
| Notification | ✅ | ❌ |
| Setup | ✅ | ❌ |
| SessionStart | ✅ | ❌ |
| SessionEnd | ✅ | ❌ |

Your config is correct—all PostToolUse hooks use `type: "command"`. Testing a `"prompt"` type would either be ignored or produce a configuration error.[1]
