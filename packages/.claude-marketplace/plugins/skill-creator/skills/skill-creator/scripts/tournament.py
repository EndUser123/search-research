#!/usr/bin/env python3
"""tournament.py - deterministic single-elimination bracket logic.

Pure logic, no I/O, no randomness. The bracket math for the tournament mode of
the Blind Comparator (agents/comparator.md) + references/tournament_protocol.md.
Any skill that needs to rank N candidates (improve / red-team / skill-audit prune)
cites the protocol and uses this for the schedule.

Single-elimination invariant: N items -> exactly N-1 real matches (each match
eliminates one; byes auto-advance without a match). Verified in selfcheck.

Usage:
  python tournament.py <N>            # print the first-round pairing + match budget
  python tournament.py selfcheck
"""
from __future__ import annotations
import sys
from typing import Any

BYE = "__BYE__"  # sentinel for an auto-advancing slot (odd item count)


def pair_round(items: list[Any]) -> list[tuple[Any, Any]]:
    """Pair items left-to-right; an odd leftover is paired with BYE (auto-advance)."""
    pairs: list[tuple[Any, Any]] = []
    for i in range(0, len(items) - 1, 2):
        pairs.append((items[i], items[i + 1]))
    if len(items) % 2 == 1:
        pairs.append((items[-1], BYE))
    return pairs


def is_real_match(p: tuple[Any, Any]) -> bool:
    return BYE not in p


def winner_of(p: tuple[Any, Any], decision: str) -> Any:
    """Map a per-match decision ('a'|'b'|'tie') to the advancing item.

    'tie' -> the 'a' item by convention (the bracket must progress; the
    orchestrator's rubric should have broken the tie before calling this).
    A BYE match auto-advances its real item regardless of decision.
    """
    a, b = p
    if b == BYE:
        return a
    if a == BYE:
        return b
    return a if decision != "b" else b


def match_budget(n: int) -> int:
    """Total real matches to crown a champion from n items (single-elim invariant)."""
    return max(0, n - 1)


def _selfcheck() -> None:
    # Pairing: even N -> N/2 real pairs, no BYE.
    assert pair_round(["a", "b", "c", "d"]) == [("a", "b"), ("c", "d")]
    # Odd N -> last item gets a BYE.
    assert pair_round(["a", "b", "c"]) == [("a", "b"), ("c", BYE)]
    # Invariant: total real matches across a full tournament == N-1.
    for n in range(1, 9):
        items = list(range(n))
        rounds: list[list[tuple]] = []
        real = 0
        cur = items
        while len(cur) > 1:
            pr = pair_round(cur)
            rounds.append(pr)
            real += sum(1 for p in pr if is_real_match(p))
            # simulate: lower index wins each real match; BYE auto-advances
            cur = [winner_of(p, "a") for p in pr]
        assert real == match_budget(n), f"n={n}: {real} != {match_budget(n)}"
        assert len(cur) == 1, f"n={n}: not one champion ({cur})"
    # winner_of: 'b' decision picks second; tie/BYE rules.
    assert winner_of(("a", "b"), "b") == "b"
    assert winner_of(("a", "b"), "a") == "a"
    assert winner_of(("a", "b"), "tie") == "a"
    assert winner_of(("c", BYE), "a") == "c"
    print(f"selfcheck OK: bracket invariant holds for N=1..8 (N-1 real matches, 1 champion)")


def _print_schedule(n: int) -> None:
    items = [f"item_{i}" for i in range(n)]
    print(f"N={n}  budget={match_budget(n)} real matches (single-elim)")
    print(f"round 1 pairs: {pair_round(items)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(0)
    if args[0] == "selfcheck":
        _selfcheck(); sys.exit(0)
    if args[0].isdigit():
        _print_schedule(int(args[0])); sys.exit(0)
    print(__doc__); sys.exit(1)
