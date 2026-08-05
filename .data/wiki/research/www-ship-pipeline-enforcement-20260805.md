# Ship Pipelines for AI Coding Agents — How Practitioners Actually Enforce Review → Fix → Verify → Merge

Research date: 2026-08-05. Tools searched: DDG (via `ddgs_search.py`), `web_fetch`, GitHub repository browsing. Sources cited inline with absolute URLs.

---

## Executive answer (TL;DR)

Three patterns dominate what practitioners report actually working. They are layered, not alternatives:

1. **Mechanical enforcement via hooks (PreToolUse + Stop) that physically block tool calls.** The LLM is not asked to "remember to run review"; the OS-level hook either denies the write/finish or the session continues. This is the dominant, evidence-backed pattern.
2. **Engine-agnostic deterministic gate CLIs/protocols** (e.g., `mergegate`, `agents-shipgate`) that sit in front of any coding agent and enforce a state machine for register → impact → assign → branch → PR → merge. The agent cannot merge; the gate merges.
3. **Multi-agent adversarial validation** — the writer cannot grade its own work. Review agents run in fresh context, produce typed verdicts with evidence, and the aggregate verdict decides merge/recover/escalate.

A phase state machine (DEFINE → DISCUSS → IMPLEMENT → REVIEW → COMPLETE or its variants) is the universal abstraction. The hooks, the gate CLI, and the validation orchestrator all enforce the state machine — they don't replace it.

**On the "Python/script vs prompt" question:** the strong consensus is *scripts gate, prompts advise*. Hooks and CLIs run deterministically regardless of session length, context pressure, model drift, or adversarial input. Prompts do not. The threshold named by multiple practitioners: rules whose violation produces an irreversible consequence belong in a hook; rules whose violation produces a recoverable mistake can stay in a prompt.

---

## What "actually works" — the four enforcement layers

Layered architecture, each layer catches what the previous one misses:

| Layer | Mechanism | What it catches | What it misses |
|---|---|---|---|
| **L1: Hook** | PreToolUse/Stop script that exits 2 or emits `permissionDecision: deny` | Destructive ops, out-of-phase writes, premature completion | Content quality; an LLM-fooling pattern |
| **L2: Tool permission** | Allowed/denied tool list per agent | Operations the agent shouldn't be able to attempt at all | Steps within allowed tools (e.g., the agent was allowed to write but to the wrong file) |
| **L3: Engine-agnostic gate CLI** | Separate process tracks state machine + file locks; only it can mark merge complete | Skipped PR steps, parallel-branch contention, missing artifacts | What happens inside the agent's prompt loop |
| **L4: Adversarial validator** | Independent subagent/skill in fresh context grades the diff against the spec | Locally-correct-but-globally-wrong code, missing invariants, security holes | Things that look correct to a focused reviewer |

One practitioner ([saytooy_arch](https://zenn.dev/saytooy_arch/articles/04-hook-phase-gate)) reports "Out of the 18 incidents, zero have recurred since the introduction of the hooks" after moving all quality-process rules from L3 (written definitions in `quality_process.md`) to L1 (PreToolUse hooks that exit 2).

**Recommended** (`Confidence: H`): combine all four layers for a ship pipeline. Hooks handle "the agent can't skip a step." The gate CLI handles "the agent can't merge without artifacts." Adversarial review handles "the agent's code is wrong even if all steps ran."

---

## The dominant pattern: PreToolUse + Stop hooks

### Why hooks beat prompts

`ranjankumar.in/hooks-policy-as-code-agent-enforcement` (cited inline below) names three failure modes of prompt-only safety that hooks close:

> "Context dilution. As a session grows, early instructions compete with later context for attention weight… The model still sees it. It attends to it less.
> Novel task framing. An agent asked to 'clean up the workspace aggressively' in a context where multiple legitimate deletions have already occurred may classify `rm -rf` as consistent with the established pattern.
> Adversarial inputs. Prompt injection through files, web content, or tool outputs can override inline constraints… A `PreToolUse` hook is a separate process running outside the model's context — it cannot be injected into."

The framing is precise: *"Every rule you trust to a CLAUDE.md instruction is a rule the agent can violate. Every rule encoded in a hook is a rule the agent cannot violate."*

### The four lifecycle events that matter

| Event | Fires when | Use for |
|---|---|---|
| `SessionStart` | Once per session | Load state, inject context, set gates |
| `PreToolUse` | After Claude creates tool params, **before tool runs** | **Block dangerous operations; this is the enforcement event** |
| `PostToolUse` | After tool succeeds | Format, lint, audit-log, inject feedback |
| `Stop` | Session about to end | **Completion gates; exit 2 forces continuation** |

`PreToolUse` is the only event that can physically block before execution. `Stop` is the gate for "the agent declared victory but the work isn't done."

### The exit-code semantics that matter

From `ranjankumar.in/hooks-policy-as-code-agent-enforcement`:

> "`exit 0` with no JSON output: allow the operation, proceed. JSON with `permissionDecision: 'deny'`: block the tool call, reason visible to Claude. `exit 2` without JSON: block the tool call, reason shown directly to the user (not Claude). **The critical mistake:** using `exit 1` instead of `exit 2` for security hooks. `exit 1` signals a hook error — Claude Code logs it and proceeds with the tool call anyway. `exit 2` or a `deny` decision in JSON actually blocks execution."

So the bar for an LLM-loop ship gate is: shell script + exit-code-2 semantics + `permissionDecision: deny` JSON.

### What stops a "skip the review" attempt

The phase-gate pattern in `saytooy_arch`:

```
User/Agent → Edit/Write tool invocation
  → PreToolUse hook (check_process_gate.sh)
    → Get current stage from current_phase.txt
    → Identify necessary previous stage gates via stage mapping
    → Verify gate file signatures
    → No signature or FAIL → exit 2 (Block)
    → Signature present & PASS → exit 0 (Allow)
```

The `current_phase.txt` is a tiny file that the slash command writes; the hook reads it on every write. The agent cannot write a file in phase N unless the gate file from phase N-1 has a reviewer's signature on it.

A complementary pattern that emerged from `saytooy_arch`: the **Delegation Marker Pattern** — JSON files that only a specific agent role is allowed to create or delete. The agent that wants to edit `incident_ledger.md` cannot, because it cannot produce the `incident_commander_delegation.json` marker. This is the structural fix for "I want agent A to be the only one allowed to do X" when hooks can't see the actor.

---

## Engine-agnostic deterministic gate CLIs

The newer pattern: separate the **gate protocol** from the **agent runtime**. The agent does not merge; the gate CLI merges. The agent's role is to *produce artifacts* that the gate then validates deterministically.

### `mergegate` — Rust CLI, engine-agnostic (ShunsukeHayashi/mergegate)

`https://github.com/ShunsukeHayashi/mergegate` — Apache-2.0, 152 commits, Rust.

> "MergeGate is an engine-agnostic gate CLI for AI-assisted development. It does not need to be your coding agent, your chat runtime, or your terminal UI. Its job is simpler and more durable: register work, record impact, lock files, assign execution, track branch and PR state, verify completion."

The state machine is explicit: `register → impact → assign → branch → pr → merge | manual-complete`. Exit codes mean what you think they mean — `1` warnings, `2` real consistency problem (orphaned locks, invalid transitions, circular dependencies).

The critical design choice: **"Engine agnostic: Use Claude Code, Codex, Gemini CLI, or another agent runtime."** The product is the workflow gate, not the assistant. The agent runtime can change; the gate protocol does not.

### `agents-shipgate` — Python CLI + GitHub Action (ThreeMoonsLab/agents-shipgate)

`https://github.com/ThreeMoonsLab/agents-shipgate` — Apache-2.0, 287 commits, Python + PyPI + GitHub Action marketplace.

This one is explicitly a Tool-Use Readiness gate for MCP/OpenAPI/SDK tool-surface changes, but the architecture is the template that ship-pipeline implementers should study:

> "Local-first and static by default — no agent execution, tool calls, LLM calls, or network access."

The decision engine is **deterministic and stable**. The exit semantics: `0` pass, `2` config error, `3` parse error, `4` other error, `20` strict-mode gate failure. The control surface (`merge_verdict`: `mergeable | human_review_required | insufficient_evidence | blocked | unknown`) is a deterministic projection of `release_decision.decision`. Crucially, the gate writes a terminal **content-addressed closure** (`verification-receipt.json`) last — validate it before trusting anything earlier.

The interesting adoption harness: Claude Code hooks are auto-installed for it via `agents-shipgate init --claude-code`. The install writes three hooks: a `PreToolUse` trust-root guard, a cheap trigger check after `Edit|Write/MultiEdit`, and the full verifier at `Stop`. **This is the pattern: the gate is the product, the hooks are the local feedback loop, CI is authoritative.**

**Recommended** (`Confidence: H`): study this for the architecture. The pattern of "gate produces deterministic JSON; everything else is a projection of it" is the most important design choice in the space. Local copy: `https://github.com/ThreeMoonsLab/agents-shipgate`.

### Why a separate CLI beats a hook for the merge step

A PreToolUse hook is limited to: (a) reading JSON from stdin, (b) returning exit code + JSON decision, (c) being invoked by the agent host. A gate CLI is a long-lived process with its own state, file locks, and audit ledger. For the final merge — where you need to coordinate branch state, PR state, capability locks, content-addressed receipts, and external authorization — a CLI is the right layer. Hooks are the right layer for "block this write because we're not in review yet."

---

## Phase state machines as the universal abstraction

Every concrete project studied uses the same underlying structure:

| Project | Phases | Key insight |
|---|---|---|
| `prgazevedo/claude-code-workflows` | OFF → DEFINE → DISCUSS → IMPLEMENT → REVIEW → COMPLETE | Hooks block writes per phase; "REVIEW skip protection" hard-gates COMPLETE on `findings_acknowledged` |
| `GWUDCAP/cc-sessions` (DAIC) | Discussion → Alignment → Implementation → Check | Edit/Write/MultiEdit **completely blocked by default**; agent earns the right to write code via approval trigger phrases |
| `omeeragtoprak/agentic-engineering-protocol` | Explore → Plan → Implement → Verify → Deliver | Stop hook (`verify-gate.sh`) blocks "task complete" while the project's check fails; safety override after repeated blocks |
| `aws-samples/sample-specship` (Kiro Power) | Recon → Plan → Build → Validate → Ship | Up to 7 adversarial validators in parallel as independent subagents; each produces typed verdict with evidence |
| `eriklieben` dev-verify skill | Build → Analyzers → Format → Tests → Security → Diff review | All phases run before stopping; results presented as numbered list with fix menu |
| `ShunsukeHayashi/mergegate` | register → impact → assign → branch → pr → merge | CLI-as-state-machine, not agent-as-state-machine |
| `ThreeMoonsLab/agents-shipgate` | detect → init → check → verify → audit → bootstrap | Static-by-default verifier; capabilities.lock.json is the diff primitive |

The shape is consistent enough that "phased pipeline with mechanical enforcement at each transition" is a recognizable genre now. The label varies (DAIC, SPEC, WFM, AEP, MergeGate), but the architecture doesn't.

### REVIEW-skip protection — the specific failure this prevents

`prgazevedo/claude-code-workflows/blob/main/plugin/docs/reference/wfm-architecture.md` documents this directly:

```
Agent calls agent_set_phase "complete" (skipping review)
    → HARD GATE: findings_acknowledged not set
    → BLOCKED with explanation
    → Agent must run /review first

User runs /complete (skipping review)
    → user_initiated=true → gates bypassed
    → Allowed (user's explicit choice)
```

So even a phase-state-machine with mechanical hooks has to confront the bypass case. The mitigation: **the gate trusts user intent, blocks agent intent.** The agent can't skip review; the user can.

### Known trust gap in self-certified milestones

The `wfm-architecture.md` document is unusually honest about its limitations:

> "Milestone flags are self-certified by the agent. The gate trusts them. An agent that sets `tests_passing=true` without running tests will pass the gate. The structural mitigations are:
> 1. Milestones reset on phase entry — stale flags cannot carry over
> 2. REVIEW is mandatory before COMPLETE (agent path) — catching issues that IMPLEMENT missed
> 3. COMPLETE re-runs tests if code changed since `tests_last_passed_at`"

So the answer to "doesn't this just trust the LLM?" is: **yes, but layered.** The LLM sets the flag, but the next phase re-validates. This is not a complete solution — it's an escalation ladder. **The deeper fix, applied in `agents-shipgate` and `mergegate`, is to have the gate itself run the verification, not the agent.** That's the structural difference between hook-enforced and gate-enforced pipelines.

### MCP-tool bypass — a known hole

`wfm-architecture.md` again:

> "The write gates match tool names: `Write|Edit|MultiEdit|NotebookEdit` and `Bash`. MCP tools arrive under their own names (`mcp__server__tool`) and match neither, so a write-capable MCP tool works in every phase. In the current stack this is principle more than practice. The MCP tools in use write to external systems (memory, notes), not to the repository the gates protect."

So PreToolUse hooks with tool-name matching have a known bypass: MCP tools named `mcp__*__*`. The fix proposed: capability-based annotations in MCP, surfaced to hooks. Not yet implemented as of 2026-08-04.

**Recommended** (`Confidence: M`): if you build a phase-gate hook on this host, also deny write-capable MCP tools by name (`mcp__filesystem__write_file`, etc.) or whitelist MCP tools by capability.

---

## Multi-agent adversarial validation

The pattern: the agent that built the code **cannot** judge it. Independent validators in fresh context produce typed verdicts with evidence.

### SpecShip — the canonical example

`https://github.com/aws-samples/sample-specship` — Kiro Power, 1 commit but the README is a complete architecture doc.

> "Up to 7 adversarial validators run in parallel as independent subagents, each delegating to its gstack specialist skill (code→review, security→cso, browser→qa-only). Code, Security, Integration, Browser, Design, Alignment (always) + Load (if performance NFR exists). Each produces a typed verdict with evidence. Aggregate decides: merge / recover / escalate."

The **self-healing recovery** pattern: when a validator finds a bug, a fresh agent fixes it surgically — one fix per issue, regression test first, max 3 cycles. Parallel fixes when touching different files. This is a bounded fix loop with explicit iteration cap, modeled on the same anti-loop patterns documented in the agentic-loop literature (see DDG result "How to Stop Your LLM Agent From Looping Itself Into Oblivion" at `https://dev.to/alanwest/how-to-stop-your-llm-agent-from-looping-itself-into-oblivion-27eh`).

### Devin — write/catch/fix/merge loop

`https://cognition.com/blog/closing-the-agent-loop-devin-autofixes-review-comments` is the practitioner writeup:

> "Devin can now be configured to autofix incoming review comments from Devin Review and other review bots. Devin also continues to autofix lint and CI/CD issues. These move us a big step forward in closing the agent loop: writing and fixing its own code until its fully correct."
>
> "A review agent spends dedicated reasoning on the diff after it's written, and can go deep into specific issues not obvious just from the original plan. One agent writes, the other pressure-tests, and this continues in a loop. Write, catch, fix, merge. The agent writes. The reviewer catches. Bot triggers fire. Fixes get applied automatically. CI runs clean. The PR is ready for human review."

This is **the canonical ship loop for an autonomous agent.** Devin's "autofix from PR review bots" is a process-level pattern: any bot that comments on a PR — linters, CI, security scanners — Devin picks up the comment and patches the code. CI is the gate.

> "A coding agent is a tool. A coding agent paired with a review agent that catches bugs, suggests fixes, and automatically resolves them through bot triggers — that's a system. Systems compound. Tools don't."

Devin's metric: massively increased internal token spend, "PRs are now much more free of bugs and we can't go back." So the autofix-from-review-bots pattern is **paid for in tokens and validated in bug rate.**

### Agentic Engineering Protocol — fresh-context adversarial reviewer

`https://github.com/omeeragtoprak/agentic-engineering-protocol`:

> "Architecture: the right rule in the right layer. Monolithic instruction files degrade: the longer the always-loaded file, the more the agent ignores. AEP splits the protocol across layers… Fresh-context review — 4 subagents — On delegation, isolated context — Adversarial review, gap audit, security & performance audits — the author never grades its own work."

The four subagents: `adversarial-reviewer` (tries to refute the diff against its spec), `gap-auditor` (certifies every gap closed/deferred/open, with evidence), `security-auditor` (attacker-mindset: OWASP, boundaries, secrets), `performance-auditor` (scale hazards: hot paths, N+1, allocations).

**Validation discipline:** "Three measured rounds so far: two fixes confirmed by 0/2 → 2/2 flips (spec persistence, reviewer provenance) and one rule refuted by its shape — which produced a reusable design rule: unconditional positives are followed where conditional negatives are dropped." So the protocol itself is measured; rule changes are evidence-gated.

---

## What doesn't work alone (named anti-patterns)

### Prompt-only enforcement

`ranjankumar.in/hooks-policy-as-code-agent-enforcement` is direct on this:

> "You would not secure a database with a SQL comment that says 'please don't DROP TABLE.' You should not secure an autonomous agent with a markdown instruction that says 'please don't delete important files.'"

The home-directory nuke incident is named: "CLAUDE.md had a rule: 'never run destructive commands.' The model had read it. The model had followed it hundreds of times. And then, in one context-heavy session with a legitimately complex cleanup task, it didn't."

The threshold rule from the same source:

> "If violating the rule produces a consequence you cannot recover from in production (data loss, secret exposure, forced push to protected branch), it belongs in a hook. If violating the rule produces a consequence you can fix on the next turn (wrong format, missed lint rule, suboptimal output), it can live in a prompt."

### Self-verification ("the author grades its own work")

The phrase appears in `agentic-engineering-protocol` and `specship` independently. **Don't do it.** The fix is mechanical: dispatch the reviewer in a fresh subagent context, not as the next step in the writer's loop. `adversarial-reviewer.md` in AEP explicitly starts from the diff + spec, not the writer's narrative.

### Phases in prose only

`saytooy_arch` describes the failure directly:

> "I organized a multi-agent development team (15+ agents) using Claude Code to build a SaaS application. Even though I wrote 'skipping stages is prohibited' in quality_process.md, in practice: Implementation began without screen design documents. Tests were written without test specifications. Deployment was attempted without review records. 18 incidents occurred."

This is the most concrete practitioner failure-account I found. Phases in markdown: 18 incidents. Same phases enforced via PreToolUse hook: zero.

### Bloated always-on instructions

`agentic-engineering-protocol` articulates this from measured rounds:

> "Monolithic instruction files degrade: the longer the always-loaded file, the more the agent ignores. AEP splits the protocol across layers so detail is abundant where it's free and discipline is enforced where it matters."

The lean-always-on, rich-on-demand split (skill bodies load only when invoked) is the load-bearing discipline. The verification skills (adversarial reviewer, gap auditor, etc.) should not be in the always-on file — they should be subagents loaded into fresh context.

---

## Named tools — what each one actually does for the ship pipeline

| Tool | What it does for review→fix→verify→merge | What it does NOT do |
|---|---|---|
| **GitHub Copilot Workspace** | Issue-to-merge agent; PR opened automatically | Doesn't enforce a review phase; relies on GitHub PR review |
| **Cursor** (`cursor.com/automate`) | Schedule/event-based agents that build/maintain/fix | Background automation; no mechanical phase enforcement |
| **Devin** (`devin.ai`) | **Write/catch/fix/merge loop with autofix from PR review bots**; "no human in the loop for mechanical fixes" | Token cost is high; cognitive work (architecture, product direction) still human |
| **Factory** | Autonomous SWE agent | Less public detail on phase gating; default to PR review |
| **SWE-agent** (`https://github.com/SWE-agent/SWE-agent`) | Issue-to-fix agent, NeurIPS 2024 | Designed for "fix this issue" not "ship this PR"; no review-phase abstraction |
| **Harness** (delivery pipelines) | Markdown-defined AI agents at any pipeline step | The pipeline step itself is the gate, not phase enforcement |
| **Prgazevedo `claude-code-workflows`** | Phase-state-machine + PreToolUse hooks + REVIEW-skip protection | Hooks only; trusts user for milestone self-cert flags |
| **`GWUDCAP/cc-sessions`** (DAIC) | Edit/Write blocked by default; agent earns write right via trigger phrases | Slash-command ceremony; no formal review subagent |
| **`omeeragtoprak/agentic-engineering-protocol`** (AEP) | 5 phases + Stop hook + 4 fresh-context auditors | Verify-gate script depends on user-pointed `aep-check.sh`; portable but still trust-the-shell |
| **`aws-samples/sample-specship`** (Kiro Power) | recon→plan→build→validate→ship with up to 7 adversarial validators in parallel | Experimental / unofficial; self-healing loop has a 3-cycle cap |
| **`ShunsukeHayashi/mergegate`** | Engine-agnostic CLI gate; state machine; file locks; PR ledger | Engine-agnostic by design — doesn't ship its own coding agent |
| **`ThreeMoonsLab/agents-shipgate`** | Static Tool-Use Readiness review at PR time; deterministic verifier; capability locks | Static-by-default; can't verify runtime behavior (acknowledged limitation) |

For a Grok Build user specifically: `prgazevedo/claude-code-workflows` and `GWUDCAP/cc-sessions` are Claude Code plugins. Their patterns translate to Grok Build — Grok Build has `command` and `http` hooks (per `P:/AGENTS.md` host-runtime table), which are the same primitive class. The state-machine + PreToolUse approach transfers; the specific plugin install path does not.

**Recommended** (`Confidence: H`): for a Grok Build ship pipeline, study the `mergegate` state-machine + the `agents-shipgate` "gate is the product, hooks are the feedback loop, CI is authoritative" pattern. Combine with `prgazevedo`'s phase gate hooks for the local feedback loop. Use adversarial subagents (one of the 4 specialists from AEP, or a rewriter) for the verify phase.

---

## On Python/script vs LLM-follows-steps — explicit answer

The strong consensus across all sources surveyed: **scripts gate, prompts advise.** Specifically:

1. **Mechanical gates (hooks, CLIs, GitHub Actions) run regardless of model behavior.** The LLM cannot context-dilute, novel-frame, or adversarially-inject a separate process.
2. **Prompts work in short sessions on simple tasks.** They fail in production for context-dilution, novel-framing, and adversarial-injection reasons.
3. **The threshold rule:** irreversible consequences belong in a hook. Recoverable mistakes can stay in a prompt.
4. **For LLM-loop discipline specifically** (preventing skipped phases, runaway loops, premature completion): hard iteration caps, tool-call deduplication, embedding-based loop detection, and forced-decision prompts are named in the literature (see `https://dev.to/alanwest/how-to-stop-your-llm-agent-from-looping-itself-into-oblivion-27eh`, `https://dev.to/mukundakatta/your-agent-loop-needs-a-real-exit-llm-stop-conditions-15bf`). But for *phase gating* — the review→fix→verify→merge question — the answer is hooks + state machine + adversarial validators, not LLM behavior.

The Python/script vs LLM question is the wrong binary. The right framing:

- **What runs unconditionally, regardless of model state:** PreToolUse hook (shell/Python), GitHub Action (YAML), gate CLI (Python/Rust).
- **What runs only when the model chooses to invoke it:** the skill, the slash command, the next agent step.

For a ship pipeline, the merge step itself should be the former — not the latter.

---

## What to study further (concrete projects, ranked by relevance to your question)

| Rank | Project | Why study it |
|---|---|---|
| 1 | `ThreeMoonsLab/agents-shipgate` | Best example of "gate is the product, hooks + CLI + GH Action are the surfaces, content-addressed receipt is the trust root." Source: `https://github.com/ThreeMoonsLab/agents-shipgate`. |
| 2 | `prgazevedo/claude-code-workflows` | Best example of phase state machine + PreToolUse hooks + REVIEW-skip protection + self-certified milestone honesty. Architecture doc: `https://github.com/prgazevedo/claude-code-workflows/blob/main/plugin/docs/reference/wfm-architecture.md`. |
| 3 | `omeeragtoprak/agentic-engineering-protocol` | Best example of "lean always-on, rich on-demand" + Stop-hook completion gate + fresh-context adversarial reviewers. Source: `https://github.com/omeeragtoprak/agentic-engineering-protocol`. |
| 4 | `aws-samples/sample-specship` | Best example of "the agent that built the code cannot judge it" — 7 parallel adversarial validators, typed verdicts, self-healing recovery loop with 3-cycle cap. Source: `https://github.com/aws-samples/sample-specship`. |
| 5 | `GWUDCAP/cc-sessions` | Best example of DAIC — Edit/Write blocked by default; agent earns the right to write. Original inspiration for `prgazevedo`. Source: `https://github.com/GWUDCAP/cc-sessions`. |
| 6 | `ShunsukeHayashi/mergegate` | Best example of engine-agnostic Rust CLI gate; state machine + file locks + execution ledger. Source: `https://github.com/ShunsukeHayashi/mergegate`. |
| 7 | `ranjankumar.in/hooks-policy-as-code-agent-enforcement` | Best practitioner essay on why hooks beat prompts (Probabilistic-to-Deterministic Boundary). Source: `https://ranjankumar.in/hooks-policy-as-code-agent-enforcement`. |
| 8 | `saytooy_arch` "Physically Enforcing AI Agent Process Transitions with Hooks" | Best *direct practitioner failure account* — 18 incidents before hooks, 0 after. Source: `https://zenn.dev/saytooy_arch/articles/04-hook-phase-gate?locale=en`. |
| 9 | `eriklieben.com` quality-gates posts | Best example of a domain-specific verify skill (dev-verify, dev-security) — OWASP-aligned, run-all-phases-before-stopping, fix-menu UX. Source: `https://www.eriklieben.com/posts/agentic-dev-workflow-quality-gates/`. |
| 10 | `Cognition` Devin autofix blog | Best practitioner writeup of write/catch/fix/merge loop. Source: `https://cognition.com/blog/closing-the-agent-loop-devin-autofixes-review-comments`. |

---

## Disconfirming evidence / open questions

- The hook ecosystem is largely **Claude Code-shaped** (PreToolUse, PostToolUse, Stop, UserPromptSubmit). Grok Build's hook surface is documented as `command` and `http` only (per `P:/AGENTS.md`). The pattern transfers; the configuration syntax does not. **[INFERENCE]** — verified against the host-runtime table but I did not load the actual Grok Build hooks docs.
- `agents-shipgate` real-history metrics: 93% organic skip of the trigger, `blocked_recall` still 0.0 on real history (it routes to review, doesn't block). The README is unusually honest about this — "Treat it as an advisory gate while this work closes." Don't assume "deterministic gate" means "always blocks" — for the **real-history** set, it currently means "always routes to human review," which is the same conservative outcome but a different mechanism than the constructed-adversarial stratum implies.
- The "Exit code 2 forces continuation" claim for the Stop hook is documented in `ranjankumar.in`; I did not exercise it on this host to confirm current behavior. **[INFERENCE]** for the specific exit-code-to-session-continuation mapping on this model/runtime.
- The MCP-tool bypass hole in PreToolUse hooks (named in `prgazevedo/wfm-architecture.md`) is documented but the upstream fix is not landed as of 2026-08-04. If you ship a phase-gate hook on this host, the bypass is real. **[FACT]** — cited.

---

## Sources (all absolute URLs, all opened this session)

### Primary projects (GitHub READMEs)
- `https://github.com/prgazevedo/claude-code-workflows` — Phase state machine + mechanical hook enforcement
- `https://github.com/prgazevedo/claude-code-workflows/blob/main/plugin/docs/reference/wfm-architecture.md` — Architecture + known trust gap + REVIEW-skip protection
- `https://github.com/omeeragtoprak/agentic-engineering-protocol` — AEP: Explore→Plan→Implement→Verify→Deliver + Stop hook + 4 fresh-context auditors
- `https://github.com/ShunsukeHayashi/mergegate` — Engine-agnostic Rust CLI gate
- `https://github.com/ThreeMoonsLab/agents-shipgate` — Static Tool-Use Readiness gate; CLI + GitHub Action
- `https://github.com/aws-samples/sample-specship` — Kiro Power with adversarial validators
- `https://github.com/GWUDCAP/cc-sessions` — Original DAIC; inspiration for prgazevedo

### Practitioner essays / blog posts
- `https://zenn.dev/saytooy_arch/articles/04-hook-phase-gate?locale=en` — "Physically Enforcing AI Agent Process Transitions with Hooks" — 18 incidents → 0 with hooks
- `https://ranjankumar.in/hooks-policy-as-code-agent-enforcement` — "Hooks: The Enforcement Layer That Turns Agent Policy Into Agent Fact" — Probabilistic-to-Deterministic Boundary
- `https://cognition.com/blog/closing-the-agent-loop-devin-autofixes-review-comments` — Devin autofix; write/catch/fix/merge loop
- `https://www.eriklieben.com/posts/agentic-dev-workflow-quality-gates/` — dev-verify / dev-security skills; OWASP-aligned
- `https://thenewstack.io/merge-gate-coding-agents/` — "Your merge gate was a compromise" — sponsored by Signadot; context for *why* the gate is now a liability with AI agents

### LLM-loop discipline (anti-pattern)
- `https://dev.to/alanwest/how-to-stop-your-llm-agent-from-looping-itself-into-oblivion-27eh` — Hard iteration caps, dedup, loop detection
- `https://dev.to/mukundakatta/your-agent-loop-needs-a-real-exit-llm-stop-conditions-15bf` — `llm-stop-conditions` Python lib
- `https://deepwiki.com/rjmurillo/ai-agents/7.4-pretooluse-hooks-and-routing-gates` — PreToolUse as routing-level enforcement gates
- `https://code.claude.com/docs/en/agent-sdk/hooks` — Claude Agent SDK hooks reference (for the lifecycle event taxonomy)

### Tool landing pages (named-tool coverage)
- `https://cursor.com/automate` — Cursor Automations
- `https://devin.ai/` — Devin landing
- `https://github.com/SWE-agent/SWE-agent` — SWE-agent (issue-to-fix, no ship pipeline)

### Tooling references found via DDG but not deeply fetched
- `https://tweag.github.io/agentic-coding-handbook/WORKFLOW_TDD/` — TDD + agentic pairing
- `https://www.augmentcode.com/guides/ai-agent-pre-merge-verification` — Augment pre-merge verification
- `https://qubittool.com/blog/ai-code-review-automation-pipeline` — AI code review automation
- `https://github.com/boraoztunc/agent-system` — 7 specialized agents plan/implement/verify/review/ship
- `https://dev.to/leobaniak/harness-ships-autonomous-worker-agents-making-any-pipeline-step-a-markdown-defined-ai-agent-4pa9` — Harness markdown-defined agents

---

## Recommendation summary

- **For Grok Build ship pipelines specifically** (`Confidence: H`): combine a phase-state-machine written into host hooks with an engine-agnostic gate CLI for the final merge. Use adversarial fresh-context subagents (not the writer) for the verify phase. Don't trust the LLM to follow prose for any irreversible step.
- **For the specific "what if the LLM skips review" question** (`Confidence: H`): the answer is PreToolUse hooks + state machine + content-addressed receipts. The LLM skipping review requires bypassing hooks; hooks that exit 2 or return `permissionDecision: deny` cannot be reasoned around.
- **For "Python/script vs LLM" specifically** (`Confidence: H`): scripts gate, prompts advise. The merge step should be a script that runs deterministically; the agent's job is to produce the artifacts the script checks for.
- **For a starting template** (`Confidence: M`): fork `agents-shipgate` for the "gate is the product" architecture; study `prgazevedo/claude-code-workflows` for the phase-state-machine + hook-enforcement pattern; adopt AEP's adversarial-reviewer subagent split as the verify-phase shape.