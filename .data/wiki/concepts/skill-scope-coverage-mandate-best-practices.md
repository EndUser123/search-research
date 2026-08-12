---
title: "Skill scope coverage mandate best practices: how other repos and frameworks define what their pipelines surface"
created: 2026-08-12
source: session-019ff1a0
tags: [skills, scope, coverage-mandate, pipeline-design, anti-rationalization, transferable-technique, research]
summary: >
  Research across 6+ frameworks (Agent Skills standard, heliohq/ship,
  ucb-bar/autocomp, meta-agent-teams, FinXScope, and Definition-of-Done
  literature) on how teams define what their agent pipelines and skills
  must cover. Three distinct layers emerged: routing (when to invoke),
  purpose (what it achieves), and coverage mandate (what it must surface).
  Most frameworks conflate routing + purpose in the description field and
  leave coverage implicit — exactly the gap that caused our scope-boundary
  rationalization failure. The fix pattern: explicit coverage table +
  anti-rationalization clause, which we already implemented. This research
  validates the approach and adds 5 transferable techniques from other repos.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (Anthropic, 2026)
  - https://agentskills.io/specification (Agent Skills open standard, 2026)
  - https://github.com/heliohq/ship (heliohq, 2026)
  - https://github.com/ucb-bar/autocomp/blob/main/autocomp/agent_builder/README.md (ucb-bar, 2026)
  - https://github.com/jbrahy/meta-agent-teams (jbrahy, 2026)
  - https://github.com/agentscope-ai/agentscope-java/blob/master/docs/v2/en/blogs/usecases/finxscope.md (agentscope-ai, 2026)
relations:
  - target: wiki/concepts/pipeline-pause-phase-schema-contract.md
    type: complements
  - target: wiki/concepts/scope-matching-verification-discipline.md
    type: extends
  - target: wiki/concepts/llm-sycophancy-calibration-failure-research-2026.md
    type: related
  - target: wiki/concepts/done-trigger-fires-on-artifact-creation-not-integration.md
    type: related
  - target: wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md
    type: related
---

# Skill scope coverage mandate best practices

## Decision context

This session hit the same failure three times: agent encounters a scanner
gap in ship-py/close-py, rationalizes it as a "scope boundary," operator
corrects. Root cause: the skills had a description (routing) and a Goal
(purpose) but no coverage mandate (what the pipeline must surface). We
added coverage mandates + anti-rationalization clauses. The question:
do other repos and frameworks solve this differently, and what can we learn?

## Key finding: three layers, usually conflated

Across 6+ frameworks, three distinct layers of skill/pipeline definition
appear. Most frameworks conflate the first two and leave the third implicit:

| Layer | What it answers | Where it lives | Coverage |
|-------|----------------|----------------|----------|
| **Routing** | When to invoke this skill? | `description:` frontmatter | Universal — every framework has this |
| **Purpose** | What does it achieve? | Goal/summary section or description tail | Common — most skills state this |
| **Coverage mandate** | What must it surface? | **Usually missing** | Rare — this is the gap |

The Agent Skills open standard (agentskills.io) and Anthropic's best
practices guide describe `description` as covering both "what it does"
and "when to use it" — but not "what categories of issues it must surface."
The standard says: "Keep SKILL.md lean... Define clear scope: explicitly
state what the skill covers (and sometimes what it doesn't)."

This is the routing/purpose layer. No framework in the survey explicitly
requires a coverage mandate table that lists issue categories the pipeline
is responsible for detecting.

## What other repos do (5 transferable techniques)

### 1. heliohq/ship — evidence hierarchy + phase coverage matrix

heliohq/ship (an agentic development harness for Claude Code) has the
closest pattern to what we implemented. Each pipeline phase requires
specific evidence artifacts (L1: screenshots/curl/logs preferred; L2:
weak; L3: "should work" = automatic fail). The pipeline defines a
**phase coverage matrix** that maps acceptance criteria against phases.

**Transferable:** ship's coverage matrix is checked via a router skill
(`/ship:use-ship`) that verifies every acceptance criterion has a phase
covering it. This is the same pattern as our coverage mandate table, but
enforced by a router skill rather than a clause in the SKILL.md body.

Source: https://github.com/heliohq/ship

### 2. ucb-bar/autocomp — explicit agent scope with out-of-scope statement

The autocomp Agent Builder requires an `--agent-scope` flag that explicitly
lists what the agent optimizes AND what is out of scope:

> "Optimizing NKI kernel code on AWS Trainium 1. The agent rewrites
> single-kernel source code for better performance. Model-level concerns
> like sharding, serving, and distributed training are out of scope."

This scope is prepended to every prompt and used for document filtering.

**Transferable:** the "explicit out-of-scope" statement is something our
coverage mandate table does NOT have. Adding a "What ship-py does NOT
cover" row would make boundaries explicit rather than discovered through
failure. But note: our anti-rationalization clause warns against using
out-of-scope statements to rationalize gaps. The balance is: state
out-of-scope for things genuinely outside the domain (e.g., ship-py
doesn't do security audits), not for things inside the domain that the
scanner hasn't implemented yet.

Source: https://github.com/ucb-bar/autocomp/blob/main/autocomp/agent_builder/README.md

### 3. jbrahy/meta-agent-teams — constitution + auditor

meta-agent-teams defines a **constitution** (inviolable constraints no
agent may cross) plus an independent **auditor** agent that reviews
proposals for constitutional compliance, drift, and regression. The
constitution includes sections for Scope of Authority, Ethical Boundaries,
Evolution Rules, and Data Handling.

**Transferable:** the auditor pattern is a structural enforcement layer
for scope boundaries. Our coverage mandate + anti-rationalization clause
is a cognitive layer (the agent reads it). The auditor pattern adds a
mechanical layer (a separate agent checks compliance). For our workspace,
the `/review` skill already serves this role — but it's not explicitly
mandated to check coverage mandate compliance.

Source: https://github.com/jbrahy/meta-agent-teams

### 4. FinXScope (agentscope-java) — three-layer skill definition

FinXScope defines three layers of skill complexity: (1) YAML config for
simple tasks, (2) SKILL.md + scripts for medium tasks, (3) Java beans for
complex logic. Each layer has explicit scope boundaries and permission
filtering (NONE/FILTER/REJECT modes).

**Transferable:** the permission filtering concept — skills declare what
resources they're allowed to touch, and the runtime enforces it. Our
coverage mandate is informational; FinXScope's is enforcement. The gap:
our coverage mandate says what to scan, but doesn't enforce that all
categories are actually scanned.

Source: https://github.com/agentscope-ai/agentscope-java

### 5. Definition-of-Done literature — evidence-before-claim gates

The DoD literature (paelladoc, airaxai, verification-before-completion
skills) converges on one principle: **"Done" is a state demonstrated by
artifacts, not a claim.** The checklist pattern requires evidence
production before any success statement. Common rationalizations blocked:
"Agent said it worked" -> must independently verify; "Partial checks are
enough" -> full checklist required; "Looks correct" -> run the actual
verification.

**Transferable:** this is the same principle as our anti-rationalization
clause but applied to the completion claim. Our clause catches the agent
at the rationalization moment ("if you find yourself explaining why a gap
is acceptable... STOP"). The DoD pattern catches it at the claim moment
("no claims without fresh evidence"). Both are needed.

Sources:
- https://paelladoc.com/blog/definition-of-done-ai/
- https://github.com/majiayu000/claude-skill-registry (verification-before-completion)

## What this means for our workspace

Our coverage mandate + anti-rationalization clause (commit `3ef37c8`) is
novel relative to the frameworks surveyed — no other repo explicitly
requires a coverage table with an anti-rationalization anchor. The closest
patterns are:

- heliohq/ship's phase coverage matrix (but enforced by router, not clause)
- meta-agent-teams' constitution + auditor (but structural, not cognitive)
- DoD literature's evidence-before-claim (but on completion, not scope)
- [[scope-matching-verification-discipline]] (but on claim verification, not scope coverage)

Our implementation is the **cognitive layer**: the agent reads the clause
at the moment it's running the skill and encounters a gap. The structural
layers (router enforcement, auditor agent, mechanical coverage check)
are potential upgrades:

| Upgrade | Pattern source | Effort | Priority |
|---------|---------------|--------|----------|
| Coverage check in verdict phase (block SHIP DONE if category uncovered) | heliohq/ship router | Medium | Medium — catches gaps mechanically |
| `/review` checks coverage mandate compliance | meta-agent-teams auditor | Low | Low — /review already runs |
| Scanner registry that tracks which categories exist | FinXScope permissions | High | Low — overengineering for now |

**The cognitive layer is sufficient for now.** The anti-rationalization
clause catches the failure at the moment it happens. Structural enforcement
is the upgrade path if the cognitive layer proves insufficient under
closure pressure (which is the documented failure mode of prose rules —
see [[theatrical-contrition-and-over-apologetic-response-patterns]]).

## Falsifier

This research would be wrong if:
- The surveyed frameworks DO have coverage mandates that I missed (possible —
  many skills have implicit coverage in their phase list, which I treated as
  purpose rather than coverage)
- The anti-rationalization clause proves insufficient under closure pressure
  (likely — prose rules have ~50% compliance ceiling per
  [[false-choices-parallel-branch-framing]]; the structural layer would be
  needed)
- The three-layer model (routing/purpose/coverage) is wrong, and the
  frameworks' two-layer model (description/body) is actually sufficient
  (unlikely given our session evidence — the two-layer model failed 3 times)

## What people like

From the survey, practitioners value:
- **Explicit boundaries** — the autocomp `--agent-scope` pattern is praised
  for making filtering deterministic
- **Evidence hierarchies** — heliohq/ship's L1/L2/L3 evidence tiers prevent
  "should work" rationalizations
- **Independent verification** — meta-agent-teams' auditor catches what
  self-assessment misses

## What people don't like

- **Implicit coverage** — every framework surveyed leaves coverage implicit;
  practitioners discover gaps through failure, not design
- **Scope creep in skills** — Anthropic's best practices warn against
  too-broad skills ("too broad -> imprecise activation and conflicting
  instructions")
- **No anti-rationalization patterns** — no framework has a clause that
  catches the agent at the rationalization moment; they rely on evidence
  gates and auditors, which are downstream of the rationalization

## Receipts

- **ship-py SKILL.md coverage mandate**: `~/.grok/skills/ship-py/SKILL.md` "Coverage mandate" section, commit `3ef37c8`
- **close-py SKILL.md coverage mandate**: `~/.grok/skills/close-py/SKILL.md` "Coverage mandate" section, commit `3ef37c8`
- **Agent Skills best practices**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **heliohq/ship phases**: https://github.com/heliohq/ship (7-phase pipeline with evidence gates)
- **autocomp scope**: https://github.com/ucb-bar/autocomp/blob/main/autocomp/agent_builder/README.md
- **meta-agent-teams constitution**: https://github.com/jbrahy/meta-agent-teams/blob/main/docs/architecture.md

## Sources

- [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) (Anthropic, 2026) — description field covers routing + purpose, not coverage
- [Agent Skills Specification](https://agentskills.io/specification) (agentskills.io, 2026) — open standard, no coverage mandate requirement
- [heliohq/ship](https://github.com/heliohq/ship) (heliohq, 2026) — phase coverage matrix + evidence hierarchy
- [ucb-bar/autocomp Agent Builder](https://github.com/ucb-bar/autocomp/blob/main/autocomp/agent_builder/README.md) (ucb-bar, 2026) — explicit agent scope with out-of-scope
- [jbrahy/meta-agent-teams](https://github.com/jbrahy/meta-agent-teams) (jbrahy, 2026) — constitution + independent auditor
- [agentscope-java FinXScope](https://github.com/agentscope-ai/agentscope-java/blob/master/docs/v2/en/blogs/usecases/finxscope.md) (agentscope-ai, 2026) — three-layer skill definition
- [Definition of Done for AI Agents](https://paelladoc.com/blog/definition-of-done-ai/) (PaellaDoc, 2026) — evidence-before-claim gates
- [AI Agent Definition of Done](https://airaxai.com/en/digital-marketing/insights/ai-agent-definition-of-done) (AirAxAI, 2026) — DoD checklist pattern
- [verification-before-completion skill](https://github.com/majiayu000/claude-skill-registry/blob/main/skills/development/verification-before-completion-baqif2-claude-replica/SKILL.md) (claude-skill-registry, 2026) — blocks rationalization with evidence requirement

## Auto-related

- [[skill-graph]]
- [[scope-matching-verification-discipline]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[opentelemetry-logging]]

