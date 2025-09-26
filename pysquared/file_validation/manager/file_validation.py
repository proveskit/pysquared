"""
File Validation Manager implementation.

This module provides file validation functionality for creating checksums,
validating file integrity, and assessing codebase completeness in CircuitPython.

Usage Example:
    ```python
    import board
    from pysquared.logger import Logger
    from pysquared.file_validation.manager.file_validation import FileValidationManager

    # Initialize logger
    logger = Logger("file_validation")

    # Create file validation manager
    file_validator = FileValidationManager(logger)

    # Create checksum for a single file (MD5 by default for speed)
    # Memory usage is automatically optimized for constrained devices like RP2040
    checksum = file_validator.create_file_checksum("main.py")
    print(f"main.py checksum: {checksum}")

    # Create checksum with specific algorithm
    sha256_checksum = file_validator.create_file_checksum("config.py", algorithm="sha256")
    print(f"config.py SHA256: {sha256_checksum}")

    # Validate file integrity
    expected_checksum = "d41d8cd98f00b204e9800998ecf8427e"
    is_valid = file_validator.validate_file_integrity("main.py", expected_checksum)
    print(f"File integrity: {'PASS' if is_valid else 'FAIL'}")

    # Create checksums for entire codebase
    # Hidden files (starting with .) are automatically ignored
    checksums = file_validator.create_codebase_checksum("/", exclude_patterns=["__pycache__", ".pyc"])
    print(f"Codebase has {len(checksums)} files")

    # Assess codebase completeness
    assessment = file_validator.assess_codebase_completeness("/", checksums)
    print(f"Codebase complete: {assessment['is_complete']}")
    print(f"Codebase valid: {assessment['is_valid']}")
    print(f"Missing files: {assessment['missing_files']}")
    print(f"Extra files: {assessment['extra_files']}")

    # Get file and codebase sizes
    file_size = file_validator.get_file_size("main.py")
    codebase_size = file_validator.get_codebase_size("/")
    print(f"main.py size: {file_size} bytes")
    print(f"Codebase size: {codebase_size} bytes")
    ```
"""

import gc
import os
import time

import adafruit_hashlib

from ...logger import Logger

# Constants for error messages
FILE_NOT_FOUND_MSG = "File not found"
NO_SUCH_FILE_MSG = "No such file"


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
        :note: Hidden files (starting with .) are automatically excluded.
        """
        exclude_patterns = exclude_patterns or []
        file_paths = []
        stack = [(base_path, "")]

        while stack:
            current_path, relative_path = stack.pop()

            try:
                for item in os.listdir(current_path):
                    # Build paths
                    item_path = f"{current_path}/{item}" if current_path else item
                    item_relative = f"{relative_path}/{item}" if relative_path else item

                    # Skip hidden files and excluded patterns
                    if item.startswith(".") or any(
                        pattern in item_relative for pattern in exclude_patterns
                    ):
                        continue

                    # Determine if item is directory or file
                    if self._is_directory(item_path):
                        stack.append((item_path, item_relative))
                    else:
                        file_paths.append(item_relative)

            except OSError:
                # Directory doesn't exist or can't be read
                pass

        return file_paths

    def _is_directory(self, path: str) -> bool:
        """Check if a path is a directory.

        :param str path: The path to check.
        :return: True if the path is a directory, False otherwise.
        """
        try:
            os.listdir(path)
            return True
        except OSError:
            return False

    def _create_checksum(self, file_path: str, algorithm: str, timeout: float) -> str:
        """Create checksum using adafruit_hashlib.

        :param str file_path: The path to the file to checksum.
        :param str algorithm: The hash algorithm to use.
        :param float timeout: Maximum time to allow for reading the file.
        :return: The checksum as a hexadecimal string.
        :raises TimeoutError: If reading the file takes longer than the timeout.
        :raises MemoryError: If there is insufficient memory to process the file.
        """
        hash_obj = adafruit_hashlib.new(algorithm)

        # Use smaller chunk size for memory-constrained devices like RP2040
        chunk_size = 512  # Reduced from 4096 to 512 bytes

        try:
            with open(file_path, "rb") as f:
                start_time = time.monotonic()
                while True:
                    if time.monotonic() - start_time > timeout:
                        raise TimeoutError(
                            f"File read operation timed out after {timeout} seconds"
                        )

                    try:
                        chunk = f.read(chunk_size)
                        if not chunk:  # Empty chunk means end of file
                            break
                        hash_obj.update(chunk)

                        # Force garbage collection after each chunk to free memory
                        gc.collect()

                    except MemoryError:
                        # If we run out of memory, try with an even smaller chunk
                        if chunk_size > 64:
                            chunk_size = chunk_size // 2
                            self._log.warning(
                                "Memory error, reducing chunk size",
                                file_path=file_path,
                                new_chunk_size=chunk_size,
                            )
                            continue

        except MemoryError as e:
            self._log.error(
                "Memory error during checksum creation",
                file_path=file_path,
                err=e,
            )
            raise

        return hash_obj.hexdigest()

    def create_file_checksum(
        self, file_path: str, timeout: float = 10.0, algorithm: str = "md5"
    ) -> str:
        """Create a checksum for a single file.

        :param str file_path: The path to the file to checksum.
        :param float timeout: Maximum time (in seconds) to allow for reading the file. Default is 5 seconds.
        :param str algorithm: Hash algorithm to use ('md5', 'sha1', 'sha224', 'sha256', 'sha512'). Default is 'md5' for speed.
        :return: The checksum of the file as a hexadecimal string.
        :rtype: str
        :raises FileNotFoundError: If the file is not found.
        :raises TimeoutError: If reading the file takes longer than the timeout.
        :raises MemoryError: If there is insufficient memory to process the file.
        :raises RuntimeError: If there is an error reading the file or creating the checksum.
        """
        try:
            if not self._file_exists(file_path):
                raise FileNotFoundError(f"{FILE_NOT_FOUND_MSG}: {file_path}")

            checksum_str = self._create_checksum(file_path, algorithm, timeout)

            self._log.debug(
                "Created checksum for file",
                file_path=file_path,
                checksum=checksum_str,
                algorithm=algorithm,
            )
            return checksum_str

        except OSError as e:
            if NO_SUCH_FILE_MSG in str(e) or FILE_NOT_FOUND_MSG in str(e):
                self._log.error(
                    f"{FILE_NOT_FOUND_MSG} during checksum creation",
                    file_path=file_path,
                    err=FileNotFoundError(FILE_NOT_FOUND_MSG),
                )
                raise FileNotFoundError(f"{FILE_NOT_FOUND_MSG}: {file_path}") from e
            else:
                self._log.error(
                    "OS error during checksum creation", err=e, file_path=file_path
                )
                raise
        except MemoryError as e:
            self._log.error(
                "Memory error during checksum creation",
                file_path=file_path,
                err=e,
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
            gc.collect()

    def create_codebase_checksum(
        self, base_path: str, exclude_patterns: list | None = None
    ) -> dict:
        """Create checksums for all files in the codebase.

        :param str base_path: The base directory path to scan for files.
        :param List[str] | None exclude_patterns: Optional list of file patterns to exclude from checksumming.
        :return: A dictionary mapping file paths to their checksums.
        :rtype: Dict[str, str]
        :raises ValueError: If the base path is not found.
        :raises RuntimeError: If there is an error scanning the directory or creating checksums.
        """
        try:
            if not self._file_exists(base_path):
                raise ValueError(f"Base path not found: {base_path}")

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

        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            self._log.error(
                "Error creating codebase checksums", err=e, base_path=base_path
            )
            raise RuntimeError(f"Error creating codebase checksums: {e}") from e

    def validate_file_integrity(self, file_path: str, expected_checksum: str) -> bool:
        """Validate the integrity of a single file against an expected checksum.

        :param str file_path: The path to the file to validate.
        :param str expected_checksum: The expected checksum to compare against.
        :return: True if the file checksum matches the expected checksum, False otherwise.
        :rtype: bool
        :raises FileNotFoundError: If the file is not found.
        :raises RuntimeError: If there is an error reading the file or creating the checksum.
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

        except FileNotFoundError:
            # Re-raise FileNotFoundError as-is
            raise
        except Exception as e:
            self._log.error(
                "Error during file integrity validation", err=e, file_path=file_path
            )
            raise RuntimeError(f"Error during file integrity validation: {e}") from e

    def validate_codebase_integrity(
        self, base_path: str, expected_checksums: dict
    ) -> tuple:
        """Validate the integrity of all files in the codebase against expected checksums.

        :param str base_path: The base directory path to scan for files.
        :param Dict[str, str] expected_checksums: Dictionary mapping file paths to their expected checksums.
        :return: A tuple containing (is_valid, list_of_failed_files).
        :rtype: Tuple[bool, List[str]]
        :raises RuntimeError: If there is an error scanning the directory or validating files.
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
                    if FILE_NOT_FOUND_MSG in str(e):
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
        :raises RuntimeError: If there is an error scanning the directory.
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
            raise RuntimeError(f"Error identifying missing files: {e}") from e

    def get_extra_files(self, base_path: str, expected_files: list) -> list:
        """Get a list of files that exist but are not in the expected file list.

        :param str base_path: The base directory path to scan for files.
        :param List[str] expected_files: List of file paths that should exist.
        :return: List of file paths that are extra/unexpected.
        :rtype: List[str]
        :raises RuntimeError: If there is an error scanning the directory.
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
            raise RuntimeError(f"Error identifying extra files: {e}") from e

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
        :raises RuntimeError: If there is an error during assessment.
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
            raise RuntimeError(
                f"Error during codebase completeness assessment: {e}"
            ) from e

    def get_file_size(self, file_path: str) -> int:
        """Get the size of a file in bytes.

        :param str file_path: The path to the file.
        :return: The size of the file in bytes.
        :rtype: int
        :raises FileNotFoundError: If the file is not found.
        :raises RuntimeError: If there is an error accessing the file.
        """
        try:
            if not self._file_exists(file_path):
                raise FileNotFoundError(f"{FILE_NOT_FOUND_MSG}: {file_path}")

            file_size = self._get_file_size(file_path)
            self._log.debug(
                "Retrieved file size", file_path=file_path, size_bytes=file_size
            )
            return file_size

        except FileNotFoundError:
            # Re-raise FileNotFoundError as-is
            raise
        except Exception as e:
            self._log.error("Error getting file size", err=e, file_path=file_path)
            raise RuntimeError(f"Error getting file size: {e}") from e

    def get_codebase_size(
        self, base_path: str, exclude_patterns: list | None = None
    ) -> int:
        """Get the total size of all files in the codebase.

        :param str base_path: The base directory path to scan for files.
        :param List[str] | None exclude_patterns: Optional list of file patterns to exclude.
        :return: The total size of all files in bytes.
        :rtype: int
        :raises ValueError: If the base path is not found.
        :raises RuntimeError: If there is an error scanning the directory.
        """
        try:
            if not self._file_exists(base_path):
                raise ValueError(f"Base path not found: {base_path}")

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

        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            self._log.error(
                "Error calculating codebase size", err=e, base_path=base_path
            )
            raise RuntimeError(f"Error calculating codebase size: {e}") from e
