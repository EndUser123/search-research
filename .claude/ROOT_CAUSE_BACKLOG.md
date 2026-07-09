# Root Cause Backlog

Origin: 2026-07-09 session analyzing the FAP-gate conversation failures.
One-sentence root cause: the system enforces verification on the model but
nothing verifies the system, so failures accumulate silently until a
conversation surfaces four of them at once.

Status legend: [DONE] completed and verified by execution · [PARTIAL] · [OPEN]

## Short term — NEED to fix

1. [DONE 2026-07-09] **Keyword fallback was the primary trigger path (73% of firings) and noise.**
   The regex layer (614 hits) captures deliberate intent; the fallback tripped on ordinary
   troubleshooting vocabulary. The fallback was a degraded mode for daemon outages — a silent
   degraded mode, which the constitution's fail-fast rule prohibits. The hook violated rule #1
   for six weeks.
   → Fixed: `analysis_protocol_gate.py` rewritten regex-only (624 → ~200 lines). Verified:
   fires on declarative RCA prompts, silent on troubleshooting chatter. Old version at
   `hooks/_archive/analysis_protocol_gate.py.bak-20260709`.

2. [DONE 2026-07-09] **Semantic daemon path was dead code.** Zero successful firings ever
   (`fap_layer_stats.json` had no `layer2_semantic_hit` key). Deleted entirely per Replacement
   Default, along with the numpy/DaemonClient dependencies.

3. [DONE 2026-07-09] **No post-Write verification was enforced structurally.** Silent write
   truncation recurred in this very session (twice: hooks_audit.py truncated at ~11.6KB,
   one truncation parsed cleanly because the stub ended on a bare name expression).
   → Fixed: `hooks/PostToolUse_py_syntax_gate.py` — checks exists/non-empty/ast.parse on any
   .py after Edit/Write/MultiEdit, advisory, registered in settings.json. Tested against
   good/broken/empty/non-py inputs.
   Residual: ast.parse alone can miss truncation at a statement boundary; a runtime smoke or
   line-count delta check would close that.

4. [DONE 2026-07-09] **Stale metadata treated as ground truth.** HOOKS_CATALOG.md line 209
   corrected (unified_claim_verifier exists and is live; Stop_investigation_validator is simply
   unregistered). Five .bak/.DISABLED files moved to `hooks/_archive/`;
   skill_metadata_advisory.py.disabled deleted outright (see #11).

## Long term — NEED to fix

5. [PARTIAL 2026-07-09] **Hook ecosystem has no self-verification.** ~1135 hook files enforce
   behavior on the model; nothing verified the hooks.
   → `P:/.claude/scripts/hooks_audit.py` now exists: checks registration (incl. router-pattern
   convention for plugin hooks), syntax, dangling path literals, catalog drift, stats anomalies
   (incl. corrupt stats JSON = interrupted non-atomic writer), backup hygiene; `--imports` opt-in.
   First run found: 2 router-convention violations (snapshot_PreCompact.py,
   go_continuation_gate.py registered directly), 15 syntax failures (re-verify under prod
   interpreter — sandbox is 3.10), 199 dangling path references, 79 catalog-drift entries.
   Remaining: fix the findings; schedule the audit.

6. [OPEN] **Catalog must be generated, not written.** HOOKS_CATALOG.md should be derived from
   filesystem + registration manifests by the audit script. 79 drift entries prove the point.

7. [OPEN] **Environment parity for verification claims.** Sandbox 3.10 vs production 3.13+ makes
   in-session import/syntax checks structurally inconclusive. Pin a matching interpreter or run
   verification on the host. Until then every "verified" claim about hook code has an asterisk.

## Long term — SHOULD fix

8. [OPEN] **Prompt-injection gates are the wrong enforcement mechanism for verification
   behavior.** Rhetoric-injection produces rhetoric (compliance theater). Gates that check
   artifacts (file parses, test passes, cited file:line exists) produce verification. Migrate
   behavioral injections toward artifact checks; the evidence-demanding rewrite is a patch on a
   category error.

9. [OPEN] **~1135 hook files is enterprise-pattern territory for a solo dev.** Each is
   maintenance surface, latency, and a potential silent failure. Use audit telemetry to find
   hooks that never fire, fire constantly, or duplicate each other — cull aggressively.

10. [PARTIAL 2026-07-09] **Backup/disabled file hygiene + git.** Stale copies archived;
    HYGIENE check now in audit. Git: `P:\.claude\setup_git.ps1` written — must run natively
    (the Cowork sandbox mount corrupts .git writes; it left a NUL-byte .git in P:/.claude that
    the script removes first). One repo at P:\ root, logs and packages/.github_repos excluded.
    Remaining: actually run the script, then per-case decisions on embedded-repo warnings.

11. [OPEN] **Skill enforcement keyed on frontmatter presence contradicts policy.** Policy:
    all manually invoked skills are mandatory. Reality: `Stop.py:1761` (and breadcrumb/step-header
    /enforcement-tier machinery) only enforce a skill if its SKILL.md has `workflow_steps` —
    104 of 161 plugin skills lack it, so ~65% of skills are silently optional. Fix at the right
    layer: enforce on the invocation event itself (skill invoked → enforcement applies), not on
    frontmatter presence. The deleted skill_metadata_advisory hook was a noisy per-prompt patch
    for this same gap; don't recreate it — change the enforcement key.

12. [OPEN] **No coordination between concurrent agents writing the same tree.**
    Observed 2026-07-09: this session overwrote another LLM's rewrite of
    delegation-prompt-pattern.md (its 10:22 archive-before-edit implies a
    successor version existed; clobbered at 12:55 without read-before-write).
    Read-discipline alone can't close it — check-then-write races survive
    politeness. Fixes, in order: (a) git at P:\ makes clobbers recoverable
    (see #10); (b) convention: one writer per directory at a time, or agents
    claim files in a shared lockfile/manifest before editing.
    Immediate recovery: other model re-emits its version before its session
    closes; then merge, don't pick a winner.
