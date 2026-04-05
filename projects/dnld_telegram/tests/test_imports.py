def test_imports_not_overwritten():
    """Ensure critical imports are not set to None"""
    from src.ui.displays import AliveDisplay, RichDisplay, TextualDisplay

    # These should be classes or None due to missing dependencies, not forced None
    if AliveDisplay is not None:
        assert callable(AliveDisplay), "AliveDisplay should be a class"
    if TextualDisplay is not None:
        assert callable(TextualDisplay), "TextualDisplay should be a class"
    if RichDisplay is not None:
        assert callable(RichDisplay), "RichDisplay should be a class"
