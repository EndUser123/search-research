---
title: "Codex-Pi and Grok fleet integration requires a strict schema-v5 adapter"
created: 2026-08-07
source: session-20260807
tags: [codex, pi, grok, registry, schema, model-routing, orchestrator-identity, benchmark]
summary: >
  The live Grok fleet registry is schema 5 with a flat candidates array, not
  the retired v4 models/lanes shape. Codex-to-Pi routing must consume schema 5
  through an explicit provider-alias and dispatch-path adapter, while keeping
  Grok/spawn evidence separate from Codex/Pi evidence. The registry writer must
  validate the same schema in memory before atomic replacement.
type: decision
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
confidence: 0.98
last_verified: 2026-08-07
half_life_days: 90
relations:
  - target: wiki/concepts/execution-path-comparison-spawn-opencode-pi-cli.md
    type: refines
  - target: wiki/concepts/model-selection-from-pool-decision-framework.md
    type: complements
  - target: wiki/concepts/pi-agent-harness.md
    type: related
  - target: wiki/concepts/model-routing-community-implementations-comparison-2026.md
    type: related
---

# Codex-Pi and Grok fleet integration requires a strict schema-v5 adapter

## Decision context

The first attempted Codex/Pi review was blocked before any worker call. The
active registry at `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet-models.json`
was schema 5 with 14 flat-pool candidates, while the Codex selector searched
the retired v4 `models` and `lanes` structures. The same boundary also exposed
provider naming differences (`nim`/`zen` in Grok versus `nvidia-nim`/`opencode-zen`
in Pi), so a model-name-only lookup would have been unsafe.

This was an integration defect, not evidence that Pi or the providers were
unavailable. It had to be repaired before asking an external model to review
the delegation system; otherwise the review would be testing a broken route
and its result would not be diagnostic.

## Decision

Use schema 5 as the only live registry contract. The Codex selector now:

1. requires `schema_version: 5` and `candidates`;
2. matches a candidate by its explicit registry id;
3. checks provider identity through a small explicit alias table;
4. requires `dispatch_paths` to contain `pi`;
5. gates non-active lifecycle states and `excluded` policy;
6. verifies the exact Pi provider/model and expected base URL in
   `~/.pi/agent/models.json`; and
7. labels the selected identity as `orchestrator=codex` and
   `invocation_method=pi`.

The adapter treats the shared Grok registry as a capability and policy source,
not as Codex/Pi benchmark evidence. An evidence block is eligible for latency
ranking only when its own identity explicitly says `orchestrator=codex` and
`invocation_method=pi`. Grok `spawn` records and spawn-only compatibility
views therefore cannot silently rank a Codex/Pi call.

The Grok registry writer now imports the same in-memory v5 validator used by
the schema CLI, rejects v4 input, records provenance, and atomically replaces
the file with a previous-file backup. This removes the second failure mode in
which the active file was v5 but the writer still imported the removed v4
`validate` function.

## Why this is the right boundary

The strict version gate makes schema drift visible instead of falling through
to a false “provider unavailable” diagnosis. Explicit aliases are safer than
deriving a provider from a model name: the same model family can exist in
multiple provider pools, and Pi’s configured provider id is part of the
runtime identity.

Using `dispatch_paths` rather than the primary `dispatch_path` is intentional.
The live registry can say that Grok’s primary path is `spawn` while Pi is also
an allowed path. Conversely, `serde_broken` and
`tool_grounded_spawn_broken` are not global Pi failures; the adapter does not
apply those spawn-only views to a Pi route.

## What public projects contributed

The checked projects do not provide an exact drop-in for this Codex/Pi/Grok
boundary — that is a scoped research conclusion, not proof that no such
project exists. They do provide reusable patterns:

* [Worktrunk](https://github.com/max-sixty/worktrunk) demonstrates a focused
  worktree lifecycle with explicit create, switch, list, remove, and hooks.
* [Overstory](https://github.com/jayminwest/overstory) demonstrates durable
  coordinator state, typed messages, WAL-backed storage, watchdogs, merge
  queues, and crash recovery. Its cleanup behavior is also a useful warning:
  dirty or unmerged worktrees should be skipped or made explicit, not silently
  force-deleted.
* [MCO](https://github.com/mco-org/mco) demonstrates explicit provider/agent
  selection and parallel review without pretending that raw answers are an
  automatic consensus. It deliberately does not manage worktrees.
* [Gas Town](https://github.com/gastownhall/gastown) demonstrates durable
  identities, task ledgers, mailboxes, and handoffs, but its larger control
  plane is heavier than this package needs.
* The [Git worktree documentation](https://git-scm.com/docs/git-worktree.html)
  supports explicit lock, repair, prune, and clean-removal semantics that are
  relevant to the separate worktree lifecycle.

## What people like

Practitioners consistently value explicit worker identity, durable receipts,
isolated worktrees, resumable handoffs, and a coordinator that can explain why
one provider/path was selected. These patterns make failures inspectable and
make cleanup conservative after a crash.

## What people do not like

Heavy orchestration projects add state stores, watchdogs, merge queues, and
operational ceremony before a small delegation bridge needs them. Provider
aliases and compatibility shims also look convenient but hide schema drift and
can mix evidence from different invocation paths. The smallest useful design
here is therefore a strict adapter plus explicit receipts, not a new general
purpose orchestration framework.

## Receipts

Local implementation receipts:

* `P:/packages/codex-external-delegation/src/model-selector.mjs:302-318`
  implements the schema-5/id/provider-alias/dispatch-path adapter.
* `P:/packages/codex-external-delegation/src/model-selector.mjs:327-431`
  applies lifecycle, policy, Pi configuration, base-url, quota, and
  identity-bound evidence gates.
* `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_schema.py:385-451`
  exposes the shared in-memory/file validator.
* `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_writer.py:46-66`
  rejects v4 input and validates the v5 candidate before the atomic write.
* `P:/packages/codex-external-delegation/tests/model-selector.test.mjs:116-158`
  is the regression test for the live v5 shape and spawn-only view isolation.

Fresh verification receipts:

* Codex package suite: 103/103 tests passed.
* Grok model-quota registry/schema tests: 28 passed.
* Grok model-benchmark tests: 54 passed; benchmark module import succeeded.
* Active registry schema validator passed.
* Registry writer dry-run passed without applying a live write.
* `external-delegation check --worker pi` found Pi 0.82.1.
* The real CLI route selected `nvidia-nim/deepseek-ai/deepseek-v4-flash`
  provisionally from the active registry and Pi config; no external worker
  call was made during this repair.

## What this means for our workspace

Keep the active registry on schema 5 and update tests/consumers against the
flat `candidates` contract. Do not restore v4 lookup as a silent fallback.
Before any external review, require the route check above plus an identity and
result-contract smoke through the real runner. Record Codex/Pi evidence under
the four-part identity `(provider, model, invocation_method, orchestrator)`;
Grok/spawn evidence remains separate.

The current `model-benchmark` write-back code still deserves a separate,
identity-aware review before enabling registry promotion for new benchmark
data. Until that is implemented, keep benchmark measurements in telemetry or
sequestered artifacts and do not treat a successful writer dry-run as proof
that benchmark evidence has been promoted.

## Falsifier

Re-litigate this decision if the canonical Grok registry moves to a newer
validated schema, if the registry begins publishing explicit Codex/Pi
identity-bound records that require a different lookup, or if a maintained
project supplies a tested drop-in adapter with equivalent identity and failure
semantics. A live route that selects a provider whose Pi configuration or
dispatch path does not match the receipt would also falsify the current
adapter.

## Claim ledger

| Claim | Type | Evidence | Verification method | Confidence | Falsifier | Action allowed |
|---|---|---|---|---|---|---|
| The active registry is schema 5 with flat candidates | verified_fact | Active JSON and schema validator | Run `registry_schema.py` and inspect `schema_version`/`candidates` | high | Validator accepts a different canonical shape | Use v5 adapter |
| The old selector caused the blocked route | verified_fact | Selector only read v4 keys; v5 regression was red before patch | Reproduce route before/after adapter | high | A different failure remains with v5 | Keep RCA scoped |
| Grok/spawn evidence must not rank Codex/Pi | verified_fact | Four-part identity contract and adapter guard | Add mismatched evidence fixture; assert no latency rank | high | Shared evidence is explicitly identity-bound | Permit only matching evidence |
| Checked public repos provide patterns, not a drop-in | inference | Worktrunk, Overstory, MCO, Gas Town, Git docs | Re-run repository comparison when scope expands | medium | Exact maintained Codex/Pi registry adapter found | Reuse only matching components |
| Benchmark write-back is safe for v5 promotion | unsupported | Current benchmark writer is v4-shaped | Audit and test identity-aware promotion path | low | Dedicated v5 evidence writer passes | Keep promotion disabled |

## Related

[[execution-path-comparison-spawn-opencode-pi-cli]]
[[model-selection-from-pool-decision-framework]]
[[pi-agent-harness]]
[[model-routing-community-implementations-comparison-2026]]

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[agent-config-directory-taxonomy]]
- [[grok-build-workflows-rhai-orchestration]]
- [[agent-control-plane-enforcement-architectures-2026]]

## Sources

* `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet-models.json`
* `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_schema.py`
* `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_writer.py`
* `P:/packages/codex-external-delegation/src/model-selector.mjs`
* `P:/packages/codex-external-delegation/docs/grok-fleet-benchmark-normalized-2026-08-06.md`
* `P:/packages/codex-external-delegation/docs/pi-calibration-results-2026-08-06.md`
* [Worktrunk](https://github.com/max-sixty/worktrunk)
* [Overstory](https://github.com/jayminwest/overstory)
* [MCO](https://github.com/mco-org/mco)
* [Gas Town](https://github.com/gastownhall/gastown)
* [Git worktree](https://git-scm.com/docs/git-worktree.html)
