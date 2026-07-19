# Phase 1 multi-caller rollout

Date: 2026-07-14  
Overall verdict: `PASS_PARTIAL_ROLLOUT`

## Workspace and discovery

- Repository: `P:\`, branch `main`, HEAD `7d8e103927d5a5dd47099a1e2e9fbd2d4ec52d38`.
- The worktree was already materially dirty with unrelated changes and active
  worktrees; none were reset, staged, stashed, or cleaned.
- Canonical Python: `C:\Users\brsth\AppData\Roaming\Python\Python314\python.exe`.
- Canonical pytest: `C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe`.
- Discovery reports: `P:\tmp\source-discovery-phase1-multicaller-narrow.json`
  and the earlier `/all`-focused audit. The broad audit returned `needs_review`
  because `/go` has an overlapping active plan and lifecycle/default readers;
  `/go` was therefore left unchanged. A broad token match was not treated as
  proof that the three Phase 2A files are interchangeable: `phase2a.py` is the
  policy, `evaluate_phase2a.py` is the stabilized evaluator, and
  `evaluate_phase2a_prospective.py` is the prospective evaluator.

## Caller inventory

| Caller | Consumed path and current behavior | Status | Reason |
|---|---|---|---|
| `/all` | `search-research/skills/all/orchestration.py` → `search_executor.py`; local/web unified search and formatting | `INTEGRATED` | Proven exact Phase 1 artifact handoff and live smoke |
| `/find` | `search-research/skills/find/SKILL.md` → package `core` router; rich local CKS/CHS/CDS/Code/DOCS/SKILLS semantics | `UNCHANGED_NOT_NEEDED` | Replacing it with QMD would discard established local backends and output controls |
| `/web` | `search-research/skills/web/SKILL.md` → `core/cli.py`; provider-specific modes, URL fetching, synthesis, and existing artifact output | `DEFERRED` | Semantics and provider surface are materially broader than Phase 1; replacement would be a regression |
| `/go` | `cc-skills-sdlc/skills/go/SKILL.md` → `scripts/orchestrate.py`; lifecycle, worktree, Stop, and completion gates | `BLOCKED_RUNTIME_PATH` | Active plan and full reader/writer audit overlap; research must not become a mandatory gate |
| `/review` | `cc-skills-sdlc/skills/review/SKILL.md`; review routing/contract, not a research executor | `UNCHANGED_NOT_NEEDED` | No research call site to replace |
| `/red-team` | Referenced by `adv-review`, but the documented production runner is absent | `BLOCKED_RUNTIME_PATH` | No proven consumed Phase 2A-capable caller path |
| `/improve` | References exist in adjacent skills, but no canonical consumed `/improve` implementation was found in the inspected live roots | `DEFERRED` | No safe caller path to edit |

## Implemented handoff

The existing shared `/all` adapter now records minimal integration telemetry in
the immutable run artifact:

`caller`, `caller_run_id`, `research_run_id`, task signals, selected/executed
lanes, provider outcomes, opened-source count, claim statuses, stop reason,
Phase 2A requested/executed state, total runtime, and failure class.

The caller consumes the exact path returned by `run_phase1`; it never searches
for a newest artifact. Run directories are UUID-scoped and multi-terminal
isolated. Phase 2A remains off for ordinary consequential work and is only
invoked through explicit adversarial intent.

## Evaluation

Real consumed-path evaluation: 15 `/all` executions through the plugin's
canonical virtualenv, all bounded `local-only` QMD runs to avoid unnecessary
external quota consumption. Each emitted an exact run artifact. Observed
latencies ranged from approximately 1 ms for visible QMD failures to 10.8 s
for the slowest local query. The latest representative artifact was:

`P:\tmp\.codex\state\research-run-v1\7db1610b-1a86-4319-9ce3-0cc74f257c3a\research-run.json`

It recorded caller and research IDs, QMD execution, two opened sources, and
`phase2a_executed: false`.

Static/synthetic coverage also exercised local-only, broad external,
implementation, official-source, Windows compatibility, sufficient evidence,
MMX-only, Brave-only, bounded-parallel, provider unavailable, source-opening
failure, explicit disconfirmation, consequential non-adversarial work, and
foreign-artifact handling. The real run plus these bounded checks exposed no
caller formatting regression, hidden fallback, automatic Phase 2A activation,
or secret persistence. QMD returned visible discovery-only/incomplete status
when it could not provide usable local evidence.

Canonical verification:

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider
65 passed
```

## Authorization

Authorized now: Phase 1 use in `/all`, with QMD/MMX/Brave selection governed by
the existing router, exact artifact handoff, source-opening and assessment
semantics, visible failures, and no per-call approval for healthy bounded
lanes.

Still unauthorized: automatic Phase 2A; `/go` lifecycle or completion-gate
changes; replacing `/find` or `/web`; any `/red-team` integration without a
proven runner; new providers; `agy`; hidden fallback; broker/daemon/scheduler
work; and production provider configuration.

Recommended next action: collect broader real-use evidence from `/all`, then
correct or separately design the `/web` handoff only if its existing synthesis
and provider-specific controls can be preserved. Do not integrate `/go` until
its active plan and lifecycle audit are explicitly reconciled.
