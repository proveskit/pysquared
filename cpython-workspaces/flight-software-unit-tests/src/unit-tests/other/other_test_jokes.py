"""Unit tests for the jokes.json file.

This module contains unit tests to ensure that jokes.json exists, is valid JSON,
and contains the expected structure and content.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def jokes_data():
    """Loads and provides jokes data from jokes.json.

    Returns:
        list: The jokes loaded from jokes.json.
    """
    workspace_root = Path(__file__).parent.parent.parent
    jokes_path = workspace_root / "unit-tests" / "files" / "jokes.test.json"
    with open(jokes_path, "r") as f:
        return json.loads(f.read())


def test_jokes_file_exists():
    """Tests that jokes.json exists.

    This test verifies that the `jokes.json` file is present in the expected
    location within the project structure.
    """
    workspace_root = Path(__file__).parent.parent.parent
    jokes_path = workspace_root / "unit-tests" / "files" / "jokes.test.json"
    assert jokes_path.exists(), "jokes.json file not found"


def test_jokes_is_valid_json():
    """Tests that jokes.json is valid JSON.

    This test ensures that the content of `jokes.json` can be successfully
    parsed as a JSON array.
    """
    workspace_root = Path(__file__).parent.parent.parent
    jokes_path = workspace_root / "unit-tests" / "files" / "jokes.test.json"
    with open(jokes_path, "r") as f:
        data = json.loads(f.read())
    assert isinstance(data, list), "Jokes file is not a valid JSON array"


def test_jokes_not_empty(jokes_data):
    """Tests that jokes list is not empty.

    Args:
        jokes_data: Fixture providing the loaded jokes data.

    This test specifically checks that the jokes list is not empty and that
    all its elements are strings, ensuring valid content.
    """
    assert len(jokes_data) > 0, "jokes list cannot be empty"
    assert all(isinstance(joke, str) for joke in jokes_data), (
        "All jokes must be strings"
    )


def test_jokes_are_strings(jokes_data):
    """Tests that all jokes are strings.

    Args:
        jokes_data: Fixture providing the loaded jokes data.

    This test ensures that each joke in the list is a non-empty string.
    """
    for i, joke in enumerate(jokes_data):
        assert isinstance(joke, str), f"Joke at index {i} is not a string"
        assert len(joke) > 0, f"Joke at index {i} is an empty string"
