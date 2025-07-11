# OTA Update System

The OTA (Over-The-Air) Update system provides functionality for creating checksums, validating file integrity, and assessing codebase completeness for CircuitPython applications.

## Overview

The OTA update system consists of:

1. **Protocol Definition** (`protos/ota_update.py`): Defines the interface for OTA update operations
2. **Manager Implementation** (`ota_update/manager/ota_update.py`): Concrete implementation of the protocol
3. **Tests** (`tests/unit/test_ota_update.py`): Unit tests for the functionality
4. **Example** (`examples/ota_update_example.py`): Demonstration script

## Features

### File Checksum Creation
- Create MD5 checksums for individual files
- Generate checksums for entire codebases
- Support for exclusion patterns to skip certain files/directories

### File Integrity Validation
- Validate individual files against expected checksums
- Validate entire codebases against checksum manifests
- Detailed reporting of validation failures

### Codebase Assessment
- Comprehensive assessment of codebase completeness and integrity
- Detection of missing files
- Detection of extra/unexpected files
- Identification of corrupted files
- File size calculations

## Usage

### Basic Usage

```python
from pysquared.logger import Logger
from pysquared.nvm.counter import Counter
from pysquared.ota_update.manager.ota_update import OTAUpdateManager

# Initialize the system
error_counter = Counter()
logger = Logger(error_counter)
ota_manager = OTAUpdateManager(logger)

# Create checksums for a codebase
checksums = ota_manager.create_codebase_checksum(
    "/path/to/codebase",
    exclude_patterns=[".git", "__pycache__", ".pyc"]
)

# Validate file integrity
is_valid = ota_manager.validate_file_integrity(
    "/path/to/file.py",
    "expected_checksum_here"
)

# Assess codebase completeness
assessment = ota_manager.assess_codebase_completeness(
    "/path/to/codebase",
    expected_checksums
)
```

### Advanced Usage

```python
# Get missing files
missing_files = ota_manager.get_missing_files(
    "/path/to/codebase",
    ["file1.py", "file2.py", "missing_file.py"]
)

# Get extra files
extra_files = ota_manager.get_extra_files(
    "/path/to/codebase",
    ["file1.py"]  # Only expect file1.py
)

# Get codebase size
total_size = ota_manager.get_codebase_size(
    "/path/to/codebase",
    exclude_patterns=[".git", "__pycache__"]
)
```

## Protocol Interface

The `OTAUpdateProto` interface defines the following methods:

- `create_file_checksum(file_path: str) -> str`
- `create_codebase_checksum(base_path: str, exclude_patterns: Optional[List[str]] = None) -> Dict[str, str]`
- `validate_file_integrity(file_path: str, expected_checksum: str) -> bool`
- `validate_codebase_integrity(base_path: str, expected_checksums: Dict[str, str]) -> Tuple[bool, List[str]]`
- `get_missing_files(base_path: str, expected_files: List[str]) -> List[str]`
- `get_extra_files(base_path: str, expected_files: List[str]) -> List[str]`
- `assess_codebase_completeness(base_path: str, expected_checksums: Dict[str, str]) -> Dict[str, any]`
- `get_file_size(file_path: str) -> int`
- `get_codebase_size(base_path: str, exclude_patterns: Optional[List[str]] = None) -> int`

## Assessment Results

The `assess_codebase_completeness` method returns a dictionary with the following structure:

```python
{
    "is_complete": bool,           # Whether all expected files are present
    "is_valid": bool,              # Whether all present files have correct checksums
    "missing_files": List[str],    # List of missing files
    "extra_files": List[str],      # List of unexpected files
    "corrupted_files": List[str],  # List of files with incorrect checksums
    "total_files": int,            # Total number of files checked
    "valid_files": int             # Number of files with correct checksums
}
```

## CircuitPython Compatibility

The OTA update system is designed to be compatible with CircuitPython:

- Uses standard Python libraries available in CircuitPython
- Implements proper error handling and logging
- Follows the existing codebase patterns and conventions
- Uses MD5 for checksums (available in CircuitPython's `hashlib`)

## Error Handling

The system provides comprehensive error handling:

- `FileNotFoundError`: Raised when files or directories don't exist
- `Exception`: Raised for other errors with detailed logging
- All errors are logged with context information
- Graceful handling of individual file failures during batch operations

## Testing

Run the unit tests:

```bash
python -m pytest tests/unit/test_ota_update.py -v
```

## Example

Run the example script to see the system in action:

```bash
python examples/ota_update_example.py
```

## Integration with OTA Update Protocol

This system provides the foundation for a complete OTA update protocol:

1. **Ground Station**: Uses this system to create checksums for the target codebase
2. **Satellite**: Receives checksums and validates its local files
3. **Update Process**: Downloads missing/corrupted files based on assessment results
4. **Verification**: Re-validates the entire codebase after updates

## Future Enhancements

Potential enhancements for the OTA update system:

- Support for different checksum algorithms (SHA-256, etc.)
- Incremental update support
- Compression of file manifests
- Integration with radio communication for remote updates
- Rollback functionality for failed updates
- Progress reporting for large operations
