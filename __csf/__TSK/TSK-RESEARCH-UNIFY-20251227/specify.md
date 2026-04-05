# Research Unification Specification

## Objective
Unify all research implementations into a single "best of breed" research command that:
1. Is NOT in .gitignore (properly tracked in git)
2. Consolidates features from all existing research implementations
3. Provides a single entry point for `/research`

## Problem Statement
- Current `research_unified_inst.py` is in `src/lib/` which is in .gitignore
- Multiple duplicate research implementations exist across the codebase
- No single source of truth for research functionality

## Success Criteria
1. Unified research command tracked in git (not in .gitignore)
2. All web search providers available (Tavily, Serper, ZAI, Exa, etc.)
3. CKS/CHS integration working
4. Backward compatible with existing usage
5. Single CLI entry point
