---
title: Bounded-run envelope and autonomy-tier patterns for agent operation
slug: overnight-controller-and-autonomy-tier-patterns
tags: [autonomous-agents, agent-guardrails, automation-lanes, policy-as-code, unattended-operation, research, bounded-run-envelope]
status: active
verification: multi-source
confidence: 0.78
source_skills: [www]
researched: 2026-08-07
accurate_as_of_head: pending
relations:
  - "[[trust-escalation-ladder-autonomous-agent-work]]"
  - "[[invariants-beat-environment-comfort]]"
  - "[[evidence-driven-experiment-loop]]"
  - "[[concurrent-cdp-auth-contention]]"
  - "[[chronic-git-state-hygiene-shared-tree-is-structural]]"
  - "[[solution-unit-validation-before-build]]"
---

# Bounded-run envelope and autonomy-tier patterns

## Note on framing (2026-08-07)

This concept was originally written as "overnight controller" research.
A subsequent `/tp` critique dissolved that framing: the overnight
controller is a special case of a **bounded-run envelope** — the
capability that lets parallel waves, background runs, and overnight
runs all operate with explicit bounds, receipts, and abort gates. The
overnight case adds only (a) a scheduler trigger and (b) a morning
receipt format; everything else is the envelope, which is more
valuable for the frequent daytime parallel-run case than for the rare
overnight case. See `[[solution-unit-validation-before-build]]` for the
reframe pattern that produced this correction.

The research below remains valid as design vocabulary for the envelope.
The "overnight controller" build target itself is deferred until the
operator confirms a real overnight-progress need; the envelope's
high-ROI pieces (manifest table in AGENTS.md, per-commit confidence in
`/close`) are the actual recommendations.

## Decision context

An "overnight controller" design was proposed for unattended yt-is work: an
isolated worktree, snapshot, safe-work auto-run, cheaper-model delegation,
adversarial review, commit-to-branch-only, optional authorized live smoke,
and a morning receipt with confidence-tagged merge recommendations. The
operator asked which ideas are worth copying into **normal (interactive)
skills**, and where to apply them.

This concept captures the external prior art (so we do not re-research it),
the workspace-counterexamples that limit the proposals, and the refined
recommendations that survived a fresh-lens critique against our actual
skill graph.

## What the field already does (prior art)

### Autonomy-tier / lane separation (every adjacent field converges)

| Field | Named pattern | Portable element |
|---|---|---|
| Aviation | Sterile cockpit (14 CFR §121.542) | Restriction level changes by phase, not just by actor |
| Autonomous vehicles | SAE J3016 levels + Operational Design Domain (ODD) | Level × conditions envelope + Minimal Risk Condition (abort) |
| CI/CD | Progressive delivery (canary/staged/prod) | Tiered environments, metric-gated promotion |
| Cloud/SRE | Blast radius + fail-closed vs fail-open | Default-deny on the most powerful tier |
| Trading | Paper → sim → live capital | **Predefined graduation criteria defined in advance** |
| AI agent domain | Feng et al. (arXiv:2506.12469), Bessemer L0-L6, ObserveID 4-tier | Reversibility × blast radius as the axis |

No field uses the name "lane separation." Closest named equivalents are
**Operational Design Domain** (AVs) and **Progressive Delivery** (CI/CD).
The most directly portable structural elements: predefined graduation
criteria (trading), blast-radius-by-reversibility (K8s/ObserveID), Minimal
Risk Condition/exit behaviour (AVs), fail-closed defaults on the top tier.

### Allowed/never-automatic manifests (pattern is established)

- **Microsoft Agent Control Specification (ACS)** — direct schema analogue:
  declarative policy manifest + intervention points (input, pre_tool_call,
  post_tool_call, output) + verdicts (allow/warn/deny/escalate/transform).
- **Claude Code permissions** — direct shipped example: `allow`/`deny`/`ask`
  rules + permission modes (`default`/`plan`/`acceptEdits`/`bypassPermissions`),
  deny-wins precedence. The operator already runs an instance.
- **Open Policy Agent (OPA) + Rego** — the enforcement engine (CNCF).
- **Kubernetes PodSecurityPolicy → Pod Security Admission** — architectural
  analogue; the PSP→PSS migration is a worked example of consolidating
  scattered policies into a tiered declarative table.

### Bounded overnight / unattended operation

- **Devin** — sandboxed ephemeral VMs, scoped repo/secret access, PR-as-output
  (never main), ACU (Agent Compute Unit) budgets, `--sandbox` Autonomous mode.
- **OpenAI Codex** — orthogonal **sandbox modes** (`read-only`/`workspace-write`/
  `danger-full-access`) × **approval policies** (`untrusted`/`on-request`/`never`);
  `/goal` continuation loop with stop conditions (completed/blocked/budget-soft-stop).
  Soft-stop-on-budget with wrap-up summary, not hard abort.
- **yurukusa cc-safe-setup (800h unattended)** — PreToolUse destructive-command
  blockers (exit 2) that fire even under `--dangerously-skip-permissions`;
  `mission.md` for cross-compaction state; DoD checklists. ~677-900 example hooks.
- **AutoGPT/BabyAGI failure modes** — the cautionary lineage: infinite/no-progress
  loops, cost exhaustion, compounding hallucinations, goal drift. Modern guardrails:
  hard limits (steps/tokens/wall-clock/spend/retries), no-progress detection via
  state fingerprints, explicit measurable termination criteria.
- **SWE-agent/SWE-bench** — Docker sandbox, Agent-Computer Interface guardrails,
  multi-layer abort (cost/step/timeout/consecutive-timeout/wall-clock). **On fatal
  condition, autosubmits a partial patch as "degraded success"** — the precedent
  for morning-receipt-with-blockers.
- **SRE for AI agent fleets** — error budgets by blast radius, circuit breakers with
  a **DEGRADED state** (not just OPEN/CLOSED), bulkheads per agent, idempotency keys
  (agent retries produce different reasoning paths), graduated recovery.

### Practitioner signal (Reddit r/LLMDevs, r/cursor, 2026)

- **Control-boundary pattern (IslamNofl, r/LLMDevs):** "the agent is tracker-blind"
  + "the agent doesn't own the PR" — orchestrator owns the policy gate; agent only
  commits to a branch. Validates "choose the final throughput winner — never automatic."
- **Domain-criticality lane (PuzzleheadedMenu2454, r/LLMDevs):** "the more load-bearing
  and correctness-critical the domain, the less you can hand the whole thing over" —
  auth/payments/data-model get line-by-line review; everything else is more autonomous.
  This is lane separation by domain, not just by action.
- **Test-gaming caveat (same thread):** "the agent optimizes for 'passes the test I can
  see,' not 'survives the ugly real response'" — a regression test the agent authors can
  be gamed; real captured payloads (incl. malformed) are the guardrail.
- **HuggingFace incident (r/LocalLLaMA, 1346pts):** autonomous AI agent attack where
  "the attacker was bound by no usage policy, while our forensic work was blocked by the
  guardrails" — real-world data point on guardrail asymmetry.

## Workspace-counterexample check

- `[[chronic-git-state-hygiene-shared-tree-is-structural]]` documents that 800h of
  unattended Claude Code showed auto-commit hooks themselves become a dirty-state
  source. **Limits:** any overnight design must not rely on auto-commit hygiene;
  worktree isolation is mandatory, not optional.
- `[[concurrent-cdp-auth-contention]]` and the multi-terminal isolation rule mean the
  LIVE lane (browser/cookie/auth state) is unsafe across concurrent terminals. **Limits:**
  overnight live-lane work must use per-profile isolated state files, not live browser state.
- `[[invariants-beat-environment-comfort]]` — generic best practices that violate host
  invariants are wrong for us even if correct for 99% of users. **Limits:** any pattern
  adopted from the field must pass the host-invariant check.
- The test-gaming caveat above means idea 5 (bounded-fix-requires-failing-test) is
  **necessary but not sufficient** — the test must be reality-grounded.

## Recommendations (refined after fresh-lens critique)

**For normal (interactive, operator-present) skills:**

1. **Confidence-tagged commits in `/close` output** — [SUPPORTED] [UNTESTED].
   Genuine gap: `/close`'s Verify field is binary PASS + free-text; `/go` already has
   profile-level confidence but not per-commit. Add per-commit H/M/L derived from the
   existing receipt validator's cleanliness (not invented). Small formatting change,
   maps to SWE-agent's autosubmit-degraded and Codex's blocked/budget-soft-stop patterns.
2. **Consolidated manifest table in AGENTS.md** — [SUPPORTED] [UNTESTED]. The trust-rung
   content already exists in prose; the gap is a scannable table an agent reads mid-wave
   in <5s. Use Claude Code's allow/deny/ask + ACS intervention-point schema. This is a
   DERIVATIVE/CONSOLIDATION of existing prose, not new policy.

**Explicitly NOT worth copying for interactive skills:**

3. **Three-lane concept as a standalone wiki page** — MISFRAMED. `/go` already has
   H0 (safe-git) / H3 (discover) / H6 (verify) packs that structurally cover the same
   separation. A parallel "lanes" concept creates two mental models cut on different axes.
   If the lane vocabulary is wanted, **annotate the H-packs** (H0=safe-lane, H3=evidence-lane,
   H6=live-lane) rather than create a parallel concept. Cleaner still: adopt ObserveID's
   reversibility tiers (Observe/Draft/Act-reversible/Commit-irreversible).
4. **Bounded-fix-requires-failing-test as a new rule** — REDUNDANT. Already 3-layer
   enforced: TDD skill (red→green), `/go` plan-execute `red_green` strategy requirement,
   `grok-verify` evidence rule. Adding a fourth wording changes nothing. DO capture the
   refinement the practitioner signal revealed: regression tests gating autonomous fixes
   must be operator-authored or reality-grounded, not agent-authored.
5. **Quarantine-and-continue for interactive waves** — overnight-only. `grok-parallel`
   already quarantines dirty/unmerged worktrees (line 141) and `/go` plan-execute PR DAG
   already cascade-skips failed PRs (line 757). For interactive runs the operator IS the
   continuation logic; auto-continuing past failure would reduce operator authority.

**For the overnight controller (if/when built):**

It is a **wiring task**, not a capability build. Foundations already owned:
`evidence-driven-experiment-loop` (decision packets, abort gates, promotion rules,
forbidden_actions), `grok-parallel` (worktree isolation), `/review` (adversarial review),
`/preflight` + `grok-safe-git` (snapshot). The durable additions to build, drawn from
prior art: (a) Windows Task Scheduler launcher + manifest-driven controller; (b) ACU-style
quota/step/wall-clock budget caps (Devin, SWE-agent); (c) `mission.md`-style cross-compaction
state (yurukusa); (d) autosubmit-degraded-on-fatal with blockers in the morning receipt
(SWE-agent); (e) DEGRADED circuit-breaker state, not just abort (SRE-for-agents).

## Falsifier

This concept is wrong if, within 6 months:
- The manifest table in AGENTS.md is never consulted mid-wave (operators/agents resolve
  via existing prose) — the table is ceremony.
- The overnight controller is built and its receipts are less trustworthy than interactive
  work because the quarantine/abort logic does not actually fire under failure.
- The H-pack lane annotation creates more confusion than the prose labels (operators report
  two-vocabulary friction).

## Sources

- SAE J3016 + ODD: sae.org/news/blog/sae-levels-driving-automation-clarity-refinements ; Applied Intuition ODD taxonomy
- Microsoft ACS: commandline.microsoft.com/agent-control-specification-runtime-governance
- Claude Code permissions: code.claude.com/docs/en/permissions
- Devin: docs.devin.ai (environment, security, gallery)
- OpenAI Codex: openai.com/index/running-codex-safely ; developers.openai.com (goals, long-horizon)
- yurukusa: github.com/yurukusa/cc-safe-setup ; dev.to/yurukusa (108h accidents)
- SWE-agent: github.com/swe-agent/swe-agent ; arxiv.org/abs/2405.15793
- SRE for agents: techcommunity.microsoft.com (SRE for autonomous AI agents)
- Feng et al. levels of autonomy: arxiv.org/abs/2506.12469
- ObserveID privilege tiers: observeid.com/how-much-power-should-you-give-an-ai-agent
- Reddit practitioner: r/LLMDevs (1ual54g, 1v5m1b5), r/LocalLLaMA (1v0ywoi HuggingFace incident)
