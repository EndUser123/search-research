#!/usr/bin/env python3
"""Direct CKS Knowledge Ingestion Script.

This script directly ingests knowledge into the CKS database without requiring
complex module dependencies or initialization.
"""

import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data/cks_hypergraph"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database path
DB_PATH = DATA_DIR / "cks_hypergraph.db"


class DirectCKSIngestion:
    """Direct knowledge ingestion into CKS database."""

    def __init__(self) -> None:
        self.conn = None
        self.initialize_database()

    def initialize_database(self) -> bool:
        """Initialize CKS database if it doesn't exist."""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            cursor = self.conn.cursor()

            # Create knowledge nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create knowledge edges table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create vector nodes table for semantic search
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_nodes (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    vector_id TEXT UNIQUE,
                    model_name TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.conn.commit()
            print("✅ CKS database initialized")
            return True

        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False

    def generate_entry_id(self, title: str, category: str) -> str:
        """Generate unique entry ID."""
        content = f"{title}_{category}_{datetime.now().isoformat()}"
        return f"entry_{hashlib.md5(content.encode()).hexdigest()[:16]}"

    def ingest_knowledge(
        self,
        title: str,
        content: str,
        category: str,
        knowledge_type: str = "implementation",
        metadata: dict[str, Any] | None = None,
        tags: list | None = None,
    ) -> dict[str, Any]:
        """Ingest knowledge entry into CKS."""
        try:
            cursor = self.conn.cursor()

            # Generate unique ID
            entry_id = self.generate_entry_id(title, category)

            # Prepare metadata
            entry_metadata = {
                "title": title,
                "category": category,
                "source": "session_learning",
                "ingestion_date": datetime.now().isoformat(),
                "knowledge_type": knowledge_type,
                "tags": tags or [],
                **(metadata or {}),
            }

            # Store structured content
            structured_content = json.dumps(
                {
                    "title": title,
                    "content": content,
                    "summary": self._generate_summary(content),
                    "key_points": self._extract_key_points(content),
                }
            )

            # Insert knowledge node
            cursor.execute(
                """
                INSERT INTO knowledge_nodes (id, type, content, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    entry_id,
                    knowledge_type,
                    structured_content,
                    json.dumps(entry_metadata),
                ),
            )

            # Create vector node for semantic search
            vector_id = f"vector_{entry_id}"
            vector_content = f"{title} {content} {' '.join(tags or [])}"

            cursor.execute(
                """
                INSERT INTO vector_nodes (id, content, vector_id, model_name, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    vector_id,
                    vector_content,
                    vector_id,
                    "semantic_search_ready",
                    json.dumps({"source_entry_id": entry_id, "category": category}),
                ),
            )

            # Create relationships if there are tags
            self._create_tag_relationships(cursor, entry_id, tags or [])

            self.conn.commit()

            print(f"✅ Successfully ingested knowledge: {title}")
            print(f"   Entry ID: {entry_id}")
            print(f"   Category: {category}")
            print(f"   Tags: {tags or []}")

            return {
                "success": True,
                "entry_id": entry_id,
                "vector_id": vector_id,
                "title": title,
                "category": category,
                "message": f"Knowledge '{title}' successfully ingested into CKS",
            }

        except Exception as e:
            print(f"❌ Failed to ingest knowledge: {e}")
            return {
                "success": False,
                "error": str(e),
                "title": title,
            }

    def _generate_summary(self, content: str) -> str:
        """Generate a summary of the content."""
        # Simple heuristic: first few sentences
        sentences = content.split(". ")
        summary = ". ".join(sentences[:3])
        if len(summary) > 500:
            summary = summary[:497] + "..."
        return summary

    def _extract_key_points(self, content: str) -> list:
        """Extract key points from content."""
        key_points = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            # Look for bullet points, numbered lists, or key phrases
            if line.startswith(("-", "*", "#", "##")) or any(
                keyword in line.lower() for keyword in ["key", "important", "critical", "essential"]
            ):
                key_points.append(line)
                if len(key_points) >= 10:  # Limit to 10 key points
                    break

        return key_points

    def _create_tag_relationships(self, cursor, entry_id: str, tags: list) -> None:
        """Create relationships between entry and tags."""
        for tag in tags[:5]:  # Limit to 5 relationships to avoid clutter
            tag_id = f"tag_{tag.lower().replace(' ', '_').replace('-', '_')}"

            # Create tag node if it doesn't exist
            cursor.execute(
                """
                INSERT OR IGNORE INTO knowledge_nodes (id, type, content, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    tag_id,
                    "tag",
                    json.dumps({"name": tag, "type": "category_tag"}),
                    json.dumps({"tag_type": "category", "created_for": entry_id}),
                ),
            )

            # Create relationship
            relationship_id = f"rel_{entry_id}_{tag_id}"
            cursor.execute(
                """
                INSERT OR IGNORE INTO knowledge_edges (id, source_id, target_id, relationship, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    relationship_id,
                    entry_id,
                    tag_id,
                    "tagged_with",
                    json.dumps({"tag": tag, "relationship_strength": 0.9}),
                ),
            )

    def search_knowledge(self, query: str, limit: int = 5) -> list:
        """Search for knowledge entries."""
        try:
            cursor = self.conn.cursor()

            # Simple text search in content and metadata
            cursor.execute(
                """
                SELECT id, type, content, metadata, created_at
                FROM knowledge_nodes
                WHERE content LIKE ? OR metadata LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "id": row[0],
                        "type": row[1],
                        "content": json.loads(row[2]) if row[2].startswith("{") else row[2],
                        "metadata": json.loads(row[3]) if row[3].startswith("{") else row[3],
                        "created_at": row[4],
                    }
                )

            return results

        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []

    def get_statistics(self) -> dict:
        """Get CKS statistics."""
        try:
            cursor = self.conn.cursor()

            stats = {}

            # Count nodes by type
            cursor.execute("SELECT type, COUNT(*) FROM knowledge_nodes GROUP BY type")
            stats["nodes_by_type"] = dict(cursor.fetchall())

            # Total counts
            cursor.execute("SELECT COUNT(*) FROM knowledge_nodes")
            stats["total_knowledge_nodes"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vector_nodes")
            stats["total_vector_nodes"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM knowledge_edges")
            stats["total_relationships"] = cursor.fetchone()[0]

            return stats

        except Exception as e:
            print(f"❌ Failed to get statistics: {e}")
            return {}

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main() -> None:
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Direct CKS Knowledge Ingestion")
    parser.add_argument("--file", help="File containing knowledge to ingest")
    parser.add_argument("--title", help="Knowledge entry title")
    parser.add_argument("--category", help="Knowledge category")
    parser.add_argument("--type", default="implementation", help="Knowledge type")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--search", help="Search knowledge base")
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    ingestion = DirectCKSIngestion()

    try:
        if args.stats:
            stats = ingestion.get_statistics()
            print("\n📊 CKS Statistics:")
            print(json.dumps(stats, indent=2))

        elif args.search:
            results = ingestion.search_knowledge(args.search)
            print(f"\n🔍 Search results for '{args.search}':")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['metadata'].get('title', result['id'])}")
                print(f"   Type: {result['type']}")
                print(f"   Category: {result['metadata'].get('category', 'N/A')}")
                print(f"   Created: {result['created_at']}")

        elif args.file:
            # Read knowledge from file
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {args.file}")
                sys.exit(1)

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Extract title from content or use argument
            title = args.title
            if not title:
                # Look for title in content
                for line in content.split("\n")[:10]:
                    if line.strip().startswith("# "):
                        title = line.strip()[2:]
                        break
                if not title:
                    title = file_path.stem

            # Parse tags
            tags = []
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(",")]

            # Ingest knowledge
            result = ingestion.ingest_knowledge(
                title=title,
                content=content,
                category=args.category or "general",
                knowledge_type=args.type,
                tags=tags,
            )

            if result["success"]:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Failed to ingest knowledge: {result['error']}")
                sys.exit(1)

        else:
            print("Please specify an action: --file, --search, or --stats")
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        ingestion.close()


if __name__ == "__main__":
    main()
