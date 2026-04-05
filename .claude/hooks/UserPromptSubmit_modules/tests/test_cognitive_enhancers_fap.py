"""Tests for analysis_protocol_gate FAP detection and injection."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit_modules.analysis_protocol_gate import (
    _CORRECTION_PATTERN,
    _FAP_INJECTION,
    _META_PRINCIPLE_PATTERN,
    _RCA_PATTERN,
    _concept_cluster_match,
    _should_inject_fap,
    analysis_protocol_gate,
)
from UserPromptSubmit_modules.base import HookContext


def _make_context(prompt: str) -> HookContext:
    return HookContext(prompt=prompt, data={})


class TestLayer1Regex:
    def test_rca_pattern_fires(self) -> None:
        assert _RCA_PATTERN.search("What is the root cause of this bug?")
        assert _should_inject_fap("What is the root cause of this bug?") is True

    def test_meta_pattern_fires(self) -> None:
        assert _META_PRINCIPLE_PATTERN.search("This is the wrong abstraction for this problem.")
        assert _should_inject_fap("This is the wrong abstraction for this problem.") is True

    def test_correction_pattern_fires(self) -> None:
        assert _CORRECTION_PATTERN.search("You are still patching the wrong layer.")
        assert _should_inject_fap("You are still patching the wrong layer.") is True

    def test_normal_prompt_does_not_fire(self) -> None:
        assert _should_inject_fap("Please implement a retry mechanism for the API calls.") is False

    def test_short_prompt_does_not_fire(self) -> None:
        assert _should_inject_fap("Fix bug") is False


class TestLayer2ConceptClusters:
    def test_wrong_abstraction_cluster_matches_paraphrase(self) -> None:
        prompt = "We are tackling the surface symptom instead of the underlying layer."
        assert _concept_cluster_match(prompt) is True
        assert _should_inject_fap(prompt) is True

    def test_missing_principle_cluster_matches_generalization_prompt(self) -> None:
        prompt = "This fix ignores the broader pattern and misses the recurring class of failures."
        assert _concept_cluster_match(prompt) is True
        assert _should_inject_fap(prompt) is True

    def test_fix_inadequacy_requires_higher_overlap(self) -> None:
        prompt = "This patch is weak."
        assert _concept_cluster_match(prompt) is False
        assert _should_inject_fap(prompt) is False

    def test_semantic_toggle_disables_concept_layer(self) -> None:
        prompt = "This patch misses the recurring class of failures."
        with patch(
            "UserPromptSubmit_modules.analysis_protocol_gate._load_config",
            return_value={
                "enabled": True,
                "analysis_protocol_gate": True,
                "fap_semantic_enabled": False,
                "min_prompt_length": 30,
                "enhance_skills": True,
                "skip_skills": [],
            },
        ):
            assert _should_inject_fap(prompt) is False


class TestAnalysisProtocolGateHook:
    def test_fires_on_rca_prompt(self) -> None:
        result = analysis_protocol_gate(_make_context("Do a root cause analysis on this hook failure."))
        assert result.context == _FAP_INJECTION
        assert result.tokens > 0

    def test_no_fire_on_normal_prompt(self) -> None:
        result = analysis_protocol_gate(_make_context("Please add a retry loop to the API call handler."))
        assert not result.context

    def test_disabled_via_gate_flag(self) -> None:
        with patch(
            "UserPromptSubmit_modules.analysis_protocol_gate._load_config",
            return_value={
                "enabled": True,
                "analysis_protocol_gate": False,
                "min_prompt_length": 30,
                "enhance_skills": True,
                "skip_skills": [],
            },
        ):
            result = analysis_protocol_gate(_make_context("Do a root cause analysis on this failure."))
            assert not result.context

    def test_disabled_via_global_enabled_flag(self) -> None:
        with patch(
            "UserPromptSubmit_modules.analysis_protocol_gate._load_config",
            return_value={
                "enabled": False,
                "analysis_protocol_gate": True,
                "min_prompt_length": 30,
                "enhance_skills": True,
                "skip_skills": [],
            },
        ):
            result = analysis_protocol_gate(_make_context("Do a root cause analysis on this failure."))
            assert not result.context

    def test_injection_references_protocol_doc(self) -> None:
        assert "P:/docs/failure-analysis-protocol.md" in _FAP_INJECTION

    def test_priority_is_current_value(self) -> None:
        result = analysis_protocol_gate(_make_context("Do a root cause analysis on this failure and document it."))
        assert result.priority == 11.8
