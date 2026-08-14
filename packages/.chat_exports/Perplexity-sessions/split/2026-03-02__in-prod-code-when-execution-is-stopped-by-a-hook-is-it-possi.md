---
title: "In prod code, when execution is stopped by a hook, is it possible to show which hook blocked the execution, especially i"
date: "2026-03-02"
mode: "COPILOT"
uuid: "ed31b4d0-906c-47eb-80cd-e80121440387"
entry_count: 5
---

## Human

In prod code, when execution is stopped by a hook, is it possible to show which hook blocked the execution, especially if we're using a router?

## Assistant

Yes, but you have to implement it yourself: the platform doesn’t currently surface “which hook blocked” out of the box, even with routers.[1][2][3]

### What the platform gives you

- A non‑zero/2 exit code means “blocked”, but the UI/logging only shows that the *event* was blocked, not the specific hook or router branch.[3][4]
- Feature requests are open to distinguish intentional blocks from errors, which implies there’s no native per‑hook attribution yet.[2][1]

### Pattern: make the blocking hook self‑identifying

In prod, the simplest reliable approach is: every hook that might block must include its own identifier in stderr or JSON, and your router must preserve that.

1. **In the leaf hook** (command/script/TS hook), always emit an ID when you block:  
   - Stderr only pattern:  
     - `echo "BLOCKED by stop_tests_hook (Stop/Router:quality-gates)" >&2` then `exit 2`.[5][4]
   - JSON pattern (for events that read JSON on exit 0):  
     - `{ "decision": "block", "reason": "Blocked by stop_tests_hook: tests failing" }` with exit 0, or whatever the event supports.[4][3]

2. **In your router hook**, do not overwrite that information:  
   - If the router *delegates* to sub‑hooks (e.g., calls them as subprocesses), propagate their stderr and exit code unchanged so Claude sees `exit 2 + "BLOCKED by …"` from the leaf hook.  
   - If the router *aggregates* multiple hooks, have each sub‑hook return a structured payload (e.g., JSON) that includes `"blocking_hook_id"`; the router picks the highest‑priority block and forwards that ID in its own stderr/JSON.  

### Concrete router strategy

- Give every hook a stable **hook_id** (e.g., `"pretooluse.block_destructive"`, `"stop.tests_gate"`).  
- Have each hook that can block emit: `BLOCKED: <hook_id> – <human_reason>` on stderr when it returns exit 2.[5][4]
- In a router that chooses between multiple hooks:  
  - Run children, collect their outputs.  
  - If any child wants to block, select one and re‑emit `BLOCKED: <child_hook_id> …` from the router with exit 2.  

This way, when prod execution stops, the message shown to Claude/you explicitly tells you which hook and (optionally) which router branch caused the block, even though the core system doesn’t track that for you.[3][4][5]

## Human

How to configure router hooks to output blocking reason

## Assistant

Configure router hooks by defining a single "router" command hook in your `.claude/settings.json` that delegates to child hooks based on input JSON, then propagates the first blocking reason and exit code unchanged. This preserves the leaf hook's stderr message (e.g., "BLOCKED by tests_hook") so Claude sees exactly which sub-hook blocked execution.[1][2]

### Router config pattern

Add this to your settings under the target event (e.g., `"Stop"` or `"PreToolUse"`):

```
"hooks": {
  "Stop": [  // or your event
    {
      "matcher": "*",  // or specific like "Bash"
      "hooks": [
        {
          "type": "command",
          "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/router.sh"
        }
      ]
    }
  ]
}
```

Hooks run in parallel by default, but routers are serial single-command hooks that *internally* call children sequentially or conditionally.[2]

### Router script template

Save as `.claude/hooks/router.sh` (chmod +x it). It reads stdin JSON, routes to child scripts, and forwards the block:

```bash
#!/bin/bash
INPUT=$(cat)  # Full event JSON on stdin

# Parse common fields for routing
EVENT_NAME=$(echo "$INPUT" | jq -r '.hook_event_name')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')

# Route logic: call children based on conditions
# Example: tests first (highest priority), then secrets, then linter
run_hook() {
  local hook_name=$1
  local hook_path=".claude/hooks/${hook_name}.sh"
  if [[ -x "$hook_path" ]]; then
    echo "$INPUT" | "$hook_path"  # Pass full JSON to child
    local child_exit=$?
    if [[ $child_exit == 2 ]]; then
      # Propagate child's stderr + exit 2 (Claude sees child's block message)
      return 2
    fi
  fi
}

# Run in priority order; first block wins
run_hook "tests_guard"     || exit 2
run_hook "secrets_scan"    || exit 2
run_hook "linter_check"    || exit 2

# No blocks: allow
exit 0
```

Child hooks (e.g., `.claude/hooks/tests_guard.sh`) self-identify on block:

```bash
#!/bin/bash
INPUT=$(cat)
# Your logic...
if ! tests_pass; then
  echo "BLOCKED by tests_guard: 3/12 tests failing (session: $SESSION_ID)" >&2
  exit 2  # Router propagates this stderr + exit
fi
exit 0
```

### Why this works for prod + routers

- **Native parallelism**: Only one "router" hook matches/runs per event; internals handle sequencing.[2]
- **Block propagation**: Child's stderr goes to Claude verbatim on exit 2 (no overwrite).[1][2]
- **No infinite loops**: Check `stop_hook_active: true` in Stop routers.[3]
- **Debug**: Ctrl+O shows full stderr; `claude --debug` logs matcher/hook execution.[1]

Test: Pipe sample JSON to `./router.sh` and check `echo $?` + stderr. Scale by adding `case` or JSON conditions in `run_hook` for dynamic routing.[2][1]

## Human

Example PreToolUse hook script for router blocking

## Assistant

Here's a complete, production-ready PreToolUse router hook example tailored for your Claude Code setup. It routes Bash/destructive commands through child guards (tests, secrets, linter), propagates the first block's reason + exit 2, and self-identifies on all outputs.[1][2][3]

### settings.json config

Add to `.claude/settings.json` (project-level for your monorepo):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pretooluse_router.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

This intercepts *all* Bash tools before execution.[3][1]

### Router script: pretooluse_router.sh

Save as `.claude/hooks/pretooluse_router.sh` (chmod +x). It delegates to children, preserves their block message:

```bash
#!/bin/bash
set -euo pipefail

INPUT=$(cat)  # Full PreToolUse JSON on stdin
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

echo "Router pretooluse_router: Evaluating '$COMMAND' (session: $SESSION_ID)" >&2

# Priority-ordered guards; first block wins
run_guard() {
  local guard_name=$1
  local guard_path="$CLAUDE_PROJECT_DIR/.claude/hooks/pretooluse_${guard_name}.sh"
  if [[ -x "$guard_path" ]]; then
    echo "Router: Running guard $guard_name" >&2
    echo "$INPUT" | "$guard_path"
    local guard_exit=$?
    if [[ $guard_exit == 2 ]]; then
      echo "Router pretooluse_router: BLOCKED by guard '$guard_name' – propagating" >&2
      return 2  # Child stderr already emitted; Claude sees it
    fi
  else
    echo "Router: Skipping missing guard $guard_name" >&2
  fi
}

# Run guards in order
run_guard "tests"     || exit 2
run_guard "secrets"   || exit 2
run_guard "destructive" || exit 2
run_guard "linter"    || exit 2

# All passed
echo "Router pretooluse_router: All guards passed for '$COMMAND'" >&2
exit 0
```

### Child guard examples

Each child (e.g., `pretooluse_tests.sh`) is self-contained, emits its own ID'd reason on block:

**pretooluse_tests.sh** (chmod +x):
```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

if [[ "$COMMAND" =~ (npm\ test|pytest) ]]; then
  # Simulate test check; replace with your logic
  if ! npm test --silent; then
    echo "BLOCKED by pretooluse_tests: Tests failing (run manually first)" >&2
    exit 2
  fi
fi
exit 0
```

**pretooluse_secrets.sh**:
```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

if echo "$COMMAND" | grep -qiE '(api|token|password|key)'; then
  echo "BLOCKED by pretooluse_secrets: Command risks leaking secrets" >&2
  exit 2
fi
exit 0
```

**pretooluse_destructive.sh** (classic rm/git guard):
```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

if echo "$COMMAND" | grep -qiE '(rm\ -rf|git\ reset\ --hard|drop\ table)'; then
  echo "BLOCKED by pretooluse_destructive: Destructive command denied" >&2
  exit 2
fi
exit 0
```

### How it behaves

- **Block**: First guard hits exit 2 → its stderr (e.g., "BLOCKED by pretooluse_tests...") shows to Claude/user; tool call cancels.[1][3]
- **Allow**: All exit 0 → router exits 0, tool runs.
- **Debug**: `claude --debug` or Ctrl+O for full stderr trace showing router + guards.[1]
- **Windows/PowerShell**: Use `.ps1` equivalents (e.g., `pretooluse_router.ps1`) with `exit 2`; test in Git Bash.[2]

Extend: Add JSON parsing for MCP tools or dynamic guards via `jq` conditions.[3][1]

## Human

Common mistakes when implementing blocking hooks exit code 2

## Assistant

Common pitfalls with exit code 2 blocking hooks include shell pollution, wrong output streams, platform quirks, and config mismatches that silently fail to block or hide reasons. These often stem from how Claude Code strictly interprets stdin/stdout/stderr and exit codes per event.[1][2][3]

### Output stream errors

- Writing block reasons to `stdout` instead of `stderr`: Claude ignores stdout on exit 2 (except UserPromptSubmit/SessionStart); use `>&2` or `print(..., file=sys.stderr)`.[2][1]
- Echoing extra content before JSON/stderr: Pure stderr/JSON only—no prefixes/suffixes, or parsing fails.[2]

### Exit code mishandling

| Mistake | Effect | Fix [1][2] |
|---------|--------|----------------------|
| Exit 1 or other non-2 | Non-blocking error; tool/prompt runs anyway | Always `exit 2` for blocks |
| No explicit exit | Defaults to 0; no block | `exit 2` at end of block path |
| Router overwrites child stderr | Claude sees router's generic message, not leaf reason | Propagate child's exit/stderr unchanged |

### Platform & config issues

- Windows/Git Bash path/execution fails: Hooks don't run at all.[4]
  - Fix: Full paths (`$CLAUDE_PROJECT_DIR/.claude/hooks/script.sh`), `#!/bin/bash -l`, test standalone.
- Wrong matcher/event: e.g., PreToolUse matcher="Bash*" misses tools.[3][1]
- Plugins vs direct hooks: Exit 2 behaves differently (halts instead of blocking).[5]
  - Fix: Use `.claude/settings.json` direct hooks only for prod blocks.

### Event-specific gotchas

| Event | Common mistake | Behavior on exit 2 [1] |
|-------|----------------|-----------------------------|
| PreToolUse | Assumes blocks all tools | Doesn't block Write/Edit (bug); only Bash reliably |
| Stop | Infinite loop | Check `stop_hook_active: true`; limit depth |
| UserPromptSubmit | JSON on exit 0 instead of 2 | Use `{"decision": "block", "reason": "..."}` + exit 0 for erase |

### Debug checklist

- `/hooks` command: Verify matcher/hook list.
- `claude --debug`: Full traces (debug to stdout, not stderr).[6][2]
- Ctrl+O: Toggle verbose stderr.
- Test: `echo '{"tool_name": "Bash"}' | ./hook.sh; echo $?`[3]

Avoid shebangs like `#!/usr/bin/env bash` if profile pollutes stdin (use pure `#!/bin/bash`).[2]

## Human

Best practices for stderr output in blocking hooks

## Assistant

Keep stderr in blocking hooks (exit 2) concise, actionable, and Claude-friendly: structure it as "BLOCKED by <hook_id>: <specific reason> (<hint>)" so Claude can parse, explain, and fix. Always use `>&2`/`sys.stderr`; never stdout, as it's ignored on exit 2.[1][2][3]

### Core formatting rules

- **One-liner max**: 80 chars; Claude tokens it verbatim as feedback.[4][1]
- **Include identifiers**: Hook name + session/context for traceability (e.g., `tests_guard`).[5]
- **Actionable + hint**: Reason why blocked + what Claude should do next.[2][3]
- **No JSON on exit 2**: Pure text only; stdout/JSON ignored.[1][2]

| Good stderr | Why good [1][4] | Bad stderr |
|-------------|----------------------------------|------------|
| `BLOCKED by pretooluse_secrets: API key in command; redact first` | ID, reason, hint | `Secret detected!` (vague) |
| `BLOCKED by tests_guard: 2/5 failing (run npm test manually)` | Metrics + action | `Tests fail` (no numbers/help) |
| `BLOCKED by router/destructive: rm -rf denied (use git rm)` | Router path + alt | `Dangerous command` (panic) |

### Bash/Python examples

**Bash** (`echo ... >&2; exit 2`):
```bash
echo "BLOCKED by pretooluse_linter: TypeScript strict mode violation in src/utils.ts; run tsc --noEmit" >&2
exit 2
```

**Python** (`sys.stderr.write(...); sys.exit(2)`):
```python
import sys, json
data = json.load(sys.stdin)
cmd = data['tool_input']['command']
if 'rm -rf' in cmd:
    sys.stderr.write("BLOCKED by pretooluse_destructive: rm -rf blocked; use targeted git rm instead\n")
    sys.exit(2)
```

### Pro tips for prod

- **Structured prefixes**: Consistent "BLOCKED by <id>:" for easy grep/filtering.[5]
- **Context from JSON**: Inject `session_id`, `tool_name`, or counts (e.g., `jq` metrics).[2][1]
- **Multi-line OK but rare**: Claude sees it as one message; use only for complex diagnostics.[6]
- **Non-blocking logs**: Use exit 1 + verbose stderr for warnings (Ctrl+O to see).[1]
- **Debug/test**: `claude --debug` + `2>&1 | grep BLOCKED`; Ctrl+O for live view.[6][7]

This makes blocks informative for Claude (it reasons over your stderr) while debuggable for you.[3][2][1]
