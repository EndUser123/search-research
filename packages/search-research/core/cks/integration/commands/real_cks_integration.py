import asyncio
import hashlib
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""
Real CKS Integration for /learn Command

This module provides the proper integration between the /learn command and the
real Cognitive Knowledge System infrastructure, replacing the simulated version.
"""


# Add project paths
project_root = Path(__file__).parent.parent.parent

# Import real CKS components
try:
    from co.learn_spec_2025 import CKSConfig, KnowledgeEntry, KnowledgeManager

    REAL_CKS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Real CKS not available: {e}")
    REAL_CKS_AVAILABLE = False
    KnowledgeManager = None
    KnowledgeEntry = None
    CKSConfig = None

# Import context detection from our simulation (reusable)
try:
    from simple_cks_test import ContextDetector, KnowledgeType
except ImportError:
    ContextDetector = None
    KnowledgeType = None


@dataclass
class CKSIntegrationResult:
    """Result from CKS integration operations."""

    success: bool
    entry_id: str | None = None
    processing_time: float = 0.0
    stored_in_real_cks: bool = False
    cks_stats: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class RealCKSIntegration:
    """Proper integration with the real Cognitive Knowledge System."""

    def __init__(self) -> None:
        """Initialize real CKS integration."""
        self.knowledge_manager = None
        self.context_detector = ContextDetector() if ContextDetector else None

        if REAL_CKS_AVAILABLE:
            try:
                # Initialize with CKS configuration
                config = CKSConfig(
                    db_path="data/knowledge.db",  # Real CKS database path
                    log_level="INFO",
                    enable_fts=True,
                )
                self.knowledge_manager = KnowledgeManager(config)
                print("✅ Connected to real CKS infrastructure")
            except Exception as e:
                print(f"⚠️ CKS initialization error: {e}")
        else:
            print("❌ Real CKS not available - using fallback")

    def _generate_knowledge_id(self, content: str) -> str:
        """Generate unique ID for knowledge entry."""
        timestamp = datetime.now().isoformat()
        content_hash = hashlib.md5(f"{content}{timestamp}".encode()).hexdigest()[:12]
        return f"cks_{content_hash}_{int(time.time())}"

    def _extract_entities(self, content: str) -> list[str]:
        """Extract entities from content."""
        entities = []

        # Technical terms
        tech_patterns = [
            r"\b(CKS|AI|ML|API|GPU|CPU|SQL|NoSQL|HTTP|JSON|XML|Python|JavaScript|React|Vue|Angular)\b",
            r"\b(vector\s+embedding|semantic\s+search|knowledge\s+graph|hyper\s*graph)\b",
        ]

        import re

        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities.extend(matches)

        # URLs and file paths
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]*'
        entities.extend(re.findall(url_pattern, content))

        return list(set(entities))

    def _generate_tags(self, content: str, knowledge_type: str) -> list[str]:
        """Generate content-based tags."""
        content_lower = content.lower()
        tags = [knowledge_type]

        # Topic-based tagging
        topic_keywords = {
            "programming": ["python", "javascript", "code", "function", "class", "method"],
            "database": ["sql", "database", "query", "table", "index", "schema"],
            "api": ["endpoint", "request", "response", "rest", "graphql", "api"],
            "security": ["authentication", "authorization", "security", "encryption", "token"],
            "performance": ["optimization", "performance", "speed", "latency", "cache"],
            "ai-ml": ["machine learning", "artificial intelligence", "neural", "model", "training"],
            "cks": ["cognitive knowledge system", "cks", "knowledge graph", "vector embedding"],
            "architecture": ["design", "pattern", "architecture", "structure", "system"],
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(topic)

        return tags

    async def ingest_knowledge(
        self,
        input_data: str,
        category: str | None = None,
        title: str | None = None,
        user_context: str | None = None,
    ) -> CKSIntegrationResult:
        """Ingest knowledge into the real CKS system."""
        start_time = time.time()

        try:
            # Detect knowledge type
            knowledge_type = "direct_text"
            confidence = 0.5

            if self.context_detector:
                detected_type, detected_confidence = self.context_detector.detect_type(input_data)
                knowledge_type = detected_type.value
                confidence = detected_confidence

            # Generate metadata
            entry_id = self._generate_knowledge_id(input_data)
            entities = self._extract_entities(input_data)
            tags = self._generate_tags(input_data, knowledge_type)

            # Determine category
            if not category:
                content_lower = input_data.lower()
                if any(word in content_lower for word in ["bug", "error", "issue", "problem"]):
                    category = "troubleshooting"
                elif any(word in content_lower for word in ["how to", "tutorial", "guide"]):
                    category = "tutorial"
                elif any(word in content_lower for word in ["best practice", "pattern"]):
                    category = "best-practice"
                else:
                    category = "general"

            # Prepare for real CKS storage
            if self.knowledge_manager and REAL_CKS_AVAILABLE:
                # Create KnowledgeEntry for real CKS (correct field types)
                knowledge_entry = KnowledgeEntry(
                    id=None,  # Auto-generated by database
                    title=title or f"Knowledge Entry {entry_id}",
                    content=input_data,
                    category=category,
                    tags=", ".join(tags),  # Convert list to comma-separated string
                    timestamp=datetime.now(),
                )

                # Store in real CKS using KnowledgeManager
                result = await self.knowledge_manager.learn(knowledge_entry)

                processing_time = time.time() - start_time

                return CKSIntegrationResult(
                    success=True,
                    entry_id=entry_id,
                    processing_time=processing_time,
                    stored_in_real_cks=True,
                    cks_stats=result.get("metadata", {}),
                    metadata={
                        "knowledge_type": knowledge_type,
                        "confidence": confidence,
                        "category": category,
                        "entities": entities,
                        "tags": tags,
                        "user_context": user_context,
                    },
                )
            # Fallback storage (simulated)
            processing_time = time.time() - start_time
            return CKSIntegrationResult(
                success=True,
                entry_id=entry_id,
                processing_time=processing_time,
                stored_in_real_cks=False,
                metadata={
                    "knowledge_type": knowledge_type,
                    "confidence": confidence,
                    "category": category,
                    "entities": entities,
                    "tags": tags,
                    "user_context": user_context,
                    "fallback_mode": True,
                },
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return CKSIntegrationResult(
                success=False,
                processing_time=processing_time,
                error=str(e),
                metadata={"error_context": "cks_ingestion_failed"},
            )

    def get_cks_status(self) -> dict[str, Any]:
        """Get real CKS system status."""
        if not REAL_CKS_AVAILABLE:
            return {
                "status": "unavailable",
                "message": "Real CKS components not found",
            }

        try:
            from cli.subprocess_helper import run_subprocess

            result = run_subprocess(
                [
                    sys.executable,
                    "-m",
                    "features.cks.cks_cli",
                    "stats",
                ],
                capture_output=True,
                text=True,
                cwd=str(project_root),
            )

            if result.returncode == 0:
                return {
                    "status": "available",
                    "cli_output": result.stdout,
                    "knowledge_manager": "connected" if self.knowledge_manager else "disconnected",
                }
            return {
                "status": "error",
                "error": result.stderr,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }


async def test_real_cks_integration():
    """Test the real CKS integration."""
    print("🧪 Testing Real CKS Integration")
    print("=" * 40)

    # Initialize integration
    integration = RealCKSIntegration()

    # Show CKS status
    status = integration.get_cks_status()
    print(f"🔍 CKS Status: {status['status']}")

    # Test knowledge ingestion
    test_content = """Key insight: Real CKS integration provides persistent knowledge storage
    with vector embeddings and semantic relationships. Best practice: Always use the
    Cognitive Knowledge System for knowledge management to ensure proper semantic search
    and cross-reference capabilities."""

    result = await integration.ingest_knowledge(
        input_data=test_content,
        category="integration-test",
        title="Real CKS Integration Test",
        user_context="Testing real CKS connectivity",
    )

    print("\n📝 Ingestion Result:")
    print(f"   Success: {result.success}")
    print(f"   Entry ID: {result.entry_id}")
    print(f"   Stored in Real CKS: {result.stored_in_real_cks}")
    print(f"   Processing Time: {result.processing_time:.3f}s")

    if result.metadata:
        print(f"   Category: {result.metadata.get('category')}")
        print(f"   Tags: {', '.join(result.metadata.get('tags', []))}")
        print(f"   Entities: {', '.join(result.metadata.get('entities', []))}")

    if result.error:
        print(f"   Error: {result.error}")

    return result


if __name__ == "__main__":
    asyncio.run(test_real_cks_integration())
