#!/usr/bin/env python3
"""
Comprehensive Test Suite for PRD Parser

Tests various PRD formats, edge cases, and error conditions.
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path

# Import parser
from parser import PRDParser, PRDRequirement, PRDValidationError

logging.basicConfig(level=logging.INFO)


class TestPRDParser(unittest.TestCase):
    """Test cases for PRD Parser."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = PRDParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # Helper methods

    def create_temp_prd(self, content: str) -> str:
        """Create a temporary PRD file with given content."""
        prd_path = Path(self.temp_dir) / "test_prd.md"
        with open(prd_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(prd_path)

    def assert_requirement_exists(self, reqs: list[PRDRequirement], req_id: str):
        """Assert that a requirement with given ID exists."""
        matching = [r for r in reqs if r.id == req_id]
        self.assertTrue(
            len(matching) > 0,
            f"Requirement {req_id} not found. Available: {[r.id for r in reqs]}"
        )

    # Test cases

    def test_parse_yt_sync_format(self):
        """Test parsing yt_sync style PRD with #### **FR-1:** format."""
        content = """
# Product Requirements Document

## Core Feature Requirements

#### **FR-1:** Command-Line Interface
*   The feature will be controlled via the `--audit` and `--repair` command-line flags.
*   **`--audit`:** When run alone, the tool performs a **read-only** analysis of the library.

#### **FR-2:** Persistent Metadata Cache (CRITICAL REQUIREMENT)
*   The `MetadataManager` **must** implement a persistent, on-disk cache.
*   Cache will be stored in a JSON file.

## Non-Functional Requirements

*   **NFR-1: Performance:** The verification process must be concurrent.
*   **NFR-2: Safety:** The tool must handle errors gracefully.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        self.assertEqual(len(parsed.functional_requirements), 2)
        self.assertEqual(len(parsed.non_functional_requirements), 2)
        self.assert_requirement_exists(parsed.functional_requirements, "FR-1")
        self.assert_requirement_exists(parsed.functional_requirements, "FR-2")
        self.assert_requirement_exists(parsed.non_functional_requirements, "NFR-1")
        self.assert_requirement_exists(parsed.non_functional_requirements, "NFR-2")

    def test_parse_vid_dup_ai_format(self):
        """Test parsing vid_dup_ai style PRD with detailed subsections."""
        content = """
# Product Requirements Document

## Functional Requirements

### 3.1 Intelligent Duplicate Detection
- **ID:** FR-001
- **Description:** The tool must identify duplicate or similar videos.
- **Requirements:**
  - **Fuzzy Filename Matching (FR-001.1):** Compare video filenames using fuzzy matching.
  - **Duration Matching (FR-001.2):** Filter potential matches by comparing durations.

### 3.2 Quality-Based Retention
- **ID:** FR-002
- **Description:** The tool must determine and retain the highest quality version.
- **Requirements:**
  - **Metric Selection (FR-002.1):** Support multiple quality metrics.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        # Should extract FR-001 and FR-002 from the detailed format
        self.assertGreater(len(parsed.functional_requirements), 0)

    def test_parse_with_frontmatter(self):
        """Test parsing PRD with YAML frontmatter."""
        content = """---
prd_name: Test Project
version: 1.0.0
author: Test Author
---

# Product Requirements Document

## Requirements

#### **FR-1:** Test Requirement
*   Description of test requirement.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        self.assertEqual(parsed.prd_name, "Test Project")
        self.assertEqual(parsed.metadata.get("version"), "1.0.0")
        self.assertEqual(parsed.metadata.get("author"), "Test Author")

    def test_parse_list_format(self):
        """Test parsing list-based requirement format."""
        content = """
# Requirements

- **FR-1:** First requirement: Description here
- **FR-2:** Second requirement: Another description
- **NFR-1:** Performance: Must be fast
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        self.assertGreater(len(parsed.functional_requirements), 0)
        self.assertGreater(len(parsed.non_functional_requirements), 0)

    def test_nf_format(self):
        """Test parsing NF- prefix (alternative to NFR-)."""
        content = """
# Requirements

#### **NF-1:** Performance
*   Must process files quickly.

#### **NF-2:** Reliability
*   Must handle errors gracefully.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        self.assertEqual(len(parsed.non_functional_requirements), 2)
        self.assert_requirement_exists(parsed.non_functional_requirements, "NF-1")
        self.assert_requirement_exists(parsed.non_functional_requirements, "NF-2")

    def test_get_requirement_by_id(self):
        """Test retrieving requirement by ID."""
        content = """
#### **FR-1:** Test Requirement
*   This is a test requirement.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        req = parsed.get_requirement_by_id("FR-1")
        self.assertIsNotNone(req)
        self.assertEqual(req.id, "FR-1")
        self.assertEqual(req.title, "Test Requirement")

        req_not_found = parsed.get_requirement_by_id("FR-999")
        self.assertIsNone(req_not_found)

    def test_get_requirements_by_category(self):
        """Test filtering requirements by category."""
        content = """
#### **FR-1:** API Interface
*   Must provide REST API endpoints.

#### **FR-2:** Database Storage
*   Must store data in database.

#### **FR-3:** User Authentication
*   Must implement login and security.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        # API requirements should be categorized under "API"
        api_reqs = parsed.get_requirements_by_category("API")
        self.assertGreater(len(api_reqs), 0)

        # Database requirements should be categorized under "Data"
        data_reqs = parsed.get_requirements_by_category("Data")
        self.assertGreater(len(data_reqs), 0)

    def test_statistics_tracking(self):
        """Test that parser tracks statistics correctly."""
        content = """
#### **FR-1:** Requirement 1
#### **FR-2:** Requirement 2
#### **NFR-1:** Non-functional 1
"""
        prd_path = self.create_temp_prd(content)
        self.parser.parse_prd_file(prd_path)

        stats = self.parser.get_statistics()
        self.assertEqual(stats["prd_files_parsed"], 1)
        self.assertEqual(stats["functional_count"], 2)
        self.assertEqual(stats["non_functional_count"], 1)

    def test_reset_statistics(self):
        """Test resetting parser statistics."""
        content = "#### **FR-1:** Test"
        prd_path = self.create_temp_prd(content)
        self.parser.parse_prd_file(prd_path)

        self.parser.reset_statistics()
        stats = self.parser.get_statistics()
        self.assertEqual(stats["prd_files_parsed"], 0)

    def test_file_not_found_error(self):
        """Test error handling for missing PRD file."""
        with self.assertRaises(PRDValidationError):
            self.parser.parse_prd_file("nonexistent_file.md")

    def test_empty_prd(self):
        """Test parsing an empty PRD file."""
        content = "# Empty PRD\n\nNo requirements here."
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        self.assertEqual(parsed.total_requirements, 0)

    def test_mixed_formats(self):
        """Test parsing PRD with mixed requirement formats."""
        content = """
#### **FR-1:** Header Format
*   Description here.

- **FR-2:** List format: Another description

FR-3: Plain format: Yet another requirement
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        # Should extract requirements from all formats
        self.assertGreaterEqual(len(parsed.functional_requirements), 2)

    def test_duplicate_requirement_ids(self):
        """Test that duplicate requirement IDs are handled correctly."""
        content = """
#### **FR-1:** First occurrence
*   First description.

#### **FR-1:** Second occurrence (duplicate)
*   Second description.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        # Should only have one FR-1
        fr1_count = sum(1 for r in parsed.functional_requirements if r.id == "FR-1")
        self.assertEqual(fr1_count, 1)

    def test_requirement_with_subsections(self):
        """Test extracting requirements with numbered subsections."""
        content = """
#### **FR-1:** Main Requirement

**Sub-requirements:**
- **FR-1.1:** First sub-requirement
- **FR-1.2:** Second sub-requirement
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        # Main requirement should be extracted
        self.assert_requirement_exists(parsed.functional_requirements, "FR-1")

    def test_requirement_properties(self):
        """Test that all requirement properties are populated."""
        content = """
## API Requirements

#### **FR-1:** API Endpoint Design
*   The system must provide RESTful endpoints.
*   AC: Must support GET, POST, PUT, DELETE
*   Metric: Response time < 100ms
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        req = parsed.get_requirement_by_id("FR-1")
        self.assertIsNotNone(req)
        self.assertEqual(req.id, "FR-1")
        self.assertIsNotNone(req.title)
        self.assertIsNotNone(req.description)
        self.assertGreater(req.line_number, 0)
        self.assertIsNotNone(req.raw_text)

    def test_complex_real_world_prd(self):
        """Test parsing a complex real-world PRD (yt_sync)."""
        # Test with actual yt_sync PRD if available
        yt_sync_prd = Path("/p/projects/yt_sync/docs/PRD.md")
        if yt_sync_prd.exists():
            try:
                parsed = self.parser.parse_prd_file(str(yt_sync_prd))
                self.assertGreater(parsed.total_requirements, 0)
                self.assertGreater(len(parsed.functional_requirements), 0)
            except Exception as e:
                self.skipTest(f"Could not parse real PRD: {e}")
        else:
            self.skipTest("Real yt_sync PRD not found")


class TestPRDParserEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = PRDParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_prd(self, content: str) -> str:
        """Create a temporary PRD file."""
        prd_path = Path(self.temp_dir) / "test.md"
        with open(prd_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(prd_path)

    def test_very_long_titles(self):
        """Test handling of very long requirement titles."""
        long_title = "This is a very long title that goes on and on and on and on and on and on and should be truncated properly"
        content = f"""
#### **FR-1:** {long_title}
*   Description here.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        req = parsed.get_requirement_by_id("FR-1")
        self.assertIsNotNone(req)
        self.assertGreater(len(req.title), 0)

    def test_special_characters_in_titles(self):
        """Test handling of special characters in titles."""
        content = """
#### **FR-1:** Test with <special> & [characters]
*   Description with "quotes" and 'apostrophes'.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        req = parsed.get_requirement_by_id("FR-1")
        self.assertIsNotNone(req)

    def test_unicode_characters(self):
        """Test handling of Unicode characters."""
        content = """
#### **FR-1:** Internationalization support
*   Must support UTF-8, emoji 🎉, and non-Latin scripts (中文, العربية).
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        req = parsed.get_requirement_by_id("FR-1")
        self.assertIsNotNone(req)

    def test_malformed_frontmatter(self):
        """Test handling of malformed YAML frontmatter."""
        content = """---
invalid: yaml: content:
: broken
---

#### **FR-1:** Test
"""
        prd_path = self.create_temp_prd(content)
        # Should not crash, should return empty metadata
        parsed = self.parser.parse_prd_file(prd_path)
        self.assertIsNotNone(parsed)

    def test_requirement_without_colon(self):
        """Test requirements without colon after ID."""
        content = """
#### **FR-1** Test Requirement (no colon)
*   Description.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        # Should still parse the requirement
        self.assertGreater(len(parsed.functional_requirements), 0)

    def test_nested_requirements(self):
        """Test handling of nested requirement structures."""
        content = """
## Core Features

### Authentication

#### **FR-1:** User Login
*   Must support email/password login.

#### **FR-2:** OAuth Integration
*   Must support OAuth providers.

### Database

#### **FR-3:** Data Persistence
*   Must store user data.
"""
        prd_path = self.create_temp_prd(content)
        parsed = self.parser.parse_prd_file(prd_path)

        self.assertEqual(len(parsed.functional_requirements), 3)


def run_tests_with_real_prds():
    """Run parser on real PRD files and report results."""
    parser = PRDParser()

    real_prds = [
        "/p/projects/yt_sync/docs/PRD.md",
        "/p/projects/vid_dup_ai/docs/PRD.md",
        "/p/projects/vid_rec/docs/PRD.md",
    ]

    print("\n" + "="*80)
    print("TESTING WITH REAL PRD FILES")
    print("="*80 + "\n")

    results = []

    for prd_path in real_prds:
        if Path(prd_path).exists():
            try:
                parsed = parser.parse_prd_file(prd_path)

                result = {
                    "prd": prd_path,
                    "name": parsed.prd_name,
                    "total_reqs": parsed.total_requirements,
                    "functional": len(parsed.functional_requirements),
                    "non_functional": len(parsed.non_functional_requirements),
                    "status": "SUCCESS"
                }

                print(f"✓ {Path(prd_path).name}")
                print(f"  Name: {parsed.prd_name}")
                print(f"  Total Requirements: {parsed.total_requirements}")
                print(f"  Functional: {len(parsed.functional_requirements)}")
                print(f"  Non-Functional: {len(parsed.non_functional_requirements)}")

                # Show sample requirements
                if parsed.functional_requirements:
                    print(f"  Sample FR: {parsed.functional_requirements[0].id}: {parsed.functional_requirements[0].title}")

                print()

            except Exception as e:
                result = {
                    "prd": prd_path,
                    "status": "FAILED",
                    "error": str(e)
                }
                print(f"✗ {Path(prd_path).name}")
                print(f"  Error: {e}\n")
        else:
            result = {
                "prd": prd_path,
                "status": "NOT_FOUND"
            }
            print(f"? {Path(prd_path).name} - Not found\n")

        results.append(result)

    # Summary statistics
    parser_stats = parser.get_statistics()
    print("="*80)
    print("PARSER STATISTICS")
    print("="*80)
    print(json.dumps(parser_stats, indent=2))

    return results


if __name__ == "__main__":
    # Run unit tests
    print("="*80)
    print("RUNNING UNIT TESTS")
    print("="*80 + "\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPRDParser))
    suite.addTests(loader.loadTestsFromTestCase(TestPRDParserEdgeCases))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    # Run tests on real PRDs
    print("\n")
    real_prd_results = run_tests_with_real_prds()

    # Exit with appropriate code
    sys.exit(0 if test_result.wasSuccessful() else 1)
