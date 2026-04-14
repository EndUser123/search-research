"""Tests for RCA hook path resolution."""

from pathlib import Path


def _load_hook_path_utils():
    hook_file = Path(__file__).parent.parent / "hooks" / "hook_path_utils.py"
    namespace: dict[str, object] = {"__file__": str(hook_file)}
    exec(hook_file.read_text(encoding="utf-8"), namespace)
    return namespace


def test_expected_hooks_resolve():
    mod = _load_hook_path_utils()
    expected_hooks = mod["EXPECTED_HOOKS"]
    verify_all_hooks = mod["verify_all_hooks"]

    results = verify_all_hooks(expected_hooks)

    assert results["evidence_scope.py"] is True
    assert results["evidence_store.py"] is True
    assert results["file_lock.py"] is True
    assert results["StopHook_rca_contract.py"] is True
    assert results["StopHook_rca_reflector.py"] is True
    assert results["StopHook_rca_auto_promotion.py"] is True
    assert all(results.values())
