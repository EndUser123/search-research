# Handoff: Response-strategy meta-layer — "how do I answer optimally?"

**Created:** 2026-07-24
**Session:** 019f91d3-2741-7f83-af68-211796180474
**Author:** grok
**Status:** Ready for implementation this session (operator wants to address it)

## The gap

No skill in the fleet has a self-reflection mechanism that asks "how do I
answer this user optimally?" before generating a response. The fleet has:

- **Skill routing** (`/go` profile inference) — picks a work profile from task
  shape. But doesn't ask "does the user want action or understanding?"
- **Evidence-first default** (AGENTS.md) — tells the agent to provide
  provisional conclusions before asking questions. But doesn't self-reflect on
  *what kind of answer* the user needs.
- **Concern detection** (`/check`) — groups work into concerns for
  verification. But it's reactive (after work), not proactive (before response).

What's missing: a **response-strategy layer** that runs before content
generation and adapts the response to the user's inferred need.

## The questions it should ask

Before generating a response, the meta-layer evaluates:

1. **Action vs understanding** — is the user asking me to DO something, or to
   HELP THEM THINK? (Determines: implement vs analyze)
2. **Depth vs speed** — do they want thoroughness or a quick answer?
   (Determines: spawn subagents vs answer inline)
3. **Delegate vs direct** — should I delegate (fire subagents) or answer
   directly from context? (Determines: latency cost vs context cost)
4. **Existing work reference** — is there prior work I should build on, or is
   this greenfield? (Determines: read handoffs/wiki vs start fresh)
5. **Decision point** — what will the user DO with my answer? (Determines:
   format, specificity, actionability)
6. **Model selection** — given the above, which model tier is appropriate for
   this response? (Connects to the model pool selection policy)

## Where this could live

Three options (to evaluate):

### Option A: New skill `/respond` or `/adapt`
A standalone skill invoked at the start of every non-trivial response. Pro:
explicit, inspectable. Con: another step the user has to know about; or the
agent has to self-invoke, which is just behavioral rules wearing a skill costume.

### Option B: Behavioral rules in AGENTS.md
A "response-strategy protocol" section in AGENTS.md that every session loads.
Pro: always-on, no invocation needed. Con: prose rules are frequently skipped
under context momentum (the same problem the evidence-first rule has).

### Option C: Hook-based enforcement
A PreResponse hook that injects the 6 questions as a structured prompt prefix.
Pro: structurally enforced, can't be skipped. Con: Grok Build may not support
PreResponse hooks (verify against `~/.grok/docs/user-guide/10-hooks.md`).

### Recommendation (initial)
Option B for the behavior, with a path to Option C if Grok Build supports the
hook type. The rules should be concrete enough to actually change behavior,
not aspirational ("think about what the user wants" is useless; "classify the
request as action/understanding/hybrid, then pick a response mode" is
actionable).

## Connection to existing work

- **Model pool selection policy** (`P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md`)
  — the response-strategy layer feeds INTO model selection. "Action vs
  understanding" determines the domain; the domain determines the model.
- **Context firewall architecture** (`P:/.data/wiki/concepts/context-firewall-architecture.md`)
  — the response-strategy layer determines whether Layer 1 extraction is needed
  (bulk reading) or whether the orchestrator should answer directly.
- **`/go` profile inference** — the response-strategy layer subsumes or
  complements profile inference. Need to decide: does it replace `/go`'s
  Step 1, or sit above it?

## What to build

1. **Define the response-strategy protocol** — the concrete 6-question
   checklist and the decision tree that maps answers to response modes.
2. **Write it to AGENTS.md** — as a behavioral rule section (Option B).
3. **Test it** — on real user messages from this session, retroactively
   classify: would the protocol have changed the response? (e.g., "screenshot
   black boxes?" → action, speed, direct, no delegation. Did I do that? Yes.
   But "/tp what do you think about M3?" → understanding, depth, delegate to
   critique subagent. Did I do that? Also yes. So where does the protocol
   actually change outcomes?)
4. **Consider the hook path** — check if Grok Build supports a pre-response
   hook that could enforce the protocol structurally.

## Acceptance criteria

- [ ] Response-strategy protocol defined (6 questions + decision tree)
- [ ] Written to AGENTS.md as a behavioral rule
- [ ] At least 3 retroactive tests on this session's user messages
- [ ] Connection to model pool policy documented
- [ ] Connection to context firewall documented

## Related

- Model pool policy: `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md`
- Context firewall: `P:/.data/wiki/concepts/context-firewall-architecture.md`
- AGENTS.md: `~/.grok/AGENTS.md`
- `/go` skill: `~/.grok/skills/go/SKILL.md` (Step 1 profile inference)
- `/tp` skill: `~/.grok/skills/tp/SKILL.md` (the skill where the gap was identified)
