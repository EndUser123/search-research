"""Tests for artifact command help discovery."""
import sys
from pathlib import Path
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).parent))

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class TestArtifactCommandDiscovery(TestCase):
    """Test that artifact commands are discoverable in the help system."""

    def test_artifact_add_markdown_exists(self):
        """artifact-add.md should exist for help discovery."""
        md_path = Path(__file__).parent.parent / "commands" / "artifact-add.md"
        self.assertTrue(md_path.exists(), f"artifact-add.md should exist at {md_path}")

    def test_artifact_audit_markdown_exists(self):
        """artifact-audit.md should exist for help discovery."""
        md_path = Path(__file__).parent.parent / "commands" / "artifact-audit.md"
        self.assertTrue(md_path.exists(), f"artifact-audit.md should exist at {md_path}")

    def test_artifact_done_markdown_exists(self):
        """artifact-done.md should exist for help discovery."""
        md_path = Path(__file__).parent.parent / "commands" / "artifact-done.md"
        self.assertTrue(md_path.exists(), f"artifact-done.md should exist at {md_path}")

    def test_artifact_commands_in_registry(self):
        """Artifact commands should be registered in commands.toml."""
        registry_path = Path(__file__).parent.parent / "registry" / "commands.toml"
        self.assertTrue(registry_path.exists(), f"Registry should exist at {registry_path}")

        with open(registry_path, "rb") as f:
            registry = tomllib.load(f)

        # Check for artifact commands (registry uses underscores)
        commands = registry.get("commands", {})
        self.assertIn("artifact_add", commands, "artifact_add should be in registry")
        self.assertIn("artifact_audit", commands, "artifact_audit should be in registry")
        self.assertIn("artifact_done", commands, "artifact_done should be in registry")

    def test_artifact_add_has_required_metadata(self):
        """artifact-add should have proper frontmatter metadata."""
        md_path = Path(__file__).parent / "artifact-add.md"
        if not md_path.exists():
            self.skipTest("artifact-add.md doesn't exist yet")

        content = md_path.read_text()
        # Check for frontmatter markers
        self.assertIn("aliases", content, "Should have aliases field")
        self.assertIn("category", content, "Should have category field")
        self.assertIn("/artifact-add", content, "Should list /artifact-add alias")


if __name__ == "__main__":
    import unittest
    unittest.main()
