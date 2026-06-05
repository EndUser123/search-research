"""Regression tests for the anti-dodge adjudicator FAIL-OPEN policy (2026-06-03).

Root cause pinned here: on 2026-06-03 a legitimate, evidence-tagged analytical
response was wrongly blocked as `self_referential_evasion`. The judge itself was
fine — it returned ALLOW on that text when re-run. The block came from the FAIL-SAFE
direction: when both providers were rate-limited, `adjudicate()` returned 'unknown'
and `_adjudicate_candidate` failed CLOSED (block), re-introducing exactly the
use/mention false positive the judge exists to remove.

The fix flips the adjudicated-candidate fail-safe to FAIL OPEN:
  * judge 'unknown' / judge-side error -> ALLOW  (the regex candidate is high-FP by
    construction; during a transient judge outage, letting it through is the lesser harm)
  * judge 'block'  -> BLOCK   (genuine dodge enforcement is preserved)
  * judge 'allow'  -> ALLOW
  * feature disabled -> BLOCK (legacy gate when the feature is off)

Capitulation-under-challenge is NOT routed through the adjudicator, so the strongest
anti-sycophancy enforcement is unaffected by this change.

These tests must NOT hit the network: a fake `anti_dodge_judge` module is injected so
each verdict is forced deterministically.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_LIB = _PLUGIN_ROOT / "__lib"
_GLOBAL_HOOKS = Path("P:/.claude/hooks")
for _p in (
    str(_PLUGIN_ROOT),
    str(_LIB),
    str(_PLUGIN_ROOT / "hooks" / "stop"),
    str(_GLOBAL_HOOKS),
    str(_GLOBAL_HOOKS / "__lib__"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_HOOK_SRC = _PLUGIN_ROOT / "hooks" / "stop" / "StopHook_unverified_stance.py"


class _FakeJudge:
    """Controllable stand-in for anti_dodge_judge.adjudicate (no network)."""

    verdict = "unknown"

    def adjudicate(self, *_a, **_k):  # signature-compatible
        return self.verdict


@pytest.fixture(scope="module")
def hook():
    """Load StopHook_unverified_stance with a fake adjudicator injected."""
    fake = types.ModuleType("anti_dodge_judge")
    _f = _FakeJudge()
    fake.adjudicate = _f.adjudicate  # type: ignore[attr-defined]
    fake._fake = _f  # type: ignore[attr-defined]
    sys.modules["anti_dodge_judge"] = fake

    spec = importlib.util.spec_from_file_location("suvs_failopen", _HOOK_SRC)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # pragma: no cover - environment-dependent import chain
        pytest.skip(f"hook import chain unavailable in this env: {exc}")
    mod._fake_judge = _f  # attach control handle
    return mod


def _decide(hook, verdict: str, *, enabled: bool = True, monkeypatch=None) -> str:
    hook._fake_judge.verdict = verdict
    val = "true" if enabled else "false"
    monkeypatch.setenv("ANTI_DODGE_JUDGE_ENABLED", val)
    return hook._adjudicate_candidate("hedged analysis discussing the hedge", [], "Hedge")


def test_unknown_fails_open(hook, monkeypatch):
    # The actual 2026-06-03 failure mode: providers unavailable -> 'unknown'.
    assert _decide(hook, "unknown", monkeypatch=monkeypatch) == "allow"


def test_explicit_block_still_blocks(hook, monkeypatch):
    # Enforcement preserved when the judge is up and says BLOCK.
    assert _decide(hook, "block", monkeypatch=monkeypatch) == "block"


def test_explicit_allow_allows(hook, monkeypatch):
    assert _decide(hook, "allow", monkeypatch=monkeypatch) == "allow"


def test_disabled_uses_legacy_block(hook, monkeypatch):
    # Feature OFF -> preserve the legacy (pre-judge) gate behavior.
    assert _decide(hook, "allow", enabled=False, monkeypatch=monkeypatch) == "block"


def test_decision_is_logged_with_fail_open_flag(hook, monkeypatch):
    logf = hook.ADJUDICATION_LOG_FILE
    if logf.exists():
        logf.unlink()
    _decide(hook, "unknown", monkeypatch=monkeypatch)
    assert logf.exists(), "adjudication decision must be logged for observability"
    import json

    last = [ln for ln in logf.read_text(encoding="utf-8").splitlines() if ln.strip()][-1]
    rec = json.loads(last)
    assert rec["verdict"] == "unknown"
    assert rec["decision"] == "allow"
    assert rec["fail_open"] is True
