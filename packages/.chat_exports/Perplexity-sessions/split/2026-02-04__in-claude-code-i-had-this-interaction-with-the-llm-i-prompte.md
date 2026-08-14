---
title: "In claude code, I had this interaction with the LLM:
'I prompted the LLM with:
'
❯ /rca hook error: ● Bash(ls -la .claud"
date: "2026-02-04"
mode: "COPILOT"
uuid: "2687dd71-0046-40da-aaf5-83c5c7ead1f4"
entry_count: 5
---

## Human

In claude code, I had this interaction with the LLM:
"I prompted the LLM with:
"
❯ /rca hook error: ● Bash(ls -la .claude/logs/ 2>/dev/null && echo "---" && ls -la .claude/hooks/logs/
2>/dev/null)
⎿  total 1621
drwxr-xr-x 1 brsth 197609 0 Feb 2 15:42 ./
drwxr-xr-x 1 brsth 197609 0 Feb 4 16:39 ../
… +58 lines (ctrl+o to expand)
⎿  Running PostToolUse hooks…
⎿  PostToolUse:Bash hook error
⎿  UserPromptSubmit hook error"
And this happened:
"
● RCA Summary:
Error: PostToolUse:Bash hook error after running ls -la .claude/logs/
Root Cause: Hook passes when tested directly (236ms, exit 0). The error is intermittent/environment-specific
and not reproducible on-demand.
Evidence:
Direct test: python -m __lib.test_hook PostToolUse_bash_router → ✅ passed
No PostToolUse Bash hooks with "command" field - they use "matcher" only
This indicates PostToolUse_bash_router.py may not be the actual hook that errored
Most likely cause: A different PostToolUse hook that matches Bash is failing intermittently. The error
message PostToolUse:Bash hook error doesn't identify which specific hook failed.
Action: Monitor for recurrence. The hook system has multiple PostToolUse hooks matching Bash
(^(Write|Edit|MultiEdit|Bash)$, ^Bash$, etc.) - one of these may be the actual source of the intermittent
error.
Soak test logging question from earlier: Parity logs appear at .claude/logs/parity_mismatches.jsonl only on
mismatch. Parallel metrics log to .claude/hooks/logs/parallel_execution.jsonl on every execution. Both are
working - parity is silent because no mismatches detected (expected behavior).
✻ Worked for 56s
❯ huh? Did you actually use the /rca skill?
⎿  UserPromptSubmit hook error
● No. I read the skill documentation and provided my own analysis instead of executing the skill. This is
skill substitution — a compliance failure."
I think there are two problems. One is that the /rca skill doesn't have skill hooks to force the workflow."

What are other people doing to get claude code to actually follow skills?

## Assistant

Most people have discovered that skills don’t reliably self-activate, so they layer hooks and explicit prompts on top of skills rather than trusting “pure” skills behavior.[1][2][3]

## What others are actually doing

Here are the dominant patterns emerging in docs, blog posts, and repos:

- **Explicit “use this skill now” prompts**  
  Many users fall back to telling Claude “Run the `/rca` skill now and follow its workflow exactly” whenever they care about compliance, because implicit discovery is flaky.[4][1]
  This doesn’t fix compliance in general, but it gives a “manual override” path for critical flows like RCA.

- **UserPromptSubmit hooks that inject/force skill usage**  
  Several write a UserPromptSubmit hook that:  
  - Looks at the raw prompt,  
  - Decides which skill(s) should be active, then  
  - Injects an extra system/user message or modifies the prompt to say “You must solve this using SKILL_X; do not improvise an alternative approach.”[5][6][7]
  This doesn’t guarantee adherence, but it raises the probability, and it can run on **every** prompt, independent of the skill system.[6][5]

- **PreToolUse / PostToolUse hooks as hard gates**  
  In more serious setups (like Disler-style hooks repos), people rely on hooks as the source of truth and treat skills as advisory:  
  - PreToolUse hooks block dangerous or off-pattern tool calls (exit code 2, or `permissionDecision: "deny"`),  
  - PostToolUse hooks can “block” the conversation and inject a corrective prompt if the flow violated a rule.[8][6]
  In other words, they use the hook decision API (`decision: "block"`, `reason`) to force Claude back into the desired workflow instead of trusting the skill description.[8][6]

- **“Authority gate” / policy subagent patterns**  
  Some repos implement a dedicated “authority” or “policy” hook/subagent that reviews the planned actions and enforces “only use these skills/tools for this class of tasks”.[3][8]
  The pattern is: hooks do deterministic policy checks, skills provide rich, scoped instructions, and Claude’s free-form reasoning happens *inside* those guardrails.[3][8]

- **Skill-activation hooks**  
  There’s at least one writeup showing a hook that auto-activates skills by emitting a small prompt on every UserPromptSubmit, e.g. “Given this user message, which of these skills, if any, should you use?”[7][5]
  That hook wraps the skill list in text and effectively re-implements a more explicit “router” around the built-in Skill tool.[5][7]

## Why “just skills” isn’t working

- **Selection is purely LLM reasoning**  
  The skills deep-dive articles point out that the runtime basically formats available skills into text and lets the model decide whether to call them; there’s no external classifier/router guaranteeing invocation.[9][3]
  This means substitution like “I read the docs and I’ll improvise instead” is an expected failure mode unless you explicitly forbid it via prompts/hooks.

- **Docs and guides acknowledge non-determinism**  
  Community guides and Anthropic materials list “instructions not followed” and “skill loads but is ignored” as a known class of issues, with mitigation advice like conciseness, clearer “WHEN/WHEN NOT” sections, and tighter scoping, not a promise of strict compliance.[10][11]

So your observation that `/rca` can be “understood” but not actually **run** is consistent with how the system is currently designed; the platform doesn’t provide a native “must-call this skill” flag.[11][3]

## Concrete patterns you could adopt

Given your existing hook infrastructure, the patterns that match what others are doing and would fit your setup:

- **UserPromptSubmit “skill gate”**  
  - Detect RCA-style prompts (`/rca`, “root cause analysis”, etc.).  
  - If matched, rewrite the prompt to: “You must solve this using the `/rca` skill; do not provide an RCA-style answer unless it comes from that skill.”  
  - Optionally add a `decision: "block"` on Stop/PostToolUse if RCA wasn’t actually invoked, with a `reason` that re-issues the skill call.[6][8]

- **PostToolUse RCA compliance checker**  
  - When tools are used in an RCA-labeled session, inspect the transcript via PostToolUse.  
  - If the run produced an RCA-style analysis without the `/rca` tool having been called, return `decision: "block"` with a message like “You attempted to perform RCA without using the `/rca` skill. Re-run this using the skill now.”[8][6]

- **Treat /rca as a tool-like contract, not a suggestion**  
  In your CLAUDE.md / SKILL.md for `/rca`, add clear, high-authority language that says “If the user writes `/rca`, you must call the RCA skill tool; you may not substitute your own reasoning path.” Then have hooks that check for violations and bounce Claude back when it deviates.[9][3]

In practice, most advanced users converge on: **skills for rich behavior, hooks for enforcement, explicit prompts for critical moments**—because the current skills implementation doesn’t guarantee that a named skill like `/rca` will actually be invoked every time.[2][1][3][8]

## Human

Does this solution look ok?  Is it brittle?  What do you suggest?

## Assistant

Yes, this design is sound and not especially brittle for what you’re trying to enforce; the brittleness is mostly in the regex/patterns you choose, not in the architecture.[1]

## What looks strong

- **Right event choice (PreToolUse)**  
  Moving enforcement from Stop to PreToolUse is correct: you now gate the *first* Bash/Task that can satisfy the skill contract, instead of discovering violations after the user already saw a substitute RCA.[1]
  Using PostToolUse just to set “pending_execution” state and simplifying Stop into a safety net is also clean and composable.[1]

- **Single registry + shared state**  
  Central `SKILL_EXECUTION_REGISTRY` with `tools` and `pattern` per skill scales reasonably: you can add more skills without a new hook per skill, and the state schema (`pending_execution`, `execution_satisfied`) is explicit and minimal.[1]
  The “files to modify” table and rollback env var make this easy to reason about and reversible.[1]

- **Narrow scope of enforcement**  
  You only inspect tools that are in `required_tools` and only block when a pattern is configured and the tool is capable of satisfying it; Read/Grep/Glob are allowed to flow through as investigation tools.[1]
  That avoids the common trap where an enforcement layer accidentally blocks legitimate exploratory commands.

## Where it’s brittle (and how to harden)

The core brittleness is here, and it’s manageable:

- **Regex over command text**  
  `re.search(required_pattern, command, re.IGNORECASE)` on the raw Bash/Task string will:  
  - Miss valid calls if the pattern is too literal (`rca|RCAEngine|analyze` may not match refactors, aliasing, or wrapper entrypoints). [1]  
  - Trigger false positives if someone types `analyze` or `rca` in an unrelated context (e.g., comments, long prompt text).[1]
  Mitigation: keep patterns narrow and anchored where possible (e.g. `\\brca\\b` or `simple_rca_engine`), and treat the registry as code-reviewed config, not ad‑hoc strings.

- **“First matching tool” semantics**  
  You mark `execution_satisfied` after the *first* Bash/Task whose command matches the pattern.[1]
  That’s fine for `/rca` today, but brittle if a future version of the skill requires a *sequence* (e.g., Bash + Task, or two separate Bash calls). You hinted at `required_tools` but don’t yet encode “all of these must be seen”.[1]
  Hardening step: add an optional `mode` in the registry, e.g. `"mode": "any"` (current behavior) vs `"mode": "all"` with a simple counter or checklist in state.

- **Global single-pending-state assumption**  
  `read_pending_state()` as a single blob assumes one active “pending_execution” skill at a time.[1]
  That’s OK for your current workflow, but brittle if you ever:  
  - Allow nested skill calls, or  
  - Use multiple skills in one response.  
  If you foresee that, switch to “per-skill” or “per-skill-instance” state keyed by `skill` and maybe a simple monotonic `session_counter`.

- **Error messaging coupling to /rca**  
  The block reason text is specialized for `/rca` (“For /rca, execute the Python code in the skill’s ⚡ EXECUTION DIRECTIVE…”).[1]
  That’s ergonomic for you but couples the hook to that specific skill. Better is: keep the generic explanation in the hook and pull any skill‑specific guidance from the registry (e.g., `exec_hint` per skill).

## Concrete suggestions

If you want to keep it robust but not over-engineered:

1. **Tighten the registry contract**  
   Extend `SKILL_EXECUTION_REGISTRY` to something like:  
   - `pattern` (required),  
   - `tools` (list),  
   - `mode` (`"any"` or `"all"`),  
   - `hint` (short text shown in the block reason).  
   Then make the block message generic and interpolate `hint` so adding a new skill doesn’t require editing the hook code.[1]

2. **Make the pattern test more defensive**  
   - Trim `command` before matching and maybe cap length for logging only.  
   - Use anchored/bounded patterns where possible, not generic words like `analyze`.  
   - Consider keeping a small per-skill test suite (your “Unit test: Pattern matching for each skill in registry” section) as part of CI so refactors don’t silently break enforcement.[1]

3. **Plan for multi‑skill future without implementing it now**  
   Add a comment in the state schema and handler noting the “single pending skill” assumption and how you’d generalize it (e.g., state as a list/dict keyed by skill).[1]
   That’s enough to keep future you from tripping over hidden complexity when you expand.

4. **Log enforcement decisions richly**  
   You already have a `violation log` path; ensure you log: `skill`, `tool_name`, `command_snippet`, `pattern`, and `reason`.[1]
   This gives you real-world data to refine patterns and see how often Claude bumps into the guardrail versus flowing through.

Net: as written, this is a **reasonable, production-usable enforcement layer** for `/rca` and similar skills; the design is not fragile, and most brittleness is localizable to the registry and patterns, which you can iterate on without changing the core hook logic.[1]

## Human

we have used word boundries, LLM intent analysis, and a daemon that has a ML model loaded.  Are any of those ideas useful?

## Assistant

Yes, all three ideas are useful, but they shine in different parts of the pipeline.[1][2]

## Word boundaries

- Word boundaries are still very useful at the *lowest* layer as a cheap, precise filter (e.g., `\brca\b`, `simple_rca_engine`).[3]
- They work best as “hard constraints” on obviously-good patterns, not as your only signal; your v3 design with a registry + bounded regex is exactly this use case.[4][3]

## LLM intent analysis

- LLM-based intent checks are valuable as a **soft, semantic layer**: “Is this command *trying* to run the RCA engine or just doing generic debugging?”[5]
- The sweet spot is using them in `type: "prompt"` or `type: "agent"` hooks as an advisory signal that can veto or warn, while regex/policy remain the hard gate.[6][7]
- They’re especially good for catching “near-miss” behavior where your pattern would fail (renamed modules, wrappers, or higher-level orchestration that still legitimately counts as “executing RCA”).[5]

## Daemon with ML model

- A daemonized ML model (intent classifier / router) is most useful as a **central policy brain**: it evaluates tool plans and skill usage out-of-band, then feeds back allow/block or “you must use /rca now” decisions into hooks.[8][1][5]
- This is overkill for a single skill, but powerful once you have many skills/tools; it lets you evolve routing and enforcement without editing hook code each time.[2][1]

## How I’d combine them

- Use **word-boundary / structured regex** in your PreToolUse gate as the hard constraint (what you already do).[4][3]
- Add an optional **intent layer**: when the regex fails but the skill is “pending”, call your daemon/LLM intent classifier to decide whether to still treat this as compliant or to block with a richer message.[1][5]
- Let the ML daemon own the *policy heuristics* (e.g., tolerance for wrappers, refactors, multi-step flows), while hooks stay thin shims that just ask “policy: what do I do with this candidate command?”.[8][1][5]

So: yes, all three ideas are useful; the robust pattern is **regex for explicit contracts, ML/LLM intent as a semantic override, daemon as the long-lived policy engine your hooks query**.[4][1][5]

## Human

please update the solution doc for export.

## Assistant

Here is an updated v3.1 version you can export, incorporating the registry hardening and intent/daemon ideas while keeping the core design intact.[1]

```markdown
# Skill Execution Enforcement v3.1 - Solution Document

## Problem Statement

LLM loads skill documentation via Skill tool, then provides its own analysis instead of executing the skill's designated workflow. The skill *appears* executed, but the actual execution pattern was never followed. [file:26]

**Evidence:**
```json
{"event": "violation", "skill": "rca", "required": ["Bash", "Task"],
 "used": ["Bash", "Edit", "Glob", "Read", "Task"],
 "pattern": "rca|RCAEngine|analyze"}
```

LLM used Bash and Task, but commands didn't match the required execution pattern for `/rca`. [file:26]

## Current Architecture

| Component                | File                                 | Purpose                                          | Timing     |
|-------------------------|--------------------------------------|--------------------------------------------------|------------|
| Skill Enforcement Gate  | `skill_enforcement_gate.py`          | Forces Skill tool usage before Bash/Write        | PreToolUse |
| Skill Execution Tracker | `posttooluse/skill_execution_tracker.py` | Tracks tool usage after skill load          | PostToolUse|
| Skill Execution Gate    | `StopHook_skill_execution_gate.py`   | Validates execution pattern was followed         | Stop       |

[file:26]

## Gap Analysis

```text
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

**Root Cause:** Execution validation happens at Stop (post‑hoc), not PreToolUse (real‑time). [file:26]

## Solution: PreToolUse Pattern + Intent Enforcement

### Design

Move execution validation from Stop to PreToolUse. When a skill with execution requirements is loaded, validate the **first Bash/Task command** that could satisfy the contract before allowing execution. [file:26]

Additionally, make the registry the single source of truth for all enforcement metadata (patterns, tools, mode, hints, optional semantic intent), and keep Stop as a safety net. 

```text
Timeline (with fix):
  ┌─────────────────────────────────────────────────────────────────┐
  │ User: /rca hook error                                           │
  ├─────────────────────────────────────────────────────────────────┤
  │ PostToolUse: Skill("rca") loaded → set state with pattern       │
  │                                                                 │
  │ PreToolUse: Bash "python -m __lib.test_hook"                    │
  │   → Regex check: does NOT match required pattern                │
  │   → Optional intent check: "Is this actually RCA execution?"    │
  │   → BLOCK: "Command doesn't match RCA execution pattern"        │ ← Early enforcement
  │                                                                 │
  │ LLM corrects: Bash "python -c 'from src.rca...'"                │
  │   → Regex check: matches                                        │
  │   → ALLOW                                                       │
  └─────────────────────────────────────────────────────────────────┘
```

## Registry Contract

Extend `SKILL_EXECUTION_REGISTRY` to encode all enforcement behavior per skill:

```python
SKILL_EXECUTION_REGISTRY = {
    "rca": {
        "tools": ["Bash", "Task"],
        # Use bounded / anchored patterns where possible
        "pattern": r"\\b(simple_rca_engine|rca)\\b",
        # "any" → first matching tool satisfies; "all" → require all tools
        "mode": "any",
        # Hint injected into block reason for this skill
        "hint": "Execute the RCA engine code from the skill's ⚡ EXECUTION DIRECTIVE section.",
        # Optional: enable semantic intent check via daemon/LLM
        "intent_enabled": True,
    },
    # other skills...
}
```

Notes:

- **Pattern**: Prefer word boundaries or module/class names (`simple_rca_engine`) instead of generic terms like `analyze`. This reduces false positives and makes behavior more robust to incidental text. 
- **Mode**: Keeps v3 behavior (`"any"`) but allows future skills to require multiple tools (`"all"`).
- **Hint**: Keeps hook code generic; all skill‑specific guidance is in the registry.
- **Intent flag**: Controls whether to call a daemon/LLM classifier as a semantic override when regex fails.

## Implementation

### Phase 1: Merge registries

Import `SKILL_EXECUTION_REGISTRY` from `StopHook_skill_execution_gate.py` into `skill_enforcement_gate.py` so there is a single source of truth.

```python
# skill_enforcement_gate.py
from StopHook_skill_execution_gate import SKILL_EXECUTION_REGISTRY
```

[file:26]

### Phase 2: Extend state schema

When a skill is loaded, include the execution requirement in state. For now we assume one "pending" skill at a time; this can be generalized later to per‑skill state.

```python
# PostToolUse handler for Skill tool
def handle_post_tool_use(data: dict) -> dict:
    skill = extract_skill_name(data)

    # Check if skill has execution requirements
    exec_config = SKILL_EXECUTION_REGISTRY.get(skill)
    if exec_config:
        state = {
            "skill": skill,
            "phase": "pending_execution",
            "required_tools": exec_config.get("tools", []),
            "required_pattern": exec_config.get("pattern"),
            "mode": exec_config.get("mode", "any"),
            "execution_satisfied": False,
            "satisfied_tools": [],
            "timestamp": time.time(),
        }
        write_state(state)

    return {}
```

[file:26]

### Phase 3: PreToolUse pattern + optional intent validation

```python
# skill_enforcement_gate.py

def _extract_command(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        return tool_input.get("command", "") or ""
    if tool_name == "Task":
        return tool_input.get("prompt", "") or ""
    return ""

def _intent_says_ok(state: dict, tool_name: str, command: str) -> bool:
    """Optional semantic override via daemon/LLM intent classifier.

    Returns True if policy model decides this command still counts as
    correct execution for the pending skill, even if regex failed.
    """
    # This is intentionally thin; actual implementation lives in the daemon.
    exec_config = SKILL_EXECUTION_REGISTRY.get(state.get("skill", ""))
    if not exec_config or not exec_config.get("intent_enabled"):
        return False

    try:
        return query_skill_policy_daemon({
            "skill": state.get("skill"),
            "tool_name": tool_name,
            "command": command,
            "required_pattern": state.get("required_pattern"),
        })
    except Exception:
        # Fail closed to the regex decision; we rely on hard constraints.
        return False

def handle_pre_tool_use(data: dict) -> dict:
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    state = read_pending_state()
    if not state or state.get("execution_satisfied"):
        # No pending skill or already satisfied
        return {}

    required_tools = state.get("required_tools", [])
    required_pattern = state.get("required_pattern")
    mode = state.get("mode", "any")

    # Only enforce on tools that can satisfy the execution contract
    if tool_name not in required_tools:
        return {}  # Allow

    command = _extract_command(tool_name, tool_input).strip()

    # If no pattern configured, treat this as satisfying the requirement
    if not required_pattern or not command:
        return _mark_satisfied(state, tool_name)

    # Regex check with case-insensitive search
    if not re.search(required_pattern, command, re.IGNORECASE):
        # Optional semantic intent layer
        if not _intent_says_ok(state, tool_name, command):
            skill = state.get("skill", "unknown")
            snippet = command[:160] + ("..." if len(command) > 160 else "")
            exec_config = SKILL_EXECUTION_REGISTRY.get(skill, {})
            hint = exec_config.get("hint") or \
                "Execute the code specified in the skill's ⚡ EXECUTION DIRECTIVE section."

            return {
                "decision": "block",
                "reason": f"""⚠️ SKILL EXECUTION PATTERN MISMATCH

The /{skill} skill requires commands matching: `{required_pattern}`

Your command:
```text
{snippet}
```

This doesn't match the required execution pattern.

{hint}

Do NOT run investigation commands (e.g., test_hook, grep, ls) as a substitute for the required execution."""
            }

    # Pattern matched or semantic override accepted → mark satisfied
    return _mark_satisfied(state, tool_name)


def _mark_satisfied(state: dict, tool_name: str) -> dict:
    mode = state.get("mode", "any")
    satisfied_tools = state.get("satisfied_tools", [])

    if tool_name not in satisfied_tools:
        satisfied_tools.append(tool_name)

    if mode == "all":
        required_tools = set(state.get("required_tools", []))
        if required_tools.issubset(set(satisfied_tools)):
            state["execution_satisfied"] = True
    else:
        # "any" (default) → first satisfying tool is enough
        state["execution_satisfied"] = True

    state["satisfied_tools"] = satisfied_tools
    state["satisfied_by"] = tool_name
    state["satisfied_at"] = time.time()
    write_state(state)

    return {}  # Allow
```

Key properties:

- Regex is the **hard constraint**, using bounded/anchored patterns where possible.
- Optional daemon/LLM intent layer provides **semantic override** for legitimate variants that patterns miss, but cannot weaken the hard gate when it fails.
- `mode` lets future skills require all tools in a sequence without changing the hook.

### Phase 4: Simplify Stop hook

With PreToolUse enforcement, the Stop hook becomes a safety net and monitoring point. [file:26]

```python
# StopHook_skill_execution_gate.py

def handle_stop(data: dict) -> dict:
    state = read_state()
    if not state:
        return {}

    if state.get("execution_satisfied"):
        clear_state()
        return {}

    # This should rarely happen with PreToolUse enforcement
    log_event("late_violation", {
        "skill": state.get("skill"),
        "note": "PreToolUse enforcement should have caught this",
    })

    clear_state()
    return {
        "decision": "block",
        "reason": "Skill execution incomplete (fallback enforcement). "
                  "A required execution step was never observed for the pending skill."
    }
```

## Files to Modify

| File                                 | Change                                           |
|--------------------------------------|--------------------------------------------------|
| `skill_enforcement_gate.py`          | Add pattern + optional intent validation in PreToolUse |
| `StopHook_skill_execution_gate.py`   | Simplify to safety net role                      |
| `posttooluse/skill_execution_tracker.py` | Extend state schema to include mode and satisfied_tools |

[file:26]

## Testing Strategy

1. **Unit tests**  
   - Pattern matching for each skill in `SKILL_EXECUTION_REGISTRY` (including word boundaries and negative cases).  
   - `mode: "any"` vs `mode: "all"` behavior.

2. **Integration tests**  
   - `/rca` → wrong command (`test_hook`, `ls`, etc.) → PreToolUse block with clear reason.  
   - `/rca` → correct execution command → allowed, `execution_satisfied == True`.  

3. **Intent layer tests (if daemon enabled)**  
   - Regex fails but daemon returns `True` → command allowed, state satisfied.  
   - Daemon errors → we fall back to regex (fail closed).

4. **Regression tests**  
   - Skills without patterns still work (no enforcement).  
   - Read/Grep/Glob and other investigation tools remain unaffected.

## Rollback

Set environment variable to disable enforcement:

```bash
SKILL_PATTERN_ENFORCEMENT_ENABLED=false
```

Hook should short‑circuit to no‑op when this flag is false.

[file:26]

## Reversibility

**[R:2]** – Minor refactoring, affects hook behavior only. Can disable via env var without code changes. [file:26]

## Success Criteria

1. `/rca` with substitute analysis (no engine execution) → blocked at PreToolUse.  
2. `/rca` with correct execution → allowed, `execution_satisfied == True`.  
3. Stop hook violation rate drops to near-zero (only genuine edge cases).  
4. No false positives on investigation commands (Read, Grep, Glob still allowed).  
5. Registry changes (patterns, hints, mode) do not require hook code changes.

[file:26]

## Future Extensions

- **Per-skill or per-instance state**  
  Generalize `read_pending_state` to support multiple simultaneous pending skills, keyed by `skill` (and optionally a session/turn ID).

- **Central policy daemon**  
  Move `_intent_says_ok` logic into a long‑lived ML/LLM policy service that all hooks query, so routing/enforcement can evolve without touching hook code.

- **Metrics and tuning**  
  Use `skill_execution_gate.jsonl` to measure how often enforcement blocks, how often the daemon overrides, and refine patterns and registry entries accordingly.

[file:26]
```

## Human

What good ideas exist in repos that we can use for this?

## Assistant

Excellent repos and community patterns exist that you can adapt. Here are the best ideas for your skill enforcement system:

## 1. **decider/claude-hooks** - Code Quality Validator Pattern[1]

**What they do:**
- PreToolUse hooks that **block** tool execution when code quality rules are violated
- Uses hierarchical `.claude-hooks.json` configs (root + per-directory overrides)
- "Dispatcher pattern": `universal-*.py` routers call specific hook handlers
- JSON stdin/stdout for all hook communication

**Apply to your system:**
```python
# In your PreToolUse handler, adapt their hierarchical config pattern:
def load_enforcement_config(tool_context):
    """Load nearest .skill-enforcement.json walking up from current file."""
    # Start with root .claude/hooks/skill_registry.json
    # Override with project-specific .skill-enforcement.json if present
    # This lets different repos have different enforcement strictness
    return merged_config
```

Benefits: Teams can customize enforcement per project without changing hook code.[1]

## 2. **Cupcake/eqtylab** - OPA/Rego Policy Layer[2][3]

**What they do:**
- Separate **policy engine** (OPA/Rego) from hook runtime
- Hooks call the policy engine via API: "Should I allow this command?"
- Policy rules live in declarative `.rego` files, not Python

**Apply to your system:**
Your "daemon with ML model" idea maps directly here. Instead of embedding policy in hook code:

```python
# skill_enforcement_gate.py
def handle_pre_tool_use(data):
    # ...
    if required_pattern and command:
        # Call policy daemon (local or network)
        decision = query_policy_engine({
            "skill": skill,
            "tool": tool_name,
            "command": command,
            "pattern": required_pattern,
        })
        
        if decision["allow"] == False:
            return {"decision": "block", "reason": decision["reason"]}
```

Benefits: Evolve enforcement logic (regex → ML classifier → LLM intent) without touching hook code.[3][2]

## 3. **Code Pulse / Skill Activation Hooks** - File-based Skill Triggers[4][5]

**What they do:**
- `skill-rules.json` maps file path patterns to skills:
  ```json
  {
    "rca": {
      "fileTriggers": {
        "pathPatterns": ["*.log", ".claude/logs/**", "errors/**"]
      }
    }
  }
  ```
- UserPromptSubmit hook checks open files against patterns
- Auto-suggests relevant skill: "Looks like you're in logs/ — load /rca skill?"

**Apply to your system:**
Add context-based auto-enforcement:

```python
# UserPromptSubmit hook
def handle_user_prompt_submit(data):
    open_files = get_open_files(data)
    
    # Check if files match RCA context
    if any(matches_pattern(f, ["*.log", "errors/**"]) for f in open_files):
        # Pre-load RCA skill state so enforcement is ready
        return {
            "hookSpecificOutput": {
                "additionalContext": "Working with log files. Consider using /rca skill for root cause analysis."
            }
        }
```

Benefits: Proactive enforcement — hooks "know" when RCA is likely needed and arm the enforcement layer early.[5][4]

## 4. **levnikolaevich/claude-code-skills** - Multi-Phase Worker Pattern[6]

**What they do:**
- Skills organized as **L2 Coordinators** and **L3 Workers**
- Coordinator skill delegates to specialized worker skills in parallel
- Each worker has a `version` and `purpose` field in metadata
- "Fail Fast principle" — critical validators run FIRST

**Apply to your system:**
Extend your registry for multi-step enforcement:

```python
SKILL_EXECUTION_REGISTRY = {
    "rca": {
        "tools": ["Bash", "Task"],
        "pattern": r"\b(simple_rca_engine|rca)\b",
        "mode": "sequence",  # NEW: enforce ordered execution
        "phases": [
            {"name": "observe", "tools": ["Read", "Grep"], "required": True},
            {"name": "execute", "tools": ["Bash"], "pattern": r"\brca\b", "required": True},
            {"name": "report", "tools": ["Task"], "pattern": r"RCA Summary", "required": True},
        ],
        "fail_fast": True,  # Block at first phase violation
    }
}
```

Benefits: Complex skills (like RCA) have multi-step workflows that hooks can enforce sequentially.[6]

## 5. **Anthropic hook-development/patterns.md** - Permission Decision API[7][8]

**What official docs show:**
- PreToolUse can return `"allow"` to **bypass permission prompts** for trusted commands
- PostToolUse can return `"block"` with `reason` to **auto-prompt Claude** with corrective guidance
- Stop can return `"block"` with `reason` to prevent Claude from finishing

**Apply to your system:**
Use `permissionDecision: "allow"` when pattern matches:

```python
def handle_pre_tool_use(data):
    # ... pattern validation ...
    
    if pattern_matches:
        return {
            "permissionDecision": "allow",  # Skip user prompt
            "permissionDecisionReason": f"/{skill} execution pattern validated by hook"
        }
    else:
        return {
            "decision": "block",
            "reason": f"Command doesn't match /{skill} execution pattern"
        }
```

Benefits: Validated commands flow through instantly; invalid commands are blocked with clear guidance.[8][7]

## 6. **Session Hooks + Strike/Praise Pattern** - Feedback Loop[5]

**What they do:**
- SessionStart hook injects context (git log, pending tasks) into CLAUDE.md dynamically
- CSV-based "strike/praise" log tracks prompt effectiveness over time
- Hook evaluates: "Did last turn succeed or fail its objective?"

**Apply to your system:**
Track enforcement effectiveness:

```python
# PostToolUse hook after skill execution
def log_enforcement_outcome(skill, command, outcome):
    """
    outcome: "pattern_matched" | "intent_override" | "blocked"
    """
    log_entry = {
        "timestamp": time.time(),
        "skill": skill,
        "command_snippet": command[:100],
        "outcome": outcome,
        "pattern": SKILL_EXECUTION_REGISTRY[skill]["pattern"],
    }
    append_to_jsonl(".claude/logs/skill_enforcement_outcomes.jsonl", log_entry)
```

Then create a feedback skill that reviews the log and suggests pattern improvements.[5]

## 7. **Disler's Universal Dispatcher Pattern**[9]

**What they do:**
- Single `universal_hook.py` receives all hook events
- Routes to specialized handlers based on event type and context
- Centralized error handling and logging

**Apply to your system:**
Consolidate your enforcement hooks:

```python
# universal_skill_enforcement.py
def main():
    event_data = json.loads(sys.stdin.read())
    event_type = event_data.get("hookEventName")
    
    handlers = {
        "PostToolUse": handle_skill_load,      # Track skill state
        "PreToolUse": handle_pattern_check,    # Enforce execution
        "Stop": handle_completion_check,       # Safety net
    }
    
    handler = handlers.get(event_type, lambda x: {})
    result = handler(event_data)
    print(json.dumps(result))
```

Benefits: Single entry point, easier testing, shared utilities across all enforcement events.[9]

## Recommended Implementation Stack

Combining these patterns:

```
┌─────────────────────────────────────────────────────────────┐
│ USER QUERY (/rca hook error)                                │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ UserPromptSubmit Hook (Code Pulse pattern)                  │
│ - Check open files against skill-rules.json                 │
│ - If log files present → inject RCA context hint            │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ PostToolUse: Skill("rca") loaded                            │
│ - Set pending_execution state with hierarchical config      │
│   (decider pattern + Code Pulse)                            │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ PreToolUse: Bash command                                    │
│ - Regex pattern check (word boundaries)                     │
│ - If fail → query policy daemon (Cupcake pattern)           │
│   - Daemon uses ML/LLM intent classifier                    │
│   - Returns allow/deny + reason                             │
│ - If deny → block with permissionDecisionReason             │
│   (Anthropic official pattern)                              │
│ - If allow → log outcome (Strike/Praise pattern)            │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ Stop Hook: Safety net                                       │
│ - Check execution_satisfied                                 │
│ - If false → block with reason (rare with PreToolUse gate)  │
│ - Log late_violation for monitoring                         │
└─────────────────────────────────────────────────────────────┘
```

This gives you: deterministic regex gates, semantic intent override, hierarchical config, feedback loops, and a central policy brain.[7][4][2][3][9][6][1][5]
