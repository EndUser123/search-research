---
title: "Skill techniques index: reusable patterns we've developed or adopted"
created: 2026-07-21
source: session-2026-07-21
sources:
  - P:/.data/wiki/concepts/skill-authoring-patterns-dos-and-donts.md
  - P:/.data/wiki/concepts/compound-skill-improvement-patterns.md
  - P:/.data/wiki/concepts/prospective-prioritization-multi-lens-what-next.md
  - P:/.data/wiki/concepts/deliberation-waste-re-deriving-same-answer.md
  - P:/.data/wiki/concepts/fabricated-causal-chain-receipt-required.md
  - P:/.data/wiki/concepts/multi-agent-correlated-errors.md
  - P:/.data/wiki/concepts/evidence-first-default-and-needless-confirmation.md
  - P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md
tags: [skill-techniques, patterns, reusable, skill-design, techniques-index]
host: both
agent: grok
verification: cross_referenced_to_existing_concepts
cognitive_load: 4
summary: "Curated index of 19 reusable techniques we've developed or adopted across our skill portfolio. Each technique has: what it prevents, where it's implemented, and how to apply it to a new skill. Use this when designing or improving any skill — scan the list for techniques that fit the failure modes you're addressing."
---

# Skill techniques index: reusable patterns

This is the curated index of techniques we've developed or adopted across our skill portfolio. It's different from the [[skill-authoring-patterns-dos-and-donts]] (which covers industry-wide skill-authoring best practices) — this page covers techniques **specific to our portfolio** and **developed from our own failure modes**.

Use this when designing or improving any skill. Scan the list for techniques that address the failure modes you're worried about.

## How to read this index

Each technique has:
- **Prevents:** the failure mode it exists to stop
- **Implemented in:** which of our skills use it
- **How to apply:** concrete steps to add it to a new skill
- **Cost:** what it costs to use (tokens, latency, complexity)

---

## Gathering techniques (research, discovery, input)

### T1. Preflight verification

**Prevents:** inaccurate handoffs/reports that cite stale or wrong facts
**Implemented in:** `/handoff` Step 5; `/preflight` skill; AGENTS.md mandatory preflight rule
**How to apply:** before writing any claim into a durable artifact, verify it against current source files. Run a discovery scan; if it contradicts a claim, correct/downgrade/drift the claim before writing.
**Cost:** 1-3 tool calls per claim verified; ~30s added per handoff

### T2. Source quality scoring (CREDIBLE-lite)

**Prevents:** citing low-authority sources as primary evidence
**Implemented in:** `/www` Phase 2.3
**How to apply:** score each scraped source on 4 dimensions (authority, recency, evidence, bias), 1-3 each. Sources scoring ≤6/12 are flagged `[LOW-QUALITY]` and used only for triangulation.
**Cost:** ~1 paragraph of reasoning per source

### T3. Conflict detection

**Prevents:** silently resolving disagreements between sources
**Implemented in:** `/www` Phase 2.4
**How to apply:** for each finding, compare what sources say. If they disagree, mark explicitly: "⚠️ CONFLICTING CLAIMS: source A says X, source B says Y." Use authority/recency for factual conflicts; present both sides for interpretive conflicts.
**Cost:** ~1 sentence per detected conflict

### T4. Source diversity check

**Prevents:** echo chamber — all sources from the same vendor/type
**Implemented in:** `/www` Phase 2.2
**How to apply:** ensure the scraped set spans official docs, peer-reviewed papers, practitioner blogs, and community discussions. If all sources are the same type, widen the search and note it.
**Cost:** 1 check; may trigger 1-2 additional searches

### T5. Research ledger (incremental reuse)

**Prevents:** re-researching the same topic on subsequent runs
**Implemented in:** `/www` research ledger at `P:/.data/www-ledger/`; proposed for `/aar` ledger
**How to apply:** each run writes a ledger entry recording topic, sources used, gaps addressed, gaps unresolved. Next run on the same topic reads the ledger and skips already-resolved gaps unless sources have changed.
**Cost:** 1 file write per run; 1 file read at start of next run

---

## Thinking techniques (reasoning, synthesis, judgment)

### T6. Context firewall

**Prevents:** synthesis quality collapse when source content exceeds context capacity
**Implemented in:** `/design` Step 0.5; `/www` Phase 2.6
**How to apply:** when total source content exceeds ~5000 words, compress into an evidence brief first (extract only gap-relevant passages, drop boilerplate). Synthesize from the brief, not the raw sources.
**Cost:** 1 subagent spawn for compression; ~2-3k tokens for the brief

### T7. Two-lens critique

**Prevents:** anchor capture — the same agent that produced a framing cannot reliably challenge it
**Implemented in:** `/tp` default mode (fresh subagent + same-agent synthesis)
**How to apply:** spawn a fresh subagent with a target + minimal context bundle. The subagent critiques from a different framing. The parent verifies findings against session evidence (spot-check gate).
**Cost:** ~60-90s; 1 subagent spawn; ~500-token context bundle

### T8. Model disclosure

**Prevents:** claiming a "different lens" when the subagent inherited the parent model
**Implemented in:** `/tp` Step 2 (added 2026-07-21)
**How to apply:** record the model slug used by the subagent. If omitted, disclose "parent-inherited (<model>) — fresh-context but same-model lens." State this in the synthesis header.
**Cost:** 1 line of disclosure

### T9. Evidence-basis tagging

**Prevents:** uncritically propagating inferences as if they were verified facts
**Implemented in:** `/tp` Step 2.5; AGENTS.md verification receipt rule
**How to apply:** every finding tagged `[from-bundle]` / `[from-file-read <path:line>]` / `[from-grep <pattern> @ <path>]` / `[from-command <desc>]` / `[from-first-principles]`. The orchestrator weights findings by tag.
**Cost:** 1 tag per finding

### T10. Spot-check gate

**Prevents:** subagent synthesis errors propagating unchecked into reports
**Implemented in:** AGENTS.md "Subagent synthesis → report gate" rule; `/tp` Step 3
**How to apply:** when a subagent returns a synthesis, verify at least one finding against evidence already in context before propagating. If the spot-check contradicts, the synthesis is wrong until re-investigated.
**Cost:** 1 tool call or file read per synthesis

### T11. Falsifier section

**Prevents:** skills that can't be proven wrong become unaccountable
**Implemented in:** `/tp`, `/www`, `/aar` Phase 8.5, all session-written skills
**How to apply:** every skill ends with a "Falsifier" section stating what would make it wrong within 6 months. Name concrete patterns (e.g., "if Phase 1's short-circuit fires <10% of the time").
**Cost:** 1 paragraph per skill

---

## Outputting techniques (artifacts, persistence, format)

### T12. Opportunity durability

**Prevents:** AAR opportunities being lost on session restart
**Implemented in:** `/aar` Phase 8.5
**How to apply:** every non-terminal opportunity (MONITOR, INVESTIGATE, DEFER) must be persisted to a durable location (handoff, plan, wiki, or labeled report-only) before the skill exits. Cite the durable path in the report.
**Cost:** 1 file write per non-terminal opportunity

### T13. Shape-explicit output

**Prevents:** vague "research X" producing unstructured dumps
**Implemented in:** `/www` (5 named shapes + custom)
**How to apply:** the skill takes a `shape=` parameter. Each shape has a defined output structure (table, two-column, numbered list). The model follows the structure rather than inventing one.
**Cost:** 1 parameter; ~1 paragraph of shape spec per shape

### T14. Copyable checklist

**Prevents:** multi-step workflows skipping validation steps or losing track
**Implemented in:** `/www` (top of skill); generativeprogrammer Pattern 10
**How to apply:** for workflows with >3 steps, provide a markdown checklist the model pastes into its response and ticks off. Skipped steps become visible.
**Cost:** ~12 lines of markdown per response

### T15. Retirement check

**Prevents:** the wiki growing monotonically with duplicate/contradictory concepts
**Implemented in:** `/wiki` retirement check; `/www` Phase 3.1
**How to apply:** before writing a new wiki concept, search for related concepts. If one is superseded, update its frontmatter (`status: superseded`) and append a note. Don't delete.
**Cost:** 1 qmd search; ~30s of reading

---

## Prompting techniques (description, triggers, routing)

### T16. Exclusion clause in description

**Prevents:** skills hijacking requests that belong to adjacent skills
**Implemented in:** `/www` description (added 2026-07-21); generativeprogrammer Pattern 2
**How to apply:** end the description with "Do NOT use for X (use /Y), Z (use /W)..." Name the specific adjacent skills.
**Cost:** 1 line in the description field

### T17. Pipeline pattern declaration

**Prevents:** confusion about what shape the skill is
**Implemented in:** `/www` (declared as Pipeline per developersdigest 7 patterns)
**How to apply:** name the orchestration pattern explicitly (Single, Supervisor, Pipeline, Swarm, Debate, Hierarchical, Harness). This clarifies what the skill is NOT and prevents architecture drift.
**Cost:** 1 sentence in the skill body

---

## Meta techniques (recursive, cross-cutting)

### T18. Recursive self-improvement via self-invocation

**Prevents:** skills ossifying because no one thinks to research how to improve them
**Implemented in:** `/www` on `/www` (2026-07-21); documented in [[compound-skill-improvement-patterns]]
**How to apply:** run the skill on its own design. Phase 1 surfaces what the skill does well (self-knowledge). Phase 2 researches what others do better. Phase 3 persists improvements. The skill's own discipline is the right shape for improving it.
**Cost:** 1 full skill invocation; produces both skill edits and a wiki concept

### T19. Progressive disclosure with trigger-based reference loading

**Prevents:** loading all detail on every invocation, burning context
**Implemented in:** `/aar` (lean core + references/*.md loaded on trigger); generativeprogrammer Pattern 4
**How to apply:** keep SKILL.md under 500 lines. Put detail in `references/*.md`. Define explicit triggers that fire when specific conditions are met (user request, detector signal, structural condition). Only load the reference when its trigger fires.
**Cost:** 1 reference_loader.py script; 1 trigger table in SKILL.md

### T20. Two-phase analysis (code breadth → LLM depth)

**Prevents:** wasting expensive LLM calls on artifacts that don't need them; missing high-value artifacts because the fan-out was too narrow
**Implemented in:** session 2026-07-21 (scan_techniques.py scanned 968 skills in 17s, then LLM deep-read the top 47)
**How to apply:**
1. **Phase 1 (code breadth):** write a Python script that mechanically scans all N artifacts for indicator patterns. Produces a JSON+MD report with technique/feature density per artifact. ~20s for ~1000 artifacts.
2. **Phase 2 (LLM depth):** deep-read only the high-density subset the scan identifies. Use `ccr-ornith` (free local model, parallel, ~38s per read) for mechanical file reads; parent-inherited model for synthesis and judgment.
3. **Triage:** artifacts with zero detected indicators are skipped (they're either simple utility skills or have novel patterns the indicators miss — flag the latter for manual review if line count is high).

**Cost:** ~20s code + ~40s per LLM read (ccr-ornith) vs. ~60-90s per LLM read without the code pass. 50x speedup for breadth coverage.

**Falsifier:** if the code scan consistently misses novel techniques (false negatives in the indicator patterns), the breadth pass is misleading. Mitigation: review zero-signal artifacts with high line counts manually; expand indicator patterns when new techniques are found.

### T21. Concurrency test protocol before claiming parallel support

**Prevents:** claiming a model supports parallel fan-out without testing (inference dressed as fact)
**Implemented in:** session 2026-07-21 (tested ccr-ornith with 3 concurrent subagents)
**How to apply:** before using a model for N>2 parallel subagents, spawn 3 identical trivial tasks ("return 'TEST N OK'") simultaneously. If all 3 complete with similar durations (not serially increasing), the model supports parallel fan-out. If only 1 completes or durations increase linearly, it's single-request.
**Cost:** ~40s per test (3 concurrent trivial tasks)

### T22. Model tiering for subagent tasks

**Prevents:** using expensive API models for mechanical tasks that local/free models can handle
**Implemented in:** session 2026-07-21 (verified model availability and concurrency)
**How to apply:**
- **Mechanical tasks** (file reading, pattern extraction): `ccr-ornith` (free local, parallel OK, ~38s per task)
- **Synthesis and judgment**: parent-inherited model (Grok API, higher quality)
- **Cross-model second opinion**: `/agy`, `/codex`, `/mmx` (external CLI processes)
- Check `~/.grok/tool-fallbacks.md` for known-broken model combinations before spawning
**Cost:** ~0 tokens for ccr-ornith reads vs. API token cost for parent-inherited

### T23. Held-out validation gate

**Prevents:** optimization on training-set only (overfitting); skill changes that look better but aren't
**Implemented in:** `/skillopt` (Codex), `/skill-write` (cc-skills-architect)
**How to apply:** compare candidate against baseline on examples NOT used to drive the edit. Accept only if it clearly improves on held-out data. Anti-overfitting.
**Cost:** requires a held-out test set; ~1 comparison cycle

### T24. Severity vs. confidence orthogonality

**Prevents:** conflating "how bad if real" with "how strong is the evidence"
**Implemented in:** `/review-packet-runner` (Codex)
**How to apply:** score findings on two independent axes: severity (impact if real) and confidence (evidence strength). Don't collapse into a single "importance" rating.
**Cost:** 2-column scoring per finding

### T25. Five-way epistemic classification

**Prevents:** binary fact/inference missing nuanced evidence states
**Implemented in:** `/review-packet-runner`, `/epistemic-check`
**How to apply:** classify claims as fact / inference / unsupported / contradicted / open question. Finer than the standard `[FACT]`/`[INFERENCE]`/`[UNKNOWN]` taxonomy.
**Cost:** 1 classification per claim

### T26. Account-for-everything closure

**Prevents:** findings dropped silently; incomplete accounting
**Implemented in:** `/debrief` (ACCOUNTING sentinel), `/rns` (GAP COVERAGE block)
**How to apply:** before closing, produce explicit bucket count: "ACCOUNTING: N findings → A tasked, B fixed, C deferred, D external." Regex-matched at close; every finding must be in a bucket.
**Cost:** 1 accounting line before close

### T27. Source-first classification rule

**Prevents:** false "absorbed/stub/aliased/retired" claims without evidence
**Implemented in:** `/skill-audit`, `/debrief`, `/claude-audit`
**How to apply:** for any consolidation/absorption claim: must cite old source + parent source + backend existence. Single source = `NOT_PROVEN`.
**Cost:** 3-way verification per claim

### T28. Self-attack checklist

**Prevents:** shipping a recommendation without testing it against failure vectors
**Implemented in:** `/improve` (improve-partner)
**How to apply:** before shipping a recommendation, answer each of 7 attack vectors: theater, duplication, hook-or-gate noise, wrong-layer fix, missing evidence, maintenance burden, regression risk. Each must be answered, not skipped.
**Cost:** 7 explicit checks per recommendation

### T29. Preserve-and-simplify middle option

**Prevents:** binary delete-vs-minimal-change forcing suboptimal decisions
**Implemented in:** `/improve` (improve-partner)
**How to apply:** when deletion is on the table, require ≥3 options including preserve-and-simplify as the middle option between minimal-change and delete. Explicit reasoning for why deletion is strictly better.
**Cost:** 1 additional option when deletion is considered

### T30. XSTC (Cross-Skill Transfer Check)

**Prevents:** findings that are local-only being generalized as reusable
**Implemented in:** `/debrief`, `/skill-audit`, `/claude-audit`
**How to apply:** for each finding, classify whether it's local to this artifact or transferable across skills. Required fields: classification, affected_surfaces, evidence, why_it_transfers_or_not, owner, recommended_action.
**Cost:** 1 classification per finding

### T31. CEC (Completion Evidence Contract)

**Prevents:** "done" claims without evidence for each claim type
**Implemented in:** `/debrief`, `/skill-audit`, `/claude-audit`
**How to apply:** claim-type enum maps to required evidence per type. Authority ladder: source_changed → cache_rebuilt → plugin_loaded → command_resolves → behavior_observed → live_behavior. Each "done" claim cites its authority level.
**Cost:** 1 authority citation per completion claim

### T32. Generator ≠ Validator

**Prevents:** self-validation theater (same LLM generates and certifies)
**Implemented in:** `/doc-compiler`, `/skill-to-page`
**How to apply:** generation and validation MUST be performed by distinct LLM instances. Self-validation is a blocking defect. Anti-self-deception: generic "ok"/"verified"/"works" reasons treated as false positives.
**Cost:** 2 LLM instances instead of 1

---

## Applying techniques to a new skill

When designing a new skill, scan this index for techniques that fit the failure modes you're addressing:

| If the failure mode is... | Use technique... |
|---|---|
| Stale or inaccurate claims in output | T1 (Preflight), T9 (Evidence-basis) |
| Low-quality sources cited | T2 (Source quality), T4 (Diversity) |
| Silent conflict resolution | T3 (Conflict detection) |
| Re-deriving prior work | T5 (Research ledger) |
| Synthesis collapse on large inputs | T6 (Context firewall) |
| Anchor capture | T7 (Two-lens critique), T8 (Model disclosure) |
| Unverified synthesis propagation | T9 (Evidence-basis), T10 (Spot-check gate) |
| Unaccountable skills | T11 (Falsifier) |
| Lost opportunities on restart | T12 (Opportunity durability) |
| Vague unstructured output | T13 (Shape-explicit output) |
| Skipped steps in multi-step workflows | T14 (Copyable checklist) |
| Duplicate/contradictory wiki concepts | T15 (Retirement check) |
| Skill hijacking adjacent requests | T16 (Exclusion clause) |
| Architecture confusion | T17 (Pipeline pattern declaration) |
| Skill ossification | T18 (Recursive self-improvement) |
| Context bloat from loading all detail | T19 (Progressive disclosure) |
| Wasting LLM calls on low-signal artifacts | T20 (Two-phase analysis) |
| Claiming parallel support without testing | T21 (Concurrency test protocol) |
| Using expensive models for mechanical tasks | T22 (Model tiering) |
| Optimization overfitting | T23 (Held-out validation) |
| Severity-confidence conflation | T24 (Severity vs. confidence orthogonality) |
| Binary epistemic classification too coarse | T25 (Five-way epistemic classification) |
| Silent finding drops | T26 (Account-for-everything closure) |
| False consolidation/absorption claims | T27 (Source-first classification rule) |
| Unexamined recommendations | T28 (Self-attack checklist) |
| Binary delete-vs-minimal forcing | T29 (Preserve-and-simplify middle option) |
| Local findings generalized as reusable | T30 (XSTC) |
| "Done" without evidence per claim type | T31 (CEC) |
| Self-validation theater | T32 (Generator ≠ Validator) |

## Relationship to existing concepts

- [[skill-authoring-patterns-dos-and-donts]] — industry-wide best practices (Anthropic, generativeprogrammer, anthonytd, Graphite)
- [[compound-skill-improvement-patterns]] — patterns specific to compound/orchestrator skills
- [[skill-catalog]] — the auto-generated index of all skills
- [[skill-enforcement-layers]] — Claude Code skill enforcement layer analysis
- [[portfolio-deep-read-transferable-techniques]] — 35+ additional techniques from the 47-skill deep read (not yet merged into this index)
- [[deliberation-waste-re-deriving-same-answer]] — T5 (Research ledger) prevents this at the skill level
- [[fabricated-causal-chain-receipt-required]] — T1 (Preflight), T9 (Evidence-basis), T10 (Spot-check gate) are the receipt mechanisms
- [[multi-agent-correlated-errors]] — informs T7 (Two-lens critique) and T10 (Spot-check gate)
- [[evidence-first-default-and-needless-confirmation]] — T1 (Preflight) is the structural application

## Open questions

- Should we have a technique for formal eval scenarios (anthonytd eval-driven development)? Currently none of our skills have formal evals.
- Should we add a technique for A/B loop testing (Agent A authors, Agent B uses, Agent C critiques)?
- How do T5 (Research ledger) and the proposed AAR ledger share infrastructure?
- The full portfolio deep-read identified ~35 additional techniques beyond T1-T32. See [[portfolio-deep-read-transferable-techniques]] for the complete inventory. The top 10 were promoted to T23-T32; the rest remain in the deep-read concept for future promotion.

## Regeneration

This index is **curated**, not auto-generated. It should be updated when:
- A new technique is developed (add it with the same structure)
- A technique is adopted into additional skills (update "Implemented in")
- A technique is retired or superseded (mark with `status: superseded`)

Unlike the skill catalog (which is auto-generated), this index requires human/agent judgment about what counts as a reusable technique worth indexing.

## Auto-related

- [[skill-enforcement-layers]]
- [[claude-code-skill-failure-patterns]]

