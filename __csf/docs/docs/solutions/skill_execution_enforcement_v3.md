# Skill Execution Enforcement v3.2 - Solution Document

## Problem Statement

LLM loads skill documentation via Skill tool, then provides its own analysis instead of executing the skill's designated workflow. The skill *appears* executed, but the actual execution pattern was never followed.

**Evidence:**
```json
{"event": "violation", "skill": "rca", "required": ["Bash", "Task"],
 "used": ["Bash", "Edit", "Glob", "Read", "Task"],
 "pattern": "rca|RCAEngine|analyze"}
```

LLM used Bash and Task, but commands didn't match the required execution pattern for `/rca`.

## Current Architecture

| Component | File | Purpose | Timing |
|-----------|------|---------|--------|
| Skill Enforcement Gate | `skill_enforcement_gate.py` | Forces Skill tool usage before Bash/Write | PreToolUse |
| Skill Execution Tracker | `posttooluse/skill_execution_tracker.py` | Tracks tool usage after skill load | PostToolUse |
| Skill Execution Gate | `StopHook_skill_execution_gate.py` | Validates execution pattern was followed | Stop |

## Gap Analysis

```
Timeline:
  ┌─────────────────────────────────────────────────────────────────┐
  │ User: /rca hook error                                           │
  ├─────────────────────────────────────────────────────────────────┤
  │ PreToolUse: Skill tool? ✅ Allow                                │
  │ PostToolUse: Skill("rca") loaded → set state                    │
  │                                                                 │
  │ PreToolUse: Bash? skill loaded ✅ Allow                         │ ← GAP: No pattern check
  │ LLM runs: python -m __lib.test_hook ...                         │ ← Wrong command
  │ PostToolUse: Bash used → record tool                            │
  │                                                                 │
  │ PreToolUse: Read? ✅ Allow (investigation tool)                 │
  │ LLM provides own RCA analysis...                                │ ← Substitution happens
  │                                                                 │
  │ Stop hook: pattern not matched → VIOLATION                      │ ← Too late!
  │ User already received substitute analysis                       │
  └─────────────────────────────────────────────────────────────────┘
```

**Root Cause:** Execution validation happens at Stop (post-hoc), not PreToolUse (real-time).

## Solution: Parallel Regex + Daemon Enforcement

### Design

Move execution validation from Stop to PreToolUse. Run regex and daemon checks **in parallel**, with disagreement detection and daemon failure fallback.

```
PreToolUse: Bash command arrives
    │
    ├──► Regex check (fast, deterministic)
    │         └──► result: match/no-match
    │
    └──► Daemon intent check (parallel, semantic)
              └──► result: ok/not-ok/error
    │
    ▼
Decision Matrix:
┌─────────────┬─────────────┬─────────────────────────────────┐
│ Regex       │ Daemon      │ Action                          │
├─────────────┼─────────────┼─────────────────────────────────┤
│ match       │ ok          │ ALLOW                           │
│ match       │ not-ok      │ ALLOW + WARN (disagreement)     │
│ match       │ error       │ ALLOW (daemon failed)           │
│ no-match    │ ok          │ ALLOW + WARN (disagreement)     │
│ no-match    │ not-ok      │ BLOCK                           │
│ no-match    │ error       │ BLOCK + notify daemon failed    │
└─────────────┴─────────────┴─────────────────────────────────┘
```

### Key Behaviors

| Scenario | Outcome | Notification |
|----------|---------|--------------|
| Both agree → allow | Allow | None |
| Both agree → block | Block | Standard block message |
| Disagree | Use regex result | `⚠️ DISAGREEMENT: Regex={X}, Daemon={Y}. Using regex.` |
| Daemon fails | Use regex result | `⚠️ Daemon unavailable, using regex only.` |

### Benefits

- No single point of failure
- Disagreements surface tuning opportunities
- Daemon errors don't block work
- Logs capture cases where one method would have been wrong

## Registry Contract

Extend `SKILL_EXECUTION_REGISTRY` with tighter patterns and hints:

```python
SKILL_EXECUTION_REGISTRY = {
    "rca": {
        "tools": ["Bash", "Task"],
        # Tighter pattern matching actual module/class names
        "pattern": r"src\.rca|SimpleRCAEngine|RCAEngine|EnhancementRouter",
        # Skill-specific guidance injected into block message
        "hint": "Execute the Python code from the skill's ⚡ EXECUTION DIRECTIVE section.",
        # Enable daemon semantic check for this skill
        "intent_enabled": True,
    },
    "ask-olymp": {
        "tools": ["Bash", "Task"],
        "pattern": r"ask_cli\.py|ask-olymp",
        "hint": "Run the ask_cli.py command as specified in the skill.",
        "intent_enabled": False,
    },
    "commit": {
        "tools": ["Bash"],
        "pattern": r"git\s+commit",
        "hint": "Run git commit with appropriate message.",
        "intent_enabled": False,
    },
    # ... other skills
}
```

### Pattern Design Rationale

| Old Pattern | Problem | New Pattern |
|-------------|---------|-------------|
| `rca\|RCAEngine\|analyze` | `analyze` matches unrelated commands | `src\.rca\|SimpleRCAEngine\|RCAEngine\|EnhancementRouter` |
| `\brca\b` (P's suggestion) | Fails on `from src.rca.` (`.` not word boundary) | `src\.rca` matches import paths |

Verified against actual RCA skill execution:
```python
from src.rca.enhancement_router import EnhancementRouter  # ✅ matches src\.rca
from src.rca.simple_rca_engine import SimpleRCAEngine     # ✅ matches src\.rca, SimpleRCAEngine
engine = ProductionRCAEngine()                            # ✅ matches RCAEngine suffix
```

## Implementation

### Phase 1: Merge registries and add schema

Import `SKILL_EXECUTION_REGISTRY` into `skill_enforcement_gate.py`, extend schema:

```python
# skill_enforcement_gate.py
from StopHook_skill_execution_gate import SKILL_EXECUTION_REGISTRY

# Helper for cleaner code
def _extract_command(tool_name: str, tool_input: dict) -> str:
    """Extract command string from tool input."""
    if tool_name == "Bash":
        return tool_input.get("command", "") or ""
    if tool_name == "Task":
        return tool_input.get("prompt", "") or ""
    return ""
```

### Phase 2: Extend state schema

When skill is loaded, include pattern and intent config:

```python
def handle_post_tool_use(data: dict) -> dict:
    skill = extract_skill_name(data)

    exec_config = SKILL_EXECUTION_REGISTRY.get(skill)
    if exec_config:
        state = {
            "skill": skill,
            "phase": "pending_execution",
            "required_tools": exec_config.get("tools", []),
            "required_pattern": exec_config.get("pattern"),
            "hint": exec_config.get("hint", ""),
            "intent_enabled": exec_config.get("intent_enabled", False),
            "execution_satisfied": False,
            "timestamp": time.time(),
        }
        write_state(state)

    return {}
```

### Phase 3: Parallel PreToolUse validation

```python
import concurrent.futures
from daemons.daemon_client import DaemonClient

def _check_regex(pattern: str, command: str) -> bool:
    """Deterministic regex check."""
    if not pattern:
        return True
    return bool(re.search(pattern, command, re.IGNORECASE))

def _check_daemon_intent(skill: str, command: str, pattern: str) -> tuple[bool, str]:
    """
    Semantic intent check via daemon.

    Returns: (ok: bool, status: str)
    - (True, "ok") - daemon says command is valid execution
    - (False, "not-ok") - daemon says command is not valid
    - (False, "error") - daemon unavailable or failed
    """
    try:
        client = DaemonClient(auto_start=False, enable_fallback=False, timeout=2.0)
        result = client.query("skill_intent", {
            "skill": skill,
            "command": command,
            "pattern": pattern,
        })
        if result.get("status") == "success":
            return (result.get("is_valid", False), "ok" if result.get("is_valid") else "not-ok")
        return (False, "error")
    except Exception:
        return (False, "error")

def handle_pre_tool_use(data: dict) -> dict:
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    state = read_pending_state()
    if not state or state.get("execution_satisfied"):
        return {}

    required_tools = state.get("required_tools", [])
    if tool_name not in required_tools:
        return {}

    command = _extract_command(tool_name, tool_input).strip()
    if not command:
        return {}

    required_pattern = state.get("required_pattern")
    intent_enabled = state.get("intent_enabled", False)
    skill = state.get("skill", "unknown")
    hint = state.get("hint", "")

    # Run checks in parallel
    regex_match = _check_regex(required_pattern, command)

    daemon_ok = False
    daemon_status = "disabled"
    if intent_enabled:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_check_daemon_intent, skill, command, required_pattern)
            try:
                daemon_ok, daemon_status = future.result(timeout=2.5)
            except concurrent.futures.TimeoutError:
                daemon_status = "timeout"

    # Decision matrix
    if regex_match and (daemon_status in ("disabled", "ok", "error", "timeout") or daemon_ok):
        # Allow - regex matched
        if daemon_status == "not-ok":
            log_event("disagreement", {
                "skill": skill,
                "regex": "match",
                "daemon": "not-ok",
                "command": command[:200],
                "decision": "allow",
            })
            # Warn but allow
            print(f"⚠️ DISAGREEMENT: Regex=match, Daemon=not-ok. Using regex (ALLOW).", file=sys.stderr)

        if daemon_status == "error":
            print(f"⚠️ Daemon unavailable, using regex only.", file=sys.stderr)

        return _mark_satisfied(state, tool_name)

    if not regex_match and daemon_ok:
        # Disagreement: daemon says ok but regex failed
        log_event("disagreement", {
            "skill": skill,
            "regex": "no-match",
            "daemon": "ok",
            "command": command[:200],
            "decision": "allow",
        })
        print(f"⚠️ DISAGREEMENT: Regex=no-match, Daemon=ok. Using regex (ALLOW).", file=sys.stderr)
        return _mark_satisfied(state, tool_name)

    # Block - regex failed and daemon didn't override
    snippet = command[:160] + ("..." if len(command) > 160 else "")

    daemon_note = ""
    if daemon_status == "error":
        daemon_note = "\n\n⚠️ Daemon unavailable, using regex only."
    elif daemon_status == "timeout":
        daemon_note = "\n\n⚠️ Daemon timeout, using regex only."

    return {
        "decision": "block",
        "reason": f"""⚠️ SKILL EXECUTION PATTERN MISMATCH

The /{skill} skill requires commands matching: `{required_pattern}`

Your command:
```
{snippet}
```

This doesn't match the required execution pattern.

{hint if hint else "Execute the code specified in the skill's ⚡ EXECUTION DIRECTIVE section."}

Do NOT run investigation commands (test_hook, grep, ls) as a substitute.{daemon_note}"""
    }

def _mark_satisfied(state: dict, tool_name: str) -> dict:
    state["execution_satisfied"] = True
    state["satisfied_by"] = tool_name
    state["satisfied_at"] = time.time()
    write_state(state)
    return {}
```

### Phase 4: Simplify Stop hook

With PreToolUse enforcement, Stop becomes safety net:

```python
def handle_stop(data: dict) -> dict:
    state = read_state()
    if not state:
        return {}

    if state.get("execution_satisfied"):
        clear_state()
        return {}

    # Rarely fires with PreToolUse enforcement
    log_event("late_violation", {
        "skill": state.get("skill"),
        "note": "PreToolUse enforcement should have caught this",
    })

    clear_state()
    return {
        "decision": "block",
        "reason": "Skill execution incomplete (fallback enforcement)."
    }
```

### Phase 5: Daemon intent endpoint

Add skill intent query to daemon:

```python
# In daemon server
def handle_skill_intent(request: dict) -> dict:
    """
    Semantic intent classification for skill execution.

    Uses embedding similarity against known good commands for the skill.
    """
    skill = request.get("skill", "")
    command = request.get("command", "")

    # Load known good commands for this skill
    known_commands = SKILL_COMMAND_EXAMPLES.get(skill, [])
    if not known_commands:
        return {"status": "success", "is_valid": False, "reason": "no_examples"}

    # Compute similarity
    command_embedding = embed(command)
    similarities = [cosine_sim(command_embedding, embed(kc)) for kc in known_commands]
    max_similarity = max(similarities)

    # Threshold: 0.75 similarity to any known good command
    is_valid = max_similarity >= 0.75

    return {
        "status": "success",
        "is_valid": is_valid,
        "similarity": max_similarity,
        "matched": known_commands[similarities.index(max_similarity)] if is_valid else None,
    }
```

## Files to Modify

| File | Change |
|------|--------|
| `skill_enforcement_gate.py` | Add parallel regex+daemon validation in PreToolUse |
| `StopHook_skill_execution_gate.py` | Update registry with `hint`, `intent_enabled`; simplify to safety net |
| `posttooluse/skill_execution_tracker.py` | Extend state schema |
| `daemons/semantic_daemon.py` | Add `skill_intent` query handler |

## Testing Strategy

1. **Unit tests**
   - Pattern matching for each skill (positive and negative cases)
   - Decision matrix: all 6 combinations of regex × daemon outcomes

2. **Integration tests**
   - `/rca` → wrong command → block with hint
   - `/rca` → correct command → allow
   - Daemon timeout → falls back to regex

3. **Disagreement tests**
   - Regex match + daemon not-ok → allow + warn + log
   - Regex no-match + daemon ok → allow + warn + log

4. **Regression tests**
   - Skills without patterns still work
   - Investigation tools (Read, Grep, Glob) unaffected

## Rollback

```bash
SKILL_PATTERN_ENFORCEMENT_ENABLED=false  # Disable PreToolUse pattern check
SKILL_INTENT_DAEMON_ENABLED=false        # Disable daemon layer only
```

## Reversibility

**[R:2]** - Hook behavior changes only. Env var disable without code changes.

## Success Criteria

1. `/rca` with substitute analysis → blocked at PreToolUse
2. `/rca` with correct execution → allowed
3. Stop hook violation rate drops to near-zero
4. Disagreements logged for tuning
5. Daemon failures don't block work

## Monitoring

Log file: `P:/.claude/logs/skill_execution_gate.jsonl`

Events to track:
- `skill_loaded` - skill invoked
- `execution_satisfied` - correct execution detected
- `blocked` - PreToolUse block
- `disagreement` - regex and daemon disagree
- `late_violation` - Stop hook fired (should be rare)
- `daemon_error` - daemon unavailable
