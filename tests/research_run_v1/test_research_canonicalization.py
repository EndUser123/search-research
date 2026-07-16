from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
PLUGIN = ROOT / "packages/.claude-marketplace/plugins/search-research"
sys.path.insert(0, str(PLUGIN))


def test_research_is_canonical_and_all_is_compatibility_only() -> None:
    research_skill = (PLUGIN / "skills/research/SKILL.md").read_text(encoding="utf-8")
    all_skill = (PLUGIN / "skills/all/SKILL.md").read_text(encoding="utf-8")
    assert "Canonical research workflow" in research_skill
    assert "compatibility wrapper" in all_skill.lower()
    assert "owns provider selection" not in all_skill.lower()
    all_python = "\n".join(path.read_text(encoding="utf-8") for path in (PLUGIN / "skills/all").glob("*.py"))
    assert "from research_runtime" not in all_python


def test_all_orchestration_delegates_with_compatibility_caller() -> None:
    import skills.all.orchestration as compatibility

    seen: dict[str, object] = {}

    async def fake(query: str, **kwargs: object) -> str:
        seen["query"] = query
        seen.update(kwargs)
        return "ok"

    original = compatibility._execute_unified_search
    compatibility._execute_unified_search = fake
    try:
        assert asyncio.run(compatibility.execute_unified_search("q")) == "ok"
    finally:
        compatibility._execute_unified_search = original
    assert seen == {"query": "q", "caller": "search-research:/all"}


def test_canonical_research_executor_has_distinct_caller_default() -> None:
    source = (PLUGIN / "skills/research/search_executor.py").read_text(encoding="utf-8")
    assert "execute_phase1_for_research" in source
    assert 'caller: str = "search-research:/research"' in source
    assert 'caller="search-research:/all"' in source


def test_research_signal_contract_keeps_complementary_provider_explicit_only() -> None:
    from skills.research import search_executor

    signals = search_executor._phase1_task_signals("semantic repository comparison", "auto", "exa")
    assert signals.explicit_lane == "exa"
    assert signals.agent_selected is True
    assert signals.needs_independent_recall is False
    assert "BROAD_EXTERNAL_DISCOVERY" not in signals.requested_roles
    assert search_executor._phase1_task_signals("semantic repository comparison", "auto").explicit_lane is None
