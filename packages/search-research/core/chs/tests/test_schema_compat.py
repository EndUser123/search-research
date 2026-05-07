"""Test CHS schema compatibility layer."""

import sys

sys.path.insert(0, "P:\\\\__csf/src")
import sqlite3
from pathlib import Path

from .schema_compat import CHSSchemaCompat, SchemaVersion

db_path = Path("P:\\\\__csf/data/chat_history.db")
print("=== Testing CHS Schema Compatibility Layer ===\n")
print("Test 1: Database exists")
print(f"  Path: {db_path}")
print(f"  Exists: {db_path.exists()}")
print()
if not db_path.exists():
    print("ERROR: Database file not found, cannot continue testing")
    sys.exit(1)
print("Test 2: Connect to database")
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("  Status: Connected successfully")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)
print()
print("Test 3: Detect schema version")
version = CHSSchemaCompat.detect_schema_version(conn)
print(f"  Detected: {version}")
expected = SchemaVersion.LEGACY
if version == expected:
    print(f"  Status: PASS (expected {expected})")
else:
    print(f"  Status: FAIL (expected {expected}, got {version})")
print()
print("Test 4: Get messages table name")
messages_table = CHSSchemaCompat.get_messages_table(conn)
print(f"  Table name: {messages_table}")
expected_table = "chat_messages"
if messages_table == expected_table:
    print(f"  Status: PASS (expected {expected_table})")
else:
    print(f"  Status: FAIL (expected {expected_table}, got {messages_table})")
print()
print("Test 5: Get FTS table name")
fts_table = CHSSchemaCompat.get_fts_table(conn)
print(f"  FTS table: {fts_table}")
if fts_table in ["message_search", "chat_messages_fts", "messages_fts"]:
    print("  Status: PASS (valid FTS table)")
else:
    print("  Status: FAIL (not a valid FTS table)")
print()
print("Test 6: Validate required tables")
validation = CHSSchemaCompat.validate_required_tables(conn)
for table, exists in validation.items():
    status = "✓" if exists else "✗"
    print(f"  {status} {table}: {exists}")
print()
print("Test 7: Get schema health message")
health_msg = CHSSchemaCompat.get_schema_health_message(conn)
if health_msg:
    print(f"  Warning: {health_msg}")
else:
    print("  Status: Schema is valid")
print()
print("Test 8: Test search query")
try:
    from core.chs.search import search_fts_messages

    test_queries = ["SEC-001", "TDD workflow", "chat history"]
    for query in test_queries:
        results = search_fts_messages(conn, query, limit=5)
        print(f"  Query '{query}': {len(results)} results")
        if results and "error" in results[0]:
            print(f"    Error: {results[0].get('message')}")
        elif results:
            print(f"    Top score: {results[0].get('score', 0):.4f}")
            print(f"    Snippet: {results[0].get('content', '')[:50]}...")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback

    traceback.print_exc()
print()
conn.close()
print("=== Schema Compatibility Layer Tests Complete ===")
