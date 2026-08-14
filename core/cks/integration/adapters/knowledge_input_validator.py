import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .cks_constitutional_validator import CKSConstitutionalValidator

"""CKS Input Validation Framework.

Comprehensive input validation for CKS commands (/cks, /query, /learn).
Ensures security, constitutional compliance, and proper parameter handling.

Security Features:
- SQL injection prevention
- Command injection prevention
- Parameter bounds checking
- Input sanitization
- Rate limiting
- Constitutional compliance validation

Constitutional Compliance:
- Evidence-based validation
- Non-catastrophic language enforcement
- Solo developer optimization
- MCSVP compliance for multi-component operations
"""


logger = logging.getLogger(__name__)


class CKSCommand(Enum):
    """CKS command types."""

    CKS = "cks"
    QUERY = "query"
    LEARN = "learn"


class ValidationLevel(Enum):
    """Validation severity levels."""

    NOTE = "note"
    CONCERN = "concern"
    ISSUE = "issue"
    VIOLATION = "violation"


@dataclass
class ValidationResult:
    """Result of input validation."""

    is_valid: bool
    command: CKSCommand
    validation_level: ValidationLevel
    issues: list[str]
    recommendations: list[str]
    sanitized_parameters: dict[str, Any]
    evidence: dict[str, Any]
    constitutional_compliance: dict[str, Any] | None = None


class CKSInputValidator:
    """Comprehensive input validation framework for CKS commands."""

    def __init__(self) -> None:
        """Initialize CKS input validator."""
        self.logger = logging.getLogger(__name__)
        self.constitutional_validator = CKSConstitutionalValidator()

        # Security patterns
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"])",
            r"(;)",
            r"(--)",
            r"(/\*.*\*/)",
            r"(\bxp_cmdshell\b)",
            r"(\bsp_oacreate\b)",
        ]

        self.command_injection_patterns = [
            r"(\$\(.*\))",
            r"(`.*`)",
            r"(\|\|)",
            r"(&&)",
            r"(;)",
            r"(>\s*/dev/)",
            r"(>\s*/tmp/)",
            r"(>\s*/var/)",
        ]

        # Parameter bounds
        self.parameter_bounds = {
            "max_query_length": 1000,
            "max_title_length": 200,
            "max_content_length": 50000,
            "max_results_limit": 100,
            "max_tags_count": 20,
            "max_file_size_mb": 100,
            "max_concurrent_requests": 10,
        }

        # Rate limiting (simple in-memory tracking)
        self.request_history: dict[str, list[datetime]] = {}

        self.logger.info(
            "CKSInputValidator initialized with security and constitutional compliance",
        )

    def validate_command_input(
        self,
        command: str,
        parameters: dict[str, Any],
        user_context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validate input for any CKS command.

        Args:
        ----
            command: CKS command type (/cks, /query, /learn)
            parameters: Command parameters to validate
            user_context: Optional user context for rate limiting

        Returns:
        -------
            ValidationResult with comprehensive validation details

        """
        try:
            command_enum = CKSCommand(command.lower().lstrip("/"))
        except ValueError:
            return ValidationResult(
                is_valid=False,
                command=CKSCommand.CKS,  # Default
                validation_level=ValidationLevel.VIOLATION,
                issues=[f"Unknown command: {command}"],
                recommendations=["Use /cks, /query, or /learn"],
                sanitized_parameters={},
                evidence={"validation_timestamp": datetime.now().isoformat()},
            )

        # Rate limiting check
        if not self._check_rate_limit(user_context):
            return ValidationResult(
                is_valid=False,
                command=command_enum,
                validation_level=ValidationLevel.ISSUE,
                issues=["Rate limit exceeded"],
                recommendations=["Wait before making another request"],
                sanitized_parameters={},
                evidence={
                    "rate_limited": True,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        # Command-specific validation
        if command_enum == CKSCommand.CKS:
            return self._validate_cks_input(parameters, user_context)
        if command_enum == CKSCommand.QUERY:
            return self._validate_query_input(parameters, user_context)
        if command_enum == CKSCommand.LEARN:
            return self._validate_learn_input(parameters, user_context)
        return None

    def _validate_cks_input(
        self,
        parameters: dict[str, Any],
        user_context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validate /cks command input."""
        issues = []
        recommendations = []
        sanitized = {}

        # Validate operation type
        operation = parameters.get("operation", "").strip()
        if not operation:
            issues.append("Missing operation parameter")
            recommendations.append(
                "Specify operation: search, learn, integrate, status",
            )
        elif operation not in ["search", "learn", "integrate", "status", "analyze"]:
            issues.append(f"Invalid operation: {operation}")
            recommendations.append(
                "Valid operations: search, learn, integrate, status, analyze",
            )
        else:
            sanitized["operation"] = operation

        # Validate query parameters for search operations
        if operation == "search":
            query = parameters.get("query", "").strip()
            if not query:
                issues.append("Missing query for search operation")
                recommendations.append("Provide search query")
            else:
                # Security and bounds validation
                query_validation = self._validate_text_parameter(
                    query,
                    "query",
                    self.parameter_bounds["max_query_length"],
                )
                issues.extend(query_validation["issues"])
                recommendations.extend(query_validation["recommendations"])
                sanitized["query"] = query_validation["sanitized"]

        # Validate integration parameters
        if operation == "integrate":
            integration_type = parameters.get("integration_type", "").strip()
            if integration_type not in [
                "hdma",
                "serena",
                "chat_history",
                "web_content",
            ]:
                issues.append(f"Invalid integration type: {integration_type}")
                recommendations.append(
                    "Valid types: hdma, serena, chat_history, web_content",
                )
            else:
                sanitized["integration_type"] = integration_type

        # Validate graph selection
        graphs = parameters.get("graphs", [])
        if graphs:
            valid_graphs = ["knowledge", "vector", "causal", "social", "system"]
            invalid_graphs = [g for g in graphs if g not in valid_graphs]
            if invalid_graphs:
                issues.append(f"Invalid graph types: {invalid_graphs}")
                recommendations.append(f"Valid graphs: {valid_graphs}")
            sanitized["graphs"] = [g for g in graphs if g in valid_graphs]

        # Constitutional compliance validation
        constitutional_result = self.constitutional_validator.validate_cks_operation(
            parameters,
            {"graphs": graphs if graphs else [], "operation": operation},
        )

        validation_level = self._determine_validation_level(
            issues,
            constitutional_result,
        )

        return ValidationResult(
            is_valid=len(issues) == 0 and constitutional_result.compliant,
            command=CKSCommand.CKS,
            validation_level=validation_level,
            issues=issues,
            recommendations=recommendations,
            sanitized_parameters=sanitized,
            evidence={
                "validation_timestamp": datetime.now().isoformat(),
                "operation": operation,
                "constitutional_compliance": constitutional_result.compliant,
            },
            constitutional_compliance=constitutional_result.evidence,
        )

    def _validate_query_input(
        self,
        parameters: dict[str, Any],
        user_context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validate /query command input."""
        issues = []
        recommendations = []
        sanitized = {}

        # Validate search term
        search_term = parameters.get("search_term", "").strip()
        if not search_term:
            issues.append("Missing search term")
            recommendations.append("Provide search term for query")
        else:
            # Security and bounds validation
            query_validation = self._validate_text_parameter(
                search_term,
                "search_term",
                self.parameter_bounds["max_query_length"],
            )
            issues.extend(query_validation["issues"])
            recommendations.extend(query_validation["recommendations"])
            sanitized["search_term"] = query_validation["sanitized"]

        # Validate max_results
        max_results = parameters.get("max_results", 10)
        if not isinstance(max_results, int) or max_results < 1:
            issues.append("max_results must be a positive integer")
            recommendations.append("Set max_results to 1-100")
            sanitized["max_results"] = 10
        elif max_results > self.parameter_bounds["max_results_limit"]:
            issues.append(
                f"max_results exceeds limit of {self.parameter_bounds['max_results_limit']}",
            )
            recommendations.append(
                f"Use max_results <= {self.parameter_bounds['max_results_limit']}",
            )
            sanitized["max_results"] = self.parameter_bounds["max_results_limit"]
        else:
            sanitized["max_results"] = max_results

        # Validate filters
        filters = parameters.get("filters", {})
        if filters and not isinstance(filters, dict):
            issues.append("filters must be a dictionary")
            recommendations.append("Provide filters as key-value pairs")
            sanitized["filters"] = {}
        else:
            sanitized["filters"] = filters

        # Validate graph types for query
        graph_types = parameters.get("graph_types", [])
        if graph_types:
            valid_graphs = ["knowledge", "vector", "causal", "social", "system"]
            invalid_graphs = [g for g in graph_types if g not in valid_graphs]
            if invalid_graphs:
                issues.append(f"Invalid graph types: {invalid_graphs}")
                recommendations.append(f"Valid graphs: {valid_graphs}")
            sanitized["graph_types"] = [g for g in graph_types if g in valid_graphs]

        # Constitutional compliance validation
        constitutional_result = self.constitutional_validator.validate_cks_operation(
            parameters,
            {"graphs": graph_types if graph_types else [], "operation": "query"},
        )

        validation_level = self._determine_validation_level(
            issues,
            constitutional_result,
        )

        return ValidationResult(
            is_valid=len(issues) == 0 and constitutional_result.compliant,
            command=CKSCommand.QUERY,
            validation_level=validation_level,
            issues=issues,
            recommendations=recommendations,
            sanitized_parameters=sanitized,
            evidence={
                "validation_timestamp": datetime.now().isoformat(),
                "operation": "query",
                "constitutional_compliance": constitutional_result.compliant,
            },
            constitutional_compliance=constitutional_result.evidence,
        )

    def _validate_learn_input(
        self,
        parameters: dict[str, Any],
        user_context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validate /learn command input."""
        issues = []
        recommendations = []
        sanitized = {}

        # Validate knowledge type
        knowledge_type = parameters.get("knowledge_type", "").strip()
        if not knowledge_type:
            issues.append("Missing knowledge_type parameter")
            recommendations.append(
                "Specify knowledge_type: pattern, solution, experience, analysis",
            )
        elif knowledge_type not in [
            "pattern",
            "solution",
            "experience",
            "analysis",
            "rca_finding",
        ]:
            issues.append(f"Invalid knowledge_type: {knowledge_type}")
            recommendations.append(
                "Valid types: pattern, solution, experience, analysis, rca_finding",
            )
        else:
            sanitized["knowledge_type"] = knowledge_type

        # Validate title
        title = parameters.get("title", "").strip()
        if not title:
            issues.append("Missing title parameter")
            recommendations.append("Provide a descriptive title")
        else:
            title_validation = self._validate_text_parameter(
                title,
                "title",
                self.parameter_bounds["max_title_length"],
            )
            issues.extend(title_validation["issues"])
            recommendations.extend(title_validation["recommendations"])
            sanitized["title"] = title_validation["sanitized"]

        # Validate content
        content = parameters.get("content", "").strip()
        if not content:
            issues.append("Missing content parameter")
            recommendations.append("Provide content to learn")
        else:
            content_validation = self._validate_text_parameter(
                content,
                "content",
                self.parameter_bounds["max_content_length"],
            )
            issues.extend(content_validation["issues"])
            recommendations.extend(content_validation["recommendations"])
            sanitized["content"] = content_validation["sanitized"]

        # Validate tags
        tags = parameters.get("tags", [])
        if tags:
            if not isinstance(tags, list):
                issues.append("tags must be a list")
                recommendations.append("Provide tags as a list of strings")
                sanitized["tags"] = []
            elif len(tags) > self.parameter_bounds["max_tags_count"]:
                issues.append(
                    f"Too many tags: {len(tags)} > {self.parameter_bounds['max_tags_count']}",
                )
                recommendations.append(
                    f"Use <= {self.parameter_bounds['max_tags_count']} tags",
                )
                sanitized["tags"] = tags[: self.parameter_bounds["max_tags_count"]]
            else:
                # Validate individual tags
                valid_tags = []
                for tag in tags:
                    if isinstance(tag, str) and len(tag.strip()) <= 50:
                        valid_tags.append(tag.strip())
                sanitized["tags"] = valid_tags

        # Validate evidence (required for constitutional compliance)
        evidence = parameters.get("evidence", "").strip()
        if not evidence:
            issues.append("Missing evidence parameter")
            recommendations.append("Provide evidence for the knowledge being learned")
        else:
            evidence_validation = self._validate_text_parameter(
                evidence,
                "evidence",
                1000,
            )
            issues.extend(evidence_validation["issues"])
            recommendations.extend(evidence_validation["recommendations"])
            sanitized["evidence"] = evidence_validation["sanitized"]

        # Validate source
        source = parameters.get("source", "manual").strip()
        if not source or len(source) > 100:
            issues.append("Invalid or missing source parameter")
            recommendations.append("Provide source (max 100 characters)")
            sanitized["source"] = "manual"
        else:
            sanitized["source"] = source

        # Constitutional compliance validation
        constitutional_result = self.constitutional_validator.validate_cks_operation(
            parameters,
            {"knowledge_type": knowledge_type, "operation": "learn"},
        )

        validation_level = self._determine_validation_level(
            issues,
            constitutional_result,
        )

        return ValidationResult(
            is_valid=len(issues) == 0 and constitutional_result.compliant,
            command=CKSCommand.LEARN,
            validation_level=validation_level,
            issues=issues,
            recommendations=recommendations,
            sanitized_parameters=sanitized,
            evidence={
                "validation_timestamp": datetime.now().isoformat(),
                "operation": "learn",
                "knowledge_type": knowledge_type,
                "constitutional_compliance": constitutional_result.compliant,
            },
            constitutional_compliance=constitutional_result.evidence,
        )

    def _validate_text_parameter(
        self,
        text: str,
        parameter_name: str,
        max_length: int,
    ) -> dict[str, Any]:
        """Validate text parameter for security and bounds."""
        issues = []
        recommendations = []
        sanitized = text

        # Length check
        if len(text) > max_length:
            issues.append(f"{parameter_name} exceeds maximum length of {max_length}")
            recommendations.append(
                f"Shorten {parameter_name} to <= {max_length} characters",
            )
            sanitized = text[:max_length]

        # SQL injection check
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Potential SQL injection detected in {parameter_name}")
                recommendations.append("Remove SQL keywords and special characters")
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # Command injection check
        for pattern in self.command_injection_patterns:
            if re.search(pattern, text):
                issues.append(
                    f"Potential command injection detected in {parameter_name}",
                )
                recommendations.append(
                    "Remove command operators and special characters",
                )
                sanitized = re.sub(pattern, "", sanitized)

        # Script injection check
        script_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
        ]
        for pattern in script_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(
                    f"Potential script injection detected in {parameter_name}",
                )
                recommendations.append("Remove script tags and event handlers")
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # Basic sanitization
        sanitized = re.sub(r"[^\w\s\-.,!?;:()[\]{}'\"@#$%^&*+=|\\/<>]", "", sanitized)
        sanitized = sanitized.strip()

        return {
            "issues": issues,
            "recommendations": recommendations,
            "sanitized": sanitized,
        }

    def _check_rate_limit(self, user_context: dict[str, Any] | None = None) -> bool:
        """Check rate limiting for user requests."""
        if not user_context:
            return True  # No rate limiting without context

        user_id = user_context.get("user_id", "anonymous")
        now = datetime.now()

        # Clean old requests (older than 1 hour)
        if user_id in self.request_history:
            self.request_history[user_id] = [
                req_time
                for req_time in self.request_history[user_id]
                if (now - req_time).seconds < 3600
            ]
        else:
            self.request_history[user_id] = []

        # Check rate limit (max 60 requests per hour)
        if (
            len(self.request_history[user_id])
            >= self.parameter_bounds["max_concurrent_requests"] * 6
        ):
            return False

        # Add current request
        self.request_history[user_id].append(now)
        return True

    def _determine_validation_level(
        self,
        issues: list[str],
        constitutional_result: Any,
    ) -> ValidationLevel:
        """Determine validation severity level."""
        if not constitutional_result.compliant:
            return ValidationLevel.VIOLATION

        issue_count = len(issues)
        if issue_count == 0:
            return ValidationLevel.NOTE
        if issue_count <= 2:
            return ValidationLevel.CONCERN
        if issue_count <= 5:
            return ValidationLevel.ISSUE
        return ValidationLevel.VIOLATION

    def get_validation_summary(self) -> dict[str, Any]:
        """Get validation system summary and statistics."""
        return {
            "validator_version": "1.0.0",
            "security_features": [
                "SQL injection prevention",
                "Command injection prevention",
                "Script injection prevention",
                "Parameter bounds checking",
                "Rate limiting",
                "Input sanitization",
            ],
            "constitutional_compliance": {
                "enabled": True,
                "validator": "CKSConstitutionalValidator",
                "catastrophic_terms_prevented": 7,
            },
            "parameter_bounds": self.parameter_bounds,
            "supported_commands": [cmd.value for cmd in CKSCommand],
            "validation_levels": [level.value for level in ValidationLevel],
            "statistics": {
                "requests_tracked": len(self.request_history),
                "active_users": len(self.request_history),
            },
        }
