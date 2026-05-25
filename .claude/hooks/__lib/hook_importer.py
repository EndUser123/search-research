#!/usr/bin/env python3
"""
Hook Importer - In-Process Hook Execution
==========================================

Universal in-process hook executor with graceful fallback.

Eliminates subprocess.spawn() overhead (20-50ms) by running hooks
in the same process via dynamic module loading and thread-based execution.

Benefits:
- No subprocess.spawn() overhead (2-5x faster)
- No process contention/lockups with multiple terminals
- Direct Python object access to hook state
- Better error handling and return values
- Graceful fallback to subprocess if unavailable

Usage:
    from hook_importer import HookImporter

    importer = HookImporter('P:/.claude/hooks')
    result = importer.execute_hook('UserPromptSubmit', timeout=15.0)
    if result.get('ok'):
        print("Hook succeeded")
    else:
        print(f"Hook failed: {result.get('error')}")

Architecture:
- Lazy module loading with importlib.util
- Module caching (avoid re-import overhead)
- Thread-based timeout (daemon=True for isolation)
- Exception handling (hook failures don't crash importer)
- IO capture (stdin/stdout/stderr redirection)

Diagnostics:
- Primary anomaly sink: importer_diagnostics in diagnostics.db
- JSONL files are fallback-only if SQLite diagnostics are unavailable
- See PROTOCOL.md for the contract and CLAUDE.md for operator guidance
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import io
import json
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from threading import Thread
from typing import Any

try:
    from cc_diagnostic_logger import DIAGNOSTICS_ENABLED as SQLITE_DIAGNOSTICS_ENABLED
    from cc_diagnostic_logger import log_importer_anomaly
except Exception:
    SQLITE_DIAGNOSTICS_ENABLED = False
    log_importer_anomaly = None


class HookImporter:
    """Import and execute hooks in-process with error isolation."""

    def __init__(self, hooks_dir: str | Path):
        """Initialize hook importer for a directory.

        Args:
            hooks_dir: Directory containing hook .py files
        """
        self.hooks_dir = Path(hooks_dir)
        self._cache: dict[str, Any] = {}
        self._diag_dir = self.hooks_dir / "logs" / "diagnostics"
        # Track source file mtimes to proactively clear stale bytecode before import failures.
        # Cleared when source mtime advances — covers both subprocess and in-process invocations.
        self._source_mtimes: dict[str, float] = {}

    def _fallback_log_diag(self, filename: str, payload: dict[str, Any]) -> None:
        """Best-effort JSONL fallback when SQLite diagnostics are unavailable."""
        try:
            self._diag_dir.mkdir(parents=True, exist_ok=True)
            entry = {"timestamp": datetime.now(UTC).isoformat(), **payload}
            with (self._diag_dir / filename).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=True) + "\n")
        except Exception:
            # Diagnostics must never affect hook execution.
            pass

    @staticmethod
    def _extract_context(input_data: str) -> dict[str, Any]:
        """Extract small identifying fields from hook stdin for diagnostics."""
        input_hash = hashlib.md5(input_data.encode("utf-8", errors="ignore")).hexdigest()[:12]
        try:
            payload = json.loads(input_data)
        except Exception:
            return {"input_bytes": len(input_data), "input_hash": input_hash}

        context: dict[str, Any] = {"input_bytes": len(input_data), "input_hash": input_hash}

        session_value = payload.get("session_id") or payload.get("sessionId")
        if isinstance(session_value, str) and session_value.strip():
            context["session_id"] = session_value.strip()

        terminal_value = payload.get("terminal_id") or payload.get("terminalId")
        if isinstance(terminal_value, str) and terminal_value.strip():
            context["terminal_id"] = terminal_value.strip()

        tool_value = payload.get("tool_name") or payload.get("tool")
        if isinstance(tool_value, str) and tool_value.strip():
            context["tool_name"] = tool_value.strip()
        return context

    def _log_anomaly(
        self,
        phase: str,
        hook_name: str,
        error_text: str,
        input_context: dict[str, Any] | None = None,
        traceback_text: str | None = None,
        stderr_text: str | None = None,
    ) -> None:
        """Log importer anomalies to SQLite, falling back to JSONL if needed."""
        payload = {
            "hook_name": hook_name,
            "phase": phase,
            "session_id": (input_context or {}).get("session_id"),
            "terminal_id": (input_context or {}).get("terminal_id"),
            "tool_name": (input_context or {}).get("tool_name"),
            "input_hash": (input_context or {}).get("input_hash"),
            "input_bytes": (input_context or {}).get("input_bytes"),
            "error_text": error_text,
            "traceback": traceback_text,
        }
        if stderr_text:
            payload["stderr"] = stderr_text[:4000]

        if SQLITE_DIAGNOSTICS_ENABLED and log_importer_anomaly is not None:
            try:
                logged = log_importer_anomaly(
                    hook_name=hook_name,
                    phase=phase,
                    error_text=error_text,
                    session_id=payload["session_id"],
                    terminal_id=payload["terminal_id"],
                    tool_name=payload["tool_name"],
                    input_hash=payload["input_hash"],
                    input_bytes=payload["input_bytes"],
                    traceback_text=traceback_text,
                )
                if logged:
                    return
            except Exception:
                pass

        filename_map = {
            "load": "hook_importer_load_errors.jsonl",
            "stderr": "hook_importer_stderr.jsonl",
            "execute": "hook_importer_errors.jsonl",
            "timeout": "hook_importer_errors.jsonl",
        }
        self._fallback_log_diag(filename_map.get(phase, "hook_importer_errors.jsonl"), payload)

    def _clear_hook_bytecode(self, hook_name: str) -> None:
        """Clear bytecode cache for a specific hook file.

        Args:
            hook_name: Name of hook file without .py extension
        """
        pycache_dir = self.hooks_dir / "__pycache__"
        if not pycache_dir.exists():
            return

        version_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
        for ext in (".pyc", ".pyo"):
            pyc_file = pycache_dir / f"{hook_name}.{version_tag}{ext}"
            pyc_file.unlink(missing_ok=True)

    def load_hook(self, hook_name: str, input_context: dict[str, Any] | None = None) -> Any:
        """Load hook module dynamically (cached).

        Args:
            hook_name: Name of hook file without .py extension

        Returns:
            Loaded module object

        Raises:
            FileNotFoundError: If hook file doesn't exist
            ImportError: If hook file has import errors
        """
        # Validate hook name before constructing paths
        try:
            from __lib.path_sanitizer import validate_hook_name

            hook_name = validate_hook_name(hook_name)
        except (ValueError, ImportError):
            raise FileNotFoundError(f"Hook not found: {hook_name}")

        if hook_name in self._cache:
            return self._cache[hook_name]

        from __lib.path_sanitizer import sanitize_hook_path

        hook_path = sanitize_hook_path(self.hooks_dir / f"{hook_name}.py")
        if not hook_path.exists():
            raise FileNotFoundError(f"Hook not found: {hook_name}")

        spec = importlib.util.spec_from_file_location(hook_name, hook_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load spec for {hook_name}")

        module = importlib.util.module_from_spec(spec)

        # Add to sys.modules for relative imports within hook
        sys.modules[hook_name] = module

        try:
            hooks_dir_str = str(self.hooks_dir.resolve())
            if hooks_dir_str not in sys.path:
                sys.path.insert(0, hooks_dir_str)
            # Proactive stale bytecode clearing: if source file has been edited since last load,
            # clear its pyc so Python picks up the new source instead of the stale cached bytecode.
            current_mtime = hook_path.stat().st_mtime
            prior_mtime = self._source_mtimes.get(hook_name, 0)
            if current_mtime > prior_mtime:
                self._clear_hook_bytecode(hook_name)
                importlib.invalidate_caches()
            self._source_mtimes[hook_name] = current_mtime
            spec.loader.exec_module(module)
        except Exception as e:
            # Cleanup failed module
            if hook_name in sys.modules:
                del sys.modules[hook_name]

            # Capture original error for logging before retry may overwrite context
            original_error = e
            retry_error = None

            # Retry logic for stale bytecode (ImportError/SyntaxError only)
            if isinstance(e, (ImportError, SyntaxError)):
                self._clear_hook_bytecode(hook_name)

                # Retry import once after bytecode cleanup
                try:
                    spec = importlib.util.spec_from_file_location(hook_name, hook_path)
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Failed to load spec for {hook_name}")

                    module = importlib.util.module_from_spec(spec)
                    sys.modules[hook_name] = module

                    hooks_dir_str = str(self.hooks_dir.resolve())
                    if hooks_dir_str not in sys.path:
                        sys.path.insert(0, hooks_dir_str)
                    spec.loader.exec_module(module)
                    self._cache[hook_name] = module
                    return module
                except Exception as retry_exc:
                    # Retry failed - capture for logging, fall through to error handling
                    retry_error = retry_exc
                    if hook_name in sys.modules:
                        del sys.modules[hook_name]

            error_suffix = ""
            if retry_error is not None:
                error_suffix = f" (retry also failed: {type(retry_error).__name__}: {retry_error})"
            self._log_anomaly(
                phase="load",
                hook_name=hook_name,
                error_text=f"{type(original_error).__name__}: {original_error}{error_suffix}",
                input_context=input_context,
                traceback_text=traceback.format_exc(),
            )
            raise ImportError(f"Failed to execute {hook_name}: {original_error}")

        self._cache[hook_name] = module
        return module

    def execute_hook(self, hook_name: str, timeout: float = 15.0) -> dict[str, Any]:
        """Execute hook in-process with timeout and error isolation.

        Args:
            hook_name: Name of hook to execute
            timeout: Maximum seconds to wait for hook completion

        Returns:
            Dict with results:
            - ok: bool - True if hook succeeded
            - error: str - Error message if hook failed
            - output: str - Captured stdout from hook
        """
        input_data = ""
        input_context: dict[str, Any] = {}

        # Save original stdio
        old_stdin = sys.stdin
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            # Prepare stdin with JSON input (read from current stdin)
            # Guard against pytest stdin capture (OSError: reading from stdin while output is captured)
            try:
                input_data = sys.stdin.read()
            except OSError:
                input_data = "{}"
            input_context = self._extract_context(input_data)
            hook = self.load_hook(hook_name, input_context=input_context)
            sys.stdin = io.StringIO(input_data)
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

            # Execute with timeout in daemon thread
            result = [None]
            exception = [None]

            def target() -> None:
                try:
                    if hasattr(hook, 'main'):
                        exit_code = hook.main()
                        result[0] = {"ok": True, "exit_code": exit_code}
                    else:
                        raise AttributeError(f"Hook {hook_name} has no main() function")
                except SystemExit as e:
                    # Hook called sys.exit() - capture exit code
                    result[0] = {"ok": e.code == 0, "exit_code": e.code}
                except Exception as e:
                    exception[0] = e

            thread = Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=timeout)

            if thread.is_alive():
                self._log_anomaly(
                    phase="timeout",
                    hook_name=hook_name,
                    error_text=f"Hook timeout after {timeout}s",
                    input_context=input_context,
                )
                return {"ok": False, "error": f"Hook timeout after {timeout}s"}

            if exception[0]:
                self._log_anomaly(
                    phase="execute",
                    hook_name=hook_name,
                    error_text=f"{type(exception[0]).__name__}: {exception[0]}",
                    input_context=input_context,
                    traceback_text="".join(
                        traceback.format_exception(
                            type(exception[0]),
                            exception[0],
                            exception[0].__traceback__,
                        )
                    ),
                )
                return {"ok": False, "error": str(exception[0])}

            # Get output
            output = sys.stdout.getvalue()
            stderr_output = sys.stderr.getvalue()

            if result[0] is None:
                # Thread finished but result not set (shouldn't happen)
                self._log_anomaly(
                    phase="execute",
                    hook_name=hook_name,
                    error_text="Hook completed without result",
                    input_context=input_context,
                )
                return {"ok": False, "error": "Hook completed without result"}

            # Add captured output to result
            result[0]["output"] = output

            if stderr_output:
                self._log_anomaly(
                    phase="stderr",
                    hook_name=hook_name,
                    error_text=f"Captured stderr ({len(stderr_output)} bytes): {stderr_output[:500]}",
                    input_context=input_context,
                    stderr_text=stderr_output,
                )

            # Print output to actual stdout (for logging/debugging)
            if output:
                print(output, end='', file=old_stdout)

            return result[0]

        except Exception as e:
            self._log_anomaly(
                phase="execute",
                hook_name=hook_name,
                error_text=f"Hook importer error: {type(e).__name__}: {e}",
                input_context=self._extract_context(input_data),
                traceback_text=traceback.format_exc(),
            )
            return {"ok": False, "error": f"Hook importer error: {e}"}

        finally:
            # Restore stdio
            sys.stdin = old_stdin
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def create_hook_importer(hooks_dir: str | Path) -> HookImporter:
    """Factory function to create HookImporter instance.

    Args:
        hooks_dir: Directory containing hook .py files

    Returns:
        HookImporter instance
    """
    return HookImporter(hooks_dir)
