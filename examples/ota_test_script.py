"""
Simple test script for OTA Update functionality on CircuitPython devices.

This script tests the basic functionality of the OTA Update Manager
including file checksum creation and validation.
"""

import os
import sys

# Import the required modules
from pysquared.logger import Logger  # noqa: E402
from pysquared.nvm.counter import Counter  # noqa: E402
from pysquared.ota_update.manager.ota_update import OTAUpdateManager  # noqa: E402


def test_ota_functionality():
    """Test the OTA update functionality."""
    print("=== OTA Update Test Script ===")

    # Initialize components
    print("1. Initializing components...")
    error_counter = Counter(0)
    logger = Logger(error_counter)
    ota_manager = OTAUpdateManager(logger)
    print("   ✓ Components initialized successfully")

    # Test 1: Create checksum for main.py
    print("\n2. Testing file checksum creation...")
    try:
        checksum = ota_manager.create_file_checksum("main.py")
        print(f"   ✓ Checksum for main.py: {checksum}")
    except Exception as e:
        print(f"   ✗ Error creating checksum: {e}")
        return False

    # Test 2: Create checksum for boot.py (if it exists)
    print("\n3. Testing checksum for boot.py...")
    try:
        if ota_manager._file_exists("boot.py"):
            checksum = ota_manager.create_file_checksum("boot.py")
            print(f"   ✓ Checksum for boot.py: {checksum}")
        else:
            print("   - boot.py not found, skipping")
    except Exception as e:
        print(f"   ✗ Error creating checksum for boot.py: {e}")

    # Test 3: Test file integrity validation
    print("\n4. Testing file integrity validation...")
    try:
        # Get the checksum we just created
        test_checksum = ota_manager.create_file_checksum("main.py")

        # Validate it
        is_valid = ota_manager.validate_file_integrity("main.py", test_checksum)
        if is_valid:
            print("   ✓ File integrity validation passed")
        else:
            print("   ✗ File integrity validation failed")
            return False
    except Exception as e:
        print(f"   ✗ Error during integrity validation: {e}")
        return False

    # Test 4: Test with wrong checksum
    print("\n5. Testing integrity validation with wrong checksum...")
    try:
        is_valid = ota_manager.validate_file_integrity("main.py", "wrong_checksum")
        if not is_valid:
            print("   ✓ Correctly rejected wrong checksum")
        else:
            print("   ✗ Incorrectly accepted wrong checksum")
            return False
    except Exception as e:
        print(f"   ✗ Error during wrong checksum test: {e}")
        return False

    # Test 5: Test file size retrieval
    print("\n6. Testing file size retrieval...")
    try:
        file_size = ota_manager.get_file_size("main.py")
        print(f"   ✓ main.py size: {file_size} bytes")
    except Exception as e:
        print(f"   ✗ Error getting file size: {e}")

    # Test 6: Test codebase checksum creation
    print("\n7. Testing codebase checksum creation...")
    try:
        # Create checksums for current directory
        checksums = ota_manager.create_codebase_checksum(
            ".", exclude_patterns=["*.pyc", "__pycache__"]
        )
        print(f"   ✓ Created checksums for {len(checksums)} files")

        # Show first few checksums
        for i, (file_path, checksum) in enumerate(checksums.items()):
            if i < 3:  # Show first 3 files
                print(f"     {file_path}: {checksum}")
            else:
                print(f"     ... and {len(checksums) - 3} more files")
                break

    except Exception as e:
        print(f"   ✗ Error creating codebase checksums: {e}")

    print("\n=== Test completed successfully! ===")
    return True


def test_hashlib_availability():
    """Test which hashlib implementation is available."""
    print("\n=== Hashlib Availability Test ===")

    # Test adafruit_hashlib
    try:
        import adafruit_hashlib

        print("✓ adafruit_hashlib is available")

        # Test MD5 creation
        md5_hash = adafruit_hashlib.new("md5")
        md5_hash.update(b"test")
        result = md5_hash.hexdigest()
        print(f"  MD5 test result: {result}")

    except ImportError:
        print("✗ adafruit_hashlib is not available")
    except Exception as e:
        print(f"✗ Error with adafruit_hashlib: {e}")

    # Test standard hashlib
    try:
        import hashlib

        print("✓ hashlib is available")

        # Test MD5 creation
        md5_hash = hashlib.md5()
        md5_hash.update(b"test")
        result = md5_hash.hexdigest()
        print(f"  MD5 test result: {result}")

    except ImportError:
        print("✗ hashlib is not available")
    except Exception as e:
        print(f"✗ Error with hashlib: {e}")


if __name__ == "__main__":
    print("Starting OTA Update Test Script...")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")

    # Test hashlib availability first
    test_hashlib_availability()

    # Run main test
    success = test_ota_functionality()

    if success:
        print("\n🎉 All tests passed! OTA Update functionality is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")

    print("\nTest script completed.")
