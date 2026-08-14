# 2026-08-10 - Research Evaluation and Feedback

- **Created:** 8/13/2026, 7:44:35 AM
- **Exported:** 8/13/2026, 7:44:37 AM
- **Messages:** 2
- **Source:** browser_extension

---

## #1 · user

File

Do you agree with this research, and solution concept / ideas?  What would you propose changing?

## #2 · assistant

# Verdict

**I agree with the central direction, but I would not implement the proposed architecture as written.**

The document is a strong design exploration. Its best insight is that **categories should be attached to discoveries after discovery—not used as the boundary of what the model is allowed to notice**. Its weaker sections turn that insight too quickly into multiple agents, self-reported “bias metrics,” a TODO subsystem, an MCP server, and a framework adoption decision without proving that each added mechanism earns its complexity.

## What the research gets right

### 1. Discover first, classify second

Your concern about category-induced tunnel vision is valid. The proposed sequence—freeform discovery, later classification, multi-label assignment, an `other` escape hatch, and a final omission pass—is substantially better than asking an LLM to “find blockers, errors, inefficiencies, and opportunities.” 

I would preserve this principle exactly:

> 
**Taxonomy is metadata, not a search boundary.**

A useful refinement is to conduct:

1. 
an open discovery pass with no named categories;

2. 
a separate coverage sweep using broad lenses;

3. 
classification only after the candidate set is assembled.

This reduces anchoring without pretending that one unstructured pass will achieve complete coverage.

### 2. Evidence anchoring and explicit uncertainty

Requiring source references, separating direct evidence from inference, and routing insufficiently supported claims for further investigation are all correct. The document also correctly distinguishes raw findings from tasks.  

The important distinction should be:

- 
**Observation:** something noticed.

- 
**Finding:** an observation that has survived validation.

- 
**Task:** an accepted commitment to act.

Without those boundaries, every plausible observation becomes backlog pollution.

### 3. External state plus progressive retrieval

The document is right that thousands of tasks should not live in one in-prompt JSON object. Keeping rich evidence outside the working context and retrieving only the current working set is the correct architecture. Your handoff files already accomplish much of this. 

The handoff-file model was not a failed workaround. It was an early form of:

- 
progressive disclosure;

- 
evidence-oriented storage;

- 
sparse retrieval;

- 
human-inspectable long-term state.

It needs a better index and lifecycle model, not wholesale replacement.

# What I would change

## 1. Downgrade the claimed strength of the “research”

The references mix papers and formal sources with blogs, LinkedIn posts, directories, marketing pages, and small repositories. That can generate useful leads, but it does not establish that the proposed pipeline is optimal or that its metrics are validated.  

I would relabel the evidence:

- 
**Supported principle:** structured decomposition, evidence anchoring, external state, independent checking.

- 
**Plausible design hypothesis:** discover-first is better than category-first for your work.

- 
**Unvalidated proposal:** the exact number of agents, prompts, scores, schemas, and MCP boundaries.

- 
**Needs live evaluation:** whether it improves recall, precision, workload, and task completion in your real sessions.

## 2. Replace “automated bias checking” with narrower language

The proposed measures—speculation rate, contradiction count, perspective balance, checklist completion—are **telemetry about the model’s output**, not proof that bias was reduced. 

Likewise, a model claiming:

```
"traceable_claims": true
```

does not prove traceability. It proves that the model produced `true`.

Research on self-correction is mixed and task-dependent. Models can be less critical of their own earlier output than of identical material presented as external work; fresh-context review can outperform continued same-session review, while repeated review can introduce additional false positives. [[image]arXiv+3[image]arXiv+3[image]arXiv+3](https://arxiv.org/html/2606.23196v1)

Use three different controls:

1. 
**Deterministic validation:** schema, source-reference existence, hashes, duplicates, stale state.

2. 
**Independent review:** fresh context and preferably a different model lane for consequential findings.

3. 
**Measured evaluation:** comparison against human-reviewed real examples.

Do not loop until the reviewer reports “zero issues.” That creates review theatre and can cause churn.

## 3. Do not use `impact × confidence`

The document suggests impact multiplied by confidence, with blockers promoted first.  That produces the wrong behavior:

- 
A potentially catastrophic issue with weak evidence gets artificially demoted.

- 
A trivial but obvious issue can outrank a major uncertain risk.

- 
A “blocker” may be irrelevant to the user’s current goal.

- 
Model confidence is not consistently calibrated across tasks and models. [[image]arXiv](https://arxiv.org/abs/2607.20526?utm_source=chatgpt.com)

Use **routing rules**, not one blended number:

| Condition | Disposition |
| --- | --- |
| High impact, strong evidence | Propose urgent action |
| High impact, weak evidence | Investigate immediately |
| Low impact, strong evidence, low effort | Batch or quick-fix |
| Low impact, high effort | Defer |
| Stale, superseded, or duplicate | Archive |
| No actionable outcome | Retain as knowledge, not task |

Priority should consider impact, urgency, critical-path effect, evidence strength, effort, reversibility, and value—but those dimensions should remain visible rather than disappearing into one score.

## 4. Change the taxonomy

The categories currently mix fundamentally different concepts:

- 
**Blocker** is usually a relationship or state.

- 
**Error** is a finding type.

- 
**Risk** is uncertainty about a future outcome.

- 
**Inefficiency** is an impact or condition.

- 
**Improvement** is an intervention.

- 
**Opportunity** is a potential value proposition.

I recommend orthogonal fields:

```
kind:
  defect | constraint | risk | debt | opportunity | unknown

impact_dimension:
  correctness | reliability | security | usability |
  performance | cost | maintainability | workflow

cause_dimension:
  code | data | process | tool | dependency | environment | unknown

disposition:
  investigate | fix | decide | monitor | document | ignore

relations:
  blocks | depends_on | duplicates | supersedes | caused_by
```

A finding may have several impact dimensions, but only one lifecycle state and a clearly defined disposition.

## 5. Do not create three separately deployed agents yet

The document recommends separate TODO and triage skills and optionally a finder skill. 

The **logical stages should be separate**, but that does not require separate agents or skills initially.

For your environment, I would begin with one `/triage` capability containing explicit stage contracts:

1. 
discover;

2. 
validate;

3. 
consolidate;

4. 
propose actions;

5. 
present;

6. 
promote accepted actions;

7. 
update outcomes.

Different models can execute selected stages when useful. That gives you clean eval boundaries without adding routing, prompt duplication, tool exposure, and cross-agent state transfer prematurely.

Your existing scratchpad/TODO capability can remain the presenter. There is no need to build a competing TODO product merely to display triage results.

## 6. Treat MCP as an optional adapter—not the core solution

The document eventually acknowledges this, but earlier wording credits MCP with benefits that actually come from:

- 
external storage;

- 
selective retrieval;

- 
transactions;

- 
schema validation;

- 
a shared service;

- 
tool contracts.

MCP standardizes access to those capabilities. It does not itself provide them.

MCP tool descriptions and returned results can still occupy context. Some clients now defer detailed tool definitions until a tool is selected, which reduces—not eliminates—the context cost. [[image]Claude Platform Docs](https://docs.anthropic.com/en/docs/claude-code/mcp)

There is also an important deployment distinction:

- 
Local **stdio** MCP servers are generally launched for and connected to one client.

- 
A truly shared server used by multiple independent harnesses is better exposed through **Streamable HTTP** or another explicit service API. [[image]Model Context Protocol](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture)

Therefore, do not assume “one infrastructure terminal running an MCP server” will be shared correctly until the actual clients and transport are live-verified.

MCP should be added when at least one of these becomes true:

- 
Claude Code, Codex, desktop clients, and scripts must share the same state;

- 
direct file mutation has caused real concurrent-write failures;

- 
a stable cross-client tool contract has demonstrated value.

# Architecture I would implement

## End-to-end lifecycle

| Stage | Producer | Durable output | Authority | Failure direction |
| --- | --- | --- | --- | --- |
| Source capture | Session/harness | Run-scoped transcript, logs, commit and file references | Original source | Missing source blocks promotion |
| Open discovery | LLM | Candidate observations | None; advisory | Preserve but do not action |
| Coverage sweep | Fresh-context reviewer | Additional observations and omissions | None; advisory | Merge without deleting first-pass items |
| Validation | Deterministic code plus selective reviewer | Evidence-backed findings | Source references and validators | Unsupported items remain candidates |
| Action synthesis | LLM | Proposed action with prerequisites and verification | Still advisory | No automatic durable task |
| Promotion | User or explicit policy | Accepted task | User/policy authority | Reject, defer, or investigate |
| Execution | /go or specialist workflow | Change plus execution evidence | Runtime and tests | No completion claim without proof |
| Closure | Deterministic updater | Outcome, resolution, supersession links | Verified execution evidence | Reopen or mark unresolved |

## Storage model

### Immutable evidence artifacts

Keep Markdown or JSONL artifacts organized by project and run:

```
artifacts/
  triage/
    <project>/
      <run_id>/
        source-manifest.json
        observations.jsonl
        findings.jsonl
        review.md
```

These remain grep/ripgrep/QMD-friendly and provide inspectable evidence.

### SQLite lifecycle index

Use SQLite only for mutable index and workflow state:

- 
IDs and summaries;

- 
current status;

- 
labels and relations;

- 
source pointers and hashes;

- 
priority dimensions;

- 
assigned owner;

- 
accepted/rejected/deferred state;

- 
optimistic version number;

- 
idempotency key.

SQLite WAL mode supports simultaneous readers with serialized writes, but the application still needs proper transactions, timeouts, and conflict handling. [[image]SQLite](https://www.sqlite.org/wal.html)

**Avoid two mutable sources of truth:**

- 
Files own immutable evidence.

- 
Database owns mutable lifecycle state.

- 
Tasks point to evidence rather than copying all context.

### Retrieval path

Use progressive disclosure:

1. 
return IDs, titles, statuses, and one-line rationales;

2. 
fetch one finding’s structured metadata;

3. 
fetch its evidence artifact;

4. 
fetch original transcript/log/code only when necessary.

That preserves your successful handoff model while making state queryable.

# Minimum viable implementation

I would not begin with a dashboard, five production prompts, three agents, and an MCP server.

### Phase 1 — Prove the analysis contract

Build one pipeline over historical sessions:

```
source manifest
→ open discovery
→ evidence validation
→ deduplication
→ proposed actions
→ user review
```

Use one schema and local files. No MCP and no automatic task creation.

### Phase 2 — Prove persistence and multi-terminal safety

Add SQLite with:

- 
transactional writes;

- 
unique idempotency keys;

- 
source hashes;

- 
optimistic update versions;

- 
duplicate/supersession relationships;

- 
stale-reference detection.

Run real concurrent-client tests.

### Phase 3 — Add the shared interface only when justified

Expose the proven storage API through MCP when more than one harness genuinely needs it. Keep business rules in a framework-neutral service so MCP can be replaced without rewriting triage.

I would not adopt ACF merely because the document calls it “production-grade”; that description originates from the project itself, and repository popularity or self-description is not operational evidence. `mcp-agent` is more established, but even that should be adopted only if its durable workflow machinery replaces code you demonstrably need. [[GitHub]

GitHub+1](https://github.com/FutureAtoms/agentic-control-framework)

# Acceptance evidence

Synthetic fixtures are useful for schema and parser tests, but they cannot establish real discovery quality. The document currently leans too heavily on seeded examples and output invariants. 

Use a redacted corpus of real previous sessions and handoffs, human-reviewed for important findings.

Measure:

- 
supported-finding precision;

- 
recall of known consequential findings;

- 
valid evidence-reference rate;

- 
duplicate rate;

- 
accepted-task yield;

- 
stale-task rate;

- 
user review time;

- 
critical misses;

- 
concurrent lost-update count.

Hard release gates should include:

- 
**100%** of promoted tasks have resolvable evidence, an actionable outcome, prerequisites, definition of done, and verification method.

- 
**Zero** unsupported findings are automatically promoted as urgent tasks.

- 
A modified source hash marks the finding stale and blocks automatic action.

- 
Two terminals attempting conflicting updates produce a detected conflict, not silent last-write-wins.

- 
A resolved finding is not recreated on the next run unless new evidence materially changes it.

- 
Completion requires runtime evidence from the real execution path—not only a task status change.

## Bottom line

Keep the **discover-first principle**, evidence anchoring, progressive retrieval, and external durable state.

Change the proposed solution from:

> 
finder agent → triage agent → TODO agent → MCP task manager

to:

> 
**one evaluable triage lifecycle with explicit contracts → immutable evidence artifacts → validated finding index → user-authorized task promotion → verified execution**

Then add independent models, MCP, richer orchestration, or dashboards only when a measured failure demonstrates that the simpler system is insufficient.
