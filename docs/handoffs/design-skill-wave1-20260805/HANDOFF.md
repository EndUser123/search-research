# HANDOFF: /design skill Wave 1 improvements

## Objective

Implement 5 well-grounded improvements to the Grok Build `/design` skill that address gaps identified by 3-lens cross-model critique (spawn + codex). Wave 2 items (`--research-to-design` mode, evidence ledger contract) are deferred pending operator decisions.

## Status

CLOSED — Wave 1 + Wave 2 implemented and committed. Pending baseline test on a real design run.

## Wave 2 decisions (resolved by operator 2026-08-05)

1. **`--research-to-design`**: Elevated Step 0.6 (not a new mode). Claim-classification + evidence gate + verdict vocabulary added directly to Step 0.6. Commit `3019b1b`.
2. **Evidence ledger**: Extends `premise_verification_brief` (not a new artifact). The [RESEARCH]/[CONTRADICTED] labels added in Wave 1 are the ledger.
3. **Approval source**: This session (operator said "Do what you recommend"). No prior session needed.

## Commits

- `e23f10c` — Wave 1: bare /design handler, host-context injection (P1), evidence labels, contradiction handling, durable-artifact mapping
- `3019b1b` — Wave 2: elevated Step 0.6 with claim-classification, evidence gate, verdict-gated writer launch

## Last user message (verbatim)

"Do what you recommend." (in response to /tp critique of the 7-change packet recommending split-wave strategy)

## Wave 1 changes (implementing now)

### 1. Bare `/design` handler
- **Integrates at:** after Invocation section (before SDLC stage), `design/SKILL.md` ~line 78
- **Behavior:** no description → inspect context for ≤3 plausible design questions, recommend `/refine`, do NOT launch subagents
- **Acceptance criteria:** (a) bare invocation surfaces questions not a design target, (b) no `spawn_subagent` call possible before description is provided

### 2. Host-context injection (P1 from ensemble patterns)
- **Integrates at:** Setup section defines the block; Steps 1, 2, 5.5 inject it into spawn prompts
- **Behavior:** every writer/reviewer/critical-friend prompt includes bounded host-context: agent type, trust model, platform, Grok Build conventions, multi-terminal isolation, stale-data rules, repo/branch/session identity, relevant wiki concepts (≤3), evidence freshness
- **Acceptance criteria:** (a) grep for "host-context" in SKILL.md returns hits in writer/reviewer/critical-friend prompt sections, (b) wiki concept list bounded to ≤3

### 3. Evidence-label extension (`[RESEARCH]`, `[CONTRADICTED]`)
- **Integrates at:** Step 0.8 label table, `design/SKILL.md` ~line 500
- **Behavior:** `[RESEARCH]` = externally sourced claim not workspace-verified; `[CONTRADICTED]` = claim that conflicts with a verified workspace fact. Extends existing `[FACT]/[INFERENCE]/[UNKNOWN]` taxonomy.
- **Acceptance criteria:** (a) Step 0.8 table has 5 rows, (b) writer prompt references all 5 labels

### 4. Contradiction handling
- **Integrates at:** Cross-document consistency check section, `design/SKILL.md` ~line 280
- **Behavior:** when Step 0.6 research output conflicts with Step 0.7/0.8 verified facts, label the conflict and surface to writer before Step 1
- **Acceptance criteria:** consistency check section handles research-vs-workspace contradictions (not just wiki-vs-design)

### 5. Durable-artifact mapping
- **Integrates at:** Final Report section, `design/SKILL.md` ~line 1276
- **Behavior:** each output classified as: working design doc, handoff, wiki concept, eval fixture, skill update, todo item. Check for existing artifacts before creating new ones.
- **Acceptance criteria:** Final Report template includes artifact classification

## Wave 2 (deferred — needs operator decisions)

~~1. `--research-to-design` mode~~ — RESOLVED: elevated Step 0.6 (commit `3019b1b`)
~~2. Evidence ledger~~ — RESOLVED: extends premise_verification_brief (done in Wave 1)
~~3. Approval provenance~~ — RESOLVED: this session constitutes approval

## Affected files

- `C:\Users\brsth\.grok\skills\design\SKILL.md` — all 5 changes (single file)

## Verification plan

1. `grep pattern="host-context" path="C:/Users/brsth/.grok/skills/design/SKILL.md"` — must return hits in writer/reviewer/critical-friend sections
2. `grep pattern="\[RESEARCH\]|\[CONTRADICTED\]" path="C:/Users/brsth/.grok/skills/design/SKILL.md"` — must return hits in Step 0.8
3. `grep pattern="bare.*design\|no description" path="C:/Users/brsth/.grok/skills/design/SKILL.md"` — must return hits
4. Read modified sections back to confirm changes landed
5. Confirm no Claude Code hook/plugin assumptions added

## Non-goals (🚫 Never)

- Extract existing phases into child reference files (requires separate measurement evidence)
- Implement `--research-to-design` mode (Wave 2 — needs operator decision)
- Create evidence ledger artifact (Wave 2 — needs operator decision on contract)
- Modify personas (host-context is dynamic, belongs in orchestrator not static persona)
- Modify unrelated skills or wiki concepts

## Risks

- Host-context block adds ~200 tokens per subagent prompt (3 prompts × 200 = 600 tokens/run)
- The wiki-concept list in host-context must be bounded (≤3) to avoid context budget issues
- Bare `/design` handler must execute before scratch dir setup to avoid wasted UUID generation
