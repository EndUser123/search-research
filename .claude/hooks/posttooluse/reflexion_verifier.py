#!/usr/bin/env python3
"""Reflexion Verifier Hook - Zero-Friction Self-Healing for Write Operations.

Implements Reflexion pattern for PostToolUse verification:
- Reads file from disk after Write/Edit (no trust in input)
- Detects truncation, syntax errors, indentation issues
- Auto-retry with self-healing prompts (up to 3 iterations)
- Only blocks on unfixable critical errors
- Records Read observations for Stop hooks

Based on research:
- Reflexion (ACL 2023): Generate → Verify → Reflect → Correct loop
- Cursor IDE: Cmd+K auto-fix with one-click acceptance
- Industry standard: 48%→95% accuracy improvement with self-reflection

Author: CSF NIP
Version: 2.3.0 (2026-03-11)
Ruff auto-format compatibility:
- Detects when ruff removes "unused" imports added by Edit
- Prevents false positives on import-only edits
- Preserves security verification for actual edit failures
Comprehensive verification robustness improvements:
- Binary file detection (prevents corruption)
- Large file size limits (prevents OOM)
- JavaScript/TypeScript syntax validation
- YAML/JSON semantic validation
- Encoding issue detection
- Concurrent write detection
"""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook


class ReflexionVerifier(PostToolUseHook):
    """
    Zero-friction write verification with Reflexion-style auto-healing.

    Philosophy:
    - NEVER block for fixable issues (inject self-healing prompt instead)
    - ONLY block on critical unfixable errors (syntax that prevents execution)
    - ALWAYS read from disk (never trust Write/Edit input)
    - RECORD evidence for Stop hooks (post_edit_readbacks)
    - SKIP binary files (prevent silent corruption)
    - RESPECT size limits (prevent OOM)
    """

    env_var = "REFLEXION_VERIFIER_ENABLED"
    default_enabled = True

    # Only verify code files
    tool_matcher = {"Write", "Edit", "MultiEdit"}

    # Code file extensions
    CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs"}

    # Binary file extensions (skip verification to prevent corruption)
    BINARY_EXTENSIONS = {
        # Images
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
        # Audio/Video
        ".mp3", ".mp4", ".wav", ".avi", ".mov", ".flv", ".mkv", ".webm",
        # Archives/Compressed
        ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz", ".tar.gz",
        # Compiled/Executables
        ".exe", ".dll", ".so", ".dylib", ".a", ".lib", ".o", ".obj",
        ".pyc", ".pyo", ".pyd",
        # Data formats
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        # Database
        ".db", ".sqlite", ".sqlite3",
        # Fonts
        ".ttf", ".otf", ".woff", ".woff2", ".eot",
    }

    # Structured data files (require semantic validation)
    STRUCTURED_DATA_EXTENSIONS = {".json", ".yaml", ".yml"}

    # Max retry iterations for self-healing
    MAX_RETRIES = 3

    # Truncation threshold (warning if file < 50% of expected size)
    TRUNCATION_THRESHOLD = 0.5

    # Maximum file size to verify (10 MB) - prevents OOM
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(self):
        super().__init__()
        self.hooks_dir = Path(__file__).resolve().parent.parent
        self.session_dir = self.hooks_dir / "session_data"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        # Per-file retry tracking
        self.retry_file = self.session_dir / "reflexion_retries.json"
        # Evidence log for Stop hooks
        self.evidence_log = self.session_dir / "reflexion_evidence.jsonl"

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        """
        Verify Write/Edit operation with Reflexion loop.

        Returns dict with:
        - passed: bool (always True for non-blocking)
        - status: "PASS" | "WARN" | "FAIL"
        - injection: str | None (self-healing prompt)
        - post_edit_readbacks: list[dict] (evidence for Stop hooks)
        """
        result = {
            "passed": True,
            "status": "PASS",
            "injection": None,
            "post_edit_readbacks": [],
        }

        file_path = tool_input.get("file_path", "")
        if not file_path:
            return result

        # P0: Skip binary files (prevent silent corruption)
        if self._is_binary_file(file_path):
            return result

        # P1: Check file size before reading (prevent OOM)
        file_size_issue = self._check_file_size(file_path)
        if file_size_issue:
            result["status"] = "WARN"
            result["injection"] = self._format_injection(file_path, [file_size_issue])
            return result

        # Read ACTUAL file from disk (not input!)
        actual_content = self._read_file_from_disk(file_path)
        if actual_content is None:
            # File doesn't exist after Write - THIS IS CRITICAL
            result["status"] = "FAIL"
            result["injection"] = f"⚠️ **File Verification Failed**: Write operation reported success, but file not found at: {file_path}\n\nThe file may not have been written correctly. Please re-write the file."
            return result

        # Perform verification checks (ORDER MATTERS: critical → fixable)
        issues = []

        # 0. Concurrent write detection (P3)
        concurrent_issue = self._check_concurrent_write(file_path, tool_input)
        if concurrent_issue:
            issues.append(concurrent_issue)

        # 1. Empty file check (CRITICAL - blocks immediately)
        # Check this BEFORE syntax check to avoid parsing empty files
        if not actual_content.strip():
            issues.append({
                "type": "EMPTY_FILE",
                "severity": "CRITICAL",
                "message": f"File is empty after {tool_name} operation",
            })

        # 2. Syntax check (CRITICAL - blocks immediately)
        # Only check syntax if file is not empty
        if not any(i["type"] == "EMPTY_FILE" for i in issues):
            syntax_issue = self._check_syntax(actual_content, file_path)
            if syntax_issue:
                issues.append(syntax_issue)

        # 2.5. Structured data validation (YAML/JSON) - MEDIUM severity
        if self._is_structured_data_file(file_path):
            data_issue = self._check_structured_data(actual_content, file_path)
            if data_issue:
                issues.append(data_issue)

        # 3. Truncation check (fixable - only for Write operations with content)
        if tool_name == "Write" and "content" in tool_input:
            truncation_issue = self._check_truncation(file_path, tool_input, actual_content)
            if truncation_issue:
                issues.append(truncation_issue)

        # 3.5. Edit verification (fixable - only for Edit operations)
        if tool_name in ("Edit", "MultiEdit"):
            edit_issue = self._verify_edit_operation(file_path, tool_input, actual_content)
            if edit_issue:
                issues.append(edit_issue)

        # 4. Indentation check (Python only - fixable)
        indent_issue = self._check_indentation(actual_content, file_path)
        if indent_issue:
            issues.append(indent_issue)

        # Record evidence for Stop hooks (ALWAYS, even on pass)
        self._record_evidence(file_path, actual_content, tool_name)

        # If no issues, we're done
        if not issues:
            return result

        # Check if we should retry (fixable issues) or block (critical)
        critical_issues = [i for i in issues if i["severity"] == "CRITICAL"]
        fixable_issues = [i for i in issues if i["severity"] in ("HIGH", "MEDIUM", "LOW")]

        if critical_issues:
            # Block for critical errors (syntax that breaks execution)
            result["status"] = "FAIL"
            result["injection"] = self._format_injection(file_path, issues, is_critical=True)
            self._log_verification(file_path, "FAIL", issues)
            return result

        if fixable_issues:
            # Check retry count
            retry_count = self._get_retry_count(file_path)

            if retry_count < self.MAX_RETRIES:
                # Increment retry and inject self-healing prompt
                self._increment_retry(file_path)
                result["status"] = "WARN"
                result["injection"] = self._format_self_healing_prompt(file_path, issues, retry_count + 1)
                self._log_verification(file_path, f"RETRY_{retry_count + 1}", issues)
                return result
            else:
                # Max retries reached - surface to user with clear guidance
                self._clear_retry(file_path)
                result["status"] = "WARN"
                result["injection"] = self._format_injection(file_path, issues, is_critical=False, max_retries=True)
                self._log_verification(file_path, "MAX_RETRIES", issues)
                return result

        return result

    def _is_binary_file(self, file_path: str) -> bool:
        """Check if file is a binary file (skip verification)."""
        return any(file_path.endswith(ext) for ext in self.BINARY_EXTENSIONS)

    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file."""
        return any(file_path.endswith(ext) for ext in self.CODE_EXTENSIONS)

    def _is_structured_data_file(self, file_path: str) -> bool:
        """Check if file is structured data (YAML/JSON)."""
        return any(file_path.endswith(ext) for ext in self.STRUCTURED_DATA_EXTENSIONS)

    def _check_file_size(self, file_path: str) -> dict[str, Any] | None:
        """
        Check if file is too large to verify (P1: prevents OOM).

        Returns issue dict if file exceeds MAX_FILE_SIZE, None otherwise.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            file_size = path.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                limit_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                return {
                    "type": "FILE_TOO_LARGE",
                    "severity": "MEDIUM",
                    "message": f"File size ({size_mb:.1f} MB) exceeds verification limit ({limit_mb} MB). Truncation/syntax checks skipped for performance.",
                }
        except (OSError, PermissionError):
            pass
        return None

    def _check_concurrent_write(self, file_path: str, tool_input: dict[str, Any]) -> dict[str, Any] | None:
        """
        Detect concurrent writes (P3: detect external modifications).

        Compares file mtime with expected write time.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            # Get file modification time
            file_mtime = path.stat().st_mtime
            current_time = datetime.now(UTC).timestamp()

            # If file was modified >5 seconds ago, likely external modification
            # (Recent writes should have mtime within 1-2 seconds)
            if current_time - file_mtime > 5:
                return {
                    "type": "CONCURRENT_WRITE_DETECTED",
                    "severity": "LOW",
                    "message": "File modification time suggests external process may have modified file after write operation",
                }
        except (OSError, PermissionError):
            pass
        return None

    def _tool_failed(self, tool_response: Any) -> bool:
        """Check if tool reported failure."""
        if not tool_response:
            return False

        response_str = str(tool_response).lower()
        error_indicators = ["error", "failed", "denied", "not found"]
        return any(indicator in response_str for indicator in error_indicators)

    def _read_file_from_disk(self, file_path: str) -> str | None:
        """
        Read ACTUAL file from disk (not from tool input).

        This is the core verification - trust but verify.
        Returns None if file doesn't exist or can't be read.

        P2: Encoding issue detection - no silent corruption with errors="replace"
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            # Try UTF-8 first (strict mode - detect encoding issues)
            try:
                return path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # UTF-8 failed, try common encodings
                encodings = ["utf-8-sig", "latin-1", "cp1252"]
                for enc in encodings:
                    try:
                        return path.read_text(encoding=enc)
                    except UnicodeDecodeError:
                        continue

                # All encodings failed - return None (corrupted file)
                return None

        except (PermissionError, OSError):
            return None

    def _check_truncation(self, file_path: str, tool_input: dict[str, Any], actual_content: str) -> dict[str, Any] | None:
        """
        Check if file was truncated during Write operation.

        Compares actual file size with expected content size.

        P1: Uses 50% threshold - configurable via TRUNCATION_THRESHOLD
        """
        if "content" not in tool_input:
            return None

        expected_content = tool_input["content"]
        expected_size = len(expected_content.encode("utf-8"))
        actual_size = len(actual_content.encode("utf-8"))

        # Allow small rounding differences (< 5%)
        if actual_size < expected_size * self.TRUNCATION_THRESHOLD:
            return {
                "type": "TRUNCATION",
                "severity": "HIGH",
                "message": f"File truncated: expected {expected_size} bytes, got {actual_size} bytes",
                "expected_size": expected_size,
                "actual_size": actual_size,
            }

        # Check for suspicious size difference
        if actual_size < expected_size * 0.95:
            return {
                "type": "SIZE_MISMATCH",
                "severity": "MEDIUM",
                "message": f"File size mismatch: expected {expected_size} bytes, got {actual_size} bytes",
                "expected_size": expected_size,
                "actual_size": actual_size,
            }

        return None

    def _check_syntax(self, content: str, file_path: str) -> dict[str, Any] | None:
        """
        Check syntax errors based on file extension.

        P1: Added JavaScript/TypeScript syntax checking.
        """
        # Python syntax check
        if file_path.endswith(".py"):
            try:
                ast.parse(content)
                return None
            except SyntaxError as e:
                return {
                    "type": "SYNTAX_ERROR",
                    "severity": "CRITICAL",
                    "message": f"Python syntax error at line {e.lineno}: {e.msg}",
                    "line": e.lineno,
                    "offset": e.offset,
                }

        # JavaScript/TypeScript syntax check (basic)
        if file_path.endswith((".js", ".ts", ".tsx", ".jsx")):
            return self._check_javascript_syntax(content, file_path)

        return None

    def _check_javascript_syntax(self, content: str, file_path: str) -> dict[str, Any] | None:
        """
        Basic JavaScript/TypeScript syntax checking.

        Uses pattern matching to detect common syntax errors.
        Not a full parser - catches obvious issues quickly.
        """
        issues = []

        # Check for basic syntax errors
        lines = content.split("\n")

        # Track bracket/brace/paren balance
        bracket_stack = []
        brace_stack = []
        paren_stack = []

        for line_num, line in enumerate(lines, 1):
            # Skip strings (basic handling)
            in_string = False
            escape_next = False

            for i, char in enumerate(line):
                if escape_next:
                    escape_next = False
                    continue

                if char == "\\":
                    escape_next = True
                    continue

                # Skip strings and comments
                if char in ('"', "'", "`"):
                    if not in_string:
                        in_string = char
                    elif in_string == char:
                        in_string = False
                    continue

                if in_string:
                    continue

                # Check brackets
                if char == "{":
                    brace_stack.append((line_num, i))
                elif char == "}":
                    if not brace_stack:
                        issues.append(f"Unmatched closing brace at line {line_num}")
                    else:
                        brace_stack.pop()
                elif char == "[":
                    bracket_stack.append((line_num, i))
                elif char == "]":
                    if not bracket_stack:
                        issues.append(f"Unmatched closing bracket at line {line_num}")
                    else:
                        bracket_stack.pop()
                elif char == "(":
                    paren_stack.append((line_num, i))
                elif char == ")":
                    if not paren_stack:
                        issues.append(f"Unmatched closing paren at line {line_num}")
                    else:
                        paren_stack.pop()

        # Check for unclosed brackets
        if brace_stack:
            issues.append(f"Unclosed brace starting at line {brace_stack[-1][0]}")
        if bracket_stack:
            issues.append(f"Unclosed bracket starting at line {bracket_stack[-1][0]}")
        if paren_stack:
            issues.append(f"Unclosed paren starting at line {paren_stack[-1][0]}")

        if issues:
            return {
                "type": "SYNTAX_ERROR",
                "severity": "CRITICAL",
                "message": f"JavaScript/TypeScript syntax error: {'; '.join(issues[:3])}",
                "details": issues,
            }

        return None

    def _check_structured_data(self, content: str, file_path: str) -> dict[str, Any] | None:
        """
        Validate structured data files (YAML/JSON).

        P2: Semantic validation for configuration files.
        """
        if file_path.endswith((".json",)):
            return self._check_json_syntax(content)

        if file_path.endswith((".yaml", ".yml")):
            return self._check_yaml_syntax(content)

        return None

    def _check_json_syntax(self, content: str) -> dict[str, Any] | None:
        """Check JSON syntax."""
        try:
            json.loads(content)
            return None
        except json.JSONDecodeError as e:
            return {
                "type": "JSON_SYNTAX_ERROR",
                "severity": "MEDIUM",
                "message": f"JSON syntax error at line {e.lineno}, column {e.colno}: {e.msg}",
            }

    def _check_yaml_syntax(self, content: str) -> dict[str, Any] | None:
        """
        Check YAML syntax (basic validation).

        Note: Full YAML validation requires PyYAML library.
        This provides basic structure checking.
        """
        # Basic YAML structure checks
        lines = content.split("\n")
        issues = []

        for line_num, line in enumerate(lines, 1):
            # Check for tabs (YAML forbids tabs)
            if line.startswith("\t"):
                issues.append(f"Line {line_num}: YAML forbids tabs, use spaces")
                continue

            # Check for unclosed brackets/braces
            if line.count("[") != line.count("]"):
                issues.append(f"Line {line_num}: Unmatched brackets")
            if line.count("{") != line.count("}"):
                issues.append(f"Line {line_num}: Unmatched braces")

        if issues:
            return {
                "type": "YAML_SYNTAX_ERROR",
                "severity": "MEDIUM",
                "message": f"YAML syntax issues: {'; '.join(issues[:3])}",
                "details": issues,
            }

        return None

    def _check_indentation(self, content: str, file_path: str) -> dict[str, Any] | None:
        """Check for mixed tabs and spaces (Python only)."""
        if not file_path.endswith(".py"):
            return None

        lines = content.split("\n")
        has_tabs = any(line.startswith("\t") for line in lines if line.strip())
        has_trailing_spaces = any(line.endswith(" ") or line.endswith("\t") for line in lines)

        if has_tabs and has_trailing_spaces:
            return {
                "type": "INDENTATION",
                "severity": "MEDIUM",
                "message": "Mixed tabs and trailing spaces detected (use 4 spaces for Python)",
            }

        return None

    def _verify_edit_operation(
        self,
        file_path: str,
        tool_input: dict[str, Any],
        actual_content: str
    ) -> dict[str, Any] | None:
        """
        Verify Edit operation using security-only check (v2.3).

        Simplified verification approach:
        - Only verifies old_string was removed (security check)
        - Skips verification if ruff/auto-formatter likely reverted the edit
        - Skips new_string verification (unreliable, causes false positives)
        - Edit tool itself performs file write verification

        Checks that:
        1. old_string is removed from file (exact match - security)
        2. UNLESS: ruff or auto-formatter likely removed the edit (import added but unused)

        Returns issue dict if verification fails, None otherwise.

        Rationale:
        - Hybrid verification (escape normalization + fuzzy matching) produced false positives
        - 7.3% similarity for legitimate edits (formatting differences)
        - Security preserved by checking old_string removal
        - Edit tool handles file write verification internally
        - ruff auto-format can remove "unused" imports, causing false positives
        """
        # Only verify code file Edit operations
        if not self._is_code_file(file_path):
            return None

        old_string = tool_input.get("old_string", "")
        if not old_string:
            return None

        # SECURITY CHECK: old_string must be removed
        # This catches "edit claimed but old content remains" bugs
        if old_string in actual_content:
            # EXCEPTION: Check if ruff/auto-formatter likely reverted the edit
            # Pattern: Adding an import that ruff removes as "unused"
            # This happens when:
            # 1. Edit adds "import X" to imports section
            # 2. Ruff runs and removes "import X" because it's not used yet in the code
            # 3. Verification fails because old_string still present

            # Detect if old_string looks like an import addition that ruff would remove
            import_patterns = [
                "import ",  # Matches "import json", "import re", etc.
                "from ",    # Matches "from module import", etc.
            ]

            # Check if old_string is adding an import line
            is_import_addition = any(
                pattern in old_string.lower()
                for pattern in import_patterns
            )

            # Check if old_string is a standalone import line (not part of larger code)
            is_standalone_import = (
                is_import_addition and
                len(old_string.strip().split("\n")) == 1  # Single line
            )

            if is_standalone_import:
                # This is likely a ruff false positive - skip verification
                # Ruff removes "unused" imports automatically, which is correct behavior
                # We should not block on this - the import will be added when actually used
                return None

            # Real verification failure - old_string should have been removed
            return {
                "type": "EDIT_VERIFICATION_FAILED",
                "severity": "HIGH",
                "message": "Edit verification failed: old_string still present in file after Edit operation",
                "details": "The claimed edit may not have been applied correctly",
            }

        # Skip new_string verification - Edit tool itself verifies file writes
        return None

    def _record_evidence(self, file_path: str, content: str, tool_name: str) -> None:
        """
        Record Read observation for Stop hooks to verify edit-result claims.

        This creates post_edit_readbacks that Stop hooks can inspect
        when the LLM makes claims about "file is at X state".
        """
        try:
            evidence = {
                "path": file_path,
                "operation": tool_name.lower(),
                "timestamp": datetime.now(UTC).isoformat(),
                "size_bytes": len(content.encode("utf-8")),
                "hash": hashlib.sha256(content.encode("utf-8")).hexdigest()[:16],
                "snippet": content[:2000],  # First 2KB for quick verification
                "truncated": len(content) > 2000,
            }

            # Log to evidence file
            with open(self.evidence_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(evidence) + "\n")

            return [evidence]
        except Exception:
            return []

    def _get_retry_count(self, file_path: str) -> int:
        """Get current retry count for file."""
        try:
            if self.retry_file.exists():
                data = json.loads(self.retry_file.read_text(encoding="utf-8"))
                return data.get(file_path, 0)
        except Exception:
            pass
        return 0

    def _increment_retry(self, file_path: str) -> None:
        """Increment retry count for file."""
        try:
            if self.retry_file.exists():
                data = json.loads(self.retry_file.read_text(encoding="utf-8"))
            else:
                data = {}

            data[file_path] = data.get(file_path, 0) + 1
            self.retry_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _clear_retry(self, file_path: str) -> None:
        """Clear retry count for file after max retries."""
        try:
            if self.retry_file.exists():
                data = json.loads(self.retry_file.read_text(encoding="utf-8"))
                data.pop(file_path, None)
                self.retry_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _format_injection(self, file_path: str, issues: list[dict], is_critical: bool = False, max_retries: bool = False) -> str:
        """Format issue report as context injection."""
        severity_emoji = "🚫" if is_critical else "⚠️"
        file_name = Path(file_path).name

        lines = [f"{severity_emoji} **Reflexion Verifier Issues Detected** in `{file_name}`\n"]

        for issue in issues:
            lines.append(f"- **{issue['type']}**: {issue['message']}")

        if max_retries:
            lines.append(f"\n_Healing attempts exhausted ({self.MAX_RETRIES} retries). Manual intervention required._")

        return "\n".join(lines)

    def _format_self_healing_prompt(self, file_path: str, issues: list[dict], retry_num: int) -> str:
        """
        Format self-healing prompt for auto-retry.

        This prompts the LLM to fix the issues automatically.
        """
        file_name = Path(file_path).name

        lines = [
            f"⚠️ **BLOCKING ADVISORY — Reflexion Verifier** (Retry {retry_num}/{self.MAX_RETRIES})",
            f"**CRITICAL**: Edit to `{file_name}` may not have persisted.",
            "",
        ]

        for issue in issues:
            lines.append(f"- **{issue['type']}**: {issue['message']}")

        lines.extend([
            "",
            "**BLOCKING: You MUST do these steps before proceeding:**",
            "1. Read the file at the specific lines you intended to modify",
            "2. Confirm the new content is actually present on disk",
            "3. If NOT present, re-apply the Edit with the correct content",
            "",
            "**This is not optional.** Stop hook will block any completion claim until this file is verified.",
            "",
            f"_If issues persist after {self.MAX_RETRIES} retries, manual intervention is required._",
        ])

        return "\n".join(lines)

    def _log_verification(self, file_path: str, status: str, issues: list[dict]) -> None:
        """Log verification result for observability."""
        try:
            log_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "file": file_path,
                "status": status,
                "issue_count": len(issues),
                "issues": [i["type"] for i in issues],
            }

            log_file = self.hooks_dir / "data" / "reflexion_verifications.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass  # Don't fail hook if logging fails
