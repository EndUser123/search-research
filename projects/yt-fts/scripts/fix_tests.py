from pathlib import Path

test_file = Path("../tests/yt_fts/core/test_search_characterization.py")
content = test_file.read_text()

# Fix the channel tests - use actual channel name from test DB
old_code = '''    def test_channel_flag_resolves_channel_id(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "criminal", "-c", "1", "--fts-only"], env=env)
        assert result.exit_code == 0

    def test_channel_search_json_format_suppresses_resolution_output(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "criminal", "-c", "1", "--format", "json"], env=env)
        assert result.exit_code == 0'''

new_code = '''    def test_channel_flag_resolves_channel_id(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        # Use actual channel name from test DB (Sean Kochel)
        result = runner.invoke(cli, ["search", "code", "-c", "Sean Kochel", "--fts-only"], env=env)
        assert result.exit_code == 0

    def test_channel_search_json_format_suppresses_resolution_output(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        # Use actual channel name from test DB
        result = runner.invoke(cli, ["search", "code", "-c", "Sean Kochel", "--format", "json"], env=env)
        assert result.exit_code == 0'''

content = content.replace(old_code, new_code)
test_file.write_text(content, encoding="utf-8")
print("Fixed channel tests")
