---
thread_id: 019f9aff-obs-20260726
parent_handoff_path: P:/docs/handoffs/dream-skill-requirements-20260726/HANDOFF.md
current_session_id: 019f9aff-a619-70c2-8836-0bb6ae462827
current_terminal_id: grok-build-primary
produced_at: 2026-07-27T06:55:00Z
status: open
handoff_type: investigation
accurate_as_of_head: pending
---

# Session observations — 2026-07-26 dream skill session

## Why this handoff exists

Substantive session with observations worth capturing for future sessions — not
tasks or findings (those go in regular handoffs/wiki), but meta-patterns and
insights about the workspace and operator collaboration style.

## Observations

### 1. Cargo-cult metric rejection (operator pattern)
The operator pushed back hard when I proposed "AGENTS.md rule-provenance
citation rate" as a /dream success metric. Their question — "why do we want a
metric? I'm ok with this, I just don't understand what we will do to get value
from it" — was the right challenge. The honest answer was "no decision it would
change" → metric was cargo cult.

**Insight:** when proposing any measurement, name the specific decision it
would change. If you can't, the metric is theater. This is a meta-rule worth
generalizing across all skill designs. Not yet in a wiki concept — flag for
/wiki consideration.

Source: session 019f9aff turn 6 (operator: "why do we want a metric?")

### 2. Operator's filtering preference when given options
When I enumerated 8 architectural clusters for /dream, operator pushed back:
"Which ones can you answer yourself with high confidence? Show me the list
that you have low confidence on." This is the pattern that actually works for
them: filtered presentation with confidence tags, NOT exhaustive enumeration.

**Insight:** any future /refine improvement should default to filtered
presentation. The grill* research confirmed this (Matt Pocock's one-at-a-time
is too slow for this operator; batch-with-recommendations is right). Already
captured in the /refine improvement handoff stream.

Source: session 019f9aff turn 4

### 3. qmd index is stale workspace-wide
During /dream's discovery phase I found qmd has 83 docs indexed vs 221 .md
files on disk in `P:/.data/wiki/concepts/`. This is a pre-existing condition
(not caused by /dream) but it affects every skill that relies on `qmd search`
(/wiki query, /www, /dream). /dream compensates with filesystem grep as
authoritative; other skills may not.

**Insight:** qmd index staleness is a workspace-health issue. The wiki has
outgrown the index. Maintenance task: rebuild qmd index, then add an
auto-rebuild trigger (post-write hook on `P:/.data/wiki/concepts/`?). Not yet
tasked.

Source: session 019f9aff, discovery phase of /go execute

### 4. ~./grok IS a separately-tracked git repo
Discovery during /go execute: `~/.grok/` has its own `.git`, distinct from
`P:/`. User-scope skills commit to `~/.grok` main; P:/ commit handles
project-scope artifacts (handoffs, output dirs). Two-repo commit pattern is
the correct shape for user-scope skill authoring. Not previously documented
explicitly; assumed in AGENTS.md but not stated.

**Insight:** when authoring a user-scope skill, expect two commits per change.
Already applied correctly this session — no action needed, just durable
knowledge for future skill work.

Source: session 019f9aff, /go execute commit phase

### 5. "Self-dealing" anti-pattern for skill author → skill invoker
When /go execute finished authoring /dream, I deliberately did NOT auto-invoke
/dream for TP-DREAM-03 (first dry-run). Reasoning: the orchestrator that just
authored a skill shouldn't be the one to invoke it; that's self-dealing and
removes operator's gate. The Execution Status table explicitly marked TP-DREAM-03
as "operator action."

**Insight:** this principle ("skill author ≠ skill invoker on first run")
generalizes. Worth capturing as a wiki concept for any skill-authoring workflow.
Not yet captured.

Source: session 019f9aff, /go execute final phase

## Non-observations (deliberately excluded)

- Decisions about /dream design → already in handoff + SKILL.md
- Research findings about LLM dreaming → already in wiki concept
- Operator's specific preferences (host scoping, etc.) → already in handoff

These are task-level and live in the regular handoff, not here.

## Next

No tasks created from these observations. Items flagged for /wiki consideration
(observations 1, 3, 5) can be promoted by a future /wiki default-mode pass.
