---
title: "Five SDLC workflow improvements from session 019fdf3d — wiki-web-wiki synthesis"
created: 2026-08-08
source: session-019fdf3d
sources:
  - internal: P:/.data/wiki/concepts/parallel-subagent-wait-all-gate.md (existing — wait-all rule)
  - internal: P:/.data/wiki/concepts/intent-classification-before-routing-2026.md (existing — routing-side)
  - internal: P:/.data/wiki/concepts/intent-based-routing-for-ai-agent-skills-2026.md (existing — routing-side cascade)
  - internal: P:/.data/wiki/concepts/adaptive-orchestration-task-shape-classification.md (existing — adaptive routing)
  - internal: P:/.data/wiki/concepts/cli-api-drift-in-skill-scripts.md (existing — CLI drift precedent)
  - internal: P:/.data/wiki/concepts/producer-consumer-contract-drift-in-skill-chains.md (existing — field-name drift)
  - internal: P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md (existing — code-orchestration)
  - internal: P:/.data/wiki/concepts/skill-rewrite-preserve-tested-behavior-protocol.md (existing — refactor safety)
  - external: https://hoop.dev/blog/iac-drift-detection-in-github-ci-cd-keep-your-infrastructure-in-sync/ (Hoop, 2025 — continuous IaC drift detection in CI)
  - external: https://www.firefly.ai/academy/implementing-continuous-drift-detection-in-ci-cd-pipelines-with-github-actions-workflow (Firefly — drift detection in GitHub Actions)
  - external: https://spacelift.io/blog/drift-detection (Spacelift — drift detection tooling taxonomy)
  - external: https://arxiv.org/html/2406.19508v1 (arXiv 2406.19508 — Code Linting using Language Models, Jun 2024)
  - external: https://openreview.net/pdf?id=9LdJDU7E91 (IRIS — neuro-symbolic LLM + static analysis)
  - external: https://arxiv.org/html/2502.10815v1 (LintLLM — domain-specific LLM linter framework)
  - external: https://docs.agentbase.sh/primitives/essentials/background (Agentbase — Background Tasks lifecycle primitives)
  - external: https://deepwiki.com/code-yeongyu/oh-my-opencode/6.1-background-manager-architecture (oh-my-opencode Background Manager Architecture — complete BackgroundTask interface)
  - external: https://www.thenodebook.com/labs/async-task-runtime-local-job-orchestrator (NodeBook — validated task definitions, lifecycle manager)
  - external: https://github.com/whiteducksoftware/flock/blob/main/docs/patterns/async_patterns.md (Flock — Task Lifecycle Management pattern, "always clean up fire-and-forget tasks on shutdown")
  - external: https://www.gravitee.io/blog/contract-testing-microservices-strategy (Gravitee — Contract Testing for microservices)
  - external: https://gabogil.com/2026/02/22/consumer-driven-contract-testing-a-pragmatic-shift-in-integration-strategy/ (Gabo Gil, Feb 2026 — Consumer-Driven Contract Testing governance)
  - external: https://www.augmentcode.com/learn/how-to-refactor-legacy-code (Augment Code — "identify likely downstream consumers to reduce the risk of abstraction boundaries that miss critical callers")
  - external: https://www.jetbrains.com/help/pycharm/rename-refactorings.html (JetBrains — IDE rename refactorings with cross-file reference update)
  - external: https://learn.microsoft.com/en-us/visualstudio/ide/reference/refactoring-rename-move?view=visualstudio (VS — rename and move refactorings)
  - external: https://docs.aws.amazon.com/cdk/v2/guide/refactor.html (AWS CDK — "Refactor" feature for preserving deployed resources)
  - external: https://nhimg.org/glossary/automation-credential-drift/ (Automation credential drift definition + credential debris pattern)
  - external: https://www.linkedin.com/pulse/credential-debris-configuration-drift-twin-threats-enterprise-gulia-2d30f/ (Credential Debris vs Configuration Drift — twin threats)
  - external: https://unit42.paloaltonetworks.com/comparing-llm-guardrails-across-genai-platforms/ (Unit 42 — LLM guardrails false-positive comparison)
tags: [sdlc, workflow-improvements, drift-detection, intent-classification, task-lifecycle, refactor-verification, session-019fdf3d, transferable]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  Wiki-web-wiki synthesis of five SDLC improvements built or surfaced in session
  019fdf3d: (1) refactoring consumer-update phase for file-structure splits/moves,
  (2) credential/status drift detection wired into maintenance loops,
  (3) semantic intent classification for enforcement gates (Stop hooks, not routing),
  (4) dispatch-without-wait lifecycle enforcement for background subagents,
  (5) post-refactor integration testing of the full consumer pipeline.
  Each improvement is classified [CONFIRMED]/[EXTENDED]/[NOVEL] against existing
  wiki concepts and external best practices; each produces 1-2 concrete
  workspace enhancements not previously considered.
relations:
  - target: wiki/concepts/parallel-subagent-wait-all-gate
    type: extends — improvement 4 strengthens with BackgroundManager lifecycle pattern
  - target: wiki/concepts/intent-classification-before-routing-2026
    type: extends — improvement 3 applies the same technique to Stop hooks, not routing
  - target: wiki/concepts/cli-api-drift-in-skill-scripts
    type: extends — improvement 2 broadens to credentials + status, not just CLI APIs
  - target: wiki/concepts/producer-consumer-contract-drift-in-skill-chains
    type: extends — improvement 1 adds the file-path layer that concept covers at field-name layer
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: refines — improvement 5 is a micro-scale instantiation for refactor verification
  - target: wiki/concepts/check-and-fix-skills-verification-skills-should-fix-what-they-can
    type: complements — improvement 5 shares the "auto-fix what is deterministic" principle
---

# Five SDLC workflow improvements from session 019fdf3d

## Decision context

Session 019fdf3d surfaced five recurring SDLC pain points and built fixes
for three of them. The session asked: validate each against external best
practice, and find techniques we are missing. This concept captures the
synthesis. Each improvement is labelled `[CONFIRMED]` (external practice
matches what we built), `[EXTENDED]` (existing wiki + external practice
extend what we built), or `[NOVEL]` (no significant prior art in either
wiki or external research — the workspace is in new territory).

The five improvements cluster naturally:

| # | Improvement | Existing wiki | External pattern | Label |
|---|-------------|---------------|------------------|-------|
| 1 | Refactoring consumer-update phase | Field-name drift only ([[producer-consumer-contract-drift-in-skill-chains]]) | IDE rename (JetBrains/VS), CDK Refactor (AWS), Augment Code "identify downstream consumers" | **NOVEL** at the file-path layer |
| 2 | Credential/status drift detection | CLI drift ([[cli-api-drift-in-skill-scripts]]) | IaC drift (Snyk, Firefly, ArgoCD, Spacelift), GitOps continuous verification | **EXTENDED** |
| 3 | Semantic intent classification for gates | Intent classification before routing ([[intent-classification-before-routing-2026]], [[intent-based-routing-for-ai-agent-skills-2026]]) | LLM-based static analysis (IRIS, LintLLM, arXiv 2406.19508), Unit 42 guardrails survey | **EXTENDED** (different layer — Stop hooks vs routing) |
| 4 | Dispatch-without-wait lifecycle enforcement | Wait-all gate ([[parallel-subagent-wait-all-gate]]) | BackgroundManager architecture (oh-my-opencode), Flock LifecycleManager, Temporal/Prefect/Dagster lineage | **CONFIRMED** + **EXTENDED** (interface design) |
| 5 | Post-refactor integration testing | Smoke-test references ([[hook-script-capability-derivation-receipt-loop-fix]], [[diffusiongemma-direct-api-howto]]) | Consumer-Driven Contract Testing (Gabo Gil, Gravitee), "test the seam not the unit" (Augment Code) | **EXTENDED** (CDCT for skill chains) |

---

## Improvement 1: Refactoring consumer-update phase — `[NOVEL]`

### The problem

When a file is split, moved, or renamed during refactoring, every consumer
that points at the old path must be updated. On a multi-agent host, the
consumers include hook configs (`settings.json` PreToolUse entries,
`hooks.json` registrations, dispatcher chains), skill cross-references
(wikilinks, parent-skill imports, table-of-contents entries), config
paths (`.toml`, `.json`, `.yaml` references to scripts), and test
imports. Session 019fdf3d caught a critical bug where `quality_gate.py`
was split into a package but the Stop-hook config still pointed at the
old monolith path. The `/refactor` skill had no phase for consumer
update; it relied on unit tests passing, which don't exercise the hook
dispatch chain.

### What the wiki already knows

[[producer-consumer-contract-drift-in-skill-chains]] is the closest
existing concept. It covers field-name drift between skill producers
and consumers (e.g., `/refine` wrote "Original task (verbatim)" while
`/handoff` reads "Last user message (verbatim)"). That concept is at
the **inter-skill contract** layer — Markdown field names in handoffs.

This improvement is at the **file-path / dispatch-config** layer —
Python module paths in `settings.json`, hook registration paths in
`hooks.json`, JSON-pointer references in plugin manifests. The two
layers share the same drift mechanism but apply at different artifacts.

### What external research confirms

The Augment Code refactoring guide (March 2026) makes the same point
in different language: **"identify likely downstream consumers to reduce
the risk of abstraction boundaries that miss critical callers."** This
is the consumer-update phase in industry terms — it precedes the
refactor (consumer inventory) and follows the refactor (consumer
verification).

IDE-level consumer-update is a mature pattern:

| Tool | Consumer-update mechanism | Scope |
|------|---------------------------|-------|
| JetBrains (PyCharm/IntelliJ) | "Move" and "Rename" refactorings (F6 / Shift+F6) update all references atomically; Pre-refactor preview lists all affected files | Code symbols within a project |
| VS Code | Rename Symbol (F2) for cross-file symbol rename; LSP-driven for supported languages | Same |
| AWS CDK | `cdk refactor` command preserves deployed resources when construct paths change | CloudFormation stacks, not source code |
| Augment Code | "Identify downstream consumers" prompt before abstraction; post-refactor verification | Code + tests |

The **gap** between industry practice and our `/refactor` skill: IDEs
update **code references** automatically because they have language
servers and AST knowledge. Our `/refactor` skill operates on a
multi-artifact config surface (Python, JSON, TOML, Markdown, YAML) with
no unified symbol table. Consumer-update must be **discovered by grep**,
not inferred from the type system.

### Two actionable enhancements we hadn't considered

**Enhancement 1.1: Consumer inventory as a pre-refactor step (not
post-refactor).** Industry IDEs do it before; we currently do it
after. The session caught the bug post-refactor (unit tests missed it
because the dispatcher chain wasn't exercised). The fix is a mandatory
Step 0 in `/refactor`:

```
Step 0 — Consumer inventory (mandatory before any move/split/rename):
  1. List every file that references the path being moved (rg --files-with-matches "<old-path>").
  2. Classify each match: (a) code import, (b) config reference (settings.json/hooks.json),
     (c) skill cross-ref (wikilink, parent skill table), (d) test import, (e) doc reference.
  3. For each config reference, note the JSON key path (e.g., "hooks.Stop[0].command").
  4. Emit the inventory as a table: file:line | classification | update action.
```

**Enhancement 1.2: Post-refactor consumer-update verifier (separate
from unit tests).** Unit tests prove the moved module imports cleanly;
they do not prove `settings.json` still points at the new path. The
verifier walks the dispatch chain: for each PreToolUse/PostToolUse/
Stop entry, does the registered script path exist and import? This is
the `quality_gate.py` failure mode the session caught.

```
Verifier pseudocode:
  for entry in settings.json["hooks"].values():
    if entry.type == "command":
      path = entry.command.split()[0]  # python /path/to/script.py
      assert Path(path).exists(), f"hook points at missing file: {path}"
      assert importlib.util.find_spec(module_from_path(path)), f"hook script not importable: {path}"
```

The verifier is the structural fix; the consumer inventory is the
prevention. Both should be wired into `/refactor` Steps 0 and N.

### Falsifier

This enhancement is wrong if:
- The consumer inventory adds >30% overhead to every refactor for
  work that the language server already does (false positive on the
  cost). Mitigation: the inventory is a 30-second grep + 60-second
  table emit; cheaper than the bug it prevents.
- The verifier produces false positives on intentional dead-path
  references (e.g., commented-out hook entries kept as history).
  Mitigation: the verifier skips entries inside `#` comments and
  `disabled: true` blocks.

---

## Improvement 2: Credential/status drift detection in maintenance loops — `[EXTENDED]`

### The problem

Documentation about system state (API keys, MCP connections, backend
status, active credentials) drifts from reality on multi-agent hosts.
Session 019fdf3d built `credential_drift_detector.py` — a script that
probes live state and compares against the wiki/docs that claim to
describe it.

### What the wiki already knows

[[cli-api-drift-in-skill-scripts]] is the direct precedent. It
documents that skill scripts that wrap external CLIs hardcode API
assumptions (subcommand existence, flag signatures, response schemas)
that break silently when the wrapped CLI's version changes. The
structural fix proposed there was: runtime API probing + a shim module
that isolates the external API behind one import point + dependency
checks that probe API shape, not just existence.

This improvement extends the same discipline to **documentation drift**
— wiki/handoff claims about which API keys, MCP servers, and backends
are live and working. The failure mode is identical (silent
misalignment between stated and actual state), but the artifact class
is broader (Markdown documentation + .env/.toml config, not just
Python subprocess calls).

### What external research confirms

The industry pattern is called **drift detection** or **continuous
verification** in the IaC (Infrastructure-as-Code) world. Five major
sources converge on the same architecture:

| Source | Pattern | Recurrence |
|--------|---------|------------|
| Snyk (May 2023) | "Methods of detection and prevention that are effective in managing configuration drift" — preventive (IaC reapply) + detective (periodic scans) | Standard |
| Firefly (GitHub Actions guide) | "Catch infrastructure changes before they cause chaos" — wire drift scans into CI on every push | Standard |
| OpenLiberty / ArgoCD (Apr 2024) | "Closed-Loop Feedback & Control: ArgoCD's real-time monitoring ensures that the live state is always aligned with the Git repository's state. If a discrepancy is detected, ArgoCD offers visual representations of the divergence" | Closed-loop model |
| Hoop (Sep 2025) | "Tight coupling between drift detection and CI/CD controls turns the problem from reactive to proactive. GitHub Actions give you hooks to run infrastructure scans on every trigger." | Reactive → proactive |
| Spacelift (May 2026) | "Right after you run your IaC tool, both are identical, but unfortunately, they might not stay in sync for long" | Common framing |

**Hoop's framing ("reactive to proactive") is the key insight for our
workspace.** Our existing CLI-drift pattern is reactive — the script
fails when the API shape diverges, the operator notices (or doesn't).
The GitOps pattern is proactive — a scan runs on every push, drift is
detected before the failure manifests. Our `credential_drift_detector.py`
is closer to the GitOps model (it probes, doesn't wait for failure), but
it's not yet wired into a push trigger or a maintenance loop.

**Adjacent concept: Credential Debris.** A LinkedIn article (Gulia) and
NHiMG glossary entry define credential debris as "residual identity
artifacts like expired sessions, dormant tokens, abandoned MFA devices,
and over-provisioned service accounts" — and pair it with configuration
drift as "twin threats." For multi-agent hosts, credential debris is
specifically the MCP server entries, Claude/Gemini API keys, and CCR
fleet tokens that were valid at registration but are now expired,
revoked, or rotated. Drift detection on these requires an active probe
(`pwm usage`, `ccr status`, MCP `ping`), not just a config diff.

### Two actionable enhancements we hadn't considered

**Enhancement 2.1: Wire the detector into the maintenance loop on a
cron-like schedule, not just on-demand.** Hoop's proactive framing
applies: run the drift scan weekly (or on every push to `.env*` /
config files via a `PreToolUse` hook). The session's
`credential_drift_detector.py` exists; it's not yet on a schedule.
The structural fix is a `maintain/scheduled_jobs.yaml` entry.

**Enhancement 2.2: Add a "credential debris" pass alongside drift.**
Drift = claimed vs. actual. Debris = tokens/keys that no longer have
an active claim. For example, an API key referenced in `.env.toml`
but not used in any code for 30+ days is debris. The detector should
report both: (a) drift (claim doesn't match reality), (b) debris
(claim exists in reality but nothing reads it). The combined output
maps to the linkedin article's "twin threats" framing.

### Falsifier

This enhancement is wrong if:
- The drift detector's probes consume quota or rate-limit the
  external services (e.g., a `pwm usage` call after every commit).
  Mitigation: weekly cadence + on-config-change hook (not on every
  commit); cache results for 24h.
- The drift detector becomes a denial-of-service vector (a malicious
  config change triggers a cascade of external probes). Mitigation:
  rate-limit the detector itself; only run probes against named,
  pre-authorized services (not user-supplied URLs).

---

## Improvement 3: Semantic intent classification for enforcement gates — `[EXTENDED]`

### The problem

Keyword-regex-based Stop hooks accumulate false-positive suppressors
over time. Each suppressor is a new keyword added because a previous
one fired on something that wasn't actually the prohibited pattern.
The cycle is: hook fires → false positive → add suppressor → hook
fires on new phrasing → add more suppressors → eventually the hook
fires on so many things that operators ignore it. Session 019fdf3d
built `intent_classifier.py` — it classifies sentences as
RECOMMENDATION / CAUSAL_ASSERTION / DISCUSSION / NEUTRAL before
applying keyword checks. The classifier runs first, and the keyword
check only fires on RECOMMENDATION/CAUSAL_ASSERTION categories.

### What the wiki already knows

The wiki has substantial coverage of intent classification at the
**routing** layer (not the **gating** layer):

- [[intent-classification-before-routing-2026]] — three external patterns (TianPan cascade, WonderLab history injection, Pandey intent-to-action). Documents the cascade: keyword → embedding → fine-tuned SLM → LLM catch-all.
- [[intent-based-routing-for-ai-agent-skills-2026]] — applies the cascade to `/tp` session variant. Validates that LLM-based classification is sufficient for our scale (<15 categories).
- [[adaptive-orchestration-task-shape-classification]] — adaptive routing based on task shape.

Three separate concepts all address the routing layer (where the
classifier decides which skill/tool to invoke). Session 019fdf3d's
`intent_classifier.py` addresses the gating layer (where the classifier
decides whether a Stop hook should fire on a given sentence). The
mechanism is identical; the layer is different.

### What external research confirms

The academic literature on LLM-based static analysis validates the
approach and identifies the optimal hybrid:

| Source | Pattern | Recurrence |
|--------|---------|------------|
| arXiv 2406.19508 ("Code Linting using Language Models", Jun 2024) | "Language models can analyze code within its broader context, considering not just syntax but also the logical flow and intent behind the code. This contextual understanding allows for more precise identification of potential issues and more meaningful suggestions for improvement." | Foundational — semantic linting beats regex |
| arXiv 2505.12118 ("Do Code LLMs Do Static Analysis?", May 2025) | Empirically: LLMs sometimes use semantics instead of syntactic information; static-analysis-style prompts don't always improve coding | Caveat — semantic isn't always better |
| IRIS (OpenReview 9LdJDU7E91) | "We propose IRIS, a neuro-symbolic approach that systematically combines LLMs" with traditional static analysis | **Hybrid wins** |
| LintLLM (arXiv 2502.10815) | Domain-specific LLM linter for Verilog; framework generalizes | Domain-specific LLM linters viable |
| Unit 42 (Palo Alto) — LLM guardrails comparison | "Output guardrails generally exhibited low false positive rates. This was largely attributed to the LLMs themselves being aligned to refuse harmful requests or avoid generating disallowed content in response to benign prompts." | **Low false-positive is achievable with LLM-based guards** |

**The IRIS finding is the key insight for our workspace.** The
optimal pattern is **neuro-symbolic**: a deterministic rule (regex or
AST pattern) gated by an LLM classifier. The classifier answers
"is this an enforcement-relevant statement?" and the rule answers
"does this statement match the prohibited pattern?". Session
019fdf3d's `intent_classifier.py` is structurally identical to IRIS's
neuro-symbolic gate — it just operates on natural language (LLM
output) rather than source code.

**Unit 42's empirical finding (low false-positive with LLM guards)**
is the empirical backing for the approach. The earlier concern that
"LLM classifiers add noise" is empirically wrong at the guard layer;
the LLMs themselves are aligned to refuse false positives on benign
input.

### Two actionable enhancements we hadn't considered

**Enhancement 3.1: Hybrid neuro-symbolic gate, not pure semantic
classification.** The current `intent_classifier.py` runs the LLM
classifier first, then the keyword check. The IRIS pattern is the
inverse: the deterministic rule runs first (cheap, fast, no false
negatives on the obvious cases), then the LLM classifier gates the
ambiguous cases (where the rule would false-positive). Concretely:
for a Stop hook checking "claim done without verification," the
deterministic regex catches explicit "I'm done" / "task complete"
phrases; the LLM classifier catches "looks good, ship it" / "this
should work" phrasings that imply completion without verification.
The current implementation may already do this; the wiki should
document the hybrid pattern explicitly so future hooks don't reinvent
the pure-LLM-first variant.

**Enhancement 3.2: Apply the same pattern to PreToolUse hooks, not
just Stop hooks.** The wiki and `intent_classifier.py` focus on Stop
hooks (gating the model's final output). The same mechanism applies
to PreToolUse hooks (gating destructive tool calls) and UserPromptSubmit
hooks (gating user prompts that contain embedded instructions). The
classifier categories can be reused; only the keyword pattern changes
per hook. A single `intent_classifier.py` module + a per-hook keyword
table is the structural fix.

### Falsifier

This enhancement is wrong if:
- The LLM classifier adds >500ms latency to the hook (violates the
  10s ceiling on detection-vs-validation). Mitigation: cache the
  classifier output per (session, turn); most turns reuse the cached
  classification.
- The neuro-symbolic hybrid produces new false-negative cases the
  pure-LLM-first version would have caught (the deterministic rule
  is too aggressive). Mitigation: when the rule fires, log a sample;
  review the sample weekly to catch under-fitting.

---

## Improvement 4: Dispatch-without-wait lifecycle enforcement — `[CONFIRMED]` + `[EXTENDED]`

### The problem

Background subagents dispatched but never waited on before session end
is a structural anti-pattern. The orchestrator spawns N parallel
research subagents, reads partial results from M < N, and emits a
conclusion or persists a wiki concept before the missing subagents
return. Session 019fdf3d is not the origin of this problem — it's
already covered by [[parallel-subagent-wait-all-gate]] from session
019f9f4f (2026-07-26).

### What the wiki already knows

[[parallel-subagent-wait-all-gate]] is the canonical existing concept.
It establishes:

1. No durable artifact may be emitted until `get_command_or_subagent_output`
   with ALL N task IDs returns every task as completed or explicitly
   failed.
2. "Task not found" is a mechanical error in the orchestrator, not a
   signal to proceed (revised 2026-07-31 with Mode 1/2/3 protocol).
3. Re-spawning is permitted in Mode 3 (genuine loss) — the original
   is always folded in when it arrives.
4. Persistence-before-completion is the canonical failure.

The session 019fdf3d improvement is to **strengthen** this rule with
a lifecycle interface that makes the wait-all gate impossible to
bypass, not just discouraged.

### What external research confirms

Three independent agent/async-task frameworks converge on the same
interface pattern:

| Source | Pattern | Recurrence |
|--------|---------|------------|
| Agentbase (background tasks primitive) | "Task Lifecycle. Resource-Intensive Tasks: Complex computations without blocking other operations. Non-Blocking Execution. Initiate tasks and continue without waiting for completion. Status Tracking." | Three primitives: lifecycle, non-blocking, status |
| oh-my-opencode BackgroundManager (DeepWiki) | "It manages the complete lifecycle of background tasks, from creation through completion. The BackgroundTask interface represents a single background agent execution with complete lifecycle tracking." | **`BackgroundTask` interface with complete lifecycle** |
| Flock (`whiteducksoftware/flock`) | "Task Lifecycle Management. IMPORTANT: Always clean up fire-and-forget tasks on shutdown!" — `LifecycleManager` class with "Track all created tasks" | **LifecycleManager with shutdown cleanup** |
| NodeBook Runtime Labs | "Validated task definitions. Read versioned JSON task files, normalize task fields, reject duplicate ids, validate dependencies, and turn user input into one scheduler-ready shape." | **Validated task definitions before dispatch** |
| Temporal / Prefect / Dagster / Airflow / Argo Workflows | Mature lineage — durable execution, status polling, recovery from crashes | Production-grade reference |

**The convergence is striking.** All five frameworks converge on:
- A typed task object (not a raw string ID)
- A lifecycle manager that owns the task set
- Status tracking and a way to query "what's still pending?"
- Cleanup on shutdown (Flock's "Always clean up fire-and-forget tasks on shutdown!")

The current Grok Build model uses `spawn_subagent(background=true)`
returning a string task ID, with `get_command_or_subagent_output`
used manually to wait. This is the raw-strings-and-call-the-orchestrator
version of the pattern — equivalent to C's `fork()` vs Go's `goroutine`
+ `WaitGroup`. The interface is the lever; the rule is the policy.

### Two actionable enhancements we hadn't considered

**Enhancement 4.1: A `BackgroundTaskSet` (or `SubagentFleet`) class
that owns the task lifecycle.** Modeled on Flock's `LifecycleManager`
and oh-my-opencode's `BackgroundTask` interface. The class:
- Tracks every `spawn_subagent(background=true)` call by ID
- Exposes `pending() -> List[TaskID]`, `completed() -> List[TaskID]`,
  `failed() -> List[TaskID]`
- Exposes `wait_all(timeout_ms) -> WaitResult` that the Stop hook
  can call mechanically
- Auto-cleans pending tasks on shutdown (Flock's pattern)

The current wiki rule (`wait-all-before-conclude`) is prose. The
class is the structural enforcement: a Stop hook that calls
`fleet.wait_all(60_000)` cannot fire if any task is still pending.

**Enhancement 4.2: Validate task definitions before dispatch, per
NodeBook's pattern.** Before `spawn_subagent`, validate that:
- The prompt is non-empty
- The model is not in quota-exhausted state (already done by the
  `PreToolUse_spawn_model_gate.py` hook; surface it as a class
  precondition)
- The dispatch has a matching `wait_all` consumer (a lint that
  flags any `spawn_subagent` not followed by a `wait_all` in the
  same skill's reference implementation)

The lint catches the failure mode at skill-authoring time, not at
runtime. Combined with the `BackgroundTaskSet` class, the rule
becomes "the class enforces the gate; the lint enforces the gate's
usage."

### Falsifier

This enhancement is wrong if:
- The class overhead (Python object construction, state tracking)
  adds >100ms per dispatch. Mitigation: the class is a thin wrapper
  around a dict; overhead is sub-millisecond.
- The auto-cleanup fires on tasks the operator wanted to persist
  across sessions. Mitigation: the cleanup is opt-in via a
  `persist=True` flag at dispatch time.

---

## Improvement 5: Post-refactor integration testing of the consumer pipeline — `[EXTENDED]`

### The problem

After refactoring file structure (splits, moves), unit tests pass but
the consumer pipeline (hook configs → dispatcher → registered scripts)
is not exercised. Session 019fdf3d's bug — `quality_gate.py` split
into a package but Stop hook still pointing at the old monolith path
— is exactly this failure mode. Unit tests don't import
`settings.json`; they don't traverse the hook dispatch chain.

### What the wiki already knows

The wiki has multiple smoke-test references but no concept dedicated
to **post-refactor structural verification**:

- [[hook-script-capability-derivation-receipt-loop-fix]] — "6 pytest tests pass, 8 smoke tests pass, 10 behavioral hook tests pass" — mentions smoke tests but not refactor-specific.
- [[diffusiongemma-direct-api-howto]] — "minimal smoke test (minimal call)" — recipe-level smoke test, not pipeline-level.
- [[cli-api-drift-in-skill-scripts]] — "the shim's smoke test (`python wiki_search.py`) catches drift at runtime" — runtime smoke test for the shim.

The closest concept is the post-move smoke test as a verification
step, but it's embedded in other concepts (drift, hook derivation)
rather than being its own page.

### What external research confirms

The industry pattern is **Consumer-Driven Contract Testing (CDCT)**
— most directly applicable to our skill chains (each skill is a
"service" with a contract that downstream skills consume):

| Source | Pattern | Recurrence |
|--------|---------|------------|
| Gravitee (Sep 2025) | "Contract testing enforces these specifications by checking that each change adheres to the previously agreed-upon structure. If a provider modifies its API, the consumer will immediately be alerted if their expectations are no longer met." | **CDCT's value is catching the consumer-side breakage** |
| Gabo Gil (Feb 2026) | "Outdated contracts can result in a deceptive 'green' CI build that still breaks in production." — "service boundaries become explicit, which is great for decoupling but demands governance" | Governance requirement: contracts must be kept current |
| Augment Code refactoring guide | "Before introducing a new seam, identify likely downstream consumers to reduce the risk of abstraction boundaries that miss critical callers" | Pre-refactor consumer inventory + post-refactor verification |
| Microsoft Code-with-Engineering-Playbook | "Smoke testing should be performed immediately after a new build is deployed to a test environment, before any detailed testing begins. In continuous integration environments, smoke tests run automatically after every code commit that produces a new build." | **CI integration = post-every-commit verification** |

The Augment Code insight is the key one for our workspace: **before
introducing a new seam, identify likely downstream consumers**. This
is the same consumer-inventory pattern as Improvement 1, but applied
to test design rather than to refactor execution. The two combine:
consumer inventory → refactor → post-refactor integration test that
exercises every consumer identified in the inventory.

The Microsoft Playbook's framing ("smoke tests run automatically after
every code commit that produces a new build") is the **CI integration**
pattern. Our `quality_gate.py` post-refactor bug would have been
caught by a smoke test that runs on every commit to `quality_gate.py`
specifically.

### Two actionable enhancements we hadn't considered

**Enhancement 5.1: A "consumer pipeline smoke test" that walks the
full dispatch chain, distinct from unit tests.** The test is not a
pytest unit test — it's an integration test that:
1. Loads `settings.json` and `hooks.json`
2. For each registered hook, verifies the script path exists, is
   importable, and the entry-point function is callable
3. For each cross-skill reference (wikilinks, parent-skill imports),
   verifies the target file exists and contains the expected anchor
4. For each config reference (paths in `.toml`, `.env.toml`),
   verifies the path is resolvable
5. Exits non-zero if any consumer is broken

This is the test the session's `quality_gate.py` bug needed and didn't
have. It is structurally similar to CDCT's consumer-side contract
test (the consumer verifies the provider still satisfies its
expectations), but applied to file paths rather than HTTP responses.

**Enhancement 5.2: Run the smoke test as a PreToolUse hook on
destructive operations (file split, file move, file rename).** The
hook fires when a tool call would split, move, or rename a tracked
file. It runs the consumer pipeline smoke test in dry-run mode (no
writes; just reports which consumers would break). If any consumer
breaks, the hook warns (or blocks, depending on configuration). This
makes post-refactor verification **preventive** rather than
**diagnostic** — the bug surfaces before the destructive operation,
not after.

### Falsifier

This enhancement is wrong if:
- The consumer pipeline smoke test takes >30s per run (violates the
  hook timeout). Mitigation: cache results per git SHA; only re-run
  when `settings.json` / `hooks.json` / the target file's git SHA
  changes.
- The smoke test produces false positives on intentional breaking
  changes (e.g., a planned skill deprecation). Mitigation: a
  `--allow-breaking-changes` flag the operator passes when
  intentional.

---

## What this means for our workspace

The five improvements cluster into three concrete workstreams:

### Workstream A: `/refactor` skill upgrade (Improvements 1 + 5)

The `/refactor` skill needs two new phases:

- **Step 0 — Consumer inventory** (Enhancement 1.1): grep + classify
  every reference to the path being moved; emit a table; require the
  operator to confirm the inventory before proceeding.
- **Step N — Consumer pipeline smoke test** (Enhancement 5.1): walk
  the dispatch chain and prove every consumer still resolves. This is
  the test the `quality_gate.py` bug needed.

Optional: a PreToolUse hook that fires on destructive operations
(Enhancement 5.2) makes both phases preventive rather than
diagnostic.

### Workstream B: Maintenance loop enhancements (Improvement 2)

`credential_drift_detector.py` exists; it's not on a schedule. The
structural fix:

- Add a `maintain/scheduled_jobs.yaml` entry running the detector
  weekly (Enhancement 2.1).
- Add a "credential debris" pass alongside drift detection
  (Enhancement 2.2).
- Optional: a PreToolUse hook that fires on changes to `.env*` /
  credential config files, triggering the drift scan.

### Workstream C: Gating infrastructure (Improvements 3 + 4)

- **For Improvement 3:** document the neuro-symbolic hybrid pattern
  (Enhancement 3.1) explicitly in the `intent_classifier.py` SKILL /
  README so future hooks don't reinvent the pure-LLM-first variant.
  Apply the same pattern to PreToolUse hooks (Enhancement 3.2).
- **For Improvement 4:** introduce a `BackgroundTaskSet` class that
  enforces the wait-all gate mechanically (Enhancement 4.1). Add a
  lint that flags any `spawn_subagent` not followed by a `wait_all`
  in the same skill's reference implementation (Enhancement 4.2).

### Priority ordering

Per the rule "optimal long-term, not minimal fix":

| Workstream | ROI | Why |
|------------|-----|-----|
| A (`/refactor` upgrade) | High | The bug class is recurring (session 019fdf3d caught one; likely more latent). The fix is bounded (two skill phases, ~50 lines of code). |
| C.2 (`BackgroundTaskSet`) | High | The wait-all rule is prose and breaks under pressure (per [[parallel-subagent-wait-all-gate]]'s own analysis). A class makes the gate mechanical. |
| B (drift detector scheduling) | Medium | Drift detector exists; scheduling is cheap. The debris pass is incremental. |
| C.1 (intent classifier docs) | Medium | The pattern is already implemented; documentation is the gap. |
| C.2 lint (companion to class) | Low | The class enforces the gate; the lint enforces correct usage. Defer until the class is in place. |

### Sequencing

Do A first (the `quality_gate.py` bug is recent and concrete). Then
C.2 (the `BackgroundTaskSet` is the highest-leverage enforcement
fix). Then B (scheduling is cheap). Then C.1 (documentation). C.2
lint is a companion to the class; ship together.

---

## Falsifier (for the whole concept)

This concept is wrong if:
- The five improvements overlap with existing wiki concepts enough
  that no new captures are needed. Mitigation: the labels are
  explicit (`[CONFIRMED]` / `[EXTENDED]` / `[NOVEL]`); new wiki pages
  are warranted only for the `[EXTENDED]` items where the existing
  concept is at a different layer (Improvement 1 file-path vs
  producer-consumer field-name; Improvement 3 Stop-hook vs routing;
  Improvement 5 structural-refactor vs general smoke test).
- The enhancements above are over-engineering for a solo-operator
  fleet. Mitigation: each enhancement is a bounded change (≤100
  lines), with the highest-ROI items (Workstream A) motivated by a
  specific recent bug.
- Industry moves away from the patterns cited (CDCT loses favor,
  LLM-based static analysis is replaced by some new approach). The
  cited sources are 2024-2026; the patterns are recent enough to
  remain current for at least 12-18 months.

---

## Receipts (for the session's claims)

- **"We built `credential_drift_detector.py`"**: session 019fdf3d
  artifact (referenced in the session's research request; path
  TBD by session).
- **"We built `intent_classifier.py`"**: `P:/.claude/hooks/shared/intent_classifier.py`
  (read this session, lines 1-50). Existing module, not session-built.
- **"We caught a `quality_gate.py` split bug where the Stop hook
  pointed at the old monolith path"**: session 019fdf3d artifact
  (referenced in the research request).
- **DDG search results**: 10 searches run this session
  (5 topics × 2 queries each); all returned ≥4 relevant results.
- **Existing wiki coverage verified**: read 5 existing wiki concepts
  this session (`parallel-subagent-wait-all-gate`,
  `intent-classification-before-routing-2026`,
  `intent-based-routing-for-ai-agent-skills-2026`,
  `cli-api-drift-in-skill-scripts`,
  `producer-consumer-contract-drift-in-skill-chains`,
  `code-orchestrates-model-judges-skill-scale`).

---

## Auto-related

- [[parallel-subagent-wait-all-gate]] — improvement 4 strengthens with BackgroundManager interface
- [[intent-classification-before-routing-2026]] — improvement 3 applies the same technique at a different layer
- [[intent-based-routing-for-ai-agent-skills-2026]] — cascade pattern; improvement 3's hybrid is a refinement
- [[cli-api-drift-in-skill-scripts]] — improvement 2 broadens to credentials + status
- [[producer-consumer-contract-drift-in-skill-chains]] — improvement 1 adds the file-path layer
- [[code-orchestrates-model-judges-skill-scale]] — improvement 5 is a micro-scale instantiation for refactor verification
- [[check-and-fix-skills-verification-skills-should-fix-what-they-can]] — improvement 5 shares the auto-fix-what-is-deterministic principle
- [[agent-config-directory-taxonomy]] — relevant to Improvement 1's consumer-update phase (path references in plugin manifests)
- [[mechanical-enforcement-over-behavioral-reminder]] — Improvement 3 + 4 are both mechanical-enforcement instantiations
---

## /tp review deep-dive (2026-08-08)

A `/tp` (premise-critique) review surfaced 6 items from the 5 improvements
above that were flagged `[REFINE]` (need more evidence) or `[DEFER]`
(marginal ROI). This section captures the wiki-web-wiki cycle that
resolved each: external research via `search_web__query` (Brave + Exa +
DuckDuckGo fused) on 2026-08-08, plus a fresh read of our own
implementations to disambiguate the wiki's framing.

### Discovery correction (important before verdicts)

The original wiki description of Improvement 3 said `intent_classifier.py`
"runs the LLM classifier first, then the keyword check." Reading the
actual implementation this session (`P:/.claude/hooks/shared/intent_classifier.py`
lines 1-50) shows it is **embedding-based semantic classification via
sentence-transformers, ~10ms local** — not an LLM call. The IRIS
"neuro-symbolic" framing in the original concept was based on the
academic literature's LLM-vs-rule debate, which does not directly apply
when the "LLM" half is actually a 10ms embedding lookup. This changes
R1's framing materially — see R1 below.

### Verdicts (6 items)

#### R1 — Neuro-symbolic gate ordering — `CONFIRM CURRENT ARCHITECTURE` (do not flip)

**The original wiki assumed:** our gate runs an LLM classifier first,
then keyword. The IRIS pattern (deterministic rule first, LLM classifier
for ambiguous cases only) would suggest flipping.

**What the actual code does** (`P:/.claude/hooks/shared/intent_classifier.py`,
confirmed this session): runs a **local sentence-transformers embedding
classifier (~10ms) first**, then the regex `skill_enforcer` second
(`tests/test_intent_classifier_integration.py:78-83` — priority 0.5 vs 1.0).

**External evidence the IRIS pattern doesn't apply at our scale:**

- **Semgrep AI-powered detection** (`semgrep.dev/blog/2025/ai-powered-detection-with-semgrep/`):
  *"AI-powered detection starts with deterministic findings—improving
  true positive rates for IDORs and business logic vulnerabilities over
  LLM-only methods."* Semgrep is rule-first because their rules are
  cheap (millisecond regex/AST) and LLM is slow (hundreds of ms).
- **Vulnhalla** (CyberArk, `cyberark.com/resources/threat-research-blog/vulnhalla-picking-the-true-vulnerabilities-from-the-codeql-haystack`):
  *"combining CodeQL with LLM-powered reasoning"* — rule-first, LLM-for-triage.
- **Emerging Trends paper** (`lexuanbach.github.io/publication/IEA2026c.pdf`):
  *"these gains emerge primarily when agents augment established tools
  rather than replace them."*
- **DEV.to** (`dev.to/ayame0328/how-i-replaced-llm-based-code-analysis-with-static-analysis-and-got-better-results-43nl`):
  *"Confidence levels. High confidence for clear-cut cases (eval(input())),
  medium for ambiguous ones (eval() with non-obvious arguments)."*

**Where Semgrep's rule-first reasoning breaks:** when the rule is slow
(LLM, not regex), or when the semantic gap between phrasings is too
large for a single regex. Our case is the second: embedding classifier
at 10ms is fast enough that it doesn't waste budget, and paraphrased
commands ("git push --force" vs "force push the branch") need semantic
understanding — see R2 evidence on Anthropic issue 26862.

**Verdict:** the current "embedding-classifier-first, regex-second"
ordering is already optimal for our scale. The original wiki
"LLM-first" framing was inaccurate; the IRIS debate does not apply
because the slow half doesn't exist in our pipeline. **Do not flip.**

**Falsifier:** this verdict is wrong if a future hook needs to call a
real LLM (not embedding) for disambiguation. In that case, the IRIS
pattern does apply and the LLM should be the second-stage fallback, not
the first gate.

#### R2 — Semantic PreToolUse gating — `UPGRADE TO SHIP` (with bounded scope)

**External evidence is strong that semantic PreToolUse gating is
production-viable, not theoretical:**

- **Anthropic Claude Code Auto Mode** (`arxiv.org/abs/2604.04978`,
  arXiv 2604.04978): *"0.4% false positive rate and 17% false negative
  rate on production"* — Anthropic's own two-stage transcript classifier
  is the deployed reference implementation.
- **Cursor** (`cursor.com/docs/enterprise/llm-safety-and-controls`):
  *"Auto-review runs allowlisted calls, sandboxes shell commands when
  it can, and routes the rest through an LLM classifier that returns
  allow or block based on safety and how well the call matches the
  user's intent."*
- **Dyad** (`dyad.sh/blog/claude-code-permission-hooks`): *"Python-based
  system that calls Claude Sonnet to classify operations as GREEN,
  YELLOW, or RED."*
- **OpenCode Auto Mode** (`github.com/anomalyco/opencode/issues/33585`):
  *"Escalation backstop — per-session denial counters (3 consecutive /
  20 total), reset each user turn, so a false positive can't loop
  forever."* — the missing piece: backstop on false positives.
- **Open-source tools:** `claude-intent-alignment-guard`, `agent-gate`,
  `cc-toolgate` (3 separate GitHub repos).

**Evidence the current regex-only PreToolUse hooks DO have FP problems:**

- **Anthropic issue 26862** (`github.com/anthropics/claude-code/issues/26862`):
  *"High false-positive rate: Hooks that try to block patterns like
  git push --force or drizzle-kit push frequently misfire on completely
  safe commands"* (e.g., `git push origin main` blocked because hook
  sees "push" and gets confused).
- **destructive_command_guard** (`github.com/Dicklesworthstone/destructive_command_guard`):
  implements a 3-tier gate — Tier 1 quick reject (<10μs keyword), Tier 2
  context classification, Tier 3 full regex on executable spans only.
  This is exactly the deterministic-first semantic-second hybrid.

**Our existing hooks already follow the hybrid pattern, but inconsistently:**

| Hook file | Current architecture | Gap |
|-----------|---------------------|-----|
| `PreToolUse_bash_syntax_validator.py` | AST parsing + heuristics | Already semantic — no change needed |
| `PreToolUse_existence_gate.py` | Existence probing | Already semantic |
| `PreToolUse_evidence_hierarchy_gate.py` | Pattern + context | Mostly deterministic |
| `PreToolUse_referent_scope_gate.py` | Reference resolution | Semantic-adjacent |
| `PreToolUse_task_done_evidence_gate.py` | Regex on output | **FP-prone** — candidate for upgrade |
| (none) | Destructive-command detection | **MISSING** — highest-value target |

**Concrete action (bounded ~100 lines):**

1. Add a `PreToolUse_destructive_command_gate.py` hook modeled on
   `destructive_command_guard` 3-tier pattern (keyword < 10μs, context
   classification, regex only on executable spans).
2. Use the existing `intent_classifier.py` embedding module as the
   context-classification layer (reuse, don't reimplement).
3. Add an OpenCode-style escalation backstop: deny-counter per session
   (3 consecutive / 20 total) so a single misfire can't loop forever.
4. Ship the destructive-command gate FIRST; defer the upgrade of
   `task_done_evidence_gate.py` until the new pattern proves out.

**Verdict:** ship the destructive-command PreToolUse gate as the next
concrete instance of the semantic-gating pattern. The Anthropic 0.4% FP
empirical benchmark sets the bar; the OpenCode backstop is the
required safety mechanism.

**Falsifier:** this verdict is wrong if our embedding classifier takes
>100ms per call in production (violates PreToolUse latency budget). The
test in `intent_classifier.py` claims ~10ms; verify on real workloads
before shipping.

#### R3 — Wire drift detector into `/maintain` — `UPGRADE TO SHIP` (integration point already exists)

**External evidence is overwhelming that drift detection belongs in a
scheduled maintenance loop, not a new scheduler:**

- **Renovate** (`docs.renovatebot.com/key-concepts/scheduling/`,
  `stackharbor.com/en/knowledge-base/renovate-bot-dependency-updates/`):
  standard cadence is weekly, with `vulnerabilityAlerts.schedule` to
  bypass for security. Composable scheduling is built in.
- **Dependabot** (`github.blog/changelog/2025-04-22-dependabot-now-lets-you-schedule-update-frequencies-with-cron-expressions/`):
  added cron-interval support (`dependabot-core#6339`) — same composable
  pattern.
- **Spacelift** (`docs.spacelift.io/concepts/stack/drift-detection`):
  *"periodically executing proposed runs on your stable infrastructure...
  create a drift detection schedule for your stack. You will be able to
  add multiple cron rules."* Multiple cron rules per stack is the exact
  composable-check pattern.
- **Dagster Declarative Automation** (`docs.dagster.io/guides/automate/declarative-automation/migrating-from-sensors`):
  *"Conditions are built from small, composable operators (since,
  newly_true, all_deps_match) that can be combined, customized, and
  shared across assets."* — the same shape our `/maintain` needs.
- **bugfree.ai** (`bugfree.ai/knowledge-hub/drift-detection-in-gitops-workflows`):
  *"Schedule regular checks to compare the live state of your
  infrastructure with the desired state... can be done through cron
  jobs or CI/CD pipelines that trigger drift detection scripts."*
- **Devonair** (`devonair.ai/blog/workflows/cron-scheduled-maintenance`):
  production example — *"Security scan at 2 AM, Check for critical
  updates at 3 AM, Clean up temporary files at 4 AM"* — same shape as
  `/maintain` Step 2a/2b/2c.

**Critical local finding — the integration point is already built.**

Reading `C:\Users\brsth\.grok\skills\maintain\SKILL.md` lines 309-329
this session, `/maintain` already has **Step 2h — Scheduled checks**
with:

- Registry file: `P:/.data/scheduled-checks.json`
- Runner: `P:/.agents/scripts/scheduled_checks.py`
- Per-check "runs at most once per day" semantics
- Adding a new check = appending one JSON entry

The `/tp` review's "use existing `/maintain`, not a new scheduler"
verdict was correct. **No new infrastructure is needed.**

**Concrete action (bounded ~10 lines):**

Append one entry to `P:/.data/scheduled-checks.json`:

```json
{
  "id": "credential-drift-detector",
  "description": "Probe live state vs documented credentials, status, MCP connections",
  "check_type": "command",
  "check_args": {"cmd": "python ~/.grok/skills/<x>/scripts/credential_drift_detector.py --json"},
  "action_on_found": "append to P:/.data/wiki/concepts/credential-drift-reports/<date>.md",
  "frequency": "daily",
  "last_checked": null,
  "status": "pending",
  "created": "2026-08-08"
}
```

**Verdict:** ship the integration as a single JSON entry. The
`/maintain` Step 2h infrastructure already handles scheduling,
deduplication, and report generation — extending it is the right
integration pattern, not building a parallel scheduler.

**Falsifier:** this verdict is wrong if `credential_drift_detector.py`
calls quota-consuming APIs (e.g., `pwm usage` after every commit).
Mitigation: weekly cadence for quota-consuming probes; daily for
config-file diff probes that don't hit external APIs.

#### D1 — Credential debris detection — `UPGRADE WITH SCOPE` (not full deferral)

**The /tp review was right that "every backup key looks like debris"
in a naive implementation, but external practice shows the
distinction is achievable:**

- **TruffleHog verifier** (`trufflesecurity.com/blog/how-trufflehog-verifies-secrets`,
  `appsecsanta.com/trufflehog`): *"TruffleHog pulls ahead on raw
  feature count. Its 800+ detectors include active credential testing
  that confirms whether a key still works... tells you which historical
  credentials are still live and must be rotated now."* — the
  verifier API answers "is this credential actually used?"
- **TruffleHog falsepositives.go** (`github.com/trufflesecurity/trufflehog/blob/9f0b97f1/pkg/detectors/falsepositives.go`):
  explicit FP filter file — the tool treats FP management as a
  first-class concern.
- **GitGuardian ML filtering** (`devsecops.ae/secrets-scanners-comparison-2026/`):
  *"ML-based filtering that drops false positives"* — industry
  practice is to use verifier signals, not just regex match.
- **AWS IAM GetCredentialReport** (`docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_finding-unused.html`):
  *"Identify when an IAM access key was last used"* — `last_used`
  timestamp is the canonical signal.
- **Azure Operator Nexus** (`learn.microsoft.com/en-us/azure/operator-nexus/howto-credential-rotation`):
  `secretRotationStatus.lastRotationTime` field — rotation timestamp
  signal.
- **NHiMG** (`nhimg.org/faq/what-fails-when-inactive-credentials-are-not-fully-revoked-before-system-retirem/`):
  the concept of "inactive credentials" specifically — distinguishes
  from "rotated" and from "live."
- **OneUptime** (`oneuptime.com/blog/post/2026-01-30-security-secret-rotation-strategies/view`):
  *"A credential leaked six months ago is still valid if you never
  rotated it."* — the harm is unrevoked credentials, not all
  credentials.

**The signal exists. The /tp review's concern was a naive
implementation; the right scope is narrower:**

- "Debris" = (a) credentials verified as no longer functional (TruffleHog
  verifier returned 401/expired) AND (b) older than N days (e.g., 90d)
  AND (c) not referenced in any current code/config.
- "Backup" = (a) currently functional OR (b) referenced in code/config
  OR (c) recently used (last_used < N days).

**Concrete action (bounded ~50 lines):**

Add a "credential debris" pass to `credential_drift_detector.py` that
uses TruffleHog-style verification (or a lightweight equivalent) to
classify each detected credential:

| Verifier result | last_used | Classification | Action |
|----------------|-----------|----------------|--------|
| 401/expired | >90d | **Debris** | Suggest rotation |
| Functional | any | Live | No action |
| Verifier unreachable | <30d | Indeterminate | Mark for manual review |
| Verifier unreachable | >180d | Likely debris | Suggest rotation |

**Verdict:** upgrade with scope. Implement the debris pass with the
verifier-first signal (TruffleHog model), not regex-only. The naive
"every backup looks like debris" concern is addressed by the
verifier-first classification.

**Falsifier:** this verdict is wrong if the verifier calls consume quota
or hit rate limits across N services. Mitigation: batch probes (1
per service per day); cache verifier results for 24h; never probe
unauthorized services.

#### D2 — Runtime task-definition validation — `PARTIAL UPGRADE` (envelope, not full schema)

**The /tp review said "mostly covered by spawn_model_gate." The reality
is partial — model selection is covered, task envelope is not:**

Read `C:\Users\brsth\.grok\hooks\PreToolUse_spawn_model_gate.py` lines
1-100 this session. Current validation:

- ✅ Serde-broken models → block
- ✅ Quota-exhausted providers → block with fallback chain
- ✅ Reads `fleet-models.json` registry
- ❌ Prompt non-empty (not validated — empty prompt would still dispatch)
- ❌ Wait_all consumer (not validated — Improvement 4.2 lint not yet built)
- ❌ Return-shape schema (not validated — depends on caller)
- ❌ Dispatch envelope (parent context, expected duration, model lane)

**External evidence the envelope-level check is a real pattern:**

- **Director-AI Agent Preflight Guard** (`anulum.github.io/director-ai/api/agent-preflight/`):
  validates dispatch envelope, not just model selection.
- **pcvelz/superpowers** (`github.com/pcvelz/superpowers`):
  `pre-agent-task-dispatch-validate.sh` for "transcript-walking logic
  and the SUPERPOWERS_DISPATCH_GUARD=0 escape hatch. Metadata keys are
  documented in skills/shared/task-format-reference.md. Optional
  PostToolUse hook on Agent that fires the moment a subagent's [result
  is consumed]." — exact shape of our missing envelope check.
- **bugcrowd/ecs-task-definition-validator** (`github.com/bugcrowd/ecs-task-definition-validator`):
  *"Validates ECS Task Definitions with JSON Schema."* — schema
  validation pattern.
- **voxmedia/open-agent-toolkit** (`github.com/voxmedia/open-agent-toolkit`):
  `oat-dispatch-subagents` with `record-schema.md` — record schema
  for dispatch.
- **Agent Safety Gates** (`medium.com/@ThinkingLoop/agent-safety-gates-12-preflight-checks-before-tools-run-ecf1c41ba252`):
  *"12 preflight checks before tools run"* — the comprehensive gate
  list pattern.

**Bounded action (~30 lines):**

Add 3 envelope checks to `PreToolUse_spawn_model_gate.py`:

```python
# Envelope validation (additive to existing model/quota checks)
if not spawn_args.get("prompt", "").strip():
    block("empty_prompt", "Task definition missing prompt")
if "wait_all" not in caller_stack_trace and spawn_args.get("background"):
    block("missing_wait_all", "Background subagent dispatched without wait_all consumer")
if spawn_args.get("model") and not is_lane_compatible(spawn_args["model"], spawn_args.get("lane")):
    block("lane_mismatch", f"Model {spawn_args['model']} not in expected lane")
```

**Verdict:** partial upgrade — add the 3-line envelope check, don't
build a full schema validator. The model/quota validation is already
comprehensive; the envelope is the actual gap.

**Falsifier:** this verdict is wrong if the wait_all check produces
false positives on fire-and-forget subagents the operator wants to
persist across sessions. Mitigation: opt-in `persist=True` flag at
dispatch time (Flock's pattern, already cited in the parent concept).

#### D3 — Smoke test in PreToolUse — `CONFIRM DEFER WITH CARVE-OUT`

**External evidence is unanimous that running smoke tests in a
PreToolUse hook is impractical at our scale:**

- **Pre-commit perf issue** (`github.com/pre-commit/pre-commit/issues/1564`):
  *"execution time of pre-commit is >7 seconds with the before/after
  diffs, and ~1 second with those diffs disabled."* — even diff
  calculation is a budget hit.
- **Pre-commit perf issue** (`github.com/pre-commit/pre-commit/issues/3603`):
  *"Pre-commit performance issues in our large repository"* —
  documented class.
- **thoughtspile** (`thoughtspile.github.io/2021/06/14/faster-pre-commit/`):
  *"How we made our pre-commit check 7x faster"* via `--incremental
  --noEmit` — caching is essential.
- **chipper** (`github.com/phetsims/chipper/issues/1269`): *"tsc
  without project references and with incremental: true takes around
  3.7 seconds with no code changes"* — incremental caching is the
  pattern.
- **Husky issue 973** (`github.com/typicode/husky/issues/973`):
  *"Prepush hook fails on long running tests"* — the same problem
  on the pre-push side, and people move slow tests OUT.
- **Husky PR 555** (`github.com/christianpeirson/argos-edge/pull/555`):
  *"perf(husky): pre-push eslint scoped + fallow opt-in (kill
  cross-worktree stall)"* — scoping + opt-in is the mitigation pattern.

**The mitigation pattern is git-diff-scoped pre-push, not PreToolUse:**

- **Stack Overflow** (`stackoverflow.com/questions/63663011/run-tests-with-husky-pre-push-only-when-there-are-changes`):
  *"Run tests with husky pre-push only when there are changes"* —
  git diff scoping.
- **lint-staged** pattern (`dev.to/_d7eb1c1703182e3ce1782/git-hooks-with-husky-and-lint-staged-the-complete-setup-guide-for-2025-53ji`):
  scopes checks to staged files only — incremental by construction.

**The smoke-test-as-PreToolUse-hook design is structurally wrong
because:**

1. PreToolUse fires **before** the write, not after. A smoke test on
   un-written code is meaningless.
2. Even with diff scoping, the latency budget is ~5s; integration smoke
   tests routinely take 30s+.
3. The Anthropic 0.4% FP rate (R2) is on classification, not on running
   code — semantic classification is what fits the PreToolUse budget;
   smoke tests don't.

**Carve-out — where smoke testing DOES belong:**

- `~/.grok/hooks/quality_gate.py` already runs post-write smoke tests
  (per `code-orchestrates-model-judges-skill-scale.md:90`).
- `P:/docs/handoffs/.../HANDOFF.md` and `wiki/concepts/hook-script-capability-derivation-receipt-loop-fix.md`
  document the existing post-write smoke pattern.
- The scheduled_checks infrastructure (R3) can run integration smoke
  tests on a daily/weekly cadence, NOT per-PreToolUse.

**Verdict:** confirm defer. The PreToolUse budget cannot accommodate
smoke tests. **Use the existing post-write `quality_gate.py` pattern
for per-write smoke, and the scheduled_checks infrastructure for
periodic integration smoke.** A PreToolUse smoke test hook is the
wrong shape.

**Falsifier:** this verdict is wrong if a future hook needs to
**classify** whether a write will break a consumer (not run the smoke
test). That's R2's territory, not D3's. The classification can fit
PreToolUse; the actual smoke cannot.

### Summary table (for the operator)

| Item | Verdict | Why | Bounded action |
|------|---------|-----|----------------|
| **R1** Neuro-symbolic ordering | CONFIRM current | Embedding (10ms) ≠ LLM (300ms+); IRIS debate doesn't apply at our scale | None — document the discovery correction in the parent concept |
| **R2** Semantic PreToolUse gating | UPGRADE | Anthropic 0.4% FP, Cursor/Dyad/OpenCode all ship it, issue 26862 confirms regex-only has FP problem | Ship `PreToolUse_destructive_command_gate.py` (~100 lines), reuse `intent_classifier.py`, add per-session backstop |
| **R3** Drift detector into `/maintain` | UPGRADE | Integration point already built (Step 2h, `P:/.data/scheduled-checks.json`); Renovate/Dependabot/Dagster all use this pattern | Append 1 JSON entry (~10 lines) |
| **D1** Credential debris | UPGRADE with scope | TruffleHog verifier (FP filter file, active probing) + AWS/Azure last-used timestamps make the distinction achievable | Add verifier-first classification pass (~50 lines) |
| **D2** Runtime task validation | PARTIAL UPGRADE | Model/quota validation is comprehensive; envelope (prompt non-empty, wait_all, lane) is the actual gap | Add 3 envelope checks (~30 lines) |
| **D3** Smoke test in PreToolUse | CONFIRM DEFER | Latency budget violation is structural; not solvable with caching alone | Use post-write `quality_gate.py` for per-write smoke; scheduled_checks for periodic integration smoke |

### Net effect on the parent concept's Workstream C (gating infra)

Original Workstream C prioritized intent-classifier docs (Medium ROI).
After this deep-dive:

- **R2 UPGRADE** moves to HIGH ROI (concrete destructive-command gate
  with empirical FP benchmark).
- **D2 PARTIAL UPGRADE** is a LOW-EFFORT HIGH-VALUE add (30 lines).
- **R1 CONFIRM** removes a planned-but-not-needed work item.

Updated priority (from this deep-dive):

| Workstream | ROI | Why |
|------------|-----|-----|
| R2 destructive-command PreToolUse gate | **High** | Empirical 0.4% FP benchmark + multiple production tools + concrete FP problem in issue 26862 |
| R3 drift-detector scheduled-checks entry | **High** | Zero new infrastructure; one JSON entry; uses existing Step 2h |
| D1 credential debris verifier pass | **Medium** | Bounded, signal-driven, reuses TruffleHog/verifier pattern |
| D2 task envelope check | **Medium** | Bounded, fills an actual gap, doesn't conflict with spawn_model_gate |
| R1 ordering doc only | **Low** | Discovery correction is the deliverable; no code change |
| D3 PreToolUse smoke | **Defer** | Latency violation is structural, not solvable |

### Receipts (this session's claims)

- **"intent_classifier.py is embedding-based, not LLM-based":** read
  `P:/.claude/hooks/shared/intent_classifier.py` lines 1-50 this session.
- **"intent_classifier priority 0.5 < skill_enforcer priority 1.0":**
  read `P:/.claude/hooks/tests/test_intent_classifier_integration.py:78-83`
  this session.
- **"spawn_model_gate validates model/quota only, not envelope":** read
  `C:\Users\brsth\.grok\hooks\PreToolUse_spawn_model_gate.py` lines 1-100
  this session.
- **"/maintain already has Step 2h scheduled-checks infrastructure":**
  read `C:\Users\brsth\.grok\skills\maintain\SKILL.md` lines 309-329
  this session.
- **12 search_web__query calls run this session** (Brave + Exa + DDG
  fused); 10+ results each; multi-backend confirmation on the highest-
  signal results.
- **Anthropic Claude Code Auto Mode 0.4% FP rate:** arXiv 2604.04978
  via `search_web__query` result, snippet directly cited.
- **TruffleHog `falsepositives.go` file exists:** confirmed via Exa
  search result pointing to `github.com/trufflesecurity/trufflehog/blob/9f0b97f1/pkg/detectors/falsepositives.go`.

### New wiki relations (auto-related to add on wiki update)

- anthropic-claude-code-auto-mode-fp-rate — empirical 0.4% FP
  benchmark that backs R2's upgrade verdict
- trufflehog-verifier-pattern-for-credential-debris — D1's
  implementation template
- opencode-auto-mode-escalation-backstop-pattern — R2's required
  safety mechanism for false-positive loops
- scheduled-checks-composable-cadence-pattern — R3's integration
  template (already cited via `maintain/scheduled-checks.json`)
