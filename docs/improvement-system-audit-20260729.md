# Improvement-System Audit — 2026-07-29

**Task:** Audit the agentic-development environment as a continuous-improvement system against the loop `SENSE → CLASSIFY → DISCOVER → CHOOSE → EXECUTE → VERIFY → LEARN → RETIRE`.

**Method:** Read-only investigation. Every material claim cites repository evidence (file:line, artifact, command output). No behavior or functionality was modified. Two read-only `explore` subagents traced the LEARN/RETIRE and VERIFY/hook clusters in parallel; their evidence is cited inline.

**Scope mechanisms:** `/aar`, `/debrief`, `/tp`, `/close`, `/harvest`, `/todo`, `/handoff`, `/go`, `/check`, `/review`, plus `/gto` and `/rns` (verified absent — see §13).

---

## 1. Executive verdict

**IMPROVEMENT_LOOP_PARTIAL**

The environment has a dense, mechanically-sophisticated set of improvement mechanisms — arguably over-instrumented for a single operator. The **front half** of the loop (SENSE → DISCOVER → EXECUTE) works well: failures produce signals, root causes get diagnosed and documented, and code gets written. The **back half** is fragmented in three specific ways:

1. **VERIFY receipts are unreliable.** `/check` writes its verdict file (`check-state.md`) via the parent LLM, not a script. Only ~3 of ~24+ `/check` runs produced the receipt. `close_accounting.py:530-587` reads it, so a `/check FAIL` without the receipt is invisible to `/close` — the session can be declared closed while a known verification failure sits unrecorded. This is the single highest-impact gap.

2. **LEARN outputs lack reliable consumers.** AAR opportunities, harvest obligations, and `/tp` cross-domain notices are all *produced* but their *pickup* is memory-dependent. There is no opportunity-status ledger, no automatic dispatcher from OPP → execution, and the documented CROSS-DOMAIN NOTICES → harvest pipeline is unwired (the suggestion file `pending/analyze_session_patterns.json` sits unconsumed; `harvest doctor` counts `*.tmp` temps, not `*.json` suggestions).

3. **Authority overlaps without coordination.** `/aar` vs `/debrief` (retrospective), `/check` vs `/review` vs `grok-verify` (verification), `/harvest` vs `/todo` vs `/handoff` (work tracking) — each pair overlaps, and the pairs are documented as consolidation candidates (OPP-06) that have sat open for 1+ week. The operator carries the cognitive load of remembering which to invoke.

**The loop is not closed.** It is a collection of well-engineered stages connected by memory-dependent handoffs. The infrastructure to close it exists (stores, receipts, scanners) but the producer→consumer edges are unwired at the points that matter most: verification receipts, opportunity pickup, and obligation realization.

**Not a "too few mechanisms" problem.** The opposite: 45+ user-facing commands, 697 wiki concepts, 205 handoff directories (174 open). The operator is generating new work faster than it's consumed — a pattern the workspace itself documents (`research-to-execution-ratio-self-reinforcing-pattern.md`). The lever is **connecting existing mechanisms more narrowly**, not building new ones.

---

## 2. Environment and authority map

### Repository state

| Field | Value | Receipt |
|---|---|---|
| Root | `P:\` (multi-root workspace) | — |
| Branch | `main` | `git rev-parse --abbrev-ref HEAD` |
| HEAD | `96afa86` | `git rev-parse --short HEAD` |
| Dirty | 41 files (mix of modified, deleted, untracked) | `git status --porcelain` |
| Recent activity | 50+ commits 2026-07-23 → 2026-07-29 | `git log --since="2026-07-23"` |

### Installed skill roots (relevant)

| Scope | Path | Count (relevant subset) |
|---|---|---|
| Grok user | `~/.grok/skills/` | 44 skills (incl. aar, close, debrief, harvest, todo, tp, go, check, review, handoff, wiki, why, why-old) |
| Grok bundled | `~/.grok/bundled/skills/` | 22 skills (code-review, review, implement, …) |
| Workspace agent | `P:/.agents/skills/` | 16 skills (preflight, skill-prune, recover, …) |
| Installed plugins | `~/.grok/installed-plugins/` | 6 (superpowers, episodic-memory, firecrawl, …) |

### Authoritative stores (source-of-truth vs derived cache)

| Store | Path | Type | Evidence |
|---|---|---|---|
| Handoffs | `P:/docs/handoffs/<topic>-<date>/HANDOFF.md` | **Source of truth** (plain files) | 205 dirs, 174 open, 20 closed |
| Harvest events | `P:/.data/harvest/events/<ULID>.json` | **Source of truth** (immutable, event-sourced) | 28 events, 12 OPEN / 3 COLLECTED / 2 CLOSED |
| Harvest claims | `P:/.data/harvest/claims/<ULID>.claim` | **Source of truth** (concurrency authority) | 11 claims |
| Harvest pending (temps) | `P:/.data/harvest/pending/*.tmp` | Derived (atomic-write staging) | 0 files |
| Harvest pending (suggestions) | `P:/.data/harvest/pending/*.json` | **Intended source** — actually **dead-lettered** | 1 file (`analyze_session_patterns.json`), unconsumed |
| Wiki concepts | `P:/.data/wiki/concepts/*.md` | **Source of truth** | 697 files |
| AAR reports | `P:/docs/aars/aar-<session>-<date>.md` | **Source of truth** (durable copy) | 1 file |
| AAR run dirs | `~/.grok/skills/aar/.artifacts/<sid>/` | Derived (run-time artifacts) | 1 dir |
| Close evidence | `P:/.artifacts/close-evidence/<sid>.json` | **Source of truth** (SHA-256-bound ledger) | 12 session ledgers + test fixtures |
| Close attempt receipts | `P:/.artifacts/close-evidence/<sid>/attempt-*.json` | Derived (per-attempt) | ~12 dirs |
| /check receipts | `P:/.artifacts/<term>/grok-check/<ts>/check-state.md` | **Source of truth** (verdict) | 3 files of ~24+ runs |
| /tp critique log | `P:/.data/telemetry/tp-critique-log.jsonl` | **Source of truth** (append-only) | 14 entries, 2026-07-24→07-28 |
| Tasks (Claude compat) | `~/.claude/tasks/` | Source of truth (cross-host) | project-main-tasks + many session dirs |
| Telemetry: llm_cli_performance | `P:/.data/telemetry/llm_cli_performance.jsonl` | **DEAD** (stale 2026-06-01, no producer) | last entry 2026-04-02 |
| Telemetry: spawn_failures | `P:/.data/telemetry/spawn_failures.jsonl` | **EMPTY** (0 bytes, producer invocation memory-dependent) | — |

### Unresolved authority conflicts

1. **`/aar` vs `/debrief`** — both are retrospective skills. `/aar` produces a completion receipt consumed by close; `/debrief` produces nothing durable and close cannot detect it (close_accounting.py:1340 truncated comment: "Debrief detection requires…"). OPP-06 proposes consolidation; status `NEEDS_USER_DECISION`, open 1+ week.
2. **`/check` vs `/review` vs `grok-verify`** — three verification mechanisms with overlapping contracts. `/check` and `/review` auto-connect (check Step 6.2 fires review on load-bearing triggers), but `grok-verify` (a `/go` sub-skill) is a third path with no receipt consumption.
3. **`/harvest` vs `/todo` vs `/handoff`** — three work-tracking stores. Documented boundary (harvest = recover unrealized value; todo = what to do next; handoff = continuation), but harvest obligations and handoff obligations overlap and neither has a consumer that reconciles them.
4. **AAR artifact paths** — the AAR skill writes to `~/.grok/skills/aar/.artifacts/<sid>/`; close detects runtime AARs at `P:/.artifacts/grok-aar/<term>/<ts>/`. These resolve via `rglob("completion_receipt.json")` (close_accounting.py:1355), so the consumer works, but the two-path split contributed to a misleading "22 close runs : 1 AAR" ratio.

---

## 3. Mechanism inventory

This is the consolidated inventory from direct code tracing + two read-only subagents. "Consumer" distinguishes **automatic** (wired in code) from **memory-dependent** (operator/LLM must remember to look).

### 3.1 `/close` — session close-out orchestrator

| Field | Value |
|---|---|
| Purpose | Scan all evidence, resolve 14 gates, emit close summary; auto-invoke `/aar` at retrospective gate |
| Invocation | `python ~/.grok/skills/close/__lib/close_runner.py --session <id> --variant standard` |
| Trigger | Manual (operator), but fires `/aar` automatically at the retrospective gate |
| Inputs | handoffs, wiki, git commits, AAR receipts, check receipts, temp files, git state, continuation coverage, friction detector |
| Input authority | session_id (from context), per-session write-path extraction from `updates.jsonl` |
| Scope | current session (filtered by `current_session_id`) |
| Output | `P:/.artifacts/close-evidence/<sid>.json` (SHA-256-bound ledger); close summary |
| Output schema | JSON: schema_version, session_id, variant, generated_at, counts, gates(14), check_receipts, persistence_checks |
| Consumers | `validate_close_receipt.py` (receipt validator); operator reads summary |
| Consumption | automatic (validator), memory-dependent (operator follow-through) |
| Freshness | attempt receipt freshness check (rejects >600s old or future-dated) |
| Failure behavior | CLOSE INCOMPLETE on scanner timeout/malformed/gate-fail; blocks all clean-close claims |
| Evidence of invocation | 12 session attempt-receipt dirs in close-evidence/ |
| Evidence of effect | git log shows handoff/wiki/commit activity consistent with close runs |
| Burden | Low per-invocation, but operator must remember to invoke; retrospective gate auto-fires /aar |
| Overlap | consumes /aar, /check, /wiki, /handoff (by design — orchestrator) |

### 3.2 `/harvest` — recover unrealized value

| Field | Value |
|---|---|
| Purpose | Event-sourced obligation tracking with claim-based concurrency |
| Invocation | `python ~/.grok/skills/harvest/scripts/harvest.py <cmd>` |
| Trigger | Manual; close SKILL.md:130 says "run harvest show --top 10" before final summary |
| Inputs | operator-added items (ADD events); `scan-handoffs` scans `P:/docs/handoffs/` |
| Output | `P:/.data/harvest/events/<ULID>.json` (immutable, fsync'd, os.replace'd) |
| Output schema | per-event JSON with parent_event_id causal chain + claim files |
| Consumers | operator (memory-dependent); `harvest show` in close (prompt-driven) |
| Consumption | **memory-dependent** — no automatic dispatcher from OPEN item → action |
| Freshness | `evidence_status()` checks last_verification staleness (14d) |
| Failure behavior | claim-based concurrency (exit 6 on conflict); quarantine on corruption |
| Evidence of invocation | 28 events, 17 items; doctor ran this session |
| Evidence of effect | 3 COLLECTED items; **12 OPEN items all unarmed (hint-only, no verification)** |
| Burden | Moderate — 9 subcommands; operator must remember capture/arm/verify/collect lifecycle |
| Overlap | overlaps /todo (work tracking), /handoff (obligations). Documented boundary holds but both feed the same backlog |

**Critical gap:** `scan-handoffs` (harvest.py:463-525) only **prints suggestions** — it does not seed harvest items. And the documented "Inter-skill state sharing" feature (SKILL.md:240-260) where `/aar`, `/why`, `/tp` write to `pending/<skill>.json` and `doctor` reads them is **unwired**: `cmd_doctor` globs `pending/*.tmp` (store.py:50, harvest.py:pending glob), not `*.json` suggestions. The one suggestion file (`analyze_session_patterns.json`) is dead-lettered.

### 3.3 `/aar` — after-action review

| Field | Value |
|---|---|
| Purpose | 9-phase continual-improvement review with typed episodes, value accounting, opportunity landscape |
| Invocation | `/aar [target | session | <path> | --lite]`; `__lib/completion_receipt.py:finalize_aar_run` |
| Trigger | Manual; **auto-invoked by /close** retrospective gate |
| Output | `~/.grok/skills/aar/.artifacts/<sid>/{_run.json, aar-report.md, completion_receipt.json}`; durable copy at `P:/docs/aars/` |
| Output schema | completion_receipt: status, headline_lessons[], verdict, session_id, aar_type, degree_of_completion, key_findings[], operator_signals{pushback_count,…} |
| Consumers | **automatic**: `close_accounting.py:scan_retrospective` (lines 1336-1397) globs `completion_receipt.json` + `_run.json`, validates via `_validate_aar_completion` |
| Consumption | automatic for gate satisfaction; **memory-dependent for OPP-N opportunities** (no pickup dispatcher) |
| Freshness | receipt session_id binding |
| Evidence of invocation | 1 run dir (019fa48a), 1 durable report (019fa9aff) |
| Evidence of effect | the 019fa9aff AAR's 3 lessons and 4 opportunities — **all DEFER/INVESTIGATE/MONITOR, 0 ACT_NOW, 0 wiki-promoted** (Phase 9.5) |
| Burden | High per-invocation (full session review); justified by gate integration |
| Overlap | overlaps `/debrief` (OPP-06) |

**Receipt → close edge is WIRED AND WORKING.** The 22:2 close-to-AAR ratio is partly artifact-path mismatch (close finds runtime AARs at a different path) and partly genuine gate-skip on no-substantive-work sessions. Not a break.

### 3.4 `/debrief` — smart session retrospective

| Field | Value |
|---|---|
| Purpose | 5-lens fan-out retrospective (root causes, code quality, workflow friction, knowledge gaps, patterns) |
| Invocation | `/debrief [--light | --standard | --deep | --wiki | --quick]` |
| Trigger | Manual |
| Output | **NONE durable.** Directory contains only `SKILL.md` — zero scripts, zero output targets |
| Output schema | inline-only; optional Phase 5a wiki auto-save (self-applied LLM gate, not externally validated) |
| Consumers | **None automatic.** close_accounting.py:1340 cannot detect /debrief |
| Evidence of invocation | **Zero artifacts anywhere** in the audited workspace |
| Burden | Moderate — adds a command the operator must distinguish from /aar |
| Overlap | fully overlaps /aar; documented as OPP-06 consolidation candidate (open, NEEDS_USER_DECISION) |

### 3.5 `/tp` — thought-partner

| Field | Value |
|---|---|
| Purpose | critique + exploration modes; CROSS-DOMAIN NOTICES pass |
| Invocation | `/tp [quick | check | session | explore | ...]` |
| Trigger | Manual; auto-invoked by /close Step 4 (`/tp session`) |
| Output | `P:/.data/telemetry/tp-critique-log.jsonl` (14 entries); CROSS-DOMAIN NOTICES → `P:/.data/harvest/pending/tp.json` |
| Output schema | critique log: {id, timestamp, target, verdict, horizon, domains[], findings[], model, outcome} |
| Consumers | `/tp` Step 0.5 (reads patterns via `auto --limit 20`); `/skill-dev` Mode 1 (evidence sampling). **NO automatic feedback** to skill evolution/routing |
| Consumption | read-for-display only; no action consumer |
| Evidence of invocation | 14 entries, 2026-07-24→07-28 |
| Evidence of effect | verdict distributions computed; **no skill has been retired/rerouted based on them** |
| Burden | Moderate — 1320 lines, many modes |
| Overlap | overlaps /aar, /debrief (retrospective); overlaps /red-team (adversarial) |

**CROSS-DOMAIN NOTICES → harvest is unwired.** SKILL.md:367-370 documents the write to `pending/tp.json`; no grep evidence of any consumer reading it. The structural gate for research-to-execution (added 2026-07-29) is prompt-layer only (per its own falsifier).

### 3.6 `/check` — multi-concern verification

| Field | Value |
|---|---|
| Purpose | PASS/FAIL verdict with per-concern verifier subagents |
| Invocation | `/check` (orchestrator spawns verifiers); writes `$runDir/check-state.md` |
| Trigger | Manual; **no auto-fire from /go** (prose recommendation only, go SKILL.md:770-779) |
| Output | `P:/.artifacts/<term>/grok-check/<ts>/check-state.md` |
| Output schema | `**Session:** <id>`; `**Verdict:** CHECK PASS (N/M verifiers)`; ## Verifiers, ## Test results, ## Issues |
| Consumers | **automatic**: `close_accounting.py:scan_check_receipts` (530-587) rglobs check-state.md, parses verdict regex; `validate_close_receipt.py:140-150` requires it |
| Consumption | automatic IF the receipt exists; **the receipt is written by the parent LLM, not a script** |
| Evidence of invocation | ~24+ grok-check run dirs; **only 3 have check-state.md** |
| Evidence of effect | close reads the 3 that exist; ~21 runs are invisible to close |
| Burden | Moderate |
| Overlap | `/check` Step 6.2 auto-fires `/review` on load-bearing triggers (wired) |

**Critical gap:** No script in `~/.grok/skills/check/__lib/` writes `check-state.md`. Grep for `check-state` writer in `__lib/` returned 0 matches. The receipt is memory-dependent on the orchestrator LLM. A `/check FAIL` that doesn't write the receipt is invisible to the entire close loop.

### 3.7 `/review` — fresh-eyes defect hunting

| Field | Value |
|---|---|
| Purpose | Verified findings on diff/branch/PR/package |
| Invocation | `/review`; writes `$runDir/{findings.json, FINDINGS.md}` |
| Trigger | Manual; auto-fired by /check Step 6.2 |
| Output | `P:/.artifacts/<term>/grok-review/<slug>/<ts>/{findings.json, FINDINGS.md}` |
| Output schema | findings.json: findings[], suppressed[], overall_correctness, severity_counts |
| Consumers | **None automatic for fixing.** close_accounting.py and validate_close_receipt.py do NOT reference FINDINGS.md (grep returned 0 matches) |
| Consumption | **memory-dependent** — operator reads FINDINGS.md and acts |
| Evidence of invocation | ~20+ FINDINGS.md files |
| Evidence of effect | git log shows "fix(review): address N findings" commits — **but no tracking of fixed-vs-open** |
| Burden | Moderate |
| Overlap | /check auto-fires it; /review → close is NOT wired |

### 3.8 `/todo` — what should I do next

| Field | Value |
|---|---|
| Purpose | ADHD-friendly prioritized action list; orchestrates coverage_scan + close_accounting + friction_detector + email |
| Invocation | `/todo [--review | --deep | --email-only]` |
| Trigger | Manual (session start or "lost the thread") |
| Output | inline prioritized list (5 tiers); no durable artifact |
| Consumers | operator (immediate) |
| Evidence of invocation | uses friction_detector.py (todo_format.py:162), close_accounting.py (SKILL.md:84) |
| Burden | Low per-invocation; justified as the reorientation entry point |
| Overlap | consumes harvest/handoffs/wiki; does NOT consume harvest items directly (only via close_accounting) |

### 3.9 `/handoff` — work handoff

| Field | Value |
|---|---|
| Purpose | Durable document for next-session continuation; auto-update mode |
| Invocation | `/handoff [<topic> | <report> | close <path> | list]` |
| Trigger | Manual |
| Output | `P:/docs/handoffs/<topic>-<date>/HANDOFF.md` |
| Output schema | YAML chain header (thread_id, parent_handoff_path, current_session_id, status, accurate_as_of_head) + 16 mandatory fields |
| Consumers | operator (next session); close (scans for current_session_id match); list_handoffs.py |
| Consumption | memory-dependent (next session must invoke /handoff list or be pointed); `/handoff continue` is v0.2-deferred |
| Evidence of invocation | 205 dirs; 174 open, 20 closed, rest mixed |
| Evidence of effect | high generation rate (operator confirmed: "they're all new") |
| Burden | Low per-write, but 174 open items is a triage burden |
| Overlap | harvest scan-handoffs reads these; continuation_coverage extracts candidates |

### 3.10 `/go` — engineering orchestrator

| Field | Value |
|---|---|
| Purpose | discovery → execute → verify wiring |
| Invocation | `/go <task>` (plain language) |
| Trigger | Manual |
| Output | state file `P:/.artifacts/<term>/<pkg>-state.md`; Execution Status block in plan file |
| Consumers | self (resume state); operator |
| Verify phase | H6 fires `grok-verify` + `check-work` (sub-skills, NOT /check). `/check` is a **prose recommendation** after PASS (go SKILL.md:770-779), not auto-fired |
| Evidence of effect | state files exist; git log shows /go-driven commits |
| Burden | High horsepower; justified for multi-step engineering |
| Overlap | /go → /check → /close is a 3-step operator-driven chain; only first step automatic |

### 3.11 Absent mechanisms

| Mechanism | Status | Evidence |
|---|---|---|
| `/gto` | **Does not exist** at any scope | `Get-ChildItem` for `gto*` in ~/.grok/skills, P:/.grok/skills, P:/.agents/skills returned empty |
| `/rns` | **Not installed at Grok scope** | exists only in cc-skills-analysis Claude cache; catalog entry at skill-catalog.md:738 |
| lazy-closure-debt | No such mechanism found | grep for "lazy-closure" returned no matches |

### 3.12 Skill graph — machine-readable

The graph below maps every producer→consumer edge traced in this audit. It is the structural view that §4 (coverage matrix) evaluates and §6 (broken-edge analysis) diagnoses. Format: compact edge list + stage-node registry. Another LLM can parse this cold to reconstruct the loop topology without re-reading the inventory.

**Edge-type legend:**
- `AUTO` — wired in code: producer fires, consumer reads automatically.
- `MEM` — memory-dependent: operator/LLM must invoke to produce or consume.
- `BROKEN` — producer exists and writes an artifact, but no consumer reads it.
- `STALLED` — edge works mechanically, but output accumulates without realization.

**Stage-node registry** (`id | mechanism | loop stage(s) | role`):

```
N01 | active_surface_snapshot | SENSE          | SessionStart hook; enforcement-surface snapshot
N02 | friction_detector       | SENSE          | Repeated-friction pattern detector (code module)
N03 | opportunity_scan        | DISCOVER       | Harvest/handoff/capability-gap combiner (code module)
N04 | /tp                     | SENSE,DISCOVER | Critical-friend critique + exploration
N05 | tp_critique_log         | LEARN          | Append-only critique history (store)
N06 | /aar                    | LEARN          | 9-phase after-action review with receipts
N07 | /debrief                | LEARN          | 5-lens retrospective (zero durable output)
N08 | /close                  | VERIFY,LEARN   | 14-gate session close orchestrator
N09 | /check                  | VERIFY         | Multi-concern PASS/FAIL verification
N10 | /review                 | VERIFY         | Fresh-eyes defect hunting
N11 | /go                     | EXECUTE,VERIFY | Engineering orchestrator (discovery→execute→verify)
N12 | grok_verify             | VERIFY         | /go internal verify sub-skill (no receipt)
N13 | /harvest                | SENSE,CHOOSE   | Unrealized-value obligation tracker (event store)
N14 | /todo                   | CHOOSE         | ADHD-friendly prioritized action list
N15 | /handoff                | LEARN,RETIRE   | Durable continuation documents
N16 | /skill_prune            | RETIRE         | Stale-skill detector (propose-only)
N17 | /skill_dev              | RETIRE         | Skill contribution measurer
```

**Edge list** (`from → to | via artifact | type | note`):

```
# --- SENSE edges ---
N01 active_surface_snapshot → session LLM  | active-surface.last.md      | AUTO   | SessionStart hook fires every session
N02 friction_detector       → N08 /close   | FrictionCandidate objects   | AUTO   | continuation_coverage.py:996 imports
N02 friction_detector       → N14 /todo    | FrictionCandidate objects   | AUTO   | todo_format.py:162 imports
N02 friction_detector       → N04 /tp      | —                          | MEM    | /tp mentions but never auto-invokes

# --- DISCOVER edges ---
N03 opportunity_scan        → N04 /tp      | stdout                      | MEM    | fires ONLY in /tp explore (SKILL.md:529)
N04 /tp                     → N13 /harvest | pending/tp.json suggestions | BROKEN | SKILL.md:367 writes; NO consumer reads it
N06 /aar                    → OPP-N items  | AAR report                  | AUTO   | Phase 6/7 produces opportunities
OPP-N items                 → N11 /go      | handoff (sometimes)         | STALLED| no pickup dispatcher; OPP-01 open, not started

# --- VERIFY edges ---
N08 /close                  → N06 /aar     | retrospective gate          | AUTO   | close auto-invokes /aar (SKILL.md:155)
N09 /check                  → check-state  | check-state.md              | BROKEN | written by LLM not script; ~3 of 24+ runs
check-state                 → N08 /close   | scan_check_receipts         | AUTO   | close reads it (close_accounting.py:530)
N09 /check                  → N10 /review  | Step 6.2                    | AUTO   | auto-fires on load-bearing triggers
N10 /review                 → FINDINGS.md  | findings.json/FINDINGS.md   | AUTO   | every run writes structured findings
FINDINGS.md                 → N08 /close   | —                           | BROKEN | close does NOT read FINDINGS.md
N11 /go                     → N12 grok_v   | H6 pack                     | AUTO   | /go fires its own verify sub-skill
N12 grok_verify             → check-state  | —                           | BROKEN | writes no check-state-compatible receipt
N11 /go                     → N09 /check   | —                           | MEM    | prose recommendation only (go SKILL.md:770)

# --- LEARN edges ---
N06 /aar                    → receipt      | completion_receipt.json     | AUTO   | finalize_aar_run writes SHA-256-bound receipt
receipt                     → N08 /close   | scan_retrospective          | AUTO   | close reads + validates (close_accounting.py:1336)
N06 /aar                    → wiki         | Phase 9.5 promotion         | MEM    | operator decides; most AARs promote 0 concepts
N07 /debrief                → (nothing)    | —                           | BROKEN | zero durable artifacts; close cannot detect it
N04 /tp                     → N05 log      | tp-critique-log.jsonl       | AUTO   | Step 3 writes every critique
N05 log                     → N04 /tp      | Step 0.5 patterns           | AUTO   | reads own history at session start
N05 log                     → N17 skill_d  | Mode 1 evidence             | MEM    | reads for MEC analysis; no action feedback

# --- CHOOSE edges ---
N13 /harvest                → operator     | harvest show ranking        | MEM    | tiered ranking exists but no auto-dispatch
N13 OPEN items              → action       | arm/verify/collect          | STALLED| 12 OPEN items, ALL unarmed (hint-only)
N08 /close                  → N13 /harvest | "show --top 10" prompt      | MEM    | close SKILL.md:130 instructs but doesn't enforce
N14 /todo                   → operator     | 5-tier action list          | MEM    | immediate consumption; no durable artifact

# --- RETIRE edges ---
N15 /handoff                → handoffs     | HANDOFF.md                  | AUTO   | written to docs/handoffs/
handoffs                    → N08 /close   | session match scan          | AUTO   | close scans for current_session_id
handoffs                    → N13 /harvest | scan-handoffs               | AUTO   | harvest reads but only PRINTS suggestions
N16 /skill_prune            → operator     | propose-only                | MEM    | no auto-trigger; monthly cadence (prompt)
N17 /skill_dev              → N16 skill_p  | —                           | BROKEN | the two retirement skills never coordinate
```

**Mermaid diagram** (loop-stage flow with edge types; render for visual reference):

```mermaid
flowchart LR
    subgraph SENSE
        N01[active_surface<br/>hook]
        N02[friction_detector]
    end
    subgraph DISCOVER
        N03[opp_scan]
        N04[/tp]
    end
    subgraph CHOOSE
        N13[/harvest]
        N14[/todo]
    end
    subgraph EXECUTE
        N11[/go]
    end
    subgraph VERIFY
        N09[/check]
        N10[/review]
        N12[grok_verify]
    end
    subgraph LEARN
        N06[/aar]
        N07[/debrief]
        N05[critique_log]
    end
    subgraph RETIRE
        N15[/handoff]
        N16[/skill_prune]
    end
    N08[/close - 14 gates]

    N01 -->|AUTO| N08
    N02 -->|AUTO| N08
    N02 -.->|MEM| N04
    N03 -.->|MEM| N04
    N04 ===>|BROKEN<br/>tp.json| N13
    N06 -->|AUTO receipt| N08
    N08 -->|AUTO fires| N06
    N08 -.->|MEM| N13
    N09 ===>|BROKEN<br/>check-state| N08
    N09 -->|AUTO| N10
    N10 ===>|BROKEN<br/>FINDINGS| N08
    N11 -->|AUTO| N12
    N12 ===>|BROKEN<br/>no receipt| N09
    N11 -.->|MEM| N09
    N04 -->|AUTO| N05
    N05 -->|AUTO| N04
    N07 ===>|BROKEN<br/>no output| N08
    N11 -->|operator| EXEC
    EXEC --> N11
    N15 -->|AUTO| N08
    N15 -->|AUTO read| N13
    N16 -.->|MEM propose| RETIRE
```

**Reading the graph:**
- Solid arrows (`-->`) = `AUTO` edges that work.
- Dotted arrows (`-.->`) = `MEM` edges that require operator/LLM to fire.
- Triple arrows (`===>`) = `BROKEN` edges where the producer writes but no consumer reads.

**BROKEN-edge count: 8** (the triple arrows). These are the gaps that prevent the loop from closing. They cluster in VERIFY (3: check-state, FINDINGS, grok-verify) and LEARN (3: /debrief, tp.json→harvest, OPP-N→/go) and RETIRE (2: harvest suggestions, skill-dev↔skill-prune). The single highest-impact fix is the check-state.md producer (Intervention 1, §9) — it converts the loop's most-traversed BROKEN edge to AUTO.

---

## 4. Eight-stage coverage matrix

| Stage | Mechanisms present | Coverage | Authority | Blind spots | Duplicated responsibility | Evidence quality | Outputs have reliable consumers? |
|---|---|---|---|---|---|---|---|
| **1. SENSE** | friction_detector, active_surface_snapshot, tp-critique-log, spawn_failures, llm_cli_performance, AAR operator_signals | **Strong** for session-internal friction; **weak** for cross-session telemetry (2 dead/empty telemetry stores) | friction_detector: code; active_surface: SessionStart hook; telemetry: memory-dependent invocation | Dead telemetry (llm_cli_performance); empty spawn_failures | friction_detector vs tp Step 0b (different pattern sets) | High (code-traced) | friction_detector → /close, /todo (yes); telemetry → none (no) |
| **2. CLASSIFY** | harvest operations (RESCUE/GENERALIZE/CONVERT/COMPLETE/RETIRE/COMPOUND), handoff_type, AAR episode types, continuation_coverage dispositions | **Moderate** — taxonomy exists but is applied inconsistently (174 handoffs all "investigation" type) | harvest store (code); handoff frontmatter (LLM) | No classification applied to the 174 open handoffs' triage priority | harvest operations vs handoff_type (parallel taxonomies) | Medium | harvest → operator (memory-dependent) |
| **3. DISCOVER** | /tp explore + workspace_opportunity_scan, /aar opportunity landscape, harvest doctor pattern-candidates, harvest scan-handoffs, continuation_coverage | **Strong** for failure-driven; **gated** for opportunity-driven (workspace_opportunity_scan only fires in /tp explore) | tp SKILL.md (prompt); opportunity_scan (code, manual invocation) | opportunity_scan not auto-fired; harvest suggestions dead-lettered | /aar opportunities vs /tp explore vs harvest scan-handoffs (3 discovery paths) | High (code-traced) | opportunity → operator (memory-dependent) |
| **4. CHOOSE** | /todo prioritized list, harvest ranking (tiered), handoff list_handoffs.py, /tp /rns-style ranking (absent) | **Fragmented** — 3+ prioritization paths, none authoritative | /todo (LLM synthesis); harvest ranking (code); handoff list (code) | No single source of "what's the highest-value next action"; /rns not installed | /todo vs harvest ranking vs handoff list (3 overlapping views) | Medium | /todo → operator (immediate, good) |
| **5. EXECUTE** | /go, /refactor, direct editing, auto-commit policy | **Strong** — git log shows 50+ commits in 7 days | operator + /go orchestrator | None significant | /go vs direct editing (acceptable — /go for multi-step) | High (git log) | commits → git (yes) |
| **6. VERIFY** | /check, /review, grok-verify, close_accounting receipt validator, validate_stop_narrative, friction_detector edit-then-verify detection | **Partially broken** — check-state.md written only ~12% of runs; review findings not tracked | check/review (LLM-written receipts); close (code-reads receipts) | check-state.md producer gap; review→fix tracking absent | /check vs /review vs grok-verify (3 verify paths, 1 receiptless) | High (code-traced) | check-state.md → close (yes IF exists); review findings → none (no) |
| **7. LEARN** | /aar (9-phase), /debrief (5-lens), AAR completion receipts, wiki promotion, tp-critique-log patterns | **Works at prompt-layer**; /debrief produces nothing durable; OPP pickup is memory-dependent | /aar (code-validated receipt); /debrief (none); wiki (LLM) | /debrief invisible to close; OPP-N has no status ledger; cross-domain notices dead-lettered | /aar vs /debrief (full overlap, OPP-06 open) | High (code-traced) | AAR receipt → close (yes); OPP-N → operator (no) |
| **8. RETIRE** | /skill-prune (propose-only), /handoff close, DEPRECATED-description convention, harvest close/supersede | **Propose-only, manual**; no auto-trigger; catalog drift unaddressed | skill-prune (operator-confirmed); harvest close (code) | 174 open handoffs accumulate (high generation); /skill-dev ↔ /skill-prune don't coordinate | skill-prune (structural) vs skill-dev (contribution) | Medium | operator (memory-dependent) |

---

## 5. Real improvement journey traces

### Journey 1: Research-to-execution ratio pattern — **LOOP CLOSED at prompt-layer**

```
SIGNAL     : /www investigation confirmed 5 of 6 tracks that already had handoffs
DETECTION  : /tp critique (glm-5-2 fresh subagent, 7 tool calls)
CLASSIFY   : self-reinforcing meta-pattern (substrate accumulation)
PERSISTENCE: wiki concept research-to-execution-ratio-self-reinforcing-pattern.md (2026-07-27)
SELECTION  : operator identified "execute or defer, not research" as structural fix
EXECUTION  : workspace_opportunity_scan.py gained scan_open_handoffs() (commit a63a785);
             /tp SKILL.md gained opportunity scan gate (commit 66f37fc) — 2026-07-29
VERIFICATION: [NOT YET] — falsifier says "if future /tp explore correctly separates EXECUTE_OR_DEFER
              from RESEARCH, the gate worked." No test exists yet.
LEARNING   : wiki concept documents the fix + its limitation (prompt-layer, not mechanical)
RETIREMENT : N/A
```
**Where it closed:** signal → detection → wiki → structural gate (prompt-layer). **Where it's incomplete:** VERIFICATION — no test confirms the gate fires. **Classification: PROVEN up to prompt-layer implementation; INFERRED that the gate will need a mechanical equivalent.** Receipt: wiki concept lines 126-152.

### Journey 2: Close-scanner bugs (BUG-01, BUG-02) — **LOOP STUCK at document stage**

```
SIGNAL     : /close failed after a long session spanning compaction (2026-07-24)
DETECTION  : operator observed; AAR receipt binding + compact format crash
CLASSIFY   : two bugs with root cause identified
PERSISTENCE: handoff close-scanner-bugs/ (status: open, "not fixed")
SELECTION  : [STALLED] — handoff lists acceptance criteria but no session picked it up
EXECUTION  : [NOT DONE for BUG-01/BUG-02] — a SEPARATE journey (close-scanner-timeout-safe-fallback)
             shipped close_runner.py (43 tests, commit at HEAD) but did not fix these two bugs
VERIFICATION: N/A
```
**Where it broke:** between PERSISTENCE and SELECTION. The handoff was written, then orphaned. A related-but-different journey (timeout-safe fallback) was executed instead. The original handoff remains `status: open` with "not fixed." **Classification: FAILED** — the loop produced a document but no execution. Receipt: close-scanner-bugs/HANDOFF.md:22.

### Journey 3: /why refactor → /why-old retirement — **RETIRE SUCCESS**

```
SIGNAL     : /why skill needed refactoring (v3 with evidence-tier, pattern-library)
DETECTION  : operator-initiated refactor
CLASSIFY   : retire old version as A/B comparison baseline
PERSISTENCE: /why-old preserved with "ARCHIVED — pre-refactor snapshot" description prefix
SELECTION  : keep /why-old invocable for explicit A/B comparison
EXECUTION  : /why v3 shipped; /why-old kept intact as fallback reference
VERIFICATION: wiki concept adaptive-expansion-evidence-triggered-conditional-steps.md:212 references
              the A/B test: "If v3 produces equal or deeper findings than v2 on 3+ failures..."
LEARNING   : ARCHIVED-description prefix is a working retirement pattern (catalogued)
RETIREMENT : /why-old is the retiree; it remains discoverable but clearly deprecated
```
**Where it closed:** full loop. This is the single best-evidenced retirement in the workspace. **Classification: PROVEN.** Receipt: ~/.grok/skills/why-old/SKILL.md:1-9; skill-catalog.md:76.

### Journey 4: Verdict-integrity controls — **LOOP at DISCOVER→document, EXECUTE not started**

```
SIGNAL     : /tp review subagent fabricated a mechanism; orchestrator accepted without verification
DETECTION  : operator challenged the fabricated claim
CLASSIFY   : verdict-integrity control gap (8 control gaps identified by external LLM review)
PERSISTENCE: wiki concept decision-transition-auditing-verdict-integrity-controls.md (2026-07-29)
SELECTION  : handoff session-health-behave-verdict-integrity-20260729 lists 3 work streams
EXECUTION  : [NOT STARTED] — "Implementation not started for any of the three"
VERIFICATION: N/A
```
**Where it broke:** between SELECTION (handoff written) and EXECUTION. The signal was strong (operator caught a fabrication), the diagnosis was thorough (external review, 8 control gaps), but the work was handed off and not picked up. **Classification: FAILED (so far)** — a same-day handoff with no execution. Receipt: session-health-behave-verdict-integrity-20260729/HANDOFF.md.

### Journey 5: Harvest concurrency corrections — **LOOP CLOSED (engineering)**

```
SIGNAL     : TOCTOU race in harvest event store (events reclassified as conflict retroactively)
DETECTION  : review cycle identified parent-level arbitration gap
CLASSIFY   : 8 numbered corrections (F1, F2, C7, C8, G5, S5, S8, S9)
PERSISTENCE: store.py + harvest.py comments document each correction
EXECUTION  : claim-based concurrency via O_CREAT|O_EXCL (try_claim, store.py:103-127);
             publish-before-claim ordering (write_event, store.py:152-208)
VERIFICATION: test_harvest.py includes barrier-synchronized race test (Test 19);
              doctor reports 0 conflicts, 0 orphans, 0 orphan claims
LEARNING   : claim files are primary authority; ULID sort is backward-compat fallback
RETIREMENT : old ULID-sort-only behavior superseded (not deleted — backward compat)
```
**Where it closed:** full engineering loop, including verification (test + live doctor). **Classification: PROVEN.** Receipt: store.py:1-38 (property documentation), harvest.py:1-18 (correction list), doctor output this session (0 conflicts).

### Journey summary

| Journey | Stage reached | Classification |
|---|---|---|
| 1. Research-to-execution ratio | EXECUTE (prompt-layer) + LEARN | PROVEN (prompt-layer); INFERRED (mechanical needed) |
| 2. Close-scanner bugs | PERSISTENCE (stalled) | FAILED |
| 3. /why-old retirement | Full loop | PROVEN |
| 4. Verdict-integrity controls | DISCOVER→document (stalled) | FAILED (so far) |
| 5. Harvest concurrency | Full loop | PROVEN |

**Pattern:** the loop closes reliably when the fix is *code* with *tests* (Journey 5) or a *single skill edit* (Journey 3). It stalls when the fix is a *handoff waiting for a future session to pick up* (Journeys 2, 4). The handoff→execution edge is the loop's weakest link — and the operator's confirmation that handoffs are "all new" high-generation work explains why: the backlog grows faster than pickup.

---

## 6. Broken-edge analysis

Distinguished from missing mechanisms: these are **producers that exist and write artifacts, but the consumer is absent or memory-dependent**.

| # | Producer | Artifact | Intended consumer | Actual consumer | Broken? | Evidence |
|---|---|---|---|---|---|---|
| 1 | `/check` orchestrator (LLM) | `check-state.md` | `close_accounting.scan_check_receipts` | Only ~3 of ~24+ runs have it | **YES** | no script in `check/__lib/` writes it; close reads it (530-587) |
| 2 | `/review` | `FINDINGS.md`, `findings.json` | should be tracked as fixed-vs-open | NOT read by close; no fix-tracker | **YES** | grep in close/__lib/ returned 0 |
| 3 | `/debrief` | (none durable) | /wiki auto-save; operator | nothing; close can't detect it | **YES** | close_accounting.py:1340 truncated "Debrief detection requires…" |
| 4 | `/tp` CROSS-DOMAIN NOTICES | `pending/tp.json` | /harvest | no consumer reads it | **YES** | grep for tp.json consumer returned 0 |
| 5 | AAR OPP-N opportunities | AAR report + handoff | /go for ACT_NOW items | /go only when operator invokes | **YES** | OPP-01 still open; no OPP-status ledger |
| 6 | harvest suggestions | `pending/*.json` | harvest doctor | doctor globs `*.tmp`, not `*.json` | **YES** | store.py:50; analyze_session_patterns.json unconsumed |
| 7 | llm_cli_performance producer | `telemetry/llm_cli_performance.jsonl` | fleet tuning | **none — producer lost** | **YES** | last entry 2026-04-02; no producer in P:/.agents/ |
| 8 | spawn_failures producer | `telemetry/spawn_failures.jsonl` | fleet tuning | memory-dependent invocation | **YES** | 0 bytes after 60+ days |
| 9 | harvest OPEN items (12) | harvest events | action (arm/verify/collect) | **none armed** — all 12 unarmed | **YES** | doctor output: "unarmed (hint only): 12" |
| 10 | /go verify output | grok-verify + check-work | /check or /close | prose recommendation only | **YES** | go SKILL.md:770-779 |
| 11 | tp-critique-log patterns | log entries | skill evolution/routing | read-for-display only | **PARTIAL** | /tp Step 0.5 + /skill-dev read it; no action consumer |

**Broken edge vs missing mechanism:** all 11 are broken edges (producer exists, consumer absent/memory-dependent). No new mechanism is needed to fix any of them — each fix is wiring an existing producer to an existing consumer or making an existing consumer read a path it already should.

---

## 7. Cognitive-burden assessment

### User-facing command count

**~45 distinct slash commands** across the relevant scope (44 user skills + bundled + agent skills). For a single operator with ADHD, this is a high memorization surface.

### Naming clarity and routing ambiguity

| Pair | Ambiguity | Resolution cost |
|---|---|---|
| `/aar` vs `/debrief` | Both retrospective. /aar has receipts; /debrief doesn't. | Operator must know which produces durable output. OPP-06 consolidation open. |
| `/check` vs `/review` vs `grok-verify` | Three verification paths. /check = PASS/FAIL; /review = findings; grok-verify = /go sub-skill. | Operator must know /check writes the receipt close reads; grok-verify doesn't. |
| `/harvest` vs `/todo` vs `/handoff` | Three work-tracking stores with documented boundaries. | Boundaries hold but all feed the same backlog. |
| `/tp` (critique vs explore vs session) | 1320-line skill with many modes. | `/tp session` auto-fires in close; `/tp explore` is the only thing that fires workspace_opportunity_scan. |

### Dependence on remembering which skill to invoke

This is the dominant burden. The AGENTS.md "Proactive skill suggestions" table and `/go` default-on policy mitigate this, but the improvement-loop mechanisms specifically require the operator to remember:
- to run `/check` (not just /go's internal grok-verify) to produce a close-readable receipt
- to arm + verify harvest items (capture alone doesn't realize value)
- to run `/tp explore` (not `/tp session`) for opportunity scanning
- to run `/skill-prune` monthly (no auto-trigger)

### State-creating mechanisms that don't help decisions

- **Harvest:** 12 OPEN items, all unarmed. The store is mechanically excellent but functions as a capture graveyard — obligations captured, none realized. The capture→arm→verify→collect lifecycle has no forcing function past capture.
- **tp-critique-log:** 14 entries read for display; no skill has been retired/rerouted based on them.

### ADHD reorientation cost

High. 174 open handoffs, 697 wiki concepts, 45 commands. `/todo` is the designed reorientation entry point and it works (consumes friction_detector, coverage_scan, email). But the triage surface is large enough that even `/todo`'s output is dense (the SKILL.md says "the operator handles 15-20 dense lines").

**Judgment:** the mechanisms are individually well-justified. The burden is **aggregate** — too many parallel paths for the same loop stage, each requiring the operator to know when to invoke it.

---

## 8. Overlap and retirement candidates

### Retirement candidate 1: `/debrief`

| Criterion | Assessment |
|---|---|
| Evidence of use | **Zero artifacts anywhere.** Directory has only SKILL.md. |
| Overlap | Fully overlaps `/aar` (retrospective). /aar has receipts + close integration; /debrief has neither. |
| Duplicated responsibility | 5-lens retrospective ≈ /aar 9-phase review |
| Cost of keeping | +1 command the operator must distinguish from /aar; close cannot detect /debrief, so invoking it doesn't satisfy the retrospective gate |
| Retirement action | Consolidate /debrief's 5-lens model into /aar as a mode, or archive with ARCHIVED prefix (like /why-old) |

**Recommendation: retire /debrief into /aar.** The operator carries the cost of a command that produces nothing close can see.

### Retirement candidate 2: `/why-old` (already retired — confirm sustained)

Already ARCHIVED. A/B comparison window has passed (refactor was 2026-07-25, 4 days ago). If v3 is validated, delete /why-old entirely. Low priority.

### Retirement candidate 3: dead telemetry stores

`llm_cli_performance.jsonl` (producer lost) and `spawn_failures.jsonl` (0 bytes). Either fix the producers or delete the files to stop false-implying a working telemetry layer.

### Consolidation candidate: verification paths

`/check`, `/review`, `grok-verify` — three paths. /check already auto-fires /review (wired). grok-verify is a /go-internal sub-skill with no receipt. Consolidation: make grok-verify write a check-state.md-compatible receipt, or document that /go must be followed by /check.

---

## 9. Ranked interventions

Generated only from demonstrated findings. No new universal orchestrator proposed.

### Intervention 1: Make `/check` write `check-state.md` via a script (not the LLM)

| Field | Value |
|---|---|
| Problem | `/check` verdict receipts are written by the parent LLM, not a script. Only ~3 of ~24+ runs have check-state.md. `/check FAIL` without the receipt is invisible to `/close`. |
| Evidence | no script in `check/__lib/` writes it; close reads it (close_accounting.py:530-587); 3 of ~24+ run dirs have it |
| Affected workflows | every session that runs /check and then /close |
| Proposed mechanism | move the check-state.md write into the /check orchestrator's finalize step (a Python script in `__lib/`), so every run produces the receipt regardless of LLM memory |
| Producer → storage → consumer | /check script → check-state.md → close_accounting.scan_check_receipts |
| Authority | the script (deterministic), not the LLM |
| Freshness | session_id binding (already in schema) |
| Failure behavior | if write fails, /check reports the error (fail-loud, not silent) |
| Dependencies | none new — close already reads the format |
| Expected outcome | 100% of /check runs produce check-state.md; close detects all /check verdicts |
| Validation method | count check-state.md files before/after over N runs; confirm close detects FAIL runs |
| Kill criteria | if after change the LLM still needs to write it (script can't capture the verdict), revert and add a prompt-level reminder instead |
| Cost / reversibility | Low cost (one script function); fully reversible (delete the function) |
| Duplication risk | none — extends existing receipt, doesn't create a new store |
| Cognitive burden | **removed** — operator no longer needs to remember /check writes the receipt |
| Consequence of doing nothing | /check FAILs continue to be silently invisible to /close |

### Intervention 2: Wire harvest `doctor` to consume `pending/*.json` suggestions

| Field | Value |
|---|---|
| Problem | The documented CROSS-DOMAIN NOTICES → harvest pipeline is unwired. `doctor` counts `*.tmp` (atomic-write temps), not `*.json` suggestions. The one suggestion file (`analyze_session_patterns.json`) is dead-lettered. |
| Evidence | store.py:50 (`PENDING = ROOT / "pending"`); harvest.py doctor globs `pending/*.tmp`; analyze_session_patterns.json unconsumed; SKILL.md:240-260 documents the intended feature |
| Affected workflows | any session where /aar, /why, or /tp writes a cross-domain notice |
| Proposed mechanism | add suggestion-file reading to `cmd_doctor` (glob `pending/*.json`, parse, offer to seed) |
| Producer → storage → consumer | /aar, /why, /tp → pending/*.json → harvest doctor |
| Authority | the suggestion files (already written by producers) |
| Failure behavior | if no suggestion files, doctor behaves as today (no regression) |
| Expected outcome | cross-domain notices and pattern suggestions surface in harvest doctor |
| Validation method | write a test suggestion file, run doctor, confirm it appears |
| Kill criteria | if suggestion files are never written by producers in practice, remove the reader |
| Cost / reversibility | Low cost (one glob + parse block); reversible |
| Cognitive burden | **removed** — operators don't need to manually seed harvest from notices |
| Consequence of doing nothing | cross-domain notices continue to accumulate unconsumed |

### Intervention 3: Retire `/debrief` into `/aar` (or archive it)

| Field | Value |
|---|---|
| Problem | /debrief produces zero durable artifacts; close cannot detect it; fully overlaps /aar; OPP-06 consolidation open 1+ week |
| Evidence | debrief/ has only SKILL.md; close_accounting.py:1340 truncated "Debrief detection requires…"; zero artifacts anywhere |
| Affected workflows | operator choosing between /aar and /debrief |
| Proposed mechanism | either (a) consolidate /debrief's 5-lens model into /aar as a `--lenses` mode, or (b) archive with ARCHIVED prefix (like /why-old) |
| Producer → storage → consumer | N/A (retirement) |
| Authority | operator decision (OPP-06 is NEEDS_USER_DECISION) |
| Expected outcome | -1 command; -1 retrospective path; retrospective gate unambiguous |
| Validation method | confirm no skill references /debrief after retirement; confirm /aar covers the 5 lenses |
| Kill criteria | if /debrief's 5-lens fan-out is materially better than /aar for some sessions, keep it and instead make it write a completion-receipt-compatible artifact |
| Cost / reversibility | Low cost (archive or merge); reversible (ARCHIVED prefix, body kept) |
| Cognitive burden | **removed** — one fewer retrospective command to distinguish |
| Consequence of doing nothing | /debrief continues to be a dead-surface command that doesn't satisfy the close gate |

---

## 10. Recommended next action

**Intervention 1: Make `/check` write `check-state.md` via a script.**

Rationale for selecting this over the other two:
1. **User-visible outcome:** directly fixes the "verification failures invisible to close" gap — the highest-impact single break in the loop.
2. **Frequency/exposure:** every session that runs /check is affected; /check is a core VERIFY mechanism.
3. **Evidence strength:** code-traced (no writer script exists; close reads the format; 3/24+ ratio measured).
4. **Downstream leverage:** reliable verification receipts make the close gate trustworthy, which makes the entire LEARN stage trustworthy.
5. **Cost/reversibility:** one script function; fully reversible.
6. **Cognitive burden:** removes an operator memory burden (no need to remember /check writes the receipt).

**This is a narrow, testable intervention with a falsifiable validation plan.** It does not create a new mechanism — it wires an existing producer to an existing consumer.

---

## 11. Verification plan (for Intervention 1)

**Falsifiable hypothesis:** moving the check-state.md write into a `__lib/` script will cause 100% of /check runs to produce the receipt, and `/close` will detect all /check verdicts (including FAILs).

**Validation steps:**
1. **Baseline measurement (before):** count existing check-state.md files vs grok-check run dirs. Confirmed: ~3 receipts of ~24+ runs.
2. **Implement:** add a `write_check_state(verdict, session_id, verifiers, run_dir)` function in `~/.grok/skills/check/__lib/`; call it at /check finalize.
3. **Test:** run /check on a disposable session; confirm check-state.md is written with correct schema.
4. **Close-integration test:** run /close on the same session; confirm `scan_check_receipts` detects it.
5. **FAIL-path test:** run a /check that produces a FAIL; confirm check-state.md is still written; confirm close reports it rather than "no verification evidence found."
6. **After N=5 real /check runs:** count receipts. Target: 5/5. Kill criterion: if <5/5, the script isn't capturing all verdict paths — revert and add prompt-level reminder instead.

**Scope binding:** the validation commands will name `check/__lib/<writer>.py` and `close_accounting.py` explicitly (per the Stop hook scope-binding contract).

---

## 12. Proven / Inferred / Unknown / Failed

| Claim | Classification | Receipt |
|---|---|---|
| Harvest store has 12 OPEN items, all unarmed | PROVEN | `harvest doctor` output this session |
| Only ~3 of ~24+ /check runs have check-state.md | PROVEN | Get-ChildItem + grep for verdict regex in .artifacts/ |
| No script in check/__lib/ writes check-state.md | PROVEN | grep for `check-state` in `__lib/` returned 0 |
| close_accounting.py reads check-state.md | PROVEN | close_accounting.py:530-587 |
| AAR completion receipt → close is wired and working | PROVEN | close_accounting.py:1336-1397; 019fa48a close-evidence shows pre_satisfied |
| /debrief produces zero durable artifacts | PROVEN | list_dir of debrief/ (only SKILL.md); grep across workspace returned 0 |
| close_accounting.py cannot detect /debrief | PROVEN | close_accounting.py:1340 truncated "Debrief detection requires…" |
| harvest doctor does not consume pending/*.json suggestions | PROVEN | store.py:50; doctor globs pending/*.tmp; analyze_session_patterns.json unconsumed |
| CROSS-DOMAIN NOTICES → harvest is unwired | PROVEN | grep for tp.json consumer returned 0 |
| 174 of 205 handoffs are open | PROVEN | handoff status distribution (Get-Content + Select-String) |
| Handoffs are "all new" (high generation, not stuck closures) | PROVEN (operator-confirmed) | operator statement this session |
| Research-to-execution ratio is a self-reinforcing pattern | PROVEN (documented) | wiki concept research-to-execution-ratio-self-reinforcing-pattern.md |
| /why-old retirement succeeded | PROVEN | why-old/SKILL.md; skill-catalog.md:76; wiki concept references A/B test |
| llm_cli_performance.jsonl is dead data | PROVEN | last entry 2026-04-02; no producer in P:/.agents/ |
| spawn_failures.jsonl is empty due to memory-dependent invocation | INFERRED | producer is correct (log_spawn.py:35-50); 0 bytes; SKILL.md recommends but doesn't enforce |
| The 22:2 close-to-AAR ratio is partly artifact-path mismatch | INFERRED | close finds runtime AARs at .artifacts/grok-aar/ via rglob; user-scope .artifacts/ is a different path |
| /go → /check is prose-recommendation only | PROVEN | go SKILL.md:770-779 |
| /review findings have no fix-tracker | PROVEN | grep for FINDINGS.md in close/__lib/ returned 0 |
| The loop closes reliably for code+test fixes, stalls for handoff-waiting fixes | INFERRED | Journey 5 (closed) vs Journeys 2,4 (stalled) |
| /gto does not exist | PROVEN | Get-ChildItem returned empty at all scopes |
| /rns is not installed at Grok scope | PROVEN | exists only in cc-skills-analysis Claude cache; skill-catalog.md:738 |
| Close-scanner-bugs (BUG-01, BUG-02) remain unfixed | PROVEN | close-scanner-bugs/HANDOFF.md:22 "not fixed" |
| The structural research-to-execution gate will need a mechanical layer | INFERRED | the wiki concept's own falsifier states this |

---

## 13. Deferred questions

These require operator decision or further investigation beyond this read-only audit:

1. **OPP-06 (/debrief consolidation):** retire /debrief into /aar, or make /debrief write a close-detectable artifact? This is the documented `NEEDS_USER_DECISION` item, open 1+ week. The evidence supports retirement (Intervention 3).

2. **Harvest realization forcing function:** 12 OPEN items, all unarmed. The capture→arm lifecycle has no forcing function past capture. Should close or todo surface "you have N unarmed harvest items — arm or close them"? This is a behavioral/prompt question, not a wiring fix.

3. **Telemetry producer recovery or deletion:** `llm_cli_performance.jsonl` (producer lost) and `spawn_failures.jsonl` (0 bytes). Recover the producers or delete the files to stop false-implying a working telemetry layer.

4. **OPP-status ledger:** AAR opportunities and harvest obligations accumulate without execution tracking. A minimal `disposition_history` field or lightweight ledger would let close/todo surface stale opportunities. This is a small new mechanism — deferred per the "no new orchestrator" constraint unless evidence proves existing mechanisms cannot track this.

5. **grok-verify receipt compatibility:** should `/go`'s internal `grok-verify` write a check-state.md-compatible receipt so close can detect /go-verified work without a separate /check invocation? This would close the /go → close gap.

---

## Final verdict

**IMPROVEMENT_LOOP_PARTIAL**

The environment is not a closed, observable, self-correcting loop. It is a collection of well-engineered stages connected by memory-dependent handoffs. The front half (SENSE → DISCOVER → EXECUTE) works; the back half (VERIFY → LEARN → RETIRE) has three specific unwired edges:

1. **Verification receipts** (check-state.md) are unreliable — the highest-impact gap.
2. **Learning outputs** (AAR opportunities, harvest obligations, cross-domain notices) lack reliable consumers.
3. **Authority overlaps** (/aar vs /debrief, /check vs /review vs grok-verify) add cognitive burden without coordination.

The smallest intervention that most improves verified outcomes is **Intervention 1** (mechanize the check-state.md write). It is narrow, testable, reversible, and closes the loop's single highest-impact break without creating any new mechanism.

The number of mechanisms is not the problem. The wiring between them is.
