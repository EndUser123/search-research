#!/usr/bin/env python
"""
Quick test to verify date filter integration
"""

def test_cli_options():
    """Test that CLI accepts date options"""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "yt_fts", "search", "--help"],
        capture_output=True, text=True, check=False
    )
    assert "--after" in result.stdout, "Missing --after option"
    assert "--before" in result.stdout, "Missing --before option"
    assert "--last" in result.stdout, "Missing --last option"
    print("✓ CLI options are present")

def test_date_parsing():
    """Test date filter parsing"""
    from src.yt_fts.utils.date_filter import parse_date_filters

    # Test basic dates
    after, before = parse_date_filters(after="2024-01-01", before="2024-12-31")
    assert after == "2024-01-01"
    assert before == "2024-12-31"
    print("✓ Basic date parsing works")

    # Test relative dates
    after, before = parse_date_filters(last="7d")
    assert after is not None
    assert before is None
    print("✓ Relative date parsing works")

    # Test error handling
    try:
        parse_date_filters(after="invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("✓ Error handling works")

def test_database_signatures():
    """Test that database functions have correct signatures"""
    import inspect

    from src.yt_fts.core.database import search_all, search_channel, search_video

    for func in [search_all, search_channel, search_video]:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        assert "after_date" in params, f"{func.__name__} missing after_date"
        assert "before_date" in params, f"{func.__name__} missing before_date"

    print("✓ Database functions have date parameters")

def test_search_handler():
    """Test that SearchHandler accepts date parameters"""
    import inspect

    from src.yt_fts.core.search import SearchHandler

    sig = inspect.signature(SearchHandler.__init__)
    params = list(sig.parameters.keys())
    assert "after_date" in params, "SearchHandler missing after_date"
    assert "before_date" in params, "SearchHandler missing before_date"

    print("✓ SearchHandler has date parameters")

if __name__ == "__main__":
    print("Testing Date Filter Implementation...")
    print("-" * 50)

    test_cli_options()
    test_date_parsing()
    test_database_signatures()
    test_search_handler()

    print("-" * 50)
    print("\n✓ All tests passed! Date filters are ready to use.\n")
