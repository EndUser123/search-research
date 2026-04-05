#!/usr/bin/env python
"""Test markdown export functionality."""

def test_markdown_exporter_imports():
    """Test that MarkdownExporter can be imported."""
    try:
        from src.yt_fts.export.markdown_exporter import MarkdownExporter, MarkdownFormat
        print("✓ MarkdownExporter imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_markdown_exporter_instantiation():
    """Test that MarkdownExporter can be instantiated."""
    try:
        from src.yt_fts.export.markdown_exporter import MarkdownExporter

        # Test Obsidian format
        exporter_obsidian = MarkdownExporter(format="obsidian")
        assert exporter_obsidian.format == "obsidian"
        print("✓ Obsidian format exporter created")

        # Test Roam format
        exporter_roam = MarkdownExporter(format="roam")
        assert exporter_roam.format == "roam"
        print("✓ Roam format exporter created")

        return True
    except Exception as e:
        print(f"✗ Instantiation failed: {e}")
        return False

def test_markdown_exporter_methods():
    """Test that MarkdownExporter has required methods."""
    try:
        from src.yt_fts.export.markdown_exporter import MarkdownExporter

        exporter = MarkdownExporter(format="obsidian")

        # Check for required methods
        assert hasattr(exporter, "export_channel"), "Missing export_channel method"
        assert hasattr(exporter, "export_video"), "Missing export_video method"
        print("✓ All required methods present")

        # Check helper methods
        assert hasattr(exporter, "_sanitize_title"), "Missing _sanitize_title method"
        assert hasattr(exporter, "_generate_frontmatter"), "Missing _generate_frontmatter method"
        print("✓ All helper methods present")

        return True
    except Exception as e:
        print(f"✗ Method check failed: {e}")
        return False

def test_cli_integration():
    """Test that CLI accepts markdown format."""
    import sys
    from io import StringIO

    from yt_fts.core.cli import cli

    # Capture help output
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        cli(["export", "--help"], standalone_mode=False)
    except SystemExit:
        pass  # --help causes SystemExit
    finally:
        help_output = sys.stdout.getvalue()
        sys.stdout = old_stdout

    assert "-f" in help_output or "--format" in help_output, "Missing --format option"
    assert "md" in help_output, "Markdown format not listed in help"
    assert "--markdown-flavor" in help_output, "Missing --markdown-flavor option"
    assert "obsidian" in help_output.lower(), "Obsidian flavor not mentioned"
    assert "roam" in help_output.lower(), "Roam flavor not mentioned"
    print("✓ CLI integration verified")
    print("✓ Markdown format available in export command")

    return True

def test_sanitize_title():
    """Test title sanitization."""
    from src.yt_fts.export.markdown_exporter import MarkdownExporter

    exporter = MarkdownExporter(format="obsidian")

    # Test basic sanitization
    assert exporter._sanitize_title("Simple Title") == "Simple Title"
    print("✓ Basic title sanitization works")

    # Test removal of invalid characters
    assert exporter._sanitize_title("Title: With/Invalid\\Chars") == "Title WithInvalidChars"
    print("✓ Invalid character removal works")

    # Test length limit
    long_title = "A" * 200
    sanitized = exporter._sanitize_title(long_title)
    assert len(sanitized) <= 100, "Title length limit not enforced"
    print("✓ Title length limit enforced")

    return True

def test_timestamp_conversion():
    """Test timestamp to seconds conversion."""
    from src.yt_fts.export.markdown_exporter import MarkdownExporter

    exporter = MarkdownExporter(format="obsidian")

    # Test HH:MM:SS format
    assert exporter._timestamp_to_seconds("01:30:45") == 5445
    print("✓ HH:MM:SS conversion works")

    # Test MM:SS format
    assert exporter._timestamp_to_seconds("02:30") == 150
    print("✓ MM:SS conversion works")

    # Test edge cases
    assert exporter._timestamp_to_seconds("00:00:00") == 0
    print("✓ Zero timestamp works")

    return True

def test_yaml_escaping():
    """Test YAML string escaping."""
    from src.yt_fts.export.markdown_exporter import MarkdownExporter

    exporter = MarkdownExporter(format="obsidian")

    # Test quote escaping
    assert exporter._escape_yaml('Title with "quotes"') == 'Title with \\"quotes\\"'
    print("✓ Quote escaping works")

    # Test backslash escaping
    assert exporter._escape_yaml("Path\\to\\file") == "Path\\\\to\\\\file"
    print("✓ Backslash escaping works")

    return True

if __name__ == "__main__":
    print("Testing Markdown Export Implementation...")
    print("-" * 50)

    tests = [
        ("Import Test", test_markdown_exporter_imports),
        ("Instantiation Test", test_markdown_exporter_instantiation),
        ("Methods Test", test_markdown_exporter_methods),
        ("CLI Integration", test_cli_integration),
        ("Title Sanitization", test_sanitize_title),
        ("Timestamp Conversion", test_timestamp_conversion),
        ("YAML Escaping", test_yaml_escaping),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            failed += 1

    print("\n" + "-" * 50)
    print(f"\nResults: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n✓ All tests passed! Markdown export is ready to use.\n")
    else:
        print(f"\n✗ {failed} test(s) failed. Please review the errors above.\n")
