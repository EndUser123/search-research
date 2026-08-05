# Handoff — Skill pre-check UserPromptSubmit hook + session wrap-up

## Status
RESOLVED — hook built, test-fired, committed. Other open items partially addressed.

## Objective

Build a UserPromptSubmit hook that detects `/<skill-name>` in the operator's
prompt, runs a quick context check, and writes a warning to the TUI scrollback
annotation if something is wrong — BEFORE the agent starts working.

## Design (agreed this session)

The hook uses the proven pattern from `UserPromptSubmit_quota_availability.py`:
fire on prompt, read state from files, write to stderr/exit code for TUI
annotation. UserPromptSubmit stdout is ignored by the model (verified
2026-08-05) — but the TUI annotation IS visible to the operator.

**The three-layer split:**
- **Layer 1 (UserPromptSubmit, pre-response):** operator sees warning in TUI
  annotation → can decide whether to proceed or rephrase
- **Layer 2 (Stop hook quality gates, post-response):** catches missing
  evidence → blocks completion claim
- **Layer 3 (Operator judgment):** catches discuss-instead-of-execute pattern

Layer 1 doesn't reach the model — it reaches the operator. That's the right
split because the operator is the one who can intervene before wasted work.

## What the hook checks

When the operator types `/<skill-name>`:

1. **Skill exists?** — does `~/.grok/skills/<name>/SKILL.md` exist?
2. **SKILL.md stale?** — has it been edited since the session started (mtime)?
3. **Required deps present?** — does `depends_on:` list skills that don't exist?
4. **Session ID available?** — is `$GROK_SESSION_ID` set or derivable?
5. **Quality gates satisfiable?** — do the evidence paths in `quality_gates:`
   frontmatter have any chance of existing (is the artifacts dir present)?

## Execution Status

Updated: 2026-08-05T15:00:00Z
Session: 019fd259-dc0a-7dd0-b0e3-1b0ef17c385d
Agent: grok

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | UserPromptSubmit_skill_precheck.py | ✅ DONE | 7 test scenarios pass; commit 5869b92 |
| 2 | skill-precheck.json registration | ✅ DONE | commit 5869b92 |
| 3 | Hook test-fired | ✅ DONE | nonexistent skill → exit 1 + stderr; valid skill → exit 0; timing 384ms (<500ms target) |
| 4 | Fix ship-rhai broken path (item 5) | ✅ DONE | /go SKILL.md + test file fixed; commit 6ca72ac |
| 5 | Wiki persistence step (item 4) | ✅ DONE | Added to ship-py + ship-rhai SKILL.md; commit 6ca72ac |
| 6 | Ship-py/rhai end-to-end testing (item 1) | ❌ NOT STARTED | Deferred — requires real work to ship |
| 7 | Scanner checks 9-11 broader testing (item 2) | ❌ NOT STARTED | Deferred — run /skill-dev audit-active |
| 8 | Self-improving patterns research (item 3) | ❌ NOT STARTED | Deferred — /www research task |
| 9 | Push unpushed commits (item 6) | ❌ NOT STARTED | Operator decision — shared state |

### Key findings during execution

- **UserPromptSubmit stdout IS ignored** (verified by prior session, confirmed by wiki). The hook targets the OPERATOR via TUI annotation (exit code + stderr), not the model. Exit 1 for critical issues (skill not found), exit 0 for warnings.
- **The hook found a real issue during testing**: `/aar` declares `depends_on: [red-team]` but `red-team` doesn't exist as a skill (deprecated per AGENTS.md). The hook correctly surfaced this.
- **Rhai workflow path was already fixed in HEAD** — the working tree had stale content from a prior session. The test file and /go SKILL.md path refs were the actual stale ones.
- **Wiki persistence as prose, not quality_gate**: adding a hard quality_gate for wiki would be too aggressive (not every ship produces wiki-worthy findings). Conditional prose instruction is the right level.

## Key files

- **Working reference:** `~/.grok/hooks/UserPromptSubmit_quota_availability.py`
- **Registration format:** `~/.grok/hooks/quota-availability-injector.json`
- **Skill catalog:** `P:/.data/wiki/concepts/skill-catalog.md`
- **Quality gates:** `~/.grok/hooks/scripts/quality_gates_frontmatter.py`
- **Wiki concept (verified):** `[[userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build]]`
- **Wiki concept (architecture):** `[[skill-step-enforcement-architecture-grok-build]]`

## Scope

- **In scope:** `~/.grok/hooks/UserPromptSubmit_skill_precheck.py` (new),
  `~/.grok/hooks/skill-precheck.json` (new registration)
- **Out of scope:** modifying quality_gate.py, modifying any SKILL.md

## Handoff is wrong if

- The TUI annotation is too subtle for the operator to notice (test with real prompts)
- The check latency is too high (must be <500ms — the quota hook runs in ~2-4s and it's noticeable)
- The check produces too many false positives (operator starts ignoring it)

## Other open work from this session

This session produced extensive work across multiple domains. Open items for
future sessions:

1. **Ship-py and ship-rhai need real end-to-end testing** — both are built but
   only smoke-tested. Run them on real work to exercise all branches.
2. **Scanner checks 9-11 need testing against more skills** — only tested on
   ship-py and ship-rhai so far. Run `/skill-dev audit-active` to validate
   across the full fleet.
3. **Self-improving patterns research** — the `/www` on "what self-improving
   patterns don't we have yet" was deferred. The prompt for the cold-start LLM:
   ```
   /go Read P:/.data/wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md first,
   then run /www "self-improving AI agent patterns we don't have yet: token
   optimization, agent improvement loops with traces and evals, accumulated
   behavioral data, semantic caching, code mode. What reusable patterns should
   we add to our wiki and skills?"
   ```
4. **Ship-py wiki persistence gap** — Check 11 (NO-WIKI-PERSISTENCE) flagged
   both ship skills. Add a wiki-write step to both.
5. **Ship-rhai broken path** — the Rhai script references `~/.grok/skills/ship/__lib/ship_receipt.py`
   but the skill was renamed to `ship-rhai`. The scanner's CROSS-SKILL-DEP check
   caught this — fix the path reference.
6. **Unpushed commits** — both repos have significant unpushed work. Push when ready:
   ```powershell
   git -C P:/ push origin main
   git -C C:/Users/brsth/.grok push origin main
   ```
