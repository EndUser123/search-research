"""
BugJail Recommendation Engine

Generates actionable fix recommendations for detected bugs and vulnerabilities.
"""

from typing import Any

from ..core.types import (
    BugCategory,
    BugSeverity,
    DetectionResult,
    FixRecommendation,
    VulnerabilityResult,
    VulnerabilityType,
)


class RecommendationEngine:
    """
    Generates actionable fix recommendations for detected issues.

    Provides specific code fixes, explanations, and best practice guidance
    for various bug categories and vulnerability types.
    """

    def __init__(self):
        """Initialize recommendation engine."""
        self.recommendation_templates = self._initialize_recommendation_templates()

    def generate_recommendations(
        self,
        issues: list[DetectionResult]
    ) -> list[FixRecommendation]:
        """
        Generate fix recommendations for detected issues.

        Args:
            issues: List of detected bugs and vulnerabilities

        Returns:
            List of fix recommendations
        """
        recommendations = []

        for issue in issues:
            # Get specific recommendation for this issue
            recommendation = self._generate_recommendation(issue)
            if recommendation:
                recommendations.append(recommendation)

        # Sort by priority
        priority_order = {
            BugSeverity.CRITICAL: 0,
            BugSeverity.HIGH: 1,
            BugSeverity.MEDIUM: 2,
            BugSeverity.LOW: 3,
            BugSeverity.INFO: 4
        }

        recommendations.sort(
            key=lambda r: priority_order.get(r.priority, 5)
        )

        return recommendations

    def _generate_recommendation(self, issue: DetectionResult) -> FixRecommendation | None:
        """Generate a recommendation for a specific issue."""
        # Handle vulnerabilities
        if isinstance(issue, VulnerabilityResult):
            return self._generate_vulnerability_recommendation(issue)

        # Handle regular bugs
        return self._generate_bug_recommendation(issue)

    def _generate_bug_recommendation(self, bug: DetectionResult) -> FixRecommendation | None:
        """Generate recommendation for a bug."""
        templates = self.recommendation_templates.get(bug.type, [])

        # Find matching template
        for template in templates:
            if self._template_matches(template, bug):
                return self._apply_template(template, bug)

        # Default recommendation
        return self._create_default_recommendation(bug)

    def _generate_vulnerability_recommendation(self, vuln: VulnerabilityResult) -> FixRecommendation | None:
        """Generate recommendation for a vulnerability."""
        vuln_templates = self._get_vulnerability_templates(vuln.vulnerability_type)

        for template in vuln_templates:
            if self._template_matches(template, vuln):
                return self._apply_template(template, vuln)

        return self._create_default_vulnerability_recommendation(vuln)

    def _initialize_recommendation_templates(self) -> dict[BugCategory, list[dict]]:
        """Initialize recommendation templates for different bug categories."""
        return {
            BugCategory.NULL_POINTER: [
                {
                    "title": "Add null check before accessing",
                    "description": "Always check if a variable is None before accessing its attributes or methods",
                    "before_example": "result = get_data()\nprocessed = result.process()",
                    "after_example": "result = get_data()\nif result is not None:\n    processed = result.process()",
                    "code_fix": "if {variable} is not None:\n    {original_code}",
                    "effort_estimate": "5 min",
                    "automation_possible": True,
                    "pattern_match": r"(\w+)\.([a-zA-Z_][a-zA-Z0-9_]*)"
                }
            ],
            BugCategory.RESOURCE_LEAK: [
                {
                    "title": "Use context manager for resource management",
                    "description": "Use 'with' statement to ensure proper resource cleanup",
                    "before_example": "file = open('data.txt')\ncontent = file.read()\nfile.close()",
                    "after_example": "with open('data.txt') as file:\n    content = file.read()",
                    "code_fix": "with {resource_expression} as {variable}:\n    {indented_code}",
                    "effort_estimate": "10 min",
                    "automation_possible": True,
                    "pattern_match": r"open\s*\([^)]+\)"
                }
            ],
            BugCategory.DIVISION_BY_ZERO: [
                {
                    "title": "Add zero check before division",
                    "description": "Always validate divisor is not zero before performing division",
                    "before_example": "result = numerator / denominator",
                    "after_example": "if denominator != 0:\n    result = numerator / denominator\nelse:\n    result = None  # or handle appropriately",
                    "code_fix": "if {divisor} != 0:\n    {division_expression}",
                    "effort_estimate": "5 min",
                    "automation_possible": True,
                    "pattern_match": r"/\s*(\w+)"
                }
            ],
            BugCategory.RACE_CONDITION: [
                {
                    "title": "Use atomic operations or locks",
                    "description": "Protect shared resources with proper synchronization mechanisms",
                    "before_example": "counter += 1  # Not thread-safe",
                    "after_example": "with lock:\n    counter += 1  # Thread-safe",
                    "code_fix": "with threading.Lock():\n    {atomic_operation}",
                    "effort_estimate": "30 min",
                    "automation_possible": False,
                    "references": [
                        "https://docs.python.org/3/library/threading.html",
                        "https://wiki.python.org/moin/PythonThreads"
                    ]
                }
            ],
            BugCategory.API_MISUSE: [
                {
                    "title": "Review API documentation for proper usage",
                    "description": "API functions should be used according to their documentation",
                    "before_example": "result = eval(user_input)",
                    "after_example": "result = ast.literal_eval(user_input)  # Safer alternative",
                    "code_fix": "# Replace eval() with safer alternative like ast.literal_eval()",
                    "effort_estimate": "1 hour",
                    "automation_possible": False,
                    "learn_more_links": [
                        "https://docs.python.org/3/library/ast.html#ast.literal_eval",
                        "https://owasp.org/www-community/attacks/Code_Injection"
                    ]
                }
            ]
        }

    def _get_vulnerability_templates(self, vuln_type: VulnerabilityType) -> list[dict]:
        """Get recommendation templates for a vulnerability type."""
        vuln_templates = {
            VulnerabilityType.A03_INJECTION: [
                {
                    "title": "Use parameterized queries",
                    "description": "Always use parameterized queries to prevent SQL injection",
                    "before_example": "cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")",
                    "after_example": "cursor.execute(\"SELECT * FROM users WHERE id = ?\", (user_id,))",
                    "code_fix": "cursor.execute({safe_query_with_placeholders}, ({parameters},))",
                    "effort_estimate": "30 min",
                    "priority": BugSeverity.CRITICAL,
                    "references": [
                        "https://owasp.org/www-community/attacks/SQL_Injection",
                        "https://docs.python.org/3/library/sqlite3.html"
                    ]
                }
            ],
            VulnerabilityType.A02_CRYPTOGRAPHIC_FAILURES: [
                {
                    "title": "Use strong cryptographic algorithms",
                    "description": "Replace weak algorithms with modern cryptographic standards",
                    "before_example": "hash_value = hashlib.md5(data).hexdigest()",
                    "after_example": "hash_value = hashlib.sha256(data).hexdigest()",
                    "code_fix": "hashlib.sha256({data})",
                    "effort_estimate": "1 hour",
                    "priority": BugSeverity.HIGH,
                    "references": [
                        "https://owasp.org/www-project-cheat-sheets/cheatsheets/Password_Storage_Cheat_Sheet.html",
                        "https://docs.python.org/3/library/hashlib.html"
                    ]
                }
            ],
            VulnerabilityType.A01_BROKEN_ACCESS_CONTROL: [
                {
                    "title": "Implement proper access control checks",
                    "description": "Always verify user permissions before accessing resources",
                    "before_example": "user_data = get_user_data(request.args.get('user_id'))",
                    "after_example": "user_id = request.args.get('user_id')\nif current_user.can_access(user_id):\n    user_data = get_user_data(user_id)\nelse:\n    return redirect('/unauthorized')",
                    "code_fix": "if authorization_check(user_id, current_user):\n    {protected_operation}",
                    "effort_estimate": "2 hours",
                    "priority": BugSeverity.HIGH,
                    "references": [
                        "https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control"
                    ]
                }
            ],
            VulnerabilityType.A08_SOFTWARE_DATA_INTEGRITY: [
                {
                    "title": "Use safe deserialization methods",
                    "description": "Avoid using pickle for untrusted data serialization",
                    "before_example": "data = pickle.loads(untrusted_data)",
                    "after_example": "data = json.loads(untrusted_data)  # Safer alternative",
                    "code_fix": "json.loads({data})  # or other safe format",
                    "effort_estimate": "1 hour",
                    "priority": BugSeverity.HIGH,
                    "references": [
                        "https://owasp.org/www-project-cheat-sheets/cheatsheets/Deserialization_Cheat_Sheet.html"
                    ]
                }
            ]
        }

        return vuln_templates.get(vuln_type, [])

    def _template_matches(self, template: dict, issue: DetectionResult) -> bool:
        """Check if a template matches an issue."""
        # Check pattern match if specified
        if "pattern_match" in template:
            import re
            pattern = template["pattern_match"]
            if not re.search(pattern, issue.code_snippet, re.IGNORECASE):
                return False

        # Check rule match
        if "rule_id" in template and issue.rule_id:
            if template["rule_id"] != issue.rule_id:
                return False

        return True

    def _apply_template(self, template: dict, issue: DetectionResult) -> FixRecommendation:
        """Apply a recommendation template to an issue."""
        # Generate code fix if template supports automation
        automated_fix = None
        if template.get("automation_possible") and "code_fix" in template:
            automated_fix = self._generate_automated_fix(template, issue)

        return FixRecommendation(
            title=template["title"],
            description=template["description"],
            code_fix=automated_fix,
            explanation=template.get("explanation", ""),
            priority=template.get("priority", issue.severity),
            effort_estimate=template.get("effort_estimate"),
            automation_possible=template.get("automation_possible", False),
            automated_fix=automated_fix,
            before_example=template.get("before_example"),
            after_example=template.get("after_example"),
            references=template.get("references", []),
            learn_more_links=template.get("learn_more_links", [])
        )

    def _generate_automated_fix(self, template: dict, issue: DetectionResult) -> str | None:
        """Generate automated fix code from template."""
        code_fix = template["code_fix"]

        # Extract variable names from issue
        if "pattern_match" in template:
            import re
            pattern = re.compile(template["pattern_match"])
            match = pattern.search(issue.code_snippet)
            if match:
                groups = match.groups()
                for i, group in enumerate(groups):
                    code_fix = code_fix.replace("{variable}", group, 1)
                    code_fix = code_fix.replace(f"{{variable{i+1}}}", group)

        return code_fix

    def _create_default_recommendation(self, bug: DetectionResult) -> FixRecommendation:
        """Create a default recommendation for a bug."""
        return FixRecommendation(
            title=f"Fix {bug.type.value.replace('_', ' ').title()}",
            description=f"Address the detected {bug.type.value} issue",
            priority=bug.severity,
            effort_estimate="30 min",
            automation_possible=False,
            references=[
                "https://stackoverflow.com/questions/tagged/python+bug"
            ]
        )

    def _create_default_vulnerability_recommendation(self, vuln: VulnerabilityResult) -> FixRecommendation:
        """Create a default recommendation for a vulnerability."""
        return FixRecommendation(
            title=f"Fix {vuln.vulnerability_type.value.replace('_', ' ').title()}",
            description=f"Address the security vulnerability: {vuln.description}",
            priority=vuln.severity,
            effort_estimate="2 hours",
            automation_possible=False,
            references=[
                f"https://owasp.org/www-project-top-ten/{vuln.vulnerability_type.value}"
            ],
            learn_more_links=[
                f"https://cwe.mitre.org/data/definitions/{vuln.cwe_id.split('-')[1]}.html"
            ] if vuln.cwe_id else []
        )

    def get_recommendation_statistics(self, recommendations: list[FixRecommendation]) -> dict[str, Any]:
        """Get statistics for generated recommendations."""
        stats = {
            "total_recommendations": len(recommendations),
            "by_priority": {},
            "automation_possible": 0,
            "estimated_total_effort": ""
        }

        effort_minutes = 0
        effort_mapping = {
            "5 min": 5,
            "10 min": 10,
            "30 min": 30,
            "1 hour": 60,
            "2 hours": 120,
            "1 day": 480
        }

        for rec in recommendations:
            # Count by priority
            priority = rec.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1

            # Count automation possibilities
            if rec.automation_possible:
                stats["automation_possible"] += 1

            # Sum effort estimates
            if rec.effort_estimate in effort_mapping:
                effort_minutes += effort_mapping[rec.effort_estimate]

        # Format total effort
        if effort_minutes < 60:
            stats["estimated_total_effort"] = f"{effort_minutes} minutes"
        elif effort_minutes < 480:
            stats["estimated_total_effort"] = f"{effort_minutes // 60} hours {effort_minutes % 60} minutes"
        else:
            days = effort_minutes // 480
            remaining = effort_minutes % 480
            hours = remaining // 60
            stats["estimated_total_effort"] = f"{days} days {hours} hours"

        return stats
