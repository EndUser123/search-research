from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""AI Distiller Health Check

Validates the functionality and health of the AI Distiller knowledge processing
components in the CSF framework.
"""


# Add src directory to path for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent


def check_ai_distiller_health() -> dict[str, Any]:
    """Check AI Distiller system health."""
    results = {
        "status": "unknown",
        "checks_performed": [],
        "errors": [],
        "warnings": [],
        "components": {},
    }

    # Check AI Distiller module availability
    distiller_result = check_ai_distiller_module()
    results["components"]["ai_distiller_module"] = distiller_result
    results["checks_performed"].append("AI Distiller module availability")

    # Check knowledge processing functionality
    knowledge_result = check_knowledge_processing()
    results["components"]["knowledge_processing"] = knowledge_result
    results["checks_performed"].append("Knowledge processing functionality")

    # Check distillation pipelines
    pipeline_result = check_distillation_pipelines()
    results["components"]["distillation_pipelines"] = pipeline_result
    results["checks_performed"].append("Distillation pipelines")

    # Check knowledge base connectivity
    kb_result = check_knowledge_base_connectivity()
    results["components"]["knowledge_base"] = kb_result
    results["checks_performed"].append("Knowledge base connectivity")

    # Collect errors and warnings
    for component, result in results["components"].items():
        if result.get("status") == "error":
            results["errors"].append(f"{component}: {result.get('error', 'Unknown error')}")
        elif result.get("status") == "warning":
            results["warnings"].append(f"{component}: {result.get('warning', 'Unknown warning')}")

    # Determine overall status
    if results["errors"]:
        results["status"] = "error"
    elif results["warnings"]:
        results["status"] = "warning"
    else:
        results["status"] = "healthy"

    return results


def check_ai_distiller_module() -> dict[str, Any]:
    """Check if AI Distiller module is available."""
    result = {
        "status": "unknown",
        "module_found": False,
        "functions_available": [],
        "error": None,
        "warning": None,
    }

    try:
        # Try to import AI distiller components
        distiller_paths = [
            "modules.ai_distiller.distiller_validator",
            "modules.knowledge.knowledge_system",
            "modules.knowledge.knowledge_validator",
        ]

        for module_path in distiller_paths:
            try:
                importlib.import_module(module_path)
                result["functions_available"].append(module_path)
                result["module_found"] = True
            except ImportError:
                # Module not found, continue checking
                pass

        if not result["functions_available"]:
            result["status"] = "warning"
            result["warning"] = "No AI Distiller modules found"
        else:
            result["status"] = "healthy"

    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Failed to check AI Distiller: {e}"

    return result


def check_knowledge_processing() -> dict[str, Any]:
    """Check knowledge processing functionality."""
    result = {
        "status": "unknown",
        "processing_available": False,
        "knowledge_bases": [],
        "error": None,
        "warning": None,
    }

    try:
        # Check for knowledge base directories
        kb_paths = [
            project_root / "src" / "data" / "knowledge_base",
            project_root / ".csf_context",
            project_root / "data" / "knowledge",
            project_root / "memory",
        ]

        for kb_path in kb_paths:
            if kb_path.exists():
                result["knowledge_bases"].append(str(kb_path))
                result["processing_available"] = True

        if not result["knowledge_bases"]:
            result["status"] = "warning"
            result["warning"] = "No knowledge base directories found"
        else:
            result["status"] = "healthy"

    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Failed to check knowledge processing: {e}"

    return result


def check_distillation_pipelines() -> dict[str, Any]:
    """Check distillation pipeline functionality."""
    result = {
        "status": "unknown",
        "pipelines_found": 0,
        "pipeline_files": [],
        "error": None,
        "warning": None,
    }

    try:
        # Look for distillation-related files
        patterns = ["*distill*", "*knowledge*", "*processing*"]

        for pattern in patterns:
            pipeline_files = list(project_root.rglob(pattern))
            for file_path in pipeline_files:
                if file_path.is_file() and file_path.suffix in [".py", ".yaml", ".yml"]:
                    result["pipeline_files"].append(str(file_path))
                    result["pipelines_found"] += 1

        if result["pipelines_found"] == 0:
            result["status"] = "warning"
            result["warning"] = "No distillation pipeline files found"
        else:
            result["status"] = "healthy"

    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Failed to check distillation pipelines: {e}"

    return result


def check_knowledge_base_connectivity() -> dict[str, Any]:
    """Check knowledge base database connectivity."""
    result = {
        "status": "unknown",
        "databases_found": 0,
        "database_files": [],
        "error": None,
        "warning": None,
    }

    try:
        # Look for knowledge base databases
        db_patterns = ["**/*.db", "**/*.sqlite", "**/*.sqlite3"]

        for pattern in db_patterns:
            db_files = list(project_root.rglob(pattern))
            for db_file in db_files:
                # Filter for knowledge-related databases
                db_path_str = str(db_file).lower()
                if any(
                    keyword in db_path_str
                    for keyword in ["knowledge", "orchestrator", "evidence", "workflow"]
                ):
                    result["database_files"].append(str(db_file))
                    result["databases_found"] += 1

        if result["databases_found"] == 0:
            result["status"] = "warning"
            result["warning"] = "No knowledge base databases found"
        else:
            result["status"] = "healthy"

    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Failed to check knowledge base connectivity: {e}"

    return result


def main():
    """Main health check execution."""
    print("AI Distiller Health Check")
    print("=" * 30)

    results = check_ai_distiller_health()

    print(f"Overall Status: {results['status'].upper()}")
    print()

    # Show component details
    for component, result in results["components"].items():
        print(f"Component: {component}")
        print(f"  Status: {result['status']}")

        if "module_found" in result:
            print(f"  Module Found: {result['module_found']}")
        if "processing_available" in result:
            print(f"  Processing Available: {result['processing_available']}")
        if "pipelines_found" in result:
            print(f"  Pipelines Found: {result['pipelines_found']}")
        if "databases_found" in result:
            print(f"  Databases Found: {result['databases_found']}")

        if result.get("error"):
            print(f"  Error: {result['error']}")
        if result.get("warning"):
            print(f"  Warning: {result['warning']}")
        print()

    # Show errors and warnings
    if results["errors"]:
        print("ERRORS:")
        for error in results["errors"]:
            print(f"  - {error}")
        print()

    if results["warnings"]:
        print("WARNINGS:")
        for warning in results["warnings"]:
            print(f"  - {warning}")
        print()

    # Exit with appropriate code
    if results["status"] == "error":
        print("[FAIL] AI Distiller health check FAILED")
        return 1
    if results["status"] == "warning":
        print("[WARN] AI Distiller health check completed with WARNINGS")
        return 0
    print("[PASS] AI Distiller health check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
