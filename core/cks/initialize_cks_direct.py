import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""
Direct CKS Hyper-Graph Initialization Script

This script initializes the CKS system with all existing content
without requiring complex module imports.
"""


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data/cks_hypergraph"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database path
DB_PATH = DATA_DIR / "cks_hypergraph.db"

print("🚀 Initializing CKS Hyper-Graph System...")
print(f"Data directory: {DATA_DIR}")
print(f"Database path: {DB_PATH}")


class CKSDirectInitializer:
    """Direct CKS initialization without complex dependencies."""

    def __init__(self) -> None:
        self.conn = None
        self.data_sources = {
            "tdd": PROJECT_ROOT
            / "src/features/modules/knowledge_system/claude_code_hooks_tdd_data.json",
            "multi_agent": PROJECT_ROOT
            / "docs/claude_multi_agent_architecture_research_summary.md",
            "memory_bank": PROJECT_ROOT / "knowledge/memory_bank/research",
        }

    def initialize_database(self) -> bool:
        """Initialize SQLite database with all required tables."""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            cursor = self.conn.cursor()

            # Create tables for each graph type
            self._create_knowledge_graph_tables(cursor)
            self._create_vector_graph_tables(cursor)
            self._create_causal_graph_tables(cursor)
            self._create_social_graph_tables(cursor)
            self._create_system_graph_tables(cursor)
            self._create_cross_graph_tables(cursor)

            self.conn.commit()
            print("✅ Database initialized with all graph tables")
            return True

        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False

    def _create_knowledge_graph_tables(self, cursor) -> None:
        """Create knowledge graph tables."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

    def _create_vector_graph_tables(self, cursor) -> None:
        """Create vector graph tables."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vector_nodes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                vector_id TEXT UNIQUE,
                model_name TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vector_embeddings (
                vector_id TEXT PRIMARY KEY,
                embedding BLOB,
                dimension INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

    def _create_causal_graph_tables(self, cursor) -> None:
        """Create causal graph tables."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS causal_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS causal_edges (
                id TEXT PRIMARY KEY,
                cause_id TEXT NOT NULL,
                effect_id TEXT NOT NULL,
                strength REAL,
                confidence REAL,
                delay_ms INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

    def _create_social_graph_tables(self, cursor) -> None:
        """Create social graph tables."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS social_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                attributes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS social_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

    def _create_system_graph_tables(self, cursor) -> None:
        """Create system graph tables."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

    def _create_cross_graph_tables(self, cursor) -> None:
        """Create cross-graph relationship tables."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cross_graph_relationships (
                id TEXT PRIMARY KEY,
                source_graph TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_graph TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                confidence REAL,
                strength REAL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

    def migrate_tdd_data(self) -> bool:
        """Migrate TDD enforcement data."""
        if not self.data_sources["tdd"].exists():
            print(f"⚠️ TDD data file not found: {self.data_sources['tdd']}")
            return False

        try:
            print("📥 Migrating TDD enforcement data...")
            cursor = self.conn.cursor()

            with open(self.data_sources["tdd"], encoding="utf-8") as f:
                tdd_data = json.load(f)

            # Create main TDD concept
            tdd_id = f"concept_tdd_{int(datetime.now().timestamp())}"
            cursor.execute(
                """
                INSERT INTO knowledge_nodes (id, type, content, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    tdd_id,
                    "concept",
                    json.dumps(
                        {
                            "name": "Claude Code Hooks TDD Enforcement",
                            "definition": tdd_data.get("title", ""),
                            "category": "tdd_enforcement",
                        },
                    ),
                    json.dumps(
                        {
                            "source": "claude_code_hooks_tdd_data.json",
                            "last_updated": tdd_data.get("last_updated"),
                            "category": tdd_data.get("category"),
                        },
                    ),
                ),
            )

            # Migrate repositories
            repositories = tdd_data.get("repositories", {})
            repo_count = 0

            for repo_name, repo_info in repositories.items():
                repo_id = f"repo_{repo_name.lower().replace('-', '_')}"

                # Create social entity for repository
                cursor.execute(
                    """
                    INSERT INTO social_nodes (id, type, name, content, attributes)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        repo_id,
                        "repository",
                        repo_name,
                        json.dumps(
                            {
                                "description": repo_info.get("description", ""),
                                "purpose": repo_info.get("purpose", ""),
                            },
                        ),
                        json.dumps(
                            {
                                "url": repo_info.get("url"),
                                "features": repo_info.get("features", []),
                                "installation": repo_info.get("installation", {}),
                            },
                        ),
                    ),
                )

                # Create knowledge concept for repository
                repo_concept_id = f"concept_{repo_id}"
                cursor.execute(
                    """
                    INSERT INTO knowledge_nodes (id, type, content, metadata)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        repo_concept_id,
                        "concept",
                        json.dumps(
                            {
                                "name": f"{repo_name} Repository",
                                "definition": repo_info.get("description", ""),
                                "category": "repository",
                            },
                        ),
                        json.dumps(
                            {
                                "url": repo_info.get("url"),
                                "features": repo_info.get("features", []),
                            },
                        ),
                    ),
                )

                # Create cross-graph relationship
                cross_rel_id = f"cross_{tdd_id}_{repo_id}"
                cursor.execute(
                    """
                    INSERT INTO cross_graph_relationships
                    (id, source_graph, source_id, target_graph, target_id, relationship_type, confidence, strength, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        cross_rel_id,
                        "knowledge",
                        tdd_id,
                        "social",
                        repo_id,
                        "knowledge_representation",
                        0.9,
                        0.8,
                        json.dumps(
                            {"relationship": "repository_implements_tdd_enforcement"},
                        ),
                    ),
                )

                # Create vector node for description
                if repo_info.get("description"):
                    vector_id = f"vector_{repo_id}_desc"
                    cursor.execute(
                        """
                        INSERT INTO vector_nodes (id, content, vector_id, model_name, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            vector_id,
                            repo_info.get("description"),
                            vector_id,
                            "placeholder",  # Would be actual embedding model
                            json.dumps({"source": "tdd_data", "repository": repo_name}),
                        ),
                    )

                repo_count += 1

            self.conn.commit()
            print(f"✅ Migrated {repo_count} TDD repositories")
            return True

        except Exception as e:
            print(f"❌ Failed to migrate TDD data: {e}")
            return False

    def migrate_multi_agent_research(self) -> bool:
        """Migrate multi-agent architecture research."""
        if not self.data_sources["multi_agent"].exists():
            print(
                f"⚠️ Multi-agent research file not found: {self.data_sources['multi_agent']}",
            )
            return False

        try:
            print("📥 Migrating multi-agent architecture research...")
            cursor = self.conn.cursor()

            with open(self.data_sources["multi_agent"], encoding="utf-8") as f:
                content = f.read()

            # Create main research concept
            research_id = f"concept_multi_agent_research_{int(datetime.now().timestamp())}"
            cursor.execute(
                """
                INSERT INTO knowledge_nodes (id, type, content, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    research_id,
                    "concept",
                    json.dumps(
                        {
                            "name": "Claude Multi-Agent Architecture Research",
                            "definition": "Systematic research on multi-agent architecture patterns for Claude Code",
                            "category": "research",
                        },
                    ),
                    json.dumps(
                        {
                            "source": "claude_multi_agent_architecture_research_summary.md",
                            "research_date": "2024-12-11",
                        },
                    ),
                ),
            )

            # Extract patterns (simplified)
            lines = content.split("\n")
            patterns_found = 0

            for i, line in enumerate(lines):
                if line.startswith("### ") and "Pattern" in line:
                    pattern_name = line[4:].strip()

                    # Extract description from next few lines
                    description = ""
                    for j in range(i + 1, min(i + 10, len(lines))):
                        if lines[j].startswith("- **Description:**"):
                            description = lines[j].split("Description:**")[1].strip()
                            break

                    # Create pattern node
                    pattern_id = (
                        f"pattern_{pattern_name.lower().replace(' ', '_').replace('-', '_')}"
                    )
                    cursor.execute(
                        """
                        INSERT INTO knowledge_nodes (id, type, content, metadata)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            pattern_id,
                            "architecture_pattern",
                            json.dumps(
                                {
                                    "name": pattern_name,
                                    "definition": description,
                                    "category": "architecture_pattern",
                                },
                            ),
                            json.dumps(
                                {
                                    "source": "research_summary",
                                    "pattern_number": patterns_found + 1,
                                },
                            ),
                        ),
                    )

                    # Create system component
                    system_id = f"system_{pattern_id}"
                    cursor.execute(
                        """
                        INSERT INTO system_nodes (id, type, name, content, status)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            system_id,
                            "architecture_pattern",
                            pattern_name,
                            json.dumps(
                                {
                                    "description": description,
                                    "status": "researched",
                                },
                            ),
                            "researched",
                        ),
                    )

                    # Create cross-graph relationship
                    cross_rel_id = f"cross_{pattern_id}_{system_id}"
                    cursor.execute(
                        """
                        INSERT INTO cross_graph_relationships
                        (id, source_graph, source_id, target_graph, target_id, relationship_type, confidence, strength, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            cross_rel_id,
                            "knowledge",
                            pattern_id,
                            "system",
                            system_id,
                            "system_workflow",
                            0.8,
                            0.7,
                            json.dumps(
                                {"relationship": "pattern_implemented_as_system"},
                            ),
                        ),
                    )

                    # Create vector node for pattern
                    vector_id = f"vector_{pattern_id}"
                    pattern_text = f"{pattern_name}: {description}"
                    cursor.execute(
                        """
                        INSERT INTO vector_nodes (id, content, vector_id, model_name, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            vector_id,
                            pattern_text,
                            vector_id,
                            "placeholder",
                            json.dumps(
                                {"source": "research", "type": "architecture_pattern"},
                            ),
                        ),
                    )

                    patterns_found += 1

            self.conn.commit()
            print(f"✅ Migrated {patterns_found} architecture patterns")
            return True

        except Exception as e:
            print(f"❌ Failed to migrate multi-agent research: {e}")
            return False

    def migrate_memory_bank_sample(self) -> bool:
        """Migrate a sample of memory bank research data."""
        if not self.data_sources["memory_bank"].exists():
            print(
                f"⚠️ Memory bank research path not found: {self.data_sources['memory_bank']}",
            )
            return False

        try:
            print("📥 Migrating memory bank research data (sample)...")
            cursor = self.conn.cursor()

            migrated_count = 0
            max_files = 50  # Limit to prevent overwhelming

            # Migrate YAML files
            for yaml_file in self.data_sources["memory_bank"].rglob("*.yaml"):
                if migrated_count >= max_files:
                    break

                try:
                    import yaml

                    with open(yaml_file, encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    concept_name = yaml_file.stem
                    relative_path = yaml_file.relative_to(
                        self.data_sources["memory_bank"],
                    )

                    concept_id = (
                        f"memory_{concept_name.lower().replace(' ', '_').replace('-', '_')}"
                    )
                    cursor.execute(
                        """
                        INSERT INTO knowledge_nodes (id, type, content, metadata)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            concept_id,
                            "memory_bank_research",
                            json.dumps(
                                {
                                    "name": concept_name,
                                    "definition": str(data)[:500] if data else "",
                                    "category": "memory_bank_research",
                                },
                            ),
                            json.dumps(
                                {
                                    "source": str(relative_path),
                                    "file_type": "yaml",
                                    "data_keys": (
                                        list(data.keys()) if isinstance(data, dict) else []
                                    ),
                                },
                            ),
                        ),
                    )

                    # Create vector node
                    vector_id = f"vector_{concept_id}"
                    text = f"{concept_name}: {str(data)[:2000] if data else ''}"
                    cursor.execute(
                        """
                        INSERT INTO vector_nodes (id, content, vector_id, model_name, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            vector_id,
                            text,
                            vector_id,
                            "placeholder",
                            json.dumps(
                                {"source": "memory_bank", "file": str(relative_path)},
                            ),
                        ),
                    )

                    migrated_count += 1

                except Exception as e:
                    print(f"⚠️ Failed to migrate {yaml_file}: {e}")
                    continue

            self.conn.commit()
            print(f"✅ Migrated {migrated_count} memory bank files")
            return True

        except Exception as e:
            print(f"❌ Failed to migrate memory bank data: {e}")
            return False

    def create_semantic_relationships(self) -> bool:
        """Create semantic relationships between migrated content."""
        try:
            print("🔗 Creating semantic relationships...")
            cursor = self.conn.cursor()

            # Create relationships between TDD and architecture patterns
            cursor.execute(
                """
                INSERT OR IGNORE INTO cross_graph_relationships
                (id, source_graph, source_id, target_graph, target_id, relationship_type, confidence, strength, metadata)
                SELECT
                    'cross_' || kn1.id || '_' || kn2.id,
                    'knowledge',
                    kn1.id,
                    'knowledge',
                    kn2.id,
                    'semantic_similarity',
                    0.75,
                    0.7,
                    '{"relationship": "tdd_architecture_synergy"}'
                FROM knowledge_nodes kn1, knowledge_nodes kn2
                WHERE kn1.type = 'concept'
                AND kn1.content LIKE '%tdd%'
                AND kn2.type = 'architecture_pattern'
                LIMIT 10
            """,
            )

            # Create causal relationships for system dependencies
            cursor.execute(
                """
                INSERT OR IGNORE INTO causal_edges
                (id, cause_id, effect_id, strength, confidence, metadata)
                SELECT
                    'causal_init_' || sn.id,
                    'system_init',
                    sn.id,
                    0.8,
                    0.9,
                    '{"dependency": "initialization_enables_component"}'
                FROM system_nodes sn
                WHERE sn.type = 'architecture_pattern'
            """,
            )

            self.conn.commit()
            print("✅ Created semantic relationships")
            return True

        except Exception as e:
            print(f"❌ Failed to create semantic relationships: {e}")
            return False

    def generate_statistics(self) -> dict[str, Any]:
        """Generate system statistics."""
        cursor = self.conn.cursor()

        stats = {}

        # Count nodes in each graph
        for table in [
            "knowledge_nodes",
            "vector_nodes",
            "causal_nodes",
            "social_nodes",
            "system_nodes",
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]

        # Count edges
        for table in [
            "knowledge_edges",
            "vector_embeddings",
            "causal_edges",
            "social_edges",
            "system_edges",
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]

        # Count cross-graph relationships
        cursor.execute("SELECT COUNT(*) FROM cross_graph_relationships")
        stats["cross_graph_relationships"] = cursor.fetchone()[0]

        return stats

    def save_system_info(self) -> bool:
        """Save system configuration and statistics."""
        try:
            stats = self.generate_statistics()

            system_info = {
                "initialized_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "database_path": str(DB_PATH),
                "statistics": stats,
                "graph_types": ["knowledge", "vector", "causal", "social", "system"],
                "relationship_types": [
                    "semantic_similarity",
                    "causal_influence",
                    "social_dependency",
                    "system_workflow",
                    "knowledge_representation",
                ],
            }

            info_path = DATA_DIR / "system_info.json"
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(system_info, f, indent=2)

            print(f"📊 System statistics: {json.dumps(stats, indent=2)}")
            print(f"💾 System info saved to: {info_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to save system info: {e}")
            return False

    def run(self) -> bool:
        """Run the complete initialization process."""
        print("\n" + "=" * 60)
        print("CKS HYPER-GRAPH INITIALIZATION")
        print("=" * 60 + "\n")

        success_steps = 0
        total_steps = 7

        # Step 1: Initialize database
        if self.initialize_database():
            success_steps += 1

        # Step 2: Migrate TDD data
        if self.migrate_tdd_data():
            success_steps += 1

        # Step 3: Migrate multi-agent research
        if self.migrate_multi_agent_research():
            success_steps += 1

        # Step 4: Migrate memory bank sample
        if self.migrate_memory_bank_sample():
            success_steps += 1

        # Step 5: Create semantic relationships
        if self.create_semantic_relationships():
            success_steps += 1

        # Step 6: Save system info
        if self.save_system_info():
            success_steps += 1

        # Step 7: Close connection
        if self.conn:
            self.conn.close()
            success_steps += 1

        # Report results
        print("\n" + "=" * 60)
        if success_steps == total_steps:
            print(f"🎉 INITIALIZATION COMPLETE! ({success_steps}/{total_steps} steps)")
            print("\nThe CKS Hyper-Graph system is ready for use!")
            print(f"Database location: {DB_PATH}")
        else:
            print(f"⚠️ INITIALIZATION PARTIAL ({success_steps}/{total_steps} steps)")
            print("Some components may not be fully migrated.")
        print("=" * 60)

        return success_steps == total_steps


def main() -> None:
    """Main entry point."""
    initializer = CKSDirectInitializer()
    success = initializer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
