# Unique Features Migration Plan

## From: `P://packages/research/` (research_skill)

### 1. Analysis & Quality Components
MIGRATE to `search-research/src/search_research/analysis/`:
- `gap_analysis.py` → `gap_analyzer.py`
- `source_reliability.py` → `contradiction_detector.py`
- `density.py` → `density_calculator.py`
- `clustering.py` → `topic_clusterer.py`, `novelty_tracker.py`

### 2. Research Orchestration
MIGRATE to `search-research/src/search_research/orchestration/`:
- `phases.py` → `phase_controller.py`
- `cli.py` → `saturation_detector.py` (extract class)
- `cost_tracker.py` → `cost_tracker.py`

### 3. Result Processing
MIGRATE to `search-research/src/search_research/processing/`:
- `normalization.py` → `result_normalizer.py`

## From: `P://projects/research-enhancement/`

### 4. Enhancement Components
MIGRATE to `search-research/src/search_research/enhancement/`:
- `enhanced_dependency_analyzer.py`
- `learning_system.py`
- `mode_relationship_mapper.py`
- `multi_mode_orchestrator.py`
- `quality_optimizer.py`
- `enhanced_research_engine.py`

## Verification
- [ ] All unique classes/functions migrated
- [ ] Tests pass
- [ ] No broken imports
- [ ] Update exports in __init__.py
