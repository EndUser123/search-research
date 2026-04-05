#!/usr/bin/env python3
"""CKS Knowledge Query and Validation Utility.

Validates that orchestrator-observability knowledge is properly structured,
indexed, searchable for future CSF development activities.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class KnowledgeQueryValidator:
    """Validates and queries CKS knowledge artifacts."""

    def __init__(self, knowledge_dir: Path | None = None) -> None:
        """Initialize with knowledge artifacts directory."""
        self.knowledge_dir = knowledge_dir or Path(__file__).parent / "knowledge_artifacts"
        self.knowledge_files = {
            "research_findings": "research_findings.json",
            "integration_patterns": "integration_patterns.json",
            "performance_knowledge": "performance_knowledge.json",
            "risk_assessments": "risk_assessments.json",
            "cross_references": "cross_references.json",
            "knowledge_summary": "knowledge_summary.json",
        }
        self.cache = {}

    def load_knowledge(self, knowledge_type: str) -> dict[str, Any] | None:
        """Load knowledge from file with caching."""
        if knowledge_type in self.cache:
            return self.cache[knowledge_type]

        if knowledge_type not in self.knowledge_files:
            return None

        file_path = self.knowledge_dir / self.knowledge_files[knowledge_type]

        try:
            with open(file_path) as f:
                knowledge = json.load(f)
                self.cache[knowledge_type] = knowledge
                return knowledge
        except Exception as e:
            print(f"❌ Error loading {knowledge_type}: {e}")
            return None

    def validate_structure(self) -> dict[str, Any]:
        """Validate that all knowledge artifacts have proper structure."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_stats": {},
        }

        for knowledge_type, filename in self.knowledge_files.items():
            file_path = self.knowledge_dir / filename

            if not file_path.exists():
                validation_results["errors"].append(f"Missing file: {filename}")
                validation_results["valid"] = False
                continue

            try:
                knowledge = self.load_knowledge(knowledge_type)

                # Basic structure validation
                if not isinstance(knowledge, dict):
                    validation_results["errors"].append(f"{filename}: Not a dictionary")
                    validation_results["valid"] = False
                    continue

                # Check for expected top-level keys
                if knowledge_type in [
                    "research_findings",
                    "integration_patterns",
                    "risk_assessments",
                ]:
                    expected_key = knowledge_type
                    if expected_key not in knowledge:
                        validation_results["errors"].append(
                            f"{filename}: Missing expected key '{expected_key}'"
                        )
                        validation_results["valid"] = False
                    elif not isinstance(knowledge[expected_key], dict):
                        validation_results["errors"].append(
                            f"{filename}: {expected_key} is not a dictionary"
                        )
                        validation_results["valid"] = False

                # File statistics
                stat = file_path.stat()
                validation_results["file_stats"][filename] = {
                    "size_bytes": stat.st_size,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }

            except json.JSONDecodeError as e:
                validation_results["errors"].append(f"{filename}: JSON decode error - {e}")
                validation_results["valid"] = False
            except Exception as e:
                validation_results["errors"].append(f"{filename}: Unexpected error - {e}")
                validation_results["valid"] = False

        return validation_results

    def query_by_category(self, category: str) -> list[dict[str, Any]]:
        """Query knowledge items by category."""
        results = []

        # Search research findings
        research = self.load_knowledge("research_findings")
        if research and "research_findings" in research:
            for key, item in research["research_findings"].items():
                if item.get("category") == category:
                    results.append(
                        {
                            "type": "research_finding",
                            "id": key,
                            "title": item.get("title", ""),
                            "content": item.get("content", ""),
                            "source": item.get("source", ""),
                            "confidence": item.get("confidence", ""),
                            "tags": item.get("tags", []),
                        }
                    )

        return results

    def query_by_tags(self, tags: list[str]) -> list[dict[str, Any]]:
        """Query knowledge items by tags."""
        results = []

        # Search all knowledge types
        for knowledge_type in ["research_findings", "integration_patterns", "risk_assessments"]:
            knowledge = self.load_knowledge(knowledge_type)

            if knowledge and knowledge_type in knowledge:
                for key, item in knowledge[knowledge_type].items():
                    item_tags = item.get("tags", [])
                    if any(tag in item_tags for tag in tags):
                        results.append(
                            {
                                "type": knowledge_type.rstrip("s"),  # Remove plural 's'
                                "id": key,
                                "title": item.get("title", ""),
                                "description": item.get("description", ""),
                                "tags": item_tags,
                            }
                        )

        return results

    def query_integration_patterns(
        self, orchestrator_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Query integration patterns, optionally filtered by orchestrator type."""
        patterns = self.load_knowledge("integration_patterns")
        cross_refs = self.load_knowledge("cross_references")

        results = []

        if patterns and "integration_patterns" in patterns:
            for pattern_id, pattern in patterns["integration_patterns"].items():
                result = {
                    "id": pattern_id,
                    "title": pattern.get("title", ""),
                    "description": pattern.get("description", ""),
                    "benefits": pattern.get("benefits", []),
                    "drawbacks": pattern.get("drawbacks", []),
                    "use_cases": pattern.get("use_cases", []),
                    "tags": pattern.get("tags", []),
                    "implementation_code": pattern.get("implementation_code", ""),
                }

                # Add orchestrator-specific information if cross-references available
                if cross_refs and "cross_references" in cross_refs:
                    orchestrator_systems = cross_refs["cross_references"].get(
                        "orchestrator_systems", {}
                    )

                    if orchestrator_type:
                        # Filter for specific orchestrator type
                        if orchestrator_type in orchestrator_systems:
                            orchestrator_info = orchestrator_systems[orchestrator_type]
                            if orchestrator_info.get("recommended_pattern") == pattern_id:
                                result["recommended_for"] = orchestrator_type
                                result["integration_priority"] = orchestrator_info.get(
                                    "integration_priority"
                                )
                                result["complexity"] = orchestrator_info.get("complexity")
                    else:
                        # Show all orchestrators that recommend this pattern
                        recommended_for = []
                        for orch_name, orch_info in orchestrator_systems.items():
                            if orch_info.get("recommended_pattern") == pattern_id:
                                recommended_for.append(
                                    {
                                        "orchestrator": orch_name,
                                        "priority": orch_info.get("integration_priority"),
                                        "complexity": orch_info.get("complexity"),
                                    }
                                )
                        if recommended_for:
                            result["recommended_for"] = recommended_for

                results.append(result)

        return results

    def query_performance_data(self, metric_type: str | None = None) -> dict[str, Any]:
        """Query performance data, optionally filtered by metric type."""
        performance = self.load_knowledge("performance_knowledge")
        results = {}

        if performance and "performance_knowledge" in performance:
            perf_data = performance["performance_knowledge"]

            if metric_type:
                if metric_type in perf_data:
                    results[metric_type] = perf_data[metric_type]
            else:
                results = perf_data

        return results

    def query_risk_assessments(self, risk_level: str | None = None) -> list[dict[str, Any]]:
        """Query risk assessments, optionally filtered by risk level."""
        risks = self.load_knowledge("risk_assessments")
        results = []

        if risks and "risk_assessments" in risks:
            for risk_id, risk in risks["risk_assessments"].items():
                if risk_level and risk.get("risk_level") != risk_level:
                    continue

                results.append(
                    {
                        "id": risk_id,
                        "title": risk.get("title", ""),
                        "risk_level": risk.get("risk_level", ""),
                        "description": risk.get("description", ""),
                        "impact": risk.get("impact", ""),
                        "probability": risk.get("probability", ""),
                        "mitigation_strategies": risk.get("mitigation_strategies", []),
                        "detection_methods": risk.get("detection_methods", []),
                        "tags": risk.get("tags", []),
                    }
                )

        return results

    def get_related_knowledge(
        self, item_id: str, item_type: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Get knowledge items related to a specific item using cross-references."""
        cross_refs = self.load_knowledge("cross_references")
        related = {
            "findings": [],
            "patterns": [],
            "performance": [],
            "risks": [],
        }

        if not cross_refs or "cross_references" not in cross_refs:
            return related

        refs = cross_refs["cross_references"]

        # Find related items based on item type
        if item_type == "finding" and item_id in refs.get("findings_to_patterns", {}):
            pattern_ids = refs["findings_to_patterns"][item_id]
            for pattern_id in pattern_ids:
                patterns = self.load_knowledge("integration_patterns")
                if patterns and "integration_patterns" in patterns:
                    pattern = patterns["integration_patterns"].get(pattern_id)
                    if pattern:
                        related["patterns"].append(
                            {
                                "id": pattern_id,
                                "title": pattern.get("title", ""),
                                "type": "pattern",
                            }
                        )

        elif item_type == "pattern" and item_id in refs.get("patterns_to_performance", {}):
            perf_id = refs["patterns_to_performance"][item_id]
            performance = self.load_knowledge("performance_knowledge")
            if performance and "performance_knowledge" in performance:
                perf = performance["performance_knowledge"].get(perf_id)
                if perf:
                    related["performance"].append(
                        {
                            "id": perf_id,
                            "title": perf.get("title", ""),
                            "type": "performance_data",
                        }
                    )

        return related

    def search_knowledge(self, query: str) -> list[dict[str, Any]]:
        """Search across all knowledge items for text matches."""
        results = []
        query_lower = query.lower()

        for knowledge_type in ["research_findings", "integration_patterns", "risk_assessments"]:
            knowledge = self.load_knowledge(knowledge_type)

            if knowledge and knowledge_type in knowledge:
                for key, item in knowledge[knowledge_type].items():
                    # Search in title, description, and content
                    searchable_text = " ".join(
                        [
                            item.get("title", ""),
                            item.get("description", ""),
                            item.get("content", ""),
                            " ".join(item.get("tags", [])),
                        ]
                    ).lower()

                    if query_lower in searchable_text:
                        results.append(
                            {
                                "type": knowledge_type.rstrip("s"),
                                "id": key,
                                "title": item.get("title", ""),
                                "description": item.get("description", ""),
                                "match_context": self._get_match_context(query, item),
                                "tags": item.get("tags", []),
                            }
                        )

        return results

    def _get_match_context(self, query: str, item: dict[str, Any]) -> str:
        """Get context showing where the query matches in the item."""
        query_lower = query.lower()

        # Check different fields for the match
        for field in ["title", "description", "content"]:
            field_value = item.get(field, "")
            if query_lower in field_value.lower():
                return f"Found in {field}"

        # Check tags
        tags = item.get("tags", [])
        for tag in tags:
            if query_lower in tag.lower():
                return f"Found in tag: {tag}"

        return "Match found"

    def generate_knowledge_report(self) -> dict[str, Any]:
        """Generate comprehensive report on knowledge artifacts."""
        validation = self.validate_structure()

        report = {
            "report_generated": datetime.now().isoformat(),
            "validation": validation,
            "knowledge_summary": {},
            "query_capabilities": {
                "by_category": ["system_analysis", "observability", "patterns", "performance"],
                "by_tags": [
                    "orchestrator",
                    "observability",
                    "integration",
                    "performance",
                    "security",
                ],
                "by_risk_level": ["CRITICAL", "MODERATE", "LOW"],
                "search": "Full-text search across all knowledge items",
            },
            "integration_examples": [
                {
                    "scenario": "New orchestrator needs observability",
                    "query": "Find integration patterns for orchestrator systems",
                    "method": "query_integration_patterns()",
                },
                {
                    "scenario": "Performance concerns with observability",
                    "query": "Check performance impact and optimizations",
                    "method": "query_performance_data('observability_overhead')",
                },
                {
                    "scenario": "Security assessment needed",
                    "query": "Find critical risks and mitigations",
                    "method": "query_risk_assessments('CRITICAL')",
                },
            ],
        }

        # Add knowledge summary from file
        summary = self.load_knowledge("knowledge_summary")
        if summary and "knowledge_summary" in summary:
            report["knowledge_summary"] = summary["knowledge_summary"]

        return report


def main() -> None:
    """Main execution demonstrating knowledge querying capabilities."""
    print("🔍 CKS Knowledge Query and Validation")
    print("=" * 50)

    validator = KnowledgeQueryValidator()

    # Validate structure
    print("\n1️⃣  Validating Knowledge Structure...")
    validation = validator.validate_structure()

    if validation["valid"]:
        print("✅ All knowledge files have valid structure")
        print(f"📊 Total knowledge files: {len(validation['file_stats'])}")
        for filename, stats in validation["file_stats"].items():
            print(f"   - {filename}: {stats['size_kb']} KB")
    else:
        print("❌ Structure validation failed:")
        for error in validation["errors"]:
            print(f"   - {error}")

    # Demonstrate querying capabilities
    print("\n2️⃣  Query Demonstration...")

    # Query by category
    print("\n   📂 Research findings in 'patterns' category:")
    pattern_findings = validator.query_by_category("patterns")
    for finding in pattern_findings[:2]:  # Show first 2
        print(f"      - {finding['title']}")
        print(f"        Confidence: {finding['confidence']}")

    # Query integration patterns
    print("\n   🔧 Available Integration Patterns:")
    patterns = validator.query_integration_patterns()
    for pattern in patterns:
        print(f"      - {pattern['title']}")
        print(f"        Benefits: {', '.join(pattern['benefits'][:2])}")

    # Query performance data
    print("\n   ⚡ Performance Data Available:")
    performance = validator.query_performance_data()
    for metric_name, metric_data in performance.items():
        print(f"      - {metric_data.get('title', metric_name)}")

    # Query risks
    print("\n   ⚠️  Risk Assessments by Level:")
    for risk_level in ["CRITICAL", "MODERATE", "LOW"]:
        risks = validator.query_risk_assessments(risk_level)
        print(f"      {risk_level}: {len(risks)} risks")
        for risk in risks:
            print(f"        - {risk['title']}")

    # Search demonstration
    print("\n   🔍 Search Example ('integration'):")
    search_results = validator.search_knowledge("integration")
    print(f"      Found {len(search_results)} matching items")
    for result in search_results[:3]:  # Show first 3
        print(f"        - {result['title']} ({result['type']}) - {result['match_context']}")

    # Generate report
    print("\n3️⃣  Generating Knowledge Report...")
    report = validator.generate_knowledge_report()

    report_file = validator.knowledge_dir / "knowledge_validation_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print("✅ Knowledge validation complete!")
    print(f"📄 Detailed report saved: {report_file}")
    print("\n💡 Knowledge is properly structured and searchable for future CSF development!")


if __name__ == "__main__":
    main()
