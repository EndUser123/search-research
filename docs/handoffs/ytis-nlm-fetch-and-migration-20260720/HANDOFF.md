---
thread_id: 019f7653-7598-79e0-a0c3-1161f9c0b793
parent_handoff_path: none
current_session_id: 019f7653-7598-79e0-a0c3-1161f9c0b793
current_terminal_id: console_aa25af78-8c68-4f72-9ff5-489b78d25ece
produced_at: 2026-07-21T03:30:00Z
status: superseded
assigned_to: grok
assigned_at: 2026-07-20T16:48:47Z
assigned_by: 019f81b3-4a76-76f3-baf7-b87184b44b7b
assignment_note: >
  Claimed for fleet coordination. The producing session is ending; any fresh
  Grok Build session may pick this up. Other hosts (Claude/Codex) should not
  take it without explicit user direction — the env vars, paths, and auth
  bootstrap are Grok/Windows-specific.
handoff_type: investigation
accurate_as_of_head: 4c76891d20a09984e33ca2d3bf40c39537f2ffed
---

# Handoff: yt-is NLM fetch enablement + migration

> **SUPERSEDED 2026-07-30** by `yt-is-nlm-to-wiki-integration-20260730`. The 7,000-video
> NLM fetch was never run; instead, 3,910 transcripts were imported from nlm-to-wiki's
> already-exported .md store via `scripts/import_nlm_transcripts.py` (title-match bridge).
> The auth architecture (storage_state.json, backup repo, keepalive) remains in use.
> Migration Phases 3-7 remain deferred. This handoff is preserved for provenance.

## 1. Objective (one sentence)

Make `yt-is fetch` reliably download transcripts via the NotebookLM path at production scale, eliminating the source-mapping-failed bug and the chronic auth instability that blocked it.

**Scope bounds:** The work scope is the **~7,000 latest videos** in the pending backlog. The total pending backlog is 51,337 videos (`has_captions=0`); the remaining ~44,000 are **out of scope** for this handoff and will be addressed in a follow-on fetch once the 7,000-video batch proves the path at scale. Any acceptance criterion, throughput estimate, or falsifier in this handoff is calibrated to the 7,000-video scope, not the 51,337 total.

## 2. Status

**OPEN** — auth architecture shipped, source-add migration (Phase 1+2) merged and verified 4/5 transcripts via NLM. The actual 7000-video production fetch has NOT been run. Migration Phases 3-7 deferred.

## 3. Producing context

- **Date:** 2026-07-20
- **Session:** `019f7653-7598-79e0-a0c3-1161f9c0b793`
- **Terminal:** `console_aa25af78-8c68-4f72-9ff5-489b78d25ece`
- **Host:** Grok Build
- **HEAD at production:** `4c76891d20a09984e33ca2d3bf40c39537f2ffed`
- **Compaction:** yes (3 segments in `~/.grok/sessions/.../compaction/`)

## 4. Read-first list (ordered)

1. `P:/packages/yt-is/docs/operations/nlm-auth-architecture.md` — the canonical auth design doc. Read before touching anything NLM-auth-related.
2. `P:/packages/yt-is/docs/operations/nlm-surface-discovery-2026-07-20.md` — inventory of all nlm CLI call sites (baseline for Phases 3-7).
3. `P:/packages/yt-is/docs/operations/refactor-plan-2026-07-20-nlm-migration.md` — the 7-phase migration plan. Phases 1+2 done; 3-7 deferred.
4. `P:/packages/yt-is/csf/nlm_client.py` — Phase 1 sync wrapper around notebooklm-py (the new access layer).
5. `P:/packages/yt-is/csf/nlm_batch.py` lines 2324-2900 — `_add_sources_chunk` (Phase 2 migrated code, the bug fix).
6. `P:/packages/yt-is/csf/nlm_auth_check.py` — preflight that auto-restores storage from backup.
7. `P:/packages/yt-is/csf/nlm_keepalive.py` — weekly keepalive script + backup pusher.
8. `P:/packages/yt-is/AGENTS.md` — NLM auth section (warning to future LLMs about deprecated paths).

## 5. Verified facts (with source paths)

- [FACT] `yt-is fetch --limit 5 --workers 1` with env `NOTEBOOKLM_PROFILE=ytis-pro-worker-01 YTIS_INDUSTRIAL_BACKLOG_THRESHOLD=1 YTIS_NLM_WORKER_AUTH_USE_CDP=0` produces 4/5 transcripts via NLM in 42 seconds. Verified 2026-07-20 at `4c76891`. (transcript_cache rows with `source='notebooklm'`, lengths 9972-19045 chars)
- [FACT] The 1/5 failure is Google API `rpc_code=9` on a specific video — intermittent, not deterministic. The same video sometimes succeeds, sometimes fails. Not a yt-is bug. (Trial 2 output, this session)
- [FACT] The nlm CLI silently drops the Nth source ID (github jacob-bd/notebooklm-mcp-cli#196). `nlm source add --json` has the same bug. Only `notebooklm-py`'s `client.sources.add_url()` returns all source IDs reliably. (Trial 1 + Trial 2, this session)
- [FACT] Auth storage at `P:/.data/yt-is/nlm-auth/storage_state.json` (14,350 bytes) works. Session probe shows 61-62 notebooks visible. (keepalive dry-run 2026-07-20)
- [FACT] Backup repo at `C:/Users/brsth/.ytis-nlm-auth-backup/` has committed storage. No remote configured. Pre-push hook blocks any push. (verified this session)
- [FACT] Preflight auto-restore works: deleted live file, ran `yt-is list`, preflight restored from backup automatically. (verified this session)
- [FACT] Weekly keepalive scheduled task `YtisNlmAuthKeepalive` registered, next run Sunday July 26 03:00. (verified via `Get-ScheduledTask`)
- [FACT] Google sessions expire under programmatic access. Bootstrap at 14:40 expired by ~22:12 (7.5 hours). Re-bootstrap via `python -m notebooklm login` detected "Already logged in" via Chrome persistent profile and refreshed silently. (observed this session)
- [FACT] All 51,337 pending videos have `has_captions=0` in `batch_status.sqlite`. The `no_captions` classification is correct. These go to the `notebooklm` lane by default. **Work scope is the ~7,000 latest of these; the remaining ~44,000 are deferred to a follow-on fetch (see §1 Scope bounds).** (DB query, this session)
- [FACT] Library versions: google-genai 2.12.1, notebooklm-mcp-cli 0.8.9, notebooklm-py 0.7.3, youtube-transcript-api 1.2.4. All verified compatible with yt-is's actual API usage. (pip show + import tests, this session)

## 6. Current state

### Done and merged to main (`4c76891`)

| Component | Status | Evidence |
|---|---|---|
| Library upgrades | ✅ Done | requirements.txt hardened; `pip show` confirms |
| Deps check module | ✅ Done | 25 tests pass; `yt-is --check-deps` works |
| NLM auth architecture | ✅ Done | storage file, backup repo, preflight, keepalive, scheduled task |
| Source-add migration Phase 1 (`csf/nlm_client.py`) | ✅ Done | 27 unit tests pass; path bug fixed |
| Source-add migration Phase 2 (`_add_sources_chunk`) | ✅ Done | 4/5 transcripts via NLM verified end-to-end |

### Not done (deferred)

| Component | Status | Why deferred |
|---|---|---|
| **7000-transcript production fetch** | NOT RUN | The actual goal. Everything else was scaffolding. |
| Migration Phase 3 (notebook CRUD) | Not started | Fetch works without it; debt reduction |
| Migration Phase 4 (source list/content) | Not started | Same |
| Migration Phase 5 (auth bootstrap) | Not started | Same |
| Migration Phase 6 (dead code removal) | Not started | Blocked by 3-5 |
| Migration Phase 7 (test updates) | Not started | Blocked by 6 |
| Review fixes R-1, R-12 | Not started | Rare edge cases; documented in review findings |

## 7. Task packets

### TASK-01: Run the 7000-transcript production fetch

- **goal:** Download ~7000 pending transcripts via the NLM path at production scale
- **in scope:** `python bin/csf-source fetch --workers 6` (or chosen worker count) from `P:/packages/yt-is`
- **out of scope:** migration Phases 3-7, code changes
- **files / anchors:** no code changes; runtime only
- **acceptance:** transcript_cache grows by ~7000 rows with `source='notebooklm'`; `batch_status.sqlite` shows videos moving from `pending` to `complete`
- **falsifier:** success rate < 90% on first pass (i.e., fewer than ~6,300 of 7,000 transcripts land in `transcript_cache` with `source='notebooklm'`); OR fetch crashes with auth error; OR fetch hangs > 30 min without progress. A run that produces 3,000/7,000 passes the old "not zero" bar but is a disaster — the 90% threshold catches that.
- **verification level required:** LIVE_BEHAVIOR
- **preflight:**
  1. Verify auth storage exists: `Test-Path P:/.data/yt-is/nlm-auth/storage_state.json`
  2. Probe session: `python -m csf.nlm_keepalive --dry-run` (should show "session alive; N notebooks visible")
  3. If session dead: `python -m notebooklm login --storage P:/.data/yt-is/nlm-auth/storage_state.json --browser chrome`
  4. Set env: `$env:NOTEBOOKLM_PROFILE="ytis-pro-worker-01"; $env:YTIS_INDUSTRIAL_BACKLOG_THRESHOLD="1"; $env:YTIS_NLM_WORKER_AUTH_USE_CDP="0"`
- **expected duration (math shown):** 5 videos took 42 seconds → 8.4 s/video. At `--workers 1`: 7,000 × 8.4s ≈ **16.3 hours**. At `--workers 6` (assuming linear scaling, unlikely under rate limits): ≈ **2.7 hours**. Realistic expectation with rate-limit degradation at 6 workers: 4–8 hours. **Either way, the run exceeds the observed 7.5-hour Google session lifespan — see §9 constraint 3 and the auth-expiry mitigation below.**
- **auth-expiry mitigation (required for any run > 7h):** Either (a) run the weekly keepalive task's session-refresh inline during the fetch, or (b) chunk the 7,000-video backlog into sub-7h windows (e.g., 2,500-video batches), re-probing auth between batches. Option (b) is safer because it bounds the blast radius of a mid-run auth death. The fetcher does NOT currently auto-rebootstrap on session expiry — confirm this before starting (check `csf/nlm_auth_check.py:ensure_storage()` for expiry detection vs. missing-file-only detection).
- **risk:** the rpc_code=9 intermittent failure affects ~1/5 videos per batch. Failed videos will need a second fetch pass. The per-video retry in Phase 2 handles some of these inline.

### TASK-02: Migration Phase 3 — notebook CRUD

- **goal:** Replace `nlm notebook create/list/delete` CLI calls with `client.notebooks.*`
- **in scope:** `csf/nlm_scraper.py:1491,1766,1778,1796,2566,2592,2619`; `csf/nlm_content_probe.py:109`
- **out of scope:** source-add (done), auth bootstrap (Phase 5)
- **acceptance:** existing notebook CRUD tests pass; fetch still produces transcripts
- **falsifier:** notebook creation fails after migration
- **verification level required:** LIVE_BEHAVIOR
- **note:** A partial Phase 3 attempt was stashed (csf/nlm_content_probe.py + csf/nlm_scraper.py changes). That stash was dropped during cleanup. Re-implement from scratch using `csf/nlm_client.py`.

### TASK-03: Migration Phases 4-7

- **goal:** Complete the migration (source list/content, auth bootstrap, dead code removal, test updates)
- **dependency:** TASK-02 (Phase 3) must complete first
- **acceptance:** `grep -r 'nlm_auth_guard.run_nlm' csf/ bin/` returns zero; full test suite passes
- **verification level required:** UNIT_TEST + LIVE_BEHAVIOR

### TASK-04: Review fixes R-1, R-12

- **goal:** Apply deferred review findings
- **R-1:** Add file lock around keepalive backup push (concurrent push race)
- **R-12:** Add retry on transient 429 in keepalive probe
- **acceptance:** review findings file updated; changes tested
- **verification level required:** UNIT_TEST

### TASK-05: Add NLM path success rate metric (fallback masking prevention)

- **goal:** Surface a derived metric in `fetch_completed` that reveals when the NLM primary path is failing but overall success is high because ytdlp fallback is covering
- **in scope:** `bin/csf-source` — the `_build_fetch_completed_payload` function (line ~318) and `_log_fetch_completed` function (line ~652). Add a computed field to the `fetch_completed` event.
- **out of scope:** new logging infrastructure (use existing `log_action` pattern); new alerting system (the metric surfaces in logs; future work could add dashboarding)
- **files / anchors:** `bin/csf-source:318-402` (payload builder), `bin/csf-source:652-720` (log completed)
- **metric spec:**
  ```
  nlm_path_success_rate: float  # nlm_succeeded / nlm_eligible (0.0-1.0)
  nlm_path_eligible: int        # videos routed to notebooklm lane
  nlm_path_succeeded: int       # videos successfully extracted via notebooklm
  fallback_masking_detected: bool  # True when nlm_path_success_rate < 0.5 AND overall success_rate > 0.8
  ```
- **acceptance:** `fetch_completed` event in `.logs/console_*.jsonl` contains the new fields; when NLM path fails but ytdlp succeeds, `fallback_masking_detected: true` appears in the log
- **falsifier:** NLM path breaks and the warning does NOT appear within one fetch run
- **verification level required:** LIVE_BEHAVIOR
- **why this matters:** The NLM source-mapping-failed bug went unnoticed for 3 months because ytdlp fallback kept overall success rate high. This metric makes the primary path's failure visible immediately, not after months of log archaeology. (AAR OPP-006, session 2026-07-20)

## 8. Open decisions

### DECISION-01: When to run the 7000-transcript fetch

- **Question:** Run it in the next session, or wait?
- **Options:**
  - (A) Next session, fresh context — recommended. Auth is bootstrapped; one command starts the fetch.
  - (B) Wait until migration Phases 3-7 are done — unnecessary; the fetch works now.
- **Selection criterion:** lowest risk of losing work. Fresh session is cleaner.
- **Currently leads:** (A)

### DECISION-02: Worker count for the production fetch

- **Question:** `--workers 1` (safe, slow) or `--workers 6` (production config, faster)?
- **Context:** The worker pool assigns `ytis-worker-{N}` profiles. These resolve to `ytis-pro-account` via PROFILE_TO_ACCOUNT (single account currently). 6 concurrent workers on one Google account may hit rate limits.
- **Options:**
  - (A) `--workers 1` first, verify throughput, then scale
  - (B) `--workers 6` directly (original production config)
- **Selection criterion:** reliability over speed (user preference)
- **Currently leads:** (A) — but this is the user's call

### DECISION-03: Resume migration or close it

- **Question:** Should Phases 3-7 be done at all?
- **Context:** The fetch works with Phase 1+2. Phases 3-7 are path-monopoly restoration (removing the CLI entirely). The dual-path (CLI for notebook CRUD, notebooklm-py for source-add) works but violates `root-cause-program.md:27`.
- **Options:**
  - (A) Resume Phases 3-7 after the fetch is running
  - (B) Leave the dual-path; accept the debt
- **Selection criterion:** path monopoly vs. working code. User stated "optimal long-term" — which favors (A).
- **Currently leads:** (A) — but defer until after the fetch is verified at scale

## 9. Hard constraints

1. **Never commit `storage_state.json` to any repo with a remote.** It contains live Google session cookies. The `.gitignore` at `P:/packages/yt-is/.gitignore` explicitly excludes `.data/yt-is/nlm-auth/`.
2. **Never delete `P:/.data/yt-is/nlm-auth/storage_state.json` or the backup repo.** Preflight auto-restores, but if both are gone, re-bootstrap requires interactive login.
3. **Auth bootstrap is interactive (one-time).** `python -m notebooklm login --storage P:/.data/yt-is/nlm-auth/storage_state.json --browser chrome`. Opens Chrome, user logs in. After that, session persists for weeks/months.
4. **The nlm CLI `source add` command is broken (silent N-1 source ID drop).** Do not use it for source-add. Use `client.sources.add_url()` via `csf/nlm_client.py` instead.
5. **Invariant A2** (`csf/nlm_batch.py:3167`): "uncorroborated list-order pairing is never used to fill gaps." Phase 2 eliminates the need for this invariant by using typed Source objects, but the invariant is preserved by construction.
6. **Multi-worker correctness:** workers must not share notebooks. Each worker creates its own worker notebook with a unique title.
7. **`YTIS_NLM_WORKER_AUTH_USE_CDP=0`** is required for the current auth model. The CDP family-refresh machinery is deprecated and produces 0.0s no-op refreshes (red-team FM-4).

## 10. Cross-reference couplings

- `P:/packages/yt-is/AGENTS.md` NLM auth section → points to `docs/operations/nlm-auth-architecture.md`. If the doc moves, update the pointer.
- `csf/nlm_client.py` → imports `STORAGE_PATH` from `csf/nlm_auth_check`. If the storage path changes, both must update.
- `csf/nlm_keepalive.py` → pushes to `C:/Users/brsth/.ytis-nlm-auth-backup/`. If the backup repo moves, update `BACKUP_REPO` constant.
- `bin/yt-is` → calls `ensure_storage()` from `csf/nlm_auth_check`. Preflight runs on every invocation except `--help`.
- `refactor-plan-2026-07-20-nlm-migration.md` → references Phase numbers that are now partially done. Phases 1+2 merged; 3-7 pending.
- `~/.grok/AGENTS.md` § "Automate user meta-actions" → references `P:/docs/goals/reduce-user-meta-actions-2026-07-20.md`.
- `~/.grok/AGENTS.md` § "Optimal long-term solution" → supersedes old "Minimal fix" framing. If reverted, skills will drift back to minimal-change bias.

## 11. Other outstanding streams

- **Preference-effectiveness goal** (`P:/docs/goals/reduce-user-meta-actions-20260720.md`) — standing goal to reduce user-initiated meta-actions. Open. No session-scoped deadline.
- **Preference edits to workspace-level files** (`P:/AGENTS.md`, `P:/.claude/CLAUDE.md`) — global files updated but workspace-level files may still carry old "simplicity first" framing. Low priority; ambient context from globals dominates.
- **Persona files** (`~/.grok/personas/design-doc-writer.toml`, `design-doc-reviewer.toml`) — mentioned as potentially containing old "simplicity" framing but not checked. If `/design` still drifts, check these.

## 12. Explicit non-goals

- Do NOT revert the auth architecture to the CLI/CDP-family model. It's deprecated for good reasons (documented in `nlm-auth-architecture.md`).
- Do NOT remove the nlm CLI from the system. It's useful for debugging and still used by Phases 3-7's unmigrated code.
- Do NOT run `YTIS_NLM_WORKER_AUTH_USE_CDP=1`. The CDP path opens browser popups and produces 0.0s no-op refreshes.
- Do NOT attempt to fix the rpc_code=9 Google API intermittent failure. It's upstream. Per-video retry handles it.
- Do NOT merge Phases 3-7 without end-to-end verification (the lesson from Phase 2's path bug — unverified code ships broken).
- Do NOT run the production fetch from this session. Start fresh.

## 13. Resumption protocol

1. **Fresh session.** Read this handoff first.
2. **Verify auth:** `python -m csf.nlm_keepalive --dry-run` from `P:/packages/yt-is`. Expected: "session alive; N notebooks visible." If expired, re-bootstrap: `python -m notebooklm login --storage P:/.data/yt-is/nlm-auth/storage_state.json --browser chrome`.
3. **Set env vars:**
   ```powershell
   $env:NOTEBOOKLM_PROFILE = "ytis-pro-worker-01"
   $env:YTIS_INDUSTRIAL_BACKLOG_THRESHOLD = "1"
   $env:YTIS_NLM_WORKER_AUTH_USE_CDP = "0"
   ```
4. **Start with a 5-video smoke test:** `python bin/csf-source fetch --limit 5 --workers 1`
5. **If 4+/5 succeed:** run the full 7,000-video backlog at `--workers 1` first (≈16 hours; see TASK-01 math). Only raise to `--workers 6` after a stable 1-hour sample at `--workers 1` shows no auth degradation and acceptable rpc_code=9 retry rate. Chunking into 2,500-video batches is recommended over a single 16-hour run (see TASK-01 auth-expiry mitigation).
6. **Monitor:** check `P:/packages/yt-is/.logs/console_*.jsonl` for `fetch_completed` events and `transcript_cache` growth.

## 14. Suggested next invocation

```
Read P:/docs/handoffs/ytis-nlm-fetch-and-migration-20260720/HANDOFF.md, then run the 7000-transcript fetch. Start with a 5-video smoke test to verify auth, then scale to --workers 1 for the full backlog. Set YTIS_NLM_WORKER_AUTH_USE_CDP=0. If auth has expired, re-bootstrap with: python -m notebooklm login --storage P:/.data/yt-is/nlm-auth/storage_state.json --browser chrome
```

## 15. Last user message (verbatim)

> "okay what's left"

(Prior context: user had asked for commit+push, worktree cleanup, and then "what's left." The answer was: the 7000-transcript fetch is the one outstanding item.)

## 16. Epistemic labels per claim

- `[FACT]` 4/5 transcripts via NLM verified at commit `4c76891` (transcript_cache rows)
- `[FACT]` Auth architecture shipped and verified (keepalive, preflight, backup)
- `[FACT]` rpc_code=9 is intermittent and upstream (Trial 2 showed different videos failing on different runs)
- `[FACT]` Phase 2 code eliminates the source-mapping-failed bug class (typed Source.id replaces stdout parsing)
- `[INFERENCE]` The production fetch will work at scale because the 5-video test exercised the same code path. Risk: rate limiting at 6 workers on one account.
- `[INFERENCE]` Google session expiry is the main risk to a long fetch. Observed 7.5-hour lifespan. The fetch may need auth refresh mid-run.
- `[UNKNOWN]` Whether `--workers 6` will hit Google rate limits. Not tested.
- `[UNKNOWN]` Total runtime for 7000 videos. 5 videos = 42s, but NLM add+materialize has per-source latency.
