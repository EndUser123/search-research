"""Narrow, read-only Brave Search lane for the Phase 1 evaluation.

This is intentionally not a provider registry or fallback layer.  It uses one
bounded Brave Web Search request and keeps authentication state in memory only.
The request/response shape follows the inspected canonical Brave client under
the search-research plugin, but avoids importing that plugin's broad package
graph (which currently requires an unrelated optional dependency).
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .phase1 import LaneExecution, NormalizedResult, _iso
from .router import CapabilityRecord, TaskSignals, recommend


BRAVE_LANE = "brave"
BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
DEFAULT_VALIDITY_SECONDS = 300
BraveRequester = Callable[[str, dict[str, str], int], tuple[int, bytes]]
_UNSET_API_KEY = object()


@dataclass(frozen=True)
class BraveObservation:
    provider: str
    observed_at: str
    valid_until: str
    authentication_state: str
    readiness: str
    observation_method: str
    api_endpoint: str = BRAVE_API_URL
    quota: dict[str, Any] | None = None
    errors: tuple[str, ...] = ()
    scope: str = "process-environment-api-key"

    @property
    def ready(self) -> bool:
        return self.readiness == "ready"

    def to_capability(self) -> CapabilityRecord:
        return CapabilityRecord(
            lane=BRAVE_LANE,
            role="SEARCH_DISCOVERY",
            independence_group="external_search",
            capabilities=frozenset({"external_discovery", "current_web", "independent_recall", "implementation_discovery", "repository_discovery", "maintenance_discovery", "compatibility_discovery", "authority_candidate_discovery", "omission_sensitive_discovery"}),
            ready=self.ready,
            authenticated=self.authentication_state == "configured",
            automatic=True,
            authority="advisory",
            readiness_observed_at=self.observed_at,
            readiness_valid_until=self.valid_until,
            observation_method=self.observation_method,
            recent_anomaly=bool(self.errors),
            supported_roles=frozenset({
                "IMPLEMENTATION_DISCOVERY", "AUTHORITATIVE_SOURCE_DISCOVERY",
                "REPOSITORY_PROJECT_DISCOVERY", "MAINTENANCE_STATUS",
                "COMPATIBILITY_RESEARCH", "OMISSION_SENSITIVE_DISCOVERY",
            }),
        )


def observe_brave(*, api_key: str | None | object = _UNSET_API_KEY, validity_seconds: int = DEFAULT_VALIDITY_SECONDS, now: datetime | None = None) -> BraveObservation:
    observed = now or datetime.now(timezone.utc)
    valid_until = observed + timedelta(seconds=validity_seconds)
    configured = bool(os.environ.get("BRAVE_API_KEY")) if api_key is _UNSET_API_KEY else bool(api_key)
    if not configured:
        return BraveObservation(BRAVE_LANE, _iso(observed), _iso(valid_until), "unknown", "unavailable", "brave-env-presence-v1", errors=("authentication_not_configured",))
    return BraveObservation(BRAVE_LANE, _iso(observed), _iso(valid_until), "configured", "ready", "brave-env-presence-v1")


def _request(url: str, headers: dict[str, str], timeout_seconds: int) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.status, response.read(2_000_000)


def normalize_brave_results(query: str, payload: dict[str, Any], retrieved_at: str | None = None) -> tuple[NormalizedResult, ...]:
    retrieved = retrieved_at or _iso()
    rows = payload.get("web", {}).get("results", []) if isinstance(payload.get("web"), dict) else []
    if not isinstance(rows, list):
        raise ValueError("brave_result_shape_missing_web_results")
    results: list[NormalizedResult] = []
    seen: set[str] = set()
    for index, item in enumerate(rows):
        if not isinstance(item, dict) or not isinstance(item.get("url"), str) or not item["url"].strip():
            continue
        url = item["url"].strip()
        identity = url.rstrip("/").lower()
        if identity in seen:
            continue
        seen.add(identity)
        results.append(NormalizedResult(
            provider=BRAVE_LANE,
            lane_role="independent_external_discovery",
            query=query,
            result_id=f"brave-{index}-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16]}",
            title=str(item.get("title") or "Untitled"),
            url_or_source_ref=url,
            snippet=str(item.get("description") or item.get("snippet") or ""),
            published_at=str(item["age"]) if item.get("age") else None,
            retrieved_at=retrieved,
            source_identity=identity,
            provider_provenance={"api": BRAVE_API_URL, "result_index": index, "response_field": "web.results"},
        ))
    return tuple(results)


def execute_brave_search(
    query: str,
    observation: BraveObservation,
    *,
    timeout_seconds: int = 15,
    max_results: int = 5,
    api_key: str | None = None,
    requester: BraveRequester = _request,
    role: str = "IMPLEMENTATION_DISCOVERY",
) -> LaneExecution:
    """Perform exactly one Brave request; never retry or fall back."""
    started = _iso()
    signals = TaskSignals(
        needs_current_web=True,
        needs_independent_recall=True,
        explicit_lane=BRAVE_LANE,
        agent_selected=True,
        requested_roles=frozenset({role}),
        as_of=observation.observed_at,
    )
    decision = recommend(signals, (observation.to_capability(),))
    if not decision.recommendations:
        reasons = list(decision.rejected[0].reasons) if decision.rejected else [decision.stop_reason]
        return LaneExecution(BRAVE_LANE, BRAVE_LANE, "independent_external_discovery", query, "not_attempted", started, _iso(), failures=({"outcome": "router_rejected", "reasons": reasons},))
    if not observation.ready:
        return LaneExecution(BRAVE_LANE, BRAVE_LANE, "independent_external_discovery", query, "not_attempted", started, _iso(), failures=({"outcome": "provider_not_ready", "reasons": list(observation.errors)},))
    key = api_key or os.environ.get("BRAVE_API_KEY")
    if not key:
        return LaneExecution(BRAVE_LANE, BRAVE_LANE, "independent_external_discovery", query, "failed", started, _iso(), failures=({"outcome": "authentication_not_configured"},))
    params = urllib.parse.urlencode({"q": query, "count": max(1, min(max_results, 20))})
    try:
        status, body = requester(f"{BRAVE_API_URL}?{params}", {"Accept": "application/json", "X-Subscription-Token": key}, timeout_seconds)
        if status < 200 or status >= 400:
            return LaneExecution(BRAVE_LANE, BRAVE_LANE, "independent_external_discovery", query, "failed", started, _iso(), failures=({"outcome": f"http_status:{status}"},))
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("brave_result_shape_not_object")
        results = normalize_brave_results(query, payload)
    except TimeoutError:
        return LaneExecution(BRAVE_LANE, BRAVE_LANE, "independent_external_discovery", query, "failed", started, _iso(), failures=({"outcome": "timeout"},))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        return LaneExecution(BRAVE_LANE, BRAVE_LANE, "independent_external_discovery", query, "failed", started, _iso(), failures=({"outcome": f"{type(exc).__name__}:{str(exc)[:160]}"},))
    return LaneExecution(BRAVE_LANE, BRAVE_LANE, "independent_external_discovery", query, "success" if results else "empty", started, _iso(), results=results)
