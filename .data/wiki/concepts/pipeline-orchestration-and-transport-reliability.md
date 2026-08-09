---
title: "Pipeline orchestration and transport reliability: run-all patterns + schema-validated IPC for mixed deterministic/agentic pipelines"
created: 2026-08-08
source: session-2026-08-08 (/www research, two questions on ship-py design)
sources:
  - P:/.data/wiki/concepts/ship-py-phase-fragmentation-llm-controlled-continuation.md
  - P:/.data/wiki/concepts/llm-text-degeneration-and-output-validation-gates.md
  - P:/.data/wiki/concepts/close-runner-json-arg-parsing-bug.md
  - P:/.data/wiki/concepts/close-authority-state-machine-design.md
  - P:/.data/wiki/concepts/run-all-lifecycle-skills-unconditionally-conditional-detection-is-the-gap.md
  - P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md
  - P:/.data/wiki/concepts/langgraph-tool-args-validation-middleware.md
  - P:/.data/wiki/concepts/ai-agent-schema-standards.md
  - P:/.data/wiki/concepts/check-after-ship-py-verification-sequence.md
  - https://medium.com/@simhadrisriram3/agentic-ai-design-patterns-9e65fb37069f
  - https://www.fundesk.io/deterministic-agentic-workflows-ai-reasoning-guide
  - https://www.mindstudio.ai/blog/structured-ai-coding-workflow-deterministic-agentic-nodes
  - https://java.agentscope.io/en/multi-agent/workflow.html
  - https://www.olostep.com/blog/ai-agent-architecture
  - https://docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/
  - https://www.ertas.ai/compare/pydantic-ai-vs-langgraph
  - https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html
  - https://thinhdanggroup.github.io/airflow-prefect-dagster/
  - https://www.prefect.io/compare/airflow
  - https://medium.com/@MadhavPrajapati/deep-dive-into-passing-data-between-tasks-using-xcom-in-apache-airflow-21d719b71098
  - https://techplanet.today/post/sqlite-is-all-you-need-for-durable-workflows-a-practical-guide-to-lightweight-orchestration
  - https://pl-rants.net/posts/when-not-json/
  - https://www.dolthub.com/blog/2024-11-18-json-sqlite-vs-dolt/
  - https://medium.com/@QuarkAndCode/idempotency-guide-iac-apis-data-pipelines-temporal-workflows-8d85dc280613
  - https://docs.pyworkflow.dev/concepts/fault-tolerance
  - https://developers.googleblog.com/build-long-running-ai-agents-that-pause-resume-and-never-lose-context-with-adk/
  - https://alexop.dev/posts/claude-code-workflows-deterministic-orchestration/
  - https://deepwiki.com/humanlayer/12-factor-agents/3.6-factor-6:-launchpauseresume-with-simple-apis
  - https://blog.sista.ai/2026/03/resumable-agent-workflows-how-to-build.html
  - https://jsonparser.com/json-schema-contract-testing
  - https://zuplo.com/learning-center/how-api-schema-validation-boosts-effective-contract-testing
  - https://lik.ai/guides/data-serialization-formats/
  - https://gist.github.com/MangaD/77dba2f4c7055b35637fb596c175ffb1
  - https://martin.kleppmann.com/2012/12/05/schema-evolution-in-avro-protocol-buffers-thrift.html
  - https://www.digitalapplied.com/blog/data-contracts-for-ai-agent-pipelines
  - https://pydantic.dev/docs/ai/api/pydantic-ai/capabilities/
  - https://agentpatterns.ai/security/improper-output-handling-downstream-sinks/
tags: [pipeline-orchestration, run-all, inter-process-communication, schema-validation, json-schema, pydantic, deterministic-agentic, ship-py, ipc-reliability, workflow-engine, checkpoint-resume]
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
summary: >
  Two coupled questions on ship-py's design: (1) should we add a `run-all`
  subcommand that runs all 13 deterministic phases in one Python process,
  pausing only for LLM-judgment phases? (2) how do we make JSON-file IPC
  between phases reliable when the agent writes wrong schema shapes?
  The workspace already has the relevant building blocks (Rhai workflow
  engine for orchestration, Pydantic-style output gates at lines 189-206,
  close-authority state machine) but they aren't wired together. The
  recommendation is a hybrid: Python `run-all` subcommand with
  `pause_for` declarations on agentic phases (LangGraph interrupt pattern
  ported to a CLI), AND Pydantic v2 strict models at every phase boundary
  (replacing the current `for required_key in ("bugs", "risks", "suggestions"):`
  minimal check). SQLite is appropriate only if state complexity grows
  beyond ~5 phases × ~3 files; for the current shape, well-validated JSON
  files plus durable state.json checkpoints are sufficient.
relations:
  - target: wiki/concepts/ship-py-phase-fragmentation-llm-controlled-continuation.md
    type: extends — proposes the architectural fix (run-all + resume) for the phase-fragmentation gap
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: instance-of — run-all is the code-orchestrates model-judges pattern applied to ship-py
  - target: wiki/concepts/llm-text-degeneration-and-output-validation-gates
    type: extends — the lines-189-206 gate is the kernel; Pydantic v2 is the upgrade
  - target: wiki/concepts/close-authority-state-machine-design
    type: related — INTG-1 (forgeable receipts) and INTG-2 (validator ignores gate content) are the same failure class
  - target: wiki/concepts/run-all-lifecycle-skills-unconditionally-conditional-detection-is-the-gap
    type: extends — "run all unconditionally" was the close-check lesson; ship-py's deterministic phases can run-all unconditionally, agentic phases cannot
  - target: wiki/concepts/grok-build-workflows-rhai-orchestration
    type: related — ship-rhai is the canonical code-orchestrates-model-judges instance; ship-py run-all is the lightweight Python-port of the same idea
  - target: wiki/concepts/langgraph-tool-args-validation-middleware
    type: instance-of — schema-before-execution with self-correction is the LangGraph pattern; ship-py needs the same gate
  - target: wiki/concepts/check-after-ship-py-verification-sequence
    type: related — check-after-ship-py is the independent verification that catches drift; run-all is the orthogonal improvement that catches phase-skip
---

# Pipeline orchestration and transport reliability for ship-py

## Decision context

The /www research task produced two tightly coupled questions about ship-py's
design. They share a root cause — ship-py is **phase-fragmented** (13 separate
CLI subcommands, agent invokes each manually) and **transport-fragile** (each
phase's output is a hand-written JSON file the next phase loads with minimal
schema validation). Fixing one without the other doesn't solve the underlying
problem: a `run-all` orchestrator that doesn't validate phase outputs will
crash or produce wrong verdicts; a schema validator that only fires when the
agent bothers to invoke the next phase is decoration.

This concept synthesizes the workspace's existing knowledge on both problems
with external research, and recommends a single coordinated fix.

---

## Question 1: The "run-all" subcommand pattern

### The problem (verbatim from the operator)

> ship-py is a 13-phase Python-orchestrated pipeline (detect → refactor-scan
> → refactor → skill-dev → auto-fix → check → review → risk → fix → verify →
> doc-check → verdict → merge → publish). Currently each phase is a separate
> command the agent runs manually. The proposed fix: add a `run-all` subcommand
> that runs all deterministic phases in one Python process, pausing only for
> phases that need LLM judgment (review, fix). The agent calls `run-all`,
> spawns subagents for review/fix when instructed, then calls `run-all --resume`
> to continue.

The 13-phase pipeline has the same architectural gap documented in
[[ship-py-phase-fragmentation-llm-controlled-continuation]]: "the LLM
controls continuation between phases — it must choose to invoke each
subsequent subcommand. This makes ship-py 'model orchestrates, code
calculates' rather than 'code orchestrates, model judges.'" The
SKILL.md's aspirational claim ("the LLM can't skip phases because the
script drives each step") is violated at every continuation boundary —
none of them are enforced.

### What the workspace already knows

**Phase-fragmentation is documented and the proposed fix is already on the
fix-path list.** `[[ship-py-phase-fragmentation-llm-controlled-continuation]]`
already enumerates "convert to a true Python loop controller: a single
`ship_orchestrator.py run` command that runs a `while` loop, spawning
subagents via subprocess or SDK calls at each phase" as fix path #3. The
`run-all` proposal is this fix with a `pause_for` declaration making the
agentic-boundary explicit.

**"Run all unconditionally" is a validated design lesson from close-check.**
[[run-all-lifecycle-skills-unconditionally-conditional-detection-is-the-gap]]
documents why close-check Phase 3 runs all 5 lifecycle skills unconditionally:
"conditional detection IS the gap. Every miss in detection produces an
uncaptured finding. The cost of running a skill that wasn't needed (a few
minutes of subagent time) is far lower than the cost of missing a skill
that was needed." **But the lesson only applies when the work is cheap
enough to redo unconditionally.** Close-check's 5 skills are idempotent
scanners. ship-py's 13 phases are not all idempotent (refactor → skill-dev →
auto-fix modify files; verdict is terminal); running all unconditionally
across sessions would re-modify files. The boundary is **the deterministic
phases CAN run-all, the agentic phases CANNOT**.

**The Rhai workflow engine is the canonical code-orchestrates-model-judges
implementation in this workspace.** [[grok-build-workflows-rhai-orchestration]]
documents that ship-rhai "runs as a Rhai workflow. The workflow engine
controls the loop... The LLM does judgment INSIDE each phase. The engine
decides what runs NEXT. The LLM cannot skip a phase because the engine calls
it regardless." The ship-py `run-all` proposal is the Python-port equivalent
of this — same architecture, different language binding.

**The 12-factor agent "launch/pause/resume" pattern (Factor 6) applies
directly.** External research surfaced this exact pattern
([HumanLayer 12-factor agents](https://deepwiki.com/humanlayer/12-factor-agents/3.6-factor-6:-launchpauseresume-with-simple-apis)):
"launch/pause/resume with simple APIs... enables agents to participate in
complex, multi-system workflows while maintaining clear control boundaries
and enabling human oversight at critical decision points." The `run-all` +
`--resume` shape is exactly this primitive.

### External approaches (mixed deterministic + agentic pipelines)

| Framework | Loop controller | Pause point | Resume semantics | Source |
|-----------|----------------|-------------|------------------|--------|
| **LangGraph** | Code (graph nodes + edges) | `interrupt()` inside a node/tool | `Command(resume=...)` passes human decision back | [BSWEN](https://docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/) |
| **Pydantic AI** | Code (agents + dependencies) | None built-in | Must layer on persistence yourself | [Ertas AI](https://www.ertas.ai/compare/pydantic-ai-vs-langgraph) |
| **Google ADK** | Durable state machine | `pause()` / `resume()` | "Persistent checkpoint-and-resume, event-driven idle time handling" | [Google Developers Blog May 2026](https://developers.googleblog.com/build-long-running-ai-agents-that-pause-resume-and-never-lose-context-with-adk/) |
| **Microsoft Conductor** | Deterministic orchestrator | Agent gates | Resume from last committed state | [Microsoft Open Source Blog](https://opensource.microsoft.com/blog/2026/05/14/conductor-deterministic-orchestration-for-multi-agent-ai-workflows/) |
| **AgentScope Java** | Directed graph; "Mix deterministic and agentic steps: Some nodes run without an LLM; others call a model or an agent with tools. Explicit state: Each node reads and updates state" | Per-node type | State propagation through graph | [AgentScope workflow docs](https://java.agentscope.io/en/multi-agent/workflow.html) |
| **Claude Code workflows** | JS script with `agent()` / `parallel()` | Per-agent decision | Journaled; resume reuses committed host calls | [alexop.dev](https://alexop.dev/posts/claude-code-workflows-deterministic-orchestration/) |
| **PyWorkflow** | Python functions | Checkpoint-based | "Workflows continue from the last successful checkpoint, not from the beginning" | [PyWorkflow docs](https://docs.pyworkflow.dev/concepts/fault-tolerance) |

**The "deterministic orchestration" design principle is the consensus
across frameworks.** [Olostep](https://www.olostep.com/blog/ai-agent-architecture):
"Deterministic orchestration forces the model down a predefined track.
Agentic orchestration empowers the model to dynamically evaluate and select
its next tool." [Medium agentic-AI](https://medium.com/@simhadrisriram3/agentic-ai-design-patterns-9e65fb37069f):
"A deterministic workflow follows a fixed, rule-based execution path, even
if it uses an LLM internally. Key characteristics: the entire flow is
predefined, no runtime decision-making, the LLM is embedded inside the
control flow, not controlling it. Steps are executed in a fixed order."

**The pause/resume contract has a precise academic specification.**
[arXiv 2608.03836](https://arxiv.org/html/2608.03836) — "Resume Means Resume":
> "The Resume Contract states six properties over the persistence API —
> prefix continuation, effect exactly-once, fork determinism, checkpoint
> validity, consume-once, recovery determinism — plus a fork-intent
> protocol obligation and a liveness obligation."

This is over-formal for a 13-phase CLI, but the underlying properties are
the falsifiers for any resume implementation: can `run-all --resume`
restart after a crash at any phase and produce the same final state?

### Failure modes of `run-all` vs `run-each`

| Failure mode | `run-each` (current) | `run-all` (proposed) | Mitigation |
|---|---|---|---|
| **Agent skips a phase** | Common; the documented closure-pressure bug ([ship-py-phase-fragmentation-llm-controlled-continuation]) | Blocked by orchestrator; phase must run or exit | The whole point |
| **Phase crashes mid-pipeline** | Operator restarts manually from that phase | `run-all --resume` reloads state.json and continues from last checkpoint | Idempotency requirement on each phase |
| **State diverges between phases** | Each invocation reads state independently; drift possible | Single Python process holds canonical state; state.json is the snapshot | Lock the state.json with a mutex; checkpoint after every phase |
| **Phase requires human/agent judgment** | N/A (agent invokes when ready) | `run-all` halts at `pause_for:` declaration; outputs resume token; agent spawns subagent; invokes `run-all --resume <token>` | The `pause_for` declaration list |
| **Resume from wrong phase** | Impossible (each invocation is one phase) | `run-all --resume <token>` validates phase sequence against declaration order; rejects out-of-order resume | State.json carries the last-completed-phase; reject resume from earlier phase unless `--force` |
| **State file grows unbounded** | Each phase writes its own; cleanup is manual | Orchestrator prunes after `--resume`; long-running sessions accumulate evidence/ | Optional: separate durable evidence from ephemeral state |
| **Cost of running all unconditionally** | Agent invokes only the needed phases | Re-runs all deterministic phases every time, including ones already done | Idempotency on the deterministic phases (the work product is the same); checkpoint-skip on completion |

### Recommendation for Question 1

**Yes — add `run-all` with `pause_for:` declarations. Use the AgentScope
Java design as the template (directed graph of mixed deterministic /
agentic nodes, explicit state at each node).**

Concretely:

```
# ship_orchestrator.py run-all config (pseudocode)
phases = [
    ("detect",         DETERMINISTIC,  no_pause),
    ("refactor-scan",  DETERMINISTIC,  no_pause),
    ("refactor",       DETERMINISTIC,  no_pause),
    ("skill-dev",      DETERMINISTIC,  no_pause),
    ("auto-fix",       DETERMINISTIC,  no_pause),
    ("check",          DETERMINISTIC,  no_pause),
    ("review",         AGENTIC,        pause_for="subagent"),     # LLM judgment
    ("risk",           DETERMINISTIC,  no_pause),
    ("fix",            AGENTIC,        pause_for="subagent"),     # LLM judgment
    ("verify",         DETERMINISTIC,  no_pause),
    ("doc-check",      DETERMINISTIC,  no_pause),
    ("verdict",        DETERMINISTIC,  no_pause),
    ("merge",          DETERMINISTIC,  no_pause),
    ("publish",        DETERMINISTIC,  no_pause),
]
```

```bash
# Agent invocation pattern
python ship_orchestrator.py run-all          # runs deterministic phases
                                              # halts at review with resume_token
python ship_orchestrator.py spawn-review     # agent spawns N review subagents
                                              # writes findings.json
python ship_orchestrator.py run-all --resume # validates findings.json, continues
                                              # halts at fix with new resume_token
python ship_orchestrator.py spawn-fix        # agent spawns fix subagent
python ship_orchestrator.py run-all --resume # completes to verdict
```

**Critical property:** the `pause_for` declaration list is the agent's
script — it cannot invent a new pause point the orchestrator doesn't know
about, and it cannot skip a `pause_for` and proceed past an agentic
boundary without producing a valid `findings.json`. This is the
`[[code-orchestrates-model-judges-skill-scale]]` invariant at the
phase-continuation layer.

**Not the answer:** the pure Rhai engine ([[grok-build-workflows-rhai-orchestration]])
is the canonical workspace pattern but requires either converting ship-py to
Rhai (high transition cost) or running ship-py as a child workflow under
ship-rhai (architectural layer cake). For ship-py's current shape — a
single 13-phase pipeline, not a fan-out workflow — the Python `while`
loop with state.json checkpoint is the lowest-cost implementation that
delivers the invariant.

### Falsifier for Question 1

The `run-all` recommendation is wrong if:

1. **The deterministic phases aren't actually deterministic** — if any of
   `detect`/`refactor-scan`/`refactor`/`auto-fix`/`check`/`risk`/`verify`/
   `doc-check`/`verdict`/`merge`/`publish` make an LLM call, the
   orchestrator will stall without producing resumable state. The 11
   phases marked DETERMINISTIC above are an assertion; verifying it
   requires reading each phase's source.

2. **The agentic boundary is ambiguous** — if "review" or "fix" can
   produce more than one shape of output (e.g., sometimes a
   `findings.json`, sometimes a `verdict.json`), the `--resume` validator
   can't gate cleanly. Mitigated by Question 2's schema enforcement.

3. **The pause interrupts the operator's flow** — if `run-all` halts
   mid-pipeline and the operator has to manually spawn subagents and
   re-invoke, the latency cost may exceed the benefit over the current
   manual phase-by-phase invocation. Measure: median pause-to-resume
   latency should be <60s for the pattern to be net-positive.

4. **Crash recovery breaks idempotency** — if any deterministic phase is
   non-idempotent (re-running produces different state), `--resume` from
   a crashed run will diverge. All 11 deterministic phases must be
   idempotent over the same `state.json` input.

---

## Question 2: Schema-validated inter-process transport

### The problem (verbatim from the operator)

> ship-py phases communicate via JSON files. The agent writes a findings
> JSON (e.g., `{bugs: [...], risks: [...], suggestions: [...]}`), then
> passes `--findings-file <path>` to the next phase. The problem: the
> agent sometimes writes the wrong schema (e.g., `findings` instead of
> `bugs`), causing the phase to fail. This happened twice in one session.

### What the workspace already knows

**ship-py has output validation gates, but they're minimal.**
[[llm-text-degeneration-and-output-validation-gates]] documents the
existing gate at `ship_orchestrator.py` lines 189-206:

```python
# 1. Check file exists
findings_path = Path(args.findings_file)
if not findings_path.exists():
    return error
# 2. Check file is valid JSON
findings = json.loads(findings_path.read_text())
# 3. Check schema (required keys exist)
for required_key in ("bugs", "risks", "suggestions"):
    if required_key not in findings:
        return error
```

**This catches the documented failure mode** (agent writes `findings` instead
of `bugs`) — but **it doesn't catch a half-dozen related ones**: wrong type
inside `bugs` (a string instead of an object list), wrong field names inside
each bug, missing nested fields, etc. The gate is a key-existence check,
not a schema check.

**The same failure class recurs at three places in the workspace.**

| Location | Failure | Reference |
|---|---|---|
| `close_runner.py` | Caller passed full session record (dict) as `session_dir` arg (str); OSError [WinError 123] | [[close-runner-json-arg-parsing-bug]] |
| `close-authority` | AAR receipt is forgeable (no producer attestation); validator ignores gate content on reload | [[close-authority-state-machine-design]] INTG-1, INTG-2 |
| `ship-py` findings | Agent writes `findings` key instead of `bugs`/`risks`/`suggestions` | This concept |

All three are "schema mismatch at a system boundary, silent or
half-silent failure downstream." The pattern recurs because **none of the
boundary checkers assert types** — close_runner doesn't `isinstance(path, (str, Path))`,
close-authority doesn't sign the receipt, ship-py doesn't check that `bugs`
is a `list[dict]`.

**LangGraph's `ToolArgsValidationMiddleware` is the workspace-canonical
schema-before-execution pattern.**
[[langgraph-tool-args-validation-middleware]]:
"Validates tool-call arguments against each tool's JSON schema before the
tool executes... Invalid arguments trigger error ToolMessages that cause
the model to re-invoke and self-correct... Only the final valid AIMessage
enters the agent state." This is exactly the pattern ship-py needs: every
phase boundary validates the input against a Pydantic (or JSON Schema)
contract, and a mismatch produces a clear error that names the missing
key (not an opaque "phase failed").

**The cross-industry principle is "treat agent output as untrusted input
to the next system."** AgentPatterns.ai (cited in
[[llm-text-degeneration-and-output-validation-gates]]): "Treat agent
output as untrusted input to the next system — every downstream sink
needs its own per-sink validation gate." This applies even when the
producer is the same agent — the producer in a future session, or a
sibling session, or a context-degraded state, is not the producer the
contract was negotiated with.

### External approaches

**Pydantic v2 strict models are the de-facto contract in 2026 LLM pipelines.**
[Digital Applied — Data Contracts for AI Agent Pipelines](https://www.digitalapplied.com/blog/data-contracts-for-ai-agent-pipelines):
"Pydantic's docs are precise about what validation guarantees: the output
of instantiating a model conforms to the declared types and constraints."
[Pydantic AI capabilities](https://pydantic.dev/docs/ai/api/pydantic-ai/capabilities/):
"Fires for ValidationError (schema mismatch) and ModelRetry (custom
validator...)." The validator returns a structured error naming the
specific field that failed — exactly the "clear error message" the
current ship-py gate lacks.

**JSON Schema is the broader ecosystem standard.**
[JSONParser](https://jsonparser.com/json-schema-contract-testing):
"Build a JSON Schema from scratch for an API response and use it to catch
missing fields, type mismatches, enum violations, and nested-shape errors
in real contract testing." [Zuplo](https://zuplo.com/learning-center/how-api-schema-validation-boosts-effective-contract-testing):
"Verifying that providers and consumers can successfully communicate
according to agreed-upon rules, contract testing prevents integration
issues." JSON Schema is broader than Pydantic (works across language
boundaries), but Pydantic v2 is more ergonomic for Python pipelines and
generates a JSON Schema as a byproduct.

**Schema-evolution formats (Protobuf, Cap'n Proto, FlatBuffers) solve a
different problem.** [Lik.ai](https://lik.ai/guides/data-serialization-formats/):
"FlatBuffers supports the same schema evolution capabilities as Protocol
Buffers and Cap'n Proto... Cap'n Proto also features..." [MangaD gist](https://gist.github.com/MangaD/77dba2f4c7055b35637fb596c175ffb1):
"Requires pre-compiled schema (.proto), not self-describing (harder for
ad-hoc analysis), not human-readable." The trade-off: binary formats are
fast and have schema evolution, but they are **not self-describing** (you
need the `.proto` to read them) and **not human-readable** (the agent
can't eyeball a `.pb` file). For ship-py — where the agent is the writer
and the Python is the reader, and the JSON is small (a few KB of
findings) — Protobuf's performance and evolution wins don't apply.
**The JSON + Pydantic shape is the right fit.**

**SQLite for pipeline state is appropriate, but for a different reason
than schema validation.** [SQLite is All You Need for Durable Workflows](https://techplanet.today/post/sqlite-is-all-you-need-for-durable-workflows-a-practical-guide-to-lightweight-orchestration)
(May 2026): "SQLite provides ACID guarantees and durable state management
without requiring a separate database service. There's no network hop, no
extra control plane, and no new operational surface area." [PL Rants](https://pl-rants.net/posts/when-not-json/):
"I discarded the option back on day 2 or 3 because parsing the largest
configuration file took 1.4s, which was significantly slower than the
SQLite's 300ms." [DoltHub](https://www.dolthub.com/blog/2024-11-18-json-sqlite-vs-dolt/):
"SQLite is more lightweight than running your DB engine in a separate
process. SQLite doesn't require inter-process communication or server
management." **The performance gap (5× slower for JSON parsing) only
matters at scale** — for ship-py's current load (5-10 small JSON files,
sub-millisecond parse), JSON is fine. SQLite becomes the right answer if:
- File count grows past ~50
- Cross-phase queries become necessary (e.g., "show all bugs across all
  findings from session X")
- Concurrent writers become a problem (multiple subagents writing at once)

**Workflow-engine data-passing patterns are the production reference.**

| Engine | Transport | Small-data limit | Source |
|--------|-----------|------------------|--------|
| **Airflow XCom** | "Serialize values to the metadata database" | "XComs are for small data" (no exact limit) | [Airflow TaskFlow docs](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html), [Madhav Prajapati](https://medium.com/@MadhavPrajapati/deep-dive-into-passing-data-between-tasks-using-xcom-in-apache-airflow-21d719b71098) |
| **Prefect** | "Return Python objects between tasks in-process; for distributed patterns, rely on storage libs or task runners like Dask" | None for in-process | [Prefect vs Airflow](https://www.prefect.io/compare/airflow) |
| **Dagster** | "Data passing between tasks uses XCom, a side channel that serializes values to the metadata database" | Same as Airflow | [CodeWords](https://www.codewords.ai/blog/dagster-vs-airflow) |
| **Airflow TaskFlow API** | "Function's return value passed to next task — no manual use of XComs required" | Auto-abstracted | [Airflow TaskFlow](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html) |

**The production-engine consensus:** **validate at the boundary, store
in-process state when you can, fall back to a metadata DB for
distributed runs, and accept the serialization overhead as the
price of decoupling.**

### Recommendation for Question 2

**Three-layer fix, in priority order:**

**Layer 1 — Pydantic v2 strict models at every phase boundary** (highest
impact, lowest cost):

```python
# ship_orchestrator.py schema definitions
from pydantic import BaseModel, Field
from typing import Literal

class Finding(BaseModel):
    severity: Literal["critical", "high", "medium", "low"]
    location: str
    description: str
    suggested_fix: str | None = None

class FindingsFile(BaseModel, extra="forbid"):
    bugs: list[Finding]
    risks: list[Finding]
    suggestions: list[Finding]

# In each cmd_<phase>():
try:
    parsed = FindingsFile.model_validate_json(findings_path.read_text())
except ValidationError as e:
    return Error(
        phase="review",
        error="schema_mismatch",
        details=e.errors(include_url=False),  # list of {loc, msg, type}
        path=str(findings_path),
    )
```

`extra="forbid"` is the property that catches the documented failure:
"agent writes `findings` key instead of `bugs`" — it produces a clear
`extra_forbidden` error naming the offending field, not an opaque
"required key missing." The `e.errors()` output lists every mismatch
in one pass, so the agent gets all the schema feedback at once.

**Layer 2 — Reusable Pydantic models at the writer side too.** The agent
that writes `findings.json` should be writing from the same Pydantic
model the next phase validates against — `.model_dump_json()` produces
output guaranteed to validate. Single source of truth in
`ship_orchestrator.py` (or a new `ship_schemas.py`) prevents drift
between writer and reader.

**Layer 3 — State checkpointing, kept simple.** For the current pipeline
shape, `state.json` as a single JSON file with `last_completed_phase`
plus a per-phase `findings.json` is sufficient. SQLite only becomes
necessary if cross-phase queries become common or if concurrent
subagents write to the same evidence pool (not currently the case —
subagents write to their own `findings-<agent-id>.json`, which the
orchestrator merges).

**NOT recommended:** Protobuf/Cap'n Proto/FlatBuffers. The schema
evolution wins apply to long-lived wire protocols with N producers
and M consumers over years. ship-py has 1 producer (the agent) and
~13 consumers (the phases), all in the same Python process, and the
schemas will evolve with the agent. JSON + Pydantic is the right
tooling for this shape.

**NOT recommended:** "Self-healing from minor schema mismatches" (the
operator's last sub-question). The drift cost — agent silently writes
wrong key, the validator silently coerces, the phase silently processes
garbage, the operator sees a green pipeline that produced wrong output —
is worse than the friction cost of failing loudly. The LangGraph pattern
is **schema-mismatch → structured error → agent self-corrects on retry**,
not **schema-mismatch → silent coercion**. Self-healing is for
known-recoverable errors (network retries, transient DB failures);
schema mismatches are unknown-recoverable by definition (you don't know
what the agent intended).

### Falsifier for Question 2

The Pydantic-strict recommendation is wrong if:

1. **The schema check is over-constrained** — if the agent legitimately
   needs to evolve the schema mid-session (e.g., adding a new required
   field during a phase), strict mode rejects the new shape. Mitigation:
   `extra="ignore"` on stable fields, `extra="forbid"` only on the
   exact documented failure cases (`bugs`/`risks`/`suggestions` keys).
   The Pydantic `model_validator` decorator can implement complex
   "allow if phase is X" rules.

2. **The error feedback is too noisy** — if `e.errors()` returns 20
   mismatches for one malformed file and the agent can't prioritize
   which to fix, the gate becomes unhelpful noise. Mitigation: surface
   only the first mismatch; the agent fixes and re-runs, gets the next.

3. **SQLite is needed earlier than the recommendation claims** — if the
   evidence pool grows past ~50 files (many concurrent review subagents,
   long-running session), JSON file proliferation becomes the actual
   problem. Re-evaluate when the file count per session exceeds ~50.

4. **The agent invents a new schema that's correct and useful** — if a
   Pydantic-strict validator rejects a schema the agent invented for a
   genuinely new finding type (e.g., "compliance checks"), the validator
   blocks legitimate work. Mitigation: Pydantic models should be
   co-evolved with the agent prompt; a stale Pydantic model is the same
   failure class as a stale contract.

---

## Coupled fix: how run-all + Pydantic-strict work together

The two recommendations compose into a single architectural shift:

| Layer | Before | After |
|---|---|---|
| **Loop controller** | LLM invokes each phase manually | Python `run-all` runs deterministic phases; pauses at `pause_for:` declarations |
| **State** | One JSON per phase, no checkpoint | Single `state.json` with `last_completed_phase`; per-phase findings files |
| **Schema validation** | Key-existence check (3 required keys) | Pydantic v2 strict models with `extra="forbid"`, clear field-named errors |
| **Resume** | Manual restart from the failed phase | `run-all --resume <token>` validates state and continues from next phase |
| **Cross-phase queries** | Grep over many JSON files | Possible only after SQLite adoption; not in scope for v1 |

**The minimum-viable implementation:**

1. Add `cmd_run_all()` and `cmd_run_all_resume()` to `ship_orchestrator.py`.
2. Add `pause_for:` declarations per phase (deterministic / agentic).
3. Replace lines 189-206 schema check with Pydantic `FindingsFile.model_validate_json()`.
4. Add `state.json` write after each phase, with `last_completed_phase`.
5. Test: `run-all` from Phase 0, pause at review, write findings, `run-all --resume`, pause at fix, write fix output, `run-all --resume`, complete to verdict.

**What this DOESN'T do:** it doesn't add the close-authority-style
producer attestation (HMAC-signed receipts) — that is INTG-1's fix
path, not a run-all requirement. The trust model is "the orchestrator
trusts the file because the file was loaded from the prior phase's
output and the schema validated" — sufficient for a single-agent
ship-py session, not sufficient for cross-agent / cross-session
trust. That stronger model is a separate concept.

---

## What this means for our workspace

- **ship-py** should ship the `run-all` + Pydantic-strict fix together
  (single PR, since they're coupled). Fix path #1 (inter-phase gate in
  each cmd) and fix path #3 (Python loop controller) from
  [[ship-py-phase-fragmentation-llm-controlled-continuation]] collapse
  into the same implementation.

- **close-authority** (the [[close-authority-state-machine-design]]
  follow-up) should adopt Pydantic-strict for its receipt schema as a
  structural defense against INTG-2 (validator ignores gate content on
  reload) and as a stepping stone toward INTG-1 (forgeable AAR
  receipts). The validator becomes a Pydantic model; `extra="forbid"`
  prevents the documented bypass.

- **close-runner** should add `isinstance(session_dir, (str, Path))` and
  path-syntax validation at the boundary per
  [[close-runner-json-arg-parsing-bug]].

- **skill architecture generally** should adopt the
  "Pydantic model as the contract" pattern. Every skill that takes a
  file path argument should validate at the boundary; every skill that
  reads a JSON input should use `model_validate_json()` with explicit
  strict flags.

## Receipts

**Wiki-grounded (verified by `read_file` this session):**
- `P:/.data/wiki/concepts/ship-py-phase-fragmentation-llm-controlled-continuation.md`
- `P:/.data/wiki/concepts/llm-text-degeneration-and-output-validation-gates.md`
- `P:/.data/wiki/concepts/close-runner-json-arg-parsing-bug.md`
- `P:/.data/wiki/concepts/close-authority-state-machine-design.md`
- `P:/.data/wiki/concepts/run-all-lifecycle-skills-unconditionally-conditional-detection-is-the-gap.md`
- `P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md`
- `P:/.data/wiki/concepts/langgraph-tool-args-validation-middleware.md`
- `P:/.data/wiki/concepts/ai-agent-schema-standards.md`
- `P:/.data/wiki/concepts/check-after-ship-py-verification-sequence.md`

**Web-verified (DDG search, top-5 ranked hits, all accessed 2026-08-08):**
- AgentScope Java workflow (mixed deterministic/agentic, explicit state)
- LangGraph human-in-the-loop (`interrupt()` + `Command(resume=...)`)
- Pydantic AI vs LangGraph comparison (LangGraph has checkpoint; Pydantic AI does not)
- Airflow TaskFlow API (XCom abstracted as function return value)
- Prefect vs Airflow (Python objects in-process, storage libs distributed)
- SQLite is All You Need for Durable Workflows (May 2026)
- Cap'n Proto / FlatBuffers / Protobuf comparison (schema evolution, NOT self-describing)
- JSON Schema contract testing (JSONParser, Zuplo)
- 12-factor agents Factor 6 (launch/pause/resume)
- arXiv 2608.03836 Resume Means Resume (six-property contract)

**Not verified this session (assertions to verify before shipping):**
- The exact line-number citations in `ship_orchestrator.py` (lines 189-206
  for the gate; lines 64, 150, 161, 171, 293, 393 for subcommands) come
  from [[ship-py-phase-fragmentation-llm-controlled-continuation]] and
  were not re-verified this session.
- The 13-phase list (detect → refactor-scan → refactor → skill-dev →
  auto-fix → check → review → risk → fix → verify → doc-check → verdict
  → merge → publish) is from the operator's prompt, not from re-reading
  ship-py source. The phases marked DETERMINISTIC vs AGENTIC in the
  recommendation are an inference based on naming; verifying requires
  reading each phase's source.

## Falsifier (concept-level)

This synthesis is wrong if:

1. **The "deterministic vs agentic" boundary is wrong** — if any
   phase marked DETERMINISTIC actually requires LLM judgment, the
   `run-all` orchestrator stalls. Verify by reading each phase.

2. **Pydantic strict breaks legitimate schema evolution** — if the
   agent legitimately evolves the findings schema mid-session, strict
   mode is a blocker. Re-evaluate after one full ship-py run with
   the new orchestrator.

3. **The pause-to-resume latency is too high** — if median operator
   pause at `pause_for:` declarations is >60s, the orchestrator
   adds friction without benefit. Measure before declaring the
   pattern net-positive.

4. **The schema mismatch wasn't the actual bottleneck** — if ship-py
   is failing for reasons unrelated to schema validation (e.g.,
   review agents producing empty findings, fix agents producing
   no-op diffs), adding Pydantic strict surfaces the same
   underlying problem in a louder voice without addressing it.
   Run a 30-day instrumented sample before declaring the fix
   complete.