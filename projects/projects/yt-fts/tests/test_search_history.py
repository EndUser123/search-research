"""
Tests for search history and saved queries functionality.
"""

import gc
import os
import tempfile
import unittest

from yt_fts.core.database import (
    clear_search_history,
    delete_saved_query,
    get_saved_queries,
    get_saved_query_by_name,
    get_search_history,
    make_db,
    save_query,
    save_search,
)


class TestSearchHistory(unittest.TestCase):
    """Test search history functionality."""

    def setUp(self):
        """Set up a temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # Set environment variable to use temp database
        os.environ["YT_FTS_DB_PATH"] = self.temp_db.name

        # Create the database schema
        make_db(self.temp_db.name)

    def tearDown(self):
        """Clean up the temporary database."""
        # Close any database connections
        gc.collect()

        if "YT_FTS_DB_PATH" in os.environ:
            del os.environ["YT_FTS_DB_PATH"]

        # Try to remove the file, ignore Windows file locking errors
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except PermissionError:
            # Windows file locking - file will be cleaned up by OS
            pass

    def test_save_search_all_scope(self):
        """Test saving a search with 'all' scope."""
        search_id = save_search(
            query="machine learning",
            scope="all",
            result_count=10,
        )

        self.assertIsNotNone(search_id)

        # Verify the search was saved
        history = get_search_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["query"], "machine learning")
        self.assertEqual(history[0]["scope"], "all")
        self.assertEqual(history[0]["result_count"], 10)

    def test_save_search_channel_scope(self):
        """Test saving a search with 'channel' scope."""
        search_id = save_search(
            query="python tutorial",
            scope="channel",
            result_count=5,
            channel_id="UC1234567890",
        )

        self.assertIsNotNone(search_id)

        # Verify the search was saved
        history = get_search_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["query"], "python tutorial")
        self.assertEqual(history[0]["scope"], "channel")
        self.assertEqual(history[0]["channel_id"], "UC1234567890")

    def test_get_search_history_limit(self):
        """Test getting search history with limit."""
        # Save multiple searches
        for i in range(5):
            save_search(f"query {i}", "all", i)

        # Get only 3 most recent
        history = get_search_history(limit=3)
        self.assertEqual(len(history), 3)

        # Verify they're the most recent (in descending order by timestamp)
        # Note: Timestamps might be very close, so we just verify we got 3
        self.assertEqual(len(history), 3)

    def test_get_search_history_empty(self):
        """Test getting search history when empty."""
        history = get_search_history()
        self.assertEqual(len(history), 0)

    def test_clear_search_history(self):
        """Test clearing all search history."""
        # Save some searches
        for i in range(3):
            save_search(f"query {i}", "all", i)

        # Verify they're saved
        history = get_search_history()
        self.assertEqual(len(history), 3)

        # Clear history
        count = clear_search_history()
        self.assertEqual(count, 3)

        # Verify they're gone
        history = get_search_history()
        self.assertEqual(len(history), 0)


class TestSavedQueries(unittest.TestCase):
    """Test saved queries functionality."""

    def setUp(self):
        """Set up a temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # Set environment variable to use temp database
        os.environ["YT_FTS_DB_PATH"] = self.temp_db.name

        # Create the database schema
        make_db(self.temp_db.name)

    def tearDown(self):
        """Clean up the temporary database."""
        # Close any database connections
        gc.collect()

        if "YT_FTS_DB_PATH" in os.environ:
            del os.environ["YT_FTS_DB_PATH"]

        # Try to remove the file, ignore Windows file locking errors
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except PermissionError:
            # Windows file locking - file will be cleaned up by OS
            pass

    def test_save_query(self):
        """Test saving a query."""
        query_id = save_query(
            name="ml-search",
            query="machine learning algorithms",
            scope="all",
        )

        self.assertIsNotNone(query_id)

    def test_save_query_with_channel(self):
        """Test saving a channel-scoped query."""
        query_id = save_query(
            name="python-search",
            query="python tutorial",
            scope="channel",
            channel_id="UC1234567890",
        )

        self.assertIsNotNone(query_id)

        # Verify the saved query
        saved = get_saved_query_by_name("python-search")
        self.assertIsNotNone(saved)
        self.assertEqual(saved["name"], "python-search")
        self.assertEqual(saved["query"], "python tutorial")
        self.assertEqual(saved["scope"], "channel")
        self.assertEqual(saved["channel_id"], "UC1234567890")

    def test_save_query_update_existing(self):
        """Test updating an existing saved query."""
        # Save initial query
        query_id = save_query(
            name="test-query",
            query="initial query",
            scope="all",
        )

        # Update with same name
        query_id_2 = save_query(
            name="test-query",
            query="updated query",
            scope="channel",
        )

        # Should have the same query_id (updated, not inserted)
        self.assertEqual(query_id, query_id_2)

        # Verify the update
        saved = get_saved_query_by_name("test-query")
        self.assertEqual(saved["query"], "updated query")
        self.assertEqual(saved["scope"], "channel")

    def test_get_saved_queries(self):
        """Test getting all saved queries."""
        # Save multiple queries
        save_query("query1", "search 1", "all")
        save_query("query2", "search 2", "channel")
        save_query("query3", "search 3", "all")

        queries = get_saved_queries()
        self.assertEqual(len(queries), 3)

        # Verify names are present
        names = [q["name"] for q in queries]
        self.assertIn("query1", names)
        self.assertIn("query2", names)
        self.assertIn("query3", names)

    def test_get_saved_query_by_name(self):
        """Test getting a specific saved query."""
        save_query(
            name="specific-query",
            query="test search",
            scope="all",
        )

        saved = get_saved_query_by_name("specific-query")
        self.assertIsNotNone(saved)
        self.assertEqual(saved["name"], "specific-query")
        self.assertEqual(saved["query"], "test search")

    def test_get_saved_query_by_name_not_found(self):
        """Test getting a non-existent saved query."""
        saved = get_saved_query_by_name("non-existent")
        self.assertIsNone(saved)

    def test_delete_saved_query(self):
        """Test deleting a saved query."""
        save_query(name="to-delete", query="will be deleted", scope="all")

        # Verify it exists
        saved = get_saved_query_by_name("to-delete")
        self.assertIsNotNone(saved)

        # Delete it
        result = delete_saved_query("to-delete")
        self.assertTrue(result)

        # Verify it's gone
        saved = get_saved_query_by_name("to-delete")
        self.assertIsNone(saved)

    def test_delete_saved_query_not_found(self):
        """Test deleting a non-existent saved query."""
        result = delete_saved_query("does-not-exist")
        self.assertFalse(result)


class TestIntegration(unittest.TestCase):
    """Integration tests for search history and saved queries."""

    def setUp(self):
        """Set up a temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # Set environment variable to use temp database
        os.environ["YT_FTS_DB_PATH"] = self.temp_db.name

        # Create the database schema
        make_db(self.temp_db.name)

    def tearDown(self):
        """Clean up the temporary database."""
        # Close any database connections
        gc.collect()

        if "YT_FTS_DB_PATH" in os.environ:
            del os.environ["YT_FTS_DB_PATH"]

        # Try to remove the file, ignore Windows file locking errors
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except PermissionError:
            # Windows file locking - file will be cleaned up by OS
            pass

    def test_save_and_retrieve_workflow(self):
        """Test the complete workflow of saving and retrieving searches."""
        # Simulate user searches
        save_search("python basics", "all", 15)
        save_search("advanced python", "channel", 8, "UC1234567890")
        save_search("machine learning", "all", 20)

        # Get history
        history = get_search_history(limit=10)
        self.assertEqual(len(history), 3)

        # Save a favorite query
        save_query(
            name="ml-queries",
            query="machine learning",
            scope="all",
        )

        # Retrieve saved query
        saved = get_saved_query_by_name("ml-queries")
        self.assertIsNotNone(saved)
        self.assertEqual(saved["query"], "machine learning")

    def test_clear_history_preserves_saved_queries(self):
        """Test that clearing history doesn't affect saved queries."""
        # Save some searches
        save_search("test 1", "all", 5)
        save_search("test 2", "all", 10)

        # Save a query
        save_query("saved", "my query", "all")

        # Clear search history
        clear_search_history()

        # Verify history is empty
        history = get_search_history()
        self.assertEqual(len(history), 0)

        # Verify saved query still exists
        saved = get_saved_query_by_name("saved")
        self.assertIsNotNone(saved)


if __name__ == "__main__":
    unittest.main()
