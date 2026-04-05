# Architecture Decision: Optimal /all Skill Design for Context Firewall

**Date:** 2026-03-11
**Template:** fast (LOW complexity, Generic domain)
**Decision Path:** DEFAULT (general architecture decision)

## Decision Statement

**What's changing:** Restructure /all skill from subprocess execution (CLI tool) to inline skill execution that leverages subagents as intelligent context firewall.

**Why:** Current architecture runs Python in subprocess where Agent tool is unavailable, defeating the entire purpose of using LLM intelligence for semantic filtering.

**Goal:** Subagent receives raw search results (30-50 items), extracts 5-10 key insights using LLM understanding, main agent ONLY sees filtered insights (not raw data).

## Options

### Option A: Inline skill execution with Agent tool calls

**Implementation:**
- SKILL.md executes search code inline using Bash tool
- Pass results to Agent tool for Layer 2 filtering
- Return filtered insights to user
- Subagent becomes intelligent context firewall

**Pro:** Correct architecture - subagent IS the LLM filter, main agent never sees raw data

**Con:** Requires SKILL.md refactoring (current all.py becomes module)

**Differs on:** Execution model (subprocess vs inline), LLM utilization (keyword-based vs semantic)

### Option B: Keep subprocess execution, add Agent tool bridge

**Implementation:**
- all.py runs as subprocess, writes JSON to temp file
- SKILL.md reads JSON, passes to Agent tool
- Subagent filters, returns to main agent

**Pro:** Minimal refactoring, preserves current structure

**Con:** Still creates intermediate file, indirect execution path, subprocess isolation unnecessary

**Differs on:** Execution model (subprocess with bridge vs pure inline), data flow (file-based vs direct)

### Option C: Pure Python filtering (current state)

**Implementation:** Status quo - keyword-based filtering in layer2_filter.py

**Pro:** Fast, deterministic, no LLM overhead

**Con:** No semantic understanding, crude keyword matching, defeats subagent purpose

**Differs on:** Intelligence level (rule-based vs LLM semantic), filtering quality

## Recommendation

**Option A** - Inline skill execution with Agent tool calls

**Why A > B:** Option B's subprocess-to-file-to-Agent pipeline is architecturally redundant. If Agent tool is available in SKILL.md context, running Python as subprocess adds no value - just adds file I/O and process spawning overhead. Execute Python inline where Agent tool lives.

**Why A > C:** Keyword-based filtering (Option C) cannot understand query context or semantic relevance. User insight: "python is a rough tool without intelligence" - subagent IS the intelligent context firewall.

## Implementation

### Before (Current - Broken)

```python
# SKILL.md executes: python all.py "query"
# all.py runs as subprocess - NO Agent tool access

async def search_universal_with_filtering(...):
    results = await router.search_async(query, limit=limit)
    # Layer 2: Only keyword-based filtering (no LLM)
    filtered_results = await _keyword_based_filtering(results, query)
    return filtered_results
```

### After (Fixed - Option A)

```python
# SKILL.md - Inline execution

# Step 1: Execute search using Bash tool
import asyncio
from search_research import UnifiedAsyncRouter

router = UnifiedAsyncRouter(mode="auto", enable_jmri=True)
results = await router.search_async(query, limit=40)

# Step 2: Pass results to Agent tool for Layer 2 filtering
if should_apply_context_filter(results, query):
    filtered = Agent(
        subagent_type="general-purpose",
        prompt=f"""Filter these search results to key insights:

QUERY: {query}
RESULTS: {results}

Extract 5-10 most relevant insights, group by theme.
Return JSON with themes and insights.""",
        description="Context-aware result filtering"
    )
    # Main agent sees ONLY filtered insights, not raw data
    display_themed_results(filtered)
```

**Rollback:** Revert all.py to subprocess entry point, remove inline Agent calls from SKILL.md.

## Quick Ramifications

- **Breaks anything?** No - UnifiedAsyncRouter remains unchanged, only execution context moves from subprocess to inline
- **Edge cases:** Large result sets (>50 items) - subagent receives all, filters to key insights, main agent context saved
- **Constraints:** Subagent token limits apply, but that's intentional (forcing distillation)

## Confidence

**Confidence: 85%** — Based on: (1) User's explicit requirement: "agents need to get the info, they are the context firewall", (2) Claude Code Agent tool documentation confirms it IS the LLM interface in skill context, (3) subprocess execution pattern is architectural mismatch for LLM-based filtering.

**Evidence basis:**
- User requirements: Direct quote from conversation
- System documentation: Agent tool specification
- Current implementation: all.py subprocess execution confirmed non-functional for Layer 2

**Key assumptions:**
1. Agent tool is available in SKILL.md inline execution (confirmed by system prompt)
2. UnifiedAsyncRouter can be imported and used in skill context (already tested)
3. Subagent token limits are acceptable tradeoff for semantic filtering quality

**Weakest assumption:** Subagent can handle 40-50 result items without hallucination or truncation.

**Mitigation:** Implement hybrid approach - Layer 1 Python reduces to 20 items, Layer 2 subagent filters to 5-10 key insights. Best of both: semantic relevance with manageable token count.

## Adversarial Self-Review

**Weakest assumption:** Subagent token limits won't prevent effective filtering of 40-item result sets.

**If wrong:** Subagent truncates input, misses relevant results, returns incomplete filtering.

**Mitigation:** Implement Layer 1 pre-filter (Python reduces to 20 items) before passing to Layer 2 subagent. Balances token limits with semantic filtering quality.

## Related Files

- P:/packages/search-research/skills/all/all.py - Current subprocess implementation
- P:/packages/search-research/skills/all/layer2_filter.py - Layer 2 filtering logic (needs Agent tool integration)
- P:/packages/search-research/skills/all/SKILL.md - Needs refactoring to inline execution
- P:/packages/search-research/src/search_research/__init__.py - UnifiedAsyncRouter export

## Next Steps

1. Extract search execution logic from all.py into importable module
2. Refactor SKILL.md to execute searches inline
3. Integrate Agent tool calls for Layer 2 filtering
4. Test with real searches to verify subagent filtering quality
5. Implement Layer 1 pre-filter (20-item limit) if subagent truncation observed
