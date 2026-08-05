# ADR-010: Use Pi with provider-aware model selection

## Status

Accepted

## Date

2026-08-04

## Context

Codex needs a lower-cost external worker for bounded, low-ambiguity tasks. The
worker must receive an explicit packet, operate within a bounded tool surface,
return machine-consumable evidence, and never be silently replaced by another
worker when it fails. The model choice must account for task fit, provider,
quota pool, context, capability, health, and latency.

Open Dynamic Workflow was audited as a possible replacement. It provides useful
provider, process, artifact, retry, and structured-output patterns, but its Pi
adapter uses Pi JSON mode rather than RPC, does not own our packet/result
contract, and permits retry through workflow/profile/call configuration.

The local Pi installation already has a proven non-interactive invocation shape
in the existing delegation package:

```text
pi -p --no-session --mode json --model <model> --tools read,grep,find,ls
```

## Decision

Use Pi as the default automatic dispatch path for `BOUNDED_EXECUTION`. Select an
exact `(model, provider, path)` candidate at routing time. Do not use one
universal model default.

The initial candidate policy is:

- OpenCode Go DeepSeek for eligible mechanical/extraction work only when a
  fresh quota snapshot reports headroom in every reported subscription window;
- NVIDIA DeepSeek for mechanical work when its capability and rate limits fit;
- NVIDIA Nemotron 3 Ultra through Pi for reasoning work when its Pi-verified
  transport remains healthy;
- MiniMax M3 through MiniMax for coding and structured-output work;
- GLM-5.2 through Z.ai for reasoning-heavy bounded work;
- Zen DeepSeek as an alternate eligible pool.

Quota is evaluated as a provider-pool constraint, not as a generic free-model
preference. The Grok `fleet_quota.py` refresh is the normalized producer at
`~/.cache/opencode/fleet-quota-cache.json`; the selector also reads the
per-provider `opencode-quota` state when the normalized cache does not contain
that provider. A 30-minute freshness bound applies to quota-backed shared
subscriptions. A fresh zero in any reported window makes a shared provider
ineligible. Dedicated regenerating providers may remain eligible when their
snapshot is missing or stale, but a fresh zero blocks them. NVIDIA is modeled
as unlimited with a rate limit because it has no quota API; it is not rejected
because the quota cache has no NVIDIA row. Zen-free is modeled as a
rate-limited free pool for the same reason.

The v4 fleet registry's canonical health is per transport at
`models[*].transports`. Grok's legacy top-level `serde_broken` and
`spawn_broken` arrays are compatibility views for `spawn_subagent` only; a Pi
or OpenCode failure must not become a global serde diagnosis, and quota
exhaustion must not become `serde_broken`. The shared `registry_writer.py`
regenerates those views under a cross-process lock, validates the candidate,
records provenance, and replaces the file atomically. The active benchmark
write-back uses that updater; the historical v3-to-v4 migration refuses to
operate on an existing v4 registry.

Keep OpenCode available as an explicit alternative. A failed Pi invocation
halts the delegation and returns its failure evidence; it does not invoke
OpenCode, agy, MMX, or another worker automatically.

Codex remains authoritative for classification, packet construction, model
selection, containment, verification, and acceptance. Pi remains a leaf worker.

## Alternatives considered

### Open Dynamic Workflow as the complete orchestration layer

Rejected as a drop-in replacement. It contains valuable reusable patterns, but
its workflow engine would introduce a second policy owner and does not provide
our required packet hash, terminal-result rule, or no-fallback contract.

### OpenCode as the default worker

Superseded. OpenCode remains an explicit alternative, but Pi is the selected
default because it is already installed, already wired into the package, and
has an existing bounded read-only invocation and smoke evidence.

### Pi RPC as the first implementation path

Deferred. The current JSON event-mode path is already implemented and tested.
RPC remains a follow-up only if JSON mode fails a concrete acceptance gate such
as event correlation, terminal-state proof, or output framing.

## Consequences

- The generic classifier emits Pi packets for eligible bounded work.
- The selector records the chosen model, provider, quota pool, reasons, and
  confidence in the packet.
- OpenCode packets require explicit selection and a fresh invocation.
- The existing marker-based result contract remains authoritative.
- Pi high-availability/failover is not part of the delegation architecture.
  The `pi-high-availability` package and its `ha.json` configuration are
  removed; each delegation invocation targets one explicit provider/model and
  stops on failure.
- The Codex-facing skill is named `codex-pi`. It does not depend on the
  Grok/Claude `/go` command. Write-mode worktrees use the shared lifecycle
  helper directly, while Codex validates the resulting worktree identity and
  owns acceptance.
- Automatic selection reads the local fleet registry, Pi model registry, and
  quota sources. Packet-supplied provider health is not an authority. A
  provisional selection is allowed when those local sources establish
  capability and current quota eligibility but transport history is
  incomplete; runtime provider/model identity verification remains mandatory.
- OpenCode model arguments are qualified as `<provider>/<model>` at command
  construction when a caller supplies a provider-local model ID. This avoids
  silently routing a model such as `deepseek-ai/deepseek-v4-pro` to the wrong
  OpenCode provider. The NVIDIA DeepSeek V4 Pro model is declared under the
  `nvidia-nim` provider in the operator's authoritative OpenCode config.
- Pi's read-only lane is limited to read/search/list tools; its write lane is
  limited to file-editing tools and does not enable shell or network-capable
  tools. Codex runs verification after the worker returns.
- The bridge resolves a package cwd inside the actual Git repository and runs
  the worker in the corresponding subdirectory of the task worktree. Worktree
  state is preserved for parent review by default. An explicit
  `clean_if_empty` policy uses shared preflight, non-force Git removal, and
  safe branch deletion; dirty, scope-violating, or otherwise uncertain
  worktrees are retained/quarantined.
- We reuse Open Dynamic Workflow ideas selectively rather than adding it as a
  runtime dependency.

## Verification required before production activation

- `external-delegation check --worker pi` succeeds.
- Provider-aware selection chooses the expected candidate for representative
  mechanical, coding, reasoning, context, and quota cases.
- Read-only Pi smoke returns the required marker.
- Missing marker, timeout, provider failure, and model mismatch fail closed.
- The fixture remains unchanged after the read-only smoke.
- Codex independently verifies the returned evidence.
