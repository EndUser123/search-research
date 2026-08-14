---
title: "In claude code, how can we solve this skill self-verifying problem so that it's the skills responsibility that it get fo"
date: "2026-04-23"
mode: "CONCISE"
uuid: "83688002-5b8c-4e02-80d1-246387da300f"
entry_count: 5
---

## Human

In claude code, how can we solve this skill self-verifying problem so that it's the skills responsibility that it get followed properly.

## Assistant

Claude Code skills enforce self-verification through hooks that intercept agent events, ensuring workflow steps complete before advancing or stopping.[1][2][3]

## Core Pattern
Skills self-verify via a 4-component system in `SKILL.md` frontmatter and hook files: (1) `workflow-state.json` state file tracking phases/artifacts; (2) `PreToolUse` gates blocking invalid tools (e.g., REFACTOR before REDPHASE tests fail); (3) `PostToolUse` validators/transitions marking completion via artifact checks; (4) `Stop` agent hook spawning a subagent to inspect state/artifacts and output `{"ok": false, "reason": "..."}` if incomplete, blocking STOP.[2][4][1]

This shifts responsibility to the skill: Claude cannot skip phases (tool-blocked) or finish early (STOP-blocked). Confidence: high—matches file's "canonical pattern" and docs; untested in your setup (assumes hooks schema supports `type: agent`).[3][1]

## Implementation Steps
1. Define phases in `SKILL.md` (e.g., PREFLIGHT→DISCOVERY→PLANNING→EXECUTION) with allowed tools, artifacts (e.g., `deduplicated.json`, git tags).
2. Create state manager (`statemanagerrefactor.py`): Hash cwd+session ID for instance isolation; read/write JSON with `current_phase`, `completed_steps:[]`, `artifacts:{}`.
3. Add `PreToolUse` hook (Python command): Read state; if tool (e.g., Edit) not allowed in phase, return `{"ok": false}`.
4. Add `PostToolUse` hooks: Validator checks output/errors/artifacts; transition advances phase if criteria met (e.g., grep for "pytest FAIL" in REDPHASE).
5. Add `Stop` agent hook: Prompt subagent "Read `workflow-state.json`; verify all 15 steps/artifacts; output JSON `ok`/reason"; Claude parses text for block.[5][1][2]

Example YAML frontmatter snippet:
```
hooks:
  PreToolUse:
    - matcher: "Edit|Write|Bash|Task"
      hooks:
        - type: command
          command: python CLAUDEPROJECTDIR/skills/refactorhooks/PreToolUsegate.py
  PostToolUse:
    - matcher: "Bash|Task"
      hooks:
        - type: command
          command: python .../PostToolUsevalidator.py
        - type: command
          command: python .../PostToolUsetransition.py
  Stop:
    - type: agent
      promptfile: .../Stoprefactorverifier.py  # Outputs verification prompt
```


## Key Files Generated (From Transcript)
- `packages/skills/sdlc/refactorhooks/statemanagerrefactor.py` (133 lines: phase tracking).[1]
- `PreToolUserefactorgate.py` (37 lines: tool blocking).[1]
- `PostToolUserefactorvalidator.py` (59 lines: output checks).[1]
- `PostToolUserefactortransition.py` (64 lines: phase advance).[1]
- `Stoprefactorverifier.py` (125 lines: agent prompt for artifact scan).[1]

## Limitations & Fixes
- **Phase mismatch**: File notes 4 phases vs. 15 SKILL.md steps—fix by state-logging all steps (add `writestate` calls in skill) or artifact-only verification (content checks, not existence).[1]
- **Fragile transitions**: Text matching on outputs (e.g., "git tag")—fix with structured artifact writes (e.g., `refactor-session-<id>.json`).[1]
- **Stop loop**: Agent must output parseable `{"ok": false}` in text; test via dry-run.[3]
- **Session isolation**: Use cwd-hash; multi-terminal risk if shared dir—add PID/timestamp.[1]

Next: Test hooks in isolation (`Bash` simulate state); if schema errors (e.g., `type: agent`), fallback to `command` wrapper piping to subagent. Does your refactor skill already emit state writes?[2][1]

## Human

Build a full self-verifying Claude Code skill system with hooks and auto-healing reflex skills​
Example code for self-improving reflex skill in Claude Code
How to set up PreToolUse hook for skill verification
Sample hook config to block non-compliant skill use

## Assistant

Claude Code skills self-verify and auto-heal using hooks in `SKILL.md` frontmatter or `.claude/settings.json` to gate tools, track state, and block incomplete workflows via `PreToolUse`, `PostToolUse`, and `Stop` events.[1][2]

## Architecture
A self-verifying skill uses a **phase state machine** (`workflow-state-<hash>.json`): PreToolUse blocks out-of-phase tools (e.g., REFACTOR before tests fail); PostToolUse validates/updates state (artifacts exist, no errors); Stop agent inspects state and denies if gaps remain, forcing continuation. Auto-healing "reflex" skills spawn via Stop hook (type: "agent") to fix violations, e.g., regenerate missing artifacts.[2][3][1]

**Why it works**: Hooks run deterministically before/after events; exit 2 or `{"permissionDecision": "deny"}` blocks non-compliance. State persists via cwd-hash for multi-session. Consensus: Docs confirm agent Stop hooks spawn subagents with Read/Grep/Bash for verification.[1]

## Setup Steps
1. Create `hooks/` dir in project (`.claude/hooks/` or `$CLAUDE_PROJECT_DIR/skills/<skill>/hooks/`).
2. Write Python state manager: Tracks `current_phase`, `completed: {step: bool}`, `artifacts: []`.
3. Define hooks in `SKILL.md` frontmatter YAML (scoped to skill) or `.claude/settings.json` (project-wide).
4. Test: `Bash` simulate phases; check `/hooks` menu.
5. Add reflex: Stop hook spawns "fixer" agent if `ok: false`.[2][1]

**Edge cases**: Subagents inherit hooks—use `agent_id` to scope state; timeouts default 600s (set `timeout: 30`); matcher regex (e.g., `^Bash`).[1]

## State Manager Code
Minimal Python (`hooks/state.py`): Hash-isolated JSON CRUD.

```python
#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import hashlib

def get_state_path():
    cwd = Path.cwd()
    state_id = hashlib.md5(str(cwd).encode()).hexdigest()[:8]
    return cwd / f".claude/hooks/workflow-state-{state_id}.json"

def read_state():
    path = get_state_path()
    return json.loads(path.read_text()) if path.exists() else {"phase": "init", "completed": {}, "artifacts": []}

def write_state(state):
    path = get_state_path()
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(state, indent=2))

if __name__ == "__main__":
    op = sys.argv[1] if len(sys.argv) > 1 else "read"
    state = read_state()
    if op == "read":
        print(json.dumps(state))
    elif op == "advance" and len(sys.argv) > 2:
        state["phase"] = sys.argv[2]
        write_state(state)
        print(json.dumps({"ok": True}))
    else:
        print(json.dumps({"error": "Invalid op"}), file=sys.stderr)
        sys.exit(1)
```
 Run: `python hooks/state.py read` → state JSON stdin/stdout for hooks.[2][1]

## PreToolUse Gate Hook
Blocks tools not allowed in phase (e.g., no REFACTOR in DISCOVERY). Config matcher: `"Edit|Write|Bash|Task"`.

**hook.py**:
```python
#!/usr/bin/env python3
import sys
import json
exec(open("/path/to/hooks/state.py").read())  # Reuse state

data = json.loads(sys.stdin.read())
tool = data["tool_name"]
state = read_state()
allowed = {"discovery": ["Bash", "Read"], "planning": ["Bash", "Write"]}.get(state["phase"], [])

if tool not in allowed:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"{tool} not allowed in {state['phase']}; complete prior phase"
        }
    }))
    sys.exit(0)

sys.exit(0)  # Allow
```


**Config** (in SKILL.md):
```
---
hooks:
  PreToolUse:
    - matcher: "Edit|Write|Bash|Task"
      hooks:
        - type: command
          command: "python $CLAUDE_PROJECT_DIR/skills/refactor/hooks/gate.py"
          timeout: 10
---
```
Blocks non-compliant use; Claude sees reason, retries compliantly.[2][1]

## PostToolUse Hooks
Chain validator + transition.

**validator.py** (check artifacts/errors):
```python
#!/usr/bin/env python3
# ... state.py exec
data = json.loads(sys.stdin.read())
output = data.get("tool_output", {}).get("stdout", "") + data.get("stderr", "")
state = read_state()

if "error" in output.lower() or data.get("exit_code", 0) != 0:
    print(json.dumps({"decision": "block", "reason": "Tool failed"}))
    sys.exit(0)

# Check artifact, e.g., grep deduplicated.json exists
if state["phase"] == "discovery" and "deduplicated.json" not in output:
    print(json.dumps({"decision": "block", "reason": "Missing deduplicated.json"}))
    sys.exit(0)

sys.exit(0)
```

**transition.py** (advance phase):
```python
# ... state
data = json.loads(sys.stdin.read())
state = read_state()
if "pytest FAIL" in data.get("tool_output", {}).get("stdout", ""):  # RED phase check
    state["phase"] = "red"
    state["completed"]["discovery"] = True
    write_state(state)
sys.exit(0)
```
Config: matcher `"Bash|Task"`, two `command` hooks.[1][2]

## Stop Verifier & Reflex
Agent-type spawns subagent to verify; if incomplete, spawn reflex fixer.

**verifier.py** (promptfile for agent):
```
You are workflow verifier. Read .claude/hooks/workflow-state-*.json. Check all phases complete, artifacts exist (Glob/Grep), tests pass (Bash pytest).

Output ONLY JSON: {"ok": true} or {"ok": false, "gaps": ["missing X", "Y failed"]}

If false, suggest reflex: spawn agent "reflex-fixer" with prompt "Fix gaps: {gaps}".
```
Config:
```
Stop:
  - type: agent
    promptfile: "$CLAUDE_PROJECT_DIR/skills/refactor/hooks/verifier.py"
```
If `{"ok": false}`, blocks STOP (exit 2 parsed); Claude sees gaps, calls reflex skill (self-healing).[1][2]

## Sample Full Config (.claude/settings.json)
```json
{
  "hooks": {
    "PreToolUse": [{"matcher": "Edit|Write|Bash|Task", "hooks": [{"type": "command", "command": "python hooks/gate.py"}]}],
    "PostToolUse": [{"matcher": "Bash|Task", "hooks": [
      {"type": "command", "command": "python hooks/validator.py"},
      {"type": "command", "command": "python hooks/transition.py"}
    ]}],
    "Stop": [{"hooks": [{"type": "agent", "promptfile": "hooks/verifier.py"}]}]
  }
}
```
Reload: edit + save; verify `/hooks`.[1]

## Reflex Self-Improving Skill Example
**SKILL.md** for "reflex-fixer":
```
---
name: reflex-fixer
hooks:  # Self-verifies own execution
  Stop:
    - type: agent
      promptfile: hooks/self-verifier.py  # Meta: verifies fixer completed fixes
---
Fix workflow gaps: {{gaps}}. Use phase-appropriate tools. Writestate after each fix. STOP only if verified.
```
Spawn via verifier prompt: `spawn agent "reflex-fixer" prompt "Fix: {{gaps}}"`. Loops until `ok: true`.[3][2]

**Assumptions**: Hooks in `P.claude/skills/` (your paths); Python3 envvars set. Test incrementally—start with gate. Uncertainty: Agent hook stability (docs: experimental); verify in your MCP.[1]

Next step: Place files in `P.claude/skills/refactor/hooks/`, load skill, run refactor task, inspect state/logs.

## Human

Do your suggestions address the situation where the skill has no Python entry points, by default? I mean, we can add entry points, if needed.  or useful.

## Assistant

No—Python is **not** required. Claude Code hooks are command-driven and communicate through stdin/stdout/exit codes, so a skill with no Python entry points can still self-verify using shell scripts, `jq`, Node, or any executable command you choose.[1][2][3]

What matters is not “does the skill have a Python entry point,” but “does the skill have deterministic hook commands and a shared state contract.”[4][1]

## What changes

A normal Claude Code skill is mostly instruction text, so by default it cannot enforce its own compliance; it can only ask the model to comply.[5][4]
To make the skill responsible for being followed, you add a hook layer beside the skill, not necessarily inside a Python runtime: `PreToolUse` blocks invalid actions, `PostToolUse` records evidence, and `Stop` refuses completion when required artifacts or states are missing.[1][4]

That means your skill can stay “no entry point” in the usual sense, while the enforcement lives in standalone hook commands under `.claude/hooks/` or equivalent project-scoped hook paths.[2][6]

## Minimal requirement

The real minimum is:

- A state file or state convention, for example `.claude/workflow-state.json`.[4]
- One or more hook commands that can read incoming JSON from stdin and return either exit codes or structured JSON on stdout.[2][1]
- A skill prompt that tells Claude to create or update the expected artifacts so the hooks have something concrete to verify.[4]

Without that state/evidence contract, the hook system becomes guessy and brittle, because it is trying to infer workflow progress from natural-language behavior alone.[4]

## No-Python options

You can implement the full system with any of these:

| Option | Good for | Notes |
|---|---|---|
| Bash + jq | Fastest guardrails | Reads stdin JSON and blocks with exit code 2 or structured stdout JSON.[2][6] |
| Node script | Better portability/JSON handling | Good if your repo is already Node-heavy.[1][3] |
| Python script | Cleanest standard-library scripting | Useful, but optional.[1][7] |
| HTTP hook endpoint | Centralized enforcement | More moving parts; better for org-level policy.[1] |

So yes, you *can* add Python entry points, but I would not frame that as the default solution. The more accurate design is: add **hook executables**, and choose Python only if it is the cleanest executable for your environment.[7][1]

## Practical pattern

For a no-Python skill, the simplest useful version is:

- `PreToolUse` shell hook checks current phase from a JSON file and denies tools that are out of order.[6][4]
- `PostToolUse` shell or Node hook updates the state file when a required artifact appears, such as `plan.json`, a git tag, or a failing red-phase test result.[4]
- `Stop` hook checks that all completion criteria are present and blocks STOP if any are missing.[1][4]

That already gives you a self-verifying skill system, even if the skill itself is just a markdown file plus hook config.[4]

## Example without Python

Here is a minimal `PreToolUse` shell hook that blocks `Edit` until planning is complete:[6][2]

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')"
STATE_FILE=".claude/workflow-state.json"

PHASE="init"
if [ -f "$STATE_FILE" ]; then
  PHASE="$(jq -r '.phase // "init"' "$STATE_FILE")"
fi

if [ "$PHASE" = "planning" ] && [ "$TOOL_NAME" = "Edit" ]; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Edit is blocked during planning; complete plan artifacts first."
    }
  }'
  exit 0
fi

exit 0
```

And the matching config shape is command-based, not Python-specific.[2][1]

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/pretool-phase-gate.sh"
          }
        ]
      }
    ]
  }
}
```

## Best design choice

FACT: Python is optional; hooks are command-oriented and can be shell, Node, Python, or HTTP-backed.[3][1][2]
CONSENSUS: For small local skill enforcement, Bash or Node is usually enough; for richer state machines and better error handling, Python is often more maintainable.[7][6]
SPECULATION, medium confidence: In your setup, Node or Bash may be the better default because they reduce packaging friction and make the enforcement layer feel more like infrastructure than a separate app runtime.[3][6]

The premise I would challenge is “entry points” as the key concept. For Claude Code skills, the important thing is **hook-addressable enforcement**, not application-style entry points.[1][4]

## Recommended next step

Start with a no-Python implementation:

- One `workflow-state.json`.
- One `PreToolUse` blocker.
- One `Stop` verifier.
- One tiny convention in the skill: “after each phase, write/update artifact X.”

If that works but becomes too brittle or large, then promote the hooks to Python or Node for maintainability.[1][4]

Would you like a fully worked no-Python package next, using Bash plus `jq`, or a Node-based version?

## Human

Build a bash-only self-verifying Claude Code skill system with blocking hooks for dangerous actions
How to implement self-verification logic in Python command hooks

## Assistant

Yes, and the answer splits into two layers: a **bash-only enforcement system** is fully viable for blocking dangerous actions and basic workflow verification, while **Python command hooks** become useful when the verification logic needs richer state machines, file inspection, or more reliable JSON handling.[1][2][3]

One important correction: for security-critical blocking in `PreToolUse`, rely on **exit code 2 with stderr**, because current docs say that is the blocking mechanism, and there are reports that `permissionDecision: "deny"` in `PreToolUse` can be ignored in some versions.[4][1]

## Bash-only system

A bash-only self-verifying skill system works if you treat the skill as a markdown workflow plus a set of hook scripts that enforce phase order, record evidence, and block dangerous commands before execution.[2][3]

The minimal pieces are:

- `PreToolUse` bash hook for dangerous command blocking and phase gating.[5][1]
- `PostToolUse` bash hook for artifact/state updates, for example writing `.claude/workflow-state.json` when a plan file or test output appears.[3][2]
- `Stop` bash hook that checks completion criteria and exits 2 if the skill is trying to stop early.[1][3]

## Dangerous action blocker

For dangerous actions, `PreToolUse` is the right place because it can stop a tool call **before** it happens.[5][1]

Example bash hook:

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')"
COMMAND="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""')"

if [ "$TOOL_NAME" = "Bash" ]; then
  if printf '%s' "$COMMAND" | grep -Eq '(^|/:space:)rm/:space:+-rf/:space:+/($|/:space:)'; then
    echo "Blocked dangerous command: rm -rf /" >&2
    exit 2
  fi

  if printf '%s' "$COMMAND" | grep -Eq 'git/:space:+push/:space:+(-f|--force)(/:space:.*)?/:space:(main|master)\b'; then
    echo "Blocked dangerous command: force-push to protected branch" >&2
    exit 2
  fi

  if printf '%s' "$COMMAND" | grep -Eq 'git/:space:+reset/:space:+--hard\b'; then
    echo "Blocked dangerous command: git reset --hard" >&2
    exit 2
  fi
fi

exit 0
```

This matches the documented model: stdin JSON in, stderr for the rejection reason, exit 2 to block.[2][1][5]

## Bash phase verification

You can also use bash to verify workflow phase compliance, as long as the phase model is simple and artifact-driven.[3]

Example `.claude/workflow-state.json`:

```json
{
  "phase": "planning",
  "completed": {
    "discover": true,
    "deduplicate": true,
    "plan": false
  },
  "artifacts": {
    "deduplicated_json": "artifacts/deduplicated.json"
  }
}
```

A `PreToolUse` hook can block `Edit` or `Write` until `plan` is complete:[3]

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')"
STATE_FILE=".claude/workflow-state.json"

PHASE="init"
PLAN_DONE="false"

if [ -f "$STATE_FILE" ]; then
  PHASE="$(jq -r '.phase // "init"' "$STATE_FILE")"
  PLAN_DONE="$(jq -r '.completed.plan // false' "$STATE_FILE")"
fi

if [ "$TOOL_NAME" = "Edit" ] || [ "$TOOL_NAME" = "Write" ]; then
  if [ "$PHASE" = "planning" ] && [ "$PLAN_DONE" != "true" ]; then
    echo "Blocked: editing is not allowed until planning is complete and plan artifacts exist." >&2
    exit 2
  fi
fi

exit 0
```

This is enough to make the skill structurally harder to ignore, even with no Python at all.[3]

## Bash hook config

A sample config to block non-compliant skill use and dangerous actions looks like this:[1][2]

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/bash-dangerous-blocker.sh"
          }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/phase-gate.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/update-state.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/verify-stop.sh"
          }
        ]
      }
    ]
  }
}
```

## Where bash becomes weak

Bash is fine for:

- Regex-based command blocking.[5]
- Presence/absence checks for artifacts.[3]
- Simple phase flags in JSON via `jq`.[2]

Bash gets brittle when you need:

- Multi-step state transitions tied to many workflow steps.[3]
- Parsing large or variable JSON payloads reliably.[2]
- Deeper file-system inspection and content validation, for example “plan exists, adversarial review exists, tests failed first, then passed later.”[3]

That is where Python command hooks become materially better, not because Claude Code requires Python, but because the verification problem becomes real software.[6][3]

## Python self-verification logic

Python command hooks are useful for building a proper verifier that reads stdin JSON, loads a workflow state file, inspects artifacts, and returns a blocking failure when the skill has not actually satisfied its contract.[1][2]

Example Python `Stop` verifier:

```python
#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

STATE_FILE = Path(".claude/workflow-state.json")

REQUIRED_ARTIFACTS = [
    Path("artifacts/deduplicated.json"),
    Path("artifacts/plan.json"),
    Path("artifacts/adversarial-review.json"),
]

REQUIRED_COMPLETIONS = [
    "discover",
    "deduplicate",
    "plan",
    "redphase",
    "refactor",
    "regression",
]

def fail(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(2)

def main() -> None:
    _hook_input = json.load(sys.stdin)

    if not STATE_FILE.exists():
        fail("Blocked STOP: missing .claude/workflow-state.json")

    state = json.loads(STATE_FILE.read_text())

    missing_steps = [
        step for step in REQUIRED_COMPLETIONS
        if not state.get("completed", {}).get(step, False)
    ]
    if missing_steps:
        fail(f"Blocked STOP: incomplete workflow steps: {', '.join(missing_steps)}")

    missing_artifacts = [str(p) for p in REQUIRED_ARTIFACTS if not p.exists()]
    if missing_artifacts:
        fail(f"Blocked STOP: missing artifacts: {', '.join(missing_artifacts)}")

    red_failed = state.get("checks", {}).get("red_tests_failed_first", False)
    green_passed = state.get("checks", {}).get("green_tests_passed", False)

    if not red_failed:
        fail("Blocked STOP: no evidence that RED phase failed first")
    if not green_passed:
        fail("Blocked STOP: no evidence that GREEN phase passed")

    raise SystemExit(0)

if __name__ == "__main__":
    main()
```

This is the proper shape for self-verification logic: explicit contract, explicit evidence, explicit failure mode.[1][3]

## Auto-healing reflex skills

Your earlier premise included “auto-healing reflex skills.” That is plausible, but it needs care. A hook should usually **block and explain**, while the skill or agent then performs the repair; the hook itself should not become a giant repair engine unless you want harder-to-debug behavior.[3]

A safer pattern is:

- `PreToolUse` blocks the violation and explains why.[1]
- The skill instructions require Claude to run a named recovery step, such as `RECOVER_PLAN` or `REBUILD_ARTIFACTS`.[3]
- `PostToolUse` marks the recovery complete when evidence exists.[3]

That keeps hooks deterministic and keeps the repair logic in the skill workflow, where another LLM can review it more easily.[3]

## Recommendation

FACT: You can build a complete blocking self-verifying system in bash only.[2][1]
FACT: Python is not required, but it is better for nontrivial verification logic and stateful workflow enforcement.[6][1][3]
FACT: For dangerous action prevention, use `PreToolUse` plus exit code 2 and stderr, because that is the documented blocking path and JSON-based denial has had reliability issues in some reports.[4][1]

My recommendation is:

- Use **bash** for the security firewall and simple phase gates.
- Use **Python** for the Stop verifier and any nontrivial workflow state machine.
- Keep the skill contract artifact-based, not prose-based.

Would you like the next step as a full reviewed package with:
1. bash-only hooks, or  
2. hybrid bash + Python hooks with a proper state schema and reflex-skill template?

## Human

"

❯ Is there anything else you wish you knew? Any other questions I should ask of the deep research agent?



● Yes. One critical unknown remains:



  What completion signals does /refactor actually emit?



  The PostToolUse_refactor_transition.py hook works by grepping tool output for phase-completion markers (e.g., "DISCOVERY

  COMPLETE", "git tag created"). But /refactor SKILL.md prose may not tell Claude to emit any such marker. If it doesn't, the

  transition hook has nothing to detect — the state machine never advances, and the whole system is blind.



  The question to ask:



  ▎ "For /refactor SKILL.md — does the skill prose explicitly tell Claude to emit completion signals (e.g., 'type DONE', 'phase

  ▎ complete') after each step? If not, what text does Claude typically outputs when completing each of the 15 steps?"



  This is the linchpin. Everything else — the state machine, the gates, the Stop verifier — depends on those signals existing or

  being insertable into the skill prose.



  If the answer is "no signals exist and the prose doesn't tell Claude to emit them," the fix is straightforward: add a line to

  SKILL.md prose telling Claude to emit a completion marker after each phase. But if that line already exists somewhere I haven't

  seen, the system might already work.



● Ran 10 stop hooks (ctrl+o to expand)

  ⎿  Stop hook error: Hook evaluator API error: API Error: 400

  {"type":"error","error":{"type":"invalid_request_error","message":"invalid params"}}



✻ Baked for 1m 23s



❯ Well, the Deep Agent won't tell me that, but you can look it up from the skill yourself.



  Read 1 file (ctrl+o to expand)



❯ I think we've already talked about how each step can emit its own state.



● The prose does not tell Claude to emit completion signals. Each step relies on the PostToolUse_refactor_transition.py hook having

  hardcoded text patterns to detect. Let me check what those patterns actually are:



● Now I can see the full picture. Two things are now clear:



  1. The transition IS artifact-driven, not signal-driven — advance_if_complete checks if files exist on disk (deduplicated.json,

  plan.json), not whether the skill emitted a completion marker. So the absence of explicit "DONE" signals in the prose is actually

  fine — the hook looks at artifacts, not signals.



  2. The 4-phase model vs 15-step mismatch remains the real gap. The state machine lumps

  PREFLIGHT→DISCOVER→DEDUPLICATE→CLASSIFY_DEBT→PRIORITIZE all into DISCOVERY, and

  CONSTITUTIONAL_FILTER→PLAN→RED_PHASE→CHECKPOINT_RED into PLANNING. So steps 1-5 are invisible to the state machine individually.



  On your point about steps emitting their own state — the current design already does this, just at phase granularity (4 groups)

  rather than step granularity (15 individual). The skill prose drives what artifacts appear; the hook observes them and advances.

  That's sound.



  The remaining gap is narrow: the Stop verifier's checklist (lines 19-34 in Stop_refactor_verifier.py) lists 14 items that map to

  the 15 SKILL.md steps, but the state machine only records 4 phase-level checkpoints. The Stop verifier can't distinguish whether

  step 3 of 5 within DISCOVERY was done — only that DISCOVERY eventually completed.



  The question is whether that distinction matters for /refactor's actual safety. Would a phase-level record catch a real failure

  mode that step-level wouldn't?"

Does this help drive new ideas you have that can be useful?

## Assistant

Yes—this helps a lot, and it points to a more precise design. The useful new idea is to **separate three jobs that were being conflated**: runtime gating, execution trace, and end-of-run verification.[1][2]

The 4-phase model is fine for **gating**, but it is not sufficient for **proving** that all 15 refactor steps ran in this session, in order. That means the right architecture is not “replace 4 phases with 15 gated phases,” but “keep coarse gating, add a 15-step execution ledger, and make STOP verify the ledger plus session-scoped evidence.”[2][1]

## What this changes

Your quoted analysis correctly identifies that artifact-driven transitions can work without explicit “DONE” text markers, because the transition hook can watch files instead of prose signals.[1]
But it also exposes the real blind spot: artifacts alone do not prove that each of the 15 steps ran **in this run**, because files may be stale, partial, or left over from a prior invocation.[1]

So the new idea is:

- Keep the **4-phase state machine** for tool blocking.
- Add a separate **15-step append-only execution ledger**.
- Require **session-scoped evidence** for steps that produce artifacts.
- Make the **Stop hook** verify both the ledger and the evidence.[2][1]

That is the smallest design that closes the actual gap.[1]

## Why the current design is insufficient

The current design seems to oscillate between two incomplete models:

- **Phase-only model**: good enough to block `Edit/Write` before the right moments, but too coarse to prove all 15 steps ran.[1]
- **Artifact-only verifier**: better than nothing, but unsafe if `deduplicated.json`, `plan.json`, tags, or reports can exist from a prior or partial run.[1]

The important correction is this: a state machine does **not** need to gate every step in order to **record** every step.[1]
That means the burden is lower than “15 enforcement phases”; you only need 15 logged milestones, while retaining maybe 2–4 actual blocking boundaries.[1]

## Best architecture

Use three distinct stores:

| Store | Purpose | Granularity |
|---|---|---|
| `phase_state.json` | Tool gating, allowed tools, coarse execution mode | 4 phases.[1] |
| `execution_ledger.jsonl` | Immutable record that each of the 15 steps started/completed | 15 steps, append-only.[1] |
| `session_artifacts/` or artifact metadata in ledger | Session-scoped proof of outputs | Only steps that produce outputs.[1] |

That lets you answer three different questions cleanly:

- “Can Claude use this tool **now**?” → phase state.[1]
- “Did step `CLASSIFY_DEBT` run in this session?” → ledger.[1]
- “Did step `PLAN` produce the expected output for this session?” → artifact evidence.[1]

This is materially better than trying to force one file or one hook to serve all three roles.[1]

## The crucial design insight

The most useful new idea is this:

**Do not infer step completion from hook-observed side effects when the skill is inline prose unless you have no better option. Instead, make the skill write its own ledger entries as part of the workflow contract.**[1]

That matters because the file indicates `/refactor` is an inline skill, not a Python subprocess with a `main.py`, so hooks cannot naturally observe “Claude moved from step 6 to step 7” unless that movement leaves a deterministic trace.[1]
If the skill prose does not already force a trace write at each step boundary, then per-step verification is not actually closed.[1]

So the cleanest fix is to update the skill contract to require step boundary writes such as:

- `STEP_START: CLASSIFYDEBT`
- `STEP_COMPLETE: CLASSIFYDEBT`
- or better, a JSON append to the ledger.[1]

## Inline-skill constraint

This is the part that really matters for feasibility: if `/refactor` has no executable entry point and is just SKILL.md prose, then the only reliable ways to get a 15-step execution record are:[1]

- Make the skill itself issue deterministic write operations at each step boundary.[1]
- Or convert the skill into a wrapper/execution-style skill that owns state emission directly.[1]

The file strongly suggests there is **no Python entry point today**, which means “hooks alone” cannot magically know that non-tool-gating conceptual steps like `CLASSIFYDEBT`, `PRIORITIZE`, or `CONSTITUTIONALFILTER` happened unless the skill is modified to leave a record.[1]

So the answer to “does this help drive new ideas?” is yes: it reveals that the missing piece is not more sophisticated hook logic; it is an **execution trace contract in the skill itself**.[1]

## Practical design

I would redesign it this way:

- **PreToolUse gate**: blocks dangerous or out-of-order tools based on 4 coarse phases, not 15.[2][1]
- **PostToolUse transition**: updates coarse phase when hard evidence appears, for example red test failure observed, plan artifact created, checkpoint tag created.[1]
- **Skill prose change**: every one of the 15 steps must append a ledger record with `session_id`, `step`, `event`, `timestamp`.[1]
- **Stop hook**: verifies all 15 `STEP_COMPLETE` entries exist in order for the current `session_id`, and then verifies step-specific artifacts/content where applicable.[2][1]

That avoids trying to make the phase gate do work it was never meant to do.[1]

## Session correctness

Another useful idea driven by your excerpt is to make everything **session-scoped**. Without that, even a perfect Stop verifier can be fooled by stale files from a previous run.[1]

So each run should create a `session_id`, and every ledger entry and artifact should carry it, either in:

- filename,
- JSON payload,
- file header,
- or adjacent metadata.[1]

Then STOP can verify “all 15 steps completed for session `abc123`,” not merely “some files exist in the repo.”[1]

## Is 15-step tracking too burdensome?

FACT: it is more burdensome than 4-phase gating because the skill must emit a trace for every step boundary.[1]
FACT: it is not conceptually hard; it is mostly a discipline and integration change.[1]
SPECULATION, high confidence: it is worth the cost only if your real problem is “Claude sometimes silently skips conceptual steps,” not merely “Claude sometimes stops too early” or “Claude uses dangerous tools too soon.”[1]

That distinction matters. If your dominant risk is premature stopping, a strong Stop verifier plus session-scoped artifacts may be enough. If your dominant risk is skipped reasoning steps inside the refactor workflow, then you need the 15-step ledger.[3][1]

## Strong recommendation

My recommendation is:

- **Do not** expand the gating state machine to 15 enforced phases unless you truly need tool restrictions at each step.[1]
- **Do** add a 15-step execution ledger written by the skill itself.[1]
- **Do** keep 4 coarse gating phases for runtime safety.[1]
- **Do** make Stop validate current-session ledger completeness plus artifact/content checks.[2][1]

That is the best balance of correctness, complexity, and reviewability.[1]

## The next question to ask

The most discriminating follow-up question is:

“Can `/refactor` SKILL.md be safely modified so that every one of the 15 steps performs a deterministic write of `STEP_START` and `STEP_COMPLETE` with `session_id`, or does the current inline-skill format make those writes awkward/unreliable?”[1]

If the answer is yes, you have a clean solution. If the answer is no, then the honest conclusion is that `/refactor` should be partially or fully converted from pure inline prose into an execution-style wrapper so the trace is not dependent on model obedience alone.[1]

Would you like me to turn this into a concrete ADR-style proposal with the exact ledger schema, hook responsibilities, and failure modes?
