## Model: codex

### 1. Current strengths (keep)

- Five-dimensional Ishikawa fan-out across mechanical, measurement, behavioral, process, and environmental causes (`C:/Users/brsth/.grok/skills/why/SKILL.md:108-128`).
- Five Whys drill-down per contributing dimension (`C:/Users/brsth/.grok/skills/why/SKILL.md:130-145`).
- Premise labels `[FACT]`, `[INFERENCE]`, and `[UNKNOWN]`, with receipt requirements (`C:/Users/brsth/.grok/skills/why/SKILL.md:120-128`).
- Diagnostic mode verifies the observation before causal analysis and stops when the observation is false (`C:/Users/brsth/.grok/skills/why/SKILL.md:85-98`).
- Mandatory competing explanations and per-cause falsifiers reduce premature closure (`C:/Users/brsth/.grok/skills/why/SKILL.md:156-181`).
- Structural fixes are prioritized over behavioral mitigations, and `/why` does not implement fixes (`C:/Users/brsth/.grok/skills/why/SKILL.md:147-154`, `183-189`).
- Optional maker-checker verification is already defined through `--verify` (`C:/Users/brsth/.grok/skills/why/SKILL.md:243-253`).
- Clear boundaries against `/aar`, `/tp`, `/red-team`, `/design`, and `/go` (`C:/Users/brsth/.grok/skills/why/SKILL.md:27-37`).

### 2. Concrete gaps (what fails in practice)

- **Symptom:** A plausible explanation can be accepted after checking only one causal dimension ΓåÆ **root:** the current protocol mandates breadth but does not require an explicit first-divergence or evidence-completeness model ΓåÆ **why current skill misses it:** it proceeds from verified symptom directly to five dimensions, allowing trigger, proximate cause, and systemic cause to blur together (`C:/Users/brsth/.grok/skills/why/SKILL.md:100-118`).

- **Symptom:** ΓÇ£Hooks are not registeredΓÇ¥ can be inferred from zero-valued summaries even when hooks are firing ΓåÆ **root:** labels distinguish fact from inference, but do not impose a confidence ceiling based on evidence quality ΓåÆ **why current skill misses it:** a file read or logical derivation can be treated as a `[FACT]` without separating execution evidence from static evidence. The Claude reference explicitly distinguishes Tier 1 execution artifacts from Tier 3 static analysis (`C:/Users/brsth/.claude/plugins/cache/local/cc-skills-sdlc/1.0.237/skills/__lib/evidence_tiers.md`).

- **Symptom:** Agent-control failures are diagnosed as ordinary behavioral mistakes ΓåÆ **root:** no conditional control-plane analysis of contracts, identity, mutation ownership, enforcement boundaries, or negative paths ΓåÆ **why current skill misses it:** the five dimensions contain these concerns implicitly but do not force their inspection when hooks, gates, receipts, or verification are involved. This is the central gap identified in `P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md:22-32`.

- **Symptom:** A hookΓåÆpatchΓåÆgreenΓåÆblock cycle is reported as repeated failure rather than a self-reinforcing loop ΓåÆ **root:** no explicit invariant-preservation or feedback-loop test ΓåÆ **why current skill misses it:** the current falsifier asks whether fixing one cause prevents recurrence, but does not ask whether the response changed evidence or state without satisfying the invariant (`C:/Users/brsth/.grok/skills/why/SKILL.md:172-181`).

- **Symptom:** A passing exit code or written receipt is treated as proof of completion quality ΓåÆ **root:** lexical enforcement is conflated with semantic enforcement ΓåÆ **why current skill misses it:** it requires receipts but does not ask whether the receipt proves the intended outcome. The handoff identifies this lexical/semantic distinction at `P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md:179-185`.

- **Symptom:** Missing authority, stale receipts, wrong worktrees, import failures, and fail-open behavior remain unexamined ΓåÆ **root:** no evidence inventory or enforcement-specific negative-path coverage ΓåÆ **why current skill misses it:** environmental examples mention path and race issues, but no required state/authority inventory or negative-path matrix exists (`C:/Users/brsth/.grok/skills/why/SKILL.md:112-128`).

- **Symptom:** Repeated failure patterns are rediscovered from scratch ΓåÆ **root:** no pattern-library lookup ΓåÆ **why current skill misses it:** the skill has no mechanism for consulting prior wiki concepts before forming hypotheses. However, the handoffΓÇÖs proposed automatic wiki-writing loop is not yet justified by the current runtime or the no-implementation boundary.

- **Symptom:** Claude-specific RCA practices could be copied into Grok incorrectly ΓåÆ **root:** the current skill references abstract subagent behavior without runtime qualification ΓåÆ **why current skill misses it:** active Grok state shows Claude hooks are off, 18 `cc-*` plugins are disabled, and `red-team` is disabled (`C:/Users/brsth/.grok/active-surface.last.md`). The Claude RCA protocol also assumes CKS, Serena, mandatory web research, and 3ΓÇô7 hypotheses (`C:/Users/brsth/.claude/plugins/cache/local/cc-skills-sdlc/1.0.237/skills/__lib/rca_investigation_protocol.md`), none of which should become Grok requirements.

### 3. Recommended design (optimal long-term)

- Retain the current five-dimensional RCA as the default core.
- Add a short pre-causal pipeline:

  1. **Fit and intent:** distinguish explanatory, diagnostic, and post-mortem requests.
  2. **Observation verification:** retain the current diagnostic stop rule.
  3. **Evidence inventory:** record Mechanism, State, Outcome, and Authority as present, missing, or required. Missing evidence lowers confidence but does not block investigation.
  4. **First-divergence trace:** separate symptom ΓåÆ first divergence ΓåÆ immediate trigger ΓåÆ proximate cause ΓåÆ contributing conditions ΓåÆ systemic/reusable cause.
  5. **Conditional control-plane dispatch:** activate only when the failure involves hooks, gates, receipts, verification, agents, sessions, worktrees, or multi-repository scope.
  6. **MAST coverage check:** inspect FC1 specification/context, FC2 component/agent alignment, and FC3 verification/completion. Treat them as coverage categories, never prevalence or causal proof.
  7. **Five-dimensional fan-out and Five Whys:** preserve the existing method.
  8. **Classification:** classify causes as architecture/control-plane, implementation/code, workflow/process, model behavior, or environment/runtime.
  9. **Feedback-loop test:** ask whether the response changed observed evidence, state, or agent behavior without satisfying the underlying invariant. Distinguish harmful loops from bounded legitimate retries.
  10. **Competing explanations, absent-evidence, surprise, falsifier, and recommendation:** retain existing defenses and add the missing-evidence questions.

- The conditional control-plane lens should check:

  - intent-to-scope-to-mutation-to-verification-to-receipt-to-completion contract;
  - mutation and verification ownership;
  - session, repository, and worktree identity;
  - enforcement boundary;
  - fail-open/fail-closed behavior;
  - lexical result versus semantic proof;
  - negative paths: valid allow/block, stale or missing receipt, wrong identity, malformed output, import failure, exception, timeout, re-entry, false positive, and false negative.

- Replace binary `STRUCTURAL|BEHAVIORAL` output with the five-way classification, while retaining ΓÇ£structural fixes firstΓÇ¥ as prioritization guidance.

- Add compact evidence-tier annotations only where they improve decisions: current execution artifacts should outrank official documentation, static analysis, and speculation. Use the weakest evidence tier as a confidence ceiling, but do not turn numeric confidence into causal proof.

- Add read-only pattern matching against `P:/.data/wiki/concepts/` when the failure resembles a recurring system pattern. Treat a match as a hypothesis to verify, not as an established root cause.

- Do not automatically write wiki state. Instead, emit a reusable-pattern candidate in the report and leave durable capture to an explicitly authorized `/wiki` or documentation action. This preserves the handoffΓÇÖs cumulative-knowledge goal without violating the no-implementation boundary or imposing ceremony on short runs.

- Keep existing flags. Implement failure-class dispatch internally rather than adding `--bug`, `--agent`, `--pattern`, and `--system` as new user-facing modes. The existing `--diagnostic`, `--postmortem`, `--quick`, and `--verify` interface is simpler and avoids unreachable or overlapping branches.

- Make `--quick` genuinely short: observation check, evidence inventory, one primary dimension, one competing explanation, and one discriminating test. Make `--verify` explicitly conditional on available Grok subagent capability and require independent evidence checks.

The handoff recommends `C ΓåÆ B ΓåÆ A ΓåÆ D ΓåÆ E ΓåÆ F`, including automatic operator-confirmed wiki capture (`P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md:128-189`). The Codex promptΓÇÖs hard boundary is safer: `/why` may investigate and recommend but must not implement, must not require durable state for short runs, and must not assume Claude mechanisms (`C:/Users/brsth/Downloads/why-from-codex.txt`). I would therefore adopt B as read-only pattern lookup, A/E/F as core protocol improvements, and defer CΓÇÖs write loop until a separate authorized persistence workflow exists. The criterion is enforceability in the actual Grok runtime, not theoretical long-term leverage.

This is a radical structural refactor of the internal step flow but an incremental external change: existing modes, output purpose, five dimensions, Five Whys, evidence labels, falsifiers, and no-implementation boundary remain recognizable. The ROI is high because the changes target missed causal classes and false completion evidence rather than adding prose checklists.

### 4. Rejected alternatives

- **Ten mandatory dimensions.** Rejected because it duplicates the five existing dimensions and creates checklist fatigue. The handoff correctly retained five dimensions plus a conditional control-plane lens (`P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md:52-56`).

- **Mandatory 3ΓÇô7 hypotheses.** Rejected because it encourages padded or strawman alternatives. Keep at least one evidence-tested competing explanation, as already required (`P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md:93-96`).

- **Automatic wiki writes after systemic findings.** Rejected for the skill itself. It introduces durable side effects into a diagnostic command, requires persistence and confirmation semantics, and conflicts with the promptΓÇÖs investigation/recommendation boundary. Use a proposed-pattern output for a separate authorized documentation step.

- **User-facing `--bug`, `--agent`, `--pattern`, and `--system` modes.** Rejected as unnecessary interface expansion. Internal dispatch can provide the same conditional depth while preserving the current invocation contract.

- **Claude RCA protocol copied wholesale.** Rejected because it requires CKS, Serena, internet research, and hypothesis scoring that are not established Grok requirements. The active surface explicitly shows Claude hooks and disabled `cc-*` plugins are not firing (`C:/Users/brsth/.grok/active-surface.last.md`).

- **Mandatory durable state or web research on every run.** Rejected because most investigations are short and local. Both add latency and ceremony without evidence that they improve ordinary-bug findings.

### 5. Implementation priority

1. Add evidence inventory and confidence-ceiling rules.
2. Add six-layer first-divergence tracing.
3. Add conditional agent-control lens with contract-map and ownership checks.
4. Add lexical-versus-semantic enforcement and enforcement-specific negative paths.
5. Add harmful feedback-loop detection with invariant checking.
6. Replace binary cause classification with the five-way classification.
7. Add MAST FC1/FC2/FC3 coverage reporting.
8. Add surprise and absent-evidence checks to competing explanations and falsifiers.
9. Add read-only wiki pattern lookup, gated behind recurring/systemic failure signals.
10. Update output templates and verify all four existing invocation modes.
11. Add a separate, explicitly authorized documentation workflow for reusable systemic patterns if repeated investigations demonstrate value.

### 6. Falsifiers

- On at least five varied agent-control failures, the new control-plane lens consistently produces no additional verified or decision-changing findings beyond the existing five dimensions.
- Evidence-tier ceilings merely change labels or percentages without reducing unsupported causal claims.
- First-divergence tracing routinely adds ceremony but does not distinguish trigger from proximate or systemic cause.
- Feedback-loop detection produces false positives for legitimate bounded retries or ordinary continuation.
- Negative-path checks become rote checklists and fail to identify actual false positives, false negatives, fail-open behavior, or identity errors.
- Wiki pattern lookup anchors investigations on stale or superficially similar concepts and increases confirmation bias.
- The five-way classification does not change fix ownership, prioritization, or recommended next tests.
- `--quick` remains effectively as expensive as full RCA, indicating that conditional dispatch failed.
- Independent `--verify` runs cannot access the relevant Grok evidence or merely repeat the primary report instead of testing it.
- On the handoffΓÇÖs session-019f96f5 test case, the enhanced protocol still misses the feedback loop, contract-map gap, fail-open behavior, enforcement-boundary gap, or architecture/control-plane classification.

### 7. Open questions / unknowns

- Whether GrokΓÇÖs current subagent facility can independently inspect the same runtime evidence reliably enough for `--verify`; direct hook tests alone must not be treated as live-enforcement proof.
- Whether a stable, read-only wiki search interface is available to `/why` without invoking an unavailable or disabled plugin.
- Which artifact is authoritative for each class of Grok hook and receipt: configuration, active-surface snapshot, runtime logs, or execution receipts.
- Whether the proposed evidence-tier ceilings should remain qualitative or use numeric values; numeric scores may create false precision.
- Whether the existing Grok skill loader supports conditional reference files without making the core skill harder to follow.
- Whether durable systemic-pattern capture belongs in `/wiki`, `/aar`, or a dedicated handoff workflow.
- Whether the current `--quick` semantics should remain ΓÇ£single-dimensionΓÇ¥ or become the bounded fast path described above.
- The available evidence establishes the active surface at snapshot time, not necessarily every runtime state after configuration changes; `C:/Users/brsth/.grok/active-surface.last.md` warns that the snapshot can become stale.