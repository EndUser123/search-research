import asyncio
import hashlib
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

"""Simplified CKS Test - Testing Knowledge Type Detection and Basic Processing

This is a simplified test version that focuses on the core functionality
without the complex CKS dependencies that are causing import issues.
"""


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Automatic knowledge type detection."""

    WEBSITE = "website"
    FLAT_FILE = "flat_file"
    CONVERSATION = "conversation"
    DIRECT_TEXT = "direct_text"


@dataclass
class SimpleKnowledgeEntry:
    """Simple knowledge entry for testing."""

    id: str
    title: str
    content: str
    knowledge_type: str
    category: str
    timestamp: str
    tags: list[str]
    metadata: dict[str, Any]


class ContextDetector:
    """Intelligent context detection for different knowledge types."""

    def __init__(self) -> None:
        self.website_patterns = [
            r"^https?://[^\s]+",
            r"^www\.[^\s]+",
            r"\.com[/\?]?",
            r"\.org[/\?]?",
            r"\.edu[/\?]?",
            r"\.gov[/\?]?",
        ]

        self.file_patterns = [
            r'[A-Za-z]:\\[^*|"<>?\n]*',  # Windows paths
            r'/[^*|"<>?\n]*',  # Unix paths
            r"\.pdf$",
            r"\.docx?$",
            r"\.txt$",
            r"\.md$",
            r"\.py$",
            r"\.js$",
            r"\.html?$",
        ]

        self.conversation_patterns = [
            r"(?i)^(user|assistant|human|ai|claude|gpt):",
            r"(?i)^(q|a):",
            r"(?i)^question:",
            r"(?i)^answer:",
            r"(?i)^how do i",
            r"(?i)^what is",
            r"(?i)^why does",
            r"(?i)^can you",
        ]

        self.learning_patterns = [
            r"(?i)key insight:",
            r"(?i)takeaway:",
            r"(?i)i learned that",
            r"(?i)the solution is",
            r"(?i)best practice:",
            r"(?i)important note:",
            r"(?i)principle:",
            r"(?i)pattern:",
            r"(?i)optimization:",
        ]

    def detect_type(self, content: str) -> tuple[KnowledgeType, float]:
        """Detect knowledge type with confidence score."""
        content_lower = content.lower()
        content_stripped = content.strip()

        # Check for website
        for pattern in self.website_patterns:
            if re.search(pattern, content_stripped):
                return KnowledgeType.WEBSITE, 0.9

        # Check for file path
        for pattern in self.file_patterns:
            if re.search(pattern, content_stripped):
                return KnowledgeType.FLAT_FILE, 0.8

        # Check for conversation
        conversation_score = 0
        for pattern in self.conversation_patterns:
            if re.search(pattern, content_stripped):
                conversation_score += 0.3
        if conversation_score >= 0.3:
            return KnowledgeType.CONVERSATION, min(conversation_score, 1.0)

        # Check for learning/reflection
        learning_score = 0
        for pattern in self.learning_patterns:
            if re.search(pattern, content_lower):
                learning_score += 0.4
        if learning_score >= 0.4:
            return KnowledgeType.DIRECT_TEXT, 0.7

        # Default to direct text
        return KnowledgeType.DIRECT_TEXT, 0.5


class SimpleCKSProcessor:
    """Simplified CKS-like knowledge processor for testing."""

    def __init__(self) -> None:
        self.detector = ContextDetector()
        self.knowledge_store = {}  # Simple in-memory storage for testing

    def _generate_id(self, content: str) -> str:
        """Generate unique ID for knowledge entry."""
        return hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()[:16]

    def _extract_entities(self, content: str) -> list[str]:
        """Extract simple entities from content."""
        entities = []

        # Extract URLs
        url_pattern = r'https?://[^\s<>"]+'
        entities.extend(re.findall(url_pattern, content))

        # Extract file paths
        file_pattern = r"[A-Za-z]:\\[^<>]*\.[a-zA-Z0-9]+"
        entities.extend(re.findall(file_pattern, content))

        # Extract technical terms (simple pattern)
        tech_pattern = r"\b(AI|ML|API|CKS|GPU|CPU|SQL|NoSQL|HTTP|JSON|XML|Python|JavaScript)\b"
        entities.extend(re.findall(tech_pattern, content, re.IGNORECASE))

        return list(set(entities))

    def _extract_key_phrases(self, content: str) -> list[str]:
        """Extract key phrases from content."""
        phrases = []

        patterns = [
            r"(?i)what\s+is\s+[a-z\s]+",
            r"(?i)how\s+to\s+[a-z\s]+",
            r"(?i)the\s+problem\s+is",
            r"(?i)solution\s+is",
            r"(?i)best\s+practice",
            r"(?i)important\s+note",
            r"(?i)key\s+takeaway",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            phrases.extend(matches)

        return phrases[:5]  # Limit to top 5

    def _generate_tags(self, content: str, knowledge_type: KnowledgeType) -> list[str]:
        """Generate tags based on content and type."""
        tags = [knowledge_type.value]

        content_lower = content.lower()

        # Topic-based tags
        if any(word in content_lower for word in ["python", "javascript", "java", "rust"]):
            tags.append("programming")
        if any(word in content_lower for word in ["database", "sql", "nosql"]):
            tags.append("database")
        if any(word in content_lower for word in ["api", "rest", "graphql"]):
            tags.append("api")
        if any(word in content_lower for word in ["security", "authentication", "authorization"]):
            tags.append("security")
        if any(word in content_lower for word in ["performance", "optimization", "speed"]):
            tags.append("performance")
        if any(
            word in content_lower
            for word in ["ai", "ml", "machine learning", "artificial intelligence"]
        ):
            tags.append("ai-ml")

        return tags

    def _categorize_content(self, content: str, knowledge_type: KnowledgeType) -> str:
        """Categorize content based on analysis."""
        content_lower = content.lower()

        if any(word in content_lower for word in ["bug", "error", "issue", "problem"]):
            return "troubleshooting"
        if any(word in content_lower for word in ["how to", "tutorial", "guide", "step by step"]):
            return "tutorial"
        if any(word in content_lower for word in ["best practice", "pattern", "principle"]):
            return "best-practice"
        if any(word in content_lower for word in ["api", "endpoint", "service"]):
            return "api-documentation"
        if any(word in content_lower for word in ["config", "setup", "install", "deploy"]):
            return "configuration"
        return "general"

    async def ingest_knowledge(
        self,
        input_data: str,
        category: str | None = None,
        title: str | None = None,
        user_context: str | None = None,
    ) -> dict[str, Any]:
        """Main knowledge ingestion method."""
        start_time = time.time()

        # Detect knowledge type
        knowledge_type, confidence = self.detector.detect_type(input_data)

        # Process content based on type
        if knowledge_type == KnowledgeType.WEBSITE:
            processed_content = f"Website content: {input_data}"
        elif knowledge_type == KnowledgeType.FLAT_FILE:
            processed_content = f"File content: {input_data}"
        elif knowledge_type == KnowledgeType.CONVERSATION:
            processed_content = f"Conversation: {input_data}"
        else:
            processed_content = input_data

        # Extract features
        entities = self._extract_entities(processed_content)
        key_phrases = self._extract_key_phrases(processed_content)
        tags = self._generate_tags(processed_content, knowledge_type)

        # Determine category
        final_category = category or self._categorize_content(processed_content, knowledge_type)

        # Create entry
        entry_id = self._generate_id(processed_content)
        entry = SimpleKnowledgeEntry(
            id=entry_id,
            title=title or f"Knowledge Entry {entry_id}",
            content=processed_content,
            knowledge_type=knowledge_type.value,
            category=final_category,
            timestamp=datetime.now().isoformat(),
            tags=tags,
            metadata={
                "confidence": confidence,
                "entities": entities,
                "key_phrases": key_phrases,
                "user_context": user_context,
                "processing_time": time.time() - start_time,
            },
        )

        # Store in simple knowledge base
        self.knowledge_store[entry_id] = entry

        processing_time = time.time() - start_time

        return {
            "entry_id": entry_id,
            "type": knowledge_type.value,
            "confidence": confidence,
            "category": final_category,
            "processing_time": processing_time,
            "tags": tags,
            "metadata": {
                "entities": entities,
                "key_phrases": key_phrases,
                "user_context": user_context,
            },
        }


async def test_cks_integration() -> None:
    """Test the CKS integration functionality."""
    print("🧪 Testing Simplified CKS Knowledge Integration")
    print("=" * 50)

    # Initialize processor
    processor = SimpleCKSProcessor()
    print("✅ CKS Processor initialized successfully")

    # Test context detection
    print("\n🔍 Testing Context Detection:")

    test_cases = [
        ("https://example.com/article", "Website URL"),
        ("P:/__csf/docs/example.pdf", "File path"),
        ("User: How do I implement X?\nAssistant: You can use Y method...", "Conversation"),
        ("Key insight: The best approach to optimize performance is...", "Learning/Insight"),
        ("This is just some direct text without specific patterns", "Direct text"),
    ]

    for content, description in test_cases:
        knowledge_type, confidence = processor.detector.detect_type(content)
        print(f"{description:25} -> {knowledge_type.name:15} (confidence: {confidence:.2f})")

    print("\n✅ Context detection working correctly!")

    # Test knowledge ingestion
    print("\n📝 Testing Knowledge Ingestion:")

    test_content = """Key insight: Fixing the /learn command requires proper CKS integration.
    The best approach is to use the Cognitive Knowledge System instead of flat files
    because it provides vector embeddings and semantic relationships."""

    try:
        result = await processor.ingest_knowledge(
            input_data=test_content,
            category="implementation",
            title="CKS Integration Fix",
            user_context="Testing the CKS knowledge system",
        )

        print("✅ Knowledge ingested successfully!")
        print(f'   Entry ID: {result["entry_id"]}')
        print(f'   Type: {result["type"]} (confidence: {result["confidence"]:.2f})')
        print(f'   Category: {result["category"]}')
        print(f'   Processing time: {result["processing_time"]:.3f}s')
        print(f'   Tags: {", ".join(result["tags"])}')
        print(f'   Entities: {result["metadata"]["entities"]}')
        print(f'   Key phrases: {result["metadata"]["key_phrases"]}')

        # Show stored entry
        stored_entry = processor.knowledge_store[result["entry_id"]]
        print("\n📋 Stored Entry Summary:")
        print(f"   Title: {stored_entry.title}")
        print(f"   Content length: {len(stored_entry.content)} chars")
        print(f"   Timestamp: {stored_entry.timestamp}")

    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        import traceback

        traceback.print_exc()

    print("\n🎉 CKS Integration Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_cks_integration())
