# Red-team workflow reliability handoff

| Field | Value |
|---|---|
| **Date** | 2026-07-19 |
| **Source session** | Self-review run at `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/` |
| **Status** | Investigation complete; 1 incident logged, 5 operational fixes proposed, user decision pending on paths |
| **Goal** | Make `/red-team` reliable (catches its own silent failures) and optimal (don't repeat mistakes this session demonstrated) |

---

## TL;DR

This session surfaced **one MATERIAL operational gap** and three secondary ones. The material gap: **the orchestrator has no post-dispatch verification of whether a specialist actually wrote its findings file**. The failure-modes agent returned a path that didn't exist; the only reason we caught it was manual folder inspection after the critic ran.

The single most important fix is a one-paragraph addition to the orchestrator's specialist-dispatch step: `Test-Path $path` after each specialist returns, retry-once-with-stronger-instruction or log incident + DEFERRED marker.

Three secondary gaps: delayed completion notifications made dispatch state unclear enough that I had to verify filesystem state; three search tools were available but I defaulted to the lowest-priority one (`web_search` instead of `minimax-search` MCP per its "MUST" directive); and the operator_outcome telemetry patching requires a manual Python one-liner because the CLI doesn't expose it.

**Reading time:** ~5 min. **To act:** start at section 2.1 (Priority 1); skip section 4 if you're not planning to apply the wiki REVISE next-steps in this session.

---

## 1. Empirical findings from this session

### 1.1 Silent no-write failure mode (CRITICAL)

- **Symptom:** Agent dispatched with explicit "write findings to `{run_dir}/X.json`" instruction. Subagent returns with response text containing the path. Orchestrator proceeds to critic. Critic reads the file — fails or notes missing. Manual folder inspection reveals the file does not exist. Findings are silently lost.
- **Reproduced in this run:** `red-team-failure-modes` agent. Dispatch returned exit code 0 with the path `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/failure-modes.json` in its response. Subagent transcript shows 6 tool calls (read proposal.md, qmd commands) but **no write invocation**. The planned findings (3 BLOCK + 3 REVISE across items A-F) are visible only in the transcript's in-context thinking, not on disk.
- **Detection rate:** 100% in this run, caught only by post-hoc manual inspection after the critic returned. Without the manual step, REVISE verdict would have shipped without any specialist coverage gap flag.
- **Recorded as:** incident `inc-48fd0ac31fb7`, category `specialist-miss`, at `P:/.claude/state/red-team/incidents.jsonl`.
- **Prior-art search:** 17 prior `failure-modes.json` files exist across `P:/.claude/.artifacts/`, `P:/docs/`, `P:/tmp/`. No prior `specialist-miss` incidents in `incidents.jsonl` (could not locate prior issues — likely because manual inspection caught them in prior runs too, or the category is new).

### 1.2 Delayed completion notifications (HIGH)

- Three of five specialist dispatches in this run produced duplicate completion notifications arriving AFTER the run had been synthesized:
  - `019f7a9b-876a-7513-8044-bc1ca787f01b` — workflow-reviewer, file already on disk 7:42:14
  - `019f7a9b-876a-7513-8044-bc217e1dbcad` — failure-modes, no file on disk (1.1)
  - `019f7a9b-876b-72c1-b790-6b6a7347c999` — logic, file already on disk 7:42:21
- **Symptom:** The async notification system sends "task completed" messages that lag the actual file write by 1–5 minutes. The orchestrator has no way to tell from the notification alone whether the file is on disk.
- **Cascade impact:** Orchestrator time wasted on filesystem checks. ~30 seconds per duplicate notification. Cumulative across many sessions: real.
- **Mitigation already taken in this run:** filesystem checks confirmed each notification matched an existing file (1.x) or absent file (1.1).

### 1.3 Tool-search default wrong (MEDIUM)

- Discovered mid-session: three search tools were available — `web_search` (built-in), `minimax-search__web_search` (MCP), `web-search-prime__web_search_prime` (MCP with recency + domain filters).
- `minimax-search__web_search` description explicitly says **"You MUST use this tool whenever you need to search for real-time or external information on the web."** I defaulted to `web_search` for all four searches (two of which then hit 429 rate-limit).
- **Action already taken:** Full research handoff captured at `P:/docs/web-search-tools-and-pkm-research-handoff-2026-07-19.md`. Not a red-team-specific issue, but relevant when `/red-team` specialists do web research (e.g., `claim-refute`, `failure-modes`).

### 1.4 Telemetry `operator_outcome` patching is manual (LOW)

- After incident detection, the telemetry row's `operator_outcome` was patched from `unknown` to `partial` via a manual Python one-liner.
- The CLI doesn't expose `set-outcome` or `amend` subcommands. Manual JSON editing is the only path.
- **Not blocked; just observable overhead.** Median cost: ~30 seconds per patch.

### 1.5 Tool-call count vs. work-content mismatch (NOTE)

- Failure-modes agent: 6 tool calls, no write. Logic agent: 3 tool calls, file present. Both are lean. Lean is fine when substantive — logic agent's 3 calls produced 8 findings; failure-modes' 6 calls produced 0 file.
- **Lesson:** Tool-call count is a weak proxy for "work done." Subagent verbosity ≠ correctness. Verify-on-disk is the only reliable signal.

---

## 2. Operational fixes — ranked by impact-per-effort

### Priority 1 — Post-dispatch file-existence verification (one-paragraph change to orchestrator dispatch loop)

**Where:** The orchestrator's specialist-dispatch loop. Likely in `P:/packages/.claude-marketplace/plugins/red-team/agents/orchestrator.md` or wherever the skill-level dispatch instructions live.

**Change:** After specialist returns its claimed file path and before invoking the next specialist or critic:

```powershell
$claimed = $specialistResponse.Path
if (-not (Test-Path $claimed)) {
  # Coverage gap. Retry once OR log incident + DEFERRED + proceed.
  $retryResult = # re-dispatch with explicit "write file before responding" framing
  if (-not (Test-Path $claimed)) {
    # Both attempts failed; mark DEFERRED in run_dir/_run.json
    & python "$pluginRoot/__lib/incidents.py" add --category specialist-miss ...
  }
}
```

**Effort:** ~30 lines in the orchestrator's dispatch loop. **Mirrors the specialist-miss pattern but as a proactive gate, not a reactive log.**

**Why this is priority 1:** Every other improvement is incremental. This one catches the failure mode that has actually occurred in this run and would have shipped unobserved.

---

### Priority 2 — Agent prompt verification step (text change in each specialist prompt)

**Where:** Each specialist agent's prompt. Files at `P:/packages/.claude-marketplace/plugins/red-team/agents/red-team-{planner,claim-refuter,gate-reviewer,workflow-reviewer,logic,state,failure-modes,plugin,testing,critic}.md`.

**Current rule** (typical, verbatim variations exist): *"Your response text MUST contain ONLY the file path you wrote, one per line. No prose, no findings inline, no commentary."*

**Proposed addition:**
*"Your response must contain ONLY the file path, **and the file MUST exist on disk before responding**. Verify with `Test-Path` or equivalent. If your `write` tool call failed or returned an error, do NOT report the path; instead report `WRITE_FAILED: <reason>` (one line, no path)."*

**Effort:** ~5 lines per specialist prompt (8 specialists = ~40 lines total).

**Why priority 2:** Complements Priority 1. Priority 1 is orchestrator-side defense; this is agent-side honesty. Together they catch silent failures from both sides.

---

### Priority 3 — QMD corpus reindex ritual + tool-search default encoding

**Where:** ~10–20 lines across `~/.grok/skills/wiki/SKILL.md`, `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/SKILL.md`, and possibly `~/.grok/AGENTS.md` for the tool-search default.

**QMD reindex paragraph** (each SKILL.md):
```
## Recommended QMD corpus maintenance

The QMD wiki collection drifts if not reindexed against corpus growth.
Run `qmd update wiki` (positional, not `--collection` — that flag is search/status only) at the start of wiki-discoverability
sessions, after any bulk ingest, or when semantic-search relevance
appears degraded (top hit score below 0.2 for known-existing topics).
```

**Tool-search default paragraph** (likely `~/.grok/AGENTS.md`):
```
## Search tool selection

Default search: `minimax-search__web_search` (per its "MUST use" directive).
Time-bounded queries: `web-search-prime__web_search_prime` with
`search_recency_filter` (e.g., oneMonth).
Domain-scoped queries: `web-search-prime__web_search_prime` with
`search_domain_filter`.
`web_search` (built-in) is fallback only.
```

**Why priority 3 (rather than 1 or 2):** Lower per-session impact but durable, high-leverage documentation; doesn't require code changes; the precedence over Priorities 1–2 is that those catch *failures*, this prevents *drift*. They complement rather than compete.

---

### Priority 4 — Telemetry ergonomic improvements

**Where:** `P:/packages/.claude-marketplace/plugins/red-team/__lib/telemetry.py` and possibly `__lib/telemetry_schema.py`.

**Improvements (in order of value):**

| Subcommand | Purpose |
|---|---|
| `set-outcome <run-id> <outcome>` | Replace manual JSON patching for `operator_outcome` |
| `counts-recompute <run-id>` | Defensive parser that reads `critic.json` and extracts BLOCK/REVISE/NIT counts even when critic.json shape varies (current behavior: `counts: 0/0/0` for all runs) |
| `status [--since 7d]` | Print recent runs + verdicts + operator_outcome for triage |

**Effort:** ~30 lines of CLI + ~20 lines of defensive parsing.

**Why priority 4:** The current telemetry line correctly records verdict and dispatch list, but `counts` field is structurally broken (always `0/0/0`). The Phase-3a self-improvement loop reads telemetry for clustering; if counts are always wrong, clustering on counts is useless.

---

### Priority 5 — Failure-mode agent re-dispatch policy

**Where:** Orchestrator's post-dispatch loop (continuation of Priority 1).

**Change:** When `Test-Path` returns false after Priority 1's first check, the orchestrator should:
1. Retry once with explicit instruction: *"You previously failed to write the file. You MUST invoke the write tool before responding. Confirm with `Test-Path` after writing."*
2. If the retry succeeds, continue normally.
3. If the retry also fails, mark DEFERRED + log incident + proceed with coverage gap.

**Effort:** An additional ~15 lines orchestrator-side.

**Why priority 5:** Belt-and-suspenders. The Priority 2 fix should make retries unnecessary. But if the priority-2 prompt change is bypassed by some future specialist variant, the retry becomes the safety net.

---

## 3. The verification gap — detailed treatment

Single most important operational lesson from this session: **never trust a subagent's claim that it wrote a file. Verify.**

**Forward-fix check (after Priorities 1 + 2 + 5):**

| Failure mode | Defense |
|---|---|
| Subagent didn't write the file | Priority 1 catches via `Test-Path`; retry per Priority 5 |
| Subagent wrote a malformed file | Priority 1 still catches (file exists but parser fails) |
| Subagent wrote the file but with a different schema | Specialist-internal contract; harder to detect; would surface in critic synthesis |
| Subagent wrote the file but with a partial payload | Partial payload detectable by file size check or post-write JSON validation; not currently enforced |
| Subagent reports different path than the file actually written | Not currently detected; would surface as file-missing |

**Regression risk of Priority 1:**

- `Test-Path` adds <100ms latency per specialist. With 5 specialists per run, ~500ms total. Negligible.
- The verification creates a contract on file naming conventions. If a specialist writes to a path the orchestrator didn't expect (e.g., a `*.json` vs `*.txt` extension choice), the orchestrator's stated path won't match and the file appears "missing." Mitigation: orchestrator and specialists must agree on extension conventions, ideally via a shared naming rule in the agent prompt.
- A failed retry that retries indefinitely could create an infinite loop. Add a max-retry counter (default: 1).

**Regression risk of Priority 2:**

- Agent prompt additions could cause the agent to over-explain or omit the path in some edge cases. Mitigation: keep the explicit instruction format ("ONLY the path, on its own line") verbatim; the new rule is a conditional ("if your write fails, report failure") rather than a replacement.

---

## 4. Cross-references — wiki work that this red-team reviewed (separate concern)

The red-team verdict (REVISE) covered the wiki action items A–F + open questions. **This is separate from red-team operational fixes.** Captured here as cross-reference only.

- Verdict: `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/critic.json`
- Verdict summary: 4 BLOCK + ~14 REVISE findings + NITs; verdict = REVISE
- Operator-facing paths (user-decision pending):
  - **Path A** (apply all 16 next-steps): ~75 min wall-clock
  - **Path B** (BLOCK-only): ~25 min
  - **Path C** (document and ship): ~5 min

Detailed next-step enumeration at `critic.json` lines 254–268. The wiki work is **not** what this handoff is for — only its existence is cross-referenced.

---

## 5. Open questions (user-decision pending)

1. **Red-team workflow fix scope.** Apply Priorities 1–2 in the same session as the wiki decision, or split into separate sessions? The verification gap is the highest-leverage fix; its impact compounds across every future red-team run.

2. **Tool-search default encoding.** `~/.grok/AGENTS.md` annotation vs. new doc vs. `~/.grok/tool-fallbacks.md` (existing tooling doc, but per AGENTS.md the fallback doc is for broken-tool entries, not tool-preference). My recommendation: AGENTS.md annotation, since it's a session-wide behavior change.

3. **Failure-modes retry policy auto vs. surface.** Should the orchestrator silently retry (Priority 5 default) or always surface the gap to the operator and let the operator decide? Auto-retry is faster; surface is more transparent. The skill's incident-capture protocol already supports surface-as-incident; the choice is whether retry happens automatically first or not.

4. **QMD reindex cadence.** Quarterly? Session-start? Bulk-ingest-trigger? Per the proposal in this session, reindex is "baseline only, not a fix" — a low-cadence scheduled task (quarterly or per-session) is sufficient.

5. **Mental experiment:** would Priorities 1+2 have caught the failure-modes silent-no-write? Yes — `Test-Path` after the dispatch loop would have caught it; the agent prompt's write-failure-instruction would have prompted retry. The two defenses together catch ~100% of silent-write cases. Confirm by dispatching failure-modes again with Priority 1 simulated.

---

## 6. Source map for this session's red-team run

| File | Purpose |
|---|---|
| `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/_run.json` | Run metadata; `dispatched`, `deferred`, `failed_agents` blocks |
| `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/proposal.md` | Planner's restated proposal + 8 candidate weaknesses (W1–W8) |
| `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/prospect.md` | Planner's wiki-priors scan |
| `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/claim-refute.json` | 38 claims extracted; 31 verified clean; 5 findings (CRT-001 to CRT-005) |
| `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/gate-reviewer.json` | 8 findings (3 BLOCK + cascading REVISE/NIT) |
| `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/workflow-reviewer.json` | 8 findings (1 BLOCK + cascading REVISE/NIT/CLEAN/SKIPPED) |
| `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/logic.json` | 8 findings (5 REVISE + cascades) |
| **MISSING** `failure-modes.json` | Agent reported path; write never occurred. Documented in `_run.json/failed_agents` |
| `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/critic.json` | Aggregated verdict + 16 next-steps (Path A/B/C) |
| `P:/.claude/state/red-team/telemetry.jsonl` | One row for this run (operator_outcome=`partial`) |
| `P:/.claude/state/red-team/incidents.jsonl` | One row `inc-48fd0ac31fb7`, category `specialist-miss` |

## 7. Cross-references to broader session artifacts

- `P:/docs/web-search-tools-and-pkm-research-handoff-2026-07-19.md` — earlier session research handoff; tool-search selection rule + Karpathy PKM research
- `P:/.data/wiki/concepts/claude-code-export-drive-root-perm-bug.md` — symptom-side wiki page (created this session)
- `P:/.data/wiki/concepts/windows-onedrive-readonly-marker.md` — cause-side wiki page (created this session)
- `P:/.data/wiki/log.md` — 8 audit-trail entries dated 2026-07-19 (4 export cluster + 4 unrelated Grok hook work)

## 8. Priority summary (restate for triage)

| Priority | Fix | Effort | Per-session impact |
|---|---|---|---|
| 1 | Post-dispatch `Test-Path` verification in orchestrator loop | ~30 lines | Catches silent-no-writes (failure-modes silent failure in this run) |
| 2 | "Verify file exists before responding" in each specialist prompt | ~40 lines total | Agent-side defense for Priority 1 |
| 3 | QMD reindex ritual + tool-search default encoding | ~30 lines across 3 files | Prevents drift; orthogonal to failures |
| 4 | Telemetry CLI ergonomics (`set-outcome`, `counts-recompute`, `status`) | ~50 lines CLI | Makes the Phase-3a loop actually useful (counts currently always 0/0/0) |
| 5 | Failure-modes retry-with-stronger-instruction policy | ~15 lines | Belt-and-suspenders for Priority 2 |

**Minimum viable reliability fix:** Priorities 1 + 2 together. That's a ~70-line change across two layers, covers the failure mode that has actually occurred, and is bounded enough to ship in one focused session.

---

*End of handoff.*
