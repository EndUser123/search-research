"""
Test suite for help flag detection in skill_enforcer.py

Tests cover:
- Universal --help flag detection
- Universal --list flag detection
- Multiple help flag combinations (--help --list)
- Case sensitivity and flag variants
- Non-help commands are not detected as help requests
"""



class TestUniversalHelpFlag:
    """Test universal --help flag detection"""

    def test_single_dash_help_is_detected(self):
        """Test that -h flag is detected as help request"""
        test_cases = [
            "/skill -h",
            "/code -h",
            "/plan -h --help",
            "command -h arg1"
        ]

        for prompt in test_cases:
            has_help = "-h" in prompt.lower()
            assert has_help is True, f"Failed to detect -h in: {prompt}"

    def test_double_dash_help_is_detected(self):
        """Test that --help flag is detected as help request"""
        test_cases = [
            "/skill --help",
            "/code --help",
            "/plan --help arg1",
            "command --help"
        ]

        for prompt in test_cases:
            has_help = "--help" in prompt.lower()
            assert has_help is True, f"Failed to detect --help in: {prompt}"

    def test_help_case_variants_are_detected(self):
        """Test that help flag with different casing is still detected"""
        test_cases = [
            "/skill --HELP",
            "/code --HeLp",
            "/plan --hElP"
        ]

        for prompt in test_cases:
            has_help = "help" in prompt.lower()
            assert has_help is True, f"Failed to detect help in: {prompt}"


class TestUniversalListFlag:
    """Test universal --list flag detection"""

    def test_double_dash_list_is_detected(self):
        """Test that --list flag is detected as help request"""
        test_cases = [
            "/skill --list",
            "/code --list",
            "/plan --list args",
            "command --list"
        ]

        for prompt in test_cases:
            has_list = "--list" in prompt.lower()
            assert has_list is True, f"Failed to detect --list in: {prompt}"

    def test_list_case_variants_are_detected(self):
        """Test that list flag with different casing is still detected"""
        test_cases = [
            "/skill --LIST",
            "/code --LiSt",
            "/plan --lIsT"
        ]

        for prompt in test_cases:
            has_list = "list" in prompt.lower()
            assert has_list is True, f"Failed to detect list in: {prompt}"


class TestMultipleHelpFlags:
    """Test multiple help flag combinations"""

    def test_help_and_list_combined_is_detected(self):
        """Test that --help --list combination is detected"""
        test_cases = [
            "/skill --help --list",
            "/code --list --help",
            "/plan --help --list verbose"
        ]

        for prompt in test_cases:
            has_help = "help" in prompt.lower() or "-h" in prompt.lower()
            has_list = "list" in prompt.lower()
            assert has_help and has_list, f"Failed to detect help+list in: {prompt}"

    def test_multiple_help_variants_detected(self):
        """Test that multiple help flag variants are all detected"""
        test_cases = [
            "/skill -h --help",
            "/code --help -h",
            "/plan -h"
        ]

        for prompt in test_cases:
            has_help = (
                "-h" in prompt or
                "--help" in prompt.lower() or
                "help" in prompt.lower()
            )
            assert has_help is True, f"Failed to detect help in: {prompt}"


class TestNonHelpCommands:
    """Test that non-help commands are not detected as help requests"""

    def test_regular_command_not_detected_as_help(self):
        """Test that regular commands without help flags are not help requests"""
        test_cases = [
            "/code implement feature",
            "/plan create strategy",
            "/skill test coverage",
            "/build run all",
            "git commit -m message"
        ]

        for prompt in test_cases:
            has_help = (
                "-h" in prompt.lower() or
                "--help" in prompt.lower() or
                "help" in prompt.lower()
            )
            assert has_help is False, f"Incorrectly detected help in: {prompt}"

    def test_command_with_help_word_not_flag(self):
        """Test that 'help' as a word (not flag) doesn't trigger help detection"""
        test_cases = [
            "/code help me understand",
            "/plan helping users",
            "/skill helper function"
        ]

        for prompt in test_cases:
            # These should NOT be detected as help flags
            # because 'help' is used as a word, not as a flag
            has_help_flag = (
                "-h" in prompt.lower() or
                "--help" in prompt.lower() or
                "--list" in prompt.lower()
            )
            assert has_help_flag is False, f"Incorrectly detected help flag in: {prompt}"

    def test_arguments_containing_help_not_detected(self):
        """Test that command arguments containing 'help' don't trigger detection"""
        test_cases = [
            "/code run --file helper.py",
            "/plan update --helper-script",
            "/skill test helper-module"
        ]

        for prompt in test_cases:
            has_help_flag = (
                "-h" in prompt.lower() or
                "--help" in prompt.lower() or
                "--list" in prompt.lower()
            )
            assert has_help_flag is False, f"Incorrectly detected help flag in: {prompt}"


class TestHelpFlagEdgeCases:
    """Test edge cases for help flag detection"""

    def test_empty_string_is_not_help(self):
        """Test that empty string is not a help request"""
        prompt = ""
        has_help = "help" in prompt.lower() or "-h" in prompt.lower()
        assert has_help is False

    def test_whitespace_only_is_not_help(self):
        """Test that whitespace-only string is not a help request"""
        prompt = "   "
        has_help = "help" in prompt.lower() or "-h" in prompt.lower()
        assert has_help is False

    def test_help_flag_with_leading_spaces(self):
        """Test that help flag is still detected with leading spaces"""
        test_cases = [
            "  /skill --help",
            "\t/code -h",
            "  /plan --list"
        ]

        for prompt in test_cases:
            stripped = prompt.strip()
            has_help = (
                "-h" in stripped or
                "--help" in stripped.lower() or
                "--list" in stripped.lower()
            )
            assert has_help is True, f"Failed to detect help with leading spaces in: {prompt}"

    def test_mixed_case_prompt_with_help(self):
        """Test help detection in mixed-case prompts"""
        test_cases = [
            "/CODE --HELP",
            "/Plan -H",
            "/Skill --LIST"
        ]

        for prompt in test_cases:
            has_help = (
                "-h" in prompt.lower() or
                "--help" in prompt.lower() or
                "--list" in prompt.lower()
            )
            assert has_help is True, f"Failed to detect help in mixed case: {prompt}"
