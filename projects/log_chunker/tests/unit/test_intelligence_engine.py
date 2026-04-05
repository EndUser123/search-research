import pytest
from config import ChunkingConfig
from intelligence_engine import IntelligenceEngine
from rich.console import Console


def test_can_instantiate_intelligence_engine():
    """Smoke test to ensure the IntelligenceEngine can be instantiated."""
    try:
        config = ChunkingConfig()
        console = Console()
        engine = IntelligenceEngine(config, console)
        assert engine is not None
    except Exception as e:
        pytest.fail(f"Failed to instantiate IntelligenceEngine: {e}")
