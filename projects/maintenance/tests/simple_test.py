#!/usr/bin/env python3
"""
Simple test to check if basic functionality works
"""

print("🧪 Testing Basic Python Functionality...")

# Test basic imports
try:
    from pathlib import Path

    print("✅ Basic imports successful")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")

# Test file access
try:
    test_file = Path("C:/_Python/_Projects/ai_studio/src/ai_studio/youtube_cookies.py")
    if test_file.exists():
        print("✅ Can access ai_studio files")
    else:
        print("❌ Cannot access ai_studio files")
except Exception as e:
    print(f"❌ File access test failed: {e}")

# Test that our fix files exist
fix_files = [
    "C:/_Python/_Projects/fix_tensor_reshape_error.py",
    "C:/_Python/_Projects/fix_threadpool_executor_leaks.py",
    "C:/_Python/_Projects/fix_authentication_error_handling_simple.py",
    "C:/_Python/_Projects/fix_input_validation_gaps.py",
    "C:/_Python/_Projects/fix_race_conditions.py",
    "C:/_Python/_Projects/restore_browser_extension_auth.py",
]

print("\n📁 Checking Fix Files:")
for fix_file in fix_files:
    if Path(fix_file).exists():
        print(f"✅ {Path(fix_file).name}")
    else:
        print(f"❌ {Path(fix_file).name} missing")

print("\n✅ Basic functionality test completed")
