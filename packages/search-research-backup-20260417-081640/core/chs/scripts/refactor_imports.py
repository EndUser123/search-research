"""AST-based import refactoring for CHS v2 migration.

Updates all imports from knowledge.systems.chs.v2 to search_research.core.chs.

Usage:
    python -m search_research.core.chs.scripts.refactor_imports
"""

from __future__ import annotations

import ast
from pathlib import Path


class CHSImportRefactor(ast.NodeTransformer):
    """AST transformer to update CHS imports."""

    OLD_PREFIX = "knowledge.systems.chs.v2"
    NEW_PREFIX = "search_research.core.chs"

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        """Update 'from knowledge.systems.chs.v2.xxx import yyy'."""
        if node.module and node.module.startswith(self.OLD_PREFIX):
            node.module = node.module.replace(self.OLD_PREFIX, self.NEW_PREFIX)
        return node

    def visit_Import(self, node: ast.Import) -> ast.Import:
        """Update 'import knowledge.systems.chs.v2.xxx'."""
        new_names = []
        for alias in node.names:
            if alias.name.startswith(self.OLD_PREFIX):
                new_name = alias.name.replace(self.OLD_PREFIX, self.NEW_PREFIX)
                new_alias = ast.alias(name=new_name, asname=alias.asname)
                new_names.append(new_alias)
            else:
                new_names.append(alias)
        node.names = new_names
        return node


def refactor_file(file_path: Path) -> bool:
    """Refactor imports in a single Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        True if file was modified, False otherwise
    """
    content = file_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return False
    transformer = CHSImportRefactor()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    new_content = ast.unparse(new_tree)
    if new_content != content:
        file_path.write_text(new_content + "\n", encoding="utf-8")
        return True
    return False


def refactor_directory(root_dir: Path) -> list[Path]:
    """Refactor all Python files in a directory.

    Args:
        root_dir: Root directory to search

    Returns:
        List of modified file paths
    """
    modified_files = []
    for py_file in root_dir.rglob("*.py"):
        if refactor_file(py_file):
            modified_files.append(py_file)
            print(f"  Refactored: {py_file.relative_to(root_dir.parent.parent)}")
    return modified_files


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    print("CHS Import Refactoring")
    print("=" * 60)
    print(f"OLD: {CHSImportRefactor.OLD_PREFIX}")
    print(f"NEW: {CHSImportRefactor.NEW_PREFIX}")
    print()
    script_dir = Path(__file__).parent
    chs_dir = script_dir.parent
    core_dir = chs_dir.parent
    search_research = core_dir.parent
    print(f"Searching: {search_research}")
    print()
    modified = refactor_directory(search_research)
    print()
    print(f"Modified {len(modified)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
