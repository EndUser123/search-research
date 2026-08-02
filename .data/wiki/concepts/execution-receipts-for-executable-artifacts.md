---
title: "Execution receipts for executable artifacts: test before trust"
created: 2026-08-02
source: session-019fc303
tags: [verification, executable-artifacts, skills, hooks, pipelines, decision, process-discipline]
summary: >
  Before declaring any executable artifact — skill, hook, script, pipeline, config
  change — as "done," produce a receipt from executing it, not merely inspecting it.
  Reading code is inspection; running code is verification. For executable things,
  inspection is necessary but not sufficient. The two-layer gate: static checks
  (structural defects) + runtime test-fire (execution defects). Lives in AGENTS.md
  as a standing rule because skills are created through multiple entry points.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/skill-lean-code-context-efficiency.md
    type: complements
  - target: wiki/concepts/code-output-passthrough-narration-over-script-output.md
    type: related
  - target: wiki/concepts/skill-management-in-agentic-systems-research-survey.md
    type: extends
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: extends
---

# Execution receipts for executable artifacts: test before trust

## Decision context

**Why this was needed:** during session 019fc303 (2026-08-02), the `/maintain` skill was created via `/go`, declared done, and went 5 days with 6 undetected defects. The operator asked "how can we catch preflight issues earlier — we caught them only because I asked a question." The root cause: the creation workflow declared done based on code inspection alone — no execution verification. Four of the six defects would have been caught by static checks at creation time; the other two required actually test-firing the skill. The principle generalizes beyond skills: hooks, scripts, and pipelines have the same gap.

## The principle

Reading code is inspection; running code is verification. For executable artifacts, inspection is necessary but not sufficient. The rule establishes a **two-layer gate** that fires regardless of which tool created the artifact:

1. **Static checks** — paths resolve, host-conformance patterns, passthrough gaps, frontmatter complete. For skills, these are `/skill-dev` Step 1.5 checks 1-6.
2. **Runtime test-fire** — dependencies don't crash, scripts produce expected output, the skill's procedure actually works end-to-end.

Both layers are required. Static checks alone miss runtime crashes (e.g., a dependency script throws a TypeError). Test-fire alone misses structural defects (e.g., a wrong-host env var that doesn't crash but silently produces wrong behavior).

## Per-artifact-type execution receipts

| Artifact | Inspection (necessary) | Execution receipt (required before "done") |
|---|---|---|
| SKILL.md files | Read body for correctness | Run `/skill-dev measure <name>` — Step 1.5 runs 6 static checks. Then test-fire: invoke the skill with `--dry-run` or its first real call. |
| Hook scripts | Read code for logic | Run the hook against representative input; verify exit code and output |
| Pipeline scripts | Read code for correctness | Run `--dry-run` or first invocation; verify output shape |
| Config changes | Read config for syntax | Verify the target tool loads the config without error |

## Why AGENTS.md, not /create-skill or /go

Skills are created through multiple entry points: `/create-skill`, `/go`, manual file writes. The validation can't live in any single skill — it has to be a standing rule that fires regardless of which tool created the artifact. The rule bridges creation (any tool) → validation (`/skill-dev measure` + test-fire).

This is the same structural reasoning behind other AGENTS.md rules: the file-location convention, the edit-then-verify protocol, the no-destructive-git rule. They all live in AGENTS.md because the behavior must fire from every entry point, not just from the skill that defined it. See [[agentic-sdlc-skill-lifecycle-architecture]] for where this sits in the overall skill lifecycle (VERIFY stage).

## Relationship to existing rules

- **"Claims require receipts"** — this rule specifies *what kind* of receipt for *what kind* of claim. "This works" → execution receipt, not inspection receipt.
- **"Edit-then-verify" (file-operations.md)** — that rule verifies *persistence* (the edit landed). This rule verifies *function* (the artifact works).
- **"Completion-language discipline"** — this rule adds the evidence requirement behind the language: "done" requires execution proof, not just file-read proof.

## What this means for our workspace

- `/skill-dev` Step 1.5 (6 static checks) now exists and should be run after every skill creation or significant edit
- Test-fire (`--dry-run` or first invocation) should happen before declaring any executable artifact done
- The `/review` REV-003 finding (concurrent-execution lock is a no-op because the subprocess exits immediately) is the canonical example: the lock was written and committed but never test-fired. If it had been run, the no-op behavior would have been immediately obvious
- The rule applies to ALL executable artifacts, not just skills. Hooks created but never test-fired are the same failure class. See [[concurrent-cdp-auth-contention]] for the broader multi-agent isolation pattern.
- The `/review` finding (REV-003) that caught the no-op lock is itself evidence for the rule — the review was the de facto "test-fire," but it happened 5 days late. Earlier test-fire would have caught it at creation. See [[skill-management-in-agentic-systems-research-survey]] for the SLIM lifecycle pattern that motivates post-creation validation.

## Receipts

- **AGENTS.md §"Execution receipts for executable artifacts"** — lines 620-650: the rule text itself, with the per-artifact-type table and two-layer gate specification
- **`/skill-dev` SKILL.md Step 1.5** — lines 105-200: the 6 static checks (path resolution, host conformance, code-block passthrough, version freshness, frontmatter completeness, leanness) that form Layer 1 of the gate
- **`/maintain` SKILL.md Step 0** — the concurrent-execution lock (`python -c` with `msvcrt.locking`): the canonical example of a Layer 2 failure — the lock passed static inspection but is a runtime no-op (subprocess exits immediately, releasing the lock). Discovered by `/review` REV-003, not by test-fire at creation time.

## Falsifier

This rule is wrong if:
- **Inspection is actually sufficient** — if skills/hooks/scripts that pass static review never have runtime defects, the test-fire layer adds no value. The `/maintain` incident (6 defects, 2 runtime-only) empirically disproves this.
- **The test-fire cost exceeds the defect cost** — if the time spent test-firing every artifact exceeds the time lost to undetected runtime defects, the rule has negative ROI. Test-fire cost: seconds to minutes per artifact. Defect cost: the `/maintain` defects went undetected for 5 days and required operator intervention to discover. The asymmetry favors test-fire.
- **The rule never fires in practice** — if agents consistently ignore it (like other behavioral rules that don't fire under pressure), the structural enforcement (a Stop hook that detects new SKILL.md files and blocks on missing execution receipts) would be needed. The behavioral version is the floor; the mechanical version is the ceiling.

## Auto-related

- [[Are-there-repos-or-solutions-to-claude-code-gettin]]
- [[testing-methodology-both-outcomes-informative]]
- [[skill-catalog]]
- [[test-design-falsification-of-production-components]]
- [[auto-test-stop-hooks-and-property-based-testing]]

