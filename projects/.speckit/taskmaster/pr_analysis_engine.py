#!/usr/bin/env python3
"""
PR Analysis Engine for TaskMaster GitHub Integration
Analyzes pull requests for automated task creation and CWO12 compliance validation
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class PRAnalysisResult:
    """Result of PR analysis"""

    task_suggestions: list[dict[str, Any]]
    complexity_score: float
    risk_level: str
    estimated_tasks: int
    cwo12_compliance_issues: list[str]
    recommendations: list[str]
    metadata: dict[str, Any]


@dataclass
class FileChangeAnalysis:
    """Analysis of file changes in PR"""

    file_path: str
    change_type: str  # added, modified, deleted
    lines_added: int
    lines_deleted: int
    file_type: str
    complexity_impact: str
    testing_required: bool
    documentation_required: bool


class PRAnalysisEngine:
    """Advanced PR analysis engine for task creation"""

    def __init__(self, github_token: str):
        self.github_token = github_token
        self.session: aiohttp.ClientSession | None = None

        # File type configurations
        self.file_type_config = {
            "python": {
                "extensions": [".py"],
                "complexity_weight": 1.2,
                "testing_required": True,
                "documentation_patterns": [r"def\s+\w+", r"class\s+\w+"],
            },
            "javascript": {
                "extensions": [".js", ".jsx", ".ts", ".tsx"],
                "complexity_weight": 1.1,
                "testing_required": True,
                "documentation_patterns": [
                    r"function\s+\w+",
                    r"class\s+\w+",
                    r"interface\s+\w+",
                ],
            },
            "config": {
                "extensions": [".json", ".yaml", ".yml", ".toml", ".ini", ".conf"],
                "complexity_weight": 0.5,
                "testing_required": False,
                "documentation_patterns": [],
            },
            "documentation": {
                "extensions": [".md", ".rst", ".txt", ".doc"],
                "complexity_weight": 0.3,
                "testing_required": False,
                "documentation_patterns": [],
            },
            "database": {
                "extensions": [".sql", ".db", ".sqlite"],
                "complexity_weight": 1.5,
                "testing_required": True,
                "documentation_patterns": [r"CREATE\s+TABLE", r"ALTER\s+TABLE"],
            },
            "css": {
                "extensions": [".css", ".scss", ".sass", ".less"],
                "complexity_weight": 0.7,
                "testing_required": False,
                "documentation_patterns": [],
            },
            "shell": {
                "extensions": [".sh", ".bash", ".zsh", ".fish"],
                "complexity_weight": 0.8,
                "testing_required": True,
                "documentation_patterns": [],
            },
        }

        # Task generation patterns
        self.task_patterns = {
            "bug_fix": {
                "keywords": ["fix", "bug", "error", "issue", "problem", "resolve"],
                "task_types": ["bug", "testing"],
                "priority_keywords": ["critical", "urgent", "security"],
            },
            "feature": {
                "keywords": ["feature", "add", "new", "implement", "create"],
                "task_types": ["feature", "documentation"],
                "priority_keywords": ["enhancement", "improvement"],
            },
            "refactor": {
                "keywords": [
                    "refactor",
                    "cleanup",
                    "improve",
                    "optimize",
                    "restructure",
                ],
                "task_types": ["refactor", "testing"],
                "priority_keywords": ["technical_debt", "maintainability"],
            },
            "security": {
                "keywords": [
                    "security",
                    "vulnerability",
                    "auth",
                    "permission",
                    "safety",
                ],
                "task_types": ["security"],
                "priority_keywords": ["critical", "high", "urgent"],
            },
            "performance": {
                "keywords": ["performance", "speed", "optimize", "fast", "efficient"],
                "task_types": ["performance"],
                "priority_keywords": ["optimization", "improvement"],
            },
            "testing": {
                "keywords": ["test", "spec", "coverage", "qa", "verify"],
                "task_types": ["testing"],
                "priority_keywords": ["quality", "reliability"],
            },
            "documentation": {
                "keywords": ["docs", "documentation", "readme", "guide", "manual"],
                "task_types": ["documentation"],
                "priority_keywords": ["clarity", "onboarding"],
            },
        }

        # CWO12 compliance patterns
        self.cwo12_patterns = {
            "evidence_required": [
                r"(?i)no\s+evidence",
                r"(?i)missing\s+proof",
                r"(?i)unverified",
                r"(?i)needs\s+validation",
            ],
            "constitutional_violations": [
                r"(?i)bypass\s+validation",
                r"(?i)skip\s+check",
                r"(?i)override\s+rule",
                r"(?i)ignore\s+compliance",
            ],
            "documentation_required": [
                r"(?i)new\s+feature",
                r"(?i)api\s+change",
                r"(?i)breaking\s+change",
                r"(?i)schema\s+change",
            ],
        }

    async def analyze_pr(
        self, pr_data: dict[str, Any], repo_full_name: str
    ) -> PRAnalysisResult:
        """
        Comprehensive PR analysis for task creation
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Extract basic PR information
            title = pr_data.get("title", "")
            description = pr_data.get("body", "")
            labels = [label.get("name", "") for label in pr_data.get("labels", [])]
            pr_number = pr_data.get("number")

            # Get file changes
            files_changed = await self.get_pr_files(repo_full_name, pr_number)
            file_analysis = [self.analyze_file_change(file) for file in files_changed]

            # Generate task suggestions
            task_suggestions = await self.generate_task_suggestions(
                title, description, labels, file_analysis
            )

            # Calculate complexity and risk
            complexity_score = self.calculate_complexity_score(
                file_analysis, title, description
            )
            risk_level = self.assess_risk_level(complexity_score, file_analysis, labels)
            estimated_tasks = len(task_suggestions)

            # Check CWO12 compliance
            compliance_issues = self.check_cwo12_compliance(
                title, description, file_analysis
            )

            # Generate recommendations
            recommendations = self.generate_recommendations(
                complexity_score, risk_level, file_analysis, compliance_issues
            )

            # Prepare metadata
            metadata = {
                "analysis_timestamp": datetime.now().isoformat(),
                "pr_number": pr_number,
                "files_analyzed": len(file_analysis),
                "total_lines_added": sum(f.lines_added for f in file_analysis),
                "total_lines_deleted": sum(f.lines_deleted for f in file_analysis),
                "file_types_affected": list({f.file_type for f in file_analysis}),
                "labels": labels,
            }

            return PRAnalysisResult(
                task_suggestions=task_suggestions,
                complexity_score=complexity_score,
                risk_level=risk_level,
                estimated_tasks=estimated_tasks,
                cwo12_compliance_issues=compliance_issues,
                recommendations=recommendations,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error analyzing PR: {e}", exc_info=True)
            raise

    async def get_pr_files(
        self, repo_full_name: str, pr_number: int
    ) -> list[dict[str, Any]]:
        """Get file changes for a PR"""
        try:
            url = (
                f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"
            )
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get PR files: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error getting PR files: {e}")
            return []

    def analyze_file_change(self, file_data: dict[str, Any]) -> FileChangeAnalysis:
        """Analyze individual file change"""
        file_path = file_data.get("filename", "")
        change_type = file_data.get("status", "modified")
        lines_added = file_data.get("additions", 0)
        lines_deleted = file_data.get("deletions", 0)

        # Determine file type
        file_type = self.determine_file_type(file_path)

        # Get file type configuration
        config = self.file_type_config.get(
            file_type,
            {
                "complexity_weight": 1.0,
                "testing_required": False,
                "documentation_patterns": [],
            },
        )

        # Assess complexity impact
        complexity_impact = self.assess_complexity_impact(
            lines_added, lines_deleted, config["complexity_weight"]
        )

        # Determine if testing is required
        testing_required = config["testing_required"] and (
            lines_added > 10 or change_type == "added"
        )

        # Determine if documentation is required
        documentation_required = self.requires_documentation(
            file_path, change_type, config["documentation_patterns"]
        )

        return FileChangeAnalysis(
            file_path=file_path,
            change_type=change_type,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            file_type=file_type,
            complexity_impact=complexity_impact,
            testing_required=testing_required,
            documentation_required=documentation_required,
        )

    def determine_file_type(self, file_path: str) -> str:
        """Determine file type from path"""
        file_ext = Path(file_path).suffix.lower()

        for file_type, config in self.file_type_config.items():
            if file_ext in config["extensions"]:
                return file_type

        return "unknown"

    def assess_complexity_impact(
        self, lines_added: int, lines_deleted: int, weight: float
    ) -> str:
        """Assess complexity impact of file changes"""
        total_changes = lines_added + lines_deleted
        weighted_changes = total_changes * weight

        if weighted_changes > 500:
            return "high"
        elif weighted_changes > 100:
            return "medium"
        elif weighted_changes > 20:
            return "low"
        else:
            return "minimal"

    def requires_documentation(
        self, file_path: str, change_type: str, patterns: list[str]
    ) -> bool:
        """Determine if documentation is required for file change"""
        # Check if it's a new file with documentation patterns
        if change_type == "added" and patterns:
            return True

        # Check for configuration or schema files
        if any(
            pattern in file_path.lower()
            for pattern in ["config", "schema", "api", "model"]
        ):
            return True

        # Check for README or documentation files
        if file_path.lower().endswith((".md", ".rst", ".txt")):
            return False  # This IS documentation

        return False

    async def generate_task_suggestions(
        self,
        title: str,
        description: str,
        labels: list[str],
        file_analysis: list[FileChangeAnalysis],
    ) -> list[dict[str, Any]]:
        """Generate task suggestions based on PR analysis"""
        suggestions = []

        # Analyze PR content for patterns
        content_text = (title + " " + description).lower()

        # Generate tasks based on detected patterns
        for pattern_name, pattern_config in self.task_patterns.items():
            if any(keyword in content_text for keyword in pattern_config["keywords"]):
                task_suggestion = self.create_task_suggestion(
                    pattern_name,
                    pattern_config,
                    title,
                    description,
                    labels,
                    file_analysis,
                )
                suggestions.append(task_suggestion)

        # Generate tasks based on file analysis
        file_tasks = self.generate_file_based_tasks(file_analysis, title)
        suggestions.extend(file_tasks)

        # Generate testing tasks if needed
        testing_tasks = self.generate_testing_tasks(file_analysis, title, description)
        suggestions.extend(testing_tasks)

        # Generate documentation tasks if needed
        documentation_tasks = self.generate_documentation_tasks(
            file_analysis, title, description
        )
        suggestions.extend(documentation_tasks)

        # Generate review tasks
        review_tasks = self.generate_review_tasks(file_analysis, title, description)
        suggestions.extend(review_tasks)

        return suggestions

    def create_task_suggestion(
        self,
        pattern_name: str,
        pattern_config: dict[str, Any],
        title: str,
        description: str,
        labels: list[str],
        file_analysis: list[FileChangeAnalysis],
    ) -> dict[str, Any]:
        """Create a task suggestion based on detected pattern"""
        base_priority = "medium"

        # Check for priority keywords
        text = (title + " " + description).lower()
        for priority_keyword in pattern_config["priority_keywords"]:
            if priority_keyword in text:
                if priority_keyword in ["critical", "urgent", "security"]:
                    base_priority = "critical"
                elif priority_keyword in ["high", "important"]:
                    base_priority = "high"
                elif priority_keyword in ["low", "minor"]:
                    base_priority = "low"
                break

        # Determine task type
        task_type = (
            pattern_config["task_types"][0]
            if pattern_config["task_types"]
            else "development"
        )

        # Generate acceptance criteria
        acceptance_criteria = self.generate_acceptance_criteria(
            pattern_name, description
        )

        # Generate metadata
        metadata = {
            "pattern_detected": pattern_name,
            "auto_generated": True,
            "source_pr": title,
            "affected_files": [f.file_path for f in file_analysis],
            "complexity_factors": [f.complexity_impact for f in file_analysis],
        }

        return {
            "title": f"{pattern_name.replace('_', ' ').title()}: {title}",
            "description": f"Automated task created from PR analysis:\n\n{description}",
            "task_type": task_type,
            "priority": base_priority,
            "phase": "development",
            "acceptance_criteria": acceptance_criteria,
            "tags": ["github", "automated", pattern_name],
            "estimated_duration": self.estimate_task_duration(
                task_type, base_priority, file_analysis
            ),
            "metadata": metadata,
        }

    def generate_file_based_tasks(
        self, file_analysis: list[FileChangeAnalysis], title: str
    ) -> list[dict[str, Any]]:
        """Generate tasks based on file analysis"""
        tasks = []

        # Group by file type
        file_type_groups = {}
        for file in file_analysis:
            if file.file_type not in file_type_groups:
                file_type_groups[file.file_type] = []
            file_type_groups[file.file_type].append(file)

        # Generate tasks for each file type group
        for file_type, files in file_type_groups.items():
            if file_type in ["python", "javascript", "database"]:
                # Code review task
                tasks.append(
                    {
                        "title": f"Code Review: {file_type.title()} Changes",
                        "description": f"Review {len(files)} {file_type} file changes for quality and standards compliance",
                        "task_type": "code_review",
                        "priority": "medium",
                        "phase": "testing",
                        "acceptance_criteria": [
                            "All code follows coding standards",
                            "No security vulnerabilities detected",
                            "Performance impact assessed",
                            "Unit tests added where required",
                        ],
                        "tags": ["code_review", file_type, "automated"],
                        "estimated_duration": len(files) * 30,  # 30 minutes per file
                        "metadata": {
                            "file_type": file_type,
                            "files_count": len(files),
                            "files": [f.file_path for f in files],
                        },
                    }
                )

        return tasks

    def generate_testing_tasks(
        self, file_analysis: list[FileChangeAnalysis], title: str, description: str
    ) -> list[dict[str, Any]]:
        """Generate testing-related tasks"""
        tasks = []

        # Check if testing is required
        files_requiring_tests = [f for f in file_analysis if f.testing_required]
        if files_requiring_tests:
            tasks.append(
                {
                    "title": "Add Tests for Code Changes",
                    "description": f"Write unit tests for {len(files_requiring_tests)} modified files",
                    "task_type": "testing",
                    "priority": "high",
                    "phase": "testing",
                    "acceptance_criteria": [
                        "Unit tests written for all new functionality",
                        "Test coverage meets project standards",
                        "All tests pass",
                        "Edge cases considered",
                    ],
                    "tags": ["testing", "unit_tests", "automated"],
                    "estimated_duration": len(files_requiring_tests)
                    * 60,  # 1 hour per file
                    "metadata": {
                        "files_requiring_tests": [
                            f.file_path for f in files_requiring_tests
                        ]
                    },
                }
            )

        # Integration testing task
        if len(files_requiring_tests) > 1:
            tasks.append(
                {
                    "title": "Integration Testing",
                    "description": "Perform integration testing for changes across multiple files",
                    "task_type": "testing",
                    "priority": "medium",
                    "phase": "testing",
                    "acceptance_criteria": [
                        "Integration tests written",
                        "Cross-file interactions tested",
                        "API endpoints tested end-to-end",
                        "Database migrations tested",
                    ],
                    "tags": ["testing", "integration", "automated"],
                    "estimated_duration": 120,  # 2 hours
                    "metadata": {
                        "test_type": "integration",
                        "file_count": len(files_requiring_tests),
                    },
                }
            )

        return tasks

    def generate_documentation_tasks(
        self, file_analysis: list[FileChangeAnalysis], title: str, description: str
    ) -> list[dict[str, Any]]:
        """Generate documentation-related tasks"""
        tasks = []

        # Check if documentation is required
        files_requiring_docs = [f for f in file_analysis if f.documentation_required]
        if files_requiring_docs:
            tasks.append(
                {
                    "title": "Update Documentation",
                    "description": f"Update documentation for {len(files_requiring_docs)} modified files",
                    "task_type": "documentation",
                    "priority": "medium",
                    "phase": "deployment",
                    "acceptance_criteria": [
                        "API documentation updated",
                        "Code comments added where necessary",
                        "README files updated",
                        "Change log updated",
                    ],
                    "tags": ["documentation", "automated"],
                    "estimated_duration": len(files_requiring_docs)
                    * 30,  # 30 minutes per file
                    "metadata": {
                        "files_requiring_docs": [
                            f.file_path for f in files_requiring_docs
                        ]
                    },
                }
            )

        return tasks

    def generate_review_tasks(
        self, file_analysis: list[FileChangeAnalysis], title: str, description: str
    ) -> list[dict[str, Any]]:
        """Generate code review and security review tasks"""
        tasks = []

        # Security review task
        high_risk_files = [
            f for f in file_analysis if f.complexity_impact in ["high", "medium"]
        ]
        if high_risk_files:
            tasks.append(
                {
                    "title": "Security Review",
                    "description": f"Perform security review for {len(high_risk_files)} high-impact file changes",
                    "task_type": "security",
                    "priority": "high",
                    "phase": "testing",
                    "acceptance_criteria": [
                        "Security vulnerabilities identified and addressed",
                        "Authentication/authorization reviewed",
                        "Data handling validated",
                        "Input sanitization verified",
                    ],
                    "tags": ["security", "review", "automated"],
                    "estimated_duration": len(high_risk_files)
                    * 45,  # 45 minutes per file
                    "metadata": {
                        "high_risk_files": [f.file_path for f in high_risk_files]
                    },
                }
            )

        return tasks

    def generate_acceptance_criteria(
        self, pattern_name: str, description: str
    ) -> list[str]:
        """Generate acceptance criteria based on pattern and PR description"""
        base_criteria = {
            "bug_fix": [
                "Bug reproduction verified",
                "Fix implemented and tested",
                "No regressions introduced",
                "Root cause documented",
            ],
            "feature": [
                "Feature requirements implemented",
                "User acceptance criteria met",
                "Feature tested end-to-end",
                "Documentation updated",
            ],
            "refactor": [
                "Code quality improved",
                "Functionality preserved",
                "Performance maintained or improved",
                "Tests updated as needed",
            ],
            "security": [
                "Security vulnerability addressed",
                "Attack surface reduced",
                "Security tests added",
                "Compliance verified",
            ],
            "performance": [
                "Performance improvements measured",
                "Benchmarks established",
                "No functionality degradation",
                "Performance monitoring added",
            ],
            "testing": [
                "Test coverage increased",
                "Test cases comprehensive",
                "All tests pass",
                "Test maintenance documented",
            ],
            "documentation": [
                "Documentation accurate and complete",
                "Examples provided",
                "User guide updated",
                "Technical specifications updated",
            ],
        }

        return base_criteria.get(
            pattern_name,
            [
                "Requirements fully implemented",
                "Quality standards met",
                "Testing completed",
                "Documentation updated",
            ],
        )

    def estimate_task_duration(
        self, task_type: str, priority: str, file_analysis: list[FileChangeAnalysis]
    ) -> int:
        """Estimate task duration in hours"""
        base_durations = {
            "bug": 8,
            "feature": 16,
            "refactor": 12,
            "security": 20,
            "performance": 16,
            "testing": 6,
            "documentation": 4,
            "code_review": 4,
            "development": 10,
        }

        priority_multipliers = {"critical": 1.5, "high": 1.2, "medium": 1.0, "low": 0.8}

        # Calculate complexity factor
        complexity_factor = 1.0
        high_complexity_files = [
            f for f in file_analysis if f.complexity_impact == "high"
        ]
        if high_complexity_files:
            complexity_factor = 1.3
        elif any(f.complexity_impact == "medium" for f in file_analysis):
            complexity_factor = 1.1

        base_duration = base_durations.get(task_type, 10)
        priority_multiplier = priority_multipliers.get(priority, 1.0)

        return int(base_duration * priority_multiplier * complexity_factor)

    def calculate_complexity_score(
        self, file_analysis: list[FileChangeAnalysis], title: str, description: str
    ) -> float:
        """Calculate overall complexity score (0.0 - 1.0)"""
        base_score = 0.0

        # File change complexity
        for file in file_analysis:
            file_score = 0.0

            # Lines changed
            total_lines = file.lines_added + file.lines_deleted
            if total_lines > 500:
                file_score += 0.3
            elif total_lines > 200:
                file_score += 0.2
            elif total_lines > 50:
                file_score += 0.1

            # File type complexity
            type_weights = {
                "database": 0.2,
                "python": 0.15,
                "javascript": 0.12,
                "config": 0.05,
                "documentation": 0.02,
            }
            file_score += type_weights.get(file.file_type, 0.1)

            # Change type
            if file.change_type == "added":
                file_score += 0.1
            elif file.change_type == "deleted":
                file_score += 0.05

            base_score += file_score

        # Normalize by number of files
        if file_analysis:
            base_score = min(base_score / len(file_analysis), 1.0)

        # Text-based complexity indicators
        text = (title + " " + description).lower()
        complexity_keywords = [
            "complex",
            "difficult",
            "challenging",
            "refactor",
            "rewrite",
        ]
        keyword_bonus = sum(0.05 for keyword in complexity_keywords if keyword in text)

        final_score = min(base_score + keyword_bonus, 1.0)
        return round(final_score, 2)

    def assess_risk_level(
        self,
        complexity_score: float,
        file_analysis: list[FileChangeAnalysis],
        labels: list[str],
    ) -> str:
        """Assess risk level based on complexity and other factors"""
        # Base risk from complexity
        if complexity_score >= 0.8:
            base_risk = "critical"
        elif complexity_score >= 0.6:
            base_risk = "high"
        elif complexity_score >= 0.4:
            base_risk = "medium"
        else:
            base_risk = "low"

        # Adjust based on file types
        high_risk_files = [
            f for f in file_analysis if f.file_type in ["database", "config", "python"]
        ]
        if len(high_risk_files) > 2:
            if base_risk in ["low", "medium"]:
                base_risk = "high"
            elif base_risk == "high":
                base_risk = "critical"

        # Adjust based on labels
        risk_labels = [label.lower() for label in labels]
        if "security" in risk_labels:
            base_risk = "critical"
        elif "breaking-change" in risk_labels:
            base_risk = "high"

        return base_risk

    def check_cwo12_compliance(
        self, title: str, description: str, file_analysis: list[FileChangeAnalysis]
    ) -> list[str]:
        """Check for CWO12 compliance issues"""
        issues = []

        # Check for evidence requirements
        text = (title + " " + description).lower()
        for pattern in self.cwo12_patterns["evidence_required"]:
            if re.search(pattern, text):
                issues.append(f"Evidence requirement detected: {pattern}")

        # Check for constitutional violations
        for pattern in self.cwo12_patterns["constitutional_violations"]:
            if re.search(pattern, text):
                issues.append(f"Potential constitutional violation: {pattern}")

        # Check for missing documentation
        files_requiring_docs = [f for f in file_analysis if f.documentation_required]
        if files_requiring_docs and not any(
            pattern in text for pattern in self.cwo12_patterns["documentation_required"]
        ):
            issues.append("Documentation appears to be required but not mentioned")

        # Check for testing requirements
        files_requiring_tests = [f for f in file_analysis if f.testing_required]
        if files_requiring_tests and "test" not in text:
            issues.append("Testing appears to be required but not mentioned")

        # Check for breaking changes
        if "breaking" in text and "migration" not in text:
            issues.append("Breaking change detected without migration plan")

        return issues

    def generate_recommendations(
        self,
        complexity_score: float,
        risk_level: str,
        file_analysis: list[FileChangeAnalysis],
        compliance_issues: list[str],
    ) -> list[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Complexity-based recommendations
        if complexity_score >= 0.7:
            recommendations.append(
                "Consider splitting PR into smaller, focused changes"
            )
            recommendations.append("Add comprehensive testing for complex changes")

        # Risk-based recommendations
        if risk_level in ["critical", "high"]:
            recommendations.append("Require additional code review")
            recommendations.append("Consider gradual rollout")

        # File-based recommendations
        high_complexity_files = [
            f for f in file_analysis if f.complexity_impact == "high"
        ]
        if high_complexity_files:
            recommendations.append(
                f"Pay special attention to: {', '.join(f.file_path for f in high_complexity_files[:3])}"
            )

        # Testing recommendations
        files_requiring_tests = [f for f in file_analysis if f.testing_required]
        if files_requiring_tests:
            recommendations.append("Ensure comprehensive test coverage for all changes")

        # Documentation recommendations
        files_requiring_docs = [f for f in file_analysis if f.documentation_required]
        if files_requiring_docs:
            recommendations.append(
                "Update documentation for modified APIs and configurations"
            )

        # Compliance recommendations
        if compliance_issues:
            recommendations.append("Address CWO12 compliance issues before merge")
            recommendations.append("Add proper evidence for all changes")

        # General recommendations
        if not recommendations:
            recommendations.append("Changes appear well-structured and compliant")

        return recommendations

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()


# Example usage
async def main():
    """Example usage of PR analysis engine"""
    import os

    github_token = os.getenv("GITHUB_TOKEN", "your-token")
    engine = PRAnalysisEngine(github_token)

    # Example PR data (would normally come from GitHub API)
    example_pr = {
        "title": "Add user authentication feature",
        "body": "This PR adds OAuth2 authentication with JWT tokens",
        "number": 123,
        "labels": [{"name": "feature"}, {"name": "security"}],
    }

    try:
        result = await engine.analyze_pr(example_pr, "owner/repo")
        print(f"Complexity Score: {result.complexity_score}")
        print(f"Risk Level: {result.risk_level}")
        print(f"Estimated Tasks: {result.estimated_tasks}")
        print(f"Task Suggestions: {len(result.task_suggestions)}")
        print(f"Compliance Issues: {len(result.cwo12_compliance_issues)}")
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
