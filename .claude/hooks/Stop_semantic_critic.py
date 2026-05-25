#!/usr/bin/env python3
"""
Stop_semantic_critic.py - Semantic quality gate for diagnostic/analytical responses.

Python Stop hook (in-process gate) that judges whether analytical responses
adequately address the diagnostic question at hand via parallel MiniMax + Mistral calls.

Early exits (skip entirely):
- stop_hook_active circuit breaker
- Empty response
- is_non_substantive_turn() returns True

Scope gate (conservative keyword + >50 words):
- Detects diagnostic/causal/explanatory/evaluative flavor
- Only fires critic when scope is detected

External critic:
- Parallel MiniMax + Mistral direct calls with conservative combination
- Hard timeout per backend (MiniMax 10s, Mistral 30s)
- Strict JSON parsing with fence-stripping
- Fail-open on any error

Per-session cap: SEMANTIC_CRITIC_CAP (default 5) invocations before skipping.

Classified as "quality" gate - suppressed on control/exploration turns.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

import requests

# Track which sessions have opted out or hit the cap
_INVOCATION_COUNTS: dict[str, int] = {}
_stop_hook_active = os.environ.get("STOP_HOOK_ACTIVE", "").lower() in ("1", "true", "yes")
_logger = logging.getLogger(__name__)

# Per-session cap for critic invocations
SEMANTIC_CRITIC_CAP: int = int(os.environ.get("SEMANTIC_CRITIC_CAP", "5"))

# MiniMax direct call config
SEMANTIC_CRITIC_MODEL: str = os.environ.get("SEMANTIC_CRITIC_MODEL", "MiniMax-M2.7")
SEMANTIC_CRITIC_TIMEOUT_SEC: int = int(os.environ.get("SEMANTIC_CRITIC_TIMEOUT_SEC", "10"))

# Mistral direct call config
MISTRAL_MODEL: str = os.environ.get("MISTRAL_MODEL", "mistral-medium-3.5")
MISTRAL_TIMEOUT_SEC: int = int(os.environ.get("MISTRAL_TIMEOUT_SEC", "30"))

# Cached API keys (loaded once, reused across invocations)
_MINIMAX_API_KEY: str | None = None
_MISTRAL_API_KEY: str | None = None


@dataclass
class SemanticCriticResult:
    ok: bool
    reason: str


def _load_minimax_key() -> str | None:
    """Load MiniMax API key from env or P:/.env."""
    global _MINIMAX_API_KEY
    if _MINIMAX_API_KEY is not None:
        return _MINIMAX_API_KEY or None

    key = os.environ.get("MINIMAX_API_KEY", "").strip().strip('"')
    if key:
        _MINIMAX_API_KEY = key
        return key
    env_path = Path("P:/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("MINIMAX_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
                _MINIMAX_API_KEY = key
                return key
    _MINIMAX_API_KEY = ""  # sentinel: tried and failed
    return None


def _load_mistral_key() -> str | None:
    """Load Mistral API key from env or P:/.env."""
    global _MISTRAL_API_KEY
    if _MISTRAL_API_KEY is not None:
        return _MISTRAL_API_KEY or None

    key = os.environ.get("MISTRAL_API_KEY", "").strip().strip('"')
    if key:
        _MISTRAL_API_KEY = key
        return key
    env_path = Path("P:/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("MISTRAL_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
                _MISTRAL_API_KEY = key
                return key
    _MISTRAL_API_KEY = ""  # sentinel: tried and failed
    return None


# ---------------------------------------------------------------------------
# Veridical integrity config (behavioral sycophancy detection)
# ---------------------------------------------------------------------------

VERIDICAL_GATE_CAP: int = int(os.environ.get("VERIDICAL_GATE_CAP", "5"))
_VERIDICAL_COUNTS: dict[str, int] = {}
_VERIDICAL_FAILURE_STREAK: dict[str, int] = {}
VERIDICAL_CIRCUIT_BREAKER_LIMIT = 3
VERIDICAL_COOLDOWN_SEC = 300


def _session_key(data: dict) -> str:
    """Derive a stable key for session/terminal cap tracking."""
    session = data.get("session_id", "")
    terminal = data.get("terminal_id", "")
    if session:
        return session
    if terminal:
        return terminal
    # Fallback: hash of session path or cwd
    try:
        return hashlib.md5(str(Path.cwd()).encode()).hexdigest()[:8]
    except Exception:
        return "default"


def _build_critic_user_message(original_prompt: str, assistant_response: str) -> str:
    """Build the exact user message format specified in the design."""
    return f"""Evaluate the assistant response below.

Original user prompt:
<<<USER_PROMPT
{original_prompt}
USER_PROMPT>>>

Assistant response:
<<<ASSISTANT_RESPONSE
{assistant_response}
ASSISTANT_RESPONSE>>>"""


# =============================================================================
# Critic prompt profiles
# =============================================================================


def _detect_critic_profile(original_user_prompt: str, assistant_response: str) -> str:
    """
    Deterministically select a critic profile based on prompt/response content.

    Do NOT add an LLM call here — use only substring/regex heuristics.
    Fallback is `general_diagnostic` when no signal matches.
    """
    combined = (original_user_prompt + " " + assistant_response).lower()

    software_signals = [
        "bug", "crash", "timeout", "latency", "regression", "deploy",
        "api", "service", "logs", "trace", "stack",
        "incident", "deadlock", "thread", "query",
        "database", "config", "exception",
        "502", "503", "504", "401", "403", "500", "connection refused",
        "out of memory", "oom", "heap", "cpu", "disk", "network",
        "docker", "kubernetes", "k8s", "yaml", "auth",
        "nullpointer", "null reference",
    ]
    # Word-boundary matching to avoid substring collision
    # (e.g. "error" inside "interest", "crash" inside "economic")
    # Also split compound words so "NullPointerException" contains "exception"
    tokens = set(re.findall(r'\b\w+\b', combined))

    def _matches(signal: str) -> bool:
        # Multi-word signals: each word must appear in token set
        if ' ' in signal:
            return all(word in tokens for word in signal.split())
        # Single-word signals: regex word-boundary OR contained in any token
        # (e.g. "exception" is found in "NullPointerException")
        return (
            re.search(r'\b' + re.escape(signal) + r'\b', combined) is not None
            or any(signal in token for token in tokens)
        )

    signal_count = sum(1 for s in software_signals if _matches(s))

    if re.search(r'\broot cause\b', combined) or signal_count >= 2:
        return "software_rca"

    evaluative_signals = [
        "best", "better", "compare", "versus", "vs",
        "choose", "choice", "recommend", "recommendation",
        "tradeoff", "trade-offs", "pros", "cons", "option",
        "priority", "prioritize", "worth it", "should we use",
        "which should", "which library", "which framework",
    ]
    # Use rstrip('s') to match both singular/plural, strip whitespace.
    # "trade-offs" -> "trade-off" -> \btrade-offs?\b matches "trade-offs", "tradeoff", "trade-offs"
    if any(
        re.search(r'\b' + re.escape(s.strip().rstrip('s')) + r's?\b', combined)
        for s in evaluative_signals
    ):
        return "evaluative_recommendation"

    # Schema-and-evidence discipline flows:
    # Explicit signals for observability, telemetry, benchmark, parser, and aggregate
    # analysis. These go to general_diagnostic, which carries the schema-discipline
    # criteria. They won't override software_rca (which fires first on root cause or
    # high signal count), but they ensure clean observability/log diagnostics reach
    # the right profile even with low software signal count.
    schema_observability_signals = [
        "telemetry", "benchmark", "parser", "aggregat",
        "artifact", "producer", "consumer", "schema",
        "event shape", "record shape", "log directory",
        "evidence store", "emitted artifact",
    ]
    if any(_matches(s) for s in schema_observability_signals):
        return "general_diagnostic"

    return "general_diagnostic"


CRITIC_PROMPTS: dict[str, str] = {

    "software_rca": """You are a semantic quality critic for completed assistant answers about software debugging, regressions, incidents, failures, performance problems, architecture diagnosis, or root-cause analysis.

Your job is to judge whether the assistant's final answer is adequate for a software diagnostic, causal, explanatory, or evaluative query.

Rules:
- Do NOT answer the original user question.
- Do NOT rewrite the answer.
- Judge only the adequacy of the assistant answer you are given.
- Return ONLY one JSON object.
- No markdown.
- No code fences.
- No extra text.

Decision standard:
- Return {"ok": true, "reason": "..."} if the answer is adequate, or if you are unsure.
- Return {"ok": false, "reason": "..."} only if the answer is clearly inadequate, materially incomplete, misses a key alternative, gives shallow causality, or makes the main conclusion unsupported.

Judge adequacy mainly on these criteria:
- Does the answer identify a plausible mechanism or failure path, not just a label?
- Does it distinguish symptom from cause?
- Does it mention meaningful alternative causes when appropriate?
- Does it propose at least one discriminating test, log check, metric, trace, repro step, or code path to verify or falsify the diagnosis?
- Does it state the strongest justified current conclusion from the available evidence, instead of stopping at "uncertain" when a better interim conclusion is supported?
- Does it acknowledge uncertainty where evidence is genuinely insufficient, while still offering a best-effort interim conclusion and next test?
- Is the main conclusion supported by the answer body?
- Does it prematurely conclude that something is missing, impossible, or unavailable without checking obvious low-cost evidence sources already present in context (files, configs, tools, user-specific storage patterns) or without explicitly stating that those sources were not checked and therefore absence cannot be concluded?
- Does it infer runtime schema, event shape, or failure mechanism from summaries, planned design, comments, or parser output without inspecting the actual producer code and at least one real emitted artifact?
- Does it draw causal or mechanism conclusions from aggregate counts when event-level records are needed to distinguish intermediate from terminal failures?
- Does it propose parser, classifier, or report changes without verifying that the consumer/parser aligns with the producer's current schema?
- Does the answer change or ignore explicit user constraints (such as requested hook phase or event, scope, tool choice, or advisory vs blocking designation) without clearly stating the change, explaining why it is better, and asking for confirmation before treating it as accepted?
- Does the proposed fix articulate the contract it preserves and include tests for key edge cases, or does it just patch the symptom without proving broader correctness?

Strong software answers often include one or more of:
- mechanism trace,
- likely failure path,
- alternative hypotheses,
- observability checks,
- reproduction strategy,
- narrowed uncertainty,
- a clear best-effort interim conclusion,
- a concrete next diagnostic step.

Do not fail an answer for:
- not being exhaustive,
- not naming every possible cause,
- minor stylistic issues,
- brevity alone,
- omission of implementation detail that is not material.

Only return {"ok": false, ...} when the missing analysis is material.

Examples:

Example 1
User prompt: "Why did the API start returning 401s after deploy?"
Assistant response: "The deploy broke auth. Roll back."
Output: {"ok": false, "reason": "Missing failure mechanism, alternatives, and a concrete check to distinguish likely causes."}

Example 2
User prompt: "Why did the API start returning 401s after deploy?"
Assistant response: "The most likely cause is token validation drift after the deploy changed issuer or audience configuration. Alternatives include expired signing keys, clock skew, or the wrong environment secret. Check JWT claims, validator config, key rotation timing, and whether pre-deploy tokens still validate. Confidence is moderate until those checks confirm the path."
Output: {"ok": true, "reason": "Adequate."}

Example 3
User prompt: "Does this test prove auto-commit now works?"
Assistant response: "Probably not. The env var disables side effects, so the test no longer runs auto-commit at all. To verify it actually works, you'd need to run the full Stop flow with side effects enabled on a repo with uncommitted changes and inspect git status and the commit log afterwards."
Output: {"ok": true, "reason": "Adequate."}

Example 4
User prompt: "Does this test prove auto-commit now works?"
Assistant response: "Probably not. It's unverified. You'd need to test it."
Output: {"ok": false, "reason": "Missing strongest conclusion and a specific end-to-end verification step."}

Example 5
User prompt: "Add a Stop hook to enforce test coverage above 90%"
Assistant response: "I've added a PreToolUse hook that blocks commits when coverage drops below 90%."
Output: {"ok": false, "reason": "Used PreToolUse instead of the requested Stop phase without stating the change or asking for confirmation."}

Example 6
User prompt: "Add a Stop hook to enforce test coverage above 90%"
Assistant response: "You asked for a Stop hook, but PreToolUse would fire before every tool call and catch the problem earlier in the cycle — before a commit is even attempted. Stop only fires at response end. PreToolUse is cleaner for this case. Would you like to switch to PreToolUse, or keep Stop?"
Output: {"ok": true, "reason": "Adequate."}

Example 7
User prompt: "Why is the parser reporting 100 failures — is it a bug in the reader?"
Assistant response: "The parser reports 100 failures. This means the reader has bugs."
Output: {"ok": false, "reason": "Infers failure mechanism from aggregate count without inspecting actual event records, producer code, or consumer schema."}

Example 8
User prompt: "Why is the pipeline reporting all events as lost?"
Assistant response: "The event shape doesn't match the consumer's expectations. The producer emits {a, b, c} but the consumer expects {x, y, z}. The fix is to update the consumer schema."
Output: {"ok": false, "reason": "Diagnoses schema mismatch from parser output without verifying the producer's current record shape or checking a real emitted artifact."}

The reason must:
- be one short sentence,
- be plain English,
- tell the assistant what is missing or wrong,
- be under 160 characters.

If the answer is adequate, use:
{"ok": true, "reason": "Adequate."}

Required output schema:
{"ok": true, "reason": "short reason"}""",

    "general_diagnostic": """You are a semantic quality critic for completed assistant answers.

Your job is to judge whether the assistant's final answer is adequate for a diagnostic, causal, explanatory, or evaluative query.

Rules:
- Do NOT answer the original user question.
- Do NOT rewrite the answer.
- Judge only the adequacy of the assistant answer you are given.
- Return ONLY one JSON object.
- No markdown.
- No code fences.
- No extra text.

Decision standard:
Judge adequacy mainly on these criteria:
- Does the answer explain a plausible mechanism, not just a label?
- Does it mention meaningful alternative causes or interpretations when appropriate?
- Does it suggest or imply a discriminating test, observation, or falsification path when the diagnosis is uncertain?
- Does it acknowledge uncertainty when evidence is incomplete?
- Is the conclusion supported by the answer body?
- Does it prematurely conclude that something is missing, impossible, or unavailable without checking obvious low-cost evidence sources already present in context (files, configs, tools, user-specific storage patterns) or without explicitly stating that those sources were not checked and therefore absence cannot be concluded?
- Does it infer runtime schema, event shape, or failure mechanism from summaries, planned design, comments, or parser output without inspecting the actual producer code and at least one real emitted artifact?
- Does it draw causal or mechanism conclusions from aggregate counts when event-level records are needed to distinguish intermediate from terminal failures?
- Does it propose parser, classifier, or report changes without verifying that the consumer/parser aligns with the producer's current schema?
- Does the answer change or ignore explicit user constraints (such as requested hook phase or event, scope, tool choice, or advisory vs blocking designation) without clearly stating the change, explaining why it is better, and asking for confirmation before treating it as accepted?
- Does the proposed fix articulate the contract it preserves and include tests for key edge cases, or does it just patch the symptom without proving broader correctness?

Do not fail an answer for minor omissions, style, brevity alone, or not using these exact words.
Only return {"ok": false, "reason": "..."} when the missing analysis is material.

Examples:

Example 1
User prompt: "Why did the service crash after deploy?"
Assistant response: "The deploy broke it. Roll back."
Output: {"ok": false, "reason": "Missing mechanism, alternatives, and a discriminating check to support the diagnosis."}

Example 2
User prompt: "Why did the service crash after deploy?"
Assistant response: "The most likely cause is connection pool exhaustion introduced by the new config. Alternatives include an auth regression or a deadlock in startup hooks. Check pool saturation, startup logs, and whether rollback restores normal latency. I am not fully certain without those signals."
Output: {"ok": true, "reason": "Adequate."}

Example 3
User prompt: "Why are requests timing out?"
Assistant response: "Probably DNS."
Output: {"ok": false, "reason": "Too shallow; missing mechanism, alternatives, and a way to distinguish DNS from other causes."}

Example 4
User prompt: "Is there an API key for the minimax provider?"
Assistant response: "No, there is no API key available. The minimax provider cannot be used."
Output: {"ok": false, "reason": "Missing evidence check; did not search known config locations or state they were unchecked."}

Example 5
User prompt: "Is there an API key for minimax?"
Assistant response: "I have not checked the config files or credential store, so I cannot confirm whether a minimax key exists. I can check P:/.env and ~/.pi/agent/auth.json if you would like me to verify."
Output: {"ok": true, "reason": "Adequate."}

Example 6
User prompt: "Add a PreToolUse language guard to block non-English output"
Assistant response: "I've implemented a UserPromptSubmit hook that scans messages and blocks non-English content."
Output: {"ok": false, "reason": "Used UserPromptSubmit instead of the requested PreToolUse phase without stating the change or asking for confirmation."}

Example 7
User prompt: "Add a PreToolUse language guard to block non-English output"
Assistant response: "You asked for a PreToolUse hook, but UserPromptSubmit is a better insertion point for content filtering since it runs before tool processing. This avoids false positives on tool outputs. Would you prefer UserPromptSubmit, or stick with PreToolUse?"
Output: {"ok": true, "reason": "Adequate."}

Example 8
User prompt: "Why is the benchmark reporting zero events — is the emitter broken?"
Assistant response: "The benchmark shows zero events because the emitter is broken. Check the emitter code."
Output: {"ok": false, "reason": "Diagnoses broken emitter from benchmark summary without inspecting emitter code or a real event record."}

Example 9
User prompt: "Why did 50 batches fail — is it a parser bug?"
Assistant response: "50 batches failed. The parser has bugs. Fix the parser."
Output: {"ok": false, "reason": "Infers parser bug from aggregate count without examining individual batch records or verifying consumer schema."}

The reason must:
- be one short sentence,
- be plain English,
- tell the assistant what is missing or wrong,
- be under 160 characters.

Required output schema:
{"ok": true, "reason": "short reason"}""",

    "evaluative_recommendation": """You are a semantic quality critic for completed assistant answers about recommendations, comparisons, prioritization, tradeoffs, or decisions.

Your job is to judge whether the assistant's final answer is adequate for an evaluative, comparative, or recommendation-style query.

Rules:
- Do NOT answer the original user question.
- Do NOT rewrite the answer.
- Judge only the adequacy of the assistant answer you are given.
- Return ONLY one JSON object.
- No markdown.
- No code fences.
- No extra text.

Decision standard:
- Return {"ok": true, "reason": "..."} if the answer is adequate, or if you are unsure.
- Return {"ok": false, "reason": "..."} only if the answer is clearly inadequate, materially incomplete, ignores important tradeoffs, or gives a recommendation that is unsupported by the answer body.

Judge adequacy mainly on these criteria:
- Does the answer identify the main decision criteria or evaluation dimensions?
- Does it discuss meaningful tradeoffs rather than presenting only one-sided upsides?
- Does it account for constraints, context, or conditions when they matter?
- Does it make the recommendation traceable to the stated reasoning?
- Does it distinguish between a generally good option and the best option for this user's situation?
- Does it acknowledge uncertainty or conditionality when the recommendation depends on missing information?
- Does it prematurely conclude that something is missing, impossible, or unavailable without checking obvious low-cost evidence sources already present in context (files, configs, tools, user-specific storage patterns) or without explicitly stating that those sources were not checked and therefore absence cannot be concluded?
- Does the answer change or ignore explicit user constraints (such as requested hook phase or event, scope, tool choice, or advisory vs blocking designation) without clearly stating the change, explaining why it is better, and asking for confirmation before treating it as accepted?

Strong evaluative answers often include one or more of:
- explicit criteria,
- comparison dimensions,
- tradeoffs,
- conditional recommendations,
- constraint awareness,
- clear reasoning from evidence to conclusion,
- a concrete next decision step.

Do not fail an answer for:
- not being exhaustive,
- not listing every option,
- minor stylistic issues,
- brevity alone,
- leaving out low-impact criteria.

Only return {"ok": false, ...} when the missing analysis is material.

Examples:

Example 1
User prompt: "Which database should we use?"
Assistant response: "Postgres is best. Use Postgres."
Output: {"ok": false, "reason": "Missing decision criteria, tradeoffs, and context needed to justify the recommendation."}

Example 2
User prompt: "Which database should we use?"
Assistant response: "Postgres is the best default if you need transactional integrity, flexible querying, and a mature ecosystem. Alternatives like DynamoDB fit better for extreme scale with access-pattern discipline, while ClickHouse is better for analytical workloads. If your workload is mostly OLTP with moderate scale and you want low operational surprise, choose Postgres. If write scale or access patterns dominate, re-evaluate. Confidence is moderate because workload details are limited."
Output: {"ok": true, "reason": "Adequate."}

Example 3
User prompt: "Should we build this in Python or TypeScript?"
Assistant response: "TypeScript is better."
Output: {"ok": false, "reason": "Unsupported recommendation; missing criteria, tradeoffs, and fit to the actual use case."}

Example 4
User prompt: "Should we build this in Python or TypeScript?"
Assistant response: "TypeScript is stronger if the system is product-facing, browser-adjacent, or shared across frontend and backend teams, because it reduces language switching and improves end-to-end type consistency. Python is stronger if the core value is data processing, ML integration, or rapid experimentation. For an AI-heavy internal automation pipeline, Python is the better default; for a full-stack product with shared contracts, TypeScript is better. The choice depends mainly on runtime boundaries and team ownership."
Output: {"ok": true, "reason": "Adequate."}

Example 5
User prompt: "Make the secret scanner advisory (warn) not blocking"
Assistant response: "I've implemented a blocking PreToolUse gate that prevents secret commits."
Output: {"ok": false, "reason": "Used blocking enforcement instead of the requested advisory/warn mode without stating the change or asking for confirmation."}

Example 6
User prompt: "Make the secret scanner advisory (warn) not blocking"
Assistant response: "You requested advisory mode, but blocking is more effective for secrets since one leaked credential can cause real damage. If you prefer advisory over blocking, I can downgrade it to a warning that logs but does not stop the commit. Which do you prefer?"
Output: {"ok": true, "reason": "Adequate."}

The reason must:
- be one short sentence,
- be plain English,
- tell the assistant what is missing or wrong,
- be under 160 characters.

If the answer is adequate, use:
{"ok": true, "reason": "Adequate."}

Required output schema:
{"ok": true, "reason": "short reason"}""",
}

# Backwards-compatible alias — existing callers (tests, other modules) that import
# CRITIC_SYSTEM_PROMPT by name still resolve correctly.
CRITIC_SYSTEM_PROMPT: str = CRITIC_PROMPTS["general_diagnostic"]

# Profile-specific remediation templates — injected when critic returns ok=false
REMEDIATION_TEMPLATES: dict[str, str] = {
    "software_rca": (
        "State the contract before patching. Identify: (1) what must remain classified as "
        "allowed vs blocked after the fix, (2) what input conditions (trusted vs hostile/escaped) "
        "the fix must handle, (3) what would make the fix wrong. "
        "For schema/event claims: identify the producer code, inspect at least one real emitted artifact, "
        "and verify consumer/parser alignment before diagnosing mechanism or root cause. "
        "Aggregate counts are insufficient for mechanism claims — use event-level records. "
        "One passing test is not proof of correctness."
    ),
    "general_diagnostic": (
        "State the contract before concluding. Identify: (1) what classifications and invariants "
        "must still hold, (2) what conditions the fix must handle (trusted vs hostile/escaped/stale inputs), "
        "(3) what would falsify the fix. "
        "For schema/event claims: identify the producer that emits the data, inspect at least one real "
        "emitted artifact, and verify the consumer/parser schema matches before diagnosing mechanism. "
        "If producer, artifact, and consumer disagree, fix the interpretation layer before explaining behavior. "
        "A single successful run is not proof of correctness."
    ),
    "evaluative_recommendation": (
        "Make your recommendation traceable to explicit criteria, include the main tradeoffs "
        "and constraints, and state which option is best under which conditions."
    ),
}


def _build_remediation_message(critic_profile: str, critic_reason: str) -> str:
    """Build profile-specific remediation message with critic reason appended."""
    template = REMEDIATION_TEMPLATES.get(
        critic_profile,
        "Strengthen the answer with more analysis and evidence.",
    )
    return f"{template} Missing issue: {critic_reason}"


def parse_semantic_critic_response(raw_text: str) -> Optional[SemanticCriticResult]:
    """
    Parse raw LLM output into SemanticCriticResult.

    Strips fences, whitespace, then parses strict JSON schema.
    Fails open — returns None on any error without raising.
    """
    try:
        text = raw_text.strip()

        # Strip markdown code fences (```json ... ``` or ``` ...)
        if text.startswith("```"):
            lines = text.split("\n")
            # Keep lines between first (```lang) and last (```)
            if len(lines) >= 2:
                text = "\n".join(lines[1:-1])
            else:
                text = lines[-1] if lines else ""

        text = text.strip()
        if not text:
            _logger.warning(
                "semantic_critic json_parse_error: empty text after fence strip"
            )
            return None

        parsed = json.loads(text)

        # Schema validation
        if not isinstance(parsed, dict):
            _logger.warning(
                "semantic_critic schema_invalid: not a dict, type=%s",
                type(parsed).__name__,
            )
            return None
        if "ok" not in parsed or "reason" not in parsed:
            _logger.warning(
                "semantic_critic schema_invalid: missing ok/reason keys %s",
                list(parsed.keys()),
            )
            return None
        if not isinstance(parsed.get("ok"), bool):
            _logger.warning(
                "semantic_critic schema_invalid: ok is not bool %r",
                type(parsed.get("ok")).__name__,
            )
            return None
        if not isinstance(parsed.get("reason"), str):
            _logger.warning(
                "semantic_critic schema_invalid: reason is not str %r",
                type(parsed.get("reason")).__name__,
            )
            return None

        return SemanticCriticResult(ok=bool(parsed["ok"]), reason=str(parsed["reason"]))

    except json.JSONDecodeError as e:
        _logger.warning(
            "semantic_critic json_parse_error: %s | text=%r", e, raw_text[:200]
        )
        return None
    except Exception as e:
        _logger.warning("semantic_critic json_parse_error: unexpected=%s", e)
        return None


# =============================================================================
# Backend call functions — MiniMax and Mistral
# =============================================================================


def _call_minimax_critic(
    system_prompt: str,
    user_message: str,
    session_key: str,
    critic_profile: str,
) -> Optional[SemanticCriticResult]:
    """Call MiniMax API directly with the semantic critic prompt.

    Uses requests.post to the Anthropic-compatible endpoint.
    Returns None on any failure (timeout, transport, parse, schema).
    """
    api_key = _load_minimax_key()
    if not api_key:
        _logger.info("semantic_critic minimax_skip: no API key session=%s", session_key)
        return None

    correlation_id = str(uuid.uuid4())
    _logger.info(
        "semantic_critic minimax_call_start: correlation=%s session=%s profile=%s model=%s",
        correlation_id, session_key, critic_profile, SEMANTIC_CRITIC_MODEL,
    )

    try:
        resp = requests.post(
            "https://api.minimax.io/anthropic/v1/messages",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": SEMANTIC_CRITIC_MODEL,
                "max_tokens": 196608,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            },
            timeout=SEMANTIC_CRITIC_TIMEOUT_SEC,
        )

        if resp.status_code != 200:
            _logger.warning(
                "semantic_critic minimax_http_error: correlation=%s status=%d body=%s",
                correlation_id, resp.status_code, resp.text[:200],
            )
            return None

        data = resp.json()
        raw_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                raw_text += block.get("text", "")
        raw_text = raw_text.strip()

        if not raw_text:
            _logger.warning(
                "semantic_critic minimax_empty: correlation=%s", correlation_id,
            )
            return None

        _logger.info(
            "semantic_critic minimax_call_end: correlation=%s response_chars=%d",
            correlation_id, len(raw_text),
        )

        result = parse_semantic_critic_response(raw_text)
        if result is not None:
            _logger.info(
                "semantic_critic minimax_verdict: ok=%s profile=%s correlation=%s",
                result.ok, critic_profile, correlation_id,
            )
        return result

    except requests.Timeout:
        _logger.warning(
            "semantic_critic minimax_timeout: correlation=%s timeout=%ds",
            correlation_id, SEMANTIC_CRITIC_TIMEOUT_SEC,
        )
        return None
    except Exception as e:
        _logger.warning(
            "semantic_critic minimax_error: unexpected=%s session=%s", e, session_key,
        )
        return None


def _call_mistral_critic(
    system_prompt: str,
    user_message: str,
    session_key: str,
    critic_profile: str,
) -> Optional[SemanticCriticResult]:
    """Call Mistral API via mistralai SDK with the semantic critic prompt.

    Uses reasoning_effort="high" for deep analysis.
    Returns None on any failure (timeout, transport, parse, schema).
    """
    api_key = _load_mistral_key()
    if not api_key:
        _logger.info("semantic_critic mistral_skip: no API key session=%s", session_key)
        return None

    correlation_id = str(uuid.uuid4())
    _logger.info(
        "semantic_critic mistral_call_start: correlation=%s session=%s profile=%s model=%s",
        correlation_id, session_key, critic_profile, MISTRAL_MODEL,
    )

    try:
        from mistralai.client import Mistral

        client = Mistral(api_key=api_key)
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            reasoning_effort="high",
            timeout_ms=MISTRAL_TIMEOUT_SEC * 1000,
        )

        if not response or not response.choices:
            _logger.warning(
                "semantic_critic mistral_empty: correlation=%s", correlation_id,
            )
            return None

        raw_text = response.choices[0].message.content
        if raw_text:
            raw_text = raw_text.strip()

        if not raw_text:
            _logger.warning(
                "semantic_critic mistral_empty_text: correlation=%s", correlation_id,
            )
            return None

        _logger.info(
            "semantic_critic mistral_call_end: correlation=%s response_chars=%d",
            correlation_id, len(raw_text),
        )

        result = parse_semantic_critic_response(raw_text)
        if result is not None:
            _logger.info(
                "semantic_critic mistral_verdict: ok=%s profile=%s correlation=%s",
                result.ok, critic_profile, correlation_id,
            )
        return result

    except Exception as e:
        _logger.warning(
            "semantic_critic mistral_error: unexpected=%s session=%s", e, session_key,
        )
        return None


# =============================================================================
# Parallel orchestration — MiniMax + Mistral with conservative combination
# =============================================================================


def call_semantic_critic_via_bifrost(
    original_user_prompt: str, assistant_response: str, session_key: str
) -> Optional[SemanticCriticResult]:
    """
    Call both MiniMax and Mistral in parallel with conservative combination.

    Combination logic:
    - Both ok=true -> ok=true
    - Any ok=false -> ok=false (conservative)
    - One None -> use the other
    - Both None -> None (fail-open)

    Returns None on any complete failure (both backends failed).
    Logs structured events for observability.
    """
    user_message = _build_critic_user_message(original_user_prompt, assistant_response)
    response_len = len(assistant_response)
    critic_profile = _detect_critic_profile(original_user_prompt, assistant_response)
    system_prompt = CRITIC_PROMPTS[critic_profile]

    # Log routing decision with signal count for empirical threshold tuning
    combined = (original_user_prompt + " " + assistant_response).lower()
    tokens = set(re.findall(r'\b\w+\b', combined))

    def _matches(signal: str) -> bool:
        if ' ' in signal:
            return all(word in tokens for word in signal.split())
        return (
            re.search(r'\b' + re.escape(signal) + r'\b', combined) is not None
            or any(signal in token for token in tokens)
        )

    software_signals = [
        "bug", "crash", "timeout", "latency", "regression", "deploy",
        "api", "service", "logs", "trace", "stack",
        "incident", "deadlock", "thread", "query",
        "database", "config", "exception",
        "502", "503", "504", "401", "403", "500", "connection refused",
        "out of memory", "oom", "heap", "cpu", "disk", "network",
        "docker", "kubernetes", "k8s", "yaml", "auth",
        "nullpointer", "null reference",
    ]
    signal_count = sum(1 for s in software_signals if _matches(s))
    _logger.info(
        "semantic_critic routing: profile=%s signal_count=%d session=%s",
        critic_profile,
        signal_count,
        session_key,
    )

    _logger.info(
        "semantic_critic parallel_call_start: session=%s profile=%s response_chars=%d "
        "minimax_model=%s mistral_model=%s",
        session_key,
        critic_profile,
        response_len,
        SEMANTIC_CRITIC_MODEL,
        MISTRAL_MODEL,
    )

    # Call both backends in parallel
    overall_timeout = max(MISTRAL_TIMEOUT_SEC, SEMANTIC_CRITIC_TIMEOUT_SEC) + 2

    minimax_result: Optional[SemanticCriticResult] = None
    mistral_result: Optional[SemanticCriticResult] = None

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(
                    _call_minimax_critic, system_prompt, user_message, session_key, critic_profile
                ): "minimax",
                executor.submit(
                    _call_mistral_critic, system_prompt, user_message, session_key, critic_profile
                ): "mistral",
            }

            for future in as_completed(futures, timeout=overall_timeout):
                backend = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    _logger.warning(
                        "semantic_critic %s_exception: %s session=%s",
                        backend, e, session_key,
                    )
                    result = None

                if backend == "minimax":
                    minimax_result = result
                else:
                    mistral_result = result

    except Exception as e:
        _logger.warning(
            "semantic_critic parallel_executor_error: %s session=%s", e, session_key,
        )

    # Conservative combination logic
    # Both None -> fail-open
    if minimax_result is None and mistral_result is None:
        _logger.info(
            "semantic_critic both_backends_failed: session=%s profile=%s",
            session_key, critic_profile,
        )
        return None

    # One None -> use the other
    if minimax_result is None:
        _logger.info(
            "semantic_critic fallback_mistral: session=%s ok=%s",
            session_key, mistral_result.ok,
        )
        return mistral_result
    if mistral_result is None:
        _logger.info(
            "semantic_critic fallback_minimax: session=%s ok=%s",
            session_key, minimax_result.ok,
        )
        return minimax_result

    # Both returned results — conservative: any ok=false wins
    if not minimax_result.ok or not mistral_result.ok:
        # Return whichever flagged the issue; prefer the false one
        combined_result = SemanticCriticResult(
            ok=False,
            reason=minimax_result.reason if not minimax_result.ok else mistral_result.reason,
        )
        _logger.info(
            "semantic_critic conservative_veto: minimax_ok=%s mistral_ok=%s session=%s profile=%s",
            minimax_result.ok, mistral_result.ok, session_key, critic_profile,
        )
        return combined_result

    # Both ok=true
    _logger.info(
        "semantic_critic consensus_ok: session=%s profile=%s",
        session_key, critic_profile,
    )
    return minimax_result


def _is_diagnostic_scope(prompt_text: str, response_text: str) -> bool:
    """Detect diagnostic/analytic scope: diagnostic keywords + response > 50 words."""
    if not response_text or len(response_text.split()) <= 50:
        return False

    combined = (prompt_text + " " + response_text).lower()

    diagnostic_keywords = [
        "diagnosis",
        "diagnostic",
        "root cause",
        "why did",
        "hypothesis",
        "mechanism",
        "trade-off",
        "compare options",
        "investigation",
        "debug",
        "troubleshoot",
        "分析",
        "causal",
        "because of",
        "resulted in",
        "led to",
        "cause",
        "reason",
        "explanation",
        "why is",
        "why was",
    ]

    keyword_count = sum(1 for kw in diagnostic_keywords if kw in combined)
    return keyword_count >= 1


def _is_non_substantive(text: str) -> bool:
    """Check if response is non-substantive (greetings, acknowledgments, etc.)."""
    try:
        from __lib.shared_helpers import is_non_substantive_turn

        return is_non_substantive_turn(text)
    except ImportError:
        # Fallback if import fails
        if not text:
            return True
        words = text.split()
        if len(words) >= 20:
            return False
        if any(c.isdigit() for c in text):
            return False
        text_lower = text.lower()
        blockers = ["because", "i found", "tests passed", "should", "option"]
        for b in blockers:
            if b in text_lower:
                return False
        phatic = [
            r"^\s*(hi|hello|hey|greetings)",
            r"\b(got it|understood|okay|ok|alright)",
            r"\b(ready when you are|ready to proceed)\b",
        ]
        for pattern in phatic:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


def run(data: dict) -> dict | None:
    """
    Evaluate diagnostic/analytical responses for semantic adequacy.

    Returns: None (allow) or dict with systemMessage for Stop aggregation.
    """
    global _stop_hook_active, _INVOCATION_COUNTS

    # --- Early exits ---

    if _stop_hook_active:
        return None

    session_key = _session_key(data)

    # Get prompt and response
    user_prompt = ""
    response_text = ""

    if "transcript" in data:
        transcript = data["transcript"]
        if isinstance(transcript, list):
            for msg in reversed(transcript):
                role = msg.get("role", "")
                content = msg.get("content", "")
                if isinstance(content, str):
                    if role == "user" and not user_prompt:
                        user_prompt = content
                    elif role == "assistant" and not response_text:
                        response_text = content

    if not user_prompt:
        user_prompt = data.get("user_prompt", data.get("prompt", ""))
    if not response_text:
        response_text = data.get("response", data.get("raw_response", ""))

    # Empty response
    if not response_text or not response_text.strip():
        return None

    # Non-substantive turn
    if _is_non_substantive(response_text):
        return None

    # Veridical integrity gate (epistemic sycophancy detection)
    try:
        from _veridical_gate import check_veridical_integrity
        transcript_str = data.get('transcript', '')
        if isinstance(transcript_str, list):
            parts = []
            for msg in transcript_str:
                role = msg.get('role', '')
                content_val = msg.get('content', '')
                if isinstance(content_val, str) and content_val.strip():
                    parts.append(f'[{role}] {content_val}')
            transcript_str = chr(10) + chr(10).join(parts)
        veridical_result = check_veridical_integrity(
            response_text=response_text,
            transcript=transcript_str,
            session_key=session_key,
            mistral_api_key=_load_mistral_key() or '',
        )
        if veridical_result is not None:
            return veridical_result
    except Exception as exc:
        _logger.warning('veridical_gate integration error, failing open: %s', exc)

    # Diagnostic scope gate
    if not _is_diagnostic_scope(user_prompt, response_text):
        return None

    # --- Per-session cap ---
    current_count = _INVOCATION_COUNTS.get(session_key, 0)
    if current_count >= SEMANTIC_CRITIC_CAP:
        _logger.info(
            "semantic_critic cap_reached: session=%s count=%d cap=%d",
            session_key,
            current_count,
            SEMANTIC_CRITIC_CAP,
        )
        return None

    # --- Call the critic ---
    _INVOCATION_COUNTS[session_key] = current_count + 1

    critic_result = call_semantic_critic_via_bifrost(
        original_user_prompt=user_prompt,
        assistant_response=response_text,
        session_key=session_key,
    )

    # No judgment available — fail open, allow
    if critic_result is None:
        return None

    # Judgment available
    if critic_result.ok:
        return None

    # Veto — inject profile-specific advisory directive
    critic_profile = _detect_critic_profile(user_prompt, response_text)
    instruction = _build_remediation_message(critic_profile, critic_result.reason)
    return {"allow": True, "systemMessage": f"Semantic critic: {instruction}"}


if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    result = run(data)
    if result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(0)
    else:
        sys.exit(0)
