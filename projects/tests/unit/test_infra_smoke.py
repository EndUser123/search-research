"""Smoke tests for v2.0 Tool Integration."""


def test_imports_v2_tools():
    """Verify that new v2.0 tool modules can be imported."""

    # 1. Prefect Orchestration
    from src.orchestration.flows import qa_certification_flow, run_unit_tests

    assert callable(qa_certification_flow)
    assert callable(run_unit_tests)

    # 2. Flagsmith Config
    from src.config.flags import get_flag

    assert callable(get_flag)
    # Check default behavior (offline mode)
    assert get_flag("non_existent_flag", default=True) is True
    assert get_flag("non_existent_flag", default=False) is False

    # 3. Hypothesis (Dev dependency)
    import hypothesis

    assert hypothesis.__version__


def test_environment_flagsmith():
    """Verify Flagsmith fails gracefully without API key."""
    from src.config.flags import get_flag

    # Should not raise exception
    val = get_flag("test_key")
    assert val is False  # Default is False
