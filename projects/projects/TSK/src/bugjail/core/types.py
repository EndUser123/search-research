"""
BugJail Type Definitions

Core type definitions for the BugJail system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class BugSeverity(Enum):
    """Severity levels for detected bugs."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class BugCategory(Enum):
    """Categories of bugs that can be detected."""

    NULL_POINTER = "null_pointer"
    RACE_CONDITION = "race_condition"
    LOGIC_ERROR = "logic_error"
    RESOURCE_LEAK = "resource_leak"
    MEMORY_LEAK = "memory_leak"
    CONCURRENT_ACCESS = "concurrent_access"
    DATA_INCONSISTENCY = "data_inconsistency"
    API_MISUSE = "api_misuse"
    DIVISION_BY_ZERO = "division_by_zero"
    ARRAY_BOUNDS = "array_bounds"
    TYPE_ERROR = "type_error"
    INFINITE_LOOP = "infinite_loop"
    DEAD_CODE = "dead_code"
    BUFFER_OVERFLOW = "buffer_overflow"
    UNINITIALIZED_VARIABLE = "uninitialized_variable"
    INTEGER_OVERFLOW = "integer_overflow"
    STRING_FORMAT = "string_format"


class VulnerabilityType(Enum):
    """OWASP vulnerability types."""

    A01_BROKEN_ACCESS_CONTROL = "broken_access_control"
    A02_CRYPTOGRAPHIC_FAILURES = "cryptographic_failures"
    A03_INJECTION = "injection"
    A04_INSECURE_DESIGN = "insecure_design"
    A05_SECURITY_MISCONFIGURATION = "security_misconfiguration"
    A06_VULNERABLE_COMPONENTS = "vulnerable_components"
    A07_IDENTIFICATION_AUTHENTICATION = "identification_authentication"
    A08_SOFTWARE_DATA_INTEGRITY = "software_data_integrity"
    A09_LOGGING_MONITORING = "logging_monitoring"
    A10_SERVER_SIDE_REQUEST_FORGERY = "server_side_request_forgery"


class ConstitutionalComplianceLevel(Enum):
    """Constitutional compliance validation levels."""

    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL_VIOLATION = "critical_violation"


@dataclass
class DetectionResult:
    """Result of a bug or vulnerability detection."""

    # Core identification
    id: str
    type: BugCategory
    severity: BugSeverity
    message: str
    description: str

    # Location information
    file_path: str
    line_number: int
    column_number: int = 0
    end_line_number: int | None = None
    end_column_number: int | None = None

    # Context
    code_snippet: str = ""
    function_name: str | None = None
    class_name: str | None = None
    module_name: str | None = None

    # Confidence and metadata
    confidence: float = 0.0
    rule_id: str | None = None
    rule_name: str | None = None
    tags: set[str] = field(default_factory=set)

    # Temporal data
    detected_at: datetime = field(default_factory=datetime.now)

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VulnerabilityResult(DetectionResult):
    """Extended detection result for vulnerabilities."""

    vulnerability_type: VulnerabilityType
    owasp_reference: str | None = None
    cwe_id: str | None = None
    cvss_score: float | None = None
    exploitability: str | None = None
    impact: str | None = None
    remediation_complexity: str | None = None

    # Compliance
    constitutional_compliance: ConstitutionalComplianceLevel = ConstitutionalComplianceLevel.COMPLIANT
    compliance_violations: list[str] = field(default_factory=list)


@dataclass
class FixRecommendation:
    """Actionable fix recommendation for a detected issue."""

    # Recommendation content
    title: str
    description: str
    code_fix: str | None = None
    explanation: str = ""

    # Fix metadata
    priority: BugSeverity = BugSeverity.MEDIUM
    effort_estimate: str | None = None  # e.g., "5 min", "2 hours", "1 day"
    automation_possible: bool = False
    automated_fix: str | None = None

    # Context
    before_example: str | None = None
    after_example: str | None = None

    # Additional resources
    references: list[str] = field(default_factory=list)
    learn_more_links: list[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """Comprehensive analysis report for bug detection."""

    # Report metadata
    id: str
    target_path: str
    analysis_type: str = "full_scan"
    generated_at: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0

    # Summary statistics
    total_issues: int = 0
    bugs_by_severity: dict[BugSeverity, int] = field(default_factory=dict)
    bugs_by_category: dict[BugCategory, int] = field(default_factory=dict)
    vulnerabilities_by_type: dict[VulnerabilityType, int] = field(default_factory=dict)

    # Detailed results
    bugs: list[DetectionResult] = field(default_factory=list)
    vulnerabilities: list[VulnerabilityResult] = field(default_factory=list)
    recommendations: list[FixRecommendation] = field(default_factory=list)

    # Files analyzed
    files_analyzed: list[str] = field(default_factory=list)
    files_with_issues: list[str] = field(default_factory=list)
    lines_analyzed: int = 0

    # Compliance summary
    constitutional_compliance: ConstitutionalComplianceLevel = ConstitutionalComplianceLevel.COMPLIANT
    compliance_summary: dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    analysis_metrics: dict[str, Any] = field(default_factory=dict)

    # Configuration used
    configuration: Optional['BugJailConfig'] = None


@dataclass
class BugJailConfig:
    """Configuration for BugJail detection system."""

    # Detection settings
    enable_bug_detection: bool = True
    enable_vulnerability_scanning: bool = True
    enable_constitutional_compliance: bool = True

    # Severity filters
    min_severity_level: BugSeverity = BugSeverity.LOW
    include_info_level: bool = False

    # File and language settings
    include_patterns: list[str] = field(default_factory=lambda: ["**/*.py", "**/*.js", "**/*.ts"])
    exclude_patterns: list[str] = field(default_factory=lambda: [
        "**/node_modules/**",
        "**/__pycache__/**",
        "**/.git/**",
        "**/venv/**",
        "**/env/**"
    ])
    supported_languages: set[str] = field(default_factory=lambda: {"python", "javascript", "typescript"})

    # Pattern libraries
    enable_owasp_patterns: bool = True
    enable_custom_patterns: bool = True
    custom_pattern_paths: list[str] = field(default_factory=list)

    # Analysis depth
    enable_data_flow_analysis: bool = True
    enable_control_flow_analysis: bool = True
    enable_interprocedural_analysis: bool = False  # Expensive
    max_analysis_depth: int = 10

    # Performance settings
    max_files_per_scan: int = 1000
    timeout_seconds: int = 300
    parallel_analysis: bool = True
    max_workers: int = 4

    # Integration settings
    integrate_with_exploration: bool = True
    enable_real_time_detection: bool = False  # For IDE integration

    # Reporting
    generate_recommendations: bool = True
    include_code_snippets: bool = True
    max_snippet_lines: int = 5

    # Security and compliance
    constitutional_framework_path: str | None = None
    security_policies_path: str | None = None
    compliance_standards: list[str] = field(default_factory=lambda: ["OWASP_TOP_10", "CSF_NIP"])

    # Caching
    enable_caching: bool = True
    cache_directory: str | None = None
    cache_ttl_hours: int = 24

    # Experimental features
    enable_ml_detection: bool = False
    enable_semantic_analysis: bool = False


@dataclass
class DetectionPattern:
    """Pattern definition for bug detection."""

    # Pattern identification
    id: str
    name: str
    category: BugCategory
    severity: BugSeverity

    # Pattern definition
    pattern: str  # Regex or AST pattern
    language: str
    pattern_type: str = "regex"  # regex, ast, semantic

    # Metadata
    description: str
    tags: set[str] = field(default_factory=set)
    references: list[str] = field(default_factory=list)

    # Configuration
    enabled: bool = True
    confidence_threshold: float = 0.5

    # OWASP mapping (for vulnerabilities)
    owasp_category: VulnerabilityType | None = None
    cwe_id: str | None = None


@dataclass
class ExplorationIntegration:
    """Integration point for exploration workflow."""

    # Integration metadata
    workflow_step: str  # e.g., "cwo12_step5", "pre_commit"
    trigger_event: str  # e.g., "file_change", "manual_scan"

    # Analysis configuration
    analysis_types: list[str] = field(default_factory=list)
    priority_files: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)

    # Callbacks
    on_detection_callback: str | None = None
    on_vulnerability_callback: str | None = None
    on_compliance_violation_callback: str | None = None
