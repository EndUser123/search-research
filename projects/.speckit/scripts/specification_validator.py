#!/usr/bin/env python3
"""
Speckit Specification Validator

Validates speckit specifications for completeness, quality, and compliance.
Provides quality gates and validation checks for all specification types.
"""

import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ValidationLevel(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    level: ValidationLevel
    category: str
    message: str
    line_number: int | None = None
    suggestion: str | None = None


@dataclass
class ValidationReport:
    file_path: str
    validation_results: list[ValidationResult]
    overall_status: str
    score: float
    issues_by_level: dict[str, int]


class SpecificationValidator:
    """Validates speckit specification files."""

    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()

    def validate_specification(self, spec_file: Path) -> ValidationReport:
        """
        Validate a specification file.

        Args:
            spec_file: Path to specification markdown file

        Returns:
            Validation report with all findings
        """
        if not spec_file.exists():
            raise FileNotFoundError(f"Specification file not found: {spec_file}")

        with open(spec_file, encoding="utf-8") as f:
            content = f.read()

        # Determine specification type from filename
        spec_type = self._determine_spec_type(spec_file.name)

        # Run validation rules
        validation_results = []
        validation_results.extend(self._validate_structure(content, spec_type))
        validation_results.extend(self._validate_required_sections(content, spec_type))
        validation_results.extend(self._validate_content_quality(content, spec_type))
        validation_results.extend(self._validate_placeholders(content))
        validation_results.extend(self._validate_knowledge_integration(content))
        validation_results.extend(self._validate_tdd_content(content, spec_type))

        # Calculate overall status and score
        overall_status, score = self._calculate_overall_status(validation_results)
        issues_by_level = self._count_issues_by_level(validation_results)

        return ValidationReport(
            file_path=str(spec_file),
            validation_results=validation_results,
            overall_status=overall_status,
            score=score,
            issues_by_level=issues_by_level,
        )

    def validate_project_directory(
        self, project_dir: Path
    ) -> dict[str, ValidationReport]:
        """
        Validate all specification files in a project directory.

        Args:
            project_dir: Path to project specification directory

        Returns:
            Dictionary of validation reports by filename
        """
        reports = {}

        # Find all specification files
        spec_files = list(project_dir.glob("*.md"))
        if not spec_files:
            return {
                "error": ValidationReport(
                    file_path=str(project_dir),
                    validation_results=[
                        ValidationResult(
                            level=ValidationLevel.ERROR,
                            category="structure",
                            message="No specification files found",
                        )
                    ],
                    overall_status="error",
                    score=0.0,
                    issues_by_level={"error": 1},
                )
            }

        # Validate each specification file
        for spec_file in spec_files:
            try:
                reports[spec_file.name] = self.validate_specification(spec_file)
            except Exception as e:
                reports[spec_file.name] = ValidationReport(
                    file_path=str(spec_file),
                    validation_results=[
                        ValidationResult(
                            level=ValidationLevel.ERROR,
                            category="validation",
                            message=f"Validation failed: {str(e)}",
                        )
                    ],
                    overall_status="error",
                    score=0.0,
                    issues_by_level={"error": 1},
                )

        return reports

    def _determine_spec_type(self, filename: str) -> str:
        """Determine specification type from filename."""
        if "SPECIFY" in filename.upper():
            return "specify"
        elif "PLAN" in filename.upper():
            return "plan"
        elif "TASKS" in filename.upper():
            return "tasks"
        elif "IMPLEMENT" in filename.upper():
            return "implement"
        else:
            return "unknown"

    def _initialize_validation_rules(self) -> dict[str, dict]:
        """Initialize validation rules for different specification types."""
        return {
            "specify": {
                "required_sections": [
                    "## Project Information",
                    "## Feature Overview",
                    "## Requirements",
                    "## User Stories",
                    "## Success Criteria",
                    "## Integration Requirements",
                ],
                "critical_fields": ["Project ID", "Project Name", "Work Type"],
                "knowledge_integration_required": True,
                "acceptance_criteria_required": True,
            },
            "plan": {
                "required_sections": [
                    "## Project Information",
                    "## System Architecture",
                    "## TDD Strategy",
                    "## Implementation Strategy",
                    "## Quality Assurance",
                ],
                "critical_fields": ["Project ID", "Phase", "Technology Stack"],
                "tdd_strategy_required": True,
                "architecture_diagrams_required": True,
            },
            "tasks": {
                "required_sections": [
                    "## Project Information",
                    "## TDD-Driven Task Organization",
                    "## Task Dependencies Graph",
                    "## Quality Gates",
                ],
                "critical_fields": ["Project ID", "Phase", "Total Estimated Effort"],
                "task_structure_required": True,
                "dependencies_required": True,
            },
            "implement": {
                "required_sections": [
                    "## Project Information",
                    "## Task Execution Plan",
                    "## Quality Assurance Results",
                    "## Evidence Collection",
                ],
                "critical_fields": ["Project ID", "Phase", "Implementation Status"],
                "execution_tracking_required": True,
                "quality_gates_required": True,
            },
        }

    def _validate_structure(
        self, content: str, spec_type: str
    ) -> list[ValidationResult]:
        """Validate document structure."""
        results = []

        lines = content.split("\n")
        headers = []

        # Extract all headers
        for i, line in enumerate(lines, 1):
            if line.startswith("#"):
                headers.append((line.strip(), i))

        # Check for proper header hierarchy
        if not any(h[0].startswith("# ") for h in headers):
            results.append(
                ValidationResult(
                    level=ValidationLevel.ERROR,
                    category="structure",
                    message="Document must have at least one H1 header",
                    suggestion="Add a main title using # Title",
                )
            )

        # Check for H2 headers
        h2_headers = [h for h in headers if h[0].startswith("## ")]
        if len(h2_headers) < 3:
            results.append(
                ValidationResult(
                    level=ValidationLevel.WARNING,
                    category="structure",
                    message="Document has few H2 sections",
                    suggestion="Consider adding more sections for better organization",
                )
            )

        return results

    def _validate_required_sections(
        self, content: str, spec_type: str
    ) -> list[ValidationResult]:
        """Validate required sections are present."""
        results = []

        if spec_type not in self.validation_rules:
            results.append(
                ValidationResult(
                    level=ValidationLevel.WARNING,
                    category="content",
                    message=f"Unknown specification type: {spec_type}",
                    suggestion="Ensure filename follows standard naming (SPECIFY, PLAN, TASKS, IMPLEMENT)",
                )
            )
            return results

        rules = self.validation_rules[spec_type]
        required_sections = rules.get("required_sections", [])

        for section in required_sections:
            if section not in content:
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        category="content",
                        message=f"Missing required section: {section}",
                        suggestion=f"Add the '{section}' section to the document",
                    )
                )

        return results

    def _validate_content_quality(
        self, content: str, spec_type: str
    ) -> list[ValidationResult]:
        """Validate content quality."""
        results = []

        # Check for placeholder text
        placeholder_patterns = [
            r"\[.*\]",  # Square brackets with content
            r"TODO:",  # TODO items
            r"FIXME:",  # FIXME items
            r"XXX:",  # XXX items
        ]

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern in placeholder_patterns:
                if re.search(pattern, line) and not line.strip().startswith("<!--"):
                    # Skip if it's a legitimate use of brackets (like checklist items)
                    if not (
                        line.strip().startswith("- [")
                        or line.strip().startswith("  - [")
                    ):
                        results.append(
                            ValidationResult(
                                level=ValidationLevel.WARNING,
                                category="content",
                                message=f"Placeholder text found: {line.strip()[:50]}...",
                                line_number=i,
                                suggestion="Replace placeholder with actual content",
                            )
                        )

        # Check for very short sections
        sections = content.split("## ")
        for section in sections:
            if section.strip():
                lines_in_section = len(section.split("\n"))
                if lines_in_section < 3:
                    section_title = section.split("\n")[0].strip()
                    results.append(
                        ValidationResult(
                            level=ValidationLevel.INFO,
                            category="content",
                            message=f"Section '{section_title}' is very short",
                            suggestion="Consider adding more detail to this section",
                        )
                    )

        return results

    def _validate_placeholders(self, content: str) -> list[ValidationResult]:
        """Validate for specific placeholders that need replacement."""
        results = []

        # Common placeholders that should be replaced
        critical_placeholders = [
            "TSK-XXX",
            "[Feature Name]",
            "[Date]",
            "[UUID]",
            "[number]",
            "[Hours]",
        ]

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for placeholder in critical_placeholders:
                if placeholder in line:
                    results.append(
                        ValidationResult(
                            level=ValidationLevel.ERROR,
                            category="content",
                            message=f"Critical placeholder not replaced: {placeholder}",
                            line_number=i,
                            suggestion=f"Replace {placeholder} with actual value",
                        )
                    )

        return results

    def _validate_knowledge_integration(self, content: str) -> list[ValidationResult]:
        """Validate knowledge system integration."""
        results = []

        # Check for knowledge discovery section
        if "Knowledge Discovery Results" in content:
            knowledge_section = content.split("Knowledge Discovery Results")[1].split(
                "##"
            )[0]

            # Check if knowledge discovery is populated
            if (
                "[List relevant patterns]" in knowledge_section
                or "[Description]" in knowledge_section
            ):
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        category="knowledge_integration",
                        message="Knowledge discovery section contains placeholder content",
                        suggestion="Populate knowledge discovery with actual search results",
                    )
                )
        else:
            results.append(
                ValidationResult(
                    level=ValidationLevel.WARNING,
                    category="knowledge_integration",
                    message="No knowledge discovery section found",
                    suggestion="Add knowledge discovery to leverage organizational knowledge",
                )
            )

        return results

    def _validate_tdd_content(
        self, content: str, spec_type: str
    ) -> list[ValidationResult]:
        """Validate TDD-related content."""
        results = []

        if spec_type in ["plan", "tasks", "implement"]:
            # Check for TDD strategy in plan
            if spec_type == "plan" and "TDD Strategy" not in content:
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        category="tdd",
                        message="TDD Strategy section missing from plan",
                        suggestion="Add TDD Strategy section with test pyramid and approach",
                    )
                )

            # Check for test-related content in tasks
            if spec_type == "tasks" and "TDD" not in content:
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        category="tdd",
                        message="Tasks specification lacks TDD organization",
                        suggestion="Organize tasks using TDD red-green-refactor cycles",
                    )
                )

            # Check for quality gates in implement
            if spec_type == "implement" and "Quality Gates" not in content:
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        category="tdd",
                        message="Implementation lacks quality gate tracking",
                        suggestion="Add quality gates and validation checkpoints",
                    )
                )

        return results

    def _calculate_overall_status(
        self, results: list[ValidationResult]
    ) -> tuple[str, float]:
        """Calculate overall validation status and score."""
        if not results:
            return "passed", 100.0

        # Count issues by level
        critical_count = sum(1 for r in results if r.level == ValidationLevel.CRITICAL)
        error_count = sum(1 for r in results if r.level == ValidationLevel.ERROR)
        warning_count = sum(1 for r in results if r.level == ValidationLevel.WARNING)
        info_count = sum(1 for r in results if r.level == ValidationLevel.INFO)

        # Determine status
        if critical_count > 0:
            return "failed", 0.0
        elif error_count > 0:
            return "failed", max(0, 70 - error_count * 10)
        elif warning_count > 5:
            return "warning", max(70, 90 - warning_count * 2)
        else:
            return "passed", max(90, 100 - warning_count * 3 - info_count)

    def _count_issues_by_level(self, results: list[ValidationResult]) -> dict[str, int]:
        """Count issues by validation level."""
        counts = {level.value: 0 for level in ValidationLevel}
        for result in results:
            counts[result.level.value] += 1
        return counts


def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Speckit Specification Validator")
    parser.add_argument("path", help="Path to specification file or directory")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show summary")
    parser.add_argument(
        "--threshold",
        type=float,
        default=70.0,
        help="Minimum score to pass (default: 70.0)",
    )

    args = parser.parse_args()

    path = Path(args.path)
    validator = SpecificationValidator()

    try:
        if path.is_file():
            # Validate single file
            report = validator.validate_specification(path)
            reports = {path.name: report}
        elif path.is_dir():
            # Validate directory
            reports = validator.validate_project_directory(path)
        else:
            print(f"Error: Path not found: {path}", file=sys.stderr)
            sys.exit(1)

        # Calculate overall results
        total_files = len(reports)
        passed_files = sum(1 for r in reports.values() if r.overall_status == "passed")
        failed_files = sum(1 for r in reports.values() if r.overall_status == "failed")
        warning_files = sum(
            1 for r in reports.values() if r.overall_status == "warning"
        )

        average_score = (
            sum(r.score for r in reports.values()) / total_files
            if total_files > 0
            else 0
        )

        # Prepare output
        output_data = {
            "summary": {
                "total_files": total_files,
                "passed_files": passed_files,
                "failed_files": failed_files,
                "warning_files": warning_files,
                "average_score": round(average_score, 1),
                "overall_status": (
                    "passed" if average_score >= args.threshold else "failed"
                ),
            },
            "reports": {},
        }

        for filename, report in reports.items():
            output_data["reports"][filename] = {
                "overall_status": report.overall_status,
                "score": report.score,
                "issues_by_level": report.issues_by_level,
                "validation_results": [
                    {
                        "level": r.level.value,
                        "category": r.category,
                        "message": r.message,
                        "line_number": r.line_number,
                        "suggestion": r.suggestion,
                    }
                    for r in report.validation_results
                ],
            }

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            if not args.quiet:
                print(f"Validation results saved to {args.output}")
        else:
            if not args.quiet:
                print(json.dumps(output_data, indent=2))
            else:
                # Quiet mode - just show summary
                print(
                    f"Files: {total_files}, Passed: {passed_files}, Failed: {failed_files}, "
                    f"Warnings: {warning_files}, Score: {average_score:.1f}"
                )

        # Set exit code based on overall status
        sys.exit(0 if output_data["summary"]["overall_status"] == "passed" else 1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
