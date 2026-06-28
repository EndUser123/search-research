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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook


@dataclass
class DeferredEdit:
    """A single Edit queued for batch verification."""
    file_path: str
    old_string: str
    tool_input: dict[str, Any]
    queued_at: datetime


class ReflexionVerifier(PostToolUseHook):
    STRUCTURED_DATA_EXTENSIONS = {".json", ".yaml", ".yml"}

    # Max retry iterations for self-healing
    MAX_RETRIES = 3

    # Truncation threshold (warning if file < 50% of expected size)
    TRUNCATION_THRESHOLD = 0.5

    # Maximum file size to verify (10 MB) - prevents OOM
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # Flush triggers
    _IDLE_FLUSH_SECONDS = 5.0

    # Binary file extensions to skip
    BINARY_EXTENSIONS = {
        ".exe", ".dll", ".so", ".dylib", ".bin", ".obj",
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
        ".pdf", ".zip", ".gz", ".tar", ".rar", ".7z",
        ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".webm",
        ".woff", ".woff2", ".ttf", ".eot", ".otf",
    }

    # Code file extensions to verify
    CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs"}

    def __init__(self):
        super().__init__()
        self.hooks_dir = Path(__file__).resolve().parent.parent
        from _bootstrap import state_root
        self.session_dir = state_root()
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

        # FLUSH SENTINEL: tool_name "" signals end of task — flush all deferred
        if not tool_name:
            if hasattr(self, "_deferred_verifies"):
                for key in list(self._deferred_verifies.keys()):
                    self._flush_deferred_verifies(key)
            return result

        # P0: Check for idle timeout flush on previously-seen files
        import time as _time
        if hasattr(self, "_idle_timestamps"):
            for key, last_ts in list(self._idle_timestamps.items()):
                if last_ts > 0 and (_time.time() - last_ts) > self._IDLE_FLUSH_SECONDS:
                    # Resolve path from key to get file_path
                    p = Path(key)
                    issues = self._flush_deferred_verifies(str(p))
                    if issues:
                        # Inject the failure as a warning (non-blocking)
                        result["status"] = "FAIL"
                        result["injection"] = self._format_injection(key, issues)

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

        key = str(Path(file_path).resolve())

        # Initialize deferred buffer and idle tracker on first Edit to this file
        if not hasattr(self, "_deferred_verifies"):
            self._deferred_verifies: dict[str, list[DeferredEdit]] = {}
        if not hasattr(self, "_idle_timestamps"):
            self._idle_timestamps: dict[str, float] = {}

        # Check if we should flush due to idle timeout (same file, > 5s since last Edit)
        import time as _time
        last_ts = self._idle_timestamps.get(key, 0)
        if last_ts > 0 and (_time.time() - last_ts) > self._IDLE_FLUSH_SECONDS:
            # Idle timeout — flush pending verifications for this file
            self._flush_deferred_verifies(file_path)

        # Buffer this Edit for deferred verification
        deferred = DeferredEdit(
            file_path=file_path,
            old_string=old_string,
            tool_input=tool_input,
            queued_at=datetime.now(UTC),
        )
        self._deferred_verifies.setdefault(key, []).append(deferred)
        self._idle_timestamps[key] = _time.time()

        # Returning None = skip immediate verification, defer to flush
        return None

    def _flush_deferred_verifies(self, file_path: str) -> list[dict[str, Any]]:
        """
        Flush all deferred verifications for file_path, newest-to-oldest.

        Returns list of issue dicts (same shape as _verify_edit_operation returns).
        """
        key = str(Path(file_path).resolve())
        deferred_list = self._deferred_verifies.get(key, [])
        if not deferred_list:
            return []

        # Clear buffer immediately — prevent double-flush on recursive call
        del self._deferred_verifies[key]

        # Remove idle tracker
        self._idle_timestamps.pop(key, None)

        # Sort newest-first: most recent old_string verified first
        deferred_list.sort(key=lambda d: d.queued_at, reverse=True)

        issues: list[dict[str, Any]] = []
        # Read file ONCE for all verifications
        actual_content = self._read_file_from_disk(file_path) or ""

        for deferred in deferred_list:
            old_string = deferred.old_string
            if old_string not in actual_content:
                # old_string correctly absent — pass
                continue

            # Exception: ruff removed a standalone import addition
            is_import_addition = (
                len(old_string.strip().split("\n")) == 1
                and ("import " in old_string.lower() or old_string.strip().startswith("from "))
            )
            if is_import_addition:
                continue

            issues.append({
                "type": "EDIT_VERIFICATION_FAILED",
                "severity": "HIGH",
                "message": "Deferred edit verification failed: old_string still present after batch of edits",
                "details": f"old_string: {old_string[:100]!r}",
            })

        return issues

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
