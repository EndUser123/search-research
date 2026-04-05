"""
BugJail Detector Core

Main detection engine for bugs and vulnerabilities.
"""

import ast
import hashlib
import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from ..compliance.validator import ConstitutionalValidator
from ..patterns.library import PatternLibrary
from ..recommendations.engine import RecommendationEngine
from ..vulnerability.scanner import VulnerabilityScanner
from .types import (
    BugJailConfig,
    BugSeverity,
    DetectionPattern,
    DetectionResult,
    VulnerabilityResult,
)


class BugJailDetector:
    """
    Main BugJail detection engine.

    Coordinates bug detection, vulnerability scanning, and compliance validation
    with support for multiple analysis techniques and language support.
    """

    def __init__(self, config: BugJailConfig | None = None):
        """Initialize the BugJail detector."""
        self.config = config or BugJailConfig()
        self.pattern_library = PatternLibrary()
        self.vulnerability_scanner = VulnerabilityScanner()
        self.compliance_validator = ConstitutionalValidator()
        self.recommendation_engine = RecommendationEngine()

        # Detection state
        self._analysis_cache: dict[str, Any] = {}
        self._stats = {
            "files_analyzed": 0,
            "bugs_detected": 0,
            "vulnerabilities_found": 0,
            "compliance_violations": 0,
            "analysis_time": 0.0,
            "cache_hits": 0
        }

        # Initialize pattern sets
        self._load_patterns()

    def analyze_path(self, target_path: str | Path) -> 'AnalysisReport':
        """
        Analyze a file or directory for bugs and vulnerabilities.

        Args:
            target_path: Path to file or directory to analyze

        Returns:
            Comprehensive analysis report
        """
        from .types import AnalysisReport

        target_path = Path(target_path).resolve()
        start_time = time.time()

        # Initialize report
        report = AnalysisReport(
            id=str(uuid.uuid4()),
            target_path=str(target_path),
            configuration=self.config
        )

        # Collect files to analyze
        files_to_analyze = self._collect_files(target_path)
        report.files_analyzed = [str(f) for f in files_to_analyze]

        if not files_to_analyze:
            report.duration_seconds = time.time() - start_time
            return report

        # Analyze files
        all_bugs: list[DetectionResult] = []
        all_vulnerabilities: list[VulnerabilityResult] = []
        lines_analyzed = 0

        if self.config.parallel_analysis:
            # Parallel analysis
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_file = {
                    executor.submit(self._analyze_file, file_path): file_path
                    for file_path in files_to_analyze
                }

                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        file_results = future.result(timeout=self.config.timeout_seconds)
                        all_bugs.extend(file_results.get("bugs", []))
                        all_vulnerabilities.extend(file_results.get("vulnerabilities", []))
                        lines_analyzed += file_results.get("lines_analyzed", 0)
                        if file_results.get("bugs") or file_results.get("vulnerabilities"):
                            report.files_with_issues.append(str(file_path))
                    except Exception as e:
                        print(f"Error analyzing {file_path}: {e}")
        else:
            # Sequential analysis
            for file_path in files_to_analyze:
                try:
                    file_results = self._analyze_file(file_path)
                    all_bugs.extend(file_results.get("bugs", []))
                    all_vulnerabilities.extend(file_results.get("vulnerabilities", []))
                    lines_analyzed += file_results.get("lines_analyzed", 0)
                    if file_results.get("bugs") or file_results.get("vulnerabilities"):
                        report.files_with_issues.append(str(file_path))
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")

        # Filter results by severity
        all_bugs = self._filter_by_severity(all_bugs)
        all_vulnerabilities = self._filter_by_severity(all_vulnerabilities)

        # Generate recommendations
        recommendations = []
        if self.config.generate_recommendations:
            all_issues = all_bugs + all_vulnerabilities
            recommendations = self.recommendation_engine.generate_recommendations(all_issues)

        # Constitutional compliance validation
        if self.config.enable_constitutional_compliance:
            compliance_result = self.compliance_validator.validate_results(
                all_bugs, all_vulnerabilities
            )
            report.constitutional_compliance = compliance_result.compliance_level
            report.compliance_summary = compliance_result.summary

            # Add compliance violations to results
            for violation in compliance_result.violations:
                if hasattr(violation, 'vulnerability_type'):
                    all_vulnerabilities.append(violation)
                else:
                    all_bugs.append(violation)

        # Update statistics
        report.total_issues = len(all_bugs) + len(all_vulnerabilities)
        report.bugs = all_bugs
        report.vulnerabilities = all_vulnerabilities
        report.recommendations = recommendations
        report.lines_analyzed = lines_analyzed
        report.duration_seconds = time.time() - start_time

        # Count by category and severity
        for bug in all_bugs:
            report.bugs_by_severity[bug.severity] = report.bugs_by_severity.get(bug.severity, 0) + 1
            report.bugs_by_category[bug.type] = report.bugs_by_category.get(bug.type, 0) + 1

        for vuln in all_vulnerabilities:
            report.bugs_by_severity[vuln.severity] = report.bugs_by_severity.get(vuln.severity, 0) + 1
            report.vulnerabilities_by_type[vuln.vulnerability_type] = \
                report.vulnerabilities_by_type.get(vuln.vulnerability_type, 0) + 1

        # Update detector stats
        self._stats["files_analyzed"] += len(files_to_analyze)
        self._stats["bugs_detected"] += len(all_bugs)
        self._stats["vulnerabilities_found"] += len(all_vulnerabilities)
        self._stats["analysis_time"] += report.duration_seconds

        return report

    def _analyze_file(self, file_path: Path) -> dict[str, Any]:
        """Analyze a single file for bugs and vulnerabilities."""
        file_path = Path(file_path)
        language = self._detect_language(file_path)

        # Skip unsupported languages
        if language not in self.config.supported_languages:
            return {"bugs": [], "vulnerabilities": [], "lines_analyzed": 0}

        # Check cache
        cache_key = self._get_cache_key(file_path)
        if self.config.enable_caching and cache_key in self._analysis_cache:
            self._stats["cache_hits"] += 1
            return self._analysis_cache[cache_key]

        # Read file content
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding='latin-1') as f:
                content = f.read()

        lines = content.splitlines()
        line_count = len(lines)

        results = {
            "bugs": [],
            "vulnerabilities": [],
            "lines_analyzed": line_count
        }

        # Bug detection
        if self.config.enable_bug_detection:
            bugs = self._detect_bugs(content, language, file_path, lines)
            results["bugs"] = bugs

        # Vulnerability scanning
        if self.config.enable_vulnerability_scanning:
            vulnerabilities = self._scan_vulnerabilities(content, language, file_path, lines)
            results["vulnerabilities"] = vulnerabilities

        # Cache results
        if self.config.enable_caching:
            self._analysis_cache[cache_key] = results

        return results

    def _detect_bugs(self, content: str, language: str, file_path: Path, lines: list[str]) -> list[DetectionResult]:
        """Detect bugs in file content."""
        bugs = []

        # Get patterns for language
        patterns = self.pattern_library.get_patterns_for_language(language)

        for pattern in patterns:
            if not pattern.enabled:
                continue

            # Pattern-based detection
            if pattern.pattern_type == "regex":
                regex_bugs = self._detect_with_regex(pattern, content, file_path, lines)
                bugs.extend(regex_bugs)
            elif pattern.pattern_type == "ast" and language == "python":
                ast_bugs = self._detect_with_ast(pattern, content, file_path)
                bugs.extend(ast_bugs)

        # Data flow analysis (if enabled)
        if self.config.enable_data_flow_analysis and language == "python":
            data_flow_bugs = self._detect_data_flow_issues(content, file_path)
            bugs.extend(data_flow_bugs)

        return bugs

    def _scan_vulnerabilities(self, content: str, language: str, file_path: Path, lines: list[str]) -> list[VulnerabilityResult]:
        """Scan for security vulnerabilities."""
        if not self.config.enable_owasp_patterns:
            return []

        return self.vulnerability_scanner.scan_file(content, language, file_path, lines)

    def _detect_with_regex(self, pattern: DetectionPattern, content: str, file_path: Path, lines: list[str]) -> list[DetectionResult]:
        """Detect bugs using regex patterns."""
        bugs = []

        try:
            regex = re.compile(pattern.pattern, re.MULTILINE | re.DOTALL)
            for match in regex.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                col_num = match.start() - content.rfind('\n', 0, match.start()) - 1

                # Get code snippet
                snippet_lines = max(0, line_num - 2), min(len(lines), line_num + 2)
                snippet = '\n'.join(lines[snippet_lines[0]:snippet_lines[1]])

                bug = DetectionResult(
                    id=str(uuid.uuid4()),
                    type=pattern.category,
                    severity=pattern.severity,
                    message=pattern.description,
                    description=f"Detected {pattern.name} at line {line_num}",
                    file_path=str(file_path),
                    line_number=line_num,
                    column_number=col_num,
                    code_snippet=snippet,
                    rule_id=pattern.id,
                    rule_name=pattern.name,
                    tags=pattern.tags,
                    confidence=pattern.confidence_threshold,
                    metadata={
                        "pattern_match": match.group(0),
                        "language": pattern.language
                    }
                )
                bugs.append(bug)

        except re.error as e:
            print(f"Invalid regex pattern {pattern.id}: {e}")

        return bugs

    def _detect_with_ast(self, pattern: DetectionPattern, content: str, file_path: Path) -> list[DetectionResult]:
        """Detect bugs using AST analysis."""
        bugs = []

        try:
            tree = ast.parse(content)
            ast_visitor = BugASTVisitor(pattern, file_path)
            ast_visitor.visit(tree)
            bugs.extend(ast_visitor.bugs)
        except SyntaxError:
            # Skip files with syntax errors
            pass

        return bugs

    def _detect_data_flow_issues(self, content: str, file_path: Path) -> list[DetectionResult]:
        """Detect data flow issues (simplified implementation)."""
        # This would be a more sophisticated data flow analysis
        # For now, return empty list
        return []

    def _collect_files(self, target_path: Path) -> list[Path]:
        """Collect files to analyze based on configuration."""
        files = []

        if target_path.is_file():
            if self._should_include_file(target_path):
                files.append(target_path)
        else:
            for file_path in target_path.rglob('*'):
                if file_path.is_file() and self._should_include_file(file_path):
                    files.append(file_path)

        # Limit files per scan
        if len(files) > self.config.max_files_per_scan:
            files = files[:self.config.max_files_per_scan]

        return files

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included in analysis."""
        file_str = str(file_path)

        # Check exclude patterns
        for exclude_pattern in self.config.exclude_patterns:
            if file_path.match(exclude_pattern):
                return False

        # Check include patterns
        for include_pattern in self.config.include_patterns:
            if file_path.match(include_pattern):
                return True

        return False

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()

        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift'
        }

        return language_map.get(suffix, 'unknown')

    def _filter_by_severity(self, results: list[DetectionResult | VulnerabilityResult]) -> list[DetectionResult | VulnerabilityResult]:
        """Filter results by minimum severity level."""
        if not self.config.include_info_level and self.config.min_severity_level == BugSeverity.LOW:
            # Exclude INFO level
            return [r for r in results if r.severity != BugSeverity.INFO]

        # Filter by minimum severity
        severity_order = {
            BugSeverity.INFO: 0,
            BugSeverity.LOW: 1,
            BugSeverity.MEDIUM: 2,
            BugSeverity.HIGH: 3,
            BugSeverity.CRITICAL: 4
        }

        min_level = severity_order.get(self.config.min_severity_level, 0)
        return [r for r in results if severity_order.get(r.severity, 0) >= min_level]

    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key for file analysis."""
        try:
            stat = file_path.stat()
            file_hash = hashlib.md5(f"{file_path}_{stat.st_mtime}_{stat.st_size}".encode()).hexdigest()
            return f"analysis_{file_hash}"
        except OSError:
            # Fallback to path-based key
            return f"analysis_{hash(str(file_path))}"

    def _load_patterns(self):
        """Load detection patterns."""
        # Load built-in patterns
        self.pattern_library.load_builtin_patterns()

        # Load custom patterns if specified
        if self.config.custom_pattern_paths:
            for pattern_path in self.config.custom_pattern_paths:
                if os.path.exists(pattern_path):
                    self.pattern_library.load_patterns_from_file(pattern_path)

    def get_statistics(self) -> dict[str, Any]:
        """Get detection statistics."""
        return self._stats.copy()

    def clear_cache(self):
        """Clear analysis cache."""
        self._analysis_cache.clear()

    def reset_statistics(self):
        """Reset detection statistics."""
        self._stats = {
            "files_analyzed": 0,
            "bugs_detected": 0,
            "vulnerabilities_found": 0,
            "compliance_violations": 0,
            "analysis_time": 0.0,
            "cache_hits": 0
        }


class BugASTVisitor(ast.NodeVisitor):
    """AST visitor for bug detection."""

    def __init__(self, pattern: DetectionPattern, file_path: Path):
        self.pattern = pattern
        self.file_path = file_path
        self.bugs: list[DetectionResult] = []

    def visit(self, node):
        """Visit AST node and check for pattern matches."""
        # This is a simplified implementation
        # In practice, you'd have specific node type checks based on pattern

        if hasattr(node, 'lineno'):
            # Create detection result for matching node
            bug = DetectionResult(
                id=str(uuid.uuid4()),
                type=self.pattern.category,
                severity=self.pattern.severity,
                message=self.pattern.description,
                description=f"AST-based detection of {self.pattern.name}",
                file_path=str(self.file_path),
                line_number=node.lineno,
                column_number=getattr(node, 'col_offset', 0),
                rule_id=self.pattern.id,
                rule_name=self.pattern.name,
                confidence=self.pattern.confidence_threshold,
                metadata={
                    "ast_type": type(node).__name__,
                    "language": "python"
                }
            )
            self.bugs.append(bug)

        # Continue traversal
        super().generic_visit(node)
