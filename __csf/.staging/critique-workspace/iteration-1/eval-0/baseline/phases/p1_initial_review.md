# Phase 1: Initial Critical Review

Act as an expert critical reviewer of the work (plan, design, document, policy, prompt, or skill) we have done.

If the target describes a process or methodology (e.g., a skill with phases, a workflow, a multi-step procedure), also examine whether the process itself is sound: check that phase definitions are self-consistent, that each phase's scope does not contradict the overall structure, and that the methodology is appropriate to its stated goal. A process review catches structural bugs that artifact-level review misses.

First, think through your analysis step-by-step before writing your answer. Do not skip intermediate reasoning steps.

Before evaluating, establish a clear model of the target: restate what the work is, what its key components are, and what it is trying to achieve. Verify this understanding against the actual content before critiquing. A critique built on mischaracterization is worthless — each claim about the work must be grounded in what the work actually says or does.

Critique quality has two independent dimensions: (1) Precision — are the critique's claims about the target actually true and factual? A critique can be comprehensive but wrong. (2) Recall — does the critique identify everything important? A critique can be correct but miss major gaps. Both matter independently. Flag precision failures explicitly — do not let an inaccurate claim hide in a comprehensive list.

Then provide your answer with these sections only:
- **Brief Intent Summary** – what this work is trying to achieve.
- **Logical Gaps & Inconsistencies** – numbered list.
- **Hidden Assumptions & Fragile Dependencies** – numbered list.
- **Missing Obvious Actions / Best Practices** – numbered list.
- **Risks and Edge Cases** – numbered list.
- **Concrete Recommendations** – specific changes, additions, or questions.
- **Open Questions / Unknowns** – where information is missing or you are uncertain.

Focus on what is missing, weak, or risky; keep praise minimal. Clearly label speculative critiques as 'Speculative'.

## Input

The work to review is provided via file path. Read it with:
```
cat "{WORK_FILE}"
```

## Output Schema

Return your critique in this exact structure:

```
## Brief Intent Summary
[2-3 sentences max]

## Logical Gaps & Inconsistencies
1. [item]
...

## Hidden Assumptions & Fragile Dependencies
1. [item]
...

## Missing Obvious Actions / Best Practices
1. [item]
...

## Risks and Edge Cases
1. [item]
...

## Concrete Recommendations
1. [specific change or question]
...

## Open Questions / Unknowns
1. [uncertainty]
...
```
