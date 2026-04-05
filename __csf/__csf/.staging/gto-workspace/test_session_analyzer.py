"""Tests for session_analyzer module."""


import pytest
from scripts.session_analyzer import SessionAnalyzer


def test_session_analyzer_initialization():
    """Test SessionAnalyzer can be initialized with a transcript path."""
    analyzer = SessionAnalyzer(transcript_path="test.jsonl")
    assert analyzer.transcript_path == "test.jsonl"


def test_session_analyzer_extract_todos_from_conversation():
    """Test extracting TODO/FIXME markers from conversation text."""
    analyzer = SessionAnalyzer(transcript_path="test.jsonl")

    # Sample conversation with TODO markers
    conversation = """
    User: I need to fix the authentication bug
    Assistant: I'll help with that. There's a TODO in auth.py line 45.
    User: Also check FIXME in login.py
    """

    todos = analyzer.extract_todos(conversation)
    assert len(todos) == 2
    assert any("auth.py" in todo for todo in todos)
    assert any("login.py" in todo for todo in todos)


def test_session_analyzer_detect_unfinished_work():
    """Test detecting unfinished work from conversation."""
    analyzer = SessionAnalyzer(transcript_path="test.jsonl")

    conversation = """
    User: Implement the feature
    Assistant: I'll start working on it now.
    User: Let me know when done
    [No completion message]
    """

    unfinished = analyzer.detect_unfinished_work(conversation)
    assert len(unfinished) > 0
    assert any("working" in task.lower() or "start" in task.lower() for task in unfinished)


def test_session_analyzer_analyze_session():
    """Test full session analysis returns structured report."""
    analyzer = SessionAnalyzer(transcript_path="test.jsonl")

    report = analyzer.analyze_session()

    assert "todos" in report
    assert "unfinished_work" in report
    assert "session_metrics" in report
    assert isinstance(report["todos"], list)
    assert isinstance(report["unfinished_work"], list)


@pytest.mark.parametrize("file_content,expected_count", [
    ("# TODO: Fix this bug\n# TODO: Add feature", 2),
    ("No todos here", 0),
    ("FIXME: broken", 1),
])
def test_extract_todos_various_formats(file_content, expected_count):
    """Test TODO extraction handles various comment formats."""
    analyzer = SessionAnalyzer(transcript_path="test.jsonl")
    todos = analyzer.extract_todos(file_content)
    assert len(todos) == expected_count
