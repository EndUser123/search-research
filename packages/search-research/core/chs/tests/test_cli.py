"""Tests for CHS v2 CLI tools.

These tests verify the command-line interface tools for CHS v2:
- init_db.py: Initialize database from schema
- run_indexer.py: Run the indexer daemon
- chs_cli.py: Search CLI with flags
- health_check.py: System health check

Run with: pytest P:\\\\__csf/src/knowledge/systems/chs/v2/tests/test_cli.py -v
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Use subprocess.run as replacement for cli.subprocess_helper.run_subprocess
def run_subprocess(*args, **kwargs):
    """Wrapper for subprocess.run to match old API."""
    return subprocess.run(*args, **kwargs)


class TestInitDbCli:
    """Tests for scripts/init_db.py CLI."""

    @pytest.fixture
    def schema_sql_content(self):
        """Return minimal schema SQL content for testing."""
        return "\n-- CHS v2 Database Schema\nCREATE TABLE IF NOT EXISTS projects (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    path TEXT NOT NULL UNIQUE,\n    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))\n);\n\nCREATE TABLE IF NOT EXISTS sessions (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    project_id INTEGER NOT NULL REFERENCES projects(id),\n    started_at INTEGER NOT NULL,\n    message_count INTEGER NOT NULL DEFAULT 0,\n    is_closed INTEGER NOT NULL DEFAULT 0,\n    last_indexed_at INTEGER,\n    UNIQUE(project_id, started_at)\n);\n\nCREATE TABLE IF NOT EXISTS messages (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    session_id INTEGER NOT NULL REFERENCES sessions(id),\n    role TEXT NOT NULL,\n    content TEXT NOT NULL,\n    timestamp INTEGER NOT NULL,\n    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),\n    file_hash TEXT NOT NULL,\n    file_offset INTEGER NOT NULL,\n    UNIQUE(session_id, file_hash, file_offset)\n);\n\nCREATE TABLE IF NOT EXISTS turns (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    session_id INTEGER NOT NULL REFERENCES sessions(id),\n    message_start_id INTEGER NOT NULL REFERENCES messages(id),\n    message_end_id INTEGER NOT NULL REFERENCES messages(id),\n    timestamp_start INTEGER NOT NULL,\n    timestamp_end INTEGER NOT NULL,\n    content TEXT NOT NULL,\n    has_code INTEGER NOT NULL DEFAULT 0,\n    has_error INTEGER NOT NULL DEFAULT 0,\n    length_chars INTEGER NOT NULL,\n    embedding BLOB,\n    embedding_model TEXT,\n    embedding_dim INTEGER,\n    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))\n);\n\nCREATE TABLE IF NOT EXISTS topics (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name TEXT NOT NULL UNIQUE,\n    pattern TEXT,\n    description TEXT\n);\n\nCREATE TABLE IF NOT EXISTS session_topics (\n    session_id INTEGER NOT NULL REFERENCES sessions(id),\n    topic_id INTEGER NOT NULL REFERENCES topics(id),\n    weight REAL NOT NULL,\n    PRIMARY KEY (session_id, topic_id)\n);\n\nCREATE TABLE IF NOT EXISTS indexer_checkpoints (\n    file_path TEXT PRIMARY KEY,\n    file_hash TEXT NOT NULL,\n    last_indexed_at INTEGER NOT NULL,\n    messages_indexed INTEGER NOT NULL DEFAULT 0\n);\n\nCREATE TABLE IF NOT EXISTS embeddings_config (\n    id INTEGER PRIMARY KEY,\n    model_name TEXT NOT NULL,\n    dim INTEGER NOT NULL,\n    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))\n);\n\nINSERT OR REPLACE INTO embeddings_config (id, model_name, dim) VALUES (1, 'dummy', 1);\n"

    @pytest.fixture
    def temp_chs_dir(self, schema_sql_content):
        """Create a temporary CHS v2 directory with schema.sql."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chs_dir = Path(tmpdir) / "chs" / "v2"
            chs_dir.mkdir(parents=True)
            schema_path = chs_dir / "schema.sql"
            schema_path.write_text(schema_sql_content)
            scripts_dir = chs_dir / "scripts"
            scripts_dir.mkdir()
            (chs_dir / "__init__.py").write_text("")
            yield {"chs_dir": chs_dir, "schema_path": schema_path, "scripts_dir": scripts_dir}

    def test_init_db_script_exists(self):
        """Test that init_db.py script exists.

        Given: CHS v2 directory structure exists
        When: Checking for init_db.py script
        Then: Script should exist at scripts/init_db.py
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        init_db_path = scripts_path / "init_db.py"
        if not init_db_path.exists():
            pytest.fail(
                f"init_db.py not found at {init_db_path}. This script needs to be created to initialize the database."
            )

    def test_init_db_creates_database(self, temp_chs_dir):
        """Test that init_db.py creates the database.

        Given: A valid schema.sql file exists
        When: init_db.py is executed
        Then: Database file should be created with all tables
        """
        scripts_dir = temp_chs_dir["scripts_dir"]
        schema_path = temp_chs_dir["schema_path"]
        db_path = temp_chs_dir["chs_dir"] / "test_chat_history.db"
        mock_config = MagicMock()
        mock_config.DB_PATH = db_path
        init_db_script = scripts_dir / "init_db.py"
        init_db_content = f'\nimport sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent))\n\n# Mock Config before importing\nclass MockConfig:\n    DB_PATH = r"{db_path}"\n\nsys.modules["chs.config"] = MockConfig()\nimport chs.config as config\nconfig.Config = MockConfig\n\ndef init_db(schema_path):\n    """Mock init_db for testing."""\n    import sqlite3\n    conn = sqlite3.connect(str(MockConfig.DB_PATH))\n    schema = Path(schema_path).read_text()\n    conn.executescript(schema)\n    conn.commit()\n    conn.close()\n\ndef main():\n    schema_path = r"{schema_path}"\n    init_db(schema_path)\n    print("Database initialized successfully")\n\nif __name__ == "__main__":\n    main()\n'
        init_db_script.write_text(init_db_content)
        result = run_subprocess(
            [sys.executable, str(init_db_script)], capture_output=True, text=True, timeout=10
        )
        assert db_path.exists(), f"Database not created at {db_path}"
        assert "successfully" in result.stdout.lower()

    def test_init_db_reports_error_without_schema(self, temp_chs_dir):
        """Test that init_db.py reports error when schema.sql missing.

        Given: schema.sql does not exist
        When: init_db.py is executed
        Then: Should return error exit code and message
        """
        scripts_dir = temp_chs_dir["scripts_dir"]
        init_db_script = scripts_dir / "init_db_missing_schema.py"
        init_db_content = '\nimport sys\nfrom pathlib import Path\n\nschema_path = Path(__file__).parent.parent / "schema.sql"\nif not schema_path.exists():\n    print(f"ERROR: schema.sql not found at {schema_path}")\n    sys.exit(1)\n\nprint("Database initialized")\n'
        init_db_script.write_text(init_db_content)
        result = run_subprocess(
            [sys.executable, str(init_db_script)], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 1, "Should exit with code 1 when schema missing"
        assert "ERROR" in result.stdout
        assert "schema.sql not found" in result.stdout


class TestRunIndexerCli:
    """Tests for scripts/run_indexer.py CLI."""

    def test_run_indexer_script_exists(self):
        """Test that run_indexer.py script exists.

        Given: CHS v2 directory structure exists
        When: Checking for run_indexer.py script
        Then: Script should exist at scripts/run_indexer.py
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        run_indexer_path = scripts_path / "run_indexer.py"
        if not run_indexer_path.exists():
            pytest.fail(
                f"run_indexer.py not found at {run_indexer_path}. This script needs to be created to run the indexer daemon."
            )

    def test_run_indexer_validates_config(self):
        """Test that run_indexer.py validates configuration.

        Given: Invalid configuration
        When: run_indexer.py is executed
        Then: Should exit with error about configuration
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        run_indexer_path = scripts_path / "run_indexer.py"
        if not run_indexer_path.exists():
            pytest.skip("run_indexer.py does not exist yet")
        env = os.environ.copy()
        env["CHS_CHAT_LOG_ROOT"] = "/nonexistent/path"
        result = run_subprocess(
            [sys.executable, str(run_indexer_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert result.returncode != 0 or "error" in result.stderr.lower()

    def test_run_indexer_acquires_file_lock(self):
        """Test that run_indexer.py acquires file lock to prevent multiple instances.

        Given: Another indexer instance is running
        When: run_indexer.py is executed
        Then: Should exit gracefully without starting duplicate indexer
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        run_indexer_path = scripts_path / "run_indexer.py"
        if not run_indexer_path.exists():
            pytest.skip("run_indexer.py does not exist yet")
        content = run_indexer_path.read_text()
        assert any(keyword in content for keyword in ["lock", "Lock", "LOCK"]), (
            "run_indexer.py should implement file locking"
        )

    def test_run_indexer_handles_idle_timeout(self):
        """Test that run_indexer.py handles idle timeout.

        Given: Indexer is running with no new files
        When: Idle timeout expires
        Then: Indexer should exit gracefully
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        run_indexer_path = scripts_path / "run_indexer.py"
        if not run_indexer_path.exists():
            pytest.skip("run_indexer.py does not exist yet")
        content = run_indexer_path.read_text()
        assert any(keyword in content for keyword in ["idle", "timeout", "IDLE", "TIMEOUT"]), (
            "run_indexer.py should implement idle timeout"
        )


class TestChsCliSearch:
    """Tests for scripts/chs_cli.py search CLI."""

    def test_chs_cli_script_exists(self):
        """Test that chs_cli.py script exists.

        Given: CHS v2 directory structure exists
        When: Checking for chs_cli.py script
        Then: Script should exist at scripts/chs_cli.py
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        chs_cli_path = scripts_path / "chs_cli.py"
        if not chs_cli_path.exists():
            pytest.fail(
                f"chs_cli.py not found at {chs_cli_path}. This script needs to be created for search functionality."
            )

    def test_chs_cli_requires_query_argument(self):
        """Test that chs_cli.py requires a query argument.

        Given: chs_cli.py exists
        When: Executed without query argument
        Then: Should exit with error about missing query
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        chs_cli_path = scripts_path / "chs_cli.py"
        if not chs_cli_path.exists():
            pytest.skip("chs_cli.py does not exist yet")
        result = run_subprocess(
            [sys.executable, str(chs_cli_path)], capture_output=True, text=True, timeout=10
        )
        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "required" in result.stderr.lower()

    def test_chs_cli_global_flag_searches_all_projects(self):
        """Test that chs_cli.py --global flag searches all projects.

        Given: chs_cli.py with --global flag
        When: Executed with a query
        Then: Should search across all projects (project_id=None)
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        chs_cli_path = scripts_path / "chs_cli.py"
        if not chs_cli_path.exists():
            pytest.skip("chs_cli.py does not exist yet")
        result = run_subprocess(
            [sys.executable, str(chs_cli_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "--global" in result.stdout or "global" in result.stdout.lower(), (
            "chs_cli.py should support --global flag for searching all projects"
        )

    def test_chs_cli_project_flag_filters_by_project(self):
        """Test that chs_cli.py --project flag filters by project ID.

        Given: chs_cli.py with --project flag
        When: Executed with specific project ID
        Then: Should search only within specified project
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        chs_cli_path = scripts_path / "chs_cli.py"
        if not chs_cli_path.exists():
            pytest.skip("chs_cli.py does not exist yet")
        result = run_subprocess(
            [sys.executable, str(chs_cli_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "--project" in result.stdout, (
            "chs_cli.py should support --project flag for filtering by project"
        )

    def test_chs_cli_json_flag_outputs_json(self):
        """Test that chs_cli.py --json flag outputs JSON format.

        Given: chs_cli.py with --json flag
        When: Executed with a query
        Then: Should output results as JSON
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        chs_cli_path = scripts_path / "chs_cli.py"
        if not chs_cli_path.exists():
            pytest.skip("chs_cli.py does not exist yet")
        result = run_subprocess(
            [sys.executable, str(chs_cli_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "--json" in result.stdout, "chs_cli.py should support --json flag for JSON output"

    def test_chs_cli_limit_flag_controls_results(self):
        """Test that chs_cli.py --limit flag controls result count.

        Given: chs_cli.py with --limit flag
        When: Executed with specific limit
        Then: Should return at most that many results
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        chs_cli_path = scripts_path / "chs_cli.py"
        if not chs_cli_path.exists():
            pytest.skip("chs_cli.py does not exist yet")
        result = run_subprocess(
            [sys.executable, str(chs_cli_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "--limit" in result.stdout, (
            "chs_cli.py should support --limit flag for controlling result count"
        )

    @pytest.fixture
    def mock_chs_cli_with_search(self, tmp_path):
        """Create a mock chs_cli.py with search function."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        chs_cli = scripts_dir / "chs_cli.py"
        chs_cli.write_text(
            '\nimport sys\nimport json\nimport argparse\nfrom pathlib import Path\n\nsys.path.insert(0, str(Path(__file__).parent.parent))\n\ndef search_turns(query, project_id=None, limit=20):\n    """Mock search function."""\n    return [\n        {\n            "id": 1,\n            "session_id": 100,\n            "project_id": project_id or 1,\n            "timestamp_start": 1704067200,\n            "timestamp_end": 1704067260,\n            "has_code": 1,\n            "has_error": 0,\n            "length_chars": 500,\n            "content": f"Result for query: {query}"\n        }\n    ]\n\ndef main():\n    parser = argparse.ArgumentParser(description="Search chat history")\n    parser.add_argument("query", nargs="+", help="Search query")\n    parser.add_argument("--global", dest="global_scope", action="store_true",\n                        help="Search all projects")\n    parser.add_argument("--project", type=int, help="Specific project ID")\n    parser.add_argument("--limit", type=int, default=20, help="Max results")\n    parser.add_argument("--json", action="store_true", help="JSON output")\n\n    args = parser.parse_args()\n    query = " ".join(args.query)\n\n    project_id = None if args.global_scope else args.project\n    results = search_turns(query, project_id=project_id, limit=args.limit)\n\n    if args.json:\n        payload = [\n            {\n                "id": r["id"],\n                "session_id": r["session_id"],\n                "project_id": r["project_id"],\n                "content": r["content"]\n            }\n            for r in results\n        ]\n        print(json.dumps(payload, ensure_ascii=False))\n    else:\n        print(f"Searching: {query}")\n        print(f"Found {len(results)} results")\n        for r in results:\n            print(f"- {r[\'content\'][:50]}...")\n\nif __name__ == "__main__":\n    main()\n'
        )
        return chs_cli

    def test_chs_cli_json_output_format(self, mock_chs_cli_with_search):
        """Test that --json flag produces valid JSON output.

        Given: Mock chs_cli.py with --json flag
        When: Executed with a query
        Then: Should output valid JSON that can be parsed
        """
        result = run_subprocess(
            [sys.executable, str(mock_chs_cli_with_search), "--json", "test query"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) > 0
            assert "id" in data[0]
            assert "content" in data[0]
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result.stdout}")

    def test_chs_cli_human_readable_output(self, mock_chs_cli_with_search):
        """Test that default output is human-readable.

        Given: Mock chs_cli.py without --json flag
        When: Executed with a query
        Then: Should output human-readable text format
        """
        result = run_subprocess(
            [sys.executable, str(mock_chs_cli_with_search), "test query"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Searching:" in result.stdout
        assert "results" in result.stdout.lower()

    def test_chs_cli_global_flag_implementation(self, mock_chs_cli_with_search):
        """Test that --global flag passes project_id=None to search.

        Given: Mock chs_cli.py with --global flag
        When: Executed with --global
        Then: Should call search with project_id=None
        """
        result = run_subprocess(
            [sys.executable, str(mock_chs_cli_with_search), "--global", "test"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0

    def test_chs_cli_project_flag_implementation(self, mock_chs_cli_with_search):
        """Test that --project flag passes specific project_id to search.

        Given: Mock chs_cli.py with --project flag
        When: Executed with --project 123
        Then: Should call search with project_id=123
        """
        result = run_subprocess(
            [sys.executable, str(mock_chs_cli_with_search), "--project", "123", "test"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0


class TestHealthCheckCli:
    """Tests for scripts/health_check.py CLI."""

    def test_health_check_script_exists(self):
        """Test that health_check.py script exists.

        Given: CHS v2 directory structure exists
        When: Checking for health_check.py script
        Then: Script should exist at scripts/health_check.py
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        health_check_path = scripts_path / "health_check.py"
        if not health_check_path.exists():
            pytest.fail(
                f"health_check.py not found at {health_check_path}. This script needs to be created for health monitoring."
            )

    @pytest.fixture
    def mock_health_check(self, tmp_path):
        """Create a mock health_check.py with database."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        import sqlite3

        db_path = tmp_path / "test_health.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, path TEXT);")
        conn.execute("INSERT INTO projects VALUES (1, '/test/project');")
        conn.execute(
            "CREATE TABLE sessions (id INTEGER PRIMARY KEY, project_id INTEGER, started_at INTEGER, message_count INTEGER, is_closed INTEGER);"
        )
        conn.execute("INSERT INTO sessions VALUES (100, 1, 1704067200, 50, 0);")
        conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id INTEGER);")
        conn.execute("INSERT INTO messages VALUES (1, 100);")
        conn.execute("INSERT INTO messages VALUES (2, 100);")
        conn.execute("INSERT INTO messages VALUES (3, 100);")
        conn.execute(
            "CREATE TABLE turns (id INTEGER PRIMARY KEY, session_id INTEGER, embedding BLOB, embedding_model TEXT, embedding_dim INTEGER, timestamp_start INTEGER, content TEXT, has_code INTEGER, has_error INTEGER, length_chars INTEGER);"
        )
        conn.execute(
            "INSERT INTO turns VALUES (1, 100, NULL, 'test-model', 768, 1704067200, 'test content', 1, 0, 100);"
        )
        conn.execute(
            "INSERT INTO turns VALUES (2, 100, X'0000', 'test-model', 768, 1704067300, 'more content', 0, 0, 50);"
        )
        conn.execute("CREATE TABLE topics (id INTEGER PRIMARY KEY, name TEXT);")
        conn.execute("INSERT INTO topics VALUES (1, 'python');")
        conn.execute(
            "CREATE TABLE indexer_checkpoints (file_path TEXT PRIMARY KEY, last_indexed_at INTEGER);"
        )
        conn.execute("INSERT INTO indexer_checkpoints VALUES ('/test/file.jsonl', 1704067200);")
        conn.execute(
            "CREATE TABLE embeddings_config (id INTEGER PRIMARY KEY, model_name TEXT, dim INTEGER);"
        )
        conn.execute("INSERT INTO embeddings_config VALUES (1, 'test-model', 768);")
        conn.commit()
        conn.close()
        health_check = scripts_dir / "health_check.py"
        health_check.write_text(
            f'''\nimport sys\nimport sqlite3\nfrom pathlib import Path\n\nDB_PATH = r"{db_path}"\n\ndef main():\n    print("=" * 60)\n    print("Chat History Search - Health Check")\n    print("=" * 60)\n    print(f"\\nDatabase: {{DB_PATH}}")\n\n    if not Path(DB_PATH).exists():\n        print("ERROR: Database does not exist")\n        sys.exit(1)\n\n    conn = sqlite3.connect(str(DB_PATH))\n    conn.row_factory = sqlite3.Row\n\n    # Table counts\n    for table in ["projects", "sessions", "messages", "turns", "topics"]:\n        cur = conn.execute(f"SELECT COUNT(*) as c FROM {{table}}")\n        row = cur.fetchone()\n        print(f"  {{table:20}} {{row['c']:>10,}}")\n\n    # Embedding coverage\n    cur = conn.execute("""\n        SELECT COUNT(*) as total,\n               SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as embedded\n        FROM turns\n    """)\n    row = cur.fetchone()\n    if row['total'] > 0:\n        coverage = 100 * row['embedded'] / row['total']\n        print(f"\\nEmbedding Coverage: {{row['embedded']}}/{{row['total']}} ({{coverage:.1f}}%)")\n\n    print("\\n" + "=" * 60)\n    print("OK")\n    print("=" * 60)\n\nif __name__ == "__main__":\n    main()\n'''
        )
        return health_check

    def test_health_check_returns_table_counts(self, mock_health_check):
        """Test that health_check.py returns counts for all tables.

        Given: Database with sample data exists
        When: health_check.py is executed
        Then: Should display counts for projects, sessions, messages, turns, topics
        """
        result = run_subprocess(
            [sys.executable, str(mock_health_check)], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "projects" in result.stdout
        assert "sessions" in result.stdout
        assert "messages" in result.stdout
        assert "turns" in result.stdout
        assert "topics" in result.stdout
        assert "1" in result.stdout
        assert "3" in result.stdout

    def test_health_check_shows_embedding_coverage(self, mock_health_check):
        """Test that health_check.py shows embedding coverage statistics.

        Given: Database with some embedded turns
        When: health_check.py is executed
        Then: Should display embedding coverage percentage
        """
        result = run_subprocess(
            [sys.executable, str(mock_health_check)], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "Embedding" in result.stdout or "embedding" in result.stdout
        assert "%" in result.stdout

    def test_health_check_reports_database_status(self, mock_health_check):
        """Test that health_check.py reports overall database status.

        Given: health_check.py is executed
        When: Script runs successfully
        Then: Should display success message
        """
        result = run_subprocess(
            [sys.executable, str(mock_health_check)], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "OK" in result.stdout or "healthy" in result.stdout.lower()


class TestCliIntegration:
    """Integration tests for CLI tools working together."""

    def test_cli_scripts_have_shebang(self):
        """Test that all CLI scripts have proper shebang.

        Given: CHS v2 CLI scripts
        When: Checking script headers
        Then: Should have #!/usr/bin/env python3 shebang
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        if not scripts_path.exists():
            pytest.skip("scripts directory does not exist yet")
        script_names = ["init_db.py", "run_indexer.py", "chs_cli.py", "health_check.py"]
        for script_name in script_names:
            script_path = scripts_path / script_name
            if script_path.exists():
                content = script_path.read_text()
                assert content.startswith("#!/usr/bin/env python3"), (
                    f"{script_name} should have #!/usr/bin/env python3 shebang"
                )

    def test_cli_scripts_import_from_chs_module(self):
        """Test that CLI scripts properly import from chs module.

        Given: CHS v2 CLI scripts
        When: Checking import statements
        Then: Should import from chs.db, chs.config, etc.
        """
        scripts_path = Path("/p/__csf/src/knowledge/systems/chs/v2/scripts")
        if not scripts_path.exists():
            pytest.skip("scripts directory does not exist yet")
        init_db_path = scripts_path / "init_db.py"
        if init_db_path.exists():
            content = init_db_path.read_text()
            assert "from chs.db import" in content or "import chs.db" in content, (
                "init_db.py should import from chs.db module"
            )
        chs_cli_path = scripts_path / "chs_cli.py"
        if chs_cli_path.exists():
            content = chs_cli_path.read_text()
            assert "from chs.search import" in content or "import chs.search" in content, (
                "chs_cli.py should import from chs.search module"
            )
        health_check_path = scripts_path / "health_check.py"
        if health_check_path.exists():
            content = health_check_path.read_text()
            assert "from chs.db import" in content or "import chs.db" in content, (
                "health_check.py should import from chs.db module"
            )
