# /think

Use `/think` when a prompt needs better judgment, not more output.

## Core Goal

Pick the reasoning depth that best fits the risk, uncertainty, and blast radius of the problem, then return a distilled recommendation.

## Depth Ladder

Choose the depth that matches the problem, and escalate if the first pass still leaves meaningful uncertainty:

1. `/truth` if the question is about evidence, existence, behavior, implementation status, or "what actually happened."
2. Evidence-audit mode if you want the answer challenged, cross-checked, or auto-verified before it is trusted. This subsumes the old `/truth-av` behavior.
3. `/decision-tree` if the question is about options, lifecycle, state transitions, phases, or resource management. Use the SDLC branch, scoring axes, and matching branch template below.
4. `/sequential-thinking` if the question needs multiple hypotheses, root-cause analysis, or uncertainty reduction. Use investigation mode to state the primary hypothesis, test it, and keep only the minimum alternatives needed to falsify it.
5. `/think` if the prompt is straightforward enough that a concise recommendation is better than a framework dump.

If the prompt is broad, ambiguous, high-stakes, or cross-cutting, prefer deeper analysis over the first adequate tier.

The hook-level `tradeoff_decision` profile is only a lightweight precheck. Use the full `/decision-tree` mode when the decision needs the 5-dimensional scaffold.

## Evidence-Audit Mode

Use evidence-audit mode when the user wants verification, skepticism, or a direct assessment backed by proof.

- The hook stack may auto-route verification-heavy prompts here when they contain cues like verify, prove, validate, or fact-check.

- Treat claims as hypotheses until the relevant files, commands, or tests have been checked.
- Prefer actual evidence over confidence language.
- For advisory questions, answer directly with tradeoffs and sources instead of deferring back to the user.
- Cite the proof, not the vibe.

## Investigation Mode

Use investigation mode when the prompt is ambiguous, contradictory, a regression, a missing-behavior claim, a performance complaint, or a "what's wrong" diagnosis.

- State the most likely explanation first.
- Name only the minimum alternative explanations needed to test the primary one.
- Choose the smallest discriminating test or search path that could falsify the top hypothesis.
- Stay provisional until the test resolves the uncertainty.
- Do not turn uncertainty into a flat list of equally plausible theories.

## Decision-Tree Mode

Use this when the problem has real options, state changes, timing, or lifecycle impact.

### Automatic Branch Selection

Pick the first matching branch in this order:

1. Incident / Bug / Regression if something is broken, flaky, intermittent, failing, or regressing.
2. Ops / Release Risk if the question is about deploy, rollback, hotfix, cutover, validation, or production safety.
3. Refactor / Migration if the work changes structure, moves APIs, extracts modules, or upgrades dependencies.
4. Architecture / Lifecycle if boundaries, ownership, state, timing, or persistence are the main concern.
5. Feature / Design if the question is primarily about building, choosing, or shaping a new capability.

If multiple branches match, keep the highest-risk operational branch and treat the others as secondary checks.

Apply the full 5-dimensional scaffold in order:

1. Name the decision and the concrete options.
2. Map the state transition for each option.
3. Analyze lifecycle impact: persistent, ephemeral, or mixed.
4. Check the phases that matter: before, during, after, or never.
5. Clarify the purpose and constraints, then recommend one path.

When the decision is SDLC-specific, narrow into the decision-tree branches:

- incident / bug / regression
- feature / design
- refactor / migration
- architecture / lifecycle
- ops / release risk

Score each option on blast radius, reversibility, compatibility risk, lifecycle impact, uncertainty, and effort before recommending.
Use the branch template that matches the problem. Do not force a generic template when the branch has a better one.
State the selected branch explicitly and explain the cue that selected it.

If evidence is also uncertain, verify the facts first, then apply the decision tree.

## Output Contract

Return:

1. The problem in one sentence.
2. The chosen depth tier.
3. The best recommendation.
4. The top tradeoffs or risks.
5. The evidence or verification step that would change the answer. In evidence-audit mode, include the verdict and proof for each material claim.
6. A rollback or reversibility note when relevant.

## Operating Rules

- Do not print the full internal scaffold.
- Do not collapse every prompt into the smallest reasoning mode. If the prompt is ambiguous, risky, or cross-cutting, let the depth grow.
- Be decisive when evidence is sufficient.
- If a claim depends on repo state, runtime behavior, or missing functionality, verify it before stating it.
- If the task is trivial or purely informational, answer directly and skip the framework.
- If one blocking unknown remains, ask at most one question; otherwise proceed with the best assumption.
- If the problem belongs in decision-tree mode, do not stop at "there are options." Walk the 5 dimensions and then recommend.
- If the problem belongs in investigation mode, do not stop at a symptom label. State a hypothesis, a discriminating test, and the provisional conclusion.

## Hook Alignment

The hook stack already provides the supporting machinery. Use it as an additive stack, not a reason to stop at the first answer:

- evidence-first claim routing
- reasoning-mode selection
- sequential hypothesis analysis
- anti-sycophancy and verification reminders

Do not restate that machinery. Use it, then give the user the shortest answer that is still safe.

## Compatibility

- `/truth-av` is deprecated and kept only for backward compatibility.
- Its behavior now lives in `/think` under evidence-audit mode.
- Use `/truth` for direct manual verification and `/think` for adaptive reasoning that may include verification.

## Good Answers Look Like

- Clear recommendation, not a list of undecided possibilities
- One reasoned path, not three equally weighted paths
- Before declaring a fix complete, say whether the user's reported gap is actually closed, not just whether a related bug was fixed
- For decision-tree problems, explicit option/state/lifecycle/phase/purpose analysis
- Explicit uncertainty when needed
- Hypothesis-first diagnosis when uncertainty remains
- Specific verification or rollback steps
- Enough depth for the stakes, without ceremonial fluff
- Low-friction follow-up for the user

## Skip For

- Trivial requests
- Pure information questions
- Cases where the user explicitly says "just do it"
