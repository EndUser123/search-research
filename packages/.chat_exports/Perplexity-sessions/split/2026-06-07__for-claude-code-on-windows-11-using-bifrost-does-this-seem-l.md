---
title: "For claude code on windows 11, using bifrost, does this seem like it will work?
'# Context Window Resilience Implementat"
date: "2026-06-07"
mode: "COPILOT"
uuid: "ced647a1-4efa-49c8-bfc7-71013089df9b"
entry_count: 3
---

## Human

For claude code on windows 11, using bifrost, does this seem like it will work?
"# Context Window Resilience Implementation Plan


> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.


**Goal:** Prevent Claude Code/Bifrost runs from halting on context-window overflow by classifying the failure, checkpointing a compact continuation packet, and reinjecting only a bounded resume context on the next turn.


**Architecture:** Treat context-window overflow as a retryable orchestration event, not a task failure. The ai-api layer owns overflow detection and compact continuation packet emission. The hook layer owns bounded resume injection and expiry. Both sides share a small JSON state contract so a resumed turn starts with the current goal, current task, recent decisions, and active files, not the full transcript.


**Tech Stack:** Python, existing hook registry, JSON state files, pytest, `requests`, `pathlib`.


---


### Task 1: Classify overflow and emit a continuation packet in ai-api


**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/context_window_guard.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/bf_agent.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_bf_agent.py`


- [ ] **Step 1: Write the failing tests for overflow classification and one retry after overflow.**


```python
def test_context_window_error_is_classified():
    assert bf_agent._is_context_window_error(
        "API Error: The model has reached its context window limit."
    )



def test_bifrost_call_retries_once_after_context_window_limit(monkeypatch, tmp_path):
    calls = []


    def fake_bifrost_call(*args, **kwargs):
        calls.append(kwargs.get("prompt", args[1] if len(args) > 1 else ""))
        if len(calls) == 1:
            return {
                "ok": False,
                "error": "The model has reached its context window limit.",
                "text": "",
                "error_type": "ContextWindowLimit",
            }
        return {"ok": True, "text": "resumed answer", "error": None, "error_type": ""}


    monkeypatch.setattr(bf_agent, "bifrost_call", fake_bifrost_call)
    result = bf_agent.run_simple(
        "review",
        "Explain the architecture risks and recover from overflow.",
        model="M3",
        route="auto",
        domain="architecture",
    )


    assert result["ok"] is True
    assert result["text"] == "resumed answer"
```


- [ ] **Step 2: Run the focused pytest target and confirm it fails for the right reason.**


Run:
```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -k "context_window or overflow" -q -p no:cacheprovider
```
Expected:
- The new overflow test fails before implementation.
- The existing non-overflow tests still pass.


- [ ] **Step 3: Implement the minimal overflow guard and continuation packet writer.**


Implement these helpers in `bf_agent.py` or `context_window_guard.py`:


```python
def _is_context_window_error(message: str | None) -> bool: ...
def _build_context_overflow_packet(...) -> dict[str, Any]: ...
def _write_context_overflow_packet(packet: dict[str, Any]) -> Path: ...
def _retry_with_compact_context(...) -> WorkerResult: ...
```


Required behavior:
- Detect the provider message `context window limit` or equivalent overflow wording.
- Write a compact packet with `model`, `route`, `domain`, `task`, `prompt_digest`, `timestamp`, and `resume_hint`.
- Retry exactly once with the compact packet instead of the full prior prompt.
- Fail open if the packet cannot be written, but still mark the error as retryable in the returned result.


- [ ] **Step 4: Re-run the targeted tests and confirm the retry path passes.**


Run:
```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -k "context_window or overflow" -q -p no:cacheprovider
python -m py_compile P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\context_window_guard.py
```
Expected:
- Overflow is classified as retryable.
- The second call succeeds using the compacted context.


- [ ] **Step 5: Commit the ai-api overflow guard once the tests are green.**


```powershell
git add P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\context_window_guard.py P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py
git commit -m "feat: recover from context window overflow"
```


### Task 2: Add bounded resume injection in the hook layer


**Files:**
- Create: `P:/.claude/hooks/UserPromptSubmit_modules/context_window_injector.py`
- Modify: `P:/.claude/hooks/UserPromptSubmit_modules/failure_context_injector.py`
- Modify: `P:/.claude/hooks/UserPromptSubmit_modules/handoff_context_injector.py`
- Modify: `P:/.claude/hooks/UserPromptSubmit_modules/registry.py`
- Test: `P:/.claude/hooks/tests/test_context_window_injector.py`


- [ ] **Step 1: Write the failing tests for bounded injection and expiry.**


```python
def test_context_window_packet_injects_short_resume_message(tmp_path):
    packet = {
        "timestamp": time.time(),
        "model": "M3",
        "resume_hint": "Resume from checkpoint with the current task only.",
        "goal": "Prevent context-window halts.",
        "current_task": "Implement compact resume logic.",
        "active_files": ["bf_agent.py", "SessionStart.py"],
    }
    ...
    assert len(result.context) <= 1200
    assert "Resume from checkpoint" in result.context



def [REDACTED](tmp_path):
    packet = {..., "timestamp": time.time() - 4000}
    ...
    assert result == HookResult.empty()
```


- [ ] **Step 2: Run the focused pytest target and confirm it fails before implementation.**


Run:
```powershell
python -m pytest P:\.claude\hooks\tests\test_context_window_injector.py -q -p no:cacheprovider
```
Expected:
- The new injector tests fail before the module exists.


- [ ] **Step 3: Implement the new injector and register it ahead of heavier context injectors.**


Implement `context_window_injector.py` to:
- Read a small JSON packet from the existing hook state area, not the transcript.
- Inject only a short resume spine, not the full prior conversation.
- Enforce a hard character/token cap.
- Expire stale packets automatically.


Register it in `registry.py` near the existing `handoff_context_injector`, `context_summary`, and `failure_context_injector` hooks.


- [ ] **Step 4: Re-run the hook tests and confirm the payload stays bounded.**


Run:
```powershell
python -m pytest P:\.claude\hooks\tests\test_context_window_injector.py P:\.claude\hooks\tests\test_userpromptsubmit_inprocess.py -q -p no:cacheprovider
```
Expected:
- The resume message is compact.
- Stale packets disappear.
- No other hook injection path regresses.


- [ ] **Step 5: Commit the hook-layer overflow handling once the tests are green.**


```powershell
git add P:\.claude\hooks\UserPromptSubmit_modules\context_window_injector.py P:\.claude\hooks\UserPromptSubmit_modules\failure_context_injector.py P:\.claude\hooks\UserPromptSubmit_modules\handoff_context_injector.py P:\.claude\hooks\UserPromptSubmit_modules\registry.py P:\.claude\hooks\tests\test_context_window_injector.py
git commit -m "feat: inject compact resume context after overflow"
```


### Task 3: Harden compaction summarization against empty output


**Files:**
- Modify: the active `PreCompact` hook entrypoint that emits the compaction summary
- Modify: the underlying summary builder / handoff capture module used by `PreCompact`
- Modify: `P:/.claude/hooks/tests/test_precompact_session_files.py`
- Add or modify: a dedicated `P:/.claude/hooks/tests/test_precompact_summary.py` if the current test file does not cover summary failure modes


- [ ] **Step 1: Write the failing test for an empty compaction summary.**


```python
def test_precompact_empty_summary_falls_back_to_minimal_checkpoint(monkeypatch, tmp_path):
    # Arrange: summary generator returns empty string / None.
    # Assert: PreCompact still writes a checkpoint packet and does not abort compaction.
```


- [ ] **Step 2: Run the focused pytest target and confirm the current behavior fails for the right reason.**


Run:
```powershell
python -m pytest P:\.claude\hooks\tests\test_precompact_session_files.py -q -p no:cacheprovider
```


- [ ] **Step 3: Implement a fail-open fallback when summarization returns empty output.**


Required behavior:
- Detect an empty or whitespace-only summary from the compaction summarizer.
- Preserve the pre-compact checkpoint even if the summary is empty.
- Emit a minimal structured fallback packet instead of halting compaction.
- Include the current goal, active task pointer, and active files in the fallback packet.
- Mark the event as recoverable in diagnostics so the next session can resume cleanly.


- [ ] **Step 4: Re-run the tests and confirm compaction no longer aborts on empty output.**


Run:
```powershell
python -m pytest P:\.claude\hooks\tests\test_precompact_session_files.py P:\.claude\hooks\tests\test_precompact_summary.py -q -p no:cacheprovider
```


Expected:
- Empty summarization no longer halts compaction.
- The fallback checkpoint is still written.
- The next session has a usable resume packet.


- [ ] **Step 5: Commit the compaction summarizer guard once the tests are green.**


```powershell
git add P:\.claude\hooks\tests\test_precompact_session_files.py P:\.claude\hooks\tests\test_precompact_summary.py
git commit -m "feat: fail open on empty compaction summary"
```


### Task 4: Make session startup/resume explicit and compact


**Files:**
- Modify: `P:/.claude/hooks/SessionStart.py`
- Modify: `P:/.claude/hooks/tests/test_sessionstart.py`
- Optional: Modify `P:/.claude/hooks/SessionStart_constraint_display.py` if the resume banner needs to show a budget warning


- [ ] **Step 1: Write a failing test that startup prefers the compact resume packet over a large transcript.**


```python
def test_session_start_prefers_compact_resume_packet(monkeypatch, tmp_path):
    # Arrange: existing transcript is large, but compact resume packet exists.
    # Assert: SessionStart emits only the compact resume summary and task pointer.
```


- [ ] **Step 2: Run the startup test and confirm the current behavior is still transcript-heavy.**


Run:
```powershell
python -m pytest P:\.claude\hooks\tests\test_sessionstart.py -q -p no:cacheprovider
```


- [ ] **Step 3: Update `SessionStart.py` to surface the compact packet first.**


Required behavior:
- Prefer the latest valid compact resume packet.
- Keep the startup message short and machine-readable.
- Reject stale packets and fall back to the normal session-start behavior.
- Do not re-inject the whole prior transcript.


- [ ] **Step 4: Re-run the startup tests and confirm the resume behavior stays bounded.**


Run:
```powershell
python -m pytest P:\.claude\hooks\tests\test_sessionstart.py -q -p no:cacheprovider
```
Expected:
- Startup displays a compact resume state, not a transcript dump.


- [ ] **Step 5: Commit the startup-resume refinement once the tests are green.**


```powershell
git add P:\.claude\hooks\SessionStart.py P:\.claude\hooks\tests\test_sessionstart.py
git commit -m "feat: keep session resume compact after overflow"
```


### Task 5: Verify end-to-end behavior and document the contract


**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/SKILL.md`
- Modify: `P:/.claude/hooks/README.md`
- Modify: `P:/.claude/hooks/HOOKS_CATALOG_v3.md` or the nearest canonical hooks catalog if the injector names need to be listed


- [ ] **Step 1: Run the targeted tests for both layers together.**


Run:
```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -k "context_window or overflow" -q -p no:cacheprovider
python -m pytest P:\.claude\hooks\tests\test_context_window_injector.py P:\.claude\hooks\tests\test_sessionstart.py -q -p no:cacheprovider
```


- [ ] **Step 2: Run a manual smoke test that simulates overflow and confirms the next prompt resumes from the packet.**


Use the existing ai-api command path or a small repro script that forces a `context window limit` error and verify:
- The failure is marked retryable.
- The compact packet is written.
- The next turn sees the resume spine instead of the full history.


- [ ] **Step 3: Update the docs with the exact failure signature and the recovery contract.**


Document:
- The exact overflow error string seen in practice.
- The packet filename and TTL.
- The fact that the model window itself is not increased; work is resumed in a fresh compact turn.
- The relevant env vars for turning recovery on/off or tuning the cap.


- [ ] **Step 4: Do a final diff review for stale paths and oversized context injection.**


Check for:
- Any remaining full-transcript reinjection.
- Any unbounded hook output.
- Any retry loops that could recurse indefinitely.
- Any stale references to old state-file locations.


- [ ] **Step 5: Commit the docs and verification changes.**


```powershell
git add P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\SKILL.md P:\.claude\hooks\README.md P:\.claude\hooks\HOOKS_CATALOG_v3.md
git commit -m "docs: document context window recovery contract"
```


## Coverage Check


- Overflow is detected in the ai-api layer before the task gets stuck.
- The retry path sends a compact continuation packet instead of the full prompt history.
- Empty compaction summaries fail open into a minimal fallback checkpoint instead of aborting `/compact`.
- The hook layer reinjects only a bounded resume summary.
- Session start prefers compact resume state over transcript bloat.
- The failure becomes a checkpoint, not a session-ending halt."

## Assistant

Based on my research and the implementation plan you've shared, here's my assessment:

## Overall Assessment: **Mostly viable, but with critical path issues**

The architecture is sound and aligns with how Claude Code hooks work, but there are several problems that will prevent this from working as designed on Windows 11 with Bifrost.

***

### Key Issues to Address

| Issue | Severity | Why It Matters |
|-------|----------|----------------|
| **Path inconsistency** | 🔴 Critical | Plan uses `P:/` in some places and `P:\` in others; Windows paths in the plan use forward slashes inconsistently with PowerShell paths [1] |
| **Python hooks vs Node.js requirement** | 🔴 Critical | Claude Code hooks on Windows work best with `node` (not Python) — Node.js is guaranteed available; Python may not be in PATH [1] |
| **SessionStart context injection changed** | 🟠 Medium | As of Claude Code 2.1.0, SessionStart hooks no longer display user-visible messages; context is silently injected via `hookSpecificOutput.additionalContext` [2][3] |
| **Bifrost error signature uncertain** | 🟠 Medium | The exact error string `"The model has reached its context window limit."` needs verification for your Bifrost setup; different providers use different signatures [4] |
| **Hook execution model** | 🟡 Low | Hooks run in parallel and are non-blocking; the plan assumes synchronous state file sharing which may need queue-based decoupling [3] |

***

### What Will Work

| Component | Status |
|-----------|--------|
| Overflow detection via error string matching | ✅ Works if error signature is correct |
| Compact continuation packet JSON contract | ✅ Works (portable, stateless) |
| pytest-based TDD approach | ✅ Works |
| Bounded resume injection concept | ✅ Works in principle |
| Fail-open on empty summarization | ✅ Good defensive pattern |

***

### Required Corrections

#### 1. **Use Node.js for hooks, not Python**

```json
// In settings.json, use:
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "node .claude/hooks/context_window_injector.mjs"
      }
    ]
  }
}
```

Python works only if your team has Python everywhere; Node.js is guaranteed since Claude Code requires it.[1]

#### 2. **Fix path conventions**

Your plan mixes:
- `P:/packages/.claude-marketplace/...` (forward slashes)
- `P:\packages\.claude-marketplace\...` (backward slashes)

Use `path.join()` in Node.js or `pathlib` in Python consistently.[1]

#### 3. **Update SessionStart for Claude Code 2.1.0+**

SessionStart hooks must now output JSON to `additionalContext` silently, not print visible messages:[3][2]

```javascript
// Instead of printing to stdout:
console.log("Resuming from checkpoint...");

// Output JSON for silent injection:
console.log(JSON.stringify({
  additionalContext: "Resume from checkpoint with current task only."
}));
```

#### 4. **Verify Bifrost error signature**

The exact error string depends on your Bifrost configuration and upstream provider. You need to check what your actual Bifrost setup returns:

```python
# Don't hardcode one string; check your logs:
_CONTEXT_ERROR_PATTERNS = [
    "context window limit",
    "context exceeded",
    "context length exceeded",
    "maximum context length",
]
```

***

### Architecture Validation

Your layered approach is **correct**:

| Layer | Responsibility | Status |
|-------|---------------|--------|
| ai-api layer | Detect overflow, write packet | ✅ Correct boundary |
| hook layer | Inject bounded resume | ✅ Correct boundary |
| JSON state contract | Shared contract | ✅ Good decoupling |
| PreCompact guard | Fail-open on empty | ✅ Essential resilience |

The key insight — treating context overflow as a retryable orchestration event, not a task failure — is architecturally sound.[3]

***

### One Clarifying Question

Before implementing, I need to know: **What is the actual error signature your Bifrost setup returns when hitting context window limits?**

Check your Bifrost logs for the exact `error` or `error_type` field when this happens. The plan assumes `"The model has reached its context window limit."` but your setup may return something different like `"context exceeded"` or `"too many tokens"`.[4]

## Human

"Path inconsistency", Is this a real issue?   It seems trivial to fix.
python is available and is used extensivly.
It is 6/7/2026 now, "SessionStart context injection changed", is this relevant to the latest version of claude code?
"Bifrost error signature uncertain", how confident are you of this?  Is there a way to mitigate the issue?
"Hook execution model", what's the mitigation?

## Assistant

Perfect. Now I have enough information to answer your questions directly. Let me provide the detailed analysis:

***

## Your Questions Answered

### 1. **"Path inconsistency" — Is this a real issue?**

**Answer:** Yes, but trivial to fix. It's a real issue because:

| Problem | Impact |
|---------|--------|
| `P:/` vs `P:\` mixing | Python's `pathlib` handles both, but PowerShell commands in the plan use `P:\` format |
| Cross-platform path placeholders | The plan uses literal `P:\` paths, but hooks should use `${CLAUDE_PROJECT_DIR}` for portability [1] |

**Fix:** Use `pathlib.Path()` consistently in Python, or use the path placeholders like `${CLAUDE_PROJECT_DIR}`. The plan's PowerShell commands need backslashes (`P:\path\to\file`), but Python code can use either.[1]

***

### 2. **"SessionStart context injection changed" — Is this relevant to the latest Claude Code?**

**Answer:** **Yes, absolutely relevant.** As of Claude Code 2.1.112+:

| Change | What It Means |
|--------|---------------|
| SessionStart hooks no longer display user-visible messages | Context is silently injected via `hookSpecificOutput.additionalContext` [2][3] |
| Startup performance improved by deferring SessionStart execution | Reduces time-to-interactive by ~500ms [4] |
| Version 2.1.26-2.1.30 changed SessionStart behavior | Users reported "SessionStart:startup hook error" locking sessions [5] |

**Your plan's Task 4 needs to change:**

```python
# OLD (wrong for 2.1.112+):
print("Resuming from checkpoint with current task...")

# NEW (correct):
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "Resume from checkpoint with current task only."
    }
}))
```

Reference: [Hooks reference - SessionStart](https://code.claude.com/docs/en/hooks#sessionstart)[1]

***

### 3. **"Bifrost error signature uncertain" — How confident are you? Mitigation?**

**Confidence Level:** **~70% uncertain** — I cannot verify your exact error signature without seeing your logs.

**Why uncertain:**
- Bifrost is a gateway that routes to multiple providers (Anthropic, OpenAI, etc.)[6][7]
- Different providers return different error signatures for context overflow[8][9]
- Bifrost may normalize errors or pass them through raw[7]

**Provider error signatures (from research):**

| Provider | Typical Error Signature |
|----------|------------------------|
| Anthropic/Claude | `"context window limit"` or `"too many tokens"` [9] |
| OpenAI | `"context exceeded"` (HTTP 400) [8] |
| Qwen | `"context window exceeded"` [9] |

**Mitigation Strategy:**

```python
# Instead of hardcoding one string:
_CONTEXT_ERROR_PATTERNS = [
    "context window limit",
    "context exceeded",
    "context length exceeded",
    "too many tokens",
    "maximum context length",
    "context window exceeded",
]

def _is_context_window_error(message: str | None) -> bool:
    if not message:
        return False
    return any(pattern in message.lower() for pattern in _CONTEXT_ERROR_PATTERNS)
```

**Action:** Check your Bifrost logs at `http://localhost:8080` for the exact `error` or `error_type` field when overflow happens.[10][6]

***

### 4. **"Hook execution model" — What's the mitigation?**

**The Issue:** Hooks run **in parallel** and are **non-blocking** by default:[11][1]

| Characteristic | Risk |
|---------------|------|
| Multiple hooks fire simultaneously for same event | State file writes may race |
| Hooks don't block Claude Code execution | If hook fails, Claude continues silently |
| Async hooks (`async: true`) run in background | No guarantee of completion order |

**Your plan assumes synchronous state sharing** — this is a design flaw.

**Mitigation Strategies:**

#### Option A: Use a queue-based decoupling pattern

```python
# Instead of direct file writes:
import queue
import threading

_STATE_QUEUE = queue.Queue()

def _write_context_overflow_packet(packet: dict) -> Path:
    # Queue the write, don't do it directly
    _STATE_QUEUE.put(("overflow_packet", packet, time.time()))
    # Return immediately with a temp file path
    return Path(f"/tmp/overflow_packet_{time.time()}.json")
```

#### Option B: Use atomic file operations with locks

```python
from filelock import FileLock

LOCK_FILE = Path("/tmp/context_window_lock")

def _write_context_overflow_packet(packet: dict) -> Path:
    output = Path("/tmp/overflow_packet.json")
    with FileLock(str(LOCK_FILE)):
        with open(output, "w") as f:
            json.dump(packet, f)
    return output
```

#### Option C: Use Claude Code's built-in state mechanism

```python
# Instead of custom JSON files:
# Use hook-specific output or session state
print(json.dumps({
    "hookSpecificOutput": {
        "contextWindowOverflowPacket": packet
    }
}))
```

**Reference:** [Run hooks in the background](https://code.claude.com/docs/en/hooks#run-hooks-in-the-background)[1]

***

## Updated Assessment

| Issue | Severity | Fix Complexity | Recommended? |
|-------|----------|----------------|--------------|
| Path inconsistency | 🟡 Low | Trivial | ✅ Fix with `pathlib` |
| Python vs Node.js | 🟡 Low | Medium | ✅ Use Python (you have it) |
| SessionStart change | 🔴 Critical | Medium | ✅ **Must update Task 4** |
| Error signature | 🟠 Medium | Low | ✅ Use pattern matching |
| Hook execution model | 🟠 Medium | Medium | ✅ Add file locking or queue |

***

## Will This Work?

**With the above fixes:** ✅ **Yes, this will work.**

The architecture is sound:
- ai-api layer detects overflow → writes packet ✅
- hook layer injects bounded resume ✅
- PreCompact guard fails open ✅
- SessionStart prefers compact packet ✅

**Without fixes:** ❌ **No, it will fail** on SessionStart behavior and potential state racing.

***

Does this clarify the issues? I recommend updating Task 4 for the SessionStart change and adding pattern matching for error signatures before implementing.

## Human

Strategies for managing state across agentic session restarts

## Assistant

Based on the official documentation and your architecture, here are the **strategies for managing state across agentic session restarts** in Claude Code with Bifrost:

***

## State Management Strategies for Agentic Session Restarts

### Core Distinction: Conversation State vs. Filesystem State

| State Type | How It Persists | How to Restore |
|------------|----------------|----------------|
| **Conversation history** | Auto-saved to `~/.claude/projects/<cwd>/ *.jsonl` [1][2] | Use `resume=session_id` or `continue_conversation=True` [1] |
| **Filesystem changes** | **NOT** persisted by sessions | Use file checkpointing or Git snapshots [1] |
| **Agent decisions/metadata** | Not persisted automatically | Write to custom JSON state files [3] |

***

## Strategy 1: SDK-Level Session Continuity (Automatic)

Use this for **multi-turn conversations within the same process**:

### Python: `ClaudeSDKClient`

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async with ClaudeSDKClient(options=options) as client:
    # First query: client captures session_id internally
    await client.query("Analyze the auth module")
    
    # Second query: automatically continues same session
    await client.query("Now refactor it to use JWT")
```

No session ID tracking needed — the client holds state.[1]

### TypeScript: `continue: true`

```typescript
// First query: creates new session
for await (const message of query({
  prompt: "Analyze auth module",
  options: { continue: false }
})) { /* ... */ }

// Second query: resumes most recent session
for await (const message of query({
  prompt: "Refactor to JWT",
  options: { continue: true }
})) { /* ... */ }
```



***

## Strategy 2: Resume by Session ID (Explicit)

Use this when you need to **resume a specific past session** (not the most recent) or **recover from limits**:

### Capture the Session ID

```python
async for message in query(
    prompt="Analyze the code",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Glob"])
):
    if isinstance(message, ResultMessage):
        session_id = message.session_id  # Save this
        print(f"Session ID: {session_id}")
```

### Resume Later

```python
async for message in query(
    prompt="Implement the refactoring you suggested",
    options=ClaudeAgentOptions(
        resume=session_id,  # Explicitly resume
        allowed_tools=["Read", "Edit", "Write"]
    )
):
    if isinstance(message, ResultMessage) and message.subtype == "success":
        print(message.result)
```



**Common failure mode:** If `resume` returns a fresh session instead of expected history:
- Check `cwd` matches exactly (sessions stored under `~/.claude/projects/<cwd-hash>/`)
- Session file must exist on current machine[1]

***

## Strategy 3: Fork for Alternative Paths

Use this when you want to **explore alternatives without losing the original**:

```python
# Fork from session_id into new session
forked_id = None
async for message in query(
    prompt="Instead of JWT, implement OAuth2",
    options=ClaudeAgentOptions(
        resume=session_id,
        fork_session=True  # Creates branch
    )
):
    if isinstance(message, ResultMessage):
        forked_id = message.session_id  # Fork's ID, distinct from original

# Original session untouched; resume it to continue JWT path
async for message in query(
    prompt="Continue with JWT approach",
    options=ClaudeAgentOptions(resume=session_id)
):
    print(message.result)
```

Now you have **two independent sessions**.[1]

**Important:** Forking branches conversation history, **not** filesystem. File edits by forked agents are real and visible to all sessions.[1]

***

## Strategy 4: Compact Continuation Packets (Your Plan)

This is the **custom orchestration layer** for handling context overflow:

### Packet Structure

```json
{
  "model": "M3",
  "route": "auto",
  "domain": "architecture",
  "task": "Implement compact resume logic",
  "prompt_digest": "sha256:abc123...",
  "timestamp": 1717777777.0,
  "resume_hint": "Resume from checkpoint with current task only.",
  "goal": "Prevent context-window halts",
  "current_task": "Implement compact resume logic",
  "active_files": ["bf_agent.py", "SessionStart.py"]
}
```

### Flow

1. **ai-api layer**: Detect overflow → write compact packet → retry once
2. **hook layer**: Read packet → inject bounded resume (≤1200 chars)
3. **SessionStart**: Prefer compact packet over full transcript

This treats overflow as a **retryable orchestration event**, not a task failure [query].

***

## Strategy 5: Hook-Based State Persistence

Use hooks to **save/restore state at lifecycle boundaries**:

### `Stop` Hook: Save Session State Before Exit

```python
async def save_state_on_stop(input_data, tool_use_id, context):
    """Save session state when agent stops."""
    session_state = {
        "session_id": input_data["session_id"],
        "current_task": get_current_task(),
        "active_files": get_active_files(),
        "decisions": get_recent_decisions(),
        "timestamp": time.time()
    }
    
    # Write to persistent location
    state_file = Path.home() / ".claude" / "state" / f"{input_data['session_id']}.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w") as f:
        json.dump(session_state, f)
    
    return {"hookSpecificOutput": {"hookEventName": "Stop"}}
```

Register in options:

```python
options = ClaudeAgentOptions(
    hooks={
        "Stop": [HookMatcher(hooks=[save_state_on_stop])]
    }
)
```



### `SessionStart` Hook: Load State on Resume

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Resume from checkpoint. Current task: X. Active files: [a.py, b.py]."
  }
}
```

**Note:** As of Claude Code 2.1.0+, `SessionStart` hooks inject context silently via `additionalContext`, not via visible messages.[4][5]

***

## Strategy 6: External Storage for Cross-Host Resume

Use this when resuming **across machines or in serverless/ephemeral environments**:

### Option A: Mirror Transcripts to Shared Storage

```python
from claude_agent_sdk import SessionStore

# Configure SessionStore adapter to sync to S3/GCS
options = ClaudeAgentOptions(
    session_store=SessionStore(adapter="s3", bucket="my-session-transcripts")
)
```



### Option B: Manual Session File Transfer

```bash
# On source machine
cp ~/.claude/projects/-Users-me-proj/*.jsonl /shared/storage/

# On target machine (same cwd path)
cp /shared/storage/*.jsonl ~/.claude/projects/-Users-me-proj/
claude --resume <session_id>
```

**Requirements:**
- `cwd` must match exactly
- Session file must exist on target machine[1]

***

## Strategy 7: Application-Level Checkpointing

For **long-running agentic workflows**, maintain a separate state layer:

### State Machine Pattern

```python
class AgentWorkflow:
    def __init__(self, workflow_id):
        self.workflow_id = workflow_id
        self.state_file = Path(f"/tmp/workflow_{workflow_id}.json")
    
    def checkpoint(self, phase: str, result: dict):
        """Save progress after each significant phase."""
        state = {
            "workflow_id": self.workflow_id,
            "current_phase": phase,
            "result": result,
            "timestamp": time.time(),
            "session_id": self.current_session_id
        }
        
        with open(self.state_file, "w") as f:
            json.dump(state, f)
    
    def restore(self) -> dict:
        """Reconstruct required context from checkpoint."""
        with open(self.state_file) as f:
            return json.load(f)
```

This retains **only crucial data** (not entire context) in SQLite/Redis.[3]

***

## Strategy 8: Durable Execution Frameworks

For **production-grade reliability** across restarts/failures:

| Framework | Strength | Best For |
|-----------|----------|----------|
| **Temporal.io** | Full durable execution, variables persist across resumes | Complex workflows, enterprise |
| **LangGraph** | Integrated persistence, state machine pattern | Multi-agent orchestration [3] |
| **Inngest/Trigger.dev** | No infra management, checkpointing automatic | Simpler workflows [3] |
| **Cloudflare Workflows** | No infra management, serverless | Edge deployments [3] |

***

## Strategy Comparison Matrix

| Strategy | Persistence | Cross-Host | Complexity | Best For |
|----------|-------------|------------|------------|----------|
| SDK Client (auto) | Process + disk | No | Low | Multi-turn in same process |
| Resume by ID | Disk | No (unless mirrored) | Low | Specific session recovery |
| Fork | Disk | No | Low | Alternative exploration |
| Compact packet | Custom JSON | Yes | Medium | Context overflow recovery |
| Hook-based | Custom files | Yes | Medium | Lifecycle-bound state |
| External storage | Cloud storage | Yes | High | Cross-host/serverless |
| Checkpointing | Custom DB/files | Yes | Medium | Long-running workflows |
| Durable execution | Framework DB | Yes | High | Production reliability |

***

## Critical Assumptions & Edge Cases

| Assumption | Risk | Mitigation |
|------------|------|------------|
| Session files exist on disk | Disk failure = lost history | Mirror to cloud storage |
| `cwd` matches on resume | Resume fails silently | Log cwd hash on startup |
| Hooks execute synchronously | Race conditions in state writes | Use file locks or queue |
| Compact packet ≤ context limit | Still overflows if packet too large | Enforce hard cap (e.g., 1200 chars) |
| Timestamp-based expiry works | Clock skew across hosts | Use monotonic clock or TTL |

***

## Recommended Approach for Your Use Case

Based on your architecture (Claude Code + Bifrost + agentic workers):

### Layer 1: SDK-Level Continuity (Default)
Use `ClaudeSDKClient` for automatic session management within processes.[1]

### Layer 2: Compact Packet Overflow Recovery (Your Plan)
Implement the context overflow guard as designed, with:
- Pattern-matching error detection (not hardcoded string)
- File locking for state writes
- TTL-based packet expiry

### Layer 3: Hook-Based Checkpointing
Add `Stop` hook to save workflow state + `SessionStart` hook to load it.[6][7]

### Layer 4: Optional Durable Execution
If you need production reliability across failures, consider LangGraph for state machine patterns.[3]

***

Which aspect would you like to dive deeper into? The overflow recovery implementation, hook-based checkpointing, or cross-host resume strategies?
