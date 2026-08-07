# Delegation Memory operational contract

Delegation Memory is evidence collection only. It does not participate in
worker selection, retry, fallback, or routing decisions.

## Authority and write path

`bin/external-delegation.mjs run` calls `src/runner.mjs:runPacket`. The runner
is authoritative for the terminal result, attempt outcome, artifact directory,
and worktree/scope lifecycle. `finalizeResult` writes one immutable history
entry after the terminal result is known and before `result.json` is emitted.
The parent/host remains authoritative for independent verification; the runner
records a verification outcome only when one is present in the result.

## Storage and identity

The default storage path is:

```text
<packet.cwd>/.codex/state/external-delegation/history/<task_id>/<entry_id>.json
```

Tests and embedding callers may provide `historyDir`. Each entry is written to
a unique temporary file and atomically renamed to its final `.json` path.
Temporary files are ignored. `entry_id` contains task identity, run or
invocation identity, and a UUID, so duplicate or concurrent task IDs do not
overwrite one another. The schema is `delegation-memory.v1`.

## Record and freshness rules

One entry is attempted for every terminal `runPacket` result, including
pre-worker blocked results, worker failures, timeouts, and successful results.
`started_at`, `ended_at`, and `duration_ms` are measured by the runner in the
current process. Provider/model, task type/class, failure class, contract
status, attempt, timeout, identifiers, artifact identity, and worktree/scope
outcomes come from the current packet/result. Token and cost fields are
omitted unless numeric values were actually reported in the result or its
payload usage object. No history entry is considered current for routing;
freshness is the entry timestamp, not a cached selection snapshot.

## Failure and recovery

History write failure is non-authoritative: the worker result keeps its status
and receives `telemetry.status=failed` with `failure_class=telemetry_error`.
Successful recording receives `telemetry.status=recorded` and the entry path.
The reader ignores incomplete temporary files and reports malformed `.json`
files in `skipped`; it never fabricates or repairs an entry.

## Query and retention

Run `node bin/external-delegation.mjs history [--root <directory>]`. The report
groups real entries by task type and model and returns count, success rate,
timeout rate, median duration, and verification pass rate. Verification rate
is `null` when no verification outcome was recorded. Retention is indefinite
by default; operators may archive or remove history outside the package after
preserving the associated task/artifact identifiers. The package performs no
automatic deletion.
