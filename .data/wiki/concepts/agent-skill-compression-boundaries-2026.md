---
title: "Agent skill compression boundaries: progressive disclosure, deterministic code, MCP, and hooks"
created: 2026-08-07
source: session-2026-08-07
tags: [agent-skills, progressive-disclosure, deterministic-orchestration, mcp, hooks, reasoning, fleet-architecture]
summary: >
  Skill size should be reduced by moving detail behind progressive disclosure,
  moving parsing and validation into deterministic helpers, and reserving MCP
  and hooks for the boundaries where they add shared context or lifecycle
  authority. For a solo director running fleets of agents, the natural unit is
  one user-facing capability with a small routing front door and several
  internal protocols, not a separate skill for every reasoning adjective.
type: concept
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
confidence: 0.82
last_verified: 2026-08-07
half_life_days: 180
evidence_gaps:
  - The external evidence in this entry is based on MMX result snippets; the full pages were not fetched with a second browser in this run.
  - No controlled A/B measurement yet proves that a smaller Grok /tp package preserves catch rate, latency, or operator satisfaction.
  - The scoped preflight audit attempted for the live skill/capability surface timed out, so transitive callers and registrations remain an open verification item.
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: refines
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: related
  - target: wiki/concepts/agent-control-plane-enforcement-architectures-2026.md
    type: complements
  - target: wiki/concepts/skill-management-in-agentic-systems-research-survey.md
    type: related
sources:
  - "https://docs.anthropic.com/en/docs/claude-code/skills (Extend Claude with skills - Claude Code Docs; date not exposed by MMX)"
  - "https://developers.openai.com/codex/customization/overview (Customization - ChatGPT Learn; date not exposed by MMX)"
  - "https://developers.openai.com/codex/build-skills (Build skills - ChatGPT Learn; date not exposed by MMX)"
  - "https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture (Architecture overview - MCP; 2026-07-28)"
  - "https://modelcontextprotocol.io/specification/2026-07-28/server/prompts (Prompts - MCP; 2026-07-28)"
  - "https://modelcontextprotocol.io/specification/2026-07-28/server/resources (Resources - MCP; 2026-07-28)"
  - "https://modelcontextprotocol.io/specification/2026-07-28/server/tools (Tools - MCP; 2026-07-28)"
  - "https://github.com/anthropics/skills (anthropics/skills; date not exposed by MMX)"
  - "https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/skill-development/SKILL.md?plain=1 (Claude Code skill development; date not exposed by MMX)"
  - "https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md (obra/superpowers writing-skills; date not exposed by MMX)"
  - "https://docs.anthropic.com/en/docs/claude-code/hooks (Hooks reference - Claude Code Docs; date not exposed by MMX)"
  - "https://docs.anthropic.com/en/docs/claude-code/hooks-guide (Automate actions with hooks - Claude Code Docs; date not exposed by MMX)"
---

# Agent skill compression boundaries: progressive disclosure, deterministic code, MCP, and hooks

## Decision context

The operator is a solo director coordinating fleets of AI coders across Grok
Build, Claude Code, Codex, and other terminals. The problem is not simply that
there are many files. It is that user-facing concepts such as *think*,
*reason*, *genius*, *ultrathink*, and *thought partner* can become separate
skills even when they are variants of one workflow. The goal is to reduce
always-loaded instructions without removing behavior.

The durable boundary is:

> One user-facing capability owns intent and outcome; references own detail;
> deterministic code owns mechanics; MCP owns shared context/actions; hooks own
> lifecycle invariants and authority boundaries.

This refines [[code-orchestrates-model-judges-skill-scale]]: the model should
still judge framing, alternatives, uncertainty, and significance, while code
should own the repeatable coordination and validation around that judgment.

## Research findings

### Progressive disclosure is the common compression mechanism

The Anthropic Claude Code skills result says detailed reference files can be
linked from `SKILL.md` and loaded as needed. The OpenAI Codex customization
results describe a staged path from metadata to `SKILL.md` to additional
resources. The Anthropic skills repository and plugin-development result both
describe keeping the essential workflow in the entry file and moving detailed
references, schemas, and examples behind it. The Superpowers result describes
the same separation among workflow, references, and executable helpers.

These are independent source families pointing at the same design rule: the
entry file should explain *when to use the capability, what it guarantees, and
where the relevant detail lives*. It should not be an encyclopedia of every
mode, example, provider quirk, and historical rationale.

### The natural domains are internal modules, not necessarily separate skills

For a thought-partner or reasoning capability, five domains are enough to
organize the internals:

1. **Intent and routing** — determine whether the request is critique,
   exploration, session review, recap, or execution support.
2. **Evidence and discovery** — collect the transcript, workspace facts,
   prior wiki patterns, and relevant artifacts.
3. **Lens orchestration** — choose whether a fresh model or multiple model
   families are justified, and dispatch them.
4. **Synthesis and verification** — compare agreement and dissent, classify
   claims, state uncertainty, and select a verdict.
5. **Persistence and telemetry** — write receipts, critique history, durable
   findings, and outcome data.

The first four are one user-facing thought-partner capability with mode-specific
protocols. The fifth is mostly a platform service. Creating five separate
skills would increase discovery and trigger burden; keeping all five in one
1,700-line entry file would increase context load. Internal references and
helpers are the middle path.

### “Ultrathink” is a posture or control input, not a new domain

The architecture should treat a command such as `ultrathink` as a request for
greater depth, time, or reasoning budget subject to the host’s native behavior.
It can select a deeper protocol, higher evidence threshold, or larger lens
panel, but it should not duplicate the entire reasoning skill. The native
Claude Code command must remain the authority for Claude Code semantics; a
portable skill can layer on behavior only after detecting the host and the
native command’s actual contract. A Grok or Codex alias should never imply that
the Claude command exists there.

## Boundary rules for shrinking a skill

| Concern | Keep in the entry skill | Move to code, references, MCP, or hooks |
|---|---|---|
| Trigger and intent | Short semantic intent table and explicit user override rules | Pure parsing, normalization, and manifest creation in a helper |
| Workflow | Ordered phases, stop conditions, output contract | Long protocols, examples, schemas, and provider notes in references |
| Judgment | Framing challenge, alternatives, dissent, significance | Never replace with a deterministic score that pretends to be judgment |
| Mechanics | The invariant the helper guarantees | File scans, counts, retries, command construction, JSON validation, and telemetry in code |
| Shared context | Name the source and retrieval condition | Wiki search, current documentation, and cross-agent artifacts through existing MCP/resources |
| Lifecycle enforcement | State what must be true at completion | A scoped hook checks a run receipt or state witness; it does not perform reasoning |
| Historical rationale | One sentence and a link | Full incident history and research notes in wiki/reference pages |

Three rules prevent accidental functionality loss:

- Every moved block gets one explicit link from the mode that needs it.
- Every deterministic helper has a replay test and a visible failure result.
- Every hook or MCP call has a bounded contract, timeout, and fallback that is
  disclosed rather than silently treated as success.

## Constructive red-team

| Proposal | Attack | Discriminating test | Safe response |
|---|---|---|---|
| Move detail into references | The model may not load the reference, producing a shorter but weaker skill. | Replay representative prompts with the compressed entry and require the same route, receipts, and output sections. | Use mode-local links, a reference-load receipt for load-bearing protocols, and golden replay cases. |
| Put more behavior in deterministic code | Hidden heuristics can hard-code the designer’s framing and make novel requests brittle. | Compare helper decisions against a labeled set containing ambiguous and out-of-distribution prompts. | Code parses, counts, validates, and dispatches; the model retains semantic judgment. |
| Use more MCP servers | Tool schemas and server failures can cost more context and latency than they save. | Measure cold-start tokens, call count, latency, and failure rate with and without the server. | Reuse active MCPs first; add a server only for a demonstrated shared-state or cross-client need. |
| Add hooks for every skipped step | Global hooks can create false positives, duplicate work, or fail open while appearing protective. | Run shadow mode against real sessions and label false positives, timeouts, and operator disablement. | Add only narrow lifecycle checks, initially advisory, with an explicit false-positive budget. |
| Treat lens convergence as truth | Multiple agents can share the same bundle, model family, or framing anchor. | Inject known dissent cases and compare independent evidence, not only vote counts. | Preserve dissent and evidence receipts; convergence is a signal, not proof. |

The last two attacks are especially important for a fleet director. A larger
panel can increase spend and coordination noise while making the result look
more certain. A new hook can increase apparent safety while reducing the
operator’s willingness to keep the enforcement layer enabled. These are
measurable architecture risks, not reasons to avoid automation entirely.

## Receipts

The current Grok `/tp` implementation demonstrates why compression should be
structural rather than subtractive:

- `C:\Users\brsth\.grok\skills\tp\SKILL.md` is 1,697 lines and 106,222 bytes;
  the skill directory contains 39 files. The entry file already separates
  semantic routing and explicit lens parsing (`SKILL.md:130-184`), critique
  history/wiki/preflight (`SKILL.md:909-969`), model-pool dispatch
  (`SKILL.md:1038-1139`), telemetry and wiki-save policy (`SKILL.md:1459-1473`),
  and a falsifier (`SKILL.md:1667-1695`).
- The helper `C:\Users\brsth\.grok\skills\tp\__lib\tp_dispatch.py` has
  separate transcript discovery, provider command builders, and a `main`
  entrypoint (`tp_dispatch.py:128, 480, 489, 621`). This is evidence that
  mechanics already have a natural home outside the prose protocol.
- The focused test run
  `python -m pytest -q C:\Users\brsth\.grok\skills\tp\__lib\tests`
  passed: 38 tests in 4.14 seconds on 2026-08-07. This proves the current
  test suite passed; it does not prove the live routing surface or outcome
  quality.
- `P:\.data\telemetry\tp-critique-log.jsonl` currently contains 17 valid
  records and 0 invalid records: 12 `REVISE` and 5 `PROCEED`. The recorded
  outcomes are inferred labels (`likely-acted-on`, `acted-on`, `proceeded`,
  `likely-ignored`), not a controlled measure of catch rate or decision
  quality.

The local evidence supports refactoring boundaries, but not a claim that a
particular line-count target or three-lens default is optimal.

## What this means for our workspace

For the solo-director fleet, the recommended catalog shape is:

```text
thought-partner / tp
  -> intent router
  -> mode-specific reference/protocol
  -> deterministic manifest and dispatch helper
  -> model judgment and cross-lens synthesis
  -> deterministic receipt/claim validator
  -> existing wiki, telemetry, and lifecycle surfaces
```

Keep `reason`, `genius`, `ultrathink`, and similar labels as aliases, mode
presets, or host adapters unless they have a distinct trigger, evidence
contract, and outcome metric. A new user-facing skill earns its place only
when it has a different domain boundary, not merely a different intensity
adjective.

Use existing MCPs for retrieval and current documentation where they are
already configured. Do not introduce a generic “thinking MCP”: model judgment
belongs to the model, while local parsing and validation belong in code. A
future shared run/evidence MCP is a separate decision and is covered by
[[tp-compression-mcp-hook-boundaries-2026]].

## Falsifier

This finding is wrong or incomplete if a compressed `/tp` package, tested on a
representative replay corpus, materially lowers required-reference loading,
route correctness, evidence-receipt coverage, or high-value catch rate; or if
the supposedly simpler internal module boundary causes more operator confusion
than the current catalog. It is also wrong to keep MCP and hooks at the edges if
an observed cross-host collision cannot be made reliable with filesystem
artifacts and deterministic helpers alone.

## Research receipts

Research followed the requested MMX procedure. The focused query
`site:developers.openai.com/codex/build-skills scripts references SKILL.md under 500 lines`
returned `API error: output new_sensitive (HTTP 200)`, so OpenAI claims use the
alternate overview/build-skills query results below. MMX snippets were treated
as evidence, not as proof of details absent from the snippets.

| Query used | Source title and direct URL | Publication/update date | Relevance | Evidence classification | Uncertainty |
|---|---|---|---|---|---|
| `site:docs.anthropic.com/en/docs/claude-code skills progressive disclosure SKILL.md scripts references` | [Extend Claude with skills - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/skills) | Not exposed by MMX | Says reference files can be linked from the skill and loaded as needed. | Primary | MMX snippet only; full page not independently fetched here. |
| `OpenAI Codex customization overview progressive disclosure skills` | [Customization - ChatGPT Learn](https://developers.openai.com/codex/customization/overview) | Not exposed by MMX | Supports staged customization and progressive disclosure for Codex. | Primary | MMX snippet only. |
| `OpenAI Codex customization overview progressive disclosure skills` | [Build skills - ChatGPT Learn](https://developers.openai.com/codex/build-skills) | Not exposed by MMX | Says Codex starts with metadata, then loads `SKILL.md`, then resources. | Primary | MMX snippet only; the narrower follow-up query errored. |
| `site:modelcontextprotocol.io tools resources prompts server design official` | [Architecture overview - MCP](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture) | 2026-07-28 | Distinguishes MCP tools, resources, and prompts by role. | Primary | MMX snippet only. |
| `site:modelcontextprotocol.io tools resources prompts server design official` | [Prompts - MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts) | 2026-07-28 | Defines prompts as structured messages/instructions. | Primary | MMX snippet only. |
| `site:modelcontextprotocol.io tools resources prompts server design official` | [Resources - MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/resources) | 2026-07-28 | Defines resources as shared context/data. | Primary | MMX snippet only. |
| `site:modelcontextprotocol.io tools resources prompts server design official` | [Tools - MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) | 2026-07-28 | Defines tools as model-invoked actions. | Primary | MMX snippet only. |
| `site:github.com/anthropics skills repository SKILL.md scripts references` | [anthropics/skills](https://github.com/anthropics/skills) | Not exposed by MMX | Describes skills as folders of instructions, scripts, and resources loaded dynamically. | Primary repository | Snippet only; repository state may change. |
| `site:github.com/anthropics skills repository SKILL.md scripts references` | [Claude Code skill development](https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/skill-development/SKILL.md?plain=1) | Not exposed by MMX | Advises keeping essential workflow in `SKILL.md` and moving details to references. | Primary repository | Snippet only. |
| `site:github.com/obra/superpowers skills workflow SKILL.md scripts references` | [obra/superpowers writing-skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md) | Not exposed by MMX | Shows a workflow/reference/helper separation pattern for skills. | Primary repository | Snippet only; any line-count guidance is not treated as a universal law. |
| `site:docs.anthropic.com/en/docs/claude-code hooks command prompt agent validation` | [Hooks reference - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/hooks) | Not exposed by MMX | Documents hook configuration and inspection of hook origin/behavior. | Primary | MMX snippet only. |
| `site:docs.anthropic.com/en/docs/claude-code hooks command prompt agent validation` | [Automate actions with hooks - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/hooks-guide) | Not exposed by MMX | Distinguishes prompt hooks for input-only decisions from agent hooks that verify actual state. | Primary | MMX snippet only; this is Claude Code guidance, not proof of Grok hook parity. |

## Sources

- [[code-orchestrates-model-judges-skill-scale]]
- [[skill-management-in-agentic-systems-research-survey]]
- [[agent-control-plane-enforcement-architectures-2026]]
- External sources and query receipts are listed above; the cited claims are
  limited to what the MMX results exposed.

## Auto-related

- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[skill-catalog]]
- [[codebase-knowledge-graph-mapping]]
- [[claude-code-hooks]]

## Re-evaluation — 2026-08-11

**Verdict:** still relevant + now better cross-linked. The original research action item ("Cross-link shared progressive-disclosure and MCP sources across skill architecture concepts") has been substantially addressed by subsequent work:

- **Cross-link confirmed.** `tp-compression-mcp-hook-boundaries-2026.md` (refines relation in frontmatter) shares the same Anthropic/Codex/MCP source set and the same "compression should be structural, not subtractive" thesis. Both concepts now reference each other. No drift between the two.
- **Related concepts that have landed since 2026-08-07:**
  - `agent-skills-fleet-patterns-solo-director-2026.md` — extends the "one user-facing capability, many internal protocols" thesis to the solo-director fleet topology. Aligned.
  - `best-practices-enforcement-mechanism-grok-build.md` — extends the "config > hook > metric > rule" hierarchy from the Boundary Rules table into a tested Windows architecture. Aligned.
  - `advisory-vs-mandatory-triggers.md` — splits the "lifecycle enforcement" row of the boundary table into mandatory (structural) vs optional (advisory). Refines the boundary rule.
- **No new evidence gap to close.** The "no controlled A/B measurement" gap remains open but is now explicitly bounded by the [tp-compression-mcp-hook-boundaries-2026.md](../tp-compression-mcp-hook-boundaries-2026.md) Next steps section, which prioritizes the bounded preflight audit and shadow-mode pilot as the next concrete actions. No duplication.

**What this means for the workspace:** the concept continues to anchor the "progressive disclosure + deterministic helpers + MCP at shared boundaries + hooks at lifecycle boundaries" thesis. New skill-architecture work should reference this concept for the boundary rule and the red-team attacks, not re-derive them. The MMX source citations remain primary evidence; do not refresh them unless the underlying docs change.
