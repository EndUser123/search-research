---
title: "Portable Think Kernel with Native Front Doors"
created: 2026-08-09
status: proposed_for_cold_start_review
audience: cold-start-llm, solo-director, Grok, Claude Code, Codex, OpenCode maintainers
source: workspace-inspection-and-prior-research
tags: [thinking, reasoning, tp, ultrathink, skill-compression, hooks, mcp, fleet-architecture, cold-start]
verification: design-grounded-local-inspection
confidence: medium
evidence_gaps:
  - No replay corpus yet proves that a compressed TP front door preserves current catch rates.
  - No shadow-mode data yet measures a TP-specific Stop validator's false-positive rate or operator-disablement risk.
  - Claude source contains overlapping reasoning owners and is not active in the current Grok runtime.
  - Cross-host equivalence is a design target, not a verified runtime property.
---

# Portable Think Kernel with Native Front Doors

## Cold-start review instruction

This document is a proposed solution design, not an implementation receipt.
The reviewing LLM must inspect the cited source paths, separate verified facts
from inferences, run the adversarial review in §14, and return a verdict. It
must not edit hooks, skills, plugins, MCP configuration, or defaults as part of
reviewing this document.

The design is for a solo director operating a fleet of AI coders across
multiple hosts. The objective is not to maximize the number of reasoning
features. It is to make the high-value behavior automatic, inspectable, cheap
enough to use routinely, and portable without pretending that the hosts have
the same native runtime.

## 1. Executive decision

Adopt one shared conceptual architecture:

> **Portable Think Kernel + Native Front Doors.**

Keep one user-facing thought-partner front door per host. Put the cross-host
behavior in a small versioned contract and deterministic helper layer. Keep
long reasoning methods as lazy-loaded references. Use existing delegation and
MCP servers for their native jobs. Add no generic sequential-thinking MCP in
phase one. Add only one new hook candidate, a scoped TP result validator, and
start it in shadow or advisory mode.

The design has six domains, not dozens of named skills:

1. **Triage and routing** — classify intent, risk, uncertainty, reversibility,
   ownership, and fanout.
2. **Evidence and discovery** — identify the authoritative source and the
   minimum evidence needed for the claim.
3. **Divergence** — use one or more independent lenses when a fresh framing can
   change the decision.
4. **Convergence** — compare lenses, resolve contradictions, state confidence,
   and select a recommendation.
5. **Execution and verification** — hand implementation to the native host
   execution/orchestration surface and verify the result.
6. **Learning and continuity** — retain only durable, searchable lessons when
   repeated failure demonstrates that memory is valuable.

`reason`, `genius`, `skeptic`, `tot`, `sequential-thinking`, and similar names
become references or lenses inside these domains. They do not each need to be
a top-level skill. `ULTRATHINK` is a native depth trigger or preset, not a
second reasoning architecture and not a magic model switch.

## 2. The proposed architecture

```mermaid
flowchart LR
    U["User intent or native depth trigger"] --> F["Native front door adapter"]
    F --> N["Deterministic normalizer and router"]
    N --> C["Reasoning contract and run manifest"]
    C --> E["Evidence and authority lookup"]
    C --> D["Model judgment: critique, explore, diagnose, decide"]
    D --> X{["Evidence indicates more depth?"]}
    X -->|"no"| S["Converge and emit compact result"]
    X -->|"yes"| L["Add bounded independent lens or verification"]
    L --> S
    S --> V["Deterministic receipt validator"]
    V --> O["Decision, plan, or execution handoff"]
    V -->|"missing receipt"| R["Partial, blocked, or parent review"]
    S -. "only if durable lesson is justified" .-> M["Optional lesson ledger"]
```

The key boundary is:

| Layer | Owns | Must not own |
|---|---|---|
| Native front door | Host-specific invocation, user language, local UX, native depth semantics | A second copy of every reasoning method |
| Deterministic kernel | Parsing, route selection, manifest creation, count checks, schema validation, receipt binding | Substantive judgment or hidden policy that the operator cannot inspect |
| Model | Framing, interpretation, trade-offs, critique, synthesis, meaning | Silent completion, unsupported certainty, authority promotion |
| References | Detailed protocols, examples, lens descriptions, provider notes | Lifecycle registration or mandatory global behavior |
| Hooks | Mechanical lifecycle, authority, mutation, and completion checks | General “think harder” prompting or model spawning |
| MCP | Cross-process tools, durable external state, retrieval, or domain services | Replacing the reasoning model or local parsing |
| Parent/director | Strategy, risk acceptance, integration, final judgment, escalation | Re-deriving every worker's internal reasoning |

This is the **code orchestrates, model judges** pattern at the reasoning-skill
scale. Code controls transitions and receipt shape; the model supplies the
judgment fields that code cannot reliably determine.

## 3. Why this is the right simplification

The current environment has valuable behavior, but it is distributed across
large skills, overlapping Claude plugin sources, host-specific hooks, and
native orchestration features.

### Verified local baseline

- The current Grok `/tp` source is
  `C:/Users/brsth/.grok/skills/tp/SKILL.md`: 1,495 lines and 116,605 bytes at
  inspection time, with 41 files in its directory. It already includes
  semantic intent routing, confidence and horizon depth, explicit lens-count
  overrides, session review, fresh-lens dispatch, verification, falsifiers,
  and output templates.
- The current Grok `/go` source is
  `C:/Users/brsth/.grok/skills/go/SKILL.md`: 779 lines and 60,195 bytes. It
  already treats H1 Think as “ultrathink-class,” makes horsepower packs
  default-on for most non-trivial work, and strips ceremony for sufficiently
  complete delegation packets.
- The current active-surface snapshot at
  `C:/Users/brsth/.grok/active-surface.last.md` says `claude.hooks: OFF`,
  `claude.skills: ON`, and lists the `cc-*` reasoning/thinking suite as
  disabled. The snapshot is the current Grok runtime observation, not proof
  about a separate Claude Code process.
- Codex currently has `model_reasoning_effort = "max"` in
  `C:/Users/brsth/.codex/config.toml`, plus MCP registrations and the native
  `codex-spawn` skill. The Codex orchestration skill already separates model
  identity from reasoning effort and routes low/medium/high/xhigh by task
  shape.
- The project Codex hook file `P:/.codex/hooks.json` imports Claude hook
  modules for `SessionStart` and `UserPromptSubmit`. Copying the same Claude
  hook registrations into Codex would risk double firing.
- The canonical Claude thinking source contains many separate entrypoints and
  the Claude ACA reasoning source contains overlapping hook candidates. The
  scoped preflight receipts record these as `needs_review`, not as proof that
  all candidates are live.

Preflight receipts produced for this design:

| Receipt | Result | Use in this design |
|---|---|---|
| `P:/tmp/cold-start-grok-tp-go-preflight.json` | `proceed_with_discovery`, 21 matches, zero walk errors/conflicts | Grok TP/GO source inventory |
| `P:/tmp/cold-start-think-codex-preflight.json` | `proceed_with_discovery`, 5 matches, zero walk errors/conflicts | Codex reasoning/delegation inventory |
| `P:/tmp/cold-start-think-wiki-preflight.json` | `proceed_with_discovery`, 1,356 matches, zero walk errors/conflicts | Existing design and decision inventory |
| `P:/tmp/cold-start-claude-thinking-preflight.json` | `needs_review`, overlapping hook/reason/TOT candidates | Claude migration constraint |
| `P:/tmp/cold-start-claude-aca-preflight.json` | `needs_review`, overlapping hook/reason/reflect/sequential candidates | Claude migration constraint |
| `P:/tmp/cold-start-claude-hooks-preflight.json` | `blocked` for missing optional module scopes and multiple candidates | Do not claim a single Claude hook owner yet |

### Design inference

The system is not missing reasoning techniques. It is missing a stable
boundary between user intent, depth selection, mechanical orchestration, and
model judgment. Adding more named skills would increase the operator's choice
load and create more routing collisions. A smaller kernel with lazy references
preserves capability while reducing always-loaded context.

## 4. User-facing surface

The operator should remember only three concepts:

| Need | Grok | Claude Code | Codex | OpenCode later |
|---|---|---|---|---|
| Think with challenge or explore | `/tp [question]` | native `ULTRATHINK` or the Claude TP adapter | `$tp [question]` | `tp` adapter |
| Execute a plan or change | `/go [task]` | native implementation workflow | normal Codex task / `$codex-spawn` when warranted | native execution workflow |
| Review a completed result | `/check`, `/review`, or `/tp check` | native review/verification surface | `$review-packet-runner` or native verification | native review adapter |

The operator should not need to remember lens counts, evidence flags,
confidence flags, model flags, or MCP arguments for normal work. The adapter
infers them and records the decision. Explicit arguments remain available for
expert overrides, but the normal path is argument-light.

### Explicit native semantics

#### Claude Code: `ULTRATHINK`

The local Claude `think_trigger.py` implementation treats `ULTRATHINK` as a
depth trigger/profile input. It is not evidence that a different model was
selected, and it is not equivalent to a Grok hook or a Codex reasoning setting.
The adapter should translate it to:

```text
requested_depth = deep
source = native_ultrathink
host_override = true
```

It must retain the observed Claude model/provider identity separately. The
implementation must first resolve which Claude plugin/hook source is
authoritative; the current preflight shows that this is not yet one-to-one.

#### Grok Build: `/tp` and `/go`

Keep Grok’s native `/tp` as the thought-partner front door. Keep `/go` as the
execution front door. Grok `/go` already maps “ultrathink” to the H1/H2 deep
reasoning/plan packs and defaults the relevant packs on for substantial work.
Do not create a second Grok `/reason`, `/genius`, or `/ultrathink` front door
unless it has a distinct evidence contract and outcome measure.

#### Codex

Add one thin `$tp` skill only if the native Codex UX needs a named front door.
It should reuse the shared contract and existing `codex-spawn`, review, and
verification capabilities. It should not add a second worker orchestrator or
ask the user to select a model and reasoning effort for routine work.

The adapter records requested model/effort and host-observed model/effort as
separate fields. It must not claim that a skill changed the host's global
`model_reasoning_effort` setting unless the runtime receipt proves that.

#### OpenCode

Defer the OpenCode adapter until the contract is stable and its actual active
command/plugin/MCP path is inspected. OpenCode should consume the same
contract, not inherit Claude hook assumptions or become a second source of
reasoning policy.

## 5. The six natural domains

### Domain A — Triage and routing

Input: user text, native trigger, current task state, and explicit override.

Output: a small `ReasoningRequest` and a route decision.

The router considers:

- intent: critique, explore, diagnose, decide, execute, verify, reflect;
- risk: low, medium, high, critical;
- uncertainty: low, medium, high;
- reversibility: cheap, costly, irreversible;
- authority/ownership: known, ambiguous, unknown;
- fanout: single artifact, multi-file, multi-agent, fleet/external;
- explicit user depth or lens override;
- available capacity and host constraints.

This is a mechanical routing hypothesis, not a final policy. Initial scoring
can be:

```text
score = risk + uncertainty + irreversibility + fanout + unknown_ownership
```

with each dimension scored 0–2. Suggested initial presets:

| Score / trigger | Preset | Default work |
|---|---|---|
| 0–2, no hard trigger | `light` | Direct answer or small same-agent check; no external lens |
| 3–5 | `standard` | Evidence lookup, one structured critique, compact synthesis |
| 6–10, or any irreversible/fleet trigger | `deep` | Authority discovery, independent lens, falsifier, verification receipt |

The exact thresholds must be tuned against replay fixtures. They must not be
presented as scientifically calibrated numbers in the first implementation.

### Domain B — Evidence and discovery

The kernel should ask, mechanically:

1. Is this a claim about current code/config/runtime state?
2. Is there a local source-of-truth path?
3. Is the state live, cached, generated, historical, or merely proposed?
4. What evidence is required before the model may recommend an action?

Use existing tools selectively:

- `search_wiki` for prior decisions, known failure modes, and durable patterns;
- `context7` for a concrete version-sensitive library/documentation question;
- configured web/search/research MCPs only when the task requests or needs
  external evidence;
- native file and git inspection for local authority.

Do not preload every MCP or make external retrieval a prerequisite for every
TP invocation. That would turn a fast thought-partner request into a research
workflow.

### Domain C — Divergence

The model may use these lenses as references:

| Lens | Question it answers | Default condition |
|---|---|---|
| Critical friend / skeptic | What framing, assumption, or failure mode is being missed? | Standard/deep critique |
| Alternative generation / TOT | What materially different approaches exist? | Architecture or trade-off uncertainty |
| Causal / RCA | What mechanism could produce the observed outcome? | Failure or behavior diagnosis |
| Bayesian / uncertainty | How strong is the evidence and what would change the belief? | Conflicting or sparse evidence |
| Second-order / pre-mortem | What happens after the proposed change? | Costly, irreversible, or fleet-wide change |
| Fresh cross-model lens | Does an independent process disagree? | Deep or explicit independent-review trigger |

These are not six mandatory subagents. A route selects the smallest set that
can change the decision. Independence is recorded by provider/model/family and
actual tool use; agreement alone is not proof.

### Domain D — Convergence

The synthesizer must produce compact judgment fields:

- decision or verdict;
- verified facts;
- inferences and hypotheses;
- evidence references;
- confidence and confidence basis;
- strongest falsifier;
- unresolved contradiction;
- next safe action;
- whether parent/director judgment is required.

It should not emit private chain-of-thought. The design needs inspectable
reasoning outcomes and receipts, not a transcript of hidden internal tokens.

### Domain E — Execution and verification

`/tp` stops at a decision, plan, or review handoff. `/go`, native Codex
execution, or the host's implementation workflow owns writes. Verification is
separate from reasoning and remains mandatory for changed artifacts.

The parent retains strategy, risk acceptance, integration, and final judgment.
Workers stay bounded and return evidence packets. The router may choose zero,
one, or several workers adaptively; it must not impose an arbitrary global
fanout cap without measured quality evidence.

### Domain F — Learning and continuity

Durable learning is optional and selective. A lesson is eligible only when it
is systemic, evidence-backed, falsifiable, abstract enough to reuse, and not
already represented in the wiki. A session-specific observation stays in the
run receipt or handoff.

Do not add a learning ledger merely because one is architecturally attractive.
The existing workspace research found that some ceremony decisions are stable
and mechanically classifiable; they do not require cross-session learning.

## 6. Versioned contracts

The contract is the portable part. It must be small, explicit, and host-neutral.

### `ReasoningRequest v1`

```json
{
  "schema": "reasoning-request.v1",
  "run_id": "tp-20260809-001",
  "intent": "architecture_review",
  "task_summary": "Review the proposed portable thinking architecture",
  "host": {
    "requested": "grok",
    "observed": "grok",
    "front_door": "/tp",
    "runtime_receipt": "active-surface.last.md"
  },
  "risk": "high",
  "uncertainty": "medium",
  "reversibility": "costly",
  "fanout": "fleet",
  "authority": "workspace_source_required",
  "route": {
    "depth": "deep",
    "lenses": ["fresh_critic", "alternatives", "falsifier"],
    "max_parallel": 2,
    "adaptive_expansion": true
  },
  "verification": {
    "required": ["source_receipts", "evidence_classification", "falsifier", "confidence_basis"],
    "status": "pending"
  },
  "overrides": {
    "user_requested": null,
    "native_depth_trigger": null
  }
}
```

Required invariants:

- `requested` and `observed` host identity are separate;
- user/native overrides can raise depth but cannot suppress safety/authority
  checks for a high-risk action;
- `max_parallel` is a budget/policy field, not an instruction to spawn that
  many agents;
- `adaptive_expansion` is evidence-triggered, not a license for an unbounded
  loop;
- a missing runtime receipt produces `unknown` or `needs_review`, not a claim
  of parity.

### `RunManifest v1`

The manifest is a local, atomic, inspectable artifact. It records:

```text
run_id
request_hash
contract_version
created_at
front_door
requested_host / observed_host
requested_model / observed_model
requested_effort / observed_effort
route_decision and route_reason
expected_lenses
dispatched_lenses
returned_lenses
failed_lenses and failure reasons
source_receipts
verification_requirements
status: planned | running | partial | complete | blocked
```

The manifest must not contain raw private reasoning. It may contain compact
model judgments, hashes, paths, and receipt references.

### `ReasoningReceipt v1`

Every load-bearing claim in a deep result should bind to:

```text
claim_id
claim_text
evidence_class: verified_fact | measured_metric | inference | hypothesis | unknown
source_ref
verification_method
confidence
confidence_basis
falsifier
allowed_action
```

For a light result, only the fields required by the route are emitted. The
validator must not force a full architecture-review receipt onto a trivial
question.

## 7. Deterministic defaulting and automatic arguments

### Defaults that are safe to enable

The adapter should automatically supply these when the route requires them:

- evidence classification for claims about current state;
- source-of-truth lookup for code/config/runtime claims;
- a falsifier for load-bearing recommendations;
- confidence plus confidence basis when uncertainty is medium/high;
- an explicit next check when evidence is incomplete;
- model/provider/family identity for independent lenses;
- run manifest and result receipt for multi-agent or deep routes;
- verification before completion for writes or claims of implementation.

These are arguments the user should not have to remember because omission
creates a predictable correctness failure.

### Defaults that should remain conditional

Do not make these globally automatic:

- three or more model lenses on every prompt;
- web, wiki, NotebookLM, or context retrieval on every prompt;
- a full pre-mortem or TOT tree on routine work;
- a Stop block on every response;
- a persistent lesson write on every critique;
- forced context rollover, nagging, or session-ending advice;
- global max reasoning effort for every task solely because it is available.

The rule is **automatic safety and evidence; adaptive depth and cost**.

### Override precedence

1. Explicit safety or authority policy.
2. Explicit user instruction about depth, lens count, or speed.
3. Native host contract (`ULTRATHINK`, `/tp`, `/go`, Codex effort).
4. Deterministic task-shape/risk router.
5. Historical tuning or learned preference.

An explicit `quick` request may reduce optional critique depth, but it cannot
make an unsupported completion claim or bypass a required write verification.
An explicit `deep` request raises the minimum route but does not force a fixed
number of models if capacity or host identity cannot support it.

## 8. Adaptive expansion instead of argument explosion

Use a hybrid strategy:

1. Run a fixed, cheap core: normalize, route, inspect authority, and emit the
   minimum result.
2. Inspect evidence and contradictions.
3. Add only the missing lens or verification step that can change the
   decision.
4. Stop after a bounded number of expansions or when the decision is stable.

Examples of expansion triggers:

| Observed signal | Add |
|---|---|
| Current-state claim has no source receipt | Source-of-truth inspection |
| Two sources disagree | Conflict/authority lens |
| Recommendation changes shared infrastructure | Pre-mortem and reversibility lens |
| Model recommends completion but no bound artifact changed | Verification check |
| Independent lenses agree without independent evidence | Diversity/freshness check |
| User asks “what are we missing?” after a complex session | Session/workspace coverage scan |

This avoids the failure mode where a model first classifies a hybrid problem
into one mode and thereby silently rules out the very cause it needed to test.
It also avoids the opposite failure mode where “adaptive” means every task
re-derives every procedure.

## 9. Host capability map and migration boundary

| Capability | Grok | Claude Code | Codex | Porting rule |
|---|---|---|---|---|
| Thought-partner UX | Native `/tp` | Native adapter around Claude depth/skill surface | New `$tp` skill if useful | Share contract, not command implementation |
| Deep depth trigger | `/go` H1/H2 ultrathink-class packs; `/tp` depth routing | `ULTRATHINK` depth trigger/profile | Native effort plus bounded worker routing | Record requested vs observed values |
| Fresh lens | Existing spawn/codex/agy/pool paths | Native subagent/provider path after activation verification | Native `codex-spawn` | Reuse existing delegation first |
| Evidence retrieval | Active configured wiki/web/context tools | Claude-native tools/MCP after live check | Existing configured MCPs | Trigger by need; do not preload |
| Completion validation | Grok Stop hooks can block, but failures fail open | Claude hook semantics differ | Project hooks may import Claude modules | Thin host adapters, no cross-host hook claim |
| Durable lessons | Wiki/handoff and optional external ledger | Native skill/plugin state | Codex memory/ledger patterns | Add only after repeated failure proves value |
| Execution | `/go` | Claude implementation workflow | Native task / Codex spawn | TP never owns writes |

### Claude-specific migration gate

The Claude source inventory currently contains multiple candidates for
reasoning, sequential thinking, reflection, and hooks. The local wrappers in
`P:/.claude/hooks/UserPromptSubmit_modules` delegate into the
`cc-aca-reasoning` plugin. The plugin router has explicit event lists, while
its `hooks/hooks.json` is empty. The current Grok active surface says the
Claude hook compatibility path is off.

Therefore the first Claude implementation task is not “port the best hook.”
It is a read-only authority map that determines:

1. which file is loaded by the live Claude process;
2. whether the plugin router or the local wrapper is authoritative;
3. whether `cc-skills-thinking` and `cc-aca-reasoning` overlap in the same
   event;
4. which current behavior must be preserved or retired;
5. whether a new shared contract can be inserted without duplicate firing.

Until this gate passes, Claude parity is `proposed`, not `verified`.

### Codex-specific migration gate

The project hook importer already reaches into Claude hook modules for
`SessionStart` and `UserPromptSubmit`. A Codex `$tp` skill must not register a
second copy of those modules. It should call the shared helper directly or
use a Codex-native adapter and record the active route. Existing Codex native
orchestration remains the authority for worker spawning.

### Grok-specific migration gate

Grok hooks support `command` and `http`; `PreToolUse` and `Stop` can block,
while other lifecycle events are passive. Hook failures are fail-open. The
wire format is camelCase, and `Stop` has a session-end observation that must
not be counted as a normal turn. A Claude hook port is not valid merely
because its output vocabulary looks similar.

## 10. Hooks: what is proposed and what is deliberately not proposed

### Reuse existing hooks where their contracts fit

The design reuses existing host mechanisms for:

- spawn/model/quota gating;
- verification receipts;
- claim, uncertainty, and decision-contract checks;
- close/coverage enforcement;
- wiki persistence and source-surface observation;
- active-surface and skill-staleness checks.

The reuse rule is path-specific: a hook is considered reusable only after its
registration, input envelope, output semantics, and live activation are
verified on the target host.

### The one new hook candidate: `Stop_tp_result_validator`

This name describes a proposed role, not an implementation receipt. It would
run only when an explicit TP manifest or `TP_RUN_ID` is present and would
mechanically check:

- expected lens count versus returned plus failed lenses;
- a receipt or explicit failure reason for every claimed lens;
- source/preflight disclosure for artifact-target critiques;
- evidence class and falsifier for every load-bearing finding;
- certainty not exceeding the evidence state;
- `reason == end_turn` so the session-end Stop observation is ignored.

It must not:

- spawn a model;
- call MCP to fabricate missing evidence;
- decide whether the substantive recommendation is correct;
- impose a TP contract on ordinary non-TP responses;
- create a new duplicate-dispatch path.

Rollout:

1. shadow: observe and label would-be blocks;
2. advisory: show one compact correction when the manifest is malformed;
3. blocking only for a measured, explicit TP run with a malformed receipt,
   subject to operator override and host-specific fail-open semantics.

Minimum shadow evaluation: 30 representative TP runs, with false positives,
timeouts, missing-receipt catches, operator overrides, and disablement signals
reported separately. The number is an initial gate, not a claim that 30 runs
proves general correctness.

### Hooks explicitly rejected for phase one

- A global “think harder” `UserPromptSubmit` hook.
- A hook that injects all reasoning profiles into every prompt.
- A new PreToolUse hook that duplicates model dispatch already owned by the
  manifest/helper.
- A hook that blocks because the model did not use a named skill.
- A hook that silently imports all Claude reasoning modules into Grok or Codex.

These would increase friction, create double-fire risk, and make failures
harder to attribute.

## 11. MCP design

### Phase one: no generic thinking MCP

An MCP server is valuable when it provides an external action, resource, or
shared state boundary. It is not automatically valuable because its name says
“thinking.” A generic sequential-thinking server would add another tool loop,
session state, failure mode, and context surface while duplicating the local
TP kernel.

Use existing configured MCP servers by domain:

| MCP role | Why it helps | Automatic policy |
|---|---|---|
| Wiki/search | Prevents repeated rediscovery of durable decisions and failure patterns | Invoke for system/design critiques; disclose unavailable search |
| Current docs | Avoids stale library/API assumptions | Invoke for a concrete version-sensitive question |
| Web/research | Adds external evidence or falsification | Invoke when requested or when the route requires current external facts |
| Domain MCP | Performs a domain action or retrieves domain state | Invoke only when the task has that domain intent |

### Conditional future server: `tp-run-registry`

If multiple hosts or processes need to share live TP runs, the narrowly scoped
candidate is:

```text
resources:
  tp://runs/{run_id}/manifest
  tp://runs/{run_id}/results

tools:
  tp_prepare
  tp_record_lens
  tp_validate
```

Its value would be common run identity, collision-resistant aggregation,
freshness metadata, and structured cross-client results. It would not make
models reason better.

Trigger conditions before building it:

- a reproduced cross-host collision that atomic local artifacts cannot solve;
- a current consumer that cannot safely read the shared filesystem;
- a demonstrated need for concurrent result aggregation;
- a measured benefit larger than the server's auth, availability, schema, and
  lifecycle cost.

Until then, use a local manifest plus atomic result files. A new MCP is
`deferred`, not `rejected forever`.

### Optional learning MCP

If durable lesson retrieval becomes a measured need, a reflection/lesson
server belongs to Domain F, not the thinking kernel. The `rohansx/reflect`
pattern is attractive because its upstream README describes deterministic
error-pattern extraction, agent critique, persistent SQLite/FTS5 memory, and
bounded reflection tools. It should be piloted as a lesson ledger only after
the workspace has a concrete producer/consumer and poisoning/dedup policy.

## 12. External repository research and what to borrow

These repositories are reference evidence, not local runtime proof. Their
README claims should be rechecked before code reuse, and license compatibility
must be reviewed.

| Project | Direct source | Claimed capability relevant here | Design disposition |
|---|---|---|---|
| `deepthinking-mcp` | https://github.com/danielsimonjr/deepthinking-mcp | Current README describes one Claude plugin with an MCP server, slash commands, skills, many modes, session management, proof decomposition, and visual export. Its current raw deprecation note says the project is active again and the plugin split was reversed. | Strong architecture/reference study; too large and overlapping to deploy wholesale in Grok/Codex phase one. |
| `rohansx/reflect` | https://github.com/rohansx/reflect | README describes a Rust MCP for persistent reflections, deterministic error-pattern extraction, agent critique, SQLite/FTS5 search, deduplication, and confidence scoring. | Best candidate for a later bounded lesson-ledger pilot; not a reasoning router. |
| `husniadil/ultrathink` | https://github.com/husniadil/ultrathink | README describes a Python sequential-thinking implementation with confidence, branching, assumptions, and multi-session IDs. | Borrow schema ideas; do not make sequential thought calls globally mandatory. |
| `arben-adm/mcp-sequential-thinking` | https://github.com/arben-adm/mcp-sequential-thinking | README describes staged thinking, revisions/branching, metadata, summaries, and append-only JSONL persistence. | Lightweight persistence reference; local manifest is simpler until a cross-process need exists. |
| `uddhav/creative-thinking` | https://github.com/uddhav/creative-thinking | README describes 28 techniques and a three-tool discovery/planning/execution MCP with local session persistence. | Optional exploration reference; redundant with `/tp explore` for core use. Check GPL-3.0 before reuse. |
| `ckorhonen/reflect` | https://github.com/ckorhonen/reflect | README describes a separate agent-skills pattern for extracting, verifying, and keeping lessons lean. | Useful conceptual reference; do not claim it is a fork or source of `rohansx/reflect`. |

Research uncertainty: several exact MMX queries returned errors or unrelated
results, so direct repository pages/raw primary files were used for the
strongest claims. No repository benchmark proves that adding an MCP improves
this fleet's reasoning quality. The actionable conclusion is architectural:
borrow bounded schemas and durable-state patterns, not feature count.

## 13. Proposed package/file boundary

This is a proposed ownership map for a later implementation wave. It is not
permission to create these files in the review wave.

```text
P:/packages/think-kernel/
  contracts/
    reasoning-request.v1.json
    run-manifest.v1.json
    reasoning-receipt.v1.json
  src/
    route.py              # pure normalization and depth routing
    manifest.py           # atomic manifest/result mechanics
    validate.py           # deterministic receipt validation
    evidence.py           # evidence class and source-reference helpers
  references/
    domains/
      critique.md
      explore.md
      diagnose.md
      decide.md
      reflect.md
      verify.md
  fixtures/
    routing/
    receipts/
  tests/

C:/Users/brsth/.grok/skills/tp/
  SKILL.md                # thin Grok-native front door
  reference/              # lazy-loaded protocols and examples
  __lib/                  # Grok adapter; no substantive judgment

C:/Users/brsth/.codex/skills/tp/
  SKILL.md                # thin Codex-native front door, if accepted

Claude source of truth:
  unresolved until the Claude authority-map gate passes
```

The package should not become a new giant universal skill. Its source code
should be pure, testable, and small. Host adapters should own host-specific
environment variables, hook envelopes, subagent APIs, and tool names. Shared
contracts should not import host internals.

## 14. Cold-start review packet

### Objective

Determine whether the Portable Think Kernel + Native Front Doors design is the
smallest architecture that preserves high-value TP/ultrathink/reasoning
capabilities for a solo director operating Grok, Claude Code, Codex, and
possibly OpenCode.

### Start here, in order

1. `P:/AGENTS.md` — workspace authority, host boundaries, evidence rules, and
   exploration-versus-execution policy.
2. `C:/Users/brsth/.grok/active-surface.last.md` — current Grok activation
   snapshot; do not infer activation from source files.
3. `P:/docs/designs/2026-08-09-portable-think-kernel-native-front-doors-cold-start-review.md` — this design.
4. `P:/.data/wiki/concepts/tp-compression-mcp-hook-boundaries-2026.md` — prior
   one-front-door/no-generic-thinking-MCP decision.
5. `C:/Users/brsth/.grok/skills/tp/SKILL.md` and
   `C:/Users/brsth/.grok/skills/go/SKILL.md` — current Grok contracts; read
   relevant sections first, not the whole TP file by reflex.

Then inspect only as needed:

- `P:/.data/wiki/concepts/adaptive-orchestration-task-shape-classification.md`
- `P:/.data/wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps.md`
- `P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md`
- `P:/packages/.claude-marketplace/plugins/cc-aca-reasoning/__lib/router.py`
- `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`
- `P:/.codex/hooks.json`
- `C:/Users/brsth/.codex/skills/codex-spawn/SKILL.md`

### Review phases

**Phase A — Source and authority check**

- Verify each current-state claim against the source paths.
- Identify any source that is cache, generated state, worktree, historical, or
  disabled.
- Confirm whether the proposed new document path is distinct from existing
  architecture ownership.

**Phase B — Architecture critique**

- Challenge the six-domain boundary.
- Check whether the contract is genuinely host-neutral or merely Grok-shaped.
- Check whether the deterministic router is too policy-heavy.
- Check whether the native front doors preserve the user's low-memory UX.

**Phase C — Constructive red-team**

Try to disprove these load-bearing claims:

1. One front door per host is better than many named reasoning skills.
2. Automatic evidence/receipt defaults improve outcomes without unacceptable
   friction.
3. Existing delegation/MCP surfaces are sufficient for phase one.
4. A scoped shadow validator is safer than a global thinking hook.
5. A local manifest is sufficient before a cross-host registry MCP.
6. Native `ULTRATHINK`, Grok H1, Codex effort, and future OpenCode depth can
   share a contract without claiming semantic equivalence.

For each claim, name an observable falsifier and the smallest experiment that
would distinguish the alternative explanation.

**Phase D — Review verdict**

Return:

```yaml
verdict: ACCEPT | ACCEPT_WITH_CHANGES | REJECT | BLOCKED
decision: one sentence
verified_facts:
  - claim, source path, and verification status
load_bearing_risks:
  - risk, why it matters, falsifier, severity
required_changes:
  - change required before implementation planning
optional_improvements:
  - improvement that does not change the core decision
deferred_items:
  - item and its trigger condition
implementation_authorization: NOT_GRANTED
missing_evidence:
  - evidence needed to upgrade the design
```

The reviewer must not return `ready_for_parent_review` if it has not completed
the source check and adversarial review. A review that finds a real weakness
must update the verdict and required changes rather than preserving the
original recommendation by narrative momentum.

### Copyable cold-start prompt

```text
Review P:/docs/designs/2026-08-09-portable-think-kernel-native-front-doors-cold-start-review.md.
Read P:/AGENTS.md, the current Grok active-surface snapshot, the prior TP
compression decision, current Grok tp/go contracts, P:/.codex/hooks.json, and
Codex codex-spawn before judging. This is read-only review: do not edit code,
skills, hooks, plugins, MCP config, defaults, or git state.

Separate verified facts, inferences, hypotheses, and unknowns. Red-team the
six load-bearing claims in §14, especially host parity, router policy weight,
double-fire risk, validator friction, MCP necessity, and whether one front door
really preserves capability. For each material criticism give a falsifier and
the smallest discriminating experiment. Return the YAML verdict schema in §14
with implementation_authorization: NOT_GRANTED. Do not treat a proposal,
source file, unit test, or disabled plugin as proof of live runtime activation.
```

## 15. Rollout and acceptance plan

### Phase 0 — Design and replay corpus

Status: **not started**.

Build a small, labeled replay corpus from representative TP/GO requests:
routine question, architecture choice, debugging, current-state audit,
fleet-wide change, explicit `quick`, explicit `deep`, failed lens, missing
source, and conflicting source. Preserve the current TP output as the baseline.

Acceptance:

- each scenario has expected intent, minimum evidence, and acceptable route;
- the baseline's high-value catches are identified;
- no claim is made from file size alone;
- the corpus is replayable without live external mutation.

### Phase 1 — Pure contract/helper slice

Implement only versioned schemas, route fixtures, manifest mechanics, and
receipt validation. No host hook changes.

Acceptance:

- deterministic fixtures cover explicit overrides, hybrid tasks, unknown
  ownership, and missing evidence;
- validators distinguish `partial`, `blocked`, and `complete`;
- invalid JSON, stale run IDs, missing lenses, and overconfident certainty are
  detected;
- all outputs bind to the intended run and workspace.

### Phase 2 — Grok front-door compression

Refactor `/tp` in place after replay coverage exists. Move long protocols and
provider notes to references. Move parsing, manifest, count, file discovery,
and telemetry mechanics to helpers. Preserve current variants and disclose
any behavior change.

Acceptance:

- route/variant behavior matches the baseline on the replay corpus;
- the always-loaded SKILL body is materially smaller;
- reference-load failures are visible and do not silently become stronger
  claims;
- light requests do not spawn or retrieve unnecessarily;
- fresh-lens and falsifier catches do not regress beyond an agreed threshold.

### Phase 3 — Codex adapter

Add the thin `$tp` skill only after the contract passes Phase 1. Use native
Codex worker spawning for independent lenses when the decider/budget gates
approve it. Do not copy Claude hook imports.

Acceptance:

- requested and observed model/effort are separately recorded;
- zero-worker, one-worker, and multi-worker routes are all valid;
- parent verification remains the authority;
- no duplicate `SessionStart` or `UserPromptSubmit` hook execution is added.

### Phase 4 — Claude authority-map and adapter

Resolve current plugin/wrapper ownership first. Map `ULTRATHINK` to a depth
preset while preserving native Claude behavior. Do not port Grok hook semantics
or assume the current Grok active snapshot proves Claude activation.

Acceptance:

- one live owner is identified for each Claude reasoning event;
- overlapping candidates are retired, explicitly composed, or marked
  compatibility-only;
- native Claude hook/skill execution is observed on the actual Claude host;
- cross-host claims are backed by host-specific receipts.

### Phase 5 — TP validator shadow

Run the proposed Stop validator in shadow/advisory mode. Measure latency,
false positives, missed malformed receipts, operator overrides, and whether
the hook is disabled. Do not block on an unmeasured policy.

### Phase 6 — Optional lesson ledger

Only if repeated failures show that the wiki/handoff/manifest path is
insufficient, pilot a bounded reflection ledger. Define retention, dedup,
provenance, poisoning defense, deletion, and operator review before enabling
automatic retrieval.

### Phase 7 — OpenCode adapter

Port the contract after the first three hosts have stable receipts. OpenCode
is a native adapter, not a new central policy owner.

## 16. Measurement plan

The design is successful only if it improves outcomes, not merely if it makes
files shorter.

| Dimension | Metric | Initial falsifier |
|---|---|---|
| Operator efficiency | Arguments remembered per task; time to invoke the right front door | Users still need mode/lens flags for common work |
| Context efficiency | Always-loaded tokens/bytes; reference-load rate; route latency | Smaller body causes missing protocol steps or more retries |
| Reasoning effectiveness | Independent-lens catch rate; corrected framing rate; decision reversals | Catch rate falls or agreements are correlated theater |
| Evidence quality | Percent of material claims with valid source receipt/falsifier | Validator passes malformed or unsupported claims |
| Execution quality | Rework, false completion, verification failures | More “complete” claims without verified artifacts |
| Cost | Models spawned, MCP calls, token/time per route | Deep route fires on routine tasks or quotas burn faster |
| Fleet safety | Duplicate dispatch, stale manifest, wrong host/model identity | A worker can claim a route/authority it did not receive |
| Usability | Operator override, disablement, nagging, continuation count | Global friction causes operators to disable the surface |
| Cold-start usability | Time and reads for a new LLM to identify source, route, and next safe action | Reviewer needs chat history or broad grep to understand ownership |

Compare matched scenarios against the current implementation. Do not use
convergence, file size, or number of passing unit tests as a proxy for causal
reasoning improvement. Passing tests prove only the tested helper contract;
they do not prove live host routing.

## 17. Constructive red-team and mitigations

### Risk 1 — The kernel becomes another giant skill

**Attack:** the shared contract accumulates every provider note, mode, and
incident until it recreates the current TP problem.

**Mitigation:** enforce a size budget for always-loaded front doors; put mode
details in references; require a new mode to demonstrate a distinct evidence
contract and outcome measure; reject duplicate aliases.

### Risk 2 — Deterministic routing hides policy

**Attack:** a numeric risk/uncertainty classifier looks objective but encodes
unreviewed policy and misroutes hybrid tasks.

**Mitigation:** expose route reason and input signals in the manifest; keep
thresholds fixture-tested; use adaptive expansion after evidence; allow
explicit user elevation; review ambiguous fixtures with a fresh lens.

### Risk 3 — “Automatic” becomes expensive ceremony

**Attack:** default evidence, lenses, MCP, and validators run on every prompt.

**Mitigation:** automatic only for safety/evidence fields; adaptive fanout;
light route for routine questions; measure added latency and calls; no global
MCP preload or nagging.

### Risk 4 — Independent lenses are not independent

**Attack:** three models from the same family receive the same bundle and
agree for correlated reasons.

**Mitigation:** record provider/model/family, bundle hash, actual tool calls,
and failure state; require diversity only when the route says it can change
the decision; treat agreement as evidence of convergence, not truth.

### Risk 5 — A Stop validator creates closure pressure

**Attack:** the hook blocks repeatedly, fails open silently, or causes the
operator to disable all quality gates.

**Mitigation:** scope to explicit TP manifests, shadow first, cap continuation
behavior, filter session-end Stop events, measure false positives, and keep
substantive judgment outside the hook.

### Risk 6 — Memory becomes a poisoning channel

**Attack:** a model-generated lesson is retrieved later as if it were verified
policy.

**Mitigation:** persist provenance, evidence class, falsifier, source hash,
age, and operator disposition; separate observations from directives; do not
auto-promote lessons into AGENTS or routing thresholds.

### Risk 7 — Cross-host parity is overstated

**Attack:** a shared JSON contract is mistaken for identical `ULTRATHINK`,
Grok H1, Codex effort, or OpenCode behavior.

**Mitigation:** every run records requested and observed host/model/effort;
native adapters own semantics; cross-host equivalence is an acceptance test,
not an assumption.

### Risk 8 — Shared filesystem races invalidate manifests

**Attack:** sibling agents edit the same skill, manifest, hook, or receipt
between inspection and verification.

**Mitigation:** use atomic writes, unique run IDs, content hashes, collision
checks, worktree isolation for implementation, and a fresh active-surface
snapshot before runtime claims.

## 18. Claim ledger

| Claim | Type | Evidence | Verification method | Confidence | Falsifier | Action allowed |
|---|---|---|---|---|---|---|
| Grok `/tp` already contains many high-value reasoning behaviors and is the active front door in the current Grok snapshot. | verified_fact | Current `tp/SKILL.md`, active-surface snapshot | Re-read live path and refresh snapshot before implementation | high for this session | Fresh snapshot routes `/tp` elsewhere | Preserve and refactor in place only after replay |
| Claude `ULTRATHINK` is a depth trigger/profile input, not proof of a model switch. | verified_fact | Claude `think_trigger.py` source and local wrapper | Run a Claude-native test-fire on the actual host | medium until live Claude test-fire | Runtime receipt shows a different native contract | Keep adapter semantics explicit |
| One front door with lazy references reduces operator memory load without removing capability. | inference | TP compression decision, current large TP body, skill/reference boundary | Matched replay plus cold-read test | medium | Catch rate or cold-read performance regresses | Implement only after Phase 0 |
| A deterministic router can safely own parsing and route mechanics while the model owns judgment. | inference | Adaptive task-shape and code-orchestrates wiki decisions | Fixture audit with ambiguous/hybrid prompts | medium | Router decisions cannot be explained or repeatedly misroute | Narrow helper scope |
| A generic thinking MCP is not needed in phase one. | decision | Prior local decision; no demonstrated cross-host collision | Reopen on reproduced collision or consumer need | medium-high for current scope | Local artifacts fail under actual multi-process use | Defer MCP; instrument manifests |
| A scoped TP Stop validator is worth shadow-testing. | hypothesis | Prior decision, existing Grok Stop semantics, receipt gaps | 30-run shadow study with false-positive/disablement metrics | medium-low | High friction, timeout, or low catch rate | Keep advisory/shadow or reject |
| A lesson ledger may improve cross-session continuity. | hypothesis | `rohansx/reflect` pattern and behavioral-reset research | Measure repeated failure recurrence and retrieval precision | medium-low | No repeated failure or memory poisoning | Keep deferred |
| Cross-host parity is not currently verified. | verified_fact | Active surface, host docs, preflight conflicts, separate native contracts | Host-specific runtime test-fire | high | Fresh receipts prove equivalent route and semantics | Use separate adapters |

## 19. Decision summary for the parent/director

Recommended decision: **accept the architecture as a design direction, with
implementation deferred behind replay, host-authority, and shadow-validation
gates.**

The highest-value change is not another reasoning method. It is making the
existing value composable:

- one front door per host;
- one portable request/manifest/receipt contract;
- deterministic routing and validation;
- lazy references for methods;
- native delegation for independent lenses;
- existing MCPs only when their domain is needed;
- no global think-harder hook;
- optional lesson memory only after measured recurrence;
- explicit host and runtime receipts for every parity claim.

The first implementation authorization should be limited to Phase 0: build a
read-only replay corpus and authority map. It should not include hook changes,
MCP installation, default changes, skill deletion, or Claude plugin activation.

## Sources and related workspace artifacts

- `P:/AGENTS.md`
- `C:/Users/brsth/.grok/AGENTS.md`
- `C:/Users/brsth/.grok/docs/user-guide/10-hooks.md`
- `C:/Users/brsth/.grok/active-surface.last.md`
- `C:/Users/brsth/.grok/skills/tp/SKILL.md`
- `C:/Users/brsth/.grok/skills/go/SKILL.md`
- `C:/Users/brsth/.codex/config.toml`
- `C:/Users/brsth/.codex/skills/codex-spawn/SKILL.md`
- `C:/Users/brsth/.codex/skills/codex-spawn/references/thinking-router.md`
- `P:/.codex/hooks.json`
- `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`
- `P:/packages/.claude-marketplace/plugins/cc-aca-reasoning/__lib/router.py`
- `P:/.data/wiki/concepts/tp-compression-mcp-hook-boundaries-2026.md`
- `P:/.data/wiki/concepts/adaptive-orchestration-task-shape-classification.md`
- `P:/.data/wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps.md`
- `P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md`
- `P:/.data/wiki/concepts/behavioral-reset-pattern-reflexion-and-external-critique.md`
- `P:/.data/wiki/concepts/agent-control-plane-enforcement-architectures-2026.md`
- `P:/tmp/cold-start-grok-tp-go-preflight.json`
- `P:/tmp/cold-start-think-codex-preflight.json`
- `P:/tmp/cold-start-think-wiki-preflight.json`
- `P:/tmp/cold-start-claude-thinking-preflight.json`
- `P:/tmp/cold-start-claude-aca-preflight.json`
- `P:/tmp/cold-start-claude-hooks-preflight.json`

