#!/usr/bin/env python3
"""
Test: Epistemic Bindings Helper

TASK-003: Verify commitment extraction from RCA responses

Tests that:
1. Helper extracts all 8 required commitment sections from RCA responses
2. Normalization of claim targets and artifact paths works correctly
3. Time-scope labels are detected (current-state, transcript-time, inference)
4. Malformed responses are handled gracefully
5. Empty/whitespace sections are detected
6. Root cause tier/confidence extraction works

Acceptance Criteria:
- Helper successfully extracts commitments from RCA responses with proper normalization
- All 8 commitment types extracted: Symptom, Evidence, Executed Path, Alternative Hypothesis, Falsifier, Root Cause, Fix, Verification
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add hooks directory to path (ALWAYS insert at position 0)
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


# Sample RCA response for testing (based on debugRCA SKILL.md format)
SAMPLE_RCA_RESPONSE = """
### Symptom
User reports "file doesn't exist" error when running test suite.

### Evidence
- Read `src/main.py` shows FileNotFoundError at line 42 (current-state)
- Grep for `test_file.txt` found no results in codebase (current-state)
- Bash output shows test directory exists but file missing (current-state)

### Executed Path
pytest → test_runner.py → load_test_fixtures() → open('test_file.txt')

### Alternative Hypothesis
Maybe the file was deleted by a recent cleanup script.

### Falsifier
Git log shows test_file.txt was never committed (transcript-time). The cleanup script only removes files older than 7 days, but this file was created 2 days ago according to file system timestamps (inference).

### Root Cause
**Technical:** Test fixture references `test_file.txt` that was never added to version control (src/fixtures.py:15) (Tier 1, 95%)

### Fix
Add test_file.txt to git repository and update .gitignore to not exclude test fixtures.

### Verification
- [ ] Run pytest to confirm tests pass
- [ ] Verify git status shows test_file.txt as tracked
- [ ] Confirm no regression in other test fixtures
"""

# Sample RCA response with time-scope variations
SAMPLE_RCA_WITH_MIXED_SCOPES = """
### Symptom
Intermittent timeout errors in API calls.

### Evidence
- Read api_client.py shows 30s timeout (current-state)
- Grep found timeout configuration in 3 files (transcript-time)
- No retry logic detected in codebase (inference)

### Executed Path
api.py → api_client.call() → requests.get()

### Alternative Hypothesis
Network connectivity issue.

### Falsifier
Network logs show stable connection (current-state). Other API calls succeed (current-state).

### Root Cause
**Technical:** Missing retry logic for transient failures (api_client.py:42) (Tier 2, 80%)

### Fix
Add exponential backoff retry decorator to api_client.call().

### Verification
- [ ] Test with simulated network failures
- [ ] Monitor API success rate for 24 hours
- [ ] Confirm no timeout escalation
"""

# Sample malformed RCA response
SAMPLE_RCA_MALFORMED = """
### Symptom
Error in production.

### Alternative Hypothesis
Maybe a bug?

### Root Cause
**Technical:** Something broke (Tier 1, 50%)
"""


def test_extract_all_commitment_sections():
    """Test that all 8 commitment sections are extracted from complete RCA response."""
    from __lib.epistemic_bindings import extract_commitments

    commitments = extract_commitments(SAMPLE_RCA_RESPONSE)

    # Verify all 8 sections exist
    expected_sections = [
        "Symptom",
        "Evidence",
        "Executed Path",
        "Alternative Hypothesis",
        "Falsifier",
        "Root Cause",
        "Fix",
        "Verification",
    ]

    for section in expected_sections:
        assert section in commitments, f"Missing section: {section}"
        assert commitments[section], f"Section {section} is empty"

    # Verify content extraction
    assert "file doesn't exist" in commitments["Symptom"]
    assert "pytest" in commitments["Executed Path"]
    assert "Tier 1" in commitments["Root Cause"]
    assert "95%" in commitments["Root Cause"]


def test_extract_commitment_with_missing_sections():
    """Test that missing sections are handled gracefully."""
    from __lib.epistemic_bindings import extract_commitments

    commitments = extract_commitments(SAMPLE_RCA_MALFORMED)

    # Should only have the sections that exist
    assert "Symptom" in commitments
    assert "Alternative Hypothesis" in commitments
    assert "Root Cause" in commitments

    # Missing sections should not be present
    assert "Evidence" not in commitments
    assert "Executed Path" not in commitments
    assert "Fix" not in commitments


def test_detect_time_scope_labels():
    """Test that time-scope labels are detected correctly."""
    from __lib.epistemic_bindings import detect_time_scopes

    text = """
    - Read file shows current state (current-state)
    - Previous investigation found issue (transcript-time)
    - Likely a race condition (inference)
    """

    scopes = detect_time_scopes(text)

    assert "current-state" in scopes
    assert "transcript-time" in scopes
    assert "inference" in scopes


def test_normalize_artifact_paths():
    """Test that artifact paths are normalized correctly."""
    from __lib.epistemic_bindings import normalize_artifact_path

    # Windows-style paths
    assert normalize_artifact_path("P:\\project\\file.py") == "P:/project/file.py"
    assert normalize_artifact_path("C:/Users/test/file.py") == "C:/Users/test/file.py"

    # POSIX-style paths
    assert normalize_artifact_path("/home/user/file.py") == "/home/user/file.py"

    # Relative paths
    assert normalize_artifact_path("./src/file.py") == "src/file.py"
    assert normalize_artifact_path("../parent/file.py") == "../parent/file.py"


def test_extract_root_cause_tier_and_confidence():
    """Test that tier and confidence are extracted from Root Cause section."""
    from __lib.epistemic_bindings import extract_root_cause_details

    root_cause_text = "**Technical:** Test fixture references `test_file.txt` that was never added to version control (src/fixtures.py:15) (Tier 1, 95%)"

    details = extract_root_cause_details(root_cause_text)

    assert details["tier"] == 1
    assert details["confidence"] == 95
    assert "src/fixtures.py" in details["file_path"]
    assert "15" in details["line_number"]


def test_empty_section_detection():
    """Test that empty or whitespace-only sections are detected."""
    from __lib.epistemic_bindings import is_section_empty

    # Empty section
    assert is_section_empty("") is True
    assert is_section_empty("   \n\n  \t  ") is True

    # Non-empty section
    assert is_section_empty("Some content here") is False
    assert is_section_empty("  \n  Content exists  \n  ") is False


def test_extract_verification_checklist():
    """Test that verification checklist items are extracted."""
    from __lib.epistemic_bindings import extract_verification_items

    verification_text = """
- [ ] Run pytest to confirm tests pass
- [x] Verify git status shows test_file.txt as tracked
- [ ] Confirm no regression in other test fixtures
"""

    items = extract_verification_items(verification_text)

    assert len(items) == 3
    assert items[0]["text"] == "Run pytest to confirm tests pass"
    assert items[0]["checked"] is False
    assert items[1]["text"] == "Verify git status shows test_file.txt as tracked"
    assert items[1]["checked"] is True


def run_all_tests() -> int:
    """Run all tests when script is executed directly."""
    import traceback

    print("Running epistemic bindings test coverage...\n")

    tests = [
        ("Extract all commitment sections", test_extract_all_commitment_sections),
        ("Extract commitment with missing sections", test_extract_commitment_with_missing_sections),
        ("Detect time scope labels", test_detect_time_scope_labels),
        ("Normalize artifact paths", test_normalize_artifact_paths),
        ("Extract root cause tier and confidence", test_extract_root_cause_tier_and_confidence),
        ("Empty section detection", test_empty_section_detection),
        ("Extract verification checklist", test_extract_verification_checklist),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"Testing: {name}...", end=" ")
            test_func()
            print("✓ PASS")
            passed += 1
        except AssertionError as e:
            print("✗ FAIL")
            print(f"  Error: {e}")
            failed += 1
        except Exception:
            print("✗ ERROR")
            print(f"  {traceback.format_exc()}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
