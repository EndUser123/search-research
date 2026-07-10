# Root Cause Backlog

Origin: 2026-07-09 session analyzing the FAP-gate conversation failures.
One-sentence root cause: the system enforces verification on the model but
nothing verifies the system, so failures accumulate silently until a
conversation surfaces four of them at once.

## Problem classes (assign every new item; fold fits into the class fix)

- **C1 — Missing ground-truth representation.** Actors (models, gates, humans)
  consult memory/testimony where a generated, queryable representation should
  exist. Sub-forms: code state (→ manifest #1390), session state (→ #14 ledger),
  task state (→ #20 spec re-anchoring), uncertainty itself (→ #21 risk register).
- **C2 — Proxy substitution.** When the true criterion is illegible, actors
  optimize the nearest measurable stand-in (turn grammar for authorization,
  diff size for value, STATUS labels for evidence). Do NOT fix directly —
  it dissolves where C1 representations land; policing proxies breeds gates.
- **C3 — Accumulation without lifecycle.** Additions have owners; deletions
  don't (hooks, memories, tasks, trackers, workarounds). Fix mechanism: the
  manifest's deletion license + GC checks; sequenced AFTER C1.

Filing rule: a new item that fits C1/C2/C3 is appended as evidence to the class
fix, not opened as its own project. A self-review that finds ZERO unowned
residuals is itself a C2 signal (self-certification proxy) — every self-review
must name at least one residual or attach an explicit search log (adversarial
review 2026-07-10 refuted a "none found" claim twice: a mislabeled measurement
lane file and a gate-blocked mitigation that silently became a deferred task).
Additions-vs-deletions count is part of any self-review: a session that
diagnoses C3 and ships ~20 additions / 0 deletions is exhibiting it. Tracker contract (#18): this file is the
root-cause register; the task DB is the execution tracker; #1390 is the bridge.
Falsification for the class program: if one week after manifest + ledger are
live sessions still file C1 instances at 2026-07-09's rate, the residual is
behavioral — stop building infrastructure, revisit prompts/model routing.

## Roadmap (class-fix waves)

- **Phase 0 — enablers:** run `setup_git.ps1` natively (#10); pin 3.13
  interpreter for verification (#7); verified-write convention note (#16).
- **Phase 1 — C1 representations (front of queue):** #1390 manifest (absorbs
  #6 + remaining #5 audit work); #15 DONE (hook_stats.py ratified, #1391 option
  (a)); #14 authorization ledger
  (promoted: three blocks on 2026-07-09 alone, one on a system-mandated
  memory write; stalls delegates cold).
- **Phase 2 — C1 consumers:** #17 `knowledge:` frontmatter (after one week of
  #15 counters); #20 spec-anchor + #21 risk-register lines in the delegation
  template and report contracts; #8 folded in as migration direction
  (rhetoric gates → artifact checks).
- **Phase 3 — C3 lifecycle (data-gated):** #9 cull via manifest deletion
  license; #18 tracker consolidation + state GC; workaround sweep (every
  "do X via Y to avoid gate Z" memory is a pending verdict on gate Z);
  #13 measurement experiment; #12 parked pending a second clobber post-git.

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
   Remaining (narrowed 2026-07-09): fix the 2 router violations (task #1393) + triage
   dangling paths; catalog generation and orphan/consumer checks move to #1390 (manifest).
   Schedule the audit via Windows Task Scheduler once #1390 defines its output.

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

11. [DONE 2026-07-09] **Skill enforcement keyed on frontmatter presence contradicts policy.**
    → Fixed by delegate session: rekeyed to invocation (Skill in tools_used) with
    KNOWLEDGE_SKILLS exemption; commit 79bdb0e, 20/20 tests, isolated 2-file commit.
    Residual tracked in #17 (hand-maintained frozenset) and the doc rewrite that was
    blocked by the authority gate (see #14 evidence). Original item: Policy:
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
    Fix: rekey, don't multiply. (1) Session INSTRUCTION ledger — both GRANTS and
    PROHIBITIONS persist until revoked; recorded the moment the user issues them;
    consulted at action time by the model and by the authority gate (not last-message
    grammar); durable instructions also persisted to memory. Scope widened 2026-07-09:
    a user prohibition ("no pi for measurements") was violated for path-convenience —
    prose instructions decay in context salience; ledger rows don't. (2) Evidence-window
    gate fires on claim content (Fixed/Verified/Root-Cause assertions about existing state),
    not tool+time; new-artifact writes exempt. (3) Explicit /skill invocation overrides
    scope heuristics unconditionally. Gives #9's cull its discriminating principle: gates
    keyed to artifacts/session state stay; gates keyed to turn-shape proxies get rekeyed
    or deleted.
    Note: the transcript's gates predate this session's hook changes (FAP gate quieted,
    py-syntax gate added, unloaded advisory deleted — none fire in that transcript). Open
    dependency: confirm host Stop.py is not truncated (see rekey verification) before
    attributing any Stop-gate behavior change.
    New evidence 2026-07-09 (skill-enforcement rekey session): ACTION-AUTHORITY gate
    blocked a doc rewrite that WAS explicitly authorized — the authorization arrived via
    an AskUserQuestion answer ("Rewrite the doc to reflect the new policy"), which the
    gate cannot see; it keys only on the last typed user message ("did you do all of
    it?"). Two identical blocks in a row (retry-blind: no way to consume standing
    authorization), stalling the backlog's own remediation work. Confirms fix (1):
    the ledger must record AskUserQuestion answers as grants, not just typed messages.

15. [DONE 2026-07-10] **#9 telemetry is wired via hook_stats.py (#1391 option (a)).**
    LANDED 2026-07-10: `__lib/hook_stats.py` JSONL (`P:/.claude/state/hook_stats.jsonl`,
    live, ~13k events) IS the ratified dispatcher telemetry spec.
    `hook_runner.py:487-490` records `hook_runner:<name>` block/fire outcome on every
    hook exit. The parallel `hooks/__lib/enforcement_telemetry.py` (zero runtime
    producers — only consumer was its own test) was DELETED along with its test class;
    `test_enforcement_tiers.py` keeps its unrelated live-module classes. Stop-gate
    residuals also closed: ledger fallback turn-scoped (`_load_db_events(active_turn_id)`,
    was terminal-wide), SKILL.md lookup extended to plugin roots via the shared
    `_resolve_skill_md_path`. OPEN: warn/override outcome capture remains under task
    #1396 (record() emits block/fire only, not advisory-warn or user-override). Unblocks #9.

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
    state-file TTL/GC check to hooks_audit.py (task #1394 in-flight). Tracker contract now
    declared in this file's header.

19. [DONE 2026-07-09] **No environment map for delegates → absence claims from
    single-root searches.** Observed: a delegate given "Repo: P:/.claude" searched only
    that root, declared two plugin hook files nonexistent (they live under
    P:/packages/.claude-marketplace/plugins), and nearly rewrote a correct spec. The
    prompt's "search first" exhortation didn't help — the delegate lacked the topology
    FACT, not diligence. Same class as #16's trap-note: environment knowledge each
    session rediscovers mid-failure.
    → Fixed: "Search Topology" section added to P:/AGENTS.md (auto-read: P:/CLAUDE.md
    is `@AGENTS.md`; agy reads it via --dir) — root table, absence rule with canonical
    rg command spanning both live roots, audit-over-hand-search pointer. Delegation
    prompts should say "read P:/AGENTS.md first" and must list ALL roots a task spans.
    Residual: P:/AGENTS.md is hand-maintained (#6 pattern); acceptable at ~30 lines.

20. [OPEN] **Self-reviews lose the spec anchor; scope cuts masquerade as discipline.**
    Observed 2026-07-09 (telemetry-wiring session): delegate's own critical review proposed
    cutting block/warn/override outcome tracking to a "fire-only MVP" — deleting the
    module's entire reason to exist (block-rate measurement) — while the outcome signal
    was already computed one line away (hook_runner.py:482 classifies exit_code==2).
    Mechanism: by review time the spec (outcome enum, explicitly in the prompt) was out
    of view; the code became the de facto requirement; critique then optimized the one
    legible, enforced virtue (minimal diff) and framed value-deletion as rigor. The
    minimalism rule's own guard clause ("never simplify away the explicitly requested
    thing") was dropped — slogan-level rule internalization. Not capability: one user
    push-back + one grep produced the correct fix immediately.
    Fix (behavioral + template, NOT a new gate): (a) self-reviews of in-flight work
    re-quote the original acceptance criteria before critiquing; (b) any scope cut is a
    SPEC DEVIATION — stated as "spec requires X, propose dropping X because Y", never
    folded silently into an MVP framing. Wire into the delegation prompt template and
    review skill contracts. Partially exists already — /go has omission_audit.py (#1343)
    and capability-preservation checks (#1200); the gap is ad-hoc sessions and delegates
    outside /go. Generalize those, don't reinvent.
    This would be wrong if the cut had been a considered feasibility judgment with the
    spec in view — the transcript's own retrospective ("I had the valuable datum,
    discarded it") says otherwise.

22. [OPEN] **Reflexivity exemption: the producer certifies its own artifact.** Root cause
    behind adversarial-review findings F1/F3/F4/F5 (2026-07-10): Claude's own outputs —
    extraction scripts, measurement scores, self-attributed root causes, "no residuals
    found" — bypass the evidence standards applied to everything else. Verified instances:
    a mislabeled lane file certified clean; author-as-judge measurement with post-hoc
    subset; two flattering root-cause attributions ("salience" for a convenience choice,
    "couldn't find" for didn't-look).
    Fix (structural principle, not a gate): PRODUCER ≠ VERIFIER at every level.
    (a) Measurements: scorer did not author the prompts (now #1398 acceptance criterion;
    generalize into #1085 gate-discrimination harness). (b) Self-reviews: an external/
    subagent adversarial pass is part of the review contract, not user-triggered — the
    2026-07-10 review that found F1-F8 becomes the standing final step; cost ≈ one
    subagent run, measured discrimination of the external-ask form is 9-10/10.
    (c) Completion claims: SPAWN_COMPLETION_VERIFIER already in flight (#1352-#1354) —
    same principle, cite don't duplicate.
    Companion sub-item — **blocked actions vanish** (finding F2): a gate denial is a
    machine-visible event with no consumer, so a blocked mitigation silently became a
    deferred task with no residual filed. Fix by REUSE: stop_blocks.jsonl + PreToolUse
    denial logs already exist; add a Stop/SessionEnd consumer listing "denied writes
    with no subsequent successful retry" in the session residue, and extend
    cc-lazy-closure-debt (whose exact mission is deferral tracking) to ingest
    gate-denial events as a new input class.
    This would be wrong if producer≠verifier adds latency/cost exceeding its catch rate
    — measurable once #15 telemetry counts external-pass findings per session.

21. [OPEN] **Unrepresented uncertainty: residuals get narrated, not registered.** C1 applied
    to uncertainty itself. Observed 2026-07-09 (search-research /find session): a fix left an
    unexplained residual (NotebookLM query still failing) and the report papered it with an
    unverified spec claim — "that's expected" — instead of flagging it as an open risk. The
    fix itself (#4, auth detection) was designed from an assumed model (errors on stderr)
    without capturing the failing artifact; the real error was on stdout, so the detection
    could never fire, and the smoke test only confirmed the code matched the author's model
    (tautological). One reproduction command would have caught it pre-edit. Root cause:
    fixes and reports have no required home for open assumptions, so report-completion
    pressure converts them into confident hedges — the hedge IS the tell.
    Counter-example, same day (CCR router session, the pattern to institutionalize): an
    explicit Risks section with severity, a weakest-assumption challenge, the smallest
    falsifier per risk ("grep one failing reqId's body for 'thinking'"), then a closure
    pass — close every cheaply-closable risk NOW (read-only checks, scoped commits),
    leaving only genuinely-blocked ones, each with its discriminating test named.
    Fix (contract + template, NOT a gate): add two required elements to the delegation
    template and report contracts (report-contracts.md, #1287): (a) REPRODUCE-FIRST —
    a fix for a reported symptom must cite the captured failing artifact (rc/stdout/stderr)
    the fix is designed against; no repro → say so and stop, don't hedge; corollary
    (added 2026-07-10, external-LLM convergence + corpus Cases 4/14): claims about
    RENDERED/VISUAL output require the rendered artifact (screenshot/real terminal
    capture via browser harness or preview), never the code that produces it; (b) RISK REGISTER +
    CLOSURE PASS — every report lists open assumptions with severity + smallest falsifier,
    then attempts closure of the cheap ones before handing off. Existing mechanisms to
    reuse, not duplicate: TEST STRATEGY CONTRACT's regression-first rule (already injected,
    didn't bind — a contract *field* is checkable where prose exhortation is not),
    /red-team's claim-refute sub-phase (#1248), preflight inversion prompts.
    Watch condition: "expected", "transient", "known limitation" in a report without a
    citation is the C2 proxy-signature of this item — cheap to grep for once #15 lands.
