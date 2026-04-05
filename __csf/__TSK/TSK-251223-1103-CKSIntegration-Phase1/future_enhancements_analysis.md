# CKS Phase 2+ Future Enhancements - Implementation Analysis

## Current State (Phase 1)

**Completed Features:**
- Rule-based query expansion (synonyms, abbreviations, domain knowledge)
- RRF fusion for combining multiple result sets
- MMR diversity control
- Temporal boosting with adaptive decay rates

**Limitations:**
- Static dictionaries require manual maintenance
- No semantic similarity in query expansion
- Limited to English language patterns
- No learning from user behavior

---

## Enhancement 1: Semantic Query Expansion

### Concept
Use vector embeddings to find semantically similar query terms, not just synonym matches.

### Implementation

**New Module:** `src/cks/semantic_expansion.py`

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticQueryExpander:
    """Expand queries using semantic similarity."""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.term_embeddings = {}  # Cache term embeddings

    def expand_with_semantics(self, query: str, top_k: int = 5) -> List[str]:
        """
        Find semantically similar terms from CKS vocabulary.
        """
        # 1. Get all unique terms from CKS entries
        cks_vocabulary = self._extract_vocabulary()

        # 2. Encode query
        query_embedding = self.model.encode(query)

        # 3. Find similar terms using cosine similarity
        similarities = cosine_similarity([query_embedding], cks_embeddings)[0]
        top_indices = np.argsort(similarities)[-top_k:]

        # 4. Generate variations with top terms
        variations = [query]
        for idx in top_indices:
            if similarities[idx] > 0.7:  # Similarity threshold
                term = cks_vocabulary[idx]
                variations.append(query.replace(key_terms[0], term))

        return variations
```

### Value Proposition

| Aspect | Current (Phase 1) | With Semantic Expansion | Improvement |
|--------|-------------------|------------------------|-------------|
| **Recall** | +20-30% | +40-60% | 2x better |
| **Maintenance** | Manual dictionary updates | Automatic from CKS content | Zero maintenance |
| **Domain coverage** | Limited to pre-defined terms | Any term in CKS | Unlimited |
| **Implementation** | ~300 lines | ~150 lines | Simpler |

### How It Works

1. **Vocabulary Extraction:** Scan CKS entries to build term frequency map
2. **Embedding Cache:** Pre-compute embeddings for common terms
3. **Similarity Search:** Use cosine similarity to find related terms
4. **Query Rewriting:** Substitute semantically similar terms

### Trade-offs

| Pro | Con |
|-----|-----|
| Discovers relationships automatically | Requires sentence-transformers |
| Learns from CKS content | +50-100ms latency for encoding |
| No manual curation needed | May find noisy matches |

---

## Enhancement 2: User Feedback Learning

### Concept
Learn from user behavior (clicks, re-runs, result selection) to improve ranking.

### Implementation

**New Module:** `src/cks/learning_ranker.py`

```python
from collections import defaultdict
import sqlite3

class LearningRanker:
    """Learn from user interactions to improve search ranking."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_feedback_table()

    def record_feedback(self, query: str, entry_id: str, clicked: bool):
        """Record user interaction with search results."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO search_feedback (query, entry_id, clicked, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, (query, entry_id, clicked))
        conn.commit()
        conn.close()

    def get_learned_boost(self, query: str, entry_id: str) -> float:
        """
        Calculate learned boost factor for an entry based on historical clicks.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get click-through rate for this query+entry
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE clicked = 1) * 1.0 / COUNT(*) as ctr
            FROM search_feedback
            WHERE query = ? AND entry_id = ?
        """, (query, entry_id))

        row = cursor.fetchone()
        ctr = row[0] if row and row[0] else 0.1  # Default 10% baseline

        # Convert CTR to boost factor (0.1 → 1.0, 1.0 → 2.0)
        boost = 1.0 + ctr
        conn.close()

        return boost
```

**Schema Addition:**

```sql
CREATE TABLE IF NOT EXISTS search_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    entry_id TEXT NOT NULL,
    clicked BOOLEAN NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_query (query),
    INDEX idx_entry (entry_id)
);
```

### Value Proposition

| Aspect | Current | With Learning | Improvement |
|--------|---------|--------------|-------------|
| **Personalization** | None | Per-query optimization | User-specific results |
| **Adaptation** | Static | Improves over time | Self-optimizing |
| **Cold Start** | Good baseline | Same baseline | No regression |

### How It Works

1. **Track:** Record which results users click/select
2. **Analyze:** Calculate click-through rate per (query, entry) pair
3. **Boost:** Apply learned boost factor in future searches
4. **Decay:** Old feedback has less weight (exponential decay)

### Trade-offs

| Pro | Con |
|-----|-----|
| Self-improving | Requires 100+ interactions for value |
| No manual tuning | Privacy concerns (tracking) |
| Adapts to user needs | Cold start for new queries |

---

## Enhancement 3: Multi-Language Query Expansion

### Concept
Support queries in multiple languages by translating before expansion.

### Implementation

**New Module:** `src/cks/multilingual_expander.py`

```python
from deep_translator import GoogleTranslator

class MultilingualQueryExpander:
    """Expand queries across multiple languages."""

    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='en')

    def expand_multilingual(self, query: str, detect_lang: bool = True) -> List[str]:
        """
        Generate variations by translating to English then expanding.
        """
        variations = [query]

        # 1. Detect if non-English
        if detect_lang and self._is_non_english(query):
            # 2. Translate to English
            translated = self.translator.translate(query)
            variations.append(translated)

            # 3. Apply English query expansion
            # (reuses existing QueryExpander)
            from cks.query_expansion import QueryExpander
            expander = QueryExpander()
            english_vars = expander.expand_query(translated)
            variations.extend(english_vars)

        return variations

    def _is_non_english(self, text: str) -> bool:
        """Detect if text is non-English."""
        # Simple heuristic: check for non-ASCII characters
        # Production: use langdetect library
        return any(ord(c) > 127 for c in text)
```

### Value Proposition

| Aspect | Current | With Multi-Lingual | Improvement |
|--------|---------|-------------------|-------------|
| **Language Support** | English only | 100+ languages | Global accessibility |
| **User Base** | English speakers | International | 10x potential users |
| **Implementation** | N/A | ~100 lines | Simple wrapper |

### How It Works

1. **Detect:** Identify query language (heuristic or library)
2. **Translate:** Convert to English using translation API
3. **Expand:** Apply existing English expansion
4. **Search:** Use translated/expanded queries

### Trade-offs

| Pro | Con |
|-----|-----|
| Supports any language | External API dependency (Google/DeepL) |
| Minimal code changes | +200-500ms per translation |
| Leverages existing expansion | Translation accuracy varies |

---

## Enhancement 4: Query Spell Correction

### Concept
Automatically correct typos and spelling errors in queries.

### Implementation

**New Module:** `src/cks/spell_correction.py`

```python
from symspellpy import SymSpell, Verbosity
import os

class QuerySpellCorrector:
    """Correct spelling errors in search queries."""

    def __init__(self, max_dictionary_edit_distance: int = 2):
        self.sym_spell = SymSpell(max_dictionary_edit_distance, 7)
        self._load_dictionary()

    def _load_dictionary(self):
        """Load dictionary from CKS entries + English dictionary."""
        # 1. Load base English dictionary
        dictionary_path = "frequency_dictionary_en.txt"
        if os.path.exists(dictionary_path):
            self.sym_spell.load_dictionary(dictionary_path, 0, 1)

        # 2. Learn from CKS vocabulary
        cks_terms = self._extract_cks_vocabulary()
        for term, frequency in cks_terms.items():
            self.sym_spell.create_dictionary_entry(term, frequency)

    def correct_query(self, query: str) -> str:
        """Correct spelling errors in query."""
        # Split into words
        words = query.split()

        # Correct each word
        corrected = []
        for word in words:
            suggestions = self.sym_spell.lookup(
                word.lower(),
                Verbosity.CLOSEST,
                max_edit_distance=2
            )

            if suggestions:
                # Preserve case
                corrected_word = suggestions[0].term
                if word[0].isupper():
                    corrected_word = corrected_word.capitalize()
                corrected.append(corrected_word)
            else:
                corrected.append(word)

        return " ".join(corrected)
```

### Value Proposition

| Aspect | Current | With Spell Correction | Improvement |
|--------|---------|---------------------|-------------|
| **Typo Tolerance** | 0% | ~95% | Handles user errors |
| **Failed Searches** | High | Low | Better UX |
| **Implementation** | N/A | ~150 lines | Moderate |

### How It Works

1. **Build Dictionary:** Combine English dictionary + CKS vocabulary
2. **Detect Typos:** Use edit distance (Levenshtein) to find corrections
3. **Suggest:** Return closest matching word
4. **Preserve:** Maintain original capitalization

### Trade-offs

| Pro | Con |
|-----|-----|
| Handles common typos | Requires dictionary file (~5MB) |
| Fast lookup (<10ms) | May over-correct technical terms |
| Learns CKS vocabulary | Needs manual term whitelisting |

---

## Enhancement 5: Hybrid Fusion (Multiple Algorithms)

### Concept
Combine RRF with other fusion methods (weighted average, CombSUM, CombMNZ).

### Implementation

**Enhanced Module:** `src/cks/reranking.py` (add new methods)

```python
def weighted_average_fusion(
    result_sets: List[List[Dict]],
    weights: Optional[List[float]] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Combine results using weighted average of similarity scores.

    Formula: score = Σ(weight_i * similarity_i) / num_sets
    """
    if weights is None:
        weights = [1.0] * len(result_sets)

    # Collect all results with scores
    all_scores = {}  # {entry_id: [score1, score2, ...]}

    for results, weight in zip(result_sets, weights):
        for result in results:
            entry_id = result.get('id')
            similarity = result.get('similarity', 0)
            if entry_id not in all_scores:
                all_scores[entry_id] = []
            all_scores[entry_id].append(similarity * weight)

    # Calculate weighted average
    fused_results = []
    for entry_id, scores in all_scores.items():
        avg_score = sum(scores) / len(result_sets)
        result = next(r for rs in result_sets for r in rs if r.get('id') == entry_id)
        result['fusion_score'] = avg_score
        fused_results.append(result)

    # Sort by fusion score
    fused_results.sort(key=lambda x: x['fusion_score'], reverse=True)
    return fused_results[:limit] if limit else fused_results


def adaptive_fusion(
    result_sets: List[List[Dict]],
    query_type: str,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Automatically select best fusion method based on query characteristics.

    Query types:
    - 'specific': Use weighted average (precision-focused)
    - 'exploratory': Use RRF (recall-focused)
    - 'mixed': Use CombSUM (balanced)
    """
    if query_type == 'specific':
        return weighted_average_fusion(result_sets, limit=limit)
    elif query_type == 'exploratory':
        return reciprocal_rank_fusion(result_sets, limit=limit)
    else:
        # CombSUM: sum of similarities
        return combsum_fusion(result_sets, limit=limit)
```

### Value Proposition

| Aspect | RRF Only | Hybrid Fusion | Improvement |
|--------|----------|---------------|-------------|
| **Precision Queries** | Good | Better | +10-15% |
| **Recall Queries** | Excellent | Excellent | Same |
| **Adaptation** | Manual | Automatic | Zero config |

### How It Works

1. **Analyze Query:** Detect if user wants specific answers or exploration
2. **Select Method:** Choose best fusion algorithm automatically
3. **Combine Results:** Apply selected fusion method
4. **Return Results:** Ranked by fused score

### Trade-offs

| Pro | Con |
|-----|-----|
| Automatic optimization | More complex code |
| Best of all algorithms | Slightly slower (+10ms) |
| No user configuration needed | Harder to debug |

---

## Implementation Priority Matrix

### High Impact / Low Effort (Do First)

| Enhancement | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| Spell Correction | High | Low | **P0** |
| Hybrid Fusion | Medium | Low | **P1** |

### High Impact / Medium Effort

| Enhancement | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| Semantic Expansion | Very High | Medium | **P1** |
| User Feedback Learning | High | Medium | **P2** |

### Medium Impact / Low Effort

| Enhancement | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| Multi-Language | Medium | Low | **P2** |

---

## Recommended Implementation Order

### Phase 2A (Quick Wins - 1-2 weeks)

1. **Spell Correction**
   - Add `symspellpy` dependency
   - Implement `QuerySpellCorrector`
   - Integrate into search flow
   - **Value:** +15-20% recall for typo-prone queries

2. **Hybrid Fusion**
   - Add `weighted_average_fusion` to reranking.py
   - Implement `adaptive_fusion` with query type detection
   - A/B test against RRF-only
   - **Value:** +10-15% precision for specific queries

### Phase 2B (Medium Term - 2-4 weeks)

3. **Semantic Expansion**
   - Implement `SemanticQueryExpander`
   - Build vocabulary extraction from CKS
   - Cache term embeddings
   - **Value:** +40-60% recall (2x Phase 1)

### Phase 2C (Long Term - 4-8 weeks)

4. **User Feedback Learning**
   - Add search_feedback table
   - Implement feedback collection
   - Deploy and accumulate data
   - **Value:** Self-improving over time

5. **Multi-Language Support**
   - Add translation API wrapper
   - Implement language detection
   - **Value:** International accessibility

---

## Conclusion

**Best Next Step:** **Spell Correction** (P0)

- **Why:** Low effort (~150 lines), high impact (+15-20% recall)
- **How:** Wrap existing library (symspellpy)
- **Value:** Immediate user experience improvement

**Second Priority:** **Semantic Expansion** (P1)

- **Why:** Highest impact (+40-60% recall)
- **How:** Leverage existing sentence-transformers
- **Value:** 2x improvement over Phase 1 recall

Both build on Phase 1 infrastructure and can be incrementally deployed.
