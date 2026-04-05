"""
Read Before Write Validator Module

Contains ReadBeforeWriteValidator class for enforcing READ Before WRITE protocol.

Extracted from pre_tool_use.py for better modularity and maintainability.
"""

import re
from typing import Any


class ReadBeforeWriteValidator:
    """
    READ Before WRITE protocol validator.

    Implements RBW-001: READ Before WRITE Enforcement according to CSF NIP specification.
    Based on root cause analysis from docs/root_cause_analysis.md.

    Validates that implementation work follows SRPI protocol:
    - S: Search codebase (Glob/Grep)
    - R: Read working implementations
    - P: Plan minimal change
    - I: Implement using Edit/Write tools
    """

    def __init__(self):
        """Initialize the RBW validator with configuration"""
        self.enabled = True
        self.session_searches = set()  # Track searches in current session
        self.session_reads = set()  # Track file reads in current session
        self.last_operation = None  # Track last operation type

    def validate_read_before_write(
        self, file_path: str, operation: str, tool_args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate READ Before WRITE compliance for a file operation.

        Args:
            file_path: Path to the file being operated on
            operation: Type of operation (Edit, write_to_file, read_file)
            tool_args: Arguments passed to the tool

        Returns:
            Dict with validation result and guidance
        """
        # Read operations don't need RBW enforcement (they ARE the "READ" phase)
        if operation == "read_file":
            self.session_reads.add(file_path)
            self.last_operation = "read_file"
            return {
                "allowed": True,
                "reason": "Read operation - records as SEARCH/READ phase",
                "rbw_phase": "READ",
                "action": "log_only",
            }

        # Check if this is a file that suggests implementation work
        is_code_file = self._is_code_file(file_path)

        if not is_code_file:
            return {
                "allowed": True,
                "reason": "Non-code file - RBW protocol not applicable",
                "rbw_phase": "skip",
                "action": "log_only",
            }

        # Analyze the operation for anti-patterns
        anti_patterns = self._detect_anti_patterns(tool_args)

        # Check for trial-and-error patterns
        trial_and_error = self._detect_trial_and_error(tool_args)

        # Generate guidance
        suggestions = []
        if anti_patterns:
            suggestions.extend(anti_patterns["suggestions"])
        if trial_and_error:
            suggestions.extend(trial_and_error["suggestions"])

        # Determine if this looks like a proper implementation vs random attempt
        is_proper = (
            len(self.session_reads) > 0  # Has read files
            or len(self.session_searches) > 0  # Has searched codebase
            or self._has_proper_structure(tool_args)  # Has proper code structure
        )

        if not is_proper and operation in ["replace_in_file", "write_to_file"]:
            self.last_operation = operation
            return {
                "allowed": True,  # Advisory mode - don't block, warn instead
                "reason": "[RBW] Before implementing, SEARCH codebase and READ working code first",
                "severity": "warning",
                "category": "read_before_write",
                "rbw_phase": "IMPLEMENT",
                "action": "warn",
                "suggestions": [
                    "Search codebase: Glob/Grep for related files first",
                    "Query CHS/CKS: /chs 'topic' for existing knowledge",
                    "Read working code: Find and read existing implementations",
                    "Copy exact pattern: Don't guess env vars, endpoints, paths",
                ]
                + suggestions,
                "anti_patterns_detected": list(
                    {
                        *(anti_patterns.get("patterns", []) if anti_patterns else []),
                        *(
                            trial_and_error.get("patterns", [])
                            if trial_and_error
                            else []
                        ),
                    }
                ),
            }

        self.last_operation = operation
        return {
            "allowed": True,
            "reason": f"RBW protocol: {operation} operation follows READ phase",
            "rbw_phase": "IMPLEMENT",
            "action": "log_only",
        }

    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file that requires RBW validation"""
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".cs",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".swift",
            ".kt",
            ".scala",
            ".sh",
        }
        return any(file_path.endswith(ext) for ext in code_extensions)

    def _detect_anti_patterns(self, tool_args: dict[str, Any]) -> dict[str, Any] | None:
        """Detect common anti-patterns in tool arguments"""
        patterns = []
        suggestions = []

        content = tool_args.get("new_text", "") + tool_args.get("content", "")

        # Pattern 1: Complex bash/Python one-liners (wrong tool for the job)
        if "python -c" in content.lower() or "bash -c" in content.lower():
            if len(content) > 200:  # Complex one-liner
                patterns.append("complex_bash_oneliner")
                suggestions.append(
                    "Use replace_in_file/write_to_file tools instead of complex bash one-liners"
                )

        # Pattern 2: Multiple endpoint attempts (trial-and-error)
        endpoint_count = content.lower().count("https://") + content.lower().count(
            "http://"
        )
        if endpoint_count >= 3:
            patterns.append("multiple_endpoint_attempts")
            suggestions.append(
                "Search codebase for working API integration instead of trying random endpoints"
            )

        # Pattern 3: Guessing env var names
        env_var_patterns = ["API_KEY", "TOKEN", "SECRET", "PASSWORD"]
        for pattern in env_var_patterns:
            if f"{pattern}=" in content and "os.getenv" in content:
                patterns.append("guessing_env_vars")
                suggestions.append(
                    f"Read existing code to find correct env var name for {pattern}"
                )
                break

        if patterns:
            return {"patterns": patterns, "suggestions": suggestions}
        return None

    def _detect_trial_and_error(
        self, tool_args: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Detect trial-and-error patterns"""
        patterns = []
        suggestions = []

        content = tool_args.get("new_text", "") + tool_args.get("content", "")

        # Multiple variations of similar code (retry loop)
        similar_patterns = [
            (r"try:\s*\n.*?except\s*:\s*\n.*?try:\s*\n", "nested_try_retry"),
            (r"except\s*:\s*\n.*?except\s*:", "multiple_except_blocks"),
            (r"if\s+.*?:\s*\n.*?elif\s+.*?:\s*\n.*?else:", "multiple_attempts"),
        ]

        for pattern, name in similar_patterns:
            if re.search(pattern, content, re.DOTALL):
                patterns.append(name)
                suggestions.append(
                    "Stop and read error messages - trial-and-error wastes time"
                )

        if patterns:
            return {"patterns": patterns, "suggestions": suggestions}
        return None

    def _has_proper_structure(self, tool_args: dict[str, Any]) -> bool:
        """Check if the code has proper structure (indicates thought, not random attempts)"""
        content = tool_args.get("new_text", "") + tool_args.get("content", "")

        # Signs of proper implementation:
        if len(content) < 50:
            return False  # Too small to judge

        # Has docstring or comments?
        if '"""' in content or "'''" in content or "#" in content:
            return True

        # Has proper function/class structure?
        if re.search(r"def\s+\w+\s*\(", content) or re.search(r"class\s+\w+", content):
            return True

        return False

    def record_search(self, pattern: str, tool_name: str):
        """Record a search operation"""
        self.session_searches.add(f"{tool_name}:{pattern}")

    def get_protocol_status(self) -> dict[str, Any]:
        """Get current status of RBW protocol in session"""
        return {
            "searches_performed": len(self.session_searches),
            "reads_performed": len(self.session_reads),
            "last_operation": self.last_operation,
            "protocol_phase": self._determine_phase(),
        }

    def _determine_phase(self) -> str:
        """Determine current protocol phase based on session state"""
        if len(self.session_reads) == 0 and len(self.session_searches) == 0:
            return "SEARCH_NEEDED"
        elif len(self.session_reads) > 0 and self.last_operation == "read_file":
            return "READ_COMPLETE"
        elif self.last_operation in ["replace_in_file", "write_to_file"]:
            return "IMPLEMENT_COMPLETE"
        return "UNKNOWN"
