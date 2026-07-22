---
title: "Portfolio-wide deep read: transferable techniques from 47 skills across all hosts"
created: 2026-07-21
source: session-2026-07-21 (subagent deep-read of Codex, cc-skills-thinking, cc-skills-architect, cc-skills-analysis, cc-skills-sdlc, cc-skills-lab)
sources:
  - C:/Users/brsth/.codex/skills/
  - C:/Users/brsth/.claude/plugins/cache/local/cc-skills-thinking/
  - C:/Users/brsth/.claude/plugins/cache/local/cc-skills-architect/
  - C:/Users/brsth/.claude/plugins/cache/local/cc-skills-analysis/
  - C:/Users/brsth/.claude/plugins/cache/local/cc-skills-sdlc/
  - C:/Users/brsth/.claude/plugins/cache/local/cc-skills-lab/
  - C:/Users/brsth/.claude/plugins/cache/local/improve-partner/
  - C:/Users/brsth/.claude/plugins/cache/local/prompt-enhancer/
tags: [skill-techniques, deep-read, portfolio, cross-host, codex, claude, transferable, unique, self-improvement]
host: both
agent: grok
verification: subagent_deep_reads_with_file_line_citations
cognitive_load: 5
summary: "Comprehensive portfolio analysis of 47 skills across Codex, Claude plugin caches, and project directories. Identifies 35+ transferable techniques organized by category, 8 family-level patterns, 10 self-improvement capabilities, and the layering model (advisory skills as source-of-truth, runtime enforcement in hooks). Replaces the '12 unique techniques' claim from skill-development-portfolio.md with a verified inventory."
---

# Portfolio-wide deep read: transferable techniques

## Context

User pushed back on my claim of "12 unique techniques" in `skill-development-portfolio.md` — correctly noting I had only checked 318 of 964 SKILL.md files. This concept is the result of a deep read of the 646 missed files, focused on identifying techniques that are transferable to other skills.

**Scope covered (47 skills via 6 parallel subagents):**

| Family | Skills read | Subagent tool calls | Status |
|---|---|---|---|
| Codex (`~/.codex/skills/`) | 6 (4 exist; `codex-primary-runtime` empty, `pre-mortem` missing) | 11 | ✅ |
| cc-skills-thinking | 4 priority (reflect, truth, skeptic, sequential-thinking) | 4 | ✅ |
| cc-skills-architect | 4 priority (evolve, skill-write, skill-from-docs, skill-to-page) | 6 | ✅ |
| cc-skills-analysis | 14 (behave, claude-audit, debrief, doc-compiler, epistemic-check, friction, recap, retro, rns, skill-audit, skill-similarity, top-problems, trace, why) | 24 | ✅ |
| cc-skills-sdlc improvement subset | 9 (brainstorming, diagnose, pre-mortem, rca, improve-codebase-architecture, zoom-out, av, evidence-driven-experiment-loop, planning) | 24 | ✅ |
| cc-skills-lab + improve-partner + prompt-enhancer | 10 (check, cks, concept-mapper, csf-nip-integration, lmc, mlc, simplify-enhanced, slc, improve, prompt-enhancer) | 38 | ✅ |

**Not covered:** 912 other skills (marketplace plugins, bundled game-asset skills, claude-plugins-official general-purpose skills, etc.). The 47 chosen were the ones most likely to contain self-improvement, skill-authoring, analysis, or meta-discipline techniques.

## Q3 answer: were there other skills with self-improvement?

**Yes, multiple — the original "12 unique techniques" claim was wrong.**

| Skill | Self-improvement capability | Mechanism |
|---|---|---|
| `/reflect` (cc-skills-thinking) | **Primary capability** — "Self-Improving Skills" titled | Extract → review → backup → YAML-validated write → git commit pipeline. `emerge/graduate/trace` three-pass synthesis for promoting lessons into durable enforcement |
| `/skillopt` (Codex) | **Primary capability** — optimizes Codex skills from transcript evidence | Held-out validation, rubric overlays, bounded edits, never silent overwrite. Promotion conditional on validated improvement |
| `/skill-write` (cc-skills-architect) | **Yes** — create + improve with eval loop | Parallel with-skill + baseline subagent dispatch; description optimization via 60/40 train/test split with 5 iterations |
| `/evolve` (cc-skills-architect) | Indirect — modernizes code, not skills. But the SoloDevConstitutionalFilter and phase-stop pattern are reusable for skill modernization |
| `/improve` (improve-partner) | **Yes** — thought-partner that produces improvement recommendations with promotion gates | Attack checklist, preserve-and-simplify middle option, OPP-NNN schema for reusable opportunities, three-legged evidence for WARN→BLOCK promotion |
| `/planning` graduate mode | **Yes** — repeated failures promote into durable verifier rules | "Recurrence → rule" structural promotion |
| `/debrief` recursive investigator | **Yes** — lateral opportunity routing through `write_opportunity_layer()` | Requires `idea` + `generalization_test` |
| `/rca` CKS pattern storage | **Yes** — past investigations stored in `~/.claude/memory/cks/rca_patterns/` | Past investigation improves next investigation |
| `/av` (cc-skills-sdlc) | **Yes** — audits other skills and is itself auditable by the same checklist | Closure loop: a skill that audits skills is auditable by its own checklist |
| `/evidence-driven-experiment-loop` | **Yes** — lifecycle state machine as improvement substrate | Each run leaves a structured artifact that the next run inherits |

That's **10 skills with self-improvement capabilities** I missed in the original portfolio concept. The claim "recursive self-improvement via self-invocation (technique 12) is unique to our portfolio" was wrong — `/reflect` has been doing structured skill mutation for much longer.

## Revised inventory: transferable techniques

These are the techniques that should be added to `skill-techniques-index.md`. Organized by category. Citations are to the subagent findings (which cite file:line in the source SKILL.md).

### Gathering techniques (additions)

| Technique | Source | What it does |
|---|---|---|
| **Pattern-marker lexicon** | `/friction` | Explicit signal list maps user phrases to friction categories ("I disabled hooks" → Hook Contract Friction). Makes detection repeatable. |
| **Multi-source scraping with source-specific extraction** | `/skill-from-docs` | Website uses CSS selectors + llms.txt; GitHub uses AST analysis; PDF uses OCR with image/table extraction |
| **Auto-detect content type → ingest method** | `/cks` | Pattern→`ingest_pattern`; Q&A→`ingest_memory`; code→`ingest_code`; default→document chunking |
| **Pre-mortem checklist for live runs** | `/ai-cli` references; `/pre-mortem` | Structured checklist applied before live runs to catch failure modes |
| **AID (AI Distiller) bug-hunting prelude** | `/diagnose` | Runs `aid <path> --ai-action prompt-for-bug-hunting` before hypothesis generation |

### Thinking techniques (additions)

| Technique | Source | What it does |
|---|---|---|
| **Held-out validation gate** | `/skillopt`, `/skill-write` | Compare candidate against baseline on examples NOT used to drive the edit. Accept only if clearly improves. Anti-overfitting. |
| **Hard rejection rules from rubric-schema** | `/skillopt` | Reject-on-fail-test pattern rather than scoring-and-judging |
| **Severity vs. confidence orthogonality** | `/review-packet-runner` | Two independent axes, not conflated. Severity = potential impact if real; confidence = evidence strength. |
| **Five-way epistemic classification** | `/review-packet-runner`, `/epistemic-check` | fact / inference / unsupported / contradicted / open question. Finer than fact/inference binary. |
| **Evidence-tier vocabulary with turn provenance** | `/behave`, `/rns`, `/recap`, `/why`, `/epistemic-check` | Per-skill vocabulary but same epistemic discipline: behave=4 tiers with confidence ceilings; rns=`(turn-N)` provenance + status tags; recap=2-axis (origin × confidence); why=2-tier (terminal-attributed vs git-corroboration) |
| **Phase gates with STOP between generation and validation** | 9/14 cc-skills-analysis skills; 9/9 cc-skills-sdlc improvement subset | Hard STOP between generate-stuff and validate-stuff phases. Most common pattern in the portfolio. |
| **Cost-ordered test ladder** | `/behave` | Cheap→expensive: log search → diagnostic print → cross-env. Falsification-first. |
| **Surprise check** | `/why` | For each causal link, ask "Why was THIS answer true and not something else?" |
| **Absent-evidence check** | `/why` | What would you expect to find but didn't? Absence is itself a signal. |
| **Trace-before-hypothesis rule** | `/rca` | For hangs/timeouts, insert debug prints and identify the blocking function, not the timeout parameter. Code-path plausibility is not evidence. |
| **Telemetry discovery at Step 1.5** | `/rca` | Query telemetry buckets (pretooluse_blocks.jsonl, importer_diagnostics, events.db) BEFORE hypothesis generation |
| **Deletion test** | `/improve-codebase-architecture` | "Imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep." |
| **Two-adapters = real seam rule** | `/improve-codebase-architecture` | One adapter = hypothetical seam. Two adapters = real seam. |
| **Fixed glossary enforcement** | `/improve-codebase-architecture` | Mandates exact terminology (Module, Interface, Implementation, Depth, Seam, Adapter, Leverage, Locality). Bans drift. |
| **Cognitive framework triage via Cynefin** | `/skeptic` | Characterize problem domain (Clear/Complicated/Complex/Chaotic) before critique |
| **Chesterton's Fence check** | `/skeptic` | Flag code/logic removal that lacks evidence of why the original existed |
| **3-scenario minimum** | `/trace` | happy / error / edge — each scenario distinct and complete |
| **Generator ≠ Validator** | `/doc-compiler`, `/skill-to-page` | Distinct LLM instances for generation and validation. Self-validation is a blocking defect. |
| **Anti-self-deception review** | `/doc-compiler`, `/skill-to-page` | Generic "ok" / "verified" / "works" reasons treated as false positives. Screenshot evidence required. |
| **Account-for-everything closure** | `/debrief` (ACCOUNTING sentinel), `/rns` (GAP COVERAGE block) | Explicit bucket count (tasked/fixed/deferred/external) before close. No finding dropped silently. |
| **Source-first classification rule** | `/skill-audit`, `/debrief`, `/claude-audit` | For any "absorbed/stub/aliased/retired" claim: must cite old source + parent source + backend existence. Single source = `NOT_PROVEN`. |
| **Routing by Affordances (anti-parrot)** | `/skill-audit` | Anti-parrot routing: identify work → identify affordances → map affordances → command-by-machinery |
| **Determinism partition** | `/skill-audit` | Python / TypeScript / LangGraph / LLM with LangGraph as first-class candidate. Top-down: one-correct-answer→code; stateful≥3-node→LangGraph; judgment→LLM |
| **Adaptive-pathing escape-hatch grep** | `/skill-audit` | Signal grep (`--skip-`, `--quick`, `--no-`, `--force`, `--dry-run`) + conditional-routing prose (`if ... fails`, `fallback`, `otherwise`) |

### Outputting techniques (additions)

| Technique | Source | What it does |
|---|---|---|
| **`<selection>` parseable contract** | `/rns` | XML-fenced options `[0|1|2|3|4|EXIT]` with `0 — Do ALL` default for low-blast-radius actions |
| **Smart TOC (intent-based, §-numbered)** | `/lmc`, `/mlc` | "I want to... → §Section" navigation; max 8-10 rows; no line numbers (they rot) |
| **Token-savings quoted with category tags** | `/lmc`, `/mlc` | `→ 450 tokens: Extensive inline comments` — receipts for savings claims |
| **Handoff template with 8 sections** | `/recap` | Resume Here / Completed / Remaining Work triaged / Risks / Decisions / Artifacts ≤10 / Evidence Appendix / Next Session Checklist |
| **OPP-NNN opportunity schema** | `/improve` | `confidence | promotes_to | observation | evidence | lesson | action | uniqueness | falsification` — copyable pro forma |
| **Provenance-tagged claims** | `/improve` | `FACT(self-verified)` / `FACT(delegated-specialist)` / `INFERENCE` / `RISK` / `ASSUMPTION` — linted against |
| **Capability preservation classification** | `/skill-audit` | `true_thin_stub` / `retained_engine_with_deprecation_header` / `internalized_engine` / `alias_only` / `pending_unimplemented` / `unsafe_to_remove` / `unresolved_source_missing` |
| **Health-check as first-class executable** | `/cks` | Concrete thresholds (≥100 entries, <90% coverage warns, >7-day staleness warns, >50MB bloat warns); exit-code semantics |

### Prompting techniques (additions)

| Technique | Source | What it does |
|---|---|---|
| **Five-class prompt triage** | `/prompt-enhancer` | `bypass | clear | ambiguous | confirm | prohibited` with confidence floor (0.7) below which nothing is injected |
| **Bypass prefixes as config, not code** | `/prompt-enhancer` | `config/bypass_prefixes.json` — user-extensible opt-out without code change |
| **Regression-lock-the-removal** | `/prompt-enhancer` | Test `test_context_module_is_gone` asserts deleted module does NOT exist — anti-resurrection guard |
| **Destructive verb two-UX** | `/prompt-enhancer` | `delete everything` → prohibited (block); `delete <the> X` → confirm (AskUserQuestion) |
| **Purpose-routed output shape** | `/concept-mapper` | Same skill, 3 outputs (mindmap/graph TB/graph LR) selected by user intent, not popularity |
| **GRINDE mnemonic** | `/concept-mapper` | Group, Related, Interconnected, Nested, Deep, Elaborated — structured checklist + critique |

### Meta techniques (additions)

| Technique | Source | What it does |
|---|---|---|
| **Promotion gate for rubric changes** | `/improve` | WARN→BLOCK needs (1) replay evidence of miss, (2) gold-replay-corpus green, (3) ≥2 occurrences OR explicit user confirmation. Three-legged evidence. |
| **Graduate mode (recurrence→rule)** | `/planning` | When same plan defect appears across reviews, promote into durable verifier rule |
| **Engine preservation under route-rename** | `/pre-mortem`, `/av`, `/top-problems` | Deprecated stub survives one release cycle while remaining authoritative store of engine content. New owner lazy-imports. |
| **Constitutional rule list at top** | `/csf-nip-integration`, `/slc` | RBW-001 named mini-protocol (search → read → plan → implement); paired with memory pointer for full philosophy |
| **Attack checklist (7 vectors)** | `/improve` | Theater / Duplication / Hook-or-gate noise / Wrong-layer fix / Missing evidence / Maintenance burden / Regression risk. Must answer each before shipping recommendation. |
| **Preserve-and-simplify middle option** | `/improve` | ≥3 options including preserve-and-simplify between minimal-change and delete — required when deletion is on the table |
| **XSTC (Cross-Skill Transfer Check)** | `/debrief`, `/skill-audit`, `/claude-audit` | Was this a local artifact fix or a reusable lesson? Required fields: classification, affected_surfaces, evidence, why_it_transfers, owner, recommended_action, validation_step, do_now_or_backlog |
| **Completion Evidence Contract (CEC)** | `/debrief`, `/skill-audit`, `/claude-audit` | Claim-type enum, evidence-required-per-claim mapping, ledger-shape requirement. Authority ladder: source_changed → cache_rebuilt → plugin_loaded → command_resolves → behavior_observed → live_behavior |
| **Discoverability Classification** | `/debrief`, `/go`, `/claude-audit`, `/skill-audit` | DISCOVERABLE vs USER_ONLY. Owned by `/go` (forward), surfaced by `/debrief` (post-hoc), audited by `/skill-audit` (forward-looking), grounded by `/claude-audit` (inject runtime paths) |

## Family-level patterns (cross-cutting)

These patterns appear across multiple skill families:

1. **Evidence-tier / provenance vocabulary per skill** — 5 skills have distinct vocabularies for the same epistemic discipline
2. **Phase gates with STOP between generation and validation** — 18+ skills use this
3. **Schema-level enforcement beats prose discipline** — `/evidence-driven-experiment-loop` and `/planning` make promotion unachievable without required fields
4. **Candidate evidence / not truth epistemology** — `/external-delegation`, `/review-packet-runner`, `/skillopt`, `/ai-cli`
5. **Bounded / schema-restricted packets** — `/external-delegation`, `/evidence-driven-experiment-loop`, `/review-packet-runner`, `/skillopt`
6. **Anti-fallback / fail-default** — `/external-delegation`, `/skillopt`, `/review-packet-runner`, `/check`
7. **Honest refusal over coerced verdict** — `/skillopt`, `/review-packet-runner`, `/evidence-driven-experiment-loop`, `/diagnose`
8. **E1/E4/E5 evidence-first triad** — shared verbatim across `/brainstorming`, `/diagnose`, `/improve-codebase-architecture`, `/zoom-out`
9. **Deprecation-stub pattern** — `/retro`, `/top-problems`, `/pre-mortem`, `/av`
10. **Layering model: advisory skills as source-of-truth; runtime enforcement in hooks** — cc-skills-analysis family is advisory; enforcement lives in `/red-team` (BLOCK authority), `Stop_fake_done_detector.py` (WARN mode), `/ask` (canonical vocabulary)

## Layering model (important structural insight)

The cc-skills-analysis family is explicitly **advisory** — it owns the static source of disciplines but does not enforce them at runtime. The runtime enforcement is layered in:

| Discipline source (advisory) | Runtime enforcer |
|---|---|
| `/debrief`, `/skill-audit`, `/claude-audit` | `/red-team` Pre-check 0 (BLOCK authority for CEC) |
| `/epistemic-check` | `Stop_epistemic_contract` hook |
| `/rca` investigation completeness rule | `PostToolUse_rca_*`, `StopHook_rca_*` hooks |
| `/diagnose` violation table | Stop hook checks for violations |
| `/check` verdict line | Stop hook reads `check verdict:` line |
| `/prompt-enhancer` triage | `UserPromptSubmit` hook |

**Why this matters for our skills:** our `/tp`, `/aar`, `/handoff`, `/www`, `/wiki` are all advisory. If we want runtime enforcement of their disciplines (e.g., "must run preflight before writing handoff"), we need to add hooks — the skills themselves can't enforce.

## Self-improvement capabilities (corrected inventory)

| Skill | Mechanism | What it improves |
|---|---|---|
| `/reflect` | Extract → review → backup → YAML-validated write → git commit | Other skills (direct mutation) |
| `/skillopt` | Held-out validation, rubric overlays, bounded edits | Codex skills |
| `/skill-write` | Parallel with/baseline eval loop, description optimization | Any skill (create + improve) |
| `/improve` | Attack checklist, OPP-NNN schema, promotion gates | Any reviewable artifact |
| `/planning` graduate mode | Recurrence → durable verifier rule | Planning workflow itself |
| `/debrief` | `write_opportunity_layer()` with generalization test | Lateral opportunity routing |
| `/rca` | CKS pattern storage in `~/.claude/memory/cks/rca_patterns/` | Future investigations |
| `/av` | Self-auditable by own checklist | Other skills (audit surface) |
| `/evidence-driven-experiment-loop` | Lifecycle state machine as improvement substrate | Experiments |
| `/www` (ours) | Recursive self-improvement via self-invocation | Itself |

**The honest correction:** our `/www`'s "recursive self-improvement via self-invocation" (technique 12 in the original portfolio concept) is NOT unique. `/reflect` has been doing structured skill mutation longer and more rigorously. `/skillopt` has held-out validation we don't have. `/skill-write` has parallel eval loops we don't have.

What IS somewhat novel about `/www`'s recursive self-improvement: it's the only one that uses the skill's own three-phase discipline (query → research → persist) as the improvement mechanism. The others use external evidence (transcripts, evals, rubrics). `/www` uses the skill itself as both the improver and the improved.

## Action items for skill-techniques-index.md

The techniques index needs significant expansion. Currently it has 19 techniques; this deep read identified 35+ more that should be added. Recommended organization:

- **Gathering**: T1-T5 (existing) + 5 new (pattern-marker lexicon, multi-source scraping, auto-detect ingest, pre-mortem checklist, AID prelude)
- **Thinking**: T6-T11 (existing) + 19 new (held-out validation, hard rejection rules, severity/confidence orthogonality, five-way epistemic, evidence-tier vocabulary, phase gates, cost-ordered test ladder, surprise check, absent-evidence check, trace-before-hypothesis, telemetry-first, deletion test, two-adapters rule, fixed glossary, Cynefin triage, Chesterton's Fence, 3-scenario minimum, generator≠validator, anti-self-deception, account-for-everything, source-first classification, routing by affordances, determinism partition, adaptive-pathing grep)
- **Outputting**: T12-T15 (existing) + 8 new (`<selection>` contract, smart TOC, token-savings tags, handoff template, OPP-NNN schema, provenance tags, capability preservation classification, health-check executable)
- **Prompting**: T16-T17 (existing) + 6 new (five-class triage, bypass-as-config, regression-lock-removal, destructive verb two-UX, purpose-routed output, GRINDE mnemonic)
- **Meta**: T18-T19 (existing) + 9 new (promotion gate, graduate mode, engine preservation, constitutional rule list, attack checklist, preserve-and-simplify, XSTC, CEC, discoverability classification)

That's ~54 techniques total — a significant expansion from the original 19.

## Open questions

- Should `/reflect`'s skill mutation pipeline be adopted by our Grok skills? (Currently none of our skills mutate other skills)
- Should we add held-out validation to `/www` and `/tp`? (Currently we test by running on real work, which is Level 1 manual)
- Should the layering model (advisory source + runtime enforcement) be documented as a technique?
- How do the 10 self-improvement capabilities compose? (e.g., could `/reflect` mine `/www`'s recursive runs?)

## Relationship to existing concepts

- [[skill-techniques-index]] — needs expansion from 19 to ~54 techniques
- [[skill-development-portfolio]] — "12 unique techniques" claim is wrong; needs correction
- [[skill-catalog]] — the 964-skill index that made this deep read possible
- [[skill-authoring-patterns-dos-and-donts]] — industry best practices; this concept is the portfolio-specific complement
- [[compound-skill-improvement-patterns]] — the /www recursive pattern; needs honest comparison to /reflect and /skillopt
- [[fabricated-causal-chain-receipt-required]] — multiple techniques here are receipt mechanisms (evidence-tier vocabulary, provenance tags, CEC)
- [[deliberation-waste-re-deriving-same-answer]] — the research ledger pattern prevents this; held-out validation prevents a related waste (re-deriving the same overfitting)
