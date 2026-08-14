import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""
CKS Hyper-Graph Query Interface

Provides intelligent querying capabilities across the hyper-graph system,
demonstrating semantic search, cross-graph relationships, and knowledge reasoning.
"""


# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data/cks.db"


class CKSQueryInterface:
    """Query interface for CKS hyper-graph system."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        """Initialize query interface."""
        self.db_path = db_path
        self.conn = None

    def connect(self) -> bool:
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def search_knowledge_graph(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search the knowledge graph for matching concepts."""
        cursor = self.conn.cursor()

        # Simple text-based search (in production, would use vector embeddings)
        cursor.execute(
            """
            SELECT id, type, content, metadata, created_at
            FROM knowledge_nodes
            WHERE content LIKE ? OR type LIKE ?
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
                    "content": json.loads(row[2]),
                    "metadata": json.loads(row[3]) if row[3] else {},
                    "created_at": row[4],
                    "graph_type": "knowledge",
                },
            )

        return results

    def search_vector_nodes(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search vector nodes for semantic matches."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT id, content, vector_id, model_name, metadata
            FROM vector_nodes
            WHERE content LIKE ?
            LIMIT ?
        """,
            (f"%{query}%", limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row[0],
                    "content": row[1],
                    "vector_id": row[2],
                    "model_name": row[3],
                    "metadata": json.loads(row[4]) if row[4] else {},
                    "graph_type": "vector",
                },
            )

        return results

    def find_cross_graph_relationships(
        self,
        entity_id: str,
        source_graph: str,
    ) -> list[dict[str, Any]]:
        """Find relationships between graph types."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT id, source_graph, source_id, target_graph, target_id,
                   relationship_type, confidence, strength, metadata
            FROM cross_graph_relationships
            WHERE source_id = ? AND source_graph = ?
            UNION
            SELECT id, source_graph, source_id, target_graph, target_id,
                   relationship_type, confidence, strength, metadata
            FROM cross_graph_relationships
            WHERE target_id = ? AND target_graph = ?
        """,
            (entity_id, source_graph, entity_id, source_graph),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row[0],
                    "source_graph": row[1],
                    "source_id": row[2],
                    "target_graph": row[3],
                    "target_id": row[4],
                    "relationship_type": row[5],
                    "confidence": row[6],
                    "strength": row[7],
                    "metadata": json.loads(row[8]) if row[8] else {},
                },
            )

        return results

    def get_tdd_repositories(self) -> list[dict[str, Any]]:
        """Get all TDD enforcement repositories."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT id, type, name, content, attributes, created_at
            FROM social_nodes
            WHERE type = 'repository'
        """,
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row[0],
                    "type": row[1],
                    "name": row[2],
                    "content": json.loads(row[3]),
                    "attributes": json.loads(row[4]) if row[4] else {},
                    "created_at": row[5],
                },
            )

        return results

    def get_architecture_patterns(self) -> list[dict[str, Any]]:
        """Get all architecture patterns from research."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT id, type, content, metadata, created_at
            FROM knowledge_nodes
            WHERE type = 'architecture_pattern'
        """,
        )

        results = []
        for row in cursor.fetchall():
            content = json.loads(row[2])
            results.append(
                {
                    "id": row[0],
                    "type": row[1],
                    "name": content.get("name", ""),
                    "definition": content.get("definition", ""),
                    "category": content.get("category", ""),
                    "metadata": json.loads(row[3]) if row[3] else {},
                    "created_at": row[4],
                },
            )

        return results

    def semantic_search_across_graphs(
        self,
        query: str,
        limit: int = 20,
    ) -> dict[str, list[dict[str, Any]]]:
        """Perform semantic search across all graph types."""
        results = {
            "knowledge": self.search_knowledge_graph(query, limit // 4),
            "vector": self.search_vector_nodes(query, limit // 4),
            "social": [],
            "system": [],
        }

        # Search social nodes
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, type, name, content, attributes
            FROM social_nodes
            WHERE name LIKE ? OR content LIKE ?
            LIMIT ?
        """,
            (f"%{query}%", f"%{query}%", limit // 4),
        )

        for row in cursor.fetchall():
            results["social"].append(
                {
                    "id": row[0],
                    "type": row[1],
                    "name": row[2],
                    "content": json.loads(row[3]),
                    "attributes": json.loads(row[4]) if row[4] else {},
                },
            )

        # Search system nodes
        cursor.execute(
            """
            SELECT id, type, name, content, status
            FROM system_nodes
            WHERE name LIKE ? OR content LIKE ?
            LIMIT ?
        """,
            (f"%{query}%", f"%{query}%", limit // 4),
        )

        for row in cursor.fetchall():
            results["system"].append(
                {
                    "id": row[0],
                    "type": row[1],
                    "name": row[2],
                    "content": json.loads(row[3]),
                    "status": row[4],
                },
            )

        return results

    def get_entity_insights(self, entity_id: str, graph_type: str) -> dict[str, Any]:
        """Get comprehensive insights about an entity across all graphs."""
        insights = {
            "entity_id": entity_id,
            "source_graph": graph_type,
            "cross_graph_relationships": [],
            "related_entities": {},
            "graph_insights": {},
        }

        # Get cross-graph relationships
        relationships = self.find_cross_graph_relationships(entity_id, graph_type)
        insights["cross_graph_relationships"] = relationships

        # Get related entities
        for rel in relationships:
            target_graph = rel["target_graph"]
            target_id = rel["target_id"]

            if target_graph not in insights["related_entities"]:
                insights["related_entities"][target_graph] = []

            # Get entity details
            if target_graph == "knowledge":
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT type, content, metadata FROM knowledge_nodes WHERE id = ?",
                    (target_id,),
                )
                row = cursor.fetchone()
                if row:
                    insights["related_entities"][target_graph].append(
                        {
                            "id": target_id,
                            "type": row[0],
                            "content": json.loads(row[1]),
                            "metadata": json.loads(row[2]) if row[2] else {},
                        },
                    )

            elif target_graph == "social":
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT type, name, content FROM social_nodes WHERE id = ?",
                    (target_id,),
                )
                row = cursor.fetchone()
                if row:
                    insights["related_entities"][target_graph].append(
                        {
                            "id": target_id,
                            "type": row[0],
                            "name": row[1],
                            "content": json.loads(row[2]),
                        },
                    )

        return insights

    def get_system_statistics(self) -> dict[str, Any]:
        """Get comprehensive system statistics."""
        cursor = self.conn.cursor()
        stats = {}

        # Node counts
        for table in [
            "knowledge_nodes",
            "vector_nodes",
            "causal_nodes",
            "social_nodes",
            "system_nodes",
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]

        # Edge counts
        for table in [
            "knowledge_edges",
            "vector_embeddings",
            "causal_edges",
            "social_edges",
            "system_edges",
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]

        # Cross-graph relationships
        cursor.execute("SELECT COUNT(*) FROM cross_graph_relationships")
        stats["cross_graph_relationships_count"] = cursor.fetchone()[0]

        # Relationship type distribution
        cursor.execute(
            """
            SELECT relationship_type, COUNT(*)
            FROM cross_graph_relationships
            GROUP BY relationship_type
        """,
        )
        stats["relationship_types"] = dict(cursor.fetchall())

        return stats

    def interactive_query(self) -> None:
        """Interactive query interface."""
        print("\n" + "=" * 60)
        print("CKS HYPER-GRAPH QUERY INTERFACE")
        print("=" * 60)
        print("\nAvailable commands:")
        print("  search <query>          - Search across all graphs")
        print("  tdd                     - List TDD repositories")
        print("  patterns                - List architecture patterns")
        print("  insights <entity_id>    - Get entity insights")
        print("  stats                   - Show system statistics")
        print("  quit                    - Exit interface")
        print("-" * 60)

        while True:
            try:
                command = input("\nCKS> ").strip()

                if command.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break

                if command.lower() == "tdd":
                    print("\n📚 TDD Enforcement Repositories:")
                    repos = self.get_tdd_repositories()
                    for repo in repos:
                        print(f"\n  • {repo['name']}")
                        print(f"    URL: {repo['attributes'].get('url', 'N/A')}")
                        print(
                            f"    Description: {repo['content'].get('description', 'N/A')}",
                        )

                elif command.lower() == "patterns":
                    print("\n🏗️ Architecture Patterns:")
                    patterns = self.get_architecture_patterns()
                    for pattern in patterns:
                        print(f"\n  • {pattern['name']}")
                        print(f"    Definition: {pattern['definition'][:200]}...")

                elif command.lower() == "stats":
                    print("\n📊 System Statistics:")
                    stats = self.get_system_statistics()
                    for key, value in stats.items():
                        if isinstance(value, dict):
                            print(f"\n  {key.replace('_', ' ').title()}:")
                            for k, v in value.items():
                                print(f"    - {k}: {v}")
                        else:
                            print(f"  {key}: {value}")

                elif command.startswith("search "):
                    query = command[7:]
                    print(f"\n🔍 Searching for: '{query}'")
                    results = self.semantic_search_across_graphs(query)

                    total_results = sum(len(r) for r in results.values())
                    print(f"\nFound {total_results} results:")

                    for graph_type, items in results.items():
                        if items:
                            print(
                                f"\n  {graph_type.title()} Graph ({len(items)} results):",
                            )
                            for item in items[:3]:  # Show top 3
                                if graph_type == "knowledge":
                                    name = json.loads(item["content"]).get(
                                        "name",
                                        item["id"],
                                    )
                                elif graph_type == "social":
                                    name = item.get("name", item["id"])
                                else:
                                    name = item.get("name", item["id"])
                                print(f"    • {name}")

                elif command.startswith("insights "):
                    entity_id = command[9:]
                    print(f"\n💡 Insights for entity: {entity_id}")

                    # Try to find the entity first
                    cursor = self.conn.cursor()
                    found = False

                    for table, graph in [
                        ("knowledge_nodes", "knowledge"),
                        ("social_nodes", "social"),
                        ("system_nodes", "system"),
                    ]:
                        cursor.execute(
                            f"SELECT id FROM {table} WHERE id LIKE ?",
                            (f"%{entity_id}%",),
                        )
                        rows = cursor.fetchall()
                        for row in rows:
                            insights = self.get_entity_insights(row[0], graph)
                            print(f"\n  Found in {graph} graph:")
                            print(
                                f"    Relationships: {len(insights['cross_graph_relationships'])}",
                            )
                            for rel in insights["cross_graph_relationships"]:
                                print(
                                    f"    • {rel['relationship_type']} -> {rel['target_graph']} (confidence: {rel['confidence']})",
                                )
                            found = True

                    if not found:
                        print(f"  Entity '{entity_id}' not found")

                else:
                    print("❌ Unknown command. Type 'quit' to exit.")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main() -> None:
    """Main entry point for query interface."""
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Demo mode with sample queries
        interface = CKSQueryInterface()
        if interface.connect():
            print("🎬 Running CKS Hyper-Graph Demo...\n")

            # Demo 1: Search for TDD
            print("1. Searching for 'TDD' across all graphs:")
            results = interface.semantic_search_across_graphs("TDD", limit=10)
            total = sum(len(r) for r in results.values())
            print(
                f"   Found {total} results across {len([k for k, v in results.items() if v])} graph types\n",
            )

            # Demo 2: Get architecture patterns
            print("2. Architecture patterns found:")
            patterns = interface.get_architecture_patterns()
            print(f"   Found {len(patterns)} patterns:")
            for p in patterns[:3]:
                print(f"   • {p['name']}")

            # Demo 3: System statistics
            print("\n3. System statistics:")
            stats = interface.get_system_statistics()
            print(f"   Knowledge nodes: {stats['knowledge_nodes_count']}")
            print(f"   Vector nodes: {stats['vector_nodes_count']}")
            print(
                f"   Cross-graph relationships: {stats['cross_graph_relationships_count']}",
            )

            interface.close()
        else:
            print("❌ Failed to connect to database")

    else:
        # Interactive mode
        interface = CKSQueryInterface()
        if interface.connect():
            interface.interactive_query()
            interface.close()
        else:
            print("❌ Failed to connect to database")
            sys.exit(1)


if __name__ == "__main__":
    main()
