# /improve Output Schema

The stable contract for `/improve` output. Humans, downstream tools, and future
tests/validators should rely on this shape. It mirrors `skills/improve/SKILL.md`
"Required Output Sections" — when the two disagree, **SKILL.md is authoritative**
and this file should be updated to match.

## Enforcement
`advisory`. `/improve` suggests and produces review artifacts; it does not block
actions. Only a deterministic safety/contract guard would justify `strict`, and
none exists in this plugin.

## Depth default
`mode=analyze` defaults to **complete, deep analysis** (SKILL.md Operating
Principle 7). All sections receive substantive content where evidence exists —
no empty placeholders. A lighter scan is used only when the user explicitly
requests one or the artifact is tiny and self-contained; in either case the
output must state the reason and still carry provenance tags, at least one
recommendation, and a falsification condition. When in doubt, err toward too
thorough.

## Output = these headings, in order (`mode=analyze`)

0. **Inferred target** *(required opening line)* — one-line statement of what is
   being reviewed, preceded by `Inferred target:` if the target was inferred from
   session context, or the explicit artifact path/name if the user provided one.
   This is the handoff between target acquisition and analysis; every output
   must start here. For a large artifact processed under SKILL.md's
   large-artifact protocol (transcript/JSONL/chat-history/log), append the
   chunking heuristic in one phrase (e.g., `chunked by session_id, 500-line
   windows`) so the run is reproducible.
1. **Domain Classification** — `DOMAIN`, `CONFIDENCE`, `RATIONALE`, `ALTERNATIVE`.
2. **Verified Facts (with provenance)** — one fact per bullet; every bullet ends
   with a provenance tag (see below).
3. **Binding Constraint** — the one thing truly limiting quality/reliability/maintainability.
4. **Failure Modes and Missed Opportunities** — every bullet ends with a tag.
5. **Options** — ≥2 when there's a meaningful tradeoff; ≥3 (minimal/simplify,
   preserve-and-improve, delete/replace) when deletion or structural change is on
   the table. Always include a preserve-and-simplify option for any deletion.
6. **Recommendation** — short recommendation + **falsification condition** + **confidence** (high/medium/low).
7. **Persistence** — for each do-now action, the target (`code` | `test` | `hook`
   | `prompt` | `config` | `doc` | `task` | `memory` | `automation`).
8. **Verification** — how we know each action worked (test, metric, log, review gate).

## Provenance / claim tags

Append exactly one to every substantive claim:

| Tag | Meaning |
|---|---|
| `[FACT(self-verified)]` | You personally verified this from an artifact this run. |
| `[FACT(delegated-specialist)]` | Verified in a delegated specialist agent's output (parent should still spot-verify). |
| `[INFERENCE]` | Plausible interpretation from the facts; not decision-grade. |
| `[RISK]` | Plausible but unverified failure mode; name the validating check. |
| `[ASSUMPTION]` | Untested premise; must carry a proposed test. |

Rule: `Recommendation` must be traceable to `FACT(...)` entries. Never promote
`INFERENCE`/`RISK`/`ASSUMPTION` to decision-grade.

## Mode-specific output

- `mode=analyze` — full schema above.
- `mode=generate-prompt` — emits a tuned prompt (with evidence basis + the
  falsification condition the reviewer must check); no Recommendation.
- `mode=delegate-subagent` — full schema; merged delegate claims tagged
  `[FACT(delegated-specialist)]`; Recommendation only after all delegates return.
- `mode=external-second-opinion` — emits a review packet (context, questions,
  success criteria, falsification condition); no verdict.
- `mode=queue-only` — writes a review-request artifact for later; Recommendation
  left empty.

## Interim output (delegates still running)
Prefix with `Interim facts, recommendation pending delegation`. Never fill
`Recommendation` early.

## Not a JSON spec
Output is structured **text** (the headings above). Do not introduce a JSON
envelope unless a downstream consumer in this repo begins to require one.
