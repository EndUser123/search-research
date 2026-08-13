# Codex capability/difficulty benchmark suite

This is an independent Codex-owned benchmark workstream. It is intentionally
additive: it does not edit Grok's active `model-benchmark` or `model-quota`
trees. The later merge point is the manifest and receipt contract, not a
shared mutable registry or a model-only result table.

## What is included

- `capability` suite: contract following and evidence-bounded context
  retrieval across mechanical, reasoning, and critic lanes.
- `code_pool` suite: localized patches, test authoring, debugging, multi-file
  invariants, compatibility, security edge cases, and regression repair in the
  coding lane.
- Four explicit difficulty tiers: `easy`, `medium`, `hard`, and `expert`.
- Stable case IDs, prompt/checker contracts, resource budgets, and a manifest
  SHA-256 hash.
- Offline receipt scoring with per-suite, per-capability, per-difficulty, and
  per-cell results.
- An immutable parent-owned checker (`capability-difficulty-verifier@1`) and
  fixture corpus for every coding case. Worker worktrees contain only the
  mutable case files; checker logic remains in the parent checkout. Because
  the fixture corpus is benchmark-owned and may be untracked, each coding
  task declares an explicit source-to-destination materialization path; the
  runner copies that path into the disposable worktree before Pi runs and
  records it in the worktree receipt.
- Wilson one-sided 95% lower bounds for the verified pass rate.
- Separate `pass`/`fail` quality outcomes from `blocked`/`not_run`/`unverified`
  outcomes. A quota exhaustion or transport failure cannot be counted as a
  model-quality failure.

## Exact binding required in every run

The evaluator requires all of these fields. A model-only result is not valid
fleet evidence:

`orchestrator`, `invocation_method`, `provider`, `model`, `route`, `verifier`,
`quota_pool`, `provider_account`, and `provider_scope`.

The binding is the evidence scope. A result from Grok HTTP, Codex Pi, an
OpenCode route, or a native spawn route must remain distinct even when the
provider and model names match.

## Receipt shape

The live adapter should write a `capability-difficulty-run.v1` JSON object:

```json
{
  "schema_version": "capability-difficulty-run.v1",
  "run_id": "run-2026-08-09-0001",
  "manifest_id": "codex-capability-difficulty-2026-08-09",
  "manifest_sha256": "...",
  "binding": {
    "orchestrator": "codex",
    "invocation_method": "pi",
    "provider": "nvidia-nim",
    "model": "deepseek-ai/deepseek-v4-flash",
    "route": "pi",
    "verifier": "code-pool-verifier@1",
    "quota_pool": "nvidia-nim",
    "provider_account": "account-alias",
    "provider_scope": "dedicated-account"
  },
  "cases": [
    {
      "case_id": "code_pool.localized_patch.easy.001",
      "attempt_id": "run-2026-08-09-0001-case-001",
      "execution_status": "completed",
      "verification_state": "verification_passed",
      "quota_pool": "nvidia-nim",
      "provider_account": "account-alias",
      "provider_scope": "dedicated-account",
      "raw_attempt_path": ".../attempt-1.json",
      "latency_ms": 1234,
      "token_usage": { "input": 1000, "output": 240 },
      "tool_trace": [],
      "checks": [
        { "name": "empty_case_passes", "passed": true },
        { "name": "existing_case_passes", "passed": true },
        { "name": "scope_is_limited", "passed": true }
      ]
    }
  ]
}
```

Each case repeats the effective binding and receipt paths so aggregation cannot
silently collapse observations across providers, pools, or routes. Token usage
and tool traces are preserved when the worker emits them; missing telemetry is
represented as `null`, not inferred.

`failure_class` should be included when `execution_status` is `failed` or
`blocked`, for example `quota_temporary`, `quota_monthly`, `route_retired`,
`transport`, `timeout`, or `harness`. These outcomes are retained for fleet
health analysis but excluded from the verified quality denominator. Recovery
metadata such as `retry_after`, `reset_at`, and `reprobe_at` is retained when
the provider or harness supplies it; the adapter never invents a recovery time.

## Commands

From `P:\packages\codex-external-delegation`:

```powershell
node benchmarks/capability-difficulty/bin/capability-difficulty.mjs manifest
node benchmarks/capability-difficulty/bin/capability-difficulty.mjs evaluate --run .\run.json --manifest .\manifest.json --out .\result.json
node benchmarks/capability-difficulty/bin/capability-difficulty.mjs aggregate --runs .\runs.json --manifest .\manifest.json --out .\aggregate.json
node benchmarks/capability-difficulty/bin/capability-difficulty.mjs check --case code_pool.localized_patch.easy.001 --payload .\payload.json --worktree .\worker-package --out .\checker.json
node benchmarks/capability-difficulty/bin/capability-difficulty.mjs collect --batch-summary .\batch-summary.json --binding .\binding.json --run-id run-2026-08-09-0001 --out .\capability-run.json
```

The commands are offline and do not call providers, consume quota, or write a
fleet registry. `collect` reads existing batch artifacts, runs the immutable
parent checker for successful worker results, and writes a
`capability-difficulty-run.v1` receipt. It does not execute a provider or
retry a failed task. A live batch still needs explicit Pi invocation and must
preserve the manifest hash, binding, case IDs, and verifier identity.

The generic batch runner also fails closed for benchmark manifests. A
non-dry-run batch whose task inputs contain `benchmark_manifest_id` requires an
external, expiring parent approval receipt bound to the exact `batch_id`,
benchmark manifest ID/hash, and maximum call count. Pass it explicitly with:

```powershell
node bin/external-delegation.mjs batch run --manifest .\batch-smoke-all.json --approval-receipt .\live-approval-smoke-all.json
```

The receipt must use schema
`codex-pi-benchmark-live-approval.v1`, status `approved`, scope
`capability-difficulty`, orchestrator `codex`, worker `pi`, invocation method
`pi`, and fallback policy `halt_no_automatic_fallback`; its `expires_at` must
still be in the future. `batch route` and `batch run --dry-run` never require
the receipt. Missing, mismatched, or expired approval is recorded as
`benchmark_live_approval_required` and no provider worker is started.
The all-binding manifests are required for an exhaustive benchmark claim;
selected-snapshot manifests are optional subsets and must be labeled as such.

## Promotion rule

The default policy requires at least 10 observations and 10 independently
verified successes in every suite/capability/difficulty cell. A complete
single run is useful for harness validation but is not promotion evidence.
This prevents a model from passing an easy-only subset or hiding quota blocks
inside a quality score.

## Merge points with Grok

1. Compare Grok's pool/capability cases with this manifest by stable capability
   and difficulty labels. Grok's `coding` label maps to canonical `tool-loop`;
   it is an adapter alias, not a new evidence lane.
2. Keep the stronger objective checker for each case; do not merge prompt text
   without its checker and version.
3. Normalize both sides into the receipt binding above. Grok's pool runner
   stores the structured form in telemetry `receipt_json`; notes-only records
   are diagnostic and must not be treated as promotion evidence.
4. Aggregate Codex Pi and Grok routes separately before any cross-host summary.
5. Keep provider-pool recovery tests separate from model-capability tests.

The shared route matrix is method-scoped: run all three capabilities for each
enabled method, with HTTP and PI as the common baseline and OpenCode optional.
Do not pool a Grok `trivial`/`standard` result with Codex `easy`/`medium` merely
because the labels look similar; an explicit manifest/checker crosswalk and
matching receipt provenance are required. Quality runs use evaluation budgets
and watchdog metadata without sending provider request caps such as
`max_tokens`; temporary quota/rate-limit outcomes remain blocked or deferred
evidence, not model-quality failures.
