"""
Protocol defining the interface for Over-The-Air (OTA) update functionality.
This protocol provides methods for creating checksums, validating file integrity,
and managing the update process for CircuitPython applications.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional, Tuple


class OTAUpdateProto:
    """Protocol defining the interface for OTA update operations."""

    def create_file_checksum(self, file_path: str) -> str:
        """Create a checksum for a single file.

        :param str file_path: The path to the file to checksum.
        :return: The checksum of the file as a hexadecimal string.
        :rtype: str
        :raises FileNotFoundError: If the file does not exist.
        :raises Exception: If there is an error reading the file or creating the checksum.
        """
        ...

    def create_codebase_checksum(
        self, base_path: str, exclude_patterns: "Optional[List[str]]" = None
    ) -> "Dict[str, str]":
        """Create checksums for all files in the codebase.

        :param str base_path: The base directory path to scan for files.
        :param List[str] | None exclude_patterns: Optional list of file patterns to exclude from checksumming.
        :return: A dictionary mapping file paths to their checksums.
        :rtype: Dict[str, str]
        :raises Exception: If there is an error scanning the directory or creating checksums.
        """
        ...

    def validate_file_integrity(self, file_path: str, expected_checksum: str) -> bool:
        """Validate the integrity of a single file against an expected checksum.

        :param str file_path: The path to the file to validate.
        :param str expected_checksum: The expected checksum to compare against.
        :return: True if the file checksum matches the expected checksum, False otherwise.
        :rtype: bool
        :raises FileNotFoundError: If the file does not exist.
        :raises Exception: If there is an error reading the file or creating the checksum.
        """
        ...

    def validate_codebase_integrity(
        self, base_path: str, expected_checksums: "Dict[str, str]"
    ) -> "Tuple[bool, List[str]]":
        """Validate the integrity of all files in the codebase against expected checksums.

        :param str base_path: The base directory path to scan for files.
        :param Dict[str, str] expected_checksums: Dictionary mapping file paths to their expected checksums.
        :return: A tuple containing (is_valid, list_of_failed_files).
        :rtype: Tuple[bool, List[str]]
        :raises Exception: If there is an error scanning the directory or validating files.
        """
        ...

    def get_missing_files(
        self, base_path: str, expected_files: "List[str]"
    ) -> "List[str]":
        """Get a list of files that are expected but missing from the codebase.

        :param str base_path: The base directory path to scan for files.
        :param List[str] expected_files: List of file paths that should exist.
        :return: List of file paths that are missing.
        :rtype: List[str]
        :raises Exception: If there is an error scanning the directory.
        """
        ...

    def get_extra_files(
        self, base_path: str, expected_files: "List[str]"
    ) -> "List[str]":
        """Get a list of files that exist but are not in the expected file list.

        :param str base_path: The base directory path to scan for files.
        :param List[str] expected_files: List of file paths that should exist.
        :return: List of file paths that are extra/unexpected.
        :rtype: List[str]
        :raises Exception: If there is an error scanning the directory.
        """
        ...

    def assess_codebase_completeness(
        self, base_path: str, expected_checksums: "Dict[str, str]"
    ) -> "Dict[str, Any]":
        """Assess the completeness and integrity of the codebase.

        :param str base_path: The base directory path to scan for files.
        :param Dict[str, str] expected_checksums: Dictionary mapping file paths to their expected checksums.
        :return: A dictionary containing assessment results including:
                 - is_complete: bool - Whether all expected files are present
                 - is_valid: bool - Whether all present files have correct checksums
                 - missing_files: List[str] - List of missing files
                 - extra_files: List[str] - List of unexpected files
                 - corrupted_files: List[str] - List of files with incorrect checksums
                 - total_files: int - Total number of files checked
                 - valid_files: int - Number of files with correct checksums
        :rtype: Dict[str, Any]
        :raises Exception: If there is an error during assessment.
        """
        ...

    def get_file_size(self, file_path: str) -> int:
        """Get the size of a file in bytes.

        :param str file_path: The path to the file.
        :return: The size of the file in bytes.
        :rtype: int
        :raises FileNotFoundError: If the file does not exist.
        :raises Exception: If there is an error accessing the file.
        """
        ...

    def get_codebase_size(
        self, base_path: str, exclude_patterns: "Optional[List[str]]" = None
    ) -> int:
        """Get the total size of all files in the codebase.

        :param str base_path: The base directory path to scan for files.
        :param List[str] | None exclude_patterns: Optional list of file patterns to exclude.
        :return: The total size of all files in bytes.
        :rtype: int
        :raises Exception: If there is an error scanning the directory.
        """
        ...
