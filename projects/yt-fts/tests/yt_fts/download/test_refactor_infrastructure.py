"""
Tests for refactoring infrastructure scripts.

These tests verify that the refactor tracking scripts work correctly.
"""

import pytest
from pathlib import Path


# Get project root (4 levels up from this test file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


# Import scripts with correct paths
import sys
sys.path.insert(0, str(PROJECT_ROOT / "src/yt_fts/download/refactor"))

from layer1_add_configs import verify_configs_exist
from layer2_update_constructor import (
    verify_dual_signature,
    get_constructor_signature,
)
from layer3_migrate_site import (
    CALL_SITES,
    check_call_site_migrated,
    scan_migration_status,
)


class TestLayer1_ConfigVerification:
    """Tests for Layer 1 config verification script."""

    @pytest.fixture
    def batch_config_path(self):
        """Path to batch_config.py."""
        return PROJECT_ROOT / "src/yt_fts/download/batch_config.py"

    def test_all_5_configs_exist(self, batch_config_path):
        """All 5 config dataclasses should exist."""
        assert verify_configs_exist(batch_config_path)

    def test_execution_config_exists(self, batch_config_path):
        """ExecutionConfig should be in the file."""
        code = batch_config_path.read_text()
        assert "class ExecutionConfig" in code

    def test_limits_config_exists(self, batch_config_path):
        """LimitsConfig should be in the file."""
        code = batch_config_path.read_text()
        assert "class LimitsConfig" in code

    def test_ui_config_exists(self, batch_config_path):
        """UIConfig should be in the file."""
        code = batch_config_path.read_text()
        assert "class UIConfig" in code

    def test_content_config_exists(self, batch_config_path):
        """ContentConfig should be in the file."""
        code = batch_config_path.read_text()
        assert "class ContentConfig" in code

    def test_transcript_config_exists(self, batch_config_path):
        """TranscriptConfig should be in the file."""
        code = batch_config_path.read_text()
        assert "class TranscriptConfig" in code


class TestLayer2_ConstructorVerification:
    """Tests for Layer 2 constructor verification script."""

    @pytest.fixture
    def batch_downloader_path(self):
        """Path to batch_downloader.py."""
        return PROJECT_ROOT / "src/yt_fts/download/batch_downloader.py"

    def test_dual_signature_verified(self, batch_downloader_path):
        """Constructor should have dual signature support."""
        assert verify_dual_signature(batch_downloader_path)

    def test_new_config_params_exist(self, batch_downloader_path):
        """New config parameters should exist."""
        code = batch_downloader_path.read_text()
        assert "execution_config: Any = None" in code
        assert "limits_config: Any = None" in code
        assert "content_config: Any = None" in code
        assert "ui_config: Any = None" in code
        assert "transcript_config: Any = None" in code

    def test_old_params_exist_for_backward_compat(self, batch_downloader_path):
        """Old parameters should exist for backward compatibility."""
        code = batch_downloader_path.read_text()
        assert "jobs: int = 2" in code
        assert "language: str = \"en\"" in code
        assert "max_retries: int = 3" in code

    def test_config_extraction_logic_exists(self, batch_downloader_path):
        """Config extraction logic should exist."""
        code = batch_downloader_path.read_text()
        assert "if execution_config is not None:" in code
        assert "if limits_config is not None:" in code

    def test_get_constructor_signature_returns_string(self, batch_downloader_path):
        """Should return constructor signature as string."""
        sig = get_constructor_signature(batch_downloader_path)
        assert isinstance(sig, str)
        assert "def __init__" in sig or "Not found" in sig


class TestLayer3_MigrationTracking:
    """Tests for Layer 3 migration tracking script."""

    @pytest.fixture
    def project_root(self):
        """Project root path."""
        return PROJECT_ROOT

    def test_all_7_call_sites_defined(self):
        """All 7 call sites should be defined."""
        assert len(CALL_SITES) == 7

    def test_call_site_1_batch_execution(self):
        """Call site 1 should be batch_execution.py:249."""
        site = CALL_SITES[0]
        assert site.number == 1
        assert site.file == "batch_execution.py"
        assert site.line == 249

    def test_call_site_2_download_cli(self):
        """Call site 2 should be download_cli.py:1603."""
        site = CALL_SITES[1]
        assert site.number == 2
        assert site.file == "download_cli.py"
        assert site.line == 1603

    def test_parallel_processor_sites(self):
        """Sites 3-7 should be in parallel_processor.py."""
        parallel_sites = CALL_SITES[2:]
        assert len(parallel_sites) == 5
        for site in parallel_sites:
            assert site.file == "parallel_processor.py"

    def test_site_1_migrated(self, project_root):
        """Site 1 (batch_execution.py:249) should be migrated."""
        site = CALL_SITES[0]
        assert check_call_site_migrated(site, project_root)

    def test_site_2_migrated(self, project_root):
        """Site 2 (download_cli.py:1603) should be migrated."""
        site = CALL_SITES[1]
        assert check_call_site_migrated(site, project_root)

    def test_site_3_migrated(self, project_root):
        """Site 3 (parallel_processor.py:415) should be migrated."""
        site = CALL_SITES[2]
        assert check_call_site_migrated(site, project_root)

    def test_site_4_migrated(self, project_root):
        """Site 4 (parallel_processor.py:564) should be migrated."""
        site = CALL_SITES[3]
        assert check_call_site_migrated(site, project_root)

    def test_site_5_migrated(self, project_root):
        """Site 5 (parallel_processor.py:719) should be migrated."""
        site = CALL_SITES[4]
        assert check_call_site_migrated(site, project_root)

    def test_site_6_migrated(self, project_root):
        """Site 6 (parallel_processor.py:868) should be migrated."""
        site = CALL_SITES[5]
        assert check_call_site_migrated(site, project_root)

    def test_site_7_migrated(self, project_root):
        """Site 7 (parallel_processor.py:1072) should be migrated."""
        site = CALL_SITES[6]
        assert check_call_site_migrated(site, project_root)

    def test_all_sites_migrated(self, project_root):
        """All 7 call sites should be migrated."""
        results = scan_migration_status(project_root)
        assert all(results.values())

    def test_migration_status_returns_dict(self, project_root):
        """Should return dictionary mapping sites to status."""
        results = scan_migration_status(project_root)
        assert isinstance(results, dict)
        assert len(results) == 7


class TestRefactorIntegration:
    """Integration tests for refactor infrastructure."""

    def test_refactor_infrastructure_complete(self):
        """All refactor infrastructure should be in place."""
        refactor_dir = PROJECT_ROOT / "src/yt_fts/download/refactor"
        assert refactor_dir.exists()
        assert (refactor_dir / "__init__.py").exists()
        assert (refactor_dir / "layer1_add_configs.py").exists()
        assert (refactor_dir / "layer2_update_constructor.py").exists()
        assert (refactor_dir / "layer3_migrate_site.py").exists()
        assert (refactor_dir / "layer3_verify.yaml").exists()
        assert (refactor_dir / "layer4_cleanup.py").exists()

    def test_full_migration_complete(self):
        """Full migration should be complete (Layers 1-3)."""
        # Layer 1: Configs exist
        batch_config = PROJECT_ROOT / "src/yt_fts/download/batch_config.py"
        assert verify_configs_exist(batch_config)

        # Layer 2: Constructor updated
        batch_downloader = PROJECT_ROOT / "src/yt_fts/download/batch_downloader.py"
        assert verify_dual_signature(batch_downloader)

        # Layer 3: All sites migrated
        results = scan_migration_status(PROJECT_ROOT)
        assert all(results.values())
