# LLM Citation Tracking

Automatic citation extraction and tracking for LLM responses.

## Overview

This module provides tools to automatically extract and track citations from LLM responses. It includes:

- **CitationExtractor**: Extracts video IDs and timestamps from LLM response text
- **LLMContext**: Manages context for LLM calls (query, result IDs, metadata)
- **CitationTracker**: Tracks citations for individual LLM calls
- **Context Manager & Decorator**: Easy-to-use patterns for automatic tracking

## Installation

The modules are located in `src/yt_fts/search/`:

```python
from yt_fts.search.llm_citation_hook import track_citations, track_citations_decorator
from yt_fts.search.citation_extractor import get_citation_extractor
from yt_fts.search.llm_context import create_llm_context
```

## Usage

### Context Manager Pattern

```python
from yt_fts.search.llm_citation_hook import track_citations

# Track citations for an LLM call
query = "machine learning tutorials"
result_ids = ["vid1", "vid2", "vid3"]

with track_citations(query, result_ids) as tracker:
    llm_response = ask_llm(f"Answer: {query}")
    tracker.set_response(llm_response)

# Get extracted citations
citations = tracker.get_citations()
for citation in citations:
    print(f"Video ID: {citation['video_id']}")
    print(f"Timestamp: {citation.get('timestamp', 'N/A')}")
    print(f"Context: {citation['text'][:50]}...")
```

### Decorator Pattern

```python
from yt_fts.search.llm_citation_hook import track_citations_decorator

@track_citations_decorator(query_arg="prompt", result_ids_arg="result_ids")
def ask_llm(prompt, result_ids, model="gpt-4"):
    return llm_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

# Citations are automatically extracted
response = ask_llm(
    prompt="Explain machine learning",
    result_ids=["vid1", "vid2"]
)
```

### Manual Citation Extraction

```python
from yt_fts.search.citation_extractor import get_citation_extractor

extractor = get_citation_extractor()

text = """
You can learn more at https://youtube.com/watch?v=abc12345678
Also check video xyz98765432 at 5:30 for details.
"""

citations = extractor.extract_citations(text)
# Returns: [
#   {'video_id': 'abc12345678', 'timestamp': None, 'text': '...'},
#   {'video_id': 'xyz98765432', 'timestamp': '5:30', 'text': '...'}
# ]
```

## Citation Patterns

The extractor recognizes these citation patterns:

1. **YouTube URLs**: `youtube.com/watch?v=VIDEO_ID`
2. **Short URLs**: `youtu.be/VIDEO_ID`
3. **Video ID + Timestamp**: `VIDEO_ID at 5:30` or `VIDEO_ID @ 10:15`
4. **Explicit references**: `video id: VIDEO_ID`

## API Reference

### `track_citations(query, result_ids)`

Context manager for tracking citations.

**Parameters:**
- `query` (str): The search query or prompt
- `result_ids` (List[str]): List of search result IDs

**Returns:** `CitationTracker` instance

**Methods:**
- `set_response(response)`: Set the LLM response and extract citations
- `get_response()`: Get the LLM response
- `get_citations()`: Get extracted citations

### `track_citations_decorator(query_arg, result_ids_arg)`

Decorator for automatic citation tracking.

**Parameters:**
- `query_arg` (str): Name of the argument containing the query
- `result_ids_arg` (str): Name of the argument containing result IDs

### `CitationExtractor`

**Methods:**
- `extract_citations(text)`: Extract citations from text

**Returns:** List of dictionaries with keys:
- `video_id` (str): 11-character YouTube video ID
- `timestamp` (str | None): Timestamp if found
- `text` (str): Surrounding context

## Error Handling

```python
from yt_fts.search.llm_citation_hook import CitationTrackingError

try:
    with track_citations(query, result_ids) as tracker:
        tracker.set_response(llm_response)
except CitationTrackingError as e:
    print(f"Citation tracking failed: {e}")
```

## Testing

Run tests with:

```bash
pytest tests/test_llm_citation_hook.py -v
```

## Example Output

```python
>>> extractor.extract_citations("See https://youtube.com/watch?v=abc12345678")
[{'video_id': 'abc12345678', 
  'timestamp': None, 
  'text': 'See https://youtube.com/watch?v=abc12345678'}]

>>> extractor.extract_citations("Video xyz98765432 at 5:30 explains it")
[{'video_id': 'xyz98765432', 
  'timestamp': '5:30', 
  'text': 'Video xyz98765432 at 5:30 explains it'}]
```
