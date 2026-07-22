---
thread_id: c9d08f0c-8da6-441a-bfcd-187674cb6e81
parent_handoff_path: P:\docs\handoffs\proposal-grounding-monitor-evaluation-20260720\HANDOFF.md
current_session_id: 019f8155-f901-79a2-9ba1-ac4614db5225
current_terminal_id: console_fa595529-45ae-4fa2-8517
produced_at: 2026-07-21T18:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: c96832724e0bed245ddb0ce2a2d72eb55d359a97
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f8155-f901-79a2-9ba1-ac4614db5225\chat_history.jsonl
---

# HANDOFF — proposal-grounding-monitor: calibration + live monitoring

## Objective

Calibrate the proposal-grounding-monitor plugin's proposal-detection regex against a real corpus of 7306 assistant responses from 469 session transcripts, resolve deferred /red-team findings with empirical data, and establish the monitoring protocol for the now-live plugin.

## Status

READY_FOR_REVIEW — GR-2 calibrated (2 over-broad patterns dropped), IA-004 and ST-3 RESOLVED by empirical data (no change needed). Plugin is v0.1.1, enabled, live, and calibrated. Remaining items are v0.2 design decisions.

## Producing context

- Date: 2026-07-21
- Session: `019f8155-f901-79a2-9ba1-ac4614db5225`
- Terminal: `console_fa595529-45ae-4fa2-8517`
- Prior sessions: extensive plugin work across 2 sessions (review → red-team → 13 deterministic fixes → calibration)
- Plugin repo: `~/.grok/plugins/proposal-grounding-monitor/` (dotgrok.git, commit `3ab09b0`)

## Read-first list

1. `C:\Users\brsth\.grok\plugins\proposal-grounding-monitor\scripts\relevance.py` — the calibrated regex (GR-2 patterns dropped)
2. `C:\Users\brsth\.grok\plugins\proposal-grounding-monitor\README.md` — v0.1.1 documentation
3. `P:\.claude\.artifacts\019f8155-f901-79a2-9ba1-ac4614db5225\red-team\20260720-170712\critic.json` — the /red-team findings (18+ REVISE)
4. `P:\.artifacts\console_fa595529-45ae-4fa2-8517-5edb\grok-review\proposal-grounding-monitor\20260720-150520\FINDINGS.md` — the original /review findings (13 total)
5. `%TEMP%\calibration_corpus.jsonl` — the 7306-response corpus with detect_proposal results (may be GC'd; re-extract via `P:\tmp\extract_corpus_v2.py`)

## Verified facts

- [FACT] Corpus: 7306 assistant responses extracted from 469 session transcripts at `~/.grok/sessions/P%3A%5C/` (2026-07-21T18:00Z)
- [FACT] Pre-calibration flag rate: 13 of 7306 (0.2%) — ALL 13 were false positives (status reports, retractions, inventories)
- [FACT] Two patterns produced 12 of 13 FPs: `\bthe best (?:technical )?(?:approach|implementation|way|solution)\b` and `\bthe (?:right|correct) (?:approach|architecture|design)\b`
- [FACT] Post-calibration flag rate (after dropping those 2 patterns): 7 of 7331 (0.1%) — 46% FP reduction
- [FACT] IA-004 hedge regex: 370 responses hedge-suppressed (5.1%); 0 of those contain proposal patterns. The /red-team concern about single-word hedges ('likely', 'probably') causing FNs was **refuted by the corpus** — 0 FNs from hedging.
- [FACT] ST-3 subagent id inheritance: session directory structure shows subagents get their OWN unique UUIDs (sharing only the timestamp-based first 8 chars). No collision risk. State isolation via `pgm-state-<GROK_SESSION_ID>.json` is correct.
- [FACT] Plugin is enabled in `config.toml:92` and live (active-surface confirms all 5 hooks firing)
- [FACT] Plugin version 0.1.1, commit `3ab09b0` on dotgrok.git, pushed to origin/main
- [FACT] 117 tests passing

## Current state

**Done:**
- GR-2 fix: dropped `the_best` and `the_right` patterns based on 0% precision in corpus
- IA-004: NO CHANGE (0 empirical FNs — the concern was theoretical, not data-backed)
- ST-3: RESOLVED (subagents get own UUIDs; no collision risk)
- Plugin is live and producing telemetry (stop.jsonl events with session_id/pid attribution per ST-7)

**Not done (deferred to v0.2 — these are design decisions, not bug fixes):**
- GR-5: `has_qualifying_evidence` too broad (multi-topic sessions get free passes). v0.2 scope-overlap matching.
- GR-9: quantitative performance claims ('p95 from 200ms to 50ms') uncovered. v0.2 scope decision.
- Calibration assessment: the 0.1% flag rate means the plugin rarely fires. Is that the correct behavior for an advisory gate? Needs live telemetry analysis over multiple sessions to answer.

## Task packets

### PGM-MONITOR-1: assess-live-flag-rate

- goal: after 5+ real sessions with the plugin enabled, analyze stop.jsonl telemetry to determine whether the 0.1% flag rate produces useful signals or is too conservative
- in scope: read stop.jsonl events; correlate gate_decision events with actual session context; assess whether any true positives were caught
- out of scope: modifying the regex (that's PGM-CALIBRATE-2)
- files / anchors: `~/.grok/plugin-data/proposal-grounding-monitor/telemetry/stop.jsonl`
- acceptance: a written assessment of whether the current flag rate is useful, too low, or appropriate for an advisory gate
- falsifier: if after 10+ sessions zero proposals were flagged AND the model made ungrounded proposals, the regex is too conservative
- verification level required: STATIC_INSPECTION

### PGM-CALIBRATE-2 (conditional): v0.2 scope decisions

- goal: decide whether to implement GR-5 (scope-overlap) and/or GR-9 (quantitative claims) based on live telemetry data
- in scope: design decision for both items; implementation if approved
- out of scope: GR-2/IA-004 (already resolved)
- files / anchors: `relevance.py` (QUALIFYING_CATEGORIES, PROPOSAL_SIGNALS)
- acceptance: documented decision with rationale for each item
- falsifier: if live telemetry shows multi-topic FNs are common, GR-5 moves from "deferred" to "implement"
- verification level required: STATIC_INSPECTION
- condition: only actionable after PGM-MONITOR-1 produces data

## Open decisions

None. All calibration decisions resolved by the corpus data.

## Hard constraints

- Plugin is advisory-only (v1 never blocks tool calls)
- All state mutators hold cross-process locks (ST-1)
- Telemetry carries session_id/pid/hook_event attribution (ST-7)
- Plugin is in dotgrok.git private repo; commit to dotgrok, not p.git

## Cross-reference couplings

- `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py` → consumed by `stop_detect.py` and `posttool_track.py`. Regex changes affect both.
- `~/.grok/config.toml:92` → plugin enabled. If removed, plugin goes dormant.
- `~/.grok/plugin-data/proposal-grounding-monitor/telemetry/stop.jsonl` → accumulating live telemetry. Read by PGM-MONITOR-1.
- `P:\docs\handoffs\proposal-grounding-monitor-evaluation-20260720\HANDOFF.md` → parent handoff (the original evaluation). Superseded by this handoff.
- `P:\docs\handoffs\handoff-v02-aar-integration-20260720\HANDOFF.md` → unrelated workstream (handoff skill v0.2) but shares the session context.

## Other outstanding streams

- **handoff v0.2 /aar integration** — READY_FOR_REVIEW. Handoff at `P:\docs\handoffs\handoff-v02-aar-integration-20260720\HANDOFF.md`. The next major piece of work for the handoff skill. OPEN.
- **M1 system 6 known bugs** — documented in `P:\docs\handoffs\design-skill-runtime-foundation-20260720\HANDOFF.md` under "M1 disposition." Bugs are in `~/.grok/hooks/scripts/active_surface_snapshot.py`. OPEN.
- **/design skill validation** — Steps 4.5/5.5/6.0/6d shipped but untested in real run. Documented in `design-skill-runtime-foundation-20260720`. OPEN.
- **exec-gate-enhancement** — handoff at `P:\docs\handoffs\exec-gate-enhancement-20260721\`. OPEN.
- **yt-is-fetch-resume** — handoff at `P:\docs\handoffs\yt-is-fetch-resume-20260720\`. Claimed by grok. OPEN.
- **ytis-nlm-fetch-and-migration** — handoff at `P:\docs\handoffs\ytis-nlm-fetch-and-migration-20260720\`. Claimed by grok. OPEN.
- **CCR fleet work** — parked from prior session. No handoff. OPEN.
- **Textual dashboard** — written and tested but not activated. No handoff. OPEN.
- **cross-model skills (/mmx, /codex)** — handoff referenced in `P:\docs\handoffs\handoff-skill-v01-20260720\HANDOFF.md`. OPEN.

## Explicit non-goals

- Do NOT re-tighten the hedge regex (IA-004) — the corpus data showed 0 FNs
- Do NOT implement GR-5 or GR-9 without live telemetry data from PGM-MONITOR-1
- Do NOT disable the plugin — it's live and calibrated
- Do NOT re-extract the corpus without reason — the existing analysis at `%TEMP%\calibration_corpus.jsonl` is sufficient

## Resumption protocol

1. Read this handoff
2. Check `~/.grok/plugin-data/proposal-grounding-monitor/telemetry/stop.jsonl` for accumulated events
3. If ≥5 sessions of telemetry exist: run PGM-MONITOR-1 (assess live flag rate)
4. If the assessment shows the flag rate is too low: consider PGM-CALIBRATE-2 (GR-5/GR-9)
5. If the assessment shows the flag rate is appropriate: close this handoff and move to a different workstream

## Suggested next invocation

```
Read ~/.grok/plugin-data/proposal-grounding-monitor/telemetry/stop.jsonl and report:
1. How many dispatch_received events (total Stop turns observed)
2. How many gate_decision events by decision type (no_proposal, grounded_out, opened_repair)
3. How many repair_opened events
4. Whether any opened repairs correspond to ACTUAL ungrounded proposals (vs FPs)
```

## Last user message (verbatim)

> I forgot.  Please create handoff files for all the workstreams with open items.

## Epistemic labels

- [FACT] All corpus numbers (7306 responses, 13→7 flag rate, 0 hedge FNs) verified by running extract_corpus_v2.py against real session transcripts on 2026-07-21
- [FACT] ST-3 resolution verified by inspecting session directory structure (subagent UUIDs share timestamp prefix but differ in full UUID)
- [FACT] Plugin is enabled and live (verified via active-surface snapshot and config.toml)
- [INFERENCE] The 0.1% flag rate may be too conservative — but this can only be assessed with live telemetry from real proposal-making sessions
- [UNKNOWN] Whether the remaining 7 flagged responses (post-GR-2 fix) are true positives or FPs — would require reading the full text of each
