---
thread_id: 019fa8f8-tp-template-emitter-20260802
parent_handoff_path: P:/docs/handoffs/postsession-20260801/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-08-02T14:57:00-06:00
status: open
handoff_type: implementation
accurate_as_of_head: f7f8706
---

# Handoff: /tp output-template emitter — deferred follow-on work

## Revision history
- 2026-08-03: updated — emitter tested (7 tests pass), code block removed from recommendations, accurate_as_of_head bumped. NEXT-1 (test-fire) still deferred. NEXT-2 (wiki concept) still deferred.

## 1. Objective

Capture the deferred work from the /skill-dev improve /tp session that
shipped the output-template emitter (`tp_output_template.py`) and variant
isolation (`reference/improve-protocol.md`). The shipped changes prevent
format conflation between /tp variants. The deferred items extend the
pattern, validate it live, and decide on a safety net.

## 2. Status

OPEN — emitter + isolation shipped (commit 203b033, /tp v3.6). Four
follow-on items deferred to a future session.

## 3. Producing context

**Incident (2026-08-02):** `/tp improve` produced the `/tp session` output
format (NOTED table + actionable recs) instead of the 4-dimension
improvement table. Root cause: both formats coexist in the 1700-line
SKILL.md; the session format is more frequently invoked, making it
salient in context during /tp improve generation.

**Fix shipped (Approach A + C from /skill-dev analysis):**
- `__lib/tp_output_template.py` — code generates the structural skeleton
  for each variant (--mode improve/session/explore/recap); LLM fills in
  findings content. Prevents the LLM from producing the wrong shape.
- `reference/improve-protocol.md` — improve format isolated to its own
  file so the session format does not contaminate context.
- SKILL.md variant routing table + improve section updated to point to
  both. Version bumped 3.5 → 3.6.

**Design principle:** `[[code-orchestrates-model-judges-skill-scale]]` —
code generates structure, LLM does judgment. The same principle already
applied in `/close` (close_accounting.py), `/model-quota` (fleet_quota.py),
and `/check` (check orchestrator design).

## 4. Remaining work

### NEXT-1: Test-fire emitter on a live /tp improve run

**What:** The emitter is unit-tested (all 4 modes produce correct output,
ruff clean) but has not been test-fired on a real `/tp improve` invocation.

**Why:** The execution-receipts rule (AGENTS.md) requires running executable
artifacts before declaring "done." The emitter is a passthrough script —
the same code-output-passthrough risk applies (the LLM might narrate over
the script output instead of presenting it as the skeleton). The
improve-protocol.md explicitly says "Present the emitter output as your
response skeleton" to counter this, but only a live run confirms the LLM
follows it under closure pressure.

**Acceptance criteria:**
- Run `/tp improve` in a session with enough session-chain content to
  produce real findings
- Verify the output has all 4 dimensions (Efficiency, Effectiveness,
  Insightfulness, Thought-partnership) with item counts
- Verify the completeness counter is present with real numbers (not `___`)
- Verify NO NOTED table or `0 - /go all recommendations` line appears
  (those are /tp session format)

**Effort:** S (happens naturally — no setup needed, just observe the next
`/tp improve` run)

### NEXT-2: Write wiki concept for the output-template-emitter pattern

**What:** Write `P:/.data/wiki/concepts/output-template-emitter-for-multi-variant-skills.md`.

**Why:** This is a transferable skill-design technique, not a /tp-specific
fix. Any multi-variant skill with different output contracts benefits. The
graph projection from the /skill-dev analysis identified candidates:

| Target skill | Why it applies | Integration point | Value |
|---|---|---|---|
| `/aar` | Different phases produce different artifact shapes | Phase output templates | Medium |
| `/go` | Different profiles produce different orchestration output | Profile-specific output rendering | Medium |
| `/review` | Different focus modes produce different findings formats | Findings template per focus | Low (findings format is already uniform) |

**Wiki concept content:**
- Name the pattern abstractly: "output-template emitter for multi-variant skills"
- State the principle: code generates the structural skeleton; LLM fills
  in findings content; variant isolation prevents context contamination
- Reference incidents: this session's /tp improve conflation + the
  fleet_quota.py code-output-passthrough finding (same pattern, different
  surface)
- Falsifier: if the emitter + isolation approach still produces conflation
  after 3+ real invocations, the pattern doesn't work and a different
  approach is needed (validator hook, or splitting /tp into separate skills)
- Link to existing concepts: `[[code-orchestrates-model-judges-skill-scale]]`,
  `[[visible-output-contracts-for-behavioral-skill-steps]]`,
  `[[code-output-passthrough-narration-over-script-output]]`

**Effort:** S (<15 min — the content is already in the /skill-dev analysis
output from this session)

### LATER-1: Build output validator (Approach B) if A+C proves insufficient

**What:** A script that regex-checks the LLM's /tp improve output for all
4 dimensions + completeness counter. Catches wrong format after generation
(before presenting to operator).

**When to build:** Only if NEXT-1 (live test-fire) shows the emitter +
isolation approach still produces conflation after 2–3 real invocations.
The validator is a safety net, not a primary fix — not worth the
maintenance cost preemptively.

**Design (~30 lines if built):**
- Input: the LLM's /tp improve output text
- Check: 4 dimension headers present, completeness counter present, NO
  NOTED table, NO `0 - /go` line
- Output: PASS or FAIL with specific missing elements named

**Effort:** S if needed. Deferred until evidence from NEXT-1 justifies it.

### LATER-2: Run index_skills.py to update the skill catalog

**What:** `python P:/.data/wiki/scripts/index_skills.py` — standard
maintenance after skill edits.

**Why:** The skill catalog should reflect the new files (tp_output_template.py,
improve-protocol.md) and the version bump.

**Effort:** S (one command)

## 5. Key decisions

- **Approach A+C over B or D.** The emitter (A) generates structure
  deterministically; variant isolation (C) prevents context contamination.
  Rejected: validator-only (B) — catches failures but doesn't prevent them.
  Rejected: contrast table (D) — more prose in an already-bloated file.
  Rejected: D+C without code — the failure class is "prose can't bind the
  generation pathway," and the answer is code.
- **4 modes in one emitter, not separate scripts.** The emitter supports
  improve/session/explore/recap via a `--mode` flag. One script is easier
  to maintain than four; the mode dispatch is a dict lookup.

## 6. Source files

- `C:/Users/brsth/.grok/skills/tp/__lib/tp_output_template.py` (NEW)
- `C:/Users/brsth/.grok/skills/tp/reference/improve-protocol.md` (NEW)
- `C:/Users/brsth/.grok/skills/tp/SKILL.md` (MODIFIED: variant table, improve section, version)
- `P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md` (design principle)
- `P:/.data/wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md` (enforcement layer)
- Commit: `203b033`

## Suggested next invocation

```
/go Extend tp_output_template.py to emit session mode skeleton (same pattern as improve mode). Then test-fire: run /tp improve in a session with enough content to produce real findings. Verify the output has all 4 dimensions with item counts and completeness counter — no NOTED table or 0 - /go line.
```
