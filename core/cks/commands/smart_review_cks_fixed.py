import asyncio
import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from standards_spec import StandardEntry, StandardsKnowledgeSystem

from cli.subprocess_helper import run_subprocess

#!/usr/bin/env python3
"""
CKS-Fixed Standards Checking Module for Smart Review

Properly integrates with CKS knowledge base - ALL standards validation comes from CKS,
no hardcoded patterns or validation logic.
"""


# Add paths for imports


logger = logging.getLogger(__name__)


class CKSStandardsChecker:
    """Pure CKS-based standards checker - all validation from knowledge base."""

    def __init__(self) -> None:
        self.standards_ks = StandardsKnowledgeSystem()
        self.language_detectors = {
            "python": [".py"],
            "typescript": [".ts", ".tsx"],
            "javascript": [".js", ".jsx"],
            "json": [".json"],
            "yaml": [".yml", ".yaml"],
            "toml": [".toml"],
        }

    async def initialize(self) -> None:
        """Initialize the standards knowledge base."""
        await self.standards_ks.initialize_database()
        logger.info("CKS Standards checker initialized")

    def detect_language(self, file_path: Path) -> str | None:
        """Detect language from file extension."""
        suffix = file_path.suffix.lower()
        for language, extensions in self.language_detectors.items():
            if suffix in extensions:
                return language
        return None

    async def check_file_compliance(self, file_path: Path) -> list[dict[str, Any]]:
        """Check a single file for standards compliance using ONLY CKS standards."""
        violations = []
        language = self.detect_language(file_path)

        if not language:
            return violations

        # Get ALL standards for this language from CKS - NO HARDCODED LOGIC
        try:
            standards = await self.standards_ks.query_standards(language=language)
            logger.info(
                f"CKS: Checking {file_path} against {len(standards)} {language} standards",
            )
        except Exception as e:
            logger.exception(f"CKS: Failed to query standards for {language}: {e}")
            return violations

        # Execute validation commands from CKS standards
        for standard in standards:
            violation = await self._execute_cks_validation(file_path, standard)
            if violation:
                violations.append(violation)

        # Additional content-based checks ONLY if CKS standard doesn't have validation command
        # This is for standards that need file content analysis rather than command execution
        for standard in standards:
            if not standard.validation_command:  # Only if CKS standard lacks validation command
                content_violation = await self._cks_content_check(file_path, standard)
                if content_violation:
                    violations.append(content_violation)

        return violations

    async def _execute_cks_validation(
        self,
        file_path: Path,
        standard: StandardEntry,
    ) -> dict[str, Any] | None:
        """Execute validation command from CKS standard."""
        if not standard.validation_command:
            return None

        try:
            # Execute validation command from CKS
            working_dir = file_path.parent
            command = standard.validation_command

            # Replace relative paths with absolute paths
            if "." in command:
                command = command.replace(".", str(working_dir))

            # Run the CKS validation command
            result = run_subprocess(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # If command returns non-zero, it's a violation
            if result.returncode != 0:
                return {
                    "rule_id": standard.rule_id,
                    "category": standard.category,
                    "severity": standard.severity,
                    "message": f"CKS Standard Violation: {standard.description}",
                    "file_path": str(file_path),
                    "line_number": None,
                    "suggestion": standard.example_fix,
                    "auto_fixable": standard.auto_fix_command is not None,
                    "command_output": result.stdout.strip(),
                    "command_error": result.stderr.strip(),
                    "cks_source": True,
                }

        except subprocess.TimeoutExpired:
            logger.warning(f"CKS: Validation command timed out for {standard.rule_id}")
        except Exception as e:
            logger.exception(f"CKS: Error executing validation for {standard.rule_id}: {e}")

        return None

    async def _cks_content_check(
        self,
        file_path: Path,
        standard: StandardEntry,
    ) -> dict[str, Any] | None:
        """Content-based check for CKS standards without validation commands."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Look for evidence from the standard
            if standard.example_violation:
                # Search for example violation patterns from CKS
                violation_patterns = self._extract_patterns_from_example(
                    standard.example_violation,
                )

                for line_num, line in enumerate(lines, 1):
                    for pattern in violation_patterns:
                        if pattern and pattern.lower() in line.lower():
                            return {
                                "rule_id": standard.rule_id,
                                "category": standard.category,
                                "severity": standard.severity,
                                "message": f"CKS Standard Violation: {standard.description}",
                                "file_path": str(file_path),
                                "line_number": line_num,
                                "suggestion": standard.example_fix,
                                "auto_fixable": standard.auto_fix_command is not None,
                                "cks_source": True,
                            }

        except UnicodeDecodeError:
            # Binary file, skip content analysis
            pass
        except Exception as e:
            logger.exception(f"CKS: Error reading file {file_path}: {e}")

        return None

    def _extract_patterns_from_example(self, example: str) -> list[str]:
        """Extract searchable patterns from CKS standard example violations."""
        if not example:
            return []

        patterns = []
        # Extract code snippets and keywords
        code_blocks = re.findall(r"```[^`]*```", example)
        if code_blocks:
            for block in code_blocks:
                # Remove backticks and extract meaningful patterns
                clean_block = re.sub(r"```\w*\n?", "", block).strip()
                if clean_block:
                    # Split into meaningful patterns
                    lines = clean_block.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 3:  # Only meaningful patterns
                            patterns.append(line)

        # Also extract standalone keywords/phrases
        words = re.findall(r"\b\w{3,}\b", example)
        patterns.extend([word for word in words if len(word) > 3])

        return list(set(patterns))  # Remove duplicates

    async def get_compliance_summary(
        self,
        violations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate compliance summary from CKS violations."""
        if not violations:
            return {
                "is_compliant": True,
                "violations_count": 0,
                "compliance_score": 100,
                "summary": "CKS: No standards violations detected",
            }

        # Count violations by severity
        severity_counts = {}
        for violation in violations:
            severity = violation["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        blocker_count = severity_counts.get("blocker", 0)
        error_count = severity_counts.get("error", 0)
        warning_count = severity_counts.get("warning", 0)

        # Calculate compliance score based on severity weights
        compliance_score = max(
            0,
            100 - (blocker_count * 20) - (error_count * 10) - (warning_count * 5),
        )

        return {
            "is_compliant": compliance_score >= 80,
            "violations_count": len(violations),
            "compliance_score": compliance_score,
            "severity_breakdown": severity_counts,
            "summary": f"CKS: Found {len(violations)} violations: {blocker_count} blockers, {error_count} errors, {warning_count} warnings",
        }


# Test the CKS-fixed checker
async def test_cks_checker() -> None:
    """Test the CKS-fixed standards checker."""
    checker = CKSStandardsChecker()
    await checker.initialize()

    # Test on the sample test file
    test_file = Path("test_enhanced_standards.py")
    if test_file.exists():
        print(f"Testing CKS checker on {test_file}")
        violations = await checker.check_file_compliance(test_file)

        print(f"CKS found {len(violations)} violations:")
        for violation in violations:
            print(
                f"  [{violation['severity'].upper()}] {violation['rule_id']}: {violation['message']}",
            )
            if violation.get("cks_source"):
                print("    Source: CKS Knowledge Base")

        summary = await checker.get_compliance_summary(violations)
        print("\nCKS Compliance Summary:")
        print(f"  Score: {summary['compliance_score']}")
        print(f"  Compliant: {summary['is_compliant']}")
        print(f"  Summary: {summary['summary']}")
    else:
        print(f"Test file {test_file} not found")


if __name__ == "__main__":
    asyncio.run(test_cks_checker())
