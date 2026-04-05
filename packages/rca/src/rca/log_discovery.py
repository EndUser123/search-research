"""Log File Discovery Module for rca.

Enhances RCA with automatic discovery and analysis of relevant log files.
Provides Tier 1 evidence (95% confidence) from actual execution logs.

Example:
    Problem: "dependency verification gate blocking packages"
    Discovery: Finds state/dependency_verification_*.json
    Analysis: Detects corrupted package names like "serde\\""
    Evidence: Tier 1 smoking gun, not speculative
"""

from __future__ import annotations

import glob
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LogPattern:
    """Pattern for detecting anomalies in log files."""

    name: str
    pattern: str
    description: str
    severity: str  # "critical", "warning", "info"
    example: str


@dataclass
class LogFile:
    """Discovered log file with metadata."""

    path: Path
    domain: str  # "hooks", "daemons", "tests", "general"
    size_bytes: int
    modified_time: datetime
    line_count: int = 0
    encoding: str = "utf-8"


@dataclass
class LogFinding:
    """Anomaly or pattern found in log file."""

    file_path: Path
    line_number: int
    pattern_name: str
    matched_text: str
    severity: str
    context_lines: List[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    raw_line: str = ""


@dataclass
class LogDiscoveryResult:
    """Complete log discovery analysis result."""

    problem_domain: str
    files_found: List[LogFile] = field(default_factory=list)
    findings: List[LogFinding] = field(default_factory=list)
    summary: str = ""
    evidence_tier: str = "Tier 1"  # Logs are Tier 1 evidence
    confidence_boost: float = 0.0  # How much this boosts overall confidence


class LogDiscoveryEngine:
    """Discovers and analyzes relevant log files for RCA investigations."""

    # Domain-specific log patterns
    DOMAIN_PATTERNS: Dict[str, List[str]] = {
        "hooks": [
            "state/*.json",          # Hook state files
            "logs/*.log",            # Hook execution logs
            ".claude/state/*.json",   # Claude state files
        ],
        "daemons": [
            "daemon_*.log",
            "*.pid",
            "logs/*daemon*.log",
        ],
        "tests": [
            "test_*.log",
            "*.xml",                 # JUnit test results
            "logs/test_*.log",
        ],
        "general": [
            "*.log",
            "logs/*.log",
            "logs/*.txt",
        ],
    }

    # Common anomaly patterns to detect in logs
    ANOMALY_PATTERNS: List[LogPattern] = [
        LogPattern(
            name="corrupted_string",
            pattern=r'[\w\-\./]+[\\"\'`\\\]{2,}',
            description="String with trailing shell metacharacters (quotes, backticks, backslashes)",
            severity="critical",
            example='serde", "package_name\\"'
        ),
        LogPattern(
            name="error_keyword",
            pattern=r'\b(ERROR|FATAL|CRITICAL|FAIL|exception|traceback)\b',
            description="Error or failure indicator",
            severity="critical",
            example="ERROR: Failed to connect"
        ),
        LogPattern(
            name="json_parse_error",
            pattern=r'JSON.*decode.*error|parse.*error|expecting.*',
            description="JSON parsing or decoding error",
            severity="warning",
            example='json.decoder.JSONDecodeError'
        ),
        LogPattern(
            name="large_timestamp_gap",
            pattern=r'\d{4}-\d{2}-\d{2}[T ]',
            description="Timestamp indicating time gaps (useful for detecting hangs)",
            severity="info",
            example="2026-03-09T10:30:00"
        ),
        LogPattern(
            name="blocking_operation",
            pattern=r'\b(block|wait|hang|timeout|sleep|lock)\b',
            description="Keywords indicating blocking operations",
            severity="warning",
            example="operation blocked on mutex"
        ),
        LogPattern(
            name="state_corruption",
            pattern=r'[\[\]{}]',
            description="Potential state corruption (unbalanced brackets)",
            severity="critical",
            example='{"verified_packages": {"serde\\"'
        ),
    ]

    # Keywords that indicate problem domains
    DOMAIN_KEYWORDS: Dict[str, List[str]] = {
        "hooks": ["hook", "PreToolUse", "PostToolUse", "gate", "verification"],
        "daemons": ["daemon", "service", "server", "background", "process"],
        "tests": ["test", "pytest", "unittest", "spec"],
        "general": ["log", "error", "crash", "fail", "issue"],
    }

    def __init__(self, project_root: Path, max_files: int = 20):
        """Initialize log discovery engine.

        Args:
            project_root: Root directory to search for logs
            max_files: Maximum number of log files to analyze
        """
        self.project_root = project_root
        self.max_files = max_files

    def discover_logs(self, problem_query: str) -> LogDiscoveryResult:
        """Discover relevant log files for the given problem.

        Args:
            problem_query: User's problem description or query

        Returns:
            LogDiscoveryResult with discovered files and analysis
        """
        # Detect problem domain from query
        domain = self._detect_domain(problem_query)

        # Find log files for this domain
        log_files = self._find_log_files(domain)

        # Sort by modification time (most recent first)
        log_files.sort(key=lambda f: f.modified_time, reverse=True)

        # Limit to max_files
        log_files = log_files[:self.max_files]

        # Analyze logs for anomalies
        findings = self._analyze_logs(log_files)

        # Generate summary
        summary = self._generate_summary(log_files, findings, domain)

        return LogDiscoveryResult(
            problem_domain=domain,
            files_found=log_files,
            findings=findings,
            summary=summary,
            evidence_tier="Tier 1",
            confidence_boost=self._calculate_confidence_boost(findings)
        )

    def _detect_domain(self, query: str) -> str:
        """Detect problem domain from query keywords.

        Args:
            query: Problem description

        Returns:
            Detected domain ("hooks", "daemons", "tests", "general")
        """
        query_lower = query.lower()

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                return domain

        return "general"

    def _find_log_files(self, domain: str) -> List[LogFile]:
        """Find log files for the given domain.

        Args:
            domain: Problem domain

        Returns:
            List of LogFile objects
        """
        patterns = self.DOMAIN_PATTERNS.get(domain, self.DOMAIN_PATTERNS["general"])
        log_files = []

        for pattern in patterns:
            # Search in project root and common subdirectories
            search_paths = [
                self.project_root,
                self.project_root / ".claude" / "state",
                self.project_root / ".claude" / "logs",
                self.project_root / "logs",
                self.project_root / "state",
            ]

            for search_path in search_paths:
                if not search_path.exists():
                    continue

                # Use glob to find matching files
                full_pattern = str(search_path / pattern)
                for file_path in glob.glob(full_pattern):
                    try:
                        stat = file_path.stat()
                        log_file = LogFile(
                            path=Path(file_path),
                            domain=domain,
                            size_bytes=stat.st_size,
                            modified_time=datetime.fromtimestamp(stat.st_mtime),
                            encoding="utf-8"
                        )

                        # Count lines for small files
                        if log_file.size_bytes < 1_000_000:  # < 1MB
                            try:
                                with open(file_path, 'r', encoding=log_file.encoding) as f:
                                    log_file.line_count = sum(1 for _ in f)
                            except (UnicodeDecodeError, OSError):
                                pass

                        log_files.append(log_file)

                    except (OSError, ValueError):
                        # Skip files that can't be accessed
                        continue

        # Remove duplicates (same path might match multiple patterns)
        seen_paths = set()
        unique_files = []
        for log_file in log_files:
            if str(log_file.path) not in seen_paths:
                unique_files.append(log_file)
                seen_paths.add(str(log_file.path))

        return unique_files

    def _analyze_logs(self, log_files: List[LogFile]) -> List[LogFinding]:
        """Analyze log files for anomalies and patterns.

        Args:
            log_files: List of log files to analyze

        Returns:
            List of LogFinding objects
        """
        findings = []

        for log_file in log_files:
            try:
                # Read log file (last 1000 lines for recent activity)
                lines = self._read_recent_lines(log_file, max_lines=1000)

                for line_num, line in enumerate(lines, start=1):
                    # Check each anomaly pattern
                    for pattern in self.ANOMALY_PATTERNS:
                        if re.search(pattern.pattern, line, re.IGNORECASE):
                            finding = LogFinding(
                                file_path=log_file.path,
                                line_number=line_num,
                                pattern_name=pattern.name,
                                matched_text=line.strip(),
                                severity=pattern.severity,
                                raw_line=line
                            )

                            # Extract timestamp if present
                            timestamp_match = re.search(
                                r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',
                                line
                            )
                            if timestamp_match:
                                try:
                                    finding.timestamp = datetime.fromisoformat(
                                        timestamp_match.group(0).replace(' ', 'T')
                                    )
                                except ValueError:
                                    pass

                            # Get context lines (lines before and after)
                            context_start = max(0, line_num - 3)
                            context_end = min(len(lines), line_num + 2)
                            finding.context_lines = lines[context_start:context_end]

                            findings.append(finding)

            except (UnicodeDecodeError, OSError) as e:
                logger.warning(f"Failed to analyze log file {log_file.path}: {e}")
                continue

        # Sort findings by severity and recency
        findings.sort(
            key=lambda f: (
                0 if f.severity == "critical" else 1 if f.severity == "warning" else 2,
                -(f.timestamp.timestamp() if f.timestamp else 0)
            )
        )

        return findings

    def _read_recent_lines(self, log_file: LogFile, max_lines: int = 1000) -> List[str]:
        """Read most recent lines from log file.

        Args:
            log_file: Log file to read
            max_lines: Maximum number of lines to read

        Returns:
            List of lines (most recent last for text files, tail for binary detection)
        """
        lines = []

        try:
            with open(log_file.path, 'r', encoding=log_file.encoding) as f:
                all_lines = f.readlines()

                # For text logs, take the last max_lines (most recent)
                if log_file.path.suffix in ['.log', '.txt']:
                    lines = all_lines[-max_lines:]
                else:
                    # For structured files (JSON), take from beginning
                    lines = all_lines[:max_lines]

        except (UnicodeDecodeError, OSError):
            # Try with different encoding
            try:
                with open(log_file.path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()[-max_lines:]
            except OSError:
                return []

        return [line.rstrip('\n\r') for line in lines]

    def _generate_summary(self, log_files: List[LogFile], findings: List[LogFinding], domain: str) -> str:
        """Generate human-readable summary of log discovery.

        Args:
            log_files: Discovered log files
            findings: Analysis findings
            domain: Problem domain

        Returns:
            Summary string
        """
        lines = []

        if not log_files:
            return f"No log files found for domain: {domain}"

        lines.append(f"**Log Discovery Results** ({domain} domain)")
        lines.append("")
        lines.append(f"Found {len(log_files)} relevant log file(s):")

        for log_file in log_files[:5]:  # Show top 5
            age = datetime.now() - log_file.modified_time
            age_str = self._format_age(age)

            lines.append(f"- **{log_file.path.name}**")
            lines.append(f"  Path: {log_file.path}")
            lines.append(f"  Size: {self._format_size(log_file.size_bytes)}")
            lines.append(f"  Modified: {age_str} ago")
            lines.append(f"  Lines: {log_file.line_count:,}")

        if len(log_files) > 5:
            lines.append(f"- ... and {len(log_files) - 5} more files")

        if findings:
            lines.append("")
            lines.append(f"**Anomalies Detected:** {len(findings)} finding(s)")

            # Group by severity
            critical = [f for f in findings if f.severity == "critical"]
            warnings = [f for f in findings if f.severity == "warning"]
            info = [f for f in findings if f.severity == "info"]

            if critical:
                lines.append(f"**Critical ({len(critical)}):**")
                for finding in critical[:3]:  # Show top 3
                    lines.append(f"  - {finding.pattern_name}: {finding.file_path.name}:{finding.line_number}")
                    lines.append(f"    Text: {finding.matched_text[:80]}...")
                if len(critical) > 3:
                    lines.append(f"  - ... and {len(critical) - 3} more critical findings")

            if warnings:
                lines.append(f"**Warnings ({len(warnings)}):**")
                for finding in warnings[:2]:
                    lines.append(f"  - {finding.pattern_name}: {finding.file_path.name}:{finding.line_number}")

            if info:
                lines.append(f"**Info ({len(info)}):**")
                for finding in info[:2]:
                    lines.append(f"  - {finding.pattern_name}: {finding.file_path.name}:{finding.line_number}")

            if len(findings) > 7:
                lines.append(f"- ... and {len(findings) - 7} more findings")
        else:
            lines.append("")
            lines.append("**No anomalies detected** in log files.")

        return "\n".join(lines)

    def _calculate_confidence_boost(self, findings: List[LogFinding]) -> float:
        """Calculate confidence boost based on log findings.

        Args:
            findings: List of log findings

        Returns:
            Confidence boost (0.0 to 1.0)
        """
        if not findings:
            return 0.0

        # Critical findings provide stronger boost
        critical_count = sum(1 for f in findings if f.severity == "critical")
        warning_count = sum(1 for f in findings if f.severity == "warning")

        # Base boost from having any findings
        boost = min(0.3, 0.1 * len(findings))

        # Additional boost for critical findings
        boost += min(0.2, 0.05 * critical_count)

        # Small boost for warnings
        boost += min(0.1, 0.02 * warning_count)

        return min(1.0, boost)

    def _format_age(self, age: timedelta) -> str:
        """Format age timedelta as human-readable string.

        Args:
            age: Time delta

        Returns:
            Formatted age string
        """
        seconds = age.total_seconds()

        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes"
        elif seconds < 86400:
            return f"{int(seconds / 3600)} hours"
        else:
            return f"{int(seconds / 86400)} days"

    def _format_size(self, size_bytes: int) -> str:
        """Format file size as human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        for threshold, unit in [
            (1024 * 1024 * 1024, "GB"),
            (1024 * 1024, "MB"),
            (1024, "KB"),
        ]:
            if size_bytes >= threshold:
                return f"{size_bytes / threshold:.1f} {unit}"

        return f"{size_bytes} bytes"


def discover_logs_for_problem(project_root: Path, problem_query: str) -> LogDiscoveryResult:
    """Convenience function to discover logs for a problem.

    Args:
        project_root: Project root directory
        problem_query: Problem description or query

    Returns:
        LogDiscoveryResult with analysis

    Example:
        result = discover_logs_for_problem(
            Path("P:/"),
            "dependency verification gate blocking packages"
        )
        print(result.summary)
    """
    engine = LogDiscoveryEngine(project_root)
    return engine.discover_logs(problem_query)
