---
title: "Skill-development portfolio: what our skill-writing and skill-improving skills do"
created: 2026-07-21
source: session-2026-07-21 (user asked to document skill-improving skills and unique techniques)
sources:
  - P:/.data/wiki/concepts/skill-catalog.md
  - P:/.data/wiki/concepts/skill-techniques-index.md
  - P:/.data/wiki/concepts/skill-authoring-patterns-dos-and-donts.md
  - P:/.data/wiki/concepts/compound-skill-improvement-patterns.md
  - C:/Users/brsth/.grok/skills/create-skill/SKILL.md
  - P:/packages/.claude-marketplace/plugins/cc-skills-architect/skill-write/SKILL.md
  - P:/packages/.claude-marketplace/plugins/cc-skills-architect/skill-audit/SKILL.md
tags: [skill-development, skill-writing, skill-improving, portfolio, unique-techniques]
host: both
agent: grok
verification: cross_referenced_to_actual_skills
cognitive_load: 4
summary: "What our skill-writing and skill-improving skills actually do, what's unique about our portfolio, and how to choose the right one. Covers /create-skill, /skill-write, /skill-audit, /improve, /debrief, /aar, /tp, /www in their skill-development capacity. Documents 12 techniques unique to our portfolio that aren't in industry best practices."
---

# Skill-development portfolio

## Q1: What skill-writing/improving skills do we have?

Inventory of skills whose primary function is creating, improving, or analyzing skills:

| Skill | Location | What it does | When to use |
|---|---|---|---|
| `/create-skill` | `~/.grok/skills/create-skill/` | Interactively scaffolds a new skill: asks name, scope, purpose; writes SKILL.md | New skill from scratch |
| `/skill-write` | `cc-skills-architect/skill-write` | Advanced skill authoring with pattern guidance | New skill with quality bar |
| `/skill-from-docs` | `cc-skills-architect/skill-from-docs` | Generate a skill from a documentation URL | Convert existing docs to a skill |
| `/skill-to-page` | `cc-skills-architect/skill-to-page` | Convert a skill to a wiki/documentation page | Document an existing skill |
| `/skill-audit` | `cc-skills-analysis/skill-audit` | Audit an existing skill for quality/issues | Review a skill before shipping |
| `/skill-similarity` | `cc-skills-analysis/skill-similarity` | Find similar/duplicate skills | Detect overlap before adding new |
| `/evolve` | `cc-skills-architect/evolve` | Evolve a skill iteratively | Improve an existing skill |
| `/improve` | `improve-partner/improve` | Process-improvement recommendations | Improve a workflow or process |
| `/debrief` | `~/.grok/skills/debrief/` | Session retrospective with 5 lens subagents | Learn from a session, including skill gaps |
| `/aar` | `P:/.grok/skills/aar/` | Evidence-grounded continual-improvement review | Deep session analysis with opportunity landscape |
| `/tp` | `~/.grok/skills/tp/` | Two-lens critical-friend critique | Critique a skill design decision |
| `/www` | `~/.grok/skills/www/` | Wiki-web-wiki compound research | Research how others solve a problem, persist to wiki |

### Choosing the right one

| If you want to... | Use |
|---|---|
| Create a new skill from scratch | `/create-skill` (simple) or `/skill-write` (advanced) |
| Convert docs into a skill | `/skill-from-docs` |
| Audit an existing skill for quality | `/skill-audit` |
| Find if a similar skill already exists | `/skill-similarity` then `qmd search` |
| Improve a skill iteratively | `/evolve` or `/tp` on the design |
| Learn from a session (including skill gaps) | `/debrief` (fast) or `/aar` (deep) |
| Research how others do it | `/www` |
| Document a skill in the wiki | `/skill-to-page` (auto) or manual wiki concept |

## Q2: What's unique about our portfolio?

These are techniques we've developed or adopted that are NOT in the standard skill-authoring best practices (Anthropic, generativeprogrammer, anthonytd). They came from our own failure modes.

### Unique technique 1: Two-lens critique with model disclosure

**Where:** `/tp` default mode
**What it does:** spawns a fresh subagent (no shared framing anchor) to generate a critique, then the same agent verifies and integrates each finding against session evidence (verification + novelty + integration checks)
**Why it's unique:** standard best practice says "test with a fresh instance" (anthonytd A/B loop) but doesn't formalize the verification gate. Our `/tp` adds:
- Explicit model disclosure (parent-inherited vs cross-model)
- Evidence-basis tagging per finding (`[from-bundle]`, `[from-file-read]`, `[from-grep]`, `[from-command]`, `[from-first-principles]`)
- Spot-check gate before propagation
**Failure mode it prevents:** the cc-council incident (2026-07-20) where an unchecked subagent synthesis propagated "it's a stub" into 5+ report sections

### Unique technique 2: Lean-hybrid with trigger-based reference loading

**Where:** `/aar`
**What it does:** SKILL.md is a lean core (~760 lines) with `references/*.md` loaded only when an explicit trigger fires. The loader (`__lib/reference_loader.py`) reads a trigger table from SKILL.md.
**Why it's unique:** standard progressive disclosure (Anthropic Pattern 4) says "split content into separate files." Our version adds:
- Machine-readable trigger table (not just "load when needed")
- Trigger types: user request, detector signal at severity threshold, structural condition
- "A weak detector signal alone is NOT a trigger" — prevents over-loading
**Failure mode it prevents:** loading 5 references on every AAR invocation when most are irrelevant

### Unique technique 3: Opportunity durability (Phase 8.5)

**Where:** `/aar` Phase 8.5
**What it does:** every non-terminal opportunity (MONITOR, INVESTIGATE, DEFER) must be persisted to a durable location (handoff, plan, wiki, or labeled report-only) before the skill exits
**Why it's unique:** standard retrospective patterns produce a report and stop. Our version adds:
- Mandatory durability check before exit
- Specific durable locations per finding type
- `durable_path` field in every opportunity
**Failure mode it prevents:** session 019f821c (2026-07-20) where 2 of 6 AAR opportunities existed only in the report under `.artifacts/` and were lost on restart

### Unique technique 4: Preflight verification step

**Where:** `/handoff` Step 5; `/preflight` skill; AGENTS.md mandatory preflight rule
**What it does:** before writing any claim into a durable artifact, verify it against current source files via a discovery scan
**Why it's unique:** standard handoff patterns assume the author's memory is correct. Our version adds:
- Structural verification before writing
- Discovery audit with evidence packet
- Correct/downgrade/drift protocol when preflight contradicts a claim
**Failure mode it prevents:** the yt-is handoff incident (2026-07-20) where 5 wrong root-cause diagnoses were written into a handoff without verification

### Unique technique 5: Wiki lifecycle state machine

**Where:** `wiki_state.py` in cc-skills-sdlc
**What it does:** every wiki touch must mark phases via a state machine: `discovered → ingesting → linking → linting → complete`. Hard gate — `wiki_ingest.py` refuses exit-0 on lifecycle tracking failure.
**Why it's unique:** standard wiki/PKM systems don't enforce a state machine. Our version adds:
- Phase tracking with atomic writes (`.tmp + os.replace + fsync`)
- File locking (msvcrt on Windows, fcntl on POSIX)
- Hard gate on completion
**Failure mode it prevents:** partial wiki state where a concept is written but not auto-linked, not logged, not qmd-indexed

### Unique technique 6: Context firewall

**Where:** `/design` Step 0.5; `/www` Phase 2.6
**What it does:** when source content exceeds ~5000 words, a separate subagent compresses it into a lossless-maximal brief (~3000-8000 words) before the writer consumes it
**Why it's unique:** standard subagent patterns pass full content. Our version adds:
- Explicit trigger (>3 files OR >500-line file)
- Circuit breaker (soft ~3000 / hard ~8000 words)
- Writes to `${scratch_dir}/evidence-brief.md`
**Failure mode it prevents:** the /design writer crash (2026-07-20) at 410k input tokens

### Unique technique 7: Research ledger (incremental reuse)

**Where:** `/www` Phase 3.5; `P:/.data/www-ledger/`; proposed for `/aar`
**What it does:** each research run writes a ledger entry recording what was researched, sources used, gaps addressed, gaps unresolved. Next run reads the ledger and skips already-resolved gaps.
**Why it's unique:** standard research patterns start from zero each time. Our version adds:
- Per-topic ledger files with structured frontmatter
- Gap-addressed / gap-unresolved tracking
- Source-hash comparison to detect content changes
**Failure mode it prevents:** re-researching "how to do X" every time the question comes up

### Unique technique 8: Source quality scoring (CREDIBLE-lite)

**Where:** `/www` Phase 2.3
**What it does:** scores each scraped source on 4 dimensions (authority, recency, evidence, bias), 1-3 each. Sources ≤6/12 are flagged `[LOW-QUALITY]`.
**Why it's unique:** standard research patterns cite whatever comes back from search. Our version adds:
- Adapted from the academic CREDIBLE framework to a 12-point scale
- Low-quality sources used only for triangulation, not primary citation
**Failure mode it prevents:** citing a convincing-sounding but evidence-free blog post as a primary source

### Unique technique 9: Conflict detection (no silent resolution)

**Where:** `/www` Phase 2.4
**What it does:** for each finding, compare what sources say. If they disagree, mark explicitly with both sides and investigate authority/recency.
**Why it's unique:** standard synthesis picks one answer. Our version adds:
- 3 conflict types (factual, interpretive, scope)
- Explicit conflict markers in output
- Never silently resolve
**Failure mode it prevents:** presenting a contested claim as settled

### Unique technique 10: Verification receipt rule

**Where:** `~/.grok/AGENTS.md` "Verification receipt rule"; `P:/.claude/CLAUDE.md` "Claim Verification"
**What it does:** before stating a causal claim as fact, name the verification receipt: a tool call, file citation, or command output from the last 3 turns that directly confirms the claim
**Why it's unique:** standard fact-checking is advisory. Our version adds:
- Mandatory for causal claims ("X causes Y")
- Specific receipt types (tool call, file citation, command output)
- Must relabel as `[INFERENCE]` or `[UNKNOWN]` if no receipt
**Failure mode it prevents:** the yt-is fetch failure (2026-07-20/21) where 5 different wrong causal explanations were delivered as fact

### Unique technique 11: Deliberation discipline (anti-spin rules)

**Where:** `~/.grok/AGENTS.md` "Deliberation discipline"
**What it does:** three rules that prevent token waste from re-deliberation: single-pass deliberation, short-command interpretation, thinking budget
**Why it's unique:** standard agent rules don't address deliberation waste. Our version adds:
- Falsifier per rule: "if re-deliberation changes the answer, the new evidence must be cited"
- Thinking-to-response ratio check (5x = likely waste)
- Short imperative interpretation at the most specific level
**Failure mode it prevents:** session 019f821c where 11 of 20 turns spent more on thinking than response, with 6 consecutive reversals of a binary decision

### Unique technique 12: Recursive self-improvement via self-invocation

**Where:** documented in [[compound-skill-improvement-patterns]]; demonstrated by `/www` on `/www`
**What it does:** run a skill on its own design to improve it. The skill's three-phase discipline (query → research → persist) is the right shape for self-improvement.
**Why it's unique:** no standard practice. Our version adds:
- Meta-pattern: any sufficiently structured skill can improve itself
- Phase 1 surfaces what the skill does well (self-knowledge)
- Phase 2 researches what others do better (external evidence)
- Phase 3 persists improvements (durable change)
**Failure mode it prevents:** skill ossification — skills that never get improved because no one thinks to research how

## Q2b: Lifecycle techniques (merged from skill-lifecycle-toolkit 2026-07-27)

These 5 techniques + the DEPRECATED convention were originally documented in a parallel concept (`skill-lifecycle-toolkit.md`). Merged here to consolidate the single source of truth.

### Technique 13: DEPRECATED-description convention (retiring skills)

**What it does:** when retiring a skill, prepend `DEPRECATED — use /<replacement> instead.` to the `description` frontmatter field. Keep the body intact as fallback reference.
**Why over archive (Move-Item):** frontmatter edit is atomic and non-locking on Windows (avoids file-lock IOException); the catalog scanner still sees the entry with its redirection; recoverable by reverting the edit.
**Existing examples:** `check-work/SKILL.md`, `code-review/SKILL.md`

### Technique 14: TDD for skills (RED-GREEN-REFACTOR)

**Source:** superpowers `writing-skills` (ENABLED on Grok Build)
**What it does:** if you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.
**The cycle:** RED (run pressure scenario without skill, document failures) → GREEN (write skill addressing those failures) → REFACTOR (find rationalizations to skip, add counters, re-test).

### Technique 15: Held-out validation

**Source:** `skillopt` (Codex-native)
**What it does:** only accept a skill improvement if it wins on examples NOT used to drive the edit. Prevents overfitting to specific test cases.
**Procedure:** split evidence into training (drive the edit) and held-out (validate). Score baseline on both. Apply edit. Score candidate on both. Accept only if: improves on ≥1 dimension, no regression on others, gain supported by held-out.

### Technique 16: Description optimization

**Source:** `skill-write` (cc-skills-architect) + `skill-creator` (Anthropic marketplace)
**What it does:** the `description` frontmatter field is the ONLY signal the model sees at selection time. Optimize for trigger accuracy using train/test split.
**Procedure:** generate 20 eval queries (8-10 should-trigger, 8-10 should-not-trigger). Split 60/40 train/held-out. Evaluate, propose improvements, re-evaluate on both. Select by TEST score, not train.

### Technique 17: Pressure testing for discipline skills

**Source:** superpowers `writing-skills`
**What it does:** discipline-enforcing skills need to resist rationalization. Test under pressure, not neutral conditions.
**Pressure types:** time, sunk cost, authority, exhaustion. Combine 2-3. Run scenario with skill loaded; observe compliance vs rationalization. Capture rationalizations, add counters, re-test.

### Technique 18: Rationalization tables

**Source:** superpowers `writing-skills`
**What it does:** agents find loopholes under pressure. Capture every rationalization explicitly and counter it in the skill body.
**Pattern:** each excuse gets a row: `| Excuse | Reality |`. "Too simple to test" → "Simple code breaks. Test takes 30 seconds."

## Q3: Are we doing anything unique that should be documented?

**Yes — the 12 techniques above.** Most are already documented across individual wiki concepts and AGENTS.md rules. The techniques index at [[skill-techniques-index]] consolidates them. What was missing before this session:

- **No consolidated view** of which skills do what (the catalog fixes this)
- **No techniques index** mapping failure modes to techniques (the techniques index fixes this)
- **No documentation of what's unique** vs industry best practices (this concept fixes this)

## Relationship to existing concepts

- [[skill-catalog]] — auto-generated index of all 248 skills
- [[skill-techniques-index]] — 19 reusable techniques with failure-mode-to-technique mapping
- [[skill-authoring-patterns-dos-and-donts]] — industry best practices (Anthropic, generativeprogrammer, anthonytd, Graphite)
- [[compound-skill-improvement-patterns]] — patterns specific to compound/orchestrator skills
- [[skill-enforcement-layers]] — Claude Code skill enforcement layer analysis
- [[fabricated-causal-chain-receipt-required]] — technique 10 (verification receipt)
- [[deliberation-waste-re-deriving-same-answer]] — technique 11 (deliberation discipline)
- [[multi-agent-correlated-errors]] — informs technique 1 (two-lens critique)
- [[evidence-first-default-and-needless-confirmation]] — technique 4 (preflight)

## Open questions

- Should `/skill-to-page` be run on all our unique-technique skills to generate per-skill wiki pages? (Currently the catalog + techniques index cover this; per-skill pages would add depth but also maintenance burden)
- Are there techniques in the marketplace skills (cc-skills-architect, cc-skills-analysis) that we should adopt?
- Should the "unique techniques" section be promoted to its own concept page for searchability?

## Regeneration

This concept is **curated**, not auto-generated. Update when:
- A new unique technique is developed
- A technique is adopted into additional skills
- A technique is retired or superseded

## Auto-related

- [[skill-enforcement-layers]]

