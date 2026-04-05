#!/usr/bin/env python3
"""
AST Analysis Tool for dnld_telegram
Analyzes code flow to find database connection patterns and async context issues.
"""

import ast
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FunctionCall:
    """Represents a function call with context."""

    function_name: str
    file_path: str
    line_number: int
    context: str
    is_async: bool
    parent_function: str | None = None


@dataclass
class DatabaseOperation:
    """Represents a database-related operation."""

    operation_type: str  # 'connection', 'query', 'transaction'
    function_call: FunctionCall
    context_managers: list[str]
    async_depth: int


class DatabasePatternAnalyzer(ast.NodeVisitor):
    """AST visitor to find database operation patterns."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.current_function = None
        self.async_depth = 0
        self.context_managers = []

        # Results
        self.function_calls = []
        self.database_operations = []
        self.async_contexts = []
        self.imports = []

        # Patterns to look for
        self.db_patterns = {
            "get_connection",
            "aiosqlite",
            "SQLiteConnectionPool",
            "ensure_channel_exists",
            "_get_database_files",
            "get_connection_pool",
        }
        self.async_patterns = {"async with", "__aenter__", "__aexit__", "asyncio"}

    def visit_FunctionDef(self, node):
        """Track function definitions and their async nature."""
        old_function = self.current_function
        self.current_function = node.name

        if isinstance(node, ast.AsyncFunctionDef):
            self.async_depth += 1

        self.generic_visit(node)

        if isinstance(node, ast.AsyncFunctionDef):
            self.async_depth -= 1

        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node):
        """Handle async function definitions."""
        self.visit_FunctionDef(node)

    def visit_Call(self, node):
        """Track function calls, especially database-related ones."""
        func_name = self._get_function_name(node.func)

        if func_name:
            call = FunctionCall(
                function_name=func_name,
                file_path=self.file_path,
                line_number=node.lineno,
                context=f"in {self.current_function}"
                if self.current_function
                else "global",
                is_async=self.async_depth > 0,
                parent_function=self.current_function,
            )
            self.function_calls.append(call)

            # Check for database operations
            if any(pattern in func_name for pattern in self.db_patterns):
                db_op = DatabaseOperation(
                    operation_type=self._classify_db_operation(func_name),
                    function_call=call,
                    context_managers=self.context_managers.copy(),
                    async_depth=self.async_depth,
                )
                self.database_operations.append(db_op)

        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        """Track async context managers."""
        for item in node.items:
            context_name = self._get_function_name(item.context_expr)
            if context_name:
                self.context_managers.append(context_name)

                # Track async context
                self.async_contexts.append(
                    {
                        "context": context_name,
                        "file": self.file_path,
                        "line": node.lineno,
                        "function": self.current_function,
                        "depth": self.async_depth,
                    }
                )

        self.generic_visit(node)

        # Remove context managers when exiting
        for item in node.items:
            context_name = self._get_function_name(item.context_expr)
            if context_name and context_name in self.context_managers:
                self.context_managers.remove(context_name)

    def visit_Import(self, node):
        """Track imports."""
        for alias in node.names:
            self.imports.append(
                {
                    "module": alias.name,
                    "alias": alias.asname,
                    "file": self.file_path,
                    "line": node.lineno,
                }
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track from imports."""
        for alias in node.names:
            self.imports.append(
                {
                    "module": f"{node.module}.{alias.name}"
                    if node.module
                    else alias.name,
                    "alias": alias.asname,
                    "file": self.file_path,
                    "line": node.lineno,
                }
            )
        self.generic_visit(node)

    def _get_function_name(self, node):
        """Extract function name from various node types."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_function_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Call):
            return self._get_function_name(node.func)
        return None

    def _classify_db_operation(self, func_name):
        """Classify the type of database operation."""
        if "connection" in func_name.lower():
            return "connection"
        elif any(
            word in func_name.lower()
            for word in ["select", "insert", "update", "delete", "execute"]
        ):
            return "query"
        elif "transaction" in func_name.lower():
            return "transaction"
        else:
            return "other"


def analyze_file(file_path: Path) -> DatabasePatternAnalyzer:
    """Analyze a single Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = DatabasePatternAnalyzer(str(file_path))
        analyzer.visit(tree)
        return analyzer
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None


def find_database_call_chains(analyzers: list[DatabasePatternAnalyzer]) -> dict:
    """Find call chains that lead to database operations."""

    # Build function call graph
    call_graph = defaultdict(list)
    all_db_ops = []

    for analyzer in analyzers:
        if analyzer:
            all_db_ops.extend(analyzer.database_operations)

            # Build call relationships
            for call in analyzer.function_calls:
                if call.parent_function:
                    call_graph[call.parent_function].append(call)

    # Find paths to database operations
    db_call_paths = []
    for db_op in all_db_ops:
        path = find_call_path_to_db(db_op, call_graph)
        db_call_paths.append(
            {
                "db_operation": {
                    "type": db_op.operation_type,
                    "function": db_op.function_call.function_name,
                    "file": db_op.function_call.file_path,
                    "line": db_op.function_call.line_number,
                    "context": db_op.function_call.context,
                    "async_depth": db_op.async_depth,
                    "context_managers": db_op.context_managers,
                },
                "call_path": path,
            }
        )

    return {
        "database_call_paths": db_call_paths,
        "total_db_operations": len(all_db_ops),
        "files_analyzed": len([a for a in analyzers if a]),
    }


def find_call_path_to_db(db_op: DatabaseOperation, call_graph: dict) -> list[str]:
    """Find the call path that leads to a database operation."""
    # This is a simplified version - would need more sophisticated analysis
    # for complete call path tracing
    path = []
    if db_op.function_call.parent_function:
        path.append(db_op.function_call.parent_function)
    path.append(db_op.function_call.function_name)
    return path


def analyze_concurrent_patterns(analyzers: list[DatabasePatternAnalyzer]) -> dict:
    """Analyze potential concurrent access patterns."""

    concurrent_risks = []
    async_db_ops = []

    for analyzer in analyzers:
        if analyzer:
            for db_op in analyzer.database_operations:
                if db_op.function_call.is_async:
                    async_db_ops.append(db_op)

    # Group by file and function to find potential concurrent access
    by_context = defaultdict(list)
    for db_op in async_db_ops:
        key = f"{db_op.function_call.file_path}:{db_op.function_call.parent_function}"
        by_context[key].append(db_op)

    # Look for contexts with multiple database operations
    for context, ops in by_context.items():
        if len(ops) > 1:
            concurrent_risks.append(
                {
                    "context": context,
                    "operation_count": len(ops),
                    "operations": [
                        {
                            "type": op.operation_type,
                            "function": op.function_call.function_name,
                            "line": op.function_call.line_number,
                        }
                        for op in ops
                    ],
                }
            )

    return {
        "concurrent_risks": concurrent_risks,
        "total_async_db_ops": len(async_db_ops),
        "risk_contexts": len(concurrent_risks),
    }


def main():
    """Main analysis function."""
    src_dir = Path("src")

    if not src_dir.exists():
        print("src directory not found")
        return

    # Find all Python files
    python_files = list(src_dir.rglob("*.py"))
    print(f"Analyzing {len(python_files)} Python files...")

    # Analyze each file
    analyzers = []
    for file_path in python_files:
        if file_path.name != "__pycache__":
            analyzer = analyze_file(file_path)
            analyzers.append(analyzer)

    # Generate reports
    print("\n" + "=" * 50)
    print("DATABASE OPERATION ANALYSIS")
    print("=" * 50)

    # Call chain analysis
    call_chains = find_database_call_chains(analyzers)
    print(
        f"\nFound {call_chains['total_db_operations']} database operations across {call_chains['files_analyzed']} files"
    )

    # Concurrent pattern analysis
    concurrent_analysis = analyze_concurrent_patterns(analyzers)
    print(
        f"Found {concurrent_analysis['total_async_db_ops']} async database operations"
    )
    print(
        f"Identified {concurrent_analysis['risk_contexts']} potential concurrent access contexts"
    )

    # Save detailed report
    report = {
        "call_chains": call_chains,
        "concurrent_patterns": concurrent_analysis,
        "analysis_summary": {
            "files_analyzed": len(python_files),
            "total_db_operations": call_chains["total_db_operations"],
            "async_db_operations": concurrent_analysis["total_async_db_ops"],
            "concurrent_risk_contexts": concurrent_analysis["risk_contexts"],
        },
    }

    with open("DATABASE_AST_ANALYSIS.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("\nDetailed report saved to: DATABASE_AST_ANALYSIS.json")

    # Print key findings
    print("\n" + "=" * 50)
    print("KEY FINDINGS")
    print("=" * 50)

    if concurrent_analysis["concurrent_risks"]:
        print("\n🚨 CONCURRENT ACCESS RISKS FOUND:")
        for risk in concurrent_analysis["concurrent_risks"]:
            print(f"  📍 {risk['context']}: {risk['operation_count']} operations")
            for op in risk["operations"]:
                print(f"    - {op['type']}: {op['function']} (line {op['line']})")

    print("\n📊 Database Operations by File:")
    file_ops = defaultdict(int)
    for analyzer in analyzers:
        if analyzer and analyzer.database_operations:
            file_ops[analyzer.file_path] = len(analyzer.database_operations)

    for file_path, count in sorted(file_ops.items(), key=lambda x: x[1], reverse=True):
        print(f"  {count:2d} operations: {file_path}")


if __name__ == "__main__":
    main()
