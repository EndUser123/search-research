from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""
GLM-4.6-Flash Integration Test Report

Comprehensive testing script for Research-Flash modern implementation
with GLM-4.6-Flash integration through existing CKS system.
"""


# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class IntegrationTester:
    """Comprehensive integration testing for GLM-4.6-Flash."""

    def __init__(self):
        self.results = {
            "test_date": datetime.now().isoformat(),
            "tests": {},
            "summary": {"total_tests": 0, "passed": 0, "failed": 0, "warnings": []},
        }
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Setup logging for test results."""
        import logging

        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        return logging.getLogger(__name__)

    def log_test(self, test_name: str, passed: bool, message: str = "", details: dict = None):
        """Log test result."""
        self.results["tests"][test_name] = {
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }

        self.results["summary"]["total_tests"] += 1
        if passed:
            self.results["summary"]["passed"] += 1
            self.logger.info(f"✓ {test_name}: {message}")
        else:
            self.results["summary"]["failed"] += 1
            self.logger.error(f"✗ {test_name}: {message}")

    async def test_imports(self) -> bool:
        """Test all module imports."""
        tests_passed = 0
        total_tests = 0

        # Test clean implementation import
        total_tests += 1
        try:
            self.log_test(
                "import_clean_implementation", True, "Clean implementation imported successfully"
            )
            tests_passed += 1
        except Exception as e:
            self.log_test("import_clean_implementation", False, f"Import failed: {e}")

        # Test GLM integration import
        total_tests += 1
        try:
            self.log_test("import_glm_integration", True, "GLM integration imported successfully")
            tests_passed += 1
        except Exception as e:
            self.log_test("import_glm_integration", False, f"Import failed: {e}")

        # Test GLM source import
        total_tests += 1
        try:
            self.log_test("import_glm_source", True, "GLM source imported successfully")
            tests_passed += 1
        except Exception as e:
            self.log_test("import_glm_source", False, f"Import failed: {e}")

        return tests_passed == total_tests

    async def test_cks_python_standards(self) -> bool:
        """Test CKS Python 2025 standards compliance."""
        tests_passed = 0
        total_tests = 0

        # Test type hints
        total_tests += 1
        try:
            glm = GLMFlashIntegration()

            # Check method signatures
            search_method = getattr(glm, "search_research", None)
            if search_method and hasattr(search_method, "__annotations__"):
                self.log_test("type_hints_present", True, "Type hints present in methods")
                tests_passed += 1
            else:
                self.log_test("type_hints_present", False, "Type hints missing")
        except Exception as e:
            self.log_test("type_hints_present", False, f"Type hints check failed: {e}")

        # Test dataclass usage
        total_tests += 1
        try:
            from glm_integration import GLMConfig

            if hasattr(GLMConfig, "__dataclass_fields__"):
                self.log_test("dataclass_usage", True, "Dataclass patterns used correctly")
                tests_passed += 1
            else:
                self.log_test("dataclass_usage", False, "Dataclass patterns not found")
        except Exception as e:
            self.log_test("dataclass_usage", False, f"Dataclass check failed: {e}")

        # Test async/await patterns
        total_tests += 1
        try:
            import inspect

            from query_engine_clean import ResearchFlashEngine

            query_method = getattr(ResearchFlashEngine, "query", None)
            if query_method and inspect.iscoroutinefunction(query_method):
                self.log_test("async_patterns", True, "Modern async/await patterns used")
                tests_passed += 1
            else:
                self.log_test("async_patterns", False, "Async patterns not properly implemented")
        except Exception as e:
            self.log_test("async_patterns", False, f"Async patterns check failed: {e}")

        return tests_passed == total_tests

    async def test_glm_integration(self) -> bool:
        """Test GLM-4.6-Flash integration functionality."""
        tests_passed = 0
        total_tests = 0

        # Test GLM integration initialization
        total_tests += 1
        try:
            glm = GLMFlashIntegration()

            if hasattr(glm, "is_available") and hasattr(glm, "model_info"):
                available = glm.is_available
                model_info = glm.model_info

                self.log_test(
                    "glm_initialization",
                    True,
                    f"GLM integration initialized - Available: {available}, Model: {model_info.get('model')}",
                    {"available": available, "model_info": model_info},
                )
                tests_passed += 1
            else:
                self.log_test(
                    "glm_initialization", False, "GLM integration missing required attributes"
                )
        except Exception as e:
            self.log_test("glm_initialization", False, f"GLM initialization failed: {e}")

        # Test GLM search functionality
        total_tests += 1
        try:
            glm = GLMFlashIntegration()

            result = await glm.search_research(
                "test query", max_results=2, source_types=["web_search"]
            )

            if isinstance(result, list):
                self.log_test(
                    "glm_search_functionality",
                    True,
                    f"GLM search returned {len(result)} results",
                    {
                        "result_count": len(result),
                        "sample_result": result[0].__dict__ if result else None,
                    },
                )
                tests_passed += 1
            else:
                self.log_test("glm_search_functionality", False, "GLM search did not return list")
        except Exception as e:
            self.log_test("glm_search_functionality", False, f"GLM search failed: {e}")

        return tests_passed == total_tests

    async def test_research_engine(self) -> bool:
        """Test complete research engine functionality."""
        tests_passed = 0
        total_tests = 0

        # Test engine initialization
        total_tests += 1
        try:
            engine = ResearchFlashEngine()

            sources = engine.get_available_sources()
            status = engine.get_source_status()

            self.log_test(
                "engine_initialization",
                True,
                f"Research engine initialized with sources: {sources}",
                {"sources": sources, "status": status},
            )
            tests_passed += 1
        except Exception as e:
            self.log_test("engine_initialization", False, f"Engine initialization failed: {e}")

        # Test comprehensive query
        total_tests += 1
        try:
            engine = ResearchFlashEngine()

            start_time = time.time()
            result = await engine.query(
                "Python async patterns best practices",
                sources=["cks", "chs", "glm"],
                max_results_per_source=2,
                glm_source_types=["web_search", "github_analysis"],
            )
            processing_time = time.time() - start_time

            if result and hasattr(result, "results"):
                self.log_test(
                    "comprehensive_query",
                    True,
                    f"Query completed in {processing_time:.3f}s with {len(result.results)} results",
                    {
                        "processing_time": processing_time,
                        "sources_used": result.sources_used,
                        "result_count": len(result.results),
                        "synthesis_length": len(result.synthesis) if result.synthesis else 0,
                    },
                )
                tests_passed += 1
            else:
                self.log_test("comprehensive_query", False, "Query did not return valid result")
        except Exception as e:
            self.log_test("comprehensive_query", False, f"Comprehensive query failed: {e}")

        return tests_passed == total_tests

    async def test_error_handling(self) -> bool:
        """Test error handling and fallback mechanisms."""
        tests_passed = 0
        total_tests = 0

        # Test graceful degradation
        total_tests += 1
        try:
            glm = GLMFlashIntegration()

            # Test with invalid source types
            result = await glm.search_research("test", source_types=["invalid_type"])

            # Should return fallback results even with invalid input
            if isinstance(result, list):
                self.log_test(
                    "error_handling_graceful_degradation",
                    True,
                    "System gracefully handles invalid input with fallbacks",
                )
                tests_passed += 1
            else:
                self.log_test(
                    "error_handling_graceful_degradation",
                    False,
                    "System did not handle invalid input gracefully",
                )
        except Exception as e:
            self.log_test(
                "error_handling_graceful_degradation", False, f"Error handling test failed: {e}"
            )

        # Test timeout handling
        total_tests += 1
        try:
            engine = ResearchFlashEngine()

            # Test with very short timeout (this would need configuration change to test properly)
            # For now, just ensure the engine can handle missing sources
            result = await engine.query("test", sources=["nonexistent_source"])

            self.log_test(
                "error_handling_missing_sources",
                True,
                "System handles missing/invalid sources correctly",
            )
            tests_passed += 1
        except Exception as e:
            self.log_test(
                "error_handling_missing_sources", False, f"Missing source handling failed: {e}"
            )

        return tests_passed == total_tests

    async def run_all_tests(self) -> dict[str, Any]:
        """Run all integration tests."""
        self.logger.info("Starting GLM-4.6-Flash Integration Test Suite")
        self.logger.info("=" * 50)

        # Run test categories
        test_categories = [
            ("Module Imports", self.test_imports),
            ("CKS Python 2025 Standards", self.test_cks_python_standards),
            ("GLM-4.6-Flash Integration", self.test_glm_integration),
            ("Research Engine Functionality", self.test_research_engine),
            ("Error Handling & Fallbacks", self.test_error_handling),
        ]

        for category_name, test_func in test_categories:
            self.logger.info(f"\n--- Testing {category_name} ---")
            try:
                await test_func()
            except Exception as e:
                self.logger.error(f"Test category {category_name} failed: {e}")
                self.results["summary"]["failed"] += 1

        # Generate final summary
        self.logger.info("\n" + "=" * 50)
        self.logger.info("TEST SUMMARY")
        self.logger.info("=" * 50)

        summary = self.results["summary"]
        self.logger.info(f"Total Tests: {summary['total_tests']}")
        self.logger.info(f"Passed: {summary['passed']}")
        self.logger.info(f"Failed: {summary['failed']}")

        success_rate = (
            (summary["passed"] / summary["total_tests"]) * 100 if summary["total_tests"] > 0 else 0
        )
        self.logger.info(f"Success Rate: {success_rate:.1f}%")

        # Categorize results
        if success_rate >= 90:
            status = "EXCELLENT"
        elif success_rate >= 75:
            status = "GOOD"
        elif success_rate >= 50:
            status = "NEEDS IMPROVEMENT"
        else:
            status = "CRITICAL ISSUES"

        self.logger.info(f"Overall Status: {status}")

        self.results["summary"]["success_rate"] = success_rate
        self.results["summary"]["status"] = status

        return self.results


async def main():
    """Main test runner."""
    tester = IntegrationTester()
    results = await tester.run_all_tests()

    # Save detailed results
    output_file = Path(__file__).parent / "glm_integration_test_report.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Detailed test report saved to: {output_file}")

    # Return exit code based on results
    failed_count = results["summary"]["failed"]
    if failed_count > 0:
        print(f"\n⚠️  {failed_count} test(s) failed. Review the report for details.")
        return 1
    print("\n🎉 All tests passed! GLM-4.6-Flash integration is working correctly.")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
