"""Tests for rebuild_qmd_index.py."""
import sys
import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))


def test_script_imports():
    """Script can be imported without errors."""
    import rebuild_qmd_index
    assert hasattr(rebuild_qmd_index, "_add_with_retry")
    assert hasattr(rebuild_qmd_index, "_clear_gpu_cache")


def test_has_retry_function():
    """Script has _add_with_retry for OOM recovery."""
    import rebuild_qmd_index
    assert callable(rebuild_qmd_index._add_with_retry)


def test_has_gpu_cache_clear_function():
    """Script has _clear_gpu_cache for VRAM management."""
    import rebuild_qmd_index
    assert callable(rebuild_qmd_index._clear_gpu_cache)


def test_cpu_flag_parsing():
    """Script accepts --cpu flag."""
    source = inspect.getsource(__import__("rebuild_qmd_index"))
    assert '--cpu' in source


def test_retry_catches_oom():
    """_add_with_retry retries on OOM error and clears cache between attempts."""
    import rebuild_qmd_index

    mock_coll = MagicMock()
    mock_coll.add_document.side_effect = [
        Exception("CUDA error: out of memory"),
        None,  # succeeds on retry
    ]

    with patch.object(rebuild_qmd_index, '_clear_gpu_cache') as mock_clear:
        filepath = Path("/fake/test-file.md")
        success, error = rebuild_qmd_index._add_with_retry(
            mock_coll, filepath, "test content", max_retries=3
        )

    assert success is True
    assert mock_clear.call_count == 1
    assert mock_coll.add_document.call_count == 2


def test_retry_gives_up_after_max():
    """_add_with_retry returns False after max_retries OOM errors."""
    import rebuild_qmd_index

    mock_coll = MagicMock()
    mock_coll.add_document.side_effect = Exception("CUDA error: out of memory")

    with patch.object(rebuild_qmd_index, '_clear_gpu_cache'):
        filepath = Path("/fake/test-file.md")
        success, error = rebuild_qmd_index._add_with_retry(
            mock_coll, filepath, "test content", max_retries=3
        )

    assert success is False
    assert "out of memory" in error.lower()
    assert mock_coll.add_document.call_count == 3


def test_non_oom_error_not_retried():
    """_add_with_retry does not retry on non-OOM errors."""
    import rebuild_qmd_index

    mock_coll = MagicMock()
    mock_coll.add_document.side_effect = ValueError("invalid markdown")

    filepath = Path("/fake/test-file.md")
    success, error = rebuild_qmd_index._add_with_retry(
        mock_coll, filepath, "test content", max_retries=3
    )

    assert success is False
    assert "invalid markdown" in error
    assert mock_coll.add_document.call_count == 1  # no retry


def test_script_has_main_logic():
    """Script has the expected structure."""
    import rebuild_qmd_index
    source = inspect.getsource(rebuild_qmd_index)
    assert "add_document" in source
    assert "list_documents" in source
    assert "wiki" in source
    assert "_add_with_retry" in source
