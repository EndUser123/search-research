from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from research_runtime.brave_lane import execute_brave_search, normalize_brave_results, observe_brave


NOW = "2026-07-13T13:00:00Z"


def test_brave_observation_has_no_secret_material_and_unconfigured_is_unready() -> None:
    observation = observe_brave(api_key=None, now=datetime(2026, 7, 13, 13, 0, tzinfo=timezone.utc))
    assert observation.readiness == "unavailable"
    assert "api_key" not in json.dumps(observation.__dict__).lower()


def test_brave_not_ready_is_not_invoked() -> None:
    calls: list[str] = []
    observation = observe_brave(api_key=None, now=datetime(2026, 7, 13, 13, 0, tzinfo=timezone.utc))
    result = execute_brave_search("q", observation, requester=lambda url, headers, timeout: calls.append(url))
    assert result.status == "not_attempted"
    assert not calls


def test_brave_normalizes_results_and_retains_provider_provenance() -> None:
    results = normalize_brave_results("q", {"web": {"results": [
        {"title": "A", "url": "https://github.com/openai/example/", "description": "implementation"},
        {"title": "duplicate", "url": "https://github.com/openai/example", "description": "other"},
    ]}}, retrieved_at=NOW)
    assert len(results) == 1
    assert results[0].provider == "brave"
    assert results[0].provider_provenance["response_field"] == "web.results"


def test_brave_one_bounded_request_and_parse_failure_is_visible() -> None:
    calls: list[tuple[str, int]] = []
    observation = observe_brave(api_key="test-key", now=datetime(2026, 7, 13, 13, 0, tzinfo=timezone.utc))

    def requester(url, headers, timeout):
        calls.append((url, timeout))
        return 200, b"not-json"

    result = execute_brave_search("q", observation, api_key="test-key", timeout_seconds=7, requester=requester)
    assert result.status == "failed"
    assert len(calls) == 1
    assert calls[0][1] == 7
    assert "JSONDecodeError" in result.failures[0]["outcome"]
