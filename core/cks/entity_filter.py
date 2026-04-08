"""CKS Entity Filter Extension.

Adds entity filtering, hybrid retrieval, and session recall logging to CKS.

Usage:
    from .entity_filter import CKSEntityFilter

    # Extend CKS with entity filtering
    cks = CKS()
    entity_cks = CKSEntityFilter(cks)

    # Create entities
    entity_cks.create_entity("cks", "Constitutional Knowledge System", "project")

    # Link entities to entries
    entity_cks.link_entity(entry_id, "cks")

    # Search with entity filter
    results = entity_cks.search_with_entity_filter("database patterns", entity_slug="cks")
"""

import re
from datetime import UTC, datetime
from uuid import uuid4


class CKSEntityFilter:
    """Entity Filter Extension for CKS.

    Adds hybrid entity + semantic retrieval, entity detection, and recall logging.
    Wraps a CKS instance to provide entity-aware search capabilities.
    """

    # Known entities for auto-detection (can be extended)
    KNOWN_ENTITIES = {
        "cks": "Constitutional Knowledge System",
        "desktop-commander": "Desktop Commander",
        "claude-code": "Claude Code",
        "nse": "Next Step Engine",
        "cwo12": "CWO12 Workflow Engine",
        "taskmaster": "TaskMaster",
    }

    def __init__(self, cks_instance) -> None:
        """Initialize entity filter with CKS instance.

        Args:
            cks_instance: An instance of CKS to extend

        """
        self.cks = cks_instance
        self._ensure_entities_exist()

    def _ensure_entities_exist(self) -> None:
        """Create known entities if they don't exist."""
        for slug, name in self.KNOWN_ENTITIES.items():
            try:
                self.create_entity(slug, name, "project")
            except Exception:
                pass  # Entity already exists

    # ========================================================================
    # Entity Management
    # ========================================================================

    def create_entity(self, slug: str, name: str, entity_type: str) -> str:
        """Create a new entity.

        Args:
            slug: Entity slug (e.g., "cks", "desktop-commander")
            name: Human-readable name
            entity_type: Type (project, environment, cluster, component)

        Returns:
            Entity slug

        Raises:
            ValueError: If entity_type is invalid

        """
        valid_types = ["project", "environment", "cluster", "component"]
        if entity_type not in valid_types:
            raise ValueError(f"Invalid entity_type: {entity_type}. Must be one of {valid_types}")

        self.cks.conn.execute(
            """INSERT OR IGNORE INTO entities (slug, name, type, created_at)
               VALUES (?, ?, ?, ?)""",
            (slug, name, entity_type, datetime.now(UTC).isoformat()),
        )
        self.cks.conn.commit()

        return slug

    def link_entity(self, entry_id: str, entity_slug: str) -> bool:
        """Link an entity to an entry.

        Args:
            entry_id: Entry ID
            entity_slug: Entity slug

        Returns:
            True if linked, False if already linked

        """
        try:
            self.cks.conn.execute(
                """INSERT OR IGNORE INTO entry_entities (entry_id, entity_type, created_at)
                   VALUES (?, ?, ?)""",
                (entry_id, entity_slug, datetime.now(UTC).isoformat()),
            )
            self.cks.conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ Failed to link entity: {e}")
            return False

    def unlink_entity(self, entry_id: str, entity_slug: str) -> bool:
        """Unlink an entity from an entry.

        Args:
            entry_id: Entry ID
            entity_slug: Entity slug

        Returns:
            True if unlinked

        """
        self.cks.conn.execute(
            "DELETE FROM entry_entities WHERE entry_id = ? AND entity_type = ?",
            (entry_id, entity_slug),
        )
        self.cks.conn.commit()
        return True

    def get_entities_for_entry(self, entry_id: str) -> list[dict]:
        """Get all entities linked to an entry.

        Args:
            entry_id: Entry ID

        Returns:
            List of entity dicts

        """
        rows = self.cks.conn.execute(
            """SELECT ee.entity_type, ee.entity_data, ee.created_at
               FROM entry_entities ee
               WHERE ee.entry_id = ?""",
            (entry_id,),
        ).fetchall()

        return [
            {
                "slug": row["entity_type"],
                "name": row.get("entity_data", ""),
                "type": row["entity_type"],
                "linked_at": row["created_at"],
            }
            for row in rows
        ]

    def get_all_entities(self, entity_type: str | None = None) -> list[dict]:
        """Get all entities, optionally filtered by type.

        Args:
            entity_type: Optional type filter

        Returns:
            List of entity dicts

        """
        if entity_type:
            rows = self.cks.conn.execute(
                "SELECT slug, name, type, created_at FROM entities WHERE type = ?",
                (entity_type,),
            ).fetchall()
        else:
            rows = self.cks.conn.execute(
                "SELECT slug, name, type, created_at FROM entities",
            ).fetchall()

        return [
            {
                "slug": row["slug"],
                "name": row["name"],
                "type": row["type"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    # ========================================================================
    # Entity Detection
    # ========================================================================

    def _detect_entities_in_query(self, query: str) -> list[str]:
        """Detect entity mentions in query.

        Args:
            query: Search query

        Returns:
            List of detected entity slugs

        """
        query_lower = query.lower()
        detected = []

        # Check known entities
        for slug in self.KNOWN_ENTITIES:
            # Match whole word or hyphenated phrase
            pattern = r"\b" + re.escape(slug.lower()) + r"\b"
            if re.search(pattern, query_lower):
                detected.append(slug)

        return detected

    # ========================================================================
    # Entity-Filtered Search
    # ========================================================================

    def search_with_entity_filter(
        self,
        query: str,
        entity_slug: str | None = None,
        entry_type: str | None = None,
        limit: int = 5,
        auto_detect: bool = True,
    ) -> list[dict]:
        """Search with optional entity filtering.

        Combines semantic search with entity filtering for hybrid retrieval.

        Args:
            query: Search query
            entity_slug: Optional entity slug to filter by
            entry_type: Optional entry type filter
            limit: Max results to return
            auto_detect: Auto-detect entities from query if entity_slug not provided

        Returns:
            List of entry dicts with entity information

        """
        # Auto-detect entities if not provided
        if entity_slug is None and auto_detect:
            detected = self._detect_entities_in_query(query)
            if detected:
                entity_slug = detected[0]  # Use first detected entity
                print(f"[EntityFilter] Auto-detected entity: {entity_slug}")

        # Get semantic results (fetch more for filtering)
        fetch_limit = limit * 2 if entity_slug else limit
        results = self.cks.search_semantic(query, entry_type=entry_type, limit=fetch_limit)

        # Filter by entity if specified
        if entity_slug:
            filtered_results = []
            seen_ids = set()

            for result in results:
                entry_id = result.get("id")
                if entry_id in seen_ids:
                    continue

                # Check if entry has this entity
                rows = self.cks.conn.execute(
                    "SELECT 1 FROM entry_entities WHERE entry_id = ? AND entity_type = ?",
                    (entry_id, entity_slug),
                ).fetchall()

                if rows:
                    # Add entity info to result
                    result["entity_slug"] = entity_slug
                    result["entities"] = self.get_entities_for_entry(entry_id)
                    filtered_results.append(result)
                    seen_ids.add(entry_id)

                if len(filtered_results) >= limit:
                    break

            results = filtered_results

        # Add entity info to all results
        for result in results:
            if "entities" not in result:
                entry_id = result.get("id")
                result["entities"] = self.get_entities_for_entry(entry_id)

        return results

    # ========================================================================
    # Recall Logging
    # ========================================================================

    def log_recall(
        self, session_id: str, query: str, results: list[dict], entity_slug: str | None = None
    ) -> None:
        """Log recall for debugging and analysis.

        Args:
            session_id: Session identifier
            query: Search query
            results: Search results from search_semantic or search_with_entity_filter
            entity_slug: Optional entity filter used

        """
        for result in results:
            log_id = str(uuid4())
            self.cks.conn.execute(
                """INSERT INTO recall_log (id, session_id, timestamp, query, entry_id, ranking, entity_slug)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    log_id,
                    session_id,
                    datetime.now(UTC).isoformat(),
                    query,
                    result.get("id"),
                    result.get("final_score") or result.get("similarity"),
                    entity_slug,
                ),
            )

        self.cks.conn.commit()

    def get_recall_history(
        self,
        session_id: str | None = None,
        entity_slug: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get recall history for debugging.

        Args:
            session_id: Optional session filter
            entity_slug: Optional entity filter
            limit: Max results

        Returns:
            List of recall log entries

        """
        query = "SELECT * FROM recall_log"
        params = []

        conditions = []
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        if entity_slug:
            conditions.append("entity_slug = ?")
            params.append(entity_slug)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self.cks.conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "timestamp": row["timestamp"],
                "query": row["query"],
                "entry_id": row["entry_id"],
                "ranking": row["ranking"],
                "entity_slug": row["entity_slug"],
            }
            for row in rows
        ]

    def prune_old_recall_logs(self, days: int = 90) -> None:
        """Prune recall logs older than specified days.

        Args:
            days: Days to retain (default: 90)

        """
        self.cks.conn.execute(
            f"""DELETE FROM recall_log
               WHERE timestamp < datetime('now', '-{days} days')""",
        )
        self.cks.conn.commit()
        print(f"[EntityFilter] Pruned recall logs older than {days} days")


# Convenience function for quick entity-filtered search
def search_entities(query: str, entity: str | None = None, limit: int = 5) -> list[dict]:
    """Quick entity-filtered search.

    Args:
        query: Search query
        entity: Optional entity slug
        limit: Max results

    Returns:
        Search results with entity information

    """
    from .entity_filter import CKSEntityFilter
    from .unified import CKS

    cks = CKS()
    entity_cks = CKSEntityFilter(cks)
    return entity_cks.search_with_entity_filter(query, entity_slug=entity, limit=limit)
