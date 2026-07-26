---
title: "Instruction-to-state closure gap: desired state and obligation ledgers"
concept_type: "design-decision"
created: 2026-07-25
agent: codex
host: both
verification: "web-research-backed"
sources:
  - https://developer.hashicorp.com/terraform/language/state/purpose
  - https://www.hashicorp.com/en/blog/detecting-and-managing-drift-with-terraform
  - https://learn.microsoft.com/en-us/azure/sre-agent/agent-hooks
  - https://bazel.build/concepts/hermeticity
  - https://bazel.build/versions/7.5.0/reference/test-encyclopedia?hl=en
  - https://arxiv.org/abs/2602.11988
tags: [agent-runtime, state-management, completion-verification, configuration-drift, obligations, design-pattern]
summary: >
  Repeated cleanup and re-verification are symptoms of an instruction-to-state
  closure gap: the runtime records actions and some evidence, but does not keep
  a durable, task-scoped contract connecting the instruction, expected end
  state, current observed state, owner, and fresh completion evidence. The
  recommended design is a small stable desired-state manifest plus a
  session-scoped obligation ledger, backed by external-state verification and
  isolated tests.
relations:
  - target: wiki/concepts/external-state-cross-check-as-structural-fix
    type: extends
  - target: wiki/concepts/verification-state-tracking-content-identity-vs-temporal-proxies
    type: related
  - target: wiki/concepts/verification-before-completion-principle
    type: related
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build
    type: related
---

# Instruction-to-state closure gap

## Problem name

Use **Instruction-to-State Closure Gap (ISCG)** as the issue name.

The underlying root cause can be described as **conversation-centric
completion**: the agent can discuss, perform, and report a change without a
durable machine-checked link between the instruction and the current external
state. “Repeated stale cleanup” is the visible symptom; lost or untracked
postconditions are the mechanism.

## Observed local shape

The Grok runtime already has useful pieces:

- `C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py` records
  verification receipts and modified-file fingerprints.
- `C:/Users/brsth/.grok/hooks/scripts/quality_gate.py` consumes receipt state to
  detect stale verification for modified code.
- `C:/Users/brsth/.grok/active-surface.last.md` records the hook/configuration
  surface observed at session start.

Those pieces answer parts of “what action happened?” and “was this code state
verified?” They do not, by themselves, represent every instruction-specific
postcondition such as “this diagnostic hook must be removed,” “this generated
artifact must not be recreated,” or “the active runtime must contain exactly
this hook set.” A session-start snapshot can also become stale after
configuration changes.

## External evidence and trade-offs

Desired-state systems are valuable because they compare declared configuration
with real-world state and expose drift. Terraform documents state as the
mapping between configuration and real infrastructure, while HashiCorp’s drift
guidance uses the same configuration/state/plan model for reconciliation.
[Terraform state](https://developer.hashicorp.com/terraform/language/state/purpose)
[HashiCorp drift guidance](https://www.hashicorp.com/en/blog/detecting-and-managing-drift-with-terraform)

The recurring cost is the state layer itself: freshness, out-of-band changes,
locking, ownership, and coordination. Therefore a full machine-wide manifest
would likely reproduce the complexity that makes large desired-state systems
unpopular.

Hermetic testing is a complementary solution, not a replacement for state.
Bazel describes hermetic builds and tests as isolated, reproducible, and based
on declared inputs. This makes a temporary canary configuration suitable for
testing hook discovery and enforcement without contaminating persistent
configuration.
[Bazel hermeticity](https://bazel.build/concepts/hermeticity)
[Bazel test environment](https://bazel.build/versions/7.5.0/reference/test-encyclopedia?hl=en)

Hook systems are useful enforcement points: Microsoft documents agent hooks as
places to evaluate tool use and stop or continue behavior. The lesson for Grok
is to make hooks enforce an independently derived state result; the hook should
not be the sole author of the state it evaluates.
[Microsoft Agent Hooks](https://learn.microsoft.com/en-us/azure/sre-agent/agent-hooks)

Large instruction files are not a free substitute. A recent empirical study of
`AGENTS.md` files found that excessive or unnecessary requirements can reduce
task success and increase inference cost. Stable policy belongs in instructions;
volatile task state belongs in machine-readable artifacts.
[AGENTS.md study](https://arxiv.org/abs/2602.11988)

## Recommended architecture

Use two layers rather than one giant manifest:

1. **Stable desired-state manifest** — what the normal runtime should contain:
   enabled/disabled hooks, authoritative configuration paths, expected command
   paths, ownership, and lifecycle.
2. **Session-scoped obligation ledger** — what the current instruction requires:
   expected end state, files/configuration in scope, verifier, evidence
   fingerprint, owner/session, and lifecycle status (`OPEN`, `SATISFIED`,
   `BLOCKED`, or `SUPERSEDED`).

The completion path becomes:

```text
instruction -> obligation -> mutation -> observed state
           -> desired/current comparison -> fresh evidence -> claim allowed
```

The Stop hook should block an unsupported completion claim when an obligation
is open, the observed state disagrees with the required state, or the evidence
fingerprint is stale. It should not infer a new obligation from vague prose at
Stop time; obligation creation should happen at instruction/task intake or via
an explicit command.

## Design constraints

- Hash or otherwise bind evidence to the actual files/configuration inspected.
- Recompute active runtime state when configuration changes; do not treat a
  session-start snapshot as current proof.
- Record ownership and session identity so one session cannot dismiss another
  session’s work as irrelevant.
- Make missing, malformed, or unreadable obligation state a visible degraded
  condition, not an implicit success.
- Keep canary tests hermetic and ephemeral, with cleanup itself verified.
- Keep AGENTS.md focused on durable policy and pointers, not a complete live
  inventory.

## Alternatives considered

| Alternative | Decision | Reason |
|---|---|---|
| Stronger prose rules | Reject as primary fix | The agent can rationalize around rules it controls. |
| Giant machine-wide manifest | Defer | Better visibility, but excessive state/ownership/maintenance cost. |
| Receipts only | Insufficient | Receipts prove actions/evidence, not that every instruction postcondition exists. |
| Hooks only | Insufficient | Hooks enforce decisions but need an external source of truth. |
| Obligation ledger plus narrow manifest | Select | Captures task-specific intent without making every artifact globally managed. |
| Hermetic tests alone | Complementary | Prevents test contamination but does not track persistent desired state. |

## Falsifier

This design is wrong if the existing receipt and active-surface mechanisms can
already represent and enforce arbitrary instruction-specific postconditions
without adding a durable obligation concept. The first implementation branch
must therefore inventory their schemas and prove the smallest missing case
before adding new state.

## Related

- [[external-state-cross-check-as-structural-fix]]@extends
- [[verification-state-tracking-content-identity-vs-temporal-proxies]]@related
- [[verification-before-completion-principle]]@related
- [[best-practices-enforcement-mechanism-grok-build]]@related

## Sources

- Local runtime inspection on 2026-07-25: quality-gate, receipt-writer, and
  active-surface artifacts named above.
- External research listed in frontmatter and linked inline.
