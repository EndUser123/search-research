---
title: "Work discovery skill organization: best practices and domain mapping for AI agent fleets"
created: 2026-08-03
source: session-019fb177 (/www research + design session)
tags: [work-discovery, skill-organization, best-practice, agile, kanban, gtd, itsm, adhd, external-memory]
summary: >
  Research across Agile/Scrum, Kanban, GTD, and ITSM frameworks identifies 12
  work-management domains. For a solo operator directing an AI fleet, only 10
  are needed — triage/clarification and prioritization/planning are NOT needed
  because the operator makes those decisions directly. The key insight: skill
  consolidation should serve missing domains, not merge overlapping ones. The
  operator's pain is discovery breadth (too many commands), not missing
  ceremonies. Also: ADHD external-memory research says ambient retrieval is
  load-bearing — a system requiring willpower to maintain fails under load.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://www.prodpod.com/blog/invented-now-next-later-roadmap/ (ProdPad, 2024)
  - https://goalsandprogress.com/prioritization-methods-complete-guide/ (Goals & Progress, 2025)
  - https://goalsandprogress.com/task-management-adhd-systems/ (Goals & Progress, 2025)
  - https://blog.devgenius.io/docker-cmd-vs-entrypoint-the-most-misunderstood-concept-explained-f7c9e9f4d45b (DevGenius, 2023)
  - https://www.mindstudio.ai/blog/subtraction-principle-ai-agents-fewer-tools (MindStudio, 2025)
relations:
  - target: wiki/concepts/ai-thought-partner-industry-expectations-and-now-next-later.md
    type: extends
  - target: wiki/concepts/review-attacks-implementation-misses-framing.md
    type: related
  - target: wiki/concepts/skill-graph.md
    type: related
---

# Work discovery skill organization: best practices and domain mapping

## Decision context

The operator directs a fleet of AI agents on a multi-root workspace with 90+
skills, 176+ open handoffs, and 5+ skills touching "what should I do?"
discovery. The pain point: running 5 commands (`/todo + /tp do + /tp improve
+ /handoff + /wiki`) to get a unified view of open work. The question: how do
standard work-management frameworks organize this, and how do we map to them?

## The 12 standard domains (from 4 frameworks)

| Domain | Scrum | Kanban | GTD | ITSM | Needed for solo + fleet? |
|--------|-------|--------|-----|------|--------------------------|
| Intake / capture | Product owner adds | Entry column | Capture | Incident logged | **Yes** — `/handoff`, `/harvest` |
| Triage / clarification | Backlog refinement | Upstream Kanban | Clarify | Incident classification | **No** — handoffs are pre-structured at creation |
| Organization / backlog | Product backlog | Backlog column | Organize | CMDB categorization | **Yes** — handoffs (flat list) |
| Prioritization / planning | Sprint planning | WIP limit + pull | Reflect | Change advisory board | **No** — operator decides directly |
| Status / tracking | Daily standup | Board visualization | Current action list | Incident status | **Yes** — `/todo` |
| Execution | The sprint | In-progress column | Engage | Resolution work | **Yes** — `/go`, `/refactor` |
| Delivery / completion | Sprint review | Done column | Task completed | Incident resolved | **Yes** — `/check`, `/close-check` |
| Retrospective | Sprint retro | — | Weekly review | Post-incident review | **Yes** — `/tp session`, `/aar` |
| Improvement discovery | Retro action items | Flow optimization | Reflect | Problem management | **Yes** — `/tp improve`, `/skill-dev` |
| Knowledge capture | — | — | Reference filing | Knowledge management | **Yes** — `/wiki`, `/handoff` |
| Obligation / debt tracking | Carryover | Aging items | Open loops | Known errors | **Yes** — `/harvest` |
| Quality verification | Definition of Done | Exit criteria | — | Change validation | **Yes** — `/check`, `/review`, `/trace` |

**Two domains are NOT needed for a solo operator:**

1. **Triage / clarification** — handoffs are pre-structured (16 fields,
   acceptance criteria, scope bounds) at creation time. There is no firehose
   of unclassified incoming work. Triage solves a problem we don't have.

2. **Prioritization / planning** — the operator decides what to work on by
   saying `/go fix X` or `/tp review Y`. The prioritization happens in the
   operator's head. They've never said "I don't know what to do" — they've
   said "I have to run too many commands to find out what's open." That's a
   **discovery** problem, not a **prioritization** problem.

## Key research findings

### 1. NOW/NEXT/LATER with impact sorting (not tiers)

ProdPad's NOW/NEXT/LATER framework, widely adopted across product management,
organizes by time horizon with explicit commitment: NOW is small enough that
everything in it actually ships. The operator's adaptation: sort by impact
within each horizon. No effort column — the operator doesn't care about
transition cost. This extends [[ai-thought-partner-industry-expectations-and-now-next-later]]
which documented the timeframe continuum for advisory AI.

### 2. ADHD external memory: ambient retrieval is load-bearing

The strongest finding for our context: the system must survive the operator
being tired or context-switched. A system requiring willpower to maintain
will fail under load. **Ambient retrieval** (the system proactively tells you
what's open) is more important than perfect categorization. This validates
`/todo` as a scan-and-surface tool, not a planning tool.

### 3. Subtraction principle: fewer loaded tools = better AI performance

Empirically validated: AI models perform worse when given too many options.
Loaded context directly competes with task context. This argues for skill
consolidation — but only when it reduces *loaded* context, not just file count.

### 4. ENTRYPOINT+CMD pattern: one entry, mode flags

Docker's model: one fixed entry point (always runs) + overridable defaults.
Satisfies "one command" + "separate concerns." However, our session found
that `/tp`'s 4D matrix already implements this pattern — the question isn't
whether to build a new router, but whether to fix the existing delegation.
This relates to [[invariants-beat-environment-comfort]] — the invariant
(one command for one question) should drive the implementation, not the
pattern name.

### 5. Scan functions, not skills

The key architectural insight: producer skills don't need to be skills at
all. `/todo` calls functions directly — `scan_findings()`, `scan_harvest()`,
`scan_critique_log()` — each a few lines of Python returning structured data.
Skills become optional entry points over shared functions, not the functions
themselves.

## What this means for our workspace

1. **The operator's pain is discovery breadth, not missing ceremonies.**
   `/todo` needs more scan sources (FINDINGS.md, WIKI markers, harvest,
   critique log, research suggestions, epistemic debt, dreams) — not new
   planning or triage skills.

2. **/todo is the discovery front door.** Not `/tp session` (a retrospective),
   not `/work` (an architecture). `/todo` scans and surfaces; the operator
   decides and acts.

3. **Producer skills can be functions.** `/friction`, `/capture`'s scan logic,
   and parts of `/harvest` can be extracted into `scan_functions.py` that
   `/todo` imports. The skills survive if the operator wants standalone use.
   See [[skill-graph]] for the producer/consumer data-flow model.

4. **Don't add domains the operator doesn't need.** Triage and planning were
   proposed as "missing" — but the operator doesn't want them. Adding
   ceremonies nobody asked for is the same anti-pattern as adding skills
   nobody invokes.

## Receipts

- **scan_functions.py** (`~/.grok/skills/todo/__lib/scan_functions.py`):
  11-source scanner implementing the scan-function model. `scan_all()` at
  line ~635, `SCANNER_REGISTRY` at line ~619. Verified working: 45 items,
  <2s runtime (session 019fb177, 2026-08-02).
- **/todo SKILL.md** (`~/.grok/skills/todo/SKILL.md`): NOW/NEXT/LATER format
  documented in Step 1. Operator approved format after 5 rounds of correction
  (session 019fb177 transcript).
- **/wiki RNS format** (`~/.grok/skills/wiki/SKILL.md` lines 310-358):
  the reference format /todo now matches. `## Recommended next steps` header,
  `N - description` format, `0 - Do all` footer.
- **Skill graph** (`P:/.data/wiki/concepts/skill-graph.md`): producer/consumer
  data-flow section added session 019fb177.

## Falsifier

This domain mapping is wrong if:
- The operator starts saying "I don't know what to work on" (triage needed)
- The operator wants the system to commit-gate work items (planning needed)
- Scan functions miss important work that only an LLM-based skill would catch
- The subtraction principle doesn't apply (more skills = better performance)

## Sources

- [ProdPad — NOW/NEXT/LATER roadmap](https://www.prodpod.com/blog/invented-now-next-later-roadmap/) — originator of the framework
- [Goals & Progress — Prioritization methods complete guide](https://goalsandprogress.com/prioritization-methods-complete-guide/) — 12-framework survey
- [Goals & Progress — ADHD task management systems](https://goalsandprogress.com/task-management-adhd-systems/) — ambient retrieval as load-bearing constraint
- [DevGenius — Docker CMD vs ENTRYPOINT](https://blog.devgenius.io/docker-cmd-vs-entrypoint-the-most-misunderstood-concept-explained-f7c9e9f4d45b) — ENTRYPOINT+CMD pattern
- [MindStudio — Subtraction principle for AI agents](https://www.mindstudio.ai/blog/subtraction-principle-ai-agents-fewer-tools) — fewer tools = better performance

## Auto-related

- [[skill-graph]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[opentelemetry-logging]]

