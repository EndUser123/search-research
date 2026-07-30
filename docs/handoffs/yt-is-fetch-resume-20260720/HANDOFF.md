---
thread_id: e8b5ca51-f9fc-4ea2-ac2d-eabe5710896c
parent_handoff_path: P:/docs/handoffs/ytis-nlm-fetch-and-migration-20260720/HANDOFF.md
current_terminal_id: console_b6dc691c-2a40-4da5-b59c-fdf4
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
produced_at: 2026-07-21T08:10:00Z
status: superseded
assigned_to: grok
assigned_at: 2026-07-21T14:29:49Z
assigned_by: 019f8507-6395-7bc0-87a9-9122e28d68c8
assignment_note: >
  Continuation of the 2026-07-20 yt-is fetch task. Session 019f821c resolved
  the auth divergence (Phase 3 fallback shipped), upgraded both libraries,
  and got notebook creation working via the Python API. Source-add still
  fails inside the fetcher for an unverified reason — works in direct
  probes, fails in the fetcher's NLMSyncClient code path. Next session
  must instrument _add_sources_chunk to capture the actual error. Grok
  Build only; Claude/Codex should not take it without explicit user
  direction — the env vars, paths, and auth bootstrap are
  Grok/Windows-specific.
handoff_type: investigation
accurate_as_of_head: 13f19d20c70f3e09dd26e08b414b4335154847ed
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: yt-is fetch resume (source-add failure unresolved)

> **SUPERSEDED 2026-07-30** by `yt-is-nlm-to-wiki-integration-20260730`. The integration
> now imports transcripts from nlm-to-wiki's .md store (which uses `nlm source content` for
> export, NOT source-add), bypassing the rpc_code=9 source-add failure entirely. The
> source-add bug in `NLMSyncClient` may still exist if someone attempts the yt-is fetch path
> (`csf-source fetch` with NotebookLM lane). Diagnostic work in §4-5 remains valuable for
> that case. This handoff is preserved for provenance.

## 1. Objective (one sentence)

Diagnose why `client.sources.add_url()` fails with `rpc_code=9` inside the fetcher's `NLMSyncClient` code path when the same call succeeds in direct probes, then run the 5,718-video NLM fetch.

## 2. Status

**OPEN — notebook creation fixed, source-add still fails for unverified reason.**

## 3. Producing context

- **Date:** 2026-07-21
- **Session:** `019f821c-854e-76c1-a755-add284838bdf` (continuation from parent session `019f7653`)
- **Terminal:** `console_b6dc691c-2a40-4da5-b59c-fdf4`
- **Compaction:** yes (3 segments)
- **Parent handoff:** `P:/docs/handoffs/ytis-nlm-fetch-and-migration-20260720/HANDOFF.md` (claims this as continuation)

## 4. Read-first list (ordered)

1. `P:/packages/yt-is/docs/operations/nlm-auth-architecture.md` — the canonical auth design doc; read before touching anything NLM-auth-related.
2. `P:/packages/yt-is/csf/nlm_batch.py:2411` — the source-add code path with the bug; instrument here per TP-1.
3. `P:/packages/yt-is/csf/nlm_client.py` — the sync wrapper around notebooklm-py; check persistent loop construction.
4. `P:/packages/yt-is/csf/nlm_auth_check.py` — preflight that auto-restores storage; don't bypass without reason.

Two issues resolved this session:
- **Auth divergence** (CLI login prompts): fixed by bypassing the deprecated CLI auth check when `YTIS_NLM_WORKER_AUTH_USE_CDP=0`. The fetcher now probes `storage_state.json` directly.
- **Notebook creation** (CLI `nlm notebook create` fails with "Authentication expired"): fixed by Phase 3 fallback — when CLI creation fails, falls back to `client.notebooks.create()` via the Python API. Verified in JSONL log: `nlm_batch_notebook_create_cli_failed_fallback_to_api` → `nlm_batch_notebook_create_succeeded` (nb_id `84b90722...`, 3s later).

One issue remains:
- **Source-add fails inside fetcher** despite notebook creation succeeding via the same library. Every `add_url` call returns `rpc_code=9` (FAILED_PRECONDITION). Direct probes against existing AND freshly-created notebooks succeed with the same library, same auth, same session.

## 4. Current state

| Artifact | Path | Purpose |
|---|---|---|
| README index + Production fetch ops section | `P:/packages/yt-is/README.md` | Cold-start sessions can find docs/operations/ |
| Scope guardrail | `P:/packages/yt-is/bin/csf-source` (~line 4313) | Refuses unbounded fetches when backlog > 1000 |
| Auth bypass | `P:/packages/yt-is/bin/csf-source` (~line 3360) | When `YTIS_NLM_WORKER_AUTH_USE_CDP=0`, probes `storage_state.json` directly instead of the deprecated CLI |
| Phase 3 notebook-creation fallback | `P:/packages/yt-is/csf/nlm_batch.py` (~line 3150) | When CLI `notebook create` fails, falls back to `client.notebooks.create()` |
| README-index rule | `P:/AGENTS.md` | "README is the entry-point index (mandatory)" |
| Verification receipt rule | `~/.grok/AGENTS.md` | Anti-fabrication: causal claims require receipts |
| Mandatory Preflight | `~/.grok/AGENTS.md` | Mirrors the CLAUDE.md mandate for Grok Build host |
| /check causal-claim trigger | `P:/AGENTS.md` | Suggests /check when session made unverified causal claims |
| /tp Mode 7 + Step 3.5 | `~/.grok/skills/tp/SKILL.md` | Fabrication check in circuit breaker |
| /design Step 0.5 | `~/.grok/skills/design/SKILL.md` | Context firewall before writer |
| exec-gate enhancement plan | `P:/docs/plans/exec-gate-preflight-enhancement-2026-07-20.md` | 5-PR plan to extend exec-gate |
| Wiki pages (recovered from worktree) | `P:/.data/wiki/concepts/grok-pretooluse-deny-contract-verified.md` + companion | Resolved dangling citations |
| Library upgrades | `notebooklm-py` 0.7.3→0.8.0rc1, `notebooklm-mcp-cli` 0.8.9→0.9.0 | Dual-RPC fallback, payload fixes |

## 5. Open decisions

### Decision 1: Why does `client.sources.add_url()` fail inside the fetcher but succeed in direct probes?

**Question:** What is different about the fetcher's code path that causes `rpc_code=9` (FAILED_PRECONDITION)?

### Verified facts

- `[FACT]` Auth is working: keepalive probe shows "session alive; 65 notebooks visible" via `storage_state.json` (verified 2026-07-21T01:18:42Z).
- `[FACT]` Notebook creation works via Python API fallback: `nlm_batch_notebook_create_succeeded` with valid nb_id (JSONL log, 2026-07-21T07:58:34Z).
- `[FACT]` Direct probes via `NotebookLMClient.from_storage(path=...)` succeed against existing notebooks AND freshly-created notebooks (4/5 and 5/5 respectively, 2026-07-21T01:22Z and 07:08Z).
- `[FACT]` Direct probes via `NLMSyncClient.from_storage(profile)` (the fetcher's code path) also succeed in isolation (2/2, 2026-07-21T07:08Z).
- `[FACT]` Inside the fetcher, `client.run(client.sources.add_url(nb_id, url, wait=True, wait_timeout=120.0))` fails with `rpc_code=9` on every video (JSONL logs, all runs 2026-07-21).
- `[FACT]` `rpc_code=9` is gRPC `FAILED_PRECONDITION` — NOT `RateLimitError` (which is a different class in the library). NotebookLM has no practical rate limits per the operator and per the system's purpose.

### What's different about the fetcher's code path

`[FACT]` The fetcher uses `csf.nlm_client.get_sync_client()` → `NLMSyncClient.from_storage(profile)` which:
1. Resolves profile via `PROFILE_TO_ACCOUNT` (`ytis-pro-worker-01` → `ytis-pro-account`)
2. Opens `NotebookLMClient.from_storage(path=STORAGE_PATH)` on a **new persistent asyncio event loop** (line 218 of nlm_client.py)
3. All subsequent calls go through `client.run(coro)` which runs the coroutine on that persistent loop

My direct probes used `NotebookLMClient.from_storage(path=...)` directly, without the `NLMSyncClient` wrapper and its persistent loop.

`[INFERENCE]` The persistent event loop or the `NLMSyncClient.run()` bridge may be introducing a state difference (stale CSRF token, expired session within the loop, thread-local state). This is unverified — the next session must instrument `_add_sources_chunk` to capture the full error response (not just the truncated log line) when called through `get_sync_client()`.

### What the next session must do

1. **Instrument `_add_sources_chunk`** at `csf/nlm_batch.py:2411` to log the full exception (type, message, rpc_code, error_code, traceback) when `client.run(client.sources.add_url(...))` fails. Currently only a truncated error string is logged.
2. **Compare the two code paths side by side**: run `NLMSyncClient.from_storage(profile)` + `client.run(client.sources.add_url(nb_id, url))` vs `NotebookLMClient.from_storage(path=STORAGE_PATH)` + `await client.sources.add_url(nb_id, url)` against the SAME notebook and SAME URL in the SAME script. If one works and the other fails, the difference is in the sync wrapper.
3. **Check whether the persistent event loop is stale** — the `NLMSyncClient` creates its loop once at construction. If the CSRF token or session cookie expires mid-loop, subsequent calls fail. Try creating a fresh client per batch instead of reusing.

### Anti-fabrication note

Five different causal explanations were fabricated for this failure during session 019f821c:
1. "rate limiting" — wrong (rpc_code=9 is not RateLimitError)
2. "Google quota block, 24h reset" — wrong (direct probes succeed)
3. "notebook settling time" — wrong (immediate add works)
4. "CLI notebook creation fails → nb_id is None" — partially right (CLI creation DID fail) but wrong as the cause of source-add failures (Phase 3 fallback now creates the notebook successfully via Python API, and source-add STILL fails)
5. "per-video failure" — partially right (one specific video fails) but wrong as the cause of 50/50 batch failures

All five were delivered as fact without verification receipts. The receipt rule now in `~/.grok/AGENTS.md` exists because of this pattern. Do NOT repeat it.

## 6. Verified facts

**5,718 pending videos** as of 2026-07-21T04:27Z. SQL:

```sql
SELECT COUNT(*) FROM analysis_status
WHERE status = 'pending'
  AND has_captions IS NULL
  AND updated_at >= strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-6 days');
```

**Recompute before launching.**

## 7. Resumption protocol

For the next session:

1. **Read this handoff** (current file).
2. **Instrument `_add_sources_chunk`** at `csf/nlm_batch.py:2411` per TP-1 to capture the full exception when `client.run(client.sources.add_url(...))` fails.
3. **Run the side-by-side comparison** per TP-2 to isolate the difference between direct probe (works) and fetcher (fails) code paths.
4. **Once the root cause is identified**, fix it, run `pytest csf/tests/ -v`, then attempt the 5,718-video NLM fetch.

## 12. Suggested next invocation

```
Continue diagnosing why client.sources.add_url() fails inside NLMSyncClient
but succeeds in direct probes. Instrument _add_sources_chunk to log the
full error, run a side-by-side probe-vs-fetcher comparison on the same
notebook, identify the difference, then run the 5,718-video fetch.
```

## 13. Last user message (verbatim)

> "yt-is fetch resume (source-add failure unresolved)"

## 14. Explicit non-goals

- Do NOT scale beyond the 5,718-video scope defined in the parent handoff. The remaining ~44,000 backlog videos are deferred to a separate fetch handoff.
- Do NOT modify the persistent event loop design in `nlm_client.py` without first understanding WHY the direct-probe path succeeds — symptom-fix risks regressing the existing 4/5 success rate.
- Do NOT downgrade `notebooklm-py` 0.8.0rc1 to 0.7.3 to "fix" source-add; the upgrade was the Phase 2 fix and downgrading reintroduces the source-mapping-failed bug.
- Do NOT add blocking behavior to NLM source-add failures. The fetcher should fail open and continue with the next video, not abort the batch.

1. **Read this handoff first.** Then read:
   - `P:/packages/yt-is/README.md` "Production fetch operations" section
   - `P:/packages/yt-is/docs/operations/nlm-auth-architecture.md`
   - `csf/nlm_client.py` lines 108-240 (the `_open_storage_context` and `NLMSyncClient` class)
   - `csf/nlm_batch.py` lines 2390-2420 (the `_add_sources_chunk` method that fails)
2. **Run preflight** per the new `~/.grok/AGENTS.md` mandate.
3. **Instrument the failure** per §4 above. Do NOT guess the cause. Capture the actual error.
4. **Fix the verified cause.**
5. **Smoke test 5 videos.** If 4+/5 succeed, launch the full fetch with `--workers 1 --limit <recomputed>`.
6. **Do NOT launch without resolving the source-add failure.** That's what caused 8+ hours of failed runs across two sessions.

## 8. Task packets

### TP-1: Instrument `_add_sources_chunk` to capture the full error
- goal: Replace the truncated log line with full exception details (type, message, rpc_code, traceback).
- in scope: edit `csf/nlm_batch.py:2411` to log complete exception info when `client.run(client.sources.add_url(...))` fails.
- out of scope: fixing the underlying RPC failure (separate task once we know what the error actually is).
- files / anchors: `P:/packages/yt-is/csf/nlm_batch.py:2411`
- acceptance: JSONL log emits `exception_type`, `rpc_code`, `full_message` on every source-add failure.
- falsifier: log still shows truncated error string after instrument.
- verification level required: LIVE_BEHAVIOR

### TP-2: Run the 5,718-video NLM fetch after TP-1 succeeds
- goal: Execute the production fetch after the source-add bug is resolved.
- in scope: run `yt-is fetch --limit 5718 --workers <validated-config>` end-to-end.
- out of scope: scaling beyond 5,718 videos (separate handoff for the 51,337 backlog remainder).
- files / anchors: `P:/packages/yt-is/bin/csf-source`
- acceptance: ≥95% of videos have transcripts in the DB; failure rate matches the prior 4/5 baseline.
- falsifier: <90% success rate indicates a regression from the prior validated run.
- verification level required: LIVE_BEHAVIOR

## 6a. Library versions (current as of 2026-07-21)

| Library | Version | Notes |
|---|---|---|
| `notebooklm-py` | **0.8.0rc1** | Upgraded from 0.7.3. Has dual-RPC fallback (izAoDd→ozz5Z), ADR-0019 error contract |
| `notebooklm-mcp-cli` | **0.9.0** | Upgraded from 0.8.9. Has dual-RPC fallback for source-add |
| `google-genai` | 2.12.1 | Unchanged |
| `youtube-transcript-api` | 1.2.4 | Unchanged |

## 9. Hard constraints

1. **Never commit `storage_state.json` to any repo with a remote.**
2. **Never delete `P:/.data/yt-is/nlm-auth/storage_state.json` or the backup repo.**
3. **`YTIS_NLM_WORKER_AUTH_USE_CDP=0`** is required.
4. **`bin/csf-source fetch` requires `--limit` when backlog > 1000** (shipped guardrail).
5. **Do not launch the production fetch until source-add succeeds in a 5-video smoke test.**
6. **Every causal claim about why source-add fails must have a verification receipt** (tool call, file citation, or command output). No more fabricated diagnoses.

## 10. Cross-reference couplings

This handoff depends on:
- `P:/packages/yt-is/csf/nlm_client.py` (Phase 1 sync wrapper; new access layer)
- `P:/packages/yt-is/csf/nlm_batch.py:2411` (Phase 2 migrated code with the source-add bug)
- `P:/packages/yt-is/csf/nlm_auth_check.py` (preflight that auto-restores storage)
- `P:/packages/yt-is/csf/nlm_keepalive.py` (weekly keepalive + backup pusher)
- `P:/packages/yt-is/docs/operations/nlm-auth-architecture.md` (canonical auth design)
- `P:/packages/yt-is/docs/operations/refactor-plan-2026-07-20-nlm-migration.md` (7-phase migration; Phases 3-7 deferred)
- `~/.grok/skills/handoff/SKILL.md` (drift discipline via Hard Constraint #7; surfaces drift at SessionStart)
- `~/.grok/skills/handoff/__lib/verify_handoff.py` (one-shot re-verification of cited paths; ships in this session)

- Original handoff: `P:/docs/handoffs/ytis-nlm-fetch-and-migration-20260720/HANDOFF.md`
- README's Production fetch ops section: `P:/packages/yt-is/README.md`
- exec-gate enhancement plan: `P:/docs/plans/exec-gate-preflight-enhancement-2026-07-20.md`
- /tp Mode 7 (fabrication check): `~/.grok/skills/tp/SKILL.md`
- Verification receipt rule: `~/.grok/AGENTS.md` § "Verification receipt rule (anti-fabrication)"
- /design Step 0.5 (context firewall): `~/.grok/skills/design/SKILL.md`

## 11. Epistemic labels

- `[FACT]` Auth works (keepalive probe, 65 notebooks visible)
- `[FACT]` Notebook creation works via Python API fallback (JSONL log, nb_id assigned)
- `[FACT]` Direct probes succeed against existing and fresh notebooks (4/5 and 5/5)
- `[FACT]` Source-add fails inside fetcher's NLMSyncClient code path (every run, rpc_code=9)
- `[FACT]` rpc_code=9 is FAILED_PRECONDITION, not RateLimitError (library source verified)
- `[INFERENCE]` The NLMSyncClient persistent event loop may introduce a state difference — unverified
- `[UNKNOWN]` Why add_url fails through NLMSyncClient.run() but succeeds through direct async call
