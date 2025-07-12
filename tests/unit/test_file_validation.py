"""Tests for the File Validation system."""

import unittest
from unittest.mock import Mock, mock_open, patch

from pysquared.file_validation.manager.file_validation import FileValidationManager
from pysquared.logger import Logger


class TestFileValidationManager(unittest.TestCase):
    """Test cases for FileValidationManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock(spec=Logger)
        self.file_validator = FileValidationManager(self.logger)

    def test_create_file_checksum_success(self):
        """Test successful file checksum creation."""
        test_content = b"Hello, World!"
        # SHA256 checksum of 'Hello, World!' is dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f
        expected_checksum = (
            "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        )

        with patch("builtins.open", mock_open(read_data=test_content)):
            with patch.object(self.file_validator, "_file_exists", return_value=True):
                checksum = self.file_validator.create_file_checksum("test.txt")

        self.assertEqual(checksum, expected_checksum)

    def test_create_file_checksum_file_not_found(self):
        """Test file checksum creation when file doesn't exist."""
        with patch.object(self.file_validator, "_file_exists", return_value=False):
            with self.assertRaises(Exception) as context:
                self.file_validator.create_file_checksum("nonexistent.txt")

        self.assertIn("File not found", str(context.exception))

    def test_create_file_checksum_os_error(self):
        """Test file checksum creation with OSError."""
        with patch("builtins.open", side_effect=OSError("No such file")):
            with patch.object(self.file_validator, "_file_exists", return_value=True):
                with self.assertRaises(Exception) as context:
                    self.file_validator.create_file_checksum("test.txt")

        self.assertIn("File not found", str(context.exception))

    def test_create_codebase_checksum_success(self):
        """Test successful codebase checksum creation."""
        with patch.object(self.file_validator, "_file_exists", return_value=True):
            with patch.object(
                self.file_validator,
                "_walk_directory",
                return_value=["file1.txt", "file2.txt"],
            ):
                with patch.object(
                    self.file_validator, "create_file_checksum"
                ) as mock_checksum:
                    mock_checksum.side_effect = ["checksum1", "checksum2"]

                    result = self.file_validator.create_codebase_checksum("/test")

        expected = {"file1.txt": "checksum1", "file2.txt": "checksum2"}
        self.assertEqual(result, expected)

    def test_create_codebase_checksum_base_path_not_found(self):
        """Test codebase checksum creation when base path doesn't exist."""
        with patch.object(self.file_validator, "_file_exists", return_value=False):
            with self.assertRaises(Exception) as context:
                self.file_validator.create_codebase_checksum("/nonexistent")

        self.assertIn("Base path not found", str(context.exception))

    def test_validate_file_integrity_success(self):
        """Test successful file integrity validation."""
        with patch.object(
            self.file_validator, "create_file_checksum", return_value="test_checksum"
        ):
            result = self.file_validator.validate_file_integrity(
                "test.txt", "test_checksum"
            )

        self.assertTrue(result)

    def test_validate_file_integrity_failure(self):
        """Test file integrity validation failure."""
        with patch.object(
            self.file_validator, "create_file_checksum", return_value="wrong_checksum"
        ):
            result = self.file_validator.validate_file_integrity(
                "test.txt", "test_checksum"
            )

        self.assertFalse(result)

    def test_validate_file_integrity_file_not_found(self):
        """Test file integrity validation when file doesn't exist."""
        with patch.object(
            self.file_validator,
            "create_file_checksum",
            side_effect=Exception("File not found"),
        ):
            with self.assertRaises(Exception) as context:
                self.file_validator.validate_file_integrity(
                    "nonexistent.txt", "test_checksum"
                )

        self.assertIn("File not found", str(context.exception))

    def test_validate_codebase_integrity_success(self):
        """Test successful codebase integrity validation."""
        expected_checksums = {"file1.txt": "checksum1", "file2.txt": "checksum2"}

        with patch.object(
            self.file_validator, "validate_file_integrity", return_value=True
        ):
            is_valid, failed_files = self.file_validator.validate_codebase_integrity(
                "/test", expected_checksums
            )

        self.assertTrue(is_valid)
        self.assertEqual(failed_files, [])

    def test_validate_codebase_integrity_with_failures(self):
        """Test codebase integrity validation with some failures."""
        expected_checksums = {"file1.txt": "checksum1", "file2.txt": "checksum2"}

        def mock_validate(file_path, checksum):
            return file_path.endswith("file1.txt")  # Only first file is valid

        with patch.object(
            self.file_validator, "validate_file_integrity", side_effect=mock_validate
        ):
            is_valid, failed_files = self.file_validator.validate_codebase_integrity(
                "/test", expected_checksums
            )

        self.assertFalse(is_valid)
        self.assertEqual(failed_files, ["file2.txt"])

    def test_get_missing_files(self):
        """Test getting missing files."""
        expected_files = ["file1.txt", "file2.txt", "file3.txt"]

        def mock_exists(file_path):
            return file_path.endswith("file1.txt") or file_path.endswith("file2.txt")

        with patch.object(self.file_validator, "_file_exists", side_effect=mock_exists):
            missing_files = self.file_validator.get_missing_files(
                "/test", expected_files
            )

        self.assertEqual(missing_files, ["file3.txt"])

    def test_get_extra_files(self):
        """Test getting extra files."""
        expected_files = ["file1.txt", "file2.txt"]

        with patch.object(
            self.file_validator,
            "_walk_directory",
            return_value=["file1.txt", "file2.txt", "extra.txt"],
        ):
            extra_files = self.file_validator.get_extra_files("/test", expected_files)

        self.assertEqual(extra_files, ["extra.txt"])

    def test_assess_codebase_completeness(self):
        """Test codebase completeness assessment."""
        expected_checksums = {"file1.txt": "checksum1", "file2.txt": "checksum2"}

        with patch.object(self.file_validator, "get_missing_files", return_value=[]):
            with patch.object(
                self.file_validator, "get_extra_files", return_value=["extra.txt"]
            ):
                with patch.object(
                    self.file_validator,
                    "validate_codebase_integrity",
                    return_value=(True, []),
                ):
                    assessment = self.file_validator.assess_codebase_completeness(
                        "/test", expected_checksums
                    )

        self.assertTrue(assessment["is_complete"])
        self.assertTrue(assessment["is_valid"])
        self.assertEqual(assessment["missing_files"], [])
        self.assertEqual(assessment["extra_files"], ["extra.txt"])
        self.assertEqual(assessment["corrupted_files"], [])
        self.assertEqual(assessment["total_files"], 2)
        self.assertEqual(assessment["valid_files"], 2)

    def test_get_file_size_success(self):
        """Test successful file size retrieval."""
        with patch.object(self.file_validator, "_file_exists", return_value=True):
            with patch.object(self.file_validator, "_get_file_size", return_value=1024):
                size = self.file_validator.get_file_size("test.txt")

        self.assertEqual(size, 1024)

    def test_get_file_size_file_not_found(self):
        """Test file size retrieval when file doesn't exist."""
        with patch.object(self.file_validator, "_file_exists", return_value=False):
            with self.assertRaises(Exception) as context:
                self.file_validator.get_file_size("nonexistent.txt")

        self.assertIn("File not found", str(context.exception))

    def test_get_codebase_size_success(self):
        """Test successful codebase size calculation."""
        with patch.object(self.file_validator, "_file_exists", return_value=True):
            with patch.object(
                self.file_validator,
                "_walk_directory",
                return_value=["file1.txt", "file2.txt"],
            ):
                with patch.object(
                    self.file_validator, "get_file_size", side_effect=[512, 1024]
                ):
                    total_size = self.file_validator.get_codebase_size("/test")

        self.assertEqual(total_size, 1536)

    def test_get_codebase_size_base_path_not_found(self):
        """Test codebase size calculation when base path doesn't exist."""
        with patch.object(self.file_validator, "_file_exists", return_value=False):
            with self.assertRaises(Exception) as context:
                self.file_validator.get_codebase_size("/nonexistent")

        self.assertIn("Base path not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()
