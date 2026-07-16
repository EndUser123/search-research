"""Bounded adapters for the canonical search-research Exa and DDG backends.

This module is intentionally a lane adapter, not a provider registry or
fallback broker.  It imports the already-owned provider implementations only
when a lane is explicitly selected, normalizes their documented result shape
into the Phase 1 contract, and preserves readiness, timeout, and failure
telemetry.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .phase1 import LaneExecution, NormalizedResult, _iso
from .router import CapabilityRecord, TaskSignals, recommend

EXA = "exa"
DDG = "duckduckgo"
SUPPORTED = frozenset({EXA, DDG})
DEFAULT_VALIDITY_SECONDS = 300


@dataclass(frozen=True)
class ExternalObservation:
    provider: str
    observed_at: str
    valid_until: str
    readiness: str
    authentication_state: str
    observation_method: str
    errors: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.readiness == "ready"

    def to_capability(self) -> CapabilityRecord:
        if self.provider == EXA:
            capabilities = frozenset({
                "external_discovery", "current_web", "semantic_external_discovery",
                "conceptual_discovery",
            })
            roles = frozenset({"SEMANTIC_EXTERNAL_DISCOVERY", "CONCEPTUAL_RECALL", "EXPLORATORY_RESEARCH"})
        else:
            capabilities = frozenset({
                "external_discovery", "current_web", "independent_index_discovery",
                "independent_recall", "broad_discovery",
            })
            roles = frozenset({"BROAD_EXTERNAL_DISCOVERY", "GENERAL_WEB_RESEARCH"})
        return CapabilityRecord(
            lane=self.provider,
            role="SEARCH_DISCOVERY",
            independence_group=self.provider,
            capabilities=capabilities,
            circuit="CLOSED" if self.provider == EXA else "RESTRICTED",
            ready=self.ready,
            authenticated=self.authentication_state in {"configured", "not_required"},
            automatic=self.provider == EXA,
            authority="advisory",
            readiness_observed_at=self.observed_at,
            readiness_valid_until=self.valid_until,
            observation_method=self.observation_method,
            recent_anomaly=bool(self.errors),
            supported_roles=roles,
        )


def _load_workspace_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(Path("P:/.env"), override=False)
    except Exception:
        return


def _backend(provider: str, factory: Callable[[str], Any] | None = None) -> Any:
    if factory:
        return factory(provider)
    _load_workspace_env()
    root = Path("P:/packages/.claude-marketplace/plugins/search-research")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if provider == EXA:
        from core.providers.exa import ExaBackend
        return ExaBackend(max_results=5)
    if provider == DDG:
        from core.providers.ddgs_backend import DDGsBackend
        return DDGsBackend(max_results=5)
    raise ValueError(f"unsupported_external_provider:{provider}")


def observe_external(provider: str, *, factory: Callable[[str], Any] | None = None, now: datetime | None = None) -> ExternalObservation:
    if provider not in SUPPORTED:
        raise ValueError(f"unsupported_external_provider:{provider}")
    observed = now or datetime.now(timezone.utc)
    valid_until = observed + timedelta(seconds=DEFAULT_VALIDITY_SECONDS)
    try:
        backend = _backend(provider, factory)
        available = bool(backend.is_available())
    except Exception as exc:
        return ExternalObservation(provider, _iso(observed), _iso(valid_until), "unavailable", "unknown", "canonical-plugin-provider-v1", (f"observation_error:{type(exc).__name__}",))
    if not available:
        auth = "not_required" if provider == DDG else "unknown"
        return ExternalObservation(provider, _iso(observed), _iso(valid_until), "unavailable", auth, "canonical-plugin-provider-v1", ("provider_not_available",))
    return ExternalObservation(provider, _iso(observed), _iso(valid_until), "ready", "configured" if provider == EXA else "not_required", "canonical-plugin-provider-v1")


def _normalize(provider: str, query: str, rows: list[dict[str, Any]], retrieved_at: str) -> tuple[NormalizedResult, ...]:
    results: list[NormalizedResult] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        url = str(row.get("url") or row.get("href") or "").strip()
        if not url:
            continue
        identity = url.rstrip("/").lower()
        if identity in seen:
            continue
        seen.add(identity)
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        results.append(NormalizedResult(
            provider=provider,
            lane_role="semantic_external_discovery" if provider == EXA else "independent_index_discovery",
            query=query,
            result_id=f"{provider}-{index}-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16]}",
            title=str(row.get("title") or "Untitled"),
            url_or_source_ref=url,
            snippet=str(row.get("content") or row.get("snippet") or ""),
            published_at=str(metadata["published_date"]) if metadata.get("published_date") else None,
            retrieved_at=retrieved_at,
            source_identity=identity,
            provider_provenance={"backend": "search-research.core.providers", "provider": provider, "result_index": index},
        ))
    return tuple(results)


def execute_external_search(
    query: str,
    observation: ExternalObservation,
    *,
    timeout_seconds: int = 15,
    factory: Callable[[str], Any] | None = None,
) -> LaneExecution:
    """Perform one explicitly selected Exa or DDG request; never fall back."""
    started = _iso()
    signals = TaskSignals(
        needs_current_web=True,
        # Exa is semantic discovery, not the independent-index lane. DDG is
        # the lane that explicitly satisfies independent recall.
        needs_independent_recall=observation.provider == DDG,
        explicit_lane=observation.provider,
        agent_selected=True,
        requested_roles=frozenset({"CONCEPTUAL_RECALL" if observation.provider == EXA else "BROAD_EXTERNAL_DISCOVERY"}),
        as_of=observation.observed_at,
    )
    decision = recommend(signals, (observation.to_capability(),))
    if not decision.recommendations:
        reasons = list(decision.rejected[0].reasons) if decision.rejected else [decision.stop_reason]
        return LaneExecution(observation.provider, observation.provider, "external_discovery", query, "not_attempted", started, _iso(), failures=({"outcome": "router_rejected", "reasons": reasons},))
    if not observation.ready:
        return LaneExecution(observation.provider, observation.provider, "external_discovery", query, "not_attempted", started, _iso(), failures=({"outcome": "provider_not_ready", "reasons": list(observation.errors)},))
    try:
        backend = _backend(observation.provider, factory)
        rows = asyncio.run(asyncio.wait_for(backend.search(query, max_results=5, timeout=timeout_seconds), timeout=timeout_seconds + 2))
        results = _normalize(observation.provider, query, rows if isinstance(rows, list) else [], _iso())
    except asyncio.TimeoutError:
        return LaneExecution(observation.provider, observation.provider, "external_discovery", query, "failed", started, _iso(), failures=({"outcome": "timeout"},))
    except Exception as exc:
        return LaneExecution(observation.provider, observation.provider, "external_discovery", query, "failed", started, _iso(), failures=({"outcome": f"{type(exc).__name__}:{str(exc)[:160]}"},))
    return LaneExecution(observation.provider, observation.provider, "external_discovery", query, "success" if results else "empty", started, _iso(), results=results)
