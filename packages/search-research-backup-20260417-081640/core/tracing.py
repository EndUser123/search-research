"""Tracing instrumentation for query and decision audit logging."""

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class QueryTrace:
    """Query trace record with all instrumentation fields."""

    query_id: str
    timestamp: str
    question: str
    path_taken: str
    backend_hits: dict[str, int]
    sources: list[str]
    final_quality: float
    contradiction_detected: bool
    decision_audit_id: Optional[str] = None

    def to_jsonl(self) -> str:
        """Serialize to JSON line format."""
        return json.dumps(asdict(self))


@dataclass
class DecisionAuditEntry:
    """Decision audit entry for wiki update decisions."""

    decision_id: str
    timestamp: str
    page_id: str
    decision_type: str
    query_id: str
    quality_score: float
    sources: list[str]
    reason: str

    def to_jsonl(self) -> str:
        """Serialize to JSON line format."""
        return json.dumps(asdict(self))


class QueryTracer:
    """Logs query traces to JSONL file."""

    def __init__(self, log_path: str = "logs/query_log.jsonl") -> None:
        """Initialize tracer with log file path.

        Creates the log directory if it does not exist.
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def start_trace(self, question: str) -> str:
        """Start a new query trace.

        Returns a UUID string identifying the trace.
        """
        return str(uuid.uuid4())

    def log_trace(self, trace: QueryTrace) -> None:
        """Append a QueryTrace record to the log file.

        Silently continues on OSError (pipeline continues).
        """
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(trace.to_jsonl() + "\n")
        except OSError:
            pass


class DecisionAuditor:
    """Logs decision audit entries to JSONL file."""

    def __init__(self, log_path: str = "logs/decision_audit_log.jsonl") -> None:
        """Initialize auditor with log file path.

        Creates the log directory if it does not exist.
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_decision(self, entry: DecisionAuditEntry) -> None:
        """Append a DecisionAuditEntry to the log file.

        Silently continues on OSError (pipeline continues).
        """
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(entry.to_jsonl() + "\n")
        except OSError:
            pass

    def record_wiki_update(
        self,
        page_id: str,
        decision_type: str,
        query_id: str,
        quality_score: float,
        sources: list[str],
        reason: str,
    ) -> str:
        """Record a wiki update decision.

        This is a STUB implementation - no wiki write occurs.
        Creates a DecisionAuditEntry and logs it, returns the decision_id.

        Returns the decision_id UUID string.
        """
        decision_id = str(uuid.uuid4())
        entry = DecisionAuditEntry(
            decision_id=decision_id,
            timestamp="2026-04-14T10:00:00Z",  # stub timestamp
            page_id=page_id,
            decision_type=decision_type,
            query_id=query_id,
            quality_score=quality_score,
            sources=sources,
            reason=reason,
        )
        self.log_decision(entry)
        return decision_id
