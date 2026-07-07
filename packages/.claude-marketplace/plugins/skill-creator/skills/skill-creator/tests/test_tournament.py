"""test_tournament.py - codify tournament.py bracket logic.

Asserts the single-elimination invariant (N-1 real matches, exactly 1 champion)
and the BYE-handling rules. Plus the CLI `selfcheck` exit code so the script
remains self-testable from any working directory.
"""
from __future__ import annotations
import importlib.util, json, subprocess, sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "tournament.py"
_SPEC = importlib.util.spec_from_file_location("_tournament_under_test", SCRIPT)
assert _SPEC.loader is not None
T = importlib.util.module_from_spec(_SPEC)  # type: ignore[arg-type]
_SPEC.loader.exec_module(T)


def test_even_round_pairing():
    assert T.pair_round(["a", "b", "c", "d"]) == [("a", "b"), ("c", "d")]


def test_odd_round_bye():
    assert T.pair_round(["a", "b", "c"]) == [("a", "b"), ("c", T.BYE)]


def test_single_item_returns_pair_with_bye():
    assert T.pair_round(["only"]) == [("only", T.BYE)]


def test_match_budget_invariant():
    for n in range(1, 9):
        assert T.match_budget(n) == max(0, n - 1)


def test_simulated_tournament_single_elim_invariant():
    """N items -> exactly N-1 real matches across all rounds, 1 champion."""
    for n in range(1, 9):
        items = list(range(n))
        rounds = []
        real = 0
        cur = items
        while len(cur) > 1:
            pr = T.pair_round(cur)
            rounds.append(pr)
            real += sum(1 for p in pr if T.is_real_match(p))
            cur = [T.winner_of(p, "a") for p in pr]
        assert real == T.match_budget(n), f"n={n}: {real} != {T.match_budget(n)}"
        assert len(cur) == 1, f"n={n}: not one champion ({cur})"


def test_winner_of_decisions_and_byes():
    assert T.winner_of(("a", "b"), "a") == "a"
    assert T.winner_of(("a", "b"), "b") == "b"
    assert T.winner_of(("a", "b"), "tie") == "a"   # tie -> first item by convention
    assert T.winner_of(("c", T.BYE), "b") == "c"  # BYE auto-advances the real item
    assert T.winner_of((T.BYE, "x"), "a") == "x"  # BYE on the left


def test_is_real_match():
    assert T.is_real_match(("a", "b")) is True
    assert T.is_real_match(("c", T.BYE)) is False
    assert T.is_real_match((T.BYE, "d")) is False


def test_cli_selfcheck():
    """The `selfcheck` CLI arg must exit 0 and print `selfcheck OK`."""
    import shutil
    py = shutil.which("python") or sys.executable
    r = subprocess.run([py, str(SCRIPT), "selfcheck"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "selfcheck OK" in r.stdout