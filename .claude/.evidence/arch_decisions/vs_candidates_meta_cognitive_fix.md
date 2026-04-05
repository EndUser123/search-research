# Verbalized Sampling Options: Meta-Cognitive Decision Architecture

## Option 1: Mandatory Pre-Output Self-Questioning
<lens>: evidence_based
<probability>: 0.65
<changes>:
- Add cognitive checkpoint before ALL solution proposals
- Before suggesting any architecture/solution, run 3-question litmus test:
  1. "Why this specific value?" (detects arbitrary thresholds)
   2. "Does this work with concurrent execution?" (detects race conditions)
  3. "Is this necessary or nice-to-have?" (detects over-engineering)
- Only proceed if all questions have satisfactory answers
- Integrates questioning_patterns.md into decision workflow

## Option 2: Comparative Analysis First (Optimal-Last Swap)
<lens>: systems_thinking
<probability>: 0.80
<changes>:
- For ANY problem with multiple solution approaches:
  1. Generate 2-3 diverse candidates first (Verbalized Sampling)
  2. Analyze tradeoffs of each candidate
  3. Select optimal solution based on contextual factors
- Bias toward native/platform-native solutions over custom code
- Prefer prompting/pattern-matching over script/automation
- "Search → Evaluate → Implement" sequence instead of "Implement → Check → Fix"

## Option 3: Multi-Pass Reasoning with Critic Layer
<lens>: alternative_quality
<probability>: 0.40
<changes>:
- First pass: Generate initial solution proposal
- Second pass: Internal "critic" evaluates against known patterns:
  - Over-engineering detection
  - Tool-appropriateness check (script vs native vs prompt)
  - Format fragility assessment
- Third pass: Revised proposal with confidence calibration
- Add adversarial self-review step before output
- Higher latency but better quality

## Option 4: Tool Selection Hierarchy
<lens>: consolidation
<probability>: 0.55
<changes>:
- Define explicit tool selection hierarchy:
  1. Native platform features (prompt-based) - Preferred
  2. Existing patterns (skills, hooks) - Check if exists
  3. New scripts - Last resort, only if 1-2 don't exist
- Require discovery phase before suggesting new code
- Add "Check existing implementations" gate before proposing solutions
- Integrates discovery_patterns.md into workflow
