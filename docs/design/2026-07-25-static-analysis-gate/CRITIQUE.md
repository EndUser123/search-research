# Critical-Friend Review: Mechanical detection of predictable code problems

**Reviewer:** Grok Build (critical-friend subagent)
**Date:** 2026-07-25
**Mode:** Premise critique, not implementation review (correctness reviewer signed off 0 issues; that surface is settled).
**Stance up front:** The direction is sound and the source is faithfully inherited, but **two load-bearing empirical premises are unverified, one is partially falsified by a one-time grep, and the 7-PR scope includes gold-plating while omitting a success-metric loop.** Verdict: **REVISE** — not "don't build it," but "test the premises and trim the scope before committing to 7 PRs."

---

## 1. Problem framing

**The problem the design is actually solving, in one sentence:** *Build a permanent Stop-hook gate so no AI-generated Python edit ships without passing ruff+pyright, plus an 8-check 3.14-gotcha AST detector and a contract-test harness, across this workspace's own skill code.*

**Does that match "how should we implement the findings?"** Partially, and the mismatch is the core issue.

The findings (research wiki, verified at `P:/.data/wiki/concepts/predictable-code-problems-detection-python-314-ai-generated.md`) are a **detection taxonomy** + **8 gotchas** + **5 AI-code patterns**. The research's own emphasis (lines 53, 226–237) is:

- The **AI-specific** defect classes (Part 3, the 1.7× rate) are caught by *"Code review at interfaces + behavioral tests — Static tools miss these."*
- The workspace **already implements** several detection strategies: `/check`, `/review`, the `validate_*.py` gates (lines 226–228).

So the design mechanizes the layer the research calls **least AI-specific and already partly covered** (type errors, undefined names — ruff/pyright), while the layer the research calls **highest-value for AI code** (Part 3 patterns) is acknowledged as already handled by the existing review/test pipeline. The design does not quantify which layer actually produces defects *in this workspace*. It assumes the static layer is the gap without measuring whether the Part-3 layer (already covered) is where the real defect pressure is.

This is not a fatal framing error — wiring up installed tools is a legitimate reading of "implement the findings." But the framing presents the hook as *"the research's central finding"* when the research's actual central finding is a **taxonomy insight** ("different bug classes need different detection methods; no single tool covers all"), not an **enforcement prescription**. The Stop-hook is the design's invention on top of the research, and it picks the lower-leverage layer to mechanize.

---

## 2. Optimal long-term vs. simplicity

### Over-engineering (gold-plating)

**(a) Component C (`py314_audit`) is a permanent detector for a problem a one-time grep shows is absent.**
- The research's *own* recommended detection for the 8 gotchas is a one-time `rg` audit (lines 99, 104, 109, 142–145). I ran it.
- **Receipt (OBSERVED):** `rg '\b(locals\(\)|get_type_hints|__trunc__|pickle\.(dumps|loads|load)|NotImplemented)\b'` over live `P:/.grok` (13 .py) and `P:/.agents` (156 .py) → **0 matches.** The only matches in `P:/.claude` are inside `worktrees/*` *test fixtures* that assert `pickle.loads` is unsafe-by-design (a security test, not usage) — and worktrees are explicitly "stale copies, exclude from truth claims" per `P:/AGENTS.md`.
- A one-time audit already answered "do we have these 3.14 problems?" → **no.** Building an 8-check AST module + tests + a PR (PR 3) to *permanently* re-check for an absent problem is gold-plating. The optimal long-term shape is a **one-shot audit script** (exactly what the research recommended), re-run only when 3.14 usage actually appears or on Python upgrade. The design even acknowledges the detector is down to 5 real checks (#5 placeholder, #7 delegated to ruff, #8 informational) — so "8-gotcha detector" is itself oversold framing.

**(b) PR 6 (`contract_runner`) is out of scope for "implement the findings."**
It tests the *test infrastructure* (validators) — reflexive hardening the research touches only via Pattern 2. That is a different problem ("are our validators correct?") than "detect predictable code problems." Valuable in principle, but it is scope creep relative to the user's ask, and it adds a `CONTRACTS` schema convention to files other agents maintain. Defer or drop.

### Under-engineering (missing from the optimal solution)

**(c) No success metric or validation loop.** The design adds a per-turn latency tax (the Stop hook) but defines no baseline defect rate, no catch-rate target, and no review criterion for the trace log (`static-gate-<sid>.log` is written but nothing reads it). Open Q1 is about *latency* tuning, not *value* validation. The optimal long-term solution states upfront: "after 30 days, if false-block rate > X or true-catch rate < Y, retire the gate." Without this, the gate becomes permanent infrastructure justified by a premise that was never checked ex post.

**(d) The gate protects Python only, but Python may not be where this workspace's risk concentrates.** **Receipt (OBSERVED):** live `.grok` = **13** .py files; `.agents` = 156; the load-bearing AI-infra also includes `hooks/*.json`, `settings.json`, `SKILL.md` frontmatter — a syntax error in any of which silently breaks *all* hooks. The design inherits the research's Python focus without examining whether Python is THIS workspace's highest-risk surface. The ratio (13 live .py files in `.grok` vs. the JSON/MD config that actually wires enforcement) should at least be named and dismissed explicitly, not inherited by default.

### The structural inversion in Component A

`MAX_FILES=40` caps coverage. Big turns (the ones that most need checking — mass refactors, multi-file generations) get **partial** coverage; small turns get full checks. The cap inverts the value: it full-checks the low-risk turns and sample-checks the high-risk ones. The design treats this as a latency concession (Open Q1) but doesn't acknowledge it as a coverage inversion. A gate that silently under-covers exactly the turns that produce the most defects is not "mechanical verification"; it's mechanical verification with a hole where the load is heaviest.

---

## 3. Falsifiability

Three concrete falsifiers; one is already partially run.

1. **The "agents skip ruff" premise (ROOT CAUSE — unverified either way).** The entire Component A rests on the claim that agents ship Python edits *without* running static analysis. **Receipt status: NONE.** The design asserts it ("`/check` permits linters and agents skip them — verified empirically") but provides no transcript scan, no log, no count. This workspace already imposes edit-then-verify, the receipt rule, and `/check`/`/review` — a verification regime far heavier than the "human who skips steps 2-4" the research describes. **Falsifier:** scan the last N sessions' transcripts for Python edits where ruff/pyright was not invoked; if agents already run them (or `/check` Phase B catches static errors before close), the gate's marginal value collapses and Alternative 2 (manual `/static` only) becomes optimal. The design's rejection of Alternative 2 rests *entirely* on this unverified premise.

2. **The latency premise.** The value prop is "sub-second to ~1s feedback." **[INFERENCE]** pyright is a Node.js process that cold-starts by loading type stubs; it is plausibly 2–5s even on a handful of files (I have not measured it on this host — that measurement is the falsifier). If real-world Stop-latency on a 5–10 file turn exceeds ~2s, the gate becomes a tax on every Python-editing turn — the exact "noise-trap that makes lint gates get disabled" the design warns about (D1). **Falsifier:** measure `pyright --outputjson` cold-start on a representative 5-file turn *before* PR 4.

3. **The 3.14-risk premise (partially falsified).** See §2(a): the one-time grep the research itself recommends returns 0 live occurrences. The permanent detector (Component C) addresses a non-manifest problem in the current codebase.

---

## 4. Anchoring — premises brought in without examination

1. **The actor-mapping slip (most important).** The thesis quote is real (research line 216: *"automate the verification that humans skip"*). But line 208 specifies what "humans skip" means: *"When AI writes code, **humans** skip steps 2-4 (run locally, click through UI, verify behavior)."* That is about a **human developer accepting** AI-generated code in a normal dev workflow. The design remaps "humans skip" → "**the agent** doesn't choose to run ruff." The agent is the *author*, not the human *acceptor*; and this workspace already loads the agent with verification obligations the "skipping human" never had. The analogy is treated as identity. The design should either justify the remap or acknowledge that the research's missing-feedback-loop is about a different actor in a different workflow.

2. **The 1.7× generalization.** The rate comes from studies of general AI-assisted code (GitClear, CodeRabbit — large codebases, many developers, thin review). This workspace's AI code is ~169 live files, single-operator-overseen, already passing through `/review` + `/check`. Applying 1.7× to motivate urgency here is an unexamined ecological transfer. The local defect rate is **UNKNOWN** — and the design proposes no way to measure it, yet uses the imported rate to set scope.

3. **"Mechanical = reliable" recursion, unresolved.** §2.4 honestly admits the detection infra is "itself the highest-value target for the detection infrastructure." But the gate is AI-generated code, `fail-open` by design — so a broken/misconfigured gate *silently stops protecting* with no alarm. The `contract_runner` (PR 6) tests the *validators*, **not the gate itself.** The gate's own contract (does it still block on a known-bad file?) is not in any runner. "Who watches the watchman" is acknowledged and then dropped. The optimal solution includes a self-test: a canary `.py` file with a deliberate `F821` that the gate must block on, checked periodically — otherwise fail-open degrades to silent-no-op unobserved.

---

## Context-derived domains (selected)

### Cost / performance (central practical risk)
- pyright in a Stop hook fires on **every** Python-editing turn. If the operator does ~20 such turns/session, even 2s/turn = ~40s/session of turn-end blocking, multiplied across 5 concurrent sessions each spawning pyright → real CPU contention on a shared host. The design addresses per-hook fail-open but **not resource contention across concurrent pyright invocations.** Worth one paragraph: does the host saturate, and should the gate serialize or skip-if-busy?

### Observed vs. invented (label discipline)
The tooling-state claims genuinely check out (**OBSERVED**: `ruff.toml` absent; `pyrightconfig.json` targets 3.14 with the dead `extraPaths`; hooks `pyproject.toml` is py312/S-only; all tools installed). But the **two empirical premises that justify the entire design** — (i) agents skip static analysis, (ii) 3.14 risk is manifest here — are **ASSERTED, not observed.** Premise (ii) I falsified via grep; premise (i) is unverified either way. A design that labels its tool inventory "OBSERVED" while leaving its causal premises unobserved has its receipts in the wrong place.

---

## What I would change (specific, prioritized)

1. **Before PR 4:** run the transcript scan (falsifier #1) and the pyright cold-start measurement (falsifier #2). If either fails, **Component A does not ship** and Alternative 2 (manual `/static` skill) is the optimal long-term solution — dramatically smaller, zero hook risk, and the design's own rejection of Alt 2 dissolves.
2. **Demote Component C** from a permanent 8-check module to a **one-shot audit script** (the `rg` the research actually recommended), re-triggered only on Python-version change or when a gotcha pattern appears in a diff. Drop PR 3 as a standalone; fold the audit into `/static --py314` as a thin pass.
3. **Drop or defer PR 6** (`contract_runner`) as out of scope for "implement the findings."
4. **Add a gate self-test canary** (a known-bad `.py` the gate must block) checked on a schedule — closes the fail-open recursion.
5. **Add a 30-day trace-log review + retire criterion** to PR 4 before calling the gate "shipped."
6. **Name and dismiss the Python-vs-JSON/MD risk-surface question explicitly** (13 live `.grok` .py files vs. the load-bearing config) rather than inheriting the research's Python focus by default.

With (1)–(3), the design shrinks from 7 PRs to roughly 3 (config + `/static` skill + `/check`&`/review` integration) — which is a faithful, optimal-long-term implementation of the findings *as a detection capability*, with the enforcement hook gated behind its own premises being verified.

---

## Verdict

**REVISE.**

The framing is not fatally wrong: the research is real, the thesis quote is real, the tools are installed, and the wiring gap is genuine. But:

- The **root-cause premise** (agents skip static analysis) is **unverified** and is the sole basis for the hook vs. the manual skill.
- The **3.14-risk premise** is **partially falsified** by the research's own recommended grep (0 live occurrences).
- The **latency premise** is **unmeasured** and the value prop ("sub-second") is likely wrong for pyright.
- The **scope includes gold-plating** (permanent py314 detector for an absent problem; contract_runner) **and omits a success loop** (no metric, no retire criterion, no gate self-test).

None of these are implementation bugs — they are premise and scope issues. Resolve the three falsifiers, trim the scope, and the remaining design is a strong optimal-long-term solution. As written, it risks building 7 PRs of permanent infrastructure on two untested empirical claims and one already-falsified one.
