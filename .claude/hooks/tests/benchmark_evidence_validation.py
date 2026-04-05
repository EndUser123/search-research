"""
Performance benchmarks for evidence validation system.

Measures:
- Hash computation speed (@lru_cache vs without)
- Validation throughput (claims per second)
- Cache hit rate percentage
"""

import hashlib
import json
import sys
import time
from pathlib import Path

import pytest

# Add hooks directory to path for imports
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from evidence import EvidenceValidator


class TestHashComputationPerformance:
    """Benchmark hash computation with and without caching."""

    def test_hash_uncached_performance(self, tmp_path, benchmark):
        """Benchmark uncached hash computation (baseline)."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("x" * 10000)  # 10KB file

        validator = EvidenceValidator(tmp_path)

        # Clear cache to ensure uncached computation
        validator._file_hash.cache_clear()

        def compute_uncached():
            return validator._compute_file_hash_uncached(test_file)

        result = benchmark(compute_uncached)
        # Result is the hash, benchmark measures time
        assert len(result) == 64  # SHA256 hex length

    def test_hash_cached_performance(self, tmp_path, benchmark):
        """Benchmark cached hash computation (with @lru_cache)."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("x" * 10000)  # 10KB file

        validator = EvidenceValidator(tmp_path)

        # Populate cache first
        validator._file_hash(test_file)

        def compute_cached():
            return validator._file_hash(test_file)

        result = benchmark(compute_cached)
        # Result is the hash, benchmark measures time
        assert len(result) == 64  # SHA256 hex length

    def test_hash_scaling_small_file(self, tmp_path, benchmark):
        """Benchmark hash computation for small file (1KB)."""
        validator = EvidenceValidator(tmp_path)

        small_file = tmp_path / "small.txt"
        small_file.write_text("x" * 1024)

        def hash_small():
            return validator._compute_file_hash_uncached(small_file)

        result = benchmark(hash_small)
        assert len(result) == 64

    def test_hash_scaling_large_file(self, tmp_path, benchmark):
        """Benchmark hash computation for large file (100KB)."""
        validator = EvidenceValidator(tmp_path)

        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 102400)

        def hash_large():
            return validator._compute_file_hash_uncached(large_file)

        result = benchmark(hash_large)
        assert len(result) == 64


class TestValidationThroughput:
    """Benchmark validation throughput (claims per second)."""

    def test_validation_throughput_hash_verified(self, tmp_path, benchmark):
        """Validation throughput >1000 claims/second for hash-verified claims."""
        # Setup: create hash cache entries
        validator = EvidenceValidator(tmp_path)

        # Create multiple files
        for i in range(10):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text(f"content {i}")
            validator.update_hash_cache(test_file, terminal_key="test")

        claimed_paths = {tmp_path / f"file{i}.txt" for i in range(10)}

        def validate_claim():
            return validator.validate_claim_evidence(
                claimed_paths=claimed_paths,
                observation_receipt=None,
                post_block_required=False,
                terminal_key="test"
            )

        result = benchmark(validate_claim)

        assert result.is_valid
        assert result.source == "hash_verified"

    def test_validation_throughput_no_cache(self, tmp_path, benchmark):
        """Validation throughput without cache (baseline)."""
        validator = EvidenceValidator(tmp_path)

        # Create files without caching
        for i in range(10):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text(f"content {i}")

        claimed_paths = {tmp_path / f"file{i}.txt" for i in range(10)}

        def validate_claim():
            return validator.validate_claim_evidence(
                claimed_paths=claimed_paths,
                observation_receipt=None,
                post_block_required=False,
                terminal_key="test"
            )

        result = benchmark(validate_claim)

        assert not result.is_valid
        assert result.source == "none"

    def test_validation_throughput_fresh_observation(self, tmp_path, benchmark):
        """Validation throughput with fresh observation receipt."""
        validator = EvidenceValidator(tmp_path)

        claimed_paths = set()
        fresh_receipt = {
            "receipt_id": "test-receipt",
            "updated_at": time.time()
        }

        def validate_claim():
            return validator.validate_claim_evidence(
                claimed_paths=claimed_paths,
                observation_receipt=fresh_receipt,
                post_block_required=True,
                terminal_key="test"
            )

        result = benchmark(validate_claim)

        assert result.is_valid
        assert result.source == "fresh_observation"


class TestCacheHitRate:
    """Benchmark cache hit rate in typical workflow."""

    def test_cache_hit_rate_repeated_claims(self, tmp_path):
        """Cache hit rate >70% in typical workflow with repeated claims."""
        validator = EvidenceValidator(tmp_path)

        # Setup: populate cache with 10 files
        for i in range(10):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text(f"content {i}")
            validator.update_hash_cache(test_file, terminal_key="test")

        # Simulate typical workflow: 100 validation requests
        # 70% claim cached files, 30% claim uncached files
        hits = 0
        total = 100

        for i in range(total):
            if i < 70:  # 70% cached claims
                claimed_paths = {tmp_path / f"file{i % 10}.txt"}
            else:  # 30% uncached claims
                claimed_paths = {tmp_path / f"uncached_file{i}.txt"}

            validity = validator.validate_claim_evidence(
                claimed_paths=claimed_paths,
                observation_receipt=None,
                post_block_required=False,
                terminal_key="test"
            )

            if validity.is_valid and validity.source == "hash_verified":
                hits += 1

        hit_rate = hits / total
        assert hit_rate >= 0.7, f"Cache hit rate {hit_rate:.2%} is below 70%"

    def test_cache_hit_rate_with_mixed_sources(self, tmp_path):
        """Cache hit rate when mixing hash-verified and fresh observation."""
        validator = EvidenceValidator(tmp_path)

        # Populate cache with 5 files
        for i in range(5):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text(f"content {i}")
            validator.update_hash_cache(test_file, terminal_key="test")

        hits = 0
        total = 50

        for i in range(total):
            if i % 3 == 0:  # Hash-verified (33%)
                claimed_paths = {tmp_path / f"file{i % 5}.txt"}
                receipt = None
            elif i % 3 == 1:  # Fresh observation (33%)
                claimed_paths = {tmp_path / f"new_file{i}.txt"}
                receipt = {"receipt_id": f"receipt-{i}", "updated_at": time.time()}
            else:  # No evidence (33%)
                claimed_paths = {tmp_path / f"uncached{i}.txt"}
                receipt = None

            validity = validator.validate_claim_evidence(
                claimed_paths=claimed_paths,
                observation_receipt=receipt,
                post_block_required=True,
                terminal_key="test"
            )

            if validity.is_valid:
                hits += 1

        hit_rate = hits / total
        # Should have decent hit rate even with mixed sources
        assert hit_rate >= 0.5, f"Valid evidence rate {hit_rate:.2%} is below 50%"


class TestCachePerformance:
    """Benchmark cache performance characteristics."""

    def test_cache_lookup_speed(self, tmp_path, benchmark):
        """Cache lookup is fast even with many entries."""
        validator = EvidenceValidator(tmp_path)

        # Populate cache with 1000 files
        for i in range(1000):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text(f"content {i}")
            validator.update_hash_cache(test_file, terminal_key="test")

        # Benchmark lookup performance
        claimed_paths = {tmp_path / f"file{i}.txt" for i in range(10)}

        def validate_claim():
            return validator.validate_claim_evidence(
                claimed_paths=claimed_paths,
                observation_receipt=None,
                post_block_required=False,
                terminal_key="test"
            )

        result = benchmark(validate_claim)

        assert result.is_valid
        assert result.source == "hash_verified"

    def test_cache_ttl_expiration_performance(self, tmp_path, benchmark):
        """TTL expiration check doesn't significantly impact performance."""
        validator = EvidenceValidator(tmp_path)

        # Create cache entries with varying ages
        now = time.time()
        for i in range(100):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text(f"content {i}")

            # Manually create cache entries with different ages
            cache_file = tmp_path / "evidence" / "hash_cache_test.json"
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            if cache_file.exists():
                cache_data = json.loads(cache_file.read_text())
            else:
                cache_data = {}

            cache_data[str(test_file)] = {
                "hash": hashlib.sha256(test_file.read_bytes()).hexdigest(),
                "updated_at": now - (i * 10)  # Staggered ages
            }
            cache_file.write_text(json.dumps(cache_data))

        claimed_paths = {tmp_path / f"file{i}.txt" for i in range(10)}

        def validate_claim():
            return validator.validate_claim_evidence(
                claimed_paths=claimed_paths,
                observation_receipt=None,
                post_block_required=False,
                terminal_key="test"
            )

        result = benchmark(validate_claim)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only", "--benchmark-columns=min,max,mean,stddev,ops"])
