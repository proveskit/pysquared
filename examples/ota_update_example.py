#!/usr/bin/env python3
"""
OTA Update System Example

This example demonstrates the OTA update system functionality including:
- Creating checksums for files and codebases
- Validating file integrity
- Assessing codebase completeness
"""

import os
import sys
import tempfile
import types

# Add the pysquared directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# Mock the CircuitPython modules for this example
mock_micro = types.ModuleType("microcontroller")
setattr(
    mock_micro,
    "nvm",
    type(
        "nvm",
        (),
        {
            "__getitem__": lambda self, idx: 0,
            "__setitem__": lambda self, idx, val: None,
        },
    )(),
)  # type: ignore
sys.modules["microcontroller"] = mock_micro

from pysquared.logger import Logger  # noqa: E402
from pysquared.nvm.counter import Counter  # noqa: E402
from pysquared.ota_update.manager.ota_update import OTAUpdateManager  # noqa: E402


def create_test_files(base_dir: str) -> None:
    """Create test files for demonstration."""
    # Create some test files
    test_files = {
        "main.py": "print('Hello, World!')\n",
        "config.json": '{"debug": true, "version": "1.0.0"}\n',
        "lib/utils.py": "def helper():\n    return 'helper function'\n",
        "data/test.txt": "This is test data\n",
    }

    for file_path, content in test_files.items():
        full_path = os.path.join(base_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    print(f"Created test files in {base_dir}")


def main():
    """Main example function."""
    print("OTA Update System Example")
    print("=" * 50)

    # Initialize the system
    error_counter = Counter(0)  # Use index 0 for this example
    logger = Logger(error_counter)
    ota_manager = OTAUpdateManager(logger)

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")

        # Create test files
        create_test_files(temp_dir)

        # Example 1: Create checksum for a single file
        print("\n1. Creating checksum for a single file:")
        main_py_path = os.path.join(temp_dir, "main.py")
        checksum = ota_manager.create_file_checksum(main_py_path)
        print(f"   main.py checksum: {checksum}")

        # Example 2: Create checksums for entire codebase
        print("\n2. Creating checksums for entire codebase:")
        checksums = ota_manager.create_codebase_checksum(
            temp_dir, exclude_patterns=["__pycache__", ".pyc"]
        )
        print(f"   Found {len(checksums)} files:")
        for file_path, file_checksum in checksums.items():
            print(f"     {file_path}: {file_checksum}")

        # Example 3: Validate file integrity
        print("\n3. Validating file integrity:")
        is_valid = ota_manager.validate_file_integrity(main_py_path, checksum)
        print(f"   main.py integrity check: {'PASS' if is_valid else 'FAIL'}")

        # Example 4: Validate with wrong checksum
        print("\n4. Validating with wrong checksum:")
        is_valid = ota_manager.validate_file_integrity(main_py_path, "0000")
        print(f"   main.py with wrong checksum: {'PASS' if is_valid else 'FAIL'}")

        # Example 5: Get file size
        print("\n5. Getting file sizes:")
        file_size = ota_manager.get_file_size(main_py_path)
        print(f"   main.py size: {file_size} bytes")

        # Example 6: Get codebase size
        print("\n6. Getting codebase size:")
        total_size = ota_manager.get_codebase_size(temp_dir)
        print(f"   Total codebase size: {total_size} bytes")

        # Example 7: Assess codebase completeness
        print("\n7. Assessing codebase completeness:")
        assessment = ota_manager.assess_codebase_completeness(temp_dir, checksums)
        print(f"   Is complete: {assessment['is_complete']}")
        print(f"   Is valid: {assessment['is_valid']}")
        print(f"   Total files: {assessment['total_files']}")
        print(f"   Valid files: {assessment['valid_files']}")
        print(f"   Missing files: {len(assessment['missing_files'])}")
        print(f"   Extra files: {len(assessment['extra_files'])}")
        print(f"   Corrupted files: {len(assessment['corrupted_files'])}")

        # Example 8: Test with missing files
        print("\n8. Testing with missing files:")
        expected_files = list(checksums.keys()) + ["missing_file.py"]
        missing_files = ota_manager.get_missing_files(temp_dir, expected_files)
        print(f"   Missing files: {missing_files}")

        # Example 9: Test with extra files
        print("\n9. Testing with extra files:")
        expected_files = ["main.py"]  # Only expect main.py
        extra_files = ota_manager.get_extra_files(temp_dir, expected_files)
        print(f"   Extra files: {extra_files}")

        # Example 10: Demonstrate checksum algorithm
        print("\n10. Checksum algorithm demonstration:")
        test_content = b"Hello, World!"
        manual_checksum = sum(test_content) & 0xFFFF
        print(f"   Content: {test_content}")
        print(f"   Manual checksum: {manual_checksum:04x}")

        # Create a temporary file with this content
        test_file = os.path.join(temp_dir, "test_checksum.txt")
        with open(test_file, "wb") as f:
            f.write(test_content)

        file_checksum = ota_manager.create_file_checksum(test_file)
        print(f"   File checksum: {file_checksum}")
        print(f"   Match: {file_checksum == format(manual_checksum, '04x')}")

    print("\nExample completed successfully!")
    print(f"Total errors logged: {logger.get_error_count()}")


if __name__ == "__main__":
    main()
