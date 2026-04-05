#!/usr/bin/env python3
"""Test for enforce_verification_gate function - RED phase."""
from __future__ import annotations

from pathlib import Path

import pytest


class TestVerificationGateImport:
    """Test verification gate import method."""

    def test_importlib_load_module(self):
        """Test that post_fix_validator can be loaded via importlib."""
        import importlib.util

        hooks_dir = Path("P:/.claude/hooks")
        validator_path = hooks_dir / "post_fix_validator.py"

        if not validator_path.exists():
            pytest.skip(f"Validator file not found: {validator_path}")

        # Load module
        spec = importlib.util.spec_from_file_location("post_fix_validator", validator_path)
        assert spec is not None, "Spec is None"

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify functions exist
        assert hasattr(module, "suggest_fix_verification")
        assert hasattr(module, "run_fix_verification")
        assert callable(module.suggest_fix_verification)

    def test_rca_session_module(self):
        """Test that rca.session module can be imported."""
        from rca.session import ProblemType, record_debug_start

        # Basic smoke test
        assert ProblemType.ERROR in ProblemType

        session_id = record_debug_start(
            problem_description="Test problem",
            problem_type=ProblemType.ERROR,
            context="test_module"
        )

        assert session_id is not None
        assert isinstance(session_id, str)

    def test_rca_error_signature(self):
        """Test that rca.error_signature module works."""
        from rca.error_signature import ErrorSignature, extract_signature

        sig = extract_signature("AttributeError: 'NoneType' object has no attribute 'x'")
        assert sig is not None
        assert sig.error_type == "AttributeError"

    def test_rca_integration_modules(self):
        """Test that rca integration modules can be imported."""
        from rca.integration.explore_integration import ExploreIntegration
        from rca.integration.cks_pattern_integration import CKSPatternRegistry

        explore = ExploreIntegration()
        assert explore is not None

        # Note: TaskMasterIntegration deprecated, replaced by CKS
        # CKSPatternRegistry may be None if CKS is not available
        cks = CKSPatternRegistry()
        assert cks is not None

    def test_rca_core_modules(self):
        """Test that rca core modules can be imported."""
        from rca.core.context_analyzer import ContextAnalyzer
        from rca.core.tool_selector import ToolSelector
        from rca.core.performance_optimizer import PerformanceOptimizer

        ctx_analyzer = ContextAnalyzer()
        assert ctx_analyzer is not None

        tool_sel = ToolSelector()
        assert tool_sel is not None

        perf_opt = PerformanceOptimizer()
        assert perf_opt is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
