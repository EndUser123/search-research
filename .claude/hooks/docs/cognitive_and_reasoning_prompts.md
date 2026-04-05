# Cognitive Frameworks & Reasoning Modes - Prompt Reference Guide

## Unified Tag System

Both cognitive frameworks and reasoning modes now emit visible tags in responses:

- **[COG]** - Active Cognitive Frameworks (e.g., Cynefin, Hanlon's Razor, Devil's Advocate)
- **[SEQ]** - Sequential reasoning mode (step-by-step analysis)
- **[MAS]** - Multi-Agent reasoning mode (multiple perspectives)
- **[2ST]** - Two-Stage reasoning mode (separate reasoning and implementation)

**How it works**: Both systems inject explicit instructions for the model to prepend tags to responses, ensuring consistent visibility into active reasoning approaches.

## How to Invoke with Simple Prompts

### Cognitive Frameworks ([COG] tag)

Cognitive frameworks trigger automatically based on prompt intent. No special syntax needed.

**Diagnostic Prompts** (triggers: Calibrated Confidence, Cynefin, Hanlon's Razor):
```
diagnose why the API is returning 500 errors
investigate the memory leak in our service
what's causing the database slowdown?
```

**Implementation Prompts** (triggers: Assumption Surfacing, Outcome Anchoring, Inversion, Chesterton's Fence, Devil's Advocate):
```
implement a new user authentication system
refactor the payment processing module
add feature to export data as CSV
```

**Root Cause Analysis** (triggers: Cynefin Classification):
```
#rca why did the deployment fail?
perform root cause analysis on the incident
```

**Long/Complex Prompts** (triggers: Socratic Decomposition):
```
I need to improve the overall system architecture but I'm not sure where to start.
There are multiple issues with the codebase and I need help prioritizing fixes.
```

### Reasoning Modes ([SEQ], [MAS], [COG] tags)

Reasoning modes trigger automatically based on keywords in your prompt.

**Sequential Mode ([SEQ])** - Step-by-step analysis:
```
explain how to implement OAuth 2.0
describe the architecture of our system
how does the caching layer work?
step by step guide to deploying
```

**Multi-Agent Mode ([MAS])** - Compare alternatives/perspectives:
```
should we use Redis or Memcached?
compare PostgreSQL vs MongoDB for this use case
what are the trade-offs between REST and GraphQL?
which is better: microservices or monolith?
```

**Graph Mode** - Explore branching scenarios:
```
explore different architecture options for the payment system
what if we scale horizontally instead of vertically?
consider options for handling failure scenarios
branch the deployment strategy into multiple paths
```

**Two-Stage Mode** - Implementation tasks:
```
write a function to validate email addresses
create a class for managing user sessions
implement a REST API endpoint for orders
```

## Manual Override Modes

### Cognitive Frameworks Overrides

**Force Deep Analysis** (`#deep`):
```
#deep analyze the performance bottleneck
```
Forces implementation topic with all frameworks.

**Force RCA** (`#rca`):
```
#rca investigate the data corruption issue
```
Forces meta_rca topic with Cynefin framework.

**Fast Mode** (`#fast`):
```
#fast commit these changes
```
Disables all cognitive frameworks.

### Reasoning Modes

Reasoning modes are selected automatically, but you can influence them by using keywords from the tables above.

## Example: Unified Tag Emission

When you use a diagnostic prompt:

```
User: diagnose why the API is returning 500 errors
```

**Injected context**:
```
[COG] Active Cognitive Frameworks: Calibrated Confidence, Cynefin Classification, Hanlon's Razor

**TAG EMISSION REQUIRED**: Begin your response with '[COG]' tag followed by the active framework names above. This provides visibility into which cognitive frameworks are active. Format: '[COG] Active Frameworks: X, Y, Z'

**Calibrated Confidence**: For key claims in your response, state confidence: HIGH (verified via tool output/docs), MEDIUM (based on code reading), or LOW (inference — flag it). Do not present LOW-confidence claims as facts.

**Cynefin Framework**: Classify this problem domain before investigating. Is this Clear (known cause-effect, apply SOPs), Complicated (investigate to find cause), Complex (probe-sense-respond, experimentation needed), or Chaotic (act first to stabilize)? Select the appropriate analysis approach based on domain classification.

**Hanlon's Razor**: Before attributing issues to malice or intentional sabotage, consider simpler explanations: bugs, confusion, mistakes, time pressure, or misunderstanding. What evidence supports malice vs. incompetence vs. systemic causes?
```

**Model response starts with**:
```
[COG] Active Frameworks: Calibrated Confidence, Cynefin Classification, Hanlon's Razor

Based on the 500 error, I need to investigate...
```

When you use a comparison prompt:

```
User: should we use Redis or Memcached for caching?
```

**Injected context**:
```
Reasoning mode: multi_agent
Confidence: 2/4
Using multi_agent reasoning approach for this query.

**TAG EMISSION REQUIRED**: Begin your response with '[MAS]' tag to indicate the active reasoning mode. This provides visibility into which reasoning approach is being used.
```

**Model response starts with**:
```
[MAS]

When comparing Redis vs Memcached for caching, we need to consider...
```

And when the reasoning package processes the query, it will emit `[MAS]` in the final response.

## Testing

To verify both systems are working:

```bash
# Test cognitive frameworks
cd P:/packages/reasoning
python test_tag_emission.py cognitive

# Test reasoning modes
python test_tag_emission.py reasoning
```

## Architecture

**Cognitive Frameworks Hook**:
- Location: `P:/.claude/hooks/UserPromptSubmit_modules/cognitive_enhancers.py`
- Event: UserPromptSubmit (before tool execution)
- Function: `cognitive_enhancers(context: HookContext) -> HookResult`
- Config: `P:/.claude/hooks/cognitive_enhancers_config.json`

**Reasoning Mode Selector Hook**:
- Location: `P:/packages/reasoning/hooks/Start_reasoning_mode_selector.py`
- Event: Start (session start)
- Function: `process_prompt(data: dict) -> dict`
- Config: Environment-based (keyword detection)

Both systems use keyword-based intent detection and automatically inject context without requiring manual invocation.
