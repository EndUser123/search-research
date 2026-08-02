---
thread_id: workspace-health-batch-20260802
parent_handoff_path: none
current_session_id: 019f9a89-d902-7930-ad3a-bab7e682830b
current_terminal_id: console
produced_at: 2026-08-02T15:30:00Z
last_updated_by: 019f9a89-d902-7930-ad3a-bab7e682830b
last_updated_at: 2026-08-02T15:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: e5575252251bf1ebdb4a1e549653e3c55463acdc
---

# Handoff: Workspace health batch — 5 small items from close-check + /tp improve

## Objective

Five independent workspace-health items surfaced by close-check-2 and /tp improve. All are small (S effort each), independent, and can be batched in a single session. Together they reduce noise, false positives, and friction in workspace infrastructure.

## Status

OPEN — ready for implementation. No design decisions needed.

## Producing context

Produced 2026-08-02 by session 019f9a89 (terminal: console). Items from close-check-2 report + /tp improve 4-dimension analysis.

## Read-first list

1. Close-check-2 report: `C:/Users/brsth/.grok/sessions/P%3A%5C/019f9a89-d902-7930-ad3a-bab7e682830b/workflows/wf_019fc0c821c17ee3875416f770c66bb9/scratch/pre-close-report.md`
2. `P:/.agents/scripts/launch_llm_chrome.py` — os.system bug (item 3)
3. `~/.grok/hooks/quality-gate.json` — hook registration (item 5)
4. `/tp improve` output in session transcript (item 5)

## Verified facts

- [FACT] 15 handoffs >30 days old in coverage output (source: close-check-2 report)
- [FACT] launch_llm_chrome.py lines 122-125 use os.system() with discarded return codes (source: close-check-2 /trace output)
- [FACT] 5+ FMEA-flagged files don't exist at claimed paths: tp_dispatch.py, synthesize_subtopics.py, log_spawn.py, ship_receipt.py, scheduled_checks.py (source: close-check-2 /trace)
- [FACT] spawn_model_gate.py edited 9× in one session window (source: /friction analysis)

## Task packets

### WH-01: Audit and deprecate stale handoffs

- **Goal:** Close or deprecate 15 handoffs older than 30 days whose target systems may no longer exist or whose questions have been answered
- **In scope:** `aar-uncaptured-knowledge-audit-20260723`, `cascade-pattern`, `sqlite-telemetry-backend`, `routing-library`, `response-strategy-meta-layer`, `codex-skill-20260720`, `agentic-workflows-research-20260724`, `notebooklm-consolidation-20260724`, `skill-infra-session-20260724`, `solution-before-rootcause-20260724`, `www-proactive-trigger-design`, `model-telemetry-integration`, `data-source-integration-20260724`, `www-research-backlog-20260724`, `keep-smaller-copy-tui`
- **Out of scope:** Recent handoffs (<14 days old)
- **How:** For each: read the handoff, check if target files still exist, check if the question was answered by subsequent work. If stale → `/handoff close`. If still valid → leave open.
- **Acceptance:** ≥10 of 15 handoffs closed or explicitly re-validated as still open
- **Falsifier:** if most handoffs are still valid, the audit produces little gain
- **Verification level:** STATIC_INSPECTION

### WH-02: Fix close-check scanner crash on concurrent commits

- **Goal:** Close-check Phase 2 scanner crashed because sibling sessions committed between reads, causing evidence ledger to not generate
- **In scope:** The scanner code in `close/__lib/close_accounting.py` that reads the evidence ledger
- **Out of scope:** Workflow Rhai script itself
- **How:** Add retry or snapshot logic — read HEAD once at scan start, use that for all subsequent operations within the sweep window
- **Acceptance:** Close-check completes successfully even when sibling sessions commit during the sweep
- **Falsifier:** if concurrent commits don't actually cause the crash (different root cause), this fix won't help
- **Verification level:** LIVE_BEHAVIOR — run close-check while another session commits

### WH-03: Fix launch_llm_chrome.py os.system return codes (LOW)

- **Goal:** Capture stderr and return codes from schtasks calls for debuggability
- **In scope:** `P:/.agents/scripts/launch_llm_chrome.py` lines 122-125
- **Out of scope:** Other scripts (this is the only flagged os.system usage)
- **How:** Replace `os.system(cmd)` with `subprocess.run(cmd, capture_output=True, text=True)` and log stderr on failure
- **Acceptance:** When schtasks fails, the error message includes the actual schtasks stderr
- **Falsifier:** downstream `count_chrome_processes()` guard at line 192-198 already prevents false-positive "Chrome ready" — this is debuggability, not correctness
- **Verification level:** UNIT_TEST
- **Note:** LOW severity. The downstream guard exists. This is about error messages, not safety.

### WH-04: Retire stale FMEA scan paths

- **Goal:** Update FMEA scan configuration to reference current file paths instead of phantom locations
- **In scope:** FMEA scan paths for: tp_dispatch.py, synthesize_subtopics.py, log_spawn.py, ship_receipt.py, scheduled_checks.py
- **Out of scope:** Files that DO exist (launch_llm_chrome.py, close_accounting.py, index_skills.py, fleet_quota.py)
- **How:** For each phantom file: find the actual current location (if it exists) or remove it from the scan config. The close-check-2 trace already found: PostToolUse_auto_verify.py is now lint_hook.py (and is structurally disabled); tp_dispatch.py and others may have been renamed or removed.
- **Acceptance:** FMEA scan returns only existing-file findings; no phantom paths
- **Falsifier:** if the FMEA scanner auto-discovers files (no hardcoded paths), the issue is in discovery logic, not config
- **Verification level:** STATIC_INSPECTION

### WH-05: Batch-design rule for security/control-plane files

- **Goal:** Add an AGENTS.md rule or convention: for files in `~/.grok/hooks/` and `~/.grok/skills/*/__lib/`, complete the design before the first edit rather than iterating 9× in one window
- **In scope:** `~/.grok/AGENTS.md` File editing protocol section
- **Out of scope:** Non-security files (wiki concepts, handoffs — iterative editing is normal for those)
- **How:** Add a sub-rule under "File editing protocol": "For files in hooks/ or security-sensitive paths (__lib/ in security skills), enumerate all changes before editing. If the file has been edited 3+ times in one session window, stop and write a design note before continuing."
- **Acceptance:** Rule is present in AGENTS.md and references the spawn_model_gate 9× edit incident
- **Falsifier:** if agents don't read AGENTS.md rules (the enforcement gap), this rule won't fire — but it's still correct to have it documented
- **Verification level:** STATIC_INSPECTION

## Open decisions

None — all items are mechanical with clear acceptance criteria.

## Hard constraints

- WH-01: Do NOT close a handoff without reading it first. Some "stale" handoffs may contain still-relevant decisions.
- WH-03: The downstream `count_chrome_processes()` guard must NOT be removed — it's the safety net.

## Cross-reference couplings

- WH-01 → feeds the `harvest-burn-down-20260801` handoff (closing stale handoffs reduces the total count)
- WH-02 → close-check workflow reliability; related to `close-check-lifecycle-auto-chain-20260801`
- WH-03 → `P:/.data/wiki/concepts/chrome-job-object-escape-via-task-scheduler.md` documents the design
- WH-04 → close-check FMEA phase produces these flags every run
- WH-05 → `~/.grok/AGENTS.md` "File editing protocol" section

## Other outstanding streams

- **harvest-burn-down-20260801** (Rev 1) — cluster 27 OPEN harvest items, close top 5-10
- **close-check-lifecycle-auto-chain-20260801** — auto-invoke surface-only skills
- **agentic-rules-not-firing-enforcement-investigation-20260726** (Rev 1) — deferred
- **verifier-false-confidence-bug-20260802** — separate handoff for the 3-state receipt enum fix

## Explicit non-goals

- Do NOT redesign the close-check workflow (WH-02 is a fix, not a redesign)
- Do NOT redesign the FMEA scanner (WH-04 is path updates, not architecture)
- Do NOT add enforcement mechanisms for the batch-design rule (WH-05 is documentation, the enforcement gap is a separate investigation)

## Resumption protocol

1. Start with WH-01 (stale handoff audit) — it's the highest-leverage item and reduces noise for all subsequent work
2. Then WH-04 (FMEA paths) and WH-05 (AGENTS.md rule) — both are quick edits
3. Then WH-03 (launch_llm_chrome.py) — small code fix
4. Then WH-02 (scanner crash) — needs live testing

## Suggested next invocation

```
Pick up the workspace health batch handoff at P:/docs/handoffs/workspace-health-batch-20260802/HANDOFF.md.
Start with WH-01 (stale handoff audit). 5 items total, all S effort.
```

## Last user message (verbatim)

"/handoff" (auto-update mode — creating handoffs for untracked items 7-11 from the /tp unified list)

## Epistemic labels

- [FACT] All 5 items surfaced by close-check-2 or /tp improve (receipts in close-check report)
- [FACT] launch_llm_chrome.py bug confirmed by /trace (3 scenarios, no critical errors)
- [INFERENCE] WH-01 is the highest-leverage item because stale handoffs have negative leverage
- [UNKNOWN] Whether the close-check scanner crash (WH-02) is reproducible — it may have been a one-time concurrent-commit race

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T15:30 | 019f9a89... | created |
