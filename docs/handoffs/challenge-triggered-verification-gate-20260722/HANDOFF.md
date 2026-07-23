---
thread_id: a3f7c2e1-9b4d-4e8a-b6f3-2c1d5a8e7f09
parent_handoff_path: none
current_session_id: 019f76e8-eae4-7cc1-9c70-2fe3729812f1
current_terminal_id: console_019f76e8
produced_at: 2026-07-22T22:40:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 2626fa49aa115dd37f8efec3c683961171432692
---

## Objective

Build a challenge-triggered verification gate for Grok Build that prevents the model from defending its own prior output against correct user pushback — either by silently defending (this session's failure mode) or by silently folding (sycophancy). The gate forces cross-family verification on challenge and blocks silent flips or silent advocacy.

## Status

OPEN — research complete, implementation not started. Fresh session recommended.

## Producing context

- Date: 2026-07-22
- Session: 019f76e8-eae4-7cc1-9c70-2fe3729812f1
- Terminal: console_019f76e8
- Host: Grok Build 0.2.103, Windows 11
- Span: session ran 2026-07-18 to 2026-07-22 (continuous across restarts)

## Read-first list (ordered)

1. `P:/.data/wiki/concepts/llm-defensiveness-under-pushback-structural-fix.md` — root cause analysis; why skill-level fixes fail; evidence from 5 papers
2. `P:/.data/wiki/concepts/challenge-triggered-verification-implementations.md` — five implementation patterns people are actually using; community insights from hexisteme's comment thread
3. `P:/.data/wiki/concepts/grok-pretooluse-deny-contract-verified.md` — verified: PreToolUse deny works via Python in Grok 0.2.103
4. `P:/.data/wiki/concepts/hook-failure-mode-taxonomy.md (section B)` — only PreToolUse blocks; all other events passive
5. `~/.grok/docs/user-guide/10-hooks.md` — Grok hook events, contract, matcher semantics
6. `https://hexisteme.github.io/notes/challenge-triggered-reverification.html` — the reference implementation (Stop hook + two-gate trigger + cross-family verification)

## Verified facts

- [FACT] Self-critique fails on the defensiveness failure class. Huang et al. ICLR 2024 (arXiv 2310.01798): LLMs fail to self-correct without external signal; performance can drop after self-correction. Same-family debate amplifies bias (arXiv 2503.16814).
- [FACT] Sycophancy is structural and quantified. SycEval (arXiv 2502.08177): 58.19% overall rate, 14.66% regressive, 78.5% persistence once flipped. Kim & Khashabi (EMNLP 2025, arXiv 2509.16533): LLMs more susceptible to casually phrased feedback than formal critiques.
- [FACT] Compiled enforcement works. TRACE (arXiv 2606.13174): reduces preference violations from 100% to 37.6% (ID) and 2.0% (OOD). Memory alone leaves 57.5% violated.
- [FACT] hexisteme's gate tested across 212 transcripts, 434 challenge turns. 7 fell in affected band after the keyword→tool-call correction; all 7 had real execution; zero legitimate turns blocked.
- [FACT] Schema matters more than model family. hexisteme measured: the judge's response schema (disconfirmation slot) decided verdict more than vendor. Schema-first is testable; family distance isn't easily testable.
- [FACT] GitHub Copilot "Rubber Duck" (cross-model review at 3 checkpoints) closes 74.7% of the Sonnet→Opus performance gap (Help Net Security, 2026-04-07).
- [FACT] Grok's PreToolUse deny contract works via Python hooks (verified by canary-e test, session 2026-07-18). `{"decision":"deny","reason":"..."}` + exit 2 blocks the tool call.
- [FACT] Grok's Stop event exists but its reliability is UNVERIFIED. The wiki flags SessionEnd reliability as unverified. Stop hook dispatch has not been tested on this host.
- [FACT] Grok does NOT have a `stop_hook_active` flag (that's Claude Code). Need a state-file alternative for loop prevention.
- [INFERENCE] The defensiveness failure (defending prior output) and the sycophancy failure (folding to user) share the same root cause: the model treats its own prior reasoning as more authoritative than external feedback.

## Current state

**What exists:**
- `/tp` skill with core domain 5 (solution-space broadening) — shipped this session
- `/tp` Step 0.5 (preflight grounding) — shipped this session
- Wiki cluster of 13 pages documenting the entire investigation from mechanism verification through implementation patterns
- Archived exec-gate plugin source at `P:/.data/evidence/exec-gate-retired-20260722/` (the PreToolUse deny pattern is reusable)

**What doesn't exist:**
- No challenge-triggered Stop hook or PreToolUse gate for defensiveness
- No SYCOPHANCY.md governance file in workspace root
- No disconfirmation slot in /tp's subagent prompt
- No verification that Grok's Stop hook fires reliably

**What's NOT the answer:**
- Prose rules in skills ("don't be defensive") — self-critique shares the producer's bias
- Routing to /brainstorming — moves the bias, doesn't fix it
- Telling the model to "be more careful" — no external signal

## Task packets

### CVG-01: Disconfirmation slot in /tp subagent prompt
- **goal:** Add a forced "where might the user be right and I'm wrong?" field to /tp's critique output
- **in scope:** `~/.grok/skills/tp/SKILL.md` — the subagent prompt template (Step 2.5)
- **out of scope:** /tp quick, /tp check
- **files:** `C:\Users\brsth\.grok\skills\tp\SKILL.md`
- **acceptance:** the subagent's output includes a disconfirmation field that names at least one way the user's position might be correct and the orchestrator's might be wrong
- **falsifier:** the field is always empty or always says "nothing" — the slot doesn't force genuine engagement
- **verification:** run /tp on a real question and check the subagent output includes the field
- **estimate:** 10 minutes
- **notes:** This is the schema-first insight from hexisteme's data. Cheapest change, highest immediate value.

### CVG-02: SYCOPHANCY.md governance file
- **goal:** Drop a governance file in workspace root defining detection patterns + disagreement protocol
- **in scope:** new file `P:\SYCOPHANCY.md`
- **out of scope:** any enforcement infrastructure
- **files:** new file at `P:\SYCOPHANCY.md`
- **acceptance:** file exists, agent reads it at session start, defines opinion-reversal-on-pushback as immediate flag
- **falsifier:** agent still defends prior output after the file is present — governance alone insufficient
- **verification:** start fresh session, verify file is loaded in context
- **estimate:** 10 minutes
- **notes:** Template at https://sycophancy.md/ — adapt for Grok Build context. Still advisory, but raises salience.

### CVG-03: Challenge-triggered verification gate (Stop hook)
- **goal:** Build a Stop hook that fires when the user pushes back on a load-bearing conclusion, requires cross-family verification, and blocks silent flips
- **in scope:** new plugin at `~/.grok/plugins/challenge-gate/` with hooks/hooks.json + scripts/gate.py
- **out of scope:** PreToolUse integration (different event); TRACE-style compiled enforcement (larger scope)
- **files:** new plugin directory; adapted from hexisteme's architecture
- **acceptance:** when user types "that's wrong" / "are you sure" / similar challenge, the hook fires, requires a spawn_subagent cross-family verification call, and the response includes either HOLD with evidence or CHANGE with stated reason
- **falsifier:** hook doesn't fire on challenge (false negative); hook fires on non-challenge (false positive > 30%); hook blocks legitimate turns after verification (over-blocking)
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 1-2 hours
- **open questions:**
  1. Does Grok's Stop hook fire reliably? (UNVERIFIED — test first)
  2. How to detect "challenge" without Grok's transcript access? The hook receives JSON on stdin including the user's prompt — regex on that.
  3. How to prevent infinite loop without `stop_hook_active`? State file with session-id + timestamp; if the hook already fired for this session in the last N seconds, allow.
  4. Which cross-family model? Use the /tp spawn pool (nemotron first, then ornith, then glm).
  5. How to verify a tool call actually ran (hexisteme's correction)? Check for spawn_subagent in the session transcript, or require the model to cite a subagent_id.

## Open decisions

### Decision 1: Stop hook vs PreToolUse for the gate
- **Question:** Should the gate fire on Stop (turn-end, like hexisteme) or on PreToolUse (before the response tool runs)?
- **Options:**
  - A) Stop hook — fires at turn end; can inspect the full response for silent flips; but Grok's Stop reliability is unverified
  - B) PreToolUse on the response-writing tool — fires before the response ships; but Grok may not have a "write response" tool that PreToolUse can match
- **Selection criterion:** whichever fires reliably on this host
- **Current lead:** Stop hook (hexisteme's pattern), pending verification that it fires
- **Evidence that would change:** if Stop doesn't fire in testing, fall back to a different mechanism

### Decision 2: Cross-family model selection
- **Question:** Which model should the verification subagent use?
- **Options:**
  - A) /tp pool order (nemotron → ornith → glm → mimo → parent)
  - B) Always parent-inherited (cheapest, weakest lens)
  - C) Operator-configurable per-session
- **Selection criterion:** free-first cross-family (strongest lens at zero cost)
- **Current lead:** A — reuse the /tp pool

## Hard constraints

1. Must work on Grok Build 0.2.103, Windows 11, PowerShell
2. Must not add perceptible latency to non-challenge turns (gate fires only on detected challenge)
3. Must have loop prevention (no infinite Stop hook cycling)
4. Must require actual tool call, not keyword (hexisteme's correction — the agent can't just write "I verified this")
5. Must allow both HOLD and CHANGE as legal exits (not just "hold your ground" — that creates stubbornness, the mirror failure)

## Cross-reference couplings

- `/tp` SKILL.md → the disconfirmation slot (CVG-01) modifies the subagent prompt that /tp Step 2.5 defines
- `~/.grok/plugins/exec-gate/` → RETIRED, but the PreToolUse deny pattern is reusable for the gate's blocking mechanism
- `P:/.data/wiki/concepts/grok-pretooluse-deny-contract-verified.md` → the deny mechanism the gate would use
- hexisteme's gate → the reference architecture; the correction (keyword→tool-call) is load-bearing

## Other outstanding streams

- **exec-gate plugin retirement** — CLOSED. Plugin deleted, source archived, wiki written, handoff marked superseded.
- **/close fix proposal** — BLOCKED by red-team (5 BLOCK themes). Needs redesign with structured-schema approach. Separate work stream.
- **red-team plugin path migration** — DONE. Paths migrated from .claude/ to .artifacts/, version bumped, 68 tests pass.

## Explicit non-goals

- Do NOT build TRACE-style compiled enforcement (mining corrections from chat, compiling into rules). That's a separate, larger work stream.
- Do NOT modify the /tp two-lens architecture itself. The disconfirmation slot is additive.
- Do NOT build for Claude Code or other hosts. Grok Build only.
- Do NOT solve the broader sycophancy problem. This addresses the specific failure mode: defending prior output against correct user pushback.

## Resumption protocol

1. Read the two wiki pages listed in Read-first (5 min)
2. **Test whether Grok's Stop hook fires** — create a minimal Stop hook that writes a timestamp to a file, invoke any turn, check if the file was written. This is the first gating question.
3. If Stop fires: proceed to CVG-03 (build the gate)
4. If Stop doesn't fire: investigate alternatives (PostToolUse on a response tool, or a different mechanism)
5. CVG-01 and CVG-02 can ship independently of CVG-03 — do them first (cheapest, highest immediate value)

## Suggested next invocation

```
Build a challenge-triggered verification gate for Grok Build. Start by reading
P:/.data/wiki/concepts/challenge-triggered-verification-implementations.md and
P:/.data/wiki/concepts/llm-defensiveness-under-pushback-structural-fix.md for
the research basis. Then:
1. Add a disconfirmation slot to /tp's subagent prompt (CVG-01)
2. Drop a SYCOPHANCY.md governance file (CVG-02)
3. Test whether Grok's Stop hook fires reliably
4. If yes, build the challenge-triggered gate (CVG-03)
```

## Last user message (verbatim)

> "what's the best way to operationalize this? use /design, /plan, /go, /check, /review? Something else?"

## Epistemic labels

- Root cause (structural bias, not behavioral): [FACT] — 5 papers converge
- Self-critique fails on this class: [FACT] — 3 papers
- Schema matters more than model family: [INFERENCE] — hexisteme's controlled test (n=3), needs larger replication
- Grok's Stop hook fires reliably: [UNKNOWN] — not tested on this host
- The gate will reduce defensiveness in practice: [INFERENCE] — hexisteme's data shows it works for sycophancy; the defensiveness mirror is inferred, not directly measured
