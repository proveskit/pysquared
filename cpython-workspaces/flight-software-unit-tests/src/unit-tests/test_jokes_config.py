"""Integration tests for JokesConfig, ability to get the jokes out of the config.

This module contains integration tests that verify the complete JokesConfig pipeline
Of getting, initializing, adding, saving and removing jokes
"""

import json
import os
import tempfile

import pytest
from pysquared.config.jokes_config import JokesConfig


@pytest.fixture()
def jokes_file_fixture():
    """Create a temporary jokes JSON file for testing."""
    jokes = [
        "Why did the chicken cross the road? To get to the other side!",
        "Parallel lines have so much in common… it’s a shame they’ll never meet.",
    ]
    temp_dir = tempfile.mkdtemp()

    path = os.path.join(temp_dir, "jokes.test.json")
    with open(path, "w") as f:
        json.dump(jokes, f)

    yield path

    os.remove(path)
    os.rmdir(temp_dir)


def test_load_jokes_success(jokes_file_fixture):
    """Tests if you can load jokes
    Args:
        jokes_file_fixture: JSON file fixture."""
    config = JokesConfig(jokes_file_fixture)
    assert isinstance(config.jokes, list)
    assert len(config.jokes) == 2
    assert all(isinstance(j, str) for j in config.jokes)


def test_invalid_jokes_file_format():
    """Tests what happens when invalid file for jokes"""

    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write('{"not": "a list"}')
        tmp_path = tmp.name

    with pytest.raises(ValueError):
        JokesConfig(tmp_path)

    os.remove(tmp_path)


def test_validate_joke_valid(jokes_file_fixture):
    """Tests validate joke function
    Args:
        jokes_file_fixture: JSON file fixture."""
    config = JokesConfig(jokes_file_fixture)
    config.validate_joke("This is a valid joke.")


@pytest.mark.parametrize("bad_joke", [None, 123, "", " " * 10, "A" * 501])
def test_validate_joke_invalid(jokes_file_fixture, bad_joke):
    """Tests Validate Bad Joke, this raises
    Args:
        bad joke: badly formatted json file .
    """
    config = JokesConfig(jokes_file_fixture)

    with pytest.raises((TypeError, ValueError)):
        config.validate_joke(bad_joke)


def test_add_joke_temporary(jokes_file_fixture):
    """Testing adding a joke temporarily. This will add a joke to the list
    but not the physical config file

    Args:
        jokes_file_fixture: JSON file fixture.
    """
    config = JokesConfig(jokes_file_fixture)
    new_joke = "This is a temporary test joke."
    config.add_joke(new_joke)
    assert new_joke in config.jokes


def test_add_joke_permanent(jokes_file_fixture):
    """This tests adding a joke permanently to the json object
    Args:
        jokes_file_fixture: JSON file fixture.
    """
    config = JokesConfig(jokes_file_fixture)
    new_joke = "This is a permanent test joke."
    config.add_joke(new_joke, temporary=False)

    # Reload config to ensure it was saved
    new_config = JokesConfig(jokes_file_fixture)
    assert new_joke in new_config.jokes


def test_update_joke_temporary(jokes_file_fixture):
    """This tests editing a specific joke using the index
    Args:
        jokes_file_fixture: JSON file fixture."""

    config = JokesConfig(jokes_file_fixture)
    updated_joke = "Updated joke temporarily"
    config.update_joke(0, updated_joke)
    assert config.jokes[0] == updated_joke


def test_update_joke_permanent(jokes_file_fixture):
    """This tests editing a specific joke using the index and saving it permanently in the JSON
    Args:
        jokes_file_fixture: JSON file fixture."""

    config = JokesConfig(jokes_file_fixture)
    updated_joke = "Updated joke permanently"
    config.update_joke(0, updated_joke, temporary=False)

    new_config = JokesConfig(jokes_file_fixture)
    assert new_config.jokes[0] == updated_joke


def test_update_joke_invalid_index(jokes_file_fixture):
    """This Test makes sure that indexing the JSON with an invalid index raises an Index Error
    Args:
        jokes_file_fixture: JSON file fixture.
    """
    config = JokesConfig(jokes_file_fixture)
    with pytest.raises(IndexError):
        config.update_joke(100, "Doesn't matter")


def test_remove_joke_temporary(jokes_file_fixture):
    """removing a joke from the JSON object
    Args:
        jokes_file_fixture: JSON file fixture."""
    config = JokesConfig(jokes_file_fixture)
    joke_to_remove = config.jokes[0]
    config.remove_joke(0)
    assert joke_to_remove not in config.jokes


def test_remove_joke_permanent(jokes_file_fixture):
    """removing a joke from the JSON object permanatly
    Args:
        jokes_file_fixture: JSON file fixture."""
    config = JokesConfig(jokes_file_fixture)
    joke_to_remove = config.jokes[0]
    config.remove_joke(0, temporary=False)

    new_config = JokesConfig(jokes_file_fixture)
    assert joke_to_remove not in new_config.jokes


def test_remove_joke_invalid_index(jokes_file_fixture):
    """removing a joke with an invalid index gives an IndexError
    Args:
        jokes_file_fixture: JSON file fixture."""
    config = JokesConfig(jokes_file_fixture)
    with pytest.raises(IndexError):
        config.remove_joke(100)


def test_get_joke_valid(jokes_file_fixture):
    """Gets a joke from the file fixture and ensures it is valid
    Args:
        jokes_file_fixture: JSON file fixture."""
    config = JokesConfig(jokes_file_fixture)
    joke = config.get_joke(0)
    assert isinstance(joke, str)


def test_get_joke_invalid_index(jokes_file_fixture):
    """removing a joke from an incorrect index and ensures it raises an IndexError
    Args:
        jokes_file_fixture: JSON file fixture."""
    config = JokesConfig(jokes_file_fixture)
    with pytest.raises(IndexError):
        config.get_joke(100)
