"""
This module provides the JokesConfig class, which handles loading,
validating, and updating jokes from a jokes.json file.

Classes:
    JokesConfig: Loads jokes from a JSON file, validates joke entries,
        allows updating jokes (temporary or permanent), and saves changes.
"""

import json


class JokesConfig:
    """
    Jokes configuration handler.

    Loads jokes from a JSON file as a list of strings. Provides methods
    to validate jokes, update them temporarily (RAM-only) or permanently
    (saved back to file), and retrieve jokes.

    Attributes:
        jokes_file (str): Path to the jokes JSON file.
        jokes (list[str]): List of joke strings.

    Methods:
        validate_joke(joke: str):
            Validates a single joke string.
        add_joke(joke: str, temporary: bool = True):
            Adds a new joke.
        update_joke(index: int, joke: str, temporary: bool = True):
            Updates an existing joke by index.
        remove_joke(index: int, temporary: bool = True):
            Removes a joke by index.
        save():
            Saves current jokes list to file.
    """

    def __init__(self, jokes_file: str) -> None:
        """
        Initialize JokesConfig by loading jokes from a JSON file.

        Args:
            jokes_file (str): Path to the jokes.json file.

        Raises:
            FileNotFoundError: If the jokes file does not exist.
            json.JSONDecodeError: If the file content is not valid JSON.
            ValueError: If the JSON content is not a list of strings.
        """
        self.jokes_file = jokes_file

        with open(self.jokes_file, "r") as f:
            data = json.load(f)

        if not isinstance(data, list) or not all(
            isinstance(joke, str) for joke in data
        ):
            raise ValueError("jokes.json must be a list of strings")

        self.jokes = data

    def validate_joke(self, joke: str) -> None:
        """
        Validate a joke string.

        Args:
            joke (str): The joke to validate.

        Raises:
            TypeError: If joke is not a string.
            ValueError: If joke is empty or too long.
        """
        if not isinstance(joke, str):
            raise TypeError("Joke must be a string")
        if len(joke.strip()) == 0:
            raise ValueError("Joke cannot be empty")
        if len(joke) > 500:
            raise ValueError("Joke is too long (max 500 characters)")

    def add_joke(self, joke: str, temporary: bool = True) -> None:
        """
        Add a new joke to the list.

        Args:
            joke (str): Joke string to add.
            temporary (bool): If True, add only in RAM. If False, save to file.
        """
        self.validate_joke(joke)
        self.jokes.append(joke)

        if not temporary:
            self.save()

    def update_joke(self, index: int, joke: str, temporary: bool = True) -> None:
        """
        Update an existing joke by its index.

        Args:
            index (int): Index of the joke to update.
            joke (str): New joke string.
            temporary (bool): If True, update only in RAM. If False, save to file.

        Raises:
            IndexError: If index is out of range.
        """
        if index < 0 or index >= len(self.jokes):
            raise IndexError("Joke index out of range")
        self.validate_joke(joke)
        self.jokes[index] = joke

        if not temporary:
            self.save()

    def remove_joke(self, index: int, temporary: bool = True) -> None:
        """
        Remove a joke by index.

        Args:
            index (int): Index of the joke to remove.
            temporary (bool): If True, remove only in RAM. If False, save to file.

        Raises:
            IndexError: If index is out of range.
        """
        if index < 0 or index >= len(self.jokes):
            raise IndexError("Joke index out of range")
        del self.jokes[index]

        if not temporary:
            self.save()

    def save(self) -> None:
        """
        Save the current jokes list back to the JSON file.
        """
        with open(self.jokes_file, "w") as f:
            json.dump(self.jokes, f)

    def get_joke(self, index: int) -> str:
        """
        Retrieve a joke by its index.

        Args:
            index (int): Index of the joke to retrieve.

        Returns:
            str: The joke string at the specified index.

        Raises:
            IndexError: If index is out of range.
        """
        if index < 0 or index >= len(self.jokes):
            raise IndexError("Joke index out of range")
        return self.jokes[index]
