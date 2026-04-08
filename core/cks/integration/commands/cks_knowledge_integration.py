import asyncio
import hashlib
import json
import logging
import re
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiofiles
import requests
from bs4 import BeautifulSoup

"""CKS-Integrated Knowledge Management System

Intelligent knowledge ingestion with automatic context detection and CKS integration.
Handles websites, flat files, conversations, and direct text with semantic analysis.

Constitutional Requirements:
- Mandatory CKS integration (Part J of Constitution)
- Evidence-based processing with comprehensive logging
- GPU acceleration with CPU fallback
- Context-aware processing for different knowledge types
- Vector embeddings and semantic relationship building
"""


# import CKS components
try:
    from .co.learn_spec_2025 import CKSConfig, KnowledgeEntry, KnowledgeManager, QueryRequest

    CKS_AVAILABLE = True
except ImportError as e:
    CKS_AVAILABLE = False
    logging.warning(f"CKS not available: {e}")
    KnowledgeEntry = None
    QueryRequest = None
    CKSConfig = None
    KnowledgeManager = None

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Automatic knowledge type detection."""

    WEBSITE = "website"
    FLAT_FILE = "flat_file"
    CONVERSATION = "conversation"
    DIRECT_TEXT = "direct_text"
    CODE_SNIPPET = "code_snippet"
    COMMAND_OUTPUT = "command_output"
    ERROR_LOG = "error_log"
    DOCUMENTATION = "documentation"


class ProcessingResult:
    """Standard result for knowledge processing operations."""

    def __init__(self, success: bool, message: str, data: dict[str, Any] | None = None) -> None:
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.utcnow()


@dataclass
class KnowledgeContext:
    """Context information for knowledge entries."""

    source_type: KnowledgeType
    source_identifier: str
    original_input: str
    processed_content: str
    metadata: dict[str, Any]
    relationships: list[str]
    tags: list[str]
    confidence: float = 0.8


class ContextDetector:
    """Intelligent context detection for different knowledge types."""

    def __init__(self) -> None:
        self.patterns = {
            KnowledgeType.WEBSITE: [
                r"^https?://[^\s]+$",  # URLs
                r"www\.[^\s]+",  # Domain patterns
                r"\.com$",  # TLDs
                r"http[s]?://",  # HTTP/HTTPS protocol
            ],
            KnowledgeType.FLAT_FILE: [
                r"^[A-Za-z]:\\.*",  # Windows paths
                r"^/",  # Unix paths
                r"\.(txt|md|py|js|json|xml)$",  # File extensions
                r"/",  # Path separators
                r"\\",  # Windows separators
            ],
            KnowledgeType.CONVERSATION: [
                r".*said:",  # Dialog patterns
                r".*asked:",  # Q&A patterns
                r".*replied:",  # Response patterns
                r".*thought:",  # Internal monologue
                r".*figured out:",  # Problem-solving
            ],
            KnowledgeType.CODE_SNIPPET: [
                r"^```",  # Code blocks
                r"def | class | import | from",  # Python patterns
                r"function|var|let|const",  # Programming patterns
                r"\{\s*.*\}",  # Object literals
            ],
            KnowledgeType.COMMAND_OUTPUT: [
                r"^\[.*\]",  # Command output brackets
                r"ERROR:",  # Error messages
                r"WARNING:",  # Warning messages
                r"SUCCESS:",  # Success messages
                r"Failed:",  # Failure messages
            ],
            KnowledgeType.ERROR_LOG: [
                r"Traceback",  # Python tracebacks
                r"Exception:",  # Exception messages
                r"Error:",  # Generic errors
                r"Failed:",  # Failure indicators
            ],
            KnowledgeType.DOCUMENTATION: [
                r"# ",  # Markdown headers
                r"TODO:",  # TODO items
                r"NOTE:",  # Notes
                r"IMPORTANT:",  # Important markers
            ],
        }

    def detect_type(self, content: str) -> tuple[KnowledgeType, float]:
        """Detect knowledge type with confidence scoring."""
        scores = dict.fromkeys(KnowledgeType, 0.0)

        for ktype, patterns in self.patterns.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    score += 1.0
            scores[ktype] = score / len(patterns)

        # Get the highest scoring type
        best_type = max(scores.items(), key=lambda x: x[1])
        return best_type[0] if best_type[1] > 0 else KnowledgeType.DIRECT_TEXT, best_type[1]


class ContentProcessor:
    """Smart content processing for different knowledge types."""

    def __init__(self) -> None:
        self.context_detector = ContextDetector()

    async def process_website(self, url_or_content: str) -> ProcessingResult:
        """Process website content with web scraping."""
        try:
            # Check if it's a URL or raw HTML
            if re.match(r"^https?://", url_or_content):
                # It's a URL - fetch content
                logger.info(f"Fetching content from URL: {url_or_content}")
                response = requests.get(url_or_content, timeout=30)
                response.raise_for_status()
                content = response.text
                source_id = url_or_content
            else:
                # It's raw HTML content
                content = url_or_content
                source_id = f"html_content_{hashlib.md5(content.encode()).hexdigest()[:8]}"

            # Parse HTML
            soup = BeautifulSoup(content, "html.parser")

            # Extract main content (remove navigation, ads, etc.)
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()

            # Extract title
            title = soup.title.string.strip() if soup.title else "No Title"

            # Extract main text content
            text_content = soup.get_text(separator=" ", strip=True)

            # Clean up text (excess whitespace)
            processed_content = " ".join(text_content.split())

            # Extract metadata
            metadata = {
                "url": url_or_content if re.match(r"^https?://", url_or_content) else None,
                "title": title,
                "domain": urlparse(url_or_content).netloc
                if re.match(r"^https?://", url_or_content)
                else None,
                "content_length": len(processed_content),
                "scraped_at": datetime.utcnow().isoformat(),
            }

            # Generate tags
            tags = ["website", "scraped"]
            if metadata.get("domain"):
                tags.append(f"domain:{metadata['domain']}")

            return ProcessingResult(
                success=True,
                message=f"Successfully processed website: {title}",
                data={
                    "content": processed_content,
                    "metadata": metadata,
                    "tags": tags,
                    "source_id": source_id,
                },
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                message=f"Failed to process website: {e}",
                data={"error": str(e), "traceback": traceback.format_exc()},
            )

    async def process_flat_file(self, file_path: str) -> ProcessingResult:
        """Process flat file content with appropriate parsing."""
        try:
            path = Path(file_path)

            if not path.exists():
                return ProcessingResult(
                    success=False,
                    message=f"File not found: {file_path}",
                )

            # Read file content
            async with aiofiles.open(path, encoding="utf-8") as f:
                content = await f.read()

            # Determine file type and process accordingly
            extension = path.suffix.lower()
            source_id = f"file_{path.name}_{hashlib.md5(content.encode()).hexdigest()[:8]}"

            metadata = {
                "file_path": str(path),
                "file_name": path.name,
                "file_size": len(content),
                "file_extension": extension,
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            }

            processed_content = content
            tags = ["file", extension.lstrip(".")]

            # Special processing for different file types
            if extension in [".md", ".markdown"]:
                processed_content = self._process_markdown(content)
                tags.extend(["markdown", "documentation"])
            elif extension in [".py", ".js", ".java", ".cpp"]:
                processed_content = self._process_code(content)
                tags.extend(["code", extension.lstrip(".")])
            elif extension == ".json":
                processed_content = self._process_json(content)
                tags.extend(["json", "structured"])

            return ProcessingResult(
                success=True,
                message=f"Successfully processed file: {path.name}",
                data={
                    "content": processed_content,
                    "metadata": metadata,
                    "tags": tags,
                    "source_id": source_id,
                },
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                message=f"Failed to process file: {e}",
                data={"error": str(e), "traceback": traceback.format_exc()},
            )

    def _process_markdown(self, content: str) -> str:
        """Extract main content from markdown."""
        # Remove front matter if present
        front_matter_pattern = r"^---\n.*?\n---\n"
        content = re.sub(front_matter_pattern, "", content, flags=re.MULTILINE | re.DOTALL)

        # Remove excessive whitespace
        return " ".join(content.split())

    def _process_code(self, content: str) -> str:
        """Extract meaningful content from code."""
        # Remove comments and excessive whitespace
        lines = []
        for line in content.split("\n"):
            line = line.strip()
            # Skip empty lines and single-line comments
            if line and not line.startswith("#") and not line.startswith("//"):
                lines.append(line)
        return " ".join(lines)

    def _process_json(self, content: str) -> str:
        """Extract meaningful content from JSON."""
        try:
            parsed = json.loads(content)
            return json.dumps(parsed, indent=2, separators=(",", ": "))
        except json.JSONDecodeError:
            # Fallback to raw text processing
            return " ".join(content.split())

    async def process_conversation(self, conversation: str) -> ProcessingResult:
        """Process conversation context with pattern recognition."""
        try:
            # Extract conversational patterns
            lines = conversation.split("\n")

            # Find key insights and solutions
            insights = []
            current_content = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detect speaker changes (basic pattern)
                if ":" in line and len(line.split(":")[0]) < 30:
                    line.split(":")[0].strip()
                    content = ":".join(line.split(":")[1:]).strip()
                else:
                    content = line

                # Look for problem-solving patterns
                if any(
                    keyword in content.lower()
                    for keyword in [
                        "figured out",
                        "realized",
                        "discovered",
                        "found",
                        "solution is",
                        "the issue was",
                    ]
                ):
                    insights.append(f"Insight: {content}")

                current_content.append(content)

            # Combine insights with main content
            processed_content = "\n".join(current_content)
            if insights:
                processed_content += "\n\nKey Insights:\n" + "\n".join(insights)

            metadata = {
                "conversation_length": len(conversation),
                "insights_count": len(insights),
                "speakers_detected": len(
                    {
                        line.split(":")[0]
                        for line in lines
                        if ":" in line and len(line.split(":")[0]) < 30
                    }
                ),
            }

            return ProcessingResult(
                success=True,
                message=f"Successfully processed conversation with {len(insights)} insights",
                data={
                    "content": processed_content,
                    "metadata": metadata,
                    "tags": ["conversation", "insights", "problem-solving"],
                    "source_id": f"conversation_{hashlib.md5(conversation.encode()).hexdigest()[:8]}",
                },
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                message=f"Failed to process conversation: {e}",
                data={"error": str(e), "traceback": traceback.format_exc()},
            )

    async def process_direct_text(self, text: str) -> ProcessingResult:
        """Process direct text input."""
        try:
            # Clean and structure the text
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            processed_content = " ".join(lines)

            metadata = {
                "input_length": len(text),
                "lines_count": len(lines),
                "processed_length": len(processed_content),
            }

            # Generate simple tags based on content
            tags = ["direct_input"]
            if "code" in processed_content.lower():
                tags.append("code")
            if "error" in processed_content.lower():
                tags.append("error")
            if "solution" in processed_content.lower():
                tags.append("solution")

            return ProcessingResult(
                success=True,
                message=f"Successfully processed direct text ({len(processed_content)} chars)",
                data={
                    "content": processed_content,
                    "metadata": metadata,
                    "tags": tags,
                    "source_id": f"direct_{hashlib.md5(text.encode()).hexdigest()[:8]}",
                },
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                message=f"Failed to process direct text: {e}",
                data={"error": str(e), "traceback": traceback.format_exc()},
            )


class CKSKnowledgeIntegration:
    """Main CKS integration orchestrator for intelligent knowledge ingestion."""

    def __init__(self, config: CKSConfig = None) -> None:
        """Initialize CKS knowledge integration."""
        self.config = config or CKSConfig()
        self.content_processor = ContentProcessor()
        self.context_detector = ContextDetector()

        if CKS_AVAILABLE:
            self.manager = KnowledgeManager(config)
            logger.info("CKS Knowledge Integration initialized successfully")
        else:
            self.manager = None
            logger.warning("CKS not available - using fallback mode")

    async def ingest_knowledge(
        self,
        input_data: str,
        category: str | None = None,
        title: str | None = None,
        user_context: str | None = None,
    ) -> dict[str, Any]:
        """Intelligent knowledge ingestion with automatic context detection."""
        start_time = time.time()

        try:
            # Detect input type
            detected_type, confidence = self.context_detector.detect_type(input_data)
            logger.info(
                f"Detected knowledge type: {detected_type.value} (confidence: {confidence:.2f})"
            )

            # Process content based on type
            if detected_type == KnowledgeType.WEBSITE:
                result = await self.content_processor.process_website(input_data)
            elif detected_type == KnowledgeType.FLAT_FILE:
                result = await self.content_processor.process_flat_file(input_data)
            elif detected_type == KnowledgeType.CONVERSATION:
                result = await self.content_processor.process_conversation(input_data)
            else:
                result = await self.content_processor.process_direct_text(input_data)

            if not result.success:
                return {
                    "state": "FAILED",
                    "return_code": 1,
                    "error": result.message,
                    "operation_time_ms": (time.time() - start_time) * 1000,
                }

            # Create enhanced context
            context = KnowledgeContext(
                source_type=detected_type,
                source_identifier=result.data.get("source_id", "unknown"),
                original_input=input_data,
                processed_content=result.data["content"],
                metadata=result.data["metadata"],
                relationships=[],
                tags=result.data["tags"],
                confidence=confidence,
            )

            # Extract semantic information
            semantic_info = await self._extract_semantic_info(context)
            context.metadata.update(semantic_info)

            # Generate smart title if not provided
            if not title:
                title = await self._generate_title(context)

            # Generate enhanced tags
            enhanced_tags = await self._generate_tags(context)
            context.tags.extend(enhanced_tags)

            # Add user context if provided
            if user_context:
                context.tags.append("user_context")
                context.metadata["user_context"] = user_context

            # Auto-categorize if not provided
            if not category:
                category = await self._auto_categorize(context)

            # Create knowledge entry
            if CKS_AVAILABLE and self.manager:
                entry = KnowledgeEntry(
                    category=category,
                    title=title,
                    content=context.processed_content,
                    tags=",".join(context.tags),
                    timestamp=datetime.utcnow(),
                )

                # Add rich metadata to content
                enhanced_content = self._enrich_content(entry, context)
                entry.content = enhanced_content

                # Store in CKS
                result = await self.manager.learn(entry)

                # Add relationship data
                if context.relationships:
                    await self._store_relationships(context.relationships, entry.id)

                operation_time = (time.time() - start_time) * 1000

                return {
                    "state": "VERIFIED",
                    "return_code": 0,
                    "entry_id": result["entry_id"],
                    "operation_time_ms": operation_time,
                    "knowledge_type": detected_type.value,
                    "confidence": confidence,
                    "auto_categorization": category != "manual",
                    "title_generated": not bool(title),
                    "semantic_enrichment": len(semantic_info) > 0,
                    "tags_enhanced": len(enhanced_tags) > 0,
                    "output": f"Successfully stored '{title}' in CKS with {len(context.tags)} tags",
                    "context": {
                        "type": detected_type.value,
                        "source": context.source_identifier,
                        "metadata": context.metadata,
                        "relationships": context.relationships,
                        "tags": context.tags,
                    },
                }
            # Fallback mode without CKS
            operation_time = (time.time() - start_time) * 1000
            return {
                "state": "DEGRADED",
                "return_code": 2,
                "operation_time_ms": operation_time,
                "knowledge_type": detected_type.value,
                "confidence": confidence,
                "warning": "CKS not available - using fallback mode",
                "processed_content": context.processed_content,
                "context": context.__dict__,
                "output": "Processed content but CKS integration unavailable",
            }

        except Exception as e:
            logger.exception(f"Error in knowledge ingestion: {e}")
            return {
                "state": "FAILED",
                "return_code": 3,
                "error": str(e),
                "operation_time_ms": (time.time() - start_time) * 1000,
                "traceback": traceback.format_exc(),
            }

    async def _extract_semantic_info(self, context: KnowledgeContext) -> dict[str, Any]:
        """Extract semantic information from content."""
        try:
            semantic_info = {}

            # Extract entities and concepts
            entities = self._extract_entities(context.processed_content)
            if entities:
                semantic_info["entities"] = entities

            # Extract key phrases
            key_phrases = self._extract_key_phrases(context.processed_content)
            if key_phrases:
                semantic_info["key_phrases"] = key_phrases

            # Extract technical terms
            technical_terms = self._extract_technical_terms(context.processed_content)
            if technical_terms:
                semantic_info["technical_terms"] = technical_terms

            return semantic_info

        except Exception as e:
            logger.warning(f"Error extracting semantic info: {e}")
            return {}

    def _extract_entities(self, content: str) -> list[str]:
        """Extract entities from content."""
        # Simple entity extraction (can be enhanced with NLP)
        entities = []

        # Email patterns
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        entities.extend(re.findall(email_pattern, content))

        # URL patterns
        url_pattern = r'https?://[^\s<>"\'\)]+'
        entities.extend(re.findall(url_pattern, content))

        # File path patterns
        file_pattern = r'\b(?:[A-Za-z]:\\|/)[^<>"\'\s]*\.(?:py|js|md|json|xml|txt|yaml|yml)\b'
        entities.extend(re.findall(file_pattern, content))

        return list(set(entities))

    def _extract_key_phrases(self, content: str) -> list[str]:
        """Extract key phrases from content."""
        # Simple key phrase extraction
        phrases = []

        # Common patterns
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

        return list(set(phrases))

    def _extract_technical_terms(self, content: str) -> list[str]:
        """Extract technical terms from content."""
        # Common technical term patterns
        tech_terms = [
            "API",
            "REST",
            "HTTP",
            "HTTPS",
            "JSON",
            "XML",
            "HTML",
            "CSS",
            "JavaScript",
            "Python",
            "TypeScript",
            "React",
            "Vue",
            "Angular",
            "Node.js",
            "Express",
            "SQL",
            "NoSQL",
            "database",
            "schema",
            "migration",
            "deployment",
            "Docker",
            "Kubernetes",
            "AWS",
            "Azure",
            "GCP",
            "CI/CD",
            "DevOps",
            "pytest",
            "testing",
            "coverage",
            "linting",
            "refactoring",
            "optimization",
        ]

        found_terms = []
        for term in tech_terms:
            if re.search(r"\b" + re.escape(term) + r"\b", content, re.IGNORECASE):
                found_terms.append(term)

        return found_terms

    async def _generate_title(self, context: KnowledgeContext) -> str:
        """Generate smart title based on context."""
        try:
            content = context.processed_content[:200]  # First 200 chars

            # Look for titles in the content
            title_patterns = [
                r"^#\s*(.+)$",  # Markdown headers
                r"Title:\s*(.+)",  # Explicit title
                r"Subject:\s*(.+)",  # Email subject
                r"ERROR:\s*(.+)",  # Error message title
                r"SUCCESS:\s*(.+)",  # Success message title
            ]

            for pattern in title_patterns:
                match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                if match:
                    return match.group(1).strip()

            # Generate title based on content type and metadata
            if context.source_type == KnowledgeType.WEBSITE:
                title = context.metadata.get("title", "Website Content")
            elif context.source_type == KnowledgeType.FLAT_FILE:
                title = f"{context.metadata.get('file_name', 'File')} Processing"
            elif context.source_type == KnowledgeType.CONVERSATION:
                title = "Conversation Analysis"
            else:
                title = "Knowledge Entry"

            # Add confidence indicator if low
            if context.confidence < 0.6:
                title += f" ({context.source_type.value})"

            return title

        except Exception as e:
            logger.warning(f"Error generating title: {e}")
            return "Knowledge Entry"

    async def _generate_tags(self, context: KnowledgeContext) -> list[str]:
        """Generate smart tags based on context."""
        tags = context.tags.copy()

        try:
            # Add source type tags
            tags.append(f"source:{context.source_type.value}")

            # Add confidence level
            if context.confidence > 0.8:
                tags.append("high_confidence")
            elif context.confidence < 0.5:
                tags.append("low_confidence")

            # Add file type tags if applicable
            if "file_extension" in context.metadata:
                ext = context.metadata["file_extension"]
                if ext:
                    tags.append(f"ext:{ext}")

            # Add domain tags for websites
            if "domain" in context.metadata:
                domain = context.metadata["domain"]
                if domain:
                    tags.append(f"domain:{domain}")

            # Add semantic info tags
            if "technical_terms" in context.metadata:
                for term in context.metadata["technical_terms"][:5]:  # Limit to top 5
                    tags.append(f"tech:{term.lower()}")

            # Add date-based tags
            current_date = datetime.utcnow().strftime("%Y-%m-%d")
            tags.append(f"date:{current_date}")

            # Add relationship tags
            tags.extend([f"rel:{rel}" for rel in context.relationships[:3]])  # Limit to 3

            return list(set(tags))

        except Exception as e:
            logger.warning(f"Error generating tags: {e}")
            return tags

    async def _auto_categorize(self, context: KnowledgeContext) -> str:
        """Automatically categorize knowledge based on context."""
        try:
            # Category mapping based on content type and metadata
            category_mapping = {
                KnowledgeType.WEBSITE: "web_scraping",
                KnowledgeType.FLAT_FILE: "file_processing",
                KnowledgeType.CONVERSATION: "conversation_analysis",
                KnowledgeType.CODE_SNIPPET: "code_pattern",
                KnowledgeType.ERROR_LOG: "error_analysis",
                KnowledgeType.DOCUMENTATION: "documentation",
            }

            # Use detected type as primary category
            primary_category = category_mapping.get(context.source_type, "general")

            # Refine based on content analysis
            content_lower = context.processed_content.lower()

            # Check for specific patterns
            if "security" in content_lower or "vulnerability" in content_lower:
                primary_category = "security"
            elif "performance" in content_lower or "optimization" in content_lower:
                primary_category = "performance"
            elif "database" in content_lower or "sql" in content_lower:
                primary_category = "database"
            elif "api" in content_lower or "rest" in content_lower:
                primary_category = "api_design"
            elif "ui" in content_lower or "interface" in content_lower:
                primary_category = "ui_design"
            elif "deployment" in content_lower or "ci/cd" in content_lower:
                primary_category = "devops"

            # Check file extension for specialized categories
            if "file_extension" in context.metadata:
                ext = context.metadata["file_extension"]
                if ext in [".py", ".js", ".ts", ".java"]:
                    primary_category = "programming"
                elif ext in [".md", ".rst", ".txt"]:
                    primary_category = "documentation"
                elif ext in [".json", ".yaml", ".yml"]:
                    primary_category = "data_format"
                elif ext in [".log", ".out"]:
                    primary_category = "log_analysis"

            return primary_category

        except Exception as e:
            logger.warning(f"Error auto-categorizing: {e}")
            return "general"

    def _enrich_content(self, entry: KnowledgeEntry, context: KnowledgeContext) -> str:
        """Enrich content with rich metadata and context."""
        try:
            enriched_parts = [
                f"**Title:** {entry.title}",
                f"**Category:** {entry.category}",
                f"**Source Type:** {context.source_type.value}",
                f"**Source:** {context.source_identifier}",
                f"**Confidence:** {context.confidence:.2f}",
                f"**Date:** {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "**Metadata:**",
                f"- File: {context.metadata.get('file_path', 'N/A')}",
                f"- Size: {context.metadata.get('content_length', 'N/A')} chars",
                "",
                "**Tags:**",
                f"- {', '.join(entry.tags.split(','))}",
                "",
                "**Content:**",
                entry.content,
            ]

            return "\n".join(enriched_parts)

        except Exception as e:
            logger.warning(f"Error enriching content: {e}")
            return entry.content

    async def _store_relationships(self, relationships: list[str], entry_id: int) -> None:
        """Store semantic relationships in CKS (placeholder for future implementation)."""
        # TODO: Implement relationship storage when CKS supports it
        logger.info(f"Would store relationships for entry {entry_id}: {relationships}")


# CLI interface
async def main() -> None:
    """Main CLI interface for CKS knowledge integration."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="CKS-Integrated Knowledge Ingestion")
    parser.add_argument("input", help="Input content, URL, or file path")
    parser.add_argument("--category", help="Knowledge category")
    parser.add_argument("--title", help="Knowledge entry title")
    parser.add_argument("--context", help="Additional user context")
    parser.add_argument("--test", action="store_true", help="Run in test mode")

    args = parser.parse_args()

    # Initialize CKS integration
    integration = CKSKnowledgeIntegration()

    try:
        # Read input from file if provided
        if args.test and Path(args.input).exists():
            async with aiofiles.open(args.input) as f:
                input_data = await f.read()
        else:
            input_data = args.input

        # Ingest knowledge
        result = await integration.ingest_knowledge(
            input_data=input_data,
            category=args.category,
            title=args.title,
            user_context=args.context,
        )

        print(f"\nResult: {result['state']}")
        print(f"Message: {result['output']}")

        if result["state"] == "VERIFIED":
            print(f"Entry ID: {result.get('entry_id', 'N/A')}")
            print(f"Operation Time: {result['operation_time_ms']:.1f}ms")
            print(f"Knowledge Type: {result['knowledge_type']}")
            print(f"Auto-Categorization: {result.get('auto_categorization', 'N/A')}")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
