"""Tests for rebuild_qmd_index.py."""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))


def test_script_imports():
    """Script can be imported without errors."""
    # The script sets CUDA_VISIBLE_DEVICES on import; save and restore
    old = os.environ.get("CUDA_VISIBLE_DEVICES")
    import rebuild_qmd_index
    if old is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = old
    else:
        os.environ.pop("CUDA_VISIBLE_DEVICES", None)
    assert hasattr(rebuild_qmd_index, "BATCH_SIZE")
    assert rebuild_qmd_index.BATCH_SIZE == 5


def test_batch_size_is_small():
    """Batch size must be small enough to avoid GPU OOM."""
    import rebuild_qmd_index
    assert rebuild_qmd_index.BATCH_SIZE <= 10


def test_cpu_mode_enforced():
    """Script forces CPU mode to avoid GPU OOM."""
    # The module sets CUDA_VISIBLE_DEVICES=-1 at import time
    import rebuild_qmd_index
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "-1"


def test_script_has_main_logic():
    """Script has the expected structure (batch loop, add_document calls)."""
    import inspect
    import rebuild_qmd_index
    source = inspect.getsource(rebuild_qmd_index)
    assert "add_document" in source
    assert "BATCH_SIZE" in source
    assert "list_documents" in source
    assert "wiki" in source
