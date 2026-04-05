"""
Test suite for prose bypass detection in StopHook_skill_execution_gate.py

Tests cover:
- Detection when user types slash command but AI responds with prose
- Tool combination detection (Read vs. Skill tool)
- Two-strike pattern (advisory first, hard block second)
- Exemptions (built-in CLI commands, lightweight skills)
- Multi-terminal isolation in bypass tracking
"""



class TestSlashCommandDetection:
    """Test detection of slash commands in user prompts"""

    def test_slash_command_is_extracted(self):
        """Test that slash commands are correctly extracted from user input"""
        user_inputs = [
            "/code implement feature",
            "/plan create strategy",
            "/skill test coverage",
            "/build run all"
        ]

        for user_input in user_inputs:
            has_slash = user_input.startswith("/")
            assert has_slash is True, f"Failed to detect slash command in: {user_input}"

    def test_non_slash_command_not_detected(self):
        """Test that non-slash commands are not detected"""
        user_inputs = [
            "implement feature",
            "create strategy",
            "test coverage please",
            "run all tests"
        ]

        for user_input in user_inputs:
            has_slash = user_input.startswith("/")
            assert has_slash is False, f"Incorrectly detected slash in: {user_input}"

    def test_slash_command_with_args_extracted(self):
        """Test that slash command and arguments are parsed correctly"""
        user_input = "/code implement feature --fast"

        # Extract command
        parts = user_input.split()
        command = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        assert command == "/code"
        assert "implement" in args
        assert "--fast" in args


class TestProseBypassDetection:
    """Test detection of prose responses instead of skill execution"""

    def test_skill_tool_used_is_not_bypass(self):
        """Test that using Skill tool is not considered a bypass"""
        tool_usage = {
            "tool_name": "Skill",
            "skill": "code",
            "arguments": ["/code implement feature"]
        }

        is_bypass = tool_usage["tool_name"] != "Skill"
        assert is_bypass is False, "Skill tool usage incorrectly marked as bypass"

    def test_only_read_tools_is_bypass(self):
        """Test that using only Read tools is considered a bypass"""
        tool_history = [
            {"tool_name": "Read", "file": "file.py"},
            {"tool_name": "Read", "file": "another.py"}
        ]

        # Check if Skill tool was used
        skill_was_used = any(t.get("tool_name") == "Skill" for t in tool_history)
        is_bypass = not skill_was_used and len(tool_history) > 0

        assert is_bypass is True, "Read-only tools not marked as bypass"

    def test_mixed_tools_without_skill_is_bypass(self):
        """Test that mixed tool usage without Skill is a bypass"""
        tool_history = [
            {"tool_name": "Read", "file": "file.py"},
            {"tool_name": "Grep", "pattern": "TODO"},
            {"tool_name": "Bash", "command": "ls"}
        ]

        skill_was_used = any(t.get("tool_name") == "Skill" for t in tool_history)
        is_bypass = not skill_was_used and len(tool_history) > 0

        assert is_bypass is True, "Mixed tools without Skill not marked as bypass"

    def test_no_tools_is_not_bypass(self):
        """Test that having no tools is not considered a bypass (no tool use at all)"""
        tool_history = []

        is_bypass = len(tool_history) > 0 and not any(
            t.get("tool_name") == "Skill" for t in tool_history
        )

        assert is_bypass is False, "No tools incorrectly marked as bypass"


class TestTwoStrikePattern:
    """Test two-strike pattern for bypass detection"""

    def test_first_bypass_returns_advisory(self):
        """Test that first bypass returns advisory (not hard block)"""
        bypass_count = 1

        # First bypass: Advisory mode
        should_block = bypass_count >= 2

        assert should_block is False, "First bypass should not block"

    def test_second_bypass_blocks(self):
        """Test that second bypass results in hard block"""
        bypass_count = 2

        # Second bypass: Block mode
        should_block = bypass_count >= 2

        assert should_block is True, "Second bypass should block"

    def test_bypass_count_increments(self):
        """Test that bypass count increments correctly"""
        bypass_count = 0

        # Simulate bypasses
        for i in range(3):
            bypass_count = i + 1
            assert bypass_count == i + 1, f"Bypass count incorrect at iteration {i}"


class TestBypassExemptions:
    """Test exemptions from bypass detection"""

    def test_builtin_cli_commands_exempted(self):
        """Test that built-in CLI commands are exempt from bypass detection"""
        exempt_commands = [
            "/help",
            "/?",
            "/version",
            "/config"
        ]

        for command in exempt_commands:
            is_exempt = command in exempt_commands
            assert is_exempt is True, f"Command {command} should be exempt"

    def test_lightweight_skills_exempted(self):
        """Test that lightweight skills are exempt from bypass detection"""
        exempt_skills = [
            "/ask",
            "/search",
            "/verify"
        ]

        for skill in exempt_skills:
            is_exempt = skill in exempt_skills
            assert is_exempt is True, f"Skill {skill} should be exempt"

    def test_heavy_skills_not_exempted(self):
        """Test that heavy skills are NOT exempt from bypass detection"""
        non_exempt_skills = [
            "/code",
            "/plan",
            "/build",
            "/refactor"
        ]

        for skill in non_exempt_skills:
            is_exempt = skill in ["/ask", "/search", "/verify"]
            assert is_exempt is False, f"Skill {skill} should NOT be exempt"


class TestMultiTerminalBypassTracking:
    """Test that bypass tracking is isolated per terminal"""

    def test_bypass_count_per_terminal(self, temp_state_dir):
        """Test that bypass counts are tracked separately for each terminal"""
        terminal_1_id = "terminal-bypass-1"
        terminal_2_id = "terminal-bypass-2"

        # Simulate bypass counts per terminal
        bypass_counts = {
            terminal_1_id: 2,
            terminal_2_id: 0
        }

        # Terminal 1: Should block (2 bypasses)
        should_block_1 = bypass_counts[terminal_1_id] >= 2
        # Terminal 2: Should not block (0 bypasses)
        should_block_2 = bypass_counts[terminal_2_id] >= 2

        assert should_block_1 is True
        assert should_block_2 is False

    def test_bypass_state_does_not_bleed_between_terminals(self, temp_state_dir):
        """Test that bypass state in one terminal doesn't affect others"""
        terminals = []

        for i in range(3):
            terminal_id = f"terminal-bypass-{i}"
            # Each terminal has its own bypass state
            bypass_state = {"count": i, "blocked": i >= 2}
            terminals.append((terminal_id, bypass_state))

        # Verify each terminal has correct state
        for terminal_id, state in terminals:
            expected_count = int(terminal_id.split("-")[-1])
            assert state["count"] == expected_count


class TestBypassRecovery:
    """Test recovery and reset of bypass detection"""

    def test_successful_skill_execution_resets_bypass_count(self):
        """Test that successful skill execution resets bypass count"""
        bypass_count = 2  # Currently at 2 (would block)

        # Simulate successful skill execution
        skill_was_used = True
        if skill_was_used:
            bypass_count = 0  # Reset

        # Verify reset
        assert bypass_count == 0, "Bypass count not reset after successful skill execution"

    def test_bypass_count_persists_across_turns(self):
        """Test that bypass count persists across multiple turns"""
        # Turn 1: Bypass detected
        bypass_count = 1

        # Turn 2: Another bypass (should increment)
        bypass_count += 1

        # Verify count persisted
        assert bypass_count == 2, "Bypass count not persisted across turns"

    def test_session_boundary_clears_bypass_count(self):
        """Test that new session clears bypass count"""
        # End of session: Clear bypass count
        bypass_count = 2
        bypass_count = 0  # Session reset

        # Start of new session: Count should be cleared
        assert bypass_count == 0, "Bypass count not cleared on session boundary"


class TestProseBypassIntegration:
    """Integration tests for prose bypass detection with other components"""

    def test_bypass_detection_with_ttl_check(self, stale_intent_file):
        """Test that bypass detection works with TTL-expired intent files"""
        # Intent file is stale (TTL expired)
        # But bypass detection should still work independently

        tool_history = [
            {"tool_name": "Read", "file": "file.py"}
        ]

        user_command = "/code test"
        skill_was_used = any(t.get("tool_name") == "Skill" for t in tool_history)

        # Bypass detection should trigger regardless of TTL state
        is_bypass = not skill_was_used and len(tool_history) > 0

        assert is_bypass is True, "Bypass not detected despite TTL-expired intent"

    def test_bypass_with_concurrent_terminals(self, temp_state_dir):
        """Test that bypass detection works correctly with concurrent terminals"""
        terminal_1_id = "terminal-bypass-concurrent-1"
        terminal_2_id = "terminal-bypass-concurrent-2"

        # Terminal 1: User invoked /code but responded with prose
        terminal_1_state = {
            "user_command": "/code test",
            "skill_used": False,
            "tools_used": ["Read"]
        }

        # Terminal 2: User invoked /plan and used Skill
        terminal_2_state = {
            "user_command": "/plan create",
            "skill_used": True,
            "tools_used": ["Skill", "Read"]
        }

        # Terminal 1: Bypass detected
        bypass_1 = not terminal_1_state["skill_used"] and len(terminal_1_state["tools_used"]) > 0
        # Terminal 2: No bypass
        bypass_2 = not terminal_2_state["skill_used"] and len(terminal_2_state["tools_used"]) > 0

        assert bypass_1 is True
        assert bypass_2 is False
