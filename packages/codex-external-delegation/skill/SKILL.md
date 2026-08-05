---
name: codex-pi
description: Delegate bounded low-ambiguity work from Codex through Pi using subscription-backed or local models, with generated packets, timeouts, artifacts, worktree isolation for writes, and parent verification. OpenCode remains available only through a separate explicit invocation.
---

# External Delegation

Codex remains the parent and owns task classification, scope, risk decisions, integration, and final judgment. Use the bridge for low-ambiguity work such as read-only exploration, extraction, classification, test execution, documentation drafts, or a tightly specified mechanical change.

Do not delegate ambiguous diagnosis, architecture, security decisions, final review, destructive actions, external mutations, or work whose result cannot be independently verified.

## Default workflow

1. Decide whether this is bounded execution or parent-owned reasoning.
2. If bounded, create a packet JSON in the current task's state directory. Do not ask the user to write the packet.
3. Default to `mode: "read_only"` and `worker: "pi"`. If the caller has not
   selected a model, use the provider-aware selector: choose the best eligible
   `(model, provider, path)` candidate from current capability, quota, health,
   context, and latency evidence. Automatic selection reads the local fleet
   registry, Pi model registry, and quota cache; caller-supplied health is not
   authoritative. A `provisional` selection is allowed only when those local
   sources clear the gates but Pi transport history is incomplete; runtime
   identity verification remains mandatory.
4. Include explicit `allowed_paths`, `forbidden_actions`, `output_schema.required`, and exact `verification.commands`.
5. Do not add fallback workers. If Pi fails, halt and return its failure evidence. OpenCode requires a new explicit invocation with a new task ID and packet.
6. For write mode, provide a `worktree_request` or a previously provisioned
   `isolated_cwd`; never authorize writes in the main checkout. The bridge
   resolves a package cwd inside the actual Git repository and runs the worker
   in the corresponding subdirectory of the task worktree.
7. Run `node P:\packages\codex-external-delegation\bin\external-delegation.mjs run --packet <packet-path>`.
8. Inspect the normalized JSON result and raw artifacts under `.codex/state/external-delegation/<task_id>/`.
9. Independently inspect changed files and rerun verification before accepting any result.

## Safety contract

- A worker is not successful unless it returns the required structured result marker.
- Timeouts, provider failures, quota/auth failures, context overflow, missing commands, malformed output, and worker errors are distinct failure classes.
- The bridge makes one worker attempt. Infrastructure failures are recorded as
  failure evidence; automatic retries and fallback workers are disabled.
- Pi read-only runs allow only read/search/list tools. Pi write runs allow only
  file-editing tools (read, grep, find, ls, edit, write); shell and
  network-capable tools remain disabled, so verification commands belong to
  Codex after the worker returns.
- Write packets require both `write_scope` and `isolated_cwd`; otherwise the bridge blocks before spawning a worker.
- A write packet with `worktree_request` may provision a task worktree through
  the shared lifecycle helper; the bridge verifies its Git registration and
  repository identity before spawning Pi.
- Worktree state is preserved for parent review by default. An explicit
  `worktree_cleanup: "clean_if_empty"` policy may remove a worktree only when
  the entire Git worktree is clean, shared preflight has no actionable finding,
  and non-force Git removal succeeds. Dirty or scope-violating worktrees are
  retained and marked quarantined; unmerged branches are retained.
- Worktrees isolate tracked writes, not arbitrary filesystem reads. Runtime
  isolation and post-run scope verification remain mandatory.
- Never expose API keys or auth files in a packet, prompt, artifact, or final response.

## Packet shape

```json
{
  "schema_version": "2",
  "task_id": "unique-task-id",
  "worker": "pi",
  "task_domain": "mechanical",
  "objective": "List all callers of the parser and return file paths with line numbers.",
  "cwd": "P:/repo",
  "mode": "read_only",
  "allowed_paths": ["src/", "tests/"],
  "forbidden_actions": ["edit files", "run network commands"],
  "output_schema": { "required": ["files", "observations"] },
  "verification": { "commands": ["rg -n parser src tests"] }
}
```

The parent must treat the worker response as candidate evidence, not truth.

## Provider-aware selection

The candidate identity is the complete tuple `(model, provider, dispatch path)`.
MiniMax M3 through MiniMax, GLM-5.2 through Z.ai, Nemotron 3 Ultra through
NVIDIA, DeepSeek through OpenCode Go, DeepSeek through NVIDIA, and DeepSeek
through Zen are separate candidates with different quota pools, latency,
limits, and runtime behavior.

Apply gates before ranking:

- task quality floor and role fit;
- context, tool, image, reasoning, and structured-output capability;
- provider availability and quota headroom;
- recent reliability and p90 latency;
- identity verification and containment support.

Among eligible candidates, prefer task fit, then reliability, quota headroom,
latency, and cost. A preflight quota failure may remove a candidate before
launch. Once a worker starts, failures halt without automatic fallback.

The bridge records the selected candidate, quota pool, reasons, alternatives,
and confidence in `packet.model_selection`. If no candidate clears the gates,
routing blocks with `no_eligible_external_candidate`.
