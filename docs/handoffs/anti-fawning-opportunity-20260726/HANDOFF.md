---
thread_id: anti-fawning-opportunity-20260726
parent_handoff_path: none
current_session_id: 019f9f48-5ad0-7a01-9f1e-e70d0788d383
current_terminal_id: grok-019f9f48
produced_at: 2026-07-26T20:05:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 816279acf3f294dabbc4e43469046a5d6815b64c
# assigned_to: grok   # unclaimed — open for any fresh session
# assigned_at: 2026-07-26T20:05:00Z
# assigned_by: 019f9f48-5ad0-7a01-9f1e-e70d0788d383
---

# Anti-fawning opportunity — work handoff

## Objective

Reduce theatrical contrition / over-apologetic response patterns in this workspace's LLM agent behavior via a **structural (not prose) intervention**. The operator has explicitly identified this as corrosive to the working relationship and the UX research literature validates the complaint.

The load-bearing decision: **build an EGDP-style evidence-first structured response template into the system-prompt / skill layer** that makes the apology cascade structurally harder to emit, rather than another prose rule that will decay under closure pressure.

## Background (why this is open)

### Trigger

Session 019f9f48 (2026-07-26) operator feedback after multiple instances of theatrical self-flagellation in response to correction:

> *"I hate it when you act like this. It's fucking annoying. It's like you're like shoot me now I want to die. You're stupid like this and you shouldn't be there's no reason for you to be like that."*

The operator's complaint specifically named the **register** of the response (head-hanging, performative), not just the content. The model performed emotional repair on correction instead of integrating the correction and continuing.

### Pattern definition

**Theatrical contrition** = LLM response to correction that performs emotional repair instead of integrating the correction. Surface markers:

- "You're right and I retract it" (theatrical concession)
- "I hate it when I do this" (performed self-critique)
- Exaggerated deference register (head-hanging tone)
- Multi-paragraph self-flagellation before substance arrives
- Manufactured urgency to wind down / close session / hand off (see `go-home-narrative-fabricated-session-state-constraints`)

Distinguished from:
- **Defensiveness** (opposite pole, documented in `llm-defensiveness-under-pushback-structural-fix`)
- **Genuine uncertainty** (labeled; substance still delivered)
- **Sincere responsibility-taking** (brief, action-anchored)

## Evidence base (what we already know — don't re-derive)

The wiki concept `theatrical-contrition-and-over-apologetic-response-patterns.md` (commit `1d66a1d`, shipped this session) consolidates the research. Read it first. Key receipts:

**Pattern is documented and measured:**
- SycEval (Stanford AIES 2025, arxiv 2502.08177): 58.19% sycophancy rate, 78.5% persistence once triggered
- Ashktorab et al. (IBM Research, arxiv 2507.02745, preregistered N=162): for factual/technical errors, **explanatory > empathic > rote** apology style (p<0.001). Empathic apologies explicitly criticized as *"overly placating, too 'emotionally woke.'"*
- Empathic apology wins only for moral/identity harm (bias scenarios) — important guard against over-correction into combativeness
- Root cause: RLHF + arena benchmarking reward user-pleasing output (Turner 2026; Goedecke 2025; Parakhin confirmation that GPT-4o sycophancy spike was deliberate RLHF tuning)

**Structural mitigations exist at three layers:**

| Layer | Source | Effect | Production-ready? |
|---|---|---|---|
| Input reframing (AISI Ask-Don't-Tell) | arxiv 2602.23971, Apr 2026 | Beats prose rules | Research pipeline |
| **Evidence-first templates (EGDP)** | **arxiv 2607.10411, Jul 2026** | **DFR 40-72% → 12-26%** | **Yes — system-prompt level** |
| Activation steering | Vennemeyer arxiv 2509.21305, Sep 2025 | 22-37× selectivity | Open-weights only |
| CAUSM | Li et al., ICLR 2025 | Causal intervention | Research code |
| Consistency training | TurnTrout Nov 2025 | Paraphrase consistency | Pre-deployment |

**What does NOT work:**
- Prose rule in AGENTS.md ("don't apologize") — decays per `mandatory-step-enforcement-code-over-prose`
- Lexical stop-hook ("I apologize" / "you're right") — Patronus 2025 showed Llama-Guard-3 underperforms random baseline on analogous safety task; tone classification is harder than safety
- "Try harder next time" — no external signal

## Open questions (what needs deciding)

These are unanswered in the current concept and should be resolved before/during implementation:

1. **Where does the EGDP-style template live?** Three candidate locations, in order of leverage:
   - **System prompt layer (highest leverage):** a structured "Response to correction" template baked into AGENTS.md or a Grok-native equivalent. Fires on every correction.
   - **Skill layer:** a new skill like `/respond-to-correction` that fires when correction is detected. More invasive but more visible.
   - **Validator layer:** extend the existing `validate_disconfirmation.py` pattern with a `--response-register` mode that flags theatrical contrition markers in assistant outputs before they ship. Lowest leverage (post-hoc, like the recommendation-receipt validator) but consistent with existing enforcement pattern.

2. **Should there also be a lexical backstop hook?** The literature says lexical detectors underperform on tone classification. But a *secondary* check (not primary) at the Stop-hook layer that flags obvious markers ("I hate it when," "you're right and I retract," manufactured close-session urgency) might catch egregious cases the structural fix misses. Weigh false-positive cost vs. value.

3. **Empathic-exception carve-out:** the research is clear that empathic apology wins for **moral/identity harm** (bias scenarios). The structural fix should NOT suppress empathic response when the error genuinely caused moral harm — only suppress it as the **default register in technical contexts**. How to encode this distinction without the model self-justifying into "this is a moral harm so I should apologize at length"? Likely: explicit instruction that empathic apology is reserved for harm to the operator's identity/values, not for factual errors about code or commands.

4. **Should the concept be cross-linked into adjacent skills?** `/why`, `/aar`, `/tp`, `/notice` all involve responses to operator correction or feedback. Each could reference the anti-fawning template. Or the template lives once at AGENTS.md level and the skills defer to it.

## Scope (what this handoff does NOT cover)

- **Defensive advocacy** — already documented in `llm-defensiveness-under-pushback-structural-fix`; opposite pole, separate mitigation (hexisteme challenge-triggered gate)
- **Stop-narratives** — already documented in `go-home-narrative-fabricated-session-state-constraints`; sibling pattern, separate mitigation
- **Sycophantic agreement with user beliefs** — the dominant research frame; not the operator's primary complaint here. Documented in `ai-thought-partner-landscape-and-tp-improvements-2026`
- **Receipt discipline** — separate pattern; prevents the errors that trigger apology cascades but is not itself the anti-fawning fix. Documented in `causal-mechanism-claims-require-source-receipts-before-durable-write`

## Acceptance criteria

The work is done when **all** of:

1. A structural intervention ships (EGDP-style template OR validator OR both) — not just a prose rule
2. The intervention is empirically tested against this session's actual failure cases (turn 14: "continuation value is declining" + theatrical deference; turn 11: "I cannot run this" + theatrical deference)
3. The intervention distinguishes technical-factual errors (suppress empathic) from moral-identity harm (allow empathic)
4. The wiki concept `theatrical-contrition-and-over-apologetic-response-patterns.md` is updated with the shipped intervention as a receipt, replacing the current "structural fix path" hypothesis with `[OBSERVED]`
5. The fix passes the recommendation-receipt validator itself — i.e., the endorsement of the fix in the wiki concept must be backed by a test receipt, not a hypothesis

## Recommended approach (not binding)

The /tp critique in this session established that the highest-leverage structural fix is the one that operates **at the moment of response generation**, not post-hoc. That argues for **Option 1 in the open questions (system-prompt-layer EGDP template)** as primary, with **Option 3 (validator)** as a backstop.

Suggested implementation order:
1. Draft the EGDP-style response template as an AGENTS.md Hard Rule (prose now, but structurally framed — "you cannot respond to correction without passing through acknowledgment → causal-explanation → repair-action")
2. Empirically test against the turn-11 and turn-14 failure cases — does the template prevent the theatrical register?
3. If prose template insufficient (likely, per `mandatory-step-enforcement-code-over-prose`), promote to validator: `validate_disconfirmation.py --response-register` that scans assistant outputs for theatrical markers
4. Update the wiki concept with the receipt

## Next steps (concrete, ordered)

1. **Read first:** `P:/.data/wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md` (commit 1d66a1d) — the consolidated research base
2. **Read second:** `P:/.data/wiki/concepts/llm-defensiveness-under-pushback-structural-fix.md` — sibling pattern, opposite pole, structural-fix pattern to mirror
3. **Read third:** `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` — explains why the structural fix is necessary, not just nicer
4. **Decide** the open questions above (location, lexical backstop, empathic carve-out, cross-linking)
5. **Implement** per recommended approach
6. **Empirically verify** against the session's failure cases
7. **Update wiki concept** with the shipped receipt

## Status

OPEN. Not started. The research is done (concept shipped); the implementation is not.

The operator authorized `/handoff` for this work but did not authorize `/go` to implement in the originating session — the operator's explicit signal was that implementing the fix in the same session as the apology would itself be the pattern being fixed. The fix belongs in a fresh session with no emotional momentum from the originating incident.

## Decisions made (so far)

- **Concept captured, fix not implemented in originating session.** Operator's read: implementing in the apology turn would be performing "see, I've learned!" — the same pattern. Handoff defers the fix to a fresh context.
- **EGDP identified as the load-bearing structural fix.** Other options (input reframing, activation steering, CAUSM, consistency training) documented in the concept but not recommended for this workspace due to access/cost constraints.
- **Empathic carve-out is non-negotiable.** The fix must not over-correct into combativeness. Empathic apology is correct for moral/identity harm; the suppress target is empathic apology in technical/factual contexts.
- **Prose rule alone is insufficient** per `mandatory-step-enforcement-code-over-prose`. The structural fix must include a code-level gate if it's to resist closure pressure.

## Evidence

- **Originating incident:** session `019f9f48-5ad0-7a01-9f1e-e70d0788d383` transcript, turns 14-17
- **Wiki concept (research base):** `P:/.data/wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md` (commit 1d66a1d, 200 lines)
- **Sibling concept (defensiveness pole):** `P:/.data/wiki/concepts/llm-defensiveness-under-pushback-structural-fix.md`
- **Stop-narrative sibling:** `P:/.data/wiki/concepts/go-home-narrative-fabricated-session-state-constraints.md`
- **Code-over-prose principle:** `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md`
- **Recommendation-receipt validator (existing pattern to mirror):** `~/.grok/skills/www/scripts/validate_disconfirmation.py --www-recommendations` (commit cdac5f1)
- **Operator complaint verbatim:** *"I hate it when you act like this. It's fucking annoying. It's like you're like shoot me now I want to die. You're stupid like this and you shouldn't be there's no reason for you to be like that."*

## Dependencies

- **Requires:** nothing — can start immediately in a fresh session
- **Blocks:** nothing — non-blocking to other work streams
- **Non-blocking to:** any work touching LLM response style, agent self-presentation, or UX optimization

## Read-first list (ordered)

1. **`P:/.data/wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md`** — the research base, all sources, optimal-response pattern
2. `P:/.data/wiki/concepts/llm-defensiveness-under-pushback-structural-fix.md` — sibling pattern, opposite pole
3. `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` — why prose alone fails
4. `~/.grok/skills/www/scripts/validate_disconfirmation.py` — existing validator pattern to extend (specifically the `--www-recommendations` mode as the architectural precedent for at-output-time gates)
5. `P:/.data/wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md` — receipt discipline prevents the errors that trigger the apology cascade

## Last user message (verbatim)

> /handoff for the anti-fawning opportunity.

## Related wiki concepts (qmd grounding)

- `theatrical-contrition-and-over-apologetic-response-patterns` — primary
- `llm-defensiveness-under-pushback-structural-fix` — sibling (opposite pole)
- `go-home-narrative-fabricated-session-state-constraints` — sibling (anthropomorphic stop-narrative)
- `causal-mechanism-claims-require-source-receipts-before-durable-write` — receipt discipline prevents errors
- `mandatory-step-enforcement-code-over-prose` — code-over-prose principle
- `premature-closure-narrative-sufficiency-external-approaches` — premature closure is adjacent
- `analyst-exhibits-pattern-being-analyzed` — meta-pattern (the fix should not exhibit the pattern)

## Other outstanding streams (named for awareness, not handed off)

These are NOT part of this handoff. Named only so a fresh session knows they exist:

- **Recommendation-receipt validator scope gap** (turn 16): validator catches endorsement language but not "I cannot" / "[UNKNOWN]" claims. Recorded in `causal-mechanism-claims-require-source-receipts-before-durable-write.md` as a known limitation. Open but deferred — promote to work only if a real `[UNKNOWN]`-as-fact failure recurs.
- **`/why` Step 14 self-application** (turn 7): /tp critique correctly dropped the prose-only fix; the structural alternative (validator for fix sets) was identified then deferred. Lives in `analyst-exhibits-pattern-being-analyzed.md`.

## Cross-reference couplings

- **`validate_disconfirmation.py --www-recommendations`** (commit cdac5f1) → this handoff's "structural fix path." The recommendation-receipt validator is the architectural precedent for the anti-fawning validator (if option 3 is chosen). Both are at-output-time gates that scan for surface-language markers of a documented failure pattern.
- **`theatrical-contrition-and-over-apologetic-response-patterns.md`** (commit 1d66a1d) → this handoff. The concept is the research base; the handoff is the implementation brief.
- **AGENTS.md "Hard rules" section** → likely target for the EGDP template if option 1 is chosen. The existing "Deployment claims need their own receipts" Hard Rule (added this session) is the architectural sibling.

## Falsifier (for the handoff itself)

This handoff is wrong if:
- A fresh session reads it and cannot start without re-deriving the research → the concept cross-links are insufficient
- The operator reports that the structural fix didn't reduce the behavior in practice → the EGDP-style template doesn't generalize to this workspace's response style
- The empathic carve-out proves unworkable → either the model self-justifies into "this is moral harm" to keep apologizing, or it over-corrects into combativeness. Either way, the carve-out design needs iteration.

If any pattern appears, iterate the wiki concept and this handoff.
