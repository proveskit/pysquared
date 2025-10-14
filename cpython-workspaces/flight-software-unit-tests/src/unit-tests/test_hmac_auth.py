"""Unit tests for the HMACAuthenticator class.

This module contains unit tests for the `HMACAuthenticator` class, which is
responsible for generating and verifying HMAC signatures for command messages.
"""

import hmac

from pysquared.hmac_auth import HMACAuthenticator


def test_hmac_authenticator_init():
    """
    This initizalises the HMACauthenticator and ensures the correct safety key is saved
    """
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key, hmac_class=hmac.new)

    assert authenticator._secret_key == secret_key.encode("utf-8")


def test_generate_hmac():
    """
    this ensures the generate hmac function reyurns a string of the correct size and format
    """
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key, hmac_class=hmac.new)

    message = '{"command": "send_joke", "name": "TestSat"}'
    counter = 42

    hmac_value = authenticator.generate_hmac(message, counter)

    # Check the HMAC is valid hex and 64 characters
    assert isinstance(hmac_value, str)
    assert len(hmac_value) == 64
    assert all(c in "0123456789abcdef" for c in hmac_value)


def test_generate_hmac_consistency():
    """Tests that HMAC generation is consistent for the same inputs."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key, hmac_class=hmac.new)

    message = '{"command": "reset"}'
    counter = 100

    hmac1 = authenticator.generate_hmac(message, counter)
    hmac2 = authenticator.generate_hmac(message, counter)

    assert hmac1 == hmac2


def test_generate_hmac_different_messages():
    """Tests that different messages produce different HMACs."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key, hmac_class=hmac.new)

    message1 = '{"command": "send_joke"}'
    message2 = '{"command": "reset"}'
    counter = 50

    hmac1 = authenticator.generate_hmac(message1, counter)
    hmac2 = authenticator.generate_hmac(message2, counter)

    assert hmac1 != hmac2


def test_generate_hmac_different_counters():
    """Tests that different counters produce different HMACs."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key, hmac_class=hmac.new)

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

    authenticator1 = HMACAuthenticator("secret1", hmac_class=hmac.new)
    authenticator2 = HMACAuthenticator("secret2", hmac_class=hmac.new)

    hmac1 = authenticator1.generate_hmac(message, counter)
    hmac2 = authenticator2.generate_hmac(message, counter)

    assert hmac1 != hmac2


def test_verify_hmac_valid():
    """Tests HMAC verification with valid HMAC."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key, hmac_class=hmac.new)

    message = '{"command": "send_joke"}'
    counter = 75

    hmac_value = authenticator.generate_hmac(message, counter)
    is_valid = authenticator.verify_hmac(message, counter, hmac_value)

    assert is_valid is True


def test_verify_hmac_invalid():
    """Tests HMAC verification with invalid HMAC."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key, hmac_class=hmac.new)

    message = '{"command": "send_joke"}'
    counter = 75

    # Use a fake HMAC
    fake_hmac = "0" * 64
    is_valid = authenticator.verify_hmac(message, counter, fake_hmac)

    assert is_valid is False


def test_verify_hmac_wrong_message():
    """Tests HMAC verification fails when message is modified."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key, hmac_class=hmac.new)

    original_message = '{"command": "send_joke"}'
    modified_message = '{"command": "reset"}'
    counter = 80

    hmac_value = authenticator.generate_hmac(original_message, counter)
    is_valid = authenticator.verify_hmac(modified_message, counter, hmac_value)

    assert is_valid is False


def test_verify_hmac_wrong_counter():
    """Tests HMAC verification fails when counter is modified (replay attack)."""
    secret_key = "test_secret"
    authenticator = HMACAuthenticator(secret_key, hmac_class=hmac.new)

    message = '{"command": "send_joke"}'
    original_counter = 90
    modified_counter = 89

    hmac_value = authenticator.generate_hmac(message, original_counter)
    is_valid = authenticator.verify_hmac(message, modified_counter, hmac_value)

    assert is_valid is False


def test_verify_hmac_wrong_secret():
    """Tests HMAC verification fails when secret is different."""
    message = '{"command": "send_joke"}'
    counter = 95

    authenticator1 = HMACAuthenticator("secret1", hmac_class=hmac.new)
    authenticator2 = HMACAuthenticator("secret2", hmac_class=hmac.new)

    hmac_value = authenticator1.generate_hmac(message, counter)
    is_valid = authenticator2.verify_hmac(message, counter, hmac_value)

    assert is_valid is False


def test_compare_digest_equal_strings():
    """Returns True when strings are identical."""
    assert HMACAuthenticator.compare_digest("abcdef", "abcdef") is True


def test_compare_digest_different_strings_same_length():
    """Returns False when strings differ but are same length."""
    assert HMACAuthenticator.compare_digest("abcdef", "abcdeg") is False


def test_compare_digest_different_length_strings():
    """Returns False when strings are of different lengths."""
    assert HMACAuthenticator.compare_digest("abcdef", "abcde") is False


def test_compare_digest_empty_strings():
    """Returns True when both are empty strings."""
    assert HMACAuthenticator.compare_digest("", "") is True


def test_compare_digest_one_empty_string():
    """Returns False when one is empty and the other is not."""
    assert HMACAuthenticator.compare_digest("", "a") is False
    assert HMACAuthenticator.compare_digest("a", "") is False
