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
   Convergent evidence 2026-07-09: an independent external review (agy/Gemini) reached the
   same conclusion by a different route ("delete the meta-scripts; reduce surface"). Live cost
   observed in that same transcript: four gate collisions (skill-first gate, 260-min-stale
   evidence-window block, directory policy, /dev/stdin failure) before the actual task began,
   plus an apparent false-positive Stop-hook warning at the end. Keep the telemetry-driven
   cull form — wholesale deletion is the same blunt instrument in reverse.

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

13. [OPEN] **Edit-as-exploration incentive: diffs are legible, reading is invisible.**
    Root-cause candidate from the 2026-07-09 churn review (source: agy transcript — external
    LLM, treat as hypothesis): the harness shows the user diffs but not reads, so the model's
    exploration budget defaults to edits — editing substitutes for understanding, producing
    the observed churn (same file edited 6x, each edit followed by "I was wrong about X").
    Fix direction: make the discovery artifact (system map, files-read ledger, invariants
    list) a first-class deliverable like diffs are. Mechanism exists in /go and /refactor
    discovery-first contracts; this is a generalization decision, not an invention. The
    delegation template already does this for delegates (written-residue element); the
    default session prompt never got the same treatment.
    GATED ON MEASUREMENT, prospective not retrospective: the transcript's proposed test
    (re-run 3 past sessions through the discipline, self-graded) can't work — retrospective
    counterfactual judged by the model that produced the churn is fake-map theater inside the
    measurement. Instead: over the next N non-trivial tasks, alternate discovery-map-first vs
    default; count from git history — edits per file per session, reverted/re-edited files,
    time-to-stable. Requires #10 (git) — churn measurement needs history.
    Falsification condition (from the transcript, kept): if maps get written but the edits
    they precede are unchanged, the artifact requirement isn't the fix — the model lacks a
    working mental model of the system, which no gate or map requirement can supply.

14. [OPEN] **Gates key on turn-local proxies for session-level state.** Generalizes #11.
    Observed 2026-07-09 (search-research session transcript): (a) ACTION-AUTHORITY gate
    blocked an already-authorized build because the most recent message was a slash command
    — grammar of the last turn used as proxy for standing authorization, manufacturing the
    exact re-ask stall the user was angry about; (b) evidence-window gate blocked writing a
    NEW handoff file (asserts nothing about existing state) on tool=Write + 274-min-since-
    Bash — time-since-tool as proxy for claim content; (c) /wiki DEFAULT-TO-SESSION heuristic
    overrode an explicit /wiki invocation — message shape as proxy for invocation intent;
    (d) two gates issued contradictory instructions in one turn (authority gate: don't write;
    intent-misalignment Stop: you didn't write) — direct #9 evidence.
    Fix: rekey, don't multiply. (1) Session authorization ledger — grants persist until
    revoked; authority gate consults ledger, not last-message grammar. (2) Evidence-window
    gate fires on claim content (Fixed/Verified/Root-Cause assertions about existing state),
    not tool+time; new-artifact writes exempt. (3) Explicit /skill invocation overrides
    scope heuristics unconditionally. Gives #9's cull its discriminating principle: gates
    keyed to artifacts/session state stay; gates keyed to turn-shape proxies get rekeyed
    or deleted.
    Note: the transcript's gates predate this session's hook changes (FAP gate quieted,
    py-syntax gate added, unloaded advisory deleted — none fire in that transcript). Open
    dependency: confirm host Stop.py is not truncated (see rekey verification) before
    attributing any Stop-gate behavior change.

15. [OPEN] **#9 is unexecutable as specified: no gate telemetry exists.** The FAP fallback
    was caught only because that one hook kept a stats file; the other ~1,100 hooks have no
    firing/block/override counters. Predictable: the telemetry-driven cull stalls or degrades
    into judgment-based deletion. Fix: one shared counter helper in the dispatchers (fire,
    block, warn, override per hook name, atomic writes) — instrumentation before cull.
    Blocks #9; feeds #14's keep/rekey/delete decisions with data.

16. [OPEN] **Cowork sandbox mount is structurally unreliable; every session inherits it.**
    Observed 2026-07-09: three Write truncations at ~11.6KB, one cp truncation, blocked
    deletes, git config written as NUL bytes, and read views that disagreed across calls
    (grep saw line 1984 while ast.parse saw a 100-line file). Nothing records this;
    each session rediscovers it mid-failure. Predictable: silent corruption of files a
    delegate just verified (rekey files are the live example). Mitigation until platform
    fix: verified-write protocol as documented convention (checksum + structure check after
    every mount write), host-native execution for critical files, and a trap-note in the
    peer-delegation CONTEXT block (already in the template).

17. [OPEN] **Rekey friction wave + manually-maintained KNOWLEDGE_SKILLS set.** ~89 skills
    became mandatory at once (2026-07-09 rekey); some legitimately answer in prose and are
    not in the 17-entry frozenset. Predictable within days: prose blocks that feel like #14
    false positives, each needing a hand-edit to a central hand-maintained list — the #4/#6
    hand-maintained-metadata-drift pattern rebuilt on purpose (the rekey report itself flags
    this in Deferrals). Fix: watch the first week's blocks (needs #15 counters); move
    classification into SKILL.md frontmatter (`knowledge: true`) so it lives with the skill;
    keep the frozenset only as a migration shim.

18. [OPEN] **Tracking artifacts sprawl with no reconciliation or retirement.** This backlog
    coexists with the task DB (#1387, #1329, ...), next-steps.txt, plan.md, and wiki pages —
    multiple hand-maintained views of one truth, the catalog-drift pattern at the planning
    layer. Session state files also never get GC'd (hooks/state/, session_data/,
    consultation/followup JSONs, dreaming-daemon-state.json.1 rotation debris). Predictable:
    trackers disagree about done-ness; a future session reads stale state. Fix: declare one
    canonical tracker and make others generated-or-deleted (Replacement Default); add a
    state-file TTL/GC check to hooks_audit.py.
