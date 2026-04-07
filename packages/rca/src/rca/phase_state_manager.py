"""Phase State Manager for rca Tier 1.

Manages persistence of phase outputs for resumable RCA sessions.
"""

import json
import sys
import warnings
import weakref
from datetime import datetime
from pathlib import Path
from typing import Any

# Spool directory for CKS fallback storage
SPOOL_DIR = "P:/.claude/state/debugrca_phase_spool/"


def _get_cks_class():
    """Lazy import CKS to avoid deprecation warnings during import.

    Returns:
        CKS class if available, None otherwise.

    Raises:
        ImportError: Only raised if CKS path exists but import fails.
    """
    import os

    _csf_src = os.environ.get("CSF_SRC", "P:/__csf/src")
    _csf_src_path = str(Path(_csf_src).resolve())

    # Check if the CSF src path exists before adding to sys.path
    if not Path(_csf_src_path).exists():
        return None

    if _csf_src_path not in sys.path:
        sys.path.insert(0, _csf_src_path)

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            from cks.unified import CKS
        return CKS
    except ImportError:
        return None


def _parse_cks_metadata(metadata_json: str) -> dict[str, Any]:
    """Parse CKS metadata JSON and extract inner metadata.

    CKS wraps custom metadata in an inner 'metadata' key.
    This function handles both wrapped and unwrapped formats.

    Args:
        metadata_json: JSON string from CKS metadata field.

    Returns:
        Parsed metadata dictionary.
    """
    outer_metadata = json.loads(metadata_json) if metadata_json else {}
    return outer_metadata.get("metadata", outer_metadata)


class PhaseStateManager:
    """Manages phase state persistence using CKS.

    Allows RCA sessions to be resumed by persisting phase outputs
    and tracking which phases have been completed.

    Attributes:
        state_dir: Directory for state storage.
        enabled: Whether state persistence is enabled.

    Examples:
        >>> manager = PhaseStateManager()
        >>> state_id = manager.save("gather", {"evidence": [...]}, "session-123")
        >>> restored = manager.restore(state_id)
        >>> manager.list_phases("session-123")
        ["gather"]
    """

    # Phase order for resume point calculation
    PHASE_ORDER = ["gather", "isolate", "hypothesize", "test", "fix"]

    def __init__(self, state_dir: str | None = None, enabled: bool = True):
        """Initialize the phase state manager.

        Args:
            state_dir: Custom state directory path.
            enabled: Whether state persistence is enabled.
        """
        from .config import get_state_dir

        self.state_dir = state_dir or get_state_dir()
        self.enabled = enabled
        self._cks = None
        self._cks_owner = False
        self._closed = False
        self._spool_mode = False

        # Validate state_dir is writable
        try:
            Path(self.state_dir).mkdir(parents=True, exist_ok=True)
            test_file = Path(self.state_dir) / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
        except OSError as e:
            warnings.warn(f"PhaseStateManager: state_dir is not writable: {self.state_dir} ({e})")

        if enabled:
            CKS = _get_cks_class()
            if CKS is not None:
                db_path = f"{self.state_dir}/phase_state.db"
                self._cks = CKS(db_path=db_path)
                self._cks_owner = True

                # Register finalizer to guarantee cleanup even if __del__ is not called
                # This is more reliable than __del__ for ensuring resource cleanup
                self._finalizer = weakref.finalize(self, self._cleanup_cks_connection, self._cks)
            else:
                # Fall back to spool directory for file-based storage
                self._spool_mode = True
                self._spool_dir = Path(SPOOL_DIR)
                self._spool_dir.mkdir(parents=True, exist_ok=True)
                self._finalizer = None
        else:
            # No cleanup needed for disabled manager
            self._finalizer = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes CKS connection."""
        self.close()
        return False

    def __del__(self):
        """Destructor - ensures CKS connection is closed.

        This is a fallback cleanup mechanism. The primary cleanup should
        happen via context manager or explicit close() call. weakref.finalize
        is also registered for additional reliability.
        """
        self.close()

    @staticmethod
    def _cleanup_cks_connection(cks_connection) -> None:
        """Static method to close CKS connection (used by weakref.finalize).

        Args:
            cks_connection: The CKS instance to close (may be None).
        """
        if cks_connection is not None:
            try:
                cks_connection.close()
            except Exception:
                # Silently ignore errors during cleanup
                pass

    def close(self) -> None:
        """Explicitly close the CKS connection.

        This should be called when done using the manager outside of a
        context manager to avoid ResourceWarnings about unclosed connections.

        The method is idempotent - safe to call multiple times.
        """
        if self._closed:
            return

        if self._cks_owner and self._cks is not None:
            try:
                self._cks.close()
            except Exception:
                pass  # Silently ignore errors during close

        # Detach finalizer since we've already cleaned up
        if self._finalizer is not None and self._finalizer.alive:
            self._finalizer.detach()

        self._closed = True
        self._cks = None

    def save(self, phase: str, output: dict[str, Any], session_id: str) -> str:
        """Save phase output to CKS or spool directory.

        Args:
            phase: Phase name (gather, isolate, hypothesize, test, fix).
            output: Phase output data to persist.
            session_id: Unique session identifier.

        Returns:
            The state ID for retrieval, or empty string if disabled.

        Examples:
            >>> manager = PhaseStateManager()
            >>> state_id = manager.save("gather", {"evidence": []}, "session-123")
            >>> isinstance(state_id, str)
            True
        """
        if not self.enabled:
            return ""

        title = f"{session_id}:{phase}"
        content = json.dumps(output) if output else "{}"
        metadata = {
            "session_id": session_id,
            "phase": phase,
            "output": output,
        }

        if self._spool_mode:
            # Spool mode: save to JSON file
            import hashlib

            entry_id = hashlib.sha256(f"{session_id}:{phase}".encode()).hexdigest()[:16]
            spool_file = self._spool_dir / f"{entry_id}.json"
            spool_data = {
                "id": entry_id,
                "title": title,
                "content": content,
                "type": "rca_phase_state",
                "metadata": metadata,
            }
            spool_file.write_text(json.dumps(spool_data, indent=2), encoding="utf-8")
            return entry_id

        entry_id = self._cks.ingest_pattern(
            title=title,
            content=content,
            entry_type="rca_phase_state",
            metadata=metadata,
        )

        return entry_id

    def restore(self, state_id: str) -> dict[str, Any] | None:
        """Restore phase state from CKS or spool directory.

        Args:
            state_id: The state ID returned by save().

        Returns:
            The restored phase state with flattened keys, or None if not found.

        Examples:
            >>> manager = PhaseStateManager()
            >>> state = manager.restore("state_id")
            >>> state["phase"]
            "gather"
        """
        if not self.enabled or not state_id:
            return None

        if self._spool_mode:
            # Spool mode: restore from JSON file
            spool_file = self._spool_dir / f"{state_id}.json"
            if spool_file.exists():
                try:
                    spool_data = json.loads(spool_file.read_text(encoding="utf-8"))
                    inner_metadata = spool_data.get("metadata", {})
                    output = inner_metadata.get("output", {})
                    result = {
                        "phase": inner_metadata.get("phase"),
                        "session_id": inner_metadata.get("session_id"),
                    }
                    if isinstance(output, dict):
                        result.update(output)
                    return result
                except Exception:
                    pass
            return None

        cursor = None
        try:
            cursor = self._cks.conn.cursor()
            cursor.execute("SELECT title, content, metadata FROM entries WHERE id = ?", (state_id,))
            row = cursor.fetchone()
            if row:
                _, _, metadata_json = row
                inner_metadata = _parse_cks_metadata(metadata_json)
                output = inner_metadata.get("output", {})

                result = {
                    "phase": inner_metadata.get("phase"),
                    "session_id": inner_metadata.get("session_id"),
                }
                if isinstance(output, dict):
                    result.update(output)
                return result
        except Exception:
            pass
        finally:
            if cursor:
                cursor.close()

        return None

    def list_phases(self, session_id: str) -> list[str]:
        """List completed phases for a session.

        Args:
            session_id: The session identifier.

        Returns:
            List of completed phase names in PHASE_ORDER.

        Examples:
            >>> manager = PhaseStateManager()
            >>> manager.list_phases("session-123")
            ["gather", "isolate"]
        """
        if not self.enabled:
            return []

        if self._spool_mode:
            # Spool mode: list from JSON files
            phases = []
            try:
                for spool_file in self._spool_dir.glob("*.json"):
                    try:
                        spool_data = json.loads(spool_file.read_text(encoding="utf-8"))
                        inner_metadata = spool_data.get("metadata", {})
                        if inner_metadata.get("session_id") == session_id:
                            phase = inner_metadata.get("phase")
                            if phase and phase in self.PHASE_ORDER and phase not in phases:
                                phases.append(phase)
                    except Exception:
                        continue
                return [p for p in self.PHASE_ORDER if p in phases]
            except Exception:
                return []

        cursor = None
        try:
            cursor = self._cks.conn.cursor()
            cursor.execute("SELECT metadata FROM entries WHERE type = ?", ("rca_phase_state",))
            phases = []
            for row in cursor.fetchall():
                metadata_json = row[0]
                inner_metadata = _parse_cks_metadata(metadata_json)
                if inner_metadata.get("session_id") == session_id:
                    phase = inner_metadata.get("phase")
                    if phase and phase in self.PHASE_ORDER and phase not in phases:
                        phases.append(phase)

            return [p for p in self.PHASE_ORDER if p in phases]
        except Exception:
            return []
        finally:
            if cursor:
                cursor.close()

    def get_resume_point(self, session_id: str) -> str | None:
        """Get the next phase to execute for a session.

        Args:
            session_id: The session identifier.

        Returns:
            The next phase name, or None if all phases complete.

        Examples:
            >>> manager = PhaseStateManager()
            >>> manager.get_resume_point("session-123")
            "isolate"
        """
        completed = self.list_phases(session_id)
        for phase in self.PHASE_ORDER:
            if phase not in completed:
                return phase
        return None

    def export_session(self, session_id: str) -> dict[str, Any]:
        """Export all phase states for a session.

        Creates a comprehensive export of all completed phases for a session,
        including phase data and resume point information.

        Args:
            session_id: The session identifier.

        Returns:
            A dictionary with keys: session_id, phases (dict), resume_point,
            and metadata (with export_timestamp).

        Examples:
            >>> manager = PhaseStateManager()
            >>> export = manager.export_session("session-123")
            >>> export["resume_point"]
            "isolate"
        """
        export_data: dict[str, Any] = {
            "session_id": session_id,
            "phases": {},
            "resume_point": None,
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
            },
        }

        if not self.enabled:
            export_data["resume_point"] = "gather"
            return export_data

        if self._spool_mode:
            # Spool mode: export from JSON files
            try:
                for spool_file in self._spool_dir.glob("*.json"):
                    try:
                        spool_data = json.loads(spool_file.read_text(encoding="utf-8"))
                        inner_metadata = spool_data.get("metadata", {})
                        if inner_metadata.get("session_id") == session_id:
                            phase = inner_metadata.get("phase")
                            output = inner_metadata.get("output", {})
                            if phase and isinstance(output, dict):
                                export_data["phases"][phase] = output
                    except Exception:
                        continue
            except Exception:
                pass
        else:
            cursor = None
            try:
                cursor = self._cks.conn.cursor()
                cursor.execute("SELECT metadata FROM entries WHERE type = ?", ("rca_phase_state",))

                for row in cursor.fetchall():
                    metadata_json = row[0]
                    inner_metadata = _parse_cks_metadata(metadata_json)

                    if inner_metadata.get("session_id") == session_id:
                        phase = inner_metadata.get("phase")
                        output = inner_metadata.get("output", {})

                        if phase and isinstance(output, dict):
                            export_data["phases"][phase] = output

            except Exception:
                pass
            finally:
                if cursor:
                    cursor.close()

        export_data["resume_point"] = self.get_resume_point(session_id)
        return export_data
