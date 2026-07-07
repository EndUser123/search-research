# Tournament Protocol — pairwise single-elimination ranking

When a skill needs to **rank N candidates** (pick the best option, rank resumes,
prioritize fixes, choose a retirement order), a tournament beats cold-scoring:
each head-to-head match runs in a fresh sub-agent context with a rubric, so the
model never holds all N in context at once (context-window bias + goal drift).
The bracket math is deterministic; the judgments are delegated.

This is the canonical protocol any skill cites — `/improve` (rank ≥3 options +
OPPs), `/red-team` (rank candidate fixes), `/skill-audit prune` (rank retirement
candidates). **No skill owns tournament logic**; they all reference this doc and
call the comparator as the per-match judge.

## The contract (3 pieces)

1. **Per-match judge** = the Blind Comparator agent (`agents/comparator.md`).
   It already does blind A/B with a 2-dimension rubric and emits
   `{"winner": "A"|"B"|"TIE", ...}`. Tournament mode reuses it unchanged — the
   bracket just calls it N−1 times.
2. **Bracket logic** = `scripts/tournament.py` (pure, deterministic, unit-tested).
   `pair_round(items)` seeds a round; `winner_of(pair, decision)` advances;
   `match_budget(n) == n-1`. No randomness — the repo rule.
3. **Fresh context per match** = reuse red-team's disk-backed dispatch contract
   (`red-team/commands/red-team.md` "Findings handoff"): the orchestrator holds
   only file paths; each comparator match writes `{run_dir}/match-<r>-<m>.json`
   and returns only the path.

## Algorithm

1. Collect N candidates. If N < 2, no tournament (return the single candidate).
   If N == 2, one comparator match (no bracket needed).
2. `pair_round(candidates)` → round-1 pairs (odd N → one BYE auto-advances).
3. For **each** pair: dispatch the comparator in its own sub-agent context with
   the pair + the shared rubric. BYE pairs skip the dispatch (auto-advance).
4. Read each match's `winner`, call `winner_of(pair, decision)` → round winners.
5. `pair_round(winners)` → next round. Repeat until one champion remains.
6. Emit `{run_dir}/bracket.json`: rounds, matches, decisions, champion, + the
   full placement (run a consolation pass on losers if a full ranking is needed;
   for "pick the best" the champion alone suffices).

## Why this shape

- **Fresh context per match** is the whole point — comparing 2 in isolation
  avoids the recency/salience bias that swamps cold-scoring of 50 items.
- **N−1 matches, not N²**: single-elimination is O(N log N) matches, cheap
  relative to the quality gain. Round-robin (N²) is rarely worth it.
- **Rubric up front**: define the rubric BEFORE seeding. Each match scores
  against the same rubric so results are comparable across the bracket.
- **Seeding matters**: if you have priors (e.g. similarity score, cheap-model
  pre-rank), seed strongest-vs-weakest (standard tournament seeding) so the
  final is the two strongest. With no priors, left-to-right pairing is fine.

## When NOT to tournament

- Fewer than ~4 candidates (2-3 → just compare directly; the bracket overhead
  isn't worth it).
- The ranking is deterministic (a measurable score exists) — sort, don't judge.
- The decision is hard to reverse and architectural — get a second opinion
  blind to the framing first (Recommendation Rule), then tournament the survivors.

## Verification (cold-start)

```bash
# 1) Pin the bracket invariant (N items -> exactly N-1 real matches, 1 champion):
python -m pytest plugins/skill-creator/skills/skill-creator/tests/test_tournament.py -q
# expect: 8 passed

# 2) The CLI selfcheck (no pytest):
python plugins/skill-creator/skills/skill-creator/scripts/tournament.py selfcheck

# 3) Print a first-round pairing + match budget for N candidates:
python plugins/skill-creator/skills/skill-creator/scripts/tournament.py 5
# expect: "N=5  budget=4 real matches" and 3 pairs (last is a BYE).
```

