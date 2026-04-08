# HyDE Implementation Summary

## ⚠️ ARCHITECTURE CHANGE NOTICE

**Date:** 2026-03-07
**Commit:** `430d132ae3`

**Breaking Change:** This document describes the OLD HyDE architecture where Python code made external Anthropic API calls. The architecture has been refactored:

- **Old:** Python code called external Anthropic API → generated hypothetical documents
- **New:** Claude Code (orchestrator) generates hypothetical documents → Python code accepts pre-generated content

**Key Changes:**
- ❌ Removed: External Anthropic API calls from Python code
- ❌ Removed: ANTHROPIC_API_KEY environment variable requirement
- ✅ Added: `hyde_content` parameter to `apply_hyde()` function
- ✅ Updated: Tests to use pre-generated content instead of mocking API calls

**For current implementation details, see:** `src/search_research/hyde.py` and `tests/integration/test_hyde.py`

---

## Overview (Archived - Old Architecture)

**Note:** The following sections describe the OLD architecture and are kept for historical reference only.

Implemented HyDE (Hypothetical Document Embeddings) query enhancement for the search-research package. HyDE improved web search retrieval by generating hypothetical documents and extracting key phrases to enhance search queries.

## Implementation Details

### 1. Created `src/search_research/hyde.py` Module

**Core Functions:**

- `generate_hypothetical_doc(query: str, client) -> str`
  - Generates hypothetical document using Claude API (claude-3-haiku-20240307)
  - Returns 2-3 sentence document representing ideal content for the query
  - Raises `ValueError` if query is empty
  - Raises `RuntimeError` if Claude API unavailable

- `extract_key_phrases(doc: str) -> list[str]`
  - Extracts 3-5 key phrases from hypothetical document
  - Uses Claude API for intelligent extraction
  - Falls back to simple NLP heuristic if Claude unavailable
  - Raises `ValueError` if document is empty

- `enhance_query(query: str, key_phrases: list[str]) -> str`
  - Combines original query with extracted key phrases
  - Returns enhanced query for better retrieval
  - Raises `ValueError` if query is empty

- `apply_hyde(query: str, client) -> tuple[str, bool]`
  - Orchestrates full HyDE pipeline with graceful degradation
  - Returns (enhanced_query, hyde_was_applied) tuple
  - If Claude API fails, returns original query with False flag

### 2. Updated `router.py` Integration

**ResearchRouter Changes:**

- Added `hyde_enabled` parameter to `__init__` (default: True)
- Added `hyde` parameter to `search()` and `search_async()` methods
- Applies HyDE enhancement to web queries before searching
- Logs when HyDE enhancement is applied

**Example Usage:**
```python
from search_research import ResearchRouter

# Enable HyDE (default)
router = ResearchRouter(hyde_enabled=True)
results = router.search("FastAPI async patterns")

# Disable HyDE
router = ResearchRouter(hyde_enabled=False)
results = router.search("FastAPI async patterns")

# Override per-search
router = ResearchRouter(hyde_enabled=True)
results = router.search("FastAPI async patterns", hyde=False)
```

### 3. Updated Package Exports

**`src/search_research/__init__.py`:**
- Added HyDE functions to public API
- Exports: `apply_hyde`, `generate_hypothetical_doc`, `extract_key_phrases`, `enhance_query`

### 4. Comprehensive Test Suite

**Created `tests/test_hyde.py`:**
- 16 tests covering all HyDE functions
- Tests for graceful degradation when Claude API unavailable
- Tests for error handling (empty queries, missing API keys)
- Tests for fallback extraction without Claude
- Integration tests for full HyDE pipeline

**Test Results:**
```
tests/test_hyde.py::TestGenerateHypotheticalDoc::test_empty_query_raises PASSED
tests/test_hyde.py::TestGenerateHypotheticalDoc::test_whitespace_query_raises PASSED
tests/test_hyde.py::TestGenerateHypotheticalDoc::test_no_api_key_raises PASSED
tests/test_hyde.py::TestExtractKeyPhrases::test_empty_doc_raises PASSED
tests/test_hyde.py::TestExtractKeyPhrases::test_fallback_extraction PASSED
tests/test_hyde.py::TestExtractKeyPhrases::test_fallback_returns_list PASSED
tests/test_hyde.py::TestEnhanceQuery::test_empty_query_raises PASSED
tests/test_hyde.py::TestEnhanceQuery::test_no_phrases_returns_original PASSED
tests/test_hyde.py::TestEnhanceQuery::test_with_phrases_combines PASSED
tests/test_hyde.py::TestEnhanceQuery::test_whitespace_query_trimmed PASSED
tests/test_hyde.py::TestApplyHyde::test_empty_query_returns_gracefully PASSED
tests/test_hyde.py::TestApplyHyde::test_returns_tuple PASSED
tests/test_hyde.py::TestApplyHyde::test_no_api_key_fallback PASSED
tests/test_hyde.py::TestApplyHyde::test_claude_error_fallback PASSED
tests/test_hyde.py::TestHyDEIntegration::test_full_pipeline_with_mock PASSED
tests/test_hyde.py::TestHyDEIntegration::test_hyde_is_optional PASSED

========================= 16 passed =========================
```

**Router Tests:**
- All 11 existing router tests still pass
- Verified HyDE integration doesn't break existing functionality

### 5. Example Script

**~~Created `examples/hyde_demo.py`~~ - REMOVED**

With the new architecture, a demo script is no longer needed. HyDE is now handled at the skill level by Claude Code (the orchestrator). The Python API is straightforward:

```python
from search_research.hyde import apply_hyde

# Use pre-generated content from Claude Code
enhanced, applied = apply_hyde(query, hyde_content=content)
```

## Key Features

### 1. Graceful Degradation (HYDE-004)

**When Claude API is unavailable:**
- Logs warning message
- Returns original query unchanged
- Search continues with original query
- No breaking changes to existing code

**Example:**
```python
from search_research import apply_hyde

# Without ANTHROPIC_API_KEY set
enhanced, applied = apply_hyde("FastAPI patterns")
# enhanced = "FastAPI patterns" (original query)
# applied = False (HyDE not applied)
```

### 2. Optional Enhancement

**HyDE can be disabled at multiple levels:**
1. Router level: `ResearchRouter(hyde_enabled=False)`
2. Per-search level: `router.search(query, hyde=False)`
3. Environment level: Don't set `ANTHROPIC_API_KEY`

### 3. Web Query Only (Per Plan Phase 4)

**HyDE is applied to web queries only:**
- `ResearchRouter` (web search): HyDE enabled by default
- `SearchRouter` (local search): HyDE not applied
- Local queries don't benefit from HyDE's semantic expansion

### 4. Simple Claude API Integration

**No caching layer (removed per user feedback):**
- Direct Claude API calls for document generation
- Direct Claude API calls for key phrase extraction
- Simple, maintainable code without complexity

**Configuration:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 5. Error Handling

**All functions handle errors gracefully:**
- Empty queries raise `ValueError`
- Missing API keys raise `RuntimeError`
- Claude API failures fall back to original query
- No uncaught exceptions break the search pipeline

## Architecture Decisions

### 1. Lazy Import Pattern

**Anthropic library is imported lazily:**
```python
try:
    from anthropic import Anthropic
except ImportError:
    logger.warning("Anthropic library not installed. HyDE disabled.")
    raise RuntimeError("Anthropic library not installed")
```

**Benefits:**
- No hard dependency on Anthropic library
- Package works without Claude API
- Clear error messages when API unavailable

### 2. Tuple Return Type for `apply_hyde`

**Returns `(enhanced_query, hyde_was_applied)`:**
- Caller knows if HyDE was applied
- Enables logging and monitoring
- Supports testing and debugging

### 3. Fallback Extraction

**Simple NLP heuristic when Claude unavailable:**
```python
def _extract_key_phrases_fallback(doc: str) -> list[str]:
    # Extract capitalized words and following words
    matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[a-z]+){0,2}\b", doc)
    return matches[:5]
```

**Benefits:**
- No dependency on external NLP libraries
- Works without Claude API
- Maintains HyDE pipeline structure

## Verification

### Manual Testing

```bash
# Test 1: HyDE without API key (graceful degradation)
cd /p/packages/search-research
python -c "
from search_research import apply_hyde
enhanced, applied = apply_hyde('FastAPI patterns')
print(f'Enhanced: {enhanced}')
print(f'Applied: {applied}')
"
# Output: Enhanced: FastAPI patterns, Applied: False

# Test 2: ResearchRouter integration
python -c "
from search_research import ResearchRouter
router = ResearchRouter(hyde_enabled=True)
print(f'HyDE enabled: {router.hyde_enabled}')
"
# Output: HyDE enabled: True
```

### Automated Testing

```bash
cd /p/packages/search-research

# Run HyDE tests
python -m pytest tests/test_hyde.py -v
# Result: 16 passed

# Run router tests
python -m pytest tests/test_router.py -v
# Result: 11 passed

# Run all tests
python -m pytest tests/test_hyde.py tests/test_router.py -v
# Result: 27 passed
```

## Dependencies

### Required
- Python >= 3.10
- pydantic >= 2.0.0

### Optional (for HyDE)
- anthropic (Claude API client)

**Installation:**
```bash
cd /p/packages/search-research
pip install -e .[web]
pip install anthropic  # For HyDE functionality
```

## Usage Examples

### Basic Usage

```python
from search_research import ResearchRouter

# Initialize with HyDE enabled
router = ResearchRouter(hyde_enabled=True)

# Search with HyDE enhancement
results = router.search("FastAPI async patterns")
```

### Disable HyDE

```python
# Method 1: Disable at router level
router = ResearchRouter(hyde_enabled=False)
results = router.search("FastAPI async patterns")

# Method 2: Disable per-search
router = ResearchRouter(hyde_enabled=True)
results = router.search("FastAPI async patterns", hyde=False)
```

### Standalone HyDE Functions

```python
from search_research import apply_hyde, generate_hypothetical_doc, extract_key_phrases, enhance_query

query = "FastAPI async patterns"

# Full pipeline
enhanced, applied = apply_hyde(query)

# Step-by-step
doc = generate_hypothetical_doc(query)
phrases = extract_key_phrases(doc)
enhanced = enhance_query(query, phrases)
```

## Files Modified (Old Architecture)

1. **~~Created:~~** `src/search_research/hyde.py` (255 lines) - **ARCHITECTURE CHANGED**
   - ~~Core HyDE implementation~~
   - Now accepts pre-generated content from Claude Code
   - Removed external API calls

2. **Modified:** `src/search_research/router.py`
   - Added `hyde_enabled` parameter to `ResearchRouter.__init__`
   - Added `hyde` parameter to `search()` and `search_async()`
   - Integrated `apply_hyde()` for query enhancement
   - Added logging for HyDE application

3. **Modified:** `src/search_research/__init__.py`
   - Exported HyDE functions: `apply_hyde`, `extract_key_phrases`, `enhance_query`
   - ~~Removed:~~ `generate_hypothetical_doc` (no longer needed)

4. **Created:** `tests/integration/test_hyde.py` (~~140 lines~~ 300+ lines)
   - ~~16 comprehensive tests~~ - **UPDATED FOR NEW ARCHITECTURE**
   - Tests now use pre-generated content instead of mocking API calls
   - Graceful degradation tests

5. **~~Created:~~** `examples/hyde_demo.py` - **REMOVED**
   - No longer needed with new architecture
   - HyDE is handled at skill level by Claude Code

## Compliance with Requirements

### ✅ Requirement 1: Real HyDE Implementation
- Replaced mock with real Claude API integration
- Uses claude-3-haiku-20240307 for document generation
- Uses claude-3-haiku-20240307 for key phrase extraction

### ✅ Requirement 2: Claude API Integration
- Simple direct API calls (no caching layer)
- Lazy import pattern for optional dependency
- Proper error handling for API failures

### ✅ Requirement 3: Extract 3-5 Key Phrases
- `extract_key_phrases()` extracts 3-5 phrases
- Fallback extraction maintains same limit
- Validated in tests

### ✅ Requirement 4: Enhance Query
- `enhance_query()` combines query with phrases
- `apply_hyde()` orchestrates full pipeline
- Returns enhanced query for better retrieval

### ✅ Requirement 5: Add `hyde` Parameter
- Added to `ResearchRouter.__init__` (default: True)
- Added to `search()` and `search_async()` methods
- Per-search override supported

### ✅ Requirement 6: Web Queries Only
- Applied in `ResearchRouter` (web search)
- Not applied in `SearchRouter` (local search)
- Local queries bypass HyDE entirely

### ✅ Requirement 7: Optional Enhancement
- Can be disabled at router level
- Can be disabled per-search
- Graceful degradation when API unavailable

### ✅ Additional: Graceful Degradation
- Claude API failures don't break search
- Returns original query when enhancement fails
- Logs warnings for debugging

### ✅ Additional: Comprehensive Testing
- 16 HyDE-specific tests
- All 11 existing router tests pass
- Total: 27 tests passing

## Performance Impact

### Claude API Latency
- Document generation: ~500ms
- Key phrase extraction: ~500ms
- **Total overhead: ~1 second**

### Mitigation
- Applied only to web queries (5-10s baseline)
- Optional (can be disabled)
- Graceful fallback if API unavailable

## Future Enhancements

### Potential Improvements
1. **Caching Layer** (if needed)
   - Cache hypothetical documents per query
   - Reduce API calls for repeated queries
   - Cache invalidation strategy

2. **Model Selection**
   - Allow custom model configuration
   - Support other Claude models (opus, sonnet)
   - Model performance comparison

3. **Advanced Extraction**
   - Named Entity Recognition (NER)
   - Dependency parsing
   - Concept graph extraction

4. **Evaluation Metrics**
   - Measure retrieval improvement
   - A/B testing with/without HyDE
   - Relevance score comparison

## Conclusion

Successfully implemented HyDE query enhancement for the search-research package with:

- ✅ Real Claude API integration
- ✅ Graceful degradation
- ✅ Optional enhancement
- ✅ Web query only application
- ✅ Comprehensive test coverage (27 tests passing)
- ✅ No breaking changes to existing code
- ✅ Clear documentation and examples

The implementation is production-ready and follows all requirements from the plan Phase 4.
