#!/usr/bin/env python3
"""
Tests for Deep Lens Framework - 6-lens code review system.

Tests cover:
- State/Edge-Case Lens
- Identity/Invariants Lens
- I/O Validation Lens
- Concurrency Lens
- Errors/Logging Lens
- Tests/Coverage Lens
"""

from tiers.deep_lens_verifier import (
    ConcurrencyLens,
    DeepLensVerifier,
    ErrorsLens,
    IdentityInvariantsLens,
    IOLens,
    LensResult,
    StateEdgeCaseLens,
    TestsLens,
)


class TestStateEdgeCaseLens:
    """Test StateEdgeCaseLens for state management and edge cases."""

    def test_verify_detects_uninitialized_state(self):
        """Test that lens detects uninitialized state variables."""
        lens = StateEdgeCaseLens()
        code = """
def process(data):
    result = data['value'] * 2  # No check if 'value' exists
    return result
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("uninitialized" in f.lower() for f in result.findings)

    def test_verify_detects_missing_boundary_checks(self):
        """Test that lens detects missing boundary condition checks."""
        lens = StateEdgeCaseLens()
        code = """
def process_list(items):
    for i in range(len(items)):  # No empty check
        print(items[i])
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("boundary" in f.lower() or "empty" in f.lower() for f in result.findings)

    def test_verify_passes_with_defensive_code(self):
        """Test that lens passes code with proper state handling."""
        lens = StateEdgeCaseLens()
        code = """
def process(data):
    if 'value' not in data:
        return None
    if not data['value']:
        return None
    return data['value'] * 2
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "pass"


class TestIdentityInvariantsLens:
    """Test IdentityInvariantsLens for identity preservation."""

    def test_verify_detects_mutable_default_args(self):
        """Test that lens detects mutable default arguments."""
        lens = IdentityInvariantsLens()
        code = """
def process(items=[]):  # Mutable default
    items.append(1)
    return items
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("mutable" in f.lower() for f in result.findings)

    def test_verify_detects_missing_invariant_checks(self):
        """Test that lens detects missing invariant assertions."""
        lens = IdentityInvariantsLens()
        code = """
class Counter:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1  # No assertion
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("invariant" in f.lower() or "assert" in f.lower() for f in result.findings)

    def test_verify_passes_with_invariants(self):
        """Test that lens passes code with proper invariants."""
        lens = IdentityInvariantsLens()
        code = """
class Counter:
    def __init__(self):
        self.value = 0
        assert self.value >= 0

    def increment(self):
        self.value += 1
        assert self.value >= 0
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "pass"


class TestIOLens:
    """Test IOLens for input/output validation."""

    def test_verify_detects_missing_input_validation(self):
        """Test that lens detects missing input validation."""
        lens = IOLens()
        code = """
def process(filename):
    with open(filename) as f:  # No validation
        return f.read()
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("validation" in f.lower() for f in result.findings)

    def test_verify_detects_missing_output_sanitization(self):
        """Test that lens detects missing output sanitization."""
        lens = IOLens()
        code = """
def render_html(user_input):
    return f"<div>{user_input}</div>"  # No sanitization
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("sanitize" in f.lower() or "escape" in f.lower() for f in result.findings)

    def test_verify_passes_with_validation(self):
        """Test that lens passes code with proper I/O validation."""
        lens = IOLens()
        code = """
def process(filename):
    if not filename or not isinstance(filename, str):
        raise ValueError("Invalid filename")
    if not filename.endswith('.txt'):
        raise ValueError("Invalid file type")
    with open(filename) as f:
        return f.read()
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "pass"


class TestConcurrencyLens:
    """Test ConcurrencyLens for race conditions."""

    def test_verify_detects_missing_lock(self):
        """Test that lens detects missing lock on shared resource."""
        lens = ConcurrencyLens()
        code = """
counter = 0

def increment():
    global counter
    counter += 1  # No lock
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("lock" in f.lower() for f in result.findings)

    def test_verify_detects_toctou_races(self):
        """Test that lens detects time-of-check-to-time-of-use races."""
        lens = ConcurrencyLens()
        code = """
def process(filename):
    if os.path.exists(filename):  # Check
        with open(filename) as f:  # Use
            return f.read()  # Race!
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("race" in f.lower() or "toctou" in f.lower() for f in result.findings)

    def test_verify_passes_with_locks(self):
        """Test that lens passes code with proper concurrency controls."""
        lens = ConcurrencyLens()
        code = """
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    with lock:
        counter += 1
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "pass"


class TestErrorsLens:
    """Test ErrorsLens for error handling."""

    def test_verify_detects_missing_error_handling(self):
        """Test that lens detects missing error handling."""
        lens = ErrorsLens()
        code = """
def read_file(filename):
    with open(filename) as f:  # No try/except
        return f.read()
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("error" in f.lower() or "exception" in f.lower() for f in result.findings)

    def test_verify_detects_swallowed_exceptions(self):
        """Test that lens detects swallowed exceptions."""
        lens = ErrorsLens()
        code = """
def process():
    try:
        risky_operation()
    except:
        pass  # Swallowed!
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "fail"
        assert any("swallow" in f.lower() or "logging" in f.lower() for f in result.findings)

    def test_verify_passes_with_error_handling(self):
        """Test that lens passes code with proper error handling."""
        lens = ErrorsLens()
        code = """
import logging

def process():
    try:
        risky_operation()
    except ValueError as e:
        logging.error(f"Failed: {e}")
        raise
"""
        result = lens.verify(code, context={"file": "test.py"})
        assert result.status == "pass"


class TestTestsLens:
    """Test TestsLens for test coverage."""

    def test_verify_detects_low_coverage(self):
        """Test that lens detects low test coverage."""
        lens = TestsLens()
        code = """
# No tests for this function
def complex_logic(x, y, z):
    if x > 0:
        return y * z
    return x + y + z
"""
        # Mock coverage report
        context = {"file": "test.py", "coverage": {"percent_covered": 45.0}}
        result = lens.verify(code, context=context)
        assert result.status == "fail"
        assert any("coverage" in f.lower() for f in result.findings)

    def test_verify_detects_missing_edge_case_tests(self):
        """Test that lens detects missing edge case tests."""
        lens = TestsLens()
        code = """
def process(items):
    return items[0]  # No edge case tests
"""
        # Mock test file
        context = {
            "file": "test.py",
            "tests": """
def test_process_normal():
    assert process([1, 2]) == 1
""",
        }
        result = lens.verify(code, context=context)
        assert result.status == "fail"
        assert any("edge" in f.lower() for f in result.findings)

    def test_verify_passes_with_good_coverage(self):
        """Test that lens passes code with good coverage."""
        lens = TestsLens()
        code = """
def process(items):
    if items:
        return items[0]
    return None
"""
        context = {
            "file": "test.py",
            "coverage": {"percent_covered": 95.0},
            "tests": """
def test_process_normal():
    assert process([1, 2]) == 1

def test_process_empty():
    assert process([]) is None

def test_process_none():
    assert process(None) is None
""",
        }
        result = lens.verify(code, context=context)
        assert result.status == "pass"


class TestDeepLensVerifier:
    """Test DeepLensVerifier coordinator."""

    def test_verify_all_lenses(self):
        """Test that verifier runs all 6 lenses."""
        verifier = DeepLensVerifier()
        code = "def foo(): pass"
        context = {"file": "test.py"}

        result = verifier.verify(code, context)

        assert "state_edge_case" in result
        assert "identity_invariants" in result
        assert "io" in result
        assert "concurrency" in result
        assert "errors" in result
        assert "tests" in result

    def test_verify_aggregates_findings(self):
        """Test that verifier aggregates findings from all lenses."""
        verifier = DeepLensVerifier()
        # Code with multiple issues
        code = """
def process(data):
    result = data['value'] * 2  # Uninitialized
    return result
"""
        context = {"file": "test.py"}

        result = verifier.verify(code, context)

        # Should have findings from at least state_edge_case lens
        assert result["state_edge_case"].status == "fail"
        assert len(result["state_edge_case"].findings) > 0

    def test_verify_with_coverage_threshold(self):
        """Test coverage threshold enforcement."""
        verifier = DeepLensVerifier(coverage_threshold=80.0)
        code = "def foo(): pass"
        context = {
            "file": "test.py",
            "coverage": {"percent_covered": 75.0},  # Below threshold
        }

        result = verifier.verify(code, context)

        # Tests lens should fail due to low coverage
        assert result["tests"].status == "fail"

    def test_verify_returns_overall_status(self):
        """Test that verify returns overall status."""
        verifier = DeepLensVerifier()

        # Code with issues
        code = """
def process(data):
    return data['value']  # Uninitialized
"""
        context = {"file": "test.py"}

        result = verifier.verify(code, context)

        # Overall status should be fail (at least one lens failed)
        assert result["overall_status"] == "fail"

        # Clean code should pass
        clean_code = """
def process(data):
    if 'item' not in data:
        return None
    return data['item']
"""
        # Add coverage data to make TestsLens pass
        clean_context = {
            "file": "test.py",
            "coverage": {"percent_covered": 95.0},
            "tests": """
def test_process_normal():
    assert process({'item': 42}) == 42

def test_process_missing():
    assert process({}) is None

def test_process_empty():
    assert process({'item': ''}) == ''
""",
        }
        clean_result = verifier.verify(clean_code, clean_context)
        assert clean_result["overall_status"] == "pass"


class TestLensResult:
    """Test LensResult dataclass."""

    def test_lens_result_creation(self):
        """Test creating a LensResult."""
        result = LensResult(
            status="pass", lens_name="test_lens", findings=["All good"], severity="info"
        )
        assert result.status == "pass"
        assert result.lens_name == "test_lens"
        assert len(result.findings) == 1

    def test_lens_result_to_dict(self):
        """Test LensResult to_dict conversion."""
        result = LensResult(
            status="fail", lens_name="test_lens", findings=["Issue found"], severity="high"
        )
        result_dict = result.to_dict()

        assert result_dict["status"] == "fail"
        assert result_dict["lens_name"] == "test_lens"
        assert "findings" in result_dict
