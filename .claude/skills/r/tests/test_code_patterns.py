"""Tests for code pattern scanning functionality.

These tests verify the scan_code_patterns() function which detects
TODO, FIXME, HACK, XXX, and NOTE markers in Python files.

RED PHASE: Tests will FAIL because scan_code_patterns() doesn't exist yet.
"""



class TestScanCodePatternsFindsTodo:
    """Test suite for scan_code_patterns() detecting TODO markers."""

    def test_scan_code_patterns_finds_todo(self, tmp_path):
        """
        Test that scan_code_patterns detects TODO marker in sample Python file.

        Given: A Python file with a TODO marker
        When: scan_code_patterns is called with the file path
        Then: Returns list containing the TODO marker with correct metadata
        """
        # Arrange: Create Python file with TODO marker
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "def example_function():\n"
            "    # TODO: Add input validation\n"
            "    pass\n"
        )

        # Act: Scan for code patterns
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from code_scanner import scan_code_patterns
        findings = scan_code_patterns([str(test_file)])

        # Assert: TODO marker detected
        assert len(findings) == 1
        assert findings[0]['type'] == 'TODO'
        assert findings[0]['file_path'] == str(test_file)
        assert findings[0]['line_number'] == 2
        assert findings[0]['description'] == 'Add input validation'
        assert findings[0]['risk_score'] == 3
        assert findings[0]['rollback_complexity'] == 'medium'
        assert findings[0]['state_impact'] == 'low'
        assert findings[0]['severity'] == 'medium'

    def test_scan_code_patterns_finds_fixme(self, tmp_path):
        """
        Test that scan_code_patterns detects FIXME marker in sample Python file.

        Given: A Python file with a FIXME marker
        When: scan_code_patterns is called with the file path
        Then: Returns list containing the FIXME marker with high severity
        """
        # Arrange: Create Python file with FIXME marker
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "def process_data():\n"
            "    # FIXME: This crashes on empty input\n"
            "    return data[0]\n"
        )

        # Act: Scan for code patterns
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from code_scanner import scan_code_patterns
        findings = scan_code_patterns([str(test_file)])

        # Assert: FIXME marker detected with high severity
        assert len(findings) == 1
        assert findings[0]['type'] == 'FIXME'
        assert findings[0]['line_number'] == 2
        assert findings[0]['description'] == 'This crashes on empty input'
        assert findings[0]['risk_score'] == 5
        assert findings[0]['rollback_complexity'] == 'high'
        assert findings[0]['severity'] == 'high'

    def test_scan_code_patterns_finds_multiple_markers(self, tmp_path):
        """
        Test that scan_code_patterns detects TODO, FIXME, HACK, XXX, NOTE markers.

        Given: A Python file with multiple different marker types
        When: scan_code_patterns is called with the file path
        Then: Returns list containing all markers with correct types and metadata
        """
        # Arrange: Create Python file with multiple marker types
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# TODO: Add input validation\n"
            "def example():\n"
            "    # FIXME: Handle edge case\n"
            "    # HACK: Quick workaround for performance\n"
            "    # XXX: This needs refactoring\n"
            "    # NOTE: Consider using library function\n"
            "    pass\n"
        )

        # Act: Scan for code patterns
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from code_scanner import scan_code_patterns
        findings = scan_code_patterns([str(test_file)])

        # Assert: All markers detected
        assert len(findings) == 5

        # Check TODO
        todo = [f for f in findings if f['type'] == 'TODO'][0]
        assert todo['line_number'] == 1
        assert todo['description'] == 'Add input validation'
        assert todo['risk_score'] == 3

        # Check FIXME
        fixme = [f for f in findings if f['type'] == 'FIXME'][0]
        assert fixme['line_number'] == 3
        assert fixme['risk_score'] == 5
        assert fixme['severity'] == 'high'

        # Check HACK
        hack = [f for f in findings if f['type'] == 'HACK'][0]
        assert hack['line_number'] == 4
        assert hack['description'] == 'Quick workaround for performance'
        assert hack['rollback_complexity'] == 'high'

        # Check XXX
        xxx = [f for f in findings if f['type'] == 'XXX'][0]
        assert xxx['line_number'] == 5
        assert xxx['risk_score'] == 4

        # Check NOTE
        note = [f for f in findings if f['type'] == 'NOTE'][0]
        assert note['line_number'] == 6
        assert note['risk_score'] == 3  # Same as TODO since both use T3/EDGE_CASE
        assert note['severity'] == 'medium'

    def test_scan_code_patterns_handles_no_markers(self, tmp_path):
        """
        Test that scan_code_patterns returns empty list when no markers found.

        Given: A Python file with no code markers
        When: scan_code_patterns is called with the file path
        Then: Returns empty list
        """
        # Arrange: Create Python file without markers
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "def clean_function():\n"
            "    return 42\n"
        )

        # Act: Scan for code patterns
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from code_scanner import scan_code_patterns
        findings = scan_code_patterns([str(test_file)])

        # Assert: No markers found
        assert len(findings) == 0
        assert findings == []

    def test_scan_code_patterns_handles_nonexistent_files(self, tmp_path):
        """
        Test that scan_code_patterns skips non-existent files without error.

        Given: A list containing non-existent file paths
        When: scan_code_patterns is called
        Then: Skips non-existent files and processes valid files only
        """
        # Arrange: Create one valid file
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("# TODO: Implement this\n")

        # Mix with non-existent file
        nonexistent_file = tmp_path / "does_not_exist.py"

        # Act: Scan for code patterns
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from code_scanner import scan_code_patterns
        findings = scan_code_patterns([str(valid_file), str(nonexistent_file)])

        # Assert: Only valid file scanned
        assert len(findings) == 1
        assert findings[0]['file_path'] == str(valid_file)

    def test_scan_code_patterns_skips_non_python_files(self, tmp_path):
        """
        Test that scan_code_patterns only scans Python files.

        Given: A list including non-Python files (txt, md, json)
        When: scan_code_patterns is called
        Then: Only Python files are scanned
        """
        # Arrange: Create files of different types
        py_file = tmp_path / "test.py"
        py_file.write_text("# TODO: Python file marker\n")

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("# TODO: Text file marker\n")

        md_file = tmp_path / "test.md"
        md_file.write_text("# TODO: Markdown file marker\n")

        # Act: Scan for code patterns
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from code_scanner import scan_code_patterns
        findings = scan_code_patterns([
            str(py_file),
            str(txt_file),
            str(md_file)
        ])

        # Assert: Only Python file scanned
        assert len(findings) == 1
        assert findings[0]['file_path'] == str(py_file)

    def test_scan_code_patterns_detects_state_impact_keywords(self, tmp_path):
        """
        Test that scan_code_patterns sets state_impact to high for error-related descriptions.

        Given: A Python file with TODO markers mentioning 'error' or 'fix'
        When: scan_code_patterns is called
        Then: Markers with error/fix keywords have state_impact='high'
        """
        # Arrange: Create Python file with error-related TODO
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# TODO: Fix the error handling\n"
            "def example():\n"
            "    # TODO: Implement error recovery\n"
            "    pass\n"
        )

        # Act: Scan for code patterns
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from code_scanner import scan_code_patterns
        findings = scan_code_patterns([str(test_file)])

        # Assert: Both TODOs have high state impact
        assert len(findings) == 2
        assert all(f['state_impact'] == 'high' for f in findings)
