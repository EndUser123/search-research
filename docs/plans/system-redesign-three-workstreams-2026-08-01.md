# Plan: System Redesign — Three Architectural Workstreams

**Created:** 2026-08-01
**Session:** 019fc0a7
**Status:** Draft (ready for execution)
**Evidence base:** `P:/docs/audits/system-redesign-authority-and-behavior-audit-2026-08-01.md` + `P:/tmp/system-redesign-review.md`

## Prerequisite: Hook ✅ DONE

`minimal_bias_gate.py` Stop hook shipped (commit 0e867ae in ~/.grok). This catches the minimal-change bias that produced five minimal verdicts in the initial audit.

---

## Track A: Command-Surface Consolidation

**Goal:** Reduce the user-facing command surface to ~7 intent-level commands, with all retrieval/search/reasoning mechanisms internal to those commands.

**Blocking prerequisite:** None — hook is done.

### Task A1: Define the intent-level command map

Map the current 120 Grok-active skills to these user-intent categories:

| Intent | Command | Current skills absorbed |
|---|---|---|
| Research (reduce uncertainty) | `/research` (rename from `/www`) | /web, /search-fleet, /wiki query, /find → internal mechanisms |
| Design (reduce ambiguity) | `/design` | stays as-is |
| Plan (reduce execution ambiguity) | `/plan` (plan-writer) | stays as-is |
| Implement (reduce risk) | `/go` | stays as-is |
| Review (evaluate) | `/review` | /trace → mode of /review or standalone |
| Challenge (adversarial) | `/red-team` | /tp → absorbed or kept as lighter alternative |
| Close (session lifecycle) | `/close` | /check → mode of /close |

- [ ] Write the command map as `P:/docs/designs/command-surface-map.md`
- [ ] Identify which skills become "internal mechanisms" (not user-facing)
- [ ] Identify which skills get retired vs absorbed vs kept

### Task A2: Retire confirmed dead entries

- [ ] Delete `why-old` SKILL.md and its references
- [ ] Remove `plan/SKILL.md.disabled`
- [ ] Update routing tables in AGENTS.md for any renamed/absorbed commands
- [ ] Run `index_skills.py --audit` to confirm

### Task A3: Rename /www to /research and expand

- [ ] Rename the skill directory `/www` → `/research`
- [ ] Keep `/www` as a compatibility alias (1-line redirect)
- [ ] Expand `/research` to cover the full cognitive contract: local repo evidence → wiki → web → synthesis
- [ ] Update AGENTS.md routing tables
- [ ] Update all references to `/www` across skills

**Verification:** `index_skills.py --audit` shows clean state; `grep -r '/www'` in skill files shows only the alias; operator can invoke `/research` and get the expanded behavior.

**Abandonment criterion:** If renaming breaks >3 consumed references that can't be traced, revert and keep `/www` as the name.

---

## Track B: Investigation-State Artifact

**Goal:** Persistent investigation artifact with lifecycle, created when an investigation opens, updated incrementally, readable by future sessions.

**Blocking prerequisite:** Track A Task A1 (command map) — so we know which skills are producers and consumers.

### Task B1: Design the artifact schema

- [ ] Define frontmatter: `question`, `status` (open/investigating/resolved/promoted/archived), `created`, `session_id`, `hypotheses` (structured list)
- [ ] Define body sections: Question, Hypotheses, Evidence (for/against per hypothesis), Tests (discriminating tests + outcomes), Assumptions, Recommendation, Provenance
- [ ] Write schema to `P:/docs/designs/investigation-state-schema.md`

### Task B2: Extend /why to produce and consume the artifact

- [ ] `/why --persist` writes output to `P:/docs/investigations/<topic>-<date>.md`
- [ ] `/why` Step 0.5 searches `P:/docs/investigations/` in addition to wiki and handoffs
- [ ] Add test-outcome and status fields to Step 16 output
- [ ] Add lifecycle states to the investigation file frontmatter

### Task B3: Wire consumers

- [ ] `/design` reads investigation files when evaluating alternatives
- [ ] `/red-team` reads investigation files to attack weak hypotheses
- [ ] `/go` reads resolved investigations for settled conclusions

**Verification:** Future `/why` invocation in a different session finds and references a prior investigation file.

---

## Track C: Code-Structure Graph

**Goal:** Persistent cross-package code graph answering "who calls X, what depends on Y, what breaks if Z changes."

**Blocking prerequisite:** None — independent of Tracks A and B.

### Task C1: Evaluate backends

- [ ] Test `context7` MCP for library-API structural queries
- [ ] Evaluate extending `code_analysis.py` to persist AST output
- [ ] Evaluate `tree-sitter` for incremental parsing across packages
- [ ] Benchmark: "who calls function X across all packages" vs grep baseline

### Task C2: Build the graph for P:/packages/

- [ ] Parse all Python packages under `P:/packages/`
- [ ] Build symbol graph: definitions, calls, imports, dependencies
- [ ] Store as JSON or SQLite at `P:/.data/codegraph/`
- [ ] Expose query interface (CLI or MCP tool)

**Verification:** "What depends on `close_authority.py:validate_close_receipt`?" returns correct cross-package answer faster than grep.

---

## Execution order

```
Track A (A1→A2→A3) ──┬── Track B (B1→B2→B3)
                     │
Track C (C1→C2) ─────┘  (independent, can run in parallel)
```

Track C is independent and can proceed immediately. Tracks A and B have a dependency: B needs to know which skills produce/consume investigation state, which A1 defines.
