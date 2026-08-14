"""CKS Documentation Manager.
========================

Optimal integration for ensuring documentation is stored and discoverable in CKS.

This module provides automated tools to:
- Store documentation in CKS with proper metadata
- Validate documentation completeness
- Enable cross-referencing between docs and code
- Maintain discoverability
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DocMetadata:
    """Metadata for documentation stored in CKS."""

    title: str
    category: str
    feature: str
    author: str
    created_at: datetime
    file_path: str
    doc_type: str  # 'user_guide', 'api_reference', 'pattern', 'rca', 'architecture'
    version: str
    tags: list[str]
    cross_references: list[str]
    file_hash: str


class CKSDocumentationManager:
    """Manages documentation storage in CKS with optimal discoverability."""

    def __init__(self) -> None:
        try:
            from .core.vector_manager import VectorKnowledgeManager

            self.cks = VectorKnowledgeManager()
            self.enabled = True
            logger.info("CKS Documentation Manager initialized")
        except Exception as e:
            logger.warning(f"CKS not available: {e}")
            self.enabled = False

    def store_documentation(
        self,
        doc_path: str,
        feature_name: str,
        doc_type: str = "user_guide",
        cross_references: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Store a documentation file in CKS with optimal metadata.

        Args:
            doc_path: Path to the documentation file
            feature_name: Name of the feature/component
            doc_type: Type of documentation
            cross_references: Related documents or code components
            tags: Searchable tags

        Returns:
            Success status

        """
        if not self.enabled:
            return False

        try:
            doc_path = Path(doc_path)
            if not doc_path.exists():
                logger.error(f"Documentation file not found: {doc_path}")
                return False

            # Read and process documentation
            with open(doc_path, encoding="utf-8") as f:
                content = f.read()

            # Generate metadata
            metadata = self._generate_metadata(
                doc_path,
                feature_name,
                doc_type,
                cross_references,
                tags,
            )

            # Create searchable summary
            summary = self._create_summary(content, metadata)

            # Store in CKS
            doc_id = f"{feature_name}_{doc_type}_{metadata['created_at'].strftime('%Y%m%d')}"

            success = self.cks.ingest(
                id=doc_id,
                text=summary,
                metadata={
                    "type": "documentation",
                    "category": metadata["category"],
                    "feature": feature_name,
                    "doc_type": doc_type,
                    "file_path": str(doc_path),
                    "title": metadata["title"],
                    "author": metadata["author"],
                    "version": metadata["version"],
                    "tags": metadata["tags"],
                    "cross_references": metadata["cross_references"],
                    "file_hash": metadata["file_hash"],
                    "content_length": len(content),
                    "section_count": self._count_sections(content),
                    "created_at": metadata["created_at"].isoformat(),
                },
            )

            if success:
                logger.info(f"Stored documentation in CKS: {doc_id}")
                # Store section-level metadata
                self._store_sections(content, metadata)

            return success

        except Exception as e:
            logger.exception(f"Failed to store documentation in CKS: {e}")
            return False

    def store_directory(
        self,
        docs_dir: str,
        feature_name: str,
        pattern: str = "*.md",
    ) -> dict[str, bool]:
        """Store an entire directory of documentation in CKS.

        Args:
            docs_dir: Directory containing documentation
            feature_name: Feature/component name
            pattern: File pattern to match

        Returns:
            Dictionary mapping file paths to success status

        """
        results = {}
        docs_dir = Path(docs_dir)

        for doc_file in docs_dir.glob(pattern):
            # Determine doc type from location
            doc_type = self._determine_doc_type(doc_file, docs_dir)

            # Extract cross-references from content
            cross_refs = self._extract_cross_references(doc_file)

            # Extract tags from content
            tags = self._extract_tags(doc_file)

            success = self.store_documentation(
                str(doc_file),
                feature_name,
                doc_type,
                cross_refs,
                tags,
            )
            results[str(doc_file)] = success

        logger.info(f"Stored {sum(results.values())} of {len(results)} docs in CKS")
        return results

    def validate_documentation_coverage(
        self,
        feature_name: str,
        required_docs: list[str],
    ) -> dict[str, Any]:
        """Validate that all required documentation exists in CKS.

        Args:
            feature_name: Name of feature to validate
            required_docs: List of required document types

        Returns:
            Validation results

        """
        if not self.enabled:
            return {"error": "CKS not available"}

        # Query CKS for feature documentation
        query = f"{feature_name} documentation"
        results = self.cks.search(query, limit=50)

        found_types = set()
        docs_found = []

        for result in results:
            if result["payload"].get("feature") == feature_name:
                doc_type = result["payload"].get("doc_type")
                if doc_type:
                    found_types.add(doc_type)
                    docs_found.append(
                        {
                            "doc_type": doc_type,
                            "title": result["payload"].get("title"),
                            "file_path": result["payload"].get("file_path"),
                            "score": result["score"],
                        }
                    )

        # Check requirements
        missing = set(required_docs) - found_types
        extra = found_types - set(required_docs)

        return {
            "feature": feature_name,
            "required_docs": required_docs,
            "found_docs": list(found_types),
            "missing_docs": list(missing),
            "extra_docs": list(extra),
            "coverage_percentage": (len(found_types) / len(required_docs)) * 100
            if required_docs
            else 100,
            "search_results": docs_found,
        }

    def _generate_metadata(
        self,
        doc_path: Path,
        feature_name: str,
        doc_type: str,
        cross_references: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> DocMetadata:
        """Generate metadata for documentation."""
        # Extract title from file
        title = self._extract_title(doc_path)

        # Determine category
        category = self._determine_category(doc_type)

        # Generate file hash
        file_hash = self._generate_file_hash(doc_path)

        return DocMetadata(
            title=title,
            category=category,
            feature=feature_name,
            author="CWO12 Workflow System",
            created_at=datetime.now(),
            file_path=str(doc_path),
            doc_type=doc_type,
            version="1.0",
            tags=tags or [],
            cross_references=cross_references or [],
            file_hash=file_hash,
        )

    def _create_summary(self, content: str, metadata: DocMetadata) -> str:
        """Create searchable summary for CKS."""
        # Extract key sections
        sections = self._extract_key_sections(content)

        summary_parts = [
            f"Documentation: {metadata.title}",
            f"Feature: {metadata.feature}",
            f"Type: {metadata.doc_type}",
            f"Category: {metadata.category}",
            f"Sections: {', '.join(sections[:5])}",  # First 5 sections
        ]

        if metadata.tags:
            summary_parts.append(f"Tags: {', '.join(metadata.tags)}")

        if metadata.cross_references:
            summary_parts.append(f"References: {', '.join(metadata.cross_references)}")

        # Add content preview (first 500 chars)
        content_preview = content.replace("\n", " ")[:500]
        summary_parts.append(f"Content: {content_preview}...")

        return " | ".join(summary_parts)

    def _store_sections(self, content: str, metadata: DocMetadata) -> None:
        """Store individual sections in CKS for detailed search."""
        sections = self._parse_sections(content)

        for i, (title, section_content) in enumerate(sections):
            if len(section_content.strip()) > 50:  # Only store substantial sections
                section_id = (
                    f"{metadata.feature}_section_{i}_{metadata.created_at.strftime('%Y%m%d')}"
                )

                self.cks.ingest(
                    id=section_id,
                    text=f"Section: {title}\n\n{section_content}",
                    metadata={
                        "type": "documentation_section",
                        "feature": metadata.feature,
                        "section_title": title,
                        "section_number": i,
                        "doc_title": metadata.title,
                        "doc_type": metadata.doc_type,
                        "created_at": metadata.created_at.isoformat(),
                    },
                )

    def _extract_title(self, doc_path: Path) -> str:
        """Extract title from documentation file."""
        try:
            with open(doc_path, encoding="utf-8") as f:
                first_lines = f.readlines()[:10]

            # Look for first H1 or title
            for line in first_lines:
                if line.startswith("# "):
                    return line[2:].strip()
                if line.strip().startswith("Title:"):
                    return line.split(":", 1)[1].strip()

            # Fallback to filename
            return doc_path.stem.replace("_", " ").title()
        except:
            return doc_path.stem

    def _determine_category(self, doc_type: str) -> str:
        """Determine documentation category."""
        categories = {
            "user_guide": "user_guide",
            "api_reference": "api_reference",
            "pattern": "pattern",
            "rca": "rca",
            "architecture": "architecture",
            "implementation": "implementation",
            "configuration": "configuration",
            "troubleshooting": "troubleshooting",
            "examples": "examples",
        }
        return categories.get(doc_type, "documentation")

    def _determine_doc_type(self, doc_file: Path, base_dir: Path) -> str:
        """Determine document type from file location."""
        relative_path = doc_file.relative_to(base_dir)

        if "api" in str(relative_path):
            return "api_reference"
        if "guides" in str(relative_path):
            if "integration" in str(relative_path):
                return "integration_guide"
            if "configuration" in str(relative_path):
                return "configuration"
            return "user_guide"
        if "examples" in str(relative_path):
            return "examples"
        if "pattern" in doc_file.stem.lower():
            return "pattern"
        if "rca" in doc_file.stem.lower():
            return "rca"
        if "architecture" in doc_file.stem.lower():
            return "architecture"
        return "user_guide"

    def _extract_cross_references(self, doc_file: Path) -> list[str]:
        """Extract cross-references from documentation."""
        refs = []

        try:
            with open(doc_file, encoding="utf-8") as f:
                content = f.read()

            # Look for common reference patterns
            import re

            # File references
            file_refs = re.findall(r"`([^`]+\.py)`", content)
            refs.extend([ref.replace("\\", "") for ref in file_refs])

            # Class/function references
            code_refs = re.findall(r"`([^`]+)`", content)
            refs.extend([ref for ref in code_refs if "." in ref and not ref.endswith(".py")])

            # See Also references
            see_also = re.findall(r"See Also: (.+)", content)
            refs.extend([ref.strip() for ref in see_also])

        except Exception as e:
            logger.debug(f"Could not extract cross-references: {e}")

        return list(set(refs))  # Remove duplicates

    def _extract_tags(self, doc_file: Path) -> list[str]:
        """Extract tags from documentation."""
        tags = []

        # Extract from filename
        tags.extend(doc_file.stem.lower().split("_"))

        # Extract from path
        for part in doc_file.parts:
            if len(part) > 2:
                tags.append(part.lower())

        # Common documentation tags
        doc_tags = ["guide", "tutorial", "reference", "api", "example", "howto"]
        tags.extend(doc_tags)

        return list(set(tags))

    def _extract_key_sections(self, content: str) -> list[str]:
        """Extract key section titles from content."""
        sections = []

        for line in content.split("\n"):
            if line.startswith("# "):
                sections.append(line[2:].strip())
                if len(sections) >= 10:  # Limit to first 10
                    break

        return sections

    def _parse_sections(self, content: str) -> list[tuple]:
        """Parse markdown sections."""
        sections = []
        current_title = "Introduction"
        current_content = []

        for line in content.split("\n"):
            if line.startswith("# "):
                # Save previous section
                if current_content:
                    sections.append((current_title, "\n".join(current_content)))
                # Start new section
                current_title = line[2:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Add last section
        if current_content:
            sections.append((current_title, "\n".join(current_content)))

        return sections

    def _count_sections(self, content: str) -> int:
        """Count number of sections in documentation."""
        return len([line for line in content.split("\n") if line.startswith("# ")])

    def _generate_file_hash(self, doc_path: Path) -> str:
        """Generate hash of file for change detection."""
        import hashlib

        try:
            with open(doc_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return "unknown"

    def query_documentation(
        self,
        query: str,
        feature: str | None = None,
        doc_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Query documentation from CKS."""
        if not self.enabled:
            return []

        # Build query filters
        metadata_filters = {"type": "documentation"}
        if feature:
            metadata_filters["feature"] = feature
        if doc_type:
            metadata_filters["doc_type"] = doc_type

        # For now, return search results
        # In a full implementation, this would use CKS query filters
        results = self.cks.search(query, limit=limit)

        # Filter by metadata
        filtered_results = []
        for result in results:
            payload = result.get("payload", {})
            match = True

            for key, value in metadata_filters.items():
                if payload.get(key) != value:
                    match = False
                    break

            if match:
                filtered_results.append(result)

        return filtered_results


# Convenience functions for common operations


def store_documentation_directory(docs_dir: str, feature_name: str):
    """Store entire documentation directory in CKS."""
    manager = CKSDocumentationManager()
    return manager.store_directory(docs_dir, feature_name)


def validate_documentation(feature_name: str, required_docs: list[str]):
    """Validate documentation completeness in CKS."""
    manager = CKSDocumentationManager()
    return manager.validate_documentation_coverage(feature_name, required_docs)


def search_documentation(query: str, **filters):
    """Search documentation in CKS."""
    manager = CKSDocumentationManager()
    return manager.query_documentation(query, **filters)
