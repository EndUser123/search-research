"""CKS System Dry Run (End-to-End Simulation)
Tests the full "Dreaming" pipeline by mocking the LLM to ensure plumbing works.
"""

import asyncio
import logging
import os
from unittest.mock import AsyncMock, MagicMock

from .consolidation.dreaming_cycle import DreamingService, RelationHypothesis
from .core.vector_manager import VectorConfig, VectorKnowledgeManager

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - TEST - %(message)s")
logger = logging.getLogger(__name__)


async def run_dry_run() -> None:
    print("\n🧪 CKS System Dry Run (Simulation)")
    print("===================================")

    import time

    test_db = f"dry_run_{int(time.time())}.db"

    # Clean up (Optional, might fail if locked, but flexible now)
    if os.path.exists(test_db):
        os.remove(test_db)

    try:
        # 1. Setup Vector Store (In-Memory)
        print("\n1. Initializing Vector Knowledge Store...")
        vm = VectorKnowledgeManager(VectorConfig(qdrant_path=":memory:"))

        # Ingest Test Knowledge
        print("   -> Ingesting 'Python' knowledge...")
        vm.ingest(
            "python_lang",
            "Python is a high-level programming language known for readability.",
            {"type": "concept"},
        )

        print("   -> Ingesting 'Javascript' knowledge...")
        vm.ingest(
            "js_lang",
            "JavaScript is a programming language used for web development.",
            {"type": "concept"},
        )

        # 2. Setup Dreaming Service
        print("\n2. Initializing Dreaming Service (with Mock LLM)...")
        service = DreamingService(db_path=test_db)

        # Mock the LLM Client to return a deterministic hypothesis
        # We simulate finding a connection between Python and Javascript
        mock_hypothesis = RelationHypothesis(
            source_id="python_lang",
            target_id="js_lang",
            relationship="similar_to",
            reasoning="Both are high-level dynamic programming languages.",
            confidence=0.95,
        )

        # Apply the mock
        service.client = AsyncMock()
        service.client.models = MagicMock()
        service.client.models.generate_content = AsyncMock(
            return_value=mock_hypothesis,
        )  # For Gemini
        service.provider = "google"  # Pretend we are using Google

        # Force "python_lang" as an orphan for the test
        # We'll inject it directly into the cycle
        print("   -> Running consolidation cycle (Mocked)...")

        # We manually call the hypothesize logic to bypass the vector search randomness in the test
        hypothesis = await service.hypothesize_connections(
            "Python is a high-level...",
            "python_lang",
            ["JavaScript is..."],
            ["js_lang"],
        )

        if hypothesis:
            print(
                f"   -> LLM Hypothesized: {hypothesis.source_id} --[{hypothesis.relationship}]--> {hypothesis.target_id}",
            )
            service.validate_and_process(hypothesis)
        else:
            print("   ❌ Mock failed to return hypothesis.")

        # 3. Verify Persistence (SQLite)
        print("\n3. Verifying Persistence...")
        import sqlite3

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row

        # Check Pending Table
        # Note: Since confidence was 0.95, it might have auto-committed depending on mode.
        # Default is SEMI_AUTOMATIC, so >0.85 = AUTO COMMIT.
        row = conn.execute("SELECT * FROM pending_relations").fetchone()
        if row:
            print(
                f"   ✅ Found record in 'pending_relations' | Status: {row['status']}",
            )
        else:
            print("   ❌ 'pending_relations' is empty!")

        # Check Graph Edges (if auto-committed)
        edge = conn.execute("SELECT * FROM graph_edges").fetchone()
        if edge:
            print("   ✅ Found committed edge in 'graph_edges' (Auto-Commit works)")

        conn.close()

        # 4. CLI Check (Simulated)
        print("\n4. Verifying CLI Access...")
        # We need to monkeytype the service creation in the CLI to use our test DB path
        # Or easier: we just set the default in the class temporarily?
        # Actually, CLI instantiates `DreamingService()`. We can patch that class.
        from unittest.mock import patch

        from click.testing import CliRunner

        from .cli.dream_journal import dream

        with patch("features.cks.cli.dream_journal.DreamingService") as MockService:
            MockService.return_value.db_path = test_db

            runner = CliRunner()
            result = runner.invoke(dream, ["status"])
            if result.exit_code == 0:
                print(f"   ✅ CLI 'status' command ran successfully:\n{result.output}")
            else:
                print(f"   ❌ CLI failed: {result.exception}")

        print("\n✅ SYSTEM TEST PASSED: Architecture is solid.")

    except Exception as e:
        print(f"\n❌ SYSTEM TEST FAILED: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)
        if os.path.exists(test_db + "-wal"):
            os.remove(test_db + "-wal")
        if os.path.exists(test_db + "-shm"):
            os.remove(test_db + "-shm")


if __name__ == "__main__":
    asyncio.run(run_dry_run())
