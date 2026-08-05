# /www SKILL.md Consolidation

## Status
OPEN — ready for execution

## Session
session-019fcd47 (2026-08-04/05)

## Objective

Consolidate `/www` SKILL.md from 1,177 lines to a size where a fresh agent executes all applicable phases without forgetting any. The A/B test (2026-08-04) proved 8/21 phases were skipped, 2 forgotten entirely. This is NOT an arbitrary line-count cut — it's targeted fixes based on the A/B test's per-phase breakdown.

## Evidence

- A/B test report: `P:/tmp/www-abtest-report.md`
- /tp critique: 2/2 lens convergence on REVISE (DeepSeek + Codex)
- Prior art: `research-vs-design-vs-architect-skills-and-www-self-assessment.md` (2026-07-26) — warned about bloat at 585 lines

## Scope

### 1. Compress over-specified procedures (3 items)
- Cross-session research thread tracking: 5 sub-steps → "check ledger dir for prior runs on this domain" (1 line)
- Reference-class calibration: 5 sub-steps → "check ledger for prior research quality on this domain" (1-2 lines)
- Self-Ask decomposition gate: 4 questions → "compare decomposition against breadth scan results; add any missed sub-classes" (1-2 lines)

### 2. Move depth=deep-only content to reference file
Create `reference/deep-mode-extensions.md` containing:
- Round 2.5 selective ingestion (trigger tables, hard skips, caps)
- Round 2.5b citation chaining
- ACH matrix detail (evidence × hypothesis table)
- Phase 3.25 applicability gate formal tables
- Round 3.5 host invariant check detail

### 3. Relocate post-write phases to /wiki
Phase 3.5 (research thread surfacing) and 3.6 (epistemic debt tracking) are post-write bookkeeping. They got forgotten in /www because they happen after the wiki-write handoff. Move them to `/wiki`'s post-write procedure.

### 4. Cut provenance
Remove ~150 lines of enhancement-batch history from the SKILL.md body. Git history is the changelog.

### 5. Fix the ceremony table
Enumerate ALL sub-rounds in the ceremony table so the agent doesn't cross-reference between two sections. Currently the table lists which to skip but doesn't mention Round 2 (discovery), 3.25, or 3.5 by number.

### 6. Compress remaining prose
- Source deduplication: 10 lines → 3 lines ("dedup by normalized URL before synthesis")
- Reddit tiering: 40 lines → 5 lines ("use MCP for high-value, DDG for exploratory")
- Host invariant check: 20 lines → 2 lines ("grep wiki for host invariants before persisting")
- Multi-artifact routing: 15 lines → 2 lines ("suggest /handoff if ≥2 HIGH-confidence recommendations")

### 7. Remove copyable checklist OR phase descriptions
The A/B agent said having both caused reconciliation overhead. Keep one — the phase descriptions (they're the procedure; the checklist is the duplicate).

## Acceptance criteria

1. Fresh agent runs /www on a topic and executes ALL applicable phases without forgetting any
2. Re-run the A/B test topic ("AI agent memory systems") and compare friction report to baseline
3. Core workflow phases (1a, 1b, 1.5, 2, 2b, 3) remain fully functional
4. Deep-mode content is accessible via `reference/deep-mode-extensions.md` when depth=deep
5. Post-write phases (thread surfacing, epistemic debt) run via /wiki, not /www

## Verification path

1. After consolidation, paste the A/B test prompt (from session-019fcd47) into a fresh session
2. Compare the new friction report to `P:/tmp/www-abtest-report.md`
3. Target: 0 forgotten phases, <3 skipped (only correctly-depth-gated ones)

## Files to modify

- `~/.grok/skills/www/SKILL.md` — main consolidation target
- `~/.grok/skills/www/reference/deep-mode-extensions.md` — new file (deep-mode content)
- `~/.grok/skills/wiki/SKILL.md` — add post-write thread surfacing + epistemic debt (relocated from /www)

## Constraints

- Do NOT change the core workflow (Phase 1a → 1.5 → 2 → 2b → 3)
- Do NOT remove functionality — move to reference or compress
- Do NOT add new phases
- Follow AGENTS.md file editing protocol (read → edit → verify)

## Claim

Claim this handoff with:
```powershell
python ~/.grok/skills/handoff/__lib/claim_handoff.py P:/docs/handoffs/www-consolidation-20260805/HANDOFF.md --session $env:GROK_SESSION_ID --host grok
```
