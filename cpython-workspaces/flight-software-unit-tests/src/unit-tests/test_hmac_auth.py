"""Unit tests for the HMACAuthenticator class.

This module contains unit tests for the `HMACAuthenticator` class, which is
responsible for generating and verifying HMAC signatures for command messages.
"""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from pysquared.hmac_auth import HMACAuthenticator


@pytest.fixture
def mock_hmac() -> Generator[MagicMock, None, None]:
    """Mocks the HMAC class.
    Yields:
        A MagicMock instance of HMAC.
    """
    with patch("pysquared.hmac_auth.HMAC") as mock_class:
        mock_class.return_value = MagicMock()
        yield mock_class


def test_hmac_authenticator_init():
    """Tests HMACAuthenticator initialization."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key)

    assert authenticator._secret_key == secret_key.encode("utf-8")


def test_generate_hmac():
    """Tests HMAC generation."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key)

    message = '{"command": "send_joke", "name": "TestSat"}'
    counter = 42

    hmac_value = authenticator.generate_hmac(message, counter)

    # HMAC should be a 64-character hex string (SHA-256)
    assert isinstance(hmac_value, str)
    assert len(hmac_value) == 64
    assert all(c in "0123456789abcdef" for c in hmac_value)


def test_generate_hmac_consistency():
    """Tests that HMAC generation is consistent for the same inputs."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key)

    message = '{"command": "reset"}'
    counter = 100

    hmac1 = authenticator.generate_hmac(message, counter)
    hmac2 = authenticator.generate_hmac(message, counter)

    assert hmac1 == hmac2


def test_generate_hmac_different_messages():
    """Tests that different messages produce different HMACs."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key)

    message1 = '{"command": "send_joke"}'
    message2 = '{"command": "reset"}'
    counter = 50

    hmac1 = authenticator.generate_hmac(message1, counter)
    hmac2 = authenticator.generate_hmac(message2, counter)

    assert hmac1 != hmac2


def test_generate_hmac_different_counters():
    """Tests that different counters produce different HMACs."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key)

    message = '{"command": "send_joke"}'
    counter1 = 10
    counter2 = 11

    hmac1 = authenticator.generate_hmac(message, counter1)
    hmac2 = authenticator.generate_hmac(message, counter2)

    assert hmac1 != hmac2


def test_generate_hmac_different_secrets():
    """Tests that different secrets produce different HMACs."""
    message = '{"command": "send_joke"}'
    counter = 25

    authenticator1 = HMACAuthenticator("secret1")
    authenticator2 = HMACAuthenticator("secret2")

    hmac1 = authenticator1.generate_hmac(message, counter)
    hmac2 = authenticator2.generate_hmac(message, counter)

    assert hmac1 != hmac2


def test_verify_hmac_valid(mock_hmac):
    """Tests HMAC verification with valid HMAC."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key)

    message = '{"command": "send_joke"}'
    counter = 75

    mock_hmac.return_value.hexdigest.return_value = "fake_hmac_value"
    hmac_value = authenticator.generate_hmac(message, counter)

    is_valid = authenticator.verify_hmac(message, counter, hmac_value)

    assert is_valid is True


def test_verify_hmac_invalid(mock_hmac):
    """Tests HMAC verification with invalid HMAC."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key)

    message = '{"command": "send_joke"}'
    counter = 75

    # Use a fake HMAC
    fake_hmac = "0" * 64
    mock_hmac.return_value.hexdigest.return_value = "fake_hmac_value"
    is_valid = authenticator.verify_hmac(message, counter, fake_hmac)

    assert is_valid is False


def test_verify_hmac_wrong_message():
    """Tests HMAC verification fails when message is modified."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key)

    original_message = '{"command": "send_joke"}'
    modified_message = '{"command": "reset"}'
    counter = 80

    hmac_value = authenticator.generate_hmac(original_message, counter)
    is_valid = authenticator.verify_hmac(modified_message, counter, hmac_value)

    assert is_valid is False


def test_verify_hmac_wrong_counter():
    """Tests HMAC verification fails when counter is modified (replay attack)."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key)

    message = '{"command": "send_joke"}'
    original_counter = 90
    modified_counter = 89

    hmac_value = authenticator.generate_hmac(message, original_counter)
    is_valid = authenticator.verify_hmac(message, modified_counter, hmac_value)

    assert is_valid is False


def test_verify_hmac_wrong_secret(mock_hmac):
    """Tests HMAC verification fails when secret is different."""
    message = '{"command": "send_joke"}'
    counter = 95

    authenticator1 = HMACAuthenticator("secret1")
    authenticator2 = HMACAuthenticator("secret2")

    hmac_value = authenticator1.generate_hmac(message, counter)
    is_valid = authenticator2.verify_hmac(message, counter, hmac_value)

    assert is_valid is False
