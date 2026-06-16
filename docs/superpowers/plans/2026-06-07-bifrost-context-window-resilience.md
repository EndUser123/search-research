# Bifrost Context Window Resilience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent `ai-api` and Bifrost-backed model calls from halting on context-window overflow by estimating prompt size before dispatch, compacting oversized prompts, classifying provider overflow errors, and retrying once with bounded resume context.

**Architecture:** This is the companion to `docs/superpowers/plans/2026-06-07-snapshot-v3-router-resilience.md`. Snapshot V3 handles Claude Code conversation compaction and resume. This plan handles requests we control in `cc-skills-ai-api` and Bifrost diagnostics; it does not rewrite Claude Code's internal `/compact` summarizer or mutate raw Claude Code requests inside the Bifrost daemon.

**Tech Stack:** Python 3.14, pytest, `requests`, `pathlib`, Bifrost HTTP at `localhost:8080`, `cc-skills-ai-api`, PowerShell provider config scripts.

---

## Research Notes

- Claude Code's own error docs say `Prompt is too long` means the conversation plus attachments exceeds the model context window, and recommends `/compact`, `/context`, trimming memory files, and reducing loaded MCP tools.
- Claude Code's docs also say `/compact` can fail with `Conversation too long` when there is not enough free context to hold the summary.
- Bifrost supports routing rules, fallback chains, and capacity-aware routing, but prompt pruning must happen before we send the request payload.
- Token counting should happen before dispatch. OpenAI's token-counting cookbook notes that token estimation tells us whether text is too long for a model before sending it.

Reference URLs:

- `https://code.claude.com/docs/en/errors`
- `https://docs.getbifrost.ai/providers/provider-routing`
- `https://docs.getbifrost.ai/providers/routing-rules`
- `https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb`

## Scope

In scope:

- `ai-api` direct calls.
- `ai-api` Bifrost HTTP calls.
- `run_simple`, `run_compare`, `run_review`, `run_code`, `run_domain_benchmark`, and benchmark suite calls that route through `bf_agent.bifrost_call`.
- Bifrost status/diagnostic scripts under `P:/.claude/provider-configs`.

Out of scope:

- Changing Claude Code's internal `/compact` summarizer.
- Modifying the Bifrost daemon binary.
- Inserting a new reverse proxy in front of Bifrost.
- Replaying full Claude Code transcripts into model prompts.

## File Structure Target

- Create `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/context_window_guard.py`
  - Owns context-window error classification, prompt size estimates, prompt budget decisions, compact retry prompt construction, and continuation packet writing.

- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/transport.py`
  - Applies preflight compaction before direct and Bifrost HTTP calls.
  - Classifies overflow failures and retries once with compact prompt.

- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/bf_agent.py`
  - Keeps higher-level flows from re-growing prompts after the transport layer compacts them.
  - Adds bounded history compaction for `run_code_agent`.

- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_bf_agent.py`
  - Adds integration coverage through public `bf_agent` entrypoints.

- Create `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_context_window_guard.py`
  - Unit tests for classifier, budget estimate, compaction, and packet writing.

- Modify `P:/.claude/provider-configs/scripts/bifrost_validate.py`
  - Adds an optional oversized prompt probe that verifies Bifrost surfaces context errors in a classified way.

- Modify `P:/.claude/provider-configs/cc-bifrost.ps1`
  - Adds a `--context` or status subsection that reports recent context-window errors from Bifrost logs.

- Modify `P:/.claude/provider-configs/bifrost_configured_providers.md`
  - Documents that Bifrost handles provider routing/fallback, while `ai-api` owns prompt-budget preflight.

---

### Task 1: Add Context Window Guard Unit Module

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/context_window_guard.py`
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_context_window_guard.py`

- [ ] **Step 1: Write failing unit tests**

Create `tests/test_context_window_guard.py`:

```python
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "ai-api"))

import context_window_guard as guard


def test_classifies_known_context_window_errors() -> None:
    samples = [
        "API Error: The model has reached its context window limit.",
        "Prompt is too long",
        "prompt is too long: 201543 tokens > 200000 maximum",
        "context_length_exceeded",
        "maximum context length is 4097 tokens",
        "request exceeds context window",
    ]
    for sample in samples:
        assert guard.is_context_window_error(sample), sample


def test_does_not_classify_quota_or_stream_timeout_as_context_window() -> None:
    samples = [
        "usage limit exceeded, 5-hour usage limit reached",
        "wsarecv: A connection attempt failed",
        "rate_limit_error",
        "Bifrost daemon is unreachable",
    ]
    for sample in samples:
        assert not guard.is_context_window_error(sample), sample


def test_estimate_tokens_uses_conservative_ratio() -> None:
    assert guard.estimate_tokens("a" * 4000) == 1000
    assert guard.estimate_tokens("abc") == 1


def test_prompt_exceeds_budget_accounts_for_output_tokens() -> None:
    decision = guard.assess_prompt_budget(
        prompt="a" * 40_000,
        system="",
        model="test-model",
        max_tokens=4_000,
        context_limit=10_000,
    )
    assert decision.should_compact is True
    assert decision.estimated_input_tokens == 10_000
    assert decision.available_input_tokens < decision.estimated_input_tokens


def test_compact_prompt_preserves_goal_and_tail() -> None:
    prompt = "GOAL: fix context errors\n" + ("middle\n" * 5000) + "TAIL: final instruction"
    compacted = guard.build_compact_retry_prompt(
        prompt=prompt,
        system=None,
        model="M3",
        budget_tokens=800,
        reason="preflight",
    )
    assert "GOAL: fix context errors" in compacted
    assert "TAIL: final instruction" in compacted
    assert guard.estimate_tokens(compacted) <= 800


def test_write_continuation_packet_is_atomic_and_bounded(tmp_path: Path) -> None:
    packet_path = guard.write_continuation_packet(
        artifact_root=tmp_path,
        model="M3",
        route="bifrost",
        reason="context_window_limit",
        original_prompt="large prompt",
        compact_prompt="compact prompt",
    )
    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["model"] == "M3"
    assert payload["route"] == "bifrost"
    assert payload["reason"] == "context_window_limit"
    assert payload["original_prompt_sha256"]
    assert payload["compact_prompt"]
    assert time.time() - payload["created_at_epoch"] < 10
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_context_window_guard.py -q -p no:cacheprovider
```

Expected: FAIL with `ModuleNotFoundError: No module named 'context_window_guard'`.

- [ ] **Step 3: Implement `context_window_guard.py`**

Create `skills/ai-api/context_window_guard.py`:

```python
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONTEXT_LIMIT = int(os.getenv("BF_CONTEXT_WINDOW_LIMIT", "180000"))
DEFAULT_SAFETY_MARGIN = int(os.getenv("BF_CONTEXT_SAFETY_MARGIN_TOKENS", "12000"))
MIN_RETRY_BUDGET = int(os.getenv("BF_CONTEXT_MIN_RETRY_BUDGET_TOKENS", "6000"))

_CONTEXT_ERROR_PATTERNS = (
    re.compile(r"context window limit", re.I),
    re.compile(r"prompt is too long", re.I),
    re.compile(r"context[_ -]?length[_ -]?exceeded", re.I),
    re.compile(r"maximum context length", re.I),
    re.compile(r"exceeds context window", re.I),
    re.compile(r"too many input tokens", re.I),
)


@dataclass(frozen=True)
class PromptBudgetDecision:
    estimated_input_tokens: int
    context_limit: int
    max_output_tokens: int
    safety_margin_tokens: int
    available_input_tokens: int
    should_compact: bool
    reason: str


def is_context_window_error(message: str | None) -> bool:
    if not message:
        return False
    text = str(message)
    return any(pattern.search(text) for pattern in _CONTEXT_ERROR_PATTERNS)


def estimate_tokens(text: str | None) -> int:
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def assess_prompt_budget(
    *,
    prompt: str,
    system: str | None,
    model: str,
    max_tokens: int | None,
    context_limit: int | None = None,
    safety_margin_tokens: int | None = None,
) -> PromptBudgetDecision:
    del model
    resolved_context = context_limit or DEFAULT_CONTEXT_LIMIT
    resolved_output = int(max_tokens or 0)
    margin = safety_margin_tokens if safety_margin_tokens is not None else DEFAULT_SAFETY_MARGIN
    estimated_input = estimate_tokens(prompt) + estimate_tokens(system)
    available_input = max(0, resolved_context - resolved_output - margin)
    should_compact = estimated_input > available_input
    return PromptBudgetDecision(
        estimated_input_tokens=estimated_input,
        context_limit=resolved_context,
        max_output_tokens=resolved_output,
        safety_margin_tokens=margin,
        available_input_tokens=available_input,
        should_compact=should_compact,
        reason="input_exceeds_budget" if should_compact else "within_budget",
    )


def _take_head_tail(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = max_chars // 2
    tail = max_chars - head
    return text[:head].rstrip() + "\n\n[...context compacted...]\n\n" + text[-tail:].lstrip()


def build_compact_retry_prompt(
    *,
    prompt: str,
    system: str | None,
    model: str,
    budget_tokens: int,
    reason: str,
) -> str:
    del system
    budget_tokens = max(MIN_RETRY_BUDGET, int(budget_tokens))
    max_chars = max(4000, budget_tokens * 4)
    body = _take_head_tail(prompt, max_chars=max_chars)
    compact = (
        "<context-window-retry>\n"
        f"model: {model}\n"
        f"reason: {reason}\n"
        "instruction: Continue the user's task from the bounded context below. "
        "Do not ask for the full transcript unless required.\n"
        "</context-window-retry>\n\n"
        f"{body}"
    )
    while estimate_tokens(compact) > budget_tokens and len(body) > 1000:
        body = _take_head_tail(body, max_chars=max(1000, len(body) // 2))
        compact = (
            "<context-window-retry>\n"
            f"model: {model}\n"
            f"reason: {reason}\n"
            "instruction: Continue the user's task from the bounded context below.\n"
            "</context-window-retry>\n\n"
            f"{body}"
        )
    return compact


def write_continuation_packet(
    *,
    artifact_root: Path,
    model: str,
    route: str,
    reason: str,
    original_prompt: str,
    compact_prompt: str,
) -> Path:
    root = artifact_root / "context-window"
    root.mkdir(parents=True, exist_ok=True)
    packet = {
        "schema_version": 1,
        "id": str(uuid.uuid4()),
        "created_at_epoch": time.time(),
        "model": model,
        "route": route,
        "reason": reason,
        "original_prompt_sha256": hashlib.sha256(original_prompt.encode("utf-8", errors="replace")).hexdigest(),
        "original_estimated_tokens": estimate_tokens(original_prompt),
        "compact_estimated_tokens": estimate_tokens(compact_prompt),
        "compact_prompt": compact_prompt[:24000],
    }
    target = root / "latest.json"
    temp = root / f".{packet['id']}.tmp"
    temp.write_text(json.dumps(packet, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    temp.replace(target)
    return target
```

- [ ] **Step 4: Run unit tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_context_window_guard.py -q -p no:cacheprovider
python -m py_compile P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\context_window_guard.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\cc-skills-ai-api add skills\ai-api\context_window_guard.py tests\test_context_window_guard.py
git -C P:\packages\.claude-marketplace\plugins\cc-skills-ai-api commit -m "feat: add context window guard"
```

### Task 2: Add Transport Preflight And One Retry

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/transport.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_bf_agent.py`

- [ ] **Step 1: Add failing transport tests**

Append to `tests/test_bf_agent.py`:

```python
def test_bifrost_call_compacts_oversized_prompt_before_http(monkeypatch):
    import bf_agent

    captured = {}

    monkeypatch.setattr(bf_agent, "BIFROST_VK", "test-key")
    monkeypatch.setattr(bf_agent, "_require_bifrost_credentials", lambda: None)
    monkeypatch.setattr(bf_agent, "_ensure_bifrost_health", lambda: None)
    monkeypatch.setattr(bf_agent, "_resolve_model_to_provider", lambda model: None)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"content": [{"type": "text", "text": "ok"}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["payload"] = json
        return FakeResponse()

    monkeypatch.setattr(bf_agent.requests, "post", fake_post)
    monkeypatch.setenv("BF_CONTEXT_WINDOW_LIMIT", "2000")
    monkeypatch.setenv("BF_CONTEXT_SAFETY_MARGIN_TOKENS", "200")

    result = bf_agent.bifrost_call(
        "M3",
        "GOAL: keep this\n" + ("x" * 12000) + "\nTAIL: keep this",
        correlation_id="ctx-test",
        route="bifrost",
        max_tokens=1000,
    )

    sent_prompt = captured["payload"]["messages"][0]["content"]
    assert result["ok"] is True
    assert "<context-window-retry>" in sent_prompt
    assert "GOAL: keep this" in sent_prompt
    assert "TAIL: keep this" in sent_prompt
    assert len(sent_prompt) < 12000


def test_bifrost_call_retries_once_after_context_window_http_error(monkeypatch):
    import bf_agent
    import requests

    calls = []
    monkeypatch.setattr(bf_agent, "BIFROST_VK", "test-key")
    monkeypatch.setattr(bf_agent, "_require_bifrost_credentials", lambda: None)
    monkeypatch.setattr(bf_agent, "_ensure_bifrost_health", lambda: None)
    monkeypatch.setattr(bf_agent, "_resolve_model_to_provider", lambda model: None)

    class ErrorResponse:
        text = '{"error":{"message":"The model has reached its context window limit."}}'
        status_code = 400

        def raise_for_status(self):
            raise requests.HTTPError("400 Client Error", response=self)

    class OkResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"content": [{"type": "text", "text": "recovered"}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(json["messages"][0]["content"])
        if len(calls) == 1:
            return ErrorResponse()
        return OkResponse()

    monkeypatch.setattr(bf_agent.requests, "post", fake_post)

    result = bf_agent.bifrost_call(
        "M3",
        "large prompt " * 1000,
        correlation_id="ctx-retry",
        route="bifrost",
        max_tokens=1000,
    )

    assert result["ok"] is True
    assert result["text"] == "recovered"
    assert len(calls) == 2
    assert "<context-window-retry>" in calls[1]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -k "context_window or oversized_prompt" -q -p no:cacheprovider
```

Expected: FAIL because `transport.bifrost_call` does not compact preflight and does not retry context-window HTTP errors.

- [ ] **Step 3: Modify `transport.py` imports**

Add near other imports:

```python
from context_window_guard import (
    DEFAULT_CONTEXT_LIMIT,
    assess_prompt_budget,
    build_compact_retry_prompt,
    is_context_window_error,
    write_continuation_packet,
)
```

- [ ] **Step 4: Add helper functions in `transport.py`**

Add below `BIFROST_VK`:

```python
def _context_limit_for_model(model: str) -> int:
    del model
    return int(os.getenv("BF_CONTEXT_WINDOW_LIMIT", str(DEFAULT_CONTEXT_LIMIT)))


def _prepare_prompt_for_context(
    *,
    model: str,
    prompt: str,
    system: str | None,
    max_tokens: int | None,
    route: str,
    reason: str = "preflight",
) -> tuple[str, bool]:
    decision = assess_prompt_budget(
        prompt=prompt,
        system=system,
        model=model,
        max_tokens=max_tokens,
        context_limit=_context_limit_for_model(model),
    )
    if not decision.should_compact:
        return prompt, False
    budget = max(6000, decision.available_input_tokens)
    compact_prompt = build_compact_retry_prompt(
        prompt=prompt,
        system=system,
        model=model,
        budget_tokens=budget,
        reason=reason,
    )
    try:
        write_continuation_packet(
            artifact_root=BF_ARTIFACT_ROOT,
            model=model,
            route=route,
            reason=reason,
            original_prompt=prompt,
            compact_prompt=compact_prompt,
        )
    except Exception as exc:
        logging.getLogger(__name__).warning("Failed to write context continuation packet: %s", exc)
    return compact_prompt, True
```

- [ ] **Step 5: Apply preflight before direct calls**

In `bifrost_call`, before `_direct_call(...)`, insert:

```python
prepared_prompt, compacted = _prepare_prompt_for_context(
    model=model,
    prompt=prompt,
    system=system,
    max_tokens=max_tokens,
    route=route,
)
if compacted:
    log_event(
        "context_window_preflight_compacted",
        correlation_id=correlation_id,
        compare_id=compare_id,
        model=model,
        provider=provider,
        status="compacted",
    )
else:
    prepared_prompt = prompt
```

Pass `prepared_prompt` to `_direct_call` instead of `prompt`.

- [ ] **Step 6: Apply preflight before Bifrost HTTP payload**

Before `messages = [{"role": "user", "content": prompt}]`, insert:

```python
prepared_prompt, compacted = _prepare_prompt_for_context(
    model=model,
    prompt=prompt,
    system=system,
    max_tokens=max_tokens,
    route=route,
)
if compacted:
    log_event(
        "context_window_preflight_compacted",
        correlation_id=correlation_id,
        compare_id=compare_id,
        model=model,
        provider="bifrost",
        status="compacted",
    )
messages = [{"role": "user", "content": prepared_prompt}]
```

- [ ] **Step 7: Add retry inside Bifrost HTTP error handler**

In the `except requests.HTTPError as exc:` block, before returning the error result, add:

```python
        if is_context_window_error(error_msg) and "_context_retry" not in locals():
            _context_retry = True
            retry_prompt, _ = _prepare_prompt_for_context(
                model=model,
                prompt=prompt,
                system=system,
                max_tokens=max_tokens,
                route=route,
                reason="context_window_error",
            )
            retry_payload = dict(payload)
            retry_payload["messages"] = [{"role": "user", "content": retry_prompt}]
            try:
                retry_response = requests.post(url, headers=headers, json=retry_payload, timeout=120)
                retry_response.raise_for_status()
                retry_data = retry_response.json()
                retry_content = retry_data.get("content", [])
                retry_text = "\n".join(
                    item.get("text", "")
                    for item in retry_content
                    if isinstance(item, dict) and item.get("type") == "text"
                ).strip()
                return {
                    "model": model,
                    "text": retry_text,
                    "ok": True,
                    "error": None,
                    "ttfb_ms": 0,
                    "total_ms": int((time.perf_counter() - t_scheduled) * 1000),
                    "queue_delay_ms": 0,
                    "status": "ok_context_retry",
                    "error_type": "",
                }
            except Exception as retry_exc:
                error_msg = f"{error_msg} | context retry failed: {retry_exc}"
```

If the local function structure makes `locals()` awkward, use a small `for attempt in range(2)` loop instead. Keep retry count exactly one.

- [ ] **Step 8: Run focused tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_context_window_guard.py P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -k "context_window or oversized_prompt or bifrost_call_direct_route" -q -p no:cacheprovider
python -m py_compile P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\transport.py
```

Expected: PASS.

- [ ] **Step 9: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\cc-skills-ai-api add skills\ai-api\transport.py tests\test_bf_agent.py
git -C P:\packages\.claude-marketplace\plugins\cc-skills-ai-api commit -m "feat: compact oversized bifrost prompts"
```

### Task 3: Bound `run_code_agent` Turn History

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/bf_agent.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_bf_agent.py`

- [ ] **Step 1: Add failing code-agent history test**

Append to `tests/test_bf_agent.py`:

```python
def test_run_code_agent_compacts_history_between_turns(monkeypatch):
    import bf_agent

    prompts = []

    def fake_bifrost_call(model, prompt, *args, **kwargs):
        prompts.append(prompt)
        if len(prompts) == 1:
            return {
                "ok": True,
                "text": '{"action":"read_file","path":"P:/tmp/example.py"}',
                "error": None,
                "status": "ok",
            }
        return {
            "ok": True,
            "text": '{"action":"final","answer":"done"}',
            "error": None,
            "status": "ok",
        }

    monkeypatch.setattr(bf_agent, "bifrost_call", fake_bifrost_call)
    monkeypatch.setattr(
        bf_agent,
        "tool_read_file_range",
        lambda path, offset=0, limit=12000: {"ok": True, "content": "x" * 200000, "path": path},
    )
    monkeypatch.setenv("BF_CODE_TURN_CONTEXT_LIMIT_CHARS", "12000")

    result = bf_agent.run_code_agent(
        "inspect the file",
        model="M3",
        correlation_id="code-context-test",
        max_turns=2,
        route="direct",
    )

    assert result["ok"] is True
    assert len(prompts) == 2
    assert len(prompts[1]) < 30000
    assert "[tool output compacted]" in prompts[1]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py::test_run_code_agent_compacts_history_between_turns -q -p no:cacheprovider
```

Expected: FAIL because code-agent history can grow from large tool outputs without a turn-context cap.

- [ ] **Step 3: Add history compaction helper in `bf_agent.py`**

Add near code-agent helpers:

```python
def _compact_code_turn_history(history: list[dict], limit_chars: int | None = None) -> list[dict]:
    limit = limit_chars or int(os.getenv("BF_CODE_TURN_CONTEXT_LIMIT_CHARS", "60000"))
    compacted: list[dict] = []
    total = 0
    for item in reversed(history):
        clone = dict(item)
        text = str(clone.get("content", ""))
        if len(text) > 8000:
            text = text[:4000] + "\n[tool output compacted]\n" + text[-2000:]
            clone["content"] = text
        item_len = len(str(clone))
        if total + item_len > limit and compacted:
            compacted.append({"role": "system", "content": "[older code-agent history compacted]"})
            break
        compacted.append(clone)
        total += item_len
    return list(reversed(compacted))
```

- [ ] **Step 4: Use compacted history when building the next turn prompt**

In `run_code_agent`, find the block that builds the next turn's prompt from accumulated context. Before rendering the next prompt, call:

```python
history = _compact_code_turn_history(history)
```

If the variable is named differently, use the actual accumulated turn list and keep the helper signature unchanged.

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py::test_run_code_agent_compacts_history_between_turns -q -p no:cacheprovider
python -m py_compile P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\cc-skills-ai-api add skills\ai-api\bf_agent.py tests\test_bf_agent.py
git -C P:\packages\.claude-marketplace\plugins\cc-skills-ai-api commit -m "fix: bound code agent turn history"
```

### Task 4: Add Bifrost Context Diagnostics

**Files:**
- Modify: `P:/.claude/provider-configs/scripts/bifrost_validate.py`
- Modify: `P:/.claude/provider-configs/cc-bifrost.ps1`

- [ ] **Step 1: Add validation script classifier tests manually in-script**

`P:/.claude/provider-configs/scripts` does not currently have a pytest suite. Add these pure functions to `bifrost_validate.py` above `main()`:

```python
def is_context_window_error_text(text: str) -> bool:
    lowered = text.lower()
    return any(
        token in lowered
        for token in (
            "context window limit",
            "prompt is too long",
            "context_length_exceeded",
            "maximum context length",
            "too many input tokens",
        )
    )


def classify_probe_error(text: str) -> str:
    if is_context_window_error_text(text):
        return "CONTEXT"
    if "rate" in text.lower() and "limit" in text.lower():
        return "RATE"
    if "usage limit" in text.lower() or "quota" in text.lower():
        return "QUOTA"
    return "ERROR"
```

- [ ] **Step 2: Add `--self-test` mode**

At the start of `main()`, before reading stdin, add:

```python
    if "--self-test" in sys.argv:
        assert classify_probe_error("The model has reached its context window limit.") == "CONTEXT"
        assert classify_probe_error("Prompt is too long") == "CONTEXT"
        assert classify_probe_error("usage limit exceeded") == "QUOTA"
        print("SELFTEST: OK")
        return 0
```

- [ ] **Step 3: Run self-test**

Run:

```powershell
python P:\.claude\provider-configs\scripts\bifrost_validate.py --self-test
```

Expected:

```text
SELFTEST: OK
```

- [ ] **Step 4: Add optional oversized probe mode**

In `bifrost_validate.py`, add `--context-probe` support that sends a deliberately large prompt only when explicitly requested:

```python
def run_context_probe(model: str) -> int:
    prompt = "context probe\n" + ("x" * 240000)
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1,
    }).encode()
    req = urllib.request.Request(
        GATEWAY_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT_SECONDS) as resp:
            print(f"CONTEXT-PROBE ({model}): UNEXPECTED_OK HTTP {resp.status}")
            return 1
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        classification = classify_probe_error(body)
        print(f"CONTEXT-PROBE ({model}): {classification} HTTP {exc.code}")
        return 0 if classification == "CONTEXT" else 1
    except Exception as exc:
        print(f"CONTEXT-PROBE ({model}): ERROR - {exc}")
        return 1
```

Add before stdin parsing:

```python
    if "--context-probe" in sys.argv:
        idx = sys.argv.index("--context-probe")
        model = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "M3"
        return run_context_probe(model)
```

- [ ] **Step 5: Add PowerShell status hint**

In `cc-bifrost.ps1`, add a small status section near the existing validation/status output:

```powershell
function Show-BifrostContextErrors {
    $logDb = "$env:APPDATA\bifrost\logs.db"
    if (-not (Test-Path $logDb)) {
        Write-Host "   Context errors: logs.db not found" -ForegroundColor DarkGray
        return
    }
    $query = "select count(*) from logs where lower(error) like '%context window%' or lower(error) like '%prompt is too long%';"
    try {
        $count = & sqlite3 $logDb $query 2>$null
        if ($count -and [int]$count -gt 0) {
            Write-Host "   Context errors: $count recent/matched entries in Bifrost logs" -ForegroundColor Yellow
        } else {
            Write-Host "   Context errors: none matched" -ForegroundColor Green
        }
    } catch {
        Write-Host "   Context errors: unable to inspect logs.db" -ForegroundColor DarkGray
    }
}
```

Call `Show-BifrostContextErrors` from the `--status` path.

- [ ] **Step 6: Verify scripts compile and self-test**

Run:

```powershell
python -m py_compile P:\.claude\provider-configs\scripts\bifrost_validate.py
python P:\.claude\provider-configs\scripts\bifrost_validate.py --self-test
```

Expected: compile succeeds and self-test prints `SELFTEST: OK`.

- [ ] **Step 7: Commit provider config diagnostics if tracked**

Run:

```powershell
git -C P:\ add .claude\provider-configs\scripts\bifrost_validate.py .claude\provider-configs\cc-bifrost.ps1
git -C P:\ commit -m "chore: add bifrost context diagnostics"
```

If `.claude/provider-configs` is not tracked in the current repo, record the file changes in final notes instead of forcing a commit.

### Task 5: Document The Boundary

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/SKILL.md`
- Modify: `P:/.claude/provider-configs/bifrost_configured_providers.md`
- Create: `P:/docs/superpowers/specs/2026-06-07-bifrost-context-window-resilience.md`

- [ ] **Step 1: Add ai-api docs section**

In `SKILL.md`, add a section named `Context Window Resilience`:

```markdown
## Context Window Resilience

`ai-api` estimates prompt size before dispatch. If a prompt is too large for the configured context budget, it sends a bounded compact retry prompt instead of the full source packet. If a provider still returns a context-window error, the transport retries once with compact context and writes `.data/ai-api/context-window/latest.json`.

This protects `ai-api` direct and Bifrost-routed calls. It does not modify Claude Code's internal `/compact` summarizer; Claude Code session continuity is handled by the snapshot plugin.
```

- [ ] **Step 2: Add Bifrost provider docs note**

In `bifrost_configured_providers.md`, add:

```markdown
## Context Window Boundary

Bifrost owns provider routing, fallback chains, and key/provider selection. It does not prune oversized prompts for this workspace. Prompt-budget preflight lives in `cc-skills-ai-api` before requests are sent to `localhost:8080`.

Use `cc-bf --status` to inspect recent context-window failures and `python P:\.claude\provider-configs\scripts\bifrost_validate.py --context-probe M3` for an explicit oversized-request classification probe.
```

- [ ] **Step 3: Create short spec summary**

Create `docs/superpowers/specs/2026-06-07-bifrost-context-window-resilience.md`:

```markdown
# Bifrost Context Window Resilience

This design complements Snapshot V3. Snapshot V3 preserves Claude Code session continuity around compaction. This design prevents and recovers from context-window failures in `ai-api` direct and Bifrost-routed model calls.

The implementation estimates prompt size before dispatch, compacts oversized prompts, retries once on provider context-window errors, writes a continuation packet under `.data/ai-api/context-window/latest.json`, and adds Bifrost diagnostics so context failures are visible in status output.

It deliberately does not modify the Bifrost daemon binary or Claude Code's internal summarizer.
```

- [ ] **Step 4: Verify docs references**

Run:

```powershell
rg -n "Context Window Resilience|context-window/latest.json|Context Window Boundary|Snapshot V3" P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\SKILL.md P:\.claude\provider-configs\bifrost_configured_providers.md P:\docs\superpowers\specs\2026-06-07-bifrost-context-window-resilience.md
```

Expected: all three files contain the new context-window boundary text.

- [ ] **Step 5: Commit docs**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\cc-skills-ai-api add skills\ai-api\SKILL.md
git -C P:\packages\.claude-marketplace\plugins\cc-skills-ai-api commit -m "docs: explain ai-api context resilience"
git -C P:\ add .claude\provider-configs\bifrost_configured_providers.md docs\superpowers\specs\2026-06-07-bifrost-context-window-resilience.md
git -C P:\ commit -m "docs: document bifrost context boundary"
```

### Task 6: Final Verification

**Files:**
- Read: all modified files
- Read: git status

- [ ] **Step 1: Run focused ai-api tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_context_window_guard.py P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -k "context_window or oversized_prompt or run_code_agent_compacts_history or bifrost_call_direct_route or run_simple" -q -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 2: Compile changed Python files**

Run:

```powershell
python -m py_compile P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\context_window_guard.py P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\transport.py P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py P:\.claude\provider-configs\scripts\bifrost_validate.py
```

Expected: no output and exit code `0`.

- [ ] **Step 3: Run Bifrost validation self-test**

Run:

```powershell
python P:\.claude\provider-configs\scripts\bifrost_validate.py --self-test
```

Expected: `SELFTEST: OK`.

- [ ] **Step 4: Run optional live compact prompt smoke**

Run only if Bifrost is running and credentials are available:

```powershell
python P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\scripts\run_model_eval_suite.py --help
```

Expected: clean help output. This confirms imports still work after adding the guard.

- [ ] **Step 5: Check worktree**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\cc-skills-ai-api status --short
git -C P:\ status --short
```

Expected: only intended files changed. Do not revert unrelated dirty files.

## Rollback

- To disable preflight compaction without reverting code, set `BF_CONTEXT_WINDOW_LIMIT=100000000` and `BF_CONTEXT_SAFETY_MARGIN_TOKENS=0`.
- To disable retry behavior, add `BF_CONTEXT_RETRY_ENABLED=0` if the implementation adds this environment guard; otherwise revert the `transport.py` commit.
- To remove Bifrost diagnostics, revert the provider-config commit only.
- Do not delete `.data/ai-api/context-window/latest.json`; it may explain the last overflow failure.

## Completion Criteria

The implementation is complete when:

- Oversized `ai-api` prompts compact before direct or Bifrost dispatch.
- Provider context-window errors are classified separately from quota, rate limit, and stream timeout errors.
- A context-window provider error retries exactly once with compact context.
- `run_code_agent` cannot grow unbounded prompt history from large tool outputs.
- `cc-bf --status` or the validation script exposes context-window failures distinctly.
- Docs clearly state the boundary: snapshot handles Claude Code session compaction, `ai-api` handles request-budget preflight, and Bifrost handles routing/fallback.
