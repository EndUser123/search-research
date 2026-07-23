# /red-team workspace overlay — adaptive investigation + precision incentives + cross-model specialists

This file is a workspace-level overlay that extends the bundled /red-team
skill with three features: **adaptive investigation space expansion**,
**specialist precision incentives**, and **cross-model specialist dispatch**.

## When this overlay applies

This overlay adds the features described below to every /red-team
run. It does not replace or modify any other aspect of the bundled skill.
All other phases (planning, specialist dispatch, critic verification,
synthesis, telemetry) remain unchanged.

## Expansion gate (runs after specialist manifest, before critic dispatch)

After all specialists return and the dispatch manifest is written, the
orchestrator reviews the combined findings for **new attack surfaces**
that the original plan didn't cover. This is confidence-gated expansion:
the orchestrator must be confident the operator would want more
investigation, not just curious about a tangent.

### Expansion trigger (all three required)

1. A specialist finding reveals a defect class or attack surface that
   **none of the dispatched specialists was scoped to investigate** (not
   a deeper version of an existing finding — a genuinely new surface).
2. The finding is **severity HIGH or CRITICAL** (medium/low findings
   don't trigger expansion — they go in the synthesis as-is).
3. The orchestrator is **highly confident** the operator would want this
   investigated in the same run rather than deferred to a future one.

### Expansion mechanics (bounded)

| Constraint | Limit |
|---|---|
| Max expansion rounds per run | **1** (one-shot: expanded specialists cannot trigger further expansion) |
| Max additional specialists per expansion | **2** |
| Specialist types available for expansion | any specialist from the standard roster, OR a custom specialist scoped to the new surface |
| Budget disclosure | state the expansion decision + specialist count + estimated time before dispatching |

### What does NOT trigger expansion

- A finding that's a deeper version of something another specialist already covered → fold into existing finding, don't expand
- A finding about a different part of the system than the target → note in synthesis, don't expand (wrong scope)
- A medium/low finding that's interesting but not urgent → note in synthesis, don't expand
- Curiosity about whether a pattern exists elsewhere → not confident enough, don't expand

### Expansion output

- Expanded specialists write to `{run_dir}/specialists/<name>-expanded.json`
- The dispatch manifest gets an `expansion` section recording: trigger finding, new specialist, rationale
- The synthesis includes expanded findings alongside original findings, tagged `[expanded]`

### Why one-shot, not recursive

Recursive expansion (E→F→G...) creates unbounded latency and makes the
synthesis reference a plan that drifted far from the original. One-shot
expansion catches the highest-value adjacent surface without
rabbit-holing. The /review skill's sufficiency stop is the mirror:
contract when enough evidence exists; expand when a genuinely new
HIGH/CRITICAL surface appears.

## Precision incentive (applies to every specialist dispatch)

**The over-reporting problem:** specialists generate many speculative
findings because there's no cost to being wrong — a false positive looks
thorough, while a missed finding looks like a gap. The 2026 Entelligence
benchmark shows precision ranges from 16% to 67% across AI reviewers,
meaning most findings from most tools are noise.

**Add this paragraph to every specialist dispatch prompt:**

> **Precision incentive:** Each finding that the critic marks
> `non_reproducible` reduces your specialist's quality signal. Prefer
> fewer high-confidence findings over many speculative ones. If you are
> <70% confident a finding is real, either drop it or explicitly label
> it `[speculative]` so the critic can weight it lower. The goal is
> precision, not volume. A specialist with 5 verified findings out of 7
> reported is better than one with 5 verified out of 20.

**Critic-side precision tracking:** the critic's verdicts (verified vs.
non_reproducible) are the precision signal — NOT operator acceptance
(operator trust makes acceptance unreliable). Precision per specialist =
verified / (verified + non_reproducible). Track in telemetry. After 5+
runs, specialists below 30% precision get prompt revisions in the
Phase 3b improvement loop.

## Cross-model specialist (one per run)

**The correlated-errors problem:** all parent-model specialists share
blind spots from the same model family. Research (FERZ Oct 2025, Cemri
2025) confirms that same-family N-agents barely outperform N=1 on
uncorrelated error detection. Cross-model diversity is the highest-
leverage decorrelation.

**Rule:** one specialist per /red-team run uses a cross-model CLI instead
of parent-model spawn_subagent. Use /agy (Antigravity/Gemini), /codex
(OpenAI), or /mmx (MiniMax). **Do NOT use Claude or Anthropic models**
(operator constraint).

**Which specialist gets the cross-model slot:** the one with the highest
expected value from independent verification — typically the correctness
or logic specialist, since those catch bugs most likely to share blind
spots across same-family agents.

**Implementation:** dispatch via the skill's shell-out pattern (the
specialist prompt is written to a file, the CLI runs against it, output
is parsed into the standard findings JSON). Tag findings from the cross-
model specialist with `[cross-model: <slug>]` in the synthesis.

**Telemetry:** record `cross_model_specialist: <slug>` in the run's
telemetry line. After 5+ runs, compare cross-model specialist precision
vs parent-model specialist precision to validate the decorrelation claim.

## Provenance

Added 2026-07-23:
- **Expansion gate:** after the operator's /red-team review of /tp, where
  the operator asked for adaptive expansion.
- **Precision incentive + cross-model specialist:** after /www research
  on improving red-team analysis. The 2026 Entelligence benchmark (67
  bugs, 8 tools) proved precision is the dominant quality problem (F1
  scores 13-47%, precision 16-67%). Source: wiki concept
  `improving-red-team-precision-and-cross-model.md`.
