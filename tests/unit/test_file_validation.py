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
        # MD5 checksum of 'Hello, World!' is 65a8e27d8879283831b664bd8b7f0ad4
        expected_checksum = "65a8e27d8879283831b664bd8b7f0ad4"

        with patch("builtins.open", mock_open(read_data=test_content)):
            with patch.object(self.file_validator, "_file_exists", return_value=True):
                checksum = self.file_validator.create_file_checksum("test.txt")

        self.assertEqual(checksum, expected_checksum)

    def test_create_file_checksum_sha256(self):
        """Test SHA256 file checksum creation."""
        test_content = b"Hello, World!"
        # SHA256 checksum of 'Hello, World!' is dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f
        expected_checksum = (
            "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        )

        with patch("builtins.open", mock_open(read_data=test_content)):
            with patch.object(self.file_validator, "_file_exists", return_value=True):
                checksum = self.file_validator.create_file_checksum(
                    "test.txt", algorithm="sha256"
                )

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
            """Mock validation function that only validates the first file."""
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
            """Mock file existence function that only returns True for first two files."""
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

    def test_create_file_checksum_timeout(self):
        """Test file checksum creation with timeout."""
        with patch("builtins.open", mock_open(read_data=b"test")):
            with patch.object(self.file_validator, "_file_exists", return_value=True):
                with patch("time.monotonic", side_effect=[0, 6]):  # Simulate timeout
                    with self.assertRaises(TimeoutError):
                        self.file_validator.create_file_checksum(
                            "test.txt", timeout=5.0
                        )

    def test_walk_directory_with_hidden_files(self):
        """Test directory walking with hidden files."""
        with patch("os.listdir") as mock_listdir:
            # Simulate directory with hidden files
            mock_listdir.side_effect = [
                ["file1.txt", ".hidden", "file2.txt", ".DS_Store"],  # Root directory
                OSError("Not a directory"),  # file1.txt is a file
                OSError("Not a directory"),  # file2.txt is a file
            ]

            with patch("os.stat", return_value=(0, 0, 0, 0, 0, 0, 1024, 0, 0, 0)):
                result = self.file_validator._walk_directory("/test")

        # Hidden files should be excluded
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)
        self.assertNotIn(".hidden", result)
        self.assertNotIn(".DS_Store", result)

    def test_walk_directory_with_exclude_patterns(self):
        """Test directory walking with exclude patterns."""
        with patch("os.listdir") as mock_listdir:
            mock_listdir.side_effect = [
                ["file1.txt", "file2.pyc", "file3.txt", "__pycache__"],
                OSError("Not a directory"),  # file1.txt is a file
                OSError("Not a directory"),  # file3.txt is a file
            ]

            with patch("os.stat", return_value=(0, 0, 0, 0, 0, 0, 1024, 0, 0, 0)):
                result = self.file_validator._walk_directory(
                    "/test", exclude_patterns=["__pycache__", ".pyc"]
                )

        # Excluded patterns should not be in result
        self.assertIn("file1.txt", result)
        self.assertIn("file3.txt", result)
        self.assertNotIn("file2.pyc", result)
        self.assertNotIn("__pycache__", result)

    def test_walk_directory_os_error(self):
        """Test directory walking with OSError."""
        with patch("os.listdir", side_effect=OSError("Permission denied")):
            result = self.file_validator._walk_directory("/test")
            self.assertEqual(result, [])

    def test_process_single_file_checksum_success(self):
        """Test successful single file checksum processing."""
        with patch.object(
            self.file_validator, "create_file_checksum", return_value="test_checksum"
        ):
            result = self.file_validator._process_single_file_checksum(
                "/test", "file.txt"
            )
            self.assertEqual(result, "test_checksum")

    def test_process_single_file_checksum_failure(self):
        """Test single file checksum processing failure."""
        with patch.object(
            self.file_validator,
            "create_file_checksum",
            side_effect=Exception("File error"),
        ):
            result = self.file_validator._process_single_file_checksum(
                "/test", "file.txt"
            )
            self.assertIsNone(result)

    def test_create_codebase_checksum_with_failures(self):
        """Test codebase checksum creation with some file failures."""
        with patch.object(self.file_validator, "_file_exists", return_value=True):
            with patch.object(
                self.file_validator,
                "_walk_directory",
                return_value=["file1.txt", "file2.txt", "file3.txt"],
            ):
                with patch.object(
                    self.file_validator, "_process_single_file_checksum"
                ) as mock_process:
                    mock_process.side_effect = [
                        "checksum1",
                        None,
                        "checksum3",
                    ]  # file2 fails

                    result = self.file_validator.create_codebase_checksum("/test")

        expected = {"file1.txt": "checksum1", "file3.txt": "checksum3"}
        self.assertEqual(result, expected)

    def test_validate_codebase_integrity_with_exceptions(self):
        """Test codebase integrity validation with exceptions."""
        expected_checksums = {"file1.txt": "checksum1", "file2.txt": "checksum2"}

        def mock_validate(file_path, checksum):
            """Mock validation function that raises exception for second file."""
            if file_path.endswith("file2.txt"):
                raise Exception("Validation error")
            return True

        with patch.object(
            self.file_validator, "validate_file_integrity", side_effect=mock_validate
        ):
            is_valid, failed_files = self.file_validator.validate_codebase_integrity(
                "/test", expected_checksums
            )

        self.assertFalse(is_valid)
        self.assertEqual(failed_files, ["file2.txt"])

    def test_validate_codebase_integrity_file_not_found_exception(self):
        """Test codebase integrity validation with file not found exceptions."""
        expected_checksums = {"file1.txt": "checksum1", "file2.txt": "checksum2"}

        def mock_validate(file_path, checksum):
            """Mock validation function that raises file not found for second file."""
            if file_path.endswith("file2.txt"):
                raise Exception("File not found")
            return True

        with patch.object(
            self.file_validator, "validate_file_integrity", side_effect=mock_validate
        ):
            is_valid, failed_files = self.file_validator.validate_codebase_integrity(
                "/test", expected_checksums
            )

        self.assertFalse(is_valid)
        self.assertEqual(failed_files, ["file2.txt"])

    def test_get_missing_files_empty_list(self):
        """Test getting missing files with empty expected list."""
        with patch.object(self.file_validator, "_file_exists", return_value=True):
            missing_files = self.file_validator.get_missing_files("/test", [])
            self.assertEqual(missing_files, [])

    def test_get_extra_files_empty_directory(self):
        """Test getting extra files with empty directory."""
        with patch.object(self.file_validator, "_walk_directory", return_value=[]):
            extra_files = self.file_validator.get_extra_files("/test", ["file1.txt"])
            self.assertEqual(extra_files, [])

    def test_assess_codebase_completeness_with_missing_and_corrupted(self):
        """Test codebase completeness assessment with missing and corrupted files."""
        expected_checksums = {
            "file1.txt": "checksum1",
            "file2.txt": "checksum2",
            "file3.txt": "checksum3",
        }

        with patch.object(
            self.file_validator, "get_missing_files", return_value=["file3.txt"]
        ):
            with patch.object(
                self.file_validator, "get_extra_files", return_value=["extra.txt"]
            ):
                with patch.object(
                    self.file_validator,
                    "validate_codebase_integrity",
                    return_value=(False, ["file2.txt"]),  # file2 is corrupted
                ):
                    assessment = self.file_validator.assess_codebase_completeness(
                        "/test", expected_checksums
                    )

        self.assertFalse(assessment["is_complete"])  # file3 is missing
        self.assertFalse(assessment["is_valid"])  # file2 is corrupted
        self.assertEqual(assessment["missing_files"], ["file3.txt"])
        self.assertEqual(assessment["extra_files"], ["extra.txt"])
        self.assertEqual(assessment["corrupted_files"], ["file2.txt"])
        self.assertEqual(assessment["total_files"], 3)
        self.assertEqual(assessment["valid_files"], 1)  # only file1 is valid

    def test_get_file_size_os_error(self):
        """Test file size retrieval with OSError."""
        with patch.object(self.file_validator, "_file_exists", return_value=True):
            with patch.object(
                self.file_validator,
                "_get_file_size",
                side_effect=OSError("Permission denied"),
            ):
                with self.assertRaises(Exception):
                    self.file_validator.get_file_size("test.txt")

    def test_get_codebase_size_with_file_errors(self):
        """Test codebase size calculation with some file errors."""
        with patch.object(self.file_validator, "_file_exists", return_value=True):
            with patch.object(
                self.file_validator,
                "_walk_directory",
                return_value=["file1.txt", "file2.txt", "file3.txt"],
            ):
                with patch.object(self.file_validator, "get_file_size") as mock_size:
                    mock_size.side_effect = [
                        512,
                        Exception("File error"),
                        1024,
                    ]  # file2 fails

                    total_size = self.file_validator.get_codebase_size("/test")

        # Should only include successful file sizes
        self.assertEqual(total_size, 1536)  # 512 + 1024

    def test_create_file_checksum_different_algorithms(self):
        """Test file checksum creation with different algorithms."""
        test_content = b"test content"

        algorithms = ["md5", "sha1", "sha224", "sha256", "sha512"]

        for algorithm in algorithms:
            with patch("builtins.open", mock_open(read_data=test_content)):
                with patch.object(
                    self.file_validator, "_file_exists", return_value=True
                ):
                    with patch(
                        "pysquared.file_validation.manager.file_validation.adafruit_hashlib.new"
                    ) as mock_hash:
                        mock_hash_obj = Mock()
                        mock_hash_obj.hexdigest.return_value = f"{algorithm}_checksum"
                        mock_hash.return_value = mock_hash_obj

                        result = self.file_validator.create_file_checksum(
                            "test.txt", algorithm=algorithm
                        )
                        self.assertEqual(result, f"{algorithm}_checksum")

    def test_create_file_checksum_with_timeout(self):
        """Test file checksum creation with custom timeout."""
        test_content = b"test content"

        with patch("builtins.open", mock_open(read_data=test_content)):
            with patch.object(self.file_validator, "_file_exists", return_value=True):
                with patch(
                    "pysquared.file_validation.manager.file_validation.adafruit_hashlib.new"
                ) as mock_hash:
                    mock_hash_obj = Mock()
                    mock_hash_obj.hexdigest.return_value = "test_checksum"
                    mock_hash.return_value = mock_hash_obj

                    result = self.file_validator.create_file_checksum(
                        "test.txt", timeout=10.0
                    )
                    self.assertEqual(result, "test_checksum")

    def test_create_codebase_checksum_with_exclude_patterns(self):
        """Test codebase checksum creation with exclude patterns."""
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

                    result = self.file_validator.create_codebase_checksum(
                        "/test", exclude_patterns=["*.tmp", "*.log"]
                    )

        expected = {"file1.txt": "checksum1", "file2.txt": "checksum2"}
        self.assertEqual(result, expected)

    def test_get_codebase_size_with_exclude_patterns(self):
        """Test codebase size calculation with exclude patterns."""
        with patch.object(self.file_validator, "_file_exists", return_value=True):
            with patch.object(
                self.file_validator,
                "_walk_directory",
                return_value=["file1.txt", "file2.txt"],
            ):
                with patch.object(
                    self.file_validator, "get_file_size", side_effect=[512, 1024]
                ):
                    total_size = self.file_validator.get_codebase_size(
                        "/test", exclude_patterns=["*.tmp"]
                    )

        self.assertEqual(total_size, 1536)

    def test_validate_file_integrity_with_exception(self):
        """Test file integrity validation with exception."""
        with patch.object(
            self.file_validator,
            "create_file_checksum",
            side_effect=Exception("Some error"),
        ):
            with self.assertRaises(Exception):
                self.file_validator.validate_file_integrity("test.txt", "test_checksum")

    def test_assess_codebase_completeness_with_exception(self):
        """Test codebase completeness assessment with exception."""
        expected_checksums = {"file1.txt": "checksum1"}

        with patch.object(
            self.file_validator,
            "get_missing_files",
            side_effect=Exception("Assessment error"),
        ):
            with self.assertRaises(Exception):
                self.file_validator.assess_codebase_completeness(
                    "/test", expected_checksums
                )


if __name__ == "__main__":
    unittest.main()
