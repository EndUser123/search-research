"""Domain constraint backend for CKS-backed constraint surfacing.

Searches CKS entries filtered by domain_tags column for proactive
constraint surfacing. Unlike CKSMetadataBackend (exact metadata match),
this backend matches domain keywords against the domain_tags TEXT column
using LIKE queries.

Backend name: DOMAIN_CONSTRAINT
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ...config import config

# Backend name constant (matches backend registration name)
BACKEND_DOMAIN_CONSTRAINT = "DOMAIN_CONSTRAINT"


class DomainConstraintBackend:
    """Searches CKS for domain-matched constraint entries.

    Provides proactive surfacing of constraint knowledge based on
    detected query domain. Entries with matching domain_tags are
    returned as high-priority advisory results.

    This backend is queried after domain detection identifies relevant
    domains. Results are injected into the search pipeline before
    result fusion as a separate high-priority band.

    Examples:
        >>> backend = DomainConstraintBackend()
        >>> results = backend.search(["hook", "plugin"], limit=5)
        >>> # Returns constraint entries tagged with hook and/or plugin domains
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize domain constraint backend.

        Args:
            db_path: Path to CKS database (default: from config.CKS_DB_PATH)
        """
        if db_path is None:
            db_path = config.CKS_DB_PATH
        self.db_path = Path(db_path)

    def search(
        self,
        domains: list[str],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search CKS for entries matching any of the given domain tags.

        Args:
            domains: List of domain names to match (e.g. ["hook", "plugin"])
            limit: Maximum results to return (default 5)

        Returns:
            List of constraint entry dicts with source, score, content, domains
        """
        if not self.db_path.exists():
            return []

        if not domains:
            return []

        results: list[dict[str, Any]] = []

        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build OR query for domain_tags LIKE %domain%
            # e.g. domain_tags LIKE %hook% OR domain_tags LIKE %plugin%
            or_conditions = " OR ".join(["domain_tags LIKE ?"] * len(domains))
            sql = f"""
                SELECT id, type, title, content, metadata, domain_tags, created_at
                FROM entries
                WHERE domain_tags IS NOT NULL
                  AND domain_tags != ''
                  AND ({or_conditions})
                ORDER BY created_at DESC
                LIMIT ?
            """
            params = [f"%{d}%" for d in domains] + [limit]

            cursor.execute(sql, params)

            for row in cursor.fetchall():
                # Parse metadata JSON
                metadata: dict[str, Any] = {}
                if row["metadata"]:
                    try:
                        metadata = json.loads(row["metadata"])
                    except json.JSONDecodeError:
                        pass

                result: dict[str, Any] = {
                    "source": BACKEND_DOMAIN_CONSTRAINT,
                    "backend": BACKEND_DOMAIN_CONSTRAINT,
                    "reason": f"Domain constraint matching: {domains}",
                    "type": "constraint",
                    "id": row["id"],
                    "title": row["title"] or "Domain Constraint",
                    "content": row["content"],
                    "score": 0.95,  # High fixed score — constraints are priority
                    "domains": domains,
                    "entry_type": row["type"],
                    "metadata": metadata,
                }

                results.append(result)

            conn.close()

        except sqlite3.Error:
            pass

        return results


def create_domain_constraint_backend(
    db_path: str | None = None,
) -> DomainConstraintBackend:
    """Factory function to create a DomainConstraintBackend instance.

    Args:
        db_path: Path to CKS database (default: from config.CKS_DB_PATH)

    Returns:
        DomainConstraintBackend instance
    """
    return DomainConstraintBackend(db_path=db_path)
