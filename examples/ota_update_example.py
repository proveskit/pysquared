"""
Example script demonstrating OTA Update functionality.

This script shows how to use the OTA update system to create checksums,
validate file integrity, and assess codebase completeness.
"""

import os
import sys

# Add the parent directory to the path so we can import pysquared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pysquared.logger import Logger
from pysquared.nvm.counter import Counter
from pysquared.ota_update.manager.ota_update import OTAUpdateManager


def main():
    """Main function demonstrating OTA update functionality."""
    # Initialize logger and OTA update manager
    error_counter = Counter(0)
    logger = Logger(error_counter, colorized=True)
    ota_manager = OTAUpdateManager(logger)

    # Example: Create checksums for the current directory
    current_dir = os.getcwd()
    logger.info("Starting OTA update example", current_directory=current_dir)

    try:
        # Create checksums for all files in the current directory
        logger.info("Creating checksums for codebase...")
        checksums = ota_manager.create_codebase_checksum(
            current_dir, exclude_patterns=[".git", "__pycache__", ".pyc", ".DS_Store"]
        )

        logger.info(
            "Checksums created successfully",
            total_files=len(checksums),
            sample_files=list(checksums.keys())[:5],
        )  # Show first 5 files

        # Display some sample checksums
        print("\nSample file checksums:")
        for i, (file_path, checksum) in enumerate(checksums.items()):
            if i >= 5:  # Only show first 5
                break
            print(f"  {file_path}: {checksum}")

        # Validate the integrity of a specific file
        if checksums:
            sample_file = list(checksums.keys())[0]
            sample_checksum = checksums[sample_file]
            full_path = os.path.join(current_dir, sample_file)

            logger.info("Validating file integrity", file=sample_file)
            is_valid = ota_manager.validate_file_integrity(full_path, sample_checksum)
            logger.info(
                "File integrity validation result", file=sample_file, is_valid=is_valid
            )

        # Assess codebase completeness
        logger.info("Assessing codebase completeness...")
        assessment = ota_manager.assess_codebase_completeness(current_dir, checksums)

        print("\nCodebase Assessment Results:")
        print(f"  Complete: {assessment['is_complete']}")
        print(f"  Valid: {assessment['is_valid']}")
        print(f"  Total files: {assessment['total_files']}")
        print(f"  Valid files: {assessment['valid_files']}")
        print(f"  Missing files: {len(assessment['missing_files'])}")
        print(f"  Extra files: {len(assessment['extra_files'])}")
        print(f"  Corrupted files: {len(assessment['corrupted_files'])}")

        # Get codebase size
        total_size = ota_manager.get_codebase_size(
            current_dir, exclude_patterns=[".git", "__pycache__", ".pyc", ".DS_Store"]
        )
        logger.info("Codebase size calculated", total_size_bytes=total_size)
        print(f"  Total size: {total_size} bytes ({total_size / 1024:.2f} KB)")

        # Demonstrate missing file detection
        logger.info("Demonstrating missing file detection...")
        fake_expected_files = list(checksums.keys())[:3] + ["nonexistent_file.txt"]
        missing_files = ota_manager.get_missing_files(current_dir, fake_expected_files)
        logger.info("Missing files identified", missing_files=missing_files)
        print(f"  Missing files: {missing_files}")

        # Demonstrate extra file detection
        logger.info("Demonstrating extra file detection...")
        partial_expected_files = list(checksums.keys())[:2]  # Only expect first 2 files
        extra_files = ota_manager.get_extra_files(current_dir, partial_expected_files)
        logger.info(
            "Extra files identified", extra_files=extra_files[:5]
        )  # Show first 5
        print(f"  Extra files (first 5): {extra_files[:5]}")

    except Exception as e:
        logger.error("Error during OTA update example", err=e)
        return 1

    logger.info("OTA update example completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
