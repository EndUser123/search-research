"""T7: Task projection correctness — emit task events → query open_tasks() → assert lifecycle state."""

import sys
from pathlib import Path

# Add search-research to path
_SEARCH_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent.parent / "packages" / "search-research"
if _SEARCH_RESEARCH_DIR.exists():
    sys.path.insert(0, str(_SEARCH_RESEARCH_DIR))

import pytest
from datetime import datetime, timezone, timedelta

from .db import get_connection
from .task_projection import open_tasks, resolve_task

DB_PATH = Path("P:\\\\\\__csf/data/chat_history.db")


@pytest.fixture
def clean_task_table():
    """Ensure tasks table is clean before and after each test."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    # Wipe test tasks by provider prefix
    cursor.execute("DELETE FROM tasks WHERE task_id LIKE 'test_proj_%'")
    conn.commit()
    yield
    cursor.execute("DELETE FROM tasks WHERE task_id LIKE 'test_proj_%'")
    conn.commit()


class TestOpenTasks:
    """T7: Task projection correctness."""

    def test_open_tasks_returns_empty_when_none_exist(self, clean_task_table):
        """No tasks → empty list."""
        assert open_tasks() == []

    def test_open_tasks_returns_only_unresolved(self, clean_task_table):
        """Resolved tasks must not appear."""
        conn = get_connection(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_1", "claude_code_raw", now, now, "resolved"),
        )
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_2", "claude_code_raw", now, None, "open"),
        )
        conn.commit()

        result = open_tasks()
        assert len(result) == 1
        assert result[0]["task_id"] == "test_proj_2"

    def test_open_tasks_ordered_by_opened_at_desc(self, clean_task_table):
        """Open tasks are sorted newest-first."""
        conn = get_connection(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc)
        earlier = (now - timedelta(hours=1)).isoformat()
        later = now.isoformat()
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_early", "claude_code_raw", earlier, None, "open"),
        )
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_late", "claude_code_raw", later, None, "open"),
        )
        conn.commit()

        result = open_tasks()
        assert result[0]["task_id"] == "test_proj_late"
        assert result[1]["task_id"] == "test_proj_early"

    def test_open_tasks_filtered_by_provider(self, clean_task_table):
        """provider_id filter returns only that provider's open tasks."""
        conn = get_connection(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_a", "claude_code_raw", now, None, "open"),
        )
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_b", "codex_desktop", now, None, "open"),
        )
        conn.commit()

        result = open_tasks(provider_id="claude_code_raw")
        assert len(result) == 1
        assert result[0]["task_id"] == "test_proj_a"

        result_all = open_tasks()
        assert len(result_all) == 2


class TestResolveTask:
    """T7: resolve_task marks a task as resolved."""

    def test_resolve_task_updates_resolved_at_and_status(self, clean_task_table):
        """resolve_task sets resolved_at timestamp and status='resolved'."""
        conn = get_connection(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_resolve", "claude_code_raw", now, None, "open"),
        )
        conn.commit()

        result = resolve_task("test_proj_resolve")
        assert result is True

        # Verify task is now resolved
        conn2 = get_connection(DB_PATH)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT resolved_at, status FROM tasks WHERE task_id = ?", ("test_proj_resolve",))
        row = cursor2.fetchone()
        assert row is not None
        assert row[0] is not None  # resolved_at is set
        assert row[1] == "resolved"

    def test_resolve_task_returns_false_if_not_found(self, clean_task_table):
        """resolve_task returns False for non-existent task."""
        result = resolve_task("test_proj_nonexistent")
        assert result is False

    def test_resolve_task_returns_false_if_already_resolved(self, clean_task_table):
        """resolve_task is idempotent: returns False if already resolved."""
        conn = get_connection(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_already", "claude_code_raw", now, now, "resolved"),
        )
        conn.commit()

        result = resolve_task("test_proj_already")
        assert result is False

    def test_resolve_task_with_custom_timestamp(self, clean_task_table):
        """resolve_task uses provided timestamp when given."""
        conn = get_connection(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_custom_ts", "claude_code_raw", now, None, "open"),
        )
        conn.commit()

        custom_ts = "2026-01-01T00:00:00+00:00"
        resolve_task("test_proj_custom_ts", resolved_at=custom_ts)

        conn2 = get_connection(DB_PATH)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT resolved_at FROM tasks WHERE task_id = ?", ("test_proj_custom_ts",))
        row = cursor2.fetchone()
        assert row[0] == custom_ts

    def test_resolved_task_no_longer_in_open_tasks(self, clean_task_table):
        """After resolve_task, the task disappears from open_tasks."""
        conn = get_connection(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (task_id, provider_id, opened_at, resolved_at, status) VALUES (?, ?, ?, ?, ?)",
            ("test_proj_cycle", "claude_code_raw", now, None, "open"),
        )
        conn.commit()

        assert len(open_tasks(provider_id="claude_code_raw")) == 1

        resolve_task("test_proj_cycle")

        assert len(open_tasks(provider_id="claude_code_raw")) == 0
