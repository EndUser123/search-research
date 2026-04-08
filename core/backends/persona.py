"""Persona Memory Backend for research.

Cognitive-spectrum search with 3D score support (novelty, feasibility, impact).
"""

from pathlib import Path
from typing import Any

# Backend name constant
BACKEND_PERSONA = "PERSONA"


class PersonaMemoryBackend:
    """
    Search backend for persona memory database.

    Wraps the PersonaMemory FTS5 search to enable unified
    cross-system search alongside code, docs, CKS, and CHS.

    Usage:
        backend = PersonaMemoryBackend()
        results = backend.search("database design", limit=10)
    """

    def __init__(self, db_path: str | Path | None = None):
        """Initialize the persona memory backend.

        Args:
            db_path: Optional custom path to persona_memory.db.
                     Defaults to ~/.claude/data/persona_memory.db
        """
        self._db_path = db_path
        self._memory = None
        self._available = False

        # Lazy initialization - only connect when first used
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy initialization of PersonaMemory connection."""
        if self._initialized:
            return

        try:
            # Try to import but handle gracefully if not available
            from features.cognitive.persona_memory import PersonaMemory

            self._memory = PersonaMemory(db_path=self._db_path, auto_connect=True)
            self._available = True
            self._initialized = True
        except Exception:
            # Persona memory not available - module missing or DB error
            self._available = False
            self._initialized = True

    @property
    def available(self) -> bool:
        """Check if persona memory backend is available."""
        self._ensure_initialized()
        return self._available

    def search(
        self,
        query: str,
        limit: int = 10,
        persona: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search persona memory for matching outputs.

        Args:
            query: Search query for FTS5 full-text search
            limit: Maximum number of results to return
            persona: Optional persona filter (e.g., "INNOVATOR", "JUDGE")

        Returns:
            List of search results in unified format:
            - source: "PERSONA"
            - title: Persona name + topic
            - content: Persona output content
            - score: Normalized relevance score (0.0-1.0)
            - metadata: Dict with session_id, persona, timestamp, scores
        """
        self._ensure_initialized()

        if not self._available or not self._memory:
            return []

        # Use PersonaMemory's FTS5 search
        try:
            raw_results = self._memory.search(query, limit=limit, persona=persona)
        except Exception:
            # Search failed (SQL error, DB locked, etc.)
            return []

        # Convert to unified search format
        results = []
        for r in raw_results:
            # Calculate relevance score from 3D scores if available
            score = self._calculate_score(r)

            # Extract title from content or use topic
            title = self._extract_title(r)

            # Build metadata
            metadata = {
                "session_id": r.get("session_id", ""),
                "persona": r.get("persona", ""),
                "timestamp": r.get("timestamp", ""),
                "retention": r.get("retention_tag", ""),
            }

            # Add 3D scores to metadata if available
            if r.get("novelty"):
                metadata["novelty"] = r["novelty"]
            if r.get("feasibility"):
                metadata["feasibility"] = r["feasibility"]
            if r.get("impact"):
                metadata["impact"] = r["impact"]

            results.append({
                "source": BACKEND_PERSONA,
                "title": title,
                "content": r.get("content", ""),
                "score": score,
                "metadata": metadata,
            })

        return results[:limit]

    def _calculate_score(self, result: dict[str, Any]) -> float:
        """Calculate normalized relevance score from 3D scores.

        Args:
            result: Raw persona memory result dict

        Returns:
            Float score between 0.0 and 1.0
        """
        # If 3D scores available, use average
        if result.get("novelty") or result.get("feasibility") or result.get("impact"):
            scores = [
                result.get("novelty", 0),
                result.get("feasibility", 0),
                result.get("impact", 0),
            ]
            avg = sum(s for s in scores if s > 0) / len([s for s in scores if s > 0])
            return min(avg / 100.0, 1.0)

        # Default: moderate relevance for any match
        return 0.5

    def _extract_title(self, result: dict[str, Any]) -> str:
        """Extract a title from the persona result.

        Args:
            result: Raw persona memory result dict

        Returns:
            Title string
        """
        persona = result.get("persona", "UNKNOWN")
        topic = result.get("topic", "Unknown Topic")

        # Try to extract the core idea from content
        content = result.get("content", "")

        # Check for **Idea:** or **Top Idea:** patterns
        for pattern in ["**Top Idea**", "**Idea:**"]:
            if pattern in content:
                # Extract the idea text after the pattern
                parts = content.split(pattern, 1)
                if len(parts) > 1:
                    idea = parts[1].split("\n")[0].strip()
                    # Remove rank annotations like (Rank #1, Score: 92/100)
                    idea = idea.split("(")[0].strip()
                    idea = idea.split("**")[0].strip()
                    if idea:
                        return f"[{persona}] {idea}"

        # Fallback: persona + topic
        return f"[{persona}] {topic}"

    def query_by_persona(self, persona: str, limit: int = 20) -> list[dict[str, Any]]:
        """Query all outputs from a specific persona.

        Args:
            persona: Persona name (e.g., "INNOVATOR", "JUDGE")
            limit: Maximum results

        Returns:
            List of persona outputs in unified format
        """
        self._ensure_initialized()

        if not self._available or not self._memory:
            return []

        raw_results = self._memory.query_by_persona(persona)
        return self._convert_results(raw_results[:limit])

    def query_by_min_impact(self, min_impact: int, limit: int = 20) -> list[dict[str, Any]]:
        """Query outputs with impact >= threshold.

        Args:
            min_impact: Minimum impact score (0-100)
            limit: Maximum results

        Returns:
            List of high-impact outputs in unified format
        """
        self._ensure_initialized()

        if not self._available or not self._memory:
            return []

        raw_results = self._memory.query_by_min_impact(min_impact)
        return self._convert_results(raw_results[:limit])

    def _convert_results(self, raw_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert raw persona memory results to unified format.

        Args:
            raw_results: List of raw persona memory dicts

        Returns:
            List of unified format results
        """
        results = []
        for r in raw_results:
            score = self._calculate_score(r)
            title = self._extract_title(r)

            metadata = {
                "session_id": r.get("session_id", ""),
                "persona": r.get("persona", ""),
                "timestamp": r.get("timestamp", ""),
                "retention": r.get("retention_tag", ""),
            }

            if r.get("novelty"):
                metadata["novelty"] = r["novelty"]
            if r.get("feasibility"):
                metadata["feasibility"] = r["feasibility"]
            if r.get("impact"):
                metadata["impact"] = r["impact"]

            results.append({
                "source": BACKEND_PERSONA,
                "title": title,
                "content": r.get("content", ""),
                "score": score,
                "metadata": metadata,
            })

        return results

    def get_stats(self) -> dict[str, Any] | None:
        """Get persona memory statistics.

        Returns:
            Dict with stats (total_personas, total_sessions, etc.) or None if unavailable
        """
        self._ensure_initialized()

        if not self._available or not self._memory:
            return None

        return self._memory.get_stats()

    def close(self) -> None:
        """Close the persona memory connection."""
        if self._memory:
            self._memory.close()
            self._memory = None
        self._initialized = False

    def __enter__(self):
        """Context manager entry."""
        self._ensure_initialized()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()


__all__ = ["BACKEND_PERSONA", "PersonaMemoryBackend"]
