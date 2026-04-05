#!/usr/bin/env python3
"""
Fix G004 logging f-string issues using AST rewriting.

Transforms: logger.info(f"x: {y}") → logger.info("x: %s", y)
Handles multi-line f-strings, logging.getLogger(), etc.
"""
import ast
import re
from pathlib import Path


class LoggingFStringFixer(ast.NodeTransformer):
    """AST transformer to fix logging f-strings."""

    def __init__(self):
        super().__init__()
        self.fixes = 0

    def visit_Call(self, node):
        """Visit function calls to find logging statements with f-strings."""
        # Check if this is a logging call
        if not isinstance(node.func, (ast.Attribute, ast.Name)):
            return self.generic_visit(node)

        # Determine logger method name
        method_name = None
        if isinstance(node.func, ast.Attribute):
            # Check if the attribute access is on a logger-like variable
            # Handles: logger.METHOD, self.logger.METHOD, _logger.METHOD, etc.
            if isinstance(node.func.value, ast.Name):
                # Simple name like: logger, _logger, log, etc.
                # Accept any name - assume anything with a logging method is a logger
                method_name = node.func.attr
            elif isinstance(node.func.value, ast.Attribute):
                # self.logger, obj.logger, etc.
                if node.func.value.attr == "logger":
                    method_name = node.func.attr
                # Handle logging.getLogger(__name__).METHOD
                elif node.func.value.attr == "getLogger":
                    method_name = node.func.attr
            elif isinstance(node.func.value, ast.Call):
                # Handle logging.getLogger(__name__).METHOD
                if (isinstance(node.func.value.func, ast.Attribute)
                        and node.func.value.func.attr == "getLogger"):
                    method_name = node.func.attr

        if method_name is None:
            return self.generic_visit(node)

        # Check if it's a logging method
        logging_methods = {"debug", "info", "warning", "error", "exception", "critical"}
        if method_name not in logging_methods:
            return self.generic_visit(node)

        # Check if the first argument is an f-string
        if not node.args:
            return self.generic_visit(node)

        first_arg = node.args[0]
        if not isinstance(first_arg, ast.JoinedStr):  # f-string is JoinedStr in AST
            return self.generic_visit(node)

        # Convert f-string to % format string and extract args
        format_parts = []
        new_args = []

        for value in first_arg.values:
            if isinstance(value, ast.Constant):
                # Literal string part
                format_parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                # {expr} part - convert to %s
                format_parts.append("%s")
                new_args.append(value.value)

        # Build new format string
        format_str = "".join(format_parts)
        format_str = format_str.replace("%", "%%")  # Escape % characters

        # Create new node: logger.METHOD("format", arg1, arg2, ...)
        new_node = ast.Call(
            func=ast.Attribute(
                value=node.func.value,
                attr=method_name,
                ctx=ast.Load(),
            ),
            args=[
                ast.Constant(value=format_str),
                *new_args,
                *node.args[1:],  # Keep extra args like exc_info=True
            ],
            keywords=node.keywords,
        )

        self.fixes += 1
        ast.fix_missing_locations(new_node)
        return new_node


def fix_logging_fstring_ast(content: str) -> tuple[str, int]:
    """Fix logging f-strings using AST parsing.

    Returns (fixed_content, fixes_made)
    """
    try:
        tree = ast.parse(content)
        fixer = LoggingFStringFixer()
        new_tree = fixer.visit(tree)

        # Add any missing location fields
        ast.fix_missing_locations(new_tree)

        # Generate code back
        fixed_content = ast.unparse(new_tree)
        return fixed_content, fixer.fixes
    except Exception as e:
        # AST parsing failed, return original
        print(f"  AST parsing failed: {e}")
        return content, 0


def fix_file(file_path: Path) -> int:
    """Fix a single file, return number of fixes made."""
    try:
        content = file_path.read_text(encoding='utf-8')
        fixed, count = fix_logging_fstring_ast(content)

        if count > 0:
            file_path.write_text(fixed, encoding='utf-8')
            print(f'  Fixed {count} issues in {file_path.relative_to(file_path.parents[-2])}')
        return count
    except Exception as e:
        print(f'  Error processing {file_path}: {e}')
        return 0


def main():
    import sys

    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_file():
            print(f'Fixing {target}...')
            fix_file(target)
        elif target.is_dir():
            py_files = list(target.rglob('*.py'))
            print(f'Scanning {len(py_files)} files...')
            total = 0
            for py_file in py_files:
                total += fix_file(py_file)
            print(f'\nTotal fixes: {total}')
    else:
        print('Usage: fix_g004_ast.py <file_or_directory>')
        print('Example: python fix_g004_ast.py src/yt_fts/')


if __name__ == '__main__':
    main()
