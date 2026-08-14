---
title: "do you or reddit or zai documentation or zai mcp servers, have any solution for slow searching with glm?

  ⎿  Found 63 "
date: "2025-12-27"
mode: "COPILOT"
uuid: "847a6517-5420-4de1-9027-cf6843430813"
entry_count: 1
---

## Human

do you or reddit or zai documentation or zai mcp servers, have any solution for slow searching with glm?

  ⎿  Found 63 lines (ctrl+o to expand)

● The GLM API endpoint seems slow/unresponsive. Let me test if the existing ZAI mode works (uses ResearchFlashEngine):

● Bash(cd "P:/__csf.nip" && python research/research.py --mode zai "what is GLM-4.6?" --max-results 3)
  ⎿  🔍 Researching: what is GLM-4.6?
     🧠 Mode: zai
     Loaded environment variables from P:\__csf.nip\.env
     … +12 lines (ctrl+o to expand)
  ⎿  Running PostToolUse hooks… (1/5 done)

● ZAI mode works but takes ~37s - too slow for "quick" mode.

  Summary:
  - GLM chat API endpoint: Times out (not suitable for quick mode)
  - ZAI web search: Works but ~37s (too slow for quick 5s target)

  Recommendation: For quick mode, keep GLM as optional/fallback. The fast sources are:
  - Tavily (~1.5s)
  - Serper/Google (~1.1s)
  - Exa neural (~1.2s)
  - Perplexity (~5s) ← bottleneck

  GLM/ZAI (37s) and CHS (42s initial load) are too slow for "quick" research. They're better suited for full research mode.

  Want me to:
  1. Remove GLM from quick mode (keep only fast sources)?
  2. Keep it but mark as slow/optional?
  3. Or just leave it and accept quick mode may take 30-40s?

## Assistant

## Summary: GLM Search Performance Solutions

I've researched Perplexity docs, ZAI documentation, Reddit discussions, and GitHub issues. Here's what I found:

### **The Core Problem (Confirmed)**
- **GLM direct API endpoint**: Times out completely (not viable)
- **ZAI ResearchFlashEngine**: ~37 seconds (your measurement is accurate)
- **Root causes**: 
  - Infrastructure capacity constraints (GitHub #3139)
  - Tool use reliability issues after complex tasks (GitHub #2944)
  - Architecture requires: search + generation + synthesis (inherently slow)

### **Performance Reality**
Your fast sources are genuinely 7-25x faster:
- Tavily: ~1.5s
- Serper: ~1.1s  
- Exa: ~1.2s
- **Perplexity: ~5s** ← This is your actual quick-mode bottleneck, not GLM

### **Official Position (From ZAI)**
ZAI docs acknowledge GLM has "higher parameter efficiency" and is "optimized for tool invocation" but doesn't market it for **speed**. They recommend thinking mode for complex reasoning, not search speed.

### **Recommendation: Option 1 (Remove GLM from Quick Mode)**

```python
QUICK_SOURCES = [
    "tavily",      # 1.1-1.5s
    "serper",      # 1.1s
    "exa",         # 1.2s
    "perplexity"   # 5s (acceptable, is actual bottleneck)
]

FULL_SOURCES = [
    *QUICK_SOURCES,
    "glm_zai",     # 37s - reserve for deep research
    "chs"          # 42s - reserve for deep research
]
```

**Why this works**:
1. ✅ Achieves 5s quick-mode target
2. ✅ Clear UX (no surprise delays)
3. ✅ Preserves GLM for complex reasoning in full mode
4. ✅ Data-backed (your test + GitHub issues + ZAI limitations)

**What ZAI *could* optimize** (undocumented):
- `content_size` parameter (reduce summary length) → might save 2-3s
- Timeout configuration in MCP server (not publicly documented)
- But neither solves the fundamental architecture slowness

I've saved detailed findings with implementation code to `glm_search_performance_findings.md`. The 37s measurement is spot-on and validates the decision to exclude GLM from quick mode.
