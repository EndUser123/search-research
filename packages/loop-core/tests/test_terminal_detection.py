"""Tests for terminal detection with CLAUDE_TERMINAL_ID priority."""



from scripts.terminal_detection import get_terminal_id
from scripts.state_paths import get_terminal_state_dir
from scripts.state_manager import TerminalStateManager


class TestTerminalIDPriority:
    """Test suite for CLAUDE_TERMINAL_ID priority handling."""

    def test_claude_terminal_id_env_var_priority(self, tmp_path, monkeypatch):
        """Test CLAUDE_TERMINAL_ID env var has highest priority."""
        # Set CLAUDE_TERMINAL_ID env var
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test_terminal_123")

        # Clear terminal cache to force fresh detection
        from scripts.terminal_detection import _terminal_cache
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        # Get terminal ID should prioritize CLAUDE_TERMINAL_ID
        terminal_id = get_terminal_id()
        assert terminal_id == "env_test_terminal_123"

    def test_claude_terminal_id_overrides_other_env_vars(self, tmp_path, monkeypatch):
        """Test CLAUDE_TERMINAL_ID overrides TERMINAL_ID and TERM_ID."""
        # Set multiple env vars
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "priority_terminal")
        monkeypatch.setenv("TERMINAL_ID", "lower_priority_1")
        monkeypatch.setenv("TERM_ID", "lower_priority_2")

        # Clear terminal cache
        from scripts.terminal_detection import _terminal_cache
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        # CLAUDE_TERMINAL_ID should win
        terminal_id = get_terminal_id()
        assert terminal_id == "env_priority_terminal"

    def test_different_claude_terminal_ids_get_isolated_dirs(self, tmp_path, monkeypatch):
        """Test two different CLAUDE_TERMINAL_ID values get isolated directories."""
        # Mock PROJECT_ROOT to use tmp_path
        monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))

        # Terminal A setup
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "terminal_a")

        # Clear cache for fresh detection
        from scripts.terminal_detection import _terminal_cache
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        terminal_a_id = get_terminal_id()
        terminal_a_dir = get_terminal_state_dir(terminal_a_id)

        # Terminal B setup (simulate different terminal)
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "terminal_b")

        # Clear cache again
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        terminal_b_id = get_terminal_id()
        terminal_b_dir = get_terminal_state_dir(terminal_b_id)

        # Verify different terminal IDs
        assert terminal_a_id != terminal_b_id
        assert terminal_a_id == "env_terminal_a"
        assert terminal_b_id == "env_terminal_b"

        # Verify isolated directories
        assert terminal_a_dir != terminal_b_dir
        assert "terminal_a" in str(terminal_a_dir)
        assert "terminal_b" in str(terminal_b_dir)

    def test_state_manager_uses_claude_terminal_id(self, tmp_path, monkeypatch):
        """Test TerminalStateManager uses CLAUDE_TERMINAL_ID when set."""
        monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test_terminal_manager")

        # Clear cache
        from scripts.terminal_detection import _terminal_cache
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        # Create manager (should auto-detect CLAUDE_TERMINAL_ID)
        manager = TerminalStateManager()

        assert manager.terminal_id == "env_test_terminal_manager"
        assert "test_terminal_manager" in str(manager.state_dir)

    def test_two_managers_with_different_claude_terminal_ids(self, tmp_path, monkeypatch):
        """Test two managers with different CLAUDE_TERMINAL_ID values are isolated."""
        monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))

        # Manager A setup
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "manager_a")

        from scripts.terminal_detection import _terminal_cache
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        manager_a = TerminalStateManager()
        manager_a.write_state("test", {"manager": "A"})

        # Manager B setup (simulate different terminal)
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "manager_b")

        # Clear cache again
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        manager_b = TerminalStateManager()
        manager_b.write_state("test", {"manager": "B"})

        # Verify isolated state
        state_a = manager_a.read_state("test")
        state_b = manager_b.read_state("test")

        assert state_a["manager"] == "A"
        assert state_b["manager"] == "B"

        # Verify different directories
        assert manager_a.state_dir != manager_b.state_dir

    def test_explicit_terminal_idOverrides_claude_terminal_id_env(self, tmp_path, monkeypatch):
        """Test explicit terminal_id parameter overrides CLAUDE_TERMINAL_ID env var."""
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "env_terminal")

        # Clear cache
        from scripts.terminal_detection import _terminal_cache
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        # Explicit terminal_id should override env var
        manager = TerminalStateManager(terminal_id="explicit_terminal")

        assert manager.terminal_id == "explicit_terminal"
        assert "explicit_terminal" in str(manager.state_dir)

    def test_fallback_to_other_detection_when_no_claude_terminal_id(self, tmp_path, monkeypatch):
        """Test fallback to other detection methods when CLAUDE_TERMINAL_ID not set."""
        # Ensure CLAUDE_TERMINAL_ID is not set
        monkeypatch.delenv("CLAUDE_TERMINAL_ID", raising=False)

        # Clear cache
        from scripts.terminal_detection import _terminal_cache
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        # Should fall back to other detection methods
        terminal_id = get_terminal_id()
        assert terminal_id is not None
        assert len(terminal_id) > 0

    def test_terminal_id_caching_with_claude_terminal_id(self, tmp_path, monkeypatch):
        """Test terminal ID is cached after first detection."""
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "cached_terminal")

        # Clear cache
        from scripts.terminal_detection import _terminal_cache
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        # First call should detect and cache
        terminal_id_1 = get_terminal_id()
        cached_value = getattr(_terminal_cache, "terminal_id", None)
        assert cached_value == "env_cached_terminal"

        # Second call should use cache
        terminal_id_2 = get_terminal_id()
        assert terminal_id_1 == terminal_id_2

    def test_state_paths_all_use_get_terminal_state_dir(self, tmp_path, monkeypatch):
        """Test all state paths use get_terminal_state_dir() consistently."""
        monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "consistency_test")

        # Clear cache
        from scripts.terminal_detection import _terminal_cache
        if hasattr(_terminal_cache, "terminal_id"):
            delattr(_terminal_cache, "terminal_id")

        terminal_id = get_terminal_id()

        # All paths should use get_terminal_state_dir
        state_dir = get_terminal_state_dir(terminal_id)
        state_path = state_dir / "test.json"

        # Verify path structure
        assert "consistency_test" in str(state_dir)
        assert "terminals" in str(state_dir)

    def test_empty_terminal_id_fallback_to_global_state(self, tmp_path):
        """Test empty terminal ID falls back to global state directory."""
        # Should not raise error, just return global state dir
        global_dir = get_terminal_state_dir("")

        assert global_dir.exists()
        # Should be the global state dir, not a terminal-specific one
        assert "terminals" not in str(global_dir) or global_dir.name == "state"
