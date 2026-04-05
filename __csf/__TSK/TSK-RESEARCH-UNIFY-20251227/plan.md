# Research Unification Plan

## Step 1: Fix .gitignore Issue
- Check why `src/lib` is in .gitignore
- Move unified research to tracked location
- Ensure proper git tracking

## Step 2: Consolidate Providers
- Extract providers from `research/research_engine.py` (Tavily, Serper, Exa, Perplexity)
- Keep ZAI from `research_flash/`
- Create unified provider interface

## Step 3: Integrate Features
- CKS/CHS integration from `research_unified_inst.py`
- HyDE support from `hyde/hyde_research.py`
- Progress tracking
- Result synthesis

## Step 4: Create Entry Point
- Single `research.py` command in tracked location
- Proper CLI argument parsing
- Mode detection (auto, web, knowledge, etc.)

## Step 5: Test & Validate
- Test all providers
- Validate CKS/CHS integration
- Performance benchmarks
