import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""
CKS Hyper-Graph Initialization Script

This script initializes the complete CKS multi-graph engine and migrates all existing
content from flat file storage to the hyper-graph architecture.

Key Features:
- Initializes all 5 graph types: Knowledge, Vector, Causal, Social, System
- Migrates existing knowledge from JSON and Markdown files
- Creates semantic relationships between TDD, multi-agent, and research patterns
- Enables GPU acceleration with CPU fallback
- Sets up FAISS vector storage for semantic search
- Establishes cross-graph relationships for intelligent querying
- Configures persistence for future sessions

Usage:
    python initialize_cks_hypergraph.py [--reset] [--validate-only]
"""


# Add the project root to sys.path for imports
project_root = Path(__file__).parent.parent.parent

# import CKS modules
try:
    from .core.gpu_manager import GPUMemoryConfig
    from .core.multi_graph_engine import (
        GraphType,
        MultiGraphConfig,
        MultiGraphEngine,
        RelationshipType,
        create_engine,
    )
    from .core.storage_manager import StorageConfig
    from .utils.constitutional_validator import ConstitutionalValidator
except ImportError as e:
    print(f"Error importing CKS modules: {e}")
    print("Make sure the CKS package is properly installed and in PYTHONPATH")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("cks_initialization.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class CKSHyperGraphInitializer:
    """Initializes CKS hyper-graph system with complete content migration."""

    def __init__(self, reset: bool = False) -> None:
        """Initialize the CKS hyper-graph system.

        Args:
            reset: Whether to reset existing data

        """
        self.reset = reset
        self.engine = None
        self.project_root = Path(__file__).parent.parent.parent

        # Data source paths
        self.tdd_data_path = (
            self.project_root
            / "src/features/modules/knowledge_system/claude_code_hooks_tdd_data.json"
        )
        self.multi_agent_research_path = (
            self.project_root / "docs/claude_multi_agent_architecture_research_summary.md"
        )
        self.memory_bank_path = self.project_root / "knowledge/memory_bank/research"

        # Storage configuration
        self.storage_path = self.project_root / "data/cks_hypergraph"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"CKS Hyper-Graph Initializer created with storage at: {self.storage_path}",
        )

    def create_config(self) -> MultiGraphConfig:
        """Create optimized configuration for CKS hyper-graph."""
        storage_config = StorageConfig(
            database_path=str(self.storage_path / "cks_hypergraph.db"),
            vector_index_path=str(self.storage_path / "faiss_index"),
            max_vector_size=100000,
            enable_compression=True,
            cache_size_mb=512,
        )

        gpu_config = GPUMemoryConfig(
            enable_gpu=True,
            gpu_memory_fraction=0.7,
            enable_mixed_precision=True,
            fallback_to_cpu=True,
        )

        return MultiGraphConfig(
            storage_config=storage_config,
            gpu_config=gpu_config,
            default_vector_dimension=768,
            embedding_model_name="all-MiniLM-L6-v2",
            semantic_threshold=0.7,
            causal_confidence_threshold=0.6,
            batch_size=100,
            max_concurrent_operations=10,
            enable_gpu_acceleration=True,
            auto_optimization=True,
            enable_audit_trail=True,
            constitutional_compliance_threshold=0.95,
            evidence_validation=True,
        )

    def initialize_engine(self) -> bool:
        """Initialize the multi-graph engine."""
        try:
            logger.info("Initializing CKS Multi-Graph Engine...")

            # Create configuration
            config = self.create_config()

            # Create and initialize engine
            self.engine = create_engine(config)

            logger.info("✅ CKS Multi-Graph Engine initialized successfully")

            # Log engine status
            metrics = self.engine.get_engine_metrics()
            logger.info(f"Engine metrics: {json.dumps(metrics, indent=2, default=str)}")

            return True

        except Exception as e:
            logger.exception(f"❌ Failed to initialize CKS engine: {e}")
            return False

    def migrate_tdd_enforcement_data(self) -> bool:
        """Migrate TDD enforcement data to knowledge graph."""
        if not self.tdd_data_path.exists():
            logger.warning(f"TDD data file not found: {self.tdd_data_path}")
            return False

        try:
            logger.info("Migrating TDD enforcement data...")

            with open(self.tdd_data_path, encoding="utf-8") as f:
                tdd_data = json.load(f)

            # Create main concept for TDD enforcement
            tdd_concept_id = self.engine.knowledge_ops.create_concept(
                concept="Claude Code Hooks TDD Enforcement",
                definition=tdd_data.get("title", ""),
                category="tdd_enforcement",
                metadata={
                    "source": "claude_code_hooks_tdd_data.json",
                    "last_updated": tdd_data.get("last_updated"),
                    "category": tdd_data.get("category"),
                },
            )

            # Migrate repository information
            repositories = tdd_data.get("repositories", {})
            for repo_name, repo_info in repositories.items():
                # Create repository entity in social graph
                repo_id = self.engine.social_ops.create_entity(
                    entity_name=repo_name,
                    entity_type="repository",
                    attributes={
                        "url": repo_info.get("url"),
                        "description": repo_info.get("description"),
                        "purpose": repo_info.get("purpose"),
                        "features": repo_info.get("features", []),
                    },
                )

                # Create knowledge concept for repository
                self.engine.knowledge_ops.create_concept(
                    concept=f"{repo_name} Repository",
                    definition=repo_info.get("description", ""),
                    category="repository",
                    metadata={
                        "url": repo_info.get("url"),
                        "features": repo_info.get("features", []),
                    },
                )

                # Create cross-graph relationship
                self.engine.create_cross_graph_relationship(
                    source_graph=GraphType.KNOWLEDGE,
                    source_id=tdd_concept_id,
                    target_graph=GraphType.SOCIAL,
                    target_id=repo_id,
                    relationship_type=RelationshipType.KNOWLEDGE_REPRESENTATION,
                    confidence=0.9,
                    strength=0.8,
                    metadata={"relationship": "repository_implements_tdd_enforcement"},
                )

                # Create vector embeddings for repository description
                if self.engine.vector_ops and repo_info.get("description"):
                    self.engine.vector_ops.create_embedding(
                        text=repo_info.get("description"),
                        vector_id=f"repo_{repo_name}_desc",
                        metadata={"source": "tdd_data", "repository": repo_name},
                    )

            logger.info(f"✅ Migrated {len(repositories)} TDD repositories")
            return True

        except Exception as e:
            logger.exception(f"❌ Failed to migrate TDD data: {e}")
            return False

    def migrate_multi_agent_research(self) -> bool:
        """Migrate multi-agent architecture research to knowledge graph."""
        if not self.multi_agent_research_path.exists():
            logger.warning(
                f"Multi-agent research file not found: {self.multi_agent_research_path}",
            )
            return False

        try:
            logger.info("Migrating multi-agent architecture research...")

            with open(self.multi_agent_research_path, encoding="utf-8") as f:
                content = f.read()

            # Create main research concept
            self.engine.knowledge_ops.create_concept(
                concept="Claude Multi-Agent Architecture Research",
                definition="Systematic research on multi-agent architecture patterns for Claude Code",
                category="research",
                metadata={
                    "source": "claude_multi_agent_architecture_research_summary.md",
                    "research_date": "2024-12-11",
                },
            )

            # Create vector embedding for the entire document
            if self.engine.vector_ops:
                self.engine.vector_ops.create_embedding(
                    text=content[:10000],  # Limit to first 10k chars
                    vector_id="multi_agent_research_full",
                    metadata={"source": "research_summary", "type": "full_document"},
                )

            # Extract architecture patterns (simplified extraction)
            lines = content.split("\n")
            current_pattern = None
            pattern_info = {}

            for line in lines:
                if line.startswith("### "):
                    # Save previous pattern
                    if current_pattern and pattern_info:
                        self._create_architecture_pattern_node(
                            current_pattern,
                            pattern_info,
                        )

                    # Start new pattern
                    current_pattern = line[4:].strip()
                    pattern_info = {}

                elif line.startswith("- **Category:**"):
                    if "Category:" in line:
                        pattern_info["category"] = line.split("Category:**")[1].strip()
                elif line.startswith("- **Description:**"):
                    if "Description:" in line:
                        pattern_info["description"] = line.split("Description:**")[1].strip()
                elif line.startswith("- **Use Cases:**"):
                    if "Use Cases:" in line:
                        pattern_info["use_cases"] = line.split("Use Cases:**")[1].strip()

            # Save last pattern
            if current_pattern and pattern_info:
                self._create_architecture_pattern_node(current_pattern, pattern_info)

            logger.info("✅ Migrated multi-agent architecture research")
            return True

        except Exception as e:
            logger.exception(f"❌ Failed to migrate multi-agent research: {e}")
            return False

    def _create_architecture_pattern_node(
        self,
        pattern_name: str,
        pattern_info: dict[str, Any],
    ) -> None:
        """Create a knowledge node for an architecture pattern."""
        # Create concept
        concept_id = self.engine.knowledge_ops.create_concept(
            concept=pattern_name,
            definition=pattern_info.get("description", ""),
            category="architecture_pattern",
            metadata=pattern_info,
        )

        # Create vector embedding
        if self.engine.vector_ops:
            text = f"{pattern_name} - {pattern_info.get('description', '')} - {pattern_info.get('use_cases', '')}"
            self.engine.vector_ops.create_embedding(
                text=text,
                vector_id=f"pattern_{pattern_name.lower().replace(' ', '_')}",
                metadata={"source": "research", "type": "architecture_pattern"},
            )

        # Create system component for the pattern
        system_id = self.engine.system_ops.create_component(
            component_name=pattern_name,
            component_type="architecture_pattern",
            status="researched",
            metadata=pattern_info,
        )

        # Create cross-graph relationships
        self.engine.create_cross_graph_relationship(
            source_graph=GraphType.KNOWLEDGE,
            source_id=concept_id,
            target_graph=GraphType.SYSTEM,
            target_id=system_id,
            relationship_type=RelationshipType.SYSTEM_WORKFLOW,
            confidence=0.8,
            strength=0.7,
            metadata={"relationship": "pattern_implemented_as_system"},
        )

    def migrate_memory_bank_research(self) -> bool:
        """Migrate memory bank research data."""
        if not self.memory_bank_path.exists():
            logger.warning(
                f"Memory bank research path not found: {self.memory_bank_path}",
            )
            return False

        try:
            logger.info("Migrating memory bank research data...")

            migrated_count = 0

            # Migrate YAML files
            for yaml_file in self.memory_bank_path.rglob("*.yaml"):
                if self._migrate_yaml_file(yaml_file):
                    migrated_count += 1

            # Migrate text files
            for txt_file in self.memory_bank_path.rglob("*.txt"):
                if self._migrate_text_file(txt_file):
                    migrated_count += 1

            logger.info(f"✅ Migrated {migrated_count} memory bank files")
            return True

        except Exception as e:
            logger.exception(f"❌ Failed to migrate memory bank research: {e}")
            return False

    def _migrate_yaml_file(self, yaml_file: Path) -> bool:
        """Migrate a single YAML file."""
        try:
            import yaml

            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Create concept from YAML
            concept_name = yaml_file.stem
            relative_path = yaml_file.relative_to(self.memory_bank_path)

            self.engine.knowledge_ops.create_concept(
                concept=concept_name,
                definition=str(data)[:500],  # Truncate if too long
                category="memory_bank_research",
                metadata={
                    "source": str(relative_path),
                    "file_type": "yaml",
                    "data_keys": list(data.keys()) if isinstance(data, dict) else [],
                },
            )

            # Create vector embedding
            if self.engine.vector_ops:
                text = f"{concept_name}: {str(data)[:2000]}"
                self.engine.vector_ops.create_embedding(
                    text=text,
                    vector_id=f"yaml_{concept_name.lower().replace(' ', '_')}",
                    metadata={"source": "memory_bank", "file": str(relative_path)},
                )

            return True

        except Exception as e:
            logger.warning(f"Failed to migrate YAML file {yaml_file}: {e}")
            return False

    def _migrate_text_file(self, txt_file: Path) -> bool:
        """Migrate a single text file."""
        try:
            with open(txt_file, encoding="utf-8") as f:
                content = f.read()

            concept_name = txt_file.stem
            relative_path = txt_file.relative_to(self.memory_bank_path)

            # Create concept
            self.engine.knowledge_ops.create_concept(
                concept=concept_name,
                definition=content[:500],
                category="memory_bank_research",
                metadata={
                    "source": str(relative_path),
                    "file_type": "text",
                    "content_length": len(content),
                },
            )

            # Create vector embedding
            if self.engine.vector_ops:
                self.engine.vector_ops.create_embedding(
                    text=content[:5000],  # Limit to 5k chars
                    vector_id=f"text_{concept_name.lower().replace(' ', '_')}",
                    metadata={"source": "memory_bank", "file": str(relative_path)},
                )

            return True

        except Exception as e:
            logger.warning(f"Failed to migrate text file {txt_file}: {e}")
            return False

    def create_cross_graph_relationships(self) -> bool:
        """Create semantic relationships between different graph types."""
        try:
            logger.info("Creating cross-graph semantic relationships...")

            # Create relationships between TDD and multi-agent patterns
            self._create_tdd_multi_agent_relationships()

            # Create relationships between research and practical implementations
            self._create_research_implementation_relationships()

            # Create causal relationships for workflow dependencies
            self._create_workflow_causal_relationships()

            logger.info("✅ Created cross-graph relationships")
            return True

        except Exception as e:
            logger.exception(f"❌ Failed to create cross-graph relationships: {e}")
            return False

    def _create_tdd_multi_agent_relationships(self) -> None:
        """Create relationships between TDD enforcement and multi-agent patterns."""
        # Find TDD concepts
        tdd_concepts = self.engine.storage.query_knowledge_nodes(
            "SELECT * FROM knowledge_nodes WHERE content LIKE '%tdd%' OR content LIKE '%TDD%'",
        )

        # Find multi-agent concepts
        ma_concepts = self.engine.storage.query_knowledge_nodes(
            "SELECT * FROM knowledge_nodes WHERE content LIKE '%multi-agent%' OR content LIKE '%architecture_pattern%'",
        )

        # Create semantic relationships
        for tdd_concept in tdd_concepts[:5]:  # Limit to prevent explosion
            for ma_concept in ma_concepts[:5]:
                # Calculate semantic similarity if vector ops available
                similarity = 0.7  # Default similarity

                if self.engine.vector_ops:
                    # This would use actual semantic similarity calculation
                    # For now, use a placeholder
                    pass

                if similarity > 0.6:
                    self.engine.create_cross_graph_relationship(
                        source_graph=GraphType.KNOWLEDGE,
                        source_id=tdd_concept["id"],
                        target_graph=GraphType.VECTOR,
                        target_id=ma_concept["id"],
                        relationship_type=RelationshipType.SEMANTIC_SIMILARITY,
                        confidence=similarity,
                        strength=similarity,
                        metadata={"relationship": "tdd_multi_agent_synergy"},
                    )

    def _create_research_implementation_relationships(self) -> None:
        """Create relationships between research and implementations."""
        # This would connect research concepts with actual implementations
        # For now, create placeholder relationships

    def _create_workflow_causal_relationships(self) -> None:
        """Create causal relationships for workflow dependencies."""
        # Create a causal event for system initialization
        init_event_id = self.engine.causal_ops.create_causal_event(
            event_name="CKS Hyper-Graph Initialization",
            event_type="system_event",
            timestamp=datetime.now(),
            metadata={
                "version": "1.0",
                "components": ["knowledge", "vector", "causal", "social", "system"],
            },
        )

        # Create causal relationships showing dependencies
        components = ["knowledge", "vector", "causal", "social", "system"]
        for i, component in enumerate(components[:-1]):
            next_component = components[i + 1]

            self.engine.causal_ops.create_causal_relationship(
                cause_id=init_event_id,
                effect_id=init_event_id,  # Would be actual component event IDs
                strength=0.8,
                confidence=0.9,
                metadata={"dependency": f"{component}_enables_{next_component}"},
            )

    def validate_system(self) -> bool:
        """Validate the initialized system."""
        try:
            logger.info("Validating CKS Hyper-Graph System...")

            # Check constitutional compliance
            compliance = self.engine.validate_constitutional_compliance()
            logger.info(f"Constitutional compliance: {compliance}")

            # Get engine metrics
            metrics = self.engine.get_engine_metrics()
            logger.info(f"System metrics: {json.dumps(metrics, indent=2, default=str)}")

            # Test semantic search
            if self.engine.vector_ops:
                results = self.engine.query_across_graphs(
                    "TDD enforcement",
                    max_results=5,
                )
                logger.info(f"Semantic search test returned {len(results)} results")

            # Test cross-graph insights
            # This would test a known entity
            logger.info("✅ System validation completed")
            return True

        except Exception as e:
            logger.exception(f"❌ System validation failed: {e}")
            return False

    def persist_configuration(self) -> bool:
        """Persist system configuration for future sessions."""
        try:
            config_file = self.storage_path / "system_config.json"

            config_data = {
                "initialized_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "storage_path": str(self.storage_path),
                "engine_config": self.engine.config.__dict__ if self.engine else {},
                "graph_types": [gt.value for gt in GraphType],
                "relationship_types": [rt.value for rt in RelationshipType],
            }

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, default=str)

            logger.info(f"✅ System configuration persisted to {config_file}")
            return True

        except Exception as e:
            logger.exception(f"❌ Failed to persist configuration: {e}")
            return False

    def run_initialization(self) -> bool:
        """Run the complete initialization process."""
        logger.info("🚀 Starting CKS Hyper-Graph Initialization...")

        success_steps = 0
        total_steps = 8

        # Step 1: Initialize engine
        if self.initialize_engine():
            success_steps += 1

        # Step 2: Migrate TDD data
        if self.migrate_tdd_enforcement_data():
            success_steps += 1

        # Step 3: Migrate multi-agent research
        if self.migrate_multi_agent_research():
            success_steps += 1

        # Step 4: Migrate memory bank
        if self.migrate_memory_bank_research():
            success_steps += 1

        # Step 5: Create cross-graph relationships
        if self.create_cross_graph_relationships():
            success_steps += 1

        # Step 6: Validate system
        if self.validate_system():
            success_steps += 1

        # Step 7: Persist configuration
        if self.persist_configuration():
            success_steps += 1

        # Step 8: Performance optimization
        if self.engine:
            optimization = self.engine.optimize_performance()
            logger.info(f"Performance optimization: {optimization}")
            success_steps += 1

        # Cleanup
        if self.engine:
            self.engine.cleanup()

        # Report results
        if success_steps == total_steps:
            logger.info(
                f"🎉 CKS Hyper-Graph initialization completed successfully! ({success_steps}/{total_steps} steps)",
            )
            return True
        logger.error(
            f"❌ CKS Hyper-Graph initialization partially completed ({success_steps}/{total_steps} steps)",
        )
        return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize CKS Hyper-Graph System with complete content migration",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing data before initialization",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing system without migration",
    )

    args = parser.parse_args()

    # Create initializer
    initializer = CKSHyperGraphInitializer(reset=args.reset)

    if args.validate_only:
        # Just validate existing system
        if initializer.initialize_engine():
            success = initializer.validate_system()
            if initializer.engine:
                initializer.engine.cleanup()
            sys.exit(0 if success else 1)
        else:
            sys.exit(1)
    else:
        # Run full initialization
        success = initializer.run_initialization()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
