#!/usr/bin/env python3
"""
Commit Analyzer for TaskMaster GitHub Integration
Analyzes commits for task creation, linking, and status updates
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
class CommitAnalysisResult:
    """Result of commit analysis"""

    task_creation_requests: list[dict[str, Any]]
    task_linking_requests: list[dict[str, Any]]
    task_status_updates: list[dict[str, Any]]
    evidence_collection_requests: list[dict[str, Any]]
    complexity_score: float
    affected_tasks: list[str]
    metadata: dict[str, Any]


@dataclass
class CommitEvidence:
    """Evidence collected from commit"""

    commit_hash: str
    timestamp: str
    author: str
    message: str
    files_changed: list[str]
    task_references: list[str]
    status_indicators: dict[str, str]
    completion_evidence: list[str]
    metadata: dict[str, Any]


class CommitAnalyzer:
    """Advanced commit analysis for task management integration"""

    def __init__(self, github_token: str):
        self.github_token = github_token
        self.session: aiohttp.ClientSession | None = None

        # Task creation patterns
        self.task_creation_patterns = {
            "explicit": [
                r"(?i)(?:task|tsk)(?:-)?create:\s*(.+)",
                r"(?i)(?:task|tsk)(?:-)?new:\s*(.+)",
                r"(?i)(?:task|tsk)(?:-)?add:\s*(.+)",
                r"(?i)create\s+task:\s*(.+)",
                r"(?i)add\s+task:\s*(.+)",
            ],
            "implicit": [
                r"(?i)TODO:\s*(.+)",
                r"(?i)FIXME:\s*(.+)",
                r"(?i)HACK:\s*(.+)",
                r"(?i)NOTE:\s*(.+)",
            ],
        }

        # Task linking patterns
        self.task_linking_patterns = [
            r"(?:task|tsk)[\s-]*(?:#|id)?(\w+[-]?\d*)",
            r"#(\d+)",
            r"(?:ref|reference|refs|relates|related)\s+(?:to\s+)?(?:task|tsk)[\s-]*(?:#|id)?(\w+[-]?\d*)",
            r"(?:fix|fixes|fixed|close|closes|closed|resolve|resolves|resolved)\s+(?:task|tsk)[\s-]*(?:#|id)?(\w+[-]?\d*)",
        ]

        # Status indicator patterns
        self.status_patterns = {
            "in_progress": [
                r"(?i)(?:started|begin|began|working\s+on|progress|in\s+progress)",
                r"(?i)(?:wip|work\s+in\s+progress)",
                r"(?i)(?:implementing|adding|creating|building)",
            ],
            "completed": [
                r"(?i)(?:completed|finished|done|ready|complete)",
                r"(?i)(?:implemented|added|created|built)",
                r"(?i)(?:fix|fixes|fixed|resolve|resolves|resolved)",
                r"(?i)(?:merge|merged)",
            ],
            "blocked": [
                r"(?i)(?:blocked|blocked\s+by|waiting|wait\s+for)",
                r"(?i)(?:depends|dependency|need\s+to)",
                r"(?i)(?:hold|on\s+hold)",
            ],
            "cancelled": [
                r"(?i)(?:cancelled|canceled|aborted|reverted)",
                r"(?i)(?:rollback|rolled\s+back)",
                r"(?i)(undo|undone)",
            ],
        }

        # Completion evidence patterns
        self.completion_evidence_patterns = [
            r"(?i)(?:test|tests?|testing)\s+(?:pass|passes|passed)",
            r"(?i)(?:build|built|building)\s+(?:success|successful)",
            r"(?i)(?:deploy|deployed|deployment)\s+(?:success|successful)",
            r"(?i)(?:verify|verifed|validation)\s+(?:pass|passes|passed)",
            r"(?i)(?:review|reviewed)\s+(?:approved|accepted)",
        ]

        # File type configurations
        self.file_type_config = {
            "code": {
                "extensions": [
                    ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".java",
                    ".cpp",
                    ".c",
                    ".go",
                    ".rs",
                ],
                "evidence_weight": 1.0,
                "task_relevance": "high",
            },
            "config": {
                "extensions": [
                    ".json",
                    ".yaml",
                    ".yml",
                    ".toml",
                    ".ini",
                    ".conf",
                    ".xml",
                ],
                "evidence_weight": 0.7,
                "task_relevance": "medium",
            },
            "documentation": {
                "extensions": [".md", ".rst", ".txt", ".doc", ".pdf"],
                "evidence_weight": 0.5,
                "task_relevance": "low",
            },
            "test": {
                "extensions": [
                    ".test",
                    ".spec",
                    ".test.js",
                    ".spec.js",
                    "_test.py",
                    "_spec.py",
                ],
                "evidence_weight": 0.9,
                "task_relevance": "high",
            },
            "database": {
                "extensions": [".sql", ".db", ".sqlite", ".migration"],
                "evidence_weight": 0.8,
                "task_relevance": "high",
            },
        }

    async def analyze_commit(
        self, commit_data: dict[str, Any], repo_full_name: str
    ) -> CommitAnalysisResult:
        """
        Comprehensive commit analysis
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Extract basic commit information
            commit_hash = commit_data.get("sha", "")
            message = commit_data.get("commit", {}).get("message", "")
            author = (
                commit_data.get("commit", {}).get("author", {}).get("name", "Unknown")
            )
            timestamp = commit_data.get("commit", {}).get("author", {}).get("date", "")
            url = commit_data.get("html_url", "")

            # Get detailed file information
            files_changed = await self.get_commit_files(repo_full_name, commit_hash)

            # Extract task information
            task_creation_requests = self.extract_task_creation_requests(
                message, commit_hash, author
            )
            task_linking_requests = self.extract_task_linking_requests(
                message, commit_hash
            )
            task_status_updates = self.extract_task_status_updates(message, commit_hash)

            # Collect evidence
            evidence_requests = self.collect_evidence_from_commit(
                commit_data, files_changed, message, commit_hash
            )

            # Calculate complexity
            complexity_score = self.calculate_commit_complexity(files_changed, message)

            # Find affected tasks
            affected_tasks = self.find_affected_tasks(
                task_linking_requests, message, files_changed
            )

            # Prepare metadata
            metadata = {
                "commit_hash": commit_hash,
                "author": author,
                "timestamp": timestamp,
                "url": url,
                "files_count": len(files_changed),
                "total_additions": sum(f.get("additions", 0) for f in files_changed),
                "total_deletions": sum(f.get("deletions", 0) for f in files_changed),
                "file_types": list(
                    {
                        self.determine_file_type(f.get("filename", ""))
                        for f in files_changed
                    }
                ),
                "message_length": len(message),
                "analysis_timestamp": datetime.now().isoformat(),
            }

            return CommitAnalysisResult(
                task_creation_requests=task_creation_requests,
                task_linking_requests=task_linking_requests,
                task_status_updates=task_status_updates,
                evidence_collection_requests=evidence_requests,
                complexity_score=complexity_score,
                affected_tasks=affected_tasks,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error analyzing commit: {e}", exc_info=True)
            raise

    async def get_commit_files(
        self, repo_full_name: str, commit_hash: str
    ) -> list[dict[str, Any]]:
        """Get files changed in a commit"""
        try:
            url = f"https://api.github.com/repos/{repo_full_name}/commits/{commit_hash}"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    commit_data = await response.json()
                    return commit_data.get("files", [])
                else:
                    logger.error(f"Failed to get commit files: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error getting commit files: {e}")
            return []

    def extract_task_creation_requests(
        self, message: str, commit_hash: str, author: str
    ) -> list[dict[str, Any]]:
        """Extract task creation requests from commit message"""
        requests = []

        lines = message.split("\n")
        for line_num, line in enumerate(lines):
            line = line.strip()

            # Check explicit task creation patterns
            for pattern in self.task_creation_patterns["explicit"]:
                match = re.search(pattern, line)
                if match:
                    task_title = match.group(1).strip()
                    if task_title:
                        request = self.create_task_creation_request(
                            task_title, line, lines[line_num + 1 :], commit_hash, author
                        )
                        requests.append(request)

            # Check implicit patterns (lower priority)
            if not requests:  # Only if no explicit requests found
                for pattern in self.task_creation_patterns["implicit"]:
                    match = re.search(pattern, line)
                    if match:
                        task_title = match.group(1).strip()
                        if task_title and len(task_title) > 10:  # Filter short notes
                            request = self.create_task_creation_request(
                                task_title,
                                line,
                                lines[line_num + 1 :],
                                commit_hash,
                                author,
                                priority="low",
                            )
                            requests.append(request)

        return requests

    def create_task_creation_request(
        self,
        title: str,
        trigger_line: str,
        following_lines: list[str],
        commit_hash: str,
        author: str,
        priority: str = "medium",
    ) -> dict[str, Any]:
        """Create a task creation request from extracted information"""
        # Extract description from following lines
        description_lines = []
        for line in following_lines[:5]:  # Take up to 5 lines after the trigger
            if line.strip() and not line.startswith((" ", "\t")):
                break  # Stop at first non-indented line
            if line.strip():
                description_lines.append(line.strip())

        description = (
            "\n".join(description_lines)
            if description_lines
            else f"Task created from commit: {trigger_line}"
        )

        # Determine task type from title and context
        task_type = self.determine_task_type_from_title(title)

        # Generate tags
        tags = ["github", "commit", "automated", task_type]

        # Extract acceptance criteria
        acceptance_criteria = self.extract_acceptance_criteria_from_commit(description)

        return {
            "title": title,
            "description": description,
            "task_type": task_type,
            "priority": priority,
            "phase": "development",
            "source": "github_commit",
            "tags": tags,
            "acceptance_criteria": acceptance_criteria,
            "estimated_duration": self.estimate_duration_from_commit(
                task_type, priority, description
            ),
            "metadata": {
                "trigger_commit": commit_hash,
                "trigger_author": author,
                "trigger_line": trigger_line,
                "creation_source": "commit_message",
                "auto_generated": True,
            },
        }

    def determine_task_type_from_title(self, title: str) -> str:
        """Determine task type from title content"""
        title_lower = title.lower()

        type_mapping = {
            "bug": ["bug", "fix", "error", "issue", "problem", "crash"],
            "feature": ["feature", "add", "new", "implement", "create", "build"],
            "refactor": ["refactor", "cleanup", "improve", "optimize", "restructure"],
            "documentation": ["docs", "documentation", "readme", "guide", "manual"],
            "testing": ["test", "spec", "coverage", "qa", "verify"],
            "security": ["security", "auth", "permission", "vulnerability"],
            "performance": ["performance", "speed", "optimize", "fast", "efficient"],
        }

        for task_type, keywords in type_mapping.items():
            if any(keyword in title_lower for keyword in keywords):
                return task_type

        return "development"

    def extract_acceptance_criteria_from_commit(self, description: str) -> list[str]:
        """Extract acceptance criteria from commit description"""
        criteria = []

        # Look for explicit criteria
        lines = description.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                criteria.append(line.lstrip("-* ").strip())

        # If no explicit criteria, generate generic ones based on content
        if not criteria:
            if "test" in description.lower():
                criteria.append("Tests written and passing")
            if "documentation" in description.lower():
                criteria.append("Documentation updated")
            if "fix" in description.lower():
                criteria.append("Issue resolved and tested")

        return criteria

    def estimate_duration_from_commit(
        self, task_type: str, priority: str, description: str
    ) -> int:
        """Estimate task duration from commit information"""
        base_durations = {
            "bug": 4,
            "feature": 8,
            "refactor": 6,
            "documentation": 2,
            "testing": 3,
            "security": 12,
            "performance": 8,
            "development": 5,
        }

        priority_multipliers = {"critical": 1.5, "high": 1.2, "medium": 1.0, "low": 0.8}

        base_duration = base_durations.get(task_type, 5)
        priority_multiplier = priority_multipliers.get(priority, 1.0)

        # Adjust based on description length
        complexity_factor = 1.0
        if len(description) > 200:
            complexity_factor = 1.2
        elif len(description) > 100:
            complexity_factor = 1.1

        return int(base_duration * priority_multiplier * complexity_factor)

    def extract_task_linking_requests(
        self, message: str, commit_hash: str
    ) -> list[dict[str, Any]]:
        """Extract task linking requests from commit message"""
        links = []

        for pattern in self.task_linking_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                task_ref = match.group(1)
                full_match = match.group(0)

                # Determine link type
                link_type = "reference"
                if any(
                    word in full_match.lower() for word in ["fix", "close", "resolve"]
                ):
                    link_type = "completion"

                links.append(
                    {
                        "task_id": task_ref,
                        "commit_hash": commit_hash,
                        "link_type": link_type,
                        "context": full_match,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return links

    def extract_task_status_updates(
        self, message: str, commit_hash: str
    ) -> list[dict[str, Any]]:
        """Extract task status updates from commit message"""
        status_updates = []

        message_lower = message.lower()

        for status, patterns in self.status_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    status_updates.append(
                        {
                            "status": status,
                            "commit_hash": commit_hash,
                            "confidence": self.calculate_status_confidence(
                                pattern, message
                            ),
                            "context": pattern,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    break  # Take first match for each status

        return status_updates

    def calculate_status_confidence(self, pattern: str, message: str) -> float:
        """Calculate confidence level for status detection"""
        base_confidence = 0.7

        # Higher confidence for explicit status words
        explicit_words = ["completed", "finished", "done", "started", "blocked"]
        if any(word in pattern.lower() for word in explicit_words):
            base_confidence = 0.9

        # Higher confidence for patterns at beginning of message
        if pattern.lower() in message[:100].lower():
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def collect_evidence_from_commit(
        self,
        commit_data: dict[str, Any],
        files_changed: list[dict[str, Any]],
        message: str,
        commit_hash: str,
    ) -> list[dict[str, Any]]:
        """Collect evidence from commit for task verification"""
        evidence_requests = []

        # File change evidence
        for file in files_changed:
            file_path = file.get("filename", "")
            file_type = self.determine_file_type(file_path)

            if file_type == "code":
                evidence_requests.append(
                    {
                        "type": "code_change",
                        "file_path": file_path,
                        "change_type": file.get("status", "modified"),
                        "lines_added": file.get("additions", 0),
                        "lines_deleted": file.get("deletions", 0),
                        "commit_hash": commit_hash,
                        "evidence_weight": self.file_type_config[file_type][
                            "evidence_weight"
                        ],
                    }
                )

        # Message-based evidence
        completion_evidence = self.extract_completion_evidence(message)
        if completion_evidence:
            evidence_requests.append(
                {
                    "type": "completion_evidence",
                    "evidence_items": completion_evidence,
                    "commit_hash": commit_hash,
                    "evidence_weight": 0.8,
                }
            )

        # Test evidence
        test_files = [
            f
            for f in files_changed
            if self.determine_file_type(f.get("filename", "")) == "test"
        ]
        if test_files:
            evidence_requests.append(
                {
                    "type": "test_evidence",
                    "test_files": [f.get("filename") for f in test_files],
                    "commit_hash": commit_hash,
                    "evidence_weight": 0.9,
                }
            )

        return evidence_requests

    def extract_completion_evidence(self, message: str) -> list[str]:
        """Extract completion evidence from commit message"""
        evidence = []

        for pattern in self.completion_evidence_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                evidence.append(match.group(0))

        return evidence

    def determine_file_type(self, file_path: str) -> str:
        """Determine file type from path"""
        file_ext = Path(file_path).suffix.lower()

        for file_type, config in self.file_type_config.items():
            if file_ext in config["extensions"]:
                return file_type

        return "other"

    def calculate_commit_complexity(
        self, files_changed: list[dict[str, Any]], message: str
    ) -> float:
        """Calculate complexity score for commit (0.0 - 1.0)"""
        base_score = 0.0

        # File-based complexity
        for file in files_changed:
            file_score = 0.0

            # Lines changed
            total_lines = file.get("additions", 0) + file.get("deletions", 0)
            if total_lines > 200:
                file_score += 0.3
            elif total_lines > 100:
                file_score += 0.2
            elif total_lines > 50:
                file_score += 0.1

            # File type complexity
            file_path = file.get("filename", "")
            file_type = self.determine_file_type(file_path)
            type_weights = {"code": 0.15, "config": 0.1, "database": 0.2, "test": 0.1}
            file_score += type_weights.get(file_type, 0.05)

            # Change type
            if file.get("status") == "added":
                file_score += 0.1
            elif file.get("status") == "deleted":
                file_score += 0.05

            base_score += file_score

        # Normalize by number of files
        if files_changed:
            base_score = min(base_score / len(files_changed), 0.7)

        # Message-based complexity
        message_words = len(message.split())
        if message_words > 100:
            base_score += 0.2
        elif message_words > 50:
            base_score += 0.1

        # Check for complexity indicators
        complexity_keywords = [
            "complex",
            "refactor",
            "rewrite",
            "restructure",
            "architecture",
        ]
        keyword_bonus = sum(
            0.05 for keyword in complexity_keywords if keyword in message.lower()
        )

        final_score = min(base_score + keyword_bonus, 1.0)
        return round(final_score, 2)

    def find_affected_tasks(
        self,
        task_linking_requests: list[dict[str, Any]],
        message: str,
        files_changed: list[dict[str, Any]],
    ) -> list[str]:
        """Find tasks affected by this commit"""
        affected_tasks = set()

        # From explicit linking
        for link in task_linking_requests:
            affected_tasks.add(link["task_id"])

        # From file-based task detection (would need integration with task database)
        # This is a placeholder for future enhancement
        for file in files_changed:
            file_path = file.get("filename", "")
            # Could query database for tasks related to this file
            pass

        return list(affected_tasks)

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()


# Example usage
async def main():
    """Example usage of commit analyzer"""
    import os

    github_token = os.getenv("GITHUB_TOKEN", "your-token")
    analyzer = CommitAnalyzer(github_token)

    # Example commit data (would normally come from GitHub API)
    example_commit = {
        "sha": "abc123",
        "commit": {
            "message": "Fix user authentication bug\n\nAdd proper input validation\ntask-create: Add comprehensive tests for auth",
            "author": {"name": "John Doe", "date": "2024-01-01T12:00:00Z"},
        },
        "html_url": "https://github.com/owner/repo/commit/abc123",
    }

    try:
        result = await analyzer.analyze_commit(example_commit, "owner/repo")
        print(f"Task Creation Requests: {len(result.task_creation_requests)}")
        print(f"Task Linking Requests: {len(result.task_linking_requests)}")
        print(f"Status Updates: {len(result.task_status_updates)}")
        print(f"Evidence Requests: {len(result.evidence_collection_requests)}")
        print(f"Complexity Score: {result.complexity_score}")
        print(f"Affected Tasks: {result.affected_tasks}")
    finally:
        await analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())
