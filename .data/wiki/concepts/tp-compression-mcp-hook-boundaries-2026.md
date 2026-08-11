---
title: "Grok /tp compression, MCP, and hook boundaries"
created: 2026-08-07
source: session-2026-08-07
tags: [grok-build, tp, thought-partner, mcp, hooks, skill-compression, fleet-architecture, decision]
summary: >
  Keep Grok’s native /tp as the single thought-partner front door and compress
  it by routing detail into references and deterministic helpers. Reuse active
  MCP servers for wiki and documentation retrieval; do not add a generic
  thinking MCP in phase one. The only new hook worth testing is a scoped,
  receipt-aware Stop validator for explicit /tp runs, initially in shadow or
  advisory mode.
type: decision
agent: grok
host: grok
cognitive_load: 4
verification: inferred-only
confidence: 0.74
last_verified: 2026-08-07
half_life_days: 90
evidence_gaps:
  - The preflight discovery audit for the live capability surface timed out; exact transitive callers and registration ownership still need a bounded follow-up.
  - No shadow-mode data yet measures false positives, latency, or operator disablement for a TP-specific Stop validator.
  - No cross-host collision has been demonstrated that requires a new MCP run registry rather than atomic local artifacts.
relations:
  - target: wiki/concepts/agent-skill-compression-boundaries-2026.md
    type: refines
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: refines
  - target: wiki/concepts/advisory-vs-blocking-enforcement-decision-2026.md
    type: related
  - target: wiki/concepts/agent-control-plane-enforcement-architectures-2026.md
    type: complements
  - target: wiki/concepts/close-single-authority-renderer.md
    type: related
  - target: wiki/concepts/adaptive-orchestration-task-shape-classification.md
    type: related
sources:
  - "https://docs.anthropic.com/en/docs/claude-code/skills (Extend Claude with skills - Claude Code Docs; date not exposed by MMX)"
  - "https://developers.openai.com/codex/build-skills (Build skills - ChatGPT Learn; date not exposed by MMX)"
  - "https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture (Architecture overview - MCP; 2026-07-28)"
  - "https://modelcontextprotocol.io/specification/2026-07-28/server/tools (Tools - MCP; 2026-07-28)"
  - "https://modelcontextprotocol.io/specification/2026-07-28/server/resources (Resources - MCP; 2026-07-28)"
  - "https://docs.anthropic.com/en/docs/claude-code/hooks-guide (Automate actions with hooks - Claude Code Docs; date not exposed by MMX)"
---

# Grok /tp compression, MCP, and hook boundaries

## Decision context

This decision applies to the current Grok Build terminal, where Grok’s native
`/tp` is present but the `cc-*` thinking/reasoning plugin suite is not firing.
The operator is a solo director, so the architecture must optimize fleet-level
clarity and low operator memory load rather than maximize the number of named
skills or default model calls.

The selection criteria are, in order:

1. preserve `/tp`’s high-value behavior (fresh framing, evidence, dissent,
   falsifiers, and durable learning);
2. reduce always-loaded context and argument memorization;
3. keep failure visible and mechanically testable;
4. avoid new shared infrastructure until it solves a verified cross-host
   problem; and
5. preserve portability without claiming that Claude Code, Codex, and Grok
   have identical native commands or hook semantics.

## Evidence

- `C:\Users\brsth\.grok\skills\tp\SKILL.md` currently has 1,697 lines and
  106,222 bytes; its directory has 39 files. The focused test suite passes 38
  tests in 4.14 seconds. These are current measurements, not a judgment that
  the current package is optimally sized.
- The skill already has semantic intent routing and an explicit lens-count
  override (`SKILL.md:130-184`), mandatory critique history/wiki/preflight
  steps (`SKILL.md:909-969`), model-pool and parallel-panel logic
  (`SKILL.md:1038-1139`), telemetry/wiki-save policy (`SKILL.md:1459-1473`),
  and a falsifier (`SKILL.md:1667-1695`).
- `P:\.data\telemetry\tp-critique-log.jsonl` has 17 valid rows and no invalid
  rows. Its 12 `REVISE` and 5 `PROCEED` verdicts, plus inferred action labels,
  show that the mechanism is being recorded; they do not establish causal
  quality improvement or optimal panel size.
- The active-surface snapshot says Claude-side hooks are off, the `cc-*`
  suite including `cc-skills-thinking` and `cc-aca-reasoning` is not firing, and
  `search_wiki`, `search_web`, and `context7` are configured while
  `web-search-prime`, Perplexity, and Hacker News are disabled. The snapshot
  warns that it represents SessionStart state and can become stale.
- The scoped preflight audit attempted during this investigation timed out.
  That is an evidence gap, not proof that the skill has no callers or that a
  new server is required.

## Decision

### 1. Keep one native `/tp` front door; do not add another thinking skill

Refactor the existing Grok skill in place. Treat `reason`, `genius`,
`ultrathink`, and similar terms as aliases, host adapters, or depth presets
only when they have a distinct contract. A distinct user-facing skill should
require a different domain, evidence contract, and outcome measure.

The thin front door should contain only:

- semantic intent and explicit-override parsing rules;
- the mode-to-reference map;
- stop conditions and the output/receipt contract;
- the safety rules that must be visible before dispatch; and
- the small number of invariants that cannot be delegated to a reference.

Long protocols, provider notes, examples, and incident history should move to
mode-specific references. Parsing, manifest creation, command construction,
result-file discovery, count checks, and telemetry should move to deterministic
helpers. The model remains responsible for framing, judgment, synthesis, and
meaning.

### 2. Reuse existing MCP servers; add no generic thinking MCP in phase one

The MCP architecture separates tools (actions), resources (shared context/data),
and prompts (structured interaction templates). That makes MCP useful at a
cross-client boundary, not as a replacement for the reasoning model or a local
regex/parser.

Use the configured servers as follows:

| Existing server | Value for `/tp` | Default policy |
|---|---|---|
| `search_wiki` | Retrieves prior critique patterns and durable decisions, preventing the fleet from re-deriving known failure modes. | Use for artifact/system critiques; disclose when unavailable. |
| `search_web` | Retrieves external evidence when the operator requests research and the current Grok configuration routes it there. | Use selectively; keep the MMX path when the research contract specifically requires MMX. |
| `context7` | Retrieves current library/framework documentation at the moment a critique depends on version-sensitive behavior. | Use only for a concrete documentation question; do not preload it for every `/tp`. |
| `reddit`, `reddit-rss`, `kinocut`, `opencv` | Useful domain capabilities, but not intrinsic to thought-partner routing. | Keep opt-in and domain-triggered. |

This uses existing integration surface without increasing the skill’s default
tool schema or creating another lifecycle boundary.

### 3. A future MCP candidate is conditional, not a phase-one proposal

If Grok, Codex, and Claude later need to share live TP runs across processes or
machines, the candidate is a narrowly scoped `tp-run-registry` MCP:

```text
resources:
  tp://runs/{run_id}/manifest
  tp://runs/{run_id}/results
tools:
  tp_prepare
  tp_record_lens
  tp_validate
```

Its value would be a common run identity, structured lens results, freshness
metadata, and collision-resistant aggregation for multiple clients. It would
not make the models more intelligent.

The candidate is deliberately deferred. A filesystem manifest plus atomic
result files is simpler for one Grok terminal. An MCP server would add schema
context, process/auth lifecycle, availability failures, concurrent-state
semantics, and another authority boundary. The trigger to revisit is a
reproduced cross-host collision or a verified consumer that cannot safely use
the shared filesystem—not a general desire for a cleaner architecture.

### 4. The only new hook worth testing is a scoped TP completion validator

No new global “think harder” hook is proposed. Reuse the active Grok surfaces
where their contracts fit: quality/verification receipts, spawn-model gating,
uncertainty and recommendation gates, close enforcement, and wiki persistence.

The one new hook to test is a proposed `Stop_tp_result_validator` (name is
descriptive, not an implementation receipt). It would run only when the
response has an explicit TP run manifest or `TP_RUN_ID`, and check deterministic
completion invariants:

- requested lens count versus dispatched and returned count;
- each claimed lens has a result receipt or an explicit failure reason;
- artifact-target critiques disclose the required discovery/preflight status;
- findings contain evidence classification and a falsifier;
- the verdict does not claim stronger certainty than the receipts support.

It must not spawn models, call an MCP server to invent missing evidence, or
decide whether the substantive recommendation is correct. Start in shadow or
advisory mode. Fail closed only for a malformed explicit TP run, and measure
timeouts, false positives, operator overrides, and disablement risk before
blocking anything.

Do not add a new PreToolUse duplicate-dispatch hook yet. The manifest and
dispatch helper should own duplicate prevention; add a hook only if a real
duplicate-dispatch failure survives that boundary.

## Constructive red-team of this decision

| Load-bearing claim | Steelman attack | Falsifier / measurement | Current disposition |
|---|---|---|---|
| The existing `/tp` should be compressed rather than replaced. | Its accumulated prose may encode subtle behavior that a thin router will omit. | Replay current representative cases before/after and compare route, reference-load, receipt, and catch-rate outcomes. | Refactor only after replay corpus exists; no replacement. |
| Existing MCPs are enough initially. | Shared state may already cross process boundaries and local files may race. | Reproduce a collision or identify a current consumer that cannot use atomic run artifacts. | Defer new MCP; instrument run identity first. |
| A Stop validator improves reliability. | Grok Stop hooks can fail open, race with output state, or add friction that causes disablement. | Shadow-label 30+ real TP runs for false positives, timeout rate, and operator overrides. | Advisory/shadow only until measured. |
| Three lenses are a good default. | Correlated models and shared bundles can manufacture convergence while increasing cost. | Compare adaptive 1/2/3-lens routing on matched prompts with blinded outcome labels and provider failure rates. | Treat three lenses as a tested preset, not a correctness guarantee. |
| Deterministic code can safely own more behavior. | A parser or classifier can encode hidden policy and become a second opaque skill. | Review helper decisions against ambiguous, adversarial, and novel prompt fixtures. | Limit code to mechanics and expose its decisions in the manifest. |
| Portable layering is realistic. | Claude’s `ultrathink`, Grok hooks, and Codex skills have different native contracts. | Verify each host’s active command/hook path before claiming parity. | Keep native adapters explicit; do not promise cross-host equivalence. |

The red-team changes the recommendation in one important way: the new hook is
not a shipped enforcement feature, and the new MCP is not a phase-one build.
Both are hypotheses with gates.

## Claim ledger

| Claim | Type | Evidence | Confidence | Falsifier | Action allowed |
|---|---|---|---|---|---|
| Grok native `/tp` is active while the `cc-*` thinking suite is not firing in the current snapshot. | verified_fact | `C:\Users\brsth\.grok\active-surface.last.md:300-320` and hook/plugin sections | High for the snapshot; stale-state risk remains | Fresh active-surface snapshot shows a different live route | Use as current Grok scope only; refresh before implementation. |
| `/tp` has natural seams for routing, dispatch, persistence, and falsification. | verified_fact | `SKILL.md:130-184, 909-969, 1038-1139, 1459-1473, 1667-1695`; `tp_dispatch.py` functions | High | Replay shows behavior depends on hidden cross-section prose | Refactor proposal, not automatic edit approval. |
| Progressive disclosure is the lowest-risk way to reduce always-loaded skill context. | inference | Anthropic/Codex/Anthropic skills/Superpowers result snippets plus local structure | Medium-high | Controlled replay shows reference loading misses critical behavior or raises latency materially | Build replay corpus and measure. |
| A shared TP run-registry MCP is valuable only after a cross-host state need is proven. | hypothesis | MCP tools/resources roles plus local single-terminal scope | Medium | Reproduced multi-client race cannot be solved reliably by artifacts | Instrument local manifests first; revisit if falsified. |
| A scoped Stop validator is worth shadow-testing. | hypothesis | Active Grok Stop surface plus receipt/claim gaps | Medium-low | Shadow data shows high false positives, timeouts, or operator disablement | Shadow only; no blocking rollout without evidence. |

## What this means for our workspace

**Now:** preserve the current native Grok `/tp`; use `search_wiki` for pattern
retrieval, `context7` for concrete versioned docs, and domain MCPs only when
intent requires them. Treat the two wiki pages created in this investigation
as the architecture/research record, not as implementation receipts.

**Next, if authorized:** create a replay corpus and a deterministic TP run
manifest/receipt validator inside the existing skill package. Measure default
1/2/3-lens routing and reference-load coverage. Run the proposed Stop validator
in shadow mode.

**Deferred:** a `tp-run-registry` MCP and any new global hook. They need a
demonstrated cross-host state problem and a measured value/overhead case.

## Falsifier

Re-open this decision if any of the following occurs: compressed references
lose high-value findings in replay; current local artifacts produce a verified
cross-host collision; the TP validator cannot obtain reliable run identity; or
shadow data shows that the new hook’s false-positive, timeout, or disablement
cost exceeds the value of its receipts. Re-open the “one front door” decision
if a reasoning alias develops a genuinely different domain and independently
measured outcome contract.

## Next steps — 2026-08-11 re-evaluation

**Verdict:** still relevant + actionable. None of the three original evidence gaps has been closed by subsequent work; the decision remains binding and the open questions are still open.

**Re-evaluation (2026-08-11).** The decision is now ~4 days old. Checked:
- `best-practices-enforcement-mechanism-grok-build.md` (2026-07-24) reaffirms the "config > hook > metric > rule" hierarchy and the "act on external state, not actor output" detector test this concept inherits. No conflict.
- `agent-control-plane-enforcement-architectures-2026.md` confirms the hook enforcement layer is the right pattern for the Stop validator (complement relation in frontmatter). No conflict.
- No concept has been written that addresses the timed-out preflight audit, the missing shadow-mode data, or the unproven cross-host collision. The three evidence gaps remain open.

**Specific research questions to close the evidence gaps (priority order):**

1. **Bounded preflight audit for the live skill capability surface.** The original 2026-08-07 audit timed out. Run a bounded pass via `python P:/.agents/skills/preflight/scripts/discovery_audit.py --scope P:/.grok/skills --target tp --target tp_dispatch.py --target tp-critique-log.jsonl --output P:/tmp/tp-discovery.json` to enumerate transitive callers, registration owners, and the live consistency between SKILL.md, the dispatch helper, and the telemetry artifact. Confidence needed to close gap: HIGH (full enumerated map with no orphans).

2. **Shadow-mode pilot for the Stop validator.** Build the minimal `Stop_tp_result_validator` (advisory only, no blocking) and run against 30+ real TP runs over 1–2 weeks. Measure: false-positive rate, timeout rate, operator override rate, operator disablement rate. Acceptance threshold: false-positive <10%, timeout <5%, operator override <20%, no disablement. If any threshold fails, shadow-mode continues or the validator is dropped. Confidence needed to close gap: HIGH (measured numbers, not estimates).

3. **Cross-host collision reproduction attempt.** Set up a controlled scenario: two Grok/Claude/Codex terminals both invoking TP against the same `tp-critique-log.jsonl` artifact. If they collide, this gap is closed (the MCP run-registry is no longer deferred). If they don't collide, the gap is closed by absence of evidence (the MCP remains deferred). Confidence needed to close gap: HIGH (controlled scenario with measurable result).

**Out of scope for next steps (other concepts own these):** the broader "one front door" question (reframed by `agent-skills-fleet-patterns-solo-director-2026` and the catalog-creation rule in AGENTS.md); the cross-host porting question (reframed by `git-worktree-multi-terminal-best-strategies` and the multi-terminal isolation rules).

## Sources

- [[agent-skill-compression-boundaries-2026]] — the full MMX query/result ledger
  and progressive-disclosure boundary analysis.
- [[code-orchestrates-model-judges-skill-scale]] — existing local principle for
  deterministic orchestration versus model judgment.
- [[advisory-vs-blocking-enforcement-decision-2026]] — measurement-first rule
  for avoiding broad blocking hooks.
- [Architecture overview - MCP](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture)
  — tools, resources, and prompts have different roles (MMX result; 2026-07-28).
- [Tools - MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
  — model-invoked actions (MMX result; 2026-07-28).
- [Resources - MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)
  — shared context/data (MMX result; 2026-07-28).
- [Automate actions with hooks - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/hooks-guide)
  — prompt versus state-verifying hook roles (MMX result; date not exposed).

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[hook-failure-mode-taxonomy]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[skill-step-enforcement-architecture-grok-build]]
