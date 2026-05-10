# cc-skills-lab

The Experimental Hub for Claude Code — pure logic, knowledge representation, and future trials.

## 🧠 The Lab Tribe

Pure theory and high-risk cognitive experiments.

### 1. Pure Logic & Optimization
Experiments in data compression and logic-maximal reasoning.

| Skill | Purpose | Home |
|-------|---------|------|
| cks | Constitutional Knowledge System experiments | `cks/` |
| lmc | Logic-maximal compression and optimization | `lmc/` |
| mlc | Meta-logic optimization and token trimming | `mlc/` |
| slc | Specialized logic contracts | `slc/` |
| simplify | Radical simplification protocols | `simplify/` |

### 2. Emerging Patterns
New trials for session summary and architectural coordination.

| Skill | Purpose | Home |
|-------|---------|------|
| dne | "Do Next Execution" — session summary and routing | `dne/` |
| csf-nip-integration | CSF to NIP protocol bridge | `csf-nip-integration/` |
| concept-mapper | Visualizing abstract session concepts | `concept-mapper/` |

## Artifacts Convention

All runtime artifacts write to:
`.claude/.artifacts/{terminal_id}/{skill_name}/`

Skills MUST NOT write state to their own directory or to the package root.

## Installation

Skills surfaced via junctions in `P:\\\\\\.claude/skills/`.
