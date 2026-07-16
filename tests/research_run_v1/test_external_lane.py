from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[2]))

from research_runtime.external_lane import execute_external_search, observe_external


class _Backend:
    def __init__(self, provider: str):
        self.provider = provider

    def is_available(self):
        return True

    async def search(self, query, max_results=5, timeout=15):
        return [{"title": f"{self.provider} result", "url": "https://example.com/source", "content": "useful evidence", "metadata": {"source": self.provider}}]


def _factory(provider):
    return _Backend(provider)


def test_external_observation_maps_restricted_capability():
    observation = observe_external("exa", factory=_factory)
    capability = observation.to_capability()
    assert observation.ready is True
    assert capability.automatic is True
    assert capability.circuit == "CLOSED"
    assert "semantic_external_discovery" in capability.capabilities


def test_external_lane_normalizes_and_preserves_provider_identity():
    observation = observe_external("duckduckgo", factory=_factory)
    lane = execute_external_search("independent index check", observation, factory=_factory)
    assert lane.status == "success"
    assert lane.provider == "duckduckgo"
    assert lane.results[0].provider_provenance["provider"] == "duckduckgo"
    assert lane.results[0].source_identity == "https://example.com/source"


def test_external_provider_failure_remains_visible():
    observation = observe_external("exa", factory=lambda _: SimpleNamespace(is_available=lambda: False))
    lane = execute_external_search("semantic check", observation, factory=_factory)
    assert lane.status == "not_attempted"
    assert lane.failures[0]["outcome"] == "router_rejected"


def test_explicit_lane_does_not_broaden_to_another_provider():
    from research_runtime.router import CapabilityRecord, TaskSignals, recommend

    exa = observe_external("exa", factory=_factory).to_capability()
    brave = CapabilityRecord(
        "brave", "SEARCH_DISCOVERY", "brave",
        frozenset({"external_discovery", "current_web", "independent_recall", "repository_discovery"}),
        ready=True, authenticated=True, automatic=True, observation_method="test",
        supported_roles=frozenset({"REPOSITORY_PROJECT_DISCOVERY"}),
    )
    decision = recommend(TaskSignals(needs_current_web=True, needs_independent_recall=True, explicit_lane="exa", agent_selected=True, requested_roles=frozenset({"REPOSITORY_PROJECT_DISCOVERY"})), (exa, brave))
    assert not decision.recommendations
    assert decision.stop_reason == "no_eligible_lane"


def test_ddg_is_conditional_only_when_an_evidence_gap_is_recorded():
    from research_runtime.router import TaskSignals, recommend

    ddg = observe_external("duckduckgo", factory=_factory).to_capability()
    normal = recommend(TaskSignals(needs_current_web=True, needs_independent_recall=True), (ddg,))
    conditional = recommend(TaskSignals(needs_current_web=True, needs_independent_recall=True, conditional_lane_trigger="omission_risk"), (ddg,))
    assert not normal.recommendations
    assert [item.lane for item in conditional.recommendations] == ["duckduckgo"]
    assert conditional.recommendations[0].selection_mode == "conditional"
