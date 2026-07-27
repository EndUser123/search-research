"""Tests for rebuild_qmd_index.py."""
import os
import sys
import inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_script_imports():
    """Script can be imported without errors."""
    import rebuild_qmd_index
    assert hasattr(rebuild_qmd_index, "BATCH_SIZE")
    assert rebuild_qmd_index.BATCH_SIZE == 5


def test_batch_size_is_small():
    """Batch size must be small enough to avoid GPU OOM."""
    import rebuild_qmd_index
    assert rebuild_qmd_index.BATCH_SIZE <= 10


def test_has_gpu_cache_clear_function():
    """Script has _clear_gpu_cache for VRAM management."""
    import rebuild_qmd_index
    assert hasattr(rebuild_qmd_index, "_clear_gpu_cache")
    assert callable(rebuild_qmd_index._clear_gpu_cache)


def test_cpu_flag_parsing():
    """Script accepts --cpu flag."""
    source = inspect.getsource(__import__("rebuild_qmd_index"))
    assert '"--cpu" in sys.argv' in source or "'--cpu' in sys.argv" in source


def test_script_has_main_logic():
    """Script has the expected structure (batch loop, add_document calls)."""
    import rebuild_qmd_index
    source = inspect.getsource(rebuild_qmd_index)
    assert "add_document" in source
    assert "BATCH_SIZE" in source
    assert "list_documents" in source
    assert "wiki" in source
    assert "empty_cache" in source
