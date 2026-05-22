# cc-skills-thinking

The Cognitive Hub for Claude Code — high-frequency reasoning engines, specialized loops, and self-reflection patterns.

## 🧠 The Thinking Tribe

The skills in this package are organized for CLI compatibility (flat directory) while providing deep cognitive partnership.

### 1. Master Engines (Production)
The primary routers for complex analysis and brainstorming.

| Skill | Purpose | Home |
|-------|---------|------|
| /think | Unified router (Reasoning + Strategy + Genius) | `reason/` |
| /reason | Unified reasoning engine (epistemic state routing) | `reason/` |
| /genius | Super-Genius thought partner: challenges premises | `genius/` |
| /s | Strategy engine: multi-persona brainstorming | `s/` |

### 3. Content Processing
High-speed triage and extraction for technical content (videos, articles, transcripts).

| Skill | Purpose | Home |
|-------|---------|------|
| /ut | Universal Triage: fast architectural gatekeeper for content assessment | `ut/` |
| /ux | Universal Spec Extractor: reverse-engineer videos/transcripts into Zero-Gap skill.md | `ux/` |

### 4. Cognitive Reflexes (Active Trials)
Specialized loops that refine logic and maintain mental model hygiene.

| Skill | Purpose | Home |
|-------|---------|------|
| /dream | Memory hygiene and MEMORY.md consolidation | `dream/` |
| /sequential-thinking | Generate → Critique → Improve self-reflection loop | `sequential-thinking/` |
| /tot | Tree of Thoughts: parallel approach exploration | `tot/` |
| /execution-clarity | Forces clarity on multi-step decisions | `execution-clarity/` |
| /reflect | Captures session-end learnings to CKS | `reflect/` |
| /learn | Novelty-weighted lesson extraction | `learn/` |
| /skeptic | Adversarial plan challenge | `skeptic/` |
| /truth | Falsification-based evidence verification | `truth/` |
| /pace | Cognitive load and wellness monitoring | `pace/` |
| response-atomicity | Step-by-step response construction | `response-atomicity/` |

## Artifacts Convention

All runtime artifacts write to:
`.claude/.artifacts/{terminal_id}/{skill_name}/`

Skills MUST NOT write state to their own directory or to the package root.

## Installation

Skills surfaced via junctions in `P:\\\\\\.claude/skills/`.
