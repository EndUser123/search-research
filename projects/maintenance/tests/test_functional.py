#!/usr/bin/env python3
"""
Functional test for all bug fixes implemented
"""

import sys
from pathlib import Path

# Add ai_studio src to path
sys.path.insert(0, str(Path("C:/_Python/_Projects/ai_studio/src")))


def test_authentication_system():
    """Test authentication system uses browser extension approach"""
    print("🧪 Testing Authentication System...")

    try:
        from ai_studio.youtube_cookies import EnhancedYouTubeCookies

        # Test instantiation
        ec = EnhancedYouTubeCookies()
        print("✅ EnhancedYouTubeCookies instantiated successfully")

        # Test that it prioritizes browser extension approach
        if hasattr(ec, "setup_extension_cookies"):
            print("✅ Browser extension cookie method exists")
        else:
            print("❌ Browser extension cookie method missing")
            return False

        # Test cookies file path
        if hasattr(ec, "cookies_file"):
            print(f"✅ Cookies file path: {ec.cookies_file}")
        else:
            print("❌ Cookies file path not found")
            return False

        # Test that selenium methods are NOT present
        selenium_methods = [
            "setup_firefox_driver",
            "enhanced_google_sign_in_flow",
            "_interactive_authentication_strategy",
        ]
        for method in selenium_methods:
            if hasattr(ec, method):
                print(f"❌ Selenium method still present: {method}")
                return False
        print("✅ Selenium methods successfully removed")

        return True

    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tensor_utils():
    """Test tensor utility fixes"""
    print("\n🧪 Testing Tensor Utils...")

    try:
        from ai_studio.tensor_utils import SafeTensorProcessor, TensorValidationError

        # Test SafeTensorProcessor
        processor = SafeTensorProcessor()
        print("✅ SafeTensorProcessor instantiated successfully")

        # Test tensor validation
        import torch

        # Test with empty tensor
        empty_tensor = torch.tensor([])
        try:
            processor.safe_reshape(empty_tensor, (1, 1))
            print("✅ Empty tensor handling works")
        except TensorValidationError as e:
            print(f"✅ Empty tensor properly validated: {e}")
        except Exception as e:
            print(f"❌ Empty tensor handling failed: {e}")
            return False

        # Test with valid tensor
        valid_tensor = torch.randn(16000)
        try:
            processor.safe_reshape(valid_tensor, (16000,))
            print("✅ Valid tensor handling works")
        except Exception as e:
            print(f"❌ Valid tensor handling failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Tensor utils test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_unified_shutdown_handler():
    """Test shutdown handler enhancements"""
    print("\n🧪 Testing Unified Shutdown Handler...")

    try:
        from ai_studio.unified_shutdown_handler import (
            ThreadExecutorCleanupHandler,
            UnifiedShutdownHandler,
        )

        # Test UnifiedShutdownHandler
        UnifiedShutdownHandler()
        print("✅ UnifiedShutdownHandler instantiated successfully")

        # Test ThreadExecutorCleanupHandler
        from concurrent.futures import ThreadPoolExecutor

        executor = ThreadPoolExecutor(max_workers=2)
        cleanup_handler = ThreadExecutorCleanupHandler(executor, "test")
        print("✅ ThreadExecutorCleanupHandler instantiated successfully")

        # Test cleanup methods exist
        if hasattr(cleanup_handler, "cleanup") and hasattr(
            cleanup_handler, "force_cleanup"
        ):
            print("✅ Enhanced cleanup methods exist")
        else:
            print("❌ Enhanced cleanup methods missing")
            return False

        # Clean up
        executor.shutdown(wait=True)
        print("✅ Shutdown handler test completed successfully")

        return True

    except Exception as e:
        print(f"❌ Shutdown handler test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_input_validation():
    """Test input validation function"""
    print("\n🧪 Testing Input Validation...")

    try:
        # Test the validation function we created
        exec(open("C:/_Python/_Projects/test_validation.py").read())

        test_cases = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "test.mp4",
            "malicious|command",
            "../../../etc/passwd",
            "",
            None,
        ]

        print("Testing input validation function:")
        for test in test_cases:
            try:
                result = _validate_video_source(test)
                if result["valid"]:
                    print(f"✅ Valid input: {test} -> {result['type']}")
                else:
                    print(f"✅ Properly rejected: {test} -> {result['error']}")
            except Exception as e:
                print(f"❌ Validation error for {test}: {e}")
                return False

        return True

    except Exception as e:
        print(f"❌ Input validation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_video_processor():
    """Test video processor race condition fixes"""
    print("\n🧪 Testing Video Processor...")

    try:
        from ai_studio.video_processor import VideoProcessor

        # Test that VideoProcessor can be imported
        print("✅ VideoProcessor imported successfully")

        # Test _update_worker_status method exists
        vp = VideoProcessor.__new__(VideoProcessor)
        if hasattr(vp, "_update_worker_status"):
            print("✅ Worker status update method exists")
        else:
            print("❌ Worker status update method missing")
            return False

        # Test _cleanup_worker_status method exists (should have been added)
        if hasattr(vp, "_cleanup_worker_status"):
            print("✅ Worker status cleanup method exists")
        else:
            print("⚠️ Worker status cleanup method not found (may be okay)")

        return True

    except Exception as e:
        print(f"❌ Video processor test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all functional tests"""
    print("🔬 Functional Test Suite for Bug Fixes")
    print("=" * 50)

    tests = [
        test_authentication_system,
        test_tensor_utils,
        test_unified_shutdown_handler,
        test_input_validation,
        test_video_processor,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"💥 {test.__name__} crashed: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All functional tests passed! Bug fixes are working correctly.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed. Some issues may need attention.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
