## Review packet

### Verdict

**REVISE.** The seven improvements are directionally coherent, but the packet is not yet implementation-ready. The largest gaps are the undefined evidence-ledger contract, unclear experiment semantics, duplicated research orchestration, and unsupported “approved” framing.

### Findings

1. **Scope is a skill redesign, not a narrow file-edit task.**

   [FACT] The packet says “Modify only the files required” but changes invocation behavior, pipeline stages, evidence semantics, subagent prompts, and artifact lifecycle ([prompt_0.txt:6-16](C:/Users/brsth/.grok/sessions/P%3A%5C/019fd413-5f5f-7642-8124-1c63ada98244/prompts/prompt_0.txt:6)).

   [INFERENCE] This should be framed as “implement a bounded `/design` skill contract revision,” with explicit compatibility and migration criteria. “Modify only files” is an implementation constraint, not a scope definition.

2. **`--research-to-design` substantially overlaps existing `/www` composition.**

   [FACT] Current `/design` already uses the `/www` pattern: wiki search, conditional web research, and synthesis into a domain brief ([SKILL.md:417-448](C:/Users/brsth/.grok/skills/design/SKILL.md:417)).

   [FACT] The proposed mode repeats identifying the decision, checking wiki/current implementation, classifying claims, and synthesizing evidence ([prompt_0.txt:56-68](C:/Users/brsth/.grok/sessions/P%3A%5C/019fd413-5f5f-7642-8124-1c63ada98244/prompts/prompt_0.txt:56)).

   [INFERENCE] Make this a routing/profile over Steps 0.5–0.8 plus the existing design loop, not a second nine-step research engine. Its unique addition should be the evidence gate and recommendation dispositions.

3. **The label proposal should extend Step 0.8, not create a parallel evidence system.**

   [FACT] Step 0.8 already defines `[FACT]`, `[INFERENCE]`, and `[UNKNOWN]`, including receipt requirements ([SKILL.md:490-520](C:/Users/brsth/.grok/skills/design/SKILL.md:490)).

   [FACT] The packet adds `[RESEARCH]` and `[CONTRADICTED]` but does not define precedence, receipts, or how labels interact with existing labels ([prompt_0.txt:60-68](C:/Users/brsth/.grok/sessions/P%3A%5C/019fd413-5f5f-7642-8124-1c63ada98244/prompts/prompt_0.txt:60)).

   [INFERENCE] Define one taxonomy centrally in Step 0.8. `[RESEARCH]` should mean externally sourced but not workspace-verified; `[CONTRADICTED]` should be a relationship/status over a claim, not necessarily a fifth epistemic class.

4. **The evidence ledger is underspecified.**

   [FACT] The packet names an evidence ledger but specifies neither location, schema, writer, lifecycle, nor consumers ([prompt_0.txt:10](C:/Users/brsth/.grok/sessions/P%3A%5C/019fd413-5f5f-7642-8124-1c63ada98244/prompts/prompt_0.txt:10)).

   [INFERENCE] At minimum it needs:

   - artifact path and lifetime;
   - stable claim ID;
   - claim text and label;
   - source/receipt;
   - observation timestamp or freshness;
   - confidence and unresolved contradiction;
   - linked recommendation;
   - consumer rules for writer, reviewer, critical friend, summary, and final report.

   Without this, “evidence ledger” is a reporting aspiration rather than an implementable feature.

5. **The packet is mostly theory-driven, not measurement-backed.**

   [FACT] The only explicit measurement requirement is unrelated extraction of existing phases: “requires separate measurement evidence” ([prompt_0.txt:16](C:/Users/brsth/.grok/sessions/P%3A%5C/019fd413-5f5f-7642-8124-1c63ada98244/prompts/prompt_0.txt:16)).

   [FACT] The required verification list asks for syntax checks, searches, and diagnostics, but supplies no baseline, sample runs, latency data, false-positive rate, or quality metric ([prompt_0.txt:99-111](C:/Users/brsth/.grok/sessions/P%3A%5C/019fd413-5f5f-7642-8124-1c63ada98244/prompts/prompt_0.txt:99)).

   [INFERENCE] The packet can justify P1 host context from the cited ensemble wiki, but it cannot yet justify the whole seven-change bundle as an improvement. Add a small evaluation plan: representative bare invocation, research-heavy design, contradiction case, and multi-agent prompt inspection, with before/after success criteria.

6. **“Falsification experiments” is not operationally clear.**

   [FACT] The packet asks for “the smallest discriminating experiment,” falsifiers, and stop conditions ([prompt_0.txt:65-68](C:/Users/brsth/.grok/sessions/P%3A%5C/019fd413-5f5f-7642-8124-1c63ada98244/prompts/prompt_0.txt:65)).

   [FACT] Current `/design` already requires concrete falsifiers in the critical-friend review and uses grep/tool execution/measurement for factual disputes ([SKILL.md:1061-1065](C:/Users/brsth/.grok/skills/design/SKILL.md:1061), [SKILL.md:870](C:/Users/brsth/.grok/skills/design/SKILL.md:870)).

   [INFERENCE] The packet must distinguish:

   - a research check;
   - a codebase verification;
   - a runnable code spike;
   - a naming-only falsifier.

   It must also specify who may run it, where its receipt is stored, and whether failure blocks design commitment. Otherwise this risks renaming existing falsifiability language without adding behavior.

7. **The seven changes have hidden dependencies.**

   [INFERENCE] The packet should explicitly surface these dependency edges:

   - bare `/design` must execute before setup/scratch creation and before any subagent dispatch;
   - the new mode depends on Steps 0.5–0.8 and the existing `/www`-style research;
   - labels and the ledger must be defined before writer/reviewer prompts are changed;
   - contradiction handling must feed both the existing wiki contradiction scan and the evidence gate;
   - host context must be generated once and injected consistently, rather than hand-copied into three prompts;
   - durable-artifact mapping must respect Step 6d’s existing Concept/ADR/Nothing choice;
   - “eval fixture,” “skill update,” and “todo item” have different owners and write paths.

8. **Composition with existing stages is mostly possible, but the packet does not specify the integration points.**

   [FACT] Existing `/design` already has context firewall, research, preflight, premise verification, a framing check, critical-friend review, wiki promotion, and artifact lifecycle rules ([SKILL.md:295-605](C:/Users/brsth/.grok/skills/design/SKILL.md:295), [SKILL.md:1041-1081](C:/Users/brsth/.grok/skills/design/SKILL.md:1041), [SKILL.md:1213-1235](C:/Users/brsth/.grok/skills/design/SKILL.md:1213)).

   [INFERENCE] The packet should provide a mapping table such as:

   `proposal → existing step → new behavior → artifact → blocking condition`

   In particular, durable-artifact mapping should extend the final report and Step 6d rather than bypassing them. Contradiction handling should extend the existing wiki scan at Steps 4.5/5.5 rather than introduce an independent contradiction pass.

9. **“Approved improvements” has no cited approval.**

   [FACT] The packet calls the changes “approved” but provides no approving person, date, decision artifact, or source citation ([prompt_0.txt:2](C:/Users/brsth/.grok/sessions/P%3A%5C/019fd413-5f5f-7642-8124-1c63ada98244/prompts/prompt_0.txt:2)).

   [FACT] The two supplied wiki concepts document `/risks` research and ensemble patterns; neither, in the cited sections, approves this exact `/design` change set ([multi-model-ensemble-design-patterns-for-agent-skills.md:212-261](P:/.data/wiki/concepts/multi-model-ensemble-design-patterns-for-agent-skills.md:212), [risks-skill-improvement-research-2026.md:207-231](P:/.data/wiki/concepts/risks-skill-improvement-research-2026.md:207)).

   [INFERENCE] Replace “approved” with “proposed” unless an actual decision record is cited. The ensemble wiki supports host-context propagation, but it does not approve all seven changes for `/design`.

### Claim ledger

| Claim | Type | Evidence | Confidence | Falsifier | Action |
|---|---|---|---|---|---|
| `/design` already performs wiki/web research | verified_fact | `SKILL.md:417-448` | High | Current source lacks that flow | Reuse it |
| Existing evidence labels are limited to FACT/INFERENCE/UNKNOWN | verified_fact | `SKILL.md:500-508` | High | Additional labels found in canonical skill | Extend centrally |
| Research-to-design is a distinct new pipeline | inference | Packet adds nine requirements; existing research path overlaps | Medium | A concrete non-overlapping contract is specified | Narrow to mode/profile |
| Host-context injection is justified | verified_fact | Ensemble wiki `:46-65` | High | Controlled runs show no quality improvement | Implement, then measure |
| Seven changes are approved | unsupported | Packet `:2`; no approval receipt | High | Approval artifact is produced | Relabel proposed |

### What would change this: disconfirmation conditions

The verdict would move to **PROCEED** if the packet adds:

1. a cited approval artifact, or changes “approved” to “proposed”;
2. an integration map against Steps 0.5–0.8, 5.5, and 6d;
3. a concrete ledger schema, path, lifecycle, and consumers;
4. precise falsification-experiment types, receipts, and blocking rules;
5. a minimal before/after evaluation plan;
6. a statement that `--research-to-design` reuses existing `/www`-style research rather than duplicating it.

Preflight was attempted for this review but did not complete within the workspace scan window; that limits claims about competing active plans, but it does not affect the source-level findings above.