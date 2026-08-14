---
title: "so I don't forget, can we have /go rewrite  the prompt I give it, in the form of a goal, suggest back to me if needed th"
date: "2026-07-02"
mode: "COPILOT"
uuid: "ce30da85-ccd1-4c9a-89a1-dbd70ea3a654"
entry_count: 5
---

## Human

so I don't forget, can we have /go rewrite  the prompt I give it, in the form of a goal, suggest back to me if needed that it use the new written prompt, and then action that if I approve?  or generally improve the prompt so that outcomes are better?

Is go using the custom claude code local model optimally?  it might be via agents or PI?  is it using agy optimally?  Assuming we can identify tasks that it shoudl have vs PI?

does /go have a verification step?  I don't see TDD working.  What else should we improve in it?

## Assistant

Yes: based on the attached `/go` code/doc bundle, you can add a **prompt-rewrite → suggest → approval-gated execution** flow, and it fits the current architecture fairly naturally because `/go` already has explicit task contracts, approval-gated task selection, multiple dispatch paths, and post-run review/QA gates.[1]

## What `/go` already has

`/go` is not just a thin prompt runner; it has an orchestrator, task contract creation/loading, dispatch routing for PI/Claude/local, queue/task selection with approval gating, and several verification/review scripts such as `verify-task.py`, `run-qa-verification.py`, `review-passes.py`, `mutation-gate`, `regression-runner`, and PR artifact gating.[1]

That means your idea is not a greenfield feature. The cleanest approach is to treat “rewrite the prompt into an explicit goal, propose improvements, and wait for approval before action” as an **upstream planning stage** that writes back into the same task contract model rather than bolting on a separate side-channel.[1]

## Prompt rewrite flow

A good target behavior would be:

1. User gives a raw prompt.
2. `/go` rewrites it into a structured goal, constraints, deliverables, verification expectations, and preferred execution path.
3. `/go` shows the rewritten version plus a short rationale for changes.
4. `/go` asks whether to use the rewritten prompt or the original.
5. Only after approval does `/go` create or finalize the active task and dispatch it.[1]

This is structurally compatible with the current system because `create_plan_task`, `loadorcreatetask`, `taskprompt`, and task selection/approval-gating already imply a durable intermediate representation for work before execution.[1]

### Recommended contract additions

Add fields to the task contract such as:
- `original_prompt`
- `rewritten_goal`
- `rewrite_rationale`
- `rewrite_confidence`
- `requires_rewrite_approval`
- `approved_prompt_variant` (`original` or `rewritten`)
- `verification_intent` (what success must prove)[1]

That gives you an audit trail and avoids the common failure mode where “prompt improvement” silently mutates user intent. I would treat silent rewriting as risky; the safer default is **suggested rewrite + explicit approval**, especially given your preference for epistemic traceability.[1]

## Local model, PI, and agy

FACT: the attached material shows explicit dispatch functions for `dispatchpi`, `dispatchclaude`, and `dispatchlocal`, and a `defaultdispatch()` path tied to PI unless overridden by CLI or env. The local path uses adapters for Ollama, LM Studio, and vLLM via `GOLOCALLLM`, but the shown local adapter interface is minimal: `sendprompt(prompt, systemprompt="", maxtokens=4096)` with transcript recording, not a richer agent/tool loop.[1]

FACT: the local LM Studio adapter hits `/v1/chat/completions`, but the resolver sets the model to `"default"` for LM Studio and vLLM-style configs instead of selecting a concrete model in the request payload, which suggests `/go` may be relying on the server-side default rather than intentional per-task model routing.[1]

So no, based on this artifact alone, I would **not** assume `/go` is using the custom local Claude Code model optimally.[1]

### Why it may be suboptimal

- The local dispatch shown is a single prompt/response adapter path, not an agentic loop with tools, retries, decomposition, or verifier interaction.[1]
- There is no obvious task-to-model capability matcher in the local adapter path comparable to the PI tier/model selection tests and resolver scripts present elsewhere in the bundle.[1]
- LM Studio/vLLM appear configured more like generic OpenAI-compatible backends than purpose-specialized execution engines.[1]

### What to improve

You asked whether it may be “via agents or PI” and whether it is “using agy optimally.” From the attached file, I can support only a limited claim: `/go` clearly has multi-dispatch orchestration and PI-specific model-resolution/testing machinery, but I do **not** see evidence in the snippet returned that the local path gets equivalent task-aware orchestration depth.[1]

My working recommendation:

| Task type | Best default | Why |
|---|---|---|
| Ambiguous user intent, planning, decomposition | PI or strongest planning-capable remote path | Better at rewrite, constraint extraction, and deciding execution strategy. [1] |
| Small deterministic code edits in a known repo | Local model or agy worker | Lower cost, faster turnaround, acceptable if guarded by strong verification. [1] |
| Broad refactors, architecture changes, multi-file semantic coordination | PI first, then local implementation if scoped | Higher reasoning burden and more risk of hidden regressions. [1] |
| Tool-heavy verification, review, and gatekeeping | Non-LLM scripts first, LLM second | `/go` already has hard gates and review scripts; those should dominate acceptance. [1] |

If “agy” is intended as the cheaper implementation worker, the optimal pattern is probably **PI for planning/routing/rewrite, agy or local for constrained execution, then scripted verification plus selective high-tier review**. That is consistent with the artifacts showing differentiated dispatch and multiple non-LLM gates.[1]

## Verification and TDD

FACT: `/go` does have verification machinery. The bundle includes `defaultverificationcommands`, `verify-task.py`, `run-qa-verification.py`, `regression-runner.py`, `mutation-gate`, `review-passes.py`, PR artifact fail-closed behavior, and tests asserting verification-related outcomes.[1]

So the issue is likely not “no verification exists,” but rather one of these:

- Verification is optional or weakly inferred for many tasks.
- TDD is not enforced early enough.
- Verification evidence may be post hoc rather than design-driving.
- Dispatch paths may differ in how rigorously they honor the same contract.[1]

### Why TDD may feel absent

The artifact references `defaultverificationcommands()` and tests like `test_prompt_task_gets_default_verification_command` and `test_prompt_task_can_require_explicit_verification`, which suggests verification commands can be attached, but not necessarily that tests are generated or required before edits begin.[1]

That means `/go` may support verification, yet still not behave like true TDD because:
- there may be no mandatory red-green-refactor loop,
- tests may be absent unless the prompt asks,
- and completion may depend more on downstream gates than on up-front executable specs.[1]

## Best improvements

I’d prioritize these changes.

### 1. Add rewrite approval mode
Make it first-class, not incidental:
- `--rewrite=off|suggest|require-approval|auto-for-low-risk`
- persist original and rewritten prompts in task state
- block execution until approval if rewrite materially changes scope or deliverables[1]

### 2. Separate planner from implementer
Use a planner stage to classify:
- task type,
- scope,
- risk,
- suggested dispatch,
- required verification,
- whether local/agy is acceptable.[1]

This is the biggest likely improvement to outcome quality because it prevents the wrong executor from touching the wrong class of task.[1]

### 3. Make verification contract mandatory
Every implementation task should have:
- acceptance criteria,
- verification commands,
- changed-file expectations,
- and failure conditions before execution starts.[1]

If missing, `/go` should stop and ask for clarification or synthesize a proposed verification plan for approval. That is more robust than “best effort verification.”[1]

### 4. Enforce TDD mode explicitly
Add a mode like:
- `--tdd=off|prefer|required`

In `required` mode:
- write or identify tests first,
- run them and observe failure,
- implement,
- rerun tests,
- then run broader regression/review gates.[1]

Without an explicit mode, users often infer TDD from “verification exists,” but that is not the same thing.[1]

### 5. Route local model only for bounded tasks
The local path should probably be allowed only when:
- scope is narrow,
- files are well-bounded,
- acceptance tests exist,
- and rollback/review is cheap.[1]

For open-ended design, refactors, or prompt rewrites, defaulting to PI seems safer unless you can prove the local model performs comparably on those stages.[1]

### 6. Add verifier independence
Use a distinct verifier stage that does not reuse the implementer’s exact prompt framing. `/go` already has several independent scripts and QA artifacts; strengthen that by ensuring acceptance is based on contract evidence, not implementer narrative.[1]

### 7. Add “why this dispatch” artifact
For each run, emit:
- chosen dispatch,
- rejected dispatches,
- complexity/risk score,
- verification plan,
- approval requirements.[1]

That will make it much easier to debug whether PI, local, or agy is being used well.

## My assessment

FACT: `/go` already contains meaningful orchestration and verification primitives, so you do not need to redesign it from scratch.[1]

CONSENSUS: the highest-value improvement is likely **front-loading task clarification and verification specification**, because that improves every downstream executor, whether PI, agy, or local.[1]

SPECULATION, medium confidence: your sense that the local Claude Code model is not being used optimally is probably correct if the current local path is mostly a simple adapter call rather than a fully capability-routed worker with strong task eligibility rules.[1]

### Concrete next step

I would implement this first:

- New preflight mode: `rewrite -> classify -> propose verification -> ask approval -> dispatch`.
- Make it write a structured task contract before any executor runs.
- Add `--tdd=required` and fail closed if no failing test or explicit exempt reason exists.[1]

After that, measure by run artifacts:
- rewrite acceptance rate,
- verification pass rate,
- regression escape rate,
- success by dispatch type,
- and tasks reverted after local/agy execution.[1]

Would you like me to read the attached `go_full.md` more deeply and turn this into a concrete change spec for `/go`, including proposed task-contract schema, CLI flags, and routing rules?

## Human

yes please

## Assistant

Yes — here’s a concrete change spec for `/go` based on the attached implementation. The short version is: add a **preflight planner** that rewrites prompts into a structured task contract, classifies risk and dispatch, proposes verification, and blocks execution until approval when needed; then tighten routing so PI plans, local/agy executes only bounded tasks, and verification becomes explicit rather than incidental.[1]

## Current shape

The current orchestrator already has the right extension points: `loadorcreatetask()` creates the task artifact, `taskprompt()` turns the task contract into the worker prompt, dispatch is split across `pi`, `claude`, and `local`, queue selection already supports approval-gated tasks, and `runcommontail()` runs verification, review, QA, mutation, coverage, and PR artifact generation in sequence.[1]

The main architectural limitation is that prompt intake is still too thin for your goals. For `--prompt`, `/go` mostly stores the raw prompt as `objective`, applies default verification commands if configured, and immediately dispatches; the local path is also much simpler than PI, sometimes even skipping any worker step and just running verification on the current checkout.[1]

## Main design

Add a new **preflight phase** before `task-selected` and before any dispatch. This phase should produce a richer task contract and optionally pause for approval instead of immediately converting raw user text into executable work.[1]

### Proposed flow

1. Receive raw prompt or plan.
2. Run prompt rewrite and task classification.
3. Produce a proposed task contract.
4. Decide whether approval is required.
5. If approved, finalize `active-task-<runid>.json`.
6. Dispatch to PI, local, or agy according to routing rules.
7. Run the existing tail gates, with stricter verification semantics.[1]

This fits the current architecture because the orchestrator already writes blocked artifacts, phase markers, task contracts, and dispatch-result artifacts, so a new preflight phase can be added without changing the overall control model.[1]

## Contract changes

The current `TaskContract` includes `taskid`, `title`, `objective`, `scopein`, `scopeout`, `acceptancecriteria`, `verificationcommands`, `forbiddenfiles`, `source`, and `raw`. That is a solid base, but it does not capture rewrite lineage, dispatch intent, or approval state.[1]

I’d extend it like this:

```ts
type DispatchKind = "pi" | "local" | "agy" | "claude";
type PromptVariant = "original" | "rewritten";
type TddMode = "off" | "prefer" | "required";
type ApprovalState = "not-required" | "pending" | "approved" | "rejected";

interface TaskContractV2 {
  schemaVersion: "go.task-contract.v2";
  runid: string;
  terminalid: string;

  task: {
    id: string;
    title: string;
    objective: string;
    tasktype: "implementation" | "design" | "planning" | "analysis" | "refactor";
    source: "cli" | "plan-md" | "tasks-json" | "rewrite-preflight";

    originalPrompt?: string;
    rewrittenGoal?: string;
    rewriteRationale?: string[];
    approvedPromptVariant?: PromptVariant;

    scopeIn: string[];
    scopeOut: string[];
    assumptions: string[];
    risks: string[];
    acceptanceCriteria: string[];
    verificationCommands: string[];
    forbiddenFiles: string[];

    tddMode: TddMode;
    verificationIntent: string[];
    expectedChangedFiles?: string[];
    maxChangedFiles?: number;

    planner: {
      suggestedDispatch: DispatchKind;
      dispatchReason: string[];
      complexityTier?: "t1" | "t2" | "t3" | "t4";
      confidence?: "low" | "medium" | "high";
      localEligible: boolean;
      agyEligible: boolean;
      requiresApproval: boolean;
      approvalReason?: string[];
    };

    approval: {
      state: ApprovalState;
      requestedAt?: string;
      decidedAt?: string;
      decidedBy?: string;
    };
  };
}
```

This is the minimum schema I’d use to make `/go` explainable and auditable. It preserves your preference for explicit assumptions and makes later routing decisions visible instead of implicit.[1]

### Why these fields matter

- `originalPrompt` and `rewrittenGoal` prevent silent prompt drift.[1]
- `dispatchReason` explains why PI vs local vs agy was selected.[1]
- `localEligible` and `agyEligible` prevent accidental use of a weaker worker on broad tasks.[1]
- `tddMode` and `verificationIntent` make “verification exists” different from actual TDD.[1]
- `approval.state` aligns with the existing approval-gated task-selection behavior already tested in `select-task`.[1]

## CLI changes

Add these flags to `parseargs()`:

```bash
--rewrite off|suggest|require-approval|auto
--approve rewritten|original
--planner-dispatch pi|local|agy|claude|auto
--tdd off|prefer|required
--verify-mode infer|require|require-failing-test
--dispatch-policy auto|force-local|force-pi|force-agy
--preflight-only
--show-task-contract
```

These flags map directly onto current orchestrator behavior patterns: explicit dispatch is already supported, blocked states already exist, and prompt tasks already have verification gating through `GOREQUIREEXPLICITVERIFICATION`.[1]

### Behavioral rules

- `--rewrite=suggest` shows the rewritten contract but does not block unless risk is high.[1]
- `--rewrite=require-approval` always writes a pending approval artifact and exits blocked until approved.[1]
- `--preflight-only` runs rewrite/classification/verification planning and stops before any worker dispatch.[1]
- `--tdd=required` blocks if no test-first path is defined for an implementation task.[1]

## New preflight stage

Create a script such as `scripts/preflight-task.py`. It should run before `loadorcreatetask()` finalizes the active task, or be called from within a refactored `loadorcreatetask()` pipeline.[1]

### Responsibilities

- Rewrite raw prompt into a goal-oriented objective.
- Extract scope, constraints, forbidden files, acceptance criteria, and likely changed areas.
- Propose verification commands and TDD mode.
- Score task complexity and risk.
- Recommend dispatch.
- Emit `task-proposal-<runid>.json`.
- Emit `blocked-<runid>.json` when approval is required.[1]

### New artifacts

Use artifacts consistent with the existing style:

- `task-proposal-<runid>.json`
- `approval-request-<runid>.json`
- `approval-decision-<runid>.json`
- `.preflight-complete-<runid>`
- `.awaiting-approval-<runid>`[1]

That keeps the state machine visible and consistent with existing markers like `.blocked`, `.verified`, `.qa-passed`, and `.pr-ready`.[1]

## Routing rules

The current orchestrator defaults to `pi`, supports `claude` but blocks because there is no automated worker, and has a much thinner `local` path that may only call a local adapter or skip the worker entirely and verify the current checkout.[1]

So the best next step is to stop treating dispatch as just a user override and make it **planner-owned by default**.

### Recommended routing matrix

| Task shape | Default dispatch | Why |
|---|---|---|
| Planning, rewrite, decomposition, ambiguous tasks | PI | PI already has complexity classification and transcript review support; this is the strongest planning path in the current design. [1] |
| Small bounded implementation, narrow scope, existing tests | local or agy | Lower-cost worker is acceptable when strict verification exists and file scope is tight. [1] |
| Broad refactor, API changes, behavioral drift risk | PI plan + local/agy implementation only if bounded | Existing refactor-review and behavioral drift checks imply these tasks are riskier and should start with stronger planning. [1] |
| No verification path, no tests, unclear repo state | blocked pending approval or verification plan | Existing blocked-artifact pattern already supports fail-closed behavior. [1] |

### Local eligibility gate

A task is `localEligible=true` only if all are true:
- `tasktype == implementation`
- `scopeIn` is non-empty
- `forbiddenFiles` defined if repo risk exists
- `acceptanceCriteria` non-empty
- `verificationCommands` non-empty
- `maxChangedFiles` under threshold, for example 5–10
- no major API-surface or cross-module refactor intent[1]

This is consistent with the current codebase’s concern for scope drift, forbidden files, review passes, mutation gates, and regression evidence.[1]

### On agy

I do not see direct “agy” implementation details in the retrieved attachment text, so I cannot claim how it is currently wired. The safest design is to treat `agy` as another bounded executor class with the same eligibility rules as local until proven otherwise.[1]

## Local model assessment

The attached code suggests the local path is **not** yet used optimally for sophisticated tasks. The local adapter interface is only `sendprompt(prompt, systemprompt="", maxtokens=4096)`, the LM Studio adapter calls `/v1/chat/completions`, and the resolver uses generic config forms like `lmstudio:http://localhost:1234` or `vllm:http://localhost:8000`, with `"default"` as the model value for LM Studio and vLLM-style backends.[1]

That means several likely gaps exist:
- no explicit per-task model selection in the local path,
- no transcript tool-event review equivalent to PI’s reviewed JSONL event stream,
- no clear multi-step local worker loop,
- and no strong evidence of local capability matching by task class.[1]

### Concrete local improvements

1. Add `scripts/adapters/local/classifylocal.py` to map task type and complexity to a concrete local model profile.[1]
2. Extend `GOLOCALLLM` to support named model profiles, not just provider endpoint strings.[1]
3. Require local dispatch to write a richer transcript artifact, not just prompt/response JSON.[1]
4. Add a local transcript reviewer analogous to the PI transcript review, checking read-before-write, files touched, and scope adherence.[1]

A better config shape would be:

```bash
GOLOCALLLM=lmstudio:http://localhost:1234#claude-code-fast
GOLOCALPROFILE=bounded-implementation
```

or in JSON:

```json
{
  "provider": "lmstudio",
  "baseUrl": "http://localhost:1234",
  "profiles": {
    "bounded-implementation": {
      "model": "claude-code-local",
      "maxTokens": 8192,
      "allowedTaskTypes": ["implementation"],
      "maxChangedFiles": 6
    }
  }
}
```

The current resolver format looks too thin for optimal routing.[1]

## Verification redesign

`/go` absolutely has verification steps today: `verify-task.py`, `run-qa-verification.py`, `regression-runner.py`, `review-passes.py`, `mutation-gate.py`, `coverage-gate.py`, and fail-closed PR artifact generation are all part of `runcommontail()`.[1]

But that is not the same as strong TDD. Right now, verification appears to be a **downstream gate chain**, not a mandatory up-front execution contract for every implementation task.[1]

### What to add

Add a `verification-plan` stage during preflight that must produce:
- what behavior is being changed,
- how success is observed,
- what tests are expected to fail first,
- what commands prove completion,
- and what evidence artifacts must exist.[1]

### TDD policy

Implement this rule set:

- `tdd=off`: existing behavior.
- `tdd=prefer`: if task is implementation and tests exist nearby, propose test-first and warn if skipped.
- `tdd=required`: block unless one of:
  - new/updated tests are specified first,
  - failing baseline test is recorded,
  - or an exemption reason is approved.[1]

### New artifacts

- `verification-plan-<runid>.json`
- `tdd-receipt-<runid>.json`
- `failing-test-baseline-<runid>.json`[1]

### Gating rule

For `tdd=required`, `runcommontail()` should refuse to proceed to normal verification if the task lacks a TDD receipt or exemption artifact. That is the cleanest way to turn TDD from aspiration into policy.[1]

## Specific code changes

Here is the concrete implementation order I’d use.

### 1. Refactor `loadorcreatetask()`
Change it from:
- raw prompt → active task

to:
- raw prompt → preflight proposal
- proposal → approval decision
- approval → active task[1]

Pseudocode:

```python
def loadorcreatetask(args, statedir, runid):
    draft = build_task_draft(args, statedir, runid)
    proposal = run_preflight(draft, statedir, runid, args)

    if proposal.requires_approval and not has_approval(args, statedir, runid):
        write_approval_request(statedir, runid, proposal)
        write_blocked(statedir, runid, phase="preflight", reasoncode="approval_required")
        return None

    task = finalize_task_contract(proposal, approval=get_approval(...))
    write_active_task(statedir, runid, task)
    return TaskContract.from_activetask(task)
```

This follows the same fail-closed style as existing blocked reasons like missing verification commands or worktree creation failure.[1]

### 2. Replace `taskprompt()`
The current `taskprompt()` serializes title, objective, acceptance criteria, verification commands, scope, and forbidden files into a prompt. Extend it so workers receive:
- approved prompt variant,
- assumptions,
- explicit non-goals,
- verification intent,
- and dispatch rationale.[1]

That will improve local and PI worker behavior without changing the worker protocol dramatically.

### 3. Add local transcript review
PI dispatch currently runs transcript review and can block on warnings like `BLINDWRITE`, `FORBIDDENFILE`, and `NOFILESWRITTEN`. The local path should gain an equivalent review artifact before being considered coded/eligible for downstream gates.[1]

### 4. Tighten local skipped-worker mode
The current tests show local dispatch can intentionally skip any worker and still run verification against the current checkout. That is useful for “verify only,” but risky as a default implementation path.[1]

So split local mode into:
- `local-exec`: local model edits or proposes changes.
- `local-verify`: no worker, verification-only.[1]

Do not let `local-verify` masquerade as implementation.

## Suggested policy defaults

These are the defaults I’d recommend.

| Setting | Default | Reason |
|---|---|---|
| `rewrite` | `suggest` | Improves prompt quality without over-blocking. [1] |
| `tdd` | `prefer` | Moves behavior toward test-first without breaking all workflows immediately. [1] |
| `verify-mode` | `require` | Implementation tasks should always have explicit verification commands. [1] |
| `dispatch-policy` | `auto` | Planner should own executor choice. [1] |
| high-risk approval | on | Broad refactors or ambiguous prompts should not dispatch automatically. [1] |
| local eligibility | strict | Local path is currently thinner and should stay bounded. [1] |

## Tests to add

The existing test suite already covers dispatch defaults, explicit verification requirements, approval-gated selection, local skipped-worker behavior, PI transcript review signals, mutation gates, and QA verdict handling.[1]

Add tests for:

- prompt rewrite creates `task-proposal` artifact,
- rewrite approval blocks until explicit approval,
- approved rewritten prompt becomes the worker prompt,
- planner routes ambiguous tasks to PI,
- planner blocks local dispatch for broad refactors,
- `tdd=required` blocks without failing-test evidence,
- local transcript review blocks blind writes,
- `local-verify` cannot claim implementation success artifacts.[1]

These would fit naturally beside `test_orchestratedispatch.py`, `test_pireviewtranscript.py`, and `test_selecttask.py`.[1]

## Priority order

I would implement in this order:

1. Preflight rewrite + approval artifacts.[1]
2. Richer task contract v2.[1]
3. Planner-owned dispatch recommendation.[1]
4. Verification-plan artifact and `tdd` policy.[1]
5. Local transcript review and local eligibility gate.[1]
6. Per-profile local model routing.[1]

That order gives the biggest outcome improvement early, because better task definition and verification planning improve every executor, including PI and any future agy path.[1]

## My bottom assessment

FACT: `/go` already has stronger orchestration and verification primitives than a typical prompt-to-code wrapper, including explicit task contracts, approval-gated selection, dispatch separation, transcript review for PI, and a substantial post-run gate chain.[1]

FACT: the biggest missing piece is **pre-dispatch rigor**: prompt rewrite, approval-aware goal formation, dispatch justification, and explicit verification/TDD planning are not yet first-class in the current `--prompt` path.[1]

SPECULATION, medium-high confidence: if you add the preflight planner and restrict local/agy to bounded tasks with strong verification contracts, you will likely see better consistency than trying to “make the local model smarter” first, because the current main failure mode appears architectural rather than purely model-quality related.[1]

Would you like the next step to be a **patch plan mapped to files/functions** in `go_full.md`, or a **proposed v2 JSON schema and CLI contract** you can drop into the repo docs first?

## Human

search other repos related to this topic to see if there's useful ideas to take.  note that all our solutions should be multi terminal isolated and immune to stale data, when that makes sense.  sometimes we need shared data between terminals but that's rare.

## Assistant

I found several useful external patterns, and the strongest ones align with your constraint: **default to per-terminal/per-run isolation, treat shared state as exceptional, and design recovery around stale-state resistance rather than optimistic coordination**. The most relevant ideas came from worktree-based parallel orchestration guidance, OWASP’s agent isolation guidance, and larger orchestration systems like Optio that use isolated execution environments plus reconciliation loops.[1][2]

## Best ideas

The most directly reusable idea is **one isolated execution context per task/agent**, usually a separate worktree or pod, with explicit status artifacts and a merge/review phase instead of shared mutable in-place coordination. The parallel-worktrees guide says true parallelism requires separate Claude processes in different worktrees, recommends one worktree per background agent, non-overlapping file assignments, a status file convention, and explicit result handoff through files like `RESULTS.md`.[2]

OWASP’s multi-agent isolation guidance pushes in the same direction at the security and correctness layer: agents should operate within their own context windows with no shared-state bleeding across boundaries, and credentials should be ephemeral and task-scoped. That supports your “shared state only when rare and intentional” rule, and it strengthens the case for terminal-scoped run identity and state directories instead of ambient global caches.[1]

## Repos worth studying

Here are the most useful repos or documents from this pass.

| Source | Useful idea | Relevance to `/go` |
|---|---|---|
| OWASP AISVS multi-agent isolation | No shared state bleeding; task-scoped boundaries and ephemeral credentials. [1] | Strong conceptual backing for terminal isolation and fail-closed state access. [1] |
| SpillwaveSolutions/parallel-worktrees | One worktree per agent, explicit status files, explicit result summaries, avoid overlapping file assignments, use separate terminals for real parallelism. [2] | Very close to your current `/go` model; easy to borrow conventions. [2] |
| jonwiggins/optio | Isolated repo/job pods, worktree-per-task execution, autonomous feedback loop, and a reconciliation control plane that uses periodic resync so runs do not get stuck on lost events. [1] | Best source for stale-data immunity and resumable orchestration ideas. [1] |
| Anthropic Claude Code issue on parallel task/worktree orchestration | Proposed `/fork`-style background task model with separate worktrees and headless agents. [3] | Helpful for UX and command design, though it is an issue proposal, not a production implementation. [3] |
| Nous Research Hermes issues | Isolated child agents, async human approval gates, and independent acceptance-criteria verification ideas appear in issues. [4][5][6][7] | Useful conceptually, but lower-confidence than implemented repos because these are issue threads rather than stable code. [4][5][6][7] |

## What to borrow

For `/go`, I would borrow these patterns first.

### 1. Terminal-scoped state roots
Your current bundle already has strong run-context recovery behavior and per-terminal current-run handling, which is good. The external repos reinforce that this should stay the default: one terminal should resolve to one current run, one state dir, one active task lineage, and no silent fallback to unrelated shared state.[2]

Concrete rule:
- default state lookup order should remain terminal-specific first,
- stale global artifacts should never outrank terminal-local active state,
- and any shared/global registry should be read-only advisory metadata unless explicitly requested.[2]

### 2. Explicit coordination files
The parallel-worktrees repo uses `.agent-status/*.json`, `.agent-tasks/`, and `RESULTS.md` as the contract between orchestrator and workers. That is worth stealing because it is simple, inspectable, and robust against context loss.[2]

For `/go`, use:
- `task-proposal-<runid>.json`
- `approval-request-<runid>.json`
- `verification-plan-<runid>.json`
- `dispatch-selection-<runid>.json`
- `worker-result-<runid>.json`
- `review-verdict-<runid>.json`[2]

These should be **append-only or versioned per run**, not overwritten shared files.

### 3. Reconciliation loop, not event trust
Optio’s strongest idea is the reconciliation control plane: pure decision plus CAS-style execution with periodic resync so the system does not get stuck on lost events. That is exactly the right mindset for stale-data immunity.[1]

For `/go`, this implies:
- never assume a previous phase marker still reflects reality,
- re-derive truth from artifacts and filesystem state,
- periodically recompute run status from evidence,
- and make all phase transitions idempotent.[1][2]

This is better than “set flag once and trust it forever.”

### 4. Shared state only as a coordination bus
The parallel-worktrees repo uses shared status files only for orchestration, not as a shared mutable working memory. That distinction matters. Shared state can exist, but it should be:
- sparse,
- append-mostly,
- namespaced by run/task,
- and never a live scratchpad for multiple terminals.[2]

That matches your note that shared data is occasionally needed but should be rare.

## What not to copy blindly

Some external patterns are useful but should be adapted.

- The parallel-worktrees status hub is helpful, but a plain shared `.agent-status/` directory can still become stale if status files are overwritten without leases, epochs, or heartbeat semantics. Add monotonic timestamps, writer identity, and state-version numbers if you adopt it.[2]
- Optio’s cluster-scale control plane is powerful, but `/go` probably does not need Kubernetes-style infrastructure just to get the core reliability ideas. Borrow the reconciliation and idempotency principles, not the whole deployment model.[1]
- GitHub issue threads proposing async approvals and auto-forking are good inspiration, but they are lower-authority than implemented code. Treat them as design prompts, not proof.[3][5][7]

## Recommended `/go` architecture rule

I’d formalize this as the default policy:

- **Isolation default:** every terminal gets its own active run context; every autonomous worker gets its own worktree or equivalent isolated workspace.[2]
- **Shared state exception:** shared artifacts are allowed only for orchestrator-visible summaries, approvals, or completion signals, and must be namespaced per run/task.[2]
- **Stale-data defense:** all orchestrator decisions must be recoverable from durable evidence; no single mutable “current state” file should be authoritative by itself.[1][2]
- **Recovery model:** when artifacts disagree, prefer the most recent evidence tied to the current terminal/run lineage, otherwise fail closed and request rebind/approval.[2]

## Concrete improvements for `/go`

Based on both your code bundle and these external references, I’d add the following.

### State isolation
- Keep per-terminal `current-run` files.
- Add `state-owner`, `epoch`, and `last-heartbeat` to active run/task artifacts.
- Reject cross-terminal writes unless the task is explicitly marked shared.[2]

### Shared-state safety
- Introduce a dedicated shared coordination folder, for example `.claude/shared/coordination/`, but only for:
  - approval decisions,
  - parent-child orchestration summaries,
  - merge-ready notifications.[2]
- Everything else stays in terminal/run-scoped state.[2]

### Reconciliation
- Add a `reconcile-run.py` step that recomputes run truth from:
  - active task artifact,
  - dispatch result,
  - verification artifacts,
  - worktree existence,
  - review verdicts,
  - heartbeat freshness.[1][2]

### Background worker contract
Borrow directly from the worktree guide:
- each worker writes a structured result file,
- each worker writes a human-readable summary,
- completion is signaled only after commit/evidence write,
- and file assignment boundaries are explicit.[2]

### Approval and verification
The Hermes and parallel-worktrees material reinforces your instinct that independent verification matters. So keep the implementer separate from the verifier whenever feasible, ideally with fresh context.[6][7][2]

## My recommendation

The single best external idea to import is **Optio’s reconciliation mindset**, combined with **parallel-worktrees’ one-worktree-per-agent and explicit file-based coordination**. Together, those give you a lightweight design that is multi-terminal isolated by default and much more resistant to stale state than a shared-memory or shared-file-first architecture.[1][2]

FACT: the outside material supports your current instinct that terminal isolation should be the default and shared state should be rare, explicit, and tightly scoped.[1][2]

SPECULATION, high confidence: if `/go` adopts terminal-scoped run ownership, per-worker worktree isolation, append-only coordination artifacts, and a reconciliation pass that derives truth from evidence instead of trusting stale markers, it will avoid a large class of cross-terminal corruption and stale-state bugs more effectively than adding more prompt complexity alone.[1][2]

Would you like me to turn this into a **concrete `/go` design addendum** with proposed directory layout, artifact schemas, and stale-state resolution rules?

## Human

Here's some feedback from the target LLM.  I not sure if they actually were helpful: "
● Direct answer: directionally yes — the missing piece is real — but this spec is ~5× bigger than the smallest durable change, and I'd want
  to read orchestrate.py / select-task.py before committing to the v2 contract migration.

  The pasted LLM output is a hypothesis list, not authority. Before endorsing, three claims deserve a Read test:

  1. "The local path may only call a local adapter or skip the worker entirely" — verifiable in scripts/dispatch_local.py. If true, that's
  the #1 architectural smell.
  2. GOREQUIREEXPLICITVERIFICATION exists — verifiable in orchestrate.py arg parsing.
  3. TaskContract field names — verifiable; the spec's proposed v2 doesn't actually conflict if these fields are additive (new keys, old
  keys still work). That's the cheapest path.

  ---
  What is going wrong

  /go's prompt→dispatch→gate pipeline is sound, but the intake is too thin: raw --prompt becomes objective and dispatches without an
  explicit intermediate contract. PI/local/agy then receive prompts of wildly different quality. The downstream gate chain catches failure
  but cannot prevent wasted runs.

  Best happy path — recommendation

  Ship a 2-file, no-schema-change first patch:

  1. scripts/preflight_propose.py — new script: rewrites --prompt → writes task-proposal-<runid>.json (with originalPrompt, rewrittenGoal,
  suggestedDispatch, localEligible, requiresApproval). Pure file I/O. No orchestrator changes yet.
  2. --preflight-only flag on /go — runs the proposal script and exits 0 with a one-line summary. Lets you inspect rewrites on real prompts
  without touching dispatch.

  Why this, not the full spec:
  - Reversible: zero contract migration, zero dispatch change.
  - Testable: you get real rewrites on real prompts before committing to a v2 schema.
  - The pasted spec's 6 priority items collapse to 2 architectural chunks: (A) preflight + contract v2 + planner-owned dispatch, (B)
  verification-plan + TDD policy. A needs the rewrite loop running first; B is downstream and can wait.

  What this prevents next time

  Shipping a 5-artifact v2 contract schema before anyone has inspected 20 real preflight rewrites. The schema should be informed by the
  actual rewrite distribution, not designed in advance.

  Reversal / rollback

  If the rewrite loop produces nothing useful in 20 real prompts: delete scripts/preflight_propose.py and the flag. Two-file change, no
  rollback cost.

  ---
  What I need before endorsing the v2 schema migration (read next):
  - scripts/orchestrate.py → TaskContract shape + loadorcreatetask() + taskprompt()
  - scripts/select_task.py → confirm approval-gated path
  - tests/test_select_task.py → confirm approval-gating is exercised

  Want me to read those three and report which spec claims are confirmed vs. invented? Or do you want a different first patch scope?"

I like your ideas.

## Assistant

Your target LLM’s feedback is mostly **good and corrective**. The most important part is that it challenged the larger design before endorsing it, and on the concrete claims it asked to verify, the attached bundle confirms those claims are real rather than invented.[1]

## Confirmed claims

These three checks are supported by the attached code.

1. The local path really can skip the worker entirely. In `dispatchlocal()`, if `GOLOCALLLM` is not set, `/go` writes a `dispatch-result` with status `skipped-worker`, marks `worktree-ready`, `dispatched`, and `coded`, and then runs verification against the current checkout.[1]

2. `GOREQUIREEXPLICITVERIFICATION` is real. In `loadorcreatetask()`, prompt-based tasks are blocked with `reasoncode: missingverificationcommands` when `GOREQUIREEXPLICITVERIFICATION=1` and no explicit default verification commands are present.[1]

3. The current `TaskContract` is small and additive extension is the cheapest path. The dataclass fields are `taskid`, `title`, `objective`, `scopein`, `scopeout`, `acceptancecriteria`, `verificationcommands`, `forbiddenfiles`, `source`, and `raw`, so adding proposal-side artifacts or extra JSON keys is much cheaper than forcing an immediate contract migration.[1]

So on factual grounding, the target LLM was right to demand verification first, and the repo confirms the core architectural smell: the local dispatch path is indeed thinner and can represent “coded” without any worker edit phase.[1]

## Where its advice is strongest

Its best point is **sequencing**: do not commit to a large v2 contract before observing real preflight outputs on real prompts. That is a sound product-design instinct, because the current system already has working task selection, run context recovery, approval-gated queue semantics, and gating infrastructure, while the intake path is the weakest part.[1]

I agree with its recommendation to start with a **small, reversible preflight patch**:
- one new proposal script,
- one new flag such as `--preflight-only`,
- no dispatch behavior changes yet,
- no schema migration yet.[1]

That fits your preference for minimal, evidence-led change much better than jumping directly to a full planner-owned architecture.

## Where I would refine it

I would adjust one thing: “2-file patch” is the right spirit, but probably **not literally enough** unless you count tests separately. If you add `scripts/preflight_propose.py` and `orchestrate.py` support for `--preflight-only`, you should also add at least focused tests for:
- proposal artifact creation,
- no-dispatch exit behavior,
- terminal/run isolation semantics for proposal output.[1]

So I’d frame the smallest durable change as:
- 1 new script,
- 1 orchestrator modification,
- 1 test file or additions to existing dispatch tests.[1]

That is still very small, still reversible, and much safer.

## Best next patch

I’d now recommend this as the actual phase-1 change.

### Phase 1: proposal-only preflight
Add `scripts/preflight_propose.py` that:
- accepts the prompt plus current run context,
- writes `task-proposal-<runid>.json`,
- includes only additive fields such as `originalPrompt`, `rewrittenGoal`, `suggestedDispatch`, `localEligible`, `requiresApproval`, `verificationSuggestions`, and `notes`,
- never mutates `active-task-<runid>.json`.[1]

Add `--preflight-only` to `parseargs()` so `/go`:
- creates/resolves terminal/run state as usual,
- runs proposal generation,
- writes a phase marker such as `.preflight-proposed-<runid>`,
- exits without dispatch or tail gates.[1]

This is the best first move because it gives you real data on rewrite quality while preserving the current multi-terminal safety model and avoiding stale shared-state expansion.

## Multi-terminal constraint

Your added constraint matters: any proposal system should remain **terminal-scoped and stale-safe by default**. The proposal artifact should live in the same run-specific state directory as the rest of the run artifacts, not in a shared global suggestion cache. That preserves the current run-context model, which already recovers run identity from disk and writes terminal-specific `current-run` state.[1]

So for phase 1:
- no shared proposal registry,
- no cross-terminal reuse by default,
- no “latest proposal” global file,
- proposal path keyed by `runid` and terminal-resolved `statedir`.[1]

If you later want shared proposal visibility, make it an explicit summary/export step, not the source of truth.

## What to inspect in 20 real prompts

The target LLM was also right that the schema should be informed by real rewrite distribution. I’d inspect these dimensions across at least 20 prompts:

- Did the rewrite materially improve objective clarity?
- Did it preserve user intent?
- Did it infer useful scope and forbidden files, or hallucinate them?
- Did it over-recommend PI/local?
- Did it produce actionable verification suggestions?
- Did it identify ambiguous prompts that should require approval?[1]

Only after that should you decide whether `rewrittenGoal`, `verificationIntent`, and `suggestedDispatch` belong inside the main task contract or remain proposal-only artifacts.

## My updated recommendation

So I’d combine both positions:

- Keep my larger architecture as the **likely destination**.
- Follow the target LLM’s advice for the **first implementation step**.[1]

That means:

1. Do **not** start with a full v2 migration.
2. Start with a proposal-only preflight.
3. Keep all artifacts terminal/run isolated.
4. Review a real sample set.
5. Then decide whether to:
   - add approval gating,
   - move proposal fields into the contract,
   - and make dispatch planner-owned.[1]

## Net assessment

FACT: the target LLM’s verification-oriented critique is supported by the repo, especially on local skipped-worker behavior, explicit verification gating, and the small current `TaskContract`.[1]

CONSENSUS: the smallest durable improvement is a **proposal-only preflight** that rewrites prompts and suggests verification/dispatch without changing execution semantics yet.[1]

SPECULATION, high confidence: if you jump straight to a v2 contract and planner-owned dispatch before sampling real preflight outputs, you increase design risk unnecessarily; a proposal-only first patch will likely give you most of the learning at a fraction of the implementation cost.[1]

I’d make the next step a concrete **phase-1 patch spec** for:
- `scripts/preflight_propose.py`,
- `orchestrate.py --preflight-only`,
- artifact schema,
- and 5–8 focused tests.

## Human

please give me the prompt for the target LLM to implement.

## Assistant

Use this prompt. It asks for the **smallest durable phase-1 patch**, keeps multi-terminal isolation and stale-data safety explicit, and tells the target LLM to verify the repo before changing anything.

```text
You are implementing a minimal, reversible phase-1 improvement to `/go`.

Goal:
Add a proposal-only preflight flow for prompt intake, without changing dispatch semantics yet.

Important constraints:
- Read the existing code first and verify assumptions from the repo before implementing.
- Optimize for the smallest durable change, not the largest architecture.
- Preserve existing multi-terminal isolation behavior and stale-data resistance.
- Shared cross-terminal state should be avoided unless absolutely necessary.
- Prefer additive changes over schema migrations.
- Do not break existing task selection, dispatch, or verification flows.

Repo facts already observed and should be confirmed in code:
- `scripts/orchestrate.py` currently turns `--prompt` into a thin task where `objective = raw prompt`. [file:1]
- `dispatchlocal()` can skip the worker entirely when `GOLOCALLLM` is not set and still mark coded/dispatched before verification. [file:1]
- `GOREQUIREEXPLICITVERIFICATION=1` blocks prompt tasks without explicit verification commands. [file:1]
- `runcontext.py` already has terminal-scoped run resolution and disk-authority recovery semantics intended to resist stale state. [file:1]

Implement ONLY phase 1:

1. Add a new script:
   `scripts/preflight_propose.py`

2. Add a new CLI flag to `/go`:
   `--preflight-only`

Behavior required:
- When `--preflight-only --prompt "..."` is used, `/go` should:
  - resolve run context exactly as it normally does,
  - create/use the normal terminal-scoped `statedir` and `runid`,
  - generate a proposal artifact,
  - write a phase marker,
  - print a short one-line success summary,
  - exit without dispatching any worker,
  - exit without running verification / QA / mutation / PR gates.

Do NOT:
- do a task contract v2 migration,
- change current dispatch routing,
- change approval gating behavior,
- mutate `active-task-<runid>.json` for preflight-only runs,
- introduce shared/global proposal state,
- introduce cross-terminal coupling.

Proposal artifact:
Write:
- `task-proposal-<runid>.json`

The artifact should be additive and lightweight. Suggested JSON shape:

{
  "runid": "...",
  "terminalid": "...",
  "source": "cli-preflight",
  "originalPrompt": "...",
  "rewrittenGoal": "...",
  "suggestedDispatch": "pi|local|claude",
  "localEligible": true,
  "requiresApproval": false,
  "verificationSuggestions": ["..."],
  "notes": ["..."],
  "generatedAt": "ISO-8601"
}

Requirements for proposal generation:
- Keep logic simple and deterministic.
- Rewrite the prompt into a clearer goal-oriented form.
- Suggest dispatch conservatively:
  - prefer `pi` when prompt is ambiguous, broad, or architectural,
  - allow `local` only for narrow implementation-style prompts,
  - do not invent `agy` unless it already exists in code and is actually wired.
- `localEligible` should default to false unless the prompt clearly looks like a bounded implementation task.
- `requiresApproval` should default to true only when the rewrite materially narrows/changes intent or the request is broad/ambiguous.
- `verificationSuggestions` can be heuristic strings only; do not wire them into the main task contract yet.

Integration details:
- Add `--preflight-only` to `parseargs()` in `scripts/orchestrate.py`.
- Keep normal behavior unchanged when the flag is absent.
- For `--preflight-only`, support at least the `--prompt` path.
- If `--preflight-only` is used without `--prompt`, either:
  - fail clearly with a small blocked artifact and non-zero exit, or
  - support `--plan` too if it is genuinely cheap.
Choose the smallest clean option and explain it in your summary.

State / isolation rules:
- All artifacts must be written into the existing run-scoped, terminal-scoped `statedir`.
- No global “latest proposal” file.
- No shared cache across terminals.
- Reuse existing `runcontext` / `ensureruntimeenv()` behavior rather than inventing a second run identity system.
- Avoid stale-data hazards: do not read or overwrite unrelated run artifacts.

Suggested additional phase marker:
- `.preflight-proposed-<runid>`

Testing:
Add focused tests only. Prefer extending the existing orchestrator tests if that is cheaper.
Please add tests for:
1. `--preflight-only --prompt` writes `task-proposal-<runid>.json`.
2. It does not call dispatch or `runcommontail()`.
3. It preserves terminal/run scoped state behavior.
4. Normal non-preflight behavior is unchanged.
5. If you choose to error on invalid flag combinations, test that too.

Implementation approach:
- Read first:
  - `scripts/orchestrate.py`
  - `scripts/runcontext.py`
  - existing orchestrator tests
- Then implement the smallest patch.
- Keep code style aligned with the repo.
- Prefer additive helpers/functions over large refactors.

Deliverable format:
1. First, briefly state which repo assumptions you verified.
2. Then implement the patch.
3. Then list changed files.
4. Then summarize why the change is minimal and reversible.
5. Then mention any follow-on phase-2 ideas, but do not implement them.

Non-goals for this patch:
- planner-owned dispatch
- approval workflow
- task contract migration
- TDD enforcement
- local transcript review redesign
- shared coordination bus

If something in this request conflicts with the repo’s actual structure, follow the repo and explain the mismatch before coding.
```

Why this prompt is a good fit: it targets the **small reversible patch** rather than the full redesign, aligns with the repo’s existing terminal-scoped run recovery and task flow, and explicitly avoids introducing shared stale-prone state.[1]

Two small notes:
- I intentionally left `agy` out of the required implementation path because I do not have confirmed evidence from the attached bundle that it is currently wired into dispatch.[1]
- I also constrained preflight phase 1 to proposal artifacts only, because the current code already has enough moving parts that changing `active-task` semantics too early would raise rollback cost.[1]
