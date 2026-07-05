#!/usr/bin/env python3
"""
Command Intent Validation Gate v1.1

Validates that Claude's bash commands match user intent when executing slash commands.

PROBLEM SOLVED:
- User says: /ask-cli4 "review the plan"
- Claude executes: python ask_cli.py "..." --qwen-only  ← UNAUTHORIZED RESTRICTION
- This gate blocks commands that deviate from user intent

FLOW:
1. UserPromptSubmit stores {skill, prompt} when slash command detected
2. This PreToolUse hook reads state when Bash tool is about to execute
3. Validates that any restrictive flags are justified by user's prompt
4. Returns permissionDecision: allow/deny

ARCHITECTURE (v1.2 - multi-terminal safe):
- State file: P:/.claude/hooks/state/pending_command_intent_{terminal_id}_{session_id}.json
- Session ID: Parent PID (CC process) for consistency across hook invocations
- Terminal ID: Environment variable or detected terminal identifier
- Set by: UserPromptSubmit_router.py (_store_command_intent)
- Consumed by: This hook and PreToolUse.py
- TTL: 5 minutes, auto-cleanup of stale files

FAIL-SAFE BEHAVIOR:
- Missing state file → Allow (no slash command active)
- Expired state → Allow (cleaned up automatically)
- psutil unavailable → Falls back to os.getppid() → os.getpid()

CONTRACT NOTE (2026-07-05, FM-5): Under per-turn intent semantics
(STATE-01 + Change 1), the skill-guard UPS hook clears pending_command_intent
at the first non-slash single-line UserPromptSubmit. This gate's restriction-
validation window therefore ends at that same boundary: any user follow-up
disarms this gate as well as the skill-first gate. Accepted widening of the
existing fail-open (missing-file → Allow) — NOT a regression. Migrating this
gate to skill_execution_state would not restore the restriction window,
because skill_execution_state answers "did Skill() fire" (the model's act),
not "what did the user just intend" (this gate's signal).
"""



# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

