---
thread_id: ship-py-mandatory-step-gate-20260806
parent_handoff_path: none
current_session_id: 019fcd47-0d6d-7dc0-bb6d-acd9c0bf5f45
parent_session: none
current_terminal_id: noterm
produced_at: 2026-08-06T00:30:00Z
last_updated_by: 019fcd47-0d6d-7dc0-bb6d-acd9c0bf5f45
last_updated_at: 2026-08-06T00:30:00Z
status: resolved
handoff_type: investigation
accurate_as_of_head: 34e15a811390441a5d940c40c2fe33560c6d9ce8
---

# Handoff — ship-py mandatory-step-enforcement gate

## 1. Objective

Add a state-machine gate to `ship_orchestrator.py` so the `verdict` phase refuses to produce SHIP DONE if the `review` phase was never run — preventing the LLM from skipping review and declaring success.

## 2. Status

RESOLVED — both TP-01 and TP-02 implemented in session 019fd9ae (commits d1fd2ac, a9ac479, 355cd43 in ~/.grok). The verdict gate blocks SHIP DONE when review_findings missing on non-health-check runs. cmd_fix and cmd_merge were also added in the same session (closing the missing-phases gap from ship-py-hardening-20260805). 18 tests pass.

## 3. Producing context

- **Date:** 2026-08-05/06
- **Session:** 019fcd47-0d6d-7dc0-bb6d-acd9c0bf5f45
- **Terminal:** noterm

## 4. Read-first list

1. `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` — the orchestrator with existing validation code (lines 189-206: file existence, JSON parse, schema check)
2. `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` — prescribes the state-machine gate pattern
3. `P:/.data/wiki/concepts/llm-text-degeneration-and-output-validation.md` — documents the incident that surfaced this gap (architecture review agent produced degenerate output, LLM skipped the review checkpoint)
4. `P:/.data/wiki/concepts/code-output-passthrough-narration-over-script-output.md` — documents the chronic pattern (5+ instances of LLM skipping mandatory steps under closure pressure)

## 5. Verified facts

- [FACT] `ship_orchestrator.py` lines 189-206 already implement output validation: checks findings file existence, JSON parseability, and schema (`bugs`, `risks`, `suggestion` keys). Source: read during this session.
- [FACT] The `cmd_verdict` function derives the ship receipt from state but does not check whether `review_findings` exists in state. Source: code inspection.
- [FACT] The LLM (this session) ran `/ship-py detect`, spawned review agents, then jumped to "SHIP DONE" — skipping the `review` and `verify` subcommands. The completion validator code existed but was never invoked.
- [FACT] Option A (Python controls the agent loop) is structurally impossible on Grok Build — `spawn_subagent` is a tool only the LLM can call, not Python subprocesses. Source: platform architecture.
- [FACT] PostToolUse hooks cannot target `spawn_subagent` specifically — the event fires on all spawns, and there is no per-spawn context to distinguish ship-py review from other spawns. Source: /tp critique.
- [FACT] The wiki concept `mandatory-step-enforcement-code-over-prose.md` prescribes this exact fix: state-machine guarded transitions where the next phase refuses to run if the prior phase's state requirements aren't met.

## 6. Current state

**Investigation done, implementation not started.** The fix is well-defined:

The `cmd_verdict` function in `ship_orchestrator.py` should check:
1. `state["phase"]` must be `"verify"` (or `"review"` if verify is optional)
2. `"review_findings"` must exist in state (unless health-check mode)
3. If either fails, print: "Cannot produce SHIP DONE: review phase was not run. Run `python ship_orchestrator.py review --findings-file <path> --agent-count N` first."
4. Exit non-zero.

This is ~10-15 lines of code. The state tracking already exists — each subcommand sets `state["phase"]` on entry. The validation infrastructure already exists (lines 189-206). The gate is a new check in `cmd_verdict` that uses existing state.

## 7. Task packets

### TP-01: Add verdict-phase gate to cmd_verdict
- **Goal:** `cmd_verdict` refuses to produce SHIP DONE if `review` was never run
- **In scope:** `ship_orchestrator.py` `cmd_verdict` function only
- **Out of scope:** SKILL.md changes, new hooks, pipeline restructuring
- **Files / anchors:** `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` — `cmd_verdict` function
- **Acceptance:** Running `python ship_orchestrator.py verdict` without first running `review` produces a clear error message and exits non-zero. Running `verdict` after `review` succeeds normally.
- **Falsifier:** The LLM can still claim "done" in prose without the receipt artifact — the gate prevents the receipt, not the prose claim. A Stop hook checking for the receipt artifact would be the next escalation if the prose-only claim recurs.
- **Verification level:** UNIT_TEST — test the gate logic directly

### TP-02: Add SKILL.md instruction to invoke review subcommand
- **Goal:** SKILL.md explicitly says "MUST run `review` subcommand after spawning agents, before verdict"
- **In scope:** `~/.grok/skills/ship-py/SKILL.md` — review phase section
- **Out of scope:** Other skills
- **Acceptance:** SKILL.md review section includes the mandatory command with expected arguments
- **Falsifier:** Prose instruction may not fire under closure pressure (documented in 5+ wiki concepts). The code-level gate (TP-01) is the structural backstop.

## 8. Open decisions

None. The investigation resolved all alternatives:
- Option A (Python controls loop): **REJECTED** — impossible on Grok Build
- Option B (PostToolUse hook): **REJECTED** — wrong event, over-broad, race condition
- Option C (state-machine gate): **SELECTED** — matches workspace pattern, uses existing infrastructure

## 9. Hard constraints

- Do NOT restructure the pipeline into a single-command flow — impossible on this platform
- Do NOT add PostToolUse hooks targeting spawn_subagent — they can't distinguish ship-py reviews from other spawns
- The gate must use existing state tracking — don't add new state mechanisms

## 10. Cross-reference couplings

- `mandatory-step-enforcement-code-over-prose.md` → prescribes this exact fix pattern. If the concept is retired, this handoff loses its design rationale anchor.
- `llm-text-degeneration-and-output-validation.md` → documents the incident that surfaced this gap. The completion validator code at lines 189-206 is the reference implementation cited in the concept.
- `code-output-passthrough-narration-over-script-output.md` → documents the chronic pattern (LLM skipping mandatory steps). This gate is one instance of the structural fix that concept prescribes.

## 11. Other outstanding streams (not handed off)

- **Chrome ACP P11 review finding** — 1 genuinely open review finding from background triage (9/10 reviews verified as CLOSE, this is the 1 HANDOFF). The finding documents 4 blocking bugs in P11 persistent-process lifecycle at `P:/.artifacts/console_29846765-0c74-48a2-a169-2fc1/grok-review/chrome-acp/20260730-093720/FINDINGS.md`. Reviewer recommended reverting P11 entirely. Open — needs its own handoff if pursued.

## 12. Explicit non-goals

- Do NOT build degenerate-output detection (repetition ratios, unique-token thresholds) — the file-existence check in the existing validator is sufficient
- Do NOT add input-size guards for review agents — the root cause was stochastic decoder loop, not input size
- Do NOT add prose-only fixes ("you MUST run review") without the code-level gate

## 13. Resumption protocol

1. Read `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` — focus on `cmd_verdict` function
2. Add the state check: if `"review_findings"` not in state and not health-check mode, refuse SHIP DONE
3. Test: `python ship_orchestrator.py verdict` without prior `review` → should error
4. Test: `python ship_orchestrator.py review --findings-file <test.json> --agent-count 1 --failed-count 0` then `verdict` → should succeed
5. Commit with: `fix: add mandatory review-phase gate to ship_orchestrator cmd_verdict`

## 14. Suggested next invocation

```
/go implement the ship-py mandatory-step gate handoff at P:/docs/handoffs/ship-py-mandatory-step-gate-20260806/HANDOFF.md

Two task packets:
- TP-01: Add state check to cmd_verdict (code change)
- TP-02: Add SKILL.md instruction (doc change)

Both are small (~10-15 lines each). The investigation is complete — all alternatives were evaluated and rejected with evidence.
```

## 15. Last user message (verbatim)

> "/www prove or disprove the optimal solution."

(This was the /www research that disproved the prose-only fix and confirmed the structural fix.)

## 16. Epistemic labels

- [FACT] completion validator exists in ship_orchestrator.py lines 189-206 — verified by reading code
- [FACT] LLM skipped review phase this session — verified by transcript observation
- [FACT] Option A is impossible on Grok Build — verified by platform architecture
- [FACT] PostToolUse can't target spawn_subagent specifically — verified by /tp critique
- [INFERENCE] the state-machine gate will prevent future skips — high confidence based on 5+ documented instances of the pattern and the workspace's own prescribed fix

## 17. Suggested skills for next session

- `/go` — this handoff has 2 implementation task packets ready to execute
- `/check` — after implementation, verify the gate works (unit test + live behavior)
- `/review --focus architecture` — the change touches the ship pipeline dispatch chain

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-06T00:30 | 019fcd47... | created — investigation complete, implementation ready |
| 2026-08-06T09:00 | 019fcd47... | updated — /review found 4 bugs in skill_precheck.py (COR-001/002/004/005), all fixed in commit 0c06ba6. The hook regex and terminal-marker logic were corrected. These fixes are in the same file as the terminal-output detection heuristic and should be verified together when the gate is implemented. |
