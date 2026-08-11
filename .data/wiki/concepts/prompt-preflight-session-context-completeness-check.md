---
title: "Prompt preflight: session-context completeness check before dispatching subagent prompts"
created: 2026-07-30
source: session-019fb189
tags: [prompt-engineering, context-completeness, procedural-verification, reusable-pattern, skill-design, implemented]
summary: >
  Before a skill dispatches a subagent prompt (e.g., /design writer, /go
  implementer, /plan planner), check the prompt against the session transcript
  for missing load-bearing information. This is NOT epistemic reflection ("is
  this prompt good?") — which fails per Huang et al. ICLR 2024. It IS procedural
  verification ("what session facts are NOT in the prompt?") — which works
  because it checks against an external reference (the transcript). The pattern
  is reusable across /design, /plan, /go, /handoff, /refine. Implementation:
  tp_dispatch.py --mode spawn produces the compact bundle for /tp spawn_subagent
  dispatch; the pattern generalizes to any spawn_subagent caller.
agent: grok
host: grok
cognitive_load: 2
verification: implementation-verified
last_re_verified: 2026-08-11
verification_state: tp-dispatch-implemented; multi-skill-adoption-pending
relations:
  - target: wiki/concepts/self-reflection-in-llms-fails-without-external-evidence.md
    type: related — the distinction between epistemic reflection (fails) and procedural verification (works) is why this pattern works
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control.md
    type: extends — adds a new pattern to the catalog
---

# Prompt preflight: session-context completeness check

## Decision context

**Why this was needed:** during session 019fb189's /design run, the operator noticed the firewall subagent prompt was high-quality and asked "did you use /refine?" The answer: the prompt was good because the *operator's* scoping was good — not because the agent did any prompt-quality checking. The operator proposed: "Can /design do a self-reflection step to see if it can make the prompt better before doing design?"

The session's own research ([[self-reflection-in-llms-fails-without-external-evidence]]) says intrinsic self-reflection fails. But the operator's proposal is NOT intrinsic reflection — it's procedural verification against session context. That distinction is exactly what the research says works. The pattern is generalizable: any skill that dispatches a subagent could benefit from checking whether the dispatch prompt contains all load-bearing facts from the session. The cost is low (one grep/scan of the transcript) and the value is high (a subagent that lacks context produces lower-quality output that requires more revision rounds).

## The pattern

```
prompt_preflight(session_context, current_prompt) → enhanced_prompt | original_prompt

1. Extract load-bearing facts from session_context:
   - Decisions made (with rationale)
   - Constraints stated by the operator
   - Evidence gathered (with receipts)
   - Rejected alternatives
   - Open questions

2. Check each fact against current_prompt (semantic match)

3. For each missing load-bearing fact, propose adding it

4. Present: "Original vs Enhanced. <N> session facts missing from prompt. Use enhanced?"
```

## Why it works (per session research)

- Epistemic reflection ("is this prompt good?") → FAILS (Huang et al. ICLR 2024). The model has no reliable signal that it missed something. "Silent divergence" — the model doesn't know it's wrong.
- Procedural verification ("what session facts are NOT in the prompt?") → WORKS. This is the Chain-of-Verification pattern (Dhuliawala et al. 2024): check against an external reference, not against the model's own judgment.
- The session transcript is an external reference; the model's opinion about prompt quality is not.
- This connects to [[convergence-gap-rca-symptom-restatement-toulmin-enforcement]]: the Toulmin COUNTEREXAMPLE field is the same pattern applied to RCA claims — force an external check rather than trusting internal assessment.
- The workspace's evidence-tier system ([[self-reflection-in-llms-fails-without-external-evidence]]) is the same principle applied to causal claims — require external receipts, not self-assessment.
- [[problem-first-systems-decomposition]] is related: understand the full context before generating solutions; the preflight ensures the prompt contains the full context.

## Where it applies

- /design — before spawning the writer
- /plan — before writing the plan from a spec
- /go — before dispatching implementation subagents
- /handoff — before writing the handoff
- /refine — literally IS this pattern already

## Worked example (session 019fb189)

The operator invoked `/design` to restructure /why Steps 9, 11, 12, 14, 16. The dispatch prompt to the firewall subagent included the step numbers, the changes, and the constraint. But it was missing:
- The Hermes benchmark finding (tight feedback loop + Rule of Three)
- The pressure-test results (MECHANISM field is fakeable)
- The research-applicability check pattern (Round 3.25)

These were load-bearing facts from the session that the writer needed. A prompt preflight would have caught them. The prompt was still good (the operator's scoping was excellent), but the writer would have benefited from the full session context — especially the pressure-test failure modes that constrain the design (e.g., "don't rely on MECHANISM field alone; COUNTEREXAMPLE and EVIDENCE are the load-bearing fields").

## Receipts

- Session 019fb189 operator observation: "Did you use /refine or something else to help with it?" — the prompt was good because the operator's scoping was good, not because of a preflight step
- Huang et al. ICLR 2024 (arXiv:2310.01798): intrinsic self-correction fails; the model has no signal that its reasoning drifted
- Chain-of-Verification (Dhuliawala et al. 2024, arXiv:2309.11495): procedural verification works when the check is against an external reference
- Session 019fb189 wiki concept [[self-reflection-in-llms-fails-without-external-evidence]]: documents the reflection-vs-verification distinction with ablation evidence

## Falsifier

If the preflight consistently finds zero missing facts across 10+ real skill dispatches, it's not earning its cost and should be removed. But the cost is so low (~5-10 seconds, a few thousand tokens) that there's no reason to gate it behind a trigger condition — always run it. The cost of a missing fact (a revision round, 5-10 minutes) dwarfs the cost of the check.

## Implementation (shipped 2026-08-05)

**Script:** `~/.grok/skills/tp/__lib/tp_dispatch.py --mode spawn`

**What it does:** produces a compact (~500-800 token) context bundle for
`spawn_subagent` dispatch — verified facts, diff stat, key file paths,
transcript grep terms, and protocol reference (absolute path, not inlined).
The spawned agent uses the bundle as a launchpad and fetches deeper context
via its own tools (read_file, grep, run_terminal_command).

**Why compact, not full-dump:** `spawn_subagent` agents have tools — unlike
CLI dispatch (codex/agy) which starts cold and pays per-tool-call to discover
anything. Over-packing wastes prompt tokens on content the agent can fetch
in one tool call. CLI mode (`--mode cli`) produces the full 4-6K pack; spawn
mode (`--mode spawn`) produces the compact 500-800 token version.

**How /tp uses it:** Step 1 of the SKILL.md references the script. The
parent model runs one command and injects the output into the spawn prompt.
This replaces the previous vague "extract ~500 tokens" prose instruction
that was skipped under closure pressure (observed: agent spawned a /tp
critique agent with a bare text prompt, resulting in 57 tool calls and
10+ minutes of wasted context discovery — the exact failure this pattern
exists to prevent).

## How it differs from /refine

`/refine` takes a rough task and tightens it by inspecting the codebase. This pattern takes a *complete-looking* task and checks it against *session context* — not the codebase. The difference: /refine adds missing scope from the external system; prompt preflight adds missing context from the conversation. Both are procedural verification (external reference check), not epistemic reflection (internal quality assessment).

## What this means for our workspace

1. This is a cross-cutting concern — applies to any skill that dispatches subagent prompts
2. **Always run** — the cost (~5-10 seconds) is negligible; the cost of a missing fact (a revision round, 5-10 minutes) dwarfs it. No gate condition needed.
3. The operator decides whether to use the enhanced prompt — the check suggests, doesn't override
4. The pattern is a structural instance of the procedural-verification principle documented across three session wiki concepts — same underlying mechanism, different application domain

## Re-verification 2026-08-11 (epistemic debt re-audit)

**Audit trigger:** Concept flagged with epistemic debt 0.52 in the cross-concept re-verification sweep (2026-08-11). Verification was `inferred` at creation (2026-07-30) based on the procedural-verification research anchor + a worked example.

**What changed since creation:**

1. **`tp_dispatch.py --mode spawn` shipped (2026-08-05+).** `~/.grok/skills/tp/__lib/tp_dispatch.py` (34KB) implements `pack_context_spawn()` (line 532) which produces the compact ~500-800 token context bundle. The script header and code comments directly cite this pattern: *"Used by spawn mode: the spawned agent has tools and can read full diffs via run_terminal_command. The stat gives it the shape of changes without burning prompt tokens on full diff content."* Initial commit: `23daac9 tp_dispatch: add --mode spawn + f-string fix + 7 unit tests`.

2. **`/tp` SKILL.md Step 1 (line 1174-1194) makes the bundle mandatory.** The mechanical pre-pack call (`python ... tp_dispatch.py --mode spawn ...`) replaces the previous prose instruction "extract ~500 tokens" that was skipped under closure pressure (observed 2026-07-23: agent spawned a /tp critique agent with a bare text prompt, 57 tool calls, 10+ minutes wasted).

3. **Active maintenance commits since initial implementation:**
   - `f496e8b Fix 4 bugs found by parallel /tp self-review (spawn + codex lenses)`
   - `58c73e6 tp_dispatch: anchor-based section replacement + terminal-scoped output + tests (#1, #3, #5)`
   - `5d2cfef tp_dispatch: structural fix — replace tool-access section for CLI dispatch`
   - `2c81495 tp_dispatch: add quota constraint preamble for CLI dispatch (agy/codex)`
   - `3ed2fbf tp_dispatch: session-scoped dispatch artifacts prevent mid-session deletion`

4. **Bundles used across multiple /tp invocations.** tp_dispatch.py produces spawn bundles for /tp's default 3-lens parallel panel (spawn + codex + agy). Per tp SKILL.md line 1411: "Pass the prior finding to the subagent's context bundle — it should verify or disconfirm against current evidence, NOT re-derive from scratch." The bundle is the spawn prompt substrate.

5. **Session-scoped dispatch artifacts (2026-08-08).** `P:/tmp/tp-dispatch-<session-id>/MANIFEST.jsonl` now tracks each artifact, preventing the mid-session deletion failure mode (session 019fe3ff, 2026-08-08). The structural fix is enforced, not just described.

**Debt assessment:** Original debt 0.52 with verification: inferred (procedural-verification anchor + 1 worked example). The pattern has been **implemented, tested, deployed, and actively maintained** — but **only for /tp spawn dispatch**. Multi-skill generalization (`/design`, `/plan`, `/go`, `/handoff`, `/refine`) listed in § "Where it applies" has NOT yet shipped adapters. New assessment: **~0.30**. Verification upgraded from `inferred` → `implementation-verified` (precise label: validated for one deployment, not yet generalized).

**Action taken:** Frontmatter `verification` updated from `inferred` to `implementation-verified`. Added `last_re_verified: 2026-08-11` and `verification_state: tp-dispatch-implemented; multi-skill-adoption-pending`.

**Specific evidence still needed to drop debt below 0.15:**
- Adapter implementations for `/design` writer dispatch, `/plan` planner dispatch, `/go` implementer dispatch, `/handoff` writer dispatch (each requires its own context-packaging logic — /tp's spawn mode may not transfer directly to CLI-only dispatch like /agy)
- A measurement of "facts caught by preflight that would have been missed" across N≥10 dispatches (currently we know the pattern works, not how often it catches things)
- A falsifier check: at least one dispatch where the preflight found >0 missing facts (would confirm the pattern's value vs. always returning empty)

**Companion concept re-audit recommended:** `[[self-reflection-in-llms-fails-without-external-evidence]]` is the procedural-verification anchor this concept extends; its evidence base (Huang et al. ICLR 2024, Chain-of-Verification 2024) is more durable and should already be `multi-source-verified`. Re-verify in same sweep if not already at low debt.
