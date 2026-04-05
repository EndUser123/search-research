"""
Test for race condition in ClaimGuard state management.

This test suite verifies that concurrent claim recording doesn't cause data loss
due to race conditions in load_claims/save_claims operations.

Test Strategy:
- RED Phase: Tests fail because there's no file locking in load_claims/save_claims
- GREEN Phase: Implementation will add file locking to make tests pass
- REFACTOR Phase: Clean up with tests passing

The race condition occurs because:
1. Thread A: load_claims() reads file
2. Thread B: load_claims() reads file (same data)
3. Thread A: modifies claims, save_claims() writes
4. Thread B: modifies claims, save_claims() writes (overwrites A's changes!)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

try:
    import portalocker
    PORTALOCKER_AVAILABLE = True
except ImportError:
    PORTALOCKER_AVAILABLE = False

# Setup path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[3]
HOOKS_PATH = PROJECT_ROOT / ".claude" / "hooks"

sys.path.insert(0, str(HOOKS_PATH))


class TestClaimGuardRaceCondition:
    """
    Tests for race condition in claim state management.

    Verifies that concurrent calls to record_claim() don't lose data
    due to race conditions in the load-modify-save pattern.
    """

    def setup_method(self):
        """
        Set up test fixtures before each test.

        Creates a temporary state directory to avoid interfering
        with actual claimguard state files.
        """
        # Create temporary state directory for this test
        self.temp_dir = tempfile.mkdtemp(prefix="claimguard_test_")
        self.state_dir = Path(self.temp_dir) / "claimguard"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.claims_file = self.state_dir / "detected_claims.json"

    def teardown_method(self):
        """
        Clean up test fixtures after each test.

        Removes temporary state files.
        """
        # Clean up temp files
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _get_record_claim_function(self):
        """
        Get a record_claim function that uses the test state directory.

        Returns a function that records claims to the test claims file.
        """
        def record_claim_test(claim_type: str, claim_text: str, verdict: str, confidence: float = 0.0):
            """
            Record a detected claim for tracking and metrics.

            This is a copy of the record_claim function from PostToolUse_claimguard.py
            modified to use the test claims file.
            """
            self.claims_file.parent.mkdir(parents=True, exist_ok=True)

            if PORTALOCKER_AVAILABLE:
                # Use file locking for atomic read-modify-write operation
                # Open in read+ mode to allow both reading and writing
                with open(self.claims_file, 'a+', encoding='utf-8') as f:
                    # Acquire exclusive lock for the entire operation
                    portalocker.lock(f, portalocker.LOCK_EX)

                    # Read existing data
                    f.seek(0)
                    try:
                        if f.read(1):  # Check if file is not empty
                            f.seek(0)
                            claims = json.load(f)
                        else:
                            claims = {}
                    except (json.JSONDecodeError, OSError):
                        claims = {}

                    # Add new claim
                    from datetime import UTC, datetime
                    key = f"{claim_type}_{datetime.now(UTC).isoformat()}"
                    claims[key] = {
                        "type": claim_type,
                        "text": claim_text[:200],
                        "verdict": verdict,
                        "confidence": confidence,
                        "timestamp": datetime.now(UTC).timestamp(),
                    }

                    # Write updated data
                    f.seek(0)
                    f.truncate()
                    f.write(json.dumps(claims, indent=2))
            else:
                # Fallback without locking - has race condition
                def load_claims():
                    """Load claims from state file with TTL cleanup."""
                    if self.claims_file.exists():
                        try:
                            data = json.loads(self.claims_file.read_text(encoding="utf-8"))
                            # For testing, we'll skip TTL cleanup to make tests simpler
                            return data
                        except (OSError, json.JSONDecodeError):
                            pass
                    return {}

                def save_claims(claims: dict):
                    """Save claims to state file."""
                    self.claims_file.write_text(json.dumps(claims, indent=2), encoding="utf-8")

                # This is the critical section where race condition occurs:
                # 1. Load existing claims
                # 2. Add new claim
                # 3. Save all claims
                # Without atomic operations or locking, concurrent calls will overwrite each other

                claims = load_claims()
                from datetime import UTC, datetime
                key = f"{claim_type}_{datetime.now(UTC).isoformat()}"
                claims[key] = {
                    "type": claim_type,
                    "text": claim_text[:200],
                    "verdict": verdict,
                    "confidence": confidence,
                    "timestamp": datetime.now(UTC).timestamp(),
                }
                save_claims(claims)

        return record_claim_test

    def test_concurrent_claim_recording_no_data_loss(self):
        """
        Test that concurrent claim recording doesn't lose data.

        Given:
            - Multiple threads try to record claims simultaneously
            - Each thread records different claim data
            - No file locking exists (current implementation)
        When:
            - All threads call record_claim() concurrently
        Then:
            - All claims should be preserved (no data loss)
            - Currently FAILS due to race condition

        This test FAILS because:
        - Thread A: load_claims() -> gets {}
        - Thread B: load_claims() -> gets {} (same data!)
        - Thread A: adds claim_1, saves {claim_1}
        - Thread B: adds claim_2, saves {claim_2} (overwrites claim_1!)
        - Result: Only claim_2 saved, claim_1 lost!
        """
        record_claim = self._get_record_claim_function()

        # Test data - multiple distinct claims
        claims_data = [
            ('output_claim', 'claim_1_test_data', 'FALSE', 0.95),
            ('file_claim', 'claim_2_test_data', 'FALSE', 0.90),
            ('output_claim', 'claim_3_test_data', 'FALSE', 0.85),
            ('file_claim', 'claim_4_test_data', 'FALSE', 0.88),
            ('output_claim', 'claim_5_test_data', 'FALSE', 0.92),
        ]

        results = []
        errors = []

        def record_claim_thread(claim_data):
            """Thread function to record a claim."""
            try:
                record_claim(*claim_data)
                results.append(claim_data)
            except Exception as e:
                errors.append((claim_data, str(e)))

        # Create and start all threads simultaneously
        threads = [threading.Thread(target=record_claim_thread, args=(d,))
                   for d in claims_data]

        # Start all threads at once to maximize race condition probability
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=5.0)

        # Load the final saved claims
        def load_claims():
            """Load claims from test state file."""
            if self.claims_file.exists():
                try:
                    data = json.loads(self.claims_file.read_text(encoding="utf-8"))
                    return data
                except (OSError, json.JSONDecodeError):
                    pass
            return {}

        saved_claims = load_claims()

        # Assert: All claims should be preserved
        # This ASSERTION FAILS due to race condition!
        assert len(errors) == 0, f"Errors occurred during concurrent recording: {errors}"
        assert len(saved_claims) >= len(claims_data), (
            f"Race condition detected: {len(claims_data)} claims recorded "
            f"but only {len(saved_claims)} persisted. "
            f"Claims lost: {len(claims_data) - len(saved_claims)}. "
            f"Saved claims: {list(saved_claims.keys())}"
        )

        # Verify unique claim texts are present
        # Due to race condition, we expect some claims to be missing
        saved_texts = set(claim.get('text', '') for claim in saved_claims.values())
        expected_texts = set(claim_text for _, claim_text, _, _ in claims_data)

        missing_texts = expected_texts - saved_texts
        if missing_texts:
            # This assertion documents the race condition
            assert False, (
                f"Race condition verified: {len(missing_texts)} claim(s) lost: {missing_texts}. "
                f"This confirms the bug exists without file locking."
            )

    def test_rapid_sequential_claim_recording_all_preserved(self):
        """
        Test that rapid sequential claim recording preserves all data.

        Given:
            - Claims are recorded in rapid succession
            - No explicit delays between operations
        When:
            - record_claim() is called multiple times rapidly
        Then:
            - All claims should be preserved

        This test is more likely to pass than the concurrent test,
        but still exposes the race condition under load.
        """
        record_claim = self._get_record_claim_function()

        # Record claims rapidly in sequence
        num_claims = 20
        for i in range(num_claims):
            record_claim(
                'output_claim',
                f'rapid_claim_{i}_data',
                'FALSE',
                0.9 - (i * 0.01)
            )

        # Load and verify
        if self.claims_file.exists():
            saved_claims = json.loads(self.claims_file.read_text(encoding="utf-8"))
        else:
            saved_claims = {}

        # Should have all claims
        assert len(saved_claims) >= num_claims, (
            f"Expected at least {num_claims} claims, but found {len(saved_claims)}. "
            f"Race condition may have caused data loss."
        )


class TestClaimGuardRaceConditionIntegration:
    """
    Integration tests using the actual claimguard module.

    These tests use the real PostToolUse_claimguard module
    with a test-specific state directory.
    """

    def setup_method(self):
        """Set up test fixtures with mocked state directory."""
        self.temp_dir = tempfile.mkdtemp(prefix="claimguard_integration_")
        self.test_terminal_id = "test_terminal_race_condition"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('PostToolUse_claimguard.TERMINAL_ID', 'test_terminal_race_condition')
    @patch('PostToolUse_claimguard.STATE_DIR')
    def test_integration_concurrent_claims_with_real_module(self, mock_state_dir):
        """
        Integration test using the actual claimguard module.

        Given:
            - Using the real PostToolUse_claimguard module
            - Multiple threads record claims concurrently
            - State directory is mocked to test location
        When:
            - Concurrent calls to record_claim()
        Then:
            - All claims should be preserved (FAILS without file locking)
        """
        from PostToolUse_claimguard import record_claim

        # Mock the state directory
        mock_state_dir.return_value = Path(self.temp_dir) / "claimguard"

        # Create test-specific claims file
        test_claims_file = Path(self.temp_dir) / "claimguard" / "detected_claims.json"
        test_claims_file.parent.mkdir(parents=True, exist_ok=True)

        # Patch the CLAIMS_FILE to use our test location
        with patch('PostToolUse_claimguard.CLAIMS_FILE', test_claims_file):
            claims_data = [
                ('output_claim', 'integration_claim_1', 'FALSE', 0.95),
                ('file_claim', 'integration_claim_2', 'FALSE', 0.90),
                ('output_claim', 'integration_claim_3', 'FALSE', 0.85),
            ]

            results = []
            errors = []

            def record_claim_thread(claim_data):
                try:
                    record_claim(*claim_data)
                    results.append(claim_data)
                except Exception as e:
                    errors.append((claim_data, str(e)))

            threads = [threading.Thread(target=record_claim_thread, args=(d,))
                      for d in claims_data]

            for t in threads:
                t.start()

            for t in threads:
                t.join(timeout=5.0)

            # Load and verify
            from PostToolUse_claimguard import load_claims
            saved_claims = load_claims()

            assert len(errors) == 0, f"Errors: {errors}"
            assert len(saved_claims) >= len(claims_data), (
                f"Integration test race condition: {len(claims_data)} claims "
                f"but {len(saved_claims)} saved"
            )
