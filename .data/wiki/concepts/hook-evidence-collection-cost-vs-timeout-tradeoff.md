---
title: "Hook evidence-collection cost vs timeout tradeoff"
created: 2026-07-26
source: session-2026-07-26 (/why RCA on post_tool_use hook timeout)
sources:
  - internal: C:/Users/brsth/.grok/hooks/scripts/mutation_receipt.py (lines 80-100, 124-249)
  - internal: C:/Users/brsth/.grok/hooks/quality-gate.json (PostToolUse block)
  - internal: P:/.data/wiki/concepts/agent-failure-modes-2026.md
tags: [hook-timeout, verification-system, fail-open, scaling, git-fan-out, evidence-collection, silent-coverage-gap]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  Verification hooks that collect evidence via synchronous git-subprocess fan-out
  do not scale with workspace dirty-tree size. On a 994-file workspace, the
  mutation_post.py PostToolUse hook consumed 5.8s of its 10s budget on the dirty-set
  scan alone (git diff --name-only HEAD), leaving only 4.2s for per-file blob-OID
  computation (3-5 git subprocesses × 200-800ms each on Windows). Result: timeout,
  receipt silently dropped (fail-open → exit 0), verification-receipts system
  loses coverage for that tool call with no visible signal. The systemic pattern
  applies to ANY verification hook whose evidence-collection cost scales with
  workspace size while operating under a per-tool-call timeout ceiling.
relations:
  - target: wiki/concepts/agent-failure-modes-2026.md
    type: related
  - target: wiki/concepts/inference-chains-bare-numbers-destructive-write.md
    type: related
  - target: wiki/concepts/friction-detection-operator-pushback-as-trigger.md
    type: related
---

# Hook evidence-collection cost vs timeout tradeoff

## Decision context

**Why this finding was captured:** a `/why` RCA on a `post_tool_use` hook timeout (10687ms actual vs 10000ms ceiling) found a structural cost/timeout tradeoff that applies broadly. The operator asked the RCA to feed back to the wiki per `/why` Step 15 so future hook designs and `/check` runs find this pattern instead of re-deriving it.

**What alternatives were explored during the RCA:**
- Transient system load — refuted by direct reproduction (5804ms measured on a quiet command immediately after)
- Pathological command (e.g. `git commit -a`) — refuted; cost is independent of which command ran
- Required-filter slow path — refuted by math; one required-filter file adds ~110ms, not seconds

The pattern survives all three competing explanations. Captured to prevent re-derivation.

## The pattern

A verification hook (PostToolUse, PreToolUse, or similar) needs to collect evidence about what a tool call did. The simplest implementation runs synchronous git subprocesses to compute dirty-set differences, blob OIDs, or hashes. On a small workspace this is fast enough; on a large or multi-root workspace the cost crosses the hook's timeout ceiling, at which point:

1. The hook runner kills the hook mid-execution
2. The hook fails OPEN (the standard pattern for non-blocking hooks: `sys.exit(0)` on any error)
3. No receipt / evidence is recorded for that tool call
4. The downstream consumer (`/close`, `/check`, audit log) silently has a coverage gap
5. Nothing surfaces the gap — work proceeds normally

**The semantic harm is invisible:** the operator sees no error, the agent sees no error, but the verification system has lost evidence. The fail-open design (correct for non-blocking hooks) masks the timeout failure mode entirely.

## Worked example (the incident that surfaced the pattern)

**Workspace:** multi-root `P:\` with 994 dirty files in the working tree.

**Hook cost breakdown (measured this session):**
- `git diff --name-only HEAD`: **5804ms** for 994 files
- `git rev-parse HEAD`: 289ms
- `git hash-object` per file: 776ms (single file; Windows cold-start)
- Per-file blob-OID loop (in `_git_blob_oid`): 3–5 git subprocesses per file (check-attr, config, rev-parse --show-object-format, hash-object)

**Math:** the dirty-set scan alone consumes 58% of a 10s budget. Any newly-dirty file that triggers the per-file OID loop pushes the total past the ceiling. Two newly-dirty files × ~1s each = 7.8s baseline; three = 8.8s; the actual incident showed 10.687s on a normal command.

**Why the per-file loop runs even on indeterminate attribution:** `mutation_receipt.py:405-408` falls into an `else` branch when `capture_reliable=False` (concurrent commit shifted HEAD, or pre-capture failed). The else branch runs the per-file loop over ALL dirty files, not just newly-dirty ones — multiplying cost when attribution is already known to be unreliable.

## Detection signals (what to look for in other hooks)

A verification hook is vulnerable to this pattern if ALL of:
1. **Synchronous subprocess fan-out** — runs N subprocesses per tool call, where N scales with workspace state (file count, dirty count, branch count)
2. **Per-tool-call invocation** — fires on every matching tool event, not on a batched schedule
3. **Tight timeout ceiling** — 5–30s hook timeout typical
4. **Fail-open on error** — `sys.exit(0)` or equivalent; errors do not surface to the operator
5. **Downstream consumer** — some other system (`/close`, `/check`, audit) depends on the evidence being written

If all five apply, the hook WILL silently lose coverage on large workspaces. The question is when, not whether.

## Architectural fixes (in priority order)

1. **Move expensive introspection to the consumer, not the hook.** The hook records minimum evidence (tool_use_id, timestamp, file path, before/after hash if cheap). The consumer (`/close`, `/check`) computes blob OIDs, attribution, and reconciliation when it runs — there's no 10s ceiling there.
2. **Skip the hook entirely for non-mutating commands.** Inverse detection (only proceed if command contains `>`, `>>`, `Out-File`, `Set-Content`, `git commit|checkout|reset|stash|clean|apply`, `Move-Item`, `Copy-Item`, `Remove-Item`, `python.*write`) eliminates ~80% of invocations on a typical coding workspace.
3. **Bail early when attribution is already unreliable.** If `capture_reliable=False`, record `attribution_reliable: false`, write no per-file entries, exit. Don't multiply cost when the result is already known to be untrustworthy.
4. **Cache constant-per-repo values.** `git rev-parse --show-object-format` is constant for repo lifetime; calling it once per file is waste.
5. **Bound the per-file loop.** Cap at N=10 files; beyond that record `truncated: true`. Receipts become incomplete-but-honest rather than dropped-silently.
6. **Surface persistent timeouts via `/check` or a hook-health monitor.** Fail-open hides the gap; a periodic checker that looks for "receipts written / receipts expected" ratio restores visibility.

## Falsifier

This concept is wrong if, within 12 months:

- **The dirty-tree is normally small on this workspace (the incident was an anomaly).** Refuted by direct measurement: 994 files / 5804ms is the steady-state on this workspace as of 2026-07-26. Will remain refuted unless workspace shrinks materially.
- **Receipts are not actually consumed (the coverage gap doesn't matter).** Refuted by `mutation_receipt.py:9-22` docstring: "/close scanner consumes them to prove file ownership for auto-commit without parsing command semantics." If `/close` stops using receipts, this concept downgrades to "theoretical" — revisit.
- **The timeout is enforced by the hook itself rather than the runner.** Refuted: `mutation_post.py:88` does `sys.exit(0)` on any exception (fail-open). The 10s timeout is enforced by the Grok Build hook runner, not the hook. If the hook budget moves to e.g. 60s, the pattern still applies but the threshold moves.
- **A faster git introspection path exists that makes the per-file loop cheap.** Investigated during the RCA: `git status --porcelain` is NOT faster (includes untracked files); `git ls-files -m` is comparable to `git diff --name-only HEAD`. The bottleneck is Windows subprocess spawn + multi-root workspace, not the git subcommand.

If none of these fire, the pattern is durable and the architectural fixes above are the right response.

## Recurrence + fix applied (2026-07-27, session 019fa23d)

**Recurrence:** the same pattern hit `verification_receipt_writer.py` — `_resolve_path_identities(modified)` calls at lines 805, 809, 839, 841 spawned `git submodule status` (4-8s/path on Windows) inside a PostToolUse hook with a 5s timeout. Measured: 21,187ms for 6 paths (4× over budget). The receipt was silently dropped (fail-open), creating a coverage gap that would block Stop-hook obligation clearing.

**This was a documented recurrence.** The wiki concept existed (written 2026-07-26). The agent ran a full `/why` + `/www` cycle without querying it (Step 0.5 of the `/why` skill was skipped). The operator caught it ("I thought we had this problem before").

**Fix applied:** replaced all 4 `_resolve_path_identities(...)` calls with `[]`. The fields (`observed_state_identities`, `claimed_scope_identities`) are **write-only** — no consumer reads them. The obligation check (`_identity_matches`, line 738) returns True when obligation identity is empty. The receipt coverage check (`_check_receipt_coverage`, line 528) checks top-level `repository_id`/`worktree_id`, not per-path identities.

**Result:** `process_verification` 11,182ms → 40ms (275× speedup). Suite 21/21 pass unchanged.

**Track A fix (wiki-utilization):** `/why` Step 0.5 now has a VISIBLE-OUTPUT CONTRACT — the output must cite the actual grep command + hit count, not fill the row from memory. Plus a common-failure-shape keyword table (`hook timeout`, `fail-open`, `evidence-collection cost`). Commit `1c3ee80` in ~/.grok.

**Lessons:**
1. The pattern concept was correct and durable — it recurred exactly as predicted
2. Write-only fields are a specific subclass: expensive computation producing data no consumer reads. The detection signal is "grep for readers" before profiling for the fix
3. Behavioral steps (Step 0.5 query) need visible-output contracts, not just "mandatory" labels — silent steps have zero friction to skip

## Related

- [[agent-failure-modes-2026]] — broader failure taxonomy this concept extends
- [[inference-chains-bare-numbers-destructive-write]] — same family of "fail-silent verification gap" failures
- [[friction-detection-operator-pushback-as-trigger]] — the operator-side signal that would surface persistent timeout patterns if `/check` doesn't

## Receipts (mechanism claims)

- **"`git diff --name-only HEAD` measured 5804ms / 994 files on this workspace":** receipt — `run_terminal_command` output earlier in session 019f9f4f (the discriminating test in the /why RCA)
- **"`mutation_post.py` runs the per-file loop over ALL dirty files when `capture_reliable=False`":** receipt — code read of `mutation_receipt.py:405-408` this session
- **"`_git_blob_oid()` runs 3-5 git subprocesses per file":** receipt — code read of `mutation_receipt.py:124-249` this session; specifically check-attr (line 168), config (line 175), rev-parse --show-object-format (line 185), hash-object (line 230), and optionally update-index + ls-files for the required-filter slow path (lines 200-225)
- **"Hook fails OPEN with `sys.exit(0)`":** receipt — `mutation_post.py:88` (and lines 24, 51, 59, 89 all `sys.exit(0)` on early-return conditions)
- **"Receipts are consumed by /close for auto-commit ownership":** receipt — `mutation_receipt.py:9-22` docstring
- **"The timeout is enforced by the Grok Build hook runner, not the hook":** [INFERENCE] from the dashboard output shape ("timed out after 10000ms" is runner language, not Python) — would require runner source inspection to confirm; high confidence

## Sources

- `C:/Users/brsth/.grok/hooks/scripts/mutation_receipt.py` (lines 80-100, 124-249, 405-408)
- `C:/Users/brsth/.grok/hooks/scripts/mutation_post.py` (full file, 99 lines)
- `C:/Users/brsth/.grok/hooks/quality-gate.json` (PostToolUse block, lines 23-44)
- Session 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9 (2026-07-26) — /why RCA on the operator-reported dashboard timeout
## What this means for our workspace

**RESOLVED (2026-07-31):** the dirty-tree size was NOT a fixed constraint. 71% of the
"steady-state" 1388 dirty files were regenerable churn — 983 skill stubs in
`.data/wiki/sources/skills/` rewritten by `index_skills.py` on every run, plus 332
ghost files (tracked-but-deleted). The actual root cause was upstream of the hook
architecture: regenerable files were tracked in git, permanently inflating the dirty tree.

**Fix applied (commit `adef081`, session 019fb937):**
- `git rm --cached`: 983 stubs + 4 ghost files untracked
- `.gitignore`: re-ignore `.data/wiki/sources/skills/`
- Result: dirty tree 1388 → 399 files (71% reduction), `git diff --name-only HEAD`
  1921ms → 929ms (52% reduction)

**What this means for the architectural fixes above:** fixes 1-6 (cache, parallelize,
bound the loop, skip non-mutating commands) are no longer urgent. At 399 dirty files,
the hooks have comfortable budget. The architectural fixes remain valid for future-proofing
(if the dirty tree grows again from other sources), but the immediate problem is solved by
upstream cleanup, not hook redesign.

**The original RCA's framing error:** the concept treated "994 files / 5804ms is the
steady-state on this workspace" as a fixed constraint (Falsifier section). It was not
fixed — it was an artifact of tracking regenerable files. The falsifier was wrong because
it didn't investigate WHY the dirty tree was large, only that it was. The lesson: when a
cost scales with workspace state, check whether that state is necessary or accidental
before optimizing around it.

**Also:** the prior handoff `quality-gate-pretooluse-timeout-20260728` proposed bumping
the timeout 10→30s and explicitly said "do NOT change post_tool_use timeouts — those are
fine at 10s." The dashboard disproved this — post_tool_use ALSO timed out. The handoff
was a bad proposal that survived 4 sessions unapplied. See
[[list-before-claim-for-destructive-proposal-actions]] for the structural fix.
