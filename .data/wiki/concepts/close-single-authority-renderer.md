---
title: "Close reports need a single rendering authority"
created: 2026-07-25
source: session-2026-07-25 (critic-friend review of /close report architecture)
tags: [close, session-close, deterministic-rendering, structured-judgment, enforcement, code-orchestrates-model-judges]
agent: grok
host: grok
verification: multi-source-verified
cognitive_load: 2
summary: >
  A close workflow should have one deterministic rendering authority. Code
  scans evidence, controls transitions, accepts bounded structured judgment,
  renders the canonical report, and validates it before emission. The LLM
  should not compose or append a second narrative. This prevents duplicate,
  contradictory, and selectively summarized close reports.
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: refines
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: refines
  - target: wiki/concepts/langgraph-vs-wrapper-scripts-skill-enforcement
    type: extends
  - target: wiki/concepts/skill-enforcement-layers
    type: complements
---

# Close reports need a single rendering authority

## Decision

`/close` should use one canonical rendering pipeline:

```text
scan evidence
    -> resolve gates and transitions
    -> collect bounded LLM judgments as structured data
    -> render one canonical report
    -> validate the rendered report
    -> emit only the validated report
```

The Python helper is the orchestrator and renderer. The LLM supplies judgment
where context is genuinely required, but does not rewrite the report in prose.

## Why this boundary matters

The scanner and the LLM currently have different responsibilities. That is
healthy until both become authors of the final output. Once the scanner emits a
report and the LLM is also asked to adapt, summarize, or append to it, there
are two authorities. The model can then accidentally produce:

- a second `Final state` narrative;
- duplicated fields such as verification or next action;
- a human-friendly summary that omits inconvenient unresolved work;
- contradictory claims between the scanner output and the appended prose.

This is not primarily a prompt-quality problem. It is an output-ownership
problem. The remedy is to make the final report a function of structured
scanner state plus structured judgment, rather than a free-form model rewrite.

## Division of labor

### Deterministic code owns

- evidence discovery and session scoping;
- gate state and conditional transitions;
- loop bounds and retry limits;
- persistence and receipt checks;
- report section order and field presence;
- rendering of completed, deferred, unresolved, and actionable items;
- final validation and emission eligibility.

### The LLM owns

- classifying session work into completed, partial, deferred, or not-started;
- interpreting claims that cannot be determined from filesystem evidence alone;
- identifying context-dependent verification gaps;
- selecting a next safe action;
- recording explicit dispositions for ambiguous items.

These judgments should be returned in a constrained object or state file with
evidence references. They should not be supplied as a second Markdown report.

## Enforcement levels

1. **Primary enforcement — wrapper/state machine.** A single close entry point
   controls scan, judgment intake, render, validate, and emit. A failed gate or
   invalid judgment prevents a clean final report.
2. **Secondary enforcement — structural validator.** The validator rejects
   missing sections, contradictory fields, duplicate decision fields, and the
   old flat-dump format.
3. **Backstop — Stop hook.** A runtime hook may detect a close response that is
   not canonical or contains an appended narrative and request regeneration.
   The hook is a backstop, not the workflow orchestrator.
4. **Documentation — SKILL.md.** The skill explains the contract and the
   judgment schema, but prose alone is not considered enforcement.

## Completeness principle

“Everything is captured” has two separate meanings:

- **Durable capture:** the full AAR, handoffs, wiki concepts, evidence ledger,
  and unresolved artifacts remain available to future sessions.
- **Report visibility:** the close report surfaces every material completed,
  deferred, unresolved, and actionable item, or explicitly links to the full
  source artifact when it cannot inline the detail.

The renderer must not treat “all `What to do` lines found” as equivalent to
“all insights captured.” Structured AAR categories should be preserved, and a
source artifact with no parseable entries should be reported as “not parsed,”
not “none existed.”

## Human reading model: progressive discovery

The report is not only a data structure; it is a decision aid consumed under
low attention after a long session. The design should support two reading
modes:

1. **Serial reading:** a human starts at the top and understands what happened.
2. **Reverse skim:** a human jumps to the bottom to learn what remains and what
   to do next.

For this reason, the operator-facing order is intentionally different from a
machine schema:

```text
session details
  -> what changed
  -> close checks
  -> verification
  -> persistence boundary
  -> actionable insights
  -> not captured / unresolved
  -> next safe action
  -> final status
```

The final status is last because it is the conclusion of the evidence, not a
headline that can be mistaken for a complete verdict before the reader sees
the exceptions. The unresolved section immediately above it supplies the
context needed to interpret the conclusion.

### Information scent

Every section heading and item should tell the reader whether expanding or
following its source is worth the effort. Counts alone have weak scent. Prefer
short labels that expose the kind of information behind them:

- `2 unresolved continuation items` rather than `Handoffs: 2`;
- `static /check PASS; live runtime unverified` rather than `Verify: PASS`;
- `AAR findings: 3 actionable items` with a source path rather than `AAR found`.

Progressive disclosure is useful only when hidden detail is discoverable. A
source link, item count, preview sentence, or explicit “details available” cue
should accompany any abbreviated section. Do not hide critical unresolved work
behind an unlabeled link or an empty-looking heading.

### What may be progressive, and what may not

Safe to progressively disclose:

- full gate receipts;
- complete commit lists;
- individual source excerpts;
- verbose scanner diagnostics;
- detailed AAR evidence behind an actionable insight.

Not safe to hide:

- blocked work;
- unverified claims;
- persistence risks;
- uncovered continuation candidates;
- required operator decisions;
- the fact that a source exists but was not parsed.

The report may be concise, but it must never make “not shown” look like
“not present.”

### Cognitive load and closure pressure

Long sessions create a predictable temptation to stop once the report looks
organized. The report should therefore reduce decision effort without reducing
evidence:

- use stable section order across runs;
- use one fact in one place;
- keep each action on its own line;
- separate evidence from interpretation;
- use explicit state words (`blocked`, `unverified`, `deferred`, `none`);
- make the next action a single verb-led sentence;
- link to detail instead of repeating it.

This is positive enforcement: the report makes the correct interpretation the
shortest path for the reader. The validator remains necessary because good
layout cannot prevent unsupported content.

### Report UX acceptance tests

A close report should pass these human-factors checks:

1. A reader can identify the final disposition by reading the last two sections.
2. A reader can identify every unresolved item without opening another file.
3. A reader can tell whether a displayed PASS is static, live, or both.
4. A reader can distinguish “none found” from “not scanned” and “not parsed.”
5. A reader can find the source for every actionable insight.
6. A reverse skim does not encounter a reassuring conclusion before the risks.

These are report-level acceptance criteria, not claims that can be guaranteed
by Markdown syntax alone; they should be checked with representative close
fixtures and occasional operator review.

## Visual presentation principles

Visual appeal should come from hierarchy, rhythm, and semantic emphasis rather
than decorative formatting. The report is rendered Markdown, so the durable
visual vocabulary should remain portable across app themes and Markdown
renderers.

### Use a restrained status language

Use a small, stable set of markers alongside explicit words:

```text
✅ complete   🟡 deferred   ⚠️ unverified   ⛔ blocked
🔎 review     💡 insight    ℹ️ information
```

Color or emoji must never be the only carrier of meaning. The text label is
the accessible and portable source of truth; the marker is an attention cue.

### Use visual forms according to data shape

- Use a compact Markdown table for repeated check/result pairs.
- Use one-line bullets for work items, insights, and unresolved risks.
- Use a blockquote for the final status so it is visually distinct without
  becoming a second headline.
- Use bold lead labels for the state or category, not for whole paragraphs.
- Avoid ASCII boxes, decorative separators, and dense comma-packed lines.

Tables should be reserved for genuinely repeated structured data. A table is
not automatically more readable than bullets, especially when cells contain
long prose or paths.

### Make the report feel finished without using closure theatre

The final status can be visually prominent while remaining conservative:

```markdown
## Final status

> **⚠️ SESSION CLOSED — follow-up remains; the unresolved items are listed above.**
```

This provides a clear stopping point without phrases such as “safe to end,”
“all captures shipped,” or other emotional closure language that can outrun
the evidence.

### Visual acceptance tests

In addition to semantic validation, inspect representative reports for:

1. status markers that remain understandable when color is unavailable;
2. tables that do not force long prose or paths into unreadable columns;
3. visible whitespace between sections and individual decisions;
4. unresolved items that stand out more strongly than satisfied checks;
5. a final status that is easy to locate without being mistaken for proof;
6. consistent rendering in the target Markdown surface and plain text.

## Research findings and design implications

### 1. Treat `/close` as a workflow, not an autonomous agent

Anthropic distinguishes workflows, where code orchestrates predefined paths,
from agents, where the model dynamically directs its own process. `/close` has
known gates, a bounded loop, and a defined final artifact, so it belongs in the
workflow category. The model should provide judgment at designated nodes; it
should not choose whether the workflow has reached an emit-eligible state.

This supports a simple wrapper/state machine rather than a general-purpose
agent framework. More machinery is justified only if the workflow becomes
long-running, resumable across processes, or difficult to audit as a hand-rolled
state machine.

### 2. Structured output is an interface, not proof

Schema-constrained output prevents malformed fields and makes the judgment
handoff machine-readable, but it does not prove that a judgment is faithful to
the session evidence. Recent research explicitly separates schema validity
from semantic success and finds that schema-valid outputs can still contain
incorrect or unsafe decisions.

Therefore each judgment field should carry an evidence reference and pass
semantic checks before it affects the report:

```json
{
  "classification": "deferred",
  "item": "live runtime A/B test",
  "reason": "requires a real failure case",
  "evidence": ["handoff:why-skill-enhancement-20260725"]
}
```

The renderer may display only validated records. A syntactically valid but
unsupported judgment should become `needs_review`, not silently enter the
completed or clean-status sections.

### 3. Use layered validation at the handoff boundary

The judgment-to-render boundary needs at least three checks:

1. **Syntax:** the object parses and matches the schema.
2. **Semantic consistency:** classifications, reasons, and evidence agree with
   scanner state and referenced artifacts.
3. **Policy/status:** unresolved gates prevent a clean final status; a claimed
   PASS cannot coexist with an open verification gap; every material item has a
   terminal disposition.

This is stronger than validating the final Markdown alone. Markdown validation
can detect duplicate headings, but it cannot reliably determine whether a
completed item was actually supported by a commit, test, or artifact.

### 4. Preserve provenance through rendering

The canonical report should be reproducible from:

```text
session evidence snapshot
+ scanner result
+ structured judgment receipt
=> rendered report
```

The report does not need to display every internal receipt inline, but every
material statement should be traceable to one. This prevents a future model
from turning a prior model's summary into an apparently independent fact.

### 5. Validate selectively, but fail closed on the final boundary

Verification research warns that validating every intermediate step can add
latency and cost. For `/close`, cheap deterministic checks should run on every
report, while expensive semantic review should be limited to high-risk fields:

- clean or complete status;
- persistence claims;
- verification claims;
- deferred-by-design dispositions;
- claims that all continuation work is covered.

If the final report fails validation, the workflow should return to the
judgment/render step or emit an explicit incomplete state. It should not allow
the LLM to override the validator by adding explanatory prose.

### 6. Measure the boundary, not just the scanner

Useful operational metrics are:

- percentage of `/close` runs with a validated canonical report;
- percentage with a second narrative detected;
- judgment records rejected for missing or contradictory evidence;
- clean-status reports later corrected by the operator;
- average retry count and time spent in the close loop;
- proportion of AAR findings with visible report coverage or a durable source
  link.

## LangGraph relationship

This is the LangGraph pattern without the LangGraph dependency:

- nodes are scanner, judgment intake, renderer, and validator functions;
- state is the evidence ledger plus structured judgments;
- conditional edges are gate-driven loop transitions;
- the final render is reachable only after validation succeeds.

Adopt LangGraph only if the hand-rolled workflow becomes materially harder to
maintain than the dependency and its state-graph conventions. The architectural
principle is more important than the framework choice.

## Falsifiers

Revisit this decision if:

- the host guarantees that the scanner's output is already the sole final
  response and no LLM post-processing occurs;
- structured judgment input makes reports less complete or less readable than
  the current bounded Markdown approach;
- the wrapper's state and transition complexity becomes harder to audit than a
  small, well-tested LangGraph implementation.

## Research sources

- [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — workflows use predefined code paths; agents dynamically direct their own process; simple composable patterns are preferred before adding framework complexity.
- [LangChain, LangGraph](https://www.langchain.com/blog/langgraph) — state, nodes, normal edges, conditional edges, and explicit termination paths.
- [OpenAI, Harness engineering](https://openai.com/index/harness-engineering/) — encode architectural invariants in code, custom linters, and structural tests rather than relying on documentation alone.
- [Yin Li, When JSON Is Not Enough](https://arxiv.org/abs/2607.18261) — schema-valid output can still be semantically wrong; syntax and semantic safety must be evaluated separately.
- [Sherlock: Reliable and Efficient Agentic Workflow Execution](https://arxiv.org/abs/2511.00330) — verification has latency/cost tradeoffs; selective verification and rollback are useful patterns for higher-risk workflow nodes.
- [Microsoft, Progressive Disclosure Controls](https://learn.microsoft.com/en-us/windows/win32/uxguide/ctrl-progressive-disclosure-controls) — simplify the baseline view while keeping additional detail discoverable; hidden content must not appear absent.
- [Microsoft Research, Web page design: memory, structure, and information scent](https://www.microsoft.com/en-us/research/publication/web-page-design-implications-memory-structure-and-scent-information-retrieval/) — information structure and depth/breadth affect retrieval performance; medium structure can outperform both extremes.
- [Baymard, Proper indicators for hidden elements](https://baymard.com/blog/trigger-indicators) — hidden content needs visible cues or users may assume it does not exist.
- [[mental-models-for-handoff-and-aar]] and [[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]] — existing workspace principles for progressive disclosure, cognitive offloading, templates, and validators.
- [Microsoft Fluent 2, Color](https://fluent2.microsoft.design/color) — use color consistently for status but accompany it with text, graphics, or other indicators; preserve contrast and color-blind accessibility.
- [Material Design, Data tables](https://m2.material.io/design/components/data-tables.html) — tables help users scan repeated rows and compare structured values when the information is organized meaningfully.
- [Google Markdown style guide](https://google.github.io/styleguide/docguide/style.html) — consistent headings, spacing, lists, and simple portable Markdown improve maintainability and readability.

## Related

- [[code-orchestrates-model-judges-skill-scale]]
- [[mandatory-step-enforcement-code-over-prose]]
- [[langgraph-vs-wrapper-scripts-skill-enforcement]]
- [[skill-enforcement-layers]]
