# Research: AI agent control-plane enforcement architectures

## Context

We operate a fleet of AI coding agents (Grok Build, Codex CLI, Antigravity CLI) on a shared Windows host. A post-mortem analysis of a failed session found that the environment has **strong written rules but weak control-plane enforcement**: 1,432-line AGENTS.md with correct policies (preflight before mutation, alternatives gate, evidence labels, TDD), but no hard pre-mutation gate that actually blocks. Hooks fail open. The model has universal file access, making file-based enforcement forgeable.

The analysis proposed seven enforcement options (prompt rules, skill routing, PreToolUse hooks, mutation capability broker, OS sandbox, Git/CI gates, external supervisor) and three configurations:
- **Minimal**: hooks + auto-verifier fixes + destructive-command patterns + API budgets
- **Balanced**: mutation capability broker + hooks + worktrees + semantic commit gate + dynamic surface
- **Maximum**: external workflow supervisor + brokered everything + sandboxed workers + independent review

## What we already know (validate or skip — don't re-derive)

The workspace wiki already covers: hook fail-open behavior and its taxonomy; the trusted computing base principle (enforcement must live at the hook layer or use HMAC attestation the model can't forge); lexical-vs-semantic verification gap; two-layer regex+LLM hook pattern; context rot from bloated instruction files; deterministic lifecycle enforcement vs probabilistic instruction-following; dynamic skill lifecycle management (SLIM). If external research confirms or contradicts these, note it — but don't re-research from scratch.

## Research tracks

### Track 1: Mutation capability brokers for AI agents

**The question:** How do production AI agent systems authorize specific state-changing operations with bounded scope, as opposed to giving the model blanket file/process access?

**Specific questions:**
- Are there frameworks/tools that implement capability-token-based mutation authority for LLM agents? (tokens containing: authorized paths, allowed operation classes, preflight hash, expiry/session binding)
- How do systems like OpenAI Codex's sandbox, Claude Code's permission model, Cursor's agent mode, or Devin's execution environment scope what the agent can mutate?
- What is the state of the art for "least privilege" in agent tool access — does anyone dynamically narrow tool availability per workflow phase?
- What happens when a capability is forged or stolen in an agent context — what are the known attack vectors?

**Disconfirming search:** "capability-based security too complex for AI agents" / "capability brokers add latency without preventing failures" / "simpler approaches work just as well"

### Track 2: Workflow lifecycle state machines for coding agents

**The question:** Beyond LangGraph and prompt-chain patterns, are there production-grade state machines that enforce a discovery → plan → implement → verify → review lifecycle for autonomous coding agents?

**Specific questions:**
- How do multi-agent orchestration platforms (LangGraph, CrewAI, AutoGen, OpenAI Swarm, Google ADK) enforce phase transitions? Can the model self-declare phase, or must a supervisor approve?
- What is the evidence that explicit state machines reduce agent failure rates compared to prose-rule-driven workflows?
- Are there patterns for "scope change invalidates the capability and returns to discovery" in any framework?
- How do frameworks handle the "user correction returns to discovery" transition specifically?

**Disconfirming search:** "state machines over-constrain agents" / "prompt chains outperform state machines for coding tasks" / "state machines don't prevent the failures they claim to"

### Track 3: Cross-environment enforcement contracts for multi-agent fleets

**The question:** When multiple agent runtimes (different CLIs, different models, external workers) share the same workspace, how is a unified enforcement contract maintained?

**Specific questions:**
- Does anyone run a shared authority/supervisor layer across heterogeneous agent runtimes?
- How do Git-based integration gates (pre-commit hooks, CI checks) serve as the shared contract layer — and what are their limitations?
- What are the patterns for "the supervisor owns the state machine; agents propose transitions"?
- How do fleets handle the case where one agent runtime has stronger sandboxing than another?

**Disconfirming search:** "cross-environment enforcement impractical" / "each agent runtime needs its own enforcement" / "shared contracts create coordination overhead that negates benefits"

### Track 4: Windows-specific sandboxing and isolation for AI agents

**The question:** The wiki's sandboxing research is Linux/microVM/gVisor focused. What are the practical Windows-specific patterns for isolating AI agent file/process/network access?

**Specific questions:**
- Windows AppContainer, job objects, integrity levels — which are practical for constraining an LLM agent's spawned processes?
- How do Windows ACLs + junction points + restricted tokens compare to Linux namespaces for agent isolation?
- Are there Windows equivalents of gVisor or Firecracker that work for desktop AI agent workflows?
- What does Windows Sandbox (the lightweight VM feature) offer for running untrusted agent-generated code?
- Practical patterns for "write access only to authorized paths" on Windows without breaking legitimate work

**Disconfirming search:** "Windows sandboxing insufficient for AI agents" / "OS-level isolation too coarse for agent intent" / "Windows ACLs too complex to manage per-session"

### Track 5: Invocation-scoped resource budgets and semantic verification gates

**The question:** How do agent systems enforce per-invocation spending limits and semantic (not lexical) verification before allowing completion?

**Specific questions:**
- Patterns for API/resource budgets scoped to a single task invocation, enforced at the network-call boundary (not at the model's discretion)
- How do platforms prevent "the agent spent 33K API units without asking" — is there prior art for budget capabilities?
- Semantic verification gates: beyond "tests passed" and "receipt exists," what frameworks verify "production caller reaches the new path" or "provider failure reaches the next provider"?
- Provider failover vs selection: how do multi-provider systems (not just AI — any multi-backend system) handle graceful degradation when the primary fails?

**Disconfirming search:** "per-invocation budgets too granular to enforce" / "semantic verification gates are just more tests" / "failover patterns don't transfer from non-AI systems"

## Output requirements

For each track, produce:
1. **What the field actually does** — concrete frameworks, tools, papers, not theory
2. **Empirical evidence** — measured outcomes, not just "this pattern exists"
3. **Implementation patterns** — how someone would build it
4. **Failure modes** — where each approach breaks, with specific examples
5. **Applicability to our decision** — does this evidence favor minimal, balanced, or maximum configuration?

**Final synthesis question:** Given all five tracks, which configuration (minimal hooks, balanced broker+hooks+sandbox, maximum supervisor) does the external evidence support for a solo operator running a multi-agent fleet on Windows with universal file access?
