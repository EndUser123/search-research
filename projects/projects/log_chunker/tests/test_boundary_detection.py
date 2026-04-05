from log_chunker.data_models import LogEntry
from log_chunker.plugins.boundary_config import BoundaryConfig
from log_chunker.plugins.boundary_detection import BoundaryDetector


def test_basic_chunking():
    config = BoundaryConfig(
        tag_weights={"error": 5.0, "warning": 3.0},
        threshold=8.0,
        min_chunk_size=2,
        max_chunk_size=5,
        boundary_patterns=[r"^---.*---$"],
    )

    detector = BoundaryDetector(config)

    # Create test log entries
    entries = [
        LogEntry(
            line_number=1,
            message="Info message",
            tags=["info"],
            timestamp=None,
            level="INFO",
            original_line="Info message",
        ),
        LogEntry(
            line_number=2,
            message="Warning message",
            tags=["warning"],
            timestamp=None,
            level="WARNING",
            original_line="Warning message",
        ),
        LogEntry(
            line_number=3,
            message="Error message",
            tags=["error"],
            timestamp=None,
            level="ERROR",
            original_line="Error message",
        ),  # Boundary (5+3=8)
        LogEntry(
            line_number=4,
            message="Another info",
            tags=["info"],
            timestamp=None,
            level="INFO",
            original_line="Another info",
        ),
        LogEntry(
            line_number=5,
            message="--- boundary ---",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="--- boundary ---",
        ),  # Explicit boundary
        LogEntry(
            line_number=6,
            message="Final message",
            tags=["info"],
            timestamp=None,
            level="INFO",
            original_line="Final message",
        ),
    ]

    chunks = detector.detect_boundaries(entries)

    # Should create 3 chunks: [1-3], [4], [5-6]
    assert len(chunks) == 3
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 3
    assert chunks[1].start_line == 4
    assert chunks[1].end_line == 4
    assert chunks[2].start_line == 5
    assert chunks[2].end_line == 6


def test_min_chunk_size():
    config = BoundaryConfig(
        tag_weights={"error": 10.0},
        threshold=5.0,
        min_chunk_size=3,
        max_chunk_size=10,
        boundary_patterns=[],
    )

    detector = BoundaryDetector(config)

    entries = [
        LogEntry(
            line_number=1,
            message="Info",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Info",
        ),
        LogEntry(
            line_number=2,
            message="Error",
            tags=["error"],
            timestamp=None,
            level="ERROR",
            original_line="Error",
        ),  # Score=10, but min size not reached
        LogEntry(
            line_number=3,
            message="Info",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Info",
        ),
        LogEntry(
            line_number=4,
            message="Info",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Info",
        ),
        LogEntry(
            line_number=5,
            message="Error",
            tags=["error"],
            timestamp=None,
            level="ERROR",
            original_line="Error",
        ),  # Boundary
    ]

    chunks = detector.detect_boundaries(entries)

    # Should create 1 chunk since min size wasn't reached until end
    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 5


def test_max_chunk_size():
    config = BoundaryConfig(
        tag_weights={},
        threshold=100.0,  # Never reached
        min_chunk_size=1,
        max_chunk_size=3,
        boundary_patterns=[],
    )

    detector = BoundaryDetector(config)

    entries = [
        LogEntry(
            line_number=1,
            message="Msg1",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Msg1",
        ),
        LogEntry(
            line_number=2,
            message="Msg2",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Msg2",
        ),
        LogEntry(
            line_number=3,
            message="Msg3",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Msg3",
        ),  # Max size reached
        LogEntry(
            line_number=4,
            message="Msg4",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Msg4",
        ),
        LogEntry(
            line_number=5,
            message="Msg5",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Msg5",
        ),
    ]

    chunks = detector.detect_boundaries(entries)

    # Should create 2 chunks: [1-3], [4-5]
    assert len(chunks) == 2
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 3
    assert chunks[1].start_line == 4
    assert chunks[1].end_line == 5


def test_explicit_boundary():
    config = BoundaryConfig(
        tag_weights={"error": 5.0},
        threshold=10.0,
        min_chunk_size=1,
        max_chunk_size=10,
        boundary_patterns=[r"^====.*====$"],
    )

    detector = BoundaryDetector(config)

    entries = [
        LogEntry(
            line_number=1,
            message="Info",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Info",
        ),
        LogEntry(
            line_number=2,
            message="==== boundary ====",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="==== boundary ====",
        ),  # Explicit boundary
        LogEntry(
            line_number=3,
            message="Error",
            tags=["error"],
            timestamp=None,
            level="ERROR",
            original_line="Error",
        ),
        LogEntry(
            line_number=4,
            message="Info",
            tags=[],
            timestamp=None,
            level="INFO",
            original_line="Info",
        ),
    ]

    chunks = detector.detect_boundaries(entries)

    # Should create 3 chunks: [1], [2], [3-4]
    assert len(chunks) == 3
    assert chunks[0].start_line == 1
    assert chunks[1].start_line == 2
    assert chunks[2].start_line == 3
