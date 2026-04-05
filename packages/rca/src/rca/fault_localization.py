"""Fault Localization - SBFL suspiciousness formulas.

This module implements Statistical-Based Fault Localization (SBFL) algorithms
for identifying suspicious code lines based on test coverage data.

Key formulas implemented:
- Ochiai: failed(e) / sqrt(total_failed * (failed(e) + passed(e)))
- Tarantula: (failed(e)/total_failed) / ((failed(e)/total_failed) + (passed(e)/total_passed))
- DStar: failed(e)^star / (passed(e) + (total_failed - failed(e)))
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CoverageData:
    """Coverage data for a single line of code.

    Attributes:
        file_path: Path to the source file.
        line_number: Line number in the source file.
        function_name: Name of the function containing this line (optional).
        executed_in_passing: Number of passing tests that executed this line.
        executed_in_failing: Number of failing tests that executed this line.
        total_passing: Total number of passing tests in the suite.
        total_failing: Total number of failing tests in the suite.
    """

    file_path: str
    line_number: int
    function_name: str | None = None
    executed_in_passing: int = 0
    executed_in_failing: int = 0
    total_passing: int = 0
    total_failing: int = 0


@dataclass
class SuspiciousnessScore:
    """Suspiciousness score for a single line of code.

    Attributes:
        file_path: Path to the source file.
        line_number: Line number in the source file.
        function_name: Name of the function containing this line (optional).
        score: Calculated suspiciousness score (higher is more suspicious).
        formula: Name of the formula used to calculate the score.
    """

    file_path: str
    line_number: int
    function_name: str | None
    score: float
    formula: str


def ochiai_score(cov: CoverageData) -> float:
    """Calculate Ochiai suspiciousness score.

    The Ochiai coefficient measures the similarity between the set of failing
    tests that execute this line and all failing tests.

    Formula: failed(e) / sqrt(total_failed * (failed(e) + passed(e)))

    Args:
        cov: Coverage data for a single line.

    Returns:
        Suspiciousness score between 0.0 and 1.0, where 1.0 indicates
        the line is executed in all failing tests and no passing tests.
        Returns 0.0 if there are no failing tests or division by zero occurs.

    Examples:
        >>> cov = CoverageData("test.py", 42, executed_in_passing=0,
        ...                    executed_in_failing=10, total_passing=20,
        ...                    total_failing=10)
        >>> ochiai_score(cov)
        1.0
    """
    if cov.total_failing == 0:
        return 0.0

    denominator = math.sqrt(
        cov.total_failing * (cov.executed_in_failing + cov.executed_in_passing)
    )
    if denominator == 0:
        return 0.0

    return cov.executed_in_failing / denominator


def tarantula_score(cov: CoverageData) -> float:
    """Calculate Tarantula suspiciousness score.

    Tarantula uses the ratio of failing tests that execute this line versus
    all tests that execute this line.

    Formula: (failed(e)/total_failed) / ((failed(e)/total_failed) + (passed(e)/total_passed))

    Args:
        cov: Coverage data for a single line.

    Returns:
        Suspiciousness score between 0.0 and 1.0, where 1.0 indicates
        the line is executed in all failing tests and no passing tests.
        Returns 0.0 if there are no failing or passing tests, or division by zero occurs.

    Examples:
        >>> cov = CoverageData("test.py", 42, executed_in_passing=0,
        ...                    executed_in_failing=10, total_passing=20,
        ...                    total_failing=10)
        >>> round(tarantula_score(cov), 6)
        1.0
    """
    if cov.total_failing == 0 or cov.total_passing == 0:
        return 0.0

    fail_ratio = cov.executed_in_failing / cov.total_failing
    pass_ratio = cov.executed_in_passing / cov.total_passing
    denominator = fail_ratio + pass_ratio

    if denominator == 0:
        return 0.0

    return fail_ratio / denominator


def dstar_score(cov: CoverageData, star: int = 2) -> float:
    """Calculate DStar suspiciousness score.

    DStar emphasizes lines executed in many failing tests with a configurable
    exponent parameter. Higher values of 'star' increase the emphasis on
    failing test executions.

    Formula: failed(e)^star / (passed(e) + (total_failed - failed(e)))

    Args:
        cov: Coverage data for a single line.
        star: Exponent for the failing test count (default: 2). Higher values
            increase the weight of failing test executions.

    Returns:
        Suspiciousness score as a non-negative float. May return float('inf')
        if the line is executed in all failing tests and no passing tests.
        Returns 0.0 for lines not executed in any failing tests.

    Examples:
        >>> cov = CoverageData("test.py", 42, executed_in_passing=0,
        ...                    executed_in_failing=10, total_passing=20,
        ...                    total_failing=10)
        >>> dstar_score(cov)
        inf
    """
    numerator = cov.executed_in_failing**star
    denominator = cov.executed_in_passing + (
        cov.total_failing - cov.executed_in_failing
    )

    if denominator == 0:
        return float("inf") if numerator > 0 else 0.0

    return numerator / denominator


def rank_suspicious_locations(
    coverage_data: list[CoverageData],
    formula: str = "ochiai",
) -> list[SuspiciousnessScore]:
    """Rank code locations by suspiciousness using SBFL formulas.

    Applies the specified suspiciousness formula to coverage data and returns
    results sorted by score in descending order (most suspicious first).

    Args:
        coverage_data: List of coverage data for code lines to analyze.
        formula: SBFL formula to use. Must be one of: "ochiai" (default),
            "tarantula", or "dstar". Unknown formulas default to "ochiai".

    Returns:
        List of suspiciousness scores sorted by score in descending order.
        Empty list if no coverage data provided.

    Examples:
        >>> coverage = [
        ...     CoverageData("test.py", 42, executed_in_passing=0,
        ...                  executed_in_failing=10, total_passing=20,
        ...                  total_failing=10),
        ... ]
        >>> results = rank_suspicious_locations(coverage, formula="ochiai")
        >>> len(results)
        1
        >>> results[0].score
        1.0
    """
    # Score function registry
    SCORE_FUNCTIONS: dict[str, Callable[[CoverageData], float]] = {
        "ochiai": ochiai_score,
        "tarantula": tarantula_score,
        "dstar": dstar_score,
    }

    # Validate and select scoring function
    score_func = SCORE_FUNCTIONS.get(formula, ochiai_score)
    actual_formula = formula if formula in SCORE_FUNCTIONS else "ochiai"

    # Calculate scores for all coverage data
    scores = [
        SuspiciousnessScore(
            file_path=cov.file_path,
            line_number=cov.line_number,
            function_name=cov.function_name,
            score=score_func(cov),
            formula=actual_formula,
        )
        for cov in coverage_data
    ]

    # Return sorted by score (highest suspicion first)
    return sorted(scores, key=lambda s: s.score, reverse=True)


def parse_coverage_json(
    coverage_path: str | Path,
    test_results: list[dict[str, Any]],
) -> list[CoverageData]:
    """Parse pytest-cov JSON report and test results into CoverageData.

    This function combines coverage information from pytest-cov with test
    execution results to create CoverageData objects suitable for SBFL analysis.

    Args:
        coverage_path: Path to coverage.json from pytest-cov (--cov-report=json).
        test_results: List of test result dictionaries with keys:
            - name: Test identifier (e.g., "test_module::test_func")
            - passed: Boolean indicating if test passed
            - covered_lines: Dict mapping file_path to list of executed line numbers

    Returns:
        List of CoverageData objects ready for SBFL scoring. Returns empty list
        if coverage file doesn't exist or no failing tests are present.

    Examples:
        >>> # After running: pytest --cov=src --cov-report=json tests/
        >>> test_results = [
        ...     {"name": "test_a", "passed": True,
        ...      "covered_lines": {"src/foo.py": [1, 2, 3]}},
        ...     {"name": "test_b", "passed": False,
        ...      "covered_lines": {"src/foo.py": [1, 2, 4]}},
        ... ]
        >>> coverage_data = parse_coverage_json("coverage.json", test_results)
        >>> scores = rank_suspicious_locations(coverage_data)
    """
    coverage_path = Path(coverage_path)
    if not coverage_path.exists():
        return []

    with open(coverage_path) as f:
        cov_report = json.load(f)

    # Count passing and failing tests
    total_passing = sum(1 for t in test_results if t.get("passed", False))
    total_failing = len(test_results) - total_passing

    # No faults to localize if all tests pass
    if total_failing == 0:
        return []

    # Initialize line statistics tracking
    line_stats: dict[tuple[str, int], dict[str, int]] = _initialize_line_stats(
        cov_report
    )

    # Aggregate test execution data by line
    _aggregate_test_coverage(line_stats, test_results)

    # Convert line stats to CoverageData objects
    return [
        CoverageData(
            file_path=file_path,
            line_number=line_num,
            executed_in_passing=stats["passing"],
            executed_in_failing=stats["failing"],
            total_passing=total_passing,
            total_failing=total_failing,
        )
        for (file_path, line_num), stats in line_stats.items()
    ]


def _initialize_line_stats(
    cov_report: dict[str, Any],
) -> dict[tuple[str, int], dict[str, int]]:
    """Initialize line statistics dictionary from coverage report.

    Args:
        cov_report: Coverage report dictionary from pytest-cov.

    Returns:
        Dictionary mapping (file_path, line_number) tuples to statistics
        dictionaries with 'passing' and 'failing' counters initialized to 0.
    """
    line_stats: dict[tuple[str, int], dict[str, int]] = {}

    files_data = cov_report.get("files", {})
    for file_path, file_info in files_data.items():
        executed_lines = file_info.get("executed_lines", [])
        for line_num in executed_lines:
            key = (file_path, line_num)
            if key not in line_stats:
                line_stats[key] = {"passing": 0, "failing": 0}

    return line_stats


def _aggregate_test_coverage(
    line_stats: dict[tuple[str, int], dict[str, int]],
    test_results: list[dict[str, Any]],
) -> None:
    """Aggregate test coverage data into line statistics.

    Updates line_stats in-place with execution counts from test results.

    Args:
        line_stats: Dictionary mapping (file_path, line_number) to statistics.
        test_results: List of test result dictionaries with coverage information.
    """
    for test in test_results:
        is_passing = test.get("passed", False)
        covered = test.get("covered_lines", {})

        for file_path, lines in covered.items():
            for line_num in lines:
                key = (file_path, line_num)
                if key not in line_stats:
                    line_stats[key] = {"passing": 0, "failing": 0}

                if is_passing:
                    line_stats[key]["passing"] += 1
                else:
                    line_stats[key]["failing"] += 1


def parse_pytest_json_report(
    report_path: str | Path,
) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    """Parse pytest-json-report output to extract test results.

    This function extracts test execution information from a pytest JSON report,
    which can be used as input to parse_coverage_json for SBFL analysis.

    Args:
        report_path: Path to .report.json file generated by pytest-json-report plugin.

    Returns:
        A tuple containing:
        - test_results: List of dictionaries with keys "name", "passed", and "covered_lines"
        - coverage_by_test: Empty dictionary (reserved for future per-test coverage support)

    Note:
        For full SBFL support, run pytest with:
        pytest --json-report --cov=src --cov-report=json --cov-context=test

        The covered_lines field will be empty unless combined with additional
        coverage context processing.

    Examples:
        >>> test_results, coverage = parse_pytest_json_report("report.json")
        >>> len(test_results) > 0
        True
    """
    report_path = Path(report_path)
    if not report_path.exists():
        return [], {}

    with open(report_path) as f:
        report = json.load(f)

    test_results = [
        {
            "name": test.get("nodeid", ""),
            "passed": test.get("outcome") == "passed",
            "covered_lines": {},
        }
        for test in report.get("tests", [])
    ]

    return test_results, {}
