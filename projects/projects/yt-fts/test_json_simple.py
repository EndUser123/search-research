#!/usr/bin/env python3
"""Simple test of JSON output functionality."""

import json
import sys

# Test the JSON output module directly
sys.path.insert(0, "src")

from yt_fts.core.json_output import format_error_json, format_search_results_json

print("Testing JSON output module...\n")

# Test 1: format_error_json
print("1. Testing format_error_json:")
error = format_error_json("Test error message", "test_error")
print(f"   Output: {json.dumps(error, indent=2)}")
assert "timestamp" in error
assert "message" in error
print("   ✅ PASS\n")

# Test 2: format_search_results_json with empty results
print("2. Testing format_search_results_json (empty):")
search = format_search_results_json("test query", "all", [], True, False)
print(f"   Output: {json.dumps(search, indent=2)}")
assert "query" in search
assert search["query"] == "test query"
assert search["matches"] == 0
print("   ✅ PASS\n")

# Test 3: format_search_results_json with sample data
print("3. Testing format_search_results_json (with data):")
sample_result = {
    "video_id": "abc123",
    "video_title": "Test Video",
    "video_date": "2025-01-01",
    "channel_name": "Test Channel",
    "text": "This is a test transcript",
    "timestamp": "00:01:00",
    "link": "https://youtu.be/abc123?t=60"
}
search = format_search_results_json("test", "all", [sample_result], True, False)
print(f"   Output keys: {list(search.keys())}")
assert search["matches"] == 1
assert search["videos"] == 1
assert len(search["results"]) == 1
print("   ✅ PASS\n")

print("All JSON output module tests passed! ✅")
print("\nThe JSON output module is working correctly.")
print("The CLI commands should now support --json flag.")
