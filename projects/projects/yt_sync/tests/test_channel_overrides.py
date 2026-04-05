import argparse
import tempfile
import unittest
from pathlib import Path

import yaml
from yt_sync.main_logic import apply_config_to_args, load_configuration


class TestChannelOverrides(unittest.TestCase):
    def setUp(self):
        # Create a temporary config file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.yaml"

        # Create a sample config with channel overrides
        config_content = {
            "base_dir": "/tmp/youtube",
            "url_file": "channels.txt",
            "filters": {
                "require_title": ["video", "tutorial"],
                "reject_title": ["trailer", "ad"],
            },
            "channel_overrides": {
                "TechTutorials": {
                    "skip": True,
                    "filters": {
                        "require_title": ["tech", "review"],
                        "reject_title": ["sponsor", "ad"],
                    },
                },
                "NewsNetwork": {
                    "filters": {
                        "require_category": "News & Politics",
                        "min_duration": 300,
                    }
                },
            },
        }

        # Write the config to the temporary file
        with open(self.config_path, "w") as f:
            yaml.dump(config_content, f)

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def test_load_configuration(self):
        """Test that channel_overrides are properly loaded from config."""
        config = load_configuration(self.config_path)
        self.assertIn("channel_overrides", config)
        self.assertIn("TechTutorials", config["channel_overrides"])
        self.assertIn("skip", config["channel_overrides"]["TechTutorials"])
        self.assertTrue(config["channel_overrides"]["TechTutorials"]["skip"])

    def test_apply_config_to_args(self):
        """Test that channel_overrides are properly applied to args."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--config", default="config.yaml")
        args = parser.parse_args(["--config", str(self.config_path)])

        config = load_configuration(self.config_path)
        apply_config_to_args(args, config)

        self.assertIn("channel_overrides", vars(args))
        self.assertIn("TechTutorials", args.channel_overrides)
        self.assertTrue(args.channel_overrides["TechTutorials"].get("skip"))


if __name__ == "__main__":
    unittest.main()
