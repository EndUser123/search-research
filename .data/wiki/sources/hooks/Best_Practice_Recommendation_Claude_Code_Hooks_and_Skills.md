# Greenfield Operational Standard: Fidelity-First Control Plane for Claude Code (v2.x)

## 0. Why This Exists (Root Principle, Not Symptom)
Skill hallucinations are a symptom. The underlying failure is **fluency over fidelity**: the model optimizes for plausible language unless the system forces claims/actions to be grounded and verifiable.

This standard fixes the root issue by making fidelity an operational property of the stack.

## Context and Design Rationale
This runbook is intentionally built from operational lessons learned in real Claude Code stacks:
- Skill enforcement is necessary but not sufficient.
- The deeper issue is groundedness: fluent text generation can invent plausible identifiers unless the system validates them.
- Hook architecture is tool-centric; therefore prevention and correction must be layered across events.

Design choices and why they exist:
- **Registry-first canonicalization** prevents identifier drift and alias confusion.
- **PreToolUse hard gate** enforces action safety before side effects happen.
- **Stop scanner** addresses free-text command fabrication in the only practical post-response hook point currently available.
- **Scoped atomic state** (project + terminal + session) removes stale leakage without TTL heuristics.
- **Telemetry contract** makes policy behavior auditable and tunable over time.

What this means operationally:
- You are not depending on a smarter prompt alone.
- You are enforcing a control plane where fidelity is measured, gated, and corrected.
- The system remains predictable under multi-terminal and long-running usage patterns.
## 1. Core Principles (Design Invariants)
1. **Identifiers Are Contracts**
- Commands, tool names, skill names, file paths are machine identifiers, not prose.
- Never compress, alias-on-output, or paraphrase identifiers.

2. **Evidence Before Action**
- Claims about environment capabilities must be checked against local source-of-truth registries before output/action.

3. **Prevent First, Correct Second**
- Pre-execution controls block unsafe/ungrounded actions.
- Post-response controls detect and force correction for text-level fidelity failures.

4. **Deterministic State, No TTL**
- Session state is scope-keyed (project + terminal + session), atomically written, and stale-safe by validation (not expiration).

5. **Observable Enforcement**
- Every allow/deny/correct decision is logged with reason and scope.

## 2. Repository Layout (Greenfield)
Create:

```text
.claude/
  settings.json
  hooks/
    UserPromptSubmit.py
    PreToolUse.py
    Stop_fidelity.py
    PostToolUse.py
    common.py
    config/
      command_registry.json
      skill_registry.json
    state/
    logs/
```

## 3. Hook Wiring (settings.json)
Merge into `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/UserPromptSubmit.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash|Read|Grep|Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/PreToolUse.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/PostToolUse.py",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/Stop_fidelity.py",
            "timeout": 20
          }
        ]
      }
    ]
  }
}
```

## 4. Exact Hook I/O Contract

### 4.1 UserPromptSubmit
Input (stdin JSON):
- must contain `prompt`
- may contain `session_id`, `terminal_id`

Output:
- plain text additional context/instruction
- exit `0`

Behavior:
- parse slash/skill tokens
- canonicalize to skill id
- write scoped intent file
- return strict first-action instruction

### 4.2 PreToolUse
Input:
- tool metadata (event payload), including current tool name/input
- may contain session/terminal context

Output when deny:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Fidelity gate: required Skill(...) must run first."
  }
}
```

Output when allow:
- `{}` (or no-op JSON)
- exit `0`

### 4.3 Stop
Input:
- includes `transcript_path`

Output when correction required:
```json
{
  "decision": "block",
  "reason": "Invalid command '/plan-review'. Use '/plan-workflow review <path>'."
}
```

Output when clean:
- `{}` or empty output with exit `0`

### 4.4 Exit-Code Rules
- Hook processing errors should still prefer exit `0` with safe fallback behavior.
- Never crash hard on parse failures; log and degrade gracefully.

## 5. Registry Source of Truth

### 5.1 `command_registry.json`
```json
{
  "slash_commands": ["/plan-workflow", "/hooks", "/clear"],
  "command_forms": {
    "/plan-workflow": ["review <path>", "run <path>"]
  }
}
```

### 5.2 `skill_registry.json`
```json
{
  "skills": {
    "claude-automation-recommender": {
      "aliases": [
        "claude-automation-recommender",
        "/claude-automation-recommender",
        "automation-recommender"
      ]
    }
  }
}
```

### 5.3 Validation + Fallback Policy
- If registry missing/corrupt:
  - log `registry_load_failed`
  - deny risky actions in `PreToolUse`
  - in `Stop`, avoid false claims and emit conservative correction reason
- Do not continue in permissive mode silently.

## 6. Copy/Paste Reference Implementations

### 6.1 `.claude/hooks/common.py`
```python
#!/usr/bin/env python3
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(os.getenv("CLAUDE_PROJECT_DIR", Path.cwd()))
HOOKS = ROOT / ".claude" / "hooks"
CONFIG = HOOKS / "config"
STATE = HOOKS / "state"
LOGS = HOOKS / "logs"

STATE.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS / "fidelity_control_plane.jsonl"


def read_stdin_json():
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def log_event(event: str, decision: str, reason: str, **extra):
    obj = {
        "ts": int(time.time()),
        "event": event,
        "decision": decision,
        "reason": reason,
    }
    obj.update(extra)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=True) + "\n")


def get_scope(payload: dict):
    terminal_id = str(payload.get("terminal_id") or os.getenv("TERM_SESSION_ID") or "default-terminal")
    session_id = str(payload.get("session_id") or payload.get("conversation_id") or "default-session")
    project_id = str(ROOT.resolve())
    return project_id, terminal_id, session_id


def state_path(terminal_id: str, session_id: str) -> Path:
    return STATE / f"pending_intent_{terminal_id}_{session_id}.json"


def atomic_write_json(path: Path, data: dict, retries: int = 3):
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(data, ensure_ascii=True, indent=2)
    for _ in range(retries):
        try:
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(path)
            return True
        except Exception:
            time.sleep(0.05)
    return False


def canonical_skill(prompt: str, registry: dict):
    prompt_l = (prompt or "").lower()
    for skill_id, data in (registry.get("skills") or {}).items():
        for alias in data.get("aliases", []):
            if alias.lower() in prompt_l:
                return skill_id
    return None


def extract_slash_tokens(text: str):
    return re.findall(r"/[a-z0-9-]+", text or "")
```

### 6.2 `.claude/hooks/UserPromptSubmit.py`
```python
#!/usr/bin/env python3
from common import read_stdin_json, load_json, CONFIG, get_scope, state_path, atomic_write_json, canonical_skill, log_event

payload = read_stdin_json()
prompt = payload.get("prompt", "")
project_id, terminal_id, session_id = get_scope(payload)

skill_registry = load_json(CONFIG / "skill_registry.json")
if not skill_registry:
    log_event("registry_load_failed", "degrade", "skill registry missing/corrupt", project_id=project_id, terminal_id=terminal_id, session_id=session_id)
    print("")
    raise SystemExit(0)

skill_id = canonical_skill(prompt, skill_registry)
if not skill_id:
    print("")
    raise SystemExit(0)

intent = {
    "project_id": project_id,
    "terminal_id": terminal_id,
    "session_id": session_id,
    "intent_type": "required_skill",
    "canonical_id": skill_id,
}
ok = atomic_write_json(state_path(terminal_id, session_id), intent)
if ok:
    log_event("intent_detected", "allow", "skill intent captured", project_id=project_id, terminal_id=terminal_id, session_id=session_id, canonical_id=skill_id)

print(f"Your FIRST action must be: Skill(skill='{skill_id}') exactly, no analysis.")
```

### 6.3 `.claude/hooks/PreToolUse.py`
```python
#!/usr/bin/env python3
import json
from common import read_stdin_json, load_json, get_scope, state_path, log_event

payload = read_stdin_json()
project_id, terminal_id, session_id = get_scope(payload)

p = state_path(terminal_id, session_id)
intent = load_json(p)
if not intent:
    print("{}")
    raise SystemExit(0)

if intent.get("project_id") != project_id or intent.get("terminal_id") != terminal_id or intent.get("session_id") != session_id:
    try:
        p.unlink(missing_ok=True)
    except Exception:
        pass
    log_event("state_scope_mismatch", "cleanup", "stale scope removed", project_id=project_id, terminal_id=terminal_id, session_id=session_id)
    print("{}")
    raise SystemExit(0)

blob = json.dumps(payload).lower()
required = (intent.get("canonical_id") or "").lower()
if f"skill(skill='{required}')" in blob or f"skill(\"{required}\")" in blob:
    try:
        p.unlink(missing_ok=True)
    except Exception:
        pass
    log_event("skill_loaded_unblocked", "allow", "required skill observed", project_id=project_id, terminal_id=terminal_id, session_id=session_id, canonical_id=required)
    print("{}")
    raise SystemExit(0)

log_event("pretool_denied", "deny", "required skill not loaded", project_id=project_id, terminal_id=terminal_id, session_id=session_id, canonical_id=required)
out = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"Fidelity gate: call Skill(skill='{required}') before other tools."
    }
}
print(json.dumps(out))
```

### 6.4 `.claude/hooks/Stop_fidelity.py`
```python
#!/usr/bin/env python3
import json
from pathlib import Path
from common import read_stdin_json, load_json, CONFIG, get_scope, extract_slash_tokens, log_event

payload = read_stdin_json()
project_id, terminal_id, session_id = get_scope(payload)

transcript_path = payload.get("transcript_path")
if not transcript_path:
    print("{}")
    raise SystemExit(0)

cmd_registry = load_json(CONFIG / "command_registry.json")
if not cmd_registry:
    log_event("registry_load_failed", "degrade", "command registry missing/corrupt", project_id=project_id, terminal_id=terminal_id, session_id=session_id)
    print("{}")
    raise SystemExit(0)

valid = set(cmd_registry.get("slash_commands", []))

# loop guard
guard_file = Path(str(Path(transcript_path).with_suffix(".stop_guard.json")))
count = 0
if guard_file.exists():
    try:
        count = json.loads(guard_file.read_text(encoding="utf-8")).get("count", 0)
    except Exception:
        count = 0

if count >= 2:
    log_event("stop_guard_open", "allow", "loop guard opened", project_id=project_id, terminal_id=terminal_id, session_id=session_id)
    print("{}")
    raise SystemExit(0)

last_assistant = ""
try:
    lines = Path(transcript_path).read_text(encoding="utf-8").splitlines()
    for line in reversed(lines):
        obj = json.loads(line)
        if obj.get("role") == "assistant":
            c = obj.get("content", "")
            last_assistant = c if isinstance(c, str) else json.dumps(c)
            break
except Exception:
    print("{}")
    raise SystemExit(0)

tokens = extract_slash_tokens(last_assistant)
invalid = [t for t in tokens if t not in valid]
if not invalid:
    print("{}")
    raise SystemExit(0)

count += 1
guard_file.write_text(json.dumps({"count": count}), encoding="utf-8")

bad = invalid[0]
reason = f"Invalid command '{bad}'. Use only registered commands from command_registry.json."
log_event("stop_invalid_command_detected", "block", reason, project_id=project_id, terminal_id=terminal_id, session_id=session_id)
print(json.dumps({"decision": "block", "reason": reason}))
```

### 6.5 `.claude/hooks/PostToolUse.py` (minimal)
```python
#!/usr/bin/env python3
print("{}")
```

## 7. Concrete Test Harness

### 7.1 Quick syntax check
```powershell
python -m py_compile .claude/hooks/common.py .claude/hooks/UserPromptSubmit.py .claude/hooks/PreToolUse.py .claude/hooks/Stop_fidelity.py .claude/hooks/PostToolUse.py
```
Expected: no output, exit code 0.

### 7.2 Unit-style local checks (manual)
1. Prompt containing alias `/claude-automation-recommender`.
- Expected: intent file created in `.claude/hooks/state/`.

2. Tool call before skill load.
- Expected: PreToolUse returns `permissionDecision: deny`.

3. Skill call observed.
- Expected: state file deleted, next tool allowed.

4. Transcript containing `/plan-review`.
- Expected: Stop returns `decision: block` with correction reason.

5. Stale file copied from another terminal/session.
- Expected: ignored + deleted + `state_scope_mismatch` log event.

### 7.3 Log verification
```powershell
Get-Content .claude/hooks/logs/fidelity_control_plane.jsonl | Select-String "intent_detected|pretool_denied|skill_loaded_unblocked|stop_invalid_command_detected|state_scope_mismatch"
```
Expected: matching events for each scenario.

## 8. Rollout Procedure
1. Deploy registries + `common.py`.
2. Deploy `UserPromptSubmit.py` and `PreToolUse.py`.
3. Run tests 7.1-7.3.
4. Deploy `Stop_fidelity.py` with loop guard enabled.
5. Monitor JSONL for 24-48 hours.
6. Tune registry coverage and deny reasons.

## 9. Rollback Procedure (Safe)
1. Comment out `Stop` hook in settings.
2. If needed, comment out `PreToolUse` hook.
3. Keep `UserPromptSubmit` active for low-risk guidance-only mode.
4. Archive logs before cleanup:
```powershell
Copy-Item .claude/hooks/logs/fidelity_control_plane.jsonl .claude/hooks/logs/fidelity_control_plane.rollback.snapshot.jsonl -Force
```
5. Re-enable incrementally (`UserPromptSubmit` -> `PreToolUse` -> `Stop`).

## 10. Governance Rules
- No deploy without registries, logging, and acceptance checks.
- No TTL as stale-state primary strategy.
- No unvalidated free-text command emission.
- No router replacement without rollback path.

## 11. Acceptance Checklist
- [ ] Commands emitted are canonical and in registry.
- [ ] Required skill blocks are enforced before tool usage.
- [ ] Multi-terminal/session isolation proven.
- [ ] Stop detects invalid slash mentions and requests correction.
- [ ] Loop guard prevents endless correction cycles.
- [ ] Logs provide complete audit trail.

## 12. Summary
This runbook enables full implementation in a greenfield repo with copy/paste baseline code, exact hook contracts, deterministic state handling, and operational safeguards that address the root principle (fluency over fidelity), not just one symptom.

