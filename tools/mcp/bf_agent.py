"""
bf_agent — pure Python library, no HTTP server.
Import this directly from skills that need Bifrost access.

Usage:
    from bf_agent import run_simple, run_compare, run_code
    result = run_simple("brainstorm", "what to build", model="DSv4-flash")
"""

from __future__ import annotations

import os
import time
import uuid
import json
import logging
import sys
from pathlib import Path
from typing import Annotated, TypedDict, List, Optional, Literal
from operator import add

import requests
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.types import Send

# --------------------------------------------------------------------
# Config
# --------------------------------------------------------------------

BIFROST_BASE_URL = os.getenv("BIFROST_BASE_URL", "http://localhost:8081")
BIFROST_VK = os.getenv("BIFROST_VK") or os.getenv("ANTHROPIC_API_KEY", "")
DEFAULT_MODELS = [
    m.strip()
    for m in os.getenv("BF_COMPARE_MODELS", "M27,GLM-5.1,DSv4-flash").split(",")
    if m.strip()
]
DEFAULT_MAX_TOKENS = int(os.getenv("BF_MAX_TOKENS", "2500"))
REQUEST_TIMEOUT_MS = int(os.getenv("BF_TIMEOUT_MS", "120000"))
SYNTHESIS_MODEL = os.getenv("BF_SYNTHESIS_MODEL", "M27")
BF_ALLOWED_ROOT = Path(os.getenv("BF_ALLOWED_ROOT", "P:/")).resolve()
BF_CODE_MAX_TURNS = int(os.getenv("BF_CODE_MAX_TURNS", "6"))
BF_FILE_CHAR_LIMIT = int(os.getenv("BF_FILE_CHAR_LIMIT", "12000"))
BF_DIR_ITEM_LIMIT = int(os.getenv("BF_DIR_ITEM_LIMIT", "200"))
BF_GLOB_LIMIT = int(os.getenv("BF_GLOB_LIMIT", "100"))

if not BIFROST_VK:
    raise RuntimeError("BIFROST_VK or ANTHROPIC_API_KEY is required")
if not BF_ALLOWED_ROOT.exists():
    raise RuntimeError(f"BF_ALLOWED_ROOT does not exist: {BF_ALLOWED_ROOT}")
if not BF_ALLOWED_ROOT.is_dir():
    raise RuntimeError(f"BF_ALLOWED_ROOT is not a directory: {BF_ALLOWED_ROOT}")
if REQUEST_TIMEOUT_MS <= 0:
    raise RuntimeError(f"REQUEST_TIMEOUT_MS must be positive, got: {REQUEST_TIMEOUT_MS}")
if BF_CODE_MAX_TURNS <= 0:
    raise RuntimeError(f"BF_CODE_MAX_TURNS must be positive, got: {BF_CODE_MAX_TURNS}")

VALID_MODELS = {"M27", "GLM-5.1", "DSv4-flash"}
VALID_RUN_MODES = {"brainstorm", "design", "plan", "review", "explore", "compare", "code"}

# --------------------------------------------------------------------
# Sanitization
# --------------------------------------------------------------------

import re as _re

_BEARER_RE = _re.compile(r"Bearer [\w\-]+")

def _sanitize_error(msg: str) -> str:
    """Strip Bearer tokens from error messages before logging."""
    return _BEARER_RE.sub("Bearer <redacted>", msg)

# --------------------------------------------------------------------
# Logging — structured JSON to stdout
# --------------------------------------------------------------------

LOG_LEVEL = logging.INFO
_log = logging.getLogger("bf-agent")
_log.setLevel(LOG_LEVEL)
if not _log.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _log.addHandler(_handler)
    _log.propagate = False

def log_event(
    event: str,
    correlation_id: str = "",
    compare_id: str = "",
    model: str = "",
    provider: str = "bifrost",
    t_rel_ms: int = 0,
    queue_delay_ms: int = 0,
    ttfb_ms: int = 0,
    body_ms: int = 0,
    total_ms: int = 0,
    timeout_ms: int = REQUEST_TIMEOUT_MS,
    status: str = "ok",
    error_type: str = "",
    error_msg: str = "",
    extra: dict | None = None,
):
    payload = {
        "event": event,
        "correlation_id": correlation_id,
        "compare_id": compare_id,
        "model": model,
        "provider": provider,
        "t_rel_ms": t_rel_ms,
        "queue_delay_ms": queue_delay_ms,
        "ttfb_ms": ttfb_ms,
        "body_ms": body_ms,
        "total_ms": total_ms,
        "timeout_ms": timeout_ms,
        "status": status,
        "error_type": error_type,
    }
    if error_msg:
        payload["error_msg"] = error_msg
    if extra:
        payload.update(extra)
    _log.info(json.dumps(payload))

# --------------------------------------------------------------------
# TypedDicts
# --------------------------------------------------------------------

class WorkerResult(TypedDict):
    model: str
    text: str
    ok: bool
    error: Optional[str]
    ttfb_ms: int
    total_ms: int
    queue_delay_ms: int
    status: str
    error_type: str

class GraphState(TypedDict):
    prompt: str
    models: List[str]
    results: Annotated[List[WorkerResult], add]
    synthesis: str
    correlation_id: str
    compare_id: str

# --------------------------------------------------------------------
# Prompt helpers
# --------------------------------------------------------------------

def system_prompt_for_mode(mode: str) -> str:
    prompts = {
        "brainstorm": (
            "You are a creative brainstorming partner. Generate multiple ideas, directions, and variations. "
            "Optimize for breadth before narrowing. State tradeoffs and open questions."
        ),
        "design": (
            "You are a systems architect. Focus on architecture, interfaces, module boundaries, contracts, and tradeoffs. "
            "Discuss failure modes and constraints."
        ),
        "plan": (
            "You are a project planner. Produce an ordered implementation plan with assumptions, risks, dependencies, and checkpoints."
        ),
        "review": (
            "You are a critical reviewer. Identify flaws, risks, brittleness, and stronger alternatives. Be direct and concrete."
        ),
        "explore": (
            "You are an explorer of ideas. Surface hypotheses, unknowns, promising directions, and key uncertainties."
        ),
    }
    return prompts.get(mode, prompts["brainstorm"])

def code_protocol_system_prompt() -> str:
    return (
        "You are a code agent operating through a local tool executor. "
        "You may request tools by responding with ONLY valid JSON. "
        "No markdown fences, no prose before or after the JSON. "
        "Supported actions: "
        "{\"action\":\"read_file\",\"path\":\"P:/...\"}, "
        "{\"action\":\"list_dir\",\"path\":\"P:/...\"}, "
        "{\"action\":\"glob\",\"pattern\":\"packages/**/*.py\"}, "
        "{\"action\":\"write_file\",\"path\":\"P:/...\",\"content\":\"...\"}, "
        "{\"action\":\"final_answer\",\"text\":\"...\"}. "
        "Prefer read/list/glob before making assumptions. "
        "Only use paths under the allowed root. "
        "When enough evidence is gathered, return final_answer."
    )

# --------------------------------------------------------------------
# Bifrost call helper
# --------------------------------------------------------------------

def bifrost_call(
    model: str,
    prompt: str,
    correlation_id: str,
    compare_id: str,
    system: str | None = None,
    max_tokens: int | None = None,
) -> WorkerResult:
    url = f"{BIFROST_BASE_URL}/anthropic/v1/messages"
    headers = {
        "Authorization": f"Bearer {BIFROST_VK}",
        "Content-Type": "application/json",
        "X-Correlation-ID": correlation_id,
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens or DEFAULT_MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

    t_scheduled = time.perf_counter()
    log_event(
        "model_call_scheduled",
        correlation_id=correlation_id,
        compare_id=compare_id,
        model=model,
        status="scheduled",
    )

    try:
        t_start = time.perf_counter()
        r = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_MS / 1000)
        t_done = time.perf_counter()
        r.raise_for_status()
        data = r.json()

        ttfb = int((t_done - t_start) * 1000)
        total_ms = int((t_done - t_scheduled) * 1000)

        content = data.get("content", [])
        text_parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))

        raw_text = "\n".join(text_parts).strip()
        log_event(
            "model_call_completed",
            correlation_id=correlation_id,
            compare_id=compare_id,
            model=model,
            ttfb_ms=ttfb,
            total_ms=total_ms,
            status="ok",
            extra={
                "raw_content_len": len(raw_text),
                "content_block_count": len(content),
                "bifrost_response_keys": list(data.keys()),
            },
        )
        return {
            "model": model,
            "text": raw_text,
            "ok": True,
            "error": None,
            "ttfb_ms": ttfb,
            "total_ms": total_ms,
            "queue_delay_ms": 0,
            "status": "ok",
            "error_type": "",
        }

    except requests.Timeout:
        t_done = time.perf_counter()
        total_ms = int((t_done - t_scheduled) * 1000)
        log_event(
            "model_call_timeout",
            correlation_id=correlation_id,
            compare_id=compare_id,
            model=model,
            total_ms=total_ms,
            status="timeout",
            error_type="Timeout",
        )
        return {
            "model": model,
            "text": "",
            "ok": False,
            "error": "request timed out",
            "ttfb_ms": 0,
            "total_ms": total_ms,
            "queue_delay_ms": 0,
            "status": "timeout",
            "error_type": "Timeout",
        }

    except Exception as e:
        t_done = time.perf_counter()
        total_ms = int((t_done - t_scheduled) * 1000)
        log_event(
            "model_call_failed",
            correlation_id=correlation_id,
            compare_id=compare_id,
            model=model,
            total_ms=total_ms,
            status="error",
            error_type=type(e).__name__,
            error_msg=_sanitize_error(str(e)),
        )
        return {
            "model": model,
            "text": "",
            "ok": False,
            "error": _sanitize_error(str(e)),
            "ttfb_ms": 0,
            "total_ms": total_ms,
            "queue_delay_ms": 0,
            "status": "error",
            "error_type": type(e).__name__,
        }

# --------------------------------------------------------------------
# Path guard
# --------------------------------------------------------------------

def _resolve_allowed_path(path_str: str) -> Path:
    p = Path(path_str).resolve()
    try:
        p.relative_to(BF_ALLOWED_ROOT)
    except ValueError:
        raise PermissionError(f"Access denied outside allowed root: {p}")
    return p

# --------------------------------------------------------------------
# Tool functions
# --------------------------------------------------------------------

def tool_read_file(path: str) -> dict:
    try:
        p = _resolve_allowed_path(path)
        if not p.exists() or not p.is_file():
            return {"ok": False, "error": f"not accessible: {path}"}
        p.read_text(encoding="utf-8", errors="ignore")  # re-resolve before I/O
        content = p.read_text(encoding="utf-8", errors="ignore")
        truncated = content[:BF_FILE_CHAR_LIMIT]
        return {
            "ok": True,
            "path": str(p),
            "chars": len(content),
            "truncated": len(content) > len(truncated),
            "content": truncated,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def tool_list_dir(path: str) -> dict:
    try:
        p = _resolve_allowed_path(path)
        if not p.exists():
            return {"ok": False, "error": f"directory not found: {p}"}
        if not p.is_dir():
            return {"ok": False, "error": f"not a directory: {p}"}
        items = []
        for item in sorted(p.iterdir(), key=lambda x: x.name.lower())[:BF_DIR_ITEM_LIMIT]:
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "path": str(item),
            })
        return {"ok": True, "path": str(p), "items": items}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def tool_glob(pattern: str) -> dict:
    try:
        matches = []
        for p in BF_ALLOWED_ROOT.glob(pattern):
            try:
                p.relative_to(BF_ALLOWED_ROOT)
            except ValueError:
                continue
            matches.append(str(p))
            if len(matches) >= BF_GLOB_LIMIT:
                break
        return {"ok": True, "pattern": pattern, "matches": matches}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def tool_write_file(path: str, content: str) -> dict:
    try:
        p = _resolve_allowed_path(path)
        parent = _resolve_allowed_path(str(p.parent))  # re-validate parent before mkdir
        p.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(p), "chars_written": len(content)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# --------------------------------------------------------------------
# Tool action executor
# --------------------------------------------------------------------

class ToolAction(BaseModel):
    action: Literal["read_file", "list_dir", "glob", "write_file", "final_answer"]
    path: str = ""
    content: str = ""
    pattern: str = ""

def execute_tool_action(action: dict) -> dict:
    try:
        validated = ToolAction(**action)
    except Exception:
        return {"action": action.get("action", ""), "result": {"ok": False, "error": "invalid tool action schema"}}
    kind = validated.action
    if kind == "read_file":
        return {"action": kind, "result": tool_read_file(validated.path)}
    if kind == "list_dir":
        return {"action": kind, "result": tool_list_dir(validated.path)}
    if kind == "glob":
        return {"action": kind, "result": tool_glob(validated.pattern)}
    if kind == "write_file":
        return {"action": kind, "result": tool_write_file(validated.path, validated.content)}
    if kind == "final_answer":
        return {"action": kind, "result": {}}
    return {"action": kind, "result": {"ok": False, "error": f"unknown action: {kind}"}}

# --------------------------------------------------------------------
# Compare graph nodes
# --------------------------------------------------------------------

def make_worker_node(model: str):
    def worker(state: GraphState):
        corr_id = state.get("correlation_id", "")
        cmp_id = state.get("compare_id", "")
        actual_model = state.get("model", model)
        prompt = state.get("prompt", "")

        if not prompt or not corr_id or not cmp_id:
            log_event(
                "model_call_skipped",
                correlation_id=corr_id,
                compare_id=cmp_id,
                model=actual_model,
                status="error",
                error_type="InvalidState",
                error_msg=f"missing required state fields: prompt={bool(prompt)} corr_id={bool(corr_id)} cmp_id={bool(cmp_id)}",
            )
            return {"results": [{
                "model": actual_model,
                "text": "",
                "ok": False,
                "error": "invalid state received from route_models",
                "ttfb_ms": 0,
                "total_ms": 0,
                "queue_delay_ms": 0,
                "status": "error",
                "error_type": "InvalidState",
            }]}

        log_event(
            "model_call_started",
            correlation_id=corr_id,
            compare_id=cmp_id,
            model=actual_model,
            status="started",
        )

        sys_prompt = (
            "You are one of several models being compared on the same task. "
            "Answer clearly and independently. "
            "State assumptions, tradeoffs, risks, and recommended next steps."
        )

        result = bifrost_call(actual_model, prompt, correlation_id=corr_id, compare_id=cmp_id, system=sys_prompt)
        return {"results": [result]}
    return worker

def route_models(state: GraphState):
    return {}

def synthesize(state: GraphState):
    corr_id = state.get("correlation_id", "")
    cmp_id = state.get("compare_id", "")
    t_start = time.perf_counter()

    log_event(
        "synthesis_started",
        correlation_id=corr_id,
        compare_id=cmp_id,
        status="started",
    )

    ok_results = [r for r in state.get("results", []) if r.get("ok")]
    failed = [r for r in state.get("results", []) if not r.get("ok")]
    ok_with_content = [r for r in ok_results if r.get("text", "").strip()]
    empty_ok = [r for r in ok_results if not r.get("text", "").strip()]

    if empty_ok:
        log_event(
            "synthesis_partial",
            correlation_id=corr_id,
            compare_id=cmp_id,
            status="warning",
            extra={
                "empty_ok_models": [r["model"] for r in empty_ok],
                "ok_count": len(ok_with_content),
                "failed_count": len(failed),
            },
        )

    if not ok_with_content:
        errors = "\n".join(
            f"- {r['model']}: {r.get('error') or 'unknown error' or 'empty response'}"
            for r in failed + empty_ok
        )
        synthesis_text = f"All model calls failed or returned empty.\n{errors}"
        log_event(
            "synthesis_completed",
            correlation_id=corr_id,
            compare_id=cmp_id,
            total_ms=int((time.perf_counter() - t_start) * 1000),
            status="error",
            extra={
                "ok_with_content": 0,
                "ok_empty": len(empty_ok),
                "failed": len(failed),
                "synthesis_len": len(synthesis_text),
            },
        )
        return {"synthesis": synthesis_text}

    chunks = []
    for r in ok_with_content:
        chunks.append(f"## {r['model']}\n{r['text']}")

    synthesis_prompt = (
        "You are synthesizing outputs from multiple models on the same task.\n\n"
        "Given the following answers, produce a single, structured response with:\n"
        "- Shared conclusions\n"
        "- Key disagreements\n"
        "- Best overall recommendation (and why)\n"
        "- Risks / brittleness\n"
        "- Concrete next steps\n\n"
        "Keep genuine disagreements visible; do not average them away.\n\n"
        + "\n\n".join(chunks)
    )

    final = bifrost_call(SYNTHESIS_MODEL, synthesis_prompt, correlation_id=corr_id, compare_id=cmp_id)
    if final["ok"]:
        synthesis_text = final["text"]
    else:
        log_event(
            "synthesis_fallback",
            correlation_id=corr_id,
            compare_id=cmp_id,
            status="warning",
            error_type=final.get("error_type", ""),
            error_msg=final.get("error", ""),
            extra={"models_in_synthesis": [r["model"] for r in ok_with_content]},
        )
        synthesis_text = "# Raw model outputs\n\n" + "\n\n".join(chunks)

    if failed:
        synthesis_text += (
            "\n\n# Failed model calls\n"
            + "\n".join(f"- {r['model']}: {r.get('error') or 'unknown error'}" for r in failed)
        )

    log_event(
        "synthesis_completed",
        correlation_id=corr_id,
        compare_id=cmp_id,
        total_ms=int((time.perf_counter() - t_start) * 1000),
        status="ok",
        extra={
            "ok_with_content": len(ok_with_content),
            "ok_empty": len(empty_ok),
            "failed": len(failed),
            "synthesis_len": len(synthesis_text),
        },
    )
    return {"synthesis": synthesis_text}

def build_graph(models: List[str]):
    graph = StateGraph(GraphState)
    graph.add_node("route_models", route_models)

    for model in models:
        graph.add_node(f"worker_{model}", make_worker_node(model))
        graph.add_edge(f"worker_{model}", "synthesize")

    graph.add_node("synthesize", synthesize)
    graph.set_entry_point("route_models")

    def fanout(state: GraphState):
        return [
            Send(
                f"worker_{model}",
                {
                    "model": model,
                    "prompt": state["prompt"],
                    "correlation_id": state.get("correlation_id", ""),
                    "compare_id": state.get("compare_id", ""),
                },
            )
            for model in state["models"]
        ]

    graph.add_conditional_edges("route_models", fanout)
    graph.add_edge("synthesize", END)
    return graph.compile()

# --------------------------------------------------------------------
# Code agent loop
# --------------------------------------------------------------------

def run_code_agent(prompt: str, model: str, correlation_id: str, max_turns: int) -> dict:
    compare_id = str(uuid.uuid4())
    conversation: List[dict] = []
    current_prompt = prompt
    turns: List[dict] = []

    for turn_index in range(max_turns):
        log_event(
            "code_turn_started",
            correlation_id=correlation_id,
            compare_id=compare_id,
            model=model,
            status="started",
            extra={"turn_index": turn_index + 1},
        )

        full_prompt = current_prompt if turn_index == 0 else json.dumps({"conversation": conversation}, ensure_ascii=False)
        result = bifrost_call(
            model=model,
            prompt=full_prompt,
            correlation_id=correlation_id,
            compare_id=compare_id,
            system=code_protocol_system_prompt(),
            max_tokens=DEFAULT_MAX_TOKENS,
        )

        if not result["ok"]:
            return {
                "ok": False,
                "mode": "code",
                "model": model,
                "error": result.get("error", "unknown model call error"),
                "turns": turns,
            }

        raw = result.get("text", "").strip()
        parsed: dict | None = None
        parse_error = None
        try:
            parsed = json.loads(raw)
        except Exception as e:
            parse_error = str(e)

        turns.append({
            "turn": turn_index + 1,
            "model_output": raw,
            "parsed": parsed,
            "parse_error": parse_error,
        })

        if not parsed:
            return {
                "ok": True,
                "mode": "code",
                "model": model,
                "answer": raw,
                "turns": turns,
                "completed_via": "plain_text_fallback",
            }

        action = parsed.get("action", "")
        tool_result = execute_tool_action(parsed)

        conversation.append({
            "turn": turn_index + 1,
            "model_raw": raw,
            "action": action,
            "tool_result": tool_result,
        })

        if action == "final_answer":
            return {
                "ok": True,
                "mode": "code",
                "model": model,
                "answer": parsed.get("text", ""),
                "turns": turns,
                "completed_via": "final_answer",
            }

        # build next turn's prompt with accumulated context
        ctx_parts = []
        for entry in conversation:
            ctx_parts.append(f"Turn {entry['turn']}: {entry['action']} → {json.dumps(entry['tool_result'], ensure_ascii=False)}")
        current_prompt = "Continue. Tool results so far:\n" + "\n".join(ctx_parts)

    return {
        "ok": True,
        "mode": "code",
        "model": model,
        "answer": "Max turns reached before final_answer.",
        "turns": turns,
        "completed_via": "max_turns",
    }

# --------------------------------------------------------------------
# Public API — simple wrappers for skill consumption
# --------------------------------------------------------------------

def run_simple(mode: str, prompt: str, model: str = "DSv4-flash") -> dict:
    """One-shot call for stateless modes (brainstorm/design/plan/review/explore)."""
    if mode not in VALID_RUN_MODES:
        raise ValueError(f"Unknown mode: {mode}")
    if model not in VALID_MODELS:
        raise ValueError(f"Unknown model: {model}")

    correlation_id = str(uuid.uuid4())
    log_event(
        "run_started",
        correlation_id=correlation_id,
        model=model,
        status="started",
        extra={"mode": mode, "prompt_chars": len(prompt)},
    )

    result = bifrost_call(
        model,
        prompt,
        correlation_id=correlation_id,
        compare_id="",
        system=system_prompt_for_mode(mode),
    )

    return {
        "ok": result.get("ok", False),
        "mode": mode,
        "model": model,
        "text": result.get("text", ""),
        "error": result.get("error"),
        "metrics": {
            "ttfb_ms": result.get("ttfb_ms", 0),
            "total_ms": result.get("total_ms", 0),
            "status": result.get("status", ""),
            "error_type": result.get("error_type", ""),
        },
    }


def run_compare(prompt: str, models: List[str] | None = None) -> dict:
    """Fan-out to multiple models in parallel, synthesize results via LangGraph."""
    if not models:
        models = DEFAULT_MODELS
    if not models:
        raise RuntimeError("No models configured")

    correlation_id = str(uuid.uuid4())
    compare_id = str(uuid.uuid4())

    t_wall_start = time.perf_counter()

    log_event(
        "compare_started",
        correlation_id=correlation_id,
        compare_id=compare_id,
        extra={
            "requested_models": models,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "prompt_chars": len(prompt),
            "timeout_ms": REQUEST_TIMEOUT_MS,
        },
    )

    graph = build_graph(models)
    state: GraphState = {
        "prompt": prompt,
        "models": models,
        "results": [],
        "synthesis": "",
        "correlation_id": correlation_id,
        "compare_id": compare_id,
    }

    result = graph.invoke(state)

    wall_time_ms = int((time.perf_counter() - t_wall_start) * 1000)
    all_results = result.get("results", [])
    timed_out_count = sum(1 for r in all_results if r.get("status") == "timeout")

    log_event(
        "compare_completed",
        correlation_id=correlation_id,
        compare_id=compare_id,
        t_rel_ms=wall_time_ms,
        status="ok" if timed_out_count == 0 else "partial",
        extra={
            "timed_out_models": timed_out_count,
            "models_summary": [
                {
                    "model": r["model"],
                    "ttfb_ms": r.get("ttfb_ms", 0),
                    "total_ms": r.get("total_ms", 0),
                    "queue_delay_ms": r.get("queue_delay_ms", 0),
                    "status": r.get("status", ""),
                    "error_type": r.get("error_type", ""),
                }
                for r in all_results
            ],
        },
    )

    return {
        "ok": True,
        "mode": "compare",
        "models": models,
        "results": result.get("results", []),
        "synthesis": result.get("synthesis", ""),
        "metrics": {
            "wall_time_ms": wall_time_ms,
            "timed_out_models": timed_out_count,
        },
    }


def run_code(prompt: str, model: str = "DSv4-flash", max_turns: int | None = None) -> dict:
    """Multi-turn code agent with tool loop."""
    if model not in VALID_MODELS:
        raise ValueError(f"Unknown model: {model}")

    correlation_id = str(uuid.uuid4())
    turns_limit = max_turns or BF_CODE_MAX_TURNS

    log_event(
        "code_started",
        correlation_id=correlation_id,
        model=model,
        status="started",
        extra={
            "prompt_chars": len(prompt),
            "max_turns": turns_limit,
            "allowed_root": "<redacted>",
        },
    )

    return run_code_agent(prompt, model, correlation_id, max_turns=turns_limit)