# Context Window Resilience Implementation Plan

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


def test_stale_context_window_packet_expires(tmp_path):
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
- The failure becomes a checkpoint, not a session-ending halt.
