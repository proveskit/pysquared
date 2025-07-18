"""
File Validation Manager implementation.

This module provides file validation functionality for creating checksums,
validating file integrity, and assessing codebase completeness in CircuitPython.
"""

import os
import time

import adafruit_hashlib

from ...logger import Logger


class FileValidationManager:
    """File validation functionality for CircuitPython applications."""

    def __init__(self, logger: Logger) -> None:
        """Initialize the File Validation Manager.

        :param Logger logger: Logger instance for logging messages.
        """
        self._log = logger
        self._log.debug("Initializing File Validation Manager")

    def _file_exists(self, file_path: str) -> bool:
        """Check if a file exists (CircuitPython compatible).

        :param str file_path: The path to the file to check.
        :return: True if the file exists, False otherwise.
        """
        try:
            os.stat(file_path)
            return True
        except OSError:
            return False

    def _get_file_size(self, file_path: str) -> int:
        """Get file size (CircuitPython compatible).

        :param str file_path: The path to the file.
        :return: The size of the file in bytes.
        """
        try:
            stat = os.stat(file_path)
            return stat[6]  # st_size is at index 6 in CircuitPython
        except OSError:
            return 0

    # Removed the unused _calculate_checksum method to eliminate dead code.
    def _walk_directory(
        self, base_path: str, exclude_patterns: list | None = None
    ) -> list:
        """Walk directory iteratively and return all file paths (CircuitPython compatible).

        :param str base_path: The base directory to walk.
        :param List[str] exclude_patterns: Patterns to exclude.
        :return: List of file paths relative to base_path.
        """
        exclude_patterns = exclude_patterns or []
        file_paths = []

        # Stack to keep track of directories to process
        # Each item is a tuple of (current_path, relative_path)
        stack = [(base_path, "")]

        while stack:
            current_path, relative_path = stack.pop()

            try:
                items = os.listdir(current_path)
                for item in items:
                    item_path = current_path + "/" + item if current_path else item
                    item_relative = (
                        relative_path + "/" + item if relative_path else item
                    )

                    # Check if this path should be excluded
                    if any(pattern in item_relative for pattern in exclude_patterns):
                        continue

                    # Check if it's a directory by trying to list it
                    try:
                        os.listdir(item_path)
                        # It's a directory, add to stack for later processing
                        stack.append((item_path, item_relative))
                    except OSError:
                        # It's a file, add to list
                        file_paths.append(item_relative)
            except OSError:
                # Directory doesn't exist or can't be read
                pass

        return file_paths

    def _create_checksum(self, file_path: str, algorithm: str, timeout: float) -> str:
        """Create checksum using adafruit_hashlib.

        :param str file_path: The path to the file to checksum.
        :param str algorithm: The hash algorithm to use.
        :param float timeout: Maximum time to allow for reading the file.
        :return: The checksum as a hexadecimal string.
        :raises TimeoutError: If reading the file takes longer than the timeout.
        """
        hash_obj = adafruit_hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            start_time = time.monotonic()
            while True:
                if time.monotonic() - start_time > timeout:
                    raise TimeoutError(
                        f"File read operation timed out after {timeout} seconds"
                    )
                chunk = f.read(4096)
                if not chunk:  # Empty chunk means end of file
                    break
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def create_file_checksum(
        self, file_path: str, timeout: float = 5.0, algorithm: str = "md5"
    ) -> str:
        """Create a checksum for a single file.

        :param str file_path: The path to the file to checksum.
        :param float timeout: Maximum time (in seconds) to allow for reading the file. Default is 5 seconds.
        :param str algorithm: Hash algorithm to use ('md5', 'sha1', 'sha224', 'sha256', 'sha512'). Default is 'md5' for speed.
        :return: The checksum of the file as a hexadecimal string.
        :rtype: str
        :raises Exception: If there is an error reading the file or creating the checksum.
        :raises TimeoutError: If reading the file takes longer than the timeout.
        """
        try:
            if not self._file_exists(file_path):
                raise Exception(f"File not found: {file_path}")

            checksum_str = self._create_checksum(file_path, algorithm, timeout)

            self._log.debug(
                "Created checksum for file",
                file_path=file_path,
                checksum=checksum_str,
                algorithm=algorithm,
            )
            return checksum_str

        except OSError as e:
            if "No such file" in str(e) or "File not found" in str(e):
                self._log.error(
                    "File not found during checksum creation",
                    file_path=file_path,
                    err=Exception("File not found"),
                )
                raise Exception(f"File not found: {file_path}") from e
            else:
                self._log.error(
                    "OS error during checksum creation", err=e, file_path=file_path
                )
                raise
        except Exception as e:
            self._log.error("Error creating file checksum", err=e, file_path=file_path)
            raise

    def _process_single_file_checksum(
        self, base_path: str, relative_path: str
    ) -> str | None:
        """Process a single file to create its checksum.

        :param str base_path: The base directory path.
        :param str relative_path: The relative path of the file.
        :return: The checksum if successful, None if failed.
        """
        # Construct full path
        full_path = base_path + "/" + relative_path if base_path else relative_path

        try:
            checksum = self.create_file_checksum(full_path)
            return checksum
        except Exception as e:
            self._log.warning(
                "Failed to create checksum for file",
                file_path=relative_path,
                err=e,
            )
            return None
        finally:
            # Force garbage collection after each file to prevent memory buildup
            try:
                import gc

                gc.collect()
            except ImportError:
                # gc module not available in some CircuitPython environments
                pass

    def create_codebase_checksum(
        self, base_path: str, exclude_patterns: list | None = None
    ) -> dict:
        """Create checksums for all files in the codebase.

        :param str base_path: The base directory path to scan for files.
        :param List[str] | None exclude_patterns: Optional list of file patterns to exclude from checksumming.
        :return: A dictionary mapping file paths to their checksums.
        :rtype: Dict[str, str]
        :raises Exception: If there is an error scanning the directory or creating checksums.
        """
        try:
            if not self._file_exists(base_path):
                raise Exception(f"Base path not found: {base_path}")

            checksums = {}
            exclude_patterns = exclude_patterns or []

            # Get all files in the directory tree
            file_paths = self._walk_directory(base_path, exclude_patterns)

            # Process each file
            for relative_path in file_paths:
                checksum = self._process_single_file_checksum(base_path, relative_path)
                if checksum is not None:
                    checksums[relative_path] = checksum

            self._log.info(
                "Created checksums for codebase",
                base_path=base_path,
                file_count=len(checksums),
            )
            return checksums

        except Exception as e:
            self._log.error(
                "Error creating codebase checksums", err=e, base_path=base_path
            )
            raise

    def validate_file_integrity(self, file_path: str, expected_checksum: str) -> bool:
        """Validate the integrity of a single file against an expected checksum.

        :param str file_path: The path to the file to validate.
        :param str expected_checksum: The expected checksum to compare against.
        :return: True if the file checksum matches the expected checksum, False otherwise.
        :rtype: bool
        :raises Exception: If there is an error reading the file or creating the checksum.
        """
        try:
            actual_checksum = self.create_file_checksum(file_path)
            is_valid = actual_checksum == expected_checksum

            if is_valid:
                self._log.debug("File integrity validation passed", file_path=file_path)
            else:
                self._log.warning(
                    "File integrity validation failed",
                    file_path=file_path,
                    expected=expected_checksum,
                    actual=actual_checksum,
                )

            return is_valid

        except Exception as e:
            if "File not found" in str(e):
                self._log.error(
                    "File not found during integrity validation",
                    file_path=file_path,
                    err=Exception("File not found"),
                )
                raise
            else:
                self._log.error(
                    "Error during file integrity validation", err=e, file_path=file_path
                )
                raise

    def validate_codebase_integrity(
        self, base_path: str, expected_checksums: dict
    ) -> tuple:
        """Validate the integrity of all files in the codebase against expected checksums.

        :param str base_path: The base directory path to scan for files.
        :param Dict[str, str] expected_checksums: Dictionary mapping file paths to their expected checksums.
        :return: A tuple containing (is_valid, list_of_failed_files).
        :rtype: Tuple[bool, List[str]]
        :raises Exception: If there is an error scanning the directory or validating files.
        """
        try:
            failed_files = []
            total_files = len(expected_checksums)
            validated_files = 0

            for file_path, expected_checksum in expected_checksums.items():
                # Construct full path
                full_path = base_path + "/" + file_path if base_path else file_path

                try:
                    if self.validate_file_integrity(full_path, expected_checksum):
                        validated_files += 1
                    else:
                        failed_files.append(file_path)
                except Exception as e:
                    if "File not found" in str(e):
                        failed_files.append(file_path)
                    else:
                        self._log.warning(
                            "Error validating file", file_path=file_path, err=e
                        )
                        failed_files.append(file_path)

            is_valid = len(failed_files) == 0

            self._log.info(
                "Codebase integrity validation completed",
                base_path=base_path,
                total_files=total_files,
                validated_files=validated_files,
                failed_files=len(failed_files),
                is_valid=is_valid,
            )

            return is_valid, failed_files

        except Exception as e:
            self._log.error(
                "Error during codebase integrity validation", err=e, base_path=base_path
            )
            raise

    def get_missing_files(self, base_path: str, expected_files: list) -> list:
        """Get a list of files that are expected but missing from the codebase.

        :param str base_path: The base directory path to scan for files.
        :param List[str] expected_files: List of file paths that should exist.
        :return: List of file paths that are missing.
        :rtype: List[str]
        :raises Exception: If there is an error scanning the directory.
        """
        try:
            missing_files = []

            for file_path in expected_files:
                full_path = base_path + "/" + file_path if base_path else file_path
                if not self._file_exists(full_path):
                    missing_files.append(file_path)

            self._log.debug(
                "Identified missing files",
                base_path=base_path,
                missing_count=len(missing_files),
                total_expected=len(expected_files),
            )

            return missing_files

        except Exception as e:
            self._log.error(
                "Error identifying missing files", err=e, base_path=base_path
            )
            raise

    def get_extra_files(self, base_path: str, expected_files: list) -> list:
        """Get a list of files that exist but are not in the expected file list.

        :param str base_path: The base directory path to scan for files.
        :param List[str] expected_files: List of file paths that should exist.
        :return: List of file paths that are extra/unexpected.
        :rtype: List[str]
        :raises Exception: If there is an error scanning the directory.
        """
        try:
            extra_files = []
            expected_set = set(expected_files)

            # Get all files in the directory tree
            all_files = self._walk_directory(base_path)

            for file_path in all_files:
                if file_path not in expected_set:
                    extra_files.append(file_path)

            self._log.debug(
                "Identified extra files",
                base_path=base_path,
                extra_count=len(extra_files),
            )

            return extra_files

        except Exception as e:
            self._log.error("Error identifying extra files", err=e, base_path=base_path)
            raise

    def assess_codebase_completeness(
        self, base_path: str, expected_checksums: dict
    ) -> dict:
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
        try:
            expected_files = list(expected_checksums.keys())

            # Get missing and extra files
            missing_files = self.get_missing_files(base_path, expected_files)
            extra_files = self.get_extra_files(base_path, expected_files)

            # Validate integrity of present files
            is_valid, corrupted_files = self.validate_codebase_integrity(
                base_path, expected_checksums
            )

            # Calculate statistics
            total_files = len(expected_files)
            valid_files = total_files - len(missing_files) - len(corrupted_files)
            is_complete = len(missing_files) == 0

            assessment = {
                "is_complete": is_complete,
                "is_valid": is_valid,
                "missing_files": missing_files,
                "extra_files": extra_files,
                "corrupted_files": corrupted_files,
                "total_files": total_files,
                "valid_files": valid_files,
            }

            self._log.info(
                "Codebase completeness assessment completed",
                base_path=base_path,
                is_complete=is_complete,
                is_valid=is_valid,
                total_files=total_files,
                valid_files=valid_files,
                missing_files=len(missing_files),
                extra_files=len(extra_files),
                corrupted_files=len(corrupted_files),
            )

            return assessment

        except Exception as e:
            self._log.error(
                "Error during codebase completeness assessment",
                err=e,
                base_path=base_path,
            )
            raise

    def get_file_size(self, file_path: str) -> int:
        """Get the size of a file in bytes.

        :param str file_path: The path to the file.
        :return: The size of the file in bytes.
        :rtype: int
        :raises Exception: If there is an error accessing the file.
        """
        try:
            if not self._file_exists(file_path):
                raise Exception(f"File not found: {file_path}")

            file_size = self._get_file_size(file_path)
            self._log.debug(
                "Retrieved file size", file_path=file_path, size_bytes=file_size
            )
            return file_size

        except Exception as e:
            if "File not found" in str(e):
                self._log.error(
                    "File not found when getting size",
                    file_path=file_path,
                    err=Exception("File not found"),
                )
                raise
            else:
                self._log.error("Error getting file size", err=e, file_path=file_path)
                raise

    def get_codebase_size(
        self, base_path: str, exclude_patterns: list | None = None
    ) -> int:
        """Get the total size of all files in the codebase.

        :param str base_path: The base directory path to scan for files.
        :param List[str] | None exclude_patterns: Optional list of file patterns to exclude.
        :return: The total size of all files in bytes.
        :rtype: int
        :raises Exception: If there is an error scanning the directory.
        """
        try:
            if not self._file_exists(base_path):
                raise Exception(f"Base path not found: {base_path}")

            total_size = 0
            exclude_patterns = exclude_patterns or []

            # Get all files in the directory tree
            file_paths = self._walk_directory(base_path, exclude_patterns)

            for relative_path in file_paths:
                full_path = (
                    base_path + "/" + relative_path if base_path else relative_path
                )
                try:
                    file_size = self.get_file_size(full_path)
                    total_size += file_size
                except Exception as e:
                    self._log.warning(
                        "Failed to get size for file", file_path=relative_path, err=e
                    )

            self._log.info(
                "Calculated codebase size",
                base_path=base_path,
                total_size_bytes=total_size,
            )
            return total_size

        except Exception as e:
            self._log.error(
                "Error calculating codebase size", err=e, base_path=base_path
            )
            raise
