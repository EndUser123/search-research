"""
Tests for EvidenceValidator class.

Test-Driven Development: RED phase - these tests should FAIL initially.
"""

import json

import pytest

# Import the module (will fail until we create it)
try:
    from evidence import EvidenceValidator, EvidenceValidity
except ImportError:
    pytest.skip("evidence module not created yet", allow_module_level=True)


class TestEvidenceValidity:
    """Test EvidenceValidity dataclass."""

    def test_evidence_validity_fields(self):
        """EvidenceValidity has required fields."""
        validity = EvidenceValidity(
            is_valid=True,
            source="hash_verified",
            cached_hash="abc123",
            observation_age_seconds=30.0
        )
        assert validity.is_valid is True
        assert validity.source == "hash_verified"
        assert validity.cached_hash == "abc123"
        assert validity.observation_age_seconds == 30.0


class TestEvidenceValidatorInit:
    """Test EvidenceValidator initialization."""

    def test_creates_cache_directory(self, tmp_path):
        """EvidenceValidator creates cache directory if it doesn't exist."""
        cache_dir = tmp_path / "evidence_cache"
        validator = EvidenceValidator(cache_dir)
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_accepts_existing_cache_directory(self, tmp_path):
        """EvidenceValidator accepts existing cache directory."""
        validator = EvidenceValidator(tmp_path)
        assert validator.cache_dir == tmp_path


class TestFileHash:
    """Test _file_hash method."""

    def test_returns_consistent_hash_for_same_file(self, tmp_path):
        """File hash is consistent for same file content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        validator = EvidenceValidator(tmp_path)

        hash1 = validator._file_hash(test_file)
        hash2 = validator._file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
        assert hash1.isalnum()

    def test_returns_different_hash_for_different_content(self, tmp_path):
        """Different file content produces different hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content one")
        file2.write_text("content two")

        validator = EvidenceValidator(tmp_path)

        hash1 = validator._file_hash(file1)
        hash2 = validator._file_hash(file2)

        assert hash1 != hash2

    def test_returns_empty_string_for_nonexistent_file(self, tmp_path):
        """Non-existent file returns empty hash."""
        validator = EvidenceValidator(tmp_path)
        nonexistent = tmp_path / "does_not_exist.txt"

        result = validator._file_hash(nonexistent)

        assert result == ""

    def test_hash_is_sha256_format(self, tmp_path):
        """Hash is in SHA256 hex format (64 hex characters)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        validator = EvidenceValidator(tmp_path)
        hash_value = validator._file_hash(test_file)

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)


class TestValidateClaimEvidence:
    """Test validate_claim_evidence method."""

    def test_no_evidence_returns_none_source(self, tmp_path):
        """With no cache and no observation, returns source='none'."""
        validator = EvidenceValidator(tmp_path)
        claimed_paths = {tmp_path / "any_file.txt"}

        result = validator.validate_claim_evidence(
            claimed_paths=claimed_paths,
            observation_receipt=None,
            post_block_required=False
        )

        assert result.is_valid is False
        assert result.source == "none"
        assert result.cached_hash is None
        assert result.observation_age_seconds is None

    def test_hash_verified_evidence_accepted(self, tmp_path, monkeypatch):
        """Hash-verified evidence returns source='hash_verified'."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Mock time to return a fixed timestamp
        fake_time = 1000000.0

        class FakeTime:
            def time(self):
                return fake_time

        monkeypatch.setattr("evidence.time", FakeTime())

        validator = EvidenceValidator(tmp_path)

        # Manually create a hash cache entry
        cache_file = tmp_path / "hash_cache_default.json"
        file_hash = validator._file_hash(test_file)
        cache_file.write_text(json.dumps({
            str(test_file): {
                "hash": file_hash,
                "updated_at": fake_time - 100  # 100 seconds ago
            }
        }))

        result = validator.validate_claim_evidence(
            claimed_paths={test_file},
            observation_receipt=None,
            post_block_required=True,
            terminal_key="default"
        )

        assert result.is_valid is True
        assert result.source == "hash_verified"
        assert result.cached_hash == file_hash
        assert result.observation_age_seconds == 100

    def test_expired_hash_cache_not_accepted(self, tmp_path, monkeypatch):
        """Expired hash cache entry (TTL exceeded) is not accepted."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Mock time to simulate expired cache
        fake_time = 1000000.0

        class FakeTime:
            def time(self):
                return fake_time

        monkeypatch.setattr("evidence.time", FakeTime())

        validator = EvidenceValidator(tmp_path)

        # Create an expired cache entry (>1800 seconds old)
        cache_file = tmp_path / "hash_cache_default.json"
        file_hash = validator._file_hash(test_file)
        cache_file.write_text(json.dumps({
            str(test_file): {
                "hash": file_hash,
                "updated_at": fake_time - 2000  # 2000 seconds ago (expired)
            }
        }))

        result = validator.validate_claim_evidence(
            claimed_paths={test_file},
            observation_receipt=None,
            post_block_required=True,
            terminal_key="default"
        )

        assert result.is_valid is False
        assert result.source == "none"

    def test_file_change_detected_hash_mismatch(self, tmp_path, monkeypatch):
        """Changed file is detected via hash mismatch."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        fake_time = 1000000.0

        class FakeTime:
            def time(self):
                return fake_time

        monkeypatch.setattr("evidence.time", FakeTime())

        validator = EvidenceValidator(tmp_path)

        # Cache hash for original content
        cache_file = tmp_path / "hash_cache_default.json"
        original_hash = validator._file_hash(test_file)
        cache_file.write_text(json.dumps({
            str(test_file): {
                "hash": original_hash,
                "updated_at": fake_time - 100
            }
        }))

        # Change file content
        test_file.write_text("modified content")

        result = validator.validate_claim_evidence(
            claimed_paths={test_file},
            observation_receipt=None,
            post_block_required=True,
            terminal_key="default"
        )

        # Hash mismatch means cache is invalid
        assert result.is_valid is False
        assert result.source == "none"

    def test_fresh_observation_accepted(self, tmp_path, monkeypatch):
        """Fresh observation receipt is accepted."""
        fake_time = 1000000.0

        class FakeTime:
            def time(self):
                return fake_time

        monkeypatch.setattr("evidence.time", FakeTime())

        validator = EvidenceValidator(tmp_path)

        receipt = {
            "updated_at": fake_time - 30  # 30 seconds ago
        }

        result = validator.validate_claim_evidence(
            claimed_paths=set(),
            observation_receipt=receipt,
            post_block_required=True
        )

        assert result.is_valid is True
        assert result.source == "fresh_observation"
        assert result.observation_age_seconds == 30

    def test_stale_observation_not_accepted(self, tmp_path, monkeypatch):
        """Stale observation receipt (>60 seconds) is not accepted."""
        fake_time = 1000000.0

        class FakeTime:
            def time(self):
                return fake_time

        monkeypatch.setattr("evidence.time", FakeTime())

        validator = EvidenceValidator(tmp_path)

        receipt = {
            "updated_at": fake_time - 120  # 120 seconds ago (too old)
        }

        result = validator.validate_claim_evidence(
            claimed_paths=set(),
            observation_receipt=receipt,
            post_block_required=True
        )

        assert result.is_valid is False
        assert result.source == "none"
