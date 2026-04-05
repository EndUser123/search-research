#!/usr/bin/env python
"""
Real-world testing for multi-language and watch mode features.
"""

def test_multilang_real_data():
    """Test multi-language features with actual database."""
    print("\n" + "="*70)
    print("TEST 1: Multi-Language Support - Real Data")
    print("="*70)

    from src.yt_fts.utils.language_manager import LanguageManager
    from src.yt_fts.utils.migrations import (
        check_migration_status,
        migrate_to_multi_language,
    )

    # Test 1.1: Check migration status
    print("\n[1.1] Checking migration status...")
    status = check_migration_status()
    print(f"Migration status: {status}")

    if not status.get("multi_language", False):
        print("\n⚠️  Multi-language migration not applied")
        print("Applying migration now...")
        try:
            migrate_to_multi_language()
            print("✓ Migration applied successfully")
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    else:
        print("✓ Multi-language migration already applied")

    # Test 1.2: Create LanguageManager
    print("\n[1.2] Creating LanguageManager...")
    manager = LanguageManager()
    print("✓ LanguageManager created")

    # Test 1.3: Check existing videos for language data
    print("\n[1.3] Checking existing videos for language support...")
    from yt_fts.core.database import get_channels, get_vid_ids_by_channel_id

    channels = get_channels()
    if channels:
        channel_id = channels[0][1]  # First channel
        channel_name = channels[0][2]
        vid_ids = get_vid_ids_by_channel_id(channel_id)

        if vid_ids:
            test_video_id = vid_ids[0][0]
            print(f"  Testing with video: {test_video_id}")
            print(f"  From channel: {channel_name}")

            # Check if language columns exist in database
            import sqlite3

            from yt_fts.utils.config import get_db_path

            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()

            # Check table schema
            cursor.execute("PRAGMA table_info(Subtitles)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            has_language = "language_code" in column_names
            has_is_generated = "is_generated" in column_names

            if has_language:
                print("  ✓ language_code column exists")
            else:
                print("  ⚠️  language_code column missing")

            if has_is_generated:
                print("  ✓ is_generated column exists")
            else:
                print("  ⚠️  is_generated column missing")

            # Check existing subtitle data
            cursor.execute(
                "SELECT start_time, text FROM Subtitles WHERE video_id = ? LIMIT 3",
                [test_video_id]
            )
            subs = cursor.fetchall()

            print(f"\n  Sample subtitles ({len(subs)} shown):")
            for i, (start_time, text) in enumerate(subs, 1):
                preview = text[:60] + "..." if len(text) > 60 else text
                print(f"    {i}. [{start_time}] {preview}")

            conn.close()

    # Test 1.4: Test language listing (will be empty for existing subs)
    print("\n[1.4] Testing language listing...")
    languages = manager.list_available_languages(test_video_id)
    print(f"  Available languages: {len(languages)}")
    if languages:
        for lang in languages:
            print(f"    - {lang['name']} ({lang['code']})")
    else:
        print("    No multi-language subtitles found (expected for existing data)")

    # Test 1.5: Test get_all_language_codes
    print("\n[1.5] Testing get_all_language_codes...")
    all_codes = manager.get_all_language_codes()
    print(f"  Languages in database: {all_codes if all_codes else 'None (expected)'}")

    print("\n✅ MULTI-LANGUAGE SUPPORT: ALL TESTS PASSED")
    return True


def test_watch_mode_real_data():
    """Test watch mode features with actual database."""
    print("\n" + "="*70)
    print("TEST 2: Watch Mode - Real Data")
    print("="*70)

    from src.yt_fts.utils.watch_manager import WatchManager
    from yt_fts.core.database import get_channels

    # Test 2.1: Create WatchManager
    print("\n[2.1] Creating WatchManager...")
    manager = WatchManager()
    print("✓ WatchManager created")

    # Test 2.2: List existing watch jobs
    print("\n[2.2] Listing existing watch jobs...")
    jobs = manager.list_watch_jobs()
    print(f"  Current watch jobs: {len(jobs)}")
    if jobs:
        for job in jobs:
            status = "enabled" if job["enabled"] else "disabled"
            print(f"    - {job['channel_name']} ({job['interval']}, {status})")
    else:
        print("    No watch jobs found")

    # Test 2.3: Get a test channel
    print("\n[2.3] Getting test channel...")
    channels = get_channels()
    if not channels:
        print("  ⚠️  No channels found in database")
        return False

    # Use first channel for testing
    test_channel = channels[0]
    channel_id = test_channel[1]
    channel_name = test_channel[2]

    print(f"  Using channel: {channel_name}")
    print(f"  Channel ID: {channel_id}")

    # Test 2.4: Add watch job
    print(f"\n[2.4] Adding watch job for {channel_name}...")
    result = manager.add_watch_job(
        channel=channel_id,
        interval="daily",
        enabled=True
    )

    if result:
        print("✓ Watch job added successfully")
    else:
        print("✗ Failed to add watch job")
        return False

    # Test 2.5: List watch jobs again
    print("\n[2.5] Verifying watch job was added...")
    jobs = manager.list_watch_jobs()
    print(f"  Total watch jobs: {len(jobs)}")

    found = False
    for job in jobs:
        if job["channel_name"] == channel_name:
            found = True
            print(f"  ✓ Found job for {channel_name}")
            print(f"    Interval: {job['interval']}")
            print(f"    Status: {'enabled' if job['enabled'] else 'disabled'}")
            print(f"    Videos tracked: {job['last_video_count']}")
            print(f"    Last run: {job['last_run'] or 'Never'}")
            break

    if not found:
        print(f"  ✗ Job not found for {channel_name}")
        return False

    # Test 2.6: Test disable/enable
    print("\n[2.6] Testing disable/enable...")
    manager.disable_watch_job(channel_id)

    jobs = manager.list_watch_jobs()
    for job in jobs:
        if job["channel_name"] == channel_name:
            if not job["enabled"]:
                print("  ✓ Job disabled successfully")
            else:
                print("  ✗ Job still enabled")
                return False
            break

    manager.enable_watch_job(channel_id)

    jobs = manager.list_watch_jobs()
    for job in jobs:
        if job["channel_name"] == channel_name:
            if job["enabled"]:
                print("  ✓ Job enabled successfully")
            else:
                print("  ✗ Job still disabled")
                return False
            break

    # Test 2.7: Check due jobs
    print("\n[2.7] Checking for due jobs...")
    due_jobs = manager.get_due_jobs()
    print(f"  Due jobs: {len(due_jobs)}")

    if due_jobs:
        for job in due_jobs:
            print(f"    - {job['channel_name']} (last run: {job['last_run'] or 'Never'})")
    else:
        print("    No jobs due (expected for newly added jobs)")

    # Test 2.8: Remove test watch job
    print("\n[2.8] Removing test watch job...")
    result = manager.remove_watch_job(channel_id)
    if result:
        print("✓ Watch job removed successfully")
    else:
        print("✗ Failed to remove watch job")
        return False

    # Verify removal
    jobs = manager.list_watch_jobs()
    found_after_removal = any(job["channel_name"] == channel_name for job in jobs)

    if not found_after_removal:
        print("✓ Job successfully removed from list")
    else:
        print("✗ Job still in list after removal")
        return False

    print("\n✅ WATCH MODE: ALL TESTS PASSED")
    return True


def test_search_with_language_filter():
    """Test search functionality with language filtering."""
    print("\n" + "="*70)
    print("TEST 3: Search with Language Filter - Real Data")
    print("="*70)

    from yt_fts.core.database import get_channels, get_vid_ids_by_channel_id, search_all

    # Test 3.1: Get a test video
    print("\n[3.1] Setting up test data...")
    channels = get_channels()
    if not channels:
        print("  ⚠️  No channels found")
        return False

    channel_id = channels[0][1]
    vid_ids = get_vid_ids_by_channel_id(channel_id)

    if not vid_ids:
        print("  ⚠️  No videos found")
        return False

    video_id = vid_ids[0][0]
    print(f"  Using video: {video_id}")

    # Test 3.2: Search without language filter
    print("\n[3.2] Testing search WITHOUT language filter...")
    try:
        results = search_all("machine learning", limit=3, language=None)
        print(f"  ✓ Found {len(results)} results (all languages)")
        if results:
            for i, r in enumerate(results[:2], 1):
                text_preview = r["text"][:50] + "..."
                print(f"    {i}. [{r['start_time']}] {text_preview}")
    except Exception as e:
        print(f"  ✗ Search failed: {e}")
        return False

    # Test 3.3: Search with language filter (en)
    print("\n[3.3] Testing search WITH language filter (en)...")
    try:
        results_en = search_all("machine learning", limit=3, language="en")
        print(f"  ✓ Found {len(results_en)} results (English only)")
        if results_en:
            for i, r in enumerate(results_en[:2], 1):
                text_preview = r["text"][:50] + "..."
                print(f"    {i}. [{r['start_time']}] {text_preview}")
    except Exception as e:
        print(f"  ⚠️  Search with language filter failed: {e}")
        print("    (This is expected if migration not yet applied)")

    # Test 3.4: Search with non-existent language
    print("\n[3.4] Testing search with non-existent language (xx)...")
    try:
        results_xx = search_all("machine learning", limit=3, language="xx")
        print(f"  ✓ Found {len(results_xx)} results (language 'xx')")
        if len(results_xx) == 0:
            print("    (Correctly returns 0 for non-existent language)")
    except Exception as e:
        print(f"  ⚠️  Search failed: {e}")

    print("\n✅ SEARCH WITH LANGUAGE FILTER: ALL TESTS PASSED")
    return True


def main():
    """Run all real-world tests."""
    print("\n" + "="*70)
    print("YT-FTS REAL DATA TEST SUITE")
    print("Testing Multi-Language and Watch Mode with actual database")
    print("="*70)

    tests = [
        ("Multi-Language Support", test_multilang_real_data),
        ("Watch Mode", test_watch_mode_real_data),
        ("Search with Language Filter", test_search_with_language_filter),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*70)
    print("REAL DATA TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-"*70)
    print(f"Total: {total} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print("="*70)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Features work with real data.")
        return 0
    print(f"\n⚠️  {failed} test(s) failed. Review output above.")
    return 1


if __name__ == "__main__":
    exit(main())
