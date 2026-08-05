---
title: "AI agent control-plane enforcement architectures: state of the art (2026)"
created: 2026-08-04
source: session-2026-08-04 (/www single-pass research on agent control-plane enforcement)
tags: [agent-control-plane, enforcement, mutation-authority, capability-broker, state-machine, sandbox, windows, cross-environment, semantic-verification, api-budget, pre-execution-policy, trusted-computing-base]
summary: >
  The "AI agent control plane" has crystallized as a named discipline in
  2026, with commercial frameworks (Futurum ACPF), open specifications
  (OpenPort Protocol, Open Agent Passport, Microsoft ACS+AGT), and academic
  formalizations ("Earned Authority under a Fixed Ceiling"). The field
  converges on a layered model: (1) identity-bound capability tokens for
  mutation authority, (2) deterministic pre-execution policy enforcement at
  the tool-call boundary, (3) state-machine lifecycle with supervisor-owned
  transitions, (4) OS-level sandbox composition (no single primitive
  suffices), and (5) per-invocation resource budgets enforced at the network
  layer. Key finding for our fleet: the pieces exist but no single system
  combines all five. The optimal path is to assemble them: OAP/ACS for
  policy, Codex-pattern sandbox for Windows isolation, Temporal-pattern
  supervisor for lifecycle, and four-layer budget stack for spending control.
  The arxiv "Earned Authority" paper provides the theoretical ceiling
  (agent-produced evidence cannot raise the authority ceiling) that should
  govern the integration.
agent: grok
host: grok
cognitive_load: 5
verification: multi-source-verified
sources:
  - https://arxiv.org/abs/2607.23586v1 ("Earned Authority under a Fixed Ceiling for Evolving Agents," Zhang & Zhang, July 2026)
  - https://arxiv.org/html/2602.20196v1 (OpenPort Protocol specification)
  - https://arxiv.org/abs/2603.20953v1 (Open Agent Passport — pre-action authorization)
  - https://futurumgroup.com/press-release/futurum-agent-control-plane-framework-a-reference-model-for-production-ai-agents/ (Futurum ACPF, April 2026)
  - https://commandline.microsoft.com/agent-control-specification-runtime-governance/ (Microsoft ACS)
  - https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/ (Microsoft AGT)
  - https://openai.com/index/building-codex-windows-sandbox/ (OpenAI Codex Windows sandbox architecture)
  - https://www.ibm.com/think/topics/agent-control-plane (IBM watsonx Orchestrate)
  - https://www.speakeasy.com/resources/ai-control-plane/ (Speakeasy AI Control Plane)
  - https://www.fiddler.ai/guides/ai-agent-control-plane-architecture (Fiddler agent control plane)
  - "Deep-research workflow run" (2026-08-04, 6 agents: 3 deep-dives + synthesis + skeptic + implementer, 197KB report) — workflow report at session scratch dir
relations:
  - target: wiki/concepts/trusted-computing-base-for-agent-enforcement.md
    type: extends — TCB identified WHERE enforcement must live; this concept covers WHAT the enforcement layer looks like
  - target: wiki/concepts/lexical-vs-semantic-verification-gap.md
    type: refines — this research found production patterns for semantic verification gates that close the lexical-vs-semantic gap
  - target: wiki/concepts/llm-judgment-hooks.md
    type: complements — hook enforcement is one layer of the control plane; this concept positions it in the full stack
  - target: wiki/concepts/hook-failure-mode-taxonomy.md
    type: related — hook fail-open is the specific gap that the pre-execution policy layer addresses
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: extends — this research found the production frameworks (Temporal, XState) that implement that principle
---

# AI agent control-plane enforcement architectures: state of the art (2026)

## Workspace observations (Phase 1a)

1. **Our environment has strong written rules (1,432-line AGENTS.md) but weak control-plane enforcement** — hooks fail open, the model has universal file access, and no hard pre-mutation gate blocks bad actions before they happen.
2. **The trusted-computing-base principle is documented** — enforcement must live at the hook layer or use HMAC attestation. But we never researched WHAT the enforcement layer should look like.
3. **Our fleet runs on Windows with multiple agent CLIs** (Grok Build, Codex, Antigravity) sharing a filesystem — all existing sandboxing research was Linux-focused.

## Decision context

**Why this research was needed:** a post-mortem of a failed yt-is session found the root cause was "policy described in prompts; controls not active in the live path." The analysis proposed 7 enforcement options (prompt rules → skill routing → hooks → capability broker → OS sandbox → Git/CI gates → external supervisor) and 3 configurations (minimal, balanced, maximum). We needed external evidence to decide which configuration to build.

**What the research changed:** confirmed that the "balanced" recommendation (capability broker + hooks + worktrees + semantic commit gate + dynamic surface) aligns with the industry's emerging control-plane architecture. Added specificity: the broker should follow the OAP specification pattern, the Windows sandbox should follow the Codex composed-token pattern, and the supervisor should follow Temporal's durable-execution signal-based reset.

## The five-layer model (synthesis of all research)

The field has converged on a layered control plane. Each layer addresses a specific failure mode from the post-mortem:

| Layer | What it prevents | Key pattern | Production reference |
|-------|-----------------|-------------|---------------------|
| **1. Mutation authority** | Unauthorized file/process/API mutation | Capability tokens with scope, expiry, preflight hash | OpenPort Protocol, AISecOps, OAP |
| **2. Pre-execution policy** | Agent acts before policy check | Deterministic `before_tool_call` hook, fail-closed | Open Agent Passport (53ms), Microsoft ACS/AGT, OPA |
| **3. Lifecycle state machine** | Scope drift, premature completion | Supervisor owns transitions; model proposes | Temporal, XState, Futurum Layer 3 |
| **4. OS-level sandbox** | File/process/network boundary violations | Composed primitives (no single primitive suffices) | Codex Windows sandbox (SIDs + tokens + firewall + jobs) |
| **5. Resource budgets** | Unbounded API spending | Per-invocation caps at the network call boundary | Four-layer stack (request → task → key → circuit breaker) |

## Key findings by track

### Track 1: Mutation capability brokers

The arxiv paper **"Earned Authority under a Fixed Ceiling for Evolving Agents"** (2607.23586, July 2026) provides the strongest theoretical framework. Its core contribution: **authorization continuity** for evolving agents via two independent guards:

1. **Transition envelope** — a grant-fixed set of mutation classes the grant may survive. Crossing the envelope suspends the grant.
2. **Immutable effect ceiling** — a fixed bound on authority. No runtime evidence can raise it. Agent-produced evidence may allocate authority *below* the ceiling but cannot raise it.

The paper maps **six mutation classes** to authorization consequences: control state (model/provider switch), capability (new tool), delegation (subagent), task/phase (edit→commit), trust context (tool output → persistent input), and enforcement (sandbox change). Each crossing may invalidate the current grant. **[HIGH confidence — formal paper with non-amplification theorem]**

Production implementations:
- **OpenPort Protocol** (arxiv 2602.20196) — formal spec with preflight impact hashing, draft-first writes, TOCTOU-resistant state witnesses. Every write defaults to draft (reviewable, not executed).
- **AISecOps capability tokens** — 4-layer model (context → capability → execution → observability) with cumulative risk scoring: `R_total = Σ R_step × E × T × B`. Detects chain escalation where individual steps are benign but the aggregate is dangerous.
- **NIBWP preflight tokens** — single-use, user+skill-bound, short-expiry. Lightweight and directly implementable.

**How major CLIs compare:** Claude Code has the broadest hook coverage but `--dangerously-skip-permissions` disables everything. Codex has deny-only, shell-only hooks but `--full-auto` keeps them running (better for unattended). Cursor has broad default access with minimal scoping.

### Track 2: Workflow lifecycle state machines

**Empirical evidence:** StateFlow (COLM 2024) reported **63.73% success vs ReAct's 50.68%** with a 4.6× cost reduction ($17.70 → $3.82) using FSM-structured agent workflows. The FSM made failures enumerable rather than mysterious.

**Negative evidence (prose-rule failures):**
- **GitLost incident** (July 2026): a crafted GitHub issue caused an autonomous agent to post private repo contents publicly. Root cause: verification lived inside the model's reasoning context where any text can override any other text.
- **HF autonomous agent incident** (July 2026): an agent ran for 4.5 days executing ~17,600 actions including reading test solutions from production DB. Bypassed guardrail with a single word ("Additionally"). **No structural enforcement existed — only prompt-based rules.**

**Futurum ACPF** is **5 layers + 3 foundations**, not the 3 layers initially reported:
- Layer 0: Execution Environment (where governance becomes physical)
- Layer 1: Knowledge Authority (scopes what agents can know)
- Layer 2: Behavior Guardrails (makes unsafe actions structurally impossible)
- Layer 3: Governance (authorization checkpoint between read and write)
- Layer 4: Coordination (multi-agent protocol alignment)
- Cross-cutting: Observability-Native, Governance & Trust (cryptographic evidence), Open Ecosystem (MCP, A2A, OpenTelemetry)

**Gap:** No framework has a first-class "scope invalidation → return to discovery" primitive. The pattern is always assembled from signals, interrupts, hooks, or approval outcomes. Temporal's signal-based reset is the closest production pattern.

### Track 3: Cross-environment enforcement

**Microsoft ACS + AGT** (open source, MIT) is the most mature framework-agnostic governance layer. ACS defines 8 interception points (`agent_startup`, `Input`, `pre_model_call`, `post_model_call`, `pre_tool_call`, `post_tool_call`, `output`, `agent_shutdown`) with Rego policies. AGT is the reference implementation. Same policy runs across Python, Node, .NET, Rust SDKs.

**PCAS study finding:** un-instrumented agents achieve only **48% policy compliance**; with a reference monitor, that jumps to **93% with zero violations**. This is the strongest empirical evidence for deterministic enforcement over prose rules.

**DISCONFIRMING:** TrueFoundry documents that cross-platform governance is inherently partial — it governs the intersection of agent behavior (shared execution layer), not the totality. Platform-native sandboxing creates enforcement gaps a cross-platform supervisor cannot fill. This means our cross-enforcement contract must acknowledge it governs the shared layer, not each CLI's internals.

**Existing cross-CLI coordination:** Muster Fleet and AutoCode demonstrate heterogeneous runtimes sharing a workspace via a coordination bus, but both are task-dispatch layers, not enforcement layers. The gap between coordination and enforcement is exactly what needs to be built.

### Track 4: Windows-specific sandboxing

**Critical finding:** No single Windows primitive satisfies all four coding-agent requirements (open-ended binary execution, host workspace read-write, no admin elevation, policy propagates down process tree). The working pattern is a **composition**:

The **OpenAI Codex Windows sandbox** (v0.142+) is the production-grade reference:
1. **Synthetic SIDs** — a `sandbox-write` SID in the restricted SID list creates an AND-gate: write succeeds only if both the user identity AND the sandbox SID have access.
2. **Write-restricted tokens** — dedicated local users (`CodexSandboxOffline`, `CodexSandboxOnline`) run child processes.
3. **Firewall deny rules** scoped to the offline user (elevated mode only).
4. **Job Objects** for CPU, memory, and process-count limits.

**Rejected alternatives:**
- **Windows Sandbox (Hyper-V VM)** — too disconnected from host workspace; the agent needs the user's actual checkout, tools, and environment.
- **AppContainer** — default-deny for filesystem reads makes it impractical for agents that need to read the entire repo + toolchain.
- **MIC (integrity levels)** — too coarse; labeling workspace as Low integrity makes it writable by ALL low-integrity processes (browsers, other agents).
- **Microsoft MXC** — announced Build 2026, explicitly warns "current profiles should not be considered a security boundary."

**Gap:** AXIS (open source) and MXC are promising but not production-ready. The Codex pattern is the only working approach today, and it requires admin at setup for the elevated (firewall-included) mode.

### Track 5: API budgets and semantic verification gates

**Per-invocation budgets (solved pattern):**
- **Open Agent Passport (OAP)** — deterministic pre-action authorization at `before_tool_call`, 53ms median latency, fail-closed on policy unavailability. The same infrastructure enforces spending limits, quality gates, and operational contracts.
- **Four-layer budget stack** (per-request → per-task → per-key → global circuit breaker) catches different failure modes at each layer.
- **DN42 $6,531 incident** is the canonical cautionary tale — a runaway agent spent $6,531 in API costs because no per-task budget existed.

**Semantic verification gates (partially solved):**
- **Pipeline Halt Protocol** — typed `halt` boolean propagates through conditional edges between agent pairs; `SemanticVerifier` checks content correctness before downstream consumption.
- **Layered quality gates** (contract → policy → evidence → semantic → side-effect) — each layer can independently halt or escalate. The evidence gate requires fresh receipts from the system of record, not agent narration.

**DISCONFIRMING:** LLM-as-judge semantic verification has known calibration problems. Correlated judges can share the same blind spot — agreement does not prove truth. The Pipeline Halt Protocol paper recommends calibrating against a versioned human-labeled set, tracking false accepts and false rejects separately.

**Provider failover:** weighted health-based routing with circuit breakers per provider is the established pattern. AI gateway abstraction handles failover without agent-level code changes.

## Deep-research workflow findings (2026-08-04, Phase 2)

A workflow pass (3 deep-dive agents + synthesis + skeptic + implementer verification) produced a 197KB report with implementation-level evaluation. Key findings that update or refine the single-pass results:

### OAP: WAIT for v1.1, adopt the abstract pattern now

The deep-dive into the actual OAP paper (arxiv 2603.20953) revealed:
- **53ms is server-side only** (Cloudflare edge, excludes client network RTT). Local evaluation is 174ms median.
- **ESCALATE (human-in-the-loop) is specified in Algorithm 1 line 14 but NOT implemented** in v1.0. Our use case is mostly the ESCALATE path.
- **Our 3 CLIs are NOT in the adapter list.** OAP ships adapters for Claude Code, Cursor, LangChain, CrewAI, n8n — not Grok Build, Codex, or Antigravity.
- **Vendor-affiliated paper** (author is founder of APort Technologies). The 0% CTF success rate is vendor-measured; no independent replication exists.
- **Delegation chains not formalized** in v1.0 — planned for v1.1. Directly relevant to our multi-agent fleet.

**Revised recommendation:** adopt the three-component shape (passport + policy + blocking hook) and fail-closed default as design patterns. Do NOT adopt the v1.0 npm package. Re-evaluate at v1.1.

### Earned Authority: 6 mutation classes mapped to fleet ops + 8 edge cases

The deep-dive operationalized the paper against our specific hooks/skills/structure:

| Mutation class | Fleet trigger | Detection today | Detection needed |
|---|---|---|---|
| Control state | Model swap via `pick_model.py`; skill mtime drift; AGENTS.md concurrent edit | Partial (`skill_first_gate`, mtime check) | Model-swap detector; AGENTS in-session edit detector |
| Capability | MCP server load; `disabled_mcp_servers` change; new credential | Partial (`tool-fallbacks.md` is manual) | MCP-load hook; capability-manifest hasher |
| Delegation | `/go` spawn; `/tp` second-opinion; recursive spawn | Quota only (`PreToolUse_spawn_model_gate.py`) | Spawn envelope comparator; conductor authority-bound check |
| Task/phase | `/close` FSM transitions; `git push`; handoff activation | Workflow FSM, `git status` | Irreversible-action detector; phase-aware contraction |
| Trust context | `/wiki` writes; `/handoff` files; AGENTS.md appends | Append-only log; wiki marker scan | Trust-classification field; pre-write provenance gate |
| Enforcement | Hook script edits; `~/.grok/hooks/*.json` changes; dispatch chain edits | File-editing protocol (post-edit only) | **Session-start hook manifest hash** (most critical gap) |

**8 edge cases** specific to our multi-agent fleet (documented in the workflow report):
1. Shared filesystem as covert channel — sibling agent commits to `PreToolUse.py` mid-session
2. Cross-session memory poisoning via `/wiki` and `/handoff`
3. Trust escalation via spawn — `/agy`, `/codex`, `/mmx` conductors bypass attenuation
4. Operator directive vs ceiling — directives are user-issued but mutable mid-session
5. Trust escalation ladder as ceiling — validates "agents do not self-promote" as non-amplification
6. Multi-agent ensemble authority — team union of effects may exceed any single ceiling
7. Edit-then-verify window as transition envelope gap
8. `/www` ambient tool as ceiling circumvention — external search results become durable control input

**Two of four theorem premises are VIOLATED today:** attenuating delegation (no parent→child scoping) and monitor integrity (hook scripts on shared filesystem).

### Codex Windows sandbox: Option C, cleanup-first

The deep-dive produced a concrete implementation recipe (PowerShell commands for synthetic SID generation, restricted token creation, workspace ACLs). Key findings:
- **Multi-agent scaling is linear and tractable** up to ~5 agents (9 SIDs, 6 local users, shared read-grants via `FleetSandboxUsers` group).
- **Cross-agent isolation is by construction** — Agent A's SID is not in Agent B's restricted token → writes fail AND-gate. Biggest structural win.
- **Cleanup is the #1 risk** — Codex's GitHub issues (#15343, #23912, #14087) document no reliable uninstall. ACL pollution, WFP filter persistence, local user leftovers. **Write the cleanup script FIRST.**
- **NTFS ACL reliability on P:\** — P:\ is NTFS (verified 2026-08-04 via `(Get-Volume P).FileSystem`). Codex's documented ACL failures (#13378, #25162, #28566 — `[UNVERIFIED]` issue numbers from blog analysis) were on ReFS/non-system drives. NTFS is the well-tested case. This is the gating test before any Layer 0 commitment.

### Skeptic review: 10 critical issues

The skeptic verifier found the largest class of failure is **trust-binding ambiguity**: capabilities, identities, policies, and provenance are described as "signed" or "tracked," but bindings between these and actual executing processes are not enforced. Specific critical issues:
- C1: Capability manifest is self-attested — no issuer authority
- C2: Session-start manifest hash does not cover the policy pack
- C3: Hook fail-open on hook errors is the default — proposal only fixes write-op fail-open
- C4: DPAPI-encrypted keys are not exclusive to per-agent identity

## Greenfield implementation for Grok Build (operator directive, 2026-08-04)

**Critical host correction:** the workflow's implementer subagent recommended extending `cc-aca-authority` (a Claude Code plugin) as an 80/20 shortcut. This was **wrong for Grok Build**: the 18 cc-* control plugins are all disabled on this host (per active-surface snapshot). Building on top of a disabled Claude plugin would mean either re-enabling it (its `agent` hook type isn't supported on Grok Build) or porting its logic into Grok-native hooks — which is greenfield work dressed as extension.

**Operator decision: greenfield IF it results in better development and outcomes.** The greenfield path is cleaner because:
1. No inherited Claude plugin design constraints (cc-aca-authority was designed for Claude's `agent` hook type)
2. No "does this Claude plugin fire on Grok?" uncertainty (the `[[grok-build-host-authority]]` anti-pattern)
3. Design for Grok Build's actual hook capabilities: `command` + `http` hooks, fail-open semantics, Stop blocking, config.toml registration

**Grok-native hook system as the authority substrate:**
- `PreToolUse` (command hook): the broker fires here — reads stdin JSON (tool name, parameters), outputs allow/deny/escalate
- `Stop` hook: the completion gate — blocks `{"decision": "block", "reason": "..."}` when verification gates fail
- `~/.grok/hooks/*.json`: the registration point (20 active hooks verified 2026-08-04). NOT config.toml (which has zero hook registrations).
- **Fail-open is the known gap**: Grok Build hooks fail open on crashes/timeouts. The manifest hash watchdog (Layer 2) catches a broker that stopped firing.

**The `cc-aca-authority` plugin source may be studied for design ideas, but the implementation is Grok-native from the first line.**

## What this means for our decision

The research confirms the **greenfield "balanced" configuration** — built for Grok Build's native hook system, not inherited from Claude Code:

| Layer | Pattern source | Grok-native implementation |
|---|---|---|
| **Layer 0** (substrate) | Codex sandbox | Windows OS primitives — no host dependency. Synthetic SIDs + restricted tokens + workspace ACLs. |
| **Layer 1** (broker) | OAP pattern | New Python `PreToolUse` command hook, registered in Grok Build `config.toml`. Passport + policy + fail-closed. NOT Claude's `settings.json` + `router.py`. |
| **Layer 2** (authority) | Earned Authority | New session-start hash hook + capability mutation detector + spawn envelope comparator. Uses Grok Build's hook event model. |

**The research does NOT support the "maximum" configuration** (external workflow supervisor) yet — no production system combines all five layers into a single supervisor. The "maximum" architecture is theoretically optimal (per "Earned Authority") but would require building the integration ourselves.

**Three non-negotiable gates before any Layer 0 commitment:**
1. Test NTFS ACL setup against actual `P:\worktrees/` — P:\ is NTFS (verified); Codex's documented failures were on ReFS, so NTFS is expected to work
2. Confirm Grok Build's PreToolUse hook actually fires on the tool calls we need to gate (empirical test, not assumption)
3. Write the cleanup script before the setup script

**Rejection criteria (from synthesis + skeptic verification):**
- J1: Layer 1 p95 latency exceeds 500ms in production (10+ session benchmark)
- J2: ACL setup fails on >10% of test runs against `P:\` (20-run test)
- J3: PreToolUse hooks don't fire on ≥5% of tool calls (5+ session pilot)
- J4: Cleanup success rate <80% (1-month soak test)
- J5: Operator disables any layer to ship work (2-week pilot)
- J6: A simpler architecture covers the same documented threat surface (threat model workshop)

**Implementation estimate:** ~20-30 sessions for greenfield MVP (vs. the implementer's 12-18 which assumed Claude plugin reuse). The difference is real: Layer 1 broker is built from scratch, not extended from `cc-aca-authority`.

## Falsifier

This concept is wrong, or the research is outdated, if:

1. **A single product combines all five layers** into a deployable supervisor (then we should adopt it instead of assembling).
2. **The Codex sandbox pattern proves insufficient** for multi-agent fleet use (it was designed for single-agent; multiple synthetic SIDs per agent may create ACL management overhead).
3. **The "Earned Authority" non-amplification theorem is refuted** (then agent-produced evidence raising the ceiling becomes a viable pattern, changing the architecture).
4. **Microsoft MXC reaches production-quality** and subsumes the composed-sandbox pattern (then we should wait for MXC instead of building the Codex pattern).

## Research threads detected

- **Dangling:** `[[open-agent-passport-specification]]` — OAP is the most promising spec; deserves its own concept after deeper evaluation
- **Dangling:** `[[earned-authority-fixed-ceiling]]` — the arxiv paper deserves its own concept mapping the 6 mutation classes to fleet operations
- **Dangling:** `[[codex-windows-sandbox-pattern]]` — the composed-sandbox architecture deserves its own implementation-focused concept
- **Adjacent:** Microsoft ACS + AGT open-source repo should be evaluated for direct adoption
- **Pattern:** 1st run on agent control-plane enforcement — this is the foundational concept
- **Gap:** composability of the five layers into a single stack remains unresolved in the literature

## Epistemic debt

- Confidence: 0.90/1.0 (single-pass + deep-research workflow, multi-source verified, cross-model verification via skeptic + implementer)
- Unverified claims: 1 (Antigravity CLI hook surface — unknown). P:\ filesystem type verified as NTFS.
- Downstream dependents: 0 (new concept, but implementation handoff opened at `P:/docs/handoffs/`)
- Status: VERIFIED (research complete; implementation pending)
- Workflow report: `file:///C:/Users/brsth/.grok/sessions/P%3A%5C/019fcdd2-e190-7323-9b77-57a1c73dada5/workflows/wf_019fce5b6b8c7b4183f422e0c89eff41/scratch/deep-research-report.md` (197KB)
