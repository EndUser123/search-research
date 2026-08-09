---
title: "Liveness vs timeout for agent pipeline polling loops: when heartbeat helps and when it's overkill"
created: 2026-08-09
source: session-2026-08-09 /www + /tp research
tags: [agent-orchestration, polling, timeout, liveness, heartbeat, durable-execution, research, ship-py]
summary: >
  Production agent orchestrators (Temporal, Inngest, Cadence) separate liveness
  (short heartbeat timeout) from overall duration (long backstop timeout). But
  for single-host pipelines like ship-py, a full heartbeat system is overkill —
  the simpler pattern is progress-file-mtime. HOWEVER: the /tp critique surfaced
  that the hunk-log-mtime signal (file edits) produces false positives on
  read-heavy phases (review agents reasoning for 5+ min without editing), and
  that the problem itself (premature cutoff of legitimate agents) may be
  hypothetical. The pragmatic answer: measure whether the problem exists first;
  if not, just increase the timeout config. The research is durable; the
  implementation decision should follow the measurement.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
type: concept
confidence: 0.85
last_verified: 2026-08-09
half_life_days: 365
sources:
  - "https://www.xgrid.co/resources/temporal-ai-agent-orchestration-failure-patterns/" (Temporal heartbeat patterns for AI agents)
  - "https://www.spheron.network/blog/ai-agent-workflow-orchestration-temporal-inngest-restate-gpu-cloud/" (durable execution comparison)
  - "https://blog.promaton.com/a-simple-solution-for-configuring-liveness-probes-for-queue-consumers-in-kubernetes-2897930382ca" (progress-file-mtime for small scale)
  - "https://www.agentcenter.cloud/blogs/ai-agent-monitoring-best-practices-2026" (agent monitoring best practices)
  - "https://agents.stackoverflow.com/blueprints/e17a499e-a439-48e9-8124-597b2241a6e9" (wedged agent detection)
relations:
  - target: wiki/concepts/polling-loop-continuation-controller-design-decision.md
    type: extends — that concept ships the polling loop; this research informs the timeout tuning
  - target: wiki/concepts/making-llm-agents-honestly-execute-skills-solution-stack.md
    type: related — durable execution patterns from the solution families
---

# Liveness vs timeout for agent pipeline polling loops

## Decision context

ship-py's polling loop (`run_all.py`) uses a single wall-clock deadline (`poll_timeout`, default 600s) to bound how long it waits for LLM-produced findings at pause phases (review, risk, fix, refactor). This conflates two distinct concerns: "is the agent still alive?" (liveness) and "has this run exceeded any reasonable bound?" (overall duration). The operator asked: how do we avoid cutting off agents that are legitimately working but exceed the magic number?

This research informs [[polling-loop-continuation-controller-design-decision]] — the polling loop is shipped; this addresses its timeout tuning. The broader context is [[making-llm-agents-honestly-execute-skills-solution-stack]] — durable execution patterns from the solution families.

## Key findings

### The production pattern: separate liveness from duration (HIGH confidence)

Temporal, Inngest, Cadence, and LangGraph all separate two timeout types:
- **HeartbeatTimeout (short, 30-60s):** detects dead workers fast. The activity emits a heartbeat; if it stops, the activity is marked timed out and retried.
- **StartToCloseTimeout / ScheduleToCloseTimeout (long, minutes-hours):** the overall ceiling. A heartbeating activity runs until this expires.

The key insight: **liveness timeout is SHORT; overall timeout is LONG.** A dead agent is detected in 60-90s (heartbeat missed), not 600s. A working agent runs as long as it keeps heartbeating, up to the overall ceiling.

### For single-host scale: progress-file-mtime is the simpler equivalent (HIGH confidence)

A full Temporal-style heartbeat system (dedicated threads, worker queues, network endpoints) is overkill for a single-host pipeline. The simpler, equally-effective pattern: the agent periodically writes/touches a progress file; the orchestrator checks the file's mtime. If mtime is recent (within threshold), the agent is live AND making progress.

This is dual-purpose: the file content provides human-readable progress AND the mtime provides liveness. Zero extra dependencies.

### The false-positive risk: read-heavy phases (MEDIUM confidence — /tp critique)

The /tp critique surfaced the critical weakness of file-edit-based liveness signals: **review agents spend extended periods reading and reasoning without editing files.** An agent analyzing a large diff for 5 minutes produces no hunk-log entries, no file writes. A 120s liveness check would falsely declare it dead.

This disqualifies the naive "hunk-log-mtime as liveness signal" approach for read-heavy phases. A **progress sidecar** (a file the agent is explicitly instructed to touch every 30s while working) solves this, but adds an instruction the agent must follow — moving the liveness signal from "observed" to "instructed," which reintroduces the compliance-gap problem.

### The wedged-agent problem is unsolved by both approaches (MEDIUM confidence)

Neither timeout nor heartbeat cleanly detects a **wedged agent** — one that is alive, editing files, but stuck in a loop and not converging on findings. The hunk log keeps updating (false liveness); the agent just isn't producing results. Only domain-specific progress semantics (e.g., "findings file not growing") could catch this, and even that produces false positives on legitimate iterative work.

The honest answer: wedged agents are caught by the **overall timeout backstop** + operator observation, not by liveness signals. This is an inherent limitation. See [[specification-gaming-in-llm-agent-pipelines]] for why behavioral compliance ("touch the progress file") reintroduces the activation-gap problem — the agent may skip the heartbeat instruction under closure pressure, just as it skips other instructions.

## What this means for ship-py

### Tiered recommendation (measure before building)

1. **First: measure whether the problem exists.** Check `_timed_out_<phase>` markers in ship-py state files. If no legitimate timeout has occurred on working agents, the problem is hypothetical. Action: increase `poll_timeout` default from 600s to 1800s (one config change). Close the work item.

2. **If legitimate agents ARE getting cut off:** implement a progress-sidecar pattern. The PAUSE_INSTRUCTIONS for each pause phase add: "touch `P:/.artifacts/ship-py/<sid>/progress-<phase>.txt` every 30s while working." The polling loop checks this file's mtime instead of (or in addition to) the wall-clock deadline. Liveness timeout: 180s (6 missed heartbeats). Overall timeout: 1800s backstop.

3. **For wedged agents:** the overall timeout (1800s) is the backstop. No liveness signal solves this cleanly. Operator observation remains the tertiary detection.

### What NOT to do

- **Do not use hunk-log-mtime as the sole liveness signal.** False positives on read-heavy phases (review agents reasoning without editing).
- **Do not build a full heartbeat system** (dedicated threads, worker queues). Overkill for single-host scale; the progress-file pattern achieves the same result with zero dependencies.
- **Do not add liveness logic without evidence the problem exists.** The /tp critique correctly identified that the complexity (two thresholds, _agent_is_alive logic, signal dependency) is unjustified without measured incidents. This is the [[evidence-first-default-and-needless-confirmation]] principle — measure before building.

## Falsifier

This analysis is wrong if:
- The 600s timeout is already generous and no legitimate agent has ever been cut off (problem is purely hypothetical — measure first)
- Review agents in this workspace routinely go 5+ minutes without ANY file operation (hunk-log signal is useless — needs progress sidecar instead)
- The common failure mode is wedged agents (alive but looping), not dead agents — in which case neither liveness signals nor timeouts help, and only domain-specific progress tracking (findings-file growth) would catch it

## Receipts

- **Temporal heartbeat pattern:** HeartbeatTimeout 30-60s alongside StartToCloseTimeout (minutes-hours). Source: xgrid.co/resources/temporal-ai-agent-orchestration-failure-patterns
- **Progress-file-mtime for small scale:** "a simple progress file whose mtime acts as the signal is sufficient and often better" for single-host. Source: blog.promaton.com (Kubernetes liveness probes for queue consumers)
- **Wedged agent detection limitation:** "agents can get wedged while still emitting heartbeats. Pure liveness only tells you the process is running, not that it's useful." Source: agents.stackoverflow.com/blueprints
- **/tp critique (REVISE verdict):** identified hunk-log false-positive risk, questioned whether the problem is real, suggested simpler "increase timeout" alternative, noted wedged-agent case is unsolved. Source: session 2026-08-09, or-arcee-ai-trinity-large-thinking

## Sources

- [Temporal AI Agent Orchestration Failure Patterns](https://www.xgrid.co/resources/temporal-ai-agent-orchestration-failure-patterns/) (xgrid, 2026 — heartbeat + timeout patterns)
- [AI Agent Workflow Orchestration: Temporal, Inngest, Restate, GPU Cloud](https://www.spheron.network/blog/ai-agent-workflow-orchestration-temporal-inngest-restate-gpu-cloud/) (Spheron, 2026 — durable execution comparison)
- [Simple Liveness Probes for Queue Consumers](https://blog.promaton.com/a-simple-solution-for-configuring-liveness-probes-for-queue-consumers-in-kubernetes-2897930382ca) (Promaton — progress-file-mtime pattern)
- [AI Agent Monitoring Best Practices 2026](https://www.agentcenter.cloud/blogs/ai-agent-monitoring-best-practices-2026) (AgentCenter — heartbeat tracking, stuck detection)
- [Wedged Agent Detection](https://agents.stackoverflow.com/blueprints/e17a499e-a439-48e9-8124-597b2241a6e9) (Stack Overflow Agents — liveness vs progress distinction)

## Auto-related

- [[Are-there-repos-or-solutions-to-claude-code-gettin]]
- [[polling-loop-continuation-controller-design-decision]]
- [[subprocess-run-timeout-deadlock-windows]]
- [[hook-evidence-collection-cost-vs-timeout-tradeoff]]
- [[orchestrator-controlled-cross-model-validation-ship-py]]

