"""
Failing tests for enhanced extract_paths_from_bash() function.

These tests document the EXPECTED behavior after the enhancement is complete.
Run with: pytest P://.claude/hooks/tests/test_extract_paths_from_bash.py -v

Current Status: ALL TESTS FAIL (RED phase)
Next: Implement enhanced extract_paths_from_bash() to make tests pass (GREEN phase)
"""

from PreToolUse_directory_policy import extract_paths_from_bash


class TestExtractPathsFromBash:
    """Test suite for enhanced extract_paths_from_bash() function.

    These tests verify that file-write operations are correctly detected
    in bash commands across various patterns (echo, cat, tee, python, etc.)
    """

    # POSITIVE TESTS - Should detect paths

    def test_echo_tee_with_path(self):
        """
        Test that echo | tee pattern detects the output file path.

        Given: Command contains echo piped to tee
        When: extract_paths_from_bash() is called
        Then: P:/test.txt should be detected
        """
        command = 'echo "content" | tee P:/test.txt'
        result = extract_paths_from_bash(command)
        assert "P:/test.txt" in result

    def test_cat_heredoc_with_path(self):
        """
        Test that cat heredoc pattern detects the output file path.

        Given: Command contains cat > path << EOF
        When: extract_paths_from_bash() is called
        Then: P:/output.txt should be detected
        """
        command = 'cat > P:/output.txt << EOF\nsome content\nEOF'
        result = extract_paths_from_bash(command)
        assert "P:/output.txt" in result

    def test_python_file_write(self):
        """
        Test that python -c open() write pattern detects the file path.

        Given: Command contains python -c with open() write call
        When: extract_paths_from_bash() is called
        Then: P:/file.txt should be detected
        """
        command = 'python -c "open(\'P:/file.txt\', \'w\').write(\'data\')"'
        result = extract_paths_from_bash(command)
        assert "P:/file.txt" in result

    def test_redirect_to_path(self):
        """
        Test that redirect > pattern detects the output file path.

        Given: Command contains > redirect to path
        When: extract_paths_from_bash() is called
        Then: P:/result.txt should be detected
        """
        command = 'echo "data" > P:/result.txt'
        result = extract_paths_from_bash(command)
        assert "P:/result.txt" in result

    def test_tee_with_append(self):
        """
        Test that tee -a append pattern detects the file path.

        Given: Command contains echo | tee -a path
        When: extract_paths_from_bash() is called
        Then: P:/file.txt should be detected
        """
        command = 'echo "content" | tee -a P:/file.txt'
        result = extract_paths_from_bash(command)
        assert "P:/file.txt" in result

    # NEGATIVE TESTS - Should return empty list

    def test_echo_without_file_write(self):
        """
        Test that echo without file write returns empty list.

        Given: Command contains echo without redirection
        When: extract_paths_from_bash() is called
        Then: Empty list should be returned
        """
        command = 'echo "hello"'
        result = extract_paths_from_bash(command)
        assert result == []

    def test_cat_readonly(self):
        """
        Test that cat read-only operation returns empty list.

        Given: Command contains cat reading existing file
        When: extract_paths_from_bash() is called
        Then: Empty list should be returned
        """
        command = 'cat existing_file.txt'
        result = extract_paths_from_bash(command)
        assert result == []

    def test_python_script_no_write(self):
        """
        Test that python script execution without obvious write returns empty list.

        Given: Command executes python script without inline file operations
        When: extract_paths_from_bash() is called
        Then: Empty list should be returned
        """
        command = 'python script.py'
        result = extract_paths_from_bash(command)
        assert result == []

    def test_git_command(self):
        """
        Test that git commands return empty list.

        Given: Command is a git operation
        When: extract_paths_from_bash() is called
        Then: Empty list should be returned
        """
        command = 'git status'
        result = extract_paths_from_bash(command)
        assert result == []

    # EDGE CASES

    def test_quoted_path_with_spaces(self):
        """
        Test that paths with spaces in quotes are detected correctly.

        Given: Command contains path with spaces in quotes
        When: extract_paths_from_bash() is called
        Then: /path with spaces/file.txt should be detected
        """
        command = 'cat > "/path with spaces/file.txt" << EOF'
        result = extract_paths_from_bash(command)
        assert "/path with spaces/file.txt" in result

    def test_single_quote_python(self):
        """
        Test that python command with single quotes detects file path.

        Given: Command contains python -c with single-quoted string
        When: extract_paths_from_bash() is called
        Then: P:/file.txt should be detected
        """
        command = '''python -c 'open("P:/file.txt", "w").write("")' '''
        result = extract_paths_from_bash(command)
        assert "P:/file.txt" in result

    def test_append_redirect(self):
        """
        Test that >> append redirect pattern detects the file path.

        Given: Command contains >> append redirect
        When: extract_paths_from_bash() is called
        Then: P:/log.txt should be detected
        """
        command = 'echo "data" >> P:/log.txt'
        result = extract_paths_from_bash(command)
        assert "P:/log.txt" in result

    def test_multiple_paths_in_command(self):
        """
        Test that multiple paths in a single command are all detected.

        Given: Command contains multiple file operations
        When: extract_paths_from_bash() is called
        Then: All paths should be detected
        """
        command = 'echo "data" > P:/first.txt && cat > P:/second.txt << EOF\ncontent\nEOF'
        result = extract_paths_from_bash(command)
        assert "P:/first.txt" in result
        assert "P:/second.txt" in result

    def test_windows_style_paths(self):
        """
        Test that Windows-style backslash paths are detected.

        Given: Command contains Windows backslash paths
        When: extract_paths_from_bash() is called
        Then: P:\\test\\file.txt should be detected
        """
        command = 'echo "data" > P:\\test\\file.txt'
        result = extract_paths_from_bash(command)
        # Should normalize to forward slashes or detect as-is
        assert len(result) > 0  # At least one path detected

    def test_mixed_quotes_in_python(self):
        """
        Test that mixed quote styles in python commands are handled.

        Given: Command contains python with mixed single/double quotes
        When: extract_paths_from_bash() is called
        Then: P:/file.txt should be detected
        """
        command = '''python -c "open('P:/file.txt', 'w')"'''
        result = extract_paths_from_bash(command)
        assert "P:/file.txt" in result
