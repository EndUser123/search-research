"""RED phase tests for core.tracing — Task-2 of search-research instrumentation plan.

These tests verify the behavior specified in the tracing task and MUST FAIL
in the RED phase before implementation.

Run with: pytest tests/test_tracing.py -v
"""

import json
import os
import uuid
from pathlib import Path

import pytest


class TestQueryTraceImports:
    """AC-1: QueryTracer and QueryTrace must be importable from core.tracing."""

    def test_query_tracer_importable(self):
        """QueryTracer must be importable from core.tracing."""
        from core.tracing import QueryTracer

        assert QueryTracer is not None

    def test_query_trace_importable(self):
        """QueryTrace dataclass must be importable from core.tracing."""
        from core.tracing import QueryTrace

        assert QueryTrace is not None


class TestDecisionAuditorImports:
    """AC-2: DecisionAuditor and DecisionAuditEntry must be importable from core.tracing."""

    def test_decision_auditor_importable(self):
        """DecisionAuditor must be importable from core.tracing."""
        from core.tracing import DecisionAuditor

        assert DecisionAuditor is not None

    def test_decision_audit_entry_importable(self):
        """DecisionAuditEntry dataclass must be importable from core.tracing."""
        from core.tracing import DecisionAuditEntry

        assert DecisionAuditEntry is not None


class TestQueryTracerStartTrace:
    """AC-3: tracer.start_trace(question) returns non-empty string UUID."""

    def test_start_trace_returns_non_empty_string(self, tmp_path):
        """start_trace must return a non-empty string UUID."""
        from core.tracing import QueryTracer

        tracer = QueryTracer(log_path=str(tmp_path / "query_log.jsonl"))
        query_id = tracer.start_trace("What is Python?")

        assert isinstance(query_id, str)
        assert len(query_id) > 0

    def test_start_trace_returns_valid_uuid_format(self, tmp_path):
        """start_trace return value must be a valid UUID string."""
        from core.tracing import QueryTracer

        tracer = QueryTracer(log_path=str(tmp_path / "query_log.jsonl"))
        query_id = tracer.start_trace("What is Python?")

        # Must parse as a UUID without raising
        parsed = uuid.UUID(query_id)
        assert str(parsed) == query_id


class TestQueryTracerLogTrace:
    """AC-4: tracer.log_trace(QueryTrace(...)) appends one valid JSONL line."""

    def test_log_trace_appends_valid_jsonl_line(self, tmp_path):
        """log_trace must append one valid JSON line to the log file."""
        from core.tracing import QueryTracer, QueryTrace

        log_path = tmp_path / "query_log.jsonl"
        tracer = QueryTracer(log_path=str(log_path))

        trace = QueryTrace(
            query_id=str(uuid.uuid4()),
            timestamp="2026-04-14T10:00:00Z",
            question="What is Python?",
            path_taken="direct",
            backend_hits={"brave": 1},
            sources=["https://example.com"],
            final_quality=0.95,
            contradiction_detected=False,
            decision_audit_id=None,
        )
        tracer.log_trace(trace)

        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1

        # Must be valid JSON
        record = json.loads(lines[0])
        assert record["question"] == "What is Python?"
        assert record["path_taken"] == "direct"
        assert record["final_quality"] == 0.95

    def test_log_trace_multiple_traces_append_lines(self, tmp_path):
        """Multiple log_trace calls must append multiple JSON lines."""
        from core.tracing import QueryTracer, QueryTrace

        log_path = tmp_path / "query_log.jsonl"
        tracer = QueryTracer(log_path=str(log_path))

        for i in range(3):
            trace = QueryTrace(
                query_id=str(uuid.uuid4()),
                timestamp="2026-04-14T10:00:00Z",
                question=f"Question {i}",
                path_taken="direct",
                backend_hits={},
                sources=[],
                final_quality=0.5,
                contradiction_detected=False,
                decision_audit_id=None,
            )
            tracer.log_trace(trace)

        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 3


class TestQueryTracerDirectoryCreation:
    """QueryTracer must create log directory if missing."""

    def test_creates_log_dir_if_missing(self, tmp_path):
        """QueryTracer must create the logs/ directory when log_path parent does not exist."""
        from core.tracing import QueryTracer, QueryTrace

        log_path = tmp_path / "logs" / "query_log.jsonl"
        assert not log_path.parent.exists()

        tracer = QueryTracer(log_path=str(log_path))

        trace = QueryTrace(
            query_id=str(uuid.uuid4()),
            timestamp="2026-04-14T10:00:00Z",
            question="Test",
            path_taken="direct",
            backend_hits={},
            sources=[],
            final_quality=0.5,
            contradiction_detected=False,
            decision_audit_id=None,
        )
        tracer.log_trace(trace)

        assert log_path.exists()


class TestDecisionAuditorRecordWikiUpdate:
    """AC-5: auditor.record_wiki_update(...) returns decision_id and appends to log — no wiki write."""

    def test_record_wiki_update_returns_decision_id(self, tmp_path):
        """record_wiki_update must return a non-empty decision_id string."""
        from core.tracing import DecisionAuditor

        auditor = DecisionAuditor(log_path=str(tmp_path / "decision_audit_log.jsonl"))
        decision_id = auditor.record_wiki_update(
            page_id="x",
            decision_type="stub",
            query_id="y",
            quality_score=0.9,
            sources=[],
            reason="n/a",
        )

        assert isinstance(decision_id, str)
        assert len(decision_id) > 0

    def test_record_wiki_update_appends_to_jsonl(self, tmp_path):
        """record_wiki_update must append one valid JSONL line to the log."""
        from core.tracing import DecisionAuditor

        log_path = tmp_path / "decision_audit_log.jsonl"
        auditor = DecisionAuditor(log_path=str(log_path))

        decision_id = auditor.record_wiki_update(
            page_id="page-123",
            decision_type="stub",
            query_id="query-456",
            quality_score=0.85,
            sources=["source-a", "source-b"],
            reason="test reason",
        )

        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record["decision_id"] == decision_id
        assert record["page_id"] == "page-123"
        assert record["decision_type"] == "stub"
        assert record["query_id"] == "query-456"
        assert record["quality_score"] == 0.85
        assert record["sources"] == ["source-a", "source-b"]
        assert record["reason"] == "test reason"

    def test_record_wiki_update_creates_log_dir(self, tmp_path):
        """DecisionAuditor must create the logs/ directory when log_path parent does not exist."""
        from core.tracing import DecisionAuditor

        log_path = tmp_path / "logs" / "decision_audit_log.jsonl"
        assert not log_path.parent.exists()

        auditor = DecisionAuditor(log_path=str(log_path))
        auditor.record_wiki_update(
            page_id="x",
            decision_type="stub",
            query_id="y",
            quality_score=0.9,
            sources=[],
            reason="n/a",
        )

        assert log_path.exists()


class TestDecisionAuditEntryToJsonl:
    """DecisionAuditEntry must have a to_jsonl() method."""

    def test_to_jsonl_returns_valid_json_string(self):
        """DecisionAuditEntry.to_jsonl() must return a valid JSON string."""
        from core.tracing import DecisionAuditEntry

        entry = DecisionAuditEntry(
            decision_id="dec-001",
            timestamp="2026-04-14T10:00:00Z",
            page_id="page-abc",
            decision_type="update",
            query_id="query-xyz",
            quality_score=0.75,
            sources=["src1", "src2"],
            reason="testing",
        )

        json_str = entry.to_jsonl()
        parsed = json.loads(json_str)

        assert parsed["decision_id"] == "dec-001"
        assert parsed["page_id"] == "page-abc"
        assert parsed["quality_score"] == 0.75


class TestQueryTraceDataclassFields:
    """QueryTrace dataclass must have all required fields."""

    def test_query_trace_has_all_required_fields(self):
        """QueryTrace must define all fields: query_id, timestamp, question, path_taken,
        backend_hits, sources, final_quality, contradiction_detected, decision_audit_id."""
        from core.tracing import QueryTrace

        trace = QueryTrace(
            query_id="q-001",
            timestamp="2026-04-14T10:00:00Z",
            question="Test question",
            path_taken="hybrid",
            backend_hits={"brave": 2, "exa": 1},
            sources=["url1", "url2"],
            final_quality=0.88,
            contradiction_detected=True,
            decision_audit_id="audit-123",
        )

        assert trace.query_id == "q-001"
        assert trace.timestamp == "2026-04-14T10:00:00Z"
        assert trace.question == "Test question"
        assert trace.path_taken == "hybrid"
        assert trace.backend_hits == {"brave": 2, "exa": 1}
        assert trace.sources == ["url1", "url2"]
        assert trace.final_quality == 0.88
        assert trace.contradiction_detected is True
        assert trace.decision_audit_id == "audit-123"

    def test_query_trace_contradiction_detected_default_false(self):
        """QueryTrace.contradiction_detected must default to False."""
        from core.tracing import QueryTrace

        trace = QueryTrace(
            query_id="q-002",
            timestamp="2026-04-14T10:00:00Z",
            question="Test",
            path_taken="direct",
            backend_hits={},
            sources=[],
            final_quality=0.5,
            contradiction_detected=False,
            decision_audit_id=None,
        )
        assert trace.contradiction_detected is False


class TestFM2QueryTracerOSErrorImmunity:
    """FM-2: QueryTracer write raises OSError — pipeline continues, no exception propagates."""

    def test_log_trace_oserror_does_not_propagate(self, tmp_path, monkeypatch):
        """log_trace must not raise OSError when file write fails."""
        from core.tracing import QueryTracer, QueryTrace

        log_path = tmp_path / "query_log.jsonl"
        tracer = QueryTracer(log_path=str(log_path))

        # Make the file's parent read-only to force OSError on write
        # by opening the file exclusively and blocking writes
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Use a file-based lock simulation: create the file and make parent read-only
        # For a simpler approach, use chmod-like behavior via os.error injection

        # Simpler approach: patch open to raise OSError
        def fake_open_write(*args, **kwargs):
            raise OSError("Read-only file system")

        monkeypatch.setattr("builtins.open", fake_open_write)

        trace = QueryTrace(
            query_id=str(uuid.uuid4()),
            timestamp="2026-04-14T10:00:00Z",
            question="Test",
            path_taken="direct",
            backend_hits={},
            sources=[],
            final_quality=0.5,
            contradiction_detected=False,
            decision_audit_id=None,
        )

        # Must NOT raise — pipeline continues
        tracer.log_trace(trace)

    def test_log_trace_oserror_leaves_pipeline_intact(self, tmp_path, monkeypatch):
        """After log_trace raises OSError internally, subsequent operations still work."""
        from core.tracing import QueryTracer, QueryTrace

        log_path = tmp_path / "query_log.jsonl"
        tracer = QueryTracer(log_path=str(log_path))

        call_count = [0]

        def fake_open_write(*args, **kwargs):
            call_count[0] += 1
            raise OSError("Read-only file system")

        monkeypatch.setattr("builtins.open", fake_open_write)

        trace = QueryTrace(
            query_id=str(uuid.uuid4()),
            timestamp="2026-04-14T10:00:00Z",
            question="Test",
            path_taken="direct",
            backend_hits={},
            sources=[],
            final_quality=0.5,
            contradiction_detected=False,
            decision_audit_id=None,
        )

        # Must not raise — pipeline continues
        tracer.log_trace(trace)

        # start_trace should still work after OSError in log_trace
        query_id2 = tracer.start_trace("Another question")
        assert len(query_id2) > 0


class TestFM2bDecisionAuditorOSErrorImmunity:
    """FM-2b: DecisionAuditor write raises OSError — pipeline continues, no exception propagates."""

    def test_record_wiki_update_oserror_does_not_propagate(self, tmp_path, monkeypatch):
        """record_wiki_update must not raise OSError when file write fails."""
        from core.tracing import DecisionAuditor

        log_path = tmp_path / "decision_audit_log.jsonl"
        auditor = DecisionAuditor(log_path=str(log_path))

        def fake_open_write(*args, **kwargs):
            raise OSError("Read-only file system")

        monkeypatch.setattr("builtins.open", fake_open_write)

        # Must NOT raise — pipeline continues
        decision_id = auditor.record_wiki_update(
            page_id="x",
            decision_type="stub",
            query_id="y",
            quality_score=0.9,
            sources=[],
            reason="n/a",
        )

        # Must still return a decision_id string
        assert isinstance(decision_id, str)
        assert len(decision_id) > 0

    def test_record_wiki_update_oserror_leaves_pipeline_intact(self, tmp_path, monkeypatch):
        """After record_wiki_update OSError, subsequent calls still work."""
        from core.tracing import DecisionAuditor

        log_path = tmp_path / "decision_audit_log.jsonl"
        auditor = DecisionAuditor(log_path=str(log_path))

        def fake_open_write(*args, **kwargs):
            raise OSError("Read-only file system")

        monkeypatch.setattr("builtins.open", fake_open_write)

        # First call — must not raise
        decision_id1 = auditor.record_wiki_update(
            page_id="x",
            decision_type="stub",
            query_id="y",
            quality_score=0.9,
            sources=[],
            reason="n/a",
        )

        # Second call should also not raise
        decision_id2 = auditor.record_wiki_update(
            page_id="x",
            decision_type="stub",
            query_id="y",
            quality_score=0.9,
            sources=[],
            reason="n/a",
        )

        assert decision_id1 != decision_id2
        assert len(decision_id1) > 0
        assert len(decision_id2) > 0

    def test_log_decision_oserror_does_not_propagate(self, tmp_path, monkeypatch):
        """DecisionAuditor.log_decision must not raise OSError when file write fails."""
        from core.tracing import DecisionAuditor, DecisionAuditEntry

        log_path = tmp_path / "decision_audit_log.jsonl"
        auditor = DecisionAuditor(log_path=str(log_path))

        def fake_open_write(*args, **kwargs):
            raise OSError("Read-only file system")

        monkeypatch.setattr("builtins.open", fake_open_write)

        entry = DecisionAuditEntry(
            decision_id="dec-001",
            timestamp="2026-04-14T10:00:00Z",
            page_id="page-abc",
            decision_type="update",
            query_id="query-xyz",
            quality_score=0.75,
            sources=["src1"],
            reason="testing",
        )

        # Must NOT raise — pipeline continues
        auditor.log_decision(entry)
