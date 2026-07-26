---
thread_id: web-fan-out-fresh-invocation-validation-20260726
parent_handoff_path: P:\docs\handoffs\tp-session-shipped-work-20260726\HANDOFF.md
current_session_id: 019f8b39-95e3-7121-a8de-4e3f117e511a
current_terminal_id: console_c0d59c27-a0ec-424a-b5d6-cb19fc5f7c0b
produced_at: 2026-07-26T23:05:00Z
status: open
handoff_type: investigation
accurate_as_of_head: c8a34ce12a38ab0c0f33778ea07358266d9598d4
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f8b39-95e3-7121-a8de-4e3f117e511a\chat_history.jsonl
---

# Handoff: /web mandatory fan-out recipe — fresh invocation validation

## Objective

Validate the NON-NEGOTIABLE 3-source fan-out recipe shipped in commit `cab6bf7` (`~/.grok/skills/web/SKILL.md`) on a fresh `/web` invocation. The recipe requires every `/web` call to fan out to minimax-search + web-search-prime + DDG in parallel, then RRF-merge results. The recipe was shipped in response to the DDG-omission finding (session 019f8b39, episode E11) where DDG was skipped on a 3-backend search due to default-selection bias toward visible MCP tools. The recipe has been verified once (web-search-prime history check) but never on a fresh `/web` invocation with a real query.

**Scope bounds:** Validation only. Do NOT modify the recipe until at least one fresh invocation confirms all 3 backends fire and the RRF merge produces output.

## Status

OPEN — validation not started. Trigger: next fresh `/web` invocation on a non-history-check query (i.e., a real research question, not "does web-search-prime work").

## Producing context

- **Date:** 2026-07-26
- **Producing session-id:** 019f8b39-95e3-7121-a8de-4e3f117e511a
- **Producing terminal-id:** console_c0d59c27-a0ec-424a-b5d6-cb19fc5f7c0b
- **Host/version:** Grok Build
- **Trigger:** AAR for session 019f8b39 listed /web fan-out validation as VALUE_UNREALIZED and VALUE_DEFERRED. The AAR's own close-out audit found this finding had no dedicated handoff — this file is the structural fix.

## Read-first list (ordered, with reasons)

1. **`~/.grok/skills/web/SKILL.md`** "Mandatory default fan-out recipe (NON-NEGOTIABLE)" section — the recipe being validated.
2. **Commit `cab6bf7`** — the shipped recipe implementation.
3. **`~/.grok/AGENTS.md`** § "Web-search tool selection (Grok Build only)" — the tool-selection rule that motivates the recipe.
4. **AAR report** `P:/.artifacts/aar/019f8b39-95e3-7121-a8de-4e3f117e511a/aar-report.md` — episode E11 (DDG omission), VALUE_UNREALIZED, VALUE_DEFERRED entries.

## Verified facts (with source paths)

- [FACT] Fan-out recipe shipped in commit `cab6bf7`. Source: git log.
- [FACT] Recipe is marked NON-NEGOTIABLE in SKILL.md frontmatter and body. Source: `~/.grok/skills/web/SKILL.md`.
- [FACT] DDG omission (the trigger for the recipe) was a default-selection bias toward visible MCP tools, not a memory failure. Source: session 019f8b39, user explicitly rejected "I forgot" framing.
- [FACT] web-search-prime was verified working (history check) during the session that shipped the recipe. Source: session 019f8b39 summary.
- [FACT] The full 3-source fan-out (minimax-search + web-search-prime + DDG) has never been observed firing together on a fresh `/web` invocation. Source: AAR for this session.

## Lifecycle block

- **Hypothesis:** The NON-NEGOTIABLE fan-out recipe fires all 3 backends (minimax-search + web-search-prime + DDG) on every fresh `/web` invocation and produces RRF-merged output, preventing the single-source-omission failure class.
- **Success signal:** Next fresh `/web` invocation (non-history-check query) fires all 3 backends, all 3 return content (or fail visibly), and RRF merge produces a deduplicated ranked list.
- **Failure signal:** (a) One or more backends are skipped (recipe not followed), OR (b) one or more backends fail silently (no error surfaced), OR (c) RRF merge produces no output or garbage.
- **Retirement condition:** Fan-out fires reliably across 3+ fresh invocations → recipe is validated. If recipe fails to fire, revise SKILL.md language or investigate backend compatibility.
- **Trigger for action:** Next fresh `/web` invocation on a non-history-check query in any future session.
- **Review cadence:** Next `/web` invocation.
- **Exit condition:** 3+ fresh invocations confirm reliable 3-source fan-out, OR recipe revised to address observed failures.

## Current state

**What works:**
- Recipe is shipped, committed, and marked NON-NEGOTIABLE.
- web-search-prime verified working (history check).
- minimax-search is the default MCP search tool (per AGENTS.md tool-selection rule).
- DDG exists as a backend (it was the one skipped in the original incident).

**What's not yet validated:**
- Does the recipe actually fire all 3 backends on a fresh `/web` call?
- Does DDG return content on a real query (not just exist as a backend)?
- Does the RRF merge produce useful deduplicated output?
- Are there backend failures that surface visibly vs silently?

## Task packets

### TK-VAL-01: Observe next fresh /web invocation

**Goal:** On the next fresh `/web` invocation (any future session, non-history-check query), observe whether all 3 backends fire and RRF merge produces output.

**In scope:** Passive observation. Do NOT invoke `/web` solely for validation — wait for a natural research question.

**Out of scope:** Modifying the recipe before observing it.

**Files / anchors:** `~/.grok/skills/web/SKILL.md` "Mandatory default fan-out recipe" section.

**Acceptance:** One fresh `/web` run where either (a) all 3 backends fire + RRF merge produces output, or (b) one or more backends skipped/fail — documented either way.

**Falsifier:** If DDG is skipped again on a fresh invocation despite the NON-NEGOTIABLE language, the recipe's language is insufficient and needs structural reinforcement (e.g., a hook that blocks /web without 3 backend calls).

**Verification level required:** OBSERVED.

**Estimate:** Passive — triggers on next natural `/web` invocation.

### TK-VAL-02: Confirm reliability across 3+ invocations

**Goal:** After TK-VAL-01 succeeds, confirm the recipe fires reliably across 3+ fresh invocations (not a one-off).

**Acceptance:** 3+ fresh `/web` invocations all fire the 3-source fan-out.

**Falsifier:** If the recipe fires on the first invocation but is skipped on subsequent ones, the NON-NEGOTIABLE language degrades under session fatigue — needs hook enforcement.

## Collected observations

(not yet started — populate on fresh /web invocations)

| Run date | Session | Query type | minimax fired? | web-search-prime fired? | DDG fired? | RRF merge output? | Notes |
|---|---|---|---|---|---|---|---|
| (pending) | | | | | | | |

## Open decisions

### D1: Does the recipe need hook enforcement?

**Trigger:** TK-VAL-01 or TK-VAL-02 fails (backend skipped despite NON-NEGOTIABLE language).

**Options:**
- **Language only** (current) — NON-NEGOTIABLE in SKILL.md. Sufficient if the instruction is followed.
- **Hook enforcement** — a PreToolUse or PostToolUse hook that checks `/web` invocations actually called 3 backends. Heavier but structural.

**Currently leading:** Language only (pending validation). Escalate to hook only if the recipe is skipped despite the language.

## Hard constraints

- **Do NOT modify the recipe before observing it on a fresh invocation.**
- **Do NOT invoke `/web` solely for validation.** Wait for a natural research question.
- **Edit-verify pattern.** If the decision is "hook enforcement," any hook edit requires read-back + dispatch wiring per plugin-development rules.

## Cross-reference couplings

- `~/.grok/skills/web/SKILL.md` "Mandatory default fan-out recipe" → the recipe being validated.
- `~/.grok/AGENTS.md` § "Web-search tool selection" → the tool-selection rule motivating the recipe.
- Parent handoff `tp-session-shipped-work-20260726` → documents the recipe as shipped work.

## Explicit non-goals

- **Do NOT modify the recipe before observation.**
- **Do NOT force a `/web` invocation for validation.**
- **Do NOT add hook enforcement before the language is shown to be insufficient.**

## Resumption protocol

1. Check "Collected observations" above. If empty, this handoff is waiting for a natural `/web` invocation.
2. If `/web` fires this session on a non-history-check query, observe whether all 3 backends fire and RRF merge produces output. Record in the table.
3. If 3+ rows exist with all backends firing, the recipe is validated — close this handoff.
4. If any row shows a skipped backend, escalate to D1 (hook enforcement decision) and revise.

## Suggested next invocation

```
Check /web fan-out recipe validation status. Read
P:/docs/handoffs/web-fan-out-fresh-invocation-validation-20260726/HANDOFF.md.

If "Collected observations" is empty, this is passive — wait for a natural
/web invocation on a real research question. If /web fires this session,
observe whether all 3 backends (minimax-search + web-search-prime + DDG)
fire and RRF merge produces output. Record in the table.
```

## Last user message (verbatim)

> "do it all"

(context: user approved creating all 5 durability artifacts for non-closed AAR findings. This handoff covers the /web fan-out validation finding, VALUE_DEFERRED #3.)

## Epistemic labels per claim

- [FACT] Fan-out recipe shipped in commit `cab6bf7` — git log.
- [FACT] DDG omission was default-selection bias, not memory failure — user explicitly rejected "I forgot" framing (session 019f8b39).
- [FACT] web-search-prime verified working via history check — session summary.
- [FACT] Full 3-source fan-out never observed on a fresh invocation — AAR for this session.
- [INFERENCE] The NON-NEGOTIABLE language will hold across sessions — plausible but unvalidated.
- [UNKNOWN] Whether DDG returns content on real queries — not tested in this session.
