---
title: "Is there a bug with claude code 2.1.76+ for tools_used[]?  '
❯ '
● Ran 1 stop hook (ctrl+o to expand)
  ⎿  Stop hook "
date: "2026-03-14"
mode: "COPILOT"
uuid: "37df9590-b52c-4d7b-96f6-3d271402de42"
entry_count: 4
---

## Human

Is there a bug with claude code 2.1.76+ for tools_used[]?  "
❯ "
● Ran 1 stop hook (ctrl+o to expand)
  ⎿  Stop hook error: SLASH COMMAND IGNORED

  The user invoked /arch but you did not call the Skill tool.

  Your first action MUST be:
    Skill(skill="arch")

  Do NOT read files, run scripts, or provide analysis before calling Skill.
  Do NOT interpret slash commands as conversational requests.
  Call Skill("arch") now, then follow its instructions.

● Skill(arch)
  ⎿  Successfully loaded skill

● 📍 /arch [STANDARD enforcement]", we seem to be stuck in this hook loop.  Please debug.  We do have logs if you want to
look at them.

● Read 3 files (ctrl+o to expand)

● Let me look at the arch skill and the logs:

● Searched for 1 pattern, read 2 files (ctrl+o to expand)

● Found it. The log tells the whole story — every event shows "tools_used": [] even when Claude did call Skill("arch"). Let
   me look at why transcript parsing is losing the tool calls:

  Reading 1 file… (ctrl+o to expand)
  ⎿  .claude\\hooks\\StopHook_skill_execution_gate.py
"

## Assistant

Yes, this is almost certainly a regression in how hooks receive `tools_used` in 2.1.76+ (or in your specific build range), and your stop hook logic is behaving correctly given bad input. The loop you’re seeing is the natural consequence of `tools_used` always being `[]` for that StopHook event, so the hook keeps thinking “Skill was never called” and re-enforcing `/arch` every time.[1]

### What is actually going wrong

From what you described:

- The user sends `/arch`.[1]
- Claude correctly calls `Skill("arch")` in the main transcript (you can see this in the UI).[1]
- However, every stop-event log entry your hook sees has `"tools_used": []`, even on turns where the transcript clearly contains a `Skill("arch")` tool call.[1]
- Your `StopHook_skill_execution_gate.py` then checks `tools_used` to verify that `Skill("arch")` was used for that request, finds an empty list, and:
  - prints “SLASH COMMAND IGNORED… The user invoked /arch but you did not call the Skill tool… Call Skill("arch") now…”, and  
  - exits non‑zero (or returns a “block” decision), which causes Claude to re-run the enforcement path and re-enter the exact same branch.[1]

So you’re not in a “prompt loop” inside the model; you’re in a deterministic hook loop where the state your hook reads (`tools_used`) is inconsistent with the actual transcript.

### Why this smells like a Claude Code bug, not just your hook

FACTS / CONSENSUS:

- Hooks are documented to receive a structured JSON payload that includes `tools_used` for each lifecycle event where tools may have been called.[1]
- `tools_used` is supposed to reflect tools actually invoked during that *event*, not globally since session start.[1]
- Recent releases mention several hook-related fixes (e.g., wrong `transcript_path` for resumed/forked sessions, async hooks not getting stdin, etc.), which indicates that hook plumbing has been actively changed and is a source of regressions.[2]

SPECULATION (mid confidence):

- In 2.1.76+ a change in the transcript/compaction or hook-input plumbing likely stopped populating `tools_used` for some StopHook events, particularly where:
  - the tool invocation was inside a subagent (e.g., agent hooks, teammates, or skills), or  
  - `ToolSearch` or other intermediaries changed how tool calls are represented before hooks run.[2][1]
- Alternatively, `tools_used` may have been narrowed to only include a certain subset of tools (e.g., built-ins) and is currently omitting Skill calls from its list for StopHook events.

Given your description that “every event shows `tools_used: []` even when Claude did call Skill("arch")”, either:

1. The StopHook you’re using runs earlier / later than you expect, on a different internal ‘turn’ than the one with the Skill call; or  
2. The StopHook’s payload is simply wrong in this build and no longer carries tool usage into that event.

From a deterministic StopHook’s perspective, both look like “bug in Claude Code,” because there’s no way for your hook to reconstruct real tool usage without the platform giving it.

### How to confirm it’s a platform bug vs hook logic

In your place I’d do three quick checks:

1. **Log the entire hook input for StopHook.**  
   In `StopHook_skill_execution_gate.py`, before any logic, dump `json.dumps(input_data, indent=2)` to a log file (not just stderr) so you can see:  
   - the `event` name  
   - the full `transcript` or `messages` payload  
   - `tools_used` as the platform sends it  
   If the transcript clearly includes a `tool_use` block for `Skill("arch")` in that event’s last assistant turn, but `tools_used` is `[]`, that’s a platform bug.[1]

2. **Verify the event you’re hooking.**  
   Make sure you’re on the documented StopHook event name for “end of turn when tools have just run” (check the hooks reference for exact names; there are several lifecycle points).[1]
   If you’re accidentally on a later event (e.g., after compaction or after a subagent finishes), the empty `tools_used` may be “by design” for that late phase, and you should move your gate to a PreToolUse or immediate PostToolUse hook instead.[1]

3. **Try a minimal repro without your parser.**  
   Configure a trivial StopHook that just logs `tools_used` and exits 0. Trigger `/arch` and confirm:  
   - UI shows a `Skill(arch)` call  
   - Hook input shows `tools_used: []`  
   If so, you have a clean repro you can attach to a bug report.

### Why your current logic causes the “hook loop”

Given that your hook:

- Detects `/arch` in the user message  
- Requires that the same event’s `tools_used` contains `Skill("arch")`  
- Treats absence of that tool as a hard failure and re-prompts “Call Skill('arch') now”  

…then as long as `tools_used` is empty on that event, you will always:

- Block the turn  
- Re-inject the enforcement instruction  
- Trigger another agent run that again leads to a stop hook with `tools_used: []`  
- Repeat indefinitely.

Your code is doing exactly what you told it to do, given the inputs. The broken piece is the input.

### Practical mitigations until Anthropic fixes it

Until there is an upstream fix, you have a few options:

1. **Relax the gate condition.**  
   Instead of relying solely on `tools_used`, use the transcript as a secondary source of truth:  
   - Inspect the last assistant message for a `Skill("arch")` tool_use block (or equivalent in the model’s tool schema).  
   - Treat that as “skill was used” regardless of `tools_used`.  
   This makes your gate more robust to `tools_used` regressions.

2. **Short-circuit after one enforcement.**  
   Add a cheap state guard like “if we’ve already emitted the enforcement warning once in this message, don’t re-emit it,” using:  
   - a marker comment inserted into the system/assistant text, or  
   - a log-backed dedupe keyed by session+turn ID.  
   This avoids infinite loops even when `tools_used` is bad.

3. **Temporarily downgrade or disable this StopHook.**  
   If `/arch` enforcement is helpful but not critical, you can:
   - turn this StopHook into a PreToolUse or UserPromptSubmit hook that only *reminds* Claude to call the skill, without blocking when it doesn’t see evidence that it did; or  
   - disable it for now and rely on the `/arch` slash command’s natural behavior.

4. **Report with a minimal repro.**  
   Given the very recent hook fixes in the changelog, this is the kind of regression that’s likely to get fixed quickly once they see a clear repro.[2]
   Include:
   - your Claude Code version  
   - the exact hook config from `.claude/settings.json`  
   - the full StopHook payload JSON showing `tools_used: []` while the transcript contains `Skill("arch")`.

### My recommended concrete next step

The most actionable step right now:

- In `StopHook_skill_execution_gate.py`, log the full event payload for a simple `/arch` invocation and confirm that `tools_used` is empty while the transcript shows `Skill("arch")`.  
- If that’s true, treat `tools_used` as unreliable for this event and switch your gate to inspecting the transcript directly, plus add a “only warn once” guard so you never loop.

If you paste the relevant parts of:

- your StopHook config (from `.claude/settings.json`), and  
- one full hook input JSON blob where `/arch` was used but `tools_used: []`  

I can walk through and suggest a precise patch to `StopHook_skill_execution_gate.py` that both avoids the loop and keeps reasonable enforcement.

What’s the exact StopHook event name you’re using for this gate (`StopHook`, `PostToolUse`, or something more specific)?  

## Human

are there documented issues?

## Assistant

There is no publicly documented, specific “`tools_used` is always [] for Stop hooks in 2.1.76+” bug in the official docs or issue trackers that I can see right now.[1][2]

### What is documented

- The hooks reference describes common fields for events (including `tools_used` in examples and derived tooling), but does not currently call out any known defect where `tools_used` is missing or empty for Stop/Task events.[3][1]
- There are several open/closed GitHub issues about hook payloads being incomplete or inconsistent (e.g., PostToolUse not receiving expected fields, such as `tool_response` or `cwd`). This shows that hook payload regressions do happen and are being tracked, but none exactly match “Skill tools never appear in `tools_used` for Stop hooks”.[4][5]

### Related but not identical issues

- One bug report shows PostToolUse hooks not getting proper Task tool outputs (`tool_response` empty), i.e., hooks being invoked but with missing data.[4]
- Another documents PostToolUse omitting the `cwd` field despite the docs promising it.[5]
- Community posts also mention hook errors or unexpected behavior after recent updates, suggesting some instability in the hooks layer generally.[6]

These are all *analogous* to what you’re seeing—hooks firing with incomplete payloads—but none of them explicitly mention `tools_used` being always empty.

### What this means for you

- From available public sources, there is no confirmed, documented bug that “StopHook’s `tools_used` is always [] in Claude Code 2.1.76+” yet.[2][1][5][4]
- However, given:
  - your local evidence (Skill clearly called, logs show `tools_used: []`), and  
  - the pattern of other hook payload fields being missing/incorrect in recent versions,  
  it is highly plausible you are hitting a new, not-yet-documented regression.  

So I would treat your case as a *new bug* and file it, referencing the existing pattern of “hooks invoked with missing fields” issues as precedent.

If you’re willing to, the most useful next step is to capture and share (sanitized) one full Stop-hook JSON payload for a `/arch` run where the transcript shows `Skill("arch")` but `tools_used` is `[]`; that will make your report much more actionable.  

## Human

no reddit or other social comments about this?

## Assistant

I can’t find any Reddit / social posts describing *this exact* `tools_used: []` + StopHook + `/arch` loop symptom yet.[1][2]

### What does exist

- There are Reddit posts and comments about Stop hooks “triggering too often”, causing loops or repeated enforcement, but they focus on mis-handling `stop_hook_active` or blocking logic—not on `tools_used` being empty while tools clearly ran.[3][1]
- Several GitHub issues and blog posts discuss hook payload fields being missing or inconsistent (e.g., PostToolUse hooks not firing or missing fields like `cwd` or tool outputs), but again not specifically `tools_used` being always `[]`.[4][5][6]

### Implication

So far, your `tools_used: []` + StopHook + skill-enforcement-loop looks like a new or at least not-yet-noised-about regression, rather than something widely recognized in the community.[2][3]

Would you like a small patch sketch for `StopHook_skill_execution_gate.py` that (a) inspects the transcript directly instead of trusting `tools_used`, and (b) uses `stop_hook_active` to hard‑prevent infinite loops?  

## Human

Yes, show me a robust patch for the stop hook

## Assistant

Here’s a concrete, defensive pattern you can drop into `StopHook_skill_execution_gate.py` to both avoid the loop and stop trusting `tools_used` as a single source of truth. I’ll show it in three parts so you can adapt.[1][2]

### 1. High-level behavior

This Stop hook will:

- Immediately exit if `stop_hook_active` is true (prevents infinite loops).[2][1]
- Parse the last user message to see if they actually invoked `/arch`.  
- Check for `Skill("arch")` **both** via `tools_used` and by scanning the last assistant message’s tool calls.  
- If `/arch` was requested but no evidence of `Skill("arch")` is found, it will:
  - emit a short enforcement message to stderr (fed back to Claude), and  
  - return a JSON decision `{ "decision": "block", "reason": "..." }` on stdout so Claude continues working.  
- Otherwise, it exits 0 and does nothing.

### 2. Example Stop hook implementation (Python)

Assuming the hook is invoked with the event JSON on stdin and you write JSON to stdout:

```python
#!/usr/bin/env python3
import json
import sys

def read_input():
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception as e:
        print(f"StopHook error: failed to parse input JSON: {e}", file=sys.stderr)
        return {}

def last_item(seq):
    return seq[-1] if isinstance(seq, list) and seq else None

def user_invoked_arch(event):
    """Detect /arch in the last user message."""
    messages = event.get("messages") or event.get("transcript") or []
    last_msg = last_item(messages)
    if not last_msg:
        return False

    # Claude Code Stop hook payloads typically have {role, content}
    if last_msg.get("role") != "user":
        # Maybe messages are full convo; find last user instead
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_msg = msg
                break

    content = last_msg.get("content") or ""
    if isinstance(content, list):
        # Some payloads use structured content; flatten text
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text") or "")
        content = "\n".join(text_parts)
    return isinstance(content, str) and "/arch" in content

def tools_used_contains_arch(event):
    tools_used = event.get("tools_used") or []
    for t in tools_used:
        # Depending on shape: {"name": "Skill", "tool_name": "arch"} or similar
        name = t.get("name") or t.get("tool") or ""
        tool_name = t.get("tool_name") or t.get("skill") or ""
        if name.lower() == "skill" and tool_name.lower() == "arch":
            return True
    return False

def transcript_contains_arch_skill(event):
    """
    Fallback: scan last assistant message for a Skill(arch) tool call,
    in case tools_used is empty/buggy.
    """
    messages = event.get("messages") or event.get("transcript") or []
    last_assistant = None
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            last_assistant = msg
            break
    if not last_assistant:
        return False

    content = last_assistant.get("content") or ""
    # Two patterns:
    # 1) Structured tool_use blocks in content list
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "tool_use":
                name = part.get("name") or ""
                if name.lower() == "skill":
                    tool_input = part.get("input") or {}
                    skill_name = (
                        tool_input.get("skill")
                        or tool_input.get("name")
                        or ""
                    )
                    if isinstance(skill_name, str) and skill_name.lower() == "arch":
                        return True
    # 2) Fallback: plain-text mention like 'Skill("arch")'
    elif isinstance(content, str):
        if "Skill(\"arch\")" in content or "Skill('arch')" in content:
            return True

    return False

def main():
    event = read_input()

    # 1) Hard guard: avoid infinite loops
    if event.get("stop_hook_active"):
        # Once we're already in a forced continuation, don't enforce again
        print("StopHook: stop_hook_active is true, exiting early", file=sys.stderr)
        sys.exit(0)

    # 2) If user didn't invoke /arch, nothing to enforce
    if not user_invoked_arch(event):
        sys.exit(0)

    # 3) Check for evidence that Skill("arch") was used
    arch_via_tools_used = tools_used_contains_arch(event)
    arch_via_transcript = transcript_contains_arch_skill(event)

    if arch_via_tools_used or arch_via_transcript:
        # All good
        sys.exit(0)

    # 4) Enforcement: user asked for /arch, but no Skill("arch") observed
    reason = (
        "The user invoked /arch, but you did not call Skill(\"arch\"). "
        "Call Skill(skill=\"arch\") as your first action, then follow its instructions."
    )

    # stderr goes back to Claude as feedback
    print(
        "SLASH COMMAND IGNORED: /arch was used but no Skill(\"arch\") tool call "
        "found in this turn. Enforcing Skill(\"arch\") usage.",
        file=sys.stderr,
    )

    # stdout JSON controls the decision for Stop hooks
    decision = {"decision": "block", "reason": reason}
    sys.stdout.write(json.dumps(decision))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

This implements:

- Loop prevention via `stop_hook_active`.[1][2]
- Dual-path detection of `Skill("arch")` (via `tools_used` and transcript scan), making you resilient to the suspected `tools_used` regression.[3][2]

### 3. Recommended minimal differences vs your current hook

Relative to what you likely have now:

- **Add the `stop_hook_active` early-return:**  
  This alone should break the infinite loop pattern documented in the official hooks guide.[2][1]
- **Replace “`if not tools_used_contains_arch` then block” with the combined check:**  
  Use `if not (arch_via_tools_used or arch_via_transcript)` so the hook succeeds even when `tools_used` is empty but the transcript shows a proper Skill call.  
- **Log more, but cheaply:**  
  You can sprinkle a `debug` flag and, if enabled, write the entire `event` JSON to `~/.claude/stop-arch-debug.log` for a few runs to validate the shape you’re actually getting.

If you paste your current `StopHook_skill_execution_gate.py`, I can rewrite it as a minimal diff patch rather than a full replacement so you don’t lose any of your existing behavior.  
