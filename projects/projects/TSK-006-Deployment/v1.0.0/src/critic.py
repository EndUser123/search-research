#!/usr/bin/env python3
"""
Critic System for the Persistent Learning Agent Ecosystem

This module provides comprehensive code and architecture evaluation capabilities
including quality scoring, feedback generation, and actionable recommendations.
"""

import ast
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class CriticType(Enum):
    """Types of critics available in the system."""
    CODE = "code"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"


class Severity(Enum):
    """Severity levels for issues identified by critics."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CriticIssue:
    """Represents an issue identified by a critic."""
    id: str
    type: CriticType
    severity: Severity
    title: str
    description: str
    file_path: str | None = None
    line_number: int | None = None
    column: int | None = None
    suggestion: str | None = None
    code_snippet: str | None = None
    impact: str | None = None
    effort: str | None = None
    tags: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class QualityScore:
    """Represents a quality assessment score."""
    overall: float
    categories: dict[str, float]
    issues_by_severity: dict[str, int]
    total_issues: int
    recommendations: list[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CriticResult:
    """Result of a critic evaluation."""
    success: bool
    quality_score: QualityScore
    issues: list[CriticIssue]
    recommendations: list[str]
    metrics: dict[str, Any]
    evaluation_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CodeCritic:
    """Evaluates code quality, maintainability, and best practices."""

    def __init__(self):
        self.complexity_thresholds = {
            'cyclomatic_complexity': 10,
            'cognitive_complexity': 15,
            'max_lines_per_function': 50,
            'max_parameters': 5,
            'max_nesting_depth': 4
        }
        self.quality_patterns = self._load_quality_patterns()

    def _load_quality_patterns(self) -> dict[str, list[re.Pattern]]:
        """Load code quality patterns and anti-patterns."""
        return {
            'security': [
                re.compile(r'eval\s*\('),  # Dangerous eval usage
                re.compile(r'exec\s*\('),  # Dangerous exec usage
                re.compile(r'shell=True'),  # Potential shell injection
                re.compile(r'password.*=.*["\'].*["\']'),  # Hardcoded passwords
                re.compile(r'api_key.*=.*["\'].*["\']'),  # Hardcoded API keys
            ],
            'performance': [
                re.compile(r'\.format\(.*\)\s*%'),  # Mixed formatting
                re.compile(r'for.*in.*range\(len\('),  # Inefficient iteration
                re.compile(r'\+.*\+.*\+'),  # Multiple string concatenation
            ],
            'maintainability': [
                re.compile(r'# TODO'),  # TODO comments
                re.compile(r'# FIXME'),  # FIXME comments
                re.compile(r'def\s+\w+\([^)]*\):\s*pass'),  # Empty functions
                re.compile(r'if.*:\s*pass'),  # Empty if blocks
            ],
            'style': [
                re.compile(r'^\s*\t'),  # Tabs instead of spaces
                re.compile(r'.{90,}'),  # Lines too long (will be filtered)
            ]
        }

    def analyze_code(self, code: str, file_path: str | None = None) -> CriticResult:
        """
        Analyze Python code for quality issues.

        Args:
            code: Python source code to analyze
            file_path: Optional file path for context

        Returns:
            CriticResult with issues and quality assessment
        """
        start_time = datetime.utcnow()
        issues = []

        try:
            # Parse AST
            tree = ast.parse(code)

            # Structural analysis
            issues.extend(self._analyze_ast(tree, file_path))

            # Pattern-based analysis
            issues.extend(self._analyze_patterns(code, file_path))

            # Calculate quality score
            quality_score = self._calculate_quality_score(code, issues)

            # Generate recommendations
            recommendations = self._generate_recommendations(issues, quality_score)

            # Calculate metrics
            metrics = self._calculate_metrics(code, issues)

            evaluation_time = (datetime.utcnow() - start_time).total_seconds()

            return CriticResult(
                success=True,
                quality_score=quality_score,
                issues=issues,
                recommendations=recommendations,
                metrics=metrics,
                evaluation_time=evaluation_time
            )

        except SyntaxError as e:
            issues.append(CriticIssue(
                id=f"syntax_error_{hash(str(e))}",
                type=CriticType.CODE,
                severity=Severity.CRITICAL,
                title="Syntax Error",
                description=f"Syntax error in code: {e}",
                file_path=file_path,
                line_number=e.lineno,
                column=e.offset,
                code_snippet=self._get_code_line(code, e.lineno) if e.lineno else None,
                impact="Code cannot be executed",
                effort="Fix syntax errors immediately",
                confidence=1.0
            ))

            return CriticResult(
                success=False,
                quality_score=QualityScore(
                    overall=0.0,
                    categories={'syntax': 0.0},
                    issues_by_severity={s.value: 1 if s == Severity.CRITICAL else 0
                                      for s in Severity},
                    total_issues=1,
                    recommendations=["Fix syntax errors before proceeding"]
                ),
                issues=issues,
                recommendations=["Fix syntax errors before proceeding"],
                metrics={'error': True},
                evaluation_time=(datetime.utcnow() - start_time).total_seconds()
            )

    def _analyze_ast(self, tree: ast.AST, file_path: str | None = None) -> list[CriticIssue]:
        """Analyze AST for structural issues."""
        issues = []

        for node in ast.walk(tree):
            # Function complexity analysis
            if isinstance(node, ast.FunctionDef):
                issues.extend(self._analyze_function(node, file_path))

            # Class analysis
            elif isinstance(node, ast.ClassDef):
                issues.extend(self._analyze_class(node, file_path))

            # Import analysis
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                issues.extend(self._analyze_imports(node, file_path))

        return issues

    def _analyze_function(self, node: ast.FunctionDef, file_path: str | None = None) -> list[CriticIssue]:
        """Analyze individual function for issues."""
        issues = []

        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(node)
        if complexity > self.complexity_thresholds['cyclomatic_complexity']:
            issues.append(CriticIssue(
                id=f"complexity_{node.lineno}_{node.col_offset}",
                type=CriticType.CODE,
                severity=Severity.HIGH if complexity > 20 else Severity.MEDIUM,
                title="High Cyclomatic Complexity",
                description=f"Function '{node.name}' has cyclomatic complexity of {complexity}, "
                           f"exceeding threshold of {self.complexity_thresholds['cyclomatic_complexity']}",
                file_path=file_path,
                line_number=node.lineno,
                column=node.col_offset,
                suggestion="Consider breaking this function into smaller functions",
                impact="Harder to understand, test, and maintain",
                effort="Medium to High",
                tags=['complexity', 'refactoring'],
                confidence=0.9
            ))

        # Check parameter count
        num_params = len(node.args.args)
        if num_params > self.complexity_thresholds['max_parameters']:
            issues.append(CriticIssue(
                id=f"params_{node.lineno}_{node.col_offset}",
                type=CriticType.CODE,
                severity=Severity.MEDIUM,
                title="Too Many Parameters",
                description=f"Function '{node.name}' has {num_params} parameters, "
                           f"exceeding threshold of {self.complexity_thresholds['max_parameters']}",
                file_path=file_path,
                line_number=node.lineno,
                column=node.col_offset,
                suggestion="Consider using a configuration object or reducing parameters",
                impact="Function becomes harder to use and test",
                effort="Medium",
                tags=['parameters', 'design'],
                confidence=0.8
            ))

        # Check for empty functions
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            issues.append(CriticIssue(
                id=f"empty_func_{node.lineno}_{node.col_offset}",
                type=CriticType.CODE,
                severity=Severity.LOW,
                title="Empty Function",
                description=f"Function '{node.name}' is empty (contains only pass)",
                file_path=file_path,
                line_number=node.lineno,
                column=node.col_offset,
                suggestion="Implement the function or remove it if not needed",
                impact="Incomplete functionality",
                effort="Low",
                tags=['incomplete', 'function'],
                confidence=1.0
            ))

        return issues

    def _analyze_class(self, node: ast.ClassDef, file_path: str | None = None) -> list[CriticIssue]:
        """Analyze class for issues."""
        issues = []

        # Count methods
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > 20:
            issues.append(CriticIssue(
                id=f"large_class_{node.lineno}_{node.col_offset}",
                type=CriticType.CODE,
                severity=Severity.MEDIUM,
                title="Large Class",
                description=f"Class '{node.name}' has {len(methods)} methods, "
                           f"considering splitting into smaller classes",
                file_path=file_path,
                line_number=node.lineno,
                column=node.col_offset,
                suggestion="Apply Single Responsibility Principle and split into smaller classes",
                impact="Class becomes harder to understand and maintain",
                effort="High",
                tags=['design', 'refactoring'],
                confidence=0.7
            ))

        # Check for empty classes
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            issues.append(CriticIssue(
                id=f"empty_class_{node.lineno}_{node.col_offset}",
                type=CriticType.CODE,
                severity=Severity.LOW,
                title="Empty Class",
                description=f"Class '{node.name}' is empty (contains only pass)",
                file_path=file_path,
                line_number=node.lineno,
                column=node.col_offset,
                suggestion="Implement the class or remove it if not needed",
                impact="Incomplete functionality",
                effort="Low",
                tags=['incomplete', 'class'],
                confidence=1.0
            ))

        return issues

    def _analyze_imports(self, node: ast.Import | ast.ImportFrom, file_path: str | None = None) -> list[CriticIssue]:
        """Analyze imports for issues."""
        issues = []

        if isinstance(node, ast.Import):
            for alias in node.names:
                # Check for wildcard imports (not allowed in Import, but in ImportFrom)
                if alias.name == '*':
                    issues.append(CriticIssue(
                        id=f"wildcard_import_{node.lineno}",
                        type=CriticType.CODE,
                        severity=Severity.MEDIUM,
                        title="Wildcard Import",
                        description="Wildcard imports make code harder to understand",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Import specific modules or functions instead",
                        impact="Namespace pollution and unclear dependencies",
                        effort="Low",
                        tags=['imports', 'style'],
                        confidence=0.9
                    ))

        elif isinstance(node, ast.ImportFrom):
            # Check for wildcard imports
            if node.names and any(name.name == '*' for name in node.names):
                issues.append(CriticIssue(
                    id=f"wildcard_import_{node.lineno}",
                    type=CriticType.CODE,
                    severity=Severity.MEDIUM,
                    title="Wildcard Import",
                    description="Wildcard imports make code harder to understand",
                    file_path=file_path,
                    line_number=node.lineno,
                    suggestion="Import specific modules or functions instead",
                    impact="Namespace pollution and unclear dependencies",
                    effort="Low",
                    tags=['imports', 'style'],
                    confidence=0.9
                ))

        return issues

    def _analyze_patterns(self, code: str, file_path: str | None = None) -> list[CriticIssue]:
        """Analyze code for pattern-based issues."""
        issues = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Check each pattern category
            for category, patterns in self.quality_patterns.items():
                for pattern in patterns:
                    if pattern.search(line):
                        severity = self._get_pattern_severity(category)
                        issues.append(CriticIssue(
                            id=f"{category}_{line_num}_{hash(pattern.pattern)}",
                            type=CriticType.CODE,
                            severity=severity,
                            title=self._get_pattern_title(category, pattern),
                            description=f"Detected {category} issue in line {line_num}",
                            file_path=file_path,
                            line_number=line_num,
                            column=0,
                            code_snippet=line.strip(),
                            suggestion=self._get_pattern_suggestion(category, pattern),
                            impact=self._get_pattern_impact(category),
                            effort=self._get_pattern_effort(category),
                            tags=[category, 'pattern'],
                            confidence=0.8
                        ))

        return issues

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _calculate_quality_score(self, code: str, issues: list[CriticIssue]) -> QualityScore:
        """Calculate overall quality score based on issues."""
        # Base score starts at 100
        base_score = 100.0

        # Deduct points based on severity
        deductions = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3,
            Severity.INFO: 1
        }

        total_deduction = sum(deductions[issue.severity] for issue in issues)
        overall_score = max(0, base_score - total_deduction)

        # Calculate category scores
        categories = {
            'security': 100.0,
            'performance': 100.0,
            'maintainability': 100.0,
            'style': 100.0,
            'complexity': 100.0
        }

        for issue in issues:
            category = self._get_issue_category(issue)
            if category in categories:
                categories[category] -= deductions[issue.severity]

        # Ensure scores are non-negative
        categories = {k: max(0, v) for k, v in categories.items()}

        # Count issues by severity
        issues_by_severity = {s.value: 0 for s in Severity}
        for issue in issues:
            issues_by_severity[issue.severity.value] += 1

        return QualityScore(
            overall=overall_score,
            categories=categories,
            issues_by_severity=issues_by_severity,
            total_issues=len(issues),
            recommendations=[]
        )

    def _generate_recommendations(self, issues: list[CriticIssue], quality_score: QualityScore) -> list[str]:
        """Generate actionable recommendations based on issues."""
        recommendations = []

        # Critical issues first
        critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
        if critical_issues:
            recommendations.append(f"URGENT: Fix {len(critical_issues)} critical issues that prevent code execution")

        # High priority issues
        high_issues = [i for i in issues if i.severity == Severity.HIGH]
        if high_issues:
            recommendations.append(f"Address {len(high_issues)} high-priority issues affecting code quality")

        # Category-specific recommendations
        security_issues = [i for i in issues if 'security' in i.tags]
        if security_issues:
            recommendations.append("Review and fix security vulnerabilities immediately")

        complexity_issues = [i for i in issues if 'complexity' in i.tags]
        if complexity_issues:
            recommendations.append("Refactor complex code to improve maintainability")

        # Overall recommendations based on score
        if quality_score.overall < 60:
            recommendations.append("Major code review and refactoring recommended")
        elif quality_score.overall < 80:
            recommendations.append("Code improvements needed before production deployment")
        elif quality_score.overall < 90:
            recommendations.append("Minor improvements recommended for optimal quality")

        return recommendations

    def _calculate_metrics(self, code: str, issues: list[CriticIssue]) -> dict[str, Any]:
        """Calculate various code metrics."""
        lines = code.split('\n')
        total_lines = len(lines)
        non_empty_lines = len([line for line in lines if line.strip()])

        # Count functions and classes
        try:
            tree = ast.parse(code)
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        except:
            functions = []
            classes = []

        return {
            'total_lines': total_lines,
            'non_empty_lines': non_empty_lines,
            'functions_count': len(functions),
            'classes_count': len(classes),
            'issues_per_line': len(issues) / max(1, total_lines),
            'density_issues': len(issues) / max(1, non_empty_lines),
            'avg_function_length': self._calculate_avg_function_length(functions)
        }

    def _calculate_avg_function_length(self, functions: list[ast.FunctionDef]) -> float:
        """Calculate average function length in lines."""
        if not functions:
            return 0.0

        total_length = 0
        for func in functions:
            if hasattr(func, 'end_lineno') and func.end_lineno:
                total_length += func.end_lineno - func.lineno + 1
            else:
                # Fallback: approximate based on child nodes
                total_length += len(list(ast.walk(func)))

        return total_length / len(functions)

    def _get_code_line(self, code: str, line_number: int) -> str | None:
        """Get a specific line from code."""
        lines = code.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return None

    def _get_pattern_severity(self, category: str) -> Severity:
        """Get severity level for pattern category."""
        severity_map = {
            'security': Severity.HIGH,
            'performance': Severity.MEDIUM,
            'maintainability': Severity.LOW,
            'style': Severity.LOW
        }
        return severity_map.get(category, Severity.LOW)

    def _get_pattern_title(self, category: str, pattern: re.Pattern) -> str:
        """Get title for pattern issue."""
        title_map = {
            'security': 'Security Issue',
            'performance': 'Performance Issue',
            'maintainability': 'Maintainability Issue',
            'style': 'Style Issue'
        }
        return f"{title_map.get(category, 'Pattern Issue')}: {pattern.pattern[:30]}..."

    def _get_pattern_suggestion(self, category: str, pattern: re.Pattern) -> str:
        """Get suggestion for pattern issue."""
        suggestion_map = {
            'security': 'Review and remove security vulnerabilities',
            'performance': 'Optimize for better performance',
            'maintainability': 'Improve code structure and documentation',
            'style': 'Follow coding style guidelines'
        }
        return suggestion_map.get(category, 'Review and improve code')

    def _get_pattern_impact(self, category: str) -> str:
        """Get impact description for pattern category."""
        impact_map = {
            'security': 'Potential security vulnerability',
            'performance': 'Reduced performance',
            'maintainability': 'Harder to maintain',
            'style': 'Reduced code readability'
        }
        return impact_map.get(category, 'Code quality impact')

    def _get_pattern_effort(self, category: str) -> str:
        """Get effort level for pattern category."""
        effort_map = {
            'security': 'High',
            'performance': 'Medium',
            'maintainability': 'Low',
            'style': 'Low'
        }
        return effort_map.get(category, 'Medium')

    def _get_issue_category(self, issue: CriticIssue) -> str:
        """Map issue to quality category."""
        if 'security' in issue.tags:
            return 'security'
        elif 'performance' in issue.tags:
            return 'performance'
        elif 'complexity' in issue.tags:
            return 'complexity'
        elif 'style' in issue.tags:
            return 'style'
        else:
            return 'maintainability'


class ArchitectureCritic:
    """Evaluates software architecture and design patterns."""

    def __init__(self):
        self.architecture_patterns = self._load_architecture_patterns()
        self.design_principles = self._load_design_principles()

    def _load_architecture_patterns(self) -> dict[str, Any]:
        """Load architecture patterns and best practices."""
        return {
            'layered_architecture': {
                'required_layers': ['presentation', 'business', 'data'],
                'forbidden_dependencies': ['data -> presentation', 'presentation -> business -> data']
            },
            'microservices': {
                'max_service_size': 500,  # lines of code
                'required_separation': True,
                'api_first': True
            },
            'event_driven': {
                'required_components': ['events', 'handlers', 'event_store'],
                'async_patterns': True
            }
        }

    def _load_design_principles(self) -> dict[str, Any]:
        """Load SOLID and other design principles."""
        return {
            'single_responsibility': {
                'description': 'A class should have only one reason to change',
                'check': 'count_responsibilities'
            },
            'open_closed': {
                'description': 'Software entities should be open for extension, closed for modification',
                'check': 'check_extension_points'
            },
            'liskov_substitution': {
                'description': 'Derived classes must be substitutable for their base classes',
                'check': 'check_inheritance_hierarchy'
            },
            'interface_segregation': {
                'description': 'Clients should not be forced to depend on interfaces they don\'t use',
                'check': 'check_interface_size'
            },
            'dependency_inversion': {
                'description': 'Depend on abstractions, not concretions',
                'check': 'check_dependency_direction'
            }
        }

    def analyze_architecture(self, project_path: Path, architecture_type: str = "general") -> CriticResult:
        """
        Analyze project architecture for issues and improvements.

        Args:
            project_path: Path to the project directory
            architecture_type: Type of architecture to evaluate against

        Returns:
            CriticResult with architectural analysis
        """
        start_time = datetime.utcnow()
        issues = []

        try:
            # Analyze project structure
            structure_issues = self._analyze_project_structure(project_path)
            issues.extend(structure_issues)

            # Analyze dependencies
            dependency_issues = self._analyze_dependencies(project_path)
            issues.extend(dependency_issues)

            # Analyze design patterns
            pattern_issues = self._analyze_design_patterns(project_path)
            issues.extend(pattern_issues)

            # Analyze SOLID principles
            solid_issues = self._analyze_solid_principles(project_path)
            issues.extend(solid_issues)

            # Calculate quality score
            quality_score = self._calculate_architecture_quality_score(issues)

            # Generate recommendations
            recommendations = self._generate_architecture_recommendations(issues, quality_score)

            # Calculate metrics
            metrics = self._calculate_architecture_metrics(project_path, issues)

            evaluation_time = (datetime.utcnow() - start_time).total_seconds()

            return CriticResult(
                success=True,
                quality_score=quality_score,
                issues=issues,
                recommendations=recommendations,
                metrics=metrics,
                evaluation_time=evaluation_time
            )

        except Exception as e:
            return CriticResult(
                success=False,
                quality_score=QualityScore(
                    overall=0.0,
                    categories={'architecture': 0.0},
                    issues_by_severity={s.value: 0 for s in Severity},
                    total_issues=0,
                    recommendations=[f"Architecture analysis failed: {e}"]
                ),
                issues=[],
                recommendations=[f"Architecture analysis failed: {e}"],
                metrics={'error': str(e)},
                evaluation_time=(datetime.utcnow() - start_time).total_seconds()
            )

    def _analyze_project_structure(self, project_path: Path) -> list[CriticIssue]:
        """Analyze project structure for best practices."""
        issues = []

        # Check for essential directories
        essential_dirs = ['src', 'tests', 'docs']
        missing_dirs = [d for d in essential_dirs if not (project_path / d).exists()]

        for missing_dir in missing_dirs:
            issues.append(CriticIssue(
                id=f"missing_dir_{missing_dir}",
                type=CriticType.ARCHITECTURE,
                severity=Severity.MEDIUM,
                title=f"Missing Essential Directory: {missing_dir}",
                description=f"Project is missing the {missing_dir} directory",
                file_path=str(project_path),
                suggestion=f"Create the {missing_dir} directory with appropriate structure",
                impact="Poor project organization and maintainability",
                effort="Low",
                tags=['structure', 'organization'],
                confidence=0.8
            ))

        # Check for configuration files
        config_files = ['README.md', 'requirements.txt', 'pyproject.toml', '.gitignore']
        missing_configs = [f for f in config_files if not (project_path / f).exists()]

        for missing_config in missing_configs:
            severity = Severity.HIGH if missing_config == 'README.md' else Severity.LOW
            issues.append(CriticIssue(
                id=f"missing_config_{missing_config}",
                type=CriticType.ARCHITECTURE,
                severity=severity,
                title=f"Missing Configuration File: {missing_config}",
                description=f"Project is missing {missing_config}",
                file_path=str(project_path),
                suggestion=f"Create {missing_config} with appropriate content",
                impact="Poor project documentation and dependency management",
                effort="Low",
                tags=['configuration', 'documentation'],
                confidence=0.9
            ))

        return issues

    def _analyze_dependencies(self, project_path: Path) -> list[CriticIssue]:
        """Analyze project dependencies for architectural issues."""
        issues = []

        # Look for requirements files
        req_files = list(project_path.glob("**/requirements*.txt"))
        pyproject_files = list(project_path.glob("**/pyproject.toml"))

        if not req_files and not pyproject_files:
            issues.append(CriticIssue(
                id="no_dependency_management",
                type=CriticType.ARCHITECTURE,
                severity=Severity.HIGH,
                title="No Dependency Management",
                description="Project lacks dependency management (requirements.txt or pyproject.toml)",
                file_path=str(project_path),
                suggestion="Add requirements.txt or pyproject.toml for dependency management",
                impact="Difficult dependency management and reproducibility",
                effort="Medium",
                tags=['dependencies', 'management'],
                confidence=0.9
            ))

        # Analyze import patterns
        python_files = list(project_path.glob("**/*.py"))
        circular_imports = self._detect_circular_imports(python_files)

        for circular_import in circular_imports:
            issues.append(CriticIssue(
                id=f"circular_import_{hash(circular_import)}",
                type=CriticType.ARCHITECTURE,
                severity=Severity.HIGH,
                title="Circular Import Detected",
                description=f"Circular import dependency: {circular_import}",
                file_path=str(project_path),
                suggestion="Refactor to eliminate circular dependencies",
                impact="Runtime errors and poor architecture",
                effort="High",
                tags=['dependencies', 'circular'],
                confidence=0.8
            ))

        return issues

    def _analyze_design_patterns(self, project_path: Path) -> list[CriticIssue]:
        """Analyze implementation of design patterns."""
        issues = []
        python_files = list(project_path.glob("**/*.py"))

        for py_file in python_files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    code = f.read()

                tree = ast.parse(code)

                # Check for Singleton pattern issues
                singleton_issues = self._check_singleton_pattern(tree, str(py_file))
                issues.extend(singleton_issues)

                # Check for Factory pattern implementation
                factory_issues = self._check_factory_pattern(tree, str(py_file))
                issues.extend(factory_issues)

                # Check for Observer pattern implementation
                observer_issues = self._check_observer_pattern(tree, str(py_file))
                issues.extend(observer_issues)

            except Exception:
                # Skip files that can't be parsed
                continue

        return issues

    def _analyze_solid_principles(self, project_path: Path) -> list[CriticIssue]:
        """Analyze SOLID principles adherence."""
        issues = []
        python_files = list(project_path.glob("**/*.py"))

        for py_file in python_files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    code = f.read()

                tree = ast.parse(code)

                # Single Responsibility Principle
                srp_issues = self._check_single_responsibility(tree, str(py_file))
                issues.extend(srp_issues)

                # Open/Closed Principle
                ocp_issues = self._check_open_closed(tree, str(py_file))
                issues.extend(ocp_issues)

                # Interface Segregation Principle
                isp_issues = self._check_interface_segregation(tree, str(py_file))
                issues.extend(isp_issues)

                # Dependency Inversion Principle
                dip_issues = self._check_dependency_inversion(tree, str(py_file))
                issues.extend(dip_issues)

            except Exception:
                continue

        return issues

    def _detect_circular_imports(self, python_files: list[Path]) -> list[str]:
        """Detect circular import dependencies."""
        # Simplified circular import detection
        imports = {}
        circular_imports = []

        for py_file in python_files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    code = f.read()

                tree = ast.parse(code)
                file_imports = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            file_imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            file_imports.append(node.module)

                imports[str(py_file)] = file_imports

            except Exception:
                continue

        # Simple circular dependency detection
        for file1, imports1 in imports.items():
            for imported in imports1:
                for file2, imports2 in imports.items():
                    if imported in file2 and any(file1.split('/')[-1].replace('.py', '') in imp for imp in imports2):
                        circular_imports.append(f"{file1} <-> {file2}")

        return list(set(circular_imports))

    def _check_singleton_pattern(self, tree: ast.AST, file_path: str) -> list[CriticIssue]:
        """Check Singleton pattern implementation."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for Singleton pattern indicators
                has_instance_attr = any(
                    isinstance(n, ast.Assign) and
                    any(target.id == '_instance' for target in n.targets if isinstance(target, ast.Name))
                    for n in node.body
                )

                has_new_method = any(
                    isinstance(n, ast.FunctionDef) and n.name == '__new__'
                    for n in node.body
                )

                if has_instance_attr and has_new_method:
                    # Check if it's a proper singleton
                    issues.append(CriticIssue(
                        id=f"singleton_{node.lineno}",
                        type=CriticType.ARCHITECTURE,
                        severity=Severity.MEDIUM,
                        title="Singleton Pattern Detected",
                        description=f"Class '{node.name}' appears to implement Singleton pattern",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Consider if Singleton is necessary or if dependency injection would be better",
                        impact="Global state can make testing difficult",
                        effort="Medium",
                        tags=['pattern', 'singleton'],
                        confidence=0.7
                    ))

        return issues

    def _check_factory_pattern(self, tree: ast.AST, file_path: str) -> list[CriticIssue]:
        """Check Factory pattern implementation."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for Factory pattern indicators
                if 'Factory' in node.name:
                    issues.append(CriticIssue(
                        id=f"factory_{node.lineno}",
                        type=CriticType.ARCHITECTURE,
                        severity=Severity.LOW,
                        title="Factory Pattern Usage",
                        description=f"Class '{node.name}' implements Factory pattern",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Ensure Factory pattern is used appropriately and not over-engineered",
                        impact="Can add unnecessary complexity if not needed",
                        effort="Low",
                        tags=['pattern', 'factory'],
                        confidence=0.6
                    ))

        return issues

    def _check_observer_pattern(self, tree: ast.AST, file_path: str) -> list[CriticIssue]:
        """Check Observer pattern implementation."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for Observer pattern indicators
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                observer_methods = ['attach', 'detach', 'notify', 'update']

                observer_method_count = sum(1 for method in methods if method in observer_methods)
                if observer_method_count >= 2:
                    issues.append(CriticIssue(
                        id=f"observer_{node.lineno}",
                        type=CriticType.ARCHITECTURE,
                        severity=Severity.LOW,
                        title="Observer Pattern Usage",
                        description=f"Class '{node.name}' may implement Observer pattern",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Ensure Observer pattern doesn't lead to memory leaks",
                        impact="Can cause memory leaks if not managed properly",
                        effort="Medium",
                        tags=['pattern', 'observer'],
                        confidence=0.6
                    ))

        return issues

    def _check_single_responsibility(self, tree: ast.AST, file_path: str) -> list[CriticIssue]:
        """Check Single Responsibility Principle adherence."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count different types of responsibilities
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]

                # Simple heuristic: count method name patterns
                responsibilities = set()
                for method in methods:
                    if 'save' in method.name or 'write' in method.name or 'persist' in method.name:
                        responsibilities.add('persistence')
                    if 'validate' in method.name or 'check' in method.name:
                        responsibilities.add('validation')
                    if 'render' in method.name or 'display' in method.name or 'show' in method.name:
                        responsibilities.add('presentation')
                    if 'calculate' in method.name or 'compute' in method.name:
                        responsibilities.add('calculation')

                if len(responsibilities) > 2:
                    issues.append(CriticIssue(
                        id=f"srp_violation_{node.lineno}",
                        type=CriticType.ARCHITECTURE,
                        severity=Severity.MEDIUM,
                        title="Single Responsibility Principle Violation",
                        description=f"Class '{node.name}' appears to have multiple responsibilities: {', '.join(responsibilities)}",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Consider splitting the class into smaller, focused classes",
                        impact="Reduced maintainability and cohesion",
                        effort="High",
                        tags=['solid', 'srp'],
                        confidence=0.7
                    ))

        return issues

    def _check_open_closed(self, tree: ast.AST, file_path: str) -> list[CriticIssue]:
        """Check Open/Closed Principle adherence."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for methods that modify behavior based on type checking
                for method in node.body:
                    if isinstance(method, ast.FunctionDef):
                        for child in ast.walk(method):
                            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                                if child.func.id in ['type', 'isinstance']:
                                    # This is a heuristic - might indicate OCP violation
                                    issues.append(CriticIssue(
                                        id=f"ocp_potential_{method.lineno}",
                                        type=CriticType.ARCHITECTURE,
                                        severity=Severity.LOW,
                                        title="Potential Open/Closed Principle Violation",
                                        description=f"Method '{method.name}' uses type checking which may violate OCP",
                                        file_path=file_path,
                                        line_number=method.lineno,
                                        suggestion="Consider using polymorphism or strategy pattern instead",
                                        impact="Code becomes harder to extend",
                                        effort="Medium",
                                        tags=['solid', 'ocp'],
                                        confidence=0.5
                                    ))
                                    break

        return issues

    def _check_interface_segregation(self, tree: ast.AST, file_path: str) -> list[CriticIssue]:
        """Check Interface Segregation Principle adherence."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for large interfaces (many abstract methods)
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]

                if len(methods) > 10:
                    issues.append(CriticIssue(
                        id=f"isp_violation_{node.lineno}",
                        type=CriticType.ARCHITECTURE,
                        severity=Severity.MEDIUM,
                        title="Interface Segregation Principle Violation",
                        description=f"Class '{node.name}' has {len(methods)} methods, may violate ISP",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Consider splitting into smaller, focused interfaces",
                        impact="Forces clients to depend on methods they don't use",
                        effort="Medium",
                        tags=['solid', 'isp'],
                        confidence=0.6
                    ))

        return issues

    def _check_dependency_inversion(self, tree: ast.AST, file_path: str) -> list[CriticIssue]:
        """Check Dependency Inversion Principle adherence."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for concrete dependencies in constructor
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name == '__init__':
                        # Check for concrete class instantiation
                        for child in ast.walk(method):
                            if isinstance(child, ast.Call):
                                if isinstance(child.func, ast.Name):
                                    # Instantiating concrete class
                                    issues.append(CriticIssue(
                                        id=f"dip_violation_{method.lineno}",
                                        type=CriticType.ARCHITECTURE,
                                        severity=Severity.MEDIUM,
                                        title="Dependency Inversion Principle Violation",
                                        description=f"Constructor of '{node.name}' creates concrete dependency",
                                        file_path=file_path,
                                        line_number=method.lineno,
                                        suggestion="Consider dependency injection or factory pattern",
                                        impact="Tight coupling to concrete implementations",
                                        effort="Medium",
                                        tags=['solid', 'dip'],
                                        confidence=0.7
                                    ))

        return issues

    def _calculate_architecture_quality_score(self, issues: list[CriticIssue]) -> QualityScore:
        """Calculate architecture quality score."""
        base_score = 100.0

        # Deductions based on issue severity and type
        deductions = {
            Severity.CRITICAL: 30,
            Severity.HIGH: 20,
            Severity.MEDIUM: 10,
            Severity.LOW: 5,
            Severity.INFO: 2
        }

        total_deduction = sum(deductions[issue.severity] for issue in issues)
        overall_score = max(0, base_score - total_deduction)

        # Category scores
        categories = {
            'structure': 100.0,
            'dependencies': 100.0,
            'patterns': 100.0,
            'solid_principles': 100.0,
            'scalability': 100.0
        }

        for issue in issues:
            if 'structure' in issue.tags:
                categories['structure'] -= deductions[issue.severity]
            elif 'dependencies' in issue.tags:
                categories['dependencies'] -= deductions[issue.severity]
            elif 'pattern' in issue.tags:
                categories['patterns'] -= deductions[issue.severity]
            elif 'solid' in issue.tags:
                categories['solid_principles'] -= deductions[issue.severity]
            else:
                categories['scalability'] -= deductions[issue.severity]

        categories = {k: max(0, v) for k, v in categories.items()}

        issues_by_severity = {s.value: 0 for s in Severity}
        for issue in issues:
            issues_by_severity[issue.severity.value] += 1

        return QualityScore(
            overall=overall_score,
            categories=categories,
            issues_by_severity=issues_by_severity,
            total_issues=len(issues),
            recommendations=[]
        )

    def _generate_architecture_recommendations(self, issues: list[CriticIssue], quality_score: QualityScore) -> list[str]:
        """Generate architecture-specific recommendations."""
        recommendations = []

        critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
        if critical_issues:
            recommendations.append(f"URGENT: Address {len(critical_issues)} critical architectural issues")

        solid_violations = [i for i in issues if 'solid' in i.tags]
        if solid_violations:
            recommendations.append("Review SOLID principles adherence and refactor accordingly")

        circular_imports = [i for i in issues if 'circular' in i.tags]
        if circular_imports:
            recommendations.append("Eliminate circular dependencies through architectural refactoring")

        if quality_score.categories['dependencies'] < 70:
            recommendations.append("Improve dependency management and reduce coupling")

        if quality_score.categories['solid_principles'] < 60:
            recommendations.append("Major refactoring needed to adhere to SOLID principles")

        if quality_score.overall < 70:
            recommendations.append("Consider architectural review and redesign")

        return recommendations

    def _calculate_architecture_metrics(self, project_path: Path, issues: list[CriticIssue]) -> dict[str, Any]:
        """Calculate architecture-specific metrics."""
        python_files = list(project_path.glob("**/*.py"))

        return {
            'total_files': len(python_files),
            'total_issues': len(issues),
            'issues_per_file': len(issues) / max(1, len(python_files)),
            'circular_dependencies': len([i for i in issues if 'circular' in i.tags]),
            'solid_violations': len([i for i in issues if 'solid' in i.tags]),
            'pattern_violations': len([i for i in issues if 'pattern' in i.tags]),
            'structure_issues': len([i for i in issues if 'structure' in i.tags])
        }


class CriticSystem:
    """Main critic system that orchestrates different critics."""

    def __init__(self):
        self.code_critic = CodeCritic()
        self.architecture_critic = ArchitectureCritic()
        self.critic_history = []

    def evaluate_code(self, code: str, file_path: str | None = None) -> CriticResult:
        """Evaluate code using the code critic."""
        result = self.code_critic.analyze_code(code, file_path)
        self.critic_history.append(result)
        return result

    def evaluate_architecture(self, project_path: Path, architecture_type: str = "general") -> CriticResult:
        """Evaluate architecture using the architecture critic."""
        result = self.architecture_critic.analyze_architecture(project_path, architecture_type)
        self.critic_history.append(result)
        return result

    def evaluate_project(self, project_path: Path) -> dict[str, CriticResult]:
        """Evaluate entire project comprehensively."""
        results = {}

        # Evaluate architecture
        results['architecture'] = self.evaluate_architecture(project_path)

        # Evaluate individual code files
        python_files = list(project_path.glob("**/*.py"))
        code_results = []

        for py_file in python_files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    code = f.read()

                result = self.evaluate_code(code, str(py_file))
                code_results.append((str(py_file), result))

            except Exception as e:
                # Create error result for files that can't be read
                error_result = CriticResult(
                    success=False,
                    quality_score=QualityScore(
                        overall=0.0,
                        categories={'error': 0.0},
                        issues_by_severity={s.value: 0 for s in Severity},
                        total_issues=0,
                        recommendations=[f"Could not analyze file: {e}"]
                    ),
                    issues=[],
                    recommendations=[f"Could not analyze file: {e}"],
                    metrics={'error': str(e)},
                    evaluation_time=0.0
                )
                code_results.append((str(py_file), error_result))

        results['code_files'] = code_results

        # Calculate aggregate metrics
        results['aggregate'] = self._calculate_aggregate_results(results)

        return results

    def _calculate_aggregate_results(self, results: dict[str, Any]) -> dict[str, Any]:
        """Calculate aggregate metrics from individual evaluations."""
        if 'code_files' not in results:
            return {}

        code_files = results['code_files']
        if not code_files:
            return {}

        total_issues = sum(len(result[1].issues) for result in code_files)
        avg_quality_score = sum(result[1].quality_score.overall for result in code_files) / len(code_files)

        # Aggregate issues by severity
        total_issues_by_severity = {s.value: 0 for s in Severity}
        for _, result in code_files:
            for severity, count in result.quality_score.issues_by_severity.items():
                total_issues_by_severity[severity] += count

        # Aggregate all issues
        all_issues = []
        for _, result in code_files:
            all_issues.extend(result.issues)

        return {
            'total_files_analyzed': len(code_files),
            'total_issues': total_issues,
            'average_quality_score': avg_quality_score,
            'issues_by_severity': total_issues_by_severity,
            'top_issues': sorted(all_issues, key=lambda x: x.severity.value, reverse=True)[:10]
        }

    def get_critic_summary(self) -> dict[str, Any]:
        """Get summary of all critic evaluations."""
        if not self.critic_history:
            return {'message': 'No critic evaluations performed yet'}

        total_evaluations = len(self.critic_history)
        total_issues = sum(len(result.issues) for result in self.critic_history)
        avg_quality_score = sum(result.quality_score.overall for result in self.critic_history) / total_evaluations

        return {
            'total_evaluations': total_evaluations,
            'total_issues_found': total_issues,
            'average_quality_score': avg_quality_score,
            'last_evaluation': self.critic_history[-1].timestamp.isoformat() if self.critic_history else None
        }

    def export_results(self, output_path: Path, format: str = "json") -> bool:
        """Export critic results to file."""
        try:
            if format.lower() == "json":
                results = {
                    'critic_summary': self.get_critic_summary(),
                    'evaluations': [
                        {
                            'success': result.success,
                            'quality_score': {
                                'overall': result.quality_score.overall,
                                'categories': result.quality_score.categories,
                                'total_issues': result.quality_score.total_issues
                            },
                            'issues_count': len(result.issues),
                            'recommendations_count': len(result.recommendations),
                            'evaluation_time': result.evaluation_time,
                            'timestamp': result.timestamp.isoformat()
                        }
                        for result in self.critic_history
                    ]
                }

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)

                return True

            elif format.lower() == "markdown":
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("# Critic Evaluation Report\n\n")

                    summary = self.get_critic_summary()
                    f.write("## Summary\n\n")
                    f.write(f"- Total Evaluations: {summary['total_evaluations']}\n")
                    f.write(f"- Total Issues Found: {summary['total_issues_found']}\n")
                    f.write(f"- Average Quality Score: {summary['average_quality_score']:.1f}\n\n")

                    for i, result in enumerate(self.critic_history, 1):
                        f.write(f"## Evaluation {i}\n\n")
                        f.write(f"- Quality Score: {result.quality_score.overall:.1f}\n")
                        f.write(f"- Issues Found: {len(result.issues)}\n")
                        f.write(f"- Evaluation Time: {result.evaluation_time:.2f}s\n")
                        f.write(f"- Timestamp: {result.timestamp}\n\n")

                        if result.recommendations:
                            f.write("### Recommendations\n\n")
                            for rec in result.recommendations:
                                f.write(f"- {rec}\n")
                            f.write("\n")

                return True

            else:
                return False

        except Exception as e:
            print(f"Error exporting results: {e}")
            return False


# Utility functions for external usage
def create_critic() -> CriticSystem:
    """Create a new critic system instance."""
    return CriticSystem()


def evaluate_file(file_path: str | Path) -> CriticResult:
    """Convenience function to evaluate a single file."""
    critic = create_critic()
    file_path = Path(file_path)

    if not file_path.exists():
        return CriticResult(
            success=False,
            quality_score=QualityScore(
                overall=0.0,
                categories={'error': 0.0},
                issues_by_severity={s.value: 0 for s in Severity},
                total_issues=0,
                recommendations=[f"File not found: {file_path}"]
            ),
            issues=[],
            recommendations=[f"File not found: {file_path}"],
            metrics={'error': 'File not found'},
            evaluation_time=0.0
        )

    with open(file_path, encoding='utf-8') as f:
        code = f.read()

    return critic.evaluate_code(code, str(file_path))


def evaluate_project(project_path: str | Path) -> dict[str, CriticResult]:
    """Convenience function to evaluate an entire project."""
    critic = create_critic()
    return critic.evaluate_project(Path(project_path))


def quick_evaluate_code(code: str, file_path: str | None = None) -> CriticResult:
    """Quick code evaluation without creating a critic instance."""
    critic = create_critic()
    return critic.evaluate_code(code, file_path)


def quick_evaluate_file(file_path: str | Path) -> CriticResult:
    """Quick file evaluation without creating a critic instance."""
    return evaluate_file(file_path)


def quick_evaluate_project(project_path: str | Path) -> dict[str, Any]:
    """Quick project evaluation without creating a critic instance."""
    return evaluate_project(project_path)


if __name__ == "__main__":
    # Demo usage
    print("=== Critic System Demo ===")

    # Sample code to evaluate
    sample_code = '''
def complex_function(a, b, c, d, e, f, g, h):
    """A function with too many parameters and high complexity."""
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if g > 0:
                                if h > 0:
                                    return a + b + c + d + e + f + g + h
                                else:
                                    return a + b + c + d + e + f + g
                            else:
                                return a + b + c + d + e + f
                        else:
                            return a + b + c + d + e
                    else:
                        return a + b + c + d
                else:
                    return a + b + c
            else:
                return a + b
        else:
            return a
    else:
        return 0

class EmptyClass:
    pass

def another_function():
    pass
'''

    print("\nEvaluating sample code...")
    result = evaluate_file("sample.py")

    print(f"Success: {result.success}")
    print(f"Quality Score: {result.quality_score.overall:.1f}")
    print(f"Total Issues: {result.quality_score.total_issues}")
    print(f"Evaluation Time: {result.evaluation_time:.2f}s")

    print("\nIssues found:")
    for issue in result.issues[:5]:  # Show first 5 issues
        print(f"- {issue.severity.value.upper()}: {issue.title}")
        print(f"  {issue.description}")
        print(f"  Suggestion: {issue.suggestion}")
        print()

    print("Recommendations:")
    for rec in result.recommendations[:3]:  # Show first 3 recommendations
        print(f"- {rec}")

    print("\nMetrics:")
    for key, value in result.metrics.items():
        print(f"  {key}: {value}")
