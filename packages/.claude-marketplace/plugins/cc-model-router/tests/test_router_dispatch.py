"""Smoke test for cc-model-router __lib/router.py dispatch wiring.

The router is the sole entry point (registered in settings.json). It has zero
test coverage otherwise — a typo in DISPATCH would silently disable hooks.
This test pins the expected mapping so mis-wiring an event fails loudly.

Unit-test layer (not integration): this proves the static DISPATCH/PHASE_DIR
contracts, not the subprocess execution. An integration test that actually
spawns the router with a sample payload lives elsewhere; this one is the
smallest sufficient proof that the dispatch table is correct.
"""
import importlib.util
import sys
from pathlib import Path

ROUTER_PATH = (
    Path(__file__).resolve().parent.parent / "__lib" / "router.py"
)


def _load_router_module():
    spec = importlib.util.spec_from_file_location("ccmr_router", ROUTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ccmr_router"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_session_start_dispatch():
    """SessionStart must dispatch to model_router_init.py only."""
    mod = _load_router_module()
    assert mod.DISPATCH["SessionStart"] == ["model_router_init.py"]


def test_user_prompt_submit_dispatch():
    """UserPromptSubmit must dispatch classify THEN apply (order matters)."""
    mod = _load_router_module()
    assert mod.DISPATCH["UserPromptSubmit"] == [
        "model_router_classify.py",
        "model_router_apply.py",
    ]


def test_phase_dir_mapping():
    """Event names map to the correct hook subdirectory."""
    mod = _load_router_module()
    assert mod.PHASE_DIR["SessionStart"] == "sessionstart"
    assert mod.PHASE_DIR["UserPromptSubmit"] == "userpromptsubmit"


def test_dispatched_hook_files_exist():
    """Every hook named in DISPATCH must exist on disk — else silent no-op."""
    mod = _load_router_module()
    hooks_dir = ROUTER_PATH.parent.parent / "hooks"
    for event, hook_names in mod.DISPATCH.items():
        phase = mod.PHASE_DIR[event]
        for hook_name in hook_names:
            hook_path = hooks_dir / phase / hook_name
            assert hook_path.exists(), (
                f"Dispatched hook for {event} missing on disk: {hook_path}"
            )


def test_no_unknown_events_silently_added():
    """DISPATCH only contains the two events the router is registered for.

    A third event added without a PHASE_DIR entry would silently no-op (router.py
    falls through to sys.exit(0)). Pin the key set so a future addition forces
    a deliberate PHASE_DIR update.
    """
    mod = _load_router_module()
    assert set(mod.DISPATCH.keys()) == {"SessionStart", "UserPromptSubmit"}
