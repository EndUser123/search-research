"""Unit tests for CKS integration modules.

Tests for:
- core/cks/cks_cli.py (CKSCLI class)
- core/cks/integration/commands/real_cks_integration.py (RealCKSIntegration class)
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCKSIntegrationResult:
    """Tests for CKSIntegrationResult dataclass."""

    def test_dataclass_default_values(self):
        """Test that CKSIntegrationResult has correct default values."""
        from core.cks.integration.commands.real_cks_integration import CKSIntegrationResult

        result = CKSIntegrationResult(success=True)
        assert result.success is True
        assert result.entry_id is None
        assert result.processing_time == 0.0
        assert result.stored_in_real_cks is False
        assert result.cks_stats is None
        assert result.error is None
        assert result.metadata == {}

    def test_dataclass_custom_values(self):
        """Test that CKSIntegrationResult accepts custom values."""
        from core.cks.integration.commands.real_cks_integration import CKSIntegrationResult

        result = CKSIntegrationResult(
            success=True,
            entry_id="cks_abc123",
            processing_time=1.5,
            stored_in_real_cks=True,
            cks_stats={"entries": 10},
            error=None,
            metadata={"category": "test"},
        )
        assert result.success is True
        assert result.entry_id == "cks_abc123"
        assert result.processing_time == 1.5
        assert result.stored_in_real_cks is True
        assert result.cks_stats == {"entries": 10}
        assert result.metadata == {"category": "test"}

    def test_dataclass_error_result(self):
        """Test CKSIntegrationResult for error case."""
        from core.cks.integration.commands.real_cks_integration import CKSIntegrationResult

        result = CKSIntegrationResult(
            success=False,
            processing_time=0.1,
            error="Connection failed",
        )
        assert result.success is False
        assert result.error == "Connection failed"
        assert result.stored_in_real_cks is False


class TestRealCKSIntegration:
    """Tests for RealCKSIntegration class."""

    def test_init_without_cks(self):
        """Test initialization when CKS is not available."""
        with patch.dict(
            sys.modules,
            {"co.learn_spec_2025": None, "simple_cks_test": None},
        ):
            # Force reimport to apply mock
            import importlib

            import core.cks.integration.commands.real_cks_integration as cks_module

            importlib.reload(cks_module)

            integration = cks_module.RealCKSIntegration()
            assert integration.knowledge_manager is None

    def test_generate_knowledge_id(self):
        """Test _generate_knowledge_id generates unique IDs."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        id1 = integration._generate_knowledge_id("content1")
        id2 = integration._generate_knowledge_id("content2")

        assert id1.startswith("cks_")
        assert id2.startswith("cks_")
        assert id1 != id2  # Different content should produce different IDs

    def test_extract_entities_tech_terms(self):
        """Test _extract_entities extracts technical terms."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        entities = integration._extract_entities("Using Python with React for the API endpoint")

        assert "Python" in entities
        assert "React" in entities
        assert "API" in entities

    def test_extract_entities_urls(self):
        """Test _extract_entities extracts URLs."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        entities = integration._extract_entities("Check https://example.com/docs for details")

        assert "https://example.com/docs" in entities

    def test_extract_entities_deduplicates(self):
        """Test _extract_entities deduplicates results."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        entities = integration._extract_entities("Python Python Python API API")

        # Should only have one of each
        assert entities.count("Python") == 1
        assert entities.count("API") == 1

    def test_generate_tags_basic(self):
        """Test _generate_tags produces expected tags."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        tags = integration._generate_tags("How to use Python for machine learning", "direct_text")

        assert "direct_text" in tags
        # Should detect programming and ai-ml topics
        assert "programming" in tags or "ai-ml" in tags

    def test_generate_tags_database_content(self):
        """Test _generate_tags detects database topics."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        tags = integration._generate_tags(
            "SQL query optimization for database performance", "direct_text"
        )

        assert "database" in tags

    def test_generate_tags_security_content(self):
        """Test _generate_tags detects security topics."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        tags = integration._generate_tags(
            "Authentication token encryption for security", "direct_text"
        )

        assert "security" in tags

    @pytest.mark.asyncio
    async def test_ingest_knowledge_category_detection_bug(self):
        """Test ingest_knowledge detects 'troubleshooting' category for bug content."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        result = await integration.ingest_knowledge(
            input_data="This bug in the error handling causes issues",
            category=None,
        )

        assert result.success is True
        assert result.metadata.get("category") == "troubleshooting"

    @pytest.mark.asyncio
    async def test_ingest_knowledge_category_detection_tutorial(self):
        """Test ingest_knowledge detects 'tutorial' category for how-to content."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        result = await integration.ingest_knowledge(
            input_data="How to implement a REST API with FastAPI",
            category=None,
        )

        assert result.success is True
        assert result.metadata.get("category") == "tutorial"

    @pytest.mark.asyncio
    async def test_ingest_knowledge_category_detection_best_practice(self):
        """Test ingest_knowledge detects 'best-practice' category."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        result = await integration.ingest_knowledge(
            input_data="Best practice for handling async operations",
            category=None,
        )

        assert result.success is True
        assert result.metadata.get("category") == "best-practice"

    @pytest.mark.asyncio
    async def test_ingest_knowledge_custom_category(self):
        """Test ingest_knowledge respects custom category."""
        from core.cks.integration.commands.real_cks_integration import RealCKSIntegration

        integration = RealCKSIntegration()
        result = await integration.ingest_knowledge(
            input_data="Some content here",
            category="custom-category",
        )

        assert result.success is True
        assert result.metadata.get("category") == "custom-category"

    def test_get_cks_status_unavailable(self):
        """Test get_cks_status when CKS is unavailable."""
        from core.cks.integration.commands.real_cks_integration import (
            REAL_CKS_AVAILABLE,
            RealCKSIntegration,
        )

        if not REAL_CKS_AVAILABLE:
            integration = RealCKSIntegration()
            status = integration.get_cks_status()
            assert status["status"] == "unavailable"


class TestCKSCLI:
    """Tests for CKSCLI class."""

    def test_detect_content_type_pattern(self):
        """Test detect_content_type identifies patterns."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)  # Create without __init__

        content_type = cli.detect_content_type("Results: 32% improvement in latency")
        assert content_type == "pattern"

    def test_detect_content_type_memory(self):
        """Test detect_content_type identifies memory/Q&A format."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("What is JWT authentication?")
        assert content_type == "memory"

    def test_detect_content_type_code(self):
        """Test detect_content_type identifies code."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("def process_data():\n    return True")
        assert content_type == "code"

    def test_detect_content_type_decision(self):
        """Test detect_content_type identifies decisions."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("Decided to use Redis for caching")
        assert content_type == "decision"

    def test_detect_content_type_correction(self):
        """Test detect_content_type identifies corrections."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("Fixed: null pointer in auth flow")
        assert content_type == "correction"

    def test_detect_content_type_insight(self):
        """Test detect_content_type identifies insights."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("Realized: the bottleneck was in serialization")
        assert content_type == "insight"

    def test_detect_content_type_learning(self):
        """Test detect_content_type identifies learnings."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("Learned: always validate input at boundaries")
        assert content_type == "learning"

    def test_detect_content_type_knowledge_default(self):
        """Test detect_content_type defaults to knowledge."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("Some general documentation text")
        assert content_type == "knowledge"

    def test_detect_content_type_anti_pattern_metrics(self):
        """Test detect_content_type identifies metrics patterns."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        # Metrics should trigger pattern detection
        content_type = cli.detect_content_type("Metrics: 50% latency reduction")
        assert content_type == "pattern"

    def test_detect_content_type_anti_pattern_benchmark(self):
        """Test detect_content_type identifies benchmark patterns."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("Benchmark: comparison of approaches")
        assert content_type == "pattern"


class TestCKSCLIContentDetection:
    """Edge case tests for CKSCLI content detection."""

    def test_empty_content(self):
        """Test detect_content_type handles empty content."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("")
        assert content_type == "knowledge"  # Default

    def test_whitespace_content(self):
        """Test detect_content_type handles whitespace-only content."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("   \n\t  ")
        assert content_type == "knowledge"  # Default

    def test_mixed_signals_prioritizes_pattern(self):
        """Test detect_content_type with mixed signals."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        # Contains both "Results:" (pattern) and "def " (code)
        # Pattern check comes first, so should be pattern
        content_type = cli.detect_content_type("Results: def process(): pass")
        assert content_type == "pattern"

    def test_case_insensitive_detection(self):
        """Test detect_content_type is case-insensitive."""
        from core.cks.cks_cli import CKSCLI

        cli = CKSCLI.__new__(CKSCLI)

        content_type = cli.detect_content_type("DECIDED TO use the new approach")
        assert content_type == "decision"

        content_type = cli.detect_content_type("FIXED: the bug in production")
        assert content_type == "correction"
