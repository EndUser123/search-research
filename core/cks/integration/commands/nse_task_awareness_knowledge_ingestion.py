#!/usr/bin/env python3
"""NSE Task Awareness Knowledge Integration Script.

Integrates the comprehensive NSE Task Awareness documentation into CKS
with intelligent categorization, relationship mapping, and search optimization.
"""

import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Project paths - navigate to the correct project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data/cks_hypergraph"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# NSE Task Awareness documentation paths
NSE_DOCS_DIR = PROJECT_ROOT / "docs/nse_task_awareness"
NSE_MEMORY_DIR = PROJECT_ROOT / ".speckit/memory/TSK-121720-NSETaskAwareness-1725"

print("🔧 Debug info:")
print(f"   Script dir: {SCRIPT_DIR}")
print(f"   Project root: {PROJECT_ROOT}")
print(f"   Docs dir: {NSE_DOCS_DIR}")
print(f"   Memory dir: {NSE_MEMORY_DIR}")
print(f"   Docs exists: {NSE_DOCS_DIR.exists()}")
print(f"   Memory exists: {NSE_MEMORY_DIR.exists()}")

# Database path
DB_PATH = DATA_DIR / "cks_hypergraph.db"


class NSETaskAwarenessKnowledgeIntegrator:
    """Specialized knowledge integrator for NSE Task Awareness system."""

    def __init__(self) -> None:
        self.conn = None
        self.initialize_database()
        self.knowledge_graph = {}
        self.relationships = []

    def initialize_database(self) -> bool:
        """Initialize CKS database with enhanced schema for NSE knowledge."""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            cursor = self.conn.cursor()

            # Create enhanced knowledge nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    subtype TEXT,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    importance_score REAL DEFAULT 1.0,
                    access_count INTEGER DEFAULT 0
                )
            """)

            # Create knowledge edges table for relationships
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    strength REAL DEFAULT 1.0,
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

            # Create specialized NSE knowledge index table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nse_knowledge_index (
                    id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    keywords TEXT,
                    searchable_content TEXT,
                    last_accessed TIMESTAMP,
                    FOREIGN KEY (node_id) REFERENCES knowledge_nodes (id)
                )
            """)

            self.conn.commit()
            print("✅ CKS database initialized with NSE schema enhancements")
            return True

        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False

    def generate_node_id(self, title: str, category: str) -> str:
        """Generate unique knowledge node ID."""
        content = f"nse_{title}_{category}_{datetime.now().isoformat()}"
        return f"nse_{hashlib.md5(content.encode()).hexdigest()[:16]}"

    def ingest_nse_documentation(self) -> dict[str, Any]:
        """Ingest all NSE Task Awareness documentation."""
        results = {
            "success": True,
            "ingested_files": [],
            "relationships_created": 0,
            "errors": [],
        }

        try:
            # Main documentation files
            main_docs = [
                (
                    "comprehensive_documentation.md",
                    "system_overview",
                    "NSE Task Awareness - Complete System Documentation",
                    1.0,
                ),
                (
                    "README.md",
                    "introduction",
                    "NSE Task Awareness - Introduction and Overview",
                    0.9,
                ),
                ("user_guide.md", "user_guide", "NSE Task Awareness - User Guide", 0.8),
                ("roadmap.md", "planning", "NSE Task Awareness - Development Roadmap", 0.7),
            ]

            # Process main documentation
            for doc_file, category, title, importance in main_docs:
                file_path = NSE_DOCS_DIR / doc_file
                print(f"🔍 Checking main doc: {file_path} - exists: {file_path.exists()}")
                if file_path.exists():
                    result = self._ingest_single_document(
                        file_path,
                        title,
                        category,
                        importance,
                    )
                    if result["success"]:
                        results["ingested_files"].append(result)
                    else:
                        results["errors"].append(f"Failed to ingest {doc_file}: {result['error']}")
                else:
                    results["errors"].append(f"Main doc not found: {doc_file}")

            # Process memory/specification files
            memory_files = [
                (
                    "comprehensive_documentation.md",
                    "implementation",
                    "NSE Task Awareness - Implementation Details",
                    1.0,
                ),
                ("arch.md", "architecture", "NSE Task Awareness - System Architecture", 0.9),
                (
                    "implementation_plan.md",
                    "implementation",
                    "NSE Task Awareness - Implementation Plan",
                    0.8,
                ),
                (
                    "requirements_analysis.md",
                    "requirements",
                    "NSE Task Awareness - Requirements Analysis",
                    0.8,
                ),
                ("research.md", "research", "NSE Task Awareness - Research Findings", 0.7),
                (
                    "cks_integration.md",
                    "integration",
                    "NSE Task Awareness - CKS Integration Strategy",
                    0.9,
                ),
                (
                    "task_decomposition.md",
                    "planning",
                    "NSE Task Awareness - Task Decomposition",
                    0.7,
                ),
                (
                    "quality_gate_validation.md",
                    "quality",
                    "NSE Task Awareness - Quality Gate Validation",
                    0.8,
                ),
                ("results_synthesis.md", "analysis", "NSE Task Awareness - Results Synthesis", 0.7),
                (
                    "learning_patterns_and_best_practices.md",
                    "best_practices",
                    "NSE Task Awareness - Learning Patterns and Best Practices",
                    0.9,
                ),
                (
                    "project_closure_and_final_validation.md",
                    "project_management",
                    "NSE Task Awareness - Project Closure Report",
                    0.7,
                ),
                (
                    "next_step_recommendations.md",
                    "planning",
                    "NSE Task Awareness - Next Step Recommendations",
                    0.8,
                ),
            ]

            # Process memory files
            for mem_file, category, title, importance in memory_files:
                file_path = NSE_MEMORY_DIR / mem_file
                print(f"🔍 Checking memory file: {file_path} - exists: {file_path.exists()}")
                if file_path.exists():
                    result = self._ingest_single_document(
                        file_path,
                        title,
                        category,
                        importance,
                    )
                    if result["success"]:
                        results["ingested_files"].append(result)
                    else:
                        results["errors"].append(f"Failed to ingest {mem_file}: {result['error']}")
                else:
                    results["errors"].append(f"Memory file not found: {mem_file}")

            # Create cross-references and relationships
            self._create_nse_relationships()
            results["relationships_created"] = len(self.relationships)

            print("✅ NSE Task Awareness documentation integration complete")
            print(f"   Files ingested: {len(results['ingested_files'])}")
            print(f"   Relationships created: {results['relationships_created']}")
            print(f"   Errors: {len(results['errors'])}")

            return results

        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Integration failed: {e!s}")
            return results

    def _ingest_single_document(
        self,
        file_path: Path,
        title: str,
        category: str,
        importance: float = 1.0,
    ) -> dict[str, Any]:
        """Ingest a single NSE document."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Generate unique IDs
            node_id = self.generate_node_id(title, category)
            vector_id = f"vector_{node_id}"

            # Extract key information
            summary = self._extract_summary(content)
            key_points = self._extract_key_points(content)
            keywords = self._extract_keywords(content)

            # Prepare enhanced metadata
            metadata = {
                "title": title,
                "category": category,
                "source": "nse_task_awareness",
                "file_path": str(file_path),
                "file_name": file_path.name,
                "ingestion_date": datetime.now().isoformat(),
                "importance_score": importance,
                "summary": summary,
                "key_points": key_points,
                "keywords": keywords,
                "content_length": len(content),
                "project": "TSK-121720-NSETaskAwareness-1725",
                "version": "1.0.0",
            }

            # Store structured content
            structured_content = json.dumps(
                {
                    "title": title,
                    "content": content,
                    "summary": summary,
                    "key_points": key_points,
                    "keywords": keywords,
                    "metadata": metadata,
                },
                indent=2,
            )

            # Insert knowledge node
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_nodes (id, type, subtype, content, metadata, importance_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    node_id,
                    "nse_knowledge",
                    category,
                    structured_content,
                    json.dumps(metadata),
                    importance,
                ),
            )

            # Create vector node for semantic search
            searchable_content = f"{title} {summary} {' '.join(keywords)} {' '.join(key_points)}"
            cursor.execute(
                """
                INSERT INTO vector_nodes (id, content, vector_id, model_name, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    vector_id,
                    searchable_content,
                    vector_id,
                    "nse_semantic_search",
                    json.dumps(
                        {
                            "source_node_id": node_id,
                            "category": category,
                            "importance": importance,
                        }
                    ),
                ),
            )

            # Create specialized NSE index entry
            cursor.execute(
                """
                INSERT INTO nse_knowledge_index (id, node_id, category, keywords, searchable_content)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    f"index_{node_id}",
                    node_id,
                    category,
                    json.dumps(keywords),
                    searchable_content,
                ),
            )

            self.conn.commit()

            # Track for relationship creation
            self.knowledge_graph[node_id] = {
                "title": title,
                "category": category,
                "keywords": keywords,
                "importance": importance,
            }

            print(f"✅ Ingested: {title} ({category})")
            return {
                "success": True,
                "node_id": node_id,
                "vector_id": vector_id,
                "title": title,
                "category": category,
                "importance": importance,
            }

        except Exception as e:
            print(f"❌ Failed to ingest {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "title": title,
            }

    def _extract_summary(self, content: str) -> str:
        """Extract comprehensive summary from content."""
        lines = content.split("\n")
        summary_parts = []

        # Look for key sections
        in_summary = False
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()

            # Stop at major sections after finding summary
            if line.startswith("# ") and summary_parts:
                if any(
                    keyword in line.lower()
                    for keyword in ["architecture", "implementation", "user guide", "api"]
                ):
                    break

            # Look for explicit summaries
            if any(
                keyword in line.lower() for keyword in ["what is", "overview", "summary", "purpose"]
            ):
                in_summary = True

            if in_summary and line:
                summary_parts.append(line)
                if len(summary_parts) >= 5:  # Limit summary length
                    break

        if not summary_parts:
            # Fallback: use first paragraph
            for line in lines:
                if line.strip() and not line.startswith("#"):
                    summary_parts.append(line.strip())
                    break

        return " ".join(summary_parts[:3])  # Return first 3 summary sentences

    def _extract_key_points(self, content: str) -> list[str]:
        """Extract key points from NSE documentation."""
        key_points = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()

            # Look for bullet points, numbered lists, and key phrases
            if line.startswith(("-", "*", "#", "##")) or any(
                keyword in line.lower()
                for keyword in [
                    "key",
                    "important",
                    "critical",
                    "essential",
                    "benefit",
                    "capability",
                    "feature",
                    "component",
                    "integration",
                ]
            ):
                # Clean up the line
                if line.startswith(("-", "*")):
                    line = line[1:].strip()
                if line.startswith("#"):
                    line = line.lstrip("#").strip()

                if len(line) > 10 and len(line) < 200:  # Reasonable length
                    key_points.append(line)
                    if len(key_points) >= 15:  # Limit to 15 key points
                        break

        return key_points

    def _extract_keywords(self, content: str) -> list[str]:
        """Extract NSE-specific keywords from content."""
        # NSE Task Awareness specific keywords
        nse_keywords = [
            "nse",
            "next step engine",
            "task awareness",
            "taskmaster",
            "todowrite",
            "quality assessment",
            "decision engine",
            "adapter pattern",
            "task context",
            "intelligent recommendations",
            "move_on",
            "continue_polishing",
            "finalize_current",
            "csf",
            "slash command",
            "task management",
            "completion percentage",
            "quality gates",
            "context integration",
            "performance optimization",
            "backward compatibility",
            "graceful degradation",
            "feature flags",
        ]

        # Technical keywords
        tech_keywords = [
            "architecture",
            "implementation",
            "api",
            "integration",
            "configuration",
            "troubleshooting",
            "performance",
            "migration",
            "database",
            "vector",
            "semantic search",
            "knowledge graph",
            "relationships",
            "metadata",
        ]

        content_lower = content.lower()
        found_keywords = []

        # Check for NSE-specific keywords
        for keyword in nse_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)

        # Check for technical keywords
        for keyword in tech_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)

        # Add document-specific keywords based on content
        if "architecture" in content_lower:
            found_keywords.extend(["system design", "components", "patterns"])
        if "user guide" in content_lower:
            found_keywords.extend(["tutorial", "getting started", "examples"])
        if "implementation" in content_lower:
            found_keywords.extend(["code", "development", "best practices"])

        return list(set(found_keywords))

    def _create_nse_relationships(self) -> None:
        """Create intelligent relationships between NSE knowledge nodes."""
        cursor = self.conn.cursor()

        # Define relationship patterns
        relationship_patterns = {
            ("system_overview", "architecture"): "has_architecture",
            ("system_overview", "user_guide"): "has_user_guide",
            ("system_overview", "implementation"): "has_implementation",
            ("architecture", "implementation"): "implements",
            ("implementation", "user_guide"): "documented_in",
            ("requirements", "architecture"): "informs",
            ("requirements", "implementation"): "drives",
            ("research", "requirements"): "informs",
            ("research", "implementation"): "supports",
            ("quality", "implementation"): "validates",
            ("best_practices", "implementation"): "guides",
            ("planning", "implementation"): "plans",
            ("integration", "implementation"): "enables",
        }

        # Create relationships based on patterns
        for node_id, node_data in self.knowledge_graph.items():
            for other_id, other_data in self.knowledge_graph.items():
                if node_id == other_id:
                    continue

                # Check for defined patterns
                category_pair = (node_data["category"], other_data["category"])
                if category_pair in relationship_patterns:
                    relationship = relationship_patterns[category_pair]
                    strength = self._calculate_relationship_strength(node_data, other_data)

                    rel_id = f"rel_{node_id}_{other_id}"
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO knowledge_edges
                        (id, source_id, target_id, relationship, strength, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            rel_id,
                            node_id,
                            other_id,
                            relationship,
                            strength,
                            json.dumps(
                                {
                                    "created_by": "nse_integrator",
                                    "confidence": strength,
                                    "pattern_match": True,
                                }
                            ),
                        ),
                    )
                    self.relationships.append(rel_id)

                # Create keyword-based relationships
                shared_keywords = set(node_data["keywords"]) & set(other_data["keywords"])
                if len(shared_keywords) >= 3:  # Significant keyword overlap
                    relationship = "related_by_keywords"
                    strength = min(len(shared_keywords) / 10.0, 1.0)

                    rel_id = f"rel_kw_{node_id}_{other_id}"
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO knowledge_edges
                        (id, source_id, target_id, relationship, strength, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            rel_id,
                            node_id,
                            other_id,
                            relationship,
                            strength,
                            json.dumps(
                                {
                                    "shared_keywords": list(shared_keywords),
                                    "keyword_count": len(shared_keywords),
                                }
                            ),
                        ),
                    )
                    self.relationships.append(rel_id)

        self.conn.commit()

    def _calculate_relationship_strength(self, node1: dict, node2: dict) -> float:
        """Calculate relationship strength between two nodes."""
        # Base strength from importance scores
        base_strength = (node1["importance"] + node2["importance"]) / 2.0

        # Boost for shared keywords
        shared_keywords = set(node1["keywords"]) & set(node2["keywords"])
        keyword_boost = len(shared_keywords) * 0.1

        # Category relevance boost
        category_boost = 0.0
        high_relevance_categories = ["system_overview", "architecture", "implementation"]
        if (
            node1["category"] in high_relevance_categories
            and node2["category"] in high_relevance_categories
        ):
            category_boost = 0.2

        total_strength = base_strength + keyword_boost + category_boost
        return min(total_strength, 1.0)  # Cap at 1.0

    def search_nse_knowledge(self, query: str, limit: int = 10) -> list[dict]:
        """Search NSE knowledge with semantic and keyword matching."""
        try:
            cursor = self.conn.cursor()
            query_lower = query.lower()

            # Search in NSE index for best results
            cursor.execute(
                """
                SELECT kn.id, kn.type, kn.subtype, kn.content, kn.metadata, kn.importance_score,
                       nki.keywords, nki.searchable_content
                FROM knowledge_nodes kn
                JOIN nse_knowledge_index nki ON kn.id = nki.node_id
                WHERE kn.type = 'nse_knowledge'
                AND (
                    nki.searchable_content LIKE ?
                    OR nki.keywords LIKE ?
                    OR kn.metadata LIKE ?
                )
                ORDER BY kn.importance_score DESC, kn.created_at DESC
                LIMIT ?
            """,
                (f"%{query_lower}%", f"%{query_lower}%", f"%{query_lower}%", limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "id": row[0],
                        "type": row[1],
                        "subtype": row[2],
                        "content": json.loads(row[3]) if row[3].startswith("{") else row[3],
                        "metadata": json.loads(row[4]) if row[4].startswith("{") else row[4],
                        "importance": row[5],
                        "keywords": json.loads(row[6]) if row[6] else [],
                        "relevance_score": self._calculate_relevance(query_lower, row),
                    }
                )

            # Sort by relevance
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results

        except Exception as e:
            print(f"❌ NSE knowledge search failed: {e}")
            return []

    def _calculate_relevance(self, query: str, row_data) -> float:
        """Calculate relevance score for search results."""
        relevance = 0.0

        # Query term matching in keywords
        keywords = json.loads(row_data[6]) if row_data[6] and row_data[6].startswith("[") else []
        for keyword in keywords:
            if keyword.lower() in query:
                relevance += 0.3

        # Content matching
        content = row_data[7] if row_data[7] else ""
        query_terms = query.split()
        for term in query_terms:
            if term.lower() in content.lower():
                relevance += 0.2

        # Importance boost
        relevance += row_data[5] * 0.1

        return min(relevance, 1.0)

    def get_nse_statistics(self) -> dict:
        """Get comprehensive NSE knowledge statistics."""
        try:
            cursor = self.conn.cursor()
            stats = {}

            # Node counts by category
            cursor.execute("""
                SELECT subtype, COUNT(*)
                FROM knowledge_nodes
                WHERE type = 'nse_knowledge'
                GROUP BY subtype
            """)
            stats["nodes_by_category"] = dict(cursor.fetchall())

            # Total NSE knowledge
            cursor.execute("SELECT COUNT(*) FROM knowledge_nodes WHERE type = 'nse_knowledge'")
            stats["total_nse_nodes"] = cursor.fetchone()[0]

            # Relationship counts
            cursor.execute("""
                SELECT COUNT(*) FROM knowledge_edges ke
                JOIN knowledge_nodes kn ON ke.source_id = kn.id
                WHERE kn.type = 'nse_knowledge'
            """)
            stats["total_nse_relationships"] = cursor.fetchone()[0]

            # Most important nodes
            cursor.execute("""
                SELECT metadata, importance_score
                FROM knowledge_nodes
                WHERE type = 'nse_knowledge'
                ORDER BY importance_score DESC
                LIMIT 5
            """)
            stats["top_nodes"] = [
                {
                    "title": json.loads(row[0])["title"],
                    "importance": row[1],
                }
                for row in cursor.fetchall()
            ]

            return stats

        except Exception as e:
            print(f"❌ Failed to get NSE statistics: {e}")
            return {}

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main() -> None:
    """Main CLI interface for NSE Task Awareness knowledge integration."""
    import argparse

    parser = argparse.ArgumentParser(description="NSE Task Awareness Knowledge Integration")
    parser.add_argument("--ingest", action="store_true", help="Ingest NSE documentation")
    parser.add_argument("--search", help="Search NSE knowledge base")
    parser.add_argument("--stats", action="store_true", help="Show NSE knowledge statistics")
    parser.add_argument("--limit", type=int, default=10, help="Search result limit")

    args = parser.parse_args()

    integrator = NSETaskAwarenessKnowledgeIntegrator()

    try:
        if args.ingest:
            print("🚀 Starting NSE Task Awareness knowledge integration...")
            result = integrator.ingest_nse_documentation()

            if result["success"]:
                print("\n✅ Integration completed successfully!")
                print(f"   Files processed: {len(result['ingested_files'])}")
                print(f"   Relationships created: {result['relationships_created']}")
                if result["errors"]:
                    print(f"   Warnings: {len(result['errors'])}")
            else:
                print(f"\n❌ Integration failed with {len(result['errors'])} errors")
                for error in result["errors"]:
                    print(f"   - {error}")

        elif args.search:
            results = integrator.search_nse_knowledge(args.search, args.limit)
            print(f"\n🔍 NSE Knowledge Search Results for '{args.search}':")

            if not results:
                print("   No results found.")
            else:
                for i, result in enumerate(results, 1):
                    metadata = result["metadata"]
                    print(f"\n{i}. {metadata.get('title', 'Untitled')}")
                    print(f"   Category: {metadata.get('category', 'N/A')}")
                    print(f"   Type: {result['subtype']}")
                    print(f"   Importance: {result['importance']:.2f}")
                    print(f"   Relevance: {result['relevance_score']:.2f}")

                    summary = metadata.get("summary", "")
                    if summary:
                        print(f"   Summary: {summary[:150]}{'...' if len(summary) > 150 else ''}")

        elif args.stats:
            stats = integrator.get_nse_statistics()
            print("\n📊 NSE Task Awareness Knowledge Statistics:")
            print(json.dumps(stats, indent=2))

        else:
            print("Please specify an action: --ingest, --search, or --stats")
            parser.print_help()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        integrator.close()


if __name__ == "__main__":
    main()
