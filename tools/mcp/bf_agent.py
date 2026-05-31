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
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from typing import Annotated, TypedDict, List, Optional, Literal
from operator import add

import requests
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.types import Send

# --------------------------------------------------------------------
# Config
# --------------------------------------------------------------------

def _resolve_bifrost_base_url() -> str:
    """Return the Bifrost origin, defaulting to localhost:8080.

    BIFROST_BASE_URL may be set to either an origin or an origin + path.
    We normalize to the origin because this module appends /v1 and /anthropic
    paths itself.
    """
    raw = os.getenv("BIFROST_BASE_URL", "").strip()
    if raw:
        candidate = raw if "://" in raw else f"http://{raw}"
        parsed = urlparse(candidate)
        if parsed.scheme and parsed.netloc:
            host = parsed.hostname or "localhost"
            if parsed.port:
                return f"{parsed.scheme}://{host}:{parsed.port}"
            port_text = os.getenv("BIFROST_HTTP_PORT", "8080").strip() or "8080"
            return f"{parsed.scheme}://{host}:{int(port_text)}"
        return raw.rstrip("/")

    port_text = os.getenv("BIFROST_HTTP_PORT", "8080").strip() or "8080"
    return f"http://localhost:{int(port_text)}"


BIFROST_BASE_URL = _resolve_bifrost_base_url()
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
BF_CRITIQUE_ENABLED = os.getenv("BF_CRITIQUE_ENABLED", "true").lower() != "false"
BF_ARTIFACT_ROOT = Path(os.getenv("BF_ARTIFACT_ROOT", "P:/.claude/.artifacts"))

# --------------------------------------------------------------------
# Probe cache — skip models that recently failed to avoid hanging requests
# --------------------------------------------------------------------
PROBE_CACHE_TTL_S = float(os.getenv("BF_PROBE_CACHE_TTL", "300"))
_PROBE_CACHE: dict[str, tuple[bool, float]] = {}  # model → (ok, timestamp)


def _probe_cache_get(model: str) -> bool | None:
    """Return True if model is cached as failed, False if cached as ok, None if not cached."""
    if model not in _PROBE_CACHE:
        return None
    ok, ts = _PROBE_CACHE[model]
    if time.time() - ts > PROBE_CACHE_TTL_S:
        del _PROBE_CACHE[model]
        return None
    return ok


def _probe_cache_set(model: str, ok: bool):
    """Record probe result in cache."""
    _PROBE_CACHE[model] = (ok, time.time())


def _get_terminal_id() -> str:
    """Return a terminal-unique ID for artifact paths. CWD-hashed fallback if CONSOLE_ID not set."""
    console_id = os.getenv("CONSOLE_ID", "").strip()
    if console_id:
        return console_id
    try:
        return hashlib.md5(str(Path.cwd()).encode()).hexdigest()[:8]
    except Exception:
        return uuid.uuid4().hex[:8]

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

VALID_MODELS: set[str] = set()  # Deprecated — models are validated by Bifrost at runtime
VALID_RUN_MODES = {"brainstorm", "design", "plan", "review", "explore", "compare", "code"}

# --------------------------------------------------------------------
# Sanitization
# --------------------------------------------------------------------

import re as _re

_BEARER_RE = _re.compile(r"Bearer [\w\-]+")

def _sanitize_error(msg: str) -> str:
    """Strip Bearer tokens from error messages before logging."""
    return _BEARER_RE.sub("Bearer <redacted>", msg)

def _extract_model_from_cel(cel: str) -> str | None:
    """Extract model name from a CEL expression like 'model == "deepseek/deepseek-r1"'."""
    m = _re.search(r'model\s*==\s*"([^"]+)"', cel)
    return m.group(1) if m else None

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
    route: str
    route: str

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
# Bifrost catalog — dynamic model discovery
# --------------------------------------------------------------------

def _resolve_bifrost_http_port(base_url: str) -> int:
    parsed = urlparse(base_url)
    if parsed.port:
        return parsed.port
    return int(os.getenv("BIFROST_HTTP_PORT", "8080"))


BIFROST_HTTP_PORT = _resolve_bifrost_http_port(BIFROST_BASE_URL)


def list_catalog_models(
    min_context: int = 0,
    free_only: bool = False,
) -> List[dict]:
    """List all models available in the Bifrost catalog.

    Args:
        min_context: Skip models with context_length below this (tokens).
        free_only: Skip paid models (':free' suffix or $0 price).

    Returns:
        List of dicts with keys: id, provider, model_id, context_length, label.
    """
    url = f"{BIFROST_BASE_URL}/v1/models"
    headers = {"Authorization": f"Bearer {BIFROST_VK}"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        body = r.json()
        all_models = body.get("data", []) if isinstance(body, dict) else body
    except Exception as e:
        log_event(
            "catalog_fetch_failed",
            provider="bifrost",
            status="error",
            error_type=type(e).__name__,
            error_msg=_sanitize_error(str(e)),
        )
        return []

    candidates = []
    for m in all_models:
        mid = m.get("id", "")
        if "/" not in mid:
            continue
        prov, model_id = mid.split("/", 1)
        ctx = m.get("context_length", 0) or 0

        if min_context and ctx < min_context:
            continue

        is_free = ":free" in mid or m.get("pricing", {}).get("prompt") == "0"
        if free_only and not is_free:
            continue

        label = "FREE" if is_free else "PAID"
        candidates.append({
            "id": mid,
            "provider": prov,
            "model_id": model_id,
            "context_length": ctx,
            "label": label,
        })

    return candidates


def probe_model(model: str) -> dict:
    """Probe a single model through Bifrost via /v1/chat/completions.

    Sends a 1-token completion and reads back the actual target provider
    and latency from extra_fields.

    Returns:
        dict with keys: ok, provider, latency_ms, model_requested, error.
    """
    url = f"{BIFROST_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {BIFROST_VK}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "probe"}],
        "max_tokens": 1,
    }
    try:
        t_start = time.perf_counter()
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        t_done = time.perf_counter()
        r.raise_for_status()
        body = r.json()
        extra = body.get("extra_fields", {})
        prov = extra.get("provider", "?")
        lat = extra.get("latency", 0)
        return {
            "ok": True,
            "provider": prov,
            "latency_ms": lat,
            "model_requested": model,
            "error": "",
        }
    except Exception as e:
        return {
            "ok": False,
            "provider": "?",
            "latency_ms": 0,
            "model_requested": model,
            "error": _sanitize_error(str(e)),
        }


def probe_routes() -> dict:
    """Probe all currently configured routes — DB state + live runtime verification.

    Returns:
        dict with:
          routes: list of {priority, model, provider, target, latency_ms, probe_ok, probe_error}
          ok_count, err_count, summary
    """
    import sqlite3

    db_path = os.getenv("BIFROST_DB", r"C:\Users\brsth\AppData\Roaming\bifrost\config.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT r.id, r.name, r.cel_expression, r.priority, rt.provider, rt.model
        FROM routing_rules r
        LEFT JOIN routing_targets rt ON rt.rule_id = r.id
        WHERE r.enabled = 1
        ORDER BY r.priority
    """)
    rules = []
    for row in c.fetchall():
        rules.append({
            "id": row[0], "name": row[1] or row[0],
            "cel": row[2] or "", "priority": row[3],
            "provider": row[4], "model": row[5],
        })
    conn.close()

    results = []
    ok_count = 0
    err_count = 0
    for rule in rules:
        mn = _extract_model_from_cel(rule["cel"]) or rule["cel"]
        tgt = f"{rule['provider']}/{rule['model']}" if rule["provider"] and rule["model"] else "NO TARGET"
        if not mn:
            probe_result = {"ok": False, "provider": "?", "latency_ms": 0, "model_requested": rule["id"], "error": "no model in CEL"}
            err_count += 1
        else:
            probe_result = probe_model(mn)
            if probe_result["ok"]:
                ok_count += 1
            else:
                err_count += 1
        results.append({
            "priority": rule["priority"],
            "model": mn,
            "target": tgt,
            "provider": probe_result["provider"],
            "latency_ms": probe_result.get("latency_ms", 0),
            "probe_ok": probe_result["ok"],
            "probe_error": probe_result.get("error", ""),
        })

    summary = f"{ok_count} OK, {err_count} ERROR"
    return {"routes": results, "ok_count": ok_count, "err_count": err_count, "summary": summary}


# --------------------------------------------------------------------
# Route management
# --------------------------------------------------------------------

def add_route(
    model: str,
    provider: str,
    target: str,
    name: str | None = None,
    priority: int = 50,
    enabled: bool = True,
) -> dict:
    """Add a routing rule to the Bifrost config.db.

    Args:
        model: Full model ID the route matches (e.g. "deepseek/deepseek-r1")
        provider: Target provider (e.g. "openrouter")
        target: Target model on that provider (e.g. "deepseek/deepseek-r1-0520")
        name: Human-readable name for the rule (auto-generated if omitted)
        priority: Lower = higher priority (default 50)
        enabled: Whether the rule is active immediately (default True)

    Returns:
        {"ok": True, "rule_id": <new id>} or {"ok": False, "error": "..."}
    """
    import sqlite3

    db_path = os.getenv("BIFROST_DB", r"C:\Users\brsth\AppData\Roaming\bifrost\config.db")
    if _re.search(r'["\\]', model):
        return {"ok": False, "error": "model must not contain quotes or backslashes"}
    cel_expr = f'model == "{model}"'
    rule_name = name or f"{model} → {provider}/{target}"

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Check for existing rule with same CEL expression
        c.execute("SELECT id FROM routing_rules WHERE cel_expression = ?", (cel_expr,))
        existing = c.fetchone()
        if existing:
            conn.close()
            return {"ok": False, "error": f"Rule already exists with id {existing[0]}"}

        # Insert new rule
        c.execute(
            """
            INSERT INTO routing_rules (name, cel_expression, enabled, priority)
            VALUES (?, ?, ?, ?)
            """,
            (rule_name, cel_expr, 1 if enabled else 0, priority),
        )
        rule_id = c.lastrowid

        # Insert routing target
        c.execute(
            """
            INSERT INTO routing_targets (rule_id, provider, model)
            VALUES (?, ?, ?)
            """,
            (rule_id, provider, target),
        )

        conn.commit()
        conn.close()

        log_event(
            "route_added",
            model=model,
            provider=provider,
            status="ok",
            extra={"rule_id": rule_id, "target": f"{provider}/{target}"},
        )
        return {"ok": True, "rule_id": rule_id}

    except Exception as e:
        log_event(
            "route_add_failed",
            model=model,
            provider=provider,
            status="error",
            error_type=type(e).__name__,
            error_msg=_sanitize_error(str(e)),
        )
        return {"ok": False, "error": _sanitize_error(str(e))}


def delete_route(rule_id: int) -> dict:
    """Delete a routing rule and its target by rule_id.

    Returns:
        {"ok": True} or {"ok": False, "error": "..."}
    """
    import sqlite3

    db_path = os.getenv("BIFROST_DB", r"C:\Users\brsth\AppData\Roaming\bifrost\config.db")

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Verify rule exists
        c.execute("SELECT id, name FROM routing_rules WHERE id = ?", (rule_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"ok": False, "error": f"No rule found with id {rule_id}"}

        rule_name = row[1]
        c.execute("DELETE FROM routing_targets WHERE rule_id = ?", (rule_id,))
        c.execute("DELETE FROM routing_rules WHERE id = ?", (rule_id,))
        conn.commit()
        conn.close()

        log_event("route_deleted", model=rule_name, status="ok", extra={"rule_id": rule_id})
        return {"ok": True}

    except Exception as e:
        return {"ok": False, "error": _sanitize_error(str(e))}


def list_routes() -> dict:
    """List all routing rules from config.db (enabled and disabled).

    Returns:
        {"routes": [{id, name, cel, priority, enabled, provider, target}], "count": N}
    """
    import sqlite3

    db_path = os.getenv("BIFROST_DB", r"C:\Users\brsth\AppData\Roaming\bifrost\config.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT r.id, r.name, r.cel_expression, r.priority, r.enabled, rt.provider, rt.model
        FROM routing_rules r
        LEFT JOIN routing_targets rt ON rt.rule_id = r.id
        ORDER BY r.priority
    """)
    routes = []
    for row in c.fetchall():
        routes.append({
            "id": row[0],
            "name": row[1] or row[0],
            "cel": row[2] or "",
            "priority": row[3],
            "enabled": bool(row[4]),
            "provider": row[5] or "",
            "target": f"{row[5]}/{row[6]}" if row[5] and row[6] else "",
        })
    conn.close()
    return {"routes": routes, "count": len(routes)}


# --------------------------------------------------------------------
# Direct provider call helper — bypass Bifrost for providers with known endpoints
# --------------------------------------------------------------------

import sqlite3

def _get_provider_info(provider: str) -> tuple[str, str] | None:
    """Look up base_url and api_key for a provider from Bifrost DB.
    Returns (base_url, api_key) or None if not found.
    Providers without a DB entry get hardcoded standard defaults."""
    # Standard OpenAI-compatible base URLs for providers not in config_providers
    STANDARD_BASE_URLS = {
        "groq": "https://api.groq.com/openai/v1",
        "mistral": "https://api.mistral.ai/v1",
        "cerebras": "https://api.cerebras.ai/v1",
        "gemini": "https://generativelanguage.googleapis.com",
        "openrouter": "https://openrouter.ai/api",
    }
    p_lower = provider.lower()
    try:
        db_path = os.getenv("BIFROST_DB", r"C:\Users\brsth\AppData\Roaming\bifrost\config.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            SELECT cp.network_config_json, ck.value
            FROM config_providers cp
            LEFT JOIN config_keys ck ON LOWER(ck.provider) = LOWER(cp.name) AND ck.enabled = 1
            WHERE LOWER(cp.name) = LOWER(?)
            LIMIT 1
        """, (provider,))
        row = c.fetchone()
        conn.close()

        # Try DB entry first
        if row:
            net_cfg, api_key = row
            if net_cfg:
                cfg = json.loads(net_cfg)
                base_url = cfg.get("base_url", "").rstrip("/")
                if base_url:
                    return base_url, (api_key or "").strip()

        # Fall back to standard base URLs for known providers
        if p_lower in STANDARD_BASE_URLS:
            conn2 = sqlite3.connect(db_path)
            key_row = conn2.execute(
                "SELECT value FROM config_keys WHERE LOWER(provider)=? AND enabled=1 LIMIT 1",
                (p_lower,)
            ).fetchone()
            conn2.close()
            if key_row:
                return STANDARD_BASE_URLS[p_lower], key_row[0].strip()
        return None
    except Exception:
        return None


# --------------------------------------------------------------------
# Provider capability registry — params to strip per provider
# --------------------------------------------------------------------
_PROVIDER_STRICT_PARAMS: dict[str, list[str]] = {
    "mistral": ["reasoning_effort"],
}

def _strip_unsupported_params(provider: str, payload: dict) -> dict:
    """Remove provider-incompatible params from API payload."""
    strip = _PROVIDER_STRICT_PARAMS.get(provider.lower(), [])
    if not strip:
        return payload
    return {k: v for k, v in payload.items() if k not in strip}


def _direct_call(
    provider: str,
    model: str,
    prompt: str,
    correlation_id: str,
    compare_id: str,
    system: str | None = None,
    max_tokens: int | None = None,
) -> WorkerResult:
    """Call a provider endpoint directly, bypassing Bifrost."""
    info = _get_provider_info(provider)
    if not info:
        return {
            "model": model, "text": "", "ok": False,
            "error": f"no direct endpoint for provider: {provider}",
            "ttfb_ms": 0, "total_ms": 0, "queue_delay_ms": 0,
            "status": "error", "error_type": "NoDirectEndpoint",
        }
    base_url, api_key = info

    # Gemini uses ?key= query param, not Bearer header
    provider_lower = provider.lower()
    if provider_lower == "gemini":
        headers = {"Content-Type": "application/json"}
        api_path = f"/v1beta/models/{model}:generateContent"
        gemini_params = {"key": api_key}
    else:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
        }
        api_path = (
            "/v1/messages"
            if provider_lower == "minimax"
            else "/anthropic/v1/messages"
            if provider_lower == "z.ai"
            else "/chat/completions"
            if provider_lower in ("groq", "mistral", "cerebras")
            else "/v1/chat/completions"
        )
        gemini_params = None

    messages = [{"role": "user", "content": prompt}]
    if system:
        messages.insert(0, {"role": "system", "content": system})

    # Build payload based on provider format
    if provider_lower == "gemini":
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens or DEFAULT_MAX_TOKENS},
        }
    else:
        payload = {
            "model": model,
            "max_tokens": max_tokens or DEFAULT_MAX_TOKENS,
            "messages": messages,
        }

    t_scheduled = time.perf_counter()
    log_event(
        "model_call_scheduled",
        correlation_id=correlation_id,
        compare_id=compare_id,
        model=model,
        status="scheduled",
        provider=provider,
    )

    try:
        t_start = time.perf_counter()
        payload = _strip_unsupported_params(provider_lower, payload)
        r = requests.post(
            f"{base_url}{api_path}",
            headers=headers,
            json=payload,
            params=gemini_params or None,
            timeout=30,
        )
        t_done = time.perf_counter()
        r.raise_for_status()
        data = r.json()

        ttfb = int((t_done - t_start) * 1000)
        total_ms = int((t_done - t_scheduled) * 1000)

        if provider_lower == "gemini":
            parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
            text_parts = [p.get("text", "") for p in parts if p.get("text")]
            raw_text = "\n".join(text_parts).strip()
            content_count = len(parts)
        else:
            content = data.get("content", [])
            text_parts: List[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            raw_text = "\n".join(text_parts).strip()
            if not raw_text:
                msg = (data.get("choices") or [{}])[0].get("message") or {}
                raw_text = msg.get("reasoning_content", "") or msg.get("reasoning", "") or msg.get("content", "") or ""
                raw_text = raw_text.strip()
            content_count = len(content)
        log_event(
            "model_call_completed",
            correlation_id=correlation_id,
            compare_id=compare_id,
            model=model,
            provider=provider,
            ttfb_ms=ttfb,
            total_ms=total_ms,
            status="ok",
            extra={"raw_content_len": len(raw_text), "content_block_count": content_count},
        )
        return {
            "model": model, "text": raw_text, "ok": True,
            "error": None, "ttfb_ms": ttfb, "total_ms": total_ms,
            "queue_delay_ms": 0, "status": "ok", "error_type": "",
        }
    except requests.Timeout:
        t_done = time.perf_counter()
        total_ms = int((t_done - t_scheduled) * 1000)
        log_event("model_call_timeout", correlation_id=correlation_id, compare_id=compare_id,
                  model=model, provider=provider, total_ms=total_ms, status="timeout", error_type="Timeout")
        return {"model": model, "text": "", "ok": False, "error": "request timed out",
                "ttfb_ms": 0, "total_ms": total_ms, "queue_delay_ms": 0,
                "status": "timeout", "error_type": "Timeout"}
    except Exception as e:
        t_done = time.perf_counter()
        total_ms = int((t_done - t_scheduled) * 1000)
        log_event("model_call_failed", correlation_id=correlation_id, compare_id=compare_id,
                  model=model, provider=provider, total_ms=total_ms, status="error",
                  error_type=type(e).__name__, error_msg=_sanitize_error(str(e)))
        return {"model": model, "text": "", "ok": False, "error": _sanitize_error(str(e)),
                "ttfb_ms": 0, "total_ms": total_ms, "queue_delay_ms": 0,
                "status": "error", "error_type": type(e).__name__}


# --------------------------------------------------------------------
# Routing lookup — model to provider mapping from Bifrost DB
# --------------------------------------------------------------------

def _resolve_model_to_provider(model: str) -> tuple[str, str] | None:
    """Look up which provider a model routes to, and the actual model ID.
    Returns (provider, actual_model_id) or None if not found in routing_rules."""
    try:
        db_path = os.getenv("BIFROST_DB", r"C:\Users\brsth\AppData\Roaming\bifrost\config.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            SELECT rt.provider, rt.model
            FROM routing_rules r
            JOIN routing_targets rt ON rt.rule_id = r.id
            WHERE r.enabled = 1
              AND r.cel_expression LIKE '%' || ? || '%'
            LIMIT 1
        """, (model,))
        row = c.fetchone()
        conn.close()
        return (row[0], row[1]) if row else None
    except Exception:
        return None


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
    route: str = "auto",
) -> WorkerResult:
    """
    route: "auto"  — DB lookup → direct if provider found, else Bifrost HTTP
          "direct" — force SDK call, skip DB lookup and Bifrost
          "bifrost" — force Bifrost HTTP, skip DB lookup and direct
    """
    # Determine which path to take
    force_direct = route == "direct"
    force_bifrost = route == "bifrost"

    # Auto-routing: check DB if not forced
    db_route: tuple[str, str] | None = None
    if not force_direct and not force_bifrost:
        db_route = _resolve_model_to_provider(model)

    if db_route:
        # DB says this model maps to a direct provider
        provider, actual_model = db_route
        direct_info = _get_provider_info(provider)
        if direct_info:
            # Pre-flight: skip if model is cached as recently failed
            cache_key = f"{provider}:{actual_model}"
            cached = _probe_cache_get(cache_key)
            if cached is True:
                log_event(
                    "model_call_skipped",
                    correlation_id=correlation_id,
                    compare_id=compare_id,
                    model=model,
                    provider=provider,
                    status="skipped",
                )
                return {
                    "model": model, "text": "", "ok": False,
                    "error": "model cached as unavailable",
                    "ttfb_ms": 0, "total_ms": 0, "queue_delay_ms": 0,
                    "status": "probe_cache_hit", "error_type": "",
                }
            log_event(
                "route_decision",
                correlation_id=correlation_id,
                model=model,
                provider=provider,
            )
            result = _direct_call(provider, actual_model, prompt, correlation_id, compare_id, system, max_tokens)
            _probe_cache_set(cache_key, result.get("ok", False))
            return result

    url = f"{BIFROST_BASE_URL}/anthropic/v1/messages"
    headers = {
        "x-api-key": BIFROST_VK,
        "Content-Type": "application/json",
        "X-Correlation-ID": correlation_id,
        "anthropic-version": "2023-06-01",
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

def _bf_session_path(cmp_id: str) -> Path:
    """Return the per-compare artifact directory: {BF_ARTIFACT_ROOT}/console_{tid}/bf/{cmp_id}/"""
    tid = _get_terminal_id()
    base = BF_ARTIFACT_ROOT / f"console_{tid}" / "bf" / cmp_id
    try:
        base.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return base


def _write_response_files(cmp_id: str, results: List[dict]) -> dict:
    """Write each model's raw result as {session}/responses/{model}.json"""
    session = _bf_session_path(cmp_id)
    responses_dir = session / "responses"
    try:
        responses_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    written = []
    for r in results:
        model = r.get("model", "unknown")
        path = responses_dir / f"{model}.json"
        try:
            path.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
            written.append(str(path))
        except Exception:
            pass
    return {"compare_id": cmp_id, "session": str(session), "written": written}


def _run_critique(cmp_id: str, results: List[dict], correlation_id: str) -> dict:
    """Read response files, run critic model, write critique.md"""
    session = _bf_session_path(cmp_id)
    responses_dir = session / "responses"

    # Re-read from disk to get clean state after LangGraph serialization round-trip
    model_outputs = []
    for r in results:
        model = r.get("model", "unknown")
        path = responses_dir / f"{model}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                model_outputs.append(data)
            except Exception:
                model_outputs.append(r)
        else:
            model_outputs.append(r)

    if not model_outputs:
        return {"compare_id": cmp_id, "critique_path": "", "ok": False, "error": "no response files found"}

    # Build critique prompt with full per-model data
    chunks = []
    for r in model_outputs:
        status_note = ""
        if not r.get("ok"):
            status_note = f" [ERROR: {r.get('error') or 'unknown'}]"
        elif not r.get("text", "").strip():
            status_note = " [EMPTY]"
        chunks.append(
            f"## {r['model']}{status_note}\n"
            f"TTFB: {r.get('ttfb_ms', 0)}ms | Total: {r.get('total_ms', 0)}ms | Status: {r.get('status', 'unknown')}\n"
            f"{r.get('text', '')}"
        )

    critique_prompt = (
        "You are a critical reviewer comparing outputs from multiple LLMs on the same task.\n\n"
        "For each model, assess:\n"
        "- Factual correctness of claims\n"
        "- Internal consistency (does the reasoning hold?)\n"
        "- Overconfidence or hedging flags\n"
        "- Missing considerations or oversimplifications\n\n"
        "Produce a structured critique with:\n"
        "- Key agreements across models\n"
        "- Key disagreements and which model is more credible\n"
        "- Most concerning claim (high confidence but low grounding)\n"
        "- Verdict: which model produced the best overall answer\n"
        "- Any additional concerns about failure modes\n\n"
        "Keep disagreement visible — do not average to false consensus.\n\n"
        + "\n\n".join(chunks)
    )

    critique_path = session / "critique.md"
    try:
        result = bifrost_call(
            SYNTHESIS_MODEL,
            critique_prompt,
            correlation_id=correlation_id,
            compare_id=cmp_id,
        )
        if result.get("ok") and result.get("text"):
            critique_path.write_text(result["text"], encoding="utf-8")
            return {"compare_id": cmp_id, "critique_path": str(critique_path), "ok": True}
        else:
            return {"compare_id": cmp_id, "critique_path": str(critique_path), "ok": False, "error": result.get("error", "critique call failed")}
    except Exception as e:
        return {"compare_id": cmp_id, "critique_path": str(critique_path), "ok": False, "error": str(e)}


# --------------------------------------------------------------------
# Compare graph nodes
# --------------------------------------------------------------------

def write_results(state: GraphState):
    """Write each model's response to disk, then trigger critique."""
    cmp_id = state.get("compare_id", "")
    corr_id = state.get("correlation_id", "")
    results = state.get("results", [])

    if not cmp_id:
        return {}
    write_outcome = _write_response_files(cmp_id, results)
    log_event(
        "write_results_completed",
        correlation_id=corr_id,
        compare_id=cmp_id,
        status="ok",
        extra={"session": write_outcome.get("session"), "files_written": len(write_outcome.get("written", []))},
    )
    return {"write_outcome": write_outcome}


def critique_results(state: GraphState):
    """Run critic pass over all response files."""
    cmp_id = state.get("compare_id", "")
    corr_id = state.get("correlation_id", "")
    results = state.get("results", [])

    if not cmp_id:
        return {}
    if not BF_CRITIQUE_ENABLED:
        log_event("critique_skipped", correlation_id=corr_id, compare_id=cmp_id, status="skipped", extra={"reason": "BF_CRITIQUE_ENABLED=false"})
        return {"critique_outcome": {"compare_id": cmp_id, "ok": False, "skipped": True}}

    outcome = _run_critique(cmp_id, results, corr_id)
    status = "ok" if outcome.get("ok") else "warning"
    log_event(
        "critique_completed",
        correlation_id=corr_id,
        compare_id=cmp_id,
        status=status,
        extra={"critique_path": outcome.get("critique_path", ""), "ok": outcome.get("ok", False)},
    )
    return {"critique_outcome": outcome}


def route_models(state: GraphState):
    return {}

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

    # Build chunks with timing metadata (read fresh from response files)
    session = _bf_session_path(cmp_id)
    responses_dir = session / "responses"
    chunks = []
    for r in ok_with_content:
        model = r.get("model", "unknown")
        path = responses_dir / f"{model}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                timing = f"TTFB: {data.get('ttfb_ms', 0)}ms | Total: {data.get('total_ms', 0)}ms"
                chunks.append(f"## {model}\n[{timing}]\n{data.get('text', '')}")
            except Exception:
                chunks.append(f"## {model}\n{r['text']}")
        else:
            chunks.append(f"## {model}\n{r['text']}")

    # Read critique if available
    critique_path = session / "critique.md"
    critique_text = ""
    if critique_path.exists():
        try:
            critique_text = critique_path.read_text(encoding="utf-8")
        except Exception:
            critique_text = ""

    synthesis_prompt = (
        "You are synthesizing outputs from multiple models on the same task.\n\n"
        "Given the following answers, produce a single, structured response with:\n"
        "- Shared conclusions\n"
        "- Key disagreements\n"
        "- Best overall recommendation (and why)\n"
        "- Risks / brittleness\n"
        "- Concrete next steps\n\n"
        "Keep genuine disagreements visible; do not average them away.\n\n"
        + ("\n\n## Critic Review\n\n" + critique_text + "\n\n" if critique_text else "")
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
        graph.add_edge(f"worker_{model}", "write_results")

    graph.add_node("write_results", write_results)
    graph.add_edge("write_results", "critique_results")
    graph.add_node("critique_results", critique_results)
    graph.add_edge("critique_results", "synthesize")

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

def run_code_agent(prompt: str, model: str, correlation_id: str, max_turns: int, route: str = "auto") -> dict:
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
            route=route,
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

def run_simple(mode: str, prompt: str, model: str | None = None, route: str = "auto") -> dict:
    """One-shot call for stateless modes (brainstorm/design/plan/review/explore).
    route: "auto" (DB-based routing), "direct" (force SDK), "bifrost" (force Bifrost HTTP).
    """
    if model is None:
        model = os.getenv("BF_DEFAULT_MODEL", "M27")
    if mode not in VALID_RUN_MODES:
        raise ValueError(f"Unknown mode: {mode}")

    correlation_id = str(uuid.uuid4())
    log_event(
        "run_started",
        correlation_id=correlation_id,
        model=model,
        status="started",
        extra={"mode": mode, "prompt_chars": len(prompt), "route": route},
    )

    result = bifrost_call(
        model,
        prompt,
        correlation_id=correlation_id,
        compare_id="",
        system=system_prompt_for_mode(mode),
        route=route,
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


def run_compare(prompt: str, models: List[str] | None = None, route: str = "auto") -> dict:
    """Fan-out to multiple models in parallel, synthesize results via LangGraph.
    route: "auto" (DB-based), "direct" (force SDK), "bifrost" (force Bifrost HTTP).
    """
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
            "route": route,
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
        "route": route,
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

    session_path = str(_bf_session_path(compare_id))

    return {
        "ok": True,
        "mode": "compare",
        "models": models,
        "results": result.get("results", []),
        "synthesis": result.get("synthesis", ""),
        "critique_path": str(_bf_session_path(compare_id) / "critique.md"),
        "session_path": session_path,
        "metrics": {
            "wall_time_ms": wall_time_ms,
            "timed_out_models": timed_out_count,
        },
    }


def run_code(prompt: str, model: str = "DSv4-flash", max_turns: int | None = None, route: str = "auto") -> dict:
    """Multi-turn code agent with tool loop.
    route: "auto" (DB-based), "direct" (force SDK), "bifrost" (force Bifrost HTTP).
    """

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
            "route": route,
        },
    )

    return run_code_agent(prompt, model, correlation_id, max_turns=turns_limit, route=route)
