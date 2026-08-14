---
title: "does this seem like a good plan?"
date: "2026-07-11"
mode: "COPILOT"
uuid: "f8f2d3e9-f747-4483-9abd-de4ee7a4a851"
entry_count: 1
---

## Human

does this seem like a good plan?

## Assistant

Overall this is a very solid, defensible plan for adding external delegation to Codex; it’s unusually thorough on contract separation, safety, containment, and test‑driven rollout, and is “good” in the sense of being implementable and red‑team aware.[1]

Below I’ll walk through what’s strong, what I’d tweak, and concrete next steps.

## High‑level assessment

The plan clearly defines: a versioned packet contract, result contract, subprocess runner, failure classifier, CLI, skill wiring, and a staged rollout with hard red‑team gates before write access.  It also explicitly treats “default routing” and “write delegation” as post‑gate states, which aligns with your epistemic constraints and avoids premature automation.[1]

From an architecture and safety perspective, I’d rate this high confidence (≈0.8) for achieving safe read‑only delegation and medium confidence (≈0.6–0.7) for write containment until the Tier 2 worktree mechanics are actually implemented and tested.[1]

## Strengths of the plan

### Clear separation of concerns

- Contract vs execution: `validatePacket` and `validateResult` live in a separate contract module, cleanly separating parent judgment from worker execution.[1]
- Prompt vs runner vs failure classifier: prompt rendering, failure classification, and command building are distinct interfaces (`renderPrompt`, `classifyFailure`, `buildCommand`, `runPacket`), which makes behavior easier to test and harden independently.[1]

This modularity is exactly what you want for later plugging in other workers (e.g., local LLM harnesses, additional providers) without touching the safety core.[1]

### Test‑first, adversarial mindset

- Each task starts with “write failing tests, run them, then implement,” including adversarial tests in Task 5 (task‑id traversal, malformed markers, invalid timeouts, arbitrary env, scope escape, etc.).[1]
- Red‑team findings from the existing skeleton (Windows `.cmd` EINVAL, result validator converting failed to success, advisory path scope) are explicitly captured and directly addressed in Task 5.[1]

This aligns well with your “aggressive error‑catching and pre‑mortem analysis” habit and gives you a concrete verification harness before flip‑to‑default.[1]

### Explicit containment tiers

You define three clear tiers:[1]

- Tier 0: trusted, non‑critical full‑access execution with headless auto‑approval.[1]
- Tier 1: disposable staging tree with only declared paths; read‑only tasks run there; artifacts in controlled state root.[1]
- Tier 2: disposable worktree or equivalent OS‑enforced boundary for writes, with post‑execution path verification and rejection if boundary can’t be created.[1]

Crucially, you:

- Escalate unknown sensitivity to Tier 1.[1]
- Require Tier 2 for any write.[1]
- Refuse to treat prompt text or worker permissions as proof of isolation.[1]

From a safety design standpoint, that’s very strong — it decouples UX labels (“read‑only”) from actual enforcement and makes boundary creation a prerequisite for write delegation.

### Strong global constraints and evidence capture

The global constraints are well‑chosen:[1]

- Default worker mode is read‑only; write packets must have `write_scope` and `isolated_cwd` or be rejected.[1]
- No editing of `.claude`, `.pi`, `.opencode`, or repo root unless named.[1]
- No reading or logging of API keys, auth files, `.env`, or provider credentials.[1]
- Every invocation writes raw stdout, raw stderr, packet, normalized result, and an attempt manifest under `.codex/state/external-delegation/<task_id>/`.[1]
- Raw model prose is never accepted as a successful packet; structured result marker with JSON is required.[1]

This gives you a robust audit trail and aligns with your epistemic validation goals: every attempt is evidence‑backed, replayable, and classified.

### Sensible retry and failure classification

- Retry is limited to read‑only infrastructure failures and uses fallback worker/model; it is explicitly forbidden for writes or semantic/contract errors.[1]
- Failure precedence order is deterministic: timeout, command missing, auth/quota, context limit, provider unavailable, protocol error, non‑zero exit, unknown.[1]

That prevents “try again” from masking structural issues and makes failure analytics meaningful.

## Areas I’d tighten or clarify

Most of these are “good plan, but clarify the exact enforcement and contracts.”

### Result contract robustness

You already require:[1]

- Valid `status` in `ok|failed|blocked`. [1]
- `failure_class` string for all results.[1]
- `result_payload` object for `status="ok"`.[1]
- Task 5 upgrades `validateResult(result, outputSchema)` to require every declared output field and exactly one marker.[1]

I would explicitly bake into the contract:

- That worker status (`failed`, `blocked`) is authoritative and cannot be converted to overall success even if some fields look okay.[1]
- That any mismatch between `output_schema.required` and payload keys is a contract failure, not a best‑effort parse; this is hinted, but making it “no partial success” avoids gray zones.[1]

You’re already heading there in Task 5; the plan is good, but this part is where subtle regressions can creep in, so you might add one more adversarial test: “worker returns status 'failed' but also a plausible payload; ensure overall `ok` is impossible.”[1]

### Packet validation and classification

You define required fields and minimal validation now, and plan to tighten later with:[1]

- Safe task‑id regex (e.g. `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`).[1]
- Bounded integer timeout and output limits.[1]
- Valid fallback worker/model pairs.[1]
- No caller‑supplied environment map and path traversal rejection prior to spawn.[1]

Given your threat model, I’d consider moving some of these “Task 5” items earlier, especially:

- Disallowing arbitrary env overrides and path traversal.
- Timeout and output size limits.

These are cheap to implement and significantly reduce blast radius even in read‑only mode (e.g., runaway stdout or `find` over huge trees). But as long as Task 5 is a hard gate before any default use, the plan is still acceptable.

### Windows process launching complexity

You call out a real issue: `.cmd` with `shell:false` returning `EINVAL`, and plan to fix by preferring underlying executable or a carefully quoted `ComSpec` wrapper, including tests for spaces/quotes in arguments.[1]

Given your heavy Windows usage, this is the main “engineering risk”:

- The plan is correct directionally, but the risk of subtle quoting/encoding bugs is non‑trivial.
- I’d add one more acceptance condition: a regression test ensures `runPacket` behaves identically on at least two representative commands for both PI and OpenCode (e.g., listing files, running `npm test`) with spaces in paths and prompt text.[1]

Your existing Task 5 already mentions testing arguments containing spaces, quotes, and prompt text; that’s good, but you might explicitly require cross‑platform parity (same normalized result shape on macOS/Linux vs Windows) if you care about portability later.[1]

### Containment tiers: implementation vs spec

Spec is strong, but actual enforcement will hinge on:

- How you materialize only declared paths into the Tier 1 staging directory.
- How you construct a Tier 2 worktree or equivalent boundary (e.g., `git worktree`, separate repo root, or OS‑level sandbox) and verify changed paths.[1]

Task 5 Step 5 outlines behavior well, but I’d recommend:

- Planning a small library (or at least a dedicated module) for path resolution and tree building, since containment shows up in multiple places (packet validation, runner, artifact storage).[1]
- Adding explicit adversarial tests for “write‑scope escape” that simulate a worker that tries to write just outside the allowed scope; you already mention this test, which is good.[1]

Given that write mode is blocked until isolation exists, the plan is safe: nothing can write until this is solved. So even if Tier 2 takes longer, you’re structurally protected.

## Plan completeness vs your goals

Relative to your stated interests and habits:

- Agentic system design: The plan gives Codex a skill that classifies tasks, generates packets, delegates only bounded low‑ambiguity work, and independently verifies before accepting results. That matches your “parent/worker” and “epistemic audit” patterns.[1]
- Cost and routing: OpenCode is preferred for subscription‑backed mainstream providers, with PI as fallback for custom, llama.cpp, and programmable extensions. This keeps cost/routing flexible and centralized in one package.[1]
- Epistemic validation: Evidence capture per attempt, strict contracts, non‑prose result acceptance, and adversarial tests for correctness all align with your epistemic validation focus.[1]

The main “gap” vs some of your more advanced interests (multi‑agent debate, self‑learning, behavior distillation) is that this bridge is largely “single worker” and procedural. It does not attempt:

- Multi‑worker redundancy or cross‑verification (e.g., run PI and OpenCode both on the same packet for contentious tasks).
- Automated skill improvement based on failure classification or artifacts.

I don’t think that’s a flaw — it’s appropriate scope for a first delegation bridge. But if you want this system to be a stepping stone for your self‑learning experimentation, you might later add:

- A simple feedback loop where repeated failures for a specific task type influence routing or packet templates.
- Optional “double‑execution” for high‑risk read‑only tasks to compare worker outputs.

Not necessary now; more of a roadmap note.

## Concrete next steps

Given the plan, I’d suggest:

1. **Finish Task 5 before any default routing or write enablement.**  
   Treat Task 5’s adversarial tests as non‑negotiable gates; no “beta default” until all pass on Windows.[1]

2. **Pull a few Task 5 validations earlier (if you have capacity).**  
   - Enforce safe task‑id and disallow arbitrary env in the current contract.[1]
   - Cap timeout and output size now, even for read‑only.[1]

3. **Implement Tier 1 staging first, then Tier 2.**  
   - Tier 1 gives you immediate containment for sensitive read‑only work and is much simpler than a worktree.[1]
   - Tier 2 can follow with a more thorough design (likely using `git worktree` or a dedicated “sandbox root”).

4. **Add a small “threat model” doc section to README.**  
   You already plan to document exit codes, containment tiers, and safe defaults; adding a brief threat model (“what can go wrong, and how this package mitigates it”) will be useful later when you revisit this.[1]

In terms of your core question—“does this seem like a good plan?”—yes, it’s well above typical practice for this kind of delegation bridge, and structurally aligned with your preferences for evidence, safety, and incremental rollout.[1]

To tune it for your immediate use: what’s your highest‑priority outcome right now—safe read‑only delegation for Codex, or end‑to‑end write containment so you can let external workers refactor files? 
