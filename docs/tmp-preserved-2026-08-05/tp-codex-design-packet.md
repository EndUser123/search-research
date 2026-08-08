# Critique task: /design skill improvement task packet

You are a critical friend reviewing a task packet that proposes 7 improvements to a design-doc skill. The operator asks: "does this make sense?"

## Read these files first

1. The task packet (critique target): `C:/Users/brsth/.grok/sessions/P%3A%5C/019fd413-5f5f-7642-8124-1c63ada98244/prompts/prompt_0.txt` — the task packet is in the user_query section.
2. Current /design skill: `C:/Users/brsth/.grok/skills/design/SKILL.md`
3. Ensemble patterns wiki: `P:/.data/wiki/concepts/multi-model-ensemble-design-patterns-for-agent-skills.md`
4. Risks research wiki: `P:/.data/wiki/concepts/risks-skill-improvement-research-2026.md`

## Context (verified by the orchestrator)

The /design skill (1320 lines) ALREADY has:
- Steps 0.5-0.8: context firewall, domain research (wiki+web), codebase inventory, premise verification
- Step 0.8 evidence labels: [FACT], [INFERENCE], [UNKNOWN] (but NOT [RESEARCH] or [CONTRADICTED])
- Cross-document consistency check (grep wiki for contradictions)
- Critical friend (Step 5.5) with framing check + pre-mortem + falsifier request
- Step 6d: promote key decisions to wiki
- Artifact lifecycle section (temp scaffolding vs durable wiki)
- Design Intent Contract with failure conditions
- --lite and --fast modes

It does NOT have: bare /design handler, --research-to-design mode, host-context injection (P1 gap), evidence ledger, [CONTRADICTED] label.

## The 7 proposed changes

1. Bare /design handling
2. --research-to-design mode (9-step evidence-gated pipeline)
3. Evidence labels + evidence ledger
4. Falsification experiments before architectural commitment
5. Host-context injection for all subagent prompts
6. Durable-artifact mapping
7. Contradiction handling

## Critique these questions

1. Is this a "modify files" task or a skill redesign? Does the scope match the framing?
2. Does --research-to-design duplicate the existing /www + /design composition?
3. Do the new evidence labels extend Step 0.8 or risk creating a parallel system?
4. Is the evidence ledger specified enough to implement (location, format, consumers)?
5. Does the packet cite measurement evidence for the changes, or is it theory-driven?
6. Is "falsification experiments" clear enough (code spike vs research check vs naming a falsifier)?
7. Are there hidden dependencies between the 7 changes the packet doesn't surface?
8. How do new features compose with existing Steps 0.5-0.8, 5.5, 6d?
9. The packet says "approved improvements" — where is the approval cited? The wiki concepts are about /risks, not /design.

## Output format

Tag each finding [FACT] (cite file:line) or [INFERENCE]. End with a PROCEED/REVISE/BLOCK verdict and a "what would change this" disconfirmation section.
