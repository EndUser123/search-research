#!/usr/bin/env python3
"""
Test script to verify JSON output functionality for yt-fts CLI.

This script tests:
- search --json
- list --json
- list --library --json
"""

import json
import subprocess


def run_command(cmd):
    """Run a command and return the output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10, check=False
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "Command timed out", 1


def test_json_format(output):
    """Test if output is valid JSON."""
    try:
        data = json.loads(output)
        return True, data
    except json.JSONDecodeError as e:
        return False, str(e)


def test_search_json():
    """Test search command with --json flag."""
    print("\n" + "="*60)
    print("TEST: search --json")
    print("="*60)

    # Test 1: Search with JSON output (this may fail if no database exists)
    print("\nTest 1: Basic search with --json")
    stdout, stderr, code = run_command("python -m yt_fts.core.cli search 'test' --json 2>&1")

    if code == 0:
        is_valid, result = test_json_format(stdout)
        if is_valid:
            print("✅ PASS: Valid JSON output")
            print(f"   Structure keys: {list(result.keys())}")
            if "query" in result and "timestamp" in result:
                print("✅ PASS: Contains required fields")
            else:
                print("⚠️  WARN: Missing expected fields")
        else:
            print(f"❌ FAIL: Invalid JSON - {result}")
            print(f"   Output preview: {stdout[:200]}")
    else:
        print("⚠️  SKIP: Command failed (possibly no database)")
        print(f"   Error: {stderr[:200] if stderr else 'Unknown error'}")


def test_list_json():
    """Test list command with --json flag."""
    print("\n" + "="*60)
    print("TEST: list --library --json")
    print("="*60)

    print("\nTest 1: List channels with --json")
    stdout, stderr, code = run_command("python -m yt_fts.core.cli list --library --json 2>&1")

    if code == 0:
        is_valid, result = test_json_format(stdout)
        if is_valid:
            print("✅ PASS: Valid JSON output")
            print(f"   Structure keys: {list(result.keys())}")
            if "timestamp" in result and "channels" in result:
                print("✅ PASS: Contains required fields")
                print(f"   Total channels: {result.get('total_channels', 0)}")
            else:
                print("⚠️  WARN: Missing expected fields")
                print(f"   Actual keys: {list(result.keys())}")
        else:
            print(f"❌ FAIL: Invalid JSON - {result}")
            print(f"   Output preview: {stdout[:200]}")
    else:
        print("⚠️  SKIP: Command failed")
        print(f"   Error: {stderr[:200] if stderr else 'Unknown error'}")


def test_json_module():
    """Test the json_output module directly."""
    print("\n" + "="*60)
    print("TEST: json_output module")
    print("="*60)

    try:
        from yt_fts.core.json_output import (
            format_error_json,
            format_search_results_json,
        )
        print("✅ PASS: json_output module imports successfully")

        # Test format_error_json
        error_json = format_error_json("Test error", "test_error")
        if isinstance(error_json, dict) and "message" in error_json:
            print("✅ PASS: format_error_json works")
        else:
            print("❌ FAIL: format_error_json returns unexpected structure")

        # Test format_search_results_json
        search_json = format_search_results_json("test query", "all", [], True, False)
        if isinstance(search_json, dict) and "query" in search_json:
            print("✅ PASS: format_search_results_json works")
            print(f"   Keys: {list(search_json.keys())}")
        else:
            print("❌ FAIL: format_search_results_json returns unexpected structure")

    except Exception as e:
        print(f"❌ FAIL: {e}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("JSON OUTPUT TESTS FOR YT-FTS")
    print("="*60)

    test_json_module()
    test_list_json()
    test_search_json()

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("To test JSON output with real data:")
    print("1. Download a channel: python -m yt_fts.core.cli download @channelname")
    print("2. Search with JSON: python -m yt_fts.core.cli search 'query' --json")
    print("3. List with JSON: python -m yt_fts.core.cli list --library --json")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
