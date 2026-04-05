"""Tests for Layer 4 REQUIREMENTS analysis."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from layers import layer4_requirements


class TestLayer4Run:
    """Tests for layer4_requirements.run()."""

    def test_run_returns_list(self, tmp_target):
        result = layer4_requirements.run(tmp_target)
        assert isinstance(result, list)

    def test_missing_changelog_reported(self, tmp_target):
        """When CHANGELOG.md is absent, L4 reports it."""
        findings = layer4_requirements.run(tmp_target)
        ids = [f.finding_id for f in findings]
        assert "L4-MISSING-CHANGELOG" in ids


class TestCheckArtifactStatus:
    """Tests for _check_artifact_status."""

    def test_no_changelog_returns_missing_finding(self, tmp_path):
        findings = layer4_requirements._check_artifact_status(tmp_path)
        assert len(findings) == 1
        assert findings[0].finding_id == "L4-MISSING-CHANGELOG"
