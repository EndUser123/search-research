---
title: "Solo-director AI-coder fleet: coordination, isolation, and stale-data immunity best practices"
created: 2026-07-27
source: session-019fa5a1 (/www research)
tags: [multi-agent, fleet-coordination, worktrees, isolation, stale-data, concurrency, solo-operator, best-practices, research, cross-host]
summary: >
  External research on best practices for a solo director operating a fleet of
  AI coders with multi-terminal isolation and stale-data immunity. Three
  sub-areas researched in parallel (coordination architecture, stale-data
  immunity, terminal/process isolation) + disconfirmation pass. The field
  consensus confirms our worktree-first approach as the right isolation
  primitive, but the disconfirmation (CooperBench: one strong agent beats
  coordinated fleets ~2×) qualifies the fleet-as-default premise. The
  highest-signal finding: filesystem isolation (worktrees, atomic writes)
  addresses the WRONG layer for the dominant failure mode — agents fail at
  semantic coordination (63% of failures are expectation mismatches), not
  at filesystem contention. The fix is not more isolation; it is smaller
  fleets with stronger per-agent tasks + independent verification.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - "CooperBench (Stanford et al. 2026): https://cooperbench.com/blog/curse-of-coordination — 600+ collaborative coding tasks across 12 OSS libraries"
  - "MAST taxonomy (Cemri et al. 2025, arxiv 2503.13657): multi-agent failure modes, 1600+ traces"
  - "Augment Code parallel-agent guide: https://www.augmentcode.com/guides/git-worktrees-parallel-ai-agent-execution"
  - "asklar.dev fleet lessons: https://asklar.dev/ai/tools/2026/03/24/agent-fleet-lessons.html"
  - "Anthropic multi-agent research system: https://www.anthropic.com/engineering/multi-agent-research-system"
  - "Galileo 'Why Multi-Agent Systems Fail': https://galileo.ai/blog/why-multi-agent-systems-fail"
  - "LevelUp '371 git worktrees': https://levelup.gitconnected.com/what-371-git-worktrees-taught-me-about-multi-agent-ai-36d4d61acfb5"
  - "Token Coherence (arxiv 2603.15183): MESI-like coherence for agent context"
relations:
  - target: wiki/concepts/git-worktree-multi-terminal-best-practices.md
    type: extends — that page covers the worktree mechanics; this adds the fleet-coordination + disconfirmation layer
  - target: wiki/concepts/multi-agent-correlated-errors.md
    type: complements — that page covers review diversity; this covers fleet coordination diversity
  - target: wiki/concepts/trust-escalation-ladder-autonomous-agent-work.md
    type: related — trust rungs govern how much fleet autonomy is safe
  - target: wiki/concepts/auto-commit-authority-isolation.md
    type: related — per-session auto-commit is the worktree companion
  - target: wiki/concepts/close-scanner-verification-gap-stale-read.md
    type: related — stale-data immunity in the close scanner
---

# Solo-director AI-coder fleet: coordination, isolation, and stale-data immunity

## Decision context

**Why this research was needed.** This workspace runs a fleet of AI coders
(Grok Build, Claude Code, Codex) on a shared Windows filesystem under a solo
director. The session's prior work (close-authority implementation, /check,
/review) surfaced coordination failures: stale data, split verdicts, and
self-verification gaps. The operator asked: what do external practitioners and
research recommend for this architecture? Specifically: coordination patterns
for a single approver, multi-terminal isolation, and stale-data immunity.

**What alternatives were explored.** Three sub-areas researched in parallel
(M3 subagents): (1) fleet coordination architecture, (2) stale-data immunity
patterns, (3) terminal/process isolation. A disconfirmation pass searched
for evidence against the emerging conclusions (CooperBench, MAST taxonomy,
practitioner post-mortems).

**What the research changed.** Confirmed our worktree-first approach is the
field consensus for isolation. But the disconfirmation surfaced a critical
qualification: the dominant failure mode is NOT filesystem contention — it is
semantic coordination breakdown (63% of multi-agent failures are expectation
mismatches). This redirects attention from "more isolation" to "smaller fleets
with stronger per-agent task definition + independent verification."

## The five-pillar consensus (what the field agrees on)

External sources converge on five pillars for a solo-director AI-coder fleet:

| Pillar | Technique | Our wiki coverage |
|---|---|---|
| **1. Worktree-per-agent isolation** | Each agent gets its own working directory + branch + index sharing one object store. Converts silent overwrites into visible merge conflicts. | ✅ [[git-worktree-multi-terminal-best-practices]] |
| **2. Three-tier architecture** | Coordinator (plans, no code) → Specialists (parallel impl in worktrees) → Verifier (independent check). Spec is the coordination artifact. | ✅ /go profile pattern + /check + /review |
| **3. Atomic writes + monotonic versioning** | tmp + fsync + rename for file atomicity; content-hash or version keys for artifact freshness. Readers fetch by reference, not by "newest file." | ✅ [[close-scanner-verification-gap-stale-read]] + handoff accurate_as_of_head |
| **4. Scoped shared state** | Per-agent ports (hashed from branch), separate DB files/schemas, scoped credentials, prefixed container names. The most commonly missed layer. | ⚠️ Partial — we scope .artifacts/<terminal>/ but don't isolate ports or DBs |
| **5. WIP limits + kill criteria** | Hard cap at 3–5 concurrent agents (token costs scale linearly; 5 scattered < 3 focused). Kill agents stuck 3+ iterations on same error. One file, one owner. | ⚠️ Not formalized — we auto-commit per session but don't enforce fleet-size limits |

## What people like (adoption evidence)

### Worktree isolation [HIGH confidence — multi-source]
Git worktrees are the universal recommendation for ≥2 concurrent agents on the
same repo. The mechanism: independent working directory + branch + index,
shared object store. `index.lock` contention disappears. Uncommitted edits are
invisible across worktrees. Our wiki already documents this extensively.

### Three-tier coordinator-specialist-verifier [HIGH confidence]
Anthropic's multi-agent research system, Augment Code's parallel guide, and
multiple practitioner reports converge on this architecture. The coordinator
owns planning and never writes code; specialists implement in parallel; an
independent verifier checks against the spec before merge. Our `/go` (H4
parallel) + `/check` + `/review` pipeline implements this pattern.

### Atomic writes with monotonic versioning [HIGH confidence]
The `tmp + fsync + rename` pattern (POSIX atomic) combined with content-hash
or version-keyed artifact references is the standard freshness pattern. Our
handoff `accurate_as_of_head` binding and the close-authority receipt digest
are instances of this. The principle: never select by "newest file" — select
by explicit identity + content hash.

### Copy-on-write sandbox snapshots [MEDIUM confidence — emerging]
Pre-bake a golden image (toolchain + base config), fork per-agent sandboxes
via CoW (btrfs/APFS/Firecracker overlays) in <1s. Combines container-grade
isolation with worktree-grade speed. Avoids the dependency-install tax.
We don't implement this yet — our worktrees share the host environment.

### tmux/dashboard coordination surface [MEDIUM confidence — practitioner]
Launch each agent in its own tmux pane or dashboard window so the operator
can watch, intervene, and tear down independently. Essential for fleet
observability. Our multi-terminal setup approximates this.

## What people don't like (disconfirmation — the critical qualification)

### 1. One strong agent beats a coordinated fleet [HIGH confidence — CooperBench]

**This is the highest-signal finding from the entire research.** CooperBench
(Stanford et al., 600+ tasks across 12 OSS libraries) found:
- Solo agents succeed ~2× more often than paired agents on feature-split tasks
- Scaling to 3–4 agents degrades success rates (~69% → ~30%)
- Communication tools cut merge conflicts but do NOT improve success rates
- Agents spend up to 20% of action budget talking; outcomes stay poor

**Implication for our workspace:** the fleet is not a throughput multiplier.
It is a risk-distribution mechanism. The right question is not "how many
agents?" but "what is the smallest fleet that covers the independent work
surfaces?" WIP limits of 3–5 are not just cost management — they are
success-rate optimization.

### 2. Worktrees isolate filesystems, not semantics [HIGH confidence]

Agents touch hotspot files (routes, configs, type definitions, schema, barrel
exports) regardless of worktree isolation. Lockfile divergence (`package-lock.json`)
creates massive merge diffs. Build/cache contamination (`.next/`, `dist/`) yields
stale outputs across worktrees.

**Implication:** worktree isolation is necessary but insufficient. The conflicts
that matter are semantic, not filesystem. Our [[handoff-fragmentation-under-recurrence]]
finding is an instance: the chain is explicit but one-directional — filesystem
isolation doesn't propagate status updates backward.

### 3. 63% of multi-agent failures are expectation mismatches [HIGH confidence — MAST]

The MAST taxonomy (1600+ traces across ChatDev, MetaGPT, AutoGen) attributes
31–37% of failures to inter-agent misalignment: conversation reset, task
derailment, information withholding, ignoring other agents' input. CooperBench:
expectation mismatches alone account for ~63% of failures.

**Implication:** scoped shared state assumes agents will respect boundaries.
The data says they don't. State-sharing is WHERE agents go wrong, not HOW they
go right. Our [[multi-agent-correlated-errors]] concept documents this for
review; this extends it to fleet coordination.

### 4. The human-attention bottleneck breaks at 4–6+ agents [MEDIUM confidence]

Practitioner post-mortems (asklar, startuphub.ai) name the operator's attention
as the first thing that breaks. The operator becomes scheduler, shared memory,
and reviewer simultaneously. Context-switching fails.

**Implication:** the trust-escalation ladder ([[trust-escalation-ladder-autonomous-agent-work]])
must include a fleet-size rung. More autonomy per agent is not the same as
more agents — each agent added increases the operator's coordination surface.

### 5. Atomic writes are the wrong layer [MEDIUM confidence]

Even with per-file atomicity, agents rewrite large parts of the repo mid-run,
invalidating siblings' work. Worktree `index.lock` goes stale after crashes.
One practitioner reports 371 worktrees consuming 172GB.

**Implication:** atomic writes solve torn reads but not semantic invalidation.
Our [[close-scanner-verification-gap-stale-read]] concept is an instance: the
scanner read was atomic but the state it read was semantically stale.

## Stale-data immunity patterns (the three freshness models)

External research identifies three freshness models, each with trade-offs:

| Model | Mechanism | Strength | Weakness | Our implementation |
|---|---|---|---|---|
| **Time-based** | TTL / max-age on artifacts | Simple; no coordination needed | Wrong proxy for staleness (a 1-min-old read can be stale if state changed) | `MAX_RECEIPT_AGE_SECONDS` in close_authority.py |
| **Content-based** | SHA256 / version hash on artifact | Precise — detects actual change | Requires re-hashing on every read; doesn't detect semantic staleness | `report_sha256` binding in AAR receipts; `accurate_as_of_head` in handoffs |
| **Provenance-based** | Who wrote it, when, through what process | Strongest — binds authority to producer | Requires producer attestation the consumer can verify | ⚠️ Gap — the close-authority INTG-1 finding showed this is missing |

**The provenance gap is the load-bearing finding.** Content-based freshness
detects tampering but not forgery (the forger can write valid content). Only
provenance-based freshness — "this artifact was produced by the authoritative
process, not by the model" — closes the trust boundary. This is exactly what
the /review found (INTG-1: forgeable AAR receipts).

## What this means for our workspace

### Confirmed: our approach is sound for isolation
- Worktree-per-session: ✅ field consensus
- Auto-commit-per-session: ✅ prevents silent overwrites
- Terminal-scoped .artifacts/: ✅ prevents cross-terminal clobber
- Content-hash binding (accurate_as_of_head, report_sha256): ✅ detects tampering

### Gaps the research surfaced
1. **Producer provenance (provenance-based freshness).** Content hashes detect
   tampering but not forgery. The model can write valid-content artifacts. We
   need a producer-attestation mechanism — exactly the INTG-1 finding from /review.
2. **Scoped shared state beyond .artifacts/.** We isolate artifacts by terminal
   but don't isolate ports, DB files, or credentials per agent. The research
   says this is the most commonly missed layer.
3. **Fleet-size governance.** No formal WIP limit. The research says >5 agents
   degrades success rates AND overwhelms the operator's attention. We should
   formalize a fleet-size rung in the trust ladder.
4. **Semantic conflict detection.** Worktrees isolate filesystems but not
   semantics. We need pre-merge semantic checks (not just `git diff`).

### What NOT to do (disconfirmed)
- Don't add more agents to increase throughput (CooperBench: success rate drops)
- Don't rely on inter-agent communication to coordinate (63% expectation mismatch)
- Don't treat filesystem isolation as sufficient (semantic conflicts dominate)
- Don't let worktree count grow unbounded (371 worktrees = 172GB = management problem)

## Falsifier

This concept is wrong or obsolete if:
- A future study shows multi-agent fleets outperforming solo agents on the same
  tasks (would overturn CooperBench). The evidence currently strongly disconfirms.
- Producer-provenance mechanisms become standard in AI-agent frameworks, making
  the INTG-1 class of bypass structurally impossible. Until then, the gap is real.
- Our own fleet-size measurements show >5 agents succeeding without coordination
  overhead. Would require controlled comparison on this workspace's tasks.

**Discriminating test:** run a controlled A/B: 3 agents on 3 independent tasks
vs 6 agents on 6 independent tasks. Measure: success rate, operator intervention
count, merge conflicts. If 6-agent success rate ≥ 3-agent, the CooperBench
finding doesn't apply to our task shape.

## Sources

## Receipts

Claims about local workspace implementation are grounded in cited wiki concepts
and session artifacts, not inferred:

- [FACT] Worktree-per-session is the workspace standard — `P:/.data/wiki/concepts/git-worktree-multi-terminal-best-practices.md` documents the pattern; ADR-008 codifies it. Verified by reading this session.
- [FACT] Auto-commit-per-session is standing policy — `C:\Users\brsth\.grok\AGENTS.md` § "Working in the shared main tree" rule 1: "Commit after each logical unit of work — automatically, without asking." Verified by reading AGENTS.md this session.
- [FACT] Terminal-scoped `.artifacts/` — `P:/.artifacts/<termSafe>/` convention is documented in /check and /review SKILL.md Step 0. Verified by reading both skills this session.
- [FACT] Content-hash binding via `accurate_as_of_head` — `C:\Users\brsth\.grok\skills\handoff\SKILL.md` § "Chain header" requires `accurate_as_of_head` from `git rev-parse HEAD` at write time. Verified by reading the skill this session.
- [FACT] Producer provenance gap (INTG-1) — `/review` finding INTG-1 confirmed empirically: a forged `_run.json` at `skills/aar/.artifacts/<session>/` produces CLOSE COMPLETE. Receipt: verify_intg1.py run this session printed `BYPASS SUCCESSFUL: True`.
- [FACT] No formal WIP limit — `grep -r "WIP.limit\|fleet.size\|max.agents\|concurrent.limit" P:/.data/wiki/concepts/ C:\Users\brsth\.grok\AGENTS.md` returns no policy-level hits. [INFERENCE] the absence of a formal limit means none is enforced.
- [INFERENCE] Scoped shared state gap — we isolate `.artifacts/` by terminal but the research says ports/DBs/credentials are the commonly missed layer. Whether this workspace has port conflicts is unmeasured. Would require: check for port-assignment conventions across active sessions.

## Sources

- [CooperBench "Curse of Coordination"](https://cooperbench.com/blog/curse-of-coordination) (Stanford et al. 2026) — the strongest disconfirmation; controlled experiment
- [MAST taxonomy (arxiv 2503.13657)](https://arxiv.org/pdf/2503.13657) (Cemri et al. 2025) — multi-agent failure mode classification
- [Augment Code parallel guide](https://www.augmentcode.com/guides/git-worktrees-parallel-ai-agent-execution) — practitioner worktree patterns
- [asklar.dev fleet lessons](https://asklar.dev/ai/tools/2026/03/24/agent-fleet-lessons.html) — solo-operator post-mortem
- [Anthropic multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — three-tier architecture reference
- [Galileo "Why Multi-Agent Systems Fail"](https://galileo.ai/blog/why-multi-agent-systems-fail) — failure mode analysis
- [LevelUp "371 git worktrees"](https://levelup.gitconnected.com/what-371-git-worktrees-taught-me-about-multi-agent-ai-36d4d61acfb5) — scaling limits
- [Token Coherence (arxiv 2603.15183)](https://arxiv.org/abs/2603.15183) — MESI-like coherence for agent context

---

## Revision 1 — 2026-07-27T17:15:00Z (session 019fa5a1)

**Trigger:** the operator challenged the CooperBench conclusion with a sharper
frame: "if you decompose into non-blocking streams, you get more done. You may
increase error rate, but blast radius is smaller. Fixes are smaller. What's the
real tradeoff?" This revision corrects an over-reading of CooperBench in the
original concept.

### The assumption CooperBench made that we missed

**CooperBench tested INTERDEPENDENT overlapping tasks, not independent decomposed
streams.** From the paper (arXiv 2601.13295 §2.1): "each task assigns two agents
different features that can be implemented independently but may conflict without
proper coordination." 77.3% of tasks have conflicting ground-truth solutions.
The features touch the SAME FILES. This is the hard case — coordination is required
because the work overlaps.

**Our workspace runs the opposite case:** independent decomposed streams where
agents work on non-overlapping files in isolated worktrees. CooperBench's "curse
of coordination" applies to the overlapping case, NOT to ours. The original
concept's conclusion ("smaller fleets with stronger per-agent tasks") was
correct for the wrong reason — it overgeneralized from a benchmark that tested
a different task shape.

### The real tradeoff (blast radius vs error rate)

The operator's intuition is mathematically correct. For N independent streams
each succeeding at rate p, with blast radius 1/N per stream:

- **Best-of-N:** P(at least one succeeds) = 1 - (1-p)^N. For p=0.3, N=5 -> 83.2%. For p=0.5, N=10 -> 99.9%.
- **Blast radius compensation:** net damage = (error_amplification x (1-p) x T) / N.
  - Independent topology: A_e = 17.2x (Google Research, arXiv 2512.08296)
  - Centralized (orchestrator): A_e = 4.4x
  - Parallel beats monolithic when N > A_e x (1-p). For centralized, N >= 3 suffices.

**The tradeoff is real and favors decomposition** -- but only under three conditions:
1. **Errors are uncorrelated** (different models, different prompts, different frames -- not N copies of the same brief). Without this, N=3 barely beats N=1 ([[multi-agent-correlated-errors]]).
2. **There is a verifier at the seam** (unit tests, LLM judge, orchestrator). Without it, independent topology's 17.2x error amplification dominates.
3. **N is bounded** (3-5 optimal; coordination overhead scales as n^1.724 per Google).

### How Anthropic actually solves the error-rate problem

Anthropic's multi-agent research system (engineering blog, Jun 2025):
- Runs **3-5 subagents in parallel** (typical), 10+ for complex research
- Uses **independent, non-blocking streams** -- subagents don't communicate with each other, only return condensed findings to the lead
- Lead agent is Opus 4 (stronger); subagents are Sonnet 4 (cheaper) -- 1:N ratio
- Error handling: **resume + adapt**, not kill-switch. Let the agent know when a tool fails and let it adapt. Combined with retry logic and regular checkpoints.
- **Not a "surplus" approach** -- they explicitly corrected against spawning 50 agents. Each subagent's result IS the result; no "use the best of N" selection step.
- +90.2% improvement over single-agent Opus 4 on research evals, at 15x token cost
- **Explicitly notes multi-agent underperforms on coding tasks** that need shared context -- but our workspace uses worktree isolation precisely to AVOID shared context

### Corrected conclusion

The original concept's headline ("one strong agent beats fleet ~2x") is **overgeneralized**. It applies to:
- Interdependent overlapping tasks (CooperBench's design)
- Tasks requiring shared context (Anthropic's caveat)

It does NOT apply to:
- Independent decomposed streams (our worktree-per-session model)
- Tasks with verifier-gated aggregation (our /check + /review pipeline)
- Best-of-N patterns with uncorrelated errors

**The corrected guidance:** decompose into non-blocking independent streams.
Accept higher per-stream error rate. Use small blast radius (worktree isolation)
to make fixes cheap. Add a verifier at the seam. Bound N at 3-5. This is the
optimal architecture for a solo director -- and it is exactly what our workspace
already does, minus the formal fleet-size limit and the verifier-before-verdict gate.

### What stays valid from the original

- Worktree isolation is still the right primitive
- Auto-commit-per-session is still correct
- Terminal-scoped artifacts are still needed
- Content-hash binding is still the freshness mechanism
- The 63% expectation-mismatch finding (MAST) still applies to INTERDEPENDENT tasks

### What changes

- The "smaller fleets" recommendation was right for the wrong reason. The real reason is coordination overhead scaling (n^1.724), not the curse of coordination (which applies to overlapping tasks).
- The CooperBench disconfirmation should be qualified: "applies to interdependent overlapping tasks, not independent decomposed streams"
- Best-of-N / surplus-of-agents is a validated pattern we should consider for high-stakes single-answer tasks (not for parallel implementation streams)

### Additional sources (Revision 1)

- [Google Research, "Towards a Science of Scaling Agent Systems"](https://arxiv.org/abs/2512.08296) (Kim et al., Dec 2025) -- error amplification factors by topology; the quantitative backbone of the blast-radius math
- [CooperBench paper](https://arxiv.org/html/2601.13295v1) (arXiv 2601.13295) -- methodology confirmation: interdependent overlapping tasks, not independent streams
- [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system) (Jun 2025) -- production architecture: 3-5 subagents, independent streams, resume+adapt error handling
- [AlphaCode](https://arxiv.org/abs/2203.07814) (Li et al., DeepMind) -- best-of-N at extreme scale
- [S*](https://arxiv.org/abs/2502.14382) (Li et al., 2025) -- hybrid parallel+sequential+adaptive selection
- [Snell et al. test-time compute](https://arxiv.org/abs/2408.03314) (2024) -- compute-optimal BoN
