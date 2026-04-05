import toml
from config_loader import ConfigLoader


def test_config_loader_locates_config_toml(tmp_path):
    """
    RED test: Ensure ConfigLoader can locate and parse config.toml
    in a 'config' subdirectory relative to its base_path.
    """
    # 1. Create a temporary 'config' directory
    temp_config_dir = tmp_path / "config"
    temp_config_dir.mkdir()

    # 2. Place a dummy config.toml inside this temporary 'config' directory
    dummy_config_content = {
        "app": {"name": "TestApp", "version": "1.0"},
        "database": {"host": "localhost", "port": 5432},
    }
    dummy_config_file = temp_config_dir / "config.toml"
    with open(dummy_config_file, "w") as f:
        toml.dump(dummy_config_content, f)

    # 3. Instantiate the ConfigLoader with the tmp_path as base_path
    loader = ConfigLoader(tmp_path)

    # 4. Assert that the ConfigLoader correctly finds and parses the content
    loaded_config = loader.get_config()
    assert loaded_config == dummy_config_content
