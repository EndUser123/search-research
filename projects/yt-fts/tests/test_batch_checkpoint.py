"""Tests for polymorphic checkpoint API in batch_checkpoint.py."""

import json
import pytest
from pathlib import Path

from yt_fts.download.batch_checkpoint import (
    save_checkpoint,
    load_checkpoint,
    reset_checkpoint,
    RefactorCheckpoint,
    CheckpointData,
)


@pytest.fixture
def temp_checkpoint_file(tmp_path):
    """Temporary checkpoint file for testing."""
    return tmp_path / "test_checkpoint.json"


class TestLegacyCheckpoint:
    """Tests for legacy int checkpoint format (backward compatibility)."""
    
    def test_save_and_load_int_checkpoint(self, temp_checkpoint_file):
        """Should save and load integer checkpoint."""
        save_checkpoint(5, str(temp_checkpoint_file))
        result = load_checkpoint(str(temp_checkpoint_file))
        assert result == 5
    
    def test_save_int_creates_valid_json(self, temp_checkpoint_file):
        """Should create valid JSON with type field."""
        save_checkpoint(3, str(temp_checkpoint_file))
        
        with open(temp_checkpoint_file) as f:
            data = json.load(f)
        
        assert data["type"] == "channel_index"
        assert data["last_completed_index"] == 3
        assert "timestamp" in data


class TestRefactorCheckpoint:
    """Tests for new RefactorCheckpoint dict format."""
    
    def test_save_and_load_refactor_checkpoint(self, temp_checkpoint_file):
        """Should save and load RefactorCheckpoint dict."""
        refactor_data: RefactorCheckpoint = {
            "refactor_id": "batch-downloader-config-extraction",
            "layer": 1,
            "call_site": "batch_execution.py:249",
            "status": "success",
            "timestamp": "2025-01-21T12:00:00"
        }
        
        save_checkpoint(refactor_data, str(temp_checkpoint_file))
        result = load_checkpoint(str(temp_checkpoint_file))
        
        assert isinstance(result, dict)
        assert result["refactor_id"] == "batch-downloader-config-extraction"
        assert result["layer"] == 1
    
    def test_save_refactor_without_call_site(self, temp_checkpoint_file):
        """Should save RefactorCheckpoint without optional call_site field."""
        refactor_data: RefactorCheckpoint = {
            "refactor_id": "test-refactor",
            "layer": 2,
            "status": "pending",
            "timestamp": "2025-01-21T12:00:00"
        }
        
        save_checkpoint(refactor_data, str(temp_checkpoint_file))
        result = load_checkpoint(str(temp_checkpoint_file))
        
        assert "call_site" not in result  # Optional field not present
        assert result["layer"] == 2


class TestTypeValidation:
    """Tests for type validation in polymorphic API."""
    
    def test_rejects_invalid_type(self, temp_checkpoint_file):
        """Should raise TypeError for invalid checkpoint data."""
        with pytest.raises(TypeError):
            save_checkpoint("invalid", str(temp_checkpoint_file))
    
    def test_load_returns_none_for_missing_file(self, tmp_path):
        """Should return None when checkpoint file doesn't exist."""
        non_existent = tmp_path / "non_existent.json"
        result = load_checkpoint(str(non_existent))
        assert result is None


class TestResetCheckpoint:
    """Tests for checkpoint reset functionality."""
    
    def test_reset_deletes_checkpoint_file(self, temp_checkpoint_file):
        """Should delete checkpoint file when reset."""
        # First create a checkpoint
        save_checkpoint(5, str(temp_checkpoint_file))
        assert temp_checkpoint_file.exists()
        
        # Reset it
        reset_checkpoint(str(temp_checkpoint_file))
        assert not temp_checkpoint_file.exists()
