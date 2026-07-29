---
thread_id: email-todo-quality-improvements-20260729
parent_handoff_path: none
current_session_id: 019fa276-89c7-7310-b882-096cf67652cf
current_terminal_id: grok-build-terminal
produced_at: 2026-07-29T23:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: e41514c
---

# Email category detection + /todo output quality improvements

## Objective (one sentence)

Add category detection to the email-skill so /todo can surface email items as
decisions (bills, appointments) vs noise (newsletters, promotions), and fix
/todo output quality issues the operator identified.

## Status

OPEN — needs identified and verified from operator feedback. Implementation not
started.

## Producing context

Date: 2026-07-29. Session: 019fa276. Identified during /todo review where the
operator gave detailed feedback on output quality. The email-skill Phase 0
(himalaya + ortie, 3 accounts, scan-inbox returning 45 items) is complete and
committed (commit `1781322`). The gap is between "scanning works" and "the
output is useful for decision-making."

## Read-first list

1. `P:/.agents/skills/email-skill/SKILL.md` — email-skill interface and commands
2. `P:/.agents/skills/email-skill/scripts/email_skill_lib/himalaya.py` — scan_account(), scoring logic
3. `P:/.agents/skills/email-skill/scripts/email_skill_lib/accounts.py` — account config
4. `C:/Users/brsth/.grok/skills/todo/SKILL.md` — /todo skill protocol
5. `C:/Users/brsth/.grok/skills/harvest/SKILL.md` — /harvest (the email check was placed here per operator discussion)

## Verified facts

- [FACT] scan-inbox returns 45 items across 3 accounts (verified: `python email_skill.py scan-inbox --account brsthomson`, 2026-07-29)
- [FACT] All items get imp/urg scores but no category labels (source: himalaya.py scan_account output)
- [FACT] Operator feedback on /todo output: "what newsletters? what bills? what appts? what would I want?" — the output had no categorization
- [FACT] Operator feedback: "DECIDE — this is a statement not a question" — the Hotmail token refresh item was a risk statement, not a decision
- [FACT] Operator feedback: "AT RISK — is this just a notification?" — the deleted-files item was informational, not actionable
- [FACT] Operator feedback: "FLEET STATE — is this in the best spot?" — fleet state in /todo is noise
- [FACT] `/harvest show` produces a flat list; operator asked "what's harvest for? when do we use it?" — the output didn't explain its own value proposition

## Current state

**Email scanning:** fully operational. 3 accounts (a-hominidae, troup-hominidae, brsthomson), OAuth authenticated via ortie, himalaya v2.0 API. Returns scored items.

**What's missing:**
1. **Category detection** — no classification of emails into bills, appointments, newsletters, promotions, security alerts, purchases, personal. Every item is a flat `[review]` or `[respond]` line.
2. **Hotmail token refresh** — auto-refresh is on (`auto-refresh = true` in ortie config) but untested for longevity. If tokens stop refreshing, email scanning breaks silently. No monitoring.
3. **/todo output quality** — four specific problems identified by the operator.

## Task packets

### EC-01: Email category detection

- **goal:** Classify scanned emails into actionable categories so /todo can surface decisions vs noise
- **in scope:** `email_skill_lib/himalaya.py` scan_account() output; possibly a new `categorize.py` module
- **out of scope:** Sending email, folder management, email body fetching (headers only)
- **files / anchors:** `P:/.agents/skills/email-skill/scripts/email_skill_lib/himalaya.py`
- **acceptance:** scan-inbox output includes a category field (bill, appointment, newsletter, promotion, security, purchase, personal). Operator can see "2 bills, 1 appointment, 8 newsletters" summary.
- **falsifier:** Category field is missing or always "review" for all items
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** Category heuristics from sender + subject patterns: ~2-4 hours

### EC-02: /todo output quality fixes

- **goal:** Fix the four /todo output problems the operator identified
- **in scope:** `C:/Users/brsth/.grok/skills/todo/SKILL.md` output format
- **out of scope:** /todo scanning logic (that works fine)
- **problems to fix:**
  1. DECIDE items must be actual decisions with options, not risk statements. If something is a risk, label it RISK not DECIDE.
  2. AT RISK items must be actionable (something to do) not just informational. If it's informational, put it in a NOTES section.
  3. Email items must be categorized (depends on EC-01).
  4. Fleet state does not belong in /todo. Remove it or move to session-start briefing.
- **acceptance:** Next /todo run produces decisions (with options), categorized email items, and no fleet state
- **falsifier:** Output still contains risk-statements-as-decisions, uncategorized emails, or fleet state
- **verification level required:** LIVE_BEHAVIOR (next /todo invocation)

### EC-03: Hotmail token refresh monitoring

- **goal:** Verify auto-refresh works past the 1-hour window, or add monitoring if it doesn't
- **in scope:** ortie config verification, optional monitoring script
- **out of scope:** ortie source code changes
- **acceptance:** After 1+ hour, scan-inbox still returns fresh results on the brsthomson (Hotmail) account
- **falsifier:** scan-inbox returns cached results or errors after token expiry
- **verification level required:** LIVE_BEHAVIOR
- **no_live_run_reason:** Deferred — need to wait >1 hour from last token refresh to test

## Open decisions

1. **Where should email checks live?** Operator discussed /todo vs /harvest. The email-skill is the data source; /todo is the decision surface. No decision made yet.
   - Option A: email check in /todo (it's a "what should I do" question)
   - Option B: email check in /harvest (it surfaces unrealized value)
   - Currently leading: A (/todo), because the operator asked "of /todo and /harvest which do you think an email check should be in" then ran /todo

## Hard constraints

- Email scanning must remain read-only (no sending, no folder changes)
- Category detection must work from headers only (sender + subject), not body content
- /todo output must be scannable in <30 seconds by the operator

## Cross-reference couplings

- `email_skill_lib/himalaya.py` → scan_account() output feeds /todo display
- `/todo SKILL.md` → references email-skill as data source
- `/harvest SKILL.md` → operator considered email check here
- ortie config at `~/.config/ortie/config.toml` → token refresh for all 3 accounts

## Other outstanding streams (not handed off)

- **Harvest skill** — built, tested (81 tests), reviewed 4×, refactored. Fully shipped. 2 OPEN items remain (narrative sufficiency pattern, behavioral detection tiers 3-4).
- **/tp opportunity scan gate** — implemented and closed this session.
- **Close scanner bugs** — fixed by sibling session, handoff closed.
- **SessionStart hook limitation** — documented in wiki concept, no hook built. The file-write alternative (write to a file skills read at startup) is a separate future task.

## Explicit non-goals

- Do not build email sending capability
- Do not restructure the email-skill architecture
- Do not change ortie or himalaya source code
- Do not add email body content fetching (headers only for Phase 1)

## Resumption protocol

1. Read this handoff and `P:/.agents/skills/email-skill/scripts/email_skill_lib/himalaya.py`
2. Start with EC-01: add category heuristics to scan_account() output. Use sender domain + subject pattern matching (e.g., "invoice|bill|payment due" → bill; "appointment|calendar|reminder" → appointment; known newsletter domains → newsletter)
3. Then EC-02: update /todo SKILL.md output format per the four fixes
4. Then EC-03: test Hotmail token refresh after 1+ hour

## Suggested next invocation

```
/go Implement email category detection in email-skill. Read the handoff at
P:/docs/handoffs/email-todo-quality-improvements-20260729/HANDOFF.md for
full context. Start with EC-01 (category heuristics from sender + subject),
then EC-02 (/todo output quality fixes).
```

## Last user message (verbatim)

> "dont' be lazy."

(After providing detailed feedback on /todo output quality, then asking /wiki,
then /harvest, then /handoff. The feedback on /todo output is the load-bearing
context.)

## Epistemic labels

- [FACT] All email-skill and /todo claims verified by tool calls this session
- [FACT] Operator feedback quoted verbatim from user messages
- [INFERENCE] Category heuristics from sender + subject will be sufficient for most emails — some will need body content, but that's a Phase 2 concern
- [UNKNOWN] Whether Hotmail auto-refresh works past 1 hour — needs live test after token expiry window
