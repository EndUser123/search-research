"""Tests for intent_distribution_eval runner.

Proves:
- evaluate() classifies every corpus case and matches its expected_intent (0 surprises).
- UNKNOWN share is computed correctly.
- The CLI exits 0 when within baseline, 1 when UNKNOWN drifts >10pp.
- --update-baseline writes a valid baseline file.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.chs.eval import intent_distribution_eval as ide


def _shipped_cases() -> list[dict]:
    return ide.load_cases(ide.DEFAULT_CASES)


class TestEvaluate:
    def test_shipped_corpus_classifies_as_expected(self) -> None:
        """Every shipped case must classify as its expected_intent.

        This is the corpus-correctness gate (MUST-RE-VERIFY #4): if a code
        query lands UNKNOWN, that is a finding — but it must be the INTENDED
        finding (c-intent-006), not a surprise.
        """
        report = ide.evaluate(_shipped_cases())
        assert report["total"] == 15
        assert report["surprises"] == [], (
            f"corpus drifted from expected intents: {report['surprises']}"
        )

    def test_corpus_has_required_class_coverage(self) -> None:
        cases = _shipped_cases()
        by_class = {}
        for c in cases:
            by_class[c["query_class"]] = by_class.get(c["query_class"], 0) + 1
        assert by_class.get("code", 0) >= 5
        assert by_class.get("concept", 0) >= 5
        assert by_class.get("exploratory", 0) >= 5

    def test_unknown_share_computation(self) -> None:
        report = ide.evaluate([
            {"id": "a", "query": "def foo", "query_class": "code",
             "expected_intent": "technical", "expected_backends": []},
            {"id": "b", "query": "zzz unknown gibberish word salad",
             "query_class": "concept", "expected_intent": "unknown",
             "expected_backends": []},
        ])
        # 1 of 2 → 0.5
        assert report["unknown"] == 1
        assert report["unknown_share"] == 0.5

    def test_shipped_unknown_share_is_low(self) -> None:
        """FM-3 number: on the expanded corpus UNKNOWN is far below the
        92% CHS-monoculture figure."""
        report = ide.evaluate(_shipped_cases())
        assert report["unknown_share"] < 0.20, (
            f"UNKNOWN share unexpectedly high: {report['unknown_share']}"
        )


class TestBaselineGate:
    def test_gate_passes_within_baseline(self, tmp_path: Path) -> None:
        baseline = tmp_path / "baseline.json"
        ide.write_baseline(0.0667, 15, baseline)
        rc = ide.main(["--baseline", str(baseline), "--json"])
        assert rc == 0

    def test_gate_fails_on_large_drift(self, tmp_path: Path) -> None:
        # Baseline claims 0% UNKNOWN; shipped corpus is ~6.7% → drift <10pp → pass.
        # To force a fail, set baseline to 0.90 (expects 90% UNKNOWN);
        # observed ~6.7% → drift ≈ -83pp → fail.
        baseline = tmp_path / "baseline.json"
        ide.write_baseline(0.90, 15, baseline)
        rc = ide.main(["--baseline", str(baseline)])
        assert rc == 1

    def test_update_baseline_writes_file(self, tmp_path: Path) -> None:
        baseline = tmp_path / "baseline.json"
        rc = ide.main(["--update-baseline", "--baseline", str(baseline)])
        assert rc == 0
        payload = json.loads(baseline.read_text(encoding="utf-8"))
        assert "unknown_share" in payload
        assert payload["total"] == 15

    def test_no_baseline_does_not_fail(self, tmp_path: Path) -> None:
        rc = ide.main(["--baseline", str(tmp_path / "missing.json")])
        assert rc == 0
