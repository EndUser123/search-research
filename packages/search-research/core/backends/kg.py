"""Knowledge Graph Search Backend - Entity-based search using KG data.

This backend searches a knowledge graph containing entities and their
associations with conversations.
"""

from pathlib import Path
from typing import Any
from ..config import config

SearchResult = dict[str, Any]

BACKEND_KG = "KG"


class KGBackend:
    """Knowledge Graph Entity Search.

    Searches entities loaded from a knowledge graph and finds conversations
    containing those entities.
    """

    def __init__(self, kg_data_path: str | None = None):
        """Initialize with KG data path.

        Args:
            kg_data_path: Path to knowledge graph output directory.
                Defaults to config.DEFAULT_KG_PATH (environment variable:
                SEARCH_RESEARCH_KG_PATH, or P:\\\\projects/kg_builder/knowledge_graph_output)
        """
        self._kg_data_path_input = kg_data_path  # Store original for testing
        self._kg_data_path_obj = Path(kg_data_path or config.DEFAULT_KG_PATH)
        self._index: dict[str, dict[str, Any]] = {}
        self._conversation_entities: dict[str, list[str]] = {}
        self._indexed = False

    @property
    def kg_data_path(self):
        """Get the KG data path as a Path-like object with custom __str__."""
        class _PathWrapper:
            def __init__(self, path_obj, original_str):
                self._path = path_obj
                self._original = original_str

            def __truediv__(self, other):
                return self._path.__truediv__(other)

            def __getattr__(self, name):
                return getattr(self._path, name)

            def __str__(self):
                return self._original if self._original else str(self._path)

            def __repr__(self):
                return repr(self._path)

        return _PathWrapper(self._kg_data_path_obj, self._kg_data_path_input)

    def build_index(self) -> None:
        """Build index from entities.json and conversation_entities.json."""
        self._index = {}
        self._conversation_entities = {}

        # Import json here to avoid issues
        import json

        # Load entities
        entities_path = self._kg_data_path_obj / "entities.json"
        if entities_path.exists():
            try:
                with open(entities_path, encoding="utf-8") as f:
                    entities = json.load(f)
                for entity in entities:
                    text = entity.get("text", "").lower()
                    if text:
                        self._index[text] = entity
            except (json.JSONDecodeError, OSError):
                pass

        # Load conversation entities
        conv_entities_path = self._kg_data_path_obj / "conversation_entities.json"
        if conv_entities_path.exists():
            try:
                with open(conv_entities_path, encoding="utf-8") as f:
                    self._conversation_entities = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        self._indexed = True

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for entities and optionally conversations containing them.

        Args:
            query: Search query - single entity or space-separated AND query.
            limit: Maximum number of results to return.

        Returns:
            List of SearchResult dicts with keys:
            - id: Unique identifier
            - source: Backend name ("KG")
            - title: Result title
            - content: Result content
            - score: Relevance score (0-1)
            - metadata: Additional info
        """
        # Handle empty/invalid queries
        if not query or not isinstance(query, str):
            return []
        query = query.strip()
        if not query:
            return []

        if not self._indexed:
            self.build_index()

        # Parse query - handle AND keyword
        query_normalized = query.replace(" AND ", " ")
        terms = [t.lower().strip() for t in query_normalized.split() if t.strip()]

        if not terms:
            return []

        results = []

        if len(terms) == 1:
            # Single entity search - return matching entities
            results = self._search_single_entity(terms[0], limit)
        else:
            # Multi-entity AND query - find conversations with all entities
            results = self._search_and_query(terms, limit)

        return results[:limit]

    def _search_single_entity(self, term: str, limit: int) -> list[SearchResult]:
        """Search for a single entity by exact or partial match."""
        results = []
        seen = set()

        # Exact matches first (higher score)
        for entity_text, entity in self._index.items():
            if entity_text == term:
                result = self._format_entity_result(entity, score=0.8)
                if result["id"] not in seen:
                    results.append(result)
                    seen.add(result["id"])

        # Partial matches (lower score)
        for entity_text, entity in self._index.items():
            if term in entity_text and entity_text != term:
                result = self._format_entity_result(entity, score=0.5)
                if result["id"] not in seen:
                    results.append(result)
                    seen.add(result["id"])

        return results[:limit]

    def _search_and_query(self, terms: list[str], limit: int) -> list[SearchResult]:
        """Search for conversations containing all specified entities."""
        results = []

        # Find conversations containing all terms
        for conv_id, entities in self._conversation_entities.items():
            entities_lower = [e.lower() for e in entities]

            # Check if all terms are in this conversation
            if all(term in entities_lower for term in terms):
                # Collect matching entities for metadata
                matching_entities = [
                    e for e in entities
                    if any(term in e.lower() for term in terms)
                ]

                result = {
                    "id": f"kg_conv_{conv_id}",
                    "source": BACKEND_KG,
                    "title": f"Conversation {conv_id}",
                    "content": f"Contains: {', '.join(matching_entities)}",
                    "score": 0.7,
                    "entities": matching_entities,  # Include entities at top level for boosting
                    "metadata": {
                        "conversation_id": conv_id,
                        "entities": matching_entities,
                        "entity_count": len(matching_entities),
                    },
                }
                results.append(result)

        return results[:limit]

    def _format_entity_result(self, entity: dict[str, Any], score: float) -> SearchResult:
        """Format an entity as a SearchResult."""
        entity_id = entity.get("id", "unknown")
        entity_text = entity.get("text", "")
        entity_type = entity.get("type", "")

        return {
            "id": f"kg_entity_{entity_id}",
            "source": BACKEND_KG,
            "title": f"{entity_type}: {entity_text}" if entity_type else entity_text,
            "content": entity.get("text", ""),
            "score": score,
            "entities": [entity_text],  # Include matched entity for boosting
            "metadata": {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "confidence": entity.get("confidence", 0),
                "occurrences": entity.get("occurrences", 0),
            },
        }


__all__ = ["BACKEND_KG", "KGBackend"]
