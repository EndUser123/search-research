#!/usr/bin/env python3
"""Stage 2.5: Check for logging and telemetry instrumentation."""

import ast
import sys
from pathlib import Path


def check_logging(file_path: Path) -> dict:
    """Check if a Python file has logging instrumentation."""
    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError) as e:
        return {'file': str(file_path), 'error': str(e)}
    
    has_logging_import = False
    has_logger = False
    functions_without_logging = []
    
    for node in ast.walk(tree):
        # Check for logging imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'logging':
                    has_logging_import = True
        elif isinstance(node, ast.ImportFrom):
            if node.module == 'logging':
                has_logging_import = True
        
        # Check for logger instantiation
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and 'log' in target.id.lower():
                    has_logger = True
        
        # Check functions for logging calls
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('_') and node.name != '__init__':
                continue  # Skip private methods except __init__
            
            has_log_call = False
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute):
                        if child.func.attr in ('debug', 'info', 'warning', 'error', 'critical', 'exception'):
                            has_log_call = True
                            break
            
            if not has_log_call and len(node.body) > 3:  # Only flag non-trivial functions
                functions_without_logging.append(node.name)
    
    return {
        'file': str(file_path),
        'has_logging_import': has_logging_import,
        'has_logger': has_logger,
        'functions_without_logging': functions_without_logging
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: stage2_5_logging.py <target>", file=sys.stderr)
        sys.exit(1)
    
    target = sys.argv[1]
    target_path = Path(target)
    
    if target_path.is_file():
        files = [target_path] if target_path.suffix == '.py' else []
    elif target_path.is_dir():
        files = list(target_path.rglob('*.py'))
    else:
        # Comma-separated list
        files = [Path(f.strip()) for f in target.split(',') if Path(f.strip()).suffix == '.py']
    
    if not files:
        print("No Python files found")
        sys.exit(0)
    
    total_missing = 0
    results = []
    
    for f in files:
        if not f.exists():
            continue
        result = check_logging(f)
        results.append(result)
        if result.get('functions_without_logging'):
            total_missing += len(result['functions_without_logging'])
    
    # Output results
    print(f"Checked {len(results)} files for logging instrumentation")
    
    files_without_logging = [r for r in results if not r.get('has_logging_import')]
    if files_without_logging:
        print(f"\n⚠️  {len(files_without_logging)} files without logging import:")
        for r in files_without_logging[:10]:
            print(f"   - {r['file']}")
    
    if total_missing > 0:
        print(f"\n⚠️  {total_missing} functions without logging calls:")
        for r in results:
            for func in r.get('functions_without_logging', [])[:5]:
                print(f"   - {r['file']}:{func}()")
        sys.exit(0)  # Warn but don't fail
    else:
        print("✅ All functions have logging instrumentation")
        sys.exit(0)


if __name__ == '__main__':
    main()
